"""
Reflective Vault System Models

A personal AI research garden that captures and cultivates executive thoughts over time.
Transforms fleeting ideas into valuable strategic insights through time-based reflection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from enum import Enum
import json
import uuid

class VaultEntryType(Enum):
    """Types of vault entries"""
    VOICE_MEMO = "voice_memo"
    VIDEO_CAPTURE = "video_capture"
    IMAGE_UPLOAD = "image_upload"
    TEXT_NOTE = "text_note"
    LIVE_WEBCAM = "live_webcam"
    LIVE_MICROPHONE = "live_microphone"
    SKETCH_UPLOAD = "sketch_upload"
    DOCUMENT_UPLOAD = "document_upload"

class VaultPrivacyLevel(Enum):
    """Privacy levels for vault entries"""
    LOCKED = "locked"           # No AI processing allowed
    REFLECTIVE = "reflective"   # AI can analyze and reflect
    VOLATILE = "volatile"       # AI can remix and transform freely
    COLLABORATIVE = "collaborative"  # Can be shared with team members

class VaultRipenessLevel(Enum):
    """Maturity levels for vault ideas"""
    SEED = "seed"               # Initial capture, raw idea
    SPROUTING = "sprouting"     # First reflections and connections
    GROWING = "growing"         # Multiple reflections, cross-links forming
    MATURING = "maturing"       # Rich connections, actionable insights
    RIPE = "ripe"              # Ready for harvest/implementation
    HARVESTED = "harvested"     # Converted to actionable output

class VaultOutputType(Enum):
    """Types of outputs the vault can generate"""
    DRAFT_SLIDES = "draft_slides"
    CONCEPT_ART = "concept_art"
    STARTUP_IDEAS = "startup_ideas"
    JOURNAL_FRAGMENTS = "journal_fragments"
    CODE_STUBS = "code_stubs"
    STRATEGIC_PROMPTS = "strategic_prompts"
    ACTION_ITEMS = "action_items"
    RESEARCH_QUESTIONS = "research_questions"
    VISUAL_PROTOTYPES = "visual_prototypes"

class VaultReflectionTrigger(Enum):
    """What triggers reflection cycles"""
    TIME_BASED = "time_based"       # Every X hours/days
    CONTENT_BASED = "content_based" # When related content is added
    USER_REQUESTED = "user_requested" # Manual trigger
    RIPENESS_BASED = "ripeness_based" # When idea reaches certain maturity
    CROSS_LINK_BASED = "cross_link_based" # When connections form

@dataclass
class VaultMediaMetadata:
    """Metadata for media files in the vault"""
    file_path: str
    file_type: str
    file_size: int
    duration: Optional[float] = None  # For audio/video
    dimensions: Optional[tuple] = None  # For images/video
    transcription: Optional[str] = None
    visual_description: Optional[str] = None
    audio_quality: Optional[float] = None
    video_quality: Optional[float] = None
    extracted_text: Optional[str] = None
    detected_objects: List[str] = field(default_factory=list)
    detected_faces: List[Dict] = field(default_factory=list)
    detected_emotions: List[str] = field(default_factory=list)

@dataclass
class VaultSemanticAnalysis:
    """Semantic analysis of vault content"""
    main_themes: List[str] = field(default_factory=list)
    tone_emotion: Dict[str, float] = field(default_factory=dict)
    intended_purpose: str = ""
    confidence_score: float = 0.0
    key_concepts: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    urgency_level: int = 1  # 1-5 scale
    complexity_level: int = 1  # 1-5 scale
    strategic_value: float = 0.0
    implementation_difficulty: int = 1  # 1-5 scale
    potential_impact: float = 0.0
    related_domains: List[str] = field(default_factory=list)

@dataclass
class VaultReflection:
    """A single reflection on a vault entry"""
    reflection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    trigger: VaultReflectionTrigger = VaultReflectionTrigger.TIME_BASED
    reflection_text: str = ""
    new_insights: List[str] = field(default_factory=list)
    questions_generated: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    cross_links: List[str] = field(default_factory=list)  # IDs of related entries
    ripeness_delta: float = 0.0  # Change in ripeness score
    confidence_score: float = 0.0
    model_state_hash: str = ""  # To track which model version generated this
    
@dataclass
class VaultCrossLink:
    """Connection between vault entries"""
    link_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_entry_id: str = ""
    target_entry_id: str = ""
    connection_type: str = ""  # "similar_theme", "complementary", "contradictory", etc.
    strength: float = 0.0  # 0.0 to 1.0
    discovered_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    auto_generated: bool = True

@dataclass
class VaultEntry:
    """A single entry in the reflective vault"""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Content
    entry_type: VaultEntryType = VaultEntryType.TEXT_NOTE
    title: str = ""
    description: str = ""
    raw_content: str = ""
    media_metadata: Optional[VaultMediaMetadata] = None
    
    # Privacy and permissions
    privacy_level: VaultPrivacyLevel = VaultPrivacyLevel.REFLECTIVE
    tags: List[str] = field(default_factory=list)
    
    # Analysis and reflection
    semantic_analysis: Optional[VaultSemanticAnalysis] = None
    reflections: List[VaultReflection] = field(default_factory=list)
    cross_links: List[str] = field(default_factory=list)  # IDs of linked entries
    
    # Maturity tracking
    ripeness_level: VaultRipenessLevel = VaultRipenessLevel.SEED
    ripeness_score: float = 0.0  # 0.0 to 1.0
    last_reflection: Optional[datetime] = None
    next_reflection: Optional[datetime] = None
    
    # Output tracking
    generated_outputs: List[Dict] = field(default_factory=list)
    harvest_ready: bool = False
    harvest_suggestions: List[str] = field(default_factory=list)
    
    # Metadata
    source_context: Dict[str, Any] = field(default_factory=dict)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VaultOutput:
    """Generated output from vault entries"""
    output_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_entry_ids: List[str] = field(default_factory=list)
    output_type: VaultOutputType = VaultOutputType.JOURNAL_FRAGMENTS
    title: str = ""
    content: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    user_id: str = ""
    
    # Output metadata
    quality_score: float = 0.0
    user_rating: Optional[int] = None  # 1-5 stars
    used_in_production: bool = False
    refinement_iterations: int = 0
    
    # File outputs
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    
    # Tracking
    view_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class VaultReflectionSchedule:
    """Schedule for automatic reflections"""
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    entry_id: str = ""
    
    # Scheduling
    reflection_interval: timedelta = field(default_factory=lambda: timedelta(days=3))
    next_reflection: datetime = field(default_factory=datetime.now)
    max_reflections: Optional[int] = None
    current_reflection_count: int = 0
    
    # Conditions
    min_ripeness_for_reflection: float = 0.1
    max_ripeness_for_reflection: float = 0.9
    pause_if_recently_accessed: bool = True
    pause_duration: timedelta = field(default_factory=lambda: timedelta(hours=24))
    
    # Status
    active: bool = True
    paused_until: Optional[datetime] = None
    last_reflection: Optional[datetime] = None

@dataclass
class VaultSession:
    """User session for vault interactions"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Session state
    current_entry_id: Optional[str] = None
    viewing_timeline: bool = False
    active_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Interaction tracking
    entries_viewed: List[str] = field(default_factory=list)
    reflections_triggered: int = 0
    outputs_generated: int = 0
    cross_links_explored: int = 0

