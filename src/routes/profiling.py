from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..models.psychological import (
    PsychologicalProfile, CommunicationAnalysis, BehavioralPattern,
    PsychologicalAlert, GroupDynamicsAnalysis, db
)
from ..services.profiling_engine import create_profiling_engine, ComprehensiveProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
profiling_bp = Blueprint('profiling', __name__, url_prefix='/api/profiling')

# Initialize profiling engine
profiling_engine = create_profiling_engine()

@profiling_bp.route('/profile/comprehensive/<individual_id>', methods=['GET'])
def get_comprehensive_profile(individual_id: str):
    """
    Generate comprehensive psychological profile for an individual.
    
    Query parameters:
    - days_back: Number of days to look back for analysis data (default: 30)
    - include_predictions: Whether to include predictive insights (default: true)
    - min_confidence: Minimum confidence threshold for included analyses (default: 0.3)
    """
    try:
        # Get query parameters
        days_back = int(request.args.get('days_back', 30))
        include_predictions = request.args.get('include_predictions', 'true').lower() == 'true'
        min_confidence = float(request.args.get('min_confidence', 0.3))
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({
                "error": "days_back must be between 1 and 365",
                "status": "error"
            }), 400
        
        if min_confidence < 0.0 or min_confidence > 1.0:
            return jsonify({
                "error": "min_confidence must be between 0.0 and 1.0",
                "status": "error"
            }), 400
        
        # Get analysis data from database
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        analyses = db.session.query(CommunicationAnalysis).filter(
            CommunicationAnalysis.individual_id == individual_id,
            CommunicationAnalysis.timestamp >= cutoff_date,
            CommunicationAnalysis.wordsmimir_confidence >= min_confidence
        ).all()
        
        if not analyses:
            return jsonify({
                "error": "No analysis data found for the specified criteria",
                "status": "error",
                "individual_id": individual_id,
                "criteria": {
                    "days_back": days_back,
                    "min_confidence": min_confidence
                }
            }), 404
        
        # Convert database records to analysis data format
        analysis_data = []
        for analysis in analyses:
            data = {
                "analysis_type": analysis.analysis_type.value if analysis.analysis_type else "unknown",
                "timestamp": analysis.timestamp.isoformat(),
                "confidence": analysis.wordsmimir_confidence or 0.5,
                "wordsmimir_confidence": analysis.wordsmimir_confidence,
                "overall_confidence": analysis.overall_confidence
            }
            
            # Add type-specific fields
            if analysis.analysis_type and analysis.analysis_type.value == 'text':
                data.update({
                    "linguistic_complexity": analysis.linguistic_complexity,
                    "emotional_valence": analysis.emotional_valence,
                    "cognitive_load_score": analysis.cognitive_load_score,
                    "deception_indicators": analysis.deception_indicators or [],
                    "stress_markers": analysis.stress_markers or []
                })
            elif analysis.analysis_type and analysis.analysis_type.value == 'audio':
                data.update({
                    "speech_rate": analysis.speech_rate,
                    "pitch_mean": analysis.pitch_mean,
                    "pitch_variance": analysis.pitch_variance,
                    "volume_variance": analysis.volume_variance,
                    "pause_frequency": analysis.pause_frequency,
                    "filler_word_count": analysis.filler_word_count,
                    "voice_stress_score": analysis.voice_stress_score
                })
            elif analysis.analysis_type and analysis.analysis_type.value == 'video':
                data.update({
                    "facial_expressions": analysis.facial_expressions,
                    "micro_expressions": analysis.micro_expressions,
                    "gaze_patterns": analysis.gaze_patterns,
                    "attention_score": analysis.attention_score,
                    "visual_stress_indicators": analysis.visual_stress_indicators or []
                })
            elif analysis.analysis_type and analysis.analysis_type.value == 'multimodal':
                data.update({
                    "authenticity_score": analysis.authenticity_score,
                    "congruence_score": analysis.congruence_score,
                    "linguistic_complexity": analysis.linguistic_complexity,
                    "emotional_valence": analysis.emotional_valence,
                    "speech_rate": analysis.speech_rate,
                    "voice_stress_score": analysis.voice_stress_score,
                    "facial_expressions": analysis.facial_expressions,
                    "attention_score": analysis.attention_score
                })
            
            # Add raw response if available
            if analysis.wordsmimir_raw_response:
                data["wordsmimir_raw_response"] = analysis.wordsmimir_raw_response
            
            analysis_data.append(data)
        
        # Generate comprehensive profile
        comprehensive_profile = profiling_engine.create_comprehensive_profile(
            individual_id=individual_id,
            analysis_data=analysis_data
        )
        
        # Convert to JSON-serializable format
        profile_dict = {
            "individual_id": comprehensive_profile.individual_id,
            "personality": {
                "openness": comprehensive_profile.personality.openness,
                "conscientiousness": comprehensive_profile.personality.conscientiousness,
                "extraversion": comprehensive_profile.personality.extraversion,
                "agreeableness": comprehensive_profile.personality.agreeableness,
                "neuroticism": comprehensive_profile.personality.neuroticism,
                "confidence_score": comprehensive_profile.personality.confidence_score,
                "data_points_count": comprehensive_profile.personality.data_points_count,
                "last_updated": comprehensive_profile.personality.last_updated.isoformat()
            },
            "communication": {
                "primary_style": comprehensive_profile.communication.primary_style.value,
                "style_confidence": comprehensive_profile.communication.style_confidence,
                "speech_rate_avg": comprehensive_profile.communication.speech_rate_avg,
                "pitch_variance_avg": comprehensive_profile.communication.pitch_variance_avg,
                "linguistic_complexity_avg": comprehensive_profile.communication.linguistic_complexity_avg,
                "emotional_valence_avg": comprehensive_profile.communication.emotional_valence_avg,
                "authenticity_score_avg": comprehensive_profile.communication.authenticity_score_avg,
                "congruence_score_avg": comprehensive_profile.communication.congruence_score_avg,
                "analysis_count": comprehensive_profile.communication.analysis_count,
                "last_updated": comprehensive_profile.communication.last_updated.isoformat()
            },
            "stress": {
                "current_stress_level": comprehensive_profile.stress.current_stress_level,
                "stress_trend": comprehensive_profile.stress.stress_trend,
                "primary_stress_indicators": [indicator.value for indicator in comprehensive_profile.stress.primary_stress_indicators],
                "stress_triggers": comprehensive_profile.stress.stress_triggers,
                "stress_patterns": comprehensive_profile.stress.stress_patterns,
                "resilience_score": comprehensive_profile.stress.resilience_score,
                "last_updated": comprehensive_profile.stress.last_updated.isoformat()
            },
            "behavioral_patterns": [
                {
                    "pattern_type": pattern.pattern_type,
                    "pattern_description": pattern.pattern_description,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "first_observed": pattern.first_observed.isoformat(),
                    "last_observed": pattern.last_observed.isoformat(),
                    "context_tags": pattern.context_tags,
                    "risk_level": pattern.risk_level.value
                }
                for pattern in comprehensive_profile.behavioral_patterns
            ],
            "risk_assessment": {
                "overall_risk_score": comprehensive_profile.risk_assessment.overall_risk_score,
                "risk_level": comprehensive_profile.risk_assessment.risk_level.value,
                "risk_factors": comprehensive_profile.risk_assessment.risk_factors,
                "protective_factors": comprehensive_profile.risk_assessment.protective_factors,
                "recommendations": comprehensive_profile.risk_assessment.recommendations,
                "confidence": comprehensive_profile.risk_assessment.confidence,
                "assessment_date": comprehensive_profile.risk_assessment.assessment_date.isoformat()
            },
            "profile_completeness": comprehensive_profile.profile_completeness,
            "data_quality_score": comprehensive_profile.data_quality_score,
            "last_updated": comprehensive_profile.last_updated.isoformat(),
            "analysis_period": {
                "days_back": days_back,
                "analyses_included": len(analysis_data),
                "date_range": {
                    "from": cutoff_date.isoformat(),
                    "to": datetime.utcnow().isoformat()
                }
            }
        }
        
        # Add predictive insights if requested
        if include_predictions:
            profile_dict["predictive_insights"] = {
                "performance_prediction": comprehensive_profile.predictive_insights.performance_prediction,
                "stress_prediction": comprehensive_profile.predictive_insights.stress_prediction,
                "communication_effectiveness_prediction": comprehensive_profile.predictive_insights.communication_effectiveness_prediction,
                "leadership_potential": comprehensive_profile.predictive_insights.leadership_potential,
                "team_compatibility_score": comprehensive_profile.predictive_insights.team_compatibility_score,
                "growth_areas": comprehensive_profile.predictive_insights.growth_areas,
                "strengths": comprehensive_profile.predictive_insights.strengths,
                "confidence": comprehensive_profile.predictive_insights.confidence,
                "prediction_horizon_days": comprehensive_profile.predictive_insights.prediction_horizon_days
            }
        
        return jsonify({
            "status": "success",
            "profile": profile_dict,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "engine_version": "1.0.0",
                "data_sources": ["wordsmimir", "multimedia_analysis"],
                "analysis_types_included": list(set(d["analysis_type"] for d in analysis_data))
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating comprehensive profile: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@profiling_bp.route('/profile/risk-assessment/<individual_id>', methods=['GET'])
def get_risk_assessment(individual_id: str):
    """
    Get focused risk assessment for an individual.
    
    Query parameters:
    - days_back: Number of days to look back for analysis data (default: 30)
    - risk_threshold: Minimum risk score to include in response (default: 0.0)
    """
    try:
        days_back = int(request.args.get('days_back', 30))
        risk_threshold = float(request.args.get('risk_threshold', 0.0))
        
        # Get analysis data
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        analyses = db.session.query(CommunicationAnalysis).filter(
            CommunicationAnalysis.individual_id == individual_id,
            CommunicationAnalysis.timestamp >= cutoff_date
        ).all()
        
        if not analyses:
            return jsonify({
                "error": "No analysis data found",
                "status": "error",
                "individual_id": individual_id
            }), 404
        
        # Convert to analysis data format (simplified for risk assessment)
        analysis_data = []
        for analysis in analyses:
            data = {
                "analysis_type": analysis.analysis_type.value if analysis.analysis_type else "unknown",
                "confidence": analysis.wordsmimir_confidence or 0.5,
                "voice_stress_score": analysis.voice_stress_score,
                "deception_indicators": analysis.deception_indicators or [],
                "stress_markers": analysis.stress_markers or [],
                "authenticity_score": analysis.authenticity_score,
                "congruence_score": analysis.congruence_score
            }
            analysis_data.append(data)
        
        # Generate comprehensive profile (focused on risk assessment)
        comprehensive_profile = profiling_engine.create_comprehensive_profile(
            individual_id=individual_id,
            analysis_data=analysis_data
        )
        
        risk_assessment = comprehensive_profile.risk_assessment
        
        # Filter risk factors by threshold
        filtered_risk_factors = [
            factor for factor in risk_assessment.risk_factors
            if factor.get('score', 0.0) >= risk_threshold
        ]
        
        # Get recent alerts
        recent_alerts = db.session.query(PsychologicalAlert).filter(
            PsychologicalAlert.individual_id == individual_id,
            PsychologicalAlert.created_at >= cutoff_date
        ).order_by(PsychologicalAlert.created_at.desc()).limit(10).all()
        
        alert_summary = [
            {
                "alert_type": alert.alert_type,
                "severity_level": alert.severity_level,
                "title": alert.title,
                "description": alert.description,
                "confidence_score": alert.confidence_score,
                "urgency_score": alert.urgency_score,
                "risk_level": alert.risk_level,
                "created_at": alert.created_at.isoformat()
            }
            for alert in recent_alerts
        ]
        
        return jsonify({
            "status": "success",
            "individual_id": individual_id,
            "risk_assessment": {
                "overall_risk_score": risk_assessment.overall_risk_score,
                "risk_level": risk_assessment.risk_level.value,
                "risk_factors": filtered_risk_factors,
                "protective_factors": risk_assessment.protective_factors,
                "recommendations": risk_assessment.recommendations,
                "confidence": risk_assessment.confidence,
                "assessment_date": risk_assessment.assessment_date.isoformat()
            },
            "recent_alerts": alert_summary,
            "behavioral_patterns": [
                {
                    "pattern_type": pattern.pattern_type,
                    "pattern_description": pattern.pattern_description,
                    "risk_level": pattern.risk_level.value,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence
                }
                for pattern in comprehensive_profile.behavioral_patterns
                if pattern.risk_level.value in ['medium', 'high', 'critical']
            ],
            "metadata": {
                "analysis_period_days": days_back,
                "analyses_count": len(analysis_data),
                "alerts_count": len(recent_alerts),
                "generated_at": datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating risk assessment: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@profiling_bp.route('/profile/predictions/<individual_id>', methods=['GET'])
def get_predictive_insights(individual_id: str):
    """
    Get predictive insights for an individual.
    
    Query parameters:
    - days_back: Number of days to look back for analysis data (default: 30)
    - prediction_horizon: Prediction horizon in days (default: 30)
    """
    try:
        days_back = int(request.args.get('days_back', 30))
        prediction_horizon = int(request.args.get('prediction_horizon', 30))
        
        # Get analysis data
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        analyses = db.session.query(CommunicationAnalysis).filter(
            CommunicationAnalysis.individual_id == individual_id,
            CommunicationAnalysis.timestamp >= cutoff_date
        ).all()
        
        if not analyses:
            return jsonify({
                "error": "No analysis data found",
                "status": "error",
                "individual_id": individual_id
            }), 404
        
        # Convert to analysis data format
        analysis_data = []
        for analysis in analyses:
            data = {
                "analysis_type": analysis.analysis_type.value if analysis.analysis_type else "unknown",
                "confidence": analysis.wordsmimir_confidence or 0.5,
                "linguistic_complexity": analysis.linguistic_complexity,
                "emotional_valence": analysis.emotional_valence,
                "speech_rate": analysis.speech_rate,
                "voice_stress_score": analysis.voice_stress_score,
                "authenticity_score": analysis.authenticity_score,
                "congruence_score": analysis.congruence_score,
                "attention_score": analysis.attention_score
            }
            analysis_data.append(data)
        
        # Generate comprehensive profile
        comprehensive_profile = profiling_engine.create_comprehensive_profile(
            individual_id=individual_id,
            analysis_data=analysis_data
        )
        
        predictions = comprehensive_profile.predictive_insights
        
        # Calculate trend analysis
        recent_analyses = sorted(analysis_data, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        
        # Performance trend
        performance_scores = []
        stress_scores = []
        for analysis in recent_analyses:
            # Calculate performance proxy
            perf_score = (
                (analysis.get('authenticity_score', 0.5) * 0.4) +
                (analysis.get('congruence_score', 0.5) * 0.3) +
                ((1.0 - analysis.get('voice_stress_score', 0.5)) * 0.3)
            )
            performance_scores.append(perf_score)
            stress_scores.append(analysis.get('voice_stress_score', 0.5))
        
        # Calculate trends
        performance_trend = "stable"
        stress_trend = "stable"
        
        if len(performance_scores) >= 3:
            recent_perf = sum(performance_scores[:3]) / 3
            older_perf = sum(performance_scores[-3:]) / 3
            if recent_perf > older_perf + 0.1:
                performance_trend = "improving"
            elif recent_perf < older_perf - 0.1:
                performance_trend = "declining"
        
        if len(stress_scores) >= 3:
            recent_stress = sum(stress_scores[:3]) / 3
            older_stress = sum(stress_scores[-3:]) / 3
            if recent_stress > older_stress + 0.1:
                stress_trend = "increasing"
            elif recent_stress < older_stress - 0.1:
                stress_trend = "decreasing"
        
        return jsonify({
            "status": "success",
            "individual_id": individual_id,
            "predictive_insights": {
                "performance_prediction": predictions.performance_prediction,
                "stress_prediction": predictions.stress_prediction,
                "communication_effectiveness_prediction": predictions.communication_effectiveness_prediction,
                "leadership_potential": predictions.leadership_potential,
                "team_compatibility_score": predictions.team_compatibility_score,
                "growth_areas": predictions.growth_areas,
                "strengths": predictions.strengths,
                "confidence": predictions.confidence,
                "prediction_horizon_days": prediction_horizon
            },
            "trend_analysis": {
                "performance_trend": performance_trend,
                "stress_trend": stress_trend,
                "data_points": len(recent_analyses)
            },
            "recommendations": {
                "immediate_actions": [
                    action for action in comprehensive_profile.risk_assessment.recommendations
                    if "immediate" in action.lower()
                ],
                "development_opportunities": predictions.growth_areas,
                "leverage_strengths": predictions.strengths
            },
            "metadata": {
                "analysis_period_days": days_back,
                "prediction_horizon_days": prediction_horizon,
                "analyses_count": len(analysis_data),
                "generated_at": datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating predictive insights: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@profiling_bp.route('/profile/summary/<individual_id>', methods=['GET'])
def get_profile_summary(individual_id: str):
    """
    Get a concise profile summary for executive dashboards.
    
    Query parameters:
    - days_back: Number of days to look back for analysis data (default: 7)
    """
    try:
        days_back = int(request.args.get('days_back', 7))
        
        # Get recent analysis data
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        analyses = db.session.query(CommunicationAnalysis).filter(
            CommunicationAnalysis.individual_id == individual_id,
            CommunicationAnalysis.timestamp >= cutoff_date
        ).all()
        
        if not analyses:
            return jsonify({
                "status": "success",
                "individual_id": individual_id,
                "summary": {
                    "status": "insufficient_data",
                    "message": "No recent analysis data available"
                }
            }), 200
        
        # Calculate summary metrics
        stress_scores = [a.voice_stress_score for a in analyses if a.voice_stress_score is not None]
        authenticity_scores = [a.authenticity_score for a in analyses if a.authenticity_score is not None]
        
        avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0.0
        avg_authenticity = sum(authenticity_scores) / len(authenticity_scores) if authenticity_scores else 0.5
        
        # Get recent alerts
        recent_alerts = db.session.query(PsychologicalAlert).filter(
            PsychologicalAlert.individual_id == individual_id,
            PsychologicalAlert.created_at >= cutoff_date
        ).count()
        
        high_risk_alerts = db.session.query(PsychologicalAlert).filter(
            PsychologicalAlert.individual_id == individual_id,
            PsychologicalAlert.created_at >= cutoff_date,
            PsychologicalAlert.severity_level.in_(['high', 'critical'])
        ).count()
        
        # Determine overall status
        if high_risk_alerts > 0:
            status = "attention_required"
            status_color = "red"
        elif avg_stress > 0.7:
            status = "elevated_stress"
            status_color = "orange"
        elif avg_authenticity < 0.4:
            status = "communication_concerns"
            status_color = "yellow"
        else:
            status = "normal"
            status_color = "green"
        
        return jsonify({
            "status": "success",
            "individual_id": individual_id,
            "summary": {
                "overall_status": status,
                "status_color": status_color,
                "key_metrics": {
                    "stress_level": round(avg_stress, 2),
                    "authenticity_score": round(avg_authenticity, 2),
                    "recent_analyses": len(analyses),
                    "alerts_count": recent_alerts,
                    "high_risk_alerts": high_risk_alerts
                },
                "period": {
                    "days": days_back,
                    "from": cutoff_date.isoformat(),
                    "to": datetime.utcnow().isoformat()
                }
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "data_quality": "high" if len(analyses) >= 3 else "moderate" if len(analyses) >= 1 else "low"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating profile summary: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@profiling_bp.route('/health', methods=['GET'])
def profiling_health():
    """Health check for psychological profiling service."""
    try:
        return jsonify({
            "status": "healthy",
            "profiling_engine": "initialized",
            "capabilities": [
                "comprehensive_profiling",
                "risk_assessment",
                "predictive_insights",
                "behavioral_pattern_recognition",
                "personality_analysis"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

