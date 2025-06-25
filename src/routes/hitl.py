from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import logging
from datetime import datetime

from ..services.hitl_validation import hitl_service
from ..models.validation import ValidationStatus, ValidationPriority, ValidationQueue, ValidationRule
from ..models.elite_command import db

logger = logging.getLogger(__name__)

hitl_bp = Blueprint('hitl', __name__, url_prefix='/api/hitl')

@hitl_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for HITL validation system
    """
    try:
        # Check database connectivity
        pending_count = ValidationQueue.query.filter_by(status=ValidationStatus.PENDING).count()
        
        return jsonify({
            "status": "healthy",
            "service": "Human-in-the-Loop Validation",
            "timestamp": datetime.utcnow().isoformat(),
            "pending_validations": pending_count,
            "database_connected": True
        }), 200
        
    except Exception as e:
        logger.error(f"HITL health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "Human-in-the-Loop Validation",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@hitl_bp.route('/queue', methods=['GET'])
@cross_origin()
def get_validation_queue():
    """
    Get validation queue items with optional filters
    """
    try:
        # Parse query parameters
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to', type=int)
        limit = request.args.get('limit', default=50, type=int)
        
        # Convert string parameters to enums
        status_enum = None
        if status:
            try:
                status_enum = ValidationStatus(status)
            except ValueError:
                return jsonify({"error": f"Invalid status: {status}"}), 400
        
        priority_enum = None
        if priority:
            try:
                priority_enum = ValidationPriority(priority)
            except ValueError:
                return jsonify({"error": f"Invalid priority: {priority}"}), 400
        
        # Get queue items
        items = hitl_service.get_validation_queue(
            status=status_enum,
            priority=priority_enum,
            assigned_to=assigned_to,
            limit=limit
        )
        
        return jsonify({
            "validation_queue": [item.to_dict() for item in items],
            "total_items": len(items),
            "filters_applied": {
                "status": status,
                "priority": priority,
                "assigned_to": assigned_to,
                "limit": limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting validation queue: {str(e)}")
        return jsonify({"error": "Failed to retrieve validation queue"}), 500

@hitl_bp.route('/queue/<int:validation_id>', methods=['GET'])
@cross_origin()
def get_validation_item(validation_id):
    """
    Get specific validation item details
    """
    try:
        validation_item = ValidationQueue.query.get(validation_id)
        if not validation_item:
            return jsonify({"error": "Validation item not found"}), 404
        
        return jsonify({
            "validation_item": validation_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting validation item {validation_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve validation item"}), 500

@hitl_bp.route('/queue/<int:validation_id>/assign', methods=['POST'])
@cross_origin()
def assign_validation(validation_id):
    """
    Assign validation item to a user
    """
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({"error": "user_id is required"}), 400
        
        user_id = data['user_id']
        
        success = hitl_service.assign_validation(validation_id, user_id)
        if not success:
            return jsonify({"error": "Failed to assign validation or item not found"}), 400
        
        return jsonify({
            "message": "Validation assigned successfully",
            "validation_id": validation_id,
            "assigned_to": user_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error assigning validation {validation_id}: {str(e)}")
        return jsonify({"error": "Failed to assign validation"}), 500

@hitl_bp.route('/queue/<int:validation_id>/review', methods=['POST'])
@cross_origin()
def submit_validation_review(validation_id):
    """
    Submit validation review decision
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        required_fields = ['reviewer_id', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        reviewer_id = data['reviewer_id']
        status_str = data['status']
        feedback = data.get('feedback')
        corrected_data = data.get('corrected_data')
        correction_reason = data.get('correction_reason')
        
        # Convert status string to enum
        try:
            status = ValidationStatus(status_str)
        except ValueError:
            return jsonify({"error": f"Invalid status: {status_str}"}), 400
        
        # Submit validation decision
        success = hitl_service.submit_validation_decision(
            validation_id=validation_id,
            reviewer_id=reviewer_id,
            status=status,
            feedback=feedback,
            corrected_data=corrected_data,
            correction_reason=correction_reason
        )
        
        if not success:
            return jsonify({"error": "Failed to submit validation decision"}), 400
        
        return jsonify({
            "message": "Validation review submitted successfully",
            "validation_id": validation_id,
            "status": status_str,
            "reviewed_by": reviewer_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting validation review {validation_id}: {str(e)}")
        return jsonify({"error": "Failed to submit validation review"}), 500

@hitl_bp.route('/queue/bulk-assign', methods=['POST'])
@cross_origin()
def bulk_assign_validations():
    """
    Assign multiple validation items to users
    """
    try:
        data = request.get_json()
        if not data or 'assignments' not in data:
            return jsonify({"error": "assignments list is required"}), 400
        
        assignments = data['assignments']
        results = []
        
        for assignment in assignments:
            if 'validation_id' not in assignment or 'user_id' not in assignment:
                results.append({
                    "validation_id": assignment.get('validation_id'),
                    "success": False,
                    "error": "validation_id and user_id are required"
                })
                continue
            
            success = hitl_service.assign_validation(
                assignment['validation_id'],
                assignment['user_id']
            )
            
            results.append({
                "validation_id": assignment['validation_id'],
                "user_id": assignment['user_id'],
                "success": success,
                "error": None if success else "Assignment failed"
            })
        
        successful_assignments = sum(1 for r in results if r['success'])
        
        return jsonify({
            "message": f"Bulk assignment completed: {successful_assignments}/{len(assignments)} successful",
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk assign validations: {str(e)}")
        return jsonify({"error": "Failed to process bulk assignments"}), 500

@hitl_bp.route('/metrics', methods=['GET'])
@cross_origin()
def get_validation_metrics():
    """
    Get validation system performance metrics
    """
    try:
        days = request.args.get('days', default=30, type=int)
        
        metrics = hitl_service.get_validation_metrics(days=days)
        
        return jsonify({
            "validation_metrics": metrics,
            "generated_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting validation metrics: {str(e)}")
        return jsonify({"error": "Failed to retrieve validation metrics"}), 500

@hitl_bp.route('/rules', methods=['GET'])
@cross_origin()
def get_validation_rules():
    """
    Get validation rules
    """
    try:
        data_type = request.args.get('data_type')
        active_only = request.args.get('active_only', default='true').lower() == 'true'
        
        query = ValidationRule.query
        
        if data_type:
            query = query.filter_by(data_type=data_type)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        rules = query.all()
        
        return jsonify({
            "validation_rules": [rule.to_dict() for rule in rules],
            "total_rules": len(rules),
            "filters_applied": {
                "data_type": data_type,
                "active_only": active_only
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting validation rules: {str(e)}")
        return jsonify({"error": "Failed to retrieve validation rules"}), 500

@hitl_bp.route('/rules', methods=['POST'])
@cross_origin()
def create_validation_rule():
    """
    Create new validation rule
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        required_fields = ['name', 'data_type', 'confidence_threshold', 'conditions', 'priority_mapping', 'created_by']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Create validation rule
        rule = hitl_service.create_validation_rule(
            name=data['name'],
            description=data.get('description', ''),
            data_type=data['data_type'],
            confidence_threshold=data['confidence_threshold'],
            conditions=data['conditions'],
            priority_mapping=data['priority_mapping'],
            created_by=data['created_by']
        )
        
        return jsonify({
            "message": "Validation rule created successfully",
            "validation_rule": rule.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating validation rule: {str(e)}")
        return jsonify({"error": "Failed to create validation rule"}), 500

@hitl_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@cross_origin()
def update_validation_rule(rule_id):
    """
    Update validation rule
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        rule = ValidationRule.query.get(rule_id)
        if not rule:
            return jsonify({"error": "Validation rule not found"}), 404
        
        # Update rule fields
        if 'name' in data:
            rule.name = data['name']
        if 'description' in data:
            rule.description = data['description']
        if 'confidence_threshold' in data:
            rule.confidence_threshold = data['confidence_threshold']
        if 'conditions' in data:
            rule.conditions = json.dumps(data['conditions'])
        if 'priority_mapping' in data:
            rule.priority_mapping = json.dumps(data['priority_mapping'])
        if 'is_active' in data:
            rule.is_active = data['is_active']
        
        rule.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "Validation rule updated successfully",
            "validation_rule": rule.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating validation rule {rule_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to update validation rule"}), 500

@hitl_bp.route('/dashboard', methods=['GET'])
@cross_origin()
def get_validation_dashboard():
    """
    Get validation dashboard data for executives
    """
    try:
        # Get current queue status
        pending_items = ValidationQueue.query.filter_by(status=ValidationStatus.PENDING).count()
        high_priority_items = ValidationQueue.query.filter(
            ValidationQueue.status == ValidationStatus.PENDING,
            ValidationQueue.priority.in_([ValidationPriority.CRITICAL, ValidationPriority.HIGH])
        ).count()
        
        # Get recent metrics
        metrics = hitl_service.get_validation_metrics(days=7)
        
        # Get queue breakdown by priority
        priority_breakdown = {}
        for priority in ValidationPriority:
            count = ValidationQueue.query.filter(
                ValidationQueue.status == ValidationStatus.PENDING,
                ValidationQueue.priority == priority
            ).count()
            priority_breakdown[priority.value] = count
        
        # Get queue breakdown by data type
        data_type_breakdown = {}
        data_types = db.session.query(ValidationQueue.data_type).distinct().all()
        for (data_type,) in data_types:
            count = ValidationQueue.query.filter(
                ValidationQueue.status == ValidationStatus.PENDING,
                ValidationQueue.data_type == data_type
            ).count()
            data_type_breakdown[data_type] = count
        
        return jsonify({
            "dashboard": {
                "pending_items": pending_items,
                "high_priority_items": high_priority_items,
                "priority_breakdown": priority_breakdown,
                "data_type_breakdown": data_type_breakdown,
                "recent_metrics": metrics,
                "alerts": {
                    "critical_items": priority_breakdown.get('critical', 0),
                    "overdue_items": 0,  # Could be calculated based on creation time
                    "system_health": "healthy" if pending_items < 100 else "attention_needed"
                }
            },
            "generated_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting validation dashboard: {str(e)}")
        return jsonify({"error": "Failed to retrieve validation dashboard"}), 500

@hitl_bp.route('/queue/submit', methods=['POST'])
@cross_origin()
def submit_for_validation():
    """
    Submit data for validation (used by other services)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        required_fields = ['data_type', 'source_data_id', 'original_data', 'normalized_data', 'confidence_score']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Check if validation is needed
        should_validate, priority = hitl_service.should_validate(
            data['data_type'],
            data['confidence_score'],
            data.get('additional_context')
        )
        
        if not should_validate:
            return jsonify({
                "message": "Data meets confidence threshold, validation not required",
                "confidence_score": data['confidence_score'],
                "validation_required": False
            }), 200
        
        # Queue for validation
        validation_item = hitl_service.queue_for_validation(
            data_type=data['data_type'],
            source_data_id=data['source_data_id'],
            original_data=data['original_data'],
            normalized_data=data['normalized_data'],
            confidence_score=data['confidence_score'],
            confidence_breakdown=data.get('confidence_breakdown'),
            company_id=data.get('company_id'),
            suggested_corrections=data.get('suggested_corrections')
        )
        
        return jsonify({
            "message": "Data queued for validation",
            "validation_id": validation_item.id,
            "priority": validation_item.priority.value,
            "validation_required": True
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting data for validation: {str(e)}")
        return jsonify({"error": "Failed to submit data for validation"}), 500

