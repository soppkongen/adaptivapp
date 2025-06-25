from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json

db = SQLAlchemy()

class BusinessModelType(Enum):
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    MARKETPLACE = "marketplace"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    SERVICES = "services"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    MEDIA = "media"
    GENERIC = "generic"

class MetricCategory(Enum):
    REVENUE = "revenue"
    GROWTH = "growth"
    CUSTOMER = "customer"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    PRODUCT = "product"
    MARKETING = "marketing"
    SALES = "sales"
    TEAM = "team"

class BusinessModelTemplate(db.Model):
    """
    Business model templates for specialized normalization
    """
    __tablename__ = 'business_model_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template identification
    name = db.Column(db.String(100), nullable=False, unique=True)
    business_model_type = db.Column(db.Enum(BusinessModelType), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Template configuration
    expected_metrics = db.Column(db.Text, nullable=False)  # JSON list of expected metrics
    metric_mappings = db.Column(db.Text, nullable=False)  # JSON mapping of common variations
    normalization_rules = db.Column(db.Text, nullable=False)  # JSON normalization rules
    validation_rules = db.Column(db.Text, nullable=False)  # JSON validation rules
    
    # Template metadata
    confidence_weights = db.Column(db.Text, nullable=True)  # JSON confidence scoring weights
    priority_metrics = db.Column(db.Text, nullable=True)  # JSON list of priority metrics
    
    # Template status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    version = db.Column(db.String(20), nullable=False, default="1.0")
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='business_templates')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'business_model_type': self.business_model_type.value,
            'description': self.description,
            'expected_metrics': json.loads(self.expected_metrics) if self.expected_metrics else [],
            'metric_mappings': json.loads(self.metric_mappings) if self.metric_mappings else {},
            'normalization_rules': json.loads(self.normalization_rules) if self.normalization_rules else {},
            'validation_rules': json.loads(self.validation_rules) if self.validation_rules else {},
            'confidence_weights': json.loads(self.confidence_weights) if self.confidence_weights else {},
            'priority_metrics': json.loads(self.priority_metrics) if self.priority_metrics else [],
            'is_active': self.is_active,
            'version': self.version,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MetricDefinition(db.Model):
    """
    Standardized metric definitions for business model templates
    """
    __tablename__ = 'metric_definitions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Metric identification
    metric_name = db.Column(db.String(100), nullable=False)
    metric_code = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.Enum(MetricCategory), nullable=False)
    
    # Metric definition
    description = db.Column(db.Text, nullable=False)
    calculation_method = db.Column(db.Text, nullable=False)
    unit_of_measurement = db.Column(db.String(50), nullable=True)
    data_type = db.Column(db.String(20), nullable=False)  # 'currency', 'percentage', 'count', 'ratio'
    
    # Business model associations
    applicable_models = db.Column(db.Text, nullable=False)  # JSON list of business model types
    
    # Normalization configuration
    common_variations = db.Column(db.Text, nullable=True)  # JSON list of common name variations
    conversion_rules = db.Column(db.Text, nullable=True)  # JSON conversion rules
    validation_constraints = db.Column(db.Text, nullable=True)  # JSON validation constraints
    
    # Metadata
    is_core_metric = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_code': self.metric_code,
            'category': self.category.value,
            'description': self.description,
            'calculation_method': self.calculation_method,
            'unit_of_measurement': self.unit_of_measurement,
            'data_type': self.data_type,
            'applicable_models': json.loads(self.applicable_models) if self.applicable_models else [],
            'common_variations': json.loads(self.common_variations) if self.common_variations else [],
            'conversion_rules': json.loads(self.conversion_rules) if self.conversion_rules else {},
            'validation_constraints': json.loads(self.validation_constraints) if self.validation_constraints else {},
            'is_core_metric': self.is_core_metric,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CompanyTemplate(db.Model):
    """
    Association between companies and business model templates
    """
    __tablename__ = 'company_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Associations
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('business_model_templates.id'), nullable=False)
    
    # Template customization
    custom_mappings = db.Column(db.Text, nullable=True)  # JSON custom metric mappings
    custom_rules = db.Column(db.Text, nullable=True)  # JSON custom normalization rules
    
    # Assignment metadata
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    confidence_score = db.Column(db.Float, nullable=True)  # Confidence in template assignment
    
    # Status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relationships
    company = db.relationship('Company', backref='template_assignments')
    template = db.relationship('BusinessModelTemplate', backref='company_assignments')
    assigner = db.relationship('User', backref='template_assignments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'template_id': self.template_id,
            'custom_mappings': json.loads(self.custom_mappings) if self.custom_mappings else {},
            'custom_rules': json.loads(self.custom_rules) if self.custom_rules else {},
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at.isoformat(),
            'confidence_score': self.confidence_score,
            'is_active': self.is_active
        }

