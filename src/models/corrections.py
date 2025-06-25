from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json
import uuid

db = SQLAlchemy()

class CorrectionType(Enum):
    VALUE_CORRECTION = "value_correction"
    CLASSIFICATION_CORRECTION = "classification_correction"
    RELATIONSHIP_CORRECTION = "relationship_correction"
    METADATA_CORRECTION = "metadata_correction"
    DELETION = "deletion"
    ADDITION = "addition"

class CorrectionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    REVERTED = "reverted"

class AnnotationType(Enum):
    EXPLANATION = "explanation"
    CONTEXT = "context"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"
    BUSINESS_RULE = "business_rule"
    QUALITY_NOTE = "quality_note"

class DataCorrection(db.Model):
    """
    User-driven data corrections and modifications
    """
    __tablename__ = 'data_corrections'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Correction identification
    correction_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Data reference
    data_point_id = db.Column(db.String(100), nullable=False)
    data_point_type = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(100), nullable=True)  # Specific field being corrected
    
    # Correction details
    correction_type = db.Column(db.Enum(CorrectionType), nullable=False)
    original_value = db.Column(db.Text, nullable=True)  # JSON original value
    corrected_value = db.Column(db.Text, nullable=False)  # JSON corrected value
    correction_reason = db.Column(db.Text, nullable=False)
    
    # Correction metadata
    confidence_impact = db.Column(db.Float, nullable=True)  # Expected confidence improvement
    business_impact = db.Column(db.String(20), nullable=True)  # 'low', 'medium', 'high', 'critical'
    urgency = db.Column(db.String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'urgent'
    
    # Status and workflow
    status = db.Column(db.Enum(CorrectionStatus), nullable=False, default=CorrectionStatus.PENDING)
    requires_approval = db.Column(db.Boolean, nullable=False, default=True)
    
    # User information
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    implemented_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    implemented_at = db.Column(db.DateTime, nullable=True)
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    lineage_id = db.Column(db.String(36), db.ForeignKey('data_lineage.lineage_id'), nullable=True)
    
    # Implementation details
    implementation_notes = db.Column(db.Text, nullable=True)
    rollback_data = db.Column(db.Text, nullable=True)  # JSON data for rollback
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submitted_corrections')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_corrections')
    implementer = db.relationship('User', foreign_keys=[implemented_by], backref='implemented_corrections')
    company = db.relationship('Company', backref='data_corrections')
    lineage = db.relationship('DataLineage', backref='corrections')
    
    def to_dict(self):
        return {
            'id': self.id,
            'correction_id': self.correction_id,
            'data_point_id': self.data_point_id,
            'data_point_type': self.data_point_type,
            'field_name': self.field_name,
            'correction_type': self.correction_type.value,
            'original_value': json.loads(self.original_value) if self.original_value else None,
            'corrected_value': json.loads(self.corrected_value) if self.corrected_value else None,
            'correction_reason': self.correction_reason,
            'confidence_impact': self.confidence_impact,
            'business_impact': self.business_impact,
            'urgency': self.urgency,
            'status': self.status.value,
            'requires_approval': self.requires_approval,
            'submitted_by': self.submitted_by,
            'approved_by': self.approved_by,
            'implemented_by': self.implemented_by,
            'submitted_at': self.submitted_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'implemented_at': self.implemented_at.isoformat() if self.implemented_at else None,
            'company_id': self.company_id,
            'lineage_id': self.lineage_id,
            'implementation_notes': self.implementation_notes,
            'rollback_data': json.loads(self.rollback_data) if self.rollback_data else None
        }

