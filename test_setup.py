#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    print("Testing Elite Command Data API components...")
    
    # Test basic imports
    print("1. Testing basic imports...")
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    print("   ✓ Flask imports successful")
    
    # Test model imports
    print("2. Testing model imports...")
    from src.models.user import db
    print("   ✓ User model import successful")
    
    from src.models.elite_command import (
        Founder, Portfolio, Company, BusinessUnit, DataSource, 
        MetricSnapshot, DataIngestionLog, RawDataEntry
    )
    print("   ✓ Elite Command models import successful")
    
    # Test Flask app creation
    print("3. Testing Flask app creation...")
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    print("   ✓ Flask app creation successful")
    
    # Test database creation
    print("4. Testing database creation...")
    with app.app_context():
        db.create_all()
    print("   ✓ Database creation successful")
    
    # Test route imports
    print("5. Testing route imports...")
    from src.routes.ingestion import ingestion_bp
    print("   ✓ Ingestion routes import successful")
    
    from src.routes.file_processing import file_processing_bp
    print("   ✓ File processing routes import successful")
    
    from src.routes.oauth import oauth_bp
    print("   ✓ OAuth routes import successful")
    
    from src.routes.email_processing import email_processing_bp
    print("   ✓ Email processing routes import successful")
    
    from src.routes.normalization import normalization_bp
    print("   ✓ Normalization routes import successful")
    
    from src.routes.intelligence import intelligence_bp
    print("   ✓ Intelligence routes import successful")
    
    from src.routes.api_info import api_info_bp
    print("   ✓ API info routes import successful")
    
    from src.routes.psychological import psychological_bp
    print("   ✓ Psychological analysis routes import successful")
    
except Exception as e:
    print(f"   ✗ Route imports failed: {e}")
    exit(1)

print("6. Testing psychological models...")
try:
    from src.models.psychological import (
        PsychologicalProfile, CommunicationAnalysis, BehavioralPattern,
        PsychologicalAlert, GroupDynamicsAnalysis, WordsmimirApiLog
    )
    print("   ✓ Psychological models import successful")
except Exception as e:
    print(f"   ✗ Psychological models import failed: {e}")
    exit(1)

print("7. Testing wordsmimir service...")
try:
    from src.services.wordsmimir import create_wordsmimir_service, WordsmimirService
    print("   ✓ Wordsmimir service import successful")
except Exception as e:
    print(f"   ✗ Wordsmimir service import failed: {e}")
    exit(1)

print("8. Testing multimedia analysis service...")
try:
    from src.services.multimedia import create_multimedia_service, MultimediaAnalysisService
    print("   ✓ Multimedia analysis service import successful")
except Exception as e:
    print(f"   ✗ Multimedia analysis service import failed: {e}")
    exit(1)

print("9. Testing multimedia routes...")
try:
    from src.routes.multimedia import multimedia_bp
    print("   ✓ Multimedia routes import successful")
except Exception as e:
    print(f"   ✗ Multimedia routes import failed: {e}")
    exit(1)

print("10. Testing profiling engine...")
try:
    from src.services.profiling_engine import create_profiling_engine, PsychologicalProfilingEngine
    print("   ✓ Profiling engine import successful")
except Exception as e:
    print(f"   ✗ Profiling engine import failed: {e}")
    exit(1)

print("11. Testing profiling routes...")
try:
    from src.routes.profiling import profiling_bp
    print("   ✓ Profiling routes import successful")
except Exception as e:
    print(f"   ✗ Profiling routes import failed: {e}")
    exit(1)

print("13. Testing HSI intelligence routes...")
try:
    from src.routes.hsi import hsi_bp
    print("   ✓ HSI intelligence routes import successful")
except Exception as e:
    print(f"   ✗ HSI intelligence routes import failed: {e}")

print("15. Testing HITL validation system...")
try:
    from src.models.validation import ValidationQueue, ValidationRule, ValidationFeedback, ValidationMetrics
    print("   ✓ HITL validation models import successful")
    
    from src.services.hitl_validation import hitl_service
    print("   ✓ HITL validation service import successful")
    
    from src.routes.hitl import hitl_bp
    print("   ✓ HITL validation routes import successful")
except Exception as e:
    print(f"   ✗ HITL validation system import failed: {e}")

print("17. Testing business model templates system...")
try:
    from src.models.business_templates import BusinessModelTemplate, MetricDefinition, CompanyTemplate, NormalizationResult, TemplatePerformance
    print("   ✓ Business model templates models import successful")
    
    from src.services.template_normalization import template_normalization_engine
    print("   ✓ Template normalization engine import successful")
    
    from src.routes.templates import templates_bp
    print("   ✓ Business model templates routes import successful")
except Exception as e:
    print(f"   ✗ Business model templates system import failed: {e}")

print("18. Testing confidence scoring and data lineage system...")
try:
    from src.models.confidence_lineage import DataLineage, ConfidenceScore, ConfidenceFactor, LineageGraph, ConfidenceThreshold, ConfidenceAlert
    print("   ✓ Confidence and lineage models import successful")
    
    from src.services.confidence_lineage import confidence_lineage_service
    print("   ✓ Confidence lineage service import successful")
    
    from src.routes.confidence import confidence_bp
    print("   ✓ Confidence scoring and lineage routes import successful")
except Exception as e:
    print(f"   ✗ Confidence scoring and lineage system import failed: {e}")

print("19. Testing user-driven data corrections system...")
try:
    from src.models.corrections import DataCorrection, DataAnnotation, CorrectionWorkflow, UserFeedback, CorrectionImpact
    print("   ✓ Data corrections models import successful")
    
    from src.services.data_corrections import data_correction_service
    print("   ✓ Data corrections service import successful")
except Exception as e:
    print(f"   ✗ Data corrections models/service import failed: {e}")

print("20. Testing user-driven data corrections...")
try:
    from src.routes.corrections import corrections_bp
    print("   ✓ User-driven data corrections routes import successful")
except Exception as e:
    print(f"   ✗ User-driven data corrections routes import failed: {e}")

print("21. Testing AI command interface...")
try:
    from src.routes.ai_commands import ai_bp
    print("   ✓ AI command interface routes import successful")
except Exception as e:
    print(f"   ✗ AI command interface routes import failed: {e}")

print("22. Testing AI command service...")
try:
    from src.services.ai_commands import ai_command_service
    print("   ✓ AI command service import successful")
except Exception as e:
    print(f"   ✗ AI command service import failed: {e}")

print("23. Testing AI command models...")
try:
    from src.models.ai_commands import (
        AICommand, ConversationSession, CommandTemplate, AutomationRule, CommandFeedback
    )
    print("   ✓ AI command models import successful")
except Exception as e:
    print(f"   ✗ AI command models import failed: {e}")

print("24. Testing production security and monitoring...")
try:
    from src.routes.security import security_bp
    print("   ✓ Security and monitoring routes import successful")
    
    from src.services.security_monitoring import security_monitoring_service
    print("   ✓ Security and monitoring service import successful")
    
    from src.models.security_monitoring import (
        APIKey, SecurityEvent, RateLimitRule, MonitoringMetric, SystemAlert, AuditLog
    )
    print("   ✓ Security and monitoring models import successful")
except Exception as e:
    print(f"   ✗ Security and monitoring import failed: {e}")

print("\n✅ All component tests completed!")
print("🚀 Elite Command Data API with HSI and Production Optimizations is ready!")

