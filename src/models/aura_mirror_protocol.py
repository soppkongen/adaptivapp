"""
AURA Mirror Protocol Models

Core Design Ethos: "We Only Mirror"
- AURA operates as a responsive mirror
- Only adapts what the user can already observe
- No hidden agenda, no background nudging, no behavioral scoring
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from enum import Enum
from datetime import datetime

class AURAMode(Enum):
    """AURA operational modes"""
    PROMPTED = "prompted"  # Manual user interaction
    ADAPTIVE = "adaptive"  # Passive biometric response
    DISABLED = "disabled"  # AURA completely off

class UITag(Enum):
    """Tag-based schema for UI modifications"""
    # Color tags
    COLOR_CALM = "color:calm"
    COLOR_ENERGETIC = "color:energetic"
    COLOR_NEUTRAL = "color:neutral"
    COLOR_WARM = "color:warm"
    COLOR_COOL = "color:cool"
    
    # Layout tags
    LAYOUT_MINIMAL = "layout:minimal"
    LAYOUT_DENSE = "layout:dense"
    LAYOUT_SPACIOUS = "layout:spacious"
    LAYOUT_FOCUSED = "layout:focused"
    
    # Density tags
    DENSITY_LOW = "density:low"
    DENSITY_MEDIUM = "density:medium"
    DENSITY_HIGH = "density:high"
    
    # Mood tags
    MOOD_RELAXED = "mood:relaxed"
    MOOD_ALERT = "mood:alert"
    MOOD_FOCUSED = "mood:focused"
    MOOD_CREATIVE = "mood:creative"

@dataclass
class PromptedCommand:
    """User-initiated interface modification"""
    user_id: str
    timestamp: datetime
    command_text: str
    parsed_tags: List[UITag]
    applied_changes: Dict[str, str]
    reversible: bool = True
    session_id: Optional[str] = None

@dataclass
class BiometricSignal:
    """Raw biometric data for adaptive mode"""
    user_id: str
    timestamp: datetime
    signal_type: str  # fatigue, gaze_drift, tension, stress
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    local_only: bool = True  # Always true for privacy

@dataclass
class AdaptiveResponse:
    """AURA's passive interface adaptation"""
    user_id: str
    timestamp: datetime
    trigger_signals: List[BiometricSignal]
    suggested_tags: List[UITag]
    applied_changes: Dict[str, str]
    user_visible: bool = True  # User can see what's changing
    user_controllable: bool = True  # User can revert
    gradual: bool = True  # Gradual modifications

@dataclass
class VisualAgeDelta:
    """Opt-in metric: Visual age tracking over time"""
    user_id: str
    baseline_date: datetime
    current_estimate: float
    delta_months: float
    trend_direction: str  # "improving", "stable", "aging"
    confidence: float
    local_only: bool = True

@dataclass
class FocusHeatmap:
    """Opt-in metric: Attention tracking across app sections"""
    user_id: str
    session_id: str
    timestamp: datetime
    attention_map: Dict[str, float]  # section_id -> percentage
    primary_kpi_focus: float  # percentage on primary KPIs
    distraction_events: int
    engagement_score: float

@dataclass
class CognitiveDriftIndex:
    """Opt-in metric: Disengagement pattern detection"""
    user_id: str
    session_id: str
    timestamp: datetime
    scroll_without_read_events: int
    rapid_navigation_events: int
    attention_drops: int
    drift_score: float  # 0.0 to 1.0, higher = more drift
    context_type: str  # "raw_data", "dashboard", "reports"

@dataclass
class EntropyScore:
    """Opt-in metric: Layout change and personalization demand"""
    user_id: str
    period_start: datetime
    period_end: datetime
    layout_changes: int
    theme_flips: int
    override_count: int
    entropy_value: float  # Higher = more personalization demand
    stability_trend: str  # "increasing", "stable", "decreasing"

