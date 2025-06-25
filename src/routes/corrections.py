from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

from ..services.data_corrections import data_correction_service
from ..models.corrections import (
    CorrectionType, AnnotationType, DataCorrection, DataAnnotation,
    UserFeedback, CorrectionWorkflow, db
)

corrections_bp = Blueprint('corrections', __name__, url_prefix='/api/corrections')
logger = logging.getLogger(__name__)

@corrections_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for data corrections system"""
    try:
        # Test database connectivity
        correction_count = DataCorrection.query.count()
        annotation_count = DataAnnotation.query.count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'Data Corrections and Annotations',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'total_corrections': correction_count,
                'total_annotations': annotation_count
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@corrections_bp.route('/submit', methods=['POST'])
def submit_correction():
    """Submit a data correction request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['data_point_id', 'data_point_type', 'correction_type', 
                          'corrected_value', 'correction_reason', 'submitted_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse correction type
        try:
            correction_type = CorrectionType(data['correction_type'])
        except ValueError:
            return jsonify({'error': f'Invalid correction type: {data["correction_type"]}'}), 400
        
        # Submit correction
        correction_id = data_correction_service.submit_correction(
            data_point_id=data['data_point_id'],
            data_point_type=data['data_point_type'],
            correction_type=correction_type,
            corrected_value=data['corrected_value'],
            correction_reason=data['correction_reason'],
            submitted_by=data['submitted_by'],
            field_name=data.get('field_name'),
            original_value=data.get('original_value'),
            business_impact=data.get('business_impact'),
            urgency=data.get('urgency', 'medium'),
            company_id=data.get('company_id'),
            lineage_id=data.get('lineage_id')
        )
        
        return jsonify({
            'success': True,
            'correction_id': correction_id,
            'message': 'Correction submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting correction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/approve/<correction_id>', methods=['POST'])
def approve_correction(correction_id):
    """Approve a data correction"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if 'approved_by' not in data:
            return jsonify({'error': 'Missing required field: approved_by'}), 400
        
        success = data_correction_service.approve_correction(
            correction_id=correction_id,
            approved_by=data['approved_by'],
            implementation_notes=data.get('implementation_notes')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Correction approved successfully'
            })
        else:
            return jsonify({'error': 'Failed to approve correction'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error approving correction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/implement/<correction_id>', methods=['POST'])
def implement_correction(correction_id):
    """Implement a data correction"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if 'implemented_by' not in data:
            return jsonify({'error': 'Missing required field: implemented_by'}), 400
        
        success = data_correction_service.implement_correction(
            correction_id=correction_id,
            implemented_by=data['implemented_by']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Correction implemented successfully'
            })
        else:
            return jsonify({'error': 'Failed to implement correction'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error implementing correction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/queue', methods=['GET'])
def get_corrections_queue():
    """Get corrections queue for review"""
    try:
        # Parse query parameters
        company_id = request.args.get('company_id', type=int)
        status = request.args.get('status')
        urgency = request.args.get('urgency')
        limit = request.args.get('limit', 50, type=int)
        
        corrections = data_correction_service.get_corrections_queue(
            company_id=company_id,
            status=status,
            urgency=urgency,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'corrections': corrections,
            'count': len(corrections)
        })
        
    except Exception as e:
        logger.error(f"Error getting corrections queue: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/annotations/create', methods=['POST'])
def create_annotation():
    """Create a data annotation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['data_point_id', 'data_point_type', 'annotation_type', 
                          'title', 'content', 'created_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse annotation type
        try:
            annotation_type = AnnotationType(data['annotation_type'])
        except ValueError:
            return jsonify({'error': f'Invalid annotation type: {data["annotation_type"]}'}), 400
        
        # Parse expires_at if provided
        expires_at = None
        if data.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid expires_at format. Use ISO format.'}), 400
        
        # Create annotation
        annotation_id = data_correction_service.create_annotation(
            data_point_id=data['data_point_id'],
            data_point_type=data['data_point_type'],
            annotation_type=annotation_type,
            title=data['title'],
            content=data['content'],
            created_by=data['created_by'],
            field_name=data.get('field_name'),
            visibility=data.get('visibility', 'company'),
            priority=data.get('priority', 'medium'),
            tags=data.get('tags'),
            company_id=data.get('company_id'),
            lineage_id=data.get('lineage_id'),
            expires_at=expires_at
        )
        
        return jsonify({
            'success': True,
            'annotation_id': annotation_id,
            'message': 'Annotation created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating annotation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/annotations/<data_point_id>', methods=['GET'])
def get_annotations(data_point_id):
    """Get annotations for a data point"""
    try:
        # Parse query parameters
        annotation_type = request.args.get('annotation_type')
        visibility = request.args.get('visibility')
        
        annotations = data_correction_service.get_data_annotations(
            data_point_id=data_point_id,
            annotation_type=annotation_type,
            visibility=visibility
        )
        
        return jsonify({
            'success': True,
            'data_point_id': data_point_id,
            'annotations': annotations,
            'count': len(annotations)
        })
        
    except Exception as e:
        logger.error(f"Error getting annotations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/feedback/submit', methods=['POST'])
def submit_feedback():
    """Submit user feedback"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['target_type', 'target_id', 'feedback_type', 
                          'title', 'description', 'submitted_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate rating if provided
        if data.get('rating') and (data['rating'] < 1 or data['rating'] > 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Submit feedback
        feedback_id = data_correction_service.submit_feedback(
            target_type=data['target_type'],
            target_id=data['target_id'],
            feedback_type=data['feedback_type'],
            title=data['title'],
            description=data['description'],
            submitted_by=data['submitted_by'],
            rating=data.get('rating'),
            severity=data.get('severity', 'medium'),
            category=data.get('category'),
            tags=data.get('tags'),
            company_id=data.get('company_id')
        )
        
        return jsonify({
            'success': True,
            'feedback_id': feedback_id,
            'message': 'Feedback submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/impact/analysis', methods=['GET'])
def get_impact_analysis():
    """Get correction impact analysis"""
    try:
        # Parse query parameters
        company_id = request.args.get('company_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        analysis = data_correction_service.get_correction_impact_analysis(
            company_id=company_id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting impact analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/workflows', methods=['GET'])
def get_workflows():
    """Get correction workflows"""
    try:
        company_id = request.args.get('company_id', type=int)
        
        query = CorrectionWorkflow.query.filter(CorrectionWorkflow.is_active == True)
        if company_id:
            query = query.filter(CorrectionWorkflow.company_id == company_id)
        
        workflows = query.order_by(CorrectionWorkflow.priority.asc()).all()
        
        return jsonify({
            'success': True,
            'workflows': [workflow.to_dict() for workflow in workflows],
            'count': len(workflows)
        })
        
    except Exception as e:
        logger.error(f"Error getting workflows: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/workflows/create', methods=['POST'])
def create_workflow():
    """Create a correction workflow"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['workflow_name', 'created_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse correction type if provided
        correction_type = None
        if data.get('correction_type'):
            try:
                correction_type = CorrectionType(data['correction_type'])
            except ValueError:
                return jsonify({'error': f'Invalid correction type: {data["correction_type"]}'}), 400
        
        # Create workflow
        workflow = CorrectionWorkflow(
            workflow_name=data['workflow_name'],
            workflow_description=data.get('workflow_description'),
            data_type_pattern=data.get('data_type_pattern'),
            correction_type=correction_type,
            business_impact_threshold=data.get('business_impact_threshold'),
            confidence_impact_threshold=data.get('confidence_impact_threshold'),
            requires_approval=data.get('requires_approval', True),
            auto_approve_threshold=data.get('auto_approve_threshold'),
            approval_roles=json.dumps(data.get('approval_roles', [])),
            notification_roles=json.dumps(data.get('notification_roles', [])),
            auto_implement=data.get('auto_implement', False),
            implementation_delay_hours=data.get('implementation_delay_hours', 0),
            requires_backup=data.get('requires_backup', True),
            company_id=data.get('company_id'),
            priority=data.get('priority', 100),
            created_by=data['created_by']
        )
        
        db.session.add(workflow)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'workflow_id': workflow.id,
            'message': 'Workflow created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get corrections dashboard data"""
    try:
        company_id = request.args.get('company_id', type=int)
        
        # Get queue statistics
        pending_corrections = DataCorrection.query.filter(
            DataCorrection.status == 'pending'
        )
        if company_id:
            pending_corrections = pending_corrections.filter(DataCorrection.company_id == company_id)
        pending_count = pending_corrections.count()
        
        # Get urgent corrections
        urgent_corrections = pending_corrections.filter(
            DataCorrection.urgency == 'urgent'
        ).count()
        
        # Get recent feedback
        recent_feedback = UserFeedback.query.filter(
            UserFeedback.status == 'open'
        )
        if company_id:
            recent_feedback = recent_feedback.filter(UserFeedback.company_id == company_id)
        feedback_count = recent_feedback.count()
        
        # Get impact analysis
        impact_analysis = data_correction_service.get_correction_impact_analysis(
            company_id=company_id, days=7
        )
        
        return jsonify({
            'success': True,
            'dashboard': {
                'pending_corrections': pending_count,
                'urgent_corrections': urgent_corrections,
                'open_feedback': feedback_count,
                'weekly_impact': impact_analysis
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@corrections_bp.route('/correction/<correction_id>', methods=['GET'])
def get_correction_details(correction_id):
    """Get detailed information about a specific correction"""
    try:
        correction = DataCorrection.query.filter_by(correction_id=correction_id).first()
        if not correction:
            return jsonify({'error': 'Correction not found'}), 404
        
        # Get related annotations
        annotations = data_correction_service.get_data_annotations(
            data_point_id=correction.data_point_id
        )
        
        # Get impact data if available
        impact = None
        if correction.status == 'implemented':
            from ..models.corrections import CorrectionImpact
            impact_record = CorrectionImpact.query.filter_by(
                correction_id=correction_id
            ).first()
            if impact_record:
                impact = impact_record.to_dict()
        
        return jsonify({
            'success': True,
            'correction': correction.to_dict(),
            'annotations': annotations,
            'impact': impact
        })
        
    except Exception as e:
        logger.error(f"Error getting correction details: {str(e)}")
        return jsonify({'error': str(e)}), 500

