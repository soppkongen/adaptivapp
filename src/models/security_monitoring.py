from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

db = SQLAlchemy()

class SecurityEventType(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_BREACH_ATTEMPT = "system_breach_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    API_KEY_MISUSE = "api_key_misuse"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MonitoringMetricType(Enum):
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    REQUEST_COUNT = "request_count"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DATABASE_CONNECTIONS = "database_connections"
    ACTIVE_SESSIONS = "active_sessions"
    CONFIDENCE_SCORE_AVERAGE = "confidence_score_average"
    VALIDATION_QUEUE_SIZE = "validation_queue_size"
    AI_COMMAND_SUCCESS_RATE = "ai_command_success_rate"

class APIKey(db.Model):
    """API Key management for secure access"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    key_hash = db.Column(db.String(256), nullable=False)  # Hashed API key
    key_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Access control
    user_id = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.Integer)
    permissions = db.Column(db.Text)  # JSON array of permissions
    rate_limit = db.Column(db.Integer, default=1000)  # Requests per hour
    
    # Status and lifecycle
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, nullable=False)
    revoked_at = db.Column(db.DateTime)
    revoked_by = db.Column(db.Integer)
    revocation_reason = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'id': self.id,
            'key_id': self.key_id,
            'key_name': self.key_name,
            'description': self.description,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'permissions': json.loads(self.permissions) if self.permissions else [],
            'rate_limit': self.rate_limit,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by
        }

class SecurityEvent(db.Model):
    """Security event logging and monitoring"""
    __tablename__ = 'security_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    event_type = db.Column(db.Enum(SecurityEventType), nullable=False)
    severity = db.Column(db.Enum(AlertSeverity), nullable=False)
    
    # Event details
    description = db.Column(db.Text, nullable=False)
    source_ip = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))
    
    # Associated entities
    user_id = db.Column(db.Integer)
    company_id = db.Column(db.Integer)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'))
    session_id = db.Column(db.String(255))
    
    # Event data
    event_data = db.Column(db.Text)  # JSON data
    risk_score = db.Column(db.Float, default=0.0)
    is_blocked = db.Column(db.Boolean, default=False)
    
    # Response and resolution
    response_action = db.Column(db.String(100))
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer)
    resolution_notes = db.Column(db.Text)
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'source_ip': self.source_ip,
            'user_agent': self.user_agent,
            'endpoint': self.endpoint,
            'method': self.method,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'api_key_id': self.api_key_id,
            'session_id': self.session_id,
            'event_data': json.loads(self.event_data) if self.event_data else {},
            'risk_score': self.risk_score,
            'is_blocked': self.is_blocked,
            'response_action': self.response_action,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_notes': self.resolution_notes,
            'timestamp': self.timestamp.isoformat()
        }

class RateLimitRule(db.Model):
    """Rate limiting rules and tracking"""
    __tablename__ = 'rate_limit_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Rule configuration
    endpoint_pattern = db.Column(db.String(255))  # Regex pattern for endpoints
    method = db.Column(db.String(10))  # HTTP method
    limit_count = db.Column(db.Integer, nullable=False)  # Number of requests
    time_window = db.Column(db.Integer, nullable=False)  # Time window in seconds
    
    # Scope
    applies_to_all = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer)  # Specific user
    company_id = db.Column(db.Integer)  # Specific company
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'))  # Specific API key
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=100)  # Lower number = higher priority
    
    # Actions
    block_request = db.Column(db.Boolean, default=True)
    send_alert = db.Column(db.Boolean, default=True)
    log_violation = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'description': self.description,
            'endpoint_pattern': self.endpoint_pattern,
            'method': self.method,
            'limit_count': self.limit_count,
            'time_window': self.time_window,
            'applies_to_all': self.applies_to_all,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'api_key_id': self.api_key_id,
            'is_active': self.is_active,
            'priority': self.priority,
            'block_request': self.block_request,
            'send_alert': self.send_alert,
            'log_violation': self.log_violation,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'updated_at': self.updated_at.isoformat()
        }

class MonitoringMetric(db.Model):
    """System monitoring metrics and performance data"""
    __tablename__ = 'monitoring_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    metric_type = db.Column(db.Enum(MonitoringMetricType), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    
    # Metric value
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))  # e.g., 'ms', '%', 'count'
    
    # Context
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))
    company_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    
    # Additional data
    event_metadata = db.Column(db.Text)  # JSON metadata
    tags = db.Column(db.Text)  # JSON array of tags
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_id': self.metric_id,
            'metric_type': self.metric_type.value,
            'metric_name': self.metric_name,
            'value': self.value,
            'unit': self.unit,
            'endpoint': self.endpoint,
            'method': self.method,
            'company_id': self.company_id,
            'user_id': self.user_id,
            'event_metadata': json.loads(self.event_metadata) if self.event_metadata else {},
            'tags': json.loads(self.tags) if self.tags else [],
            'timestamp': self.timestamp.isoformat()
        }

class SystemAlert(db.Model):
    """System alerts and notifications"""
    __tablename__ = 'system_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.Enum(AlertSeverity), nullable=False)
    
    # Alert content
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)  # JSON details
    
    # Source
    source_system = db.Column(db.String(50))
    source_component = db.Column(db.String(100))
    related_entity_type = db.Column(db.String(50))
    related_entity_id = db.Column(db.String(100))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer)
    acknowledged_at = db.Column(db.DateTime)
    
    # Resolution
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    
    # Escalation
    escalation_level = db.Column(db.Integer, default=0)
    escalated_at = db.Column(db.DateTime)
    escalated_to = db.Column(db.Integer)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'details': json.loads(self.details) if self.details else {},
            'source_system': self.source_system,
            'source_component': self.source_component,
            'related_entity_type': self.related_entity_type,
            'related_entity_id': self.related_entity_id,
            'is_active': self.is_active,
            'is_acknowledged': self.is_acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'is_resolved': self.is_resolved,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'escalation_level': self.escalation_level,
            'escalated_at': self.escalated_at.isoformat() if self.escalated_at else None,
            'escalated_to': self.escalated_to,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AuditLog(db.Model):
    """Comprehensive audit logging for compliance and security"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Action details
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(100))
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))
    
    # Actor information
    user_id = db.Column(db.Integer)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'))
    session_id = db.Column(db.String(255))
    source_ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    # Data changes
    old_values = db.Column(db.Text)  # JSON of old values
    new_values = db.Column(db.Text)  # JSON of new values
    changes_summary = db.Column(db.Text)
    
    # Context
    company_id = db.Column(db.Integer)
    request_id = db.Column(db.String(36))
    correlation_id = db.Column(db.String(36))
    
    # Result
    success = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text)
    response_code = db.Column(db.Integer)
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    additional_data = db.Column(db.Text)  # JSON additional data
    
    def to_dict(self):
        return {
            'id': self.id,
            'log_id': self.log_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'user_id': self.user_id,
            'api_key_id': self.api_key_id,
            'session_id': self.session_id,
            'source_ip': self.source_ip,
            'user_agent': self.user_agent,
            'old_values': json.loads(self.old_values) if self.old_values else {},
            'new_values': json.loads(self.new_values) if self.new_values else {},
            'changes_summary': self.changes_summary,
            'company_id': self.company_id,
            'request_id': self.request_id,
            'correlation_id': self.correlation_id,
            'success': self.success,
            'error_message': self.error_message,
            'response_code': self.response_code,
            'timestamp': self.timestamp.isoformat(),
            'additional_data': json.loads(self.additional_data) if self.additional_data else {}
        }

