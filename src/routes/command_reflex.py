"""
Command Reflex Layer API Routes

Unified API replacing AURA Mirror Protocol with simplified approach:
- Three entry modes: Mirror, Edit, Observe
- Three tiers: Passive, Semi-active, Active
- Clear separation of system vs user-facing metrics
- Focused on Elite Commander mission: enhance decision velocity
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, List

from ..services.command_reflex_service import CommandReflexService
from ..models.command_reflex_layer import (
    ReflexTier, EntryMode, MetricType, BiometricSignal
)

command_reflex_bp = Blueprint('command_reflex', __name__, url_prefix='/api/reflex')

# Initialize service
reflex_service = CommandReflexService()

@command_reflex_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get Command Reflex Layer system status"""
    return jsonify({
        "status": "active",
        "version": "3.0.0",
        "system_name": "Command Reflex Layer",
        "mission": "Elite Commander superuser dashboard with responsive logic to enhance decision velocity",
        "design_principle": "Context-aware system responsiveness across three tiers",
        "tiers": {
            "passive": "AURA biometric-reactive, continuous (default OFF)",
            "semi_active": "Mirror suggestions and feedback",
            "active": "Direct user commands"
        },
        "entry_modes": {
            "mirror": "Freeform feedback + adaptation: 'Too noisy', 'Feels sharp'",
            "edit": "Element-specific: 'Make this card smaller'",
            "observe": "Passive biometric reflection"
        },
        "focus": "Superuser command dashboard - not a feel-good mirror tool"
    })

