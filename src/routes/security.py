from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
import json

from ..services.security_monitoring import (
    security_monitoring_service, require_api_key, monitor_performance
)
from ..models.security_monitoring import (
    APIKey, SecurityEvent, RateLimitRule, MonitoringMetric, SystemAlert, AuditLog,
    SecurityEventType, AlertSeverity, MonitoringMetricType, db
)

security_bp = Blueprint('security', __name__, url_prefix='/api/security')
logger = logging.getLogger(__name__)

@security_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for security and monitoring system"""
    try:
        # Test database connectivity
        api_key_count = APIKey.query.count()
        event_count = SecurityEvent.query.count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'Production Security and Monitoring',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'total_api_keys': api_key_count,
                'total_security_events': event_count
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@security_bp.route('/api-keys/generate', methods=['POST'])
@require_api_key(permissions=['admin', 'api_key_management'])
@monitor_performance
def generate_api_key():
    """Generate a new API key"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['key_name', 'user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate API key
        result = security_monitoring_service.generate_api_key(
            key_name=data['key_name'],
            user_id=data['user_id'],
            company_id=data.get('company_id'),
            permissions=data.get('permissions', []),
            rate_limit=data.get('rate_limit', 1000),
            expires_in_days=data.get('expires_in_days'),
            created_by=data.get('created_by', data['user_id'])
        )
        
        return jsonify({
            'success': True,
            'api_key': result['api_key'],
            'key_id': result['key_id'],
            'expires_at': result['expires_at'],
            'message': 'API key generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating API key: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/api-keys', methods=['GET'])
@require_api_key(permissions=['admin', 'api_key_management'])
@monitor_performance
def list_api_keys():
    """List API keys with filtering options"""
    try:
        company_id = request.args.get('company_id', type=int)
        user_id = request.args.get('user_id', type=int)
        is_active = request.args.get('is_active', type=bool)
        limit = request.args.get('limit', 50, type=int)
        
        query = APIKey.query
        
        if company_id:
            query = query.filter(APIKey.company_id == company_id)
        
        if user_id:
            query = query.filter(APIKey.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(APIKey.is_active == is_active)
        
        api_keys = query.order_by(APIKey.created_at.desc()).limit(limit).all()
        
        # Remove sensitive information
        api_keys_data = []
        for key in api_keys:
            key_data = key.to_dict()
            key_data.pop('key_hash', None)  # Never expose the hash
            api_keys_data.append(key_data)
        
        return jsonify({
            'success': True,
            'api_keys': api_keys_data,
            'count': len(api_keys_data)
        })
        
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/api-keys/<key_id>/revoke', methods=['POST'])
@require_api_key(permissions=['admin', 'api_key_management'])
@monitor_performance
def revoke_api_key(key_id):
    """Revoke an API key"""
    try:
        data = request.get_json() or {}
        
        api_key = APIKey.query.filter_by(key_id=key_id).first()
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Revoke the key
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = data.get('revoked_by')
        api_key.revocation_reason = data.get('reason', 'Manual revocation')
        
        db.session.commit()
        
        # Log security event
        security_monitoring_service.log_security_event(
            event_type=SecurityEventType.DATA_MODIFICATION,
            severity=AlertSeverity.MEDIUM,
            description=f"API key '{api_key.key_name}' revoked",
            user_id=api_key.user_id,
            company_id=api_key.company_id,
            api_key_id=api_key.id,
            event_data={'revocation_reason': api_key.revocation_reason}
        )
        
        return jsonify({
            'success': True,
            'message': 'API key revoked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/events', methods=['GET'])
@require_api_key(permissions=['admin', 'security_monitoring'])
@monitor_performance
def get_security_events():
    """Get security events with filtering options"""
    try:
        company_id = request.args.get('company_id', type=int)
        event_type = request.args.get('event_type')
        severity = request.args.get('severity')
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = SecurityEvent.query.filter(
            SecurityEvent.timestamp >= start_date
        )
        
        if company_id:
            query = query.filter(SecurityEvent.company_id == company_id)
        
        if event_type:
            try:
                event_type_enum = SecurityEventType(event_type)
                query = query.filter(SecurityEvent.event_type == event_type_enum)
            except ValueError:
                return jsonify({'error': f'Invalid event type: {event_type}'}), 400
        
        if severity:
            try:
                severity_enum = AlertSeverity(severity)
                query = query.filter(SecurityEvent.severity == severity_enum)
            except ValueError:
                return jsonify({'error': f'Invalid severity: {severity}'}), 400
        
        events = query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'events': [event.to_dict() for event in events],
            'count': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error getting security events: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/rate-limits/rules', methods=['GET'])
@require_api_key(permissions=['admin', 'rate_limit_management'])
@monitor_performance
def get_rate_limit_rules():
    """Get rate limit rules"""
    try:
        company_id = request.args.get('company_id', type=int)
        is_active = request.args.get('is_active', type=bool)
        
        query = RateLimitRule.query
        
        if company_id:
            query = query.filter(
                (RateLimitRule.company_id == company_id) | 
                (RateLimitRule.applies_to_all == True)
            )
        
        if is_active is not None:
            query = query.filter(RateLimitRule.is_active == is_active)
        
        rules = query.order_by(RateLimitRule.priority.asc()).all()
        
        return jsonify({
            'success': True,
            'rules': [rule.to_dict() for rule in rules],
            'count': len(rules)
        })
        
    except Exception as e:
        logger.error(f"Error getting rate limit rules: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/rate-limits/rules/create', methods=['POST'])
@require_api_key(permissions=['admin', 'rate_limit_management'])
@monitor_performance
def create_rate_limit_rule():
    """Create a new rate limit rule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['rule_name', 'limit_count', 'time_window', 'created_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create rate limit rule
        rule = RateLimitRule(
            rule_name=data['rule_name'],
            description=data.get('description'),
            endpoint_pattern=data.get('endpoint_pattern'),
            method=data.get('method'),
            limit_count=data['limit_count'],
            time_window=data['time_window'],
            applies_to_all=data.get('applies_to_all', True),
            user_id=data.get('user_id'),
            company_id=data.get('company_id'),
            api_key_id=data.get('api_key_id'),
            priority=data.get('priority', 100),
            block_request=data.get('block_request', True),
            send_alert=data.get('send_alert', True),
            log_violation=data.get('log_violation', True),
            created_by=data['created_by']
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rule_id': rule.id,
            'message': 'Rate limit rule created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating rate limit rule: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/metrics', methods=['GET'])
@require_api_key(permissions=['admin', 'monitoring'])
@monitor_performance
def get_monitoring_metrics():
    """Get monitoring metrics with filtering options"""
    try:
        metric_type = request.args.get('metric_type')
        company_id = request.args.get('company_id', type=int)
        endpoint = request.args.get('endpoint')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 1000, type=int)
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours)
        
        query = MonitoringMetric.query.filter(
            MonitoringMetric.timestamp >= start_date
        )
        
        if metric_type:
            try:
                metric_type_enum = MonitoringMetricType(metric_type)
                query = query.filter(MonitoringMetric.metric_type == metric_type_enum)
            except ValueError:
                return jsonify({'error': f'Invalid metric type: {metric_type}'}), 400
        
        if company_id:
            query = query.filter(MonitoringMetric.company_id == company_id)
        
        if endpoint:
            query = query.filter(MonitoringMetric.endpoint == endpoint)
        
        metrics = query.order_by(MonitoringMetric.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'metrics': [metric.to_dict() for metric in metrics],
            'count': len(metrics)
        })
        
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/alerts', methods=['GET'])
@require_api_key(permissions=['admin', 'monitoring'])
@monitor_performance
def get_system_alerts():
    """Get system alerts with filtering options"""
    try:
        severity = request.args.get('severity')
        is_active = request.args.get('is_active', type=bool)
        is_acknowledged = request.args.get('is_acknowledged', type=bool)
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = SystemAlert.query.filter(
            SystemAlert.created_at >= start_date
        )
        
        if severity:
            try:
                severity_enum = AlertSeverity(severity)
                query = query.filter(SystemAlert.severity == severity_enum)
            except ValueError:
                return jsonify({'error': f'Invalid severity: {severity}'}), 400
        
        if is_active is not None:
            query = query.filter(SystemAlert.is_active == is_active)
        
        if is_acknowledged is not None:
            query = query.filter(SystemAlert.is_acknowledged == is_acknowledged)
        
        alerts = query.order_by(SystemAlert.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
@require_api_key(permissions=['admin', 'monitoring'])
@monitor_performance
def acknowledge_alert(alert_id):
    """Acknowledge a system alert"""
    try:
        data = request.get_json() or {}
        
        alert = SystemAlert.query.filter_by(alert_id=alert_id).first()
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        # Acknowledge the alert
        alert.is_acknowledged = True
        alert.acknowledged_by = data.get('acknowledged_by')
        alert.acknowledged_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert acknowledged successfully'
        })
        
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/audit-logs', methods=['GET'])
@require_api_key(permissions=['admin', 'audit_access'])
@monitor_performance
def get_audit_logs():
    """Get audit logs with filtering options"""
    try:
        action = request.args.get('action')
        resource_type = request.args.get('resource_type')
        user_id = request.args.get('user_id', type=int)
        company_id = request.args.get('company_id', type=int)
        success = request.args.get('success', type=bool)
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 1000, type=int)
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = AuditLog.query.filter(
            AuditLog.timestamp >= start_date
        )
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if company_id:
            query = query.filter(AuditLog.company_id == company_id)
        
        if success is not None:
            query = query.filter(AuditLog.success == success)
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'audit_logs': [log.to_dict() for log in logs],
            'count': len(logs)
        })
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/dashboard', methods=['GET'])
@require_api_key(permissions=['admin', 'monitoring'])
@monitor_performance
def get_security_dashboard():
    """Get comprehensive security and monitoring dashboard"""
    try:
        company_id = request.args.get('company_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        # Get security dashboard data
        dashboard_data = security_monitoring_service.get_security_dashboard(company_id, days)
        
        # Add monitoring metrics summary
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Average response time
        avg_response_time = db.session.query(db.func.avg(MonitoringMetric.value)).filter(
            MonitoringMetric.metric_type == MonitoringMetricType.RESPONSE_TIME,
            MonitoringMetric.timestamp >= start_date
        ).scalar() or 0.0
        
        # Error rate
        total_requests = db.session.query(db.func.sum(MonitoringMetric.value)).filter(
            MonitoringMetric.metric_type == MonitoringMetricType.REQUEST_COUNT,
            MonitoringMetric.timestamp >= start_date
        ).scalar() or 0
        
        total_errors = db.session.query(db.func.sum(MonitoringMetric.value)).filter(
            MonitoringMetric.metric_type == MonitoringMetricType.ERROR_RATE,
            MonitoringMetric.timestamp >= start_date
        ).scalar() or 0
        
        error_rate = (total_errors / max(total_requests, 1)) * 100
        
        # Active API keys
        active_api_keys = APIKey.query.filter_by(is_active=True).count()
        
        dashboard_data['monitoring'] = {
            'average_response_time': round(avg_response_time, 2),
            'error_rate': round(error_rate, 2),
            'total_requests': int(total_requests),
            'total_errors': int(total_errors),
            'active_api_keys': active_api_keys
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting security dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/system/collect-metrics', methods=['POST'])
@require_api_key(permissions=['admin', 'system_monitoring'])
@monitor_performance
def collect_system_metrics():
    """Manually trigger system metrics collection"""
    try:
        security_monitoring_service.collect_system_metrics()
        
        return jsonify({
            'success': True,
            'message': 'System metrics collected successfully'
        })
        
    except Exception as e:
        logger.error(f"Error collecting system metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@security_bp.route('/test/create-alert', methods=['POST'])
@require_api_key(permissions=['admin'])
@monitor_performance
def create_test_alert():
    """Create a test alert for testing purposes"""
    try:
        data = request.get_json() or {}
        
        alert_id = security_monitoring_service.create_alert(
            alert_type="test_alert",
            severity=AlertSeverity(data.get('severity', 'low')),
            title=data.get('title', 'Test Alert'),
            message=data.get('message', 'This is a test alert'),
            details=data.get('details'),
            source_system="security_monitoring",
            source_component="test_endpoint"
        )
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': 'Test alert created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating test alert: {str(e)}")
        return jsonify({'error': str(e)}), 500

