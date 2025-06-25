from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..models.psychological import (
    create_communication_analysis, get_or_create_profile,
    create_psychological_alert, update_profile_from_analysis,
    AnalysisType, db
)
from ..services.multimedia import create_multimedia_service, MediaType

# Import wordsmimir service access function
def get_wordsmimir_service():
    """Get the initialized wordsmimir service."""
    try:
        from ..routes.psychological import wordsmimir_service
        return wordsmimir_service
    except ImportError:
        return None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
multimedia_bp = Blueprint('multimedia', __name__, url_prefix='/api/multimedia')

# Initialize multimedia service
multimedia_service = None

def init_multimedia_service(upload_dir: str = "/tmp/elite_command_uploads", 
                          max_file_size: int = 500 * 1024 * 1024):
    """Initialize the multimedia analysis service."""
    global multimedia_service
    multimedia_service = create_multimedia_service(upload_dir, max_file_size)

@multimedia_bp.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Upload and analyze audio file for psychological insights."""
    try:
        # Check services
        if not multimedia_service:
            return jsonify({"error": "Multimedia service not initialized", "status": "error"}), 500
        
        wordsmimir_service = get_wordsmimir_service()
        if not wordsmimir_service:
            return jsonify({"error": "Wordsmimir service not initialized", "status": "error"}), 500
        
        # Validate form data
        if 'audio_file' not in request.files:
            return jsonify({"error": "No audio file provided", "status": "error"}), 400
        
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            return jsonify({"error": "No file selected", "status": "error"}), 400
        
        # Get form parameters
        individual_id = request.form.get('individual_id')
        communication_id = request.form.get('communication_id', str(uuid.uuid4()))
        communication_type = request.form.get('communication_type', 'audio_call')
        context_str = request.form.get('context', '{}')
        
        if not individual_id:
            return jsonify({"error": "individual_id is required", "status": "error"}), 400
        
        # Parse context
        try:
            import json
            context = json.loads(context_str)
        except json.JSONDecodeError:
            context = {}
        
        # Save uploaded file
        filename = secure_filename(audio_file.filename)
        file_extension = os.path.splitext(filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(multimedia_service.upload_dir, unique_filename)
        
        audio_file.save(file_path)
        
        # Process the audio file
        processing_result = multimedia_service.process_uploaded_file(
            file_path=file_path,
            media_type=MediaType.AUDIO,
            individual_id=individual_id,
            communication_id=communication_id
        )
        
        if not processing_result.get('success'):
            if os.path.exists(file_path):
                os.unlink(file_path)
            return jsonify({
                "error": "Audio processing failed",
                "details": processing_result.get('error'),
                "status": "error"
            }), 500
        
        # Perform psychological analysis
        analysis_results = wordsmimir_service.analyze_audio(
            audio_url=processing_result['public_url'],
            individual_id=individual_id,
            communication_id=communication_id,
            context=context
        )
        
        if analysis_results.get('error'):
            if os.path.exists(file_path):
                os.unlink(file_path)
            return jsonify({
                "error": "Psychological analysis failed",
                "details": analysis_results.get('error_message'),
                "status": "error"
            }), 500
        
        # Store results
        profile = get_or_create_profile(individual_id)
        communication_analysis = create_communication_analysis(
            communication_id=communication_id,
            individual_id=individual_id,
            analysis_type=AnalysisType.AUDIO,
            communication_type=communication_type,
            timestamp=datetime.utcnow(),
            duration_seconds=processing_result['metadata'].get('duration_seconds'),
            speech_rate=analysis_results.get('speech_rate'),
            pitch_mean=analysis_results.get('pitch_mean'),
            pitch_variance=analysis_results.get('pitch_variance'),
            volume_variance=analysis_results.get('volume_variance'),
            pause_frequency=analysis_results.get('pause_frequency'),
            filler_word_count=analysis_results.get('filler_word_count'),
            voice_stress_score=analysis_results.get('voice_stress_score'),
            overall_confidence=analysis_results.get('confidence'),
            wordsmimir_raw_response=analysis_results,
            wordsmimir_confidence=analysis_results.get('confidence'),
            wordsmimir_analysis_version=analysis_results.get('wordsmimir_version'),
            processing_status='completed'
        )
        
        update_profile_from_analysis(profile.id, analysis_results)
        
        # Generate alerts
        alerts = wordsmimir_service.generate_psychological_alerts(analysis_results, individual_id)
        for alert_data in alerts:
            create_psychological_alert(
                individual_id=individual_id,
                communication_id=communication_id,
                alert_type=alert_data['type'],
                severity_level=alert_data['severity'],
                title=alert_data['title'],
                description=alert_data['description'],
                recommendations=alert_data.get('recommendations', []),
                confidence_score=analysis_results.get('confidence', 0.0),
                urgency_score=0.8 if alert_data['severity'] == 'high' else 0.5,
                risk_level=alert_data['severity'],
                trigger_data=analysis_results
            )
        
        # Clean up
        if os.path.exists(file_path):
            os.unlink(file_path)
        
        return jsonify({
            "status": "success",
            "analysis_id": communication_analysis.id,
            "communication_id": communication_id,
            "individual_id": individual_id,
            "file_metadata": processing_result['metadata'],
            "analysis_results": {
                "speech_rate": analysis_results.get('speech_rate'),
                "voice_stress_score": analysis_results.get('voice_stress_score'),
                "pitch_statistics": {
                    "mean": analysis_results.get('pitch_mean'),
                    "variance": analysis_results.get('pitch_variance')
                },
                "filler_word_count": analysis_results.get('filler_word_count'),
                "confidence": analysis_results.get('confidence')
            },
            "alerts_generated": len(alerts),
            "profile_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Audio upload endpoint error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e), "status": "error"}), 500

@multimedia_bp.route('/upload/video', methods=['POST'])
def upload_video():
    """Upload and analyze video file for psychological insights."""
    try:
        # Check services
        if not multimedia_service:
            return jsonify({"error": "Multimedia service not initialized", "status": "error"}), 500
        
        wordsmimir_service = get_wordsmimir_service()
        if not wordsmimir_service:
            return jsonify({"error": "Wordsmimir service not initialized", "status": "error"}), 500
        
        # Validate form data
        if 'video_file' not in request.files:
            return jsonify({"error": "No video file provided", "status": "error"}), 400
        
        video_file = request.files['video_file']
        if video_file.filename == '':
            return jsonify({"error": "No file selected", "status": "error"}), 400
        
        # Get form parameters
        individual_id = request.form.get('individual_id')
        communication_id = request.form.get('communication_id', str(uuid.uuid4()))
        communication_type = request.form.get('communication_type', 'video_meeting')
        context_str = request.form.get('context', '{}')
        
        if not individual_id:
            return jsonify({"error": "individual_id is required", "status": "error"}), 400
        
        # Parse context
        try:
            import json
            context = json.loads(context_str)
        except json.JSONDecodeError:
            context = {}
        
        # Save uploaded file
        filename = secure_filename(video_file.filename)
        file_extension = os.path.splitext(filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(multimedia_service.upload_dir, unique_filename)
        
        video_file.save(file_path)
        
        # Process the video file
        processing_result = multimedia_service.process_uploaded_file(
            file_path=file_path,
            media_type=MediaType.VIDEO,
            individual_id=individual_id,
            communication_id=communication_id
        )
        
        if not processing_result.get('success'):
            if os.path.exists(file_path):
                os.unlink(file_path)
            return jsonify({
                "error": "Video processing failed",
                "details": processing_result.get('error'),
                "status": "error"
            }), 500
        
        # Perform psychological analysis
        analysis_results = wordsmimir_service.analyze_video(
            video_url=processing_result['public_url'],
            individual_id=individual_id,
            communication_id=communication_id,
            context=context
        )
        
        if analysis_results.get('error'):
            if os.path.exists(file_path):
                os.unlink(file_path)
            return jsonify({
                "error": "Psychological analysis failed",
                "details": analysis_results.get('error_message'),
                "status": "error"
            }), 500
        
        # Store results
        profile = get_or_create_profile(individual_id)
        communication_analysis = create_communication_analysis(
            communication_id=communication_id,
            individual_id=individual_id,
            analysis_type=AnalysisType.VIDEO,
            communication_type=communication_type,
            timestamp=datetime.utcnow(),
            duration_seconds=processing_result['metadata'].get('duration_seconds'),
            facial_expressions=analysis_results.get('facial_expressions'),
            micro_expressions=analysis_results.get('micro_expressions'),
            gaze_patterns=analysis_results.get('gaze_patterns'),
            attention_score=analysis_results.get('attention_score'),
            visual_stress_indicators=analysis_results.get('visual_stress_indicators'),
            overall_confidence=analysis_results.get('confidence'),
            wordsmimir_raw_response=analysis_results,
            wordsmimir_confidence=analysis_results.get('confidence'),
            wordsmimir_analysis_version=analysis_results.get('wordsmimir_version'),
            processing_status='completed'
        )
        
        update_profile_from_analysis(profile.id, analysis_results)
        
        # Generate alerts
        alerts = wordsmimir_service.generate_psychological_alerts(analysis_results, individual_id)
        for alert_data in alerts:
            create_psychological_alert(
                individual_id=individual_id,
                communication_id=communication_id,
                alert_type=alert_data['type'],
                severity_level=alert_data['severity'],
                title=alert_data['title'],
                description=alert_data['description'],
                recommendations=alert_data.get('recommendations', []),
                confidence_score=analysis_results.get('confidence', 0.0),
                urgency_score=0.8 if alert_data['severity'] == 'high' else 0.5,
                risk_level=alert_data['severity'],
                trigger_data=analysis_results
            )
        
        # Clean up
        if os.path.exists(file_path):
            os.unlink(file_path)
        
        return jsonify({
            "status": "success",
            "analysis_id": communication_analysis.id,
            "communication_id": communication_id,
            "individual_id": individual_id,
            "file_metadata": processing_result['metadata'],
            "analysis_results": {
                "facial_expressions": analysis_results.get('facial_expressions'),
                "micro_expressions_count": len(analysis_results.get('micro_expressions', [])),
                "attention_score": analysis_results.get('attention_score'),
                "stress_indicators_count": len(analysis_results.get('visual_stress_indicators', [])),
                "confidence": analysis_results.get('confidence')
            },
            "alerts_generated": len(alerts),
            "profile_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Video upload endpoint error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e), "status": "error"}), 500

@multimedia_bp.route('/supported_formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported audio and video formats."""
    return jsonify({
        "audio_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"],
        "video_formats": [".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"],
        "max_file_size_mb": 500,
        "recommended_formats": {
            "audio": ".wav (for best quality)",
            "video": ".mp4 (for best compatibility)"
        },
        "status": "success"
    })

@multimedia_bp.route('/health', methods=['GET'])
def multimedia_health():
    """Health check for multimedia analysis service."""
    try:
        wordsmimir_service = get_wordsmimir_service()
        health_status = {
            "status": "healthy",
            "multimedia_service": "initialized" if multimedia_service else "not_initialized",
            "wordsmimir_service": "initialized" if wordsmimir_service else "not_initialized",
            "upload_directory": multimedia_service.upload_dir if multimedia_service else "not_configured",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check if upload directory is writable
        if multimedia_service:
            try:
                test_file = os.path.join(multimedia_service.upload_dir, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.unlink(test_file)
                health_status["upload_directory_writable"] = True
            except Exception:
                health_status["upload_directory_writable"] = False
                health_status["status"] = "degraded"
        
        return jsonify(health_status), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

