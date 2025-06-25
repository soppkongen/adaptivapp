"""
AURA Biometric API Routes

API endpoints for handling biometric data ingestion, processing, and adaptation
in the Elite Command Data API with AURA integration.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
import json
import uuid

from ..services.biometric_processor import biometric_processor, BiometricReading, AdaptationDecision
from ..models.biometric import (
    BiometricSession, BiometricDataPoint, InterfaceAdaptation, 
    UserBiometricProfile, AdaptationRule, BiometricAlert, BiometricCalibration,
    BiometricDataType, AdaptationTrigger, AdaptationType, db
)

biometric_bp = Blueprint('biometric', __name__, url_prefix='/api/biometric')
logger = logging.getLogger(__name__)

@biometric_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for AURA biometric system"""
    try:
        # Test database connectivity
        session_count = BiometricSession.query.count()
        profile_count = UserBiometricProfile.query.count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'AURA Biometric Processing System',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'total_sessions': session_count,
                'user_profiles': profile_count,
                'processor_status': 'active'
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@biometric_bp.route('/session/start', methods=['POST'])
def start_biometric_session():
    """Start a new biometric monitoring session"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'user_id' not in data:
            return jsonify({'error': 'Missing required field: user_id'}), 400
        
        user_id = data['user_id']
        device_info = data.get('device_info', {})
        privacy_settings = data.get('privacy_settings', {})
        
        # Create new session
        session_id = str(uuid.uuid4())
        session = BiometricSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            device_info=device_info,
            privacy_settings=privacy_settings,
            session_quality=0.0,
            total_adaptations=0
        )
        
        db.session.add(session)
        
        # Create or update user profile
        user_profile = UserBiometricProfile.query.filter_by(user_id=user_id).first()
        if not user_profile:
            user_profile = UserBiometricProfile(
                user_id=user_id,
                adaptation_sensitivity=0.5,
                privacy_level='standard',
                total_sessions=0,
                total_adaptations=0,
                learning_confidence=0.0
            )
            db.session.add(user_profile)
        
        db.session.commit()
        
        return jsonify({
            'session_id': session_id,
            'status': 'started',
            'timestamp': datetime.utcnow().isoformat(),
            'user_profile': {
                'adaptation_sensitivity': user_profile.adaptation_sensitivity,
                'privacy_level': user_profile.privacy_level,
                'learning_confidence': user_profile.learning_confidence
            }
        })
        
    except Exception as e:
        logger.error(f"Error starting biometric session: {str(e)}")
        return jsonify({'error': 'Failed to start session'}), 500

@biometric_bp.route('/session/<session_id>/end', methods=['POST'])
def end_biometric_session(session_id):
    """End a biometric monitoring session"""
    try:
        session = BiometricSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.end_time = datetime.utcnow()
        
        # Calculate session quality
        data_points = BiometricDataPoint.query.filter_by(session_id=session_id).all()
        if data_points:
            avg_quality = sum(dp.data_quality for dp in data_points) / len(data_points)
            session.session_quality = avg_quality
        
        # Update user profile
        user_profile = UserBiometricProfile.query.filter_by(user_id=session.user_id).first()
        if user_profile:
            user_profile.total_sessions += 1
            user_profile.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'ended',
            'session_duration': (session.end_time - session.start_time).total_seconds(),
            'data_points_collected': len(data_points),
            'session_quality': session.session_quality,
            'total_adaptations': session.total_adaptations
        })
        
    except Exception as e:
        logger.error(f"Error ending biometric session: {str(e)}")
        return jsonify({'error': 'Failed to end session'}), 500

@biometric_bp.route('/data/ingest', methods=['POST'])
def ingest_biometric_data():
    """Ingest biometric data and trigger adaptations"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['session_id', 'timestamp', 'facial_expressions', 'gaze_position']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        session_id = data['session_id']
        
        # Verify session exists
        session = BiometricSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Create biometric reading
        reading = BiometricReading(
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
            facial_expressions=data['facial_expressions'],
            gaze_position=tuple(data['gaze_position']),
            pupil_diameter=data.get('pupil_diameter', 0.5),
            blink_rate=data.get('blink_rate', 0.15),
            attention_score=data.get('attention_score', 0.5),
            stress_level=data.get('stress_level', 0.3),
            cognitive_load=data.get('cognitive_load', 0.4),
            confidence=data.get('confidence', 0.8)
        )
        
        # Process biometric data and get adaptation decisions
        adaptation_decisions = biometric_processor.process_biometric_data(session_id, reading)
        
        # Apply adaptations
        applied_adaptations = []
        for decision in adaptation_decisions:
            adaptation = self._apply_adaptation(session_id, decision)
            if adaptation:
                applied_adaptations.append({
                    'id': adaptation.id,
                    'type': adaptation.adaptation_type,
                    'trigger': adaptation.trigger_type,
                    'parameters': adaptation.adaptation_parameters,
                    'confidence': adaptation.trigger_confidence
                })
        
        # Update session adaptation count
        session.total_adaptations += len(applied_adaptations)
        db.session.commit()
        
        return jsonify({
            'status': 'processed',
            'adaptations_applied': len(applied_adaptations),
            'adaptations': applied_adaptations,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error ingesting biometric data: {str(e)}")
        return jsonify({'error': 'Failed to process biometric data'}), 500

def _apply_adaptation(session_id: str, decision: AdaptationDecision) -> InterfaceAdaptation:
    """Apply an interface adaptation based on decision"""
    try:
        session = BiometricSession.query.filter_by(session_id=session_id).first()
        
        adaptation = InterfaceAdaptation(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            trigger_type=decision.trigger_type.value,
            trigger_data={'confidence': decision.confidence, 'urgency': decision.urgency},
            trigger_confidence=decision.confidence,
            adaptation_type=decision.adaptation_type.value,
            adaptation_parameters=decision.parameters,
            previous_state={},  # Would be populated with current interface state
            new_state=decision.parameters,
            effectiveness_score=0.0,  # Will be updated based on user response
            adaptation_source='biometric'
        )
        
        db.session.add(adaptation)
        db.session.commit()
        
        return adaptation
        
    except Exception as e:
        logger.error(f"Error applying adaptation: {str(e)}")
        return None

@biometric_bp.route('/adaptations/<session_id>', methods=['GET'])
def get_session_adaptations(session_id):
    """Get adaptations for a specific session"""
    try:
        adaptations = InterfaceAdaptation.query.filter_by(session_id=session_id).all()
        
        adaptation_list = []
        for adaptation in adaptations:
            adaptation_list.append({
                'id': adaptation.id,
                'timestamp': adaptation.timestamp.isoformat(),
                'trigger_type': adaptation.trigger_type,
                'adaptation_type': adaptation.adaptation_type,
                'parameters': adaptation.adaptation_parameters,
                'confidence': adaptation.trigger_confidence,
                'effectiveness': adaptation.effectiveness_score,
                'active': not adaptation.reverted
            })
        
        return jsonify({
            'session_id': session_id,
            'adaptations': adaptation_list,
            'total_count': len(adaptation_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting session adaptations: {str(e)}")
        return jsonify({'error': 'Failed to get adaptations'}), 500

@biometric_bp.route('/adaptation/<int:adaptation_id>/feedback', methods=['POST'])
def provide_adaptation_feedback(adaptation_id):
    """Provide feedback on adaptation effectiveness"""
    try:
        data = request.get_json()
        
        adaptation = InterfaceAdaptation.query.get(adaptation_id)
        if not adaptation:
            return jsonify({'error': 'Adaptation not found'}), 404
        
        # Update adaptation with feedback
        adaptation.user_feedback = data.get('feedback', 'neutral')  # positive, negative, neutral
        adaptation.effectiveness_score = data.get('effectiveness_score', 0.5)
        adaptation.user_response = data.get('biometric_response', {})
        
        if data.get('revert', False):
            adaptation.reverted = True
            adaptation.revert_reason = data.get('revert_reason', 'user_request')
        
        db.session.commit()
        
        return jsonify({
            'status': 'feedback_recorded',
            'adaptation_id': adaptation_id,
            'feedback': adaptation.user_feedback,
            'effectiveness': adaptation.effectiveness_score
        })
        
    except Exception as e:
        logger.error(f"Error providing adaptation feedback: {str(e)}")
        return jsonify({'error': 'Failed to record feedback'}), 500

@biometric_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_user_biometric_profile(user_id):
    """Get user's biometric profile and preferences"""
    try:
        profile = UserBiometricProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify({
            'user_id': user_id,
            'profile': {
                'adaptation_sensitivity': profile.adaptation_sensitivity,
                'privacy_level': profile.privacy_level,
                'baseline_stress_level': profile.baseline_stress_level,
                'baseline_attention_span': profile.baseline_attention_span,
                'baseline_cognitive_load': profile.baseline_cognitive_load,
                'preferred_adaptations': profile.preferred_adaptations,
                'most_effective_triggers': profile.most_effective_triggers,
                'learning_confidence': profile.learning_confidence,
                'total_sessions': profile.total_sessions,
                'total_adaptations': profile.total_adaptations
            },
            'last_updated': profile.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({'error': 'Failed to get profile'}), 500

@biometric_bp.route('/profile/<int:user_id>', methods=['PUT'])
def update_user_biometric_profile(user_id):
    """Update user's biometric profile and preferences"""
    try:
        data = request.get_json()
        
        profile = UserBiometricProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Update profile fields
        if 'adaptation_sensitivity' in data:
            profile.adaptation_sensitivity = data['adaptation_sensitivity']
        
        if 'privacy_level' in data:
            profile.privacy_level = data['privacy_level']
        
        if 'preferred_adaptations' in data:
            profile.preferred_adaptations = data['preferred_adaptations']
        
        profile.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'updated',
            'user_id': user_id,
            'updated_fields': list(data.keys())
        })
        
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@biometric_bp.route('/calibration/start', methods=['POST'])
def start_biometric_calibration():
    """Start biometric calibration process"""
    try:
        data = request.get_json()
        
        if 'user_id' not in data or 'calibration_type' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        user_id = data['user_id']
        calibration_type = data['calibration_type']
        device_info = data.get('device_info', {})
        
        # Create calibration record
        calibration = BiometricCalibration(
            user_id=user_id,
            calibration_type=calibration_type,
            calibration_data={},
            device_info=device_info,
            calibration_quality=0.0,
            valid_until=datetime.utcnow() + timedelta(days=30),  # 30-day validity
            active=False  # Will be activated when calibration completes
        )
        
        db.session.add(calibration)
        db.session.commit()
        
        return jsonify({
            'calibration_id': calibration.id,
            'status': 'started',
            'calibration_type': calibration_type,
            'instructions': self._get_calibration_instructions(calibration_type)
        })
        
    except Exception as e:
        logger.error(f"Error starting calibration: {str(e)}")
        return jsonify({'error': 'Failed to start calibration'}), 500

def _get_calibration_instructions(calibration_type: str) -> Dict[str, Any]:
    """Get calibration instructions for specific type"""
    instructions = {
        'eye_tracking': {
            'steps': [
                'Look at the center of the screen',
                'Follow the moving dot with your eyes',
                'Keep your head still during calibration',
                'Blink normally'
            ],
            'duration': 30,
            'points': 9
        },
        'facial_baseline': {
            'steps': [
                'Maintain a neutral expression',
                'Look directly at the camera',
                'Ensure good lighting on your face',
                'Avoid moving for 10 seconds'
            ],
            'duration': 10,
            'points': 1
        }
    }
    
    return instructions.get(calibration_type, {})

@biometric_bp.route('/calibration/<int:calibration_id>/complete', methods=['POST'])
def complete_biometric_calibration(calibration_id):
    """Complete biometric calibration with results"""
    try:
        data = request.get_json()
        
        calibration = BiometricCalibration.query.get(calibration_id)
        if not calibration:
            return jsonify({'error': 'Calibration not found'}), 404
        
        # Update calibration with results
        calibration.calibration_data = data.get('calibration_data', {})
        calibration.calibration_quality = data.get('quality_score', 0.0)
        calibration.active = data.get('quality_score', 0.0) > 0.7  # Activate if quality is good
        
        db.session.commit()
        
        return jsonify({
            'status': 'completed',
            'calibration_id': calibration_id,
            'quality_score': calibration.calibration_quality,
            'active': calibration.active
        })
        
    except Exception as e:
        logger.error(f"Error completing calibration: {str(e)}")
        return jsonify({'error': 'Failed to complete calibration'}), 500

@biometric_bp.route('/analytics/session/<session_id>', methods=['GET'])
def get_session_analytics(session_id):
    """Get analytics for a biometric session"""
    try:
        session = BiometricSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get session data points
        data_points = BiometricDataPoint.query.filter_by(session_id=session_id).all()
        adaptations = InterfaceAdaptation.query.filter_by(session_id=session_id).all()
        
        # Calculate analytics
        analytics = {
            'session_duration': (session.end_time - session.start_time).total_seconds() if session.end_time else None,
            'data_points_collected': len(data_points),
            'adaptations_applied': len(adaptations),
            'average_stress_level': sum(dp.stress_level for dp in data_points if dp.stress_level) / len(data_points) if data_points else 0,
            'average_attention_score': sum(dp.attention_score for dp in data_points if dp.attention_score) / len(data_points) if data_points else 0,
            'average_cognitive_load': sum(dp.cognitive_load_score for dp in data_points if dp.cognitive_load_score) / len(data_points) if data_points else 0,
            'session_quality': session.session_quality,
            'adaptation_effectiveness': sum(a.effectiveness_score for a in adaptations) / len(adaptations) if adaptations else 0
        }
        
        return jsonify({
            'session_id': session_id,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting session analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500

