from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from enum import Enum

db = SQLAlchemy()

class BusinessStage(Enum):
    STARTUP = "startup"
    GROWTH = "growth"
    MATURE = "mature"
    EXIT = "exit"

class BusinessModel(Enum):
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    CONTENT = "content"
    SERVICES = "services"
    MARKETPLACE = "marketplace"
    OTHER = "other"

class UpdateType(Enum):
    WEEKLY_UPDATE = "weekly_update"
    INCIDENT = "incident"
    INVESTMENT_THESIS = "investment_thesis"
    SALON_LOG = "salon_log"
    FINANCIAL_REPORT = "financial_report"
    STRATEGIC_UPDATE = "strategic_update"

class Founder(db.Model):
    """Founder entity representing the top-level organizational unit"""
    __tablename__ = 'founders'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # Strategic preferences and profile
    risk_tolerance = db.Column(db.Float, default=0.5)  # 0-1 scale
    strategic_focus_areas = db.Column(db.Text)  # JSON array
    communication_preferences = db.Column(db.Text)  # JSON object
    network_strength_score = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='founder', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'risk_tolerance': self.risk_tolerance,
            'strategic_focus_areas': json.loads(self.strategic_focus_areas) if self.strategic_focus_areas else [],
            'communication_preferences': json.loads(self.communication_preferences) if self.communication_preferences else {},
            'network_strength_score': self.network_strength_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Portfolio(db.Model):
    """Portfolio entity representing collections of businesses"""
    __tablename__ = 'portfolios'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    founder_id = db.Column(db.String(36), db.ForeignKey('founders.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Strategic information
    investment_thesis = db.Column(db.Text)
    target_metrics = db.Column(db.Text)  # JSON object
    diversification_strategy = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    companies = db.relationship('Company', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'founder_id': self.founder_id,
            'name': self.name,
            'investment_thesis': self.investment_thesis,
            'target_metrics': json.loads(self.target_metrics) if self.target_metrics else {},
            'diversification_strategy': self.diversification_strategy,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Company(db.Model):
    """Company entity representing individual businesses"""
    __tablename__ = 'companies'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    portfolio_id = db.Column(db.String(36), db.ForeignKey('portfolios.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100))
    
    # Business characteristics
    business_model = db.Column(db.Enum(BusinessModel), nullable=False)
    stage = db.Column(db.Enum(BusinessStage), nullable=False)
    industry = db.Column(db.String(50))
    
    # Key metrics (stored as JSON for flexibility)
    current_metrics = db.Column(db.Text)  # JSON object with ARR, churn, burn, etc.
    team_structure = db.Column(db.Text)  # JSON object
    market_position = db.Column(db.Text)  # JSON object
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business_units = db.relationship('BusinessUnit', backref='company', lazy=True, cascade='all, delete-orphan')
    data_sources = db.relationship('DataSource', backref='company', lazy=True, cascade='all, delete-orphan')
    metrics_history = db.relationship('MetricSnapshot', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'name': self.name,
            'domain': self.domain,
            'business_model': self.business_model.value if self.business_model else None,
            'stage': self.stage.value if self.stage else None,
            'industry': self.industry,
            'current_metrics': json.loads(self.current_metrics) if self.current_metrics else {},
            'team_structure': json.loads(self.team_structure) if self.team_structure else {},
            'market_position': json.loads(self.market_position) if self.market_position else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class BusinessUnit(db.Model):
    """Business unit entity for granular operational visibility"""
    __tablename__ = 'business_units'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    functional_area = db.Column(db.String(50))  # sales, marketing, product, operations
    
    # Performance and resource data
    performance_metrics = db.Column(db.Text)  # JSON object
    resource_allocation = db.Column(db.Text)  # JSON object
    strategic_initiatives = db.Column(db.Text)  # JSON array
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'functional_area': self.functional_area,
            'performance_metrics': json.loads(self.performance_metrics) if self.performance_metrics else {},
            'resource_allocation': json.loads(self.resource_allocation) if self.resource_allocation else {},
            'strategic_initiatives': json.loads(self.strategic_initiatives) if self.strategic_initiatives else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class DataSource(db.Model):
    """Data source configuration and metadata"""
    __tablename__ = 'data_sources'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # webhook, oauth, file, email
    
    # Configuration
    config = db.Column(db.Text)  # JSON object with source-specific config
    credentials = db.Column(db.Text)  # Encrypted credentials
    is_active = db.Column(db.Boolean, default=True)
    
    # Quality metrics
    reliability_score = db.Column(db.Float, default=1.0)
    last_successful_sync = db.Column(db.DateTime)
    error_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'source_type': self.source_type,
            'config': json.loads(self.config) if self.config else {},
            'is_active': self.is_active,
            'reliability_score': self.reliability_score,
            'last_successful_sync': self.last_successful_sync.isoformat() if self.last_successful_sync else None,
            'error_count': self.error_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MetricSnapshot(db.Model):
    """Historical metric snapshots for trend analysis"""
    __tablename__ = 'metric_snapshots'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False)
    
    # Metric data
    metrics = db.Column(db.Text, nullable=False)  # JSON object with all metrics
    snapshot_date = db.Column(db.DateTime, nullable=False)
    
    # Metadata
    source_id = db.Column(db.String(36), db.ForeignKey('data_sources.id'))
    confidence_score = db.Column(db.Float, default=1.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'metrics': json.loads(self.metrics) if self.metrics else {},
            'snapshot_date': self.snapshot_date.isoformat(),
            'source_id': self.source_id,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat()
        }

class DataIngestionLog(db.Model):
    """Log of all data ingestion activities"""
    __tablename__ = 'data_ingestion_logs'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    source_id = db.Column(db.String(36), db.ForeignKey('data_sources.id'), nullable=False)
    
    # Ingestion details
    ingestion_type = db.Column(db.String(50), nullable=False)  # webhook, api_poll, file_upload, email
    status = db.Column(db.String(20), nullable=False)  # success, error, partial
    
    # Data details
    records_processed = db.Column(db.Integer, default=0)
    records_successful = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    
    # Error information
    error_message = db.Column(db.Text)
    error_details = db.Column(db.Text)  # JSON object
    
    # Processing time
    started_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    processing_duration = db.Column(db.Float)  # seconds
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'ingestion_type': self.ingestion_type,
            'status': self.status,
            'records_processed': self.records_processed,
            'records_successful': self.records_successful,
            'records_failed': self.records_failed,
            'error_message': self.error_message,
            'error_details': json.loads(self.error_details) if self.error_details else {},
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_duration': self.processing_duration,
            'created_at': self.created_at.isoformat()
        }

class RawDataEntry(db.Model):
    """Raw data entries before normalization"""
    __tablename__ = 'raw_data_entries'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    source_id = db.Column(db.String(36), db.ForeignKey('data_sources.id'), nullable=False)
    ingestion_log_id = db.Column(db.String(36), db.ForeignKey('data_ingestion_logs.id'))
    
    # Raw data
    raw_data = db.Column(db.Text, nullable=False)  # JSON object with original data
    data_type = db.Column(db.String(50))  # financial, operational, customer, etc.
    
    # Processing status
    processing_status = db.Column(db.String(20), default='pending')  # pending, processed, error
    normalized_data_id = db.Column(db.String(36))  # Reference to normalized data
    
    # Metadata
    source_timestamp = db.Column(db.DateTime)
    confidence_score = db.Column(db.Float, default=1.0)
    tags = db.Column(db.Text)  # JSON array
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'ingestion_log_id': self.ingestion_log_id,
            'raw_data': json.loads(self.raw_data) if self.raw_data else {},
            'data_type': self.data_type,
            'processing_status': self.processing_status,
            'normalized_data_id': self.normalized_data_id,
            'source_timestamp': self.source_timestamp.isoformat() if self.source_timestamp else None,
            'confidence_score': self.confidence_score,
            'tags': json.loads(self.tags) if self.tags else [],
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

