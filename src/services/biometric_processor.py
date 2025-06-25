"""
AURA Biometric Processing Service

Core service for processing biometric data, detecting patterns, and triggering
interface adaptations in real-time.
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import uuid

from ..models.biometric import (
    BiometricSession, BiometricDataPoint, InterfaceAdaptation, 
    UserBiometricProfile, AdaptationRule, BiometricAlert,
    BiometricDataType, AdaptationTrigger, AdaptationType, db
)

logger = logging.getLogger(__name__)

@dataclass
class BiometricReading:
    """Structured biometric data reading"""
    timestamp: datetime
    facial_expressions: Dict[str, float]
    gaze_position: Tuple[float, float]
    pupil_diameter: float
    blink_rate: float
    attention_score: float
    stress_level: float
    cognitive_load: float
    confidence: float

@dataclass
class AdaptationDecision:
    """Decision to adapt the interface"""
    trigger_type: AdaptationTrigger
    adaptation_type: AdaptationType
    parameters: Dict[str, Any]
    confidence: float
    urgency: float
    reasoning: str

class BiometricProcessor:
    """Core biometric data processing engine"""
    
    def __init__(self):
        self.stress_threshold = 0.7
        self.cognitive_load_threshold = 0.8
        self.attention_threshold = 0.3
        self.fatigue_threshold = 0.6
        
        # Pattern detection windows
        self.short_window = 30  # seconds
        self.medium_window = 120  # seconds
        self.long_window = 300  # seconds
        
        # Adaptation cooldown periods
        self.adaptation_cooldowns = {
            AdaptationType.COLOR_SCHEME: 60,
            AdaptationType.LAYOUT_DENSITY: 120,
            AdaptationType.INFORMATION_FILTERING: 30,
            AdaptationType.TYPOGRAPHY: 180,
            AdaptationType.INTERACTION_SPEED: 45,
            AdaptationType.CONTENT_PRIORITIZATION: 60,
            AdaptationType.AUTOMATION_LEVEL: 300,
            AdaptationType.FEEDBACK_INTENSITY: 90
        }
    
    def process_biometric_data(self, session_id: str, reading: BiometricReading) -> List[AdaptationDecision]:
        """
        Process a biometric reading and determine if adaptations are needed
        
        Args:
            session_id: Current biometric session ID
            reading: Biometric data reading
            
        Returns:
            List of adaptation decisions
        """
        try:
            # Store the biometric data point
            data_point = self._store_biometric_data(session_id, reading)
            
            # Get user profile for personalized processing
            session = BiometricSession.query.filter_by(session_id=session_id).first()
            if not session:
                logger.error(f"Session {session_id} not found")
                return []
            
            user_profile = UserBiometricProfile.query.filter_by(user_id=session.user_id).first()
            
            # Analyze patterns and detect triggers
            triggers = self._detect_adaptation_triggers(session_id, reading, user_profile)
            
            # Generate adaptation decisions
            decisions = []
            for trigger in triggers:
                decision = self._generate_adaptation_decision(trigger, reading, user_profile)
                if decision and self._should_apply_adaptation(session_id, decision):
                    decisions.append(decision)
            
            # Update user profile with new data
            if user_profile:
                self._update_user_profile(user_profile, reading)
            
            return decisions
            
        except Exception as e:
            logger.error(f"Error processing biometric data: {str(e)}")
            return []
    
    def _store_biometric_data(self, session_id: str, reading: BiometricReading) -> BiometricDataPoint:
        """Store biometric data point in database"""
        data_point = BiometricDataPoint(
            session_id=session_id,
            timestamp=reading.timestamp,
            data_type=BiometricDataType.FACIAL_EXPRESSION.value,
            facial_expressions=reading.facial_expressions,
            emotion_confidence=reading.confidence,
            gaze_x=reading.gaze_position[0],
            gaze_y=reading.gaze_position[1],
            pupil_diameter=reading.pupil_diameter,
            blink_rate=reading.blink_rate,
            attention_score=reading.attention_score,
            cognitive_load_score=reading.cognitive_load,
            stress_level=reading.stress_level,
            confidence_score=reading.confidence,
            processing_latency=0.0,  # Will be calculated
            data_quality=self._calculate_data_quality(reading)
        )
        
        db.session.add(data_point)
        db.session.commit()
        
        return data_point
    
    def _calculate_data_quality(self, reading: BiometricReading) -> float:
        """Calculate quality score for biometric reading"""
        quality_factors = []
        
        # Confidence factor
        quality_factors.append(reading.confidence)
        
        # Gaze position validity (within screen bounds)
        if 0 <= reading.gaze_position[0] <= 1 and 0 <= reading.gaze_position[1] <= 1:
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.5)
        
        # Pupil diameter reasonableness (2-8mm typical range, normalized)
        if 0.1 <= reading.pupil_diameter <= 1.0:
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.7)
        
        # Blink rate reasonableness (5-20 blinks per minute typical)
        if 0.08 <= reading.blink_rate <= 0.33:  # Normalized per second
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.8)
        
        return np.mean(quality_factors)
    
    def _detect_adaptation_triggers(self, session_id: str, reading: BiometricReading, 
                                  user_profile: Optional[UserBiometricProfile]) -> List[AdaptationTrigger]:
        """Detect triggers for interface adaptation"""
        triggers = []
        
        # Get recent data for pattern analysis
        recent_data = self._get_recent_biometric_data(session_id, self.medium_window)
        
        # Stress elevation detection
        if self._detect_stress_elevation(reading, recent_data, user_profile):
            triggers.append(AdaptationTrigger.STRESS_ELEVATION)
        
        # Cognitive overload detection
        if self._detect_cognitive_overload(reading, recent_data, user_profile):
            triggers.append(AdaptationTrigger.COGNITIVE_OVERLOAD)
        
        # Attention deficit detection
        if self._detect_attention_deficit(reading, recent_data, user_profile):
            triggers.append(AdaptationTrigger.ATTENTION_DEFICIT)
        
        # Fatigue detection
        if self._detect_fatigue(reading, recent_data, user_profile):
            triggers.append(AdaptationTrigger.FATIGUE_DETECTION)
        
        # Confusion detection
        if self._detect_confusion(reading, recent_data, user_profile):
            triggers.append(AdaptationTrigger.CONFUSION_INDICATOR)
        
        # High engagement detection
        if self._detect_high_engagement(reading, recent_data, user_profile):
            triggers.append(AdaptationTrigger.HIGH_ENGAGEMENT)
        
        # Decision hesitation detection
        if self._detect_decision_hesitation(reading, recent_data, user_profile):
            triggers.append(AdaptationTrigger.DECISION_HESITATION)
        
        return triggers
    
    def _detect_stress_elevation(self, reading: BiometricReading, recent_data: List[BiometricDataPoint],
                               user_profile: Optional[UserBiometricProfile]) -> bool:
        """Detect stress elevation patterns"""
        # Current stress level check
        current_stress = reading.stress_level
        threshold = user_profile.baseline_stress_level + 0.2 if user_profile else self.stress_threshold
        
        if current_stress > threshold:
            return True
        
        # Trend analysis - increasing stress over time
        if len(recent_data) >= 5:
            recent_stress = [dp.stress_level for dp in recent_data[-5:] if dp.stress_level is not None]
            if len(recent_stress) >= 3:
                # Check for increasing trend
                trend = np.polyfit(range(len(recent_stress)), recent_stress, 1)[0]
                if trend > 0.02:  # Increasing stress trend
                    return True
        
        return False
    
    def _detect_cognitive_overload(self, reading: BiometricReading, recent_data: List[BiometricDataPoint],
                                 user_profile: Optional[UserBiometricProfile]) -> bool:
        """Detect cognitive overload patterns"""
        # High cognitive load with sustained attention
        if reading.cognitive_load > self.cognitive_load_threshold and reading.attention_score > 0.7:
            return True
        
        # Rapid pupil dilation (indicator of mental effort)
        if len(recent_data) >= 3:
            recent_pupils = [dp.pupil_diameter for dp in recent_data[-3:] if dp.pupil_diameter is not None]
            if len(recent_pupils) >= 2:
                pupil_change = recent_pupils[-1] - recent_pupils[0]
                if pupil_change > 0.1:  # Significant dilation
                    return True
        
        return False
    
    def _detect_attention_deficit(self, reading: BiometricReading, recent_data: List[BiometricDataPoint],
                                user_profile: Optional[UserBiometricProfile]) -> bool:
        """Detect attention deficit patterns"""
        # Low attention score
        if reading.attention_score < self.attention_threshold:
            return True
        
        # Erratic gaze patterns
        if len(recent_data) >= 5:
            recent_gaze_x = [dp.gaze_x for dp in recent_data[-5:] if dp.gaze_x is not None]
            recent_gaze_y = [dp.gaze_y for dp in recent_data[-5:] if dp.gaze_y is not None]
            
            if len(recent_gaze_x) >= 3 and len(recent_gaze_y) >= 3:
                gaze_variance_x = np.var(recent_gaze_x)
                gaze_variance_y = np.var(recent_gaze_y)
                
                # High variance indicates scattered attention
                if gaze_variance_x > 0.1 or gaze_variance_y > 0.1:
                    return True
        
        return False
    
    def _detect_fatigue(self, reading: BiometricReading, recent_data: List[BiometricDataPoint],
                       user_profile: Optional[UserBiometricProfile]) -> bool:
        """Detect fatigue patterns"""
        # Increased blink rate
        baseline_blink = user_profile.baseline_blink_rate if user_profile else 0.15
        if reading.blink_rate > baseline_blink * 1.5:
            return True
        
        # Declining attention over time
        if len(recent_data) >= 10:
            recent_attention = [dp.attention_score for dp in recent_data[-10:] if dp.attention_score is not None]
            if len(recent_attention) >= 5:
                # Check for declining trend
                trend = np.polyfit(range(len(recent_attention)), recent_attention, 1)[0]
                if trend < -0.01:  # Declining attention
                    return True
        
        return False
    
    def _detect_confusion(self, reading: BiometricReading, recent_data: List[BiometricDataPoint],
                         user_profile: Optional[UserBiometricProfile]) -> bool:
        """Detect confusion patterns"""
        # Facial expression analysis for confusion
        if 'confused' in reading.facial_expressions and reading.facial_expressions['confused'] > 0.3:
            return True
        
        # Combination of frowning and concentrated expression
        frown = reading.facial_expressions.get('angry', 0) + reading.facial_expressions.get('sad', 0)
        concentration = reading.facial_expressions.get('neutral', 0)
        
        if frown > 0.2 and concentration > 0.5:
            return True
        
        return False
    
    def _detect_high_engagement(self, reading: BiometricReading, recent_data: List[BiometricDataPoint],
                              user_profile: Optional[UserBiometricProfile]) -> bool:
        """Detect high engagement patterns"""
        # High attention with moderate stress (flow state)
        if reading.attention_score > 0.8 and 0.3 < reading.stress_level < 0.6:
            return True
        
        # Stable gaze with good attention
        if len(recent_data) >= 5:
            recent_gaze_x = [dp.gaze_x for dp in recent_data[-5:] if dp.gaze_x is not None]
            if len(recent_gaze_x) >= 3:
                gaze_stability = 1.0 - np.var(recent_gaze_x)
                if gaze_stability > 0.8 and reading.attention_score > 0.7:
                    return True
        
        return False
    
    def _detect_decision_hesitation(self, reading: BiometricReading, recent_data: List[BiometricDataPoint],
                                  user_profile: Optional[UserBiometricProfile]) -> bool:
        """Detect decision hesitation patterns"""
        # Micro-expressions of uncertainty
        uncertainty_expressions = ['surprised', 'fearful']
        uncertainty_score = sum(reading.facial_expressions.get(expr, 0) for expr in uncertainty_expressions)
        
        if uncertainty_score > 0.2:
            return True
        
        # Gaze pattern indicating indecision (looking back and forth)
        if len(recent_data) >= 6:
            recent_gaze_x = [dp.gaze_x for dp in recent_data[-6:] if dp.gaze_x is not None]
            if len(recent_gaze_x) >= 4:
                # Check for oscillating pattern
                direction_changes = 0
                for i in range(1, len(recent_gaze_x) - 1):
                    if ((recent_gaze_x[i] > recent_gaze_x[i-1]) != 
                        (recent_gaze_x[i+1] > recent_gaze_x[i])):
                        direction_changes += 1
                
                if direction_changes >= 2:  # Multiple direction changes
                    return True
        
        return False
    
    def _generate_adaptation_decision(self, trigger: AdaptationTrigger, reading: BiometricReading,
                                    user_profile: Optional[UserBiometricProfile]) -> Optional[AdaptationDecision]:
        """Generate adaptation decision based on trigger"""
        
        # Adaptation mapping based on triggers
        adaptation_map = {
            AdaptationTrigger.STRESS_ELEVATION: [
                (AdaptationType.COLOR_SCHEME, {'scheme': 'calming', 'intensity': 0.8}),
                (AdaptationType.INFORMATION_FILTERING, {'filter_level': 'essential_only'}),
                (AdaptationType.LAYOUT_DENSITY, {'density': 'simplified'})
            ],
            AdaptationTrigger.COGNITIVE_OVERLOAD: [
                (AdaptationType.LAYOUT_DENSITY, {'density': 'minimal'}),
                (AdaptationType.INFORMATION_FILTERING, {'filter_level': 'high_priority'}),
                (AdaptationType.TYPOGRAPHY, {'size_increase': 1.2, 'spacing_increase': 1.3})
            ],
            AdaptationTrigger.ATTENTION_DEFICIT: [
                (AdaptationType.CONTENT_PRIORITIZATION, {'highlight_important': True}),
                (AdaptationType.FEEDBACK_INTENSITY, {'intensity': 'enhanced'}),
                (AdaptationType.COLOR_SCHEME, {'contrast': 'high'})
            ],
            AdaptationTrigger.FATIGUE_DETECTION: [
                (AdaptationType.COLOR_SCHEME, {'scheme': 'warm', 'brightness': 0.7}),
                (AdaptationType.AUTOMATION_LEVEL, {'level': 'increased'}),
                (AdaptationType.INTERACTION_SPEED, {'speed': 'relaxed'})
            ],
            AdaptationTrigger.CONFUSION_INDICATOR: [
                (AdaptationType.FEEDBACK_INTENSITY, {'explanations': True, 'guidance': True}),
                (AdaptationType.LAYOUT_DENSITY, {'density': 'simplified'}),
                (AdaptationType.CONTENT_PRIORITIZATION, {'focus_mode': True})
            ],
            AdaptationTrigger.HIGH_ENGAGEMENT: [
                (AdaptationType.INFORMATION_FILTERING, {'filter_level': 'comprehensive'}),
                (AdaptationType.CONTENT_PRIORITIZATION, {'detail_level': 'enhanced'}),
                (AdaptationType.LAYOUT_DENSITY, {'density': 'detailed'})
            ],
            AdaptationTrigger.DECISION_HESITATION: [
                (AdaptationType.FEEDBACK_INTENSITY, {'decision_support': True}),
                (AdaptationType.CONTENT_PRIORITIZATION, {'comparison_mode': True}),
                (AdaptationType.AUTOMATION_LEVEL, {'suggestions': 'enhanced'})
            ]
        }
        
        if trigger not in adaptation_map:
            return None
        
        # Select best adaptation based on user profile and current context
        adaptations = adaptation_map[trigger]
        
        # For now, select the first adaptation (can be enhanced with ML)
        adaptation_type, base_parameters = adaptations[0]
        
        # Customize parameters based on user profile
        parameters = self._customize_adaptation_parameters(
            base_parameters, user_profile, reading
        )
        
        # Calculate confidence and urgency
        confidence = self._calculate_adaptation_confidence(trigger, reading, user_profile)
        urgency = self._calculate_adaptation_urgency(trigger, reading)
        
        reasoning = f"Triggered by {trigger.value} with confidence {confidence:.2f}"
        
        return AdaptationDecision(
            trigger_type=trigger,
            adaptation_type=adaptation_type,
            parameters=parameters,
            confidence=confidence,
            urgency=urgency,
            reasoning=reasoning
        )
    
    def _customize_adaptation_parameters(self, base_parameters: Dict[str, Any],
                                       user_profile: Optional[UserBiometricProfile],
                                       reading: BiometricReading) -> Dict[str, Any]:
        """Customize adaptation parameters based on user profile"""
        parameters = base_parameters.copy()
        
        if user_profile and user_profile.preferred_adaptations:
            # Apply user preferences
            preferences = user_profile.preferred_adaptations
            
            # Adjust intensity based on user sensitivity
            if 'intensity' in parameters and 'sensitivity' in preferences:
                parameters['intensity'] *= preferences['sensitivity']
            
            # Apply preferred color schemes
            if 'scheme' in parameters and 'color_preferences' in preferences:
                preferred_scheme = preferences['color_preferences'].get(parameters['scheme'])
                if preferred_scheme:
                    parameters['scheme'] = preferred_scheme
        
        return parameters
    
    def _calculate_adaptation_confidence(self, trigger: AdaptationTrigger, reading: BiometricReading,
                                       user_profile: Optional[UserBiometricProfile]) -> float:
        """Calculate confidence in adaptation decision"""
        base_confidence = reading.confidence
        
        # Adjust based on data quality
        data_quality = self._calculate_data_quality(reading)
        confidence = base_confidence * data_quality
        
        # Adjust based on user profile learning
        if user_profile and user_profile.learning_confidence:
            confidence = (confidence + user_profile.learning_confidence) / 2
        
        return min(confidence, 1.0)
    
    def _calculate_adaptation_urgency(self, trigger: AdaptationTrigger, reading: BiometricReading) -> float:
        """Calculate urgency of adaptation"""
        urgency_map = {
            AdaptationTrigger.STRESS_ELEVATION: 0.9,
            AdaptationTrigger.COGNITIVE_OVERLOAD: 0.8,
            AdaptationTrigger.CONFUSION_INDICATOR: 0.7,
            AdaptationTrigger.FATIGUE_DETECTION: 0.6,
            AdaptationTrigger.ATTENTION_DEFICIT: 0.5,
            AdaptationTrigger.DECISION_HESITATION: 0.4,
            AdaptationTrigger.HIGH_ENGAGEMENT: 0.2,
            AdaptationTrigger.EMOTIONAL_CHANGE: 0.3
        }
        
        base_urgency = urgency_map.get(trigger, 0.5)
        
        # Adjust based on severity
        if trigger == AdaptationTrigger.STRESS_ELEVATION:
            base_urgency *= reading.stress_level
        elif trigger == AdaptationTrigger.COGNITIVE_OVERLOAD:
            base_urgency *= reading.cognitive_load
        elif trigger == AdaptationTrigger.ATTENTION_DEFICIT:
            base_urgency *= (1.0 - reading.attention_score)
        
        return min(base_urgency, 1.0)
    
    def _should_apply_adaptation(self, session_id: str, decision: AdaptationDecision) -> bool:
        """Determine if adaptation should be applied based on cooldowns and rules"""
        # Check cooldown period
        cooldown = self.adaptation_cooldowns.get(decision.adaptation_type, 60)
        
        recent_adaptations = InterfaceAdaptation.query.filter(
            InterfaceAdaptation.session_id == session_id,
            InterfaceAdaptation.adaptation_type == decision.adaptation_type.value,
            InterfaceAdaptation.timestamp > datetime.utcnow() - timedelta(seconds=cooldown)
        ).count()
        
        if recent_adaptations > 0:
            return False
        
        # Check confidence threshold
        if decision.confidence < 0.6:
            return False
        
        return True
    
    def _get_recent_biometric_data(self, session_id: str, window_seconds: int) -> List[BiometricDataPoint]:
        """Get recent biometric data within time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        return BiometricDataPoint.query.filter(
            BiometricDataPoint.session_id == session_id,
            BiometricDataPoint.timestamp > cutoff_time
        ).order_by(BiometricDataPoint.timestamp.desc()).all()
    
    def _update_user_profile(self, profile: UserBiometricProfile, reading: BiometricReading):
        """Update user profile with new biometric data"""
        # Update baseline values with exponential moving average
        alpha = 0.1  # Learning rate
        
        if profile.baseline_stress_level is None:
            profile.baseline_stress_level = reading.stress_level
        else:
            profile.baseline_stress_level = (
                alpha * reading.stress_level + 
                (1 - alpha) * profile.baseline_stress_level
            )
        
        if profile.baseline_blink_rate is None:
            profile.baseline_blink_rate = reading.blink_rate
        else:
            profile.baseline_blink_rate = (
                alpha * reading.blink_rate + 
                (1 - alpha) * profile.baseline_blink_rate
            )
        
        # Update learning confidence
        profile.total_sessions = profile.total_sessions + 1 if profile.total_sessions else 1
        profile.learning_confidence = min(profile.total_sessions / 100.0, 1.0)
        profile.last_pattern_update = datetime.utcnow()
        
        db.session.commit()

# Global biometric processor instance
biometric_processor = BiometricProcessor()