@dataclass
class MoodResonanceProfile:
    """Opt-in metric: Energy and mood patterns over time"""
    user_id: str
    timestamp: datetime
    energy_level: float  # 0.0 to 1.0
    mood_indicators: Dict[str, float]  # emotion -> intensity
    micro_movement_patterns: Dict[str, float]
    tone_analysis: Optional[Dict[str, float]]
    daily_pattern: List[float]  # hourly energy levels
    opt_in_explicit: bool = True  # Must be explicitly enabled

@dataclass
class AURASettings:
    """User's AURA configuration and preferences"""
    user_id: str
    adaptive_mode_enabled: bool = False  # Default OFF
    prompted_mode_enabled: bool = True
    metric_tracking_enabled: bool = False  # Opt-in only
    enabled_metrics: List[str] = None  # Which metrics user wants
    privacy_level: str = "maximum"  # "maximum", "standard", "minimal"
    local_processing_only: bool = True
    data_retention_days: int = 7  # Local data retention
    
    def __post_init__(self):
        if self.enabled_metrics is None:
            self.enabled_metrics = []

@dataclass
class AURASession:
    """AURA session tracking for analytics"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    mode_used: AURAMode
    prompted_commands: List[PromptedCommand]
    adaptive_responses: List[AdaptiveResponse]
    metrics_generated: List[str]
    user_satisfaction: Optional[float]  # Post-session feedback
    
class AURAMirrorProtocol:
    """Core protocol implementation for AURA mirror system"""
    
    @staticmethod
    def parse_user_command(command_text: str) -> List[UITag]:
        """Parse natural language commands into UI tags"""
        command_lower = command_text.lower()
        tags = []
        
        # Color parsing
        if any(word in command_lower for word in ["soft", "calm", "gentle", "soothing"]):
            tags.append(UITag.COLOR_CALM)
        elif any(word in command_lower for word in ["bright", "energetic", "vibrant"]):
            tags.append(UITag.COLOR_ENERGETIC)
        elif any(word in command_lower for word in ["warm", "cozy"]):
            tags.append(UITag.COLOR_WARM)
        elif any(word in command_lower for word in ["cool", "crisp"]):
            tags.append(UITag.COLOR_COOL)
            
        # Layout parsing
        if any(word in command_lower for word in ["minimal", "clean", "simple"]):
            tags.append(UITag.LAYOUT_MINIMAL)
        elif any(word in command_lower for word in ["spacious", "airy", "open"]):
            tags.append(UITag.LAYOUT_SPACIOUS)
        elif any(word in command_lower for word in ["focused", "concentrated"]):
            tags.append(UITag.LAYOUT_FOCUSED)
            
        # Density parsing
        if any(word in command_lower for word in ["less dense", "spread out", "lighter"]):
            tags.append(UITag.DENSITY_LOW)
        elif any(word in command_lower for word in ["more dense", "compact", "packed"]):
            tags.append(UITag.DENSITY_HIGH)
            
        return tags
    
    @staticmethod
    def biometric_to_tags(signals: List[BiometricSignal]) -> List[UITag]:
        """Convert biometric signals to appropriate UI tags"""
        tags = []
        
        for signal in signals:
            if signal.signal_type == "fatigue" and signal.intensity > 0.6:
                tags.extend([UITag.COLOR_CALM, UITag.DENSITY_LOW, UITag.LAYOUT_SPACIOUS])
            elif signal.signal_type == "stress" and signal.intensity > 0.7:
                tags.extend([UITag.COLOR_COOL, UITag.LAYOUT_MINIMAL, UITag.MOOD_RELAXED])
            elif signal.signal_type == "gaze_drift" and signal.intensity > 0.5:
                tags.extend([UITag.LAYOUT_FOCUSED, UITag.DENSITY_MEDIUM])
                
        return list(set(tags))  # Remove duplicates
    
    @staticmethod
    def validate_privacy_compliance(data: dict) -> bool:
        """Ensure all biometric data stays local"""
        # Check that no biometric data is being transmitted
        sensitive_fields = ["facial_data", "eye_tracking", "biometric_raw"]
        return not any(field in data for field in sensitive_fields)

