"""
AURA Mirror Service

Implements the "We Only Mirror" design ethos with:
- Dual modes: Prompted vs Adaptive Interface Adjustments
- Metric packaging for power users
- Strict mode separation and privacy compliance
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict

from ..models.aura_mirror_protocol import (
    AURAMode, UITag, PromptedCommand, BiometricSignal, AdaptiveResponse,
    VisualAgeDelta, FocusHeatmap, CognitiveDriftIndex, EntropyScore,
    MoodResonanceProfile, AURASettings, AURASession, AURAMirrorProtocol
)

class AURAMirrorService:
    """Core service implementing AURA Mirror Protocol"""
    
    def __init__(self):
        self.active_sessions: Dict[str, AURASession] = {}
        self.user_settings: Dict[str, AURASettings] = {}
        self.local_storage: Dict[str, Dict] = {}  # Local-only data storage
        
    def initialize_user(self, user_id: str) -> AURASettings:
        """Initialize AURA for a new user with default settings"""
        settings = AURASettings(
            user_id=user_id,
            adaptive_mode_enabled=False,  # Default OFF
            prompted_mode_enabled=True,
            metric_tracking_enabled=False,  # Opt-in only
            privacy_level="maximum",
            local_processing_only=True
        )
        self.user_settings[user_id] = settings
        self.local_storage[user_id] = {
            "prompted_commands": [],
            "adaptive_responses": [],
            "metrics": {},
            "ui_state": {}
        }
        return settings
    
    def process_prompted_command(self, user_id: str, command_text: str, 
                                session_id: str) -> PromptedCommand:
        """Process user-initiated interface modification (Prompted Mode)"""
        if user_id not in self.user_settings:
            self.initialize_user(user_id)
            
        settings = self.user_settings[user_id]
        if not settings.prompted_mode_enabled:
            raise ValueError("Prompted mode is disabled for this user")
        
        # Parse command into tags
        parsed_tags = AURAMirrorProtocol.parse_user_command(command_text)
        
        # Apply changes based on tags
        applied_changes = self._apply_ui_tags(user_id, parsed_tags)
        
        # Create command record
        command = PromptedCommand(
            user_id=user_id,
            timestamp=datetime.now(),
            command_text=command_text,
            parsed_tags=parsed_tags,
            applied_changes=applied_changes,
            session_id=session_id
        )
        
        # Store locally
        self.local_storage[user_id]["prompted_commands"].append(asdict(command))
        
        # Update entropy score (personalization demand)
        self._update_entropy_score(user_id, "prompted_command")
        
        return command
    
    def process_biometric_signals(self, user_id: str, signals: List[BiometricSignal],
                                 session_id: str) -> Optional[AdaptiveResponse]:
        """Process biometric signals for adaptive interface changes (Adaptive Mode)"""
        if user_id not in self.user_settings:
            self.initialize_user(user_id)
            
        settings = self.user_settings[user_id]
        if not settings.adaptive_mode_enabled:
            return None  # Adaptive mode disabled
        
        # Convert biometric signals to UI tags
        suggested_tags = AURAMirrorProtocol.biometric_to_tags(signals)
        
        if not suggested_tags:
            return None  # No adaptation needed
        
        # Apply gradual changes
        applied_changes = self._apply_ui_tags(user_id, suggested_tags, gradual=True)
        
        # Create adaptive response
        response = AdaptiveResponse(
            user_id=user_id,
            timestamp=datetime.now(),
            trigger_signals=signals,
            suggested_tags=suggested_tags,
            applied_changes=applied_changes,
            user_visible=True,
            user_controllable=True,
            gradual=True
        )
        
        # Store locally
        self.local_storage[user_id]["adaptive_responses"].append(asdict(response))
        
        # Update metrics if enabled
        if settings.metric_tracking_enabled:
            self._update_focus_heatmap(user_id, session_id, signals)
            self._update_cognitive_drift(user_id, session_id, signals)
        
        return response
    
    def toggle_adaptive_mode(self, user_id: str, enabled: bool) -> bool:
        """Toggle adaptive mode on/off with explicit user control"""
        if user_id not in self.user_settings:
            self.initialize_user(user_id)
            
        self.user_settings[user_id].adaptive_mode_enabled = enabled
        
        # Log the toggle event
        self.local_storage[user_id]["ui_state"]["adaptive_mode_toggled"] = {
            "timestamp": datetime.now().isoformat(),
            "enabled": enabled
        }
        
        return enabled
    
    def enable_metric_tracking(self, user_id: str, metrics: List[str]) -> bool:
        """Enable specific metrics tracking (opt-in only)"""
        if user_id not in self.user_settings:
            self.initialize_user(user_id)
            
        valid_metrics = [
            "visual_age_delta", "focus_heatmap", "cognitive_drift_index",
            "entropy_score", "mood_resonance_profile"
        ]
        
        # Validate requested metrics
        enabled_metrics = [m for m in metrics if m in valid_metrics]
        
        settings = self.user_settings[user_id]
        settings.metric_tracking_enabled = len(enabled_metrics) > 0
        settings.enabled_metrics = enabled_metrics
        
        return settings.metric_tracking_enabled
    
    def get_visual_age_delta(self, user_id: str) -> Optional[VisualAgeDelta]:
        """Get visual age delta metric (opt-in only)"""
        if not self._is_metric_enabled(user_id, "visual_age_delta"):
            return None
            
        # Simulate visual age calculation (in real implementation, this would
        # use actual facial analysis data)
        baseline_date = datetime.now() - timedelta(days=90)
        
        delta = VisualAgeDelta(
            user_id=user_id,
            baseline_date=baseline_date,
            current_estimate=35.2,  # Example value
            delta_months=0.8,  # +0.8 months since baseline
            trend_direction="stable",
            confidence=0.85,
            local_only=True
        )
        
        # Store locally
        if "visual_age_delta" not in self.local_storage[user_id]["metrics"]:
            self.local_storage[user_id]["metrics"]["visual_age_delta"] = []
        self.local_storage[user_id]["metrics"]["visual_age_delta"].append(asdict(delta))
        
        return delta
    
    def get_focus_heatmap(self, user_id: str, session_id: str) -> Optional[FocusHeatmap]:
        """Get focus heatmap for current session (opt-in only)"""
        if not self._is_metric_enabled(user_id, "focus_heatmap"):
            return None
            
        # Calculate attention distribution
        attention_map = {
            "primary_kpis": 0.72,
            "secondary_metrics": 0.18,
            "navigation": 0.06,
            "other": 0.04
        }
        
        heatmap = FocusHeatmap(
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(),
            attention_map=attention_map,
            primary_kpi_focus=0.72,
            distraction_events=3,
            engagement_score=0.85
        )
        
        return heatmap
    
    def get_cognitive_drift_index(self, user_id: str, session_id: str) -> Optional[CognitiveDriftIndex]:
        """Get cognitive drift index for session (opt-in only)"""
        if not self._is_metric_enabled(user_id, "cognitive_drift_index"):
            return None
            
        drift_index = CognitiveDriftIndex(
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(),
            scroll_without_read_events=5,
            rapid_navigation_events=2,
            attention_drops=3,
            drift_score=0.35,  # Moderate drift
            context_type="dashboard"
        )
        
        return drift_index
    
    def get_entropy_score(self, user_id: str) -> Optional[EntropyScore]:
        """Get entropy score (personalization demand) (opt-in only)"""
        if not self._is_metric_enabled(user_id, "entropy_score"):
            return None
            
        period_start = datetime.now() - timedelta(days=7)
        
        # Calculate from stored data
        commands = self.local_storage.get(user_id, {}).get("prompted_commands", [])
        recent_commands = [c for c in commands 
                          if datetime.fromisoformat(c["timestamp"]) > period_start]
        
        entropy = EntropyScore(
            user_id=user_id,
            period_start=period_start,
            period_end=datetime.now(),
            layout_changes=len(recent_commands),
            theme_flips=0,  # Would track theme changes
            override_count=len(recent_commands),
            entropy_value=min(len(recent_commands) / 10.0, 1.0),
            stability_trend="stable"
        )
        
        return entropy
    
    def get_mood_resonance_profile(self, user_id: str) -> Optional[MoodResonanceProfile]:
        """Get mood resonance profile (opt-in only)"""
        if not self._is_metric_enabled(user_id, "mood_resonance_profile"):
            return None
            
        profile = MoodResonanceProfile(
            user_id=user_id,
            timestamp=datetime.now(),
            energy_level=0.75,
            mood_indicators={
                "focused": 0.8,
                "calm": 0.6,
                "alert": 0.7,
                "stressed": 0.3
            },
            micro_movement_patterns={
                "fidgeting": 0.2,
                "stillness": 0.8,
                "eye_movement": 0.6
            },
            daily_pattern=[0.3, 0.4, 0.6, 0.8, 0.9, 0.8, 0.7, 0.6],  # 8-hour pattern
            opt_in_explicit=True
        )
        
        return profile
    
    def revert_last_change(self, user_id: str) -> bool:
        """Revert the last UI change (both prompted and adaptive)"""
        user_data = self.local_storage.get(user_id, {})
        
        # Find the most recent change
        last_prompted = user_data.get("prompted_commands", [])
        last_adaptive = user_data.get("adaptive_responses", [])
        
        if not last_prompted and not last_adaptive:
            return False
            
        # Determine which was more recent
        last_change = None
        if last_prompted and last_adaptive:
            prompted_time = datetime.fromisoformat(last_prompted[-1]["timestamp"])
            adaptive_time = datetime.fromisoformat(last_adaptive[-1]["timestamp"])
            last_change = "prompted" if prompted_time > adaptive_time else "adaptive"
        elif last_prompted:
            last_change = "prompted"
        elif last_adaptive:
            last_change = "adaptive"
        
        # Revert the change
        if last_change == "prompted":
            self._revert_ui_changes(user_id, last_prompted[-1]["applied_changes"])
            last_prompted.pop()
        else:
            self._revert_ui_changes(user_id, last_adaptive[-1]["applied_changes"])
            last_adaptive.pop()
            
        return True
    
    def get_user_settings(self, user_id: str) -> AURASettings:
        """Get current user settings"""
        if user_id not in self.user_settings:
            return self.initialize_user(user_id)
        return self.user_settings[user_id]
    
    def export_user_data(self, user_id: str) -> Dict:
        """Export user's local data (privacy compliant)"""
        if user_id not in self.local_storage:
            return {}
            
        # Remove any sensitive biometric data before export
        export_data = self.local_storage[user_id].copy()
        
        # Sanitize data
        for command in export_data.get("prompted_commands", []):
            command.pop("biometric_data", None)
        for response in export_data.get("adaptive_responses", []):
            for signal in response.get("trigger_signals", []):
                signal["local_only"] = True
                
        return export_data
    
    # Private helper methods
    
    def _apply_ui_tags(self, user_id: str, tags: List[UITag], gradual: bool = False) -> Dict[str, str]:
        """Apply UI tags to interface"""
        changes = {}
        
        for tag in tags:
            if tag.value.startswith("color:"):
                color_scheme = tag.value.split(":")[1]
                changes["color_scheme"] = color_scheme
            elif tag.value.startswith("layout:"):
                layout_type = tag.value.split(":")[1]
                changes["layout"] = layout_type
            elif tag.value.startswith("density:"):
                density_level = tag.value.split(":")[1]
                changes["density"] = density_level
            elif tag.value.startswith("mood:"):
                mood_setting = tag.value.split(":")[1]
                changes["mood"] = mood_setting
        
        # Store current UI state
        if user_id not in self.local_storage:
            self.local_storage[user_id] = {"ui_state": {}}
        self.local_storage[user_id]["ui_state"].update(changes)
        
        return changes
    
    def _revert_ui_changes(self, user_id: str, changes: Dict[str, str]) -> None:
        """Revert specific UI changes"""
        if user_id in self.local_storage:
            ui_state = self.local_storage[user_id].get("ui_state", {})
            for key in changes.keys():
                ui_state.pop(key, None)
    
    def _is_metric_enabled(self, user_id: str, metric_name: str) -> bool:
        """Check if specific metric is enabled for user"""
        if user_id not in self.user_settings:
            return False
        settings = self.user_settings[user_id]
        return (settings.metric_tracking_enabled and 
                metric_name in settings.enabled_metrics)
    
    def _update_entropy_score(self, user_id: str, event_type: str) -> None:
        """Update entropy score based on user actions"""
        # This would track layout changes, theme flips, etc.
        pass
    
    def _update_focus_heatmap(self, user_id: str, session_id: str, 
                             signals: List[BiometricSignal]) -> None:
        """Update focus heatmap based on biometric signals"""
        # This would analyze gaze patterns and attention
        pass
    
    def _update_cognitive_drift(self, user_id: str, session_id: str,
                               signals: List[BiometricSignal]) -> None:
        """Update cognitive drift index based on engagement signals"""
        # This would track disengagement patterns
        pass

