"""
Psychological Profiling Engine

This module provides comprehensive psychological profiling capabilities that aggregate
data from multiple sources to create detailed psychological profiles, behavioral
pattern recognition, risk assessment, and predictive analytics.
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PersonalityTrait(Enum):
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"

class CommunicationStyle(Enum):
    ASSERTIVE = "assertive"
    PASSIVE = "passive"
    AGGRESSIVE = "aggressive"
    PASSIVE_AGGRESSIVE = "passive_aggressive"
    COLLABORATIVE = "collaborative"

class StressIndicator(Enum):
    LINGUISTIC = "linguistic"
    VOCAL = "vocal"
    VISUAL = "visual"
    BEHAVIORAL = "behavioral"

@dataclass
class PersonalityProfile:
    """Comprehensive personality assessment based on Big Five model."""
    openness: float  # 0.0 to 1.0
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    confidence_score: float
    last_updated: datetime
    data_points_count: int

@dataclass
class CommunicationProfile:
    """Communication style and patterns analysis."""
    primary_style: CommunicationStyle
    style_confidence: float
    speech_rate_avg: float
    pitch_variance_avg: float
    linguistic_complexity_avg: float
    emotional_valence_avg: float
    authenticity_score_avg: float
    congruence_score_avg: float
    last_updated: datetime
    analysis_count: int

@dataclass
class StressProfile:
    """Stress indicators and patterns."""
    current_stress_level: float  # 0.0 to 1.0
    stress_trend: str  # "increasing", "decreasing", "stable"
    primary_stress_indicators: List[StressIndicator]
    stress_triggers: List[str]
    stress_patterns: Dict[str, Any]
    resilience_score: float
    last_updated: datetime

@dataclass
class BehavioralPattern:
    """Identified behavioral patterns."""
    pattern_type: str
    pattern_description: str
    frequency: float
    confidence: float
    first_observed: datetime
    last_observed: datetime
    context_tags: List[str]
    risk_level: RiskLevel

@dataclass
class RiskAssessment:
    """Comprehensive risk assessment."""
    overall_risk_score: float  # 0.0 to 1.0
    risk_level: RiskLevel
    risk_factors: List[Dict[str, Any]]
    protective_factors: List[Dict[str, Any]]
    recommendations: List[str]
    confidence: float
    assessment_date: datetime

@dataclass
class PredictiveInsights:
    """Predictive analytics and insights."""
    performance_prediction: float  # 0.0 to 1.0
    stress_prediction: float
    communication_effectiveness_prediction: float
    leadership_potential: float
    team_compatibility_score: float
    growth_areas: List[str]
    strengths: List[str]
    confidence: float
    prediction_horizon_days: int

@dataclass
class ComprehensiveProfile:
    """Complete psychological profile aggregating all components."""
    individual_id: str
    personality: PersonalityProfile
    communication: CommunicationProfile
    stress: StressProfile
    behavioral_patterns: List[BehavioralPattern]
    risk_assessment: RiskAssessment
    predictive_insights: PredictiveInsights
    profile_completeness: float  # 0.0 to 1.0
    last_updated: datetime
    data_quality_score: float

class PsychologicalProfilingEngine:
    """
    Comprehensive psychological profiling engine that aggregates data from multiple
    sources to create detailed psychological profiles.
    """
    
    def __init__(self):
        self.personality_weights = {
            'linguistic_complexity': 0.3,
            'emotional_valence': 0.25,
            'speech_patterns': 0.2,
            'visual_cues': 0.15,
            'behavioral_consistency': 0.1
        }
        
        self.stress_indicators = {
            'voice_stress_score': 0.3,
            'linguistic_stress_markers': 0.25,
            'visual_stress_indicators': 0.2,
            'communication_inconsistency': 0.15,
            'behavioral_changes': 0.1
        }
        
        self.risk_factors = {
            'deception_indicators': 0.4,
            'stress_levels': 0.3,
            'communication_breakdown': 0.2,
            'behavioral_anomalies': 0.1
        }
    
    def create_comprehensive_profile(self, individual_id: str, 
                                   analysis_data: List[Dict[str, Any]]) -> ComprehensiveProfile:
        """
        Create a comprehensive psychological profile from multiple analysis data points.
        
        Args:
            individual_id: Individual identifier
            analysis_data: List of analysis results from various sources
            
        Returns:
            ComprehensiveProfile object
        """
        try:
            if not analysis_data:
                raise ValueError("No analysis data provided")
            
            # Extract and organize data by type
            text_analyses = [d for d in analysis_data if d.get('analysis_type') == 'text']
            audio_analyses = [d for d in analysis_data if d.get('analysis_type') == 'audio']
            video_analyses = [d for d in analysis_data if d.get('analysis_type') == 'video']
            multimodal_analyses = [d for d in analysis_data if d.get('analysis_type') == 'multimodal']
            
            # Create personality profile
            personality = self._create_personality_profile(
                text_analyses, audio_analyses, video_analyses, multimodal_analyses
            )
            
            # Create communication profile
            communication = self._create_communication_profile(
                text_analyses, audio_analyses, video_analyses, multimodal_analyses
            )
            
            # Create stress profile
            stress = self._create_stress_profile(
                text_analyses, audio_analyses, video_analyses, multimodal_analyses
            )
            
            # Identify behavioral patterns
            behavioral_patterns = self._identify_behavioral_patterns(analysis_data)
            
            # Perform risk assessment
            risk_assessment = self._perform_risk_assessment(
                personality, communication, stress, behavioral_patterns, analysis_data
            )
            
            # Generate predictive insights
            predictive_insights = self._generate_predictive_insights(
                personality, communication, stress, behavioral_patterns, analysis_data
            )
            
            # Calculate profile completeness and data quality
            profile_completeness = self._calculate_profile_completeness(
                text_analyses, audio_analyses, video_analyses, multimodal_analyses
            )
            data_quality_score = self._calculate_data_quality_score(analysis_data)
            
            return ComprehensiveProfile(
                individual_id=individual_id,
                personality=personality,
                communication=communication,
                stress=stress,
                behavioral_patterns=behavioral_patterns,
                risk_assessment=risk_assessment,
                predictive_insights=predictive_insights,
                profile_completeness=profile_completeness,
                last_updated=datetime.utcnow(),
                data_quality_score=data_quality_score
            )
            
        except Exception as e:
            logger.error(f"Error creating comprehensive profile: {str(e)}")
            raise
    
    def _create_personality_profile(self, text_analyses: List[Dict], 
                                  audio_analyses: List[Dict],
                                  video_analyses: List[Dict],
                                  multimodal_analyses: List[Dict]) -> PersonalityProfile:
        """Create personality profile using Big Five model."""
        
        # Initialize scores
        openness_scores = []
        conscientiousness_scores = []
        extraversion_scores = []
        agreeableness_scores = []
        neuroticism_scores = []
        
        # Extract personality indicators from text analyses
        for analysis in text_analyses:
            if 'linguistic_complexity' in analysis:
                openness_scores.append(min(analysis['linguistic_complexity'] / 10.0, 1.0))
            if 'emotional_valence' in analysis:
                agreeableness_scores.append((analysis['emotional_valence'] + 1.0) / 2.0)
            if 'stress_markers' in analysis:
                neuroticism_scores.append(min(len(analysis.get('stress_markers', [])) / 5.0, 1.0))
        
        # Extract personality indicators from audio analyses
        for analysis in audio_analyses:
            if 'speech_rate' in analysis:
                extraversion_scores.append(min(analysis['speech_rate'] / 5.0, 1.0))
            if 'voice_stress_score' in analysis:
                neuroticism_scores.append(analysis['voice_stress_score'])
            if 'pitch_variance' in analysis:
                openness_scores.append(min(analysis['pitch_variance'] / 50.0, 1.0))
        
        # Extract personality indicators from video analyses
        for analysis in video_analyses:
            if 'attention_score' in analysis:
                conscientiousness_scores.append(analysis['attention_score'])
            if 'facial_expressions' in analysis:
                expressions = analysis['facial_expressions']
                if isinstance(expressions, dict):
                    extraversion_scores.append(expressions.get('positive_emotions', 0.5))
                    agreeableness_scores.append(expressions.get('social_engagement', 0.5))
        
        # Extract personality indicators from multimodal analyses
        for analysis in multimodal_analyses:
            if 'congruence_score' in analysis:
                conscientiousness_scores.append(analysis['congruence_score'])
            if 'authenticity_score' in analysis:
                agreeableness_scores.append(analysis['authenticity_score'])
        
        # Calculate average scores with defaults
        openness = statistics.mean(openness_scores) if openness_scores else 0.5
        conscientiousness = statistics.mean(conscientiousness_scores) if conscientiousness_scores else 0.5
        extraversion = statistics.mean(extraversion_scores) if extraversion_scores else 0.5
        agreeableness = statistics.mean(agreeableness_scores) if agreeableness_scores else 0.5
        neuroticism = statistics.mean(neuroticism_scores) if neuroticism_scores else 0.5
        
        # Calculate confidence based on data availability
        total_data_points = len(openness_scores + conscientiousness_scores + 
                               extraversion_scores + agreeableness_scores + neuroticism_scores)
        confidence_score = min(total_data_points / 20.0, 1.0)  # Max confidence with 20+ data points
        
        return PersonalityProfile(
            openness=max(0.0, min(1.0, openness)),
            conscientiousness=max(0.0, min(1.0, conscientiousness)),
            extraversion=max(0.0, min(1.0, extraversion)),
            agreeableness=max(0.0, min(1.0, agreeableness)),
            neuroticism=max(0.0, min(1.0, neuroticism)),
            confidence_score=confidence_score,
            last_updated=datetime.utcnow(),
            data_points_count=total_data_points
        )
    
    def _create_communication_profile(self, text_analyses: List[Dict], 
                                    audio_analyses: List[Dict],
                                    video_analyses: List[Dict],
                                    multimodal_analyses: List[Dict]) -> CommunicationProfile:
        """Create communication style and patterns profile."""
        
        # Collect communication metrics
        speech_rates = []
        pitch_variances = []
        linguistic_complexities = []
        emotional_valences = []
        authenticity_scores = []
        congruence_scores = []
        
        # Extract from audio analyses
        for analysis in audio_analyses:
            if 'speech_rate' in analysis:
                speech_rates.append(analysis['speech_rate'])
            if 'pitch_variance' in analysis:
                pitch_variances.append(analysis['pitch_variance'])
        
        # Extract from text analyses
        for analysis in text_analyses:
            if 'linguistic_complexity' in analysis:
                linguistic_complexities.append(analysis['linguistic_complexity'])
            if 'emotional_valence' in analysis:
                emotional_valences.append(analysis['emotional_valence'])
        
        # Extract from multimodal analyses
        for analysis in multimodal_analyses:
            if 'authenticity_score' in analysis:
                authenticity_scores.append(analysis['authenticity_score'])
            if 'congruence_score' in analysis:
                congruence_scores.append(analysis['congruence_score'])
        
        # Determine primary communication style
        style_scores = {
            CommunicationStyle.ASSERTIVE: 0.0,
            CommunicationStyle.PASSIVE: 0.0,
            CommunicationStyle.AGGRESSIVE: 0.0,
            CommunicationStyle.PASSIVE_AGGRESSIVE: 0.0,
            CommunicationStyle.COLLABORATIVE: 0.0
        }
        
        # Score based on speech rate
        avg_speech_rate = statistics.mean(speech_rates) if speech_rates else 2.5
        if avg_speech_rate > 3.5:
            style_scores[CommunicationStyle.AGGRESSIVE] += 0.3
            style_scores[CommunicationStyle.ASSERTIVE] += 0.2
        elif avg_speech_rate < 1.5:
            style_scores[CommunicationStyle.PASSIVE] += 0.3
        else:
            style_scores[CommunicationStyle.ASSERTIVE] += 0.2
            style_scores[CommunicationStyle.COLLABORATIVE] += 0.2
        
        # Score based on emotional valence
        avg_emotional_valence = statistics.mean(emotional_valences) if emotional_valences else 0.0
        if avg_emotional_valence > 0.3:
            style_scores[CommunicationStyle.COLLABORATIVE] += 0.3
            style_scores[CommunicationStyle.ASSERTIVE] += 0.2
        elif avg_emotional_valence < -0.3:
            style_scores[CommunicationStyle.AGGRESSIVE] += 0.2
            style_scores[CommunicationStyle.PASSIVE_AGGRESSIVE] += 0.2
        
        # Score based on authenticity and congruence
        avg_authenticity = statistics.mean(authenticity_scores) if authenticity_scores else 0.5
        avg_congruence = statistics.mean(congruence_scores) if congruence_scores else 0.5
        
        if avg_authenticity > 0.7 and avg_congruence > 0.7:
            style_scores[CommunicationStyle.ASSERTIVE] += 0.3
            style_scores[CommunicationStyle.COLLABORATIVE] += 0.2
        elif avg_authenticity < 0.3 or avg_congruence < 0.3:
            style_scores[CommunicationStyle.PASSIVE_AGGRESSIVE] += 0.3
        
        # Determine primary style
        primary_style = max(style_scores, key=style_scores.get)
        style_confidence = style_scores[primary_style]
        
        return CommunicationProfile(
            primary_style=primary_style,
            style_confidence=min(style_confidence, 1.0),
            speech_rate_avg=statistics.mean(speech_rates) if speech_rates else 0.0,
            pitch_variance_avg=statistics.mean(pitch_variances) if pitch_variances else 0.0,
            linguistic_complexity_avg=statistics.mean(linguistic_complexities) if linguistic_complexities else 0.0,
            emotional_valence_avg=statistics.mean(emotional_valences) if emotional_valences else 0.0,
            authenticity_score_avg=avg_authenticity,
            congruence_score_avg=avg_congruence,
            last_updated=datetime.utcnow(),
            analysis_count=len(text_analyses + audio_analyses + video_analyses + multimodal_analyses)
        )
    
    def _create_stress_profile(self, text_analyses: List[Dict], 
                             audio_analyses: List[Dict],
                             video_analyses: List[Dict],
                             multimodal_analyses: List[Dict]) -> StressProfile:
        """Create stress indicators and patterns profile."""
        
        stress_scores = []
        stress_indicators = []
        stress_triggers = []
        
        # Extract stress indicators from text analyses
        for analysis in text_analyses:
            if 'stress_markers' in analysis:
                markers = analysis['stress_markers']
                if isinstance(markers, list):
                    stress_scores.append(min(len(markers) / 5.0, 1.0))
                    stress_indicators.extend([StressIndicator.LINGUISTIC] * len(markers))
                    stress_triggers.extend(markers)
        
        # Extract stress indicators from audio analyses
        for analysis in audio_analyses:
            if 'voice_stress_score' in analysis:
                stress_scores.append(analysis['voice_stress_score'])
                if analysis['voice_stress_score'] > 0.6:
                    stress_indicators.append(StressIndicator.VOCAL)
        
        # Extract stress indicators from video analyses
        for analysis in video_analyses:
            if 'visual_stress_indicators' in analysis:
                indicators = analysis['visual_stress_indicators']
                if isinstance(indicators, list):
                    stress_scores.append(min(len(indicators) / 3.0, 1.0))
                    stress_indicators.extend([StressIndicator.VISUAL] * len(indicators))
        
        # Calculate current stress level
        current_stress_level = statistics.mean(stress_scores) if stress_scores else 0.0
        
        # Determine stress trend (simplified - would need historical data)
        stress_trend = "stable"  # Default
        if current_stress_level > 0.7:
            stress_trend = "increasing"
        elif current_stress_level < 0.3:
            stress_trend = "decreasing"
        
        # Identify primary stress indicators
        indicator_counts = Counter(stress_indicators)
        primary_indicators = [indicator for indicator, count in indicator_counts.most_common(3)]
        
        # Calculate resilience score (inverse of stress consistency)
        resilience_score = max(0.0, 1.0 - (current_stress_level * 0.8))
        
        return StressProfile(
            current_stress_level=max(0.0, min(1.0, current_stress_level)),
            stress_trend=stress_trend,
            primary_stress_indicators=primary_indicators,
            stress_triggers=list(set(stress_triggers))[:10],  # Top 10 unique triggers
            stress_patterns={
                "average_stress": current_stress_level,
                "stress_frequency": len(stress_scores),
                "indicator_distribution": dict(indicator_counts)
            },
            resilience_score=resilience_score,
            last_updated=datetime.utcnow()
        )
    
    def _identify_behavioral_patterns(self, analysis_data: List[Dict[str, Any]]) -> List[BehavioralPattern]:
        """Identify behavioral patterns from analysis data."""
        
        patterns = []
        
        # Pattern: Inconsistent communication
        authenticity_scores = [d.get('authenticity_score', 0.5) for d in analysis_data 
                             if 'authenticity_score' in d]
        if authenticity_scores:
            avg_authenticity = statistics.mean(authenticity_scores)
            authenticity_variance = statistics.variance(authenticity_scores) if len(authenticity_scores) > 1 else 0
            
            if authenticity_variance > 0.1 or avg_authenticity < 0.4:
                patterns.append(BehavioralPattern(
                    pattern_type="communication_inconsistency",
                    pattern_description="Inconsistent authenticity in communication",
                    frequency=authenticity_variance,
                    confidence=0.8,
                    first_observed=datetime.utcnow() - timedelta(days=30),
                    last_observed=datetime.utcnow(),
                    context_tags=["communication", "authenticity"],
                    risk_level=RiskLevel.MEDIUM if avg_authenticity < 0.3 else RiskLevel.LOW
                ))
        
        # Pattern: High stress communication
        stress_scores = [d.get('voice_stress_score', 0.0) for d in analysis_data 
                        if 'voice_stress_score' in d]
        if stress_scores:
            avg_stress = statistics.mean(stress_scores)
            high_stress_count = sum(1 for score in stress_scores if score > 0.7)
            
            if high_stress_count > len(stress_scores) * 0.3:  # More than 30% high stress
                patterns.append(BehavioralPattern(
                    pattern_type="chronic_stress",
                    pattern_description="Frequent high-stress communication patterns",
                    frequency=high_stress_count / len(stress_scores),
                    confidence=0.9,
                    first_observed=datetime.utcnow() - timedelta(days=30),
                    last_observed=datetime.utcnow(),
                    context_tags=["stress", "vocal", "chronic"],
                    risk_level=RiskLevel.HIGH if avg_stress > 0.8 else RiskLevel.MEDIUM
                ))
        
        # Pattern: Deception indicators
        deception_counts = [len(d.get('deception_indicators', [])) for d in analysis_data 
                          if 'deception_indicators' in d]
        if deception_counts:
            avg_deception = statistics.mean(deception_counts)
            if avg_deception > 2:  # More than 2 deception indicators on average
                patterns.append(BehavioralPattern(
                    pattern_type="deception_risk",
                    pattern_description="Frequent deception indicators in communication",
                    frequency=avg_deception / 10.0,  # Normalize
                    confidence=0.7,
                    first_observed=datetime.utcnow() - timedelta(days=30),
                    last_observed=datetime.utcnow(),
                    context_tags=["deception", "risk", "communication"],
                    risk_level=RiskLevel.HIGH
                ))
        
        return patterns
    
    def _perform_risk_assessment(self, personality: PersonalityProfile,
                               communication: CommunicationProfile,
                               stress: StressProfile,
                               behavioral_patterns: List[BehavioralPattern],
                               analysis_data: List[Dict[str, Any]]) -> RiskAssessment:
        """Perform comprehensive risk assessment."""
        
        risk_factors = []
        protective_factors = []
        risk_score = 0.0
        
        # Personality-based risk factors
        if personality.neuroticism > 0.7:
            risk_factors.append({
                "factor": "high_neuroticism",
                "description": "High emotional instability",
                "weight": 0.3,
                "score": personality.neuroticism
            })
            risk_score += personality.neuroticism * 0.3
        
        if personality.conscientiousness < 0.3:
            risk_factors.append({
                "factor": "low_conscientiousness",
                "description": "Low reliability and organization",
                "weight": 0.2,
                "score": 1.0 - personality.conscientiousness
            })
            risk_score += (1.0 - personality.conscientiousness) * 0.2
        
        # Stress-based risk factors
        if stress.current_stress_level > 0.7:
            risk_factors.append({
                "factor": "high_stress",
                "description": "Elevated stress levels",
                "weight": 0.4,
                "score": stress.current_stress_level
            })
            risk_score += stress.current_stress_level * 0.4
        
        # Communication-based risk factors
        if communication.authenticity_score_avg < 0.4:
            risk_factors.append({
                "factor": "low_authenticity",
                "description": "Low communication authenticity",
                "weight": 0.3,
                "score": 1.0 - communication.authenticity_score_avg
            })
            risk_score += (1.0 - communication.authenticity_score_avg) * 0.3
        
        # Behavioral pattern risk factors
        for pattern in behavioral_patterns:
            if pattern.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                risk_factors.append({
                    "factor": pattern.pattern_type,
                    "description": pattern.pattern_description,
                    "weight": 0.2,
                    "score": pattern.frequency
                })
                risk_score += pattern.frequency * 0.2
        
        # Protective factors
        if personality.agreeableness > 0.7:
            protective_factors.append({
                "factor": "high_agreeableness",
                "description": "Strong interpersonal skills",
                "weight": 0.2,
                "score": personality.agreeableness
            })
        
        if stress.resilience_score > 0.7:
            protective_factors.append({
                "factor": "high_resilience",
                "description": "Strong stress resilience",
                "weight": 0.3,
                "score": stress.resilience_score
            })
        
        if communication.congruence_score_avg > 0.7:
            protective_factors.append({
                "factor": "high_congruence",
                "description": "Consistent communication patterns",
                "weight": 0.2,
                "score": communication.congruence_score_avg
            })
        
        # Normalize risk score
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine risk level
        if risk_score > 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score > 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score > 0.4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Generate recommendations
        recommendations = self._generate_risk_recommendations(risk_factors, protective_factors, risk_level)
        
        # Calculate confidence based on data quality
        confidence = min(personality.confidence_score + 0.2, 1.0)
        
        return RiskAssessment(
            overall_risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            protective_factors=protective_factors,
            recommendations=recommendations,
            confidence=confidence,
            assessment_date=datetime.utcnow()
        )
    
    def _generate_predictive_insights(self, personality: PersonalityProfile,
                                    communication: CommunicationProfile,
                                    stress: StressProfile,
                                    behavioral_patterns: List[BehavioralPattern],
                                    analysis_data: List[Dict[str, Any]]) -> PredictiveInsights:
        """Generate predictive insights and analytics."""
        
        # Performance prediction based on conscientiousness and stress
        performance_prediction = (
            personality.conscientiousness * 0.4 +
            (1.0 - stress.current_stress_level) * 0.3 +
            communication.congruence_score_avg * 0.3
        )
        
        # Stress prediction based on current trends and patterns
        stress_prediction = min(
            stress.current_stress_level + 0.1 if stress.stress_trend == "increasing" else
            stress.current_stress_level - 0.1 if stress.stress_trend == "decreasing" else
            stress.current_stress_level,
            1.0
        )
        
        # Communication effectiveness prediction
        communication_effectiveness = (
            communication.authenticity_score_avg * 0.4 +
            communication.congruence_score_avg * 0.3 +
            personality.agreeableness * 0.3
        )
        
        # Leadership potential assessment
        leadership_potential = (
            personality.extraversion * 0.3 +
            personality.conscientiousness * 0.3 +
            communication.style_confidence * 0.2 +
            (1.0 - stress.current_stress_level) * 0.2
        )
        
        # Team compatibility score
        team_compatibility = (
            personality.agreeableness * 0.4 +
            communication.authenticity_score_avg * 0.3 +
            (1.0 - personality.neuroticism) * 0.3
        )
        
        # Identify growth areas
        growth_areas = []
        if personality.conscientiousness < 0.5:
            growth_areas.append("Organization and reliability")
        if communication.authenticity_score_avg < 0.5:
            growth_areas.append("Communication authenticity")
        if stress.current_stress_level > 0.6:
            growth_areas.append("Stress management")
        if personality.agreeableness < 0.4:
            growth_areas.append("Interpersonal skills")
        
        # Identify strengths
        strengths = []
        if personality.conscientiousness > 0.7:
            strengths.append("High reliability and organization")
        if communication.authenticity_score_avg > 0.7:
            strengths.append("Authentic communication style")
        if stress.resilience_score > 0.7:
            strengths.append("Strong stress resilience")
        if personality.agreeableness > 0.7:
            strengths.append("Excellent interpersonal skills")
        if personality.openness > 0.7:
            strengths.append("High creativity and openness to new ideas")
        
        # Calculate prediction confidence
        confidence = min(
            (personality.confidence_score + 
             (communication.analysis_count / 10.0) + 
             (len(analysis_data) / 20.0)) / 3.0,
            1.0
        )
        
        return PredictiveInsights(
            performance_prediction=max(0.0, min(1.0, performance_prediction)),
            stress_prediction=max(0.0, min(1.0, stress_prediction)),
            communication_effectiveness_prediction=max(0.0, min(1.0, communication_effectiveness)),
            leadership_potential=max(0.0, min(1.0, leadership_potential)),
            team_compatibility_score=max(0.0, min(1.0, team_compatibility)),
            growth_areas=growth_areas,
            strengths=strengths,
            confidence=confidence,
            prediction_horizon_days=30
        )
    
    def _calculate_profile_completeness(self, text_analyses: List[Dict],
                                      audio_analyses: List[Dict],
                                      video_analyses: List[Dict],
                                      multimodal_analyses: List[Dict]) -> float:
        """Calculate profile completeness score."""
        
        completeness_factors = {
            'text_analysis': min(len(text_analyses) / 5.0, 1.0),  # Max score with 5+ analyses
            'audio_analysis': min(len(audio_analyses) / 3.0, 1.0),  # Max score with 3+ analyses
            'video_analysis': min(len(video_analyses) / 2.0, 1.0),  # Max score with 2+ analyses
            'multimodal_analysis': min(len(multimodal_analyses) / 2.0, 1.0)  # Max score with 2+ analyses
        }
        
        # Weight the factors
        weights = {
            'text_analysis': 0.3,
            'audio_analysis': 0.3,
            'video_analysis': 0.2,
            'multimodal_analysis': 0.2
        }
        
        completeness = sum(
            completeness_factors[factor] * weights[factor]
            for factor in completeness_factors
        )
        
        return max(0.0, min(1.0, completeness))
    
    def _calculate_data_quality_score(self, analysis_data: List[Dict[str, Any]]) -> float:
        """Calculate data quality score based on analysis confidence and consistency."""
        
        if not analysis_data:
            return 0.0
        
        confidence_scores = []
        for analysis in analysis_data:
            # Extract confidence scores from various sources
            if 'wordsmimir_confidence' in analysis:
                confidence_scores.append(analysis['wordsmimir_confidence'])
            elif 'confidence' in analysis:
                confidence_scores.append(analysis['confidence'])
            elif 'overall_confidence' in analysis:
                confidence_scores.append(analysis['overall_confidence'])
        
        if not confidence_scores:
            return 0.5  # Default moderate quality
        
        # Calculate average confidence
        avg_confidence = statistics.mean(confidence_scores)
        
        # Factor in data volume (more data points = higher quality)
        volume_factor = min(len(analysis_data) / 10.0, 1.0)
        
        # Factor in data recency (more recent data = higher quality)
        recency_factor = 1.0  # Simplified - would need timestamp analysis
        
        quality_score = (avg_confidence * 0.6 + volume_factor * 0.3 + recency_factor * 0.1)
        
        return max(0.0, min(1.0, quality_score))
    
    def _generate_risk_recommendations(self, risk_factors: List[Dict],
                                     protective_factors: List[Dict],
                                     risk_level: RiskLevel) -> List[str]:
        """Generate risk mitigation recommendations."""
        
        recommendations = []
        
        # General recommendations based on risk level
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("Immediate intervention recommended")
            recommendations.append("Consider professional psychological support")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Enhanced monitoring and support recommended")
            recommendations.append("Implement stress reduction strategies")
        
        # Specific recommendations based on risk factors
        for factor in risk_factors:
            if factor['factor'] == 'high_stress':
                recommendations.append("Implement stress management techniques")
                recommendations.append("Consider workload adjustment")
            elif factor['factor'] == 'low_authenticity':
                recommendations.append("Focus on authentic communication training")
                recommendations.append("Provide feedback on communication patterns")
            elif factor['factor'] == 'high_neuroticism':
                recommendations.append("Emotional regulation training recommended")
                recommendations.append("Consider mindfulness or meditation practices")
        
        # Leverage protective factors
        for factor in protective_factors:
            if factor['factor'] == 'high_resilience':
                recommendations.append("Leverage existing resilience in challenging situations")
            elif factor['factor'] == 'high_agreeableness':
                recommendations.append("Utilize strong interpersonal skills in team settings")
        
        return list(set(recommendations))  # Remove duplicates

# Factory function for creating profiling engine
def create_profiling_engine() -> PsychologicalProfilingEngine:
    """
    Factory function to create a configured PsychologicalProfilingEngine instance.
    
    Returns:
        Configured PsychologicalProfilingEngine instance
    """
    return PsychologicalProfilingEngine()

