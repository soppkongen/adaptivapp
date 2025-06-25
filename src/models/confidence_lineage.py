from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json
import uuid

db = SQLAlchemy()

class ConfidenceFactorType(Enum):
    DATA_QUALITY = "data_quality"
    SOURCE_RELIABILITY = "source_reliability"
    TRANSFORMATION_ACCURACY = "transformation_accuracy"
    VALIDATION_CONSENSUS = "validation_consensus"
    TEMPLATE_SPECIFICITY = "template_specificity"
    HISTORICAL_PERFORMANCE = "historical_performance"
    HUMAN_VERIFICATION = "human_verification"
    CROSS_VALIDATION = "cross_validation"

class LineageEventType(Enum):
    DATA_INGESTION = "data_ingestion"
    NORMALIZATION = "normalization"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"
    EXPORT = "export"
    CORRECTION = "correction"

class DataLineage(db.Model):
    """
    Complete data lineage tracking from source to final output
    """
    __tablename__ = 'data_lineage'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Lineage identification
    lineage_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    parent_lineage_id = db.Column(db.String(36), db.ForeignKey('data_lineage.lineage_id'), nullable=True)
    
    # Event details
    event_type = db.Column(db.Enum(LineageEventType), nullable=False)
    event_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Data references
    source_data_id = db.Column(db.String(100), nullable=True)  # Reference to source data
    source_data_type = db.Column(db.String(50), nullable=True)  # Type of source data
    output_data_id = db.Column(db.String(100), nullable=True)  # Reference to output data
    output_data_type = db.Column(db.String(50), nullable=True)  # Type of output data
    
    # Transformation details
    transformation_method = db.Column(db.String(100), nullable=False)
    transformation_parameters = db.Column(db.Text, nullable=True)  # JSON parameters
    
    # Quality metrics
    input_data_quality_score = db.Column(db.Float, nullable=True)
    output_data_quality_score = db.Column(db.Float, nullable=True)
    transformation_confidence = db.Column(db.Float, nullable=False)
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    system_component = db.Column(db.String(100), nullable=False)
    
    # Metadata
    processing_time_ms = db.Column(db.Integer, nullable=True)
    error_details = db.Column(db.Text, nullable=True)  # JSON error information
    
    # Relationships
    parent_lineage = db.relationship('DataLineage', remote_side=[lineage_id], backref='child_lineages')
    company = db.relationship('Company', backref='data_lineages')
    user = db.relationship('User', backref='data_lineages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'lineage_id': self.lineage_id,
            'parent_lineage_id': self.parent_lineage_id,
            'event_type': self.event_type.value,
            'event_timestamp': self.event_timestamp.isoformat(),
            'source_data_id': self.source_data_id,
            'source_data_type': self.source_data_type,
            'output_data_id': self.output_data_id,
            'output_data_type': self.output_data_type,
            'transformation_method': self.transformation_method,
            'transformation_parameters': json.loads(self.transformation_parameters) if self.transformation_parameters else {},
            'input_data_quality_score': self.input_data_quality_score,
            'output_data_quality_score': self.output_data_quality_score,
            'transformation_confidence': self.transformation_confidence,
            'company_id': self.company_id,
            'user_id': self.user_id,
            'system_component': self.system_component,
            'processing_time_ms': self.processing_time_ms,
            'error_details': json.loads(self.error_details) if self.error_details else None
        }

class ConfidenceScore(db.Model):
    """
    Granular confidence scoring for data points
    """
    __tablename__ = 'confidence_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Score identification
    score_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    lineage_id = db.Column(db.String(36), db.ForeignKey('data_lineage.lineage_id'), nullable=False)
    
    # Data reference
    data_point_id = db.Column(db.String(100), nullable=False)  # Reference to specific data point
    data_point_type = db.Column(db.String(50), nullable=False)  # Type of data point
    metric_name = db.Column(db.String(200), nullable=True)  # Name of metric if applicable
    
    # Overall confidence
    overall_confidence = db.Column(db.Float, nullable=False)
    confidence_level = db.Column(db.String(20), nullable=False)  # 'high', 'medium', 'low', 'critical'
    
    # Confidence factors breakdown
    confidence_factors = db.Column(db.Text, nullable=False)  # JSON breakdown of confidence factors
    
    # Calculation metadata
    calculation_method = db.Column(db.String(100), nullable=False)
    calculation_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    calculation_version = db.Column(db.String(20), nullable=False, default="1.0")
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Relationships
    lineage = db.relationship('DataLineage', backref='confidence_scores')
    company = db.relationship('Company', backref='confidence_scores')
    
    def to_dict(self):
        return {
            'id': self.id,
            'score_id': self.score_id,
            'lineage_id': self.lineage_id,
            'data_point_id': self.data_point_id,
            'data_point_type': self.data_point_type,
            'metric_name': self.metric_name,
            'overall_confidence': self.overall_confidence,
            'confidence_level': self.confidence_level,
            'confidence_factors': json.loads(self.confidence_factors) if self.confidence_factors else {},
            'calculation_method': self.calculation_method,
            'calculation_timestamp': self.calculation_timestamp.isoformat(),
            'calculation_version': self.calculation_version,
            'company_id': self.company_id
        }

