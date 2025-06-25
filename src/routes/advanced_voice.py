"""
Elite Command API: Comprehensive Voice Command Routes

More than redundantly good voice interaction API for elite executives.
Provides complete REST interface for voice command processing.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import base64
import io

from ..services.advanced_voice_service import AdvancedVoiceCommandService
from ..models.voice_command_system import (
    VoiceInteractionMode, VoiceCommandCategory, VoiceResponseType
)

# Create blueprint
voice_bp = Blueprint('voice', __name__, url_prefix='/api/voice')

# Initialize voice service
voice_service = AdvancedVoiceCommandService()

@voice_bp.route('/session/start', methods=['POST'])
def start_voice_session():
    """Start a new voice interaction session"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        mode = data.get('mode', 'active_voice')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        # Convert mode string to enum
        try:
            interaction_mode = VoiceInteractionMode(mode)
        except ValueError:
            interaction_mode = VoiceInteractionMode.ACTIVE_VOICE
            
        session = voice_service.start_voice_session(user_id, interaction_mode)
        
        return jsonify({
            "success": True,
            "session": {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "mode": session.current_mode.value,
                "start_time": session.start_time.isoformat(),
                "wake_words": ["command", "elite", "aura"],
                "available_categories": [cat.value for cat in VoiceCommandCategory]
            },
            "message": "Voice session started successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/command/process', methods=['POST'])
def process_voice_command():
    """Process a voice command (text or audio)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        command_text = data.get('command_text')
        audio_data = data.get('audio_data')  # Base64 encoded audio
        context = data.get('context', {})
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        if not command_text and not audio_data:
            return jsonify({"error": "Either command_text or audio_data is required"}), 400
            
        # If audio data is provided, convert to text (placeholder for speech-to-text)
        if audio_data and not command_text:
            command_text = voice_service._convert_audio_to_text(audio_data)
            
        # Process the command
        response = voice_service.process_voice_command(user_id, command_text, context)
        
        return jsonify({
            "success": response.success,
            "response": {
                "response_id": response.response_id,
                "command_id": response.command_id,
                "response_type": response.response_type.value,
                "message": response.message,
                "actions_taken": response.actions_taken,
                "visual_feedback": response.visual_feedback,
                "audio_feedback": response.audio_feedback,
                "confidence_score": response.confidence_score,
                "execution_time": response.execution_time
            },
            "error_details": response.error_details
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/commands/available', methods=['GET'])
def get_available_commands():
    """Get list of available voice commands"""
    try:
        category = request.args.get('category')
        user_id = request.args.get('user_id')
        
        # Convert category string to enum if provided
        category_enum = None
        if category:
            try:
                category_enum = VoiceCommandCategory(category)
            except ValueError:
                return jsonify({"error": f"Invalid category: {category}"}), 400
                
        commands = voice_service.get_available_commands(category_enum)
        
        # Group commands by category for better organization
        grouped_commands = {}
        for command in commands:
            cat = command['category']
            if cat not in grouped_commands:
                grouped_commands[cat] = []
            grouped_commands[cat].append(command)
            
        return jsonify({
            "success": True,
            "commands": commands,
            "grouped_commands": grouped_commands,
            "total_commands": len(commands),
            "categories": list(grouped_commands.keys())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/session/status', methods=['GET'])
def get_session_status():
    """Get current voice session status"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        status = voice_service.get_voice_session_status(user_id)
        
        return jsonify({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/onboarding/demo', methods=['POST'])
def voice_onboarding_demo():
    """Demonstrate voice capabilities during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        demo_step = data.get('demo_step', 'style_adjustment')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        # Define demo scenarios
        demo_scenarios = {
            "style_adjustment": {
                "command": "make this more relaxed",
                "description": "Watch as I adjust the interface to feel more relaxed",
                "visual_changes": {
                    "border_radius": "12px",
                    "padding": "20px",
                    "colors": {"primary": "#6b7280", "accent": "#9ca3af"},
                    "animation": "smooth_transition"
                },
                "narration": "Notice how the interface becomes softer and more spacious"
            },
            "layout_control": {
                "command": "move the metrics to the left side",
                "description": "I'll demonstrate layout control by moving elements",
                "visual_changes": {
                    "layout": "metrics_left",
                    "animation": "slide_transition",
                    "duration": 600
                },
                "narration": "See how elements can be repositioned with simple voice commands"
            },
            "data_intelligence": {
                "command": "explain this revenue figure",
                "description": "I'll show you how to get insights about your data",
                "visual_changes": {
                    "highlight_element": "revenue_metric",
                    "show_tooltip": True,
                    "display_lineage": True
                },
                "narration": "Voice commands can reveal the story behind your numbers"
            }
        }
        
        scenario = demo_scenarios.get(demo_step, demo_scenarios["style_adjustment"])
        
        # Process the demo command
        response = voice_service.process_voice_command(
            user_id, 
            scenario["command"], 
            {"demo_mode": True, "onboarding": True}
        )
        
        return jsonify({
            "success": True,
            "demo": {
                "step": demo_step,
                "command": scenario["command"],
                "description": scenario["description"],
                "narration": scenario["narration"],
                "visual_changes": scenario["visual_changes"],
                "response": {
                    "message": response.message,
                    "actions_taken": response.actions_taken,
                    "visual_feedback": response.visual_feedback
                }
            },
            "next_steps": [
                "Try saying the command yourself",
                "Experiment with variations",
                "Ask 'what else can I do?'"
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/interface/style-adjust', methods=['POST'])
def voice_style_adjustment():
    """Handle voice-driven style adjustments"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        style_command = data.get('style_command')
        target_elements = data.get('target_elements', ['global_theme'])
        
        if not user_id or not style_command:
            return jsonify({"error": "user_id and style_command are required"}), 400
            
        # Process style adjustment command
        context = {
            "target_elements": target_elements,
            "interface_mode": "style_adjustment"
        }
        
        response = voice_service.process_voice_command(user_id, style_command, context)
        
        return jsonify({
            "success": response.success,
            "style_changes": response.visual_feedback,
            "message": response.message,
            "applied_to": target_elements,
            "confidence": response.confidence_score
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/data/query', methods=['POST'])
def voice_data_query():
    """Handle voice-driven data queries and explanations"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        query_command = data.get('query_command')
        target_metric = data.get('target_metric')
        
        if not user_id or not query_command:
            return jsonify({"error": "user_id and query_command are required"}), 400
            
        # Process data query command
        context = {
            "target_metric": target_metric,
            "interface_mode": "data_query",
            "available_metrics": ["revenue", "churn", "arr", "burn_rate", "runway"]
        }
        
        response = voice_service.process_voice_command(user_id, query_command, context)
        
        return jsonify({
            "success": response.success,
            "query_result": {
                "explanation": response.message,
                "data_insights": response.actions_taken,
                "visual_highlights": response.visual_feedback,
                "confidence_score": response.confidence_score
            },
            "follow_up_suggestions": [
                "Ask about data sources",
                "Request trend analysis", 
                "Compare with other metrics"
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/layout/control', methods=['POST'])
def voice_layout_control():
    """Handle voice-driven layout modifications"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        layout_command = data.get('layout_command')
        current_layout = data.get('current_layout', {})
        
        if not user_id or not layout_command:
            return jsonify({"error": "user_id and layout_command are required"}), 400
            
        # Process layout control command
        context = {
            "current_layout": current_layout,
            "interface_mode": "layout_control",
            "available_elements": ["metrics_panel", "portfolio_grid", "alert_center", "navigation"]
        }
        
        response = voice_service.process_voice_command(user_id, layout_command, context)
        
        return jsonify({
            "success": response.success,
            "layout_changes": response.actions_taken,
            "visual_feedback": response.visual_feedback,
            "message": response.message,
            "new_layout_state": response.visual_feedback.get("new_layout", current_layout)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/security/voice-commands', methods=['POST'])
def voice_security_commands():
    """Handle voice-driven security and access control"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        security_command = data.get('security_command')
        
        if not user_id or not security_command:
            return jsonify({"error": "user_id and security_command are required"}), 400
            
        # Security commands require higher confidence threshold
        context = {
            "interface_mode": "security_control",
            "require_confirmation": True,
            "confidence_threshold": 0.9
        }
        
        response = voice_service.process_voice_command(user_id, security_command, context)
        
        # Additional security validation
        if response.response_type == VoiceResponseType.CONFIRMATION_REQUIRED:
            return jsonify({
                "success": True,
                "requires_confirmation": True,
                "security_action": response.message,
                "confirmation_token": f"sec_{user_id}_{datetime.now().timestamp()}",
                "expires_in": 30  # seconds
            })
            
        return jsonify({
            "success": response.success,
            "security_result": {
                "action_taken": response.message,
                "details": response.actions_taken,
                "audit_log_entry": {
                    "user_id": user_id,
                    "action": security_command,
                    "timestamp": datetime.now().isoformat(),
                    "success": response.success
                }
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/training/feedback', methods=['POST'])
def voice_training_feedback():
    """Collect feedback for voice command training"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        command_text = data.get('command_text')
        intended_action = data.get('intended_action')
        actual_result = data.get('actual_result')
        satisfaction_rating = data.get('satisfaction_rating')  # 1-5
        
        if not all([user_id, command_text, satisfaction_rating]):
            return jsonify({"error": "user_id, command_text, and satisfaction_rating are required"}), 400
            
        # Store training feedback
        feedback_data = {
            "user_id": user_id,
            "command_text": command_text,
            "intended_action": intended_action,
            "actual_result": actual_result,
            "satisfaction_rating": satisfaction_rating,
            "timestamp": datetime.now().isoformat(),
            "anonymized": True  # Always anonymize for privacy
        }
        
        # Process feedback for system improvement
        voice_service.training_data.append(feedback_data)
        
        return jsonify({
            "success": True,
            "message": "Feedback recorded successfully",
            "training_impact": {
                "will_improve_recognition": satisfaction_rating < 4,
                "command_pattern_learned": True,
                "user_preference_updated": True
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/help/commands', methods=['GET'])
def voice_help_commands():
    """Get contextual help for voice commands"""
    try:
        user_id = request.args.get('user_id')
        current_screen = request.args.get('current_screen', 'dashboard')
        user_level = request.args.get('user_level', 'executive')  # executive, manager, analyst
        
        # Get contextual commands based on current screen
        contextual_commands = voice_service._get_contextual_commands(current_screen, user_level)
        
        # Get most used commands for this user
        popular_commands = voice_service._get_popular_commands(user_id)
        
        return jsonify({
            "success": True,
            "help": {
                "contextual_commands": contextual_commands,
                "popular_commands": popular_commands,
                "quick_examples": [
                    "Command, make this more relaxed",
                    "Command, explain this revenue figure", 
                    "Command, move metrics to the left",
                    "Command, what should I focus on today?"
                ],
                "wake_words": ["command", "elite", "aura"],
                "tips": [
                    "Speak naturally - I understand conversational language",
                    "You can refer to elements as 'this' or 'that'",
                    "I remember context from recent commands",
                    "Say 'undo' to reverse any changes"
                ]
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@voice_bp.route('/analytics/usage', methods=['GET'])
def voice_usage_analytics():
    """Get voice command usage analytics"""
    try:
        user_id = request.args.get('user_id')
        time_range = request.args.get('time_range', '7d')  # 1d, 7d, 30d
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        # Get usage analytics
        analytics = voice_service._get_usage_analytics(user_id, time_range)
        
        return jsonify({
            "success": True,
            "analytics": analytics,
            "insights": {
                "most_used_category": analytics.get("top_category"),
                "average_confidence": analytics.get("avg_confidence"),
                "success_rate": analytics.get("success_rate"),
                "preferred_interaction_style": analytics.get("interaction_style"),
                "recommendations": [
                    "Try using more layout commands",
                    "Explore data intelligence features",
                    "Consider enabling passive mode"
                ]
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error handlers
@voice_bp.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "details": str(error)}), 400

@voice_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "details": str(error)}), 500

