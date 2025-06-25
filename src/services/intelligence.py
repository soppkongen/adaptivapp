"""
Intelligence Layer and Sorting Logic

This module implements the intelligence layer that analyzes normalized data,
generates insights, detects trends, creates alerts, and provides intelligent
sorting and prioritization of information for executive decision-making.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict
from src.models.elite_command import (
    db, MetricSnapshot, Company, BusinessUnit, DataSource
)

class IntelligenceEngine:
    """Main intelligence engine for data analysis and insights"""
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.alert_generator = AlertGenerator()
        self.insight_generator = InsightGenerator()
        self.data_sorter = DataSorter()
        self.anomaly_detector = AnomalyDetector()
    
    def generate_company_brief(self, company_id: str, days: int = 7) -> Dict[str, Any]:
        """Generate a comprehensive brief for a company"""
        try:
            # Get recent metric snapshots
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            snapshots = MetricSnapshot.query.filter(
                MetricSnapshot.company_id == company_id,
                MetricSnapshot.snapshot_date >= start_date
            ).order_by(MetricSnapshot.snapshot_date.desc()).all()
            
            if not snapshots:
                return {
                    'company_id': company_id,
                    'status': 'no_data',
                    'message': 'No recent data available for analysis'
                }
            
            # Analyze trends
            trends = self.trend_analyzer.analyze_company_trends(company_id, days)
            
            # Generate alerts
            alerts = self.alert_generator.generate_company_alerts(company_id, days)
            
            # Generate insights
            insights = self.insight_generator.generate_company_insights(company_id, days)
            
            # Get key metrics summary
            key_metrics = self._extract_key_metrics(snapshots)
            
            # Calculate health score
            health_score = self._calculate_company_health_score(snapshots, trends, alerts)
            
            return {
                'company_id': company_id,
                'brief_date': datetime.utcnow().isoformat(),
                'period': f'{days} days',
                'health_score': health_score,
                'key_metrics': key_metrics,
                'trends': trends,
                'alerts': alerts,
                'insights': insights,
                'data_quality': self._assess_data_quality(snapshots)
            }
            
        except Exception as e:
            print(f"Error generating company brief: {e}")
            return {
                'company_id': company_id,
                'status': 'error',
                'message': str(e)
            }
    
    def generate_portfolio_summary(self, portfolio_companies: List[str]) -> Dict[str, Any]:
        """Generate a portfolio-wide summary"""
        try:
            portfolio_data = {}
            
            for company_id in portfolio_companies:
                brief = self.generate_company_brief(company_id, days=30)
                portfolio_data[company_id] = brief
            
            # Aggregate portfolio metrics
            portfolio_metrics = self._aggregate_portfolio_metrics(portfolio_data)
            
            # Identify portfolio-wide trends
            portfolio_trends = self._analyze_portfolio_trends(portfolio_data)
            
            # Generate portfolio alerts
            portfolio_alerts = self._generate_portfolio_alerts(portfolio_data)
            
            # Rank companies by performance
            company_rankings = self._rank_companies_by_performance(portfolio_data)
            
            return {
                'portfolio_summary': {
                    'total_companies': len(portfolio_companies),
                    'summary_date': datetime.utcnow().isoformat(),
                    'aggregate_metrics': portfolio_metrics,
                    'portfolio_trends': portfolio_trends,
                    'portfolio_alerts': portfolio_alerts,
                    'company_rankings': company_rankings
                },
                'company_details': portfolio_data
            }
            
        except Exception as e:
            print(f"Error generating portfolio summary: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _extract_key_metrics(self, snapshots: List[MetricSnapshot]) -> Dict[str, Any]:
        """Extract key metrics from recent snapshots"""
        if not snapshots:
            return {}
        
        # Get the most recent snapshot
        latest = snapshots[0]
        latest_metrics = json.loads(latest.metrics)
        
        # Define key metric categories
        key_categories = {
            'financial': ['revenue', 'arr', 'mrr', 'burn_rate', 'runway_months', 'gross_margin'],
            'growth': ['revenue_growth_rate', 'user_growth_rate', 'customer_growth_rate'],
            'customer': ['total_customers', 'churn_rate', 'retention_rate', 'ltv', 'cac'],
            'operational': ['active_users', 'conversion_rate', 'sessions', 'uptime']
        }
        
        key_metrics = {}
        
        for category, metric_names in key_categories.items():
            category_metrics = {}
            for metric_name in metric_names:
                if metric_name in latest_metrics:
                    category_metrics[metric_name] = latest_metrics[metric_name]
            
            if category_metrics:
                key_metrics[category] = category_metrics
        
        return key_metrics
    
    def _calculate_company_health_score(self, snapshots: List[MetricSnapshot], 
                                      trends: Dict, alerts: List[Dict]) -> float:
        """Calculate overall company health score (0-100)"""
        try:
            score = 50.0  # Start with neutral score
            
            # Factor 1: Data availability and quality (0-20 points)
            data_score = min(len(snapshots) * 2, 20)
            score += data_score
            
            # Factor 2: Trend analysis (0-30 points)
            trend_score = 0
            if trends.get('positive_trends'):
                trend_score += len(trends['positive_trends']) * 5
            if trends.get('negative_trends'):
                trend_score -= len(trends['negative_trends']) * 3
            
            trend_score = max(min(trend_score, 30), -30)
            score += trend_score
            
            # Factor 3: Alert severity (-20 to 0 points)
            alert_score = 0
            for alert in alerts:
                severity = alert.get('severity', 'low')
                if severity == 'critical':
                    alert_score -= 10
                elif severity == 'high':
                    alert_score -= 5
                elif severity == 'medium':
                    alert_score -= 2
            
            alert_score = max(alert_score, -20)
            score += alert_score
            
            # Factor 4: Key metric performance (0-20 points)
            if snapshots:
                latest_metrics = json.loads(snapshots[0].metrics)
                metric_score = self._score_key_metrics(latest_metrics)
                score += metric_score
            
            # Clamp score between 0 and 100
            return max(min(score, 100), 0)
            
        except Exception as e:
            print(f"Error calculating health score: {e}")
            return 50.0
    
    def _score_key_metrics(self, metrics: Dict) -> float:
        """Score key metrics performance"""
        score = 0
        
        # Revenue growth
        if 'revenue_growth_rate' in metrics:
            growth = metrics['revenue_growth_rate']
            if growth > 0.2:  # 20%+ growth
                score += 5
            elif growth > 0.1:  # 10%+ growth
                score += 3
            elif growth > 0:  # Positive growth
                score += 1
            else:  # Negative growth
                score -= 2
        
        # Churn rate
        if 'churn_rate' in metrics:
            churn = metrics['churn_rate']
            if churn < 0.02:  # <2% churn
                score += 3
            elif churn < 0.05:  # <5% churn
                score += 1
            elif churn > 0.1:  # >10% churn
                score -= 3
        
        # Burn rate vs runway
        if 'runway_months' in metrics:
            runway = metrics['runway_months']
            if runway > 18:  # 18+ months runway
                score += 3
            elif runway > 12:  # 12+ months runway
                score += 1
            elif runway < 6:  # <6 months runway
                score -= 5
        
        return min(max(score, -10), 10)
    
    def _assess_data_quality(self, snapshots: List[MetricSnapshot]) -> Dict[str, Any]:
        """Assess the quality of available data"""
        if not snapshots:
            return {'score': 0, 'issues': ['No data available']}
        
        total_confidence = sum(s.confidence_score for s in snapshots)
        avg_confidence = total_confidence / len(snapshots)
        
        # Check data freshness
        latest_date = snapshots[0].snapshot_date
        age_hours = (datetime.utcnow() - latest_date).total_seconds() / 3600
        
        # Check data completeness
        all_metrics = set()
        for snapshot in snapshots:
            metrics = json.loads(snapshot.metrics)
            all_metrics.update(metrics.keys())
        
        issues = []
        if avg_confidence < 0.7:
            issues.append('Low confidence scores detected')
        if age_hours > 48:
            issues.append('Data is more than 48 hours old')
        if len(all_metrics) < 5:
            issues.append('Limited metric variety')
        
        quality_score = avg_confidence * 100
        if age_hours > 48:
            quality_score *= 0.8
        if len(all_metrics) < 5:
            quality_score *= 0.9
        
        return {
            'score': round(quality_score, 1),
            'confidence': round(avg_confidence, 3),
            'freshness_hours': round(age_hours, 1),
            'metric_count': len(all_metrics),
            'issues': issues
        }
    
    def _aggregate_portfolio_metrics(self, portfolio_data: Dict) -> Dict[str, Any]:
        """Aggregate metrics across portfolio companies"""
        aggregated = {
            'total_revenue': 0,
            'total_arr': 0,
            'total_customers': 0,
            'average_health_score': 0,
            'companies_with_data': 0
        }
        
        valid_companies = 0
        
        for company_id, data in portfolio_data.items():
            if data.get('status') == 'error' or data.get('status') == 'no_data':
                continue
            
            valid_companies += 1
            aggregated['companies_with_data'] = valid_companies
            
            # Aggregate health scores
            aggregated['average_health_score'] += data.get('health_score', 0)
            
            # Aggregate financial metrics
            key_metrics = data.get('key_metrics', {})
            financial = key_metrics.get('financial', {})
            
            if 'revenue' in financial:
                aggregated['total_revenue'] += financial['revenue']
            if 'arr' in financial:
                aggregated['total_arr'] += financial['arr']
            
            customer = key_metrics.get('customer', {})
            if 'total_customers' in customer:
                aggregated['total_customers'] += customer['total_customers']
        
        if valid_companies > 0:
            aggregated['average_health_score'] /= valid_companies
        
        return aggregated
    
    def _analyze_portfolio_trends(self, portfolio_data: Dict) -> List[Dict]:
        """Analyze trends across the portfolio"""
        portfolio_trends = []
        
        # Count companies with positive/negative trends
        positive_count = 0
        negative_count = 0
        
        for company_id, data in portfolio_data.items():
            if data.get('status') == 'error' or data.get('status') == 'no_data':
                continue
            
            trends = data.get('trends', {})
            if trends.get('positive_trends'):
                positive_count += 1
            if trends.get('negative_trends'):
                negative_count += 1
        
        if positive_count > negative_count:
            portfolio_trends.append({
                'type': 'positive',
                'description': f'{positive_count} companies showing positive trends',
                'impact': 'high' if positive_count > 3 else 'medium'
            })
        elif negative_count > positive_count:
            portfolio_trends.append({
                'type': 'negative',
                'description': f'{negative_count} companies showing concerning trends',
                'impact': 'high' if negative_count > 2 else 'medium'
            })
        
        return portfolio_trends
    
    def _generate_portfolio_alerts(self, portfolio_data: Dict) -> List[Dict]:
        """Generate portfolio-wide alerts"""
        portfolio_alerts = []
        
        critical_companies = []
        low_health_companies = []
        
        for company_id, data in portfolio_data.items():
            if data.get('status') == 'error' or data.get('status') == 'no_data':
                continue
            
            health_score = data.get('health_score', 50)
            alerts = data.get('alerts', [])
            
            # Check for critical alerts
            critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
            if critical_alerts:
                critical_companies.append(company_id)
            
            # Check for low health scores
            if health_score < 30:
                low_health_companies.append(company_id)
        
        if critical_companies:
            portfolio_alerts.append({
                'type': 'critical_companies',
                'severity': 'critical',
                'description': f'{len(critical_companies)} companies have critical alerts',
                'companies': critical_companies,
                'action_required': True
            })
        
        if low_health_companies:
            portfolio_alerts.append({
                'type': 'low_health',
                'severity': 'high',
                'description': f'{len(low_health_companies)} companies have low health scores',
                'companies': low_health_companies,
                'action_required': True
            })
        
        return portfolio_alerts
    
    def _rank_companies_by_performance(self, portfolio_data: Dict) -> List[Dict]:
        """Rank companies by performance metrics"""
        company_scores = []
        
        for company_id, data in portfolio_data.items():
            if data.get('status') == 'error' or data.get('status') == 'no_data':
                continue
            
            health_score = data.get('health_score', 0)
            alert_count = len(data.get('alerts', []))
            
            # Calculate performance score
            performance_score = health_score - (alert_count * 5)
            
            company_scores.append({
                'company_id': company_id,
                'health_score': health_score,
                'performance_score': performance_score,
                'alert_count': alert_count
            })
        
        # Sort by performance score
        company_scores.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return company_scores

class TrendAnalyzer:
    """Analyzes trends in metric data"""
    
    def analyze_company_trends(self, company_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze trends for a specific company"""
        try:
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            snapshots = MetricSnapshot.query.filter(
                MetricSnapshot.company_id == company_id,
                MetricSnapshot.snapshot_date >= start_date
            ).order_by(MetricSnapshot.snapshot_date.asc()).all()
            
            if len(snapshots) < 2:
                return {'status': 'insufficient_data'}
            
            # Convert to DataFrame for analysis
            df = self._snapshots_to_dataframe(snapshots)
            
            # Analyze trends for each metric
            trends = {
                'positive_trends': [],
                'negative_trends': [],
                'stable_metrics': [],
                'volatile_metrics': []
            }
            
            for column in df.columns:
                if column in ['date', 'company_id']:
                    continue
                
                trend_analysis = self._analyze_metric_trend(df[column], column)
                
                if trend_analysis['direction'] == 'increasing':
                    if self._is_positive_metric(column):
                        trends['positive_trends'].append(trend_analysis)
                    else:
                        trends['negative_trends'].append(trend_analysis)
                elif trend_analysis['direction'] == 'decreasing':
                    if self._is_positive_metric(column):
                        trends['negative_trends'].append(trend_analysis)
                    else:
                        trends['positive_trends'].append(trend_analysis)
                elif trend_analysis['direction'] == 'stable':
                    trends['stable_metrics'].append(trend_analysis)
                else:  # volatile
                    trends['volatile_metrics'].append(trend_analysis)
            
            return trends
            
        except Exception as e:
            print(f"Error analyzing trends: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _snapshots_to_dataframe(self, snapshots: List[MetricSnapshot]) -> pd.DataFrame:
        """Convert metric snapshots to DataFrame"""
        data = []
        
        for snapshot in snapshots:
            metrics = json.loads(snapshot.metrics)
            row = {
                'date': snapshot.snapshot_date,
                'company_id': snapshot.company_id
            }
            
            # Add numeric metrics only
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    row[key] = value
            
            data.append(row)
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def _analyze_metric_trend(self, series: pd.Series, metric_name: str) -> Dict[str, Any]:
        """Analyze trend for a specific metric"""
        # Remove NaN values
        clean_series = series.dropna()
        
        if len(clean_series) < 2:
            return {
                'metric': metric_name,
                'direction': 'unknown',
                'confidence': 0
            }
        
        # Calculate trend using linear regression
        x = np.arange(len(clean_series))
        y = clean_series.values
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        
        # Calculate correlation coefficient for trend strength
        correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
        
        # Determine direction
        if abs(slope) < 0.01 * np.mean(y):  # Less than 1% change
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Check for volatility
        if len(clean_series) > 3:
            volatility = np.std(y) / np.mean(y) if np.mean(y) != 0 else 0
            if volatility > 0.3:  # High volatility
                direction = 'volatile'
        
        # Calculate percentage change
        if len(clean_series) >= 2:
            start_value = clean_series.iloc[0]
            end_value = clean_series.iloc[-1]
            pct_change = ((end_value - start_value) / start_value * 100) if start_value != 0 else 0
        else:
            pct_change = 0
        
        return {
            'metric': metric_name,
            'direction': direction,
            'slope': slope,
            'correlation': abs(correlation),
            'confidence': abs(correlation),
            'percentage_change': round(pct_change, 2),
            'current_value': clean_series.iloc[-1] if len(clean_series) > 0 else None,
            'previous_value': clean_series.iloc[0] if len(clean_series) > 0 else None
        }
    
    def _is_positive_metric(self, metric_name: str) -> bool:
        """Determine if increasing values for this metric are positive"""
        positive_metrics = [
            'revenue', 'arr', 'mrr', 'users', 'customers', 'conversion_rate',
            'retention_rate', 'ltv', 'gross_margin', 'uptime', 'sessions'
        ]
        
        negative_metrics = [
            'churn_rate', 'cac', 'burn_rate', 'response_time_ms', 'error_rate'
        ]
        
        metric_lower = metric_name.lower()
        
        if any(pos in metric_lower for pos in positive_metrics):
            return True
        elif any(neg in metric_lower for neg in negative_metrics):
            return False
        else:
            # Default to positive for unknown metrics
            return True

class AlertGenerator:
    """Generates alerts based on metric thresholds and patterns"""
    
    def generate_company_alerts(self, company_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Generate alerts for a company"""
        try:
            alerts = []
            
            # Get recent snapshots
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            snapshots = MetricSnapshot.query.filter(
                MetricSnapshot.company_id == company_id,
                MetricSnapshot.snapshot_date >= start_date
            ).order_by(MetricSnapshot.snapshot_date.desc()).all()
            
            if not snapshots:
                return []
            
            latest_snapshot = snapshots[0]
            latest_metrics = json.loads(latest_snapshot.metrics)
            
            # Check threshold-based alerts
            threshold_alerts = self._check_threshold_alerts(latest_metrics)
            alerts.extend(threshold_alerts)
            
            # Check trend-based alerts
            if len(snapshots) > 1:
                trend_alerts = self._check_trend_alerts(snapshots)
                alerts.extend(trend_alerts)
            
            # Check data quality alerts
            quality_alerts = self._check_data_quality_alerts(snapshots)
            alerts.extend(quality_alerts)
            
            # Sort alerts by severity
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 3))
            
            return alerts
            
        except Exception as e:
            print(f"Error generating alerts: {e}")
            return []
    
    def _check_threshold_alerts(self, metrics: Dict) -> List[Dict]:
        """Check for threshold-based alerts"""
        alerts = []
        
        # Critical thresholds
        critical_thresholds = {
            'runway_months': {'min': 3, 'message': 'Cash runway critically low'},
            'churn_rate': {'max': 0.15, 'message': 'Churn rate critically high'},
            'uptime': {'min': 0.95, 'message': 'System uptime critically low'}
        }
        
        # High priority thresholds
        high_thresholds = {
            'runway_months': {'min': 6, 'message': 'Cash runway getting low'},
            'churn_rate': {'max': 0.10, 'message': 'Churn rate elevated'},
            'burn_rate': {'max': 100000, 'message': 'High burn rate detected'},
            'conversion_rate': {'min': 0.02, 'message': 'Conversion rate below target'}
        }
        
        # Check critical thresholds
        for metric, threshold in critical_thresholds.items():
            if metric in metrics:
                value = metrics[metric]
                if 'min' in threshold and value < threshold['min']:
                    alerts.append({
                        'type': 'threshold',
                        'severity': 'critical',
                        'metric': metric,
                        'value': value,
                        'threshold': threshold['min'],
                        'message': threshold['message'],
                        'action_required': True
                    })
                elif 'max' in threshold and value > threshold['max']:
                    alerts.append({
                        'type': 'threshold',
                        'severity': 'critical',
                        'metric': metric,
                        'value': value,
                        'threshold': threshold['max'],
                        'message': threshold['message'],
                        'action_required': True
                    })
        
        # Check high priority thresholds
        for metric, threshold in high_thresholds.items():
            if metric in metrics:
                value = metrics[metric]
                if 'min' in threshold and value < threshold['min']:
                    alerts.append({
                        'type': 'threshold',
                        'severity': 'high',
                        'metric': metric,
                        'value': value,
                        'threshold': threshold['min'],
                        'message': threshold['message'],
                        'action_required': False
                    })
                elif 'max' in threshold and value > threshold['max']:
                    alerts.append({
                        'type': 'threshold',
                        'severity': 'high',
                        'metric': metric,
                        'value': value,
                        'threshold': threshold['max'],
                        'message': threshold['message'],
                        'action_required': False
                    })
        
        return alerts
    
    def _check_trend_alerts(self, snapshots: List[MetricSnapshot]) -> List[Dict]:
        """Check for trend-based alerts"""
        alerts = []
        
        if len(snapshots) < 3:
            return alerts
        
        # Convert to DataFrame for trend analysis
        df = self._snapshots_to_dataframe(snapshots)
        
        # Check for concerning trends
        concerning_trends = {
            'revenue': {'direction': 'decreasing', 'threshold': -0.1},  # 10% decline
            'arr': {'direction': 'decreasing', 'threshold': -0.05},     # 5% decline
            'churn_rate': {'direction': 'increasing', 'threshold': 0.02}, # 2% increase
            'burn_rate': {'direction': 'increasing', 'threshold': 0.2}   # 20% increase
        }
        
        for metric, criteria in concerning_trends.items():
            if metric in df.columns:
                series = df[metric].dropna()
                if len(series) >= 3:
                    # Calculate trend
                    recent_values = series.tail(3).values
                    if len(recent_values) >= 2:
                        change = (recent_values[-1] - recent_values[0]) / recent_values[0]
                        
                        if criteria['direction'] == 'decreasing' and change < criteria['threshold']:
                            alerts.append({
                                'type': 'trend',
                                'severity': 'high',
                                'metric': metric,
                                'trend': 'declining',
                                'change_percentage': round(change * 100, 1),
                                'message': f'{metric.replace("_", " ").title()} showing declining trend',
                                'action_required': True
                            })
                        elif criteria['direction'] == 'increasing' and change > criteria['threshold']:
                            alerts.append({
                                'type': 'trend',
                                'severity': 'high',
                                'metric': metric,
                                'trend': 'increasing',
                                'change_percentage': round(change * 100, 1),
                                'message': f'{metric.replace("_", " ").title()} showing concerning increase',
                                'action_required': True
                            })
        
        return alerts
    
    def _check_data_quality_alerts(self, snapshots: List[MetricSnapshot]) -> List[Dict]:
        """Check for data quality issues"""
        alerts = []
        
        # Check for stale data
        latest_snapshot = snapshots[0]
        age_hours = (datetime.utcnow() - latest_snapshot.snapshot_date).total_seconds() / 3600
        
        if age_hours > 48:
            alerts.append({
                'type': 'data_quality',
                'severity': 'medium',
                'message': f'Data is {round(age_hours, 1)} hours old',
                'action_required': False
            })
        
        # Check for low confidence scores
        low_confidence_count = sum(1 for s in snapshots if s.confidence_score < 0.7)
        if low_confidence_count > len(snapshots) * 0.5:
            alerts.append({
                'type': 'data_quality',
                'severity': 'medium',
                'message': 'Multiple low-confidence data points detected',
                'action_required': False
            })
        
        return alerts
    
    def _snapshots_to_dataframe(self, snapshots: List[MetricSnapshot]) -> pd.DataFrame:
        """Convert snapshots to DataFrame (reused from TrendAnalyzer)"""
        data = []
        
        for snapshot in snapshots:
            metrics = json.loads(snapshot.metrics)
            row = {'date': snapshot.snapshot_date}
            
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    row[key] = value
            
            data.append(row)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        
        return df

class InsightGenerator:
    """Generates business insights from data patterns"""
    
    def generate_company_insights(self, company_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Generate insights for a company"""
        try:
            insights = []
            
            # Get data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            snapshots = MetricSnapshot.query.filter(
                MetricSnapshot.company_id == company_id,
                MetricSnapshot.snapshot_date >= start_date
            ).order_by(MetricSnapshot.snapshot_date.desc()).all()
            
            if not snapshots:
                return []
            
            # Generate different types of insights
            performance_insights = self._generate_performance_insights(snapshots)
            insights.extend(performance_insights)
            
            efficiency_insights = self._generate_efficiency_insights(snapshots)
            insights.extend(efficiency_insights)
            
            growth_insights = self._generate_growth_insights(snapshots)
            insights.extend(growth_insights)
            
            risk_insights = self._generate_risk_insights(snapshots)
            insights.extend(risk_insights)
            
            return insights
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            return []
    
    def _generate_performance_insights(self, snapshots: List[MetricSnapshot]) -> List[Dict]:
        """Generate performance-related insights"""
        insights = []
        
        if not snapshots:
            return insights
        
        latest_metrics = json.loads(snapshots[0].metrics)
        
        # Revenue efficiency insight
        if 'revenue' in latest_metrics and 'headcount' in latest_metrics:
            revenue_per_employee = latest_metrics['revenue'] / latest_metrics['headcount']
            
            if revenue_per_employee > 200000:  # $200k+ per employee
                insights.append({
                    'type': 'performance',
                    'category': 'efficiency',
                    'title': 'High Revenue Efficiency',
                    'description': f'Revenue per employee is ${revenue_per_employee:,.0f}, indicating strong productivity',
                    'impact': 'positive',
                    'confidence': 0.8
                })
            elif revenue_per_employee < 100000:  # <$100k per employee
                insights.append({
                    'type': 'performance',
                    'category': 'efficiency',
                    'title': 'Revenue Efficiency Opportunity',
                    'description': f'Revenue per employee is ${revenue_per_employee:,.0f}, below industry benchmarks',
                    'impact': 'negative',
                    'confidence': 0.7,
                    'recommendation': 'Consider productivity improvements or revenue optimization'
                })
        
        # Customer acquisition efficiency
        if 'ltv' in latest_metrics and 'cac' in latest_metrics:
            ltv_cac_ratio = latest_metrics['ltv'] / latest_metrics['cac']
            
            if ltv_cac_ratio > 3:
                insights.append({
                    'type': 'performance',
                    'category': 'customer_acquisition',
                    'title': 'Strong Unit Economics',
                    'description': f'LTV:CAC ratio of {ltv_cac_ratio:.1f}:1 indicates healthy customer economics',
                    'impact': 'positive',
                    'confidence': 0.9
                })
            elif ltv_cac_ratio < 2:
                insights.append({
                    'type': 'performance',
                    'category': 'customer_acquisition',
                    'title': 'Unit Economics Concern',
                    'description': f'LTV:CAC ratio of {ltv_cac_ratio:.1f}:1 is below recommended 3:1 threshold',
                    'impact': 'negative',
                    'confidence': 0.8,
                    'recommendation': 'Focus on increasing LTV or reducing CAC'
                })
        
        return insights
    
    def _generate_efficiency_insights(self, snapshots: List[MetricSnapshot]) -> List[Dict]:
        """Generate efficiency-related insights"""
        insights = []
        
        if len(snapshots) < 2:
            return insights
        
        # Analyze conversion funnel efficiency
        latest_metrics = json.loads(snapshots[0].metrics)
        
        if 'sessions' in latest_metrics and 'conversion_rate' in latest_metrics:
            conversion_rate = latest_metrics['conversion_rate']
            
            if conversion_rate > 0.05:  # >5% conversion
                insights.append({
                    'type': 'efficiency',
                    'category': 'conversion',
                    'title': 'High Conversion Performance',
                    'description': f'Conversion rate of {conversion_rate*100:.1f}% is above industry average',
                    'impact': 'positive',
                    'confidence': 0.8
                })
            elif conversion_rate < 0.02:  # <2% conversion
                insights.append({
                    'type': 'efficiency',
                    'category': 'conversion',
                    'title': 'Conversion Optimization Opportunity',
                    'description': f'Conversion rate of {conversion_rate*100:.1f}% has room for improvement',
                    'impact': 'neutral',
                    'confidence': 0.7,
                    'recommendation': 'Consider A/B testing landing pages and user experience improvements'
                })
        
        return insights
    
    def _generate_growth_insights(self, snapshots: List[MetricSnapshot]) -> List[Dict]:
        """Generate growth-related insights"""
        insights = []
        
        if len(snapshots) < 3:
            return insights
        
        # Analyze growth patterns
        df = self._snapshots_to_dataframe(snapshots)
        
        # Revenue growth analysis
        if 'revenue' in df.columns:
            revenue_series = df['revenue'].dropna()
            if len(revenue_series) >= 3:
                recent_growth = self._calculate_growth_rate(revenue_series.tail(3))
                
                if recent_growth > 0.1:  # >10% growth
                    insights.append({
                        'type': 'growth',
                        'category': 'revenue',
                        'title': 'Strong Revenue Growth',
                        'description': f'Revenue growing at {recent_growth*100:.1f}% rate',
                        'impact': 'positive',
                        'confidence': 0.8
                    })
                elif recent_growth < -0.05:  # >5% decline
                    insights.append({
                        'type': 'growth',
                        'category': 'revenue',
                        'title': 'Revenue Decline Detected',
                        'description': f'Revenue declining at {abs(recent_growth)*100:.1f}% rate',
                        'impact': 'negative',
                        'confidence': 0.8,
                        'recommendation': 'Investigate causes and implement recovery strategies'
                    })
        
        return insights
    
    def _generate_risk_insights(self, snapshots: List[MetricSnapshot]) -> List[Dict]:
        """Generate risk-related insights"""
        insights = []
        
        if not snapshots:
            return insights
        
        latest_metrics = json.loads(snapshots[0].metrics)
        
        # Cash runway risk
        if 'runway_months' in latest_metrics:
            runway = latest_metrics['runway_months']
            
            if runway < 6:
                insights.append({
                    'type': 'risk',
                    'category': 'financial',
                    'title': 'Cash Runway Risk',
                    'description': f'Only {runway:.1f} months of runway remaining',
                    'impact': 'negative',
                    'confidence': 0.9,
                    'recommendation': 'Urgent: Secure additional funding or reduce burn rate'
                })
            elif runway < 12:
                insights.append({
                    'type': 'risk',
                    'category': 'financial',
                    'title': 'Fundraising Timeline',
                    'description': f'{runway:.1f} months of runway - consider fundraising timeline',
                    'impact': 'neutral',
                    'confidence': 0.8,
                    'recommendation': 'Begin fundraising preparations'
                })
        
        # Customer concentration risk
        if 'total_customers' in latest_metrics and latest_metrics['total_customers'] < 10:
            insights.append({
                'type': 'risk',
                'category': 'customer',
                'title': 'Customer Concentration Risk',
                'description': f'Only {latest_metrics["total_customers"]} customers - high concentration risk',
                'impact': 'negative',
                'confidence': 0.7,
                'recommendation': 'Focus on customer acquisition and diversification'
            })
        
        return insights
    
    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate growth rate from a series"""
        if len(series) < 2:
            return 0
        
        start_value = series.iloc[0]
        end_value = series.iloc[-1]
        
        if start_value == 0:
            return 0
        
        return (end_value - start_value) / start_value
    
    def _snapshots_to_dataframe(self, snapshots: List[MetricSnapshot]) -> pd.DataFrame:
        """Convert snapshots to DataFrame"""
        data = []
        
        for snapshot in snapshots:
            metrics = json.loads(snapshot.metrics)
            row = {'date': snapshot.snapshot_date}
            
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    row[key] = value
            
            data.append(row)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        
        return df

class DataSorter:
    """Sorts and prioritizes data for executive consumption"""
    
    def sort_metrics_by_importance(self, metrics: Dict, company_context: Dict = None) -> List[Dict]:
        """Sort metrics by importance for executive attention"""
        try:
            metric_priorities = []
            
            # Define importance weights
            importance_weights = {
                # Financial metrics (highest priority)
                'revenue': 10,
                'arr': 10,
                'mrr': 9,
                'burn_rate': 9,
                'runway_months': 10,
                'gross_margin': 8,
                
                # Growth metrics
                'revenue_growth_rate': 9,
                'user_growth_rate': 7,
                'customer_growth_rate': 8,
                
                # Customer metrics
                'churn_rate': 9,
                'ltv': 8,
                'cac': 8,
                'total_customers': 7,
                
                # Operational metrics
                'active_users': 6,
                'conversion_rate': 7,
                'uptime': 6,
                
                # Team metrics
                'headcount': 5,
                'revenue_per_employee': 6
            }
            
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    importance = importance_weights.get(metric_name, 3)  # Default importance
                    
                    metric_priorities.append({
                        'metric': metric_name,
                        'value': value,
                        'importance': importance,
                        'category': self._categorize_metric(metric_name)
                    })
            
            # Sort by importance (descending)
            metric_priorities.sort(key=lambda x: x['importance'], reverse=True)
            
            return metric_priorities
            
        except Exception as e:
            print(f"Error sorting metrics: {e}")
            return []
    
    def prioritize_alerts(self, alerts: List[Dict]) -> List[Dict]:
        """Prioritize alerts for executive attention"""
        try:
            # Define priority scores
            severity_scores = {
                'critical': 100,
                'high': 75,
                'medium': 50,
                'low': 25
            }
            
            type_scores = {
                'threshold': 20,
                'trend': 15,
                'data_quality': 5
            }
            
            # Calculate priority scores
            for alert in alerts:
                severity_score = severity_scores.get(alert.get('severity', 'low'), 25)
                type_score = type_scores.get(alert.get('type', 'data_quality'), 5)
                action_score = 10 if alert.get('action_required', False) else 0
                
                alert['priority_score'] = severity_score + type_score + action_score
            
            # Sort by priority score (descending)
            alerts.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            
            return alerts
            
        except Exception as e:
            print(f"Error prioritizing alerts: {e}")
            return alerts
    
    def _categorize_metric(self, metric_name: str) -> str:
        """Categorize a metric"""
        metric_lower = metric_name.lower()
        
        if any(keyword in metric_lower for keyword in ['revenue', 'arr', 'mrr', 'burn', 'runway', 'margin']):
            return 'financial'
        elif any(keyword in metric_lower for keyword in ['growth', 'increase', 'change']):
            return 'growth'
        elif any(keyword in metric_lower for keyword in ['customer', 'churn', 'retention', 'ltv', 'cac']):
            return 'customer'
        elif any(keyword in metric_lower for keyword in ['user', 'session', 'conversion', 'uptime']):
            return 'operational'
        elif any(keyword in metric_lower for keyword in ['headcount', 'employee', 'team']):
            return 'team'
        else:
            return 'other'

class AnomalyDetector:
    """Detects anomalies in metric data"""
    
    def detect_anomalies(self, company_id: str, days: int = 30) -> List[Dict]:
        """Detect anomalies in company metrics"""
        try:
            anomalies = []
            
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            snapshots = MetricSnapshot.query.filter(
                MetricSnapshot.company_id == company_id,
                MetricSnapshot.snapshot_date >= start_date
            ).order_by(MetricSnapshot.snapshot_date.asc()).all()
            
            if len(snapshots) < 5:  # Need minimum data points
                return anomalies
            
            # Convert to DataFrame
            df = self._snapshots_to_dataframe(snapshots)
            
            # Detect anomalies for each numeric metric
            for column in df.columns:
                if column in ['date', 'company_id']:
                    continue
                
                series = df[column].dropna()
                if len(series) < 5:
                    continue
                
                metric_anomalies = self._detect_metric_anomalies(series, column)
                anomalies.extend(metric_anomalies)
            
            return anomalies
            
        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return []
    
    def _detect_metric_anomalies(self, series: pd.Series, metric_name: str) -> List[Dict]:
        """Detect anomalies in a specific metric"""
        anomalies = []
        
        try:
            # Calculate statistical thresholds
            mean_val = series.mean()
            std_val = series.std()
            
            # Define anomaly thresholds (2 standard deviations)
            upper_threshold = mean_val + (2 * std_val)
            lower_threshold = mean_val - (2 * std_val)
            
            # Find anomalous values
            for idx, value in series.items():
                if value > upper_threshold or value < lower_threshold:
                    anomaly_type = 'spike' if value > upper_threshold else 'drop'
                    
                    # Calculate severity based on how far from normal
                    deviation = abs(value - mean_val) / std_val
                    
                    if deviation > 3:
                        severity = 'high'
                    elif deviation > 2.5:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    anomalies.append({
                        'metric': metric_name,
                        'type': anomaly_type,
                        'value': value,
                        'expected_range': [lower_threshold, upper_threshold],
                        'deviation': deviation,
                        'severity': severity,
                        'timestamp': series.index[idx] if hasattr(series.index[idx], 'isoformat') else str(series.index[idx])
                    })
            
            return anomalies
            
        except Exception as e:
            print(f"Error detecting anomalies for {metric_name}: {e}")
            return []
    
    def _snapshots_to_dataframe(self, snapshots: List[MetricSnapshot]) -> pd.DataFrame:
        """Convert snapshots to DataFrame"""
        data = []
        
        for snapshot in snapshots:
            metrics = json.loads(snapshot.metrics)
            row = {'date': snapshot.snapshot_date}
            
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    row[key] = value
            
            data.append(row)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        
        return df

# Utility functions for external use

def generate_executive_brief(company_id: str, days: int = 7) -> Dict[str, Any]:
    """Generate an executive brief for a company"""
    engine = IntelligenceEngine()
    return engine.generate_company_brief(company_id, days)

def generate_portfolio_dashboard(company_ids: List[str]) -> Dict[str, Any]:
    """Generate a portfolio dashboard"""
    engine = IntelligenceEngine()
    return engine.generate_portfolio_summary(company_ids)

def detect_company_anomalies(company_id: str, days: int = 30) -> List[Dict]:
    """Detect anomalies for a company"""
    detector = AnomalyDetector()
    return detector.detect_anomalies(company_id, days)