@command_reflex_bp.route('/initialize', methods=['POST'])
def initialize_user():
    """Initialize Command Reflex Layer for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        settings = reflex_service.initialize_user(user_id)
        
        return jsonify({
            "status": "success",
            "message": "Command Reflex Layer initialized",
            "settings": {
                "passive_tier_enabled": settings.passive_tier_enabled,
                "semi_active_tier_enabled": settings.semi_active_tier_enabled,
                "active_tier_enabled": settings.active_tier_enabled,
                "wellness_insights_enabled": settings.wellness_insights_enabled,
                "auto_summarize_changes": settings.auto_summarize_changes
            },
            "note": "Passive tier (biometric) is default OFF for privacy"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/mirror', methods=['POST'])
def process_mirror_mode():
    """Process freeform feedback and adaptation (Semi-active tier)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        feedback = data.get('feedback')
        context = data.get('context', {})
        
        if not user_id or not feedback:
            return jsonify({"error": "user_id and feedback are required"}), 400
        
        command = reflex_service.process_command(
            user_id=user_id,
            raw_input=feedback,
            entry_mode=EntryMode.MIRROR,
            context=context
        )
        
        return jsonify({
            "status": "success",
            "tier": "semi_active",
            "entry_mode": "mirror",
            "feedback_processed": feedback,
            "detected_patterns": command.parsed_intent.get("detected_patterns", []),
            "tag_changes": command.tag_changes,
            "applied": command.applied,
            "summary": command.parsed_intent.get("summary", ""),
            "reversible": command.reversible,
            "timestamp": command.timestamp.isoformat()
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/edit', methods=['POST'])
def process_edit_mode():
    """Process element-specific commands (Active tier)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        command_text = data.get('command')
        target_element = data.get('target_element')
        context = data.get('context', {})
        
        if not user_id or not command_text:
            return jsonify({"error": "user_id and command are required"}), 400
        
        # Add target element to context if provided
        if target_element:
            context['current_element'] = target_element
        
        command = reflex_service.process_command(
            user_id=user_id,
            raw_input=command_text,
            entry_mode=EntryMode.EDIT,
            context=context
        )
        
        return jsonify({
            "status": "success",
            "tier": "active",
            "entry_mode": "edit",
            "command_processed": command_text,
            "target_elements": command.target_elements,
            "tag_changes": command.tag_changes,
            "applied": command.applied,
            "summary": command.parsed_intent.get("summary", ""),
            "reversible": command.reversible,
            "timestamp": command.timestamp.isoformat()
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/observe', methods=['POST'])
def process_observe_mode():
    """Process biometric signals for passive adaptation (Passive tier)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
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
                system_facing_only=True  # Always system-facing for privacy
            )
            signals.append(signal)
        
        command = reflex_service.process_biometric_signals(user_id, signals)
        
        if command is None:
            return jsonify({
                "status": "no_adaptation",
                "message": "Passive tier disabled or no adaptation needed",
                "note": "Biometric adaptation is opt-in and default OFF"
            })
        
        return jsonify({
            "status": "success",
            "tier": "passive",
            "entry_mode": "observe",
            "adaptation_reason": command.parsed_intent.get("adaptation_reason", ""),
            "tag_changes": command.tag_changes,
            "applied": command.applied,
            "summary": command.parsed_intent.get("summary", ""),
            "gradual": True,
            "system_facing_only": True,
            "timestamp": command.timestamp.isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/tiers/<tier_name>', methods=['POST'])
def toggle_tier():
    """Toggle specific tier on/off"""
    try:
        tier_name = request.view_args['tier_name']
        data = request.get_json()
        user_id = data.get('user_id')
        enabled = data.get('enabled', False)
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Map tier name to enum
        tier_mapping = {
            "passive": ReflexTier.PASSIVE,
            "semi-active": ReflexTier.SEMI_ACTIVE,
            "active": ReflexTier.ACTIVE
        }
        
        if tier_name not in tier_mapping:
            return jsonify({"error": f"Invalid tier: {tier_name}"}), 400
        
        tier = tier_mapping[tier_name]
        result = reflex_service.toggle_tier(user_id, tier, enabled)
        
        tier_descriptions = {
            "passive": "Biometric-reactive interface adaptation",
            "semi-active": "Mirror feedback and suggestions",
            "active": "Direct command processing"
        }
        
        return jsonify({
            "status": "success",
            "tier": tier_name,
            "enabled": result,
            "description": tier_descriptions[tier_name],
            "message": f"{tier_name.title()} tier {'enabled' if result else 'disabled'}",
            "note": "User has explicit control over all tiers"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/wellness/enable', methods=['POST'])
def enable_wellness_insights():
    """Enable wellness insights (opt-in only, user-facing)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        insight_types = data.get('insight_types', [])
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        result = reflex_service.enable_wellness_insights(user_id, insight_types)
        
        return jsonify({
            "status": "success",
            "wellness_insights_enabled": result,
            "enabled_insight_types": insight_types,
            "available_insights": [
                "digital_fatigue",
                "attention_pattern",
                "stress_trend",
                "focus_optimization"
            ],
            "note": "All wellness insights are opt-in and for self-reflection only",
            "privacy": "Data processed locally, user-controlled retention"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/wellness/<insight_type>', methods=['GET'])
def get_wellness_insight():
    """Get specific wellness insight (user-facing, opt-in only)"""
    try:
        insight_type = request.view_args['insight_type']
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        insight = reflex_service.get_wellness_insight(user_id, insight_type)
        
        if insight is None:
            return jsonify({
                "status": "not_available",
                "message": f"{insight_type} insight not available",
                "note": "Wellness insights require explicit opt-in"
            })
        
        return jsonify({
            "status": "success",
            "insight_type": insight.insight_type,
            "summary": insight.summary,
            "data_points": insight.data_points,
            "visualization_data": insight.visualization_data,
            "timestamp": insight.timestamp.isoformat(),
            "opt_in_explicit": insight.opt_in_explicit,
            "category": "user_facing_wellness"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/layout', methods=['GET'])
def get_layout_state():
    """Get current layout state with applied tags"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        layout_state = reflex_service.get_layout_state(user_id)
        
        return jsonify({
            "status": "success",
            "layout_state": layout_state,
            "note": "Current UI element tags and hierarchy"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/revert', methods=['POST'])
def revert_last_command():
    """Revert the last applied command"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        success = reflex_service.revert_last_command(user_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Last command reverted",
                "note": "User has full control over all interface changes"
            })
        else:
            return jsonify({
                "status": "no_changes",
                "message": "No reversible changes to revert"
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/settings', methods=['GET'])
def get_user_settings():
    """Get current user settings"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        settings = reflex_service.get_user_settings(user_id)
        
        return jsonify({
            "status": "success",
            "settings": {
                "passive_tier_enabled": settings.passive_tier_enabled,
                "semi_active_tier_enabled": settings.semi_active_tier_enabled,
                "active_tier_enabled": settings.active_tier_enabled,
                "wellness_insights_enabled": settings.wellness_insights_enabled,
                "system_metrics_enabled": settings.system_metrics_enabled,
                "biometric_processing_local_only": settings.biometric_processing_local_only,
                "data_retention_days": settings.data_retention_days,
                "auto_summarize_changes": settings.auto_summarize_changes,
                "adaptation_sensitivity": settings.adaptation_sensitivity
            },
            "system_focus": "Elite Commander superuser dashboard",
            "privacy_first": "Biometric processing local only, user controlled"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/export', methods=['GET'])
def export_user_data():
    """Export user data (privacy compliant)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        data = reflex_service.export_user_data(user_id)
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "data": data,
            "privacy_note": "Only non-sensitive data exported",
            "data_control": "User has full control over data retention and deletion"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/tags/available', methods=['GET'])
def get_available_tags():
    """Get available UI tags and their relationships"""
    try:
        tags_info = {}
        
        for tag_name, tag in reflex_service.tag_registry.tags.items():
            tags_info[tag_name] = {
                "category": tag.category,
                "conflicts_with": tag.conflicts_with,
                "description": f"{tag.category} tag: {tag_name}"
            }
        
        return jsonify({
            "status": "success",
            "available_tags": tags_info,
            "categories": ["style", "layout", "density", "mood"],
            "note": "Tags define UI element properties and adaptation targets"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@command_reflex_bp.route('/system/metrics', methods=['GET'])
def get_system_metrics_summary():
    """Get system metrics summary (internal use, aggregated only)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        settings = reflex_service.get_user_settings(user_id)
        
        if not settings.system_metrics_enabled:
            return jsonify({
                "status": "disabled",
                "message": "System metrics collection disabled"
            })
        
        # Return only aggregated, non-sensitive metrics
        user_metrics = reflex_service.system_metrics.get(user_id, [])
        
        summary = {
            "total_commands": len(user_metrics),
            "successful_adaptations": len([m for m in user_metrics if m.context.get("applied", False)]),
            "tier_usage": {
                "passive": len([m for m in user_metrics if m.context.get("tier") == "passive"]),
                "semi_active": len([m for m in user_metrics if m.context.get("tier") == "semi_active"]),
                "active": len([m for m in user_metrics if m.context.get("tier") == "active"])
            }
        }
        
        return jsonify({
            "status": "success",
            "metrics_summary": summary,
            "note": "System metrics are used for internal adaptation only",
            "privacy": "Individual biometric data never exposed"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

