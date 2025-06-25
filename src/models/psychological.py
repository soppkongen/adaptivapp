from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from enum import Enum

db = SQLAlchemy()

class AnalysisType(Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"

class PsychologicalProfile(db.Model):
    """
    Stores comprehensive psychological profiles for individuals
    based on communication analysis over time.
    """
    __tablename__ = 'psychological_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    individual_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    
    # Personality Assessment (Big Five Model)
    openness_score = db.Column(db.Float, default=0.0)
    conscientiousness_score = db.Column(db.Float, default=0.0)
    extraversion_score = db.Column(db.Float, default=0.0)
    agreeableness_score = db.Column(db.Float, default=0.0)
    neuroticism_score = db.Column(db.Float, default=0.0)
    
    # Communication Style Indicators
    communication_style = db.Column(db.String(100), nullable=True)  # direct, diplomatic, analytical, etc.
    stress_response_pattern = db.Column(db.String(100), nullable=True)
    authenticity_baseline = db.Column(db.Float, default=0.0)
    
    # Behavioral Baselines
    baseline_speech_rate = db.Column(db.Float, nullable=True)
    baseline_pitch_variance = db.Column(db.Float, nullable=True)
    baseline_emotional_state = db.Column(db.String(50), nullable=True)
    
    # Metadata
    profile_confidence = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    communications = db.relationship('CommunicationAnalysis', backref='profile', lazy=True)
    behavioral_patterns = db.relationship('BehavioralPattern', backref='profile', lazy=True)

class CommunicationAnalysis(db.Model):
    """
    Stores detailed analysis results for individual communications
    including text, audio, and video analysis metrics.
    """
    __tablename__ = 'communication_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    communication_id = db.Column(db.String(255), nullable=False, unique=True)
    individual_id = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('psychological_profiles.id'), nullable=True)
    
    # Communication Metadata
    communication_type = db.Column(db.String(50), nullable=False)  # email, meeting, call, etc.
    analysis_type = db.Column(db.Enum(AnalysisType), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Text Analysis Results
    text_content = db.Column(db.Text, nullable=True)
    linguistic_complexity = db.Column(db.Float, nullable=True)
    emotional_valence = db.Column(db.Float, nullable=True)
    cognitive_load_score = db.Column(db.Float, nullable=True)
    deception_indicators = db.Column(db.JSON, nullable=True)
    stress_markers = db.Column(db.JSON, nullable=True)
    
    # Audio Analysis Results
    speech_rate = db.Column(db.Float, nullable=True)
    pitch_mean = db.Column(db.Float, nullable=True)
    pitch_variance = db.Column(db.Float, nullable=True)
    volume_variance = db.Column(db.Float, nullable=True)
    pause_frequency = db.Column(db.Float, nullable=True)
    filler_word_count = db.Column(db.Integer, nullable=True)
    voice_stress_score = db.Column(db.Float, nullable=True)
    
    # Video Analysis Results
    facial_expressions = db.Column(db.JSON, nullable=True)
    micro_expressions = db.Column(db.JSON, nullable=True)
    gaze_patterns = db.Column(db.JSON, nullable=True)
    attention_score = db.Column(db.Float, nullable=True)
    visual_stress_indicators = db.Column(db.JSON, nullable=True)
    
    # Cross-Modal Analysis
    authenticity_score = db.Column(db.Float, nullable=True)
    congruence_score = db.Column(db.Float, nullable=True)
    overall_confidence = db.Column(db.Float, nullable=True)
    
    # Wordsmimir Specific Results
    wordsmimir_raw_response = db.Column(db.JSON, nullable=True)
    wordsmimir_confidence = db.Column(db.Float, nullable=True)
    wordsmimir_analysis_version = db.Column(db.String(50), nullable=True)
    
    # Processing Metadata
    processing_status = db.Column(db.String(50), default='pending')
    processing_errors = db.Column(db.Text, nullable=True)
    processing_duration_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BehavioralPattern(db.Model):
    """
    Stores identified patterns in individual and group behavior
    including stress responses, deception indicators, and influence dynamics.
    """
    __tablename__ = 'behavioral_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    pattern_id = db.Column(db.String(255), nullable=False, unique=True)
    individual_id = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('psychological_profiles.id'), nullable=True)
    
    # Pattern Classification
    pattern_type = db.Column(db.String(100), nullable=False)  # stress_response, deception, influence, etc.
    pattern_category = db.Column(db.String(50), nullable=False)  # behavioral, linguistic, physiological
    pattern_description = db.Column(db.Text, nullable=True)
    
    # Pattern Metrics
    frequency = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    significance_level = db.Column(db.Float, nullable=False)
    
    # Trigger Conditions
    trigger_contexts = db.Column(db.JSON, nullable=True)
    trigger_keywords = db.Column(db.JSON, nullable=True)
    trigger_emotional_states = db.Column(db.JSON, nullable=True)
    
    # Pattern Data
    pattern_indicators = db.Column(db.JSON, nullable=False)
    supporting_evidence = db.Column(db.JSON, nullable=True)
    contradicting_evidence = db.Column(db.JSON, nullable=True)
    
    # Temporal Information
    first_observed = db.Column(db.DateTime, nullable=False)
    last_observed = db.Column(db.DateTime, nullable=False)
    observation_count = db.Column(db.Integer, default=1)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PsychologicalAlert(db.Model):
    """
    Stores psychological alerts and warnings based on analysis results.
    """
    __tablename__ = 'psychological_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(255), nullable=False, unique=True)
    individual_id = db.Column(db.String(255), nullable=False)
    communication_id = db.Column(db.String(255), nullable=True)
    
    # Alert Classification
    alert_type = db.Column(db.String(100), nullable=False)  # stress, deception, anomaly, etc.
    severity_level = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    alert_category = db.Column(db.String(50), nullable=False)  # behavioral, emotional, cognitive
    
    # Alert Content
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.JSON, nullable=True)
    
    # Alert Metrics
    confidence_score = db.Column(db.Float, nullable=False)
    urgency_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    
    # Supporting Data
    trigger_data = db.Column(db.JSON, nullable=False)
    analysis_summary = db.Column(db.JSON, nullable=True)
    related_patterns = db.Column(db.JSON, nullable=True)
    
    # Status and Resolution
    status = db.Column(db.String(50), default='active')  # active, acknowledged, resolved, dismissed
    acknowledged_by = db.Column(db.String(255), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GroupDynamicsAnalysis(db.Model):
    """
    Stores analysis of group psychological dynamics and interactions.
    """
    __tablename__ = 'group_dynamics_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.String(255), nullable=False, unique=True)
    group_identifier = db.Column(db.String(255), nullable=False)
    session_id = db.Column(db.String(255), nullable=True)  # meeting, call, etc.
    
    # Group Composition
    participant_ids = db.Column(db.JSON, nullable=False)
    participant_count = db.Column(db.Integer, nullable=False)
    group_type = db.Column(db.String(100), nullable=True)  # team, board, negotiation, etc.
    
    # Group Dynamics Metrics
    power_distribution = db.Column(db.JSON, nullable=True)
    influence_patterns = db.Column(db.JSON, nullable=True)
    coalition_indicators = db.Column(db.JSON, nullable=True)
    conflict_markers = db.Column(db.JSON, nullable=True)
    
    # Emotional Climate
    group_emotional_state = db.Column(db.String(100), nullable=True)
    emotional_contagion_score = db.Column(db.Float, nullable=True)
    stress_distribution = db.Column(db.JSON, nullable=True)
    engagement_levels = db.Column(db.JSON, nullable=True)
    
    # Communication Patterns
    speaking_time_distribution = db.Column(db.JSON, nullable=True)
    interruption_patterns = db.Column(db.JSON, nullable=True)
    turn_taking_analysis = db.Column(db.JSON, nullable=True)
    topic_control_patterns = db.Column(db.JSON, nullable=True)
    
    # Group Health Indicators
    collaboration_effectiveness = db.Column(db.Float, nullable=True)
    trust_indicators = db.Column(db.JSON, nullable=True)
    psychological_safety_score = db.Column(db.Float, nullable=True)
    decision_making_efficiency = db.Column(db.Float, nullable=True)
    
    # Analysis Metadata
    analysis_confidence = db.Column(db.Float, nullable=False)
    analysis_duration = db.Column(db.Integer, nullable=True)  # in minutes
    session_timestamp = db.Column(db.DateTime, nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WordsmimirApiLog(db.Model):
    """
    Logs all interactions with the wordsmimir API for monitoring and debugging.
    """
    __tablename__ = 'wordsmimir_api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(255), nullable=False, unique=True)
    communication_id = db.Column(db.String(255), nullable=True)
    
    # Request Information
    endpoint = db.Column(db.String(255), nullable=False)
    request_method = db.Column(db.String(10), nullable=False)
    request_payload = db.Column(db.JSON, nullable=True)
    request_headers = db.Column(db.JSON, nullable=True)
    
    # Response Information
    response_status = db.Column(db.Integer, nullable=True)
    response_payload = db.Column(db.JSON, nullable=True)
    response_headers = db.Column(db.JSON, nullable=True)
    
    # Performance Metrics
    request_duration_ms = db.Column(db.Integer, nullable=True)
    processing_time_ms = db.Column(db.Integer, nullable=True)
    
    # Error Information
    error_message = db.Column(db.Text, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    api_version = db.Column(db.String(50), nullable=True)
    client_version = db.Column(db.String(50), nullable=True)

# Utility functions for model operations
def create_psychological_profile(individual_id, name=None, email=None):
    """Create a new psychological profile for an individual."""
    profile = PsychologicalProfile(
        individual_id=individual_id,
        name=name,
        email=email
    )
    db.session.add(profile)
    db.session.commit()
    return profile

def get_or_create_profile(individual_id, name=None, email=None):
    """Get existing profile or create new one if it doesn't exist."""
    profile = PsychologicalProfile.query.filter_by(individual_id=individual_id).first()
    if not profile:
        profile = create_psychological_profile(individual_id, name, email)
    return profile

def create_communication_analysis(communication_id, individual_id, analysis_type, **kwargs):
    """Create a new communication analysis record."""
    profile = get_or_create_profile(individual_id)
    
    analysis = CommunicationAnalysis(
        communication_id=communication_id,
        individual_id=individual_id,
        profile_id=profile.id,
        analysis_type=analysis_type,
        **kwargs
    )
    db.session.add(analysis)
    db.session.commit()
    return analysis

def create_psychological_alert(individual_id, alert_type, severity_level, title, description, **kwargs):
    """Create a new psychological alert."""
    import uuid
    alert_id = str(uuid.uuid4())
    
    alert = PsychologicalAlert(
        alert_id=alert_id,
        individual_id=individual_id,
        alert_type=alert_type,
        severity_level=severity_level,
        title=title,
        description=description,
        **kwargs
    )
    db.session.add(alert)
    db.session.commit()
    return alert

def update_profile_from_analysis(profile_id, analysis_results):
    """Update psychological profile based on new analysis results."""
    profile = PsychologicalProfile.query.get(profile_id)
    if not profile:
        return None
    
    # Update analysis count
    profile.analysis_count += 1
    
    # Update baselines if audio data is available
    if 'speech_rate' in analysis_results and analysis_results['speech_rate']:
        if profile.baseline_speech_rate:
            # Running average
            profile.baseline_speech_rate = (profile.baseline_speech_rate * 0.8 + 
                                          analysis_results['speech_rate'] * 0.2)
        else:
            profile.baseline_speech_rate = analysis_results['speech_rate']
    
    # Update emotional baseline
    if 'emotional_valence' in analysis_results and analysis_results['emotional_valence']:
        if profile.baseline_emotional_state:
            # Simple emotional state tracking
            if analysis_results['emotional_valence'] > 0.5:
                profile.baseline_emotional_state = 'positive'
            elif analysis_results['emotional_valence'] < -0.5:
                profile.baseline_emotional_state = 'negative'
            else:
                profile.baseline_emotional_state = 'neutral'
        else:
            if analysis_results['emotional_valence'] > 0.5:
                profile.baseline_emotional_state = 'positive'
            elif analysis_results['emotional_valence'] < -0.5:
                profile.baseline_emotional_state = 'negative'
            else:
                profile.baseline_emotional_state = 'neutral'
    
    # Update authenticity baseline
    if 'authenticity_score' in analysis_results and analysis_results['authenticity_score']:
        if profile.authenticity_baseline:
            profile.authenticity_baseline = (profile.authenticity_baseline * 0.8 + 
                                           analysis_results['authenticity_score'] * 0.2)
        else:
            profile.authenticity_baseline = analysis_results['authenticity_score']
    
    profile.last_updated = datetime.utcnow()
    db.session.commit()
    return profile

