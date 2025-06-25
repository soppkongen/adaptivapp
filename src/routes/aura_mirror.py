"""
AURA Mirror API Routes

Implements the clarified AURA protocol with:
- Strict mode separation (Prompted vs Adaptive)
- Clear toggles and user control
- Privacy-first design
- Opt-in metrics
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, List

from ..services.aura_mirror_service import AURAMirrorService
from ..models.aura_mirror_protocol import (
    BiometricSignal, AURAMode, UITag
)

aura_mirror_bp = Blueprint('aura_mirror', __name__, url_prefix='/api/aura')

# Initialize service
aura_service = AURAMirrorService()

@aura_mirror_bp.route('/initialize', methods=['POST'])
def initialize_user():
    """Initialize AURA for a new user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        settings = aura_service.initialize_user(user_id)
        
        return jsonify({
            "status": "success",
            "message": "AURA initialized for user",
            "settings": {
                "adaptive_mode_enabled": settings.adaptive_mode_enabled,
                "prompted_mode_enabled": settings.prompted_mode_enabled,
                "metric_tracking_enabled": settings.metric_tracking_enabled,
                "privacy_level": settings.privacy_level
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/prompted/command', methods=['POST'])
def process_prompted_command():
    """Process user-initiated interface modification (Prompted Mode)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        command_text = data.get('command')
        session_id = data.get('session_id', 'default')
        
        if not user_id or not command_text:
            return jsonify({"error": "user_id and command are required"}), 400
        
        command = aura_service.process_prompted_command(user_id, command_text, session_id)
        
        return jsonify({
            "status": "success",
            "mode": "prompted",
            "command_processed": command_text,
            "parsed_tags": [tag.value for tag in command.parsed_tags],
            "applied_changes": command.applied_changes,
            "reversible": command.reversible,
            "timestamp": command.timestamp.isoformat()
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/adaptive/process', methods=['POST'])
def process_adaptive_signals():
    """Process biometric signals for adaptive interface changes (Adaptive Mode)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id', 'default')
        signals_data = data.get('signals', [])
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Convert signal data to BiometricSignal objects
        signals = []
        for signal_data in signals_data:
            signal = BiometricSignal(
                user_id=user_id,
                timestamp=datetime.now(),
                signal_type=signal_data.get('type'),
                intensity=signal_data.get('intensity', 0.0),
                confidence=signal_data.get('confidence', 0.0),
                local_only=True  # Always true for privacy
            )
            signals.append(signal)
        
        response = aura_service.process_biometric_signals(user_id, signals, session_id)
        
        if response is None:
            return jsonify({
                "status": "no_adaptation",
                "message": "Adaptive mode disabled or no adaptation needed"
            })
        
        return jsonify({
            "status": "success",
            "mode": "adaptive",
            "trigger_signals": [s.signal_type for s in response.trigger_signals],
            "suggested_tags": [tag.value for tag in response.suggested_tags],
            "applied_changes": response.applied_changes,
            "user_visible": response.user_visible,
            "user_controllable": response.user_controllable,
            "gradual": response.gradual,
            "timestamp": response.timestamp.isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/settings/adaptive-mode', methods=['POST'])
def toggle_adaptive_mode():
    """Toggle adaptive mode on/off with explicit user control"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        enabled = data.get('enabled', False)
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        result = aura_service.toggle_adaptive_mode(user_id, enabled)
        
        return jsonify({
            "status": "success",
            "adaptive_mode_enabled": result,
            "message": f"Adaptive mode {'enabled' if result else 'disabled'}",
            "note": "User has explicit control over this setting"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/settings/metrics', methods=['POST'])
def enable_metrics():
    """Enable specific metrics tracking (opt-in only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        metrics = data.get('metrics', [])
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        result = aura_service.enable_metric_tracking(user_id, metrics)
        settings = aura_service.get_user_settings(user_id)
        
        return jsonify({
            "status": "success",
            "metric_tracking_enabled": result,
            "enabled_metrics": settings.enabled_metrics,
            "available_metrics": [
                "visual_age_delta",
                "focus_heatmap", 
                "cognitive_drift_index",
                "entropy_score",
                "mood_resonance_profile"
            ],
            "note": "All metrics are opt-in and processed locally only"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/metrics/visual-age-delta', methods=['GET'])
def get_visual_age_delta():
    """Get visual age delta metric (opt-in only)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        delta = aura_service.get_visual_age_delta(user_id)
        
        if delta is None:
            return jsonify({
                "status": "not_available",
                "message": "Visual age delta tracking not enabled"
            })
        
        return jsonify({
            "status": "success",
            "metric": "visual_age_delta",
            "baseline_date": delta.baseline_date.isoformat(),
            "current_estimate": delta.current_estimate,
            "delta_months": delta.delta_months,
            "trend_direction": delta.trend_direction,
            "confidence": delta.confidence,
            "note": "Example: +0.8 months since March",
            "local_only": delta.local_only
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/metrics/focus-heatmap', methods=['GET'])
def get_focus_heatmap():
    """Get focus heatmap for current session (opt-in only)"""
    try:
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id', 'default')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        heatmap = aura_service.get_focus_heatmap(user_id, session_id)
        
        if heatmap is None:
            return jsonify({
                "status": "not_available",
                "message": "Focus heatmap tracking not enabled"
            })
        
        return jsonify({
            "status": "success",
            "metric": "focus_heatmap",
            "session_id": heatmap.session_id,
            "attention_map": heatmap.attention_map,
            "primary_kpi_focus": heatmap.primary_kpi_focus,
            "distraction_events": heatmap.distraction_events,
            "engagement_score": heatmap.engagement_score,
            "insight": f"{heatmap.primary_kpi_focus*100:.0f}% of gaze spent on primary KPIs",
            "timestamp": heatmap.timestamp.isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/metrics/cognitive-drift', methods=['GET'])
def get_cognitive_drift():
    """Get cognitive drift index for session (opt-in only)"""
    try:
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id', 'default')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        drift = aura_service.get_cognitive_drift_index(user_id, session_id)
        
        if drift is None:
            return jsonify({
                "status": "not_available",
                "message": "Cognitive drift tracking not enabled"
            })
        
        return jsonify({
            "status": "success",
            "metric": "cognitive_drift_index",
            "session_id": drift.session_id,
            "scroll_without_read_events": drift.scroll_without_read_events,
            "rapid_navigation_events": drift.rapid_navigation_events,
            "attention_drops": drift.attention_drops,
            "drift_score": drift.drift_score,
            "context_type": drift.context_type,
            "insight": f"You disengaged {drift.attention_drops}x on {drift.context_type} views",
            "timestamp": drift.timestamp.isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/metrics/entropy-score', methods=['GET'])
def get_entropy_score():
    """Get entropy score (personalization demand) (opt-in only)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        entropy = aura_service.get_entropy_score(user_id)
        
        if entropy is None:
            return jsonify({
                "status": "not_available",
                "message": "Entropy score tracking not enabled"
            })
        
        return jsonify({
            "status": "success",
            "metric": "entropy_score",
            "period_start": entropy.period_start.isoformat(),
            "period_end": entropy.period_end.isoformat(),
            "layout_changes": entropy.layout_changes,
            "theme_flips": entropy.theme_flips,
            "override_count": entropy.override_count,
            "entropy_value": entropy.entropy_value,
            "stability_trend": entropy.stability_trend,
            "insight": f"Higher score = higher personalization demand"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/metrics/mood-resonance', methods=['GET'])
def get_mood_resonance():
    """Get mood resonance profile (opt-in only)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        profile = aura_service.get_mood_resonance_profile(user_id)
        
        if profile is None:
            return jsonify({
                "status": "not_available",
                "message": "Mood resonance tracking not enabled or not opted in"
            })
        
        return jsonify({
            "status": "success",
            "metric": "mood_resonance_profile",
            "energy_level": profile.energy_level,
            "mood_indicators": profile.mood_indicators,
            "micro_movement_patterns": profile.micro_movement_patterns,
            "daily_pattern": profile.daily_pattern,
            "opt_in_explicit": profile.opt_in_explicit,
            "note": "Derived from tone, expression, micro-movements",
            "timestamp": profile.timestamp.isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/revert', methods=['POST'])
def revert_last_change():
    """Revert the last UI change (both prompted and adaptive)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        success = aura_service.revert_last_change(user_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Last change reverted",
                "note": "User has full control over all changes"
            })
        else:
            return jsonify({
                "status": "no_changes",
                "message": "No changes to revert"
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/settings', methods=['GET'])
def get_user_settings():
    """Get current user settings"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        settings = aura_service.get_user_settings(user_id)
        
        return jsonify({
            "status": "success",
            "settings": {
                "adaptive_mode_enabled": settings.adaptive_mode_enabled,
                "prompted_mode_enabled": settings.prompted_mode_enabled,
                "metric_tracking_enabled": settings.metric_tracking_enabled,
                "enabled_metrics": settings.enabled_metrics,
                "privacy_level": settings.privacy_level,
                "local_processing_only": settings.local_processing_only,
                "data_retention_days": settings.data_retention_days
            },
            "design_ethos": "We Only Mirror - AURA responds like a puppy, not a judge"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/export', methods=['GET'])
def export_user_data():
    """Export user's local data (privacy compliant)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        data = aura_service.export_user_data(user_id)
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "data": data,
            "privacy_note": "All biometric data processed locally only",
            "data_retention": "Local storage only, user controlled"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@aura_mirror_bp.route('/status', methods=['GET'])
def get_aura_status():
    """Get AURA system status and design principles"""
    return jsonify({
        "status": "active",
        "version": "2.0.0",
        "design_ethos": "We Only Mirror",
        "core_principles": [
            "AURA operates as a responsive mirror",
            "Only adapts what the user can already observe",
            "No hidden agenda, no background nudging",
            "No behavioral scoring or predictions",
            "User has explicit control over all modes",
            "Privacy-first: 100% local processing",
            "All metrics are opt-in only"
        ],
        "modes": {
            "prompted": "Manual user interaction with immediate response",
            "adaptive": "Passive biometric response (default OFF)",
            "disabled": "AURA completely off"
        },
        "available_metrics": [
            "visual_age_delta",
            "focus_heatmap",
            "cognitive_drift_index", 
            "entropy_score",
            "mood_resonance_profile"
        ],
        "privacy_compliance": {
            "local_processing_only": True,
            "no_data_transmission": True,
            "user_controlled_retention": True,
            "explicit_opt_in_required": True
        }
    })

