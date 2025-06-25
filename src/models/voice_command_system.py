"""
Elite Command API: Comprehensive Voice Command System Models

More than redundantly good voice interaction architecture for elite executives.
Supports three interaction modes with extensive command coverage.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json

class VoiceInteractionMode(Enum):
    """Three distinct voice interaction modes"""
    PASSIVE_AURA = "passive_aura"      # Biometric-reactive, no speech required
    ACTIVE_VOICE = "active_voice"      # Explicit voice commands
    MANUAL_FALLBACK = "manual_fallback" # Traditional click-based UI

class VoiceCommandCategory(Enum):
    """Categories of voice commands"""
    ONBOARDING = "onboarding"
    INTERFACE_CUSTOMIZATION = "interface_customization"
    DATA_INTELLIGENCE = "data_intelligence"
    SECURITY_ACCESS = "security_access"
    NAVIGATION = "navigation"
    SYSTEM_CONTROL = "system_control"
    BUSINESS_OPERATIONS = "business_operations"
    ANALYTICS = "analytics"
    COLLABORATION = "collaboration"
    AUTOMATION = "automation"

class VoiceCommandIntent(Enum):
    """Specific intents within categories"""
    # Onboarding
    IMPORT_COMPANY_DATA = "import_company_data"
    SET_BUSINESS_TEMPLATE = "set_business_template"
    EXPLAIN_ONBOARDING_STEP = "explain_onboarding_step"
    START_VISUAL_TOUR = "start_visual_tour"
    
    # Interface Customization
    ADJUST_STYLE = "adjust_style"
    LAYOUT_CONTROL = "layout_control"
    TYPOGRAPHY = "typography"
    THEME = "theme"
    DENSITY = "density"
    CONTRAST = "contrast"
    
    # Data Intelligence
    CONFIDENCE_INSIGHT = "confidence_insight"
    LINEAGE_TRACE = "lineage_trace"
    HIGHLIGHT_KEY_METRICS = "highlight_key_metrics"
    EXPLAIN_METRIC = "explain_metric"
    COMPARE_METRICS = "compare_metrics"
    FORECAST_TREND = "forecast_trend"
    
    # Security/Access
    API_KEY_OPS = "api_key_ops"
    ACCESS_SETTINGS = "access_settings"
    AUDIT_LOG = "audit_log"
    PERMISSION_CONTROL = "permission_control"
    
    # Navigation
    FOCUS_VIEW = "focus_view"
    NAVIGATE_STRUCTURE = "navigate_structure"
    RESET_VIEW = "reset_view"
    ZOOM_ELEMENT = "zoom_element"
    
    # System Control
    UNDO_ACTION = "undo_action"
    SAVE_STATE = "save_state"
    QUERY_SYSTEM_STATE = "query_system_state"
    TOGGLE_MODE = "toggle_mode"

class VoiceConfidenceLevel(Enum):
    """Confidence levels for voice recognition"""
    VERY_HIGH = "very_high"    # 95%+
    HIGH = "high"              # 85-94%
    MEDIUM = "medium"          # 70-84%
    LOW = "low"                # 50-69%
    VERY_LOW = "very_low"      # <50%

class VoiceResponseType(Enum):
    """Types of system responses to voice commands"""
    IMMEDIATE_ACTION = "immediate_action"      # Execute immediately
    CONFIRMATION_REQUIRED = "confirmation_required"  # Ask for confirmation
    CLARIFICATION_NEEDED = "clarification_needed"   # Need more info
    DEMONSTRATION = "demonstration"           # Show how it works
    EXPLANATION = "explanation"              # Explain concept
    ERROR_HANDLING = "error_handling"        # Handle errors gracefully

@dataclass
class VoiceCommand:
    """Individual voice command definition"""
    command_id: str
    category: VoiceCommandCategory
    intent: VoiceCommandIntent
    example_phrases: List[str]
    wake_word_required: bool
    mode: VoiceInteractionMode
    confidence_threshold: float
    response_type: VoiceResponseType
    target_elements: List[str]  # UI elements affected
    api_endpoint: Optional[str]
    parameters: Dict[str, Any]
    fallback_commands: List[str]
    context_sensitive: bool
    executive_priority: int  # 1-5, 5 being highest priority

@dataclass
class VoiceActionMap:
    """Complete mapping of voice actions to system functions"""
    category: VoiceCommandCategory
    commands: List[VoiceCommand]
    description: str
    examples: List[str]
    prerequisites: List[str]
    success_metrics: Dict[str, Any]

@dataclass
class UIElementTag:
    """Tagging schema for UI elements to enable voice targeting"""
    element_id: str
    ai_path: str           # e.g., "portfolio_grid.company_card[1].performance_chart"
    ai_tag: List[str]      # e.g., ["widget", "chart", "financial-data"]
    ai_styles: List[str]   # e.g., ["sharp", "high-contrast", "dense"]
    ai_intent: str         # e.g., "display_metric"
    voice_aliases: List[str]  # Alternative names for voice targeting
    modification_allowed: bool
    batch_group: Optional[str]  # For batch modifications

@dataclass
class VoiceSession:
    """Voice interaction session tracking"""
    session_id: str
    user_id: str
    start_time: datetime
    current_mode: VoiceInteractionMode
    commands_processed: List[Dict[str, Any]]
    context_stack: List[str]  # Conversation context
    user_preferences: Dict[str, Any]
    confidence_scores: List[float]
    error_count: int
    success_count: int

@dataclass
class VoiceResponse:
    """System response to voice command"""
    response_id: str
    command_id: str
    response_type: VoiceResponseType
    message: str
    actions_taken: List[Dict[str, Any]]
    visual_feedback: Dict[str, Any]
    audio_feedback: Optional[str]
    confidence_score: float
    execution_time: float
    success: bool
    error_details: Optional[str]

@dataclass
class VoiceTrainingData:
    """Data for improving voice recognition over time"""
    command_text: str
    intended_action: str
    actual_action: str
    user_satisfaction: Optional[int]  # 1-5 rating
    context: Dict[str, Any]
    timestamp: datetime
    user_id: str
    anonymized: bool

class VoiceCommandProcessor:
    """Core voice command processing logic"""
    
    def __init__(self):
        self.wake_words = ["command", "elite", "aura"]
        self.confidence_threshold = 0.7
        self.context_window = 5  # Remember last 5 interactions
        self.active_sessions = {}
        self.command_registry = {}
        self.ui_element_registry = {}
        
    def register_command(self, command: VoiceCommand):
        """Register a new voice command"""
        self.command_registry[command.command_id] = command
        
    def register_ui_element(self, element: UIElementTag):
        """Register a UI element for voice targeting"""
        self.ui_element_registry[element.element_id] = element
        
    def process_voice_input(self, audio_data: bytes, user_id: str) -> VoiceResponse:
        """Process raw voice input and return system response"""
        # This would integrate with speech recognition service
        pass
        
    def parse_command(self, text: str, context: Dict[str, Any]) -> Optional[VoiceCommand]:
        """Parse text into a recognized voice command"""
        # NLP processing to match text to registered commands
        pass
        
    def execute_command(self, command: VoiceCommand, parameters: Dict[str, Any]) -> VoiceResponse:
        """Execute a recognized voice command"""
        # Command execution logic
        pass

# Comprehensive Voice Command Definitions
VOICE_COMMAND_REGISTRY = {
    # ONBOARDING COMMANDS
    "import_stripe_notion": VoiceCommand(
        command_id="import_stripe_notion",
        category=VoiceCommandCategory.ONBOARDING,
        intent=VoiceCommandIntent.IMPORT_COMPANY_DATA,
        example_phrases=[
            "Pull in my Stripe and Notion data",
            "Connect my Stripe and Notion accounts",
            "Import data from Stripe and Notion",
            "Link my payment and workspace data"
        ],
        wake_word_required=True,
        mode=VoiceInteractionMode.ACTIVE_VOICE,
        confidence_threshold=0.8,
        response_type=VoiceResponseType.CONFIRMATION_REQUIRED,
        target_elements=["data_connection_panel", "oauth_flow"],
        api_endpoint="/api/ingestion/oauth/connect",
        parameters={"sources": ["stripe", "notion"]},
        fallback_commands=["show data connection options"],
        context_sensitive=True,
        executive_priority=5
    ),
    
    "set_ecommerce_template": VoiceCommand(
        command_id="set_ecommerce_template",
        category=VoiceCommandCategory.ONBOARDING,
        intent=VoiceCommandIntent.SET_BUSINESS_TEMPLATE,
        example_phrases=[
            "This is an e-commerce company",
            "Set business type to e-commerce",
            "Configure for online retail",
            "Use e-commerce template"
        ],
        wake_word_required=True,
        mode=VoiceInteractionMode.ACTIVE_VOICE,
        confidence_threshold=0.85,
        response_type=VoiceResponseType.IMMEDIATE_ACTION,
        target_elements=["business_template_selector"],
        api_endpoint="/api/templates/apply",
        parameters={"template_type": "ecommerce"},
        fallback_commands=["show business templates"],
        context_sensitive=False,
        executive_priority=4
    ),
    
    # INTERFACE CUSTOMIZATION COMMANDS
    "make_more_relaxed": VoiceCommand(
        command_id="make_more_relaxed",
        category=VoiceCommandCategory.INTERFACE_CUSTOMIZATION,
        intent=VoiceCommandIntent.ADJUST_STYLE,
        example_phrases=[
            "Make this more relaxed",
            "Too serious, lighten it up",
            "Soften the interface",
            "Make it feel calmer",
            "Less intense please"
        ],
        wake_word_required=True,
        mode=VoiceInteractionMode.ACTIVE_VOICE,
        confidence_threshold=0.75,
        response_type=VoiceResponseType.IMMEDIATE_ACTION,
        target_elements=["global_theme", "all_cards", "typography"],
        api_endpoint="/api/reflex/mirror",
        parameters={"style_adjustment": "relaxed", "intensity": "medium"},
        fallback_commands=["show style options"],
        context_sensitive=True,
        executive_priority=3
    ),
    
    "move_metrics_left": VoiceCommand(
        command_id="move_metrics_left",
        category=VoiceCommandCategory.INTERFACE_CUSTOMIZATION,
        intent=VoiceCommandIntent.LAYOUT_CONTROL,
        example_phrases=[
            "Move the metrics to the left side",
            "Put metrics on the left",
            "Shift metrics panel left",
            "Relocate metrics to left side"
        ],
        wake_word_required=True,
        mode=VoiceInteractionMode.ACTIVE_VOICE,
        confidence_threshold=0.8,
        response_type=VoiceResponseType.IMMEDIATE_ACTION,
        target_elements=["metrics_panel", "dashboard_layout"],
        api_endpoint="/api/reflex/edit",
        parameters={"action": "move_element", "element": "metrics_panel", "position": "left"},
        fallback_commands=["show layout options"],
        context_sensitive=False,
        executive_priority=3
    ),
    
    # DATA INTELLIGENCE COMMANDS
    "explain_revenue_confidence": VoiceCommand(
        command_id="explain_revenue_confidence",
        category=VoiceCommandCategory.DATA_INTELLIGENCE,
        intent=VoiceCommandIntent.CONFIDENCE_INSIGHT,
        example_phrases=[
            "Why is this revenue figure low confidence?",
            "Explain the confidence score for revenue",
            "What makes this revenue number uncertain?",
            "Revenue confidence explanation"
        ],
        wake_word_required=True,
        mode=VoiceInteractionMode.ACTIVE_VOICE,
        confidence_threshold=0.85,
        response_type=VoiceResponseType.EXPLANATION,
        target_elements=["revenue_metric", "confidence_indicator"],
        api_endpoint="/api/confidence/explain",
        parameters={"metric": "revenue", "detail_level": "executive"},
        fallback_commands=["show confidence details"],
        context_sensitive=True,
        executive_priority=5
    ),
    
    "trace_number_source": VoiceCommand(
        command_id="trace_number_source",
        category=VoiceCommandCategory.DATA_INTELLIGENCE,
        intent=VoiceCommandIntent.LINEAGE_TRACE,
        example_phrases=[
            "Where did this number come from?",
            "Trace this back to its source",
            "Show me the data lineage",
            "What's the source of this metric?"
        ],
        wake_word_required=True,
        mode=VoiceInteractionMode.ACTIVE_VOICE,
        confidence_threshold=0.8,
        response_type=VoiceResponseType.DEMONSTRATION,
        target_elements=["selected_metric", "lineage_visualization"],
        api_endpoint="/api/confidence/lineage",
        parameters={"trace_depth": "full", "visualization": True},
        fallback_commands=["show data sources"],
        context_sensitive=True,
        executive_priority=5
    ),
    
    # SECURITY/ACCESS COMMANDS
    "create_readonly_key": VoiceCommand(
        command_id="create_readonly_key",
        category=VoiceCommandCategory.SECURITY_ACCESS,
        intent=VoiceCommandIntent.API_KEY_OPS,
        example_phrases=[
            "Create a new read-only key for finance team",
            "Generate readonly API key for finance",
            "Make a finance team API key",
            "New readonly key for finance department"
        ],
        wake_word_required=True,
        mode=VoiceInteractionMode.ACTIVE_VOICE,
        confidence_threshold=0.9,
        response_type=VoiceResponseType.CONFIRMATION_REQUIRED,
        target_elements=["api_key_manager", "security_panel"],
        api_endpoint="/api/security/api-keys/create",
        parameters={"permissions": "readonly", "team": "finance"},
        fallback_commands=["show API key management"],
        context_sensitive=False,
        executive_priority=5
    )
}

# UI Element Tagging Registry
UI_ELEMENT_REGISTRY = {
    "portfolio_grid": UIElementTag(
        element_id="portfolio_grid",
        ai_path="dashboard.portfolio_grid",
        ai_tag=["grid", "portfolio", "companies"],
        ai_styles=["card-layout", "responsive"],
        ai_intent="display_portfolio",
        voice_aliases=["portfolio", "companies", "grid", "company list"],
        modification_allowed=True,
        batch_group="main_content"
    ),
    
    "revenue_metric": UIElementTag(
        element_id="revenue_metric",
        ai_path="dashboard.metrics.revenue",
        ai_tag=["metric", "financial", "revenue"],
        ai_styles=["number-display", "trend-indicator"],
        ai_intent="display_metric",
        voice_aliases=["revenue", "sales", "income", "earnings"],
        modification_allowed=True,
        batch_group="financial_metrics"
    ),
    
    "confidence_indicator": UIElementTag(
        element_id="confidence_indicator",
        ai_path="dashboard.metrics.revenue.confidence",
        ai_tag=["indicator", "confidence", "quality"],
        ai_styles=["badge", "color-coded"],
        ai_intent="show_confidence",
        voice_aliases=["confidence", "reliability", "quality score"],
        modification_allowed=False,
        batch_group="quality_indicators"
    )
}