class DataAnnotation(db.Model):
    """
    User annotations and contextual information for data points
    """
    __tablename__ = 'data_annotations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Annotation identification
    annotation_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Data reference
    data_point_id = db.Column(db.String(100), nullable=False)
    data_point_type = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(100), nullable=True)  # Specific field being annotated
    
    # Annotation details
    annotation_type = db.Column(db.Enum(AnnotationType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Annotation metadata
    visibility = db.Column(db.String(20), nullable=False, default='company')  # 'private', 'team', 'company', 'public'
    priority = db.Column(db.String(20), nullable=False, default='medium')  # 'low', 'medium', 'high'
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags
    
    # User information
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    lineage_id = db.Column(db.String(36), db.ForeignKey('data_lineage.lineage_id'), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_annotations')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_annotations')
    company = db.relationship('Company', backref='data_annotations')
    lineage = db.relationship('DataLineage', backref='annotations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'annotation_id': self.annotation_id,
            'data_point_id': self.data_point_id,
            'data_point_type': self.data_point_type,
            'field_name': self.field_name,
            'annotation_type': self.annotation_type.value,
            'title': self.title,
            'content': self.content,
            'visibility': self.visibility,
            'priority': self.priority,
            'tags': json.loads(self.tags) if self.tags else [],
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'company_id': self.company_id,
            'lineage_id': self.lineage_id,
            'is_active': self.is_active,
            'is_pinned': self.is_pinned
        }

class CorrectionWorkflow(db.Model):
    """
    Workflow rules for data corrections
    """
    __tablename__ = 'correction_workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Workflow identification
    workflow_name = db.Column(db.String(100), nullable=False)
    workflow_description = db.Column(db.Text, nullable=True)
    
    # Workflow conditions
    data_type_pattern = db.Column(db.String(100), nullable=True)  # Pattern for data types
    correction_type = db.Column(db.Enum(CorrectionType), nullable=True)  # Specific correction type
    business_impact_threshold = db.Column(db.String(20), nullable=True)  # Minimum business impact
    confidence_impact_threshold = db.Column(db.Float, nullable=True)  # Minimum confidence impact
    
    # Workflow rules
    requires_approval = db.Column(db.Boolean, nullable=False, default=True)
    auto_approve_threshold = db.Column(db.Float, nullable=True)  # Auto-approve if confidence impact below this
    approval_roles = db.Column(db.Text, nullable=True)  # JSON array of required roles
    notification_roles = db.Column(db.Text, nullable=True)  # JSON array of roles to notify
    
    # Implementation rules
    auto_implement = db.Column(db.Boolean, nullable=False, default=False)
    implementation_delay_hours = db.Column(db.Integer, nullable=False, default=0)
    requires_backup = db.Column(db.Boolean, nullable=False, default=True)
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Metadata
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    priority = db.Column(db.Integer, nullable=False, default=100)  # Lower number = higher priority
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='correction_workflows')
    creator = db.relationship('User', backref='correction_workflows')
    
    def to_dict(self):
        return {
            'id': self.id,
            'workflow_name': self.workflow_name,
            'workflow_description': self.workflow_description,
            'data_type_pattern': self.data_type_pattern,
            'correction_type': self.correction_type.value if self.correction_type else None,
            'business_impact_threshold': self.business_impact_threshold,
            'confidence_impact_threshold': self.confidence_impact_threshold,
            'requires_approval': self.requires_approval,
            'auto_approve_threshold': self.auto_approve_threshold,
            'approval_roles': json.loads(self.approval_roles) if self.approval_roles else [],
            'notification_roles': json.loads(self.notification_roles) if self.notification_roles else [],
            'auto_implement': self.auto_implement,
            'implementation_delay_hours': self.implementation_delay_hours,
            'requires_backup': self.requires_backup,
            'company_id': self.company_id,
            'is_active': self.is_active,
            'priority': self.priority,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class UserFeedback(db.Model):
    """
    User feedback on data quality and system performance
    """
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Feedback identification
    feedback_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Feedback target
    target_type = db.Column(db.String(50), nullable=False)  # 'data_point', 'transformation', 'system', 'feature'
    target_id = db.Column(db.String(100), nullable=False)
    
    # Feedback content
    feedback_type = db.Column(db.String(50), nullable=False)  # 'quality', 'accuracy', 'usability', 'performance', 'bug', 'feature_request'
    rating = db.Column(db.Integer, nullable=True)  # 1-5 rating
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Feedback metadata
    severity = db.Column(db.String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'critical'
    category = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags
    
    # User information
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='open')  # 'open', 'acknowledged', 'in_progress', 'resolved', 'closed'
    resolution = db.Column(db.Text, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submitted_feedback')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_feedback')
    company = db.relationship('Company', backref='user_feedback')
    
    def to_dict(self):
        return {
            'id': self.id,
            'feedback_id': self.feedback_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'feedback_type': self.feedback_type,
            'rating': self.rating,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'category': self.category,
            'tags': json.loads(self.tags) if self.tags else [],
            'submitted_by': self.submitted_by,
            'status': self.status,
            'resolution': self.resolution,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'company_id': self.company_id,
            'submitted_at': self.submitted_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CorrectionImpact(db.Model):
    """
    Track the impact of data corrections on system performance
    """
    __tablename__ = 'correction_impacts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Impact identification
    correction_id = db.Column(db.String(36), db.ForeignKey('data_corrections.correction_id'), nullable=False)
    
    # Impact metrics
    confidence_before = db.Column(db.Float, nullable=True)
    confidence_after = db.Column(db.Float, nullable=True)
    confidence_improvement = db.Column(db.Float, nullable=True)
    
    # Downstream impacts
    affected_data_points = db.Column(db.Integer, nullable=False, default=0)
    affected_calculations = db.Column(db.Integer, nullable=False, default=0)
    affected_reports = db.Column(db.Integer, nullable=False, default=0)
    
    # Performance metrics
    processing_time_ms = db.Column(db.Integer, nullable=True)
    validation_score_improvement = db.Column(db.Float, nullable=True)
    user_satisfaction_impact = db.Column(db.Float, nullable=True)
    
    # Impact details
    impact_summary = db.Column(db.Text, nullable=True)  # JSON summary of impacts
    
    # Timestamps
    measured_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    correction = db.relationship('DataCorrection', backref='impacts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'correction_id': self.correction_id,
            'confidence_before': self.confidence_before,
            'confidence_after': self.confidence_after,
            'confidence_improvement': self.confidence_improvement,
            'affected_data_points': self.affected_data_points,
            'affected_calculations': self.affected_calculations,
            'affected_reports': self.affected_reports,
            'processing_time_ms': self.processing_time_ms,
            'validation_score_improvement': self.validation_score_improvement,
            'user_satisfaction_impact': self.user_satisfaction_impact,
            'impact_summary': json.loads(self.impact_summary) if self.impact_summary else {},
            'measured_at': self.measured_at.isoformat()
        }

