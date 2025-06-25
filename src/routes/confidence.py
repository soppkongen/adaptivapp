from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging

from ..services.confidence_lineage import confidence_lineage_service
from ..models.confidence_lineage import (
    DataLineage, ConfidenceScore, ConfidenceFactor, LineageGraph,
    ConfidenceThreshold, ConfidenceAlert, ConfidenceFactorType,
    LineageEventType, db
)

logger = logging.getLogger(__name__)

confidence_bp = Blueprint('confidence', __name__, url_prefix='/api/confidence')

@confidence_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for confidence scoring and lineage system"""
    try:
        # Check database connectivity
        lineage_count = DataLineage.query.count()
        confidence_count = ConfidenceScore.query.count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'confidence_lineage',
            'timestamp': datetime.utcnow().isoformat(),
            'stats': {
                'total_lineage_events': lineage_count,
                'total_confidence_scores': confidence_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Confidence service health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'confidence_lineage',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@confidence_bp.route('/lineage', methods=['POST'])
def create_lineage_event():
    """Create a new data lineage event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['event_type', 'transformation_method', 'system_component']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create lineage event
        lineage_id = confidence_lineage_service.create_lineage_event(
            event_type=LineageEventType(data['event_type']),
            transformation_method=data['transformation_method'],
            system_component=data['system_component'],
            source_data_id=data.get('source_data_id'),
            source_data_type=data.get('source_data_type'),
            output_data_id=data.get('output_data_id'),
            output_data_type=data.get('output_data_type'),
            transformation_parameters=data.get('transformation_parameters'),
            parent_lineage_id=data.get('parent_lineage_id'),
            company_id=data.get('company_id'),
            user_id=data.get('user_id'),
            processing_time_ms=data.get('processing_time_ms'),
            error_details=data.get('error_details')
        )
        
        return jsonify({
            'success': True,
            'lineage_id': lineage_id,
            'message': 'Lineage event created successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error creating lineage event: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/score', methods=['POST'])
def calculate_confidence_score():
    """Calculate confidence score for a data point"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['lineage_id', 'data_point_id', 'data_point_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Calculate confidence score
        score_id = confidence_lineage_service.calculate_confidence_score(
            lineage_id=data['lineage_id'],
            data_point_id=data['data_point_id'],
            data_point_type=data['data_point_type'],
            metric_name=data.get('metric_name'),
            confidence_factors=data.get('confidence_factors'),
            company_id=data.get('company_id')
        )
        
        # Get the calculated score
        confidence_score = ConfidenceScore.query.filter_by(score_id=score_id).first()
        
        return jsonify({
            'success': True,
            'score_id': score_id,
            'confidence_score': confidence_score.to_dict(),
            'message': 'Confidence score calculated successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error calculating confidence score: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/lineage/<lineage_id>', methods=['GET'])
def get_lineage_event(lineage_id):
    """Get a specific lineage event"""
    try:
        lineage = DataLineage.query.filter_by(lineage_id=lineage_id).first()
        if not lineage:
            return jsonify({'error': 'Lineage event not found'}), 404
        
        return jsonify({
            'success': True,
            'lineage': lineage.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting lineage event: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/score/<score_id>', methods=['GET'])
def get_confidence_score(score_id):
    """Get a specific confidence score with detailed breakdown"""
    try:
        confidence_score = ConfidenceScore.query.filter_by(score_id=score_id).first()
        if not confidence_score:
            return jsonify({'error': 'Confidence score not found'}), 404
        
        # Get confidence factors
        factors = ConfidenceFactor.query.filter_by(confidence_score_id=score_id).all()
        
        result = confidence_score.to_dict()
        result['factors'] = [factor.to_dict() for factor in factors]
        
        return jsonify({
            'success': True,
            'confidence_score': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting confidence score: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/lineage/trace/<data_point_id>', methods=['GET'])
def trace_data_lineage(data_point_id):
    """Trace the complete lineage of a data point"""
    try:
        # Get query parameters
        direction = request.args.get('direction', 'backward')  # 'forward', 'backward', 'both'
        max_depth = int(request.args.get('max_depth', 10))
        
        # Find lineage events for this data point
        lineage_events = DataLineage.query.filter(
            db.or_(
                DataLineage.source_data_id == data_point_id,
                DataLineage.output_data_id == data_point_id
            )
        ).all()
        
        if not lineage_events:
            return jsonify({'error': 'No lineage found for data point'}), 404
        
        # Build lineage graph
        lineage_graph = []
        for event in lineage_events:
            lineage_graph.append(event.to_dict())
        
        return jsonify({
            'success': True,
            'data_point_id': data_point_id,
            'direction': direction,
            'max_depth': max_depth,
            'lineage_graph': lineage_graph,
            'total_events': len(lineage_graph)
        }), 200
        
    except Exception as e:
        logger.error(f"Error tracing data lineage: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/company/<int:company_id>/dashboard', methods=['GET'])
def get_confidence_dashboard(company_id):
    """Get confidence dashboard for a company"""
    try:
        # Get time range
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get confidence scores for the company
        confidence_scores = ConfidenceScore.query.filter(
            ConfidenceScore.company_id == company_id,
            ConfidenceScore.calculation_timestamp >= start_date
        ).all()
        
        # Calculate statistics
        total_scores = len(confidence_scores)
        if total_scores > 0:
            avg_confidence = sum(score.overall_confidence for score in confidence_scores) / total_scores
            confidence_levels = {}
            for score in confidence_scores:
                level = score.confidence_level
                confidence_levels[level] = confidence_levels.get(level, 0) + 1
        else:
            avg_confidence = 0
            confidence_levels = {}
        
        # Get active alerts
        active_alerts = ConfidenceAlert.query.filter(
            ConfidenceAlert.company_id == company_id,
            ConfidenceAlert.status == 'active'
        ).count()
        
        # Get recent lineage events
        recent_lineage = DataLineage.query.filter(
            DataLineage.company_id == company_id,
            DataLineage.event_timestamp >= start_date
        ).order_by(DataLineage.event_timestamp.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'company_id': company_id,
            'time_range_days': days,
            'statistics': {
                'total_confidence_scores': total_scores,
                'average_confidence': round(avg_confidence, 3),
                'confidence_levels': confidence_levels,
                'active_alerts': active_alerts
            },
            'recent_lineage': [event.to_dict() for event in recent_lineage]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting confidence dashboard: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/alerts', methods=['GET'])
def get_confidence_alerts():
    """Get confidence alerts"""
    try:
        # Get query parameters
        company_id = request.args.get('company_id', type=int)
        status = request.args.get('status', 'active')
        alert_level = request.args.get('alert_level')
        limit = int(request.args.get('limit', 50))
        
        # Build query
        query = ConfidenceAlert.query
        
        if company_id:
            query = query.filter(ConfidenceAlert.company_id == company_id)
        
        if status:
            query = query.filter(ConfidenceAlert.status == status)
        
        if alert_level:
            query = query.filter(ConfidenceAlert.alert_level == alert_level)
        
        alerts = query.order_by(ConfidenceAlert.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'total_alerts': len(alerts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting confidence alerts: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge a confidence alert"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        alert = ConfidenceAlert.query.filter_by(alert_id=alert_id).first()
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        alert.status = 'acknowledged'
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert acknowledged successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/thresholds', methods=['GET'])
def get_confidence_thresholds():
    """Get confidence thresholds"""
    try:
        company_id = request.args.get('company_id', type=int)
        
        query = ConfidenceThreshold.query.filter(ConfidenceThreshold.is_active == True)
        
        if company_id:
            query = query.filter(
                db.or_(
                    ConfidenceThreshold.company_id == company_id,
                    ConfidenceThreshold.company_id.is_(None)
                )
            )
        
        thresholds = query.all()
        
        return jsonify({
            'success': True,
            'thresholds': [threshold.to_dict() for threshold in thresholds]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting confidence thresholds: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/thresholds', methods=['POST'])
def create_confidence_threshold():
    """Create a new confidence threshold"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['threshold_name', 'data_type', 'use_case', 'critical_threshold', 
                          'low_threshold', 'medium_threshold', 'high_threshold',
                          'critical_action', 'low_action', 'medium_action', 'high_action', 'created_by']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        threshold = ConfidenceThreshold(
            threshold_name=data['threshold_name'],
            data_type=data['data_type'],
            use_case=data['use_case'],
            critical_threshold=data['critical_threshold'],
            low_threshold=data['low_threshold'],
            medium_threshold=data['medium_threshold'],
            high_threshold=data['high_threshold'],
            critical_action=data['critical_action'],
            low_action=data['low_action'],
            medium_action=data['medium_action'],
            high_action=data['high_action'],
            company_id=data.get('company_id'),
            business_model_type=data.get('business_model_type'),
            created_by=data['created_by']
        )
        
        db.session.add(threshold)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'threshold': threshold.to_dict(),
            'message': 'Confidence threshold created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating confidence threshold: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/analytics/trends', methods=['GET'])