class NormalizationResult(db.Model):
    """
    Results of template-based normalization
    """
    __tablename__ = 'normalization_results'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Source data
    raw_data_id = db.Column(db.Integer, db.ForeignKey('raw_data_entry.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('business_model_templates.id'), nullable=False)
    
    # Normalization details
    original_metric_name = db.Column(db.String(200), nullable=False)
    normalized_metric_code = db.Column(db.String(50), nullable=False)
    original_value = db.Column(db.Text, nullable=False)
    normalized_value = db.Column(db.Text, nullable=False)
    
    # Normalization metadata
    normalization_method = db.Column(db.String(100), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    confidence_breakdown = db.Column(db.Text, nullable=True)  # JSON detailed confidence
    
    # Validation status
    validation_status = db.Column(db.String(50), nullable=False, default='pending')
    validation_notes = db.Column(db.Text, nullable=True)
    
    # Processing metadata
    processed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processing_time_ms = db.Column(db.Integer, nullable=True)
    
    # Relationships
    raw_data = db.relationship('RawDataEntry', backref='normalization_results')
    company = db.relationship('Company', backref='normalization_results')
    template = db.relationship('BusinessModelTemplate', backref='normalization_results')
    
    def to_dict(self):
        return {
            'id': self.id,
            'raw_data_id': self.raw_data_id,
            'company_id': self.company_id,
            'template_id': self.template_id,
            'original_metric_name': self.original_metric_name,
            'normalized_metric_code': self.normalized_metric_code,
            'original_value': self.original_value,
            'normalized_value': self.normalized_value,
            'normalization_method': self.normalization_method,
            'confidence_score': self.confidence_score,
            'confidence_breakdown': json.loads(self.confidence_breakdown) if self.confidence_breakdown else {},
            'validation_status': self.validation_status,
            'validation_notes': self.validation_notes,
            'processed_at': self.processed_at.isoformat(),
            'processing_time_ms': self.processing_time_ms
        }

class TemplatePerformance(db.Model):
    """
    Performance metrics for business model templates
    """
    __tablename__ = 'template_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template reference
    template_id = db.Column(db.Integer, db.ForeignKey('business_model_templates.id'), nullable=False)
    
    # Time period
    date = db.Column(db.Date, nullable=False)
    
    # Performance metrics
    total_normalizations = db.Column(db.Integer, nullable=False, default=0)
    successful_normalizations = db.Column(db.Integer, nullable=False, default=0)
    failed_normalizations = db.Column(db.Integer, nullable=False, default=0)
    average_confidence_score = db.Column(db.Float, nullable=True)
    average_processing_time_ms = db.Column(db.Float, nullable=True)
    
    # Accuracy metrics
    validation_accuracy = db.Column(db.Float, nullable=True)
    false_positive_rate = db.Column(db.Float, nullable=True)
    false_negative_rate = db.Column(db.Float, nullable=True)
    
    # Usage metrics
    active_companies = db.Column(db.Integer, nullable=False, default=0)
    total_data_points = db.Column(db.Integer, nullable=False, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    template = db.relationship('BusinessModelTemplate', backref='performance_metrics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'date': self.date.isoformat(),
            'total_normalizations': self.total_normalizations,
            'successful_normalizations': self.successful_normalizations,
            'failed_normalizations': self.failed_normalizations,
            'success_rate': (self.successful_normalizations / self.total_normalizations * 100) if self.total_normalizations > 0 else 0,
            'average_confidence_score': self.average_confidence_score,
            'average_processing_time_ms': self.average_processing_time_ms,
            'validation_accuracy': self.validation_accuracy,
            'false_positive_rate': self.false_positive_rate,
            'false_negative_rate': self.false_negative_rate,
            'active_companies': self.active_companies,
            'total_data_points': self.total_data_points,
            'created_at': self.created_at.isoformat()
        }

