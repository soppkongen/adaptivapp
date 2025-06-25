"""
Data Normalization and Structuring Engine

This module handles the transformation of raw data into standardized business metrics
and entities according to the Elite Command Data API schema.
"""

import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from src.models.elite_command import (
    db, RawDataEntry, MetricSnapshot, Company, BusinessUnit,
    DataSource, BusinessModel, BusinessStage
)

class DataNormalizationEngine:
    """Main engine for normalizing and structuring raw data"""
    
    def __init__(self):
        self.metric_normalizers = {
            'financial': FinancialMetricNormalizer(),
            'operational': OperationalMetricNormalizer(),
            'customer': CustomerMetricNormalizer(),
            'team': TeamMetricNormalizer(),
            'general': GeneralMetricNormalizer()
        }
        self.entity_mapper = EntityMapper()
        self.confidence_scorer = ConfidenceScorer()
    
    def process_raw_data_batch(self, batch_size: int = 100) -> Dict[str, int]:
        """Process a batch of pending raw data entries"""
        try:
            # Get pending raw data entries
            pending_entries = RawDataEntry.query.filter(
                RawDataEntry.processing_status == 'pending'
            ).limit(batch_size).all()
            
            results = {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for entry in pending_entries:
                try:
                    result = self.process_raw_data_entry(entry)
                    if result:
                        results['successful'] += 1
                    else:
                        results['skipped'] += 1
                    results['processed'] += 1
                    
                except Exception as e:
                    print(f"Error processing raw data entry {entry.id}: {e}")
                    entry.processing_status = 'error'
                    results['failed'] += 1
                    results['processed'] += 1
            
            db.session.commit()
            return results
            
        except Exception as e:
            print(f"Error in batch processing: {e}")
            return {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
    
    def process_raw_data_entry(self, entry: RawDataEntry) -> bool:
        """Process a single raw data entry"""
        try:
            # Parse raw data
            raw_data = json.loads(entry.raw_data)
            
            # Determine data type if not already set
            if not entry.data_type:
                entry.data_type = self._detect_data_type(raw_data)
            
            # Get appropriate normalizer
            normalizer = self.metric_normalizers.get(
                entry.data_type, 
                self.metric_normalizers['general']
            )
            
            # Normalize the data
            normalized_metrics = normalizer.normalize(raw_data, entry)
            
            if not normalized_metrics:
                entry.processing_status = 'skipped'
                return False
            
            # Map entities
            entity_mappings = self.entity_mapper.map_entities(raw_data, entry)
            
            # Calculate confidence score
            confidence_score = self.confidence_scorer.calculate_confidence(
                raw_data, normalized_metrics, entry
            )
            
            # Create metric snapshot
            self._create_metric_snapshot(
                entry, normalized_metrics, entity_mappings, confidence_score
            )
            
            # Update processing status
            entry.processing_status = 'processed'
            entry.processed_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            print(f"Error processing entry {entry.id}: {e}")
            entry.processing_status = 'error'
            return False
    
    def _detect_data_type(self, raw_data: Dict) -> str:
        """Detect data type from raw data content"""
        data_str = json.dumps(raw_data).lower()
        
        # Financial indicators
        financial_keywords = ['revenue', 'arr', 'mrr', 'profit', 'loss', 'expense', 'cost']
        if any(keyword in data_str for keyword in financial_keywords):
            return 'financial'
        
        # Operational indicators
        operational_keywords = ['users', 'sessions', 'conversion', 'engagement', 'performance']
        if any(keyword in data_str for keyword in operational_keywords):
            return 'operational'
        
        # Customer indicators
        customer_keywords = ['customer', 'subscriber', 'account', 'churn', 'retention']
        if any(keyword in data_str for keyword in customer_keywords):
            return 'customer'
        
        # Team indicators
        team_keywords = ['employee', 'team', 'headcount', 'hiring', 'staff']
        if any(keyword in data_str for keyword in team_keywords):
            return 'team'
        
        return 'general'
    
    def _create_metric_snapshot(self, entry: RawDataEntry, metrics: Dict, 
                              entities: Dict, confidence: float):
        """Create a normalized metric snapshot"""
        # Get data source to determine company
        data_source = DataSource.query.get(entry.source_id)
        if not data_source:
            return
        
        # Combine metrics with entity mappings and metadata
        final_metrics = {
            **metrics,
            **entities,
            'source_entry_id': entry.id,
            'normalization_timestamp': datetime.utcnow().isoformat(),
            'data_type': entry.data_type,
            'confidence_score': confidence
        }
        
        # Create metric snapshot
        snapshot = MetricSnapshot(
            id=str(uuid.uuid4()),
            company_id=data_source.company_id,
            metrics=json.dumps(final_metrics),
            snapshot_date=entry.source_timestamp or datetime.utcnow(),
            source_id=entry.source_id,
            confidence_score=confidence
        )
        
        db.session.add(snapshot)
        
        # Link back to raw entry
        entry.normalized_data_id = snapshot.id

class FinancialMetricNormalizer:
    """Normalizes financial metrics to standard format"""
    
    def normalize(self, raw_data: Dict, entry: RawDataEntry) -> Optional[Dict]:
        """Normalize financial data"""
        try:
            metrics = {}
            
            # Revenue metrics
            revenue = self._extract_revenue(raw_data)
            if revenue:
                metrics.update(revenue)
            
            # Recurring revenue metrics
            recurring = self._extract_recurring_revenue(raw_data)
            if recurring:
                metrics.update(recurring)
            
            # Cost metrics
            costs = self._extract_costs(raw_data)
            if costs:
                metrics.update(costs)
            
            # Profitability metrics
            profitability = self._extract_profitability(raw_data)
            if profitability:
                metrics.update(profitability)
            
            # Cash flow metrics
            cash_flow = self._extract_cash_flow(raw_data)
            if cash_flow:
                metrics.update(cash_flow)
            
            return metrics if metrics else None
            
        except Exception as e:
            print(f"Error normalizing financial data: {e}")
            return None
    
    def _extract_revenue(self, data: Dict) -> Dict:
        """Extract and normalize revenue metrics"""
        revenue_metrics = {}
        
        # Look for revenue in various formats
        revenue_patterns = [
            r'revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'total[_\s]revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'gross[_\s]revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        data_str = json.dumps(data).lower()
        
        for pattern in revenue_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    revenue_metrics['revenue'] = value
                    break
                except ValueError:
                    continue
        
        # Look for revenue growth
        growth_patterns = [
            r'revenue.*?(?:growth|increase)[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
            r'(?:growth|increase).*?revenue[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
        ]
        
        for pattern in growth_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    revenue_metrics['revenue_growth_rate'] = value / 100
                    break
                except ValueError:
                    continue
        
        return revenue_metrics
    
    def _extract_recurring_revenue(self, data: Dict) -> Dict:
        """Extract recurring revenue metrics (ARR, MRR)"""
        recurring_metrics = {}
        
        # ARR patterns
        arr_patterns = [
            r'arr[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'annual[_\s]recurring[_\s]revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        # MRR patterns
        mrr_patterns = [
            r'mrr[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'monthly[_\s]recurring[_\s]revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract ARR
        for pattern in arr_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    recurring_metrics['arr'] = value
                    break
                except ValueError:
                    continue
        
        # Extract MRR
        for pattern in mrr_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    recurring_metrics['mrr'] = value
                    # Calculate ARR from MRR if ARR not found
                    if 'arr' not in recurring_metrics:
                        recurring_metrics['arr'] = value * 12
                    break
                except ValueError:
                    continue
        
        return recurring_metrics
    
    def _extract_costs(self, data: Dict) -> Dict:
        """Extract cost metrics"""
        cost_metrics = {}
        
        # CAC (Customer Acquisition Cost)
        cac_patterns = [
            r'cac[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'customer[_\s]acquisition[_\s]cost[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'acquisition[_\s]cost[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        # Operating expenses
        opex_patterns = [
            r'opex[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'operating[_\s]expenses?[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'operational[_\s]costs?[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract CAC
        for pattern in cac_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    cost_metrics['cac'] = value
                    break
                except ValueError:
                    continue
        
        # Extract OPEX
        for pattern in opex_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    cost_metrics['operating_expenses'] = value
                    break
                except ValueError:
                    continue
        
        return cost_metrics
    
    def _extract_profitability(self, data: Dict) -> Dict:
        """Extract profitability metrics"""
        profit_metrics = {}
        
        # Gross margin
        margin_patterns = [
            r'gross[_\s]margin[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
            r'margin[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
        ]
        
        # EBITDA
        ebitda_patterns = [
            r'ebitda[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'earnings[_\s]before[_\s]interest[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract margins
        for pattern in margin_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    profit_metrics['gross_margin'] = value / 100 if value > 1 else value
                    break
                except ValueError:
                    continue
        
        # Extract EBITDA
        for pattern in ebitda_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    profit_metrics['ebitda'] = value
                    break
                except ValueError:
                    continue
        
        return profit_metrics
    
    def _extract_cash_flow(self, data: Dict) -> Dict:
        """Extract cash flow metrics"""
        cash_metrics = {}
        
        # Burn rate
        burn_patterns = [
            r'burn[_\s]rate[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'monthly[_\s]burn[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'cash[_\s]burn[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        # Runway
        runway_patterns = [
            r'runway[:\s]+([0-9]+(?:\.[0-9]+)?)\s*months?',
            r'cash[_\s]runway[:\s]+([0-9]+(?:\.[0-9]+)?)\s*months?'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract burn rate
        for pattern in burn_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    cash_metrics['burn_rate'] = value
                    break
                except ValueError:
                    continue
        
        # Extract runway
        for pattern in runway_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    cash_metrics['runway_months'] = value
                    break
                except ValueError:
                    continue
        
        return cash_metrics

class OperationalMetricNormalizer:
    """Normalizes operational metrics"""
    
    def normalize(self, raw_data: Dict, entry: RawDataEntry) -> Optional[Dict]:
        """Normalize operational data"""
        try:
            metrics = {}
            
            # User metrics
            users = self._extract_user_metrics(raw_data)
            if users:
                metrics.update(users)
            
            # Engagement metrics
            engagement = self._extract_engagement_metrics(raw_data)
            if engagement:
                metrics.update(engagement)
            
            # Performance metrics
            performance = self._extract_performance_metrics(raw_data)
            if performance:
                metrics.update(performance)
            
            return metrics if metrics else None
            
        except Exception as e:
            print(f"Error normalizing operational data: {e}")
            return None
    
    def _extract_user_metrics(self, data: Dict) -> Dict:
        """Extract user-related metrics"""
        user_metrics = {}
        
        # Active users
        user_patterns = [
            r'(?:active\s+)?users?[:\s]+([0-9,]+)',
            r'total[_\s]users?[:\s]+([0-9,]+)',
            r'registered[_\s]users?[:\s]+([0-9,]+)'
        ]
        
        # User growth
        growth_patterns = [
            r'user.*?growth[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
            r'growth.*?users?[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract user count
        for pattern in user_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = int(matches[0].replace(',', ''))
                    user_metrics['active_users'] = value
                    break
                except ValueError:
                    continue
        
        # Extract user growth
        for pattern in growth_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    user_metrics['user_growth_rate'] = value / 100
                    break
                except ValueError:
                    continue
        
        return user_metrics
    
    def _extract_engagement_metrics(self, data: Dict) -> Dict:
        """Extract engagement metrics"""
        engagement_metrics = {}
        
        # Session metrics
        session_patterns = [
            r'sessions?[:\s]+([0-9,]+)',
            r'page[_\s]views?[:\s]+([0-9,]+)',
            r'visits?[:\s]+([0-9,]+)'
        ]
        
        # Conversion metrics
        conversion_patterns = [
            r'conversion[_\s]rate[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
            r'conversion[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract sessions
        for pattern in session_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = int(matches[0].replace(',', ''))
                    engagement_metrics['sessions'] = value
                    break
                except ValueError:
                    continue
        
        # Extract conversion rate
        for pattern in conversion_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    engagement_metrics['conversion_rate'] = value / 100 if value > 1 else value
                    break
                except ValueError:
                    continue
        
        return engagement_metrics
    
    def _extract_performance_metrics(self, data: Dict) -> Dict:
        """Extract performance metrics"""
        performance_metrics = {}
        
        # Response time
        response_patterns = [
            r'response[_\s]time[:\s]+([0-9]+(?:\.[0-9]+)?)\s*ms',
            r'latency[:\s]+([0-9]+(?:\.[0-9]+)?)\s*ms'
        ]
        
        # Uptime
        uptime_patterns = [
            r'uptime[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
            r'availability[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract response time
        for pattern in response_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    performance_metrics['response_time_ms'] = value
                    break
                except ValueError:
                    continue
        
        # Extract uptime
        for pattern in uptime_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    performance_metrics['uptime'] = value / 100 if value > 1 else value
                    break
                except ValueError:
                    continue
        
        return performance_metrics

class CustomerMetricNormalizer:
    """Normalizes customer-related metrics"""
    
    def normalize(self, raw_data: Dict, entry: RawDataEntry) -> Optional[Dict]:
        """Normalize customer data"""
        try:
            metrics = {}
            
            # Customer count metrics
            customers = self._extract_customer_counts(raw_data)
            if customers:
                metrics.update(customers)
            
            # Retention metrics
            retention = self._extract_retention_metrics(raw_data)
            if retention:
                metrics.update(retention)
            
            # Lifetime value metrics
            ltv = self._extract_ltv_metrics(raw_data)
            if ltv:
                metrics.update(ltv)
            
            return metrics if metrics else None
            
        except Exception as e:
            print(f"Error normalizing customer data: {e}")
            return None
    
    def _extract_customer_counts(self, data: Dict) -> Dict:
        """Extract customer count metrics"""
        customer_metrics = {}
        
        # Customer patterns
        customer_patterns = [
            r'customers?[:\s]+([0-9,]+)',
            r'subscribers?[:\s]+([0-9,]+)',
            r'accounts?[:\s]+([0-9,]+)'
        ]
        
        data_str = json.dumps(data).lower()
        
        for pattern in customer_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = int(matches[0].replace(',', ''))
                    customer_metrics['total_customers'] = value
                    break
                except ValueError:
                    continue
        
        return customer_metrics
    
    def _extract_retention_metrics(self, data: Dict) -> Dict:
        """Extract retention and churn metrics"""
        retention_metrics = {}
        
        # Churn rate patterns
        churn_patterns = [
            r'churn[_\s]rate[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
            r'churn[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
        ]
        
        # Retention rate patterns
        retention_patterns = [
            r'retention[_\s]rate[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
            r'retention[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Extract churn rate
        for pattern in churn_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    retention_metrics['churn_rate'] = value / 100 if value > 1 else value
                    break
                except ValueError:
                    continue
        
        # Extract retention rate
        for pattern in retention_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0])
                    retention_metrics['retention_rate'] = value / 100 if value > 1 else value
                    break
                except ValueError:
                    continue
        
        return retention_metrics
    
    def _extract_ltv_metrics(self, data: Dict) -> Dict:
        """Extract lifetime value metrics"""
        ltv_metrics = {}
        
        # LTV patterns
        ltv_patterns = [
            r'ltv[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'lifetime[_\s]value[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'customer[_\s]lifetime[_\s]value[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        data_str = json.dumps(data).lower()
        
        for pattern in ltv_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    ltv_metrics['ltv'] = value
                    break
                except ValueError:
                    continue
        
        return ltv_metrics

class TeamMetricNormalizer:
    """Normalizes team and HR metrics"""
    
    def normalize(self, raw_data: Dict, entry: RawDataEntry) -> Optional[Dict]:
        """Normalize team data"""
        try:
            metrics = {}
            
            # Headcount metrics
            headcount = self._extract_headcount_metrics(raw_data)
            if headcount:
                metrics.update(headcount)
            
            # Productivity metrics
            productivity = self._extract_productivity_metrics(raw_data)
            if productivity:
                metrics.update(productivity)
            
            return metrics if metrics else None
            
        except Exception as e:
            print(f"Error normalizing team data: {e}")
            return None
    
    def _extract_headcount_metrics(self, data: Dict) -> Dict:
        """Extract headcount metrics"""
        headcount_metrics = {}
        
        # Headcount patterns
        headcount_patterns = [
            r'headcount[:\s]+([0-9,]+)',
            r'employees?[:\s]+([0-9,]+)',
            r'team[_\s]size[:\s]+([0-9,]+)',
            r'staff[:\s]+([0-9,]+)'
        ]
        
        data_str = json.dumps(data).lower()
        
        for pattern in headcount_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = int(matches[0].replace(',', ''))
                    headcount_metrics['headcount'] = value
                    break
                except ValueError:
                    continue
        
        return headcount_metrics
    
    def _extract_productivity_metrics(self, data: Dict) -> Dict:
        """Extract productivity metrics"""
        productivity_metrics = {}
        
        # Revenue per employee
        rpe_patterns = [
            r'revenue[_\s]per[_\s]employee[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
            r'rpe[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)'
        ]
        
        data_str = json.dumps(data).lower()
        
        for pattern in rpe_patterns:
            matches = re.findall(pattern, data_str)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    productivity_metrics['revenue_per_employee'] = value
                    break
                except ValueError:
                    continue
        
        return productivity_metrics

class GeneralMetricNormalizer:
    """Normalizes general/unclassified metrics"""
    
    def normalize(self, raw_data: Dict, entry: RawDataEntry) -> Optional[Dict]:
        """Normalize general data"""
        try:
            metrics = {}
            
            # Extract any numeric values with labels
            numeric_metrics = self._extract_numeric_metrics(raw_data)
            if numeric_metrics:
                metrics.update(numeric_metrics)
            
            # Extract categorical data
            categorical_metrics = self._extract_categorical_metrics(raw_data)
            if categorical_metrics:
                metrics.update(categorical_metrics)
            
            return metrics if metrics else None
            
        except Exception as e:
            print(f"Error normalizing general data: {e}")
            return None
    
    def _extract_numeric_metrics(self, data: Dict) -> Dict:
        """Extract numeric metrics with labels"""
        metrics = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)) and value != 0:
                    # Clean up key name
                    clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key).lower())
                    clean_key = re.sub(r'_+', '_', clean_key).strip('_')
                    metrics[clean_key] = value
        
        return metrics
    
    def _extract_categorical_metrics(self, data: Dict) -> Dict:
        """Extract categorical metrics"""
        metrics = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and len(value) < 100:  # Avoid long text
                    clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key).lower())
                    clean_key = re.sub(r'_+', '_', clean_key).strip('_')
                    metrics[f"{clean_key}_category"] = value
        
        return metrics

class EntityMapper:
    """Maps data to business entities"""
    
    def map_entities(self, raw_data: Dict, entry: RawDataEntry) -> Dict:
        """Map raw data to business entities"""
        try:
            mappings = {}
            
            # Get data source to determine company
            data_source = DataSource.query.get(entry.source_id)
            if data_source:
                mappings['company_id'] = data_source.company_id
                
                # Get company details
                company = Company.query.get(data_source.company_id)
                if company:
                    mappings['company_name'] = company.name
                    mappings['business_model'] = company.business_model.value if company.business_model else None
                    mappings['business_stage'] = company.stage.value if company.stage else None
            
            # Map to business units if applicable
            business_unit = self._identify_business_unit(raw_data, data_source.company_id if data_source else None)
            if business_unit:
                mappings['business_unit_id'] = business_unit
            
            # Add temporal mapping
            mappings['reporting_period'] = self._identify_reporting_period(raw_data)
            
            return mappings
            
        except Exception as e:
            print(f"Error mapping entities: {e}")
            return {}
    
    def _identify_business_unit(self, data: Dict, company_id: str) -> Optional[str]:
        """Identify relevant business unit"""
        if not company_id:
            return None
        
        try:
            # Look for business unit indicators in data
            data_str = json.dumps(data).lower()
            
            # Get business units for company
            business_units = BusinessUnit.query.filter(
                BusinessUnit.company_id == company_id
            ).all()
            
            for unit in business_units:
                # Check if unit name or functional area appears in data
                if (unit.name.lower() in data_str or 
                    (unit.functional_area and unit.functional_area.lower() in data_str)):
                    return unit.id
            
            return None
            
        except Exception as e:
            print(f"Error identifying business unit: {e}")
            return None
    
    def _identify_reporting_period(self, data: Dict) -> Optional[str]:
        """Identify the reporting period from data"""
        try:
            data_str = json.dumps(data).lower()
            
            # Look for time period indicators
            period_patterns = [
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
                r'q[1-4]\s+(\d{4})',
                r'(\d{1,2})/(\d{4})',
                r'(\d{4})-(\d{2})',
                r'week\s+of\s+(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in period_patterns:
                matches = re.findall(pattern, data_str)
                if matches:
                    return str(matches[0])
            
            return None
            
        except Exception as e:
            print(f"Error identifying reporting period: {e}")
            return None

class ConfidenceScorer:
    """Calculates confidence scores for normalized data"""
    
    def calculate_confidence(self, raw_data: Dict, normalized_metrics: Dict, 
                           entry: RawDataEntry) -> float:
        """Calculate confidence score for normalized data"""
        try:
            score = 1.0
            
            # Factor 1: Data source reliability
            data_source = DataSource.query.get(entry.source_id)
            if data_source:
                source_reliability = data_source.reliability_score or 1.0
                score *= source_reliability
            
            # Factor 2: Data completeness
            completeness_score = self._calculate_completeness_score(normalized_metrics)
            score *= completeness_score
            
            # Factor 3: Data consistency
            consistency_score = self._calculate_consistency_score(raw_data, normalized_metrics)
            score *= consistency_score
            
            # Factor 4: Data freshness
            freshness_score = self._calculate_freshness_score(entry)
            score *= freshness_score
            
            # Factor 5: Validation score
            validation_score = self._calculate_validation_score(normalized_metrics)
            score *= validation_score
            
            return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
            
        except Exception as e:
            print(f"Error calculating confidence score: {e}")
            return 0.5  # Default moderate confidence
    
    def _calculate_completeness_score(self, metrics: Dict) -> float:
        """Calculate score based on data completeness"""
        if not metrics:
            return 0.0
        
        # More metrics generally means higher confidence
        metric_count = len(metrics)
        
        if metric_count >= 10:
            return 1.0
        elif metric_count >= 5:
            return 0.8
        elif metric_count >= 3:
            return 0.6
        elif metric_count >= 1:
            return 0.4
        else:
            return 0.0
    
    def _calculate_consistency_score(self, raw_data: Dict, metrics: Dict) -> float:
        """Calculate score based on data consistency"""
        try:
            # Check if extracted metrics are reasonable
            score = 1.0
            
            # Check for negative values where they shouldn't be
            negative_check_fields = ['revenue', 'arr', 'mrr', 'users', 'customers']
            for field in negative_check_fields:
                if field in metrics and metrics[field] < 0:
                    score *= 0.5
            
            # Check for percentage values in reasonable ranges
            percentage_fields = ['churn_rate', 'retention_rate', 'conversion_rate', 'gross_margin']
            for field in percentage_fields:
                if field in metrics:
                    value = metrics[field]
                    if value < 0 or value > 1:
                        score *= 0.7
            
            return score
            
        except Exception as e:
            print(f"Error calculating consistency score: {e}")
            return 0.8
    
    def _calculate_freshness_score(self, entry: RawDataEntry) -> float:
        """Calculate score based on data freshness"""
        try:
            if not entry.source_timestamp:
                return 0.7  # No timestamp, moderate confidence
            
            age = datetime.utcnow() - entry.source_timestamp
            age_days = age.total_seconds() / (24 * 3600)
            
            if age_days <= 1:
                return 1.0
            elif age_days <= 7:
                return 0.9
            elif age_days <= 30:
                return 0.8
            elif age_days <= 90:
                return 0.6
            else:
                return 0.4
                
        except Exception as e:
            print(f"Error calculating freshness score: {e}")
            return 0.7
    
    def _calculate_validation_score(self, metrics: Dict) -> float:
        """Calculate score based on metric validation"""
        try:
            score = 1.0
            
            # Check for common business logic validations
            
            # LTV should be greater than CAC
            if 'ltv' in metrics and 'cac' in metrics:
                if metrics['ltv'] <= metrics['cac']:
                    score *= 0.7
            
            # Retention rate + churn rate should approximately equal 1
            if 'retention_rate' in metrics and 'churn_rate' in metrics:
                total = metrics['retention_rate'] + metrics['churn_rate']
                if abs(total - 1.0) > 0.1:
                    score *= 0.8
            
            # ARR should be approximately MRR * 12
            if 'arr' in metrics and 'mrr' in metrics:
                expected_arr = metrics['mrr'] * 12
                if abs(metrics['arr'] - expected_arr) / expected_arr > 0.2:
                    score *= 0.8
            
            return score
            
        except Exception as e:
            print(f"Error calculating validation score: {e}")
            return 0.9

# Utility functions for external use

def process_pending_data(batch_size: int = 100) -> Dict[str, int]:
    """Process pending raw data entries"""
    engine = DataNormalizationEngine()
    return engine.process_raw_data_batch(batch_size)

def normalize_single_entry(entry_id: str) -> bool:
    """Normalize a single raw data entry"""
    try:
        entry = RawDataEntry.query.get(entry_id)
        if not entry:
            return False
        
        engine = DataNormalizationEngine()
        return engine.process_raw_data_entry(entry)
        
    except Exception as e:
        print(f"Error normalizing entry {entry_id}: {e}")
        return False

