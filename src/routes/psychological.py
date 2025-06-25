from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import uuid
import json
import logging
from typing import Dict, List, Optional, Any

from ..models.psychological import (
    PsychologicalProfile, CommunicationAnalysis, BehavioralPattern,
    PsychologicalAlert, GroupDynamicsAnalysis, WordsmimirApiLog,
    create_psychological_profile, get_or_create_profile,
    create_communication_analysis, create_psychological_alert,
    update_profile_from_analysis, db, AnalysisType
)
from ..services.wordsmimir import create_wordsmimir_service, AnalysisMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
psychological_bp = Blueprint('psychological', __name__, url_prefix='/api/psychological')

# Initialize wordsmimir service (will be configured in main app)
wordsmimir_service = None

def init_wordsmimir_service(api_key: str, base_url: Optional[str] = None):
    """Initialize the wordsmimir service with configuration."""
    global wordsmimir_service
    wordsmimir_service = create_wordsmimir_service(api_key, base_url)

@psychological_bp.route('/analyze/text', methods=['POST'])
def analyze_text():
    """
    Analyze text content for psychological insights.
    
    Expected JSON payload:
    {
        "text": "Text content to analyze",
        "individual_id": "unique_individual_identifier",
        "communication_id": "unique_communication_identifier",
        "communication_type": "email|meeting|chat|document",
        "context": {
            "meeting_type": "board_meeting",
            "participants": ["id1", "id2"],
            "timestamp": "2024-01-01T10:00:00Z"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['text', 'individual_id', 'communication_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "status": "error"
                }), 400
        
        text = data['text']
        individual_id = data['individual_id']
        communication_id = data['communication_id']
        communication_type = data.get('communication_type', 'text')
        context = data.get('context', {})
        
        # Ensure wordsmimir service is initialized
        if not wordsmimir_service:
            return jsonify({
                "error": "Wordsmimir service not initialized",
                "status": "error"
            }), 500
        
        # Perform text analysis using wordsmimir
        analysis_results = wordsmimir_service.analyze_text(
            text=text,
            individual_id=individual_id,
            communication_id=communication_id,
            context=context
        )
        
        # Check for analysis errors
        if analysis_results.get('error'):
            return jsonify({
                "error": "Analysis failed",
                "details": analysis_results.get('error_message'),
                "status": "error"
            }), 500
        
        # Create or update psychological profile
        profile = get_or_create_profile(individual_id)
        
        # Store analysis results in database
        communication_analysis = create_communication_analysis(
            communication_id=communication_id,
            individual_id=individual_id,
            analysis_type=AnalysisType.TEXT,
            communication_type=communication_type,
            timestamp=datetime.utcnow(),
            text_content=text,
            linguistic_complexity=analysis_results.get('linguistic_complexity'),
            emotional_valence=analysis_results.get('emotional_valence'),
            cognitive_load_score=analysis_results.get('cognitive_load_score'),
            deception_indicators=analysis_results.get('deception_indicators'),
            stress_markers=analysis_results.get('stress_markers'),
            authenticity_score=analysis_results.get('authenticity_score'),
            overall_confidence=analysis_results.get('confidence'),
            wordsmimir_raw_response=analysis_results,
            wordsmimir_confidence=analysis_results.get('confidence'),
            wordsmimir_analysis_version=analysis_results.get('wordsmimir_version'),
            processing_status='completed'
        )
        
        # Update psychological profile with new analysis
        update_profile_from_analysis(profile.id, analysis_results)
        
        # Generate psychological alerts if needed
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
        
        # Prepare response
        response_data = {
            "status": "success",
            "analysis_id": communication_analysis.id,
            "communication_id": communication_id,
            "individual_id": individual_id,
            "analysis_results": {
                "linguistic_complexity": analysis_results.get('linguistic_complexity'),
                "emotional_valence": analysis_results.get('emotional_valence'),
                "cognitive_load_score": analysis_results.get('cognitive_load_score'),
                "authenticity_score": analysis_results.get('authenticity_score'),
                "stress_level": len(analysis_results.get('stress_markers', [])),
                "deception_indicators_count": len(analysis_results.get('deception_indicators', [])),
                "confidence": analysis_results.get('confidence')
            },
            "alerts_generated": len(alerts),
            "profile_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Text analysis endpoint error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@psychological_bp.route('/analyze/audio', methods=['POST'])
def analyze_audio():
    """
    Analyze audio content for psychological insights.
    
    Expected JSON payload:
    {
        "audio_url": "URL to audio file",
        "individual_id": "unique_individual_identifier",
        "communication_id": "unique_communication_identifier",
        "duration_seconds": 300,
        "context": {
            "meeting_type": "negotiation",
            "participants": ["id1", "id2"]
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['audio_url', 'individual_id', 'communication_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "status": "error"
                }), 400
        
        audio_url = data['audio_url']
        individual_id = data['individual_id']
        communication_id = data['communication_id']
        duration_seconds = data.get('duration_seconds')
        context = data.get('context', {})
        
        # Ensure wordsmimir service is initialized
        if not wordsmimir_service:
            return jsonify({
                "error": "Wordsmimir service not initialized",
                "status": "error"
            }), 500
        
        # Perform audio analysis using wordsmimir
        analysis_results = wordsmimir_service.analyze_audio(
            audio_url=audio_url,
            individual_id=individual_id,
            communication_id=communication_id,
            context=context
        )
        
        # Check for analysis errors
        if analysis_results.get('error'):
            return jsonify({
                "error": "Audio analysis failed",
                "details": analysis_results.get('error_message'),
                "status": "error"
            }), 500
        
        # Create or update psychological profile
        profile = get_or_create_profile(individual_id)
        
        # Store analysis results in database
        communication_analysis = create_communication_analysis(
            communication_id=communication_id,
            individual_id=individual_id,
            analysis_type=AnalysisType.AUDIO,
            communication_type='audio',
            timestamp=datetime.utcnow(),
            duration_seconds=duration_seconds,
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
        
        # Update psychological profile with new analysis
        update_profile_from_analysis(profile.id, analysis_results)
        
        # Generate psychological alerts if needed
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
        
        # Prepare response
        response_data = {
            "status": "success",
            "analysis_id": communication_analysis.id,
            "communication_id": communication_id,
            "individual_id": individual_id,
            "analysis_results": {
                "speech_rate": analysis_results.get('speech_rate'),
                "pitch_statistics": {
                    "mean": analysis_results.get('pitch_mean'),
                    "variance": analysis_results.get('pitch_variance')
                },
                "voice_stress_score": analysis_results.get('voice_stress_score'),
                "filler_word_count": analysis_results.get('filler_word_count'),
                "confidence": analysis_results.get('confidence')
            },
            "alerts_generated": len(alerts),
            "profile_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Audio analysis endpoint error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@psychological_bp.route('/analyze/video', methods=['POST'])
def analyze_video():
    """
    Analyze video content for psychological insights.
    
    Expected JSON payload:
    {
        "video_url": "URL to video file",
        "individual_id": "unique_individual_identifier",
        "communication_id": "unique_communication_identifier",
        "duration_seconds": 600,
        "context": {
            "meeting_type": "presentation",
            "audience_size": 10
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['video_url', 'individual_id', 'communication_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "status": "error"
                }), 400
        
        video_url = data['video_url']
        individual_id = data['individual_id']
        communication_id = data['communication_id']
        duration_seconds = data.get('duration_seconds')
        context = data.get('context', {})
        
        # Ensure wordsmimir service is initialized
        if not wordsmimir_service:
            return jsonify({
                "error": "Wordsmimir service not initialized",
                "status": "error"
            }), 500
        
        # Perform video analysis using wordsmimir
        analysis_results = wordsmimir_service.analyze_video(
            video_url=video_url,
            individual_id=individual_id,
            communication_id=communication_id,
            context=context
        )
        
        # Check for analysis errors
        if analysis_results.get('error'):
            return jsonify({
                "error": "Video analysis failed",
                "details": analysis_results.get('error_message'),
                "status": "error"
            }), 500
        
        # Create or update psychological profile
        profile = get_or_create_profile(individual_id)
        
        # Store analysis results in database
        communication_analysis = create_communication_analysis(
            communication_id=communication_id,
            individual_id=individual_id,
            analysis_type=AnalysisType.VIDEO,
            communication_type='video',
            timestamp=datetime.utcnow(),
            duration_seconds=duration_seconds,
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
        
        # Update psychological profile with new analysis
        update_profile_from_analysis(profile.id, analysis_results)
        
        # Generate psychological alerts if needed
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
        
        # Prepare response
        response_data = {
            "status": "success",
            "analysis_id": communication_analysis.id,
            "communication_id": communication_id,
            "individual_id": individual_id,
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
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Video analysis endpoint error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@psychological_bp.route('/analyze/multimodal', methods=['POST'])
def analyze_multimodal():
    """
    Perform comprehensive multi-modal psychological analysis.
    
    Expected JSON payload:
    {
        "text": "Text content",
        "audio_url": "URL to audio file (optional)",
        "video_url": "URL to video file (optional)",
        "individual_id": "unique_individual_identifier",
        "communication_id": "unique_communication_identifier",
        "context": {
            "meeting_type": "board_meeting",
            "importance": "high"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['individual_id', 'communication_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "status": "error"
                }), 400
        
        # At least one content type must be provided
        if not any([data.get('text'), data.get('audio_url'), data.get('video_url')]):
            return jsonify({
                "error": "At least one content type (text, audio_url, or video_url) must be provided",
                "status": "error"
            }), 400
        
        text = data.get('text')
        audio_url = data.get('audio_url')
        video_url = data.get('video_url')
        individual_id = data['individual_id']
        communication_id = data['communication_id']
        context = data.get('context', {})
        
        # Ensure wordsmimir service is initialized
        if not wordsmimir_service:
            return jsonify({
                "error": "Wordsmimir service not initialized",
                "status": "error"
            }), 500
        
        # Perform multimodal analysis using wordsmimir
        analysis_results = wordsmimir_service.analyze_multimodal(
            text=text,
            audio_url=audio_url,
            video_url=video_url,
            individual_id=individual_id,
            communication_id=communication_id,
            context=context
        )
        
        # Check for analysis errors
        if analysis_results.get('error'):
            return jsonify({
                "error": "Multimodal analysis failed",
                "details": analysis_results.get('error_message'),
                "status": "error"
            }), 500
        
        # Create or update psychological profile
        profile = get_or_create_profile(individual_id)
        
        # Extract individual modality results
        text_analysis = analysis_results.get('text_analysis', {})
        audio_analysis = analysis_results.get('audio_analysis', {})
        video_analysis = analysis_results.get('video_analysis', {})
        
        # Store comprehensive analysis results in database
        communication_analysis = create_communication_analysis(
            communication_id=communication_id,
            individual_id=individual_id,
            analysis_type=AnalysisType.MULTIMODAL,
            communication_type='multimodal',
            timestamp=datetime.utcnow(),
            text_content=text,
            # Text analysis fields
            linguistic_complexity=text_analysis.get('linguistic_complexity'),
            emotional_valence=text_analysis.get('emotional_valence'),
            cognitive_load_score=text_analysis.get('cognitive_load_score'),
            deception_indicators=text_analysis.get('deception_indicators'),
            stress_markers=text_analysis.get('stress_markers'),
            # Audio analysis fields
            speech_rate=audio_analysis.get('speech_rate'),
            pitch_mean=audio_analysis.get('pitch_mean'),
            pitch_variance=audio_analysis.get('pitch_variance'),
            volume_variance=audio_analysis.get('volume_variance'),
            pause_frequency=audio_analysis.get('pause_frequency'),
            filler_word_count=audio_analysis.get('filler_word_count'),
            voice_stress_score=audio_analysis.get('voice_stress_score'),
            # Video analysis fields
            facial_expressions=video_analysis.get('facial_expressions'),
            micro_expressions=video_analysis.get('micro_expressions'),
            gaze_patterns=video_analysis.get('gaze_patterns'),
            attention_score=video_analysis.get('attention_score'),
            visual_stress_indicators=video_analysis.get('visual_stress_indicators'),
            # Cross-modal analysis
            authenticity_score=analysis_results.get('authenticity_score'),
            congruence_score=analysis_results.get('congruence_score'),
            overall_confidence=analysis_results.get('overall_confidence'),
            wordsmimir_raw_response=analysis_results,
            wordsmimir_confidence=analysis_results.get('overall_confidence'),
            wordsmimir_analysis_version=analysis_results.get('wordsmimir_version'),
            processing_status='completed'
        )
        
        # Update psychological profile with comprehensive analysis
        update_profile_from_analysis(profile.id, analysis_results)
        
        # Generate psychological alerts based on comprehensive analysis
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
                confidence_score=analysis_results.get('overall_confidence', 0.0),
                urgency_score=0.8 if alert_data['severity'] == 'high' else 0.5,
                risk_level=alert_data['severity'],
                trigger_data=analysis_results
            )
        
        # Prepare comprehensive response
        response_data = {
            "status": "success",
            "analysis_id": communication_analysis.id,
            "communication_id": communication_id,
            "individual_id": individual_id,
            "analysis_results": {
                "authenticity_score": analysis_results.get('authenticity_score'),
                "congruence_score": analysis_results.get('congruence_score'),
                "overall_confidence": analysis_results.get('overall_confidence'),
                "modalities_analyzed": {
                    "text": bool(text),
                    "audio": bool(audio_url),
                    "video": bool(video_url)
                },
                "integrated_insights": analysis_results.get('integrated_insights', []),
                "cross_modal_analysis": {
                    "congruence_assessment": analysis_results.get('congruence_score'),
                    "authenticity_assessment": analysis_results.get('authenticity_score')
                }
            },
            "alerts_generated": len(alerts),
            "profile_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Multimodal analysis endpoint error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@psychological_bp.route('/profile/<individual_id>', methods=['GET'])
def get_psychological_profile(individual_id):
    """
    Retrieve comprehensive psychological profile for an individual.
    """
    try:
        profile = PsychologicalProfile.query.filter_by(individual_id=individual_id).first()
        
        if not profile:
            return jsonify({
                "error": "Profile not found",
                "individual_id": individual_id,
                "status": "error"
            }), 404
        
        # Get recent communications analysis
        recent_analyses = CommunicationAnalysis.query.filter_by(
            individual_id=individual_id
        ).order_by(CommunicationAnalysis.timestamp.desc()).limit(10).all()
        
        # Get behavioral patterns
        patterns = BehavioralPattern.query.filter_by(
            individual_id=individual_id
        ).order_by(BehavioralPattern.last_observed.desc()).limit(5).all()
        
        # Get active alerts
        active_alerts = PsychologicalAlert.query.filter_by(
            individual_id=individual_id,
            status='active'
        ).order_by(PsychologicalAlert.created_at.desc()).all()
        
        # Prepare response
        response_data = {
            "individual_id": individual_id,
            "profile": {
                "name": profile.name,
                "email": profile.email,
                "personality_assessment": {
                    "openness": profile.openness_score,
                    "conscientiousness": profile.conscientiousness_score,
                    "extraversion": profile.extraversion_score,
                    "agreeableness": profile.agreeableness_score,
                    "neuroticism": profile.neuroticism_score
                },
                "communication_style": profile.communication_style,
                "stress_response_pattern": profile.stress_response_pattern,
                "authenticity_baseline": profile.authenticity_baseline,
                "behavioral_baselines": {
                    "speech_rate": profile.baseline_speech_rate,
                    "pitch_variance": profile.baseline_pitch_variance,
                    "emotional_state": profile.baseline_emotional_state
                },
                "profile_confidence": profile.profile_confidence,
                "analysis_count": profile.analysis_count,
                "last_updated": profile.last_updated.isoformat() if profile.last_updated else None
            },
            "recent_analyses": [
                {
                    "communication_id": analysis.communication_id,
                    "analysis_type": analysis.analysis_type.value,
                    "timestamp": analysis.timestamp.isoformat(),
                    "authenticity_score": analysis.authenticity_score,
                    "confidence": analysis.overall_confidence
                }
                for analysis in recent_analyses
            ],
            "behavioral_patterns": [
                {
                    "pattern_type": pattern.pattern_type,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence_score,
                    "last_observed": pattern.last_observed.isoformat()
                }
                for pattern in patterns
            ],
            "active_alerts": [
                {
                    "alert_type": alert.alert_type,
                    "severity": alert.severity_level,
                    "title": alert.title,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in active_alerts
            ],
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@psychological_bp.route('/alerts/<individual_id>', methods=['GET'])
def get_psychological_alerts(individual_id):
    """
    Retrieve psychological alerts for an individual.
    """
    try:
        # Get query parameters
        status = request.args.get('status', 'active')
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 50))
        
        # Build query
        query = PsychologicalAlert.query.filter_by(individual_id=individual_id)
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        if severity:
            query = query.filter_by(severity_level=severity)
        
        alerts = query.order_by(PsychologicalAlert.created_at.desc()).limit(limit).all()
        
        # Prepare response
        response_data = {
            "individual_id": individual_id,
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity_level": alert.severity_level,
                    "title": alert.title,
                    "description": alert.description,
                    "recommendations": alert.recommendations,
                    "confidence_score": alert.confidence_score,
                    "urgency_score": alert.urgency_score,
                    "risk_level": alert.risk_level,
                    "status": alert.status,
                    "created_at": alert.created_at.isoformat(),
                    "communication_id": alert.communication_id
                }
                for alert in alerts
            ],
            "total_count": len(alerts),
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Alerts retrieval error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@psychological_bp.route('/patterns/<individual_id>', methods=['GET'])
def get_behavioral_patterns(individual_id):
    """
    Retrieve behavioral patterns for an individual.
    """
    try:
        # Get query parameters
        pattern_type = request.args.get('pattern_type')
        days = int(request.args.get('days', 30))
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = BehavioralPattern.query.filter_by(individual_id=individual_id)
        query = query.filter(BehavioralPattern.last_observed >= start_date)
        
        if pattern_type:
            query = query.filter_by(pattern_type=pattern_type)
        
        patterns = query.order_by(BehavioralPattern.confidence_score.desc()).all()
        
        # Prepare response
        response_data = {
            "individual_id": individual_id,
            "time_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "patterns": [
                {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "pattern_category": pattern.pattern_category,
                    "description": pattern.pattern_description,
                    "frequency": pattern.frequency,
                    "confidence_score": pattern.confidence_score,
                    "significance_level": pattern.significance_level,
                    "trigger_contexts": pattern.trigger_contexts,
                    "first_observed": pattern.first_observed.isoformat(),
                    "last_observed": pattern.last_observed.isoformat(),
                    "observation_count": pattern.observation_count
                }
                for pattern in patterns
            ],
            "total_count": len(patterns),
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Patterns retrieval error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@psychological_bp.route('/health', methods=['GET'])
def psychological_health():
    """
    Health check endpoint for psychological analysis service.
    """
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Check wordsmimir service status
        wordsmimir_status = "initialized" if wordsmimir_service else "not_initialized"
        
        # Get basic statistics
        total_profiles = PsychologicalProfile.query.count()
        total_analyses = CommunicationAnalysis.query.count()
        active_alerts = PsychologicalAlert.query.filter_by(status='active').count()
        
        response_data = {
            "status": "healthy",
            "wordsmimir_service": wordsmimir_status,
            "database": "connected",
            "statistics": {
                "total_profiles": total_profiles,
                "total_analyses": total_analyses,
                "active_alerts": active_alerts
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

