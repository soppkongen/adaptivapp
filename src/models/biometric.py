"""
AURA Biometric Models

Database models for storing and managing biometric data and adaptation preferences
in the Elite Command Data API with AURA integration.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.models.user import db

class BiometricDataType(Enum):
    """Types of biometric data that can be processed"""
    FACIAL_EXPRESSION = "facial_expression"
    EYE_TRACKING = "eye_tracking"
    GAZE_PATTERN = "gaze_pattern"
    ATTENTION_LEVEL = "attention_level"
    STRESS_INDICATOR = "stress_indicator"
    COGNITIVE_LOAD = "cognitive_load"
    EMOTIONAL_STATE = "emotional_state"
    PHYSIOLOGICAL = "physiological"

class AdaptationTrigger(Enum):
    """Types of adaptation triggers"""
    STRESS_ELEVATION = "stress_elevation"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    ATTENTION_DEFICIT = "attention_deficit"
    FATIGUE_DETECTION = "fatigue_detection"
    CONFUSION_INDICATOR = "confusion_indicator"
    HIGH_ENGAGEMENT = "high_engagement"
    DECISION_HESITATION = "decision_hesitation"
    EMOTIONAL_CHANGE = "emotional_change"

class AdaptationType(Enum):
    """Types of interface adaptations"""
    COLOR_SCHEME = "color_scheme"
    TYPOGRAPHY = "typography"
    LAYOUT_DENSITY = "layout_density"
    INFORMATION_FILTERING = "information_filtering"
    INTERACTION_SPEED = "interaction_speed"
    CONTENT_PRIORITIZATION = "content_prioritization"
    AUTOMATION_LEVEL = "automation_level"
    FEEDBACK_INTENSITY = "feedback_intensity"

class BiometricSession(db.Model):
    """Represents a biometric monitoring session"""
    __tablename__ = 'biometric_sessions'
    
    session_id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime)
    device_info = Column(JSON)  # Camera resolution, browser info, etc.
    privacy_settings = Column(JSON)  # User privacy preferences
    session_quality = Column(Float)  # Overall session data quality score
    total_adaptations = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", backref="biometric_sessions")
    biometric_data = relationship("BiometricDataPoint", backref="session", cascade="all, delete-orphan")
    adaptations = relationship("InterfaceAdaptation", backref="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<BiometricSession {self.session_id} for user {self.user_id}>'

class BiometricDataPoint(db.Model):
    """Individual biometric data measurements"""
    __tablename__ = 'biometric_data_points'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey('biometric_sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_type = Column(String(50), nullable=False)  # BiometricDataType enum value
    
    # Facial expression data
    facial_expressions = Column(JSON)  # {happy: 0.1, sad: 0.05, angry: 0.02, ...}
    emotion_confidence = Column(Float)
    
    # Eye tracking data
    gaze_x = Column(Float)  # Normalized gaze coordinates (0-1)
    gaze_y = Column(Float)
    pupil_diameter = Column(Float)
    blink_rate = Column(Float)
    fixation_duration = Column(Float)
    saccade_velocity = Column(Float)
    
    # Attention and cognitive metrics
    attention_score = Column(Float)  # 0-1 scale
    cognitive_load_score = Column(Float)  # 0-1 scale
    stress_level = Column(Float)  # 0-1 scale
    fatigue_indicator = Column(Float)  # 0-1 scale
    
    # Processing metadata
    confidence_score = Column(Float)  # Confidence in the measurement
    processing_latency = Column(Float)  # Time to process this data point
    data_quality = Column(Float)  # Quality score for this measurement
    
    def __repr__(self):
        return f'<BiometricDataPoint {self.id} - {self.data_type} at {self.timestamp}>'

class InterfaceAdaptation(db.Model):
    """Records of interface adaptations made based on biometric feedback"""
    __tablename__ = 'interface_adaptations'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey('biometric_sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Trigger information
    trigger_type = Column(String(50), nullable=False)  # AdaptationTrigger enum value
    trigger_data = Column(JSON)  # Biometric data that triggered the adaptation
    trigger_confidence = Column(Float)  # Confidence in the trigger detection
    
    # Adaptation details
    adaptation_type = Column(String(50), nullable=False)  # AdaptationType enum value
    adaptation_parameters = Column(JSON)  # Specific parameters of the adaptation
    previous_state = Column(JSON)  # Interface state before adaptation
    new_state = Column(JSON)  # Interface state after adaptation
    
    # Effectiveness tracking
    user_response = Column(JSON)  # Biometric response to the adaptation
    effectiveness_score = Column(Float)  # Calculated effectiveness (0-1)
    user_feedback = Column(String(10))  # 'positive', 'negative', 'neutral'
    duration_active = Column(Float)  # How long the adaptation remained active
    
    # Metadata
    adaptation_source = Column(String(20), default='biometric')  # 'biometric' or 'manual'
    reverted = Column(Boolean, default=False)
    revert_reason = Column(String(100))
    
    def __repr__(self):
        return f'<InterfaceAdaptation {self.id} - {self.adaptation_type} triggered by {self.trigger_type}>'

class UserBiometricProfile(db.Model):
    """User-specific biometric patterns and preferences"""
    __tablename__ = 'user_biometric_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Baseline biometric patterns
    baseline_stress_level = Column(Float)
    baseline_attention_span = Column(Float)
    baseline_cognitive_load = Column(Float)
    baseline_blink_rate = Column(Float)
    baseline_pupil_size = Column(Float)
    
    # Adaptation preferences learned over time
    preferred_adaptations = Column(JSON)  # Most effective adaptations for this user
    adaptation_sensitivity = Column(Float, default=0.5)  # How quickly to trigger adaptations
    privacy_level = Column(String(20), default='standard')  # 'minimal', 'standard', 'comprehensive'
    
    # Effectiveness patterns
    most_effective_triggers = Column(JSON)  # Which triggers work best for this user
    least_effective_adaptations = Column(JSON)  # Which adaptations to avoid
    optimal_interface_states = Column(JSON)  # Preferred interface configurations
    
    # Temporal patterns
    daily_patterns = Column(JSON)  # How biometrics change throughout the day
    weekly_patterns = Column(JSON)  # Weekly patterns in biometric responses
    seasonal_adjustments = Column(JSON)  # Seasonal preference adjustments
    
    # Learning metadata
    total_sessions = Column(Integer, default=0)
    total_adaptations = Column(Integer, default=0)
    learning_confidence = Column(Float, default=0.0)  # Confidence in learned patterns
    last_pattern_update = Column(DateTime)
    
    # Relationships
    user = relationship("User", backref="biometric_profile")
    
    def __repr__(self):
        return f'<UserBiometricProfile for user {self.user_id}>'

class AdaptationRule(db.Model):
    """Rules for triggering interface adaptations based on biometric patterns"""
    __tablename__ = 'adaptation_rules'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Rule definition
    trigger_conditions = Column(JSON, nullable=False)  # Conditions that trigger this rule
    adaptation_actions = Column(JSON, nullable=False)  # Actions to take when triggered
    priority = Column(Integer, default=50)  # Rule priority (0-100)
    
    # Scope and applicability
    user_specific = Column(Boolean, default=False)  # Whether rule is user-specific
    user_id = Column(Integer, ForeignKey('users.id'))  # If user-specific
    context_filters = Column(JSON)  # When this rule applies (time, page, etc.)
    
    # Effectiveness and learning
    activation_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    average_effectiveness = Column(Float, default=0.0)
    last_activated = Column(DateTime)
    
    # Control settings
    active = Column(Boolean, default=True)
    cooldown_period = Column(Integer, default=30)  # Seconds before rule can trigger again
    max_activations_per_session = Column(Integer, default=10)
    
    # Relationships
    user = relationship("User", backref="adaptation_rules")
    
    def __repr__(self):
        return f'<AdaptationRule {self.id} - {self.name}>'

class BiometricAlert(db.Model):
    """Alerts generated based on concerning biometric patterns"""
    __tablename__ = 'biometric_alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(36), ForeignKey('biometric_sessions.session_id'))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # 'stress', 'fatigue', 'strain', etc.
    severity = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    message = Column(Text, nullable=False)
    
    # Triggering data
    trigger_data = Column(JSON)  # Biometric data that triggered the alert
    threshold_exceeded = Column(JSON)  # Which thresholds were exceeded
    pattern_detected = Column(String(100))  # Pattern that triggered the alert
    
    # Response and resolution
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    action_taken = Column(String(100))  # What action was taken in response
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", backref="biometric_alerts")
    session = relationship("BiometricSession", backref="alerts")
    
    def __repr__(self):
        return f'<BiometricAlert {self.id} - {self.alert_type} for user {self.user_id}>'

class BiometricCalibration(db.Model):
    """Calibration data for biometric sensors and algorithms"""
    __tablename__ = 'biometric_calibrations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Calibration type and parameters
    calibration_type = Column(String(50), nullable=False)  # 'eye_tracking', 'facial_baseline', etc.
    calibration_data = Column(JSON, nullable=False)  # Calibration parameters
    device_info = Column(JSON)  # Device used for calibration
    
    # Quality and validity
    calibration_quality = Column(Float)  # Quality score of the calibration
    valid_until = Column(DateTime)  # When calibration expires
    active = Column(Boolean, default=True)
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used = Column(DateTime)
    effectiveness_score = Column(Float)  # How well this calibration works
    
    # Relationships
    user = relationship("User", backref="biometric_calibrations")
    
    def __repr__(self):
        return f'<BiometricCalibration {self.id} - {self.calibration_type} for user {self.user_id}>'

