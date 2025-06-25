from flask import Blueprint, request, jsonify
import json
from datetime import datetime
from src.models.elite_command import db, Company
from src.services.intelligence import (
    IntelligenceEngine, generate_executive_brief, 
    generate_portfolio_dashboard, detect_company_anomalies
)

intelligence_bp = Blueprint('intelligence', __name__)

@intelligence_bp.route('/brief/<company_id>', methods=['GET'])
def get_company_brief(company_id):
    """Get executive brief for a specific company"""
    try:
        # Validate company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get query parameters
        days = int(request.args.get('days', 7))
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({'error': 'Days must be between 1 and 365'}), 400
        
        # Generate brief
        brief = generate_executive_brief(company_id, days)
        
        return jsonify({
            'status': 'success',
            'company': {
                'id': company.id,
                'name': company.name,
                'business_model': company.business_model.value if company.business_model else None,
                'stage': company.stage.value if company.stage else None
            },
            'brief': brief
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid days parameter'}), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate company brief',
            'error': str(e)
        }), 500

@intelligence_bp.route('/portfolio/summary', methods=['POST'])
def get_portfolio_summary():
    """Get portfolio summary for multiple companies"""
    try:
        data = request.get_json()
        
        if not data or 'company_ids' not in data:
            return jsonify({'error': 'company_ids array is required'}), 400
        
        company_ids = data['company_ids']
        
        if not isinstance(company_ids, list) or len(company_ids) == 0:
            return jsonify({'error': 'company_ids must be a non-empty array'}), 400
        
        if len(company_ids) > 50:
            return jsonify({'error': 'Maximum 50 companies allowed per request'}), 400
        
        # Validate all companies exist
        companies = Company.query.filter(Company.id.in_(company_ids)).all()
        found_ids = {c.id for c in companies}
        missing_ids = set(company_ids) - found_ids
        
        if missing_ids:
            return jsonify({
                'error': 'Some companies not found',
                'missing_ids': list(missing_ids)
            }), 404
        
        # Generate portfolio summary
        portfolio_summary = generate_portfolio_dashboard(company_ids)
        
        return jsonify({
            'status': 'success',
            'portfolio_summary': portfolio_summary
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate portfolio summary',
            'error': str(e)
        }), 500

@intelligence_bp.route('/signals/network', methods=['GET'])
def get_network_signals():
    """Get network signals for introductions and relationships"""
    try:
        # This would integrate with external data sources for network analysis
        # For now, return a placeholder structure
        
        signals = {
            'intro_opportunities': [
                {
                    'type': 'customer_intro',
                    'description': 'Potential customer match identified',
                    'confidence': 0.8,
                    'action': 'Schedule introduction call'
                },
                {
                    'type': 'investor_intro',
                    'description': 'Investor with relevant portfolio interest',
                    'confidence': 0.7,
                    'action': 'Warm introduction available'
                }
            ],
            'relationship_insights': [
                {
                    'type': 'partnership_opportunity',
                    'description': 'Complementary business model identified',
                    'companies': ['company_a', 'company_b'],
                    'potential_value': 'high'
                }
            ]
        }
        
        return jsonify({
            'status': 'success',
            'signals': signals,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get network signals',
            'error': str(e)
        }), 500

@intelligence_bp.route('/rituals/status', methods=['GET'])
def get_rituals_status():
    """Get status of focus compliance, check-in streaks, meeting drift"""
    try:
        # Get query parameters
        company_id = request.args.get('company_id')
        days = int(request.args.get('days', 30))
        
        # This would analyze ritual compliance across companies
        # For now, return a structured response
        
        rituals_status = {
            'focus_compliance': {
                'score': 85,
                'trend': 'improving',
                'issues': ['2 companies missed weekly check-ins']
            },
            'checkin_streaks': {
                'longest_streak': 45,
                'companies_on_streak': 8,
                'companies_broken_streak': 2
            },
            'meeting_drift': {
                'average_drift_minutes': 12,
                'meetings_over_time': 15,
                'efficiency_score': 78
            }
        }
        
        if company_id:
            # Filter for specific company
            company = Company.query.get(company_id)
            if not company:
                return jsonify({'error': 'Company not found'}), 404
            
            rituals_status['company_specific'] = {
                'company_id': company_id,
                'company_name': company.name,
                'focus_score': 82,
                'last_checkin': '2024-01-15T10:30:00Z',
                'streak_days': 23
            }
        
        return jsonify({
            'status': 'success',
            'rituals_status': rituals_status,
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid days parameter'}), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get rituals status',
            'error': str(e)
        }), 500

@intelligence_bp.route('/anomalies/<company_id>', methods=['GET'])
def get_company_anomalies(company_id):
    """Detect anomalies for a specific company"""
    try:
        # Validate company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get query parameters
        days = int(request.args.get('days', 30))
        
        # Validate days parameter
        if days < 7 or days > 365:
            return jsonify({'error': 'Days must be between 7 and 365'}), 400
        
        # Detect anomalies
        anomalies = detect_company_anomalies(company_id, days)
        
        return jsonify({
            'status': 'success',
            'company': {
                'id': company.id,
                'name': company.name
            },
            'anomalies': anomalies,
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid days parameter'}), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to detect anomalies',
            'error': str(e)
        }), 500

@intelligence_bp.route('/trends/<company_id>', methods=['GET'])
def get_company_trends(company_id):
    """Get trend analysis for a specific company"""
    try:
        # Validate company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get query parameters
        days = int(request.args.get('days', 30))
        
        # Validate days parameter
        if days < 7 or days > 365:
            return jsonify({'error': 'Days must be between 7 and 365'}), 400
        
        # Generate trends using intelligence engine
        engine = IntelligenceEngine()
        trends = engine.trend_analyzer.analyze_company_trends(company_id, days)
        
        return jsonify({
            'status': 'success',
            'company': {
                'id': company.id,
                'name': company.name
            },
            'trends': trends,
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid days parameter'}), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to analyze trends',
            'error': str(e)
        }), 500

