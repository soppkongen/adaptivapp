"""
AURA Integrated Onboarding API Routes

Voice + Visual Adaptation Onboarding Flow
Real-time interface adaptation during AI introduction

Target: Executive / Portfolio Owner
Experience: Voice + Click → Dashboard UI + Real-time Layout Changes
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, List

from ..services.integrated_onboarding_service import IntegratedOnboardingService
from ..models.integrated_onboarding import OnboardingPhase

integrated_onboarding_bp = Blueprint('integrated_onboarding', __name__, url_prefix='/api/onboarding')

# Initialize service
onboarding_service = IntegratedOnboardingService()

@integrated_onboarding_bp.route('/start', methods=['POST'])
def start_integrated_onboarding():
    """Start integrated voice + visual adaptation onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        session = onboarding_service.start_onboarding_session(user_id)
        current_step = onboarding_service.get_current_step(user_id)
        
        return jsonify({
            "status": "success",
            "message": "Integrated onboarding started",
            "session_id": session.session_id,
            "onboarding_type": "voice_visual_adaptation",
            "target_user": "Executive / Portfolio Owner",
            "experience": "Voice + Click → Dashboard UI + Real-time Layout Changes",
            "total_duration": session.flow.total_duration,
            "current_step": {
                "phase": current_step.phase.value,
                "step_id": current_step.step_id,
                "narration": {
                    "text": current_step.narration.text,
                    "duration": current_step.narration.duration,
                    "voice_tone": current_step.narration.voice_tone,
                    "visual_cues": current_step.narration.visual_cues
                },
                "visual_transitions": [
                    {
                        "type": vt.transition_type,
                        "duration": vt.duration,
                        "from_state": vt.from_state,
                        "to_state": vt.to_state,
                        "easing": vt.easing,
                        "description": vt.description
                    } for vt in current_step.visual_transitions
                ],
                "adaptive_elements": current_step.adaptive_elements
            },
            "note": "AI will demonstrate system adaptation in real-time while introducing itself"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/current-step', methods=['GET'])
def get_current_onboarding_step():
    """Get current onboarding step with voice + visual cues"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        current_step = onboarding_service.get_current_step(user_id)
        
        if not current_step:
            return jsonify({
                "status": "no_active_onboarding",
                "message": "No active onboarding session found"
            })
        
        # Get timing information for current step
        session = onboarding_service.active_sessions.get(user_id)
        elapsed_time = (datetime.now() - session.start_time).total_seconds() if session else 0
        
        return jsonify({
            "status": "success",
            "current_step": {
                "phase": current_step.phase.value,
                "step_id": current_step.step_id,
                "narration": {
                    "text": current_step.narration.text,
                    "start_time": current_step.narration.start_time,
                    "duration": current_step.narration.duration,
                    "voice_tone": current_step.narration.voice_tone,
                    "pace": current_step.narration.pace,
                    "visual_cues": current_step.narration.visual_cues
                },
                "visual_transitions": [
                    {
                        "type": vt.transition_type,
                        "start_time": vt.start_time,
                        "duration": vt.duration,
                        "from_state": vt.from_state,
                        "to_state": vt.to_state,
                        "easing": vt.easing,
                        "description": vt.description
                    } for vt in current_step.visual_transitions
                ],
                "user_interaction_points": current_step.user_interaction_points,
                "adaptive_elements": current_step.adaptive_elements
            },
            "timing": {
                "elapsed_time": elapsed_time,
                "step_should_start": elapsed_time >= current_step.narration.start_time,
                "step_should_end": elapsed_time >= (current_step.narration.start_time + current_step.narration.duration)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/advance', methods=['POST'])
def advance_onboarding_step():
    """Advance to next onboarding step"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        success = onboarding_service.advance_onboarding(user_id)
        
        if not success:
            return jsonify({"error": "Failed to advance onboarding"}), 400
        
        next_step = onboarding_service.get_current_step(user_id)
        
        if next_step:
            return jsonify({
                "status": "advanced",
                "next_step": {
                    "phase": next_step.phase.value,
                    "step_id": next_step.step_id,
                    "narration": {
                        "text": next_step.narration.text,
                        "duration": next_step.narration.duration,
                        "voice_tone": next_step.narration.voice_tone,
                        "visual_cues": next_step.narration.visual_cues
                    }
                }
            })
        else:
            return jsonify({
                "status": "completed",
                "message": "Integrated onboarding completed successfully",
                "next_action": "dashboard_ready"
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/interaction', methods=['POST'])
def handle_user_interaction():
    """Handle user interaction during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        interaction_type = data.get('interaction_type')
        interaction_data = data.get('data', {})
        
        if not user_id or not interaction_type:
            return jsonify({"error": "user_id and interaction_type are required"}), 400
        
        result = onboarding_service.handle_user_interaction(user_id, interaction_type, interaction_data)
        
        return jsonify({
            "status": "success",
            "interaction_type": interaction_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/card-selection', methods=['POST'])
def handle_card_selection():
    """Handle agency card selection during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        card_type = data.get('card_type')
        
        if not user_id or not card_type:
            return jsonify({"error": "user_id and card_type are required"}), 400
        
        result = onboarding_service.handle_user_interaction(
            user_id, 
            "card_selection", 
            {"card_type": card_type}
        )
        
        return jsonify({
            "status": "success",
            "card_selected": card_type,
            "result": result,
            "message": f"Selected path: {card_type}",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/voice-command', methods=['POST'])
def handle_voice_command():
    """Handle voice command during onboarding"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        command = data.get('command')
        confidence = data.get('confidence', 0.8)
        
        if not user_id or not command:
            return jsonify({"error": "user_id and command are required"}), 400
        
        result = onboarding_service.handle_user_interaction(
            user_id,
            "voice_command",
            {"command": command, "confidence": confidence}
        )
        
        return jsonify({
            "status": "success",
            "command_processed": command,
            "confidence": confidence,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/adaptation-demo', methods=['GET'])
def get_adaptation_demonstrations():
    """Get available adaptation demonstrations"""
    try:
        demonstrations = onboarding_service.adaptation_demonstrations
        
        demo_info = {}
        for demo_id, demo in demonstrations.items():
            demo_info[demo_id] = {
                "demo_type": demo.demo_type.value,
                "voice_cue": demo.voice_cue,
                "duration": demo.duration,
                "user_impact_message": demo.user_impact_message,
                "visual_changes": demo.visual_changes
            }
        
        return jsonify({
            "status": "success",
            "demonstrations": demo_info,
            "note": "These demonstrations are integrated into the onboarding narration"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/agency-cards', methods=['GET'])
def get_agency_cards():
    """Get the three agency cards for immediate user choice"""
    try:
        cards = onboarding_service.agency_cards
        
        cards_info = []
        for card in cards:
            cards_info.append({
                "card_type": card.card_type.value,
                "title": card.title,
                "description": card.description,
                "icon": card.icon,
                "action_text": card.action_text,
                "hover_animation": card.hover_animation,
                "click_action": card.click_action,
                "visual_style": card.visual_style
            })
        
        return jsonify({
            "status": "success",
            "agency_cards": cards_info,
            "presentation_timing": "Appears at 0:16-0:22 during onboarding",
            "note": "Cards appear with animated entrance and hover pulses"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/voice-examples', methods=['GET'])
def get_voice_command_examples():
    """Get voice command examples for primer phase"""
    try:
        examples = onboarding_service.voice_commands
        
        examples_info = []
        for example in examples:
            examples_info.append({
                "command_text": example.command_text,
                "category": example.category,
                "expected_response": example.expected_response,
                "demonstration_available": example.demonstration_available
            })
        
        return jsonify({
            "status": "success",
            "voice_examples": examples_info,
            "presentation_timing": "Presented at 0:23-0:30 during voice primer",
            "note": "Examples are taught by doing, not just explaining"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/status', methods=['GET'])
def get_onboarding_status():
    """Get current onboarding status and progress"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        status = onboarding_service.get_onboarding_status(user_id)
        
        return jsonify({
            "status": "success",
            "onboarding_status": status,
            "onboarding_type": "integrated_voice_visual_adaptation",
            "mission": "Demonstrate system adaptation in real-time while AI introduces itself"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/complete', methods=['POST'])
def complete_onboarding():
    """Mark onboarding as completed and transition to main dashboard"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        completion_feedback = data.get('feedback', {})
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        session = onboarding_service.active_sessions.get(user_id)
        if not session:
            return jsonify({"error": "No active onboarding session"}), 400
        
        # Mark as completed
        session.completion_time = datetime.now()
        
        # Extract learned preferences
        preferences = session.adaptation_preferences_learned
        selected_path = session.selected_path
        
        return jsonify({
            "status": "completed",
            "message": "Integrated onboarding completed successfully",
            "completion_time": session.completion_time.isoformat(),
            "total_duration": (session.completion_time - session.start_time).total_seconds(),
            "learned_preferences": preferences,
            "selected_path": selected_path.value if selected_path else None,
            "user_interactions": len(session.user_interactions),
            "voice_commands_attempted": len(session.voice_commands_attempted),
            "next_action": "transition_to_main_dashboard",
            "dashboard_ready": True,
            "adaptive_system_active": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrated_onboarding_bp.route('/flow-definition', methods=['GET'])
def get_onboarding_flow_definition():
    """Get the complete onboarding flow definition"""
    try:
        return jsonify({
            "status": "success",
            "onboarding_flow": {
                "title": "AURA Integrated Onboarding: Voice + Visual Adaptation",
                "target_user": "Executive / Portfolio Owner",
                "input_modes": ["Voice", "Click"],
                "output_modes": ["Dashboard UI", "Real-time Layout Changes"],
                "total_duration": "30 seconds",
                "phases": [
                    {
                        "phase": "greeting_brand_framing",
                        "timing": "0:00-0:06",
                        "description": "AI Greeting + Brand Framing",
                        "voice_narration": "Welcome to Elite Commander. I'm your system AI. I'll adapt this interface to you — visually, cognitively, and operationally.",
                        "visual_effects": ["background_animate", "dashboard_zoom", "tone_shift"]
                    },
                    {
                        "phase": "adaptive_demonstration",
                        "timing": "0:07-0:15",
                        "description": "Adaptive Demonstration Begins",
                        "voice_narration": "Let's adjust a few things right now, so it fits you. Here's a sharp, focused layout. Now a softer, more spacious one. You might prefer calming tones… or something more energizing. All of this is adjustable by voice, anytime.",
                        "visual_effects": ["layout_sharp", "layout_soft", "color_calm", "color_energetic"]
                    },
                    {
                        "phase": "immediate_agency",
                        "timing": "0:16-0:22",
                        "description": "Immediate Agency: Present 3 Cards",
                        "voice_narration": "We'll scan your portfolio and connect live feeds. Prefer to explore first? I'll show you a sample company. Want more contrast, bigger text, less clutter? Let's make it right.",
                        "visual_effects": ["cards_appear", "hover_pulses"],
                        "user_choices": [
                            "Gather My Company Data",
                            "Try It With Demo Data", 
                            "Tune the Interface"
                        ]
                    },
                    {
                        "phase": "voice_primer",
                        "timing": "0:23-0:30",
                        "description": "Voice Primer",
                        "voice_narration": "You can say things like 'Show me the high-contrast layout', 'Connect my companies', or 'Why is revenue down this month?' You're in control. Just speak — I'll respond instantly.",
                        "visual_effects": ["mic_pulse", "ready_mode"],
                        "voice_examples": [
                            "Show me the high-contrast layout",
                            "Connect my companies",
                            "Why is revenue down this month?"
                        ]
                    }
                ]
            },
            "key_principles": [
                "AI guides user through real-time UI shifts as part of onboarding",
                "Every style change is shown as it's spoken",
                "Voice commands are taught by doing, not explaining",
                "User experiences system adapting while AI introduces itself"
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

