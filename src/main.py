import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.ingestion import ingestion_bp
from src.routes.file_processing import file_processing_bp
from src.routes.oauth import oauth_bp
from src.routes.email_processing import email_processing_bp
from src.routes.normalization import normalization_bp
from src.routes.intelligence import intelligence_bp
from src.routes.api_info import api_info_bp
from src.routes.psychological import psychological_bp, init_wordsmimir_service
from src.routes.multimedia import multimedia_bp, init_multimedia_service
from src.routes.profiling import profiling_bp
from src.routes.hsi import hsi_bp
from src.routes.hitl import hitl_bp
from src.routes.templates import templates_bp
from src.routes.confidence import confidence_bp
from src.routes.corrections import corrections_bp
from src.routes.ai_commands import ai_bp
from src.routes.security import security_bp
from src.routes.biometric import biometric_bp
from src.routes.command_reflex import command_reflex_bp
from src.routes.integrated_onboarding import integrated_onboarding_bp
from src.routes.advanced_voice import voice_bp
from src.routes.reflective_vault import vault_bp
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, continue with environment variables

# Configuration with safe defaults
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'placeholder_secret_key_change_in_production_12345')

# Wordsmimir configuration with safe defaults
app.config['WORDSMIMIR_API_KEY'] = os.environ.get('WORDSMIMIR_API_KEY', 'placeholder_wordsmimir_api_key_replace_with_real_key')
app.config['WORDSMIMIR_BASE_URL'] = os.environ.get('WORDSMIMIR_BASE_URL', 'https://wordsmimir.t-pip.no/api/v1')

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(ingestion_bp, url_prefix='/api/ingestion')
app.register_blueprint(file_processing_bp, url_prefix='/api/files')
app.register_blueprint(oauth_bp, url_prefix='/api/oauth')
app.register_blueprint(email_processing_bp, url_prefix='/api')
app.register_blueprint(normalization_bp, url_prefix='/api/normalize')
app.register_blueprint(intelligence_bp, url_prefix='/api/intelligence')
app.register_blueprint(api_info_bp, url_prefix='/api')
app.register_blueprint(psychological_bp)
app.register_blueprint(multimedia_bp)
app.register_blueprint(profiling_bp)
app.register_blueprint(hsi_bp)
app.register_blueprint(hitl_bp)
app.register_blueprint(templates_bp)
app.register_blueprint(confidence_bp)
app.register_blueprint(corrections_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(security_bp)
app.register_blueprint(biometric_bp)
app.register_blueprint(command_reflex_bp)
app.register_blueprint(integrated_onboarding_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(vault_bp)

# Database configuration with safe defaults
database_url = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Import all models to ensure they're registered
from src.models.elite_command import (
    Founder, Portfolio, Company, BusinessUnit, DataSource, 
    MetricSnapshot, DataIngestionLog, RawDataEntry
)

# Import psychological models
from src.models.psychological import (
    PsychologicalProfile, CommunicationAnalysis, BehavioralPattern,
    PsychologicalAlert, GroupDynamicsAnalysis, WordsmimirApiLog
)

with app.app_context():
    db.create_all()
    
    # Initialize wordsmimir service if API key is provided and not a placeholder
    wordsmimir_key = app.config['WORDSMIMIR_API_KEY']
    if wordsmimir_key and not wordsmimir_key.startswith('placeholder_'):
        try:
            init_wordsmimir_service(
                api_key=wordsmimir_key,
                base_url=app.config['WORDSMIMIR_BASE_URL']
            )
        except Exception as e:
            print(f"Warning: Failed to initialize Wordsmimir service: {e}")
    else:
        print("Warning: Wordsmimir API key not configured or using placeholder value")
    
    # Initialize multimedia service with safe upload directory
    upload_dir = os.environ.get('UPLOAD_DIR', '/tmp/elite_command_uploads')
    try:
        init_multimedia_service(upload_dir=upload_dir)
    except Exception as e:
        print(f"Warning: Failed to initialize multimedia service: {e}")

@app.route('/api/health')
def health():
    """Enhanced health check including psychological analysis capabilities."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Check psychological analysis tables
        from src.models.psychological import PsychologicalProfile
        profile_count = PsychologicalProfile.query.count()
        
        return jsonify({
            "status": "healthy",
            "version": "2.0.0",
            "database": "connected",
            "features": {
                "data_ingestion": "active",
                "intelligence_layer": "active", 
                "psychological_analysis": "active",
                "multimedia_analysis": "active",
                "wordsmimir_integration": "active" if app.config['WORDSMIMIR_API_KEY'] else "not_configured"
            },
            "statistics": {
                "psychological_profiles": profile_count
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({
                "message": "Elite Command Data API with Human Signal Intelligence",
                "version": "2.0.0",
                "features": [
                    "Unified Data Ingestion",
                    "Intelligent Normalization", 
                    "Executive Intelligence",
                    "Human Signal Intelligence (HSI)",
                    "Psychological Analysis",
                    "Multi-modal Communication Analysis",
                    "Audio/Video Processing",
                    "Real-time Multimedia Analysis"
                ],
                "endpoints": {
                    "health": "/api/health",
                    "api_info": "/api/info",
                    "psychological_health": "/api/psychological/health",
                    "multimedia_health": "/api/multimedia/health",
                    "profiling_health": "/api/profiling/health",
                    "hsi_health": "/api/hsi/health",
                    "hitl_health": "/api/hitl/health",
                    "templates_health": "/api/templates/health",
                    "confidence_health": "/api/confidence/health",
                    "corrections_health": "/api/corrections/health",
                    "ai_health": "/api/ai/health",
                    "text_analysis": "/api/psychological/analyze/text",
                    "audio_analysis": "/api/psychological/analyze/audio",
                    "video_analysis": "/api/psychological/analyze/video",
                    "multimodal_analysis": "/api/psychological/analyze/multimodal",
                    "audio_upload": "/api/multimedia/upload/audio",
                    "video_upload": "/api/multimedia/upload/video",
                    "multimodal_upload": "/api/multimedia/upload/multimodal",
                    "supported_formats": "/api/multimedia/supported_formats",
                    "comprehensive_profile": "/api/profiling/profile/comprehensive/{individual_id}",
                    "risk_assessment": "/api/profiling/profile/risk-assessment/{individual_id}",
                    "predictive_insights": "/api/profiling/profile/predictions/{individual_id}",
                    "profile_summary": "/api/profiling/profile/summary/{individual_id}",
                    "portfolio_overview": "/api/hsi/portfolio/overview",
                    "team_dynamics": "/api/hsi/team/dynamics",
                    "executive_alerts": "/api/hsi/alerts/executive-summary",
                    "strategic_insights": "/api/hsi/insights/strategic",
                    "validation_queue": "/api/hitl/queue",
                    "validation_dashboard": "/api/hitl/dashboard",
                    "validation_metrics": "/api/hitl/metrics",
                    "validation_rules": "/api/hitl/rules",
                    "business_model_templates": "/api/templates/business-models",
                    "metric_definitions": "/api/templates/metrics",
                    "template_normalization": "/api/templates/normalize",
                    "templates_dashboard": "/api/templates/dashboard",
                    "create_lineage": "/api/confidence/lineage",
                    "calculate_confidence": "/api/confidence/score",
                    "trace_lineage": "/api/confidence/lineage/trace/{data_point_id}",
                    "confidence_dashboard": "/api/confidence/company/{company_id}/dashboard",
                    "confidence_alerts": "/api/confidence/alerts",
                    "confidence_thresholds": "/api/confidence/thresholds",
                    "confidence_trends": "/api/confidence/analytics/trends",
                    "factor_analysis": "/api/confidence/factors/analysis",
                    "submit_correction": "/api/corrections/submit",
                    "approve_correction": "/api/corrections/approve/{correction_id}",
                    "implement_correction": "/api/corrections/implement/{correction_id}",
                    "corrections_queue": "/api/corrections/queue",
                    "create_annotation": "/api/corrections/annotations/create",
                    "get_annotations": "/api/corrections/annotations/{data_point_id}",
                    "submit_feedback": "/api/corrections/feedback/submit",
                    "correction_impact": "/api/corrections/impact/analysis",
                    "correction_workflows": "/api/corrections/workflows",
                    "corrections_dashboard": "/api/corrections/dashboard",
                    "ai_command": "/api/ai/command",
                    "ai_command_status": "/api/ai/command/{command_id}/status",
                    "ai_approve_command": "/api/ai/command/{command_id}/approve",
                    "ai_conversation": "/api/ai/conversation/{session_id}",
                    "ai_start_conversation": "/api/ai/conversation/start",
                    "ai_templates": "/api/ai/templates",
                    "ai_create_template": "/api/ai/templates/create",
                    "ai_automation_rules": "/api/ai/automation/rules",
                    "ai_create_rule": "/api/ai/automation/rules/create",
                    "ai_submit_feedback": "/api/ai/feedback/submit",
                    "ai_dashboard": "/api/ai/dashboard",
                    "ai_pending_commands": "/api/ai/commands/pending",
                    "ai_examples": "/api/ai/examples",
                    "ai_help": "/api/ai/help",
                    "security_health": "/api/security/health",
                    "generate_api_key": "/api/security/api-keys/generate",
                    "list_api_keys": "/api/security/api-keys",
                    "revoke_api_key": "/api/security/api-keys/{key_id}/revoke",
                    "security_events": "/api/security/events",
                    "rate_limit_rules": "/api/security/rate-limits/rules",
                    "create_rate_limit_rule": "/api/security/rate-limits/rules/create",
                    "monitoring_metrics": "/api/security/metrics",
                    "system_alerts": "/api/security/alerts",
                    "acknowledge_alert": "/api/security/alerts/{alert_id}/acknowledge",
                    "audit_logs": "/api/security/audit-logs",
                    "security_dashboard": "/api/security/dashboard",
                    "collect_system_metrics": "/api/security/system/collect-metrics",
                    "create_test_alert": "/api/security/test/create-alert"
                }
            })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