def get_confidence_trends():
    """Get confidence trends and analytics"""
    try:
        # Get query parameters
        company_id = request.args.get('company_id', type=int)
        days = int(request.args.get('days', 30))
        granularity = request.args.get('granularity', 'daily')  # 'hourly', 'daily', 'weekly'
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = ConfidenceScore.query.filter(
            ConfidenceScore.calculation_timestamp >= start_date
        )
        
        if company_id:
            query = query.filter(ConfidenceScore.company_id == company_id)
        
        confidence_scores = query.all()
        
        # Calculate trends
        trends = {}
        for score in confidence_scores:
            date_key = score.calculation_timestamp.strftime('%Y-%m-%d')
            if date_key not in trends:
                trends[date_key] = {
                    'date': date_key,
                    'scores': [],
                    'count': 0,
                    'average': 0
                }
            trends[date_key]['scores'].append(score.overall_confidence)
            trends[date_key]['count'] += 1
        
        # Calculate averages
        for date_key in trends:
            scores = trends[date_key]['scores']
            trends[date_key]['average'] = sum(scores) / len(scores) if scores else 0
            del trends[date_key]['scores']  # Remove raw scores to reduce response size
        
        return jsonify({
            'success': True,
            'company_id': company_id,
            'time_range_days': days,
            'granularity': granularity,
            'trends': list(trends.values())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting confidence trends: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@confidence_bp.route('/factors/analysis', methods=['GET'])
def get_factor_analysis():
    """Get confidence factor analysis"""
    try:
        # Get query parameters
        company_id = request.args.get('company_id', type=int)
        days = int(request.args.get('days', 30))
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get confidence factors
        query = db.session.query(ConfidenceFactor).join(ConfidenceScore).filter(
            ConfidenceScore.calculation_timestamp >= start_date
        )
        
        if company_id:
            query = query.filter(ConfidenceScore.company_id == company_id)
        
        factors = query.all()
        
        # Analyze factors
        factor_analysis = {}
        for factor in factors:
            factor_type = factor.factor_type.value
            if factor_type not in factor_analysis:
                factor_analysis[factor_type] = {
                    'factor_type': factor_type,
                    'count': 0,
                    'total_score': 0,
                    'total_weight': 0,
                    'average_score': 0,
                    'average_weight': 0
                }
            
            analysis = factor_analysis[factor_type]
            analysis['count'] += 1
            analysis['total_score'] += factor.factor_score
            analysis['total_weight'] += factor.factor_weight
        
        # Calculate averages
        for factor_type in factor_analysis:
            analysis = factor_analysis[factor_type]
            if analysis['count'] > 0:
                analysis['average_score'] = analysis['total_score'] / analysis['count']
                analysis['average_weight'] = analysis['total_weight'] / analysis['count']
        
        return jsonify({
            'success': True,
            'company_id': company_id,
            'time_range_days': days,
            'factor_analysis': list(factor_analysis.values())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting factor analysis: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

