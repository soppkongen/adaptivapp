"""
Enhanced Template-Based Normalization Engine

This service implements specialized normalization using business model templates,
breaking down the complex challenge of universal normalization into manageable,
business-type-specific problems.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app

from ..models.business_templates import (
    BusinessModelTemplate, MetricDefinition, CompanyTemplate, 
    NormalizationResult, TemplatePerformance, BusinessModelType, 
    MetricCategory, db
)
from ..models.elite_command import Company, RawDataEntry
from ..services.hitl_validation import hitl_service

logger = logging.getLogger(__name__)

class TemplateNormalizationEngine:
    """
    Enhanced normalization engine using business model templates
    """
    
    def __init__(self):
        self.confidence_threshold = 0.85
        self.metric_cache = {}
        self.template_cache = {}
    
    def normalize_data(self, raw_data_entry: RawDataEntry, company_id: int) -> Dict:
        """
        Normalize data using appropriate business model template
        
        Args:
            raw_data_entry: Raw data entry to normalize
            company_id: Company ID for template selection
            
        Returns:
            Normalization result dictionary
        """
        try:
            start_time = datetime.utcnow()
            
            # Get company's business model template
            template = self._get_company_template(company_id)
            if not template:
                return self._fallback_normalization(raw_data_entry, company_id)
            
            # Parse raw data
            raw_data = json.loads(raw_data_entry.data) if isinstance(raw_data_entry.data, str) else raw_data_entry.data
            
            # Normalize using template
            normalization_results = []
            
            for metric_name, metric_value in raw_data.items():
                if self._should_normalize_metric(metric_name, template):
                    result = self._normalize_metric(
                        metric_name, metric_value, template, raw_data_entry, company_id
                    )
                    if result:
                        normalization_results.append(result)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(normalization_results)
            
            # Check if validation is needed
            if overall_confidence < self.confidence_threshold:
                self._queue_for_validation(raw_data_entry, normalization_results, overall_confidence)
            
            # Record performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._record_performance(template.id, len(normalization_results), processing_time)
            
            return {
                'template_id': template.id,
                'template_name': template.name,
                'business_model_type': template.business_model_type.value,
                'normalization_results': normalization_results,
                'overall_confidence': overall_confidence,
                'processing_time_ms': processing_time,
                'validation_required': overall_confidence < self.confidence_threshold
            }
            
        except Exception as e:
            logger.error(f"Error in template normalization: {str(e)}")
            return self._fallback_normalization(raw_data_entry, company_id)
    
    def _get_company_template(self, company_id: int) -> Optional[BusinessModelTemplate]:
        """
        Get the active business model template for a company
        """
        try:
            # Check cache first
            if company_id in self.template_cache:
                return self.template_cache[company_id]
            
            # Get from database
            company_template = CompanyTemplate.query.filter_by(
                company_id=company_id,
                is_active=True
            ).first()
            
            if company_template:
                template = company_template.template
                self.template_cache[company_id] = template
                return template
            
            # Auto-assign template based on company data
            return self._auto_assign_template(company_id)
            
        except Exception as e:
            logger.error(f"Error getting company template: {str(e)}")
            return None
    
    def _auto_assign_template(self, company_id: int) -> Optional[BusinessModelTemplate]:
        """
        Automatically assign a business model template based on company data
        """
        try:
            company = Company.query.get(company_id)
            if not company:
                return None
            
            # Simple heuristics for template assignment
            # This could be enhanced with ML models
            
            business_type = self._infer_business_type(company)
            
            # Get the best template for this business type
            template = BusinessModelTemplate.query.filter_by(
                business_model_type=business_type,
                is_active=True
            ).first()
            
            if template:
                # Create company template assignment
                company_template = CompanyTemplate(
                    company_id=company_id,
                    template_id=template.id,
                    assigned_by=1,  # System assignment
                    confidence_score=0.7  # Auto-assignment confidence
                )
                
                db.session.add(company_template)
                db.session.commit()
                
                self.template_cache[company_id] = template
                logger.info(f"Auto-assigned template {template.name} to company {company_id}")
                
                return template
            
            return None
            
        except Exception as e:
            logger.error(f"Error auto-assigning template: {str(e)}")
            return None
    
    def _infer_business_type(self, company: Company) -> BusinessModelType:
        """
        Infer business model type from company data
        """
        try:
            # Simple keyword-based inference
            # This could be enhanced with more sophisticated analysis
            
            company_name = (company.name or "").lower()
            company_description = (company.description or "").lower()
            
            text = f"{company_name} {company_description}"
            
            # SaaS indicators
            saas_keywords = ['software', 'saas', 'platform', 'api', 'cloud', 'subscription']
            if any(keyword in text for keyword in saas_keywords):
                return BusinessModelType.SAAS
            
            # E-commerce indicators
            ecommerce_keywords = ['ecommerce', 'retail', 'store', 'shop', 'marketplace']
            if any(keyword in text for keyword in ecommerce_keywords):
                return BusinessModelType.ECOMMERCE
            
            # Fintech indicators
            fintech_keywords = ['fintech', 'financial', 'payment', 'banking', 'crypto']
            if any(keyword in text for keyword in fintech_keywords):
                return BusinessModelType.FINTECH
            
            # Default to generic
            return BusinessModelType.GENERIC
            
        except Exception:
            return BusinessModelType.GENERIC
    
    def _should_normalize_metric(self, metric_name: str, template: BusinessModelTemplate) -> bool:
        """
        Determine if a metric should be normalized using the template
        """
        try:
            expected_metrics = json.loads(template.expected_metrics)
            metric_mappings = json.loads(template.metric_mappings)
            
            # Check if metric is in expected metrics
            if metric_name.lower() in [m.lower() for m in expected_metrics]:
                return True
            
            # Check if metric has a mapping
            for mapped_name in metric_mappings.keys():
                if metric_name.lower() == mapped_name.lower():
                    return True
            
            # Check for partial matches
            for expected_metric in expected_metrics:
                if self._is_metric_match(metric_name, expected_metric):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking metric normalization: {str(e)}")
            return False
    
    def _is_metric_match(self, metric_name: str, expected_metric: str) -> bool:
        """
        Check if metric names match using fuzzy matching
        """
        try:
            # Simple fuzzy matching - could be enhanced with more sophisticated algorithms
            metric_name_clean = re.sub(r'[^a-zA-Z0-9]', '', metric_name.lower())
            expected_metric_clean = re.sub(r'[^a-zA-Z0-9]', '', expected_metric.lower())
            
            # Exact match
            if metric_name_clean == expected_metric_clean:
                return True
            
            # Substring match
            if metric_name_clean in expected_metric_clean or expected_metric_clean in metric_name_clean:
                return True
            
            # Common abbreviations
            abbreviations = {
                'arr': 'annual_recurring_revenue',
                'mrr': 'monthly_recurring_revenue',
                'ltv': 'lifetime_value',
                'cac': 'customer_acquisition_cost',
                'arpu': 'average_revenue_per_user'
            }
            
            if metric_name_clean in abbreviations and abbreviations[metric_name_clean] in expected_metric_clean:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _normalize_metric(self, metric_name: str, metric_value: Any, 
                         template: BusinessModelTemplate, raw_data_entry: RawDataEntry,
                         company_id: int) -> Optional[Dict]:
        """
        Normalize a specific metric using template rules
        """
        try:
            # Get metric definition
            metric_definition = self._get_metric_definition(metric_name, template)
            if not metric_definition:
                return None
            
            # Apply normalization rules
            normalized_value, confidence_breakdown = self._apply_normalization_rules(
                metric_value, metric_definition, template
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_metric_confidence(
                metric_name, metric_value, normalized_value, confidence_breakdown
            )
            
            # Create normalization result
            result = NormalizationResult(
                raw_data_id=raw_data_entry.id,
                company_id=company_id,
                template_id=template.id,
                original_metric_name=metric_name,
                normalized_metric_code=metric_definition.metric_code,
                original_value=str(metric_value),
                normalized_value=json.dumps(normalized_value),
                normalization_method=f"template_{template.business_model_type.value}",
                confidence_score=confidence_score,
                confidence_breakdown=json.dumps(confidence_breakdown)
            )
            
            db.session.add(result)
            db.session.commit()
            
            return {
                'id': result.id,
                'original_metric_name': metric_name,
                'normalized_metric_code': metric_definition.metric_code,
                'original_value': metric_value,
                'normalized_value': normalized_value,
                'confidence_score': confidence_score,
                'confidence_breakdown': confidence_breakdown,
                'metric_definition': metric_definition.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error normalizing metric {metric_name}: {str(e)}")
            return None
    
    def _get_metric_definition(self, metric_name: str, template: BusinessModelTemplate) -> Optional[MetricDefinition]:
        """
        Get metric definition for normalization
        """
        try:
            # Check cache
            cache_key = f"{template.id}_{metric_name.lower()}"
            if cache_key in self.metric_cache:
                return self.metric_cache[cache_key]
            
            # Get metric mappings from template
            metric_mappings = json.loads(template.metric_mappings)
            
            # Find mapped metric code
            metric_code = None
            for mapped_name, code in metric_mappings.items():
                if self._is_metric_match(metric_name, mapped_name):
                    metric_code = code
                    break
            
            if not metric_code:
                return None
            
            # Get metric definition
            metric_definition = MetricDefinition.query.filter_by(metric_code=metric_code).first()
            
            if metric_definition:
                self.metric_cache[cache_key] = metric_definition
            
            return metric_definition
            
        except Exception as e:
            logger.error(f"Error getting metric definition: {str(e)}")
            return None
    
    def _apply_normalization_rules(self, metric_value: Any, metric_definition: MetricDefinition,
                                 template: BusinessModelTemplate) -> Tuple[Any, Dict]:
        """
        Apply normalization rules to convert metric value
        """
        try:
            confidence_breakdown = {
                'data_type_match': 1.0,
                'value_validation': 1.0,
                'conversion_accuracy': 1.0,
                'template_specificity': 0.9
            }
            
            # Get conversion rules
            conversion_rules = json.loads(metric_definition.conversion_rules) if metric_definition.conversion_rules else {}
            
            normalized_value = metric_value
            
            # Apply data type conversion
            if metric_definition.data_type == 'currency':
                normalized_value = self._normalize_currency(metric_value, conversion_rules)
            elif metric_definition.data_type == 'percentage':
                normalized_value = self._normalize_percentage(metric_value, conversion_rules)
            elif metric_definition.data_type == 'count':
                normalized_value = self._normalize_count(metric_value, conversion_rules)
            elif metric_definition.data_type == 'ratio':
                normalized_value = self._normalize_ratio(metric_value, conversion_rules)
            
            # Validate normalized value
            if not self._validate_normalized_value(normalized_value, metric_definition):
                confidence_breakdown['value_validation'] = 0.5
            
            return normalized_value, confidence_breakdown
            
        except Exception as e:
            logger.error(f"Error applying normalization rules: {str(e)}")
            return metric_value, {'error': 1.0, 'conversion_accuracy': 0.0}
    
    def _normalize_currency(self, value: Any, conversion_rules: Dict) -> float:
        """
        Normalize currency values
        """
        try:
            # Convert to float
            if isinstance(value, str):
                # Remove currency symbols and commas
                clean_value = re.sub(r'[^\d.-]', '', value)
                numeric_value = float(clean_value)
            else:
                numeric_value = float(value)
            
            # Apply currency conversion if needed
            if 'currency_conversion' in conversion_rules:
                conversion_rate = conversion_rules['currency_conversion'].get('rate', 1.0)
                numeric_value *= conversion_rate
            
            # Apply unit conversion (e.g., cents to dollars)
            if 'unit_conversion' in conversion_rules:
                unit_factor = conversion_rules['unit_conversion'].get('factor', 1.0)
                numeric_value *= unit_factor
            
            return round(numeric_value, 2)
            
        except Exception as e:
            logger.error(f"Error normalizing currency: {str(e)}")
            return 0.0
    
    def _normalize_percentage(self, value: Any, conversion_rules: Dict) -> float:
        """
        Normalize percentage values
        """
        try:
            if isinstance(value, str):
                # Remove percentage symbol
                clean_value = value.replace('%', '').strip()
                numeric_value = float(clean_value)
            else:
                numeric_value = float(value)
            
            # Convert to decimal if needed
            if numeric_value > 1.0 and 'convert_to_decimal' in conversion_rules:
                numeric_value /= 100.0
            
            return round(numeric_value, 4)
            
        except Exception as e:
            logger.error(f"Error normalizing percentage: {str(e)}")
            return 0.0
    
    def _normalize_count(self, value: Any, conversion_rules: Dict) -> int:
        """
        Normalize count values
        """
        try:
            if isinstance(value, str):
                # Remove commas and other formatting
                clean_value = re.sub(r'[^\d]', '', value)
                numeric_value = int(clean_value)
            else:
                numeric_value = int(float(value))
            
            return numeric_value
            
        except Exception as e:
            logger.error(f"Error normalizing count: {str(e)}")
            return 0
    
    def _normalize_ratio(self, value: Any, conversion_rules: Dict) -> float:
        """
        Normalize ratio values
        """
        try:
            if isinstance(value, str):
                # Handle ratio formats like "3:1" or "3.5"
                if ':' in value:
                    parts = value.split(':')
                    if len(parts) == 2:
                        numerator = float(parts[0])
                        denominator = float(parts[1])
                        numeric_value = numerator / denominator if denominator != 0 else 0
                    else:
                        numeric_value = float(value)
                else:
                    numeric_value = float(value)
            else:
                numeric_value = float(value)
            
            return round(numeric_value, 4)
            
        except Exception as e:
            logger.error(f"Error normalizing ratio: {str(e)}")
            return 0.0
    
    def _validate_normalized_value(self, value: Any, metric_definition: MetricDefinition) -> bool:
        """
        Validate normalized value against constraints
        """
        try:
            if not metric_definition.validation_constraints:
                return True
            
            constraints = json.loads(metric_definition.validation_constraints)
            
            # Check minimum value
            if 'min_value' in constraints and value < constraints['min_value']:
                return False
            
            # Check maximum value
            if 'max_value' in constraints and value > constraints['max_value']:
                return False
            
            # Check data type
            if 'required_type' in constraints:
                required_type = constraints['required_type']
                if required_type == 'positive' and value < 0:
                    return False
                elif required_type == 'integer' and not isinstance(value, int):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating normalized value: {str(e)}")
            return False
    
    def _calculate_metric_confidence(self, metric_name: str, original_value: Any,
                                   normalized_value: Any, confidence_breakdown: Dict) -> float:
        """
        Calculate confidence score for metric normalization
        """
        try:
            # Base confidence from breakdown
            base_confidence = sum(confidence_breakdown.values()) / len(confidence_breakdown)
            
            # Adjust based on value consistency
            consistency_score = 1.0
            if isinstance(original_value, (int, float)) and isinstance(normalized_value, (int, float)):
                # Check if values are in reasonable range
                if original_value != 0:
                    ratio = abs(normalized_value / original_value)
                    if ratio > 1000 or ratio < 0.001:  # Extreme conversion
                        consistency_score = 0.5
            
            # Adjust based on metric name clarity
            name_clarity_score = 1.0
            if len(metric_name) < 3 or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', metric_name):
                name_clarity_score = 0.8
            
            final_confidence = base_confidence * consistency_score * name_clarity_score
            return min(max(final_confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating metric confidence: {str(e)}")
            return 0.5
    
    def _calculate_overall_confidence(self, normalization_results: List[Dict]) -> float:
        """
        Calculate overall confidence for all normalized metrics
        """
        try:
            if not normalization_results:
                return 0.0
            
            confidence_scores = [result['confidence_score'] for result in normalization_results]
            return sum(confidence_scores) / len(confidence_scores)
            
        except Exception:
            return 0.0
    
    def _queue_for_validation(self, raw_data_entry: RawDataEntry, 
                            normalization_results: List[Dict], confidence: float):
        """
        Queue low-confidence normalization for human validation
        """
        try:
            validation_data = {
                'raw_data_id': raw_data_entry.id,
                'normalization_results': normalization_results,
                'overall_confidence': confidence
            }
            
            hitl_service.queue_for_validation(
                data_type='normalization',
                source_data_id=str(raw_data_entry.id),
                original_data=json.loads(raw_data_entry.data) if isinstance(raw_data_entry.data, str) else raw_data_entry.data,
                normalized_data=validation_data,
                confidence_score=confidence,
                company_id=raw_data_entry.company_id
            )
            
        except Exception as e:
            logger.error(f"Error queuing for validation: {str(e)}")
    
    def _record_performance(self, template_id: int, result_count: int, processing_time: float):
        """
        Record template performance metrics
        """
        try:
            today = datetime.utcnow().date()
            
            # Get or create performance record
            performance = TemplatePerformance.query.filter_by(
                template_id=template_id,
                date=today
            ).first()
            
            if not performance:
                performance = TemplatePerformance(
                    template_id=template_id,
                    date=today
                )
                db.session.add(performance)
            
            # Update metrics
            performance.total_normalizations += 1
            performance.successful_normalizations += 1 if result_count > 0 else 0
            performance.failed_normalizations += 1 if result_count == 0 else 0
            
            # Update average processing time
            if performance.average_processing_time_ms:
                performance.average_processing_time_ms = (
                    performance.average_processing_time_ms + processing_time
                ) / 2
            else:
                performance.average_processing_time_ms = processing_time
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error recording performance: {str(e)}")
    
    def _fallback_normalization(self, raw_data_entry: RawDataEntry, company_id: int) -> Dict:
        """
        Fallback normalization when no template is available
        """
        try:
            # Basic normalization without template
            raw_data = json.loads(raw_data_entry.data) if isinstance(raw_data_entry.data, str) else raw_data_entry.data
            
            basic_results = []
            for metric_name, metric_value in raw_data.items():
                basic_results.append({
                    'original_metric_name': metric_name,
                    'normalized_metric_code': metric_name.lower().replace(' ', '_'),
                    'original_value': metric_value,
                    'normalized_value': metric_value,
                    'confidence_score': 0.3,  # Low confidence for basic normalization
                    'confidence_breakdown': {'basic_normalization': 0.3}
                })
            
            return {
                'template_id': None,
                'template_name': 'Generic Fallback',
                'business_model_type': 'generic',
                'normalization_results': basic_results,
                'overall_confidence': 0.3,
                'processing_time_ms': 10,
                'validation_required': True
            }
            
        except Exception as e:
            logger.error(f"Error in fallback normalization: {str(e)}")
            return {
                'error': str(e),
                'validation_required': True
            }

# Global service instance
template_normalization_engine = TemplateNormalizationEngine()

