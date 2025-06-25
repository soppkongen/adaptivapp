"""
Production Security and Monitoring Service

This service provides comprehensive security and monitoring capabilities for the
Elite Command Data API, including authentication, authorization, rate limiting,
security event logging, monitoring metrics collection, and alerting.
"""

import hashlib
import hmac
import time
import json
import re
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g, current_app
from collections import defaultdict, deque
import threading
import psutil
import os

from ..models.security_monitoring import (
    APIKey, SecurityEvent, RateLimitRule, MonitoringMetric, SystemAlert, AuditLog,
    SecurityEventType, AlertSeverity, MonitoringMetricType, db
)

logger = logging.getLogger(__name__)

class SecurityMonitoringService:
    """Comprehensive security and monitoring service"""
    
    def __init__(self):
        self.rate_limit_cache = defaultdict(lambda: defaultdict(deque))
        self.metrics_cache = []
        self.cache_lock = threading.Lock()
        self.monitoring_enabled = True
        
    def generate_api_key(self, key_name, user_id, company_id=None, permissions=None, 
                        rate_limit=1000, expires_in_days=None, created_by=None):
        """Generate a new API key"""
        try:
            # Generate secure random key
            import secrets
            raw_key = secrets.token_urlsafe(32)
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            
            # Set expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create API key record
            api_key = APIKey(
                key_hash=key_hash,
                key_name=key_name,
                user_id=user_id,
                company_id=company_id,
                permissions=json.dumps(permissions or []),
                rate_limit=rate_limit,
                expires_at=expires_at,
                created_by=created_by or user_id
            )
            
            db.session.add(api_key)
            db.session.commit()
            
            # Log security event
            self.log_security_event(
                event_type=SecurityEventType.DATA_ACCESS,
                severity=AlertSeverity.LOW,
                description=f"API key '{key_name}' created",
                user_id=user_id,
                company_id=company_id,
                event_data={'api_key_id': api_key.id, 'permissions': permissions}
            )
            
            return {
                'api_key': raw_key,
                'key_id': api_key.key_id,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            
        except Exception as e:
            logger.error(f"Error generating API key: {str(e)}")
            raise
    
    def validate_api_key(self, api_key):
        """Validate an API key and return associated information"""
        try:
            if not api_key:
                return None
            
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find the API key record
            api_key_record = APIKey.query.filter_by(
                key_hash=key_hash,
                is_active=True
            ).first()
            
            if not api_key_record:
                self.log_security_event(
                    event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                    severity=AlertSeverity.MEDIUM,
                    description="Invalid API key used",
                    source_ip=request.remote_addr if request else None,
                    event_data={'provided_key_hash': key_hash[:8] + '...'}
                )
                return None
            
            # Check expiration
            if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
                self.log_security_event(
                    event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                    severity=AlertSeverity.MEDIUM,
                    description="Expired API key used",
                    user_id=api_key_record.user_id,
                    company_id=api_key_record.company_id,
                    api_key_id=api_key_record.id
                )
                return None
            
            # Update usage statistics
            api_key_record.last_used_at = datetime.utcnow()
            api_key_record.usage_count += 1
            db.session.commit()
            
            return {
                'api_key_id': api_key_record.id,
                'key_id': api_key_record.key_id,
                'user_id': api_key_record.user_id,
                'company_id': api_key_record.company_id,
                'permissions': json.loads(api_key_record.permissions) if api_key_record.permissions else [],
                'rate_limit': api_key_record.rate_limit
            }
            
        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return None
    
    def check_rate_limit(self, identifier, endpoint, method, limit_count, time_window):
        """Check if request is within rate limits"""
        try:
            current_time = time.time()
            key = f"{identifier}:{endpoint}:{method}"
            
            with self.cache_lock:
                # Get request history for this identifier/endpoint
                request_history = self.rate_limit_cache[key]
                
                # Remove old requests outside the time window
                while request_history and request_history[0] < current_time - time_window:
                    request_history.popleft()
                
                # Check if we're at the limit
                if len(request_history) >= limit_count:
                    # Log rate limit violation
                    self.log_security_event(
                        event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                        severity=AlertSeverity.MEDIUM,
                        description=f"Rate limit exceeded for {endpoint}",
                        source_ip=request.remote_addr if request else None,
                        endpoint=endpoint,
                        method=method,
                        event_data={
                            'identifier': identifier,
                            'limit_count': limit_count,
                            'time_window': time_window,
                            'current_count': len(request_history)
                        }
                    )
                    return False
                
                # Add current request
                request_history.append(current_time)
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Allow request on error
    
    def apply_rate_limiting(self, api_key_info=None):
        """Apply rate limiting based on rules and API key limits"""
        try:
            endpoint = request.endpoint or request.path
            method = request.method
            
            # Get applicable rate limit rules
            rules = RateLimitRule.query.filter_by(is_active=True).order_by(RateLimitRule.priority.asc()).all()
            
            for rule in rules:
                # Check if rule applies to this request
                if rule.endpoint_pattern and not re.match(rule.endpoint_pattern, endpoint):
                    continue
                
                if rule.method and rule.method != method:
                    continue
                
                # Determine identifier for rate limiting
                identifier = None
                if api_key_info and rule.api_key_id == api_key_info['api_key_id']:
                    identifier = f"api_key:{api_key_info['api_key_id']}"
                elif api_key_info and rule.user_id == api_key_info['user_id']:
                    identifier = f"user:{api_key_info['user_id']}"
                elif api_key_info and rule.company_id == api_key_info['company_id']:
                    identifier = f"company:{api_key_info['company_id']}"
                elif rule.applies_to_all:
                    identifier = f"ip:{request.remote_addr}"
                
                if identifier:
                    # Check rate limit
                    if not self.check_rate_limit(
                        identifier, endpoint, method, 
                        rule.limit_count, rule.time_window
                    ):
                        if rule.block_request:
                            return False
            
            # Check API key specific rate limit
            if api_key_info and api_key_info.get('rate_limit'):
                identifier = f"api_key:{api_key_info['api_key_id']}"
                if not self.check_rate_limit(
                    identifier, endpoint, method,
                    api_key_info['rate_limit'], 3600  # 1 hour window
                ):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying rate limiting: {str(e)}")
            return True  # Allow request on error
    
    def log_security_event(self, event_type, severity, description, 
                          source_ip=None, user_id=None, company_id=None,
                          api_key_id=None, session_id=None, endpoint=None,
                          method=None, event_data=None, risk_score=0.0):
        """Log a security event"""
        try:
            # Get request context if available
            if request:
                source_ip = source_ip or request.remote_addr
                endpoint = endpoint or request.endpoint or request.path
                method = method or request.method
                user_agent = request.headers.get('User-Agent')
            else:
                user_agent = None
            
            # Create security event
            event = SecurityEvent(
                event_type=event_type,
                severity=severity,
                description=description,
                source_ip=source_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                company_id=company_id,
                api_key_id=api_key_id,
                session_id=session_id,
                event_data=json.dumps(event_data) if event_data else None,
                risk_score=risk_score
            )
            
            db.session.add(event)
            db.session.commit()
            
            # Create alert for high-severity events
            if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                self.create_alert(
                    alert_type="security_event",
                    severity=severity,
                    title=f"Security Event: {event_type.value}",
                    message=description,
                    details={'security_event_id': event.id, 'event_data': event_data},
                    source_system="security_monitoring",
                    source_component="security_event_logger"
                )
            
            return event.id
            
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
            return None
    
    def record_metric(self, metric_type, metric_name, value, unit=None,
                     endpoint=None, method=None, company_id=None, user_id=None,
                     metadata=None, tags=None):
        """Record a monitoring metric"""
        try:
            if not self.monitoring_enabled:
                return
            
            metric = MonitoringMetric(
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                unit=unit,
                endpoint=endpoint,
                method=method,
                company_id=company_id,
                user_id=user_id,
                metadata=json.dumps(metadata) if metadata else None,
                tags=json.dumps(tags) if tags else None
            )
            
            # Cache metrics for batch processing
            with self.cache_lock:
                self.metrics_cache.append(metric)
                
                # Flush cache if it gets too large
                if len(self.metrics_cache) >= 100:
                    self._flush_metrics_cache()
            
        except Exception as e:
            logger.error(f"Error recording metric: {str(e)}")
    
    def _flush_metrics_cache(self):
        """Flush cached metrics to database"""
        try:
            if not self.metrics_cache:
                return
            
            db.session.add_all(self.metrics_cache)
            db.session.commit()
            self.metrics_cache.clear()
            
        except Exception as e:
            logger.error(f"Error flushing metrics cache: {str(e)}")
            self.metrics_cache.clear()  # Clear cache to prevent memory issues
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric(
                MonitoringMetricType.CPU_USAGE,
                "system_cpu_usage",
                cpu_percent,
                unit="%"
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric(
                MonitoringMetricType.MEMORY_USAGE,
                "system_memory_usage",
                memory.percent,
                unit="%"
            )
            
            # Database connections (if available)
            try:
                active_connections = db.session.execute("SELECT count(*) FROM pg_stat_activity").scalar()
                self.record_metric(
                    MonitoringMetricType.DATABASE_CONNECTIONS,
                    "database_active_connections",
                    active_connections,
                    unit="count"
                )
            except:
                pass  # Not all databases support this query
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
    
    def create_alert(self, alert_type, severity, title, message, details=None,
                    source_system=None, source_component=None,
                    related_entity_type=None, related_entity_id=None):
        """Create a system alert"""
        try:
            alert = SystemAlert(
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                details=json.dumps(details) if details else None,
                source_system=source_system,
                source_component=source_component,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id
            )
            
            db.session.add(alert)
            db.session.commit()
            
            logger.warning(f"Alert created: {title} - {message}")
            
            return alert.id
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            return None
    
    def log_audit_event(self, action, resource_type, resource_id=None,
                       user_id=None, api_key_id=None, session_id=None,
                       old_values=None, new_values=None, changes_summary=None,
                       company_id=None, success=True, error_message=None,
                       response_code=None, additional_data=None):
        """Log an audit event for compliance"""
        try:
            # Get request context
            endpoint = None
            method = None
            source_ip = None
            user_agent = None
            request_id = None
            
            if request:
                endpoint = request.endpoint or request.path
                method = request.method
                source_ip = request.remote_addr
                user_agent = request.headers.get('User-Agent')
                request_id = getattr(g, 'request_id', None)
            
            audit_log = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                api_key_id=api_key_id,
                session_id=session_id,
                source_ip=source_ip,
                user_agent=user_agent,
                old_values=json.dumps(old_values) if old_values else None,
                new_values=json.dumps(new_values) if new_values else None,
                changes_summary=changes_summary,
                company_id=company_id,
                request_id=request_id,
                success=success,
                error_message=error_message,
                response_code=response_code,
                additional_data=json.dumps(additional_data) if additional_data else None
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            return audit_log.id
            
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
            return None
    
    def get_security_dashboard(self, company_id=None, days=7):
        """Get security dashboard data"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Security events summary
            events_query = SecurityEvent.query.filter(
                SecurityEvent.timestamp >= start_date
            )
            if company_id:
                events_query = events_query.filter(SecurityEvent.company_id == company_id)
            
            total_events = events_query.count()
            critical_events = events_query.filter(SecurityEvent.severity == AlertSeverity.CRITICAL).count()
            high_events = events_query.filter(SecurityEvent.severity == AlertSeverity.HIGH).count()
            
            # Recent security events
            recent_events = events_query.order_by(SecurityEvent.timestamp.desc()).limit(10).all()
            
            # Active alerts
            alerts_query = SystemAlert.query.filter(
                SystemAlert.is_active == True,
                SystemAlert.created_at >= start_date
            )
            active_alerts = alerts_query.count()
            
            # Rate limit violations
            rate_limit_events = events_query.filter(
                SecurityEvent.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
            ).count()
            
            return {
                'summary': {
                    'total_security_events': total_events,
                    'critical_events': critical_events,
                    'high_severity_events': high_events,
                    'active_alerts': active_alerts,
                    'rate_limit_violations': rate_limit_events
                },
                'recent_events': [event.to_dict() for event in recent_events]
            }
            
        except Exception as e:
            logger.error(f"Error getting security dashboard: {str(e)}")
            return {'summary': {}, 'recent_events': []}

# Global service instance
security_monitoring_service = SecurityMonitoringService()

def require_api_key(permissions=None):
    """Decorator to require valid API key authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header
            api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
            
            if not api_key:
                security_monitoring_service.log_security_event(
                    event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                    severity=AlertSeverity.MEDIUM,
                    description="Missing API key"
                )
                return jsonify({'error': 'API key required'}), 401
            
            # Validate API key
            api_key_info = security_monitoring_service.validate_api_key(api_key)
            if not api_key_info:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Check permissions
            if permissions:
                user_permissions = api_key_info.get('permissions', [])
                if not any(perm in user_permissions for perm in permissions):
                    security_monitoring_service.log_security_event(
                        event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                        severity=AlertSeverity.MEDIUM,
                        description=f"Insufficient permissions for {request.endpoint}",
                        user_id=api_key_info['user_id'],
                        company_id=api_key_info['company_id'],
                        api_key_id=api_key_info['api_key_id']
                    )
                    return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Check rate limits
            if not security_monitoring_service.apply_rate_limiting(api_key_info):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Store API key info in request context
            g.api_key_info = api_key_info
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def monitor_performance(f):
    """Decorator to monitor endpoint performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            
            # Record successful request metrics
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            security_monitoring_service.record_metric(
                MonitoringMetricType.RESPONSE_TIME,
                f"{request.endpoint}_response_time",
                response_time,
                unit="ms",
                endpoint=request.endpoint,
                method=request.method
            )
            
            security_monitoring_service.record_metric(
                MonitoringMetricType.REQUEST_COUNT,
                f"{request.endpoint}_request_count",
                1,
                unit="count",
                endpoint=request.endpoint,
                method=request.method
            )
            
            return result
            
        except Exception as e:
            # Record error metrics
            security_monitoring_service.record_metric(
                MonitoringMetricType.ERROR_RATE,
                f"{request.endpoint}_error_rate",
                1,
                unit="count",
                endpoint=request.endpoint,
                method=request.method
            )
            
            # Log security event for errors
            security_monitoring_service.log_security_event(
                event_type=SecurityEventType.SYSTEM_BREACH_ATTEMPT,
                severity=AlertSeverity.LOW,
                description=f"Error in {request.endpoint}: {str(e)}",
                user_id=getattr(g, 'api_key_info', {}).get('user_id'),
                company_id=getattr(g, 'api_key_info', {}).get('company_id')
            )
            
            raise
            
    return decorated_function