class ConfidenceFactor(db.Model):
    """
    Individual confidence factors that contribute to overall confidence
    """
    __tablename__ = 'confidence_factors'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Factor identification
    confidence_score_id = db.Column(db.String(36), db.ForeignKey('confidence_scores.score_id'), nullable=False)
    factor_type = db.Column(db.Enum(ConfidenceFactorType), nullable=False)
    
    # Factor details
    factor_name = db.Column(db.String(100), nullable=False)
    factor_description = db.Column(db.Text, nullable=True)
    
    # Factor scoring
    factor_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    factor_weight = db.Column(db.Float, nullable=False)  # Weight in overall calculation
    weighted_contribution = db.Column(db.Float, nullable=False)  # factor_score * factor_weight
    
    # Factor evidence
    evidence_data = db.Column(db.Text, nullable=True)  # JSON evidence supporting the score
    calculation_details = db.Column(db.Text, nullable=True)  # JSON calculation details
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    confidence_score = db.relationship('ConfidenceScore', backref='factors')
    
    def to_dict(self):
        return {
            'id': self.id,
            'confidence_score_id': self.confidence_score_id,
            'factor_type': self.factor_type.value,
            'factor_name': self.factor_name,
            'factor_description': self.factor_description,
            'factor_score': self.factor_score,
            'factor_weight': self.factor_weight,
            'weighted_contribution': self.weighted_contribution,
            'evidence_data': json.loads(self.evidence_data) if self.evidence_data else {},
            'calculation_details': json.loads(self.calculation_details) if self.calculation_details else {},
            'created_at': self.created_at.isoformat()
        }

class LineageGraph(db.Model):
    """
    Materialized view of data lineage graphs for efficient querying
    """
    __tablename__ = 'lineage_graphs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Graph identification
    graph_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    root_lineage_id = db.Column(db.String(36), db.ForeignKey('data_lineage.lineage_id'), nullable=False)
    
    # Graph metadata
    graph_type = db.Column(db.String(50), nullable=False)  # 'forward', 'backward', 'full'
    depth_levels = db.Column(db.Integer, nullable=False)
    total_nodes = db.Column(db.Integer, nullable=False)
    total_edges = db.Column(db.Integer, nullable=False)
    
    # Graph data
    graph_structure = db.Column(db.Text, nullable=False)  # JSON graph structure
    confidence_summary = db.Column(db.Text, nullable=False)  # JSON confidence summary
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Cache metadata
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    cache_version = db.Column(db.String(20), nullable=False, default="1.0")
    
    # Relationships
    root_lineage = db.relationship('DataLineage', backref='lineage_graphs')
    company = db.relationship('Company', backref='lineage_graphs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'graph_id': self.graph_id,
            'root_lineage_id': self.root_lineage_id,
            'graph_type': self.graph_type,
            'depth_levels': self.depth_levels,
            'total_nodes': self.total_nodes,
            'total_edges': self.total_edges,
            'graph_structure': json.loads(self.graph_structure) if self.graph_structure else {},
            'confidence_summary': json.loads(self.confidence_summary) if self.confidence_summary else {},
            'company_id': self.company_id,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'cache_version': self.cache_version
        }

class ConfidenceThreshold(db.Model):
    """
    Configurable confidence thresholds for different data types and use cases
    """
    __tablename__ = 'confidence_thresholds'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Threshold identification
    threshold_name = db.Column(db.String(100), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)
    use_case = db.Column(db.String(100), nullable=False)
    
    # Threshold values
    critical_threshold = db.Column(db.Float, nullable=False)  # Below this requires immediate attention
    low_threshold = db.Column(db.Float, nullable=False)      # Below this requires validation
    medium_threshold = db.Column(db.Float, nullable=False)   # Below this requires monitoring
    high_threshold = db.Column(db.Float, nullable=False)     # Above this is trusted
    
    # Actions
    critical_action = db.Column(db.String(100), nullable=False)  # Action for critical confidence
    low_action = db.Column(db.String(100), nullable=False)       # Action for low confidence
    medium_action = db.Column(db.String(100), nullable=False)    # Action for medium confidence
    high_action = db.Column(db.String(100), nullable=False)      # Action for high confidence
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    business_model_type = db.Column(db.String(50), nullable=True)
    
    # Metadata
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='confidence_thresholds')
    creator = db.relationship('User', backref='confidence_thresholds')
    
    def to_dict(self):
        return {
            'id': self.id,
            'threshold_name': self.threshold_name,
            'data_type': self.data_type,
            'use_case': self.use_case,
            'critical_threshold': self.critical_threshold,
            'low_threshold': self.low_threshold,
            'medium_threshold': self.medium_threshold,
            'high_threshold': self.high_threshold,
            'critical_action': self.critical_action,
            'low_action': self.low_action,
            'medium_action': self.medium_action,
            'high_action': self.high_action,
            'company_id': self.company_id,
            'business_model_type': self.business_model_type,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ConfidenceAlert(db.Model):
    """
    Alerts generated based on confidence thresholds
    """
    __tablename__ = 'confidence_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Alert identification
    alert_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    confidence_score_id = db.Column(db.String(36), db.ForeignKey('confidence_scores.score_id'), nullable=False)
    threshold_id = db.Column(db.Integer, db.ForeignKey('confidence_thresholds.id'), nullable=False)
    
    # Alert details
    alert_level = db.Column(db.String(20), nullable=False)  # 'critical', 'low', 'medium', 'high'
    alert_message = db.Column(db.Text, nullable=False)
    recommended_action = db.Column(db.String(200), nullable=False)
    
    # Alert status
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'acknowledged', 'resolved'
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    confidence_score = db.relationship('ConfidenceScore', backref='alerts')
    threshold = db.relationship('ConfidenceThreshold', backref='alerts')
    acknowledger = db.relationship('User', foreign_keys=[acknowledged_by], backref='acknowledged_alerts')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_alerts')
    company = db.relationship('Company', backref='confidence_alerts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'confidence_score_id': self.confidence_score_id,
            'threshold_id': self.threshold_id,
            'alert_level': self.alert_level,
            'alert_message': self.alert_message,
            'recommended_action': self.recommended_action,
            'status': self.status,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'company_id': self.company_id,
            'created_at': self.created_at.isoformat()
        }

