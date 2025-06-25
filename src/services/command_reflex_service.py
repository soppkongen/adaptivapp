"""
Command Reflex Layer Service

Unified service replacing AURA Mirror Protocol with simplified approach:
- Single system with three tiers: Passive, Semi-active, Active
- Eliminates redundancy between AURA and Mirror Protocol
- Clear separation of system vs user-facing metrics
- Focused on Elite Commander mission: enhance decision velocity
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from ..models.command_reflex_layer import (
    ReflexTier, EntryMode, MetricType, UITag, UIElement, ReflexCommand,
    BiometricSignal, SystemMetric, WellnessInsight, TagRegistry, LayoutTree,
    PromptParser, CommandReflexSettings
)

class CommandReflexService:
    """Unified service for all Command Reflex Layer functionality"""
    
    def __init__(self):
        self.tag_registry = TagRegistry()
        self.layout_tree = LayoutTree()
        self.prompt_parser = PromptParser()
        self.user_settings = {}
        self.command_history = {}
        self.system_metrics = {}
        self.wellness_insights = {}
        
        # Load configuration files
        self._load_tags_config()
        self._load_layout_config()
    
    def _load_tags_config(self):
        """Load tags.json configuration"""
        try:
            # In production, this would load from actual tags.json file
            # For now, using the default tags from TagRegistry
            pass
        except Exception as e:
            logging.warning(f"Could not load tags.json, using defaults: {e}")
    
    def _load_layout_config(self):
        """Load layout_tree.json configuration"""
        try:
            # In production, this would load from actual layout_tree.json file
            # For now, using the default layout from LayoutTree
            pass
        except Exception as e:
            logging.warning(f"Could not load layout_tree.json, using defaults: {e}")
    
    def initialize_user(self, user_id: str) -> CommandReflexSettings:
        """Initialize Command Reflex Layer for a user"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = CommandReflexSettings(user_id=user_id)
            self.command_history[user_id] = []
            self.system_metrics[user_id] = []
            self.wellness_insights[user_id] = []
        
        return self.user_settings[user_id]
    
    def process_command(self, user_id: str, raw_input: str, entry_mode: EntryMode, 
                       context: Dict = None) -> ReflexCommand:
        """Process user command through unified system"""
        settings = self.get_user_settings(user_id)
        
        # Determine tier based on entry mode
        if entry_mode == EntryMode.OBSERVE:
            tier = ReflexTier.PASSIVE
        elif entry_mode == EntryMode.MIRROR:
            tier = ReflexTier.SEMI_ACTIVE
        else:  # EDIT
            tier = ReflexTier.ACTIVE
        
        # Check if tier is enabled
        if not self._is_tier_enabled(settings, tier):
            raise ValueError(f"{tier.value} tier is disabled for user {user_id}")
        
        # Parse the input
        parsed_intent = self.prompt_parser.parse(raw_input, entry_mode, context)
        
        # Create command
        command = ReflexCommand(
            user_id=user_id,
            timestamp=datetime.now(),
            tier=tier,
            entry_mode=entry_mode,
            raw_input=raw_input,
            parsed_intent=parsed_intent,
            target_elements=parsed_intent.get("target_elements", []),
            tag_changes=parsed_intent.get("tag_changes", {})
        )
        
        # Apply changes to layout tree
        if command.tag_changes:
            self._apply_tag_changes(command)
            command.applied = True
            
            # Auto-summarize if enabled
            if settings.auto_summarize_changes:
                command.parsed_intent["summary"] = self._generate_change_summary(command)
        
        # Store in history
        self.command_history[user_id].append(command)
        
        # Record system metrics
        self._record_system_metrics(user_id, command)
        
        return command
    
    def process_biometric_signals(self, user_id: str, signals: List[BiometricSignal]) -> Optional[ReflexCommand]:
        """Process biometric signals for passive tier adaptation"""
        settings = self.get_user_settings(user_id)
        
        if not settings.passive_tier_enabled:
            return None
        
        # Analyze signals for adaptation needs
        adaptation_needed = self._analyze_biometric_signals(signals, settings)
        
        if not adaptation_needed:
            return None
        
        # Generate adaptive response
        tag_changes = self._biometric_signals_to_tags(signals, settings)
        
        if not tag_changes:
            return None
        
        # Create passive command
        command = ReflexCommand(
            user_id=user_id,
            timestamp=datetime.now(),
            tier=ReflexTier.PASSIVE,
            entry_mode=EntryMode.OBSERVE,
            raw_input="[Biometric adaptation]",
            parsed_intent={
                "signals": [s.__dict__ for s in signals],
                "adaptation_reason": self._get_adaptation_reason(signals)
            },
            target_elements=["dashboard"],  # Apply to main interface
            tag_changes=tag_changes
        )
        
        # Apply changes gradually
        self._apply_tag_changes(command, gradual=True)
        command.applied = True
        
        # Auto-summarize
        if settings.auto_summarize_changes:
            command.parsed_intent["summary"] = f"Adjusted interface based on {command.parsed_intent['adaptation_reason']}"
        
        # Store in history
        self.command_history[user_id].append(command)
        
        # Record system metrics
        self._record_system_metrics(user_id, command)
        
        return command
    
    def _is_tier_enabled(self, settings: CommandReflexSettings, tier: ReflexTier) -> bool:
        """Check if a tier is enabled for the user"""
        if tier == ReflexTier.PASSIVE:
            return settings.passive_tier_enabled
        elif tier == ReflexTier.SEMI_ACTIVE:
            return settings.semi_active_tier_enabled
        else:  # ACTIVE
            return settings.active_tier_enabled
    
    def _apply_tag_changes(self, command: ReflexCommand, gradual: bool = False):
        """Apply tag changes to layout tree"""
        settings = self.get_user_settings(command.user_id)
        
        # Apply to target elements or default to main areas
        target_elements = command.target_elements or ["main_content"]
        
        for element_id in target_elements:
            # Apply tag changes with sensitivity adjustment
            adjusted_changes = {}
            for tag_name, weight in command.tag_changes.items():
                adjusted_weight = weight * settings.adaptation_sensitivity
                if gradual:
                    adjusted_weight *= 0.5  # Reduce intensity for passive changes
                adjusted_changes[tag_name] = adjusted_weight
            
            self.layout_tree.update_element_tags(element_id, adjusted_changes)
            
            # Propagate to children if enabled
            if settings.propagation_factor > 0:
                self.layout_tree.propagate_changes(element_id, settings.propagation_factor)
    
    def _analyze_biometric_signals(self, signals: List[BiometricSignal], 
                                 settings: CommandReflexSettings) -> bool:
        """Analyze if biometric signals warrant interface adaptation"""
        if not signals:
            return False
        
        # Check for significant signals above threshold
        significant_signals = [
            s for s in signals 
            if s.intensity > 0.6 and s.confidence > 0.7
        ]
        
        if not significant_signals:
            return False
        
        # Check for fatigue or stress patterns
        fatigue_signals = [s for s in significant_signals if s.signal_type in ["fatigue", "eye_strain"]]
        stress_signals = [s for s in significant_signals if s.signal_type in ["stress", "tension"]]
        
        return len(fatigue_signals) > 0 or len(stress_signals) > 1
    
    def _biometric_signals_to_tags(self, signals: List[BiometricSignal], 
                                 settings: CommandReflexSettings) -> Dict[str, float]:
        """Convert biometric signals to UI tag changes"""
        tag_changes = {}
        
        for signal in signals:
            if signal.intensity < 0.6 or signal.confidence < 0.7:
                continue
            
            # Map signal types to tag adjustments
            if signal.signal_type == "fatigue":
                tag_changes.update({
                    "soft": 0.6,
                    "calm": 0.5,
                    "light": 0.4,
                    "spacious": 0.3
                })
            elif signal.signal_type == "stress":
                tag_changes.update({
                    "calm": 0.7,
                    "smooth": 0.5,
                    "relaxed": 0.6,
                    "minimal": 0.4
                })
            elif signal.signal_type == "eye_strain":
                tag_changes.update({
                    "soft": 0.8,
                    "light": 0.7,
                    "spacious": 0.5
                })
            elif signal.signal_type == "attention_drift":
                tag_changes.update({
                    "focused": 0.7,
                    "minimal": 0.6,
                    "alert": 0.4
                })
        
        return tag_changes
    
    def _get_adaptation_reason(self, signals: List[BiometricSignal]) -> str:
        """Generate human-readable adaptation reason"""
        signal_types = [s.signal_type for s in signals if s.intensity > 0.6]
        
        if "fatigue" in signal_types:
            return "signs of fatigue"
        elif "stress" in signal_types:
            return "elevated stress indicators"
        elif "eye_strain" in signal_types:
            return "eye strain detection"
        elif "attention_drift" in signal_types:
            return "attention drift patterns"
        else:
            return "biometric feedback"
    
    def _generate_change_summary(self, command: ReflexCommand) -> str:
        """Generate human-readable summary of changes"""
        if not command.tag_changes:
            return "No changes applied"
        
        # Group changes by category
        style_changes = []
        layout_changes = []
        
        for tag_name, weight in command.tag_changes.items():
            tag = self.tag_registry.tags.get(tag_name)
            if tag:
                if tag.category == "style":
                    style_changes.append(f"more {tag_name}")
                elif tag.category == "layout":
                    layout_changes.append(f"more {tag_name}")
        
        summary_parts = []
        if style_changes:
            summary_parts.append(f"Style: {', '.join(style_changes)}")
        if layout_changes:
            summary_parts.append(f"Layout: {', '.join(layout_changes)}")
        
        return "; ".join(summary_parts) if summary_parts else "Interface adjusted"
    
    def _record_system_metrics(self, user_id: str, command: ReflexCommand):
        """Record system-facing metrics for internal adaptation"""
        settings = self.get_user_settings(user_id)
        
        if not settings.system_metrics_enabled:
            return
        
        # Record command effectiveness metric
        metric = SystemMetric(
            metric_id=f"command_{len(self.system_metrics[user_id])}",
            user_id=user_id,
            timestamp=datetime.now(),
            metric_type=MetricType.SYSTEM_FACING,
            value=command.parsed_intent.get("confidence", 0.0),
            context={
                "tier": command.tier.value,
                "entry_mode": command.entry_mode.value,
                "tag_changes_count": len(command.tag_changes),
                "applied": command.applied
            }
        )
        
        self.system_metrics[user_id].append(metric)
    
    def toggle_tier(self, user_id: str, tier: ReflexTier, enabled: bool) -> bool:
        """Toggle a specific tier on/off"""
        settings = self.get_user_settings(user_id)
        
        if tier == ReflexTier.PASSIVE:
            settings.passive_tier_enabled = enabled
        elif tier == ReflexTier.SEMI_ACTIVE:
            settings.semi_active_tier_enabled = enabled
        else:  # ACTIVE
            settings.active_tier_enabled = enabled
        
        return enabled
    
    def enable_wellness_insights(self, user_id: str, insight_types: List[str]) -> bool:
        """Enable specific wellness insights (opt-in only)"""
        settings = self.get_user_settings(user_id)
        settings.wellness_insights_enabled = True
        
        # Generate sample insights for enabled types
        for insight_type in insight_types:
            insight = self._generate_wellness_insight(user_id, insight_type)
            if insight:
                self.wellness_insights[user_id].append(insight)
        
        return True
    
    def _generate_wellness_insight(self, user_id: str, insight_type: str) -> Optional[WellnessInsight]:
        """Generate a wellness insight for the user"""
        if insight_type == "digital_fatigue":
            return WellnessInsight(
                insight_id=f"fatigue_{int(datetime.now().timestamp())}",
                user_id=user_id,
                timestamp=datetime.now(),
                insight_type=insight_type,
                summary="Your digital fatigue patterns show increased strain during afternoon sessions",
                data_points=[
                    {"time": "14:00", "fatigue_level": 0.3},
                    {"time": "15:00", "fatigue_level": 0.6},
                    {"time": "16:00", "fatigue_level": 0.8}
                ],
                visualization_data={
                    "chart_type": "line",
                    "x_axis": "time",
                    "y_axis": "fatigue_level",
                    "trend": "increasing"
                }
            )
        elif insight_type == "attention_pattern":
            return WellnessInsight(
                insight_id=f"attention_{int(datetime.now().timestamp())}",
                user_id=user_id,
                timestamp=datetime.now(),
                insight_type=insight_type,
                summary="You maintain focus best during 25-minute intervals with 5-minute breaks",
                data_points=[
                    {"interval": "0-25min", "focus_score": 0.9},
                    {"interval": "25-50min", "focus_score": 0.6},
                    {"interval": "50-75min", "focus_score": 0.4}
                ],
                visualization_data={
                    "chart_type": "bar",
                    "recommendation": "Consider 25-minute focused work blocks"
                }
            )
        
        return None
    
    def get_wellness_insight(self, user_id: str, insight_type: str) -> Optional[WellnessInsight]:
        """Get specific wellness insight for user"""
        settings = self.get_user_settings(user_id)
        
        if not settings.wellness_insights_enabled:
            return None
        
        # Find most recent insight of requested type
        user_insights = self.wellness_insights.get(user_id, [])
        for insight in reversed(user_insights):
            if insight.insight_type == insight_type:
                return insight
        
        return None
    
    def revert_last_command(self, user_id: str) -> bool:
        """Revert the last applied command"""
        history = self.command_history.get(user_id, [])
        
        # Find last applied command
        for command in reversed(history):
            if command.applied and command.reversible:
                # Reverse tag changes
                reversed_changes = {
                    tag: -weight for tag, weight in command.tag_changes.items()
                }
                
                # Apply reversed changes
                for element_id in command.target_elements:
                    self.layout_tree.update_element_tags(element_id, reversed_changes)
                
                command.applied = False
                return True
        
        return False
    
    def get_user_settings(self, user_id: str) -> CommandReflexSettings:
        """Get user settings, initializing if needed"""
        if user_id not in self.user_settings:
            self.initialize_user(user_id)
        return self.user_settings[user_id]
    
    def get_layout_state(self, user_id: str) -> Dict:
        """Get current layout state for user"""
        return {
            "elements": {
                element_id: {
                    "type": element.element_type,
                    "tags": element.current_tags,
                    "parent": element.parent_id,
                    "children": element.children
                }
                for element_id, element in self.layout_tree.elements.items()
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def export_user_data(self, user_id: str) -> Dict:
        """Export user data for privacy compliance"""
        settings = self.get_user_settings(user_id)
        
        # Only export non-sensitive data
        export_data = {
            "settings": {
                "passive_tier_enabled": settings.passive_tier_enabled,
                "semi_active_tier_enabled": settings.semi_active_tier_enabled,
                "active_tier_enabled": settings.active_tier_enabled,
                "wellness_insights_enabled": settings.wellness_insights_enabled
            },
            "command_history_count": len(self.command_history.get(user_id, [])),
            "layout_customizations": len([
                cmd for cmd in self.command_history.get(user_id, [])
                if cmd.applied and cmd.tier == ReflexTier.ACTIVE
            ])
        }
        
        # Include wellness insights if enabled
        if settings.wellness_insights_enabled:
            export_data["wellness_insights"] = [
                {
                    "type": insight.insight_type,
                    "summary": insight.summary,
                    "timestamp": insight.timestamp.isoformat()
                }
                for insight in self.wellness_insights.get(user_id, [])
            ]
        
        return export_data

