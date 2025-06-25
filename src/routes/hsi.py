from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
import statistics

from ..models.psychological import (
    PsychologicalProfile, CommunicationAnalysis, BehavioralPattern,
    PsychologicalAlert, GroupDynamicsAnalysis, db
)
from ..models.elite_command import Company, Founder, Portfolio
from ..services.profiling_engine import create_profiling_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
hsi_bp = Blueprint('hsi', __name__, url_prefix='/api/hsi')

# Initialize profiling engine
profiling_engine = create_profiling_engine()

@hsi_bp.route('/portfolio/overview', methods=['GET'])
def get_portfolio_overview():
    """
    Get comprehensive portfolio-wide psychological intelligence overview.
    
    Query parameters:
    - portfolio_id: Portfolio identifier (optional, defaults to all)
    - days_back: Number of days to look back (default: 30)
    - risk_threshold: Minimum risk score to highlight (default: 0.6)
    """
    try:
        portfolio_id = request.args.get('portfolio_id')
        days_back = int(request.args.get('days_back', 30))
        risk_threshold = float(request.args.get('risk_threshold', 0.6))
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get all individuals in portfolio
        query = db.session.query(PsychologicalProfile)
        if portfolio_id:
            # Filter by portfolio if specified
            query = query.filter(PsychologicalProfile.portfolio_id == portfolio_id)
        
        profiles = query.all()
        
        if not profiles:
            return jsonify({
                "error": "No psychological profiles found",
                "status": "error"
            }), 404
        
        # Aggregate portfolio metrics
        portfolio_metrics = {
            "total_individuals": len(profiles),
            "high_risk_individuals": 0,
            "average_stress_level": 0.0,
            "average_authenticity": 0.0,
            "communication_styles": defaultdict(int),
            "personality_distribution": {
                "openness": [],
                "conscientiousness": [],
                "extraversion": [],
                "agreeableness": [],
                "neuroticism": []
            },
            "risk_distribution": defaultdict(int),
            "recent_alerts": 0,
            "critical_alerts": 0
        }
        
        individual_summaries = []
        
        for profile in profiles:
            # Get recent analyses for this individual
            recent_analyses = db.session.query(CommunicationAnalysis).filter(
                CommunicationAnalysis.individual_id == profile.individual_id,
                CommunicationAnalysis.timestamp >= cutoff_date
            ).all()
            
            if not recent_analyses:
                continue
            
            # Calculate individual metrics
            stress_scores = [a.voice_stress_score for a in recent_analyses if a.voice_stress_score is not None]
            authenticity_scores = [a.authenticity_score for a in recent_analyses if a.authenticity_score is not None]
            
            avg_stress = statistics.mean(stress_scores) if stress_scores else 0.0
            avg_authenticity = statistics.mean(authenticity_scores) if authenticity_scores else 0.5
            
            # Get recent alerts
            recent_alerts = db.session.query(PsychologicalAlert).filter(
                PsychologicalAlert.individual_id == profile.individual_id,
                PsychologicalAlert.created_at >= cutoff_date
            ).count()
            
            critical_alerts = db.session.query(PsychologicalAlert).filter(
                PsychologicalAlert.individual_id == profile.individual_id,
                PsychologicalAlert.created_at >= cutoff_date,
                PsychologicalAlert.severity_level == 'critical'
            ).count()
            
            # Determine risk level
            risk_score = avg_stress * 0.6 + (1.0 - avg_authenticity) * 0.4
            risk_level = "high" if risk_score >= risk_threshold else "medium" if risk_score >= 0.4 else "low"
            
            if risk_score >= risk_threshold:
                portfolio_metrics["high_risk_individuals"] += 1
            
            # Update portfolio aggregates
            portfolio_metrics["average_stress_level"] += avg_stress
            portfolio_metrics["average_authenticity"] += avg_authenticity
            portfolio_metrics["risk_distribution"][risk_level] += 1
            portfolio_metrics["recent_alerts"] += recent_alerts
            portfolio_metrics["critical_alerts"] += critical_alerts
            
            # Add to personality distribution
            if profile.openness is not None:
                portfolio_metrics["personality_distribution"]["openness"].append(profile.openness)
            if profile.conscientiousness is not None:
                portfolio_metrics["personality_distribution"]["conscientiousness"].append(profile.conscientiousness)
            if profile.extraversion is not None:
                portfolio_metrics["personality_distribution"]["extraversion"].append(profile.extraversion)
            if profile.agreeableness is not None:
                portfolio_metrics["personality_distribution"]["agreeableness"].append(profile.agreeableness)
            if profile.neuroticism is not None:
                portfolio_metrics["personality_distribution"]["neuroticism"].append(profile.neuroticism)
            
            # Add communication style
            if profile.communication_style:
                portfolio_metrics["communication_styles"][profile.communication_style] += 1
            
            # Create individual summary
            individual_summaries.append({
                "individual_id": profile.individual_id,
                "name": profile.name or "Unknown",
                "role": profile.role or "Unknown",
                "company_id": profile.company_id,
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level,
                "stress_level": round(avg_stress, 2),
                "authenticity_score": round(avg_authenticity, 2),
                "recent_analyses": len(recent_analyses),
                "recent_alerts": recent_alerts,
                "critical_alerts": critical_alerts,
                "last_analysis": max(a.timestamp for a in recent_analyses).isoformat() if recent_analyses else None
            })
        
        # Calculate portfolio averages
        if len(profiles) > 0:
            portfolio_metrics["average_stress_level"] /= len(profiles)
            portfolio_metrics["average_authenticity"] /= len(profiles)
        
        # Calculate personality averages
        personality_averages = {}
        for trait, values in portfolio_metrics["personality_distribution"].items():
            if values:
                personality_averages[trait] = {
                    "average": round(statistics.mean(values), 2),
                    "std_dev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
                    "min": round(min(values), 2),
                    "max": round(max(values), 2)
                }
            else:
                personality_averages[trait] = {
                    "average": 0.5,
                    "std_dev": 0.0,
                    "min": 0.0,
                    "max": 0.0
                }
        
        # Generate strategic insights
        strategic_insights = []
        
        # High stress insight
        if portfolio_metrics["average_stress_level"] > 0.6:
            strategic_insights.append({
                "type": "stress_concern",
                "priority": "high",
                "title": "Elevated Portfolio Stress Levels",
                "description": f"Average stress level ({portfolio_metrics['average_stress_level']:.2f}) exceeds recommended threshold",
                "recommendation": "Consider implementing portfolio-wide stress reduction initiatives"
            })
        
        # High risk individuals insight
        if portfolio_metrics["high_risk_individuals"] > len(profiles) * 0.2:
            strategic_insights.append({
                "type": "risk_concentration",
                "priority": "high",
                "title": "High Risk Individual Concentration",
                "description": f"{portfolio_metrics['high_risk_individuals']} individuals ({portfolio_metrics['high_risk_individuals']/len(profiles)*100:.1f}%) are high risk",
                "recommendation": "Prioritize intervention and support for high-risk individuals"
            })
        
        # Communication authenticity insight
        if portfolio_metrics["average_authenticity"] < 0.5:
            strategic_insights.append({
                "type": "communication_concern",
                "priority": "medium",
                "title": "Communication Authenticity Below Baseline",
                "description": f"Average authenticity ({portfolio_metrics['average_authenticity']:.2f}) suggests communication challenges",
                "recommendation": "Implement communication training and feedback programs"
            })
        
        # Sort individual summaries by risk score (highest first)
        individual_summaries.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return jsonify({
            "status": "success",
            "portfolio_overview": {
                "portfolio_id": portfolio_id,
                "analysis_period": {
                    "days_back": days_back,
                    "from": cutoff_date.isoformat(),
                    "to": datetime.utcnow().isoformat()
                },
                "portfolio_metrics": {
                    "total_individuals": portfolio_metrics["total_individuals"],
                    "high_risk_individuals": portfolio_metrics["high_risk_individuals"],
                    "average_stress_level": round(portfolio_metrics["average_stress_level"], 2),
                    "average_authenticity": round(portfolio_metrics["average_authenticity"], 2),
                    "communication_styles": dict(portfolio_metrics["communication_styles"]),
                    "risk_distribution": dict(portfolio_metrics["risk_distribution"]),
                    "recent_alerts": portfolio_metrics["recent_alerts"],
                    "critical_alerts": portfolio_metrics["critical_alerts"]
                },
                "personality_distribution": personality_averages,
                "strategic_insights": strategic_insights,
                "top_risk_individuals": individual_summaries[:10],  # Top 10 highest risk
                "generated_at": datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating portfolio overview: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@hsi_bp.route('/team/dynamics', methods=['POST'])
def analyze_team_dynamics():
    """
    Analyze team dynamics and compatibility for a group of individuals.
    
    Request body:
    {
        "team_members": ["individual_id1", "individual_id2", ...],
        "analysis_type": "compatibility" | "leadership" | "communication",
        "days_back": 30
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'team_members' not in data:
            return jsonify({
                "error": "team_members is required",
                "status": "error"
            }), 400
        
        team_members = data['team_members']
        analysis_type = data.get('analysis_type', 'compatibility')
        days_back = data.get('days_back', 30)
        
        if len(team_members) < 2:
            return jsonify({
                "error": "At least 2 team members required for analysis",
                "status": "error"
            }), 400
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get profiles for all team members
        profiles = db.session.query(PsychologicalProfile).filter(
            PsychologicalProfile.individual_id.in_(team_members)
        ).all()
        
        if len(profiles) != len(team_members):
            missing_profiles = set(team_members) - {p.individual_id for p in profiles}
            return jsonify({
                "error": "Missing psychological profiles",
                "missing_individuals": list(missing_profiles),
                "status": "error"
            }), 404
        
        # Analyze team composition
        team_analysis = {
            "team_size": len(team_members),
            "personality_balance": {},
            "communication_compatibility": 0.0,
            "stress_distribution": {},
            "leadership_potential": {},
            "risk_factors": [],
            "strengths": [],
            "recommendations": []
        }
        
        # Personality balance analysis
        personality_scores = {
            "openness": [p.openness for p in profiles if p.openness is not None],
            "conscientiousness": [p.conscientiousness for p in profiles if p.conscientiousness is not None],
            "extraversion": [p.extraversion for p in profiles if p.extraversion is not None],
            "agreeableness": [p.agreeableness for p in profiles if p.agreeableness is not None],
            "neuroticism": [p.neuroticism for p in profiles if p.neuroticism is not None]
        }
        
        for trait, scores in personality_scores.items():
            if scores:
                team_analysis["personality_balance"][trait] = {
                    "average": round(statistics.mean(scores), 2),
                    "variance": round(statistics.variance(scores), 2) if len(scores) > 1 else 0.0,
                    "balance_score": 1.0 - min(statistics.variance(scores), 0.25) / 0.25 if len(scores) > 1 else 1.0
                }
        
        # Communication compatibility analysis
        communication_styles = [p.communication_style for p in profiles if p.communication_style]
        style_diversity = len(set(communication_styles)) / len(communication_styles) if communication_styles else 0.0
        
        # Get recent communication analyses
        member_communications = {}
        for member_id in team_members:
            recent_analyses = db.session.query(CommunicationAnalysis).filter(
                CommunicationAnalysis.individual_id == member_id,
                CommunicationAnalysis.timestamp >= cutoff_date
            ).all()
            
            if recent_analyses:
                authenticity_scores = [a.authenticity_score for a in recent_analyses if a.authenticity_score is not None]
                congruence_scores = [a.congruence_score for a in recent_analyses if a.congruence_score is not None]
                
                member_communications[member_id] = {
                    "authenticity_avg": statistics.mean(authenticity_scores) if authenticity_scores else 0.5,
                    "congruence_avg": statistics.mean(congruence_scores) if congruence_scores else 0.5,
                    "analysis_count": len(recent_analyses)
                }
        
        # Calculate communication compatibility
        if member_communications:
            avg_authenticity = statistics.mean([m["authenticity_avg"] for m in member_communications.values()])
            avg_congruence = statistics.mean([m["congruence_avg"] for m in member_communications.values()])
            team_analysis["communication_compatibility"] = round((avg_authenticity + avg_congruence + style_diversity) / 3.0, 2)
        
        # Stress distribution analysis
        stress_levels = []
        for member_id in team_members:
            recent_analyses = db.session.query(CommunicationAnalysis).filter(
                CommunicationAnalysis.individual_id == member_id,
                CommunicationAnalysis.timestamp >= cutoff_date
            ).all()
            
            stress_scores = [a.voice_stress_score for a in recent_analyses if a.voice_stress_score is not None]
            if stress_scores:
                avg_stress = statistics.mean(stress_scores)
                stress_levels.append(avg_stress)
        
        if stress_levels:
            team_analysis["stress_distribution"] = {
                "average": round(statistics.mean(stress_levels), 2),
                "variance": round(statistics.variance(stress_levels), 2) if len(stress_levels) > 1 else 0.0,
                "high_stress_members": sum(1 for s in stress_levels if s > 0.7),
                "low_stress_members": sum(1 for s in stress_levels if s < 0.3)
            }
        
        # Leadership potential analysis
        for profile in profiles:
            if all(score is not None for score in [profile.extraversion, profile.conscientiousness, profile.agreeableness]):
                leadership_score = (
                    profile.extraversion * 0.4 +
                    profile.conscientiousness * 0.3 +
                    profile.agreeableness * 0.2 +
                    (1.0 - profile.neuroticism) * 0.1 if profile.neuroticism is not None else 0.05
                )
                
                team_analysis["leadership_potential"][profile.individual_id] = {
                    "score": round(leadership_score, 2),
                    "level": "high" if leadership_score > 0.7 else "medium" if leadership_score > 0.5 else "low"
                }
        
        # Risk factors identification
        if team_analysis["stress_distribution"].get("average", 0) > 0.6:
            team_analysis["risk_factors"].append({
                "type": "high_team_stress",
                "description": "Team shows elevated stress levels",
                "severity": "medium"
            })
        
        if team_analysis["communication_compatibility"] < 0.5:
            team_analysis["risk_factors"].append({
                "type": "communication_mismatch",
                "description": "Team members may have communication compatibility issues",
                "severity": "medium"
            })
        
        high_neuroticism_count = sum(1 for p in profiles if p.neuroticism and p.neuroticism > 0.7)
        if high_neuroticism_count > len(profiles) * 0.5:
            team_analysis["risk_factors"].append({
                "type": "emotional_instability",
                "description": "High concentration of emotionally unstable team members",
                "severity": "high"
            })
        
        # Strengths identification
        if team_analysis["personality_balance"].get("conscientiousness", {}).get("average", 0) > 0.7:
            team_analysis["strengths"].append({
                "type": "high_reliability",
                "description": "Team demonstrates high conscientiousness and reliability"
            })
        
        if team_analysis["communication_compatibility"] > 0.7:
            team_analysis["strengths"].append({
                "type": "strong_communication",
                "description": "Team shows excellent communication compatibility"
            })
        
        if len([p for p in team_analysis["leadership_potential"].values() if p["level"] == "high"]) > 0:
            team_analysis["strengths"].append({
                "type": "leadership_presence",
                "description": "Team has strong leadership potential"
            })
        
        # Generate recommendations
        if analysis_type == "compatibility":
            if team_analysis["communication_compatibility"] < 0.6:
                team_analysis["recommendations"].append("Implement team communication workshops")
            if team_analysis["personality_balance"].get("agreeableness", {}).get("average", 0) < 0.5:
                team_analysis["recommendations"].append("Focus on collaborative team-building activities")
        
        elif analysis_type == "leadership":
            high_leadership_members = [
                member_id for member_id, data in team_analysis["leadership_potential"].items()
                if data["level"] == "high"
            ]
            if high_leadership_members:
                team_analysis["recommendations"].append(f"Consider {', '.join(high_leadership_members)} for leadership roles")
            else:
                team_analysis["recommendations"].append("Provide leadership development training for team members")
        
        elif analysis_type == "communication":
            if style_diversity < 0.3:
                team_analysis["recommendations"].append("Diversify communication styles within the team")
            if team_analysis["communication_compatibility"] > 0.8:
                team_analysis["recommendations"].append("Leverage strong communication synergy for complex projects")
        
        return jsonify({
            "status": "success",
            "team_dynamics": team_analysis,
            "analysis_metadata": {
                "analysis_type": analysis_type,
                "team_size": len(team_members),
                "analysis_period_days": days_back,
                "generated_at": datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing team dynamics: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@hsi_bp.route('/alerts/executive-summary', methods=['GET'])
def get_executive_alert_summary():
    """
    Get executive summary of critical psychological alerts across the portfolio.
    
    Query parameters:
    - days_back: Number of days to look back (default: 7)
    - severity_filter: Minimum severity level (default: medium)
    - portfolio_id: Portfolio identifier (optional)
    """
    try:
        days_back = int(request.args.get('days_back', 7))
        severity_filter = request.args.get('severity_filter', 'medium')
        portfolio_id = request.args.get('portfolio_id')
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Build query for alerts
        query = db.session.query(PsychologicalAlert).filter(
            PsychologicalAlert.created_at >= cutoff_date
        )
        
        if severity_filter:
            severity_levels = {
                'low': ['low', 'medium', 'high', 'critical'],
                'medium': ['medium', 'high', 'critical'],
                'high': ['high', 'critical'],
                'critical': ['critical']
            }
            query = query.filter(PsychologicalAlert.severity_level.in_(severity_levels.get(severity_filter, ['medium', 'high', 'critical'])))
        
        alerts = query.order_by(PsychologicalAlert.created_at.desc()).all()
        
        # Aggregate alert statistics
        alert_stats = {
            "total_alerts": len(alerts),
            "critical_alerts": sum(1 for a in alerts if a.severity_level == 'critical'),
            "high_alerts": sum(1 for a in alerts if a.severity_level == 'high'),
            "medium_alerts": sum(1 for a in alerts if a.severity_level == 'medium'),
            "alert_types": Counter(a.alert_type for a in alerts),
            "affected_individuals": len(set(a.individual_id for a in alerts)),
            "trend": "stable"  # Simplified trend analysis
        }
        
        # Group alerts by individual
        individual_alerts = defaultdict(list)
        for alert in alerts:
            individual_alerts[alert.individual_id].append({
                "alert_type": alert.alert_type,
                "severity_level": alert.severity_level,
                "title": alert.title,
                "description": alert.description,
                "confidence_score": alert.confidence_score,
                "urgency_score": alert.urgency_score,
                "risk_level": alert.risk_level,
                "created_at": alert.created_at.isoformat(),
                "recommendations": alert.recommendations or []
            })
        
        # Identify high-priority individuals (multiple alerts or critical alerts)
        high_priority_individuals = []
        for individual_id, individual_alert_list in individual_alerts.items():
            critical_count = sum(1 for a in individual_alert_list if a["severity_level"] == "critical")
            total_count = len(individual_alert_list)
            
            if critical_count > 0 or total_count >= 3:
                # Get individual profile for context
                profile = db.session.query(PsychologicalProfile).filter(
                    PsychologicalProfile.individual_id == individual_id
                ).first()
                
                high_priority_individuals.append({
                    "individual_id": individual_id,
                    "name": profile.name if profile else "Unknown",
                    "role": profile.role if profile else "Unknown",
                    "company_id": profile.company_id if profile else None,
                    "alert_count": total_count,
                    "critical_alerts": critical_count,
                    "latest_alert": max(a["created_at"] for a in individual_alert_list),
                    "primary_concerns": list(set(a["alert_type"] for a in individual_alert_list))[:3]
                })
        
        # Sort by priority (critical alerts first, then total count)
        high_priority_individuals.sort(key=lambda x: (x["critical_alerts"], x["alert_count"]), reverse=True)
        
        # Generate executive recommendations
        executive_recommendations = []
        
        if alert_stats["critical_alerts"] > 0:
            executive_recommendations.append({
                "priority": "immediate",
                "action": "Address Critical Alerts",
                "description": f"{alert_stats['critical_alerts']} critical psychological alerts require immediate attention",
                "affected_count": len([i for i in high_priority_individuals if i["critical_alerts"] > 0])
            })
        
        if alert_stats["affected_individuals"] > 5:
            executive_recommendations.append({
                "priority": "high",
                "action": "Portfolio-Wide Assessment",
                "description": f"Multiple individuals ({alert_stats['affected_individuals']}) showing psychological concerns",
                "affected_count": alert_stats["affected_individuals"]
            })
        
        # Most common alert types
        top_alert_types = alert_stats["alert_types"].most_common(3)
        if top_alert_types:
            most_common_type = top_alert_types[0][0]
            executive_recommendations.append({
                "priority": "medium",
                "action": f"Address {most_common_type.replace('_', ' ').title()} Pattern",
                "description": f"Most frequent alert type: {most_common_type} ({top_alert_types[0][1]} occurrences)",
                "affected_count": top_alert_types[0][1]
            })
        
        return jsonify({
            "status": "success",
            "executive_summary": {
                "period": {
                    "days_back": days_back,
                    "from": cutoff_date.isoformat(),
                    "to": datetime.utcnow().isoformat()
                },
                "alert_statistics": alert_stats,
                "high_priority_individuals": high_priority_individuals[:10],  # Top 10
                "executive_recommendations": executive_recommendations,
                "alert_type_breakdown": dict(alert_stats["alert_types"]),
                "generated_at": datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating executive alert summary: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@hsi_bp.route('/insights/strategic', methods=['GET'])
def get_strategic_insights():
    """
    Get strategic psychological insights for executive decision-making.
    
    Query parameters:
    - scope: 'portfolio' | 'company' | 'team' (default: portfolio)
    - entity_id: ID of the specific entity (company_id, team_id, etc.)
    - days_back: Number of days to analyze (default: 30)
    - insight_types: Comma-separated list of insight types to include
    """
    try:
        scope = request.args.get('scope', 'portfolio')
        entity_id = request.args.get('entity_id')
        days_back = int(request.args.get('days_back', 30))
        insight_types = request.args.get('insight_types', '').split(',') if request.args.get('insight_types') else []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Build base query based on scope
        if scope == 'company' and entity_id:
            profiles = db.session.query(PsychologicalProfile).filter(
                PsychologicalProfile.company_id == entity_id
            ).all()
        elif scope == 'portfolio' and entity_id:
            profiles = db.session.query(PsychologicalProfile).filter(
                PsychologicalProfile.portfolio_id == entity_id
            ).all()
        else:
            # Default to all profiles
            profiles = db.session.query(PsychologicalProfile).all()
        
        if not profiles:
            return jsonify({
                "error": "No profiles found for the specified scope",
                "status": "error"
            }), 404
        
        individual_ids = [p.individual_id for p in profiles]
        
        # Get recent analyses and alerts
        recent_analyses = db.session.query(CommunicationAnalysis).filter(
            CommunicationAnalysis.individual_id.in_(individual_ids),
            CommunicationAnalysis.timestamp >= cutoff_date
        ).all()
        
        recent_alerts = db.session.query(PsychologicalAlert).filter(
            PsychologicalAlert.individual_id.in_(individual_ids),
            PsychologicalAlert.created_at >= cutoff_date
        ).all()
        
        # Generate strategic insights
        strategic_insights = {
            "scope": scope,
            "entity_id": entity_id,
            "analysis_period": {
                "days_back": days_back,
                "from": cutoff_date.isoformat(),
                "to": datetime.utcnow().isoformat()
            },
            "insights": []
        }
        
        # Talent optimization insights
        if not insight_types or 'talent_optimization' in insight_types:
            high_performers = []
            development_candidates = []
            
            for profile in profiles:
                if all(score is not None for score in [profile.conscientiousness, profile.agreeableness]):
                    performance_proxy = (profile.conscientiousness * 0.6 + profile.agreeableness * 0.4)
                    
                    if performance_proxy > 0.75:
                        high_performers.append({
                            "individual_id": profile.individual_id,
                            "name": profile.name,
                            "performance_score": round(performance_proxy, 2)
                        })
                    elif performance_proxy < 0.4:
                        development_candidates.append({
                            "individual_id": profile.individual_id,
                            "name": profile.name,
                            "performance_score": round(performance_proxy, 2)
                        })
            
            strategic_insights["insights"].append({
                "type": "talent_optimization",
                "title": "Talent Performance Distribution",
                "high_performers": high_performers[:5],
                "development_candidates": development_candidates[:5],
                "recommendations": [
                    "Leverage high performers for critical projects",
                    "Provide targeted development for underperforming individuals",
                    "Consider succession planning for key roles"
                ]
            })
        
        # Communication effectiveness insights
        if not insight_types or 'communication_effectiveness' in insight_types:
            authenticity_scores = [a.authenticity_score for a in recent_analyses if a.authenticity_score is not None]
            congruence_scores = [a.congruence_score for a in recent_analyses if a.congruence_score is not None]
            
            if authenticity_scores and congruence_scores:
                avg_authenticity = statistics.mean(authenticity_scores)
                avg_congruence = statistics.mean(congruence_scores)
                
                communication_insight = {
                    "type": "communication_effectiveness",
                    "title": "Communication Quality Assessment",
                    "metrics": {
                        "average_authenticity": round(avg_authenticity, 2),
                        "average_congruence": round(avg_congruence, 2),
                        "communication_score": round((avg_authenticity + avg_congruence) / 2, 2)
                    },
                    "recommendations": []
                }
                
                if avg_authenticity < 0.5:
                    communication_insight["recommendations"].append("Implement authenticity training programs")
                if avg_congruence < 0.5:
                    communication_insight["recommendations"].append("Focus on message consistency across channels")
                if avg_authenticity > 0.8 and avg_congruence > 0.8:
                    communication_insight["recommendations"].append("Leverage strong communication capabilities for external representation")
                
                strategic_insights["insights"].append(communication_insight)
        
        # Risk management insights
        if not insight_types or 'risk_management' in insight_types:
            high_risk_alerts = [a for a in recent_alerts if a.severity_level in ['high', 'critical']]
            stress_scores = [a.voice_stress_score for a in recent_analyses if a.voice_stress_score is not None]
            
            risk_insight = {
                "type": "risk_management",
                "title": "Psychological Risk Assessment",
                "risk_indicators": {
                    "high_risk_alerts": len(high_risk_alerts),
                    "average_stress_level": round(statistics.mean(stress_scores), 2) if stress_scores else 0.0,
                    "individuals_at_risk": len(set(a.individual_id for a in high_risk_alerts))
                },
                "recommendations": []
            }
            
            if len(high_risk_alerts) > 0:
                risk_insight["recommendations"].append("Implement immediate intervention protocols")
            if risk_insight["risk_indicators"]["average_stress_level"] > 0.6:
                risk_insight["recommendations"].append("Deploy stress reduction initiatives")
            if risk_insight["risk_indicators"]["individuals_at_risk"] > len(profiles) * 0.2:
                risk_insight["recommendations"].append("Conduct comprehensive organizational health assessment")
            
            strategic_insights["insights"].append(risk_insight)
        
        # Leadership development insights
        if not insight_types or 'leadership_development' in insight_types:
            leadership_candidates = []
            
            for profile in profiles:
                if all(score is not None for score in [profile.extraversion, profile.conscientiousness, profile.agreeableness]):
                    leadership_score = (
                        profile.extraversion * 0.4 +
                        profile.conscientiousness * 0.3 +
                        profile.agreeableness * 0.3
                    )
                    
                    if leadership_score > 0.7:
                        leadership_candidates.append({
                            "individual_id": profile.individual_id,
                            "name": profile.name,
                            "leadership_score": round(leadership_score, 2),
                            "strengths": []
                        })
                        
                        # Add specific strengths
                        if profile.extraversion > 0.8:
                            leadership_candidates[-1]["strengths"].append("High social engagement")
                        if profile.conscientiousness > 0.8:
                            leadership_candidates[-1]["strengths"].append("Exceptional reliability")
                        if profile.agreeableness > 0.8:
                            leadership_candidates[-1]["strengths"].append("Strong interpersonal skills")
            
            leadership_candidates.sort(key=lambda x: x["leadership_score"], reverse=True)
            
            strategic_insights["insights"].append({
                "type": "leadership_development",
                "title": "Leadership Potential Assessment",
                "leadership_candidates": leadership_candidates[:5],
                "recommendations": [
                    "Provide leadership development opportunities for high-potential individuals",
                    "Create mentorship programs pairing leaders with candidates",
                    "Implement succession planning for key leadership roles"
                ]
            })
        
        return jsonify({
            "status": "success",
            "strategic_insights": strategic_insights,
            "metadata": {
                "profiles_analyzed": len(profiles),
                "analyses_included": len(recent_analyses),
                "alerts_included": len(recent_alerts),
                "generated_at": datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating strategic insights: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

@hsi_bp.route('/health', methods=['GET'])
def hsi_health():
    """Health check for HSI Intelligence service."""
    try:
        return jsonify({
            "status": "healthy",
            "hsi_capabilities": [
                "portfolio_overview",
                "team_dynamics_analysis",
                "executive_alert_summary",
                "strategic_insights",
                "risk_assessment",
                "talent_optimization"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