@dataclass
class VaultAnalytics:
    """Analytics for vault usage and effectiveness"""
    user_id: str = ""
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    # Entry statistics
    total_entries: int = 0
    entries_by_type: Dict[str, int] = field(default_factory=dict)
    entries_by_privacy_level: Dict[str, int] = field(default_factory=dict)
    
    # Reflection statistics
    total_reflections: int = 0
    avg_reflections_per_entry: float = 0.0
    ripeness_progression: Dict[str, int] = field(default_factory=dict)
    
    # Output statistics
    total_outputs: int = 0
    outputs_by_type: Dict[str, int] = field(default_factory=dict)
    avg_quality_score: float = 0.0
    outputs_used_in_production: int = 0
    
    # Cross-linking statistics
    total_cross_links: int = 0
    avg_links_per_entry: float = 0.0
    strongest_connection_clusters: List[Dict] = field(default_factory=list)
    
    # User engagement
    session_count: int = 0
    avg_session_duration: timedelta = field(default_factory=lambda: timedelta(minutes=0))
    most_accessed_entries: List[str] = field(default_factory=list)

# Predefined reflection prompts for different stages
REFLECTION_PROMPTS = {
    VaultRipenessLevel.SEED: [
        "What are the core assumptions in this idea?",
        "What questions does this raise?",
        "How does this connect to current business priorities?",
        "What would need to be true for this to work?"
    ],
    VaultRipenessLevel.SPROUTING: [
        "What evidence supports or contradicts this idea?",
        "Who would be the key stakeholders?",
        "What are the potential risks and opportunities?",
        "How could this be tested quickly?"
    ],
    VaultRipenessLevel.GROWING: [
        "What resources would be required to implement this?",
        "How does this fit with the broader strategic vision?",
        "What are the competitive implications?",
        "What metrics would indicate success?"
    ],
    VaultRipenessLevel.MATURING: [
        "What is the minimum viable version of this idea?",
        "What are the key success factors?",
        "How would you pitch this to the board?",
        "What could cause this to fail?"
    ],
    VaultRipenessLevel.RIPE: [
        "What is the implementation roadmap?",
        "Who should lead this initiative?",
        "What is the expected ROI and timeline?",
        "How will you measure and track progress?"
    ]
}

# Output templates for different types
OUTPUT_TEMPLATES = {
    VaultOutputType.DRAFT_SLIDES: {
        "structure": ["Title", "Problem", "Solution", "Market", "Traction", "Team", "Ask"],
        "style": "executive_presentation",
        "length": "10-15 slides"
    },
    VaultOutputType.STRATEGIC_PROMPTS: {
        "structure": ["Context", "Key Question", "Options", "Recommendation", "Next Steps"],
        "style": "strategic_memo",
        "length": "1-2 pages"
    },
    VaultOutputType.ACTION_ITEMS: {
        "structure": ["Objective", "Tasks", "Owner", "Timeline", "Success Metrics"],
        "style": "project_plan",
        "length": "bullet_points"
    }
}

class VaultPermissions:
    """Permission levels for vault access"""
    OWNER = "owner"           # Full access to all entries
    COLLABORATOR = "collaborator"  # Access to shared entries only
    VIEWER = "viewer"         # Read-only access to shared entries
    ANALYST = "analyst"       # Can view analytics but not content

class VaultNotificationTypes:
    """Types of notifications the vault can send"""
    IDEA_RIPENED = "idea_ripened"
    NEW_CONNECTIONS = "new_connections"
    REFLECTION_READY = "reflection_ready"
    OUTPUT_GENERATED = "output_generated"
    WEEKLY_DIGEST = "weekly_digest"
    HARVEST_SUGGESTION = "harvest_suggestion"

