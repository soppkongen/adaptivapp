from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json

db = SQLAlchemy()

class ValidationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CORRECTION = "needs_correction"
    ESCALATED = "escalated"

class ValidationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ValidationQueue(db.Model):
    """
    Human-in-the-Loop validation queue for low-confidence data points
    """
    __tablename__ = 'validation_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Data identification
    data_type = db.Column(db.String(50), nullable=False)  # 'metric', 'entity', 'normalization'
    source_data_id = db.Column(db.String(100), nullable=False)  # ID of the original data
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Validation details
    confidence_score = db.Column(db.Float, nullable=False)
    confidence_threshold = db.Column(db.Float, nullable=False, default=0.85)
    priority = db.Column(db.Enum(ValidationPriority), nullable=False, default=ValidationPriority.MEDIUM)
    status = db.Column(db.Enum(ValidationStatus), nullable=False, default=ValidationStatus.PENDING)
    
    # Data content
    original_data = db.Column(db.Text, nullable=False)  # JSON string of original data
    normalized_data = db.Column(db.Text, nullable=False)  # JSON string of normalized data
    suggested_corrections = db.Column(db.Text, nullable=True)  # JSON string of AI suggestions
    
    # Confidence breakdown
    confidence_breakdown = db.Column(db.Text, nullable=True)  # JSON string of detailed confidence scores
    
    # Validation workflow
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Feedback and corrections
    reviewer_feedback = db.Column(db.Text, nullable=True)
    corrected_data = db.Column(db.Text, nullable=True)  # JSON string of corrected data
    correction_reason = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='validation_items')
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_validations')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_validations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_type': self.data_type,
            'source_data_id': self.source_data_id,
            'company_id': self.company_id,
            'confidence_score': self.confidence_score,
            'confidence_threshold': self.confidence_threshold,
            'priority': self.priority.value,
            'status': self.status.value,
            'original_data': json.loads(self.original_data) if self.original_data else None,
            'normalized_data': json.loads(self.normalized_data) if self.normalized_data else None,
            'suggested_corrections': json.loads(self.suggested_corrections) if self.suggested_corrections else None,
            'confidence_breakdown': json.loads(self.confidence_breakdown) if self.confidence_breakdown else None,
            'assigned_to': self.assigned_to,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewer_feedback': self.reviewer_feedback,
            'corrected_data': json.loads(self.corrected_data) if self.corrected_data else None,
            'correction_reason': self.correction_reason,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ValidationRule(db.Model):
    """
    Configurable rules for determining when data should be sent to validation queue
    """
    __tablename__ = 'validation_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rule identification
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    data_type = db.Column(db.String(50), nullable=False)  # 'metric', 'entity', 'normalization'
    
    # Rule configuration
    confidence_threshold = db.Column(db.Float, nullable=False, default=0.85)
    priority_mapping = db.Column(db.Text, nullable=False)  # JSON mapping confidence ranges to priorities
    
    # Conditions
    conditions = db.Column(db.Text, nullable=False)  # JSON string of rule conditions
    
    # Rule status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='validation_rules')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'data_type': self.data_type,
            'confidence_threshold': self.confidence_threshold,
            'priority_mapping': json.loads(self.priority_mapping) if self.priority_mapping else None,
            'conditions': json.loads(self.conditions) if self.conditions else None,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ValidationFeedback(db.Model):
    """
    Feedback and learning data from validation decisions
    """
    __tablename__ = 'validation_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference to validation item
    validation_id = db.Column(db.Integer, db.ForeignKey('validation_queue.id'), nullable=False)
    
    # Feedback details
    feedback_type = db.Column(db.String(50), nullable=False)  # 'correction', 'approval', 'pattern'
    feedback_data = db.Column(db.Text, nullable=False)  # JSON string of feedback details
    
    # Learning metrics
    accuracy_improvement = db.Column(db.Float, nullable=True)
    pattern_confidence = db.Column(db.Float, nullable=True)
    
    # Training data flag
    use_for_training = db.Column(db.Boolean, nullable=False, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    validation_item = db.relationship('ValidationQueue', backref='feedback_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'validation_id': self.validation_id,
            'feedback_type': self.feedback_type,
            'feedback_data': json.loads(self.feedback_data) if self.feedback_data else None,
            'accuracy_improvement': self.accuracy_improvement,
            'pattern_confidence': self.pattern_confidence,
            'use_for_training': self.use_for_training,
            'created_at': self.created_at.isoformat()
        }

class ValidationMetrics(db.Model):
    """
    Metrics tracking the performance of the validation system
    """
    __tablename__ = 'validation_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Time period
    date = db.Column(db.Date, nullable=False)
    
    # Volume metrics
    total_items_queued = db.Column(db.Integer, nullable=False, default=0)
    total_items_reviewed = db.Column(db.Integer, nullable=False, default=0)
    total_items_approved = db.Column(db.Integer, nullable=False, default=0)
    total_items_rejected = db.Column(db.Integer, nullable=False, default=0)
    total_items_corrected = db.Column(db.Integer, nullable=False, default=0)
    
    # Performance metrics
    average_review_time_minutes = db.Column(db.Float, nullable=True)
    accuracy_rate = db.Column(db.Float, nullable=True)
    false_positive_rate = db.Column(db.Float, nullable=True)
    false_negative_rate = db.Column(db.Float, nullable=True)
    
    # Confidence metrics
    average_confidence_score = db.Column(db.Float, nullable=True)
    confidence_improvement = db.Column(db.Float, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_items_queued': self.total_items_queued,
            'total_items_reviewed': self.total_items_reviewed,
            'total_items_approved': self.total_items_approved,
            'total_items_rejected': self.total_items_rejected,
            'total_items_corrected': self.total_items_corrected,
            'average_review_time_minutes': self.average_review_time_minutes,
            'accuracy_rate': self.accuracy_rate,
            'false_positive_rate': self.false_positive_rate,
            'false_negative_rate': self.false_negative_rate,
            'average_confidence_score': self.average_confidence_score,
            'confidence_improvement': self.confidence_improvement,
            'created_at': self.created_at.isoformat()
        }

