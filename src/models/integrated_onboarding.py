"""
AURA Integrated Onboarding Models

Voice + Visual Adaptation Onboarding Flow
Real-time interface adaptation during AI introduction
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class OnboardingPhase(Enum):
    """Onboarding phases with integrated voice + visual adaptation"""
    GREETING_BRAND_FRAMING = "greeting_brand_framing"
    ADAPTIVE_DEMONSTRATION = "adaptive_demonstration"
    IMMEDIATE_AGENCY = "immediate_agency"
    VOICE_PRIMER = "voice_primer"
    READY_MODE = "ready_mode"

class AdaptationDemo(Enum):
    """Types of real-time adaptation demonstrations"""
    LAYOUT_STYLE = "layout_style"
    COLOR_TONE = "color_tone"
    DENSITY_SPACING = "density_spacing"
    TYPOGRAPHY = "typography"

class OnboardingCard(Enum):
    """Three agency cards presented to user"""
    GATHER_COMPANY_DATA = "gather_company_data"
    TRY_DEMO_DATA = "try_demo_data"
    TUNE_INTERFACE = "tune_interface"

@dataclass
class VoiceNarration:
    """Voice narration with timing and visual cues"""
    text: str
    start_time: float  # seconds from onboarding start
    duration: float    # seconds
    visual_cues: List[str]  # Visual changes during narration
    voice_tone: str    # calm, energetic, professional
    pace: str          # slow, normal, fast

@dataclass
class VisualTransition:
    """Visual transition synchronized with voice"""
    transition_type: str
    start_time: float
    duration: float
    from_state: Dict[str, Any]
    to_state: Dict[str, Any]
    easing: str  # ease-in, ease-out, linear
    description: str

@dataclass
class OnboardingStep:
    """Single step in integrated onboarding flow"""
    phase: OnboardingPhase
    step_id: str
    narration: VoiceNarration
    visual_transitions: List[VisualTransition]
    user_interaction_points: List[str]
    adaptive_elements: List[str]
    
@dataclass
class OnboardingFlow:
    """Complete integrated onboarding experience"""
    user_id: str
    flow_id: str
    steps: List[OnboardingStep]
    total_duration: float
    voice_enabled: bool
    visual_adaptation_enabled: bool
    user_preferences: Dict[str, Any]
    completion_status: Dict[str, bool]
    created_at: datetime

@dataclass
class AdaptationDemonstration:
    """Real-time adaptation demonstration"""
    demo_type: AdaptationDemo
    demo_id: str
    voice_cue: str
    visual_changes: List[Dict[str, Any]]
    duration: float
    user_impact_message: str

@dataclass
class OnboardingCard:
    """Agency card presented to user"""
    card_type: OnboardingCard
    title: str
    description: str
    icon: str
    action_text: str
    hover_animation: str
    click_action: str
    visual_style: Dict[str, Any]

@dataclass
class VoiceCommand:
    """Voice command example for primer"""
    command_text: str
    category: str  # layout, data, analysis
    expected_response: str
    demonstration_available: bool

@dataclass
class OnboardingSession:
    """Complete onboarding session tracking"""
    session_id: str
    user_id: str
    flow: OnboardingFlow
    current_step: int
    start_time: datetime
    completion_time: Optional[datetime]
    user_interactions: List[Dict[str, Any]]
    adaptation_preferences_learned: Dict[str, Any]
    voice_commands_attempted: List[str]
    selected_path: Optional[OnboardingCard]
    
class OnboardingState:
    """Current state of onboarding process"""
    def __init__(self):
        self.current_phase = OnboardingPhase.GREETING_BRAND_FRAMING
        self.current_step = 0
        self.voice_active = False
        self.visual_adaptation_active = False
        self.user_engaged = False
        self.preferences_captured = {}
        self.demonstration_completed = {}
        
    def advance_phase(self, next_phase: OnboardingPhase):
        """Advance to next onboarding phase"""
        self.current_phase = next_phase
        self.current_step += 1
        
    def capture_preference(self, preference_type: str, value: Any):
        """Capture user preference during onboarding"""
        self.preferences_captured[preference_type] = {
            "value": value,
            "timestamp": datetime.now(),
            "confidence": 1.0
        }
        
    def mark_demonstration_complete(self, demo_type: AdaptationDemo):
        """Mark adaptation demonstration as completed"""
        self.demonstration_completed[demo_type.value] = {
            "completed": True,
            "timestamp": datetime.now()
        }

