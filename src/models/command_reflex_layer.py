"""
Command Reflex Layer - Unified AURA System

Replaces the previous Mirror Protocol with a simplified, unified approach:
- Command Reflex Layer = Context-aware system responsiveness
- Three tiers: Passive (AURA), Semi-active (Mirror), Active (Direct commands)
- Eliminates redundancy and conceptual drift
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
import json

class ReflexTier(Enum):
    """Three tiers of Command Reflex Layer"""
    PASSIVE = "passive"      # AURA biometric-reactive, continuous
    SEMI_ACTIVE = "semi_active"  # Mirror suggestions and feedback
    ACTIVE = "active"        # Direct user commands

class EntryMode(Enum):
    """Simplified interaction modes"""
    MIRROR = "mirror"        # Freeform feedback + adaptation: "Too noisy", "Feels sharp"
    EDIT = "edit"           # Element-specific: "Make this card smaller"
    OBSERVE = "observe"     # Passive biometric reflection

class MetricType(Enum):
    """Clear separation of metric types"""
    SYSTEM_FACING = "system_facing"    # Invisible, internal adaptation only
    USER_FACING = "user_facing"       # Optional, opt-in, visualized

@dataclass
class UITag:
    """Simplified tag system for UI elements"""
    name: str
    category: str  # style, layout, density, mood
    weight: float  # 0.0 to 1.0
    conflicts_with: List[str] = None  # Tags that conflict with this one
    
    def __post_init__(self):
        if self.conflicts_with is None:
            self.conflicts_with = []

@dataclass
class UIElement:
    """UI element with tag-based properties"""
    element_id: str
    element_type: str  # card, panel, button, etc.
    current_tags: Dict[str, float]  # tag_name -> weight
    parent_id: Optional[str] = None
    children: List[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class ReflexCommand:
    """Unified command structure for all tiers"""
    user_id: str
    timestamp: datetime
    tier: ReflexTier
    entry_mode: EntryMode
    raw_input: str
    parsed_intent: Dict[str, any]
    target_elements: List[str]
    tag_changes: Dict[str, float]
    applied: bool = False
    reversible: bool = True

@dataclass
class BiometricSignal:
    """Simplified biometric data for passive tier"""
    user_id: str
    timestamp: datetime
    signal_type: str  # fatigue, stress, attention, tension
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    system_facing_only: bool = True  # Never shown to user unless opted in

@dataclass
class SystemMetric:
    """System-facing metrics (invisible to user)"""
    metric_id: str
    user_id: str
    timestamp: datetime
    metric_type: MetricType
    value: float
    context: Dict[str, any]
    used_for_adaptation: bool = True

@dataclass
class WellnessInsight:
    """User-facing wellness metrics (opt-in only)"""
    insight_id: str
    user_id: str
    timestamp: datetime
    insight_type: str  # digital_fatigue, attention_pattern, stress_trend
    summary: str
    data_points: List[Dict]
    visualization_data: Dict
    opt_in_explicit: bool = True

class TagRegistry:
    """Central registry for all UI tags and their relationships"""
    
    def __init__(self):
        self.tags = {}
        self.conflicts = {}
        self.load_default_tags()
    
    def load_default_tags(self):
        """Load default tag definitions"""
        default_tags = {
            # Style tags
            "sharp": UITag("sharp", "style", 0.0, ["smooth", "soft"]),
            "smooth": UITag("smooth", "style", 0.0, ["sharp", "harsh"]),
            "soft": UITag("soft", "style", 0.0, ["sharp", "harsh"]),
            "harsh": UITag("harsh", "style", 0.0, ["smooth", "soft"]),
            "calm": UITag("calm", "style", 0.0, ["energetic", "vibrant"]),
            "energetic": UITag("energetic", "style", 0.0, ["calm", "muted"]),
            
            # Layout tags
            "dense": UITag("dense", "layout", 0.0, ["open", "spacious"]),
            "open": UITag("open", "layout", 0.0, ["dense", "compact"]),
            "spacious": UITag("spacious", "layout", 0.0, ["dense", "compact"]),
            "compact": UITag("compact", "layout", 0.0, ["open", "spacious"]),
            "focused": UITag("focused", "layout", 0.0, ["scattered"]),
            "minimal": UITag("minimal", "layout", 0.0, ["complex", "busy"]),
            
            # Density tags
            "light": UITag("light", "density", 0.0, ["heavy", "thick"]),
            "heavy": UITag("heavy", "density", 0.0, ["light", "thin"]),
            "thin": UITag("thin", "density", 0.0, ["heavy", "thick"]),
            "thick": UITag("thick", "density", 0.0, ["light", "thin"]),
            
            # Mood tags
            "relaxed": UITag("relaxed", "mood", 0.0, ["tense", "urgent"]),
            "alert": UITag("alert", "mood", 0.0, ["drowsy", "passive"]),
            "urgent": UITag("urgent", "mood", 0.0, ["relaxed", "calm"]),
            "passive": UITag("passive", "mood", 0.0, ["alert", "active"])
        }
        
        for tag_name, tag in default_tags.items():
            self.register_tag(tag)
    
    def register_tag(self, tag: UITag):
        """Register a new tag"""
        self.tags[tag.name] = tag
        for conflict in tag.conflicts_with:
            if conflict not in self.conflicts:
                self.conflicts[conflict] = []
            self.conflicts[conflict].append(tag.name)
    
    def get_conflicts(self, tag_name: str) -> List[str]:
        """Get tags that conflict with the given tag"""
        return self.tags.get(tag_name, UITag("", "", 0.0)).conflicts_with
    
    def resolve_conflict(self, current_tags: Dict[str, float], new_tag: str, new_weight: float) -> Dict[str, float]:
        """Resolve tag conflicts by reducing conflicting tag weights"""
        result = current_tags.copy()
        conflicts = self.get_conflicts(new_tag)
        
        for conflict in conflicts:
            if conflict in result:
                # Reduce conflicting tag weight
                result[conflict] = max(0.0, result[conflict] - new_weight * 0.7)
        
        result[new_tag] = new_weight
        return result

class LayoutTree:
    """Hierarchical representation of UI layout"""
    
    def __init__(self):
        self.elements = {}
        self.root_elements = []
        self.load_default_layout()
    
    def load_default_layout(self):
        """Load default layout structure"""
        # Main dashboard structure
        dashboard = UIElement("dashboard", "container", {"minimal": 0.3, "focused": 0.5})
        header = UIElement("header", "panel", {"compact": 0.4}, "dashboard")
        main_content = UIElement("main_content", "container", {"open": 0.6}, "dashboard")
        sidebar = UIElement("sidebar", "panel", {"dense": 0.3}, "dashboard")
        
        # Add to tree
        dashboard.children = ["header", "main_content", "sidebar"]
        
        self.elements = {
            "dashboard": dashboard,
            "header": header,
            "main_content": main_content,
            "sidebar": sidebar
        }
        self.root_elements = ["dashboard"]
    
    def add_element(self, element: UIElement):
        """Add element to layout tree"""
        self.elements[element.element_id] = element
        if element.parent_id and element.parent_id in self.elements:
            parent = self.elements[element.parent_id]
            if element.element_id not in parent.children:
                parent.children.append(element.element_id)
    
    def update_element_tags(self, element_id: str, tag_changes: Dict[str, float]):
        """Update tags for a specific element"""
        if element_id in self.elements:
            element = self.elements[element_id]
            tag_registry = TagRegistry()
            
            for tag_name, weight in tag_changes.items():
                element.current_tags = tag_registry.resolve_conflict(
                    element.current_tags, tag_name, weight
                )
    
    def propagate_changes(self, element_id: str, propagation_factor: float = 0.3):
        """Propagate tag changes to child elements"""
        if element_id not in self.elements:
            return
        
        element = self.elements[element_id]
        for child_id in element.children:
            if child_id in self.elements:
                child = self.elements[child_id]
                for tag_name, weight in element.current_tags.items():
                    if tag_name in child.current_tags:
                        # Blend parent influence with child's current state
                        child.current_tags[tag_name] = (
                            child.current_tags[tag_name] * (1 - propagation_factor) +
                            weight * propagation_factor
                        )

class PromptParser:
    """Unified prompt parser for all entry modes"""
    
    def __init__(self):
        self.tag_registry = TagRegistry()
        self.intent_patterns = self._load_intent_patterns()
    
    def _load_intent_patterns(self) -> Dict[str, Dict]:
        """Load patterns for parsing user intents"""
        return {
            "style_feedback": {
                "patterns": [
                    "too harsh", "feels sharp", "too aggressive", "too bright",
                    "too soft", "too muted", "too calm", "needs energy"
                ],
                "tag_mappings": {
                    "harsh|sharp|aggressive|bright": {"smooth": 0.7, "calm": 0.5},
                    "soft|muted|calm": {"energetic": 0.6, "sharp": 0.4},
                    "noisy|busy|cluttered": {"minimal": 0.8, "open": 0.6},
                    "empty|sparse|boring": {"dense": 0.5, "energetic": 0.4}
                }
            },
            "layout_feedback": {
                "patterns": [
                    "too dense", "too crowded", "too spacious", "too empty",
                    "hard to focus", "too scattered", "needs organization"
                ],
                "tag_mappings": {
                    "dense|crowded|packed": {"open": 0.8, "spacious": 0.6},
                    "spacious|empty|sparse": {"dense": 0.6, "compact": 0.5},
                    "scattered|disorganized": {"focused": 0.8, "minimal": 0.5},
                    "hard to focus": {"focused": 0.9, "minimal": 0.7}
                }
            },
            "element_specific": {
                "patterns": [
                    "make this smaller", "make this bigger", "hide this",
                    "emphasize this", "move this", "change color"
                ],
                "tag_mappings": {
                    "smaller|reduce|shrink": {"compact": 0.8, "minimal": 0.6},
                    "bigger|larger|expand": {"open": 0.7, "spacious": 0.5},
                    "hide|remove|less": {"minimal": 0.9, "light": 0.7},
                    "emphasize|highlight|focus": {"focused": 0.8, "alert": 0.6}
                }
            }
        }
    
    def parse(self, raw_input: str, entry_mode: EntryMode, context: Dict = None) -> Dict[str, any]:
        """Parse user input into structured intent"""
        raw_input_lower = raw_input.lower()
        
        intent = {
            "entry_mode": entry_mode,
            "raw_input": raw_input,
            "detected_patterns": [],
            "tag_changes": {},
            "target_elements": [],
            "confidence": 0.0
        }
        
        # Determine which patterns to check based on entry mode
        if entry_mode == EntryMode.MIRROR:
            pattern_categories = ["style_feedback", "layout_feedback"]
        elif entry_mode == EntryMode.EDIT:
            pattern_categories = ["element_specific"]
        else:  # OBSERVE
            return intent  # No parsing needed for passive observation
        
        # Check patterns and extract intent
        for category in pattern_categories:
            patterns = self.intent_patterns[category]
            for pattern_group, tag_mapping in patterns["tag_mappings"].items():
                pattern_words = pattern_group.split("|")
                if any(word in raw_input_lower for word in pattern_words):
                    intent["detected_patterns"].append(pattern_group)
                    intent["tag_changes"].update(tag_mapping)
                    intent["confidence"] = max(intent["confidence"], 0.8)
        
        # Extract target elements if specified
        if "this" in raw_input_lower and context and "current_element" in context:
            intent["target_elements"].append(context["current_element"])
        
        return intent

@dataclass
class CommandReflexSettings:
    """Unified settings for Command Reflex Layer"""
    user_id: str
    passive_tier_enabled: bool = False  # AURA biometric reactions (default OFF)
    semi_active_tier_enabled: bool = True  # Mirror suggestions
    active_tier_enabled: bool = True  # Direct commands
    
    # Metric preferences
    system_metrics_enabled: bool = True  # Internal adaptation metrics
    wellness_insights_enabled: bool = False  # User-facing insights (opt-in)
    
    # Privacy settings
    biometric_processing_local_only: bool = True
    data_retention_days: int = 7
    auto_summarize_changes: bool = True  # "We adjusted colors based on signs of fatigue"
    
    # Adaptation settings
    adaptation_sensitivity: float = 0.5  # 0.0 to 1.0
    propagation_factor: float = 0.3  # How much changes affect child elements
    conflict_resolution_aggressive: bool = False  # How strongly to resolve tag conflicts

