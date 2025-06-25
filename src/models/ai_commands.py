from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json
import uuid

db = SQLAlchemy()

class CommandType(Enum):
    QUERY = "query"
    MODIFICATION = "modification"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"
    CONFIGURATION = "configuration"
    REPORTING = "reporting"

class CommandStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CommandPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AICommand(db.Model):
    """
    AI-powered natural language commands
    """
    __tablename__ = 'ai_commands'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Command identification
    command_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    
    # Command content
    natural_language_input = db.Column(db.Text, nullable=False)
    parsed_intent = db.Column(db.Text, nullable=True)  # JSON parsed intent
    command_type = db.Column(db.Enum(CommandType), nullable=False)
    
    # Command execution
    generated_code = db.Column(db.Text, nullable=True)  # Generated code/queries
    execution_plan = db.Column(db.Text, nullable=True)  # JSON execution plan
    execution_result = db.Column(db.Text, nullable=True)  # JSON execution result
    
    # Command metadata
    priority = db.Column(db.Enum(CommandPriority), nullable=False, default=CommandPriority.MEDIUM)
    status = db.Column(db.Enum(CommandStatus), nullable=False, default=CommandStatus.PENDING)
    confidence_score = db.Column(db.Float, nullable=True)  # AI confidence in interpretation
    
    # User information
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)  # Conversation session
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Execution details
    execution_time_ms = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    requires_approval = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submitted_commands')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_commands')
    company = db.relationship('Company', backref='ai_commands')
    
    def to_dict(self):
        return {
            'id': self.id,
            'command_id': self.command_id,
            'natural_language_input': self.natural_language_input,
            'parsed_intent': json.loads(self.parsed_intent) if self.parsed_intent else None,
            'command_type': self.command_type.value,
            'generated_code': self.generated_code,
            'execution_plan': json.loads(self.execution_plan) if self.execution_plan else None,
            'execution_result': json.loads(self.execution_result) if self.execution_result else None,
            'priority': self.priority.value,
            'status': self.status.value,
            'confidence_score': self.confidence_score,
            'submitted_by': self.submitted_by,
            'approved_by': self.approved_by,
            'company_id': self.company_id,
            'session_id': self.session_id,
            'submitted_at': self.submitted_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time_ms': self.execution_time_ms,
            'error_message': self.error_message,
            'requires_approval': self.requires_approval
        }

class CommandTemplate(db.Model):
    """
    Pre-defined command templates for common operations
    """
    __tablename__ = 'command_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template identification
    template_name = db.Column(db.String(100), nullable=False)
    template_description = db.Column(db.Text, nullable=True)
    
    # Template content
    natural_language_patterns = db.Column(db.Text, nullable=False)  # JSON array of patterns
    command_type = db.Column(db.Enum(CommandType), nullable=False)
    code_template = db.Column(db.Text, nullable=False)  # Template with placeholders
    
    # Template metadata
    category = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags
    usage_count = db.Column(db.Integer, nullable=False, default=0)
    success_rate = db.Column(db.Float, nullable=False, default=0.0)
    
    # Access control
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    requires_approval = db.Column(db.Boolean, nullable=False, default=False)
    allowed_roles = db.Column(db.Text, nullable=True)  # JSON array of allowed roles
    
    # Context
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relationships
    company = db.relationship('Company', backref='command_templates')
    creator = db.relationship('User', backref='command_templates')
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_name': self.template_name,
            'template_description': self.template_description,
            'natural_language_patterns': json.loads(self.natural_language_patterns),
            'command_type': self.command_type.value,
            'code_template': self.code_template,
            'category': self.category,
            'tags': json.loads(self.tags) if self.tags else [],
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'is_public': self.is_public,
            'requires_approval': self.requires_approval,
            'allowed_roles': json.loads(self.allowed_roles) if self.allowed_roles else [],
            'company_id': self.company_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

class ConversationSession(db.Model):
    """
    AI conversation sessions for context management
    """
    __tablename__ = 'conversation_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Session identification
    session_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    session_name = db.Column(db.String(200), nullable=True)
    
    # Session content
    conversation_history = db.Column(db.Text, nullable=True)  # JSON conversation history
    context_data = db.Column(db.Text, nullable=True)  # JSON context data
    
    # Session metadata
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Session status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='conversation_sessions')
    company = db.relationship('Company', backref='conversation_sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'session_name': self.session_name,
            'conversation_history': json.loads(self.conversation_history) if self.conversation_history else [],
            'context_data': json.loads(self.context_data) if self.context_data else {},
            'user_id': self.user_id,
            'company_id': self.company_id,
            'is_active': self.is_active,
            'last_activity': self.last_activity.isoformat(),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class AutomationRule(db.Model):
    """
    AI-created automation rules
    """
    __tablename__ = 'automation_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rule identification
    rule_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    rule_name = db.Column(db.String(100), nullable=False)
    rule_description = db.Column(db.Text, nullable=True)
    
    # Rule definition
    trigger_conditions = db.Column(db.Text, nullable=False)  # JSON trigger conditions
    actions = db.Column(db.Text, nullable=False)  # JSON actions to execute
    
    # Rule metadata
    category = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.Enum(CommandPriority), nullable=False, default=CommandPriority.MEDIUM)
    
    # Rule status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    execution_count = db.Column(db.Integer, nullable=False, default=0)
    success_count = db.Column(db.Integer, nullable=False, default=0)
    last_executed = db.Column(db.DateTime, nullable=True)
    
    # Context
    created_by_command = db.Column(db.String(36), db.ForeignKey('ai_commands.command_id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    command = db.relationship('AICommand', backref='automation_rules')
    company = db.relationship('Company', backref='automation_rules')
    creator = db.relationship('User', backref='automation_rules')
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'rule_description': self.rule_description,
            'trigger_conditions': json.loads(self.trigger_conditions),
            'actions': json.loads(self.actions),
            'category': self.category,
            'priority': self.priority.value,
            'is_active': self.is_active,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'created_by_command': self.created_by_command,
            'company_id': self.company_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CommandFeedback(db.Model):
    """
    User feedback on AI command execution
    """
    __tablename__ = 'command_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Feedback identification
    command_id = db.Column(db.String(36), db.ForeignKey('ai_commands.command_id'), nullable=False)
    
    # Feedback content
    rating = db.Column(db.Integer, nullable=True)  # 1-5 rating
    feedback_type = db.Column(db.String(50), nullable=False)  # 'accuracy', 'speed', 'usefulness', 'clarity'
    feedback_text = db.Column(db.Text, nullable=True)
    
    # Feedback metadata
    was_helpful = db.Column(db.Boolean, nullable=True)
    interpretation_correct = db.Column(db.Boolean, nullable=True)
    result_accurate = db.Column(db.Boolean, nullable=True)
    
    # User information
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    command = db.relationship('AICommand', backref='feedback')
    submitter = db.relationship('User', backref='command_feedback')
    
    def to_dict(self):
        return {
            'id': self.id,
            'command_id': self.command_id,
            'rating': self.rating,
            'feedback_type': self.feedback_type,
            'feedback_text': self.feedback_text,
            'was_helpful': self.was_helpful,
            'interpretation_correct': self.interpretation_correct,
            'result_accurate': self.result_accurate,
            'submitted_by': self.submitted_by,
            'submitted_at': self.submitted_at.isoformat()
        }