@intelligence_bp.route('/alerts/<company_id>', methods=['GET'])
def get_company_alerts(company_id):
    """Get alerts for a specific company"""
    try:
        # Validate company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get query parameters
        days = int(request.args.get('days', 7))
        severity = request.args.get('severity')  # Optional filter
        
        # Validate parameters
        if days < 1 or days > 90:
            return jsonify({'error': 'Days must be between 1 and 90'}), 400
        
        if severity and severity not in ['critical', 'high', 'medium', 'low']:
            return jsonify({'error': 'Invalid severity level'}), 400
        
        # Generate alerts using intelligence engine
        engine = IntelligenceEngine()
        alerts = engine.alert_generator.generate_company_alerts(company_id, days)
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.get('severity') == severity]
        
        # Sort alerts by priority
        sorted_alerts = engine.data_sorter.prioritize_alerts(alerts)
        
        return jsonify({
            'status': 'success',
            'company': {
                'id': company.id,
                'name': company.name
            },
            'alerts': sorted_alerts,
            'alert_count': len(sorted_alerts),
            'period_days': days,
            'severity_filter': severity,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get alerts',
            'error': str(e)
        }), 500

@intelligence_bp.route('/insights/<company_id>', methods=['GET'])
def get_company_insights(company_id):
    """Get business insights for a specific company"""
    try:
        # Validate company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get query parameters
        days = int(request.args.get('days', 30))
        category = request.args.get('category')  # Optional filter
        
        # Validate parameters
        if days < 7 or days > 365:
            return jsonify({'error': 'Days must be between 7 and 365'}), 400
        
        valid_categories = ['performance', 'efficiency', 'growth', 'risk']
        if category and category not in valid_categories:
            return jsonify({'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'}), 400
        
        # Generate insights using intelligence engine
        engine = IntelligenceEngine()
        insights = engine.insight_generator.generate_company_insights(company_id, days)
        
        # Filter by category if specified
        if category:
            insights = [insight for insight in insights if insight.get('category') == category]
        
        return jsonify({
            'status': 'success',
            'company': {
                'id': company.id,
                'name': company.name
            },
            'insights': insights,
            'insight_count': len(insights),
            'period_days': days,
            'category_filter': category,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid parameter value'}), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate insights',
            'error': str(e)
        }), 500

@intelligence_bp.route('/metrics/sorted/<company_id>', methods=['GET'])
def get_sorted_metrics(company_id):
    """Get metrics sorted by importance for executive attention"""
    try:
        # Validate company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get the latest metrics for the company
        from src.models.elite_command import MetricSnapshot
        latest_snapshot = MetricSnapshot.query.filter(
            MetricSnapshot.company_id == company_id
        ).order_by(MetricSnapshot.snapshot_date.desc()).first()
        
        if not latest_snapshot:
            return jsonify({
                'status': 'success',
                'message': 'No metrics available for this company',
                'sorted_metrics': []
            }), 200
        
        # Parse metrics
        metrics = json.loads(latest_snapshot.metrics)
        
        # Sort metrics by importance
        engine = IntelligenceEngine()
        sorted_metrics = engine.data_sorter.sort_metrics_by_importance(
            metrics, 
            {'business_model': company.business_model.value if company.business_model else None}
        )
        
        return jsonify({
            'status': 'success',
            'company': {
                'id': company.id,
                'name': company.name
            },
            'sorted_metrics': sorted_metrics,
            'snapshot_date': latest_snapshot.snapshot_date.isoformat(),
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to sort metrics',
            'error': str(e)
        }), 500

@intelligence_bp.route('/test/intelligence', methods=['POST'])
def test_intelligence_engine():
    """Test the intelligence engine with sample data"""
    try:
        data = request.get_json() or {}
        
        # Create test company if not provided
        test_company_id = data.get('company_id', 'test-company-123')
        
        # Test different intelligence components
        results = {}
        
        # Test trend analysis
        try:
            engine = IntelligenceEngine()
            trends = engine.trend_analyzer.analyze_company_trends(test_company_id, 30)
            results['trend_analysis'] = trends
        except Exception as e:
            results['trend_analysis'] = {'error': str(e)}
        
        # Test alert generation
        try:
            alerts = engine.alert_generator.generate_company_alerts(test_company_id, 7)
            results['alert_generation'] = alerts
        except Exception as e:
            results['alert_generation'] = {'error': str(e)}
        
        # Test insight generation
        try:
            insights = engine.insight_generator.generate_company_insights(test_company_id, 30)
            results['insight_generation'] = insights
        except Exception as e:
            results['insight_generation'] = {'error': str(e)}
        
        # Test anomaly detection
        try:
            anomalies = detect_company_anomalies(test_company_id, 30)
            results['anomaly_detection'] = anomalies
        except Exception as e:
            results['anomaly_detection'] = {'error': str(e)}
        
        # Test metric sorting
        try:
            sample_metrics = {
                'revenue': 125000,
                'arr': 1500000,
                'churn_rate': 0.032,
                'active_users': 2500,
                'burn_rate': 75000,
                'runway_months': 18
            }
            sorted_metrics = engine.data_sorter.sort_metrics_by_importance(sample_metrics)
            results['metric_sorting'] = sorted_metrics
        except Exception as e:
            results['metric_sorting'] = {'error': str(e)}
        
        return jsonify({
            'status': 'success',
            'message': 'Intelligence engine test completed',
            'test_results': results,
            'test_company_id': test_company_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Intelligence engine test failed',
            'error': str(e)
        }), 500

