"""
AURA Integrated Onboarding Service

Implements voice + visual adaptation onboarding flow where the AI
demonstrates system capabilities in real-time while introducing itself.

Target: Executive / Portfolio Owner
Experience: Voice + Click → Dashboard UI + Real-time Layout Changes
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..models.integrated_onboarding import (
    OnboardingPhase, AdaptationDemo, OnboardingCard as CardType,
    VoiceNarration, VisualTransition, OnboardingStep, OnboardingFlow,
    AdaptationDemonstration, OnboardingCard, VoiceCommand, OnboardingSession,
    OnboardingState
)

class IntegratedOnboardingService:
    """Service for integrated voice + visual adaptation onboarding"""
    
    def __init__(self):
        self.active_sessions = {}
        self.onboarding_flows = {}
        self.adaptation_demonstrations = self._create_adaptation_demonstrations()
        self.voice_commands = self._create_voice_command_examples()
        self.agency_cards = self._create_agency_cards()
        
    def create_onboarding_flow(self, user_id: str) -> OnboardingFlow:
        """Create integrated onboarding flow for Elite Commander"""
        
        # Step 1: AI Greeting + Brand Framing [0:00-0:06]
        greeting_step = OnboardingStep(
            phase=OnboardingPhase.GREETING_BRAND_FRAMING,
            step_id="greeting_brand_framing",
            narration=VoiceNarration(
                text="Welcome to Elite Commander. I'm your system AI. I'll adapt this interface to you — visually, cognitively, and operationally.",
                start_time=0.0,
                duration=6.0,
                visual_cues=["background_animate", "dashboard_zoom", "tone_shift"],
                voice_tone="professional",
                pace="normal"
            ),
            visual_transitions=[
                VisualTransition(
                    transition_type="background_color",
                    start_time=0.0,
                    duration=6.0,
                    from_state={"background": "#1a1a1a", "opacity": 0.8},
                    to_state={"background": "#1e3a8a", "opacity": 1.0},
                    easing="ease-in-out",
                    description="Background animates from dark neutral to clean business blue"
                ),
                VisualTransition(
                    transition_type="dashboard_zoom",
                    start_time=2.0,
                    duration=4.0,
                    from_state={"scale": 0.95, "blur": 2},
                    to_state={"scale": 1.0, "blur": 0},
                    easing="ease-out",
                    description="Dashboard layout zooms in gently and comes into focus"
                )
            ],
            user_interaction_points=[],
            adaptive_elements=["background", "dashboard_container"]
        )
        
        # Step 2: Adaptive Demonstration Begins [0:07-0:15]
        demonstration_step = OnboardingStep(
            phase=OnboardingPhase.ADAPTIVE_DEMONSTRATION,
            step_id="adaptive_demonstration",
            narration=VoiceNarration(
                text="Let's adjust a few things right now, so it fits you. Here's a sharp, focused layout. Now a softer, more spacious one. You might prefer calming tones… or something more energizing. All of this is adjustable by voice, anytime.",
                start_time=7.0,
                duration=8.0,
                visual_cues=["layout_sharp", "layout_soft", "color_calm", "color_energetic"],
                voice_tone="engaging",
                pace="normal"
            ),
            visual_transitions=[
                # Sharp layout demonstration
                VisualTransition(
                    transition_type="layout_style",
                    start_time=8.0,
                    duration=1.5,
                    from_state={"border_radius": "8px", "padding": "16px", "font_weight": "400"},
                    to_state={"border_radius": "2px", "padding": "8px", "font_weight": "600"},
                    easing="ease-in-out",
                    description="UI switches to angular, grid-based view with tight cards and strong font"
                ),
                # Soft layout demonstration
                VisualTransition(
                    transition_type="layout_style",
                    start_time=10.0,
                    duration=1.5,
                    from_state={"border_radius": "2px", "padding": "8px", "font_weight": "600"},
                    to_state={"border_radius": "12px", "padding": "24px", "font_weight": "300"},
                    easing="ease-in-out",
                    description="Layout shifts to rounded corners, more padding, calmer appearance"
                ),
                # Calming tones demonstration
                VisualTransition(
                    transition_type="color_tone",
                    start_time=12.0,
                    duration=1.0,
                    from_state={"primary": "#1e3a8a", "secondary": "#3b82f6"},
                    to_state={"primary": "#0f766e", "secondary": "#14b8a6"},
                    easing="ease-in-out",
                    description="Switches to cool light blue/grey calming tones"
                ),
                # Energizing tones demonstration
                VisualTransition(
                    transition_type="color_tone",
                    start_time=13.5,
                    duration=1.0,
                    from_state={"primary": "#0f766e", "secondary": "#14b8a6"},
                    to_state={"primary": "#ea580c", "secondary": "#f59e0b"},
                    easing="ease-in-out",
                    description="Switches to light orange/gold energizing tones"
                )
            ],
            user_interaction_points=["observe_adaptations"],
            adaptive_elements=["all_cards", "dashboard_container", "color_scheme"]
        )
        
        # Step 3: Immediate Agency - Present 3 Cards [0:16-0:22]
        agency_step = OnboardingStep(
            phase=OnboardingPhase.IMMEDIATE_AGENCY,
            step_id="immediate_agency",
            narration=VoiceNarration(
                text="We'll scan your portfolio and connect live feeds. Prefer to explore first? I'll show you a sample company. Want more contrast, bigger text, less clutter? Let's make it right.",
                start_time=16.0,
                duration=6.0,
                visual_cues=["cards_appear", "hover_pulses"],
                voice_tone="inviting",
                pace="normal"
            ),
            visual_transitions=[
                VisualTransition(
                    transition_type="cards_appearance",
                    start_time=16.0,
                    duration=2.0,
                    from_state={"opacity": 0, "scale": 0.8, "y": 20},
                    to_state={"opacity": 1, "scale": 1.0, "y": 0},
                    easing="ease-out",
                    description="3 animated cards appear with subtle hover pulses"
                )
            ],
            user_interaction_points=["card_selection", "hover_interactions"],
            adaptive_elements=["agency_cards"]
        )
        
        # Step 4: Voice Primer [0:23-0:30]
        voice_primer_step = OnboardingStep(
            phase=OnboardingPhase.VOICE_PRIMER,
            step_id="voice_primer",
            narration=VoiceNarration(
                text="You can say things like 'Show me the high-contrast layout', 'Connect my companies', or 'Why is revenue down this month?' You're in control. Just speak — I'll respond instantly.",
                start_time=23.0,
                duration=7.0,
                visual_cues=["mic_pulse", "ready_mode"],
                voice_tone="encouraging",
                pace="normal"
            ),
            visual_transitions=[
                VisualTransition(
                    transition_type="mic_activation",
                    start_time=28.0,
                    duration=2.0,
                    from_state={"mic_opacity": 0.3, "pulse": False},
                    to_state={"mic_opacity": 1.0, "pulse": True},
                    easing="ease-in-out",
                    description="Mic icon pulses and dashboard enters ready mode"
                )
            ],
            user_interaction_points=["voice_activation", "command_attempt"],
            adaptive_elements=["mic_interface", "dashboard_state"]
        )
        
        flow = OnboardingFlow(
            user_id=user_id,
            flow_id=f"integrated_onboarding_{user_id}_{int(time.time())}",
            steps=[greeting_step, demonstration_step, agency_step, voice_primer_step],
            total_duration=30.0,
            voice_enabled=True,
            visual_adaptation_enabled=True,
            user_preferences={},
            completion_status={},
            created_at=datetime.now()
        )
        
        self.onboarding_flows[user_id] = flow
        return flow
    
    def start_onboarding_session(self, user_id: str) -> OnboardingSession:
        """Start integrated onboarding session"""
        flow = self.create_onboarding_flow(user_id)
        
        session = OnboardingSession(
            session_id=f"session_{user_id}_{int(time.time())}",
            user_id=user_id,
            flow=flow,
            current_step=0,
            start_time=datetime.now(),
            completion_time=None,
            user_interactions=[],
            adaptation_preferences_learned={},
            voice_commands_attempted=[],
            selected_path=None
        )
        
        self.active_sessions[user_id] = session
        return session
    
    def get_current_step(self, user_id: str) -> Optional[OnboardingStep]:
        """Get current onboarding step for user"""
        session = self.active_sessions.get(user_id)
        if not session:
            return None
            
        if session.current_step < len(session.flow.steps):
            return session.flow.steps[session.current_step]
        return None
    
    def advance_onboarding(self, user_id: str) -> bool:
        """Advance to next onboarding step"""
        session = self.active_sessions.get(user_id)
        if not session:
            return False
            
        session.current_step += 1
        
        # Check if onboarding is complete
        if session.current_step >= len(session.flow.steps):
            session.completion_time = datetime.now()
            return True
            
        return True
    
    def handle_user_interaction(self, user_id: str, interaction_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user interaction during onboarding"""
        session = self.active_sessions.get(user_id)
        if not session:
            return {"error": "No active onboarding session"}
        
        # Record interaction
        interaction = {
            "type": interaction_type,
            "data": data,
            "timestamp": datetime.now(),
            "step": session.current_step
        }
        session.user_interactions.append(interaction)
        
        # Process specific interactions
        if interaction_type == "card_selection":
            return self._handle_card_selection(session, data)
        elif interaction_type == "voice_command":
            return self._handle_voice_command(session, data)
        elif interaction_type == "adaptation_preference":
            return self._handle_adaptation_preference(session, data)
        
        return {"status": "interaction_recorded"}
    
    def _handle_card_selection(self, session: OnboardingSession, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agency card selection"""
        card_type = data.get("card_type")
        
        if card_type == "gather_company_data":
            session.selected_path = CardType.GATHER_COMPANY_DATA
            return {
                "action": "redirect_to_data_connection",
                "message": "Let's connect your company data sources",
                "next_steps": ["oauth_setup", "data_scanning"]
            }
        elif card_type == "try_demo_data":
            session.selected_path = CardType.TRY_DEMO_DATA
            return {
                "action": "load_demo_dashboard",
                "message": "Loading sample portfolio data",
                "demo_company": "TechFlow Dynamics"
            }
        elif card_type == "tune_interface":
            session.selected_path = CardType.TUNE_INTERFACE
            return {
                "action": "open_customization_panel",
                "message": "Let's customize your interface preferences",
                "customization_options": ["layout", "colors", "density", "typography"]
            }
        
        return {"error": "Unknown card type"}
    
    def _handle_voice_command(self, session: OnboardingSession, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice command during onboarding"""
        command = data.get("command", "").lower()
        session.voice_commands_attempted.append(command)
        
        # Process common onboarding commands
        if "high contrast" in command or "contrast" in command:
            return {
                "action": "apply_high_contrast",
                "message": "Applying high contrast layout",
                "visual_changes": {"contrast": "high", "font_weight": "bold"}
            }
        elif "connect" in command and "companies" in command:
            return {
                "action": "start_data_connection",
                "message": "Starting company data connection process"
            }
        elif "revenue" in command or "why" in command:
            return {
                "action": "show_analysis_demo",
                "message": "Here's how I analyze revenue trends",
                "demo_insight": "Revenue decreased 12% due to seasonal factors and delayed enterprise deals"
            }
        
        return {
            "action": "acknowledge_command",
            "message": f"I heard '{command}'. Let me show you how that works.",
            "suggestion": "Try 'show me the dashboard' or 'make it bigger'"
        }
    
    def _handle_adaptation_preference(self, session: OnboardingSession, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adaptation preference capture"""
        preference_type = data.get("type")
        preference_value = data.get("value")
        
        session.adaptation_preferences_learned[preference_type] = {
            "value": preference_value,
            "confidence": data.get("confidence", 0.8),
            "timestamp": datetime.now()
        }
        
        return {
            "status": "preference_captured",
            "type": preference_type,
            "value": preference_value
        }
    
    def _create_adaptation_demonstrations(self) -> Dict[str, AdaptationDemonstration]:
        """Create adaptation demonstrations for onboarding"""
        return {
            "layout_style": AdaptationDemonstration(
                demo_type=AdaptationDemo.LAYOUT_STYLE,
                demo_id="layout_sharp_to_soft",
                voice_cue="Here's a sharp, focused layout. Now a softer, more spacious one.",
                visual_changes=[
                    {"element": "cards", "property": "border-radius", "from": "8px", "to": "2px"},
                    {"element": "cards", "property": "padding", "from": "16px", "to": "8px"},
                    {"element": "text", "property": "font-weight", "from": "400", "to": "600"}
                ],
                duration=3.0,
                user_impact_message="Layout adapts to your cognitive preferences"
            ),
            "color_tone": AdaptationDemonstration(
                demo_type=AdaptationDemo.COLOR_TONE,
                demo_id="calm_to_energetic",
                voice_cue="You might prefer calming tones… or something more energizing.",
                visual_changes=[
                    {"element": "theme", "property": "primary-color", "from": "#1e3a8a", "to": "#0f766e"},
                    {"element": "theme", "property": "accent-color", "from": "#3b82f6", "to": "#14b8a6"}
                ],
                duration=2.5,
                user_impact_message="Colors adjust to your energy and focus needs"
            )
        }
    
    def _create_voice_command_examples(self) -> List[VoiceCommand]:
        """Create voice command examples for primer"""
        return [
            VoiceCommand(
                command_text="Show me the high-contrast layout",
                category="layout",
                expected_response="Applying high contrast with bold fonts and strong borders",
                demonstration_available=True
            ),
            VoiceCommand(
                command_text="Connect my companies",
                category="data",
                expected_response="Starting OAuth connection to your business tools",
                demonstration_available=True
            ),
            VoiceCommand(
                command_text="Why is revenue down this month?",
                category="analysis",
                expected_response="Analyzing revenue trends and identifying key factors",
                demonstration_available=True
            )
        ]
    
    def _create_agency_cards(self) -> List[OnboardingCard]:
        """Create the three agency cards for immediate user choice"""
        return [
            OnboardingCard(
                card_type=CardType.GATHER_COMPANY_DATA,
                title="Gather My Company Data",
                description="We'll scan your portfolio and connect live feeds.",
                icon="🔷",
                action_text="Connect Data Sources",
                hover_animation="pulse-blue",
                click_action="start_data_connection",
                visual_style={
                    "background": "linear-gradient(135deg, #3b82f6, #1e40af)",
                    "border": "2px solid #2563eb",
                    "color": "#ffffff"
                }
            ),
            OnboardingCard(
                card_type=CardType.TRY_DEMO_DATA,
                title="Try It With Demo Data",
                description="Prefer to explore first? I'll show you a sample company.",
                icon="🔶",
                action_text="Load Demo Dashboard",
                hover_animation="pulse-orange",
                click_action="load_demo_data",
                visual_style={
                    "background": "linear-gradient(135deg, #f59e0b, #d97706)",
                    "border": "2px solid #ea580c",
                    "color": "#ffffff"
                }
            ),
            OnboardingCard(
                card_type=CardType.TUNE_INTERFACE,
                title="Tune the Interface",
                description="Want more contrast, bigger text, less clutter? Let's make it right.",
                icon="🔴",
                action_text="Customize Interface",
                hover_animation="pulse-red",
                click_action="open_customization",
                visual_style={
                    "background": "linear-gradient(135deg, #ef4444, #dc2626)",
                    "border": "2px solid #b91c1c",
                    "color": "#ffffff"
                }
            )
        ]
    
    def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """Get current onboarding status"""
        session = self.active_sessions.get(user_id)
        if not session:
            return {"status": "not_started"}
        
        current_step = self.get_current_step(user_id)
        progress = (session.current_step / len(session.flow.steps)) * 100
        
        return {
            "status": "in_progress" if session.completion_time is None else "completed",
            "current_phase": current_step.phase.value if current_step else "completed",
            "progress_percentage": progress,
            "total_duration": session.flow.total_duration,
            "elapsed_time": (datetime.now() - session.start_time).total_seconds(),
            "interactions_count": len(session.user_interactions),
            "voice_commands_attempted": len(session.voice_commands_attempted),
            "preferences_learned": len(session.adaptation_preferences_learned),
            "selected_path": session.selected_path.value if session.selected_path else None
        }

