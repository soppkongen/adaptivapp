from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import logging
import json
from datetime import datetime, timedelta

from ..services.template_normalization import template_normalization_engine
from ..models.business_templates import (
    BusinessModelTemplate, MetricDefinition, CompanyTemplate, 
    NormalizationResult, TemplatePerformance, BusinessModelType, 
    MetricCategory, db
)
from ..models.elite_command import Company, RawDataEntry

logger = logging.getLogger(__name__)

templates_bp = Blueprint('templates', __name__, url_prefix='/api/templates')

@templates_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for business model templates system
    """
    try:
        # Check database connectivity
        template_count = BusinessModelTemplate.query.filter_by(is_active=True).count()
        
        return jsonify({
            "status": "healthy",
            "service": "Business Model Templates",
            "timestamp": datetime.utcnow().isoformat(),
            "active_templates": template_count,
            "database_connected": True
        }), 200
        
    except Exception as e:
        logger.error(f"Templates health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "Business Model Templates",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@templates_bp.route('/business-models', methods=['GET'])
@cross_origin()
def get_business_model_templates():
    """
    Get business model templates with optional filters
    """
    try:
        business_type = request.args.get('business_type')
        active_only = request.args.get('active_only', default='true').lower() == 'true'
        
        query = BusinessModelTemplate.query
        
        if business_type:
            try:
                business_type_enum = BusinessModelType(business_type)
                query = query.filter_by(business_model_type=business_type_enum)
            except ValueError:
                return jsonify({"error": f"Invalid business type: {business_type}"}), 400
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        templates = query.all()
        
        return jsonify({
            "business_model_templates": [template.to_dict() for template in templates],
            "total_templates": len(templates),
            "filters_applied": {
                "business_type": business_type,
                "active_only": active_only
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting business model templates: {str(e)}")
        return jsonify({"error": "Failed to retrieve business model templates"}), 500

@templates_bp.route('/business-models', methods=['POST'])
@cross_origin()
def create_business_model_template():
    """
    Create new business model template
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        required_fields = ['name', 'business_model_type', 'expected_metrics', 'metric_mappings', 'normalization_rules', 'validation_rules', 'created_by']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate business model type
        try:
            business_type = BusinessModelType(data['business_model_type'])
        except ValueError:
            return jsonify({"error": f"Invalid business model type: {data['business_model_type']}"}), 400
        
        # Create template
        template = BusinessModelTemplate(
            name=data['name'],
            business_model_type=business_type,
            description=data.get('description', ''),
            expected_metrics=json.dumps(data['expected_metrics']),
            metric_mappings=json.dumps(data['metric_mappings']),
            normalization_rules=json.dumps(data['normalization_rules']),
            validation_rules=json.dumps(data['validation_rules']),
            confidence_weights=json.dumps(data.get('confidence_weights', {})),
            priority_metrics=json.dumps(data.get('priority_metrics', [])),
            version=data.get('version', '1.0'),
            created_by=data['created_by']
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            "message": "Business model template created successfully",
            "template": template.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating business model template: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to create business model template"}), 500

@templates_bp.route('/business-models/<int:template_id>', methods=['GET'])
@cross_origin()
def get_business_model_template(template_id):
    """
    Get specific business model template details
    """
    try:
        template = BusinessModelTemplate.query.get(template_id)
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Get template performance metrics
        performance_metrics = TemplatePerformance.query.filter_by(
            template_id=template_id
        ).order_by(TemplatePerformance.date.desc()).limit(30).all()
        
        # Get companies using this template
        company_assignments = CompanyTemplate.query.filter_by(
            template_id=template_id,
            is_active=True
        ).all()
        
        return jsonify({
            "template": template.to_dict(),
            "performance_metrics": [metric.to_dict() for metric in performance_metrics],
            "company_assignments": [assignment.to_dict() for assignment in company_assignments],
            "usage_stats": {
                "active_companies": len(company_assignments),
                "total_normalizations": sum(m.total_normalizations for m in performance_metrics),
                "average_confidence": sum(m.average_confidence_score or 0 for m in performance_metrics) / len(performance_metrics) if performance_metrics else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting business model template {template_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve business model template"}), 500

@templates_bp.route('/business-models/<int:template_id>', methods=['PUT'])
@cross_origin()
def update_business_model_template(template_id):
    """
    Update business model template
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        template = BusinessModelTemplate.query.get(template_id)
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Update template fields
        if 'name' in data:
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if 'expected_metrics' in data:
            template.expected_metrics = json.dumps(data['expected_metrics'])
        if 'metric_mappings' in data:
            template.metric_mappings = json.dumps(data['metric_mappings'])
        if 'normalization_rules' in data:
            template.normalization_rules = json.dumps(data['normalization_rules'])
        if 'validation_rules' in data:
            template.validation_rules = json.dumps(data['validation_rules'])
        if 'confidence_weights' in data:
            template.confidence_weights = json.dumps(data['confidence_weights'])
        if 'priority_metrics' in data:
            template.priority_metrics = json.dumps(data['priority_metrics'])
        if 'is_active' in data:
            template.is_active = data['is_active']
        if 'version' in data:
            template.version = data['version']
        
        template.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "Business model template updated successfully",
            "template": template.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating business model template {template_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to update business model template"}), 500

@templates_bp.route('/metrics', methods=['GET'])
@cross_origin()
def get_metric_definitions():
    """
    Get metric definitions with optional filters
    """
    try:
        category = request.args.get('category')
        business_type = request.args.get('business_type')
        core_only = request.args.get('core_only', default='false').lower() == 'true'
        
        query = MetricDefinition.query
        
        if category:
            try:
                category_enum = MetricCategory(category)
                query = query.filter_by(category=category_enum)
            except ValueError:
                return jsonify({"error": f"Invalid category: {category}"}), 400
        
        if core_only:
            query = query.filter_by(is_core_metric=True)
        
        metrics = query.all()
        
        # Filter by business type if specified
        if business_type:
            filtered_metrics = []
            for metric in metrics:
                applicable_models = json.loads(metric.applicable_models) if metric.applicable_models else []
                if business_type in applicable_models:
                    filtered_metrics.append(metric)
            metrics = filtered_metrics
        
        return jsonify({
            "metric_definitions": [metric.to_dict() for metric in metrics],
            "total_metrics": len(metrics),
            "filters_applied": {
                "category": category,
                "business_type": business_type,
                "core_only": core_only
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metric definitions: {str(e)}")
        return jsonify({"error": "Failed to retrieve metric definitions"}), 500

@templates_bp.route('/metrics', methods=['POST'])
@cross_origin()
def create_metric_definition():
    """
    Create new metric definition
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        required_fields = ['metric_name', 'metric_code', 'category', 'description', 'calculation_method', 'data_type', 'applicable_models']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate category
        try:
            category = MetricCategory(data['category'])
        except ValueError:
            return jsonify({"error": f"Invalid category: {data['category']}"}), 400
        
        # Create metric definition
        metric = MetricDefinition(
            metric_name=data['metric_name'],
            metric_code=data['metric_code'],
            category=category,
            description=data['description'],
            calculation_method=data['calculation_method'],
            unit_of_measurement=data.get('unit_of_measurement'),
            data_type=data['data_type'],
            applicable_models=json.dumps(data['applicable_models']),
            common_variations=json.dumps(data.get('common_variations', [])),
            conversion_rules=json.dumps(data.get('conversion_rules', {})),
            validation_constraints=json.dumps(data.get('validation_constraints', {})),
            is_core_metric=data.get('is_core_metric', False)
        )
        
        db.session.add(metric)
        db.session.commit()
        
        return jsonify({
            "message": "Metric definition created successfully",
            "metric": metric.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating metric definition: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to create metric definition"}), 500

@templates_bp.route('/companies/<int:company_id>/template', methods=['GET'])
@cross_origin()
def get_company_template(company_id):
    """
    Get business model template assigned to a company
    """
    try:
        company_template = CompanyTemplate.query.filter_by(
            company_id=company_id,
            is_active=True
        ).first()
        
        if not company_template:
            return jsonify({"error": "No template assigned to this company"}), 404
        
        return jsonify({
            "company_template": company_template.to_dict(),
            "template": company_template.template.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting company template for {company_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve company template"}), 500

@templates_bp.route('/companies/<int:company_id>/template', methods=['POST'])
@cross_origin()
def assign_company_template(company_id):
    """
    Assign business model template to a company
    """
    try:
        data = request.get_json()
        if not data or 'template_id' not in data:
            return jsonify({"error": "template_id is required"}), 400
        
        template_id = data['template_id']
        assigned_by = data.get('assigned_by', 1)
        confidence_score = data.get('confidence_score', 1.0)
        
        # Check if template exists
        template = BusinessModelTemplate.query.get(template_id)
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Check if company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({"error": "Company not found"}), 404
        
        # Deactivate existing template assignments
        existing_assignments = CompanyTemplate.query.filter_by(
            company_id=company_id,
            is_active=True
        ).all()
        
        for assignment in existing_assignments:
            assignment.is_active = False
        
        # Create new assignment
        company_template = CompanyTemplate(
            company_id=company_id,
            template_id=template_id,
            assigned_by=assigned_by,
            confidence_score=confidence_score,
            custom_mappings=json.dumps(data.get('custom_mappings', {})),
            custom_rules=json.dumps(data.get('custom_rules', {}))
        )
        
        db.session.add(company_template)
        db.session.commit()
        
        return jsonify({
            "message": "Template assigned to company successfully",
            "company_template": company_template.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error assigning template to company {company_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to assign template to company"}), 500

@templates_bp.route('/normalize', methods=['POST'])
@cross_origin()
def normalize_data():
    """
    Normalize data using template-based normalization engine
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        required_fields = ['raw_data_id', 'company_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        raw_data_id = data['raw_data_id']
        company_id = data['company_id']
        
        # Get raw data entry
        raw_data_entry = RawDataEntry.query.get(raw_data_id)
        if not raw_data_entry:
            return jsonify({"error": "Raw data entry not found"}), 404
        
        # Normalize data
        result = template_normalization_engine.normalize_data(raw_data_entry, company_id)
        
        return jsonify({
            "message": "Data normalized successfully",
            "normalization_result": result
        }), 200
        
    except Exception as e:
        logger.error(f"Error normalizing data: {str(e)}")
        return jsonify({"error": "Failed to normalize data"}), 500

@templates_bp.route('/normalization-results', methods=['GET'])
@cross_origin()
def get_normalization_results():
    """
    Get normalization results with optional filters
    """
    try:
        company_id = request.args.get('company_id', type=int)
        template_id = request.args.get('template_id', type=int)
        validation_status = request.args.get('validation_status')
        limit = request.args.get('limit', default=50, type=int)
        
        query = NormalizationResult.query
        
        if company_id:
            query = query.filter_by(company_id=company_id)
        if template_id:
            query = query.filter_by(template_id=template_id)
        if validation_status:
            query = query.filter_by(validation_status=validation_status)
        
        results = query.order_by(NormalizationResult.processed_at.desc()).limit(limit).all()
        
        return jsonify({
            "normalization_results": [result.to_dict() for result in results],
            "total_results": len(results),
            "filters_applied": {
                "company_id": company_id,
                "template_id": template_id,
                "validation_status": validation_status,
                "limit": limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting normalization results: {str(e)}")
        return jsonify({"error": "Failed to retrieve normalization results"}), 500

@templates_bp.route('/performance', methods=['GET'])
@cross_origin()
def get_template_performance():
    """
    Get template performance metrics
    """
    try:
        template_id = request.args.get('template_id', type=int)
        days = request.args.get('days', default=30, type=int)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = TemplatePerformance.query.filter(
            TemplatePerformance.date >= start_date,
            TemplatePerformance.date <= end_date
        )
        
        if template_id:
            query = query.filter_by(template_id=template_id)
        
        performance_metrics = query.all()
        
        # Aggregate metrics by template
        template_stats = {}
        for metric in performance_metrics:
            template_id = metric.template_id
            if template_id not in template_stats:
                template_stats[template_id] = {
                    'template_id': template_id,
                    'template_name': metric.template.name,
                    'business_model_type': metric.template.business_model_type.value,
                    'total_normalizations': 0,
                    'successful_normalizations': 0,
                    'failed_normalizations': 0,
                    'average_confidence_score': 0,
                    'average_processing_time_ms': 0,
                    'daily_metrics': []
                }
            
            stats = template_stats[template_id]
            stats['total_normalizations'] += metric.total_normalizations
            stats['successful_normalizations'] += metric.successful_normalizations
            stats['failed_normalizations'] += metric.failed_normalizations
            stats['daily_metrics'].append(metric.to_dict())
        
        # Calculate averages
        for stats in template_stats.values():
            daily_metrics = stats['daily_metrics']
            if daily_metrics:
                stats['average_confidence_score'] = sum(
                    m['average_confidence_score'] or 0 for m in daily_metrics
                ) / len(daily_metrics)
                stats['average_processing_time_ms'] = sum(
                    m['average_processing_time_ms'] or 0 for m in daily_metrics
                ) / len(daily_metrics)
                stats['success_rate'] = (
                    stats['successful_normalizations'] / stats['total_normalizations'] * 100
                ) if stats['total_normalizations'] > 0 else 0
        
        return jsonify({
            "template_performance": list(template_stats.values()),
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting template performance: {str(e)}")
        return jsonify({"error": "Failed to retrieve template performance"}), 500

@templates_bp.route('/dashboard', methods=['GET'])
@cross_origin()
def get_templates_dashboard():
    """
    Get templates dashboard data for executives
    """
    try:
        # Get template overview
        total_templates = BusinessModelTemplate.query.filter_by(is_active=True).count()
        total_companies = CompanyTemplate.query.filter_by(is_active=True).count()
        
        # Get recent normalization activity
        recent_normalizations = NormalizationResult.query.filter(
            NormalizationResult.processed_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Get template usage breakdown
        template_usage = db.session.query(
            BusinessModelTemplate.name,
            BusinessModelTemplate.business_model_type,
            db.func.count(CompanyTemplate.id).label('company_count')
        ).join(CompanyTemplate).filter(
            CompanyTemplate.is_active == True
        ).group_by(BusinessModelTemplate.id).all()
        
        # Get performance summary
        recent_performance = TemplatePerformance.query.filter(
            TemplatePerformance.date >= datetime.utcnow().date() - timedelta(days=7)
        ).all()
        
        avg_confidence = sum(p.average_confidence_score or 0 for p in recent_performance) / len(recent_performance) if recent_performance else 0
        total_recent_normalizations = sum(p.total_normalizations for p in recent_performance)
        
        return jsonify({
            "dashboard": {
                "overview": {
                    "total_active_templates": total_templates,
                    "total_companies_with_templates": total_companies,
                    "recent_normalizations": recent_normalizations,
                    "average_confidence_score": round(avg_confidence, 3)
                },
                "template_usage": [
                    {
                        "template_name": usage.name,
                        "business_model_type": usage.business_model_type.value,
                        "company_count": usage.company_count
                    }
                    for usage in template_usage
                ],
                "performance_summary": {
                    "total_recent_normalizations": total_recent_normalizations,
                    "average_confidence": round(avg_confidence, 3),
                    "templates_with_low_confidence": len([
                        p for p in recent_performance 
                        if (p.average_confidence_score or 0) < 0.7
                    ])
                }
            },
            "generated_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting templates dashboard: {str(e)}")
        return jsonify({"error": "Failed to retrieve templates dashboard"}), 500

