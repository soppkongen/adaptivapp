"""
Granular Confidence Scoring and Data Lineage Service

This service provides comprehensive tracking of data transformations and
granular confidence scoring at every step of the data processing pipeline.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app

from ..models.confidence_lineage import (
    DataLineage, ConfidenceScore, ConfidenceFactor, LineageGraph,
    ConfidenceThreshold, ConfidenceAlert, ConfidenceFactorType,
    LineageEventType, db
)

logger = logging.getLogger(__name__)

class ConfidenceLineageService:
    """
    Service for managing confidence scoring and data lineage tracking
    """
    
    def __init__(self):
        self.default_confidence_weights = {
            ConfidenceFactorType.DATA_QUALITY: 0.25,
            ConfidenceFactorType.SOURCE_RELIABILITY: 0.20,
            ConfidenceFactorType.TRANSFORMATION_ACCURACY: 0.20,
            ConfidenceFactorType.TEMPLATE_SPECIFICITY: 0.15,
            ConfidenceFactorType.VALIDATION_CONSENSUS: 0.10,
            ConfidenceFactorType.HISTORICAL_PERFORMANCE: 0.05,
            ConfidenceFactorType.HUMAN_VERIFICATION: 0.03,
            ConfidenceFactorType.CROSS_VALIDATION: 0.02
        }
    
    def create_lineage_event(self, event_type: LineageEventType, 
                           transformation_method: str,
                           system_component: str,
                           source_data_id: Optional[str] = None,
                           source_data_type: Optional[str] = None,
                           output_data_id: Optional[str] = None,
                           output_data_type: Optional[str] = None,
                           transformation_parameters: Optional[Dict] = None,
                           parent_lineage_id: Optional[str] = None,
                           company_id: Optional[int] = None,
                           user_id: Optional[int] = None,
                           processing_time_ms: Optional[int] = None,
                           error_details: Optional[Dict] = None) -> str:
        """
        Create a new data lineage event
        
        Returns:
            lineage_id: Unique identifier for the lineage event
        """
        try:
            lineage = DataLineage(
                event_type=event_type,
                transformation_method=transformation_method,
                system_component=system_component,
                source_data_id=source_data_id,
                source_data_type=source_data_type,
                output_data_id=output_data_id,
                output_data_type=output_data_type,
                transformation_parameters=json.dumps(transformation_parameters) if transformation_parameters else None,
                parent_lineage_id=parent_lineage_id,
                company_id=company_id,
                user_id=user_id,
                processing_time_ms=processing_time_ms,
                error_details=json.dumps(error_details) if error_details else None,
                transformation_confidence=0.0  # Will be calculated separately
            )
            
            db.session.add(lineage)
            db.session.commit()
            
            logger.info(f"Created lineage event {lineage.lineage_id} for {transformation_method}")
            return lineage.lineage_id
            
        except Exception as e:
            logger.error(f"Error creating lineage event: {str(e)}")
            db.session.rollback()
            raise
    
    def calculate_confidence_score(self, lineage_id: str,
                                 data_point_id: str,
                                 data_point_type: str,
                                 metric_name: Optional[str] = None,
                                 confidence_factors: Optional[Dict] = None,
                                 company_id: Optional[int] = None) -> str:
        """
        Calculate granular confidence score for a data point
        
        Returns:
            score_id: Unique identifier for the confidence score
        """
        try:
            # Get or calculate confidence factors
            if confidence_factors is None:
                confidence_factors = self._calculate_confidence_factors(
                    lineage_id, data_point_id, data_point_type, company_id
                )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(confidence_factors)
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(overall_confidence, company_id)
            
            # Create confidence score record
            confidence_score = ConfidenceScore(
                lineage_id=lineage_id,
                data_point_id=data_point_id,
                data_point_type=data_point_type,
                metric_name=metric_name,
                overall_confidence=overall_confidence,
                confidence_level=confidence_level,
                confidence_factors=json.dumps(confidence_factors),
                calculation_method="granular_weighted_average",
                company_id=company_id
            )
            
            db.session.add(confidence_score)
            db.session.commit()
            
            # Create individual confidence factor records
            self._create_confidence_factor_records(confidence_score.score_id, confidence_factors)
            
            # Check for confidence alerts
            self._check_confidence_alerts(confidence_score)
            
            logger.info(f"Calculated confidence score {confidence_score.score_id} = {overall_confidence:.3f}")
            return confidence_score.score_id
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            db.session.rollback()
            raise
    
    def _calculate_confidence_factors(self, lineage_id: str, data_point_id: str,
                                    data_point_type: str, company_id: Optional[int]) -> Dict:
        """
        Calculate individual confidence factors
        """
        try:
            factors = {}
            
            # Get lineage event
            lineage = DataLineage.query.filter_by(lineage_id=lineage_id).first()
            if not lineage:
                raise ValueError(f"Lineage event {lineage_id} not found")
            
            # Data Quality Factor
            factors[ConfidenceFactorType.DATA_QUALITY.value] = self._calculate_data_quality_factor(
                lineage, data_point_id
            )
            
            # Source Reliability Factor
            factors[ConfidenceFactorType.SOURCE_RELIABILITY.value] = self._calculate_source_reliability_factor(
                lineage, company_id
            )
            
            # Transformation Accuracy Factor
            factors[ConfidenceFactorType.TRANSFORMATION_ACCURACY.value] = self._calculate_transformation_accuracy_factor(
                lineage
            )
            
            # Template Specificity Factor (if applicable)
            factors[ConfidenceFactorType.TEMPLATE_SPECIFICITY.value] = self._calculate_template_specificity_factor(
                lineage, data_point_type
            )
            
            # Validation Consensus Factor
            factors[ConfidenceFactorType.VALIDATION_CONSENSUS.value] = self._calculate_validation_consensus_factor(
                data_point_id, company_id
            )
            
            # Historical Performance Factor
            factors[ConfidenceFactorType.HISTORICAL_PERFORMANCE.value] = self._calculate_historical_performance_factor(
                lineage.transformation_method, company_id
            )
            
            # Human Verification Factor
            factors[ConfidenceFactorType.HUMAN_VERIFICATION.value] = self._calculate_human_verification_factor(
                data_point_id, company_id
            )
            
            # Cross Validation Factor
            factors[ConfidenceFactorType.CROSS_VALIDATION.value] = self._calculate_cross_validation_factor(
                data_point_id, data_point_type, company_id
            )
            
            return factors
            
        except Exception as e:
            logger.error(f"Error calculating confidence factors: {str(e)}")
            # Return default factors if calculation fails
            return {factor_type.value: {'score': 0.5, 'weight': weight, 'evidence': {}} 
                   for factor_type, weight in self.default_confidence_weights.items()}
    
    def _calculate_data_quality_factor(self, lineage: DataLineage, data_point_id: str) -> Dict:
        """
        Calculate data quality confidence factor
        """
        try:
            score = 0.8  # Default score
            evidence = {}
            
            # Check for data completeness
            if lineage.source_data_id:
                # Analyze source data quality
                completeness_score = self._analyze_data_completeness(lineage.source_data_id)
                score *= completeness_score
                evidence['completeness_score'] = completeness_score
            
            # Check for data consistency
            consistency_score = self._analyze_data_consistency(data_point_id)
            score *= consistency_score
            evidence['consistency_score'] = consistency_score
            
            # Check for data freshness
            freshness_score = self._analyze_data_freshness(lineage.event_timestamp)
            score *= freshness_score
            evidence['freshness_score'] = freshness_score
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.DATA_QUALITY],
                'evidence': evidence,
                'description': 'Data quality assessment based on completeness, consistency, and freshness'
            }
            
        except Exception as e:
            logger.error(f"Error calculating data quality factor: {str(e)}")
            return {
                'score': 0.5,
                'weight': self.default_confidence_weights[ConfidenceFactorType.DATA_QUALITY],
                'evidence': {'error': str(e)},
                'description': 'Data quality assessment failed'
            }
    
    def _calculate_source_reliability_factor(self, lineage: DataLineage, company_id: Optional[int]) -> Dict:
        """
        Calculate source reliability confidence factor
        """
        try:
            score = 0.8  # Default score
            evidence = {}
            
            # Check source system reliability
            if lineage.system_component:
                reliability_score = self._get_system_reliability_score(lineage.system_component)
                score *= reliability_score
                evidence['system_reliability'] = reliability_score
            
            # Check historical source performance
            if company_id:
                historical_score = self._get_source_historical_performance(lineage.system_component, company_id)
                score *= historical_score
                evidence['historical_performance'] = historical_score
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.SOURCE_RELIABILITY],
                'evidence': evidence,
                'description': 'Source system reliability and historical performance'
            }
            
        except Exception as e:
            logger.error(f"Error calculating source reliability factor: {str(e)}")
            return {
                'score': 0.7,
                'weight': self.default_confidence_weights[ConfidenceFactorType.SOURCE_RELIABILITY],
                'evidence': {'error': str(e)},
                'description': 'Source reliability assessment failed'
            }
    
    def _calculate_transformation_accuracy_factor(self, lineage: DataLineage) -> Dict:
        """
        Calculate transformation accuracy confidence factor
        """
        try:
            score = 0.9  # Default score for successful transformations
            evidence = {}
            
            # Check for transformation errors
            if lineage.error_details:
                score *= 0.3  # Significant penalty for errors
                evidence['has_errors'] = True
                evidence['error_details'] = json.loads(lineage.error_details)
            else:
                evidence['has_errors'] = False
            
            # Check processing time (longer times may indicate complexity/issues)
            if lineage.processing_time_ms:
                time_score = self._evaluate_processing_time(lineage.processing_time_ms, lineage.transformation_method)
                score *= time_score
                evidence['processing_time_score'] = time_score
                evidence['processing_time_ms'] = lineage.processing_time_ms
            
            # Check transformation method reliability
            method_score = self._get_transformation_method_reliability(lineage.transformation_method)
            score *= method_score
            evidence['method_reliability'] = method_score
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.TRANSFORMATION_ACCURACY],
                'evidence': evidence,
                'description': 'Transformation process accuracy and reliability'
            }
            
        except Exception as e:
            logger.error(f"Error calculating transformation accuracy factor: {str(e)}")
            return {
                'score': 0.6,
                'weight': self.default_confidence_weights[ConfidenceFactorType.TRANSFORMATION_ACCURACY],
                'evidence': {'error': str(e)},
                'description': 'Transformation accuracy assessment failed'
            }
    
    def _calculate_template_specificity_factor(self, lineage: DataLineage, data_point_type: str) -> Dict:
        """
        Calculate template specificity confidence factor
        """
        try:
            score = 0.7  # Default score
            evidence = {}
            
            # Check if template-based normalization was used
            if 'template' in lineage.transformation_method.lower():
                score = 0.9  # Higher confidence for template-based transformations
                evidence['uses_template'] = True
                
                # Check template specificity
                if lineage.transformation_parameters:
                    params = json.loads(lineage.transformation_parameters)
                    if 'template_id' in params:
                        template_score = self._get_template_specificity_score(params['template_id'], data_point_type)
                        score *= template_score
                        evidence['template_specificity'] = template_score
            else:
                evidence['uses_template'] = False
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.TEMPLATE_SPECIFICITY],
                'evidence': evidence,
                'description': 'Template specificity and applicability to data type'
            }
            
        except Exception as e:
            logger.error(f"Error calculating template specificity factor: {str(e)}")
            return {
                'score': 0.5,
                'weight': self.default_confidence_weights[ConfidenceFactorType.TEMPLATE_SPECIFICITY],
                'evidence': {'error': str(e)},
                'description': 'Template specificity assessment failed'
            }
    
    def _calculate_validation_consensus_factor(self, data_point_id: str, company_id: Optional[int]) -> Dict:
        """
        Calculate validation consensus confidence factor
        """
        try:
            score = 0.6  # Default score (no validation)
            evidence = {}
            
            # Check for human validation
            validation_results = self._get_validation_results(data_point_id, company_id)
            if validation_results:
                consensus_score = self._calculate_validation_consensus(validation_results)
                score = consensus_score
                evidence['validation_results'] = validation_results
                evidence['consensus_score'] = consensus_score
            else:
                evidence['has_validation'] = False
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.VALIDATION_CONSENSUS],
                'evidence': evidence,
                'description': 'Human validation consensus and agreement'
            }
            
        except Exception as e:
            logger.error(f"Error calculating validation consensus factor: {str(e)}")
            return {
                'score': 0.5,
                'weight': self.default_confidence_weights[ConfidenceFactorType.VALIDATION_CONSENSUS],
                'evidence': {'error': str(e)},
                'description': 'Validation consensus assessment failed'
            }
    
    def _calculate_historical_performance_factor(self, transformation_method: str, company_id: Optional[int]) -> Dict:
        """
        Calculate historical performance confidence factor
        """
        try:
            score = 0.7  # Default score
            evidence = {}
            
            # Get historical performance for this transformation method
            historical_data = self._get_transformation_historical_performance(transformation_method, company_id)
            if historical_data:
                score = historical_data['average_confidence']
                evidence['historical_data'] = historical_data
            else:
                evidence['has_historical_data'] = False
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.HISTORICAL_PERFORMANCE],
                'evidence': evidence,
                'description': 'Historical performance of transformation method'
            }
            
        except Exception as e:
            logger.error(f"Error calculating historical performance factor: {str(e)}")
            return {
                'score': 0.6,
                'weight': self.default_confidence_weights[ConfidenceFactorType.HISTORICAL_PERFORMANCE],
                'evidence': {'error': str(e)},
                'description': 'Historical performance assessment failed'
            }
    
    def _calculate_human_verification_factor(self, data_point_id: str, company_id: Optional[int]) -> Dict:
        """
        Calculate human verification confidence factor
        """
        try:
            score = 0.5  # Default score (no human verification)
            evidence = {}
            
            # Check for human verification
            verification_data = self._get_human_verification_data(data_point_id, company_id)
            if verification_data:
                score = 0.95  # High confidence for human-verified data
                evidence['verification_data'] = verification_data
            else:
                evidence['has_human_verification'] = False
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.HUMAN_VERIFICATION],
                'evidence': evidence,
                'description': 'Human verification and manual review status'
            }
            
        except Exception as e:
            logger.error(f"Error calculating human verification factor: {str(e)}")
            return {
                'score': 0.5,
                'weight': self.default_confidence_weights[ConfidenceFactorType.HUMAN_VERIFICATION],
                'evidence': {'error': str(e)},
                'description': 'Human verification assessment failed'
            }
    
    def _calculate_cross_validation_factor(self, data_point_id: str, data_point_type: str, company_id: Optional[int]) -> Dict:
        """
        Calculate cross validation confidence factor
        """
        try:
            score = 0.6  # Default score
            evidence = {}
            
            # Check for cross-validation with other data sources
            cross_validation_results = self._get_cross_validation_results(data_point_id, data_point_type, company_id)
            if cross_validation_results:
                score = cross_validation_results['agreement_score']
                evidence['cross_validation_results'] = cross_validation_results
            else:
                evidence['has_cross_validation'] = False
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'weight': self.default_confidence_weights[ConfidenceFactorType.CROSS_VALIDATION],
                'evidence': evidence,
                'description': 'Cross-validation with other data sources'
            }
            
        except Exception as e:
            logger.error(f"Error calculating cross validation factor: {str(e)}")
            return {
                'score': 0.5,
                'weight': self.default_confidence_weights[ConfidenceFactorType.CROSS_VALIDATION],
                'evidence': {'error': str(e)},
                'description': 'Cross validation assessment failed'
            }
    
    def _calculate_overall_confidence(self, confidence_factors: Dict) -> float:
        """
        Calculate overall confidence score from individual factors
        """
        try:
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for factor_type, factor_data in confidence_factors.items():
                if isinstance(factor_data, dict) and 'score' in factor_data and 'weight' in factor_data:
                    score = factor_data['score']
                    weight = factor_data['weight']
                    total_weighted_score += score * weight
                    total_weight += weight
            
            if total_weight > 0:
                overall_confidence = total_weighted_score / total_weight
            else:
                overall_confidence = 0.5  # Default if no factors
            
            return min(max(overall_confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {str(e)}")
            return 0.5
    
    def _determine_confidence_level(self, confidence_score: float, company_id: Optional[int]) -> str:
        """
        Determine confidence level based on score and thresholds
        """
        try:
            # Get company-specific thresholds or use defaults
            thresholds = self._get_confidence_thresholds(company_id)
            
            if confidence_score >= thresholds['high']:
                return 'high'
            elif confidence_score >= thresholds['medium']:
                return 'medium'
            elif confidence_score >= thresholds['low']:
                return 'low'
            else:
                return 'critical'
                
        except Exception as e:
            logger.error(f"Error determining confidence level: {str(e)}")
            return 'medium'
    
    def _get_confidence_thresholds(self, company_id: Optional[int]) -> Dict:
        """
        Get confidence thresholds for a company
        """
        try:
            if company_id:
                threshold = ConfidenceThreshold.query.filter_by(
                    company_id=company_id,
                    is_active=True
                ).first()
                
                if threshold:
                    return {
                        'critical': threshold.critical_threshold,
                        'low': threshold.low_threshold,
                        'medium': threshold.medium_threshold,
                        'high': threshold.high_threshold
                    }
            
            # Default thresholds
            return {
                'critical': 0.3,
                'low': 0.5,
                'medium': 0.7,
                'high': 0.85
            }
            
        except Exception as e:
            logger.error(f"Error getting confidence thresholds: {str(e)}")
            return {'critical': 0.3, 'low': 0.5, 'medium': 0.7, 'high': 0.85}
    
    def _create_confidence_factor_records(self, confidence_score_id: str, confidence_factors: Dict):
        """
        Create individual confidence factor records
        """
        try:
            for factor_type_str, factor_data in confidence_factors.items():
                if isinstance(factor_data, dict):
                    factor_type = ConfidenceFactorType(factor_type_str)
                    
                    factor = ConfidenceFactor(
                        confidence_score_id=confidence_score_id,
                        factor_type=factor_type,
                        factor_name=factor_data.get('description', factor_type_str),
                        factor_description=factor_data.get('description', ''),
                        factor_score=factor_data.get('score', 0.5),
                        factor_weight=factor_data.get('weight', 0.1),
                        weighted_contribution=factor_data.get('score', 0.5) * factor_data.get('weight', 0.1),
                        evidence_data=json.dumps(factor_data.get('evidence', {})),
                        calculation_details=json.dumps(factor_data)
                    )
                    
                    db.session.add(factor)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating confidence factor records: {str(e)}")
            db.session.rollback()
    
    def _check_confidence_alerts(self, confidence_score: ConfidenceScore):
        """
        Check if confidence score triggers any alerts
        """
        try:
            # Get applicable thresholds
            thresholds = ConfidenceThreshold.query.filter(
                db.or_(
                    ConfidenceThreshold.company_id == confidence_score.company_id,
                    ConfidenceThreshold.company_id.is_(None)
                ),
                ConfidenceThreshold.is_active == True
            ).all()
            
            for threshold in thresholds:
                alert_level = None
                recommended_action = None
                
                if confidence_score.overall_confidence <= threshold.critical_threshold:
                    alert_level = 'critical'
                    recommended_action = threshold.critical_action
                elif confidence_score.overall_confidence <= threshold.low_threshold:
                    alert_level = 'low'
                    recommended_action = threshold.low_action
                elif confidence_score.overall_confidence <= threshold.medium_threshold:
                    alert_level = 'medium'
                    recommended_action = threshold.medium_action
                
                if alert_level:
                    alert = ConfidenceAlert(
                        confidence_score_id=confidence_score.score_id,
                        threshold_id=threshold.id,
                        alert_level=alert_level,
                        alert_message=f"Confidence score {confidence_score.overall_confidence:.3f} is below {alert_level} threshold",
                        recommended_action=recommended_action,
                        company_id=confidence_score.company_id
                    )
                    
                    db.session.add(alert)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error checking confidence alerts: {str(e)}")
            db.session.rollback()
    
    # Helper methods for factor calculations (simplified implementations)
    
    def _analyze_data_completeness(self, source_data_id: str) -> float:
        """Analyze data completeness - simplified implementation"""
        return 0.9  # Placeholder
    
    def _analyze_data_consistency(self, data_point_id: str) -> float:
        """Analyze data consistency - simplified implementation"""
        return 0.85  # Placeholder
    
    def _analyze_data_freshness(self, timestamp: datetime) -> float:
        """Analyze data freshness - simplified implementation"""
        age_hours = (datetime.utcnow() - timestamp).total_seconds() / 3600
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.9
        elif age_hours < 168:  # 1 week
            return 0.7
        else:
            return 0.5
    
    def _get_system_reliability_score(self, system_component: str) -> float:
        """Get system reliability score - simplified implementation"""
        reliability_scores = {
            'wordsmimir_api': 0.95,
            'template_normalization': 0.9,
            'file_processing': 0.85,
            'email_processing': 0.8,
            'webhook_ingestion': 0.9
        }
        return reliability_scores.get(system_component, 0.7)
    
    def _get_source_historical_performance(self, system_component: str, company_id: Optional[int]) -> float:
        """Get source historical performance - simplified implementation"""
        return 0.8  # Placeholder
    
    def _evaluate_processing_time(self, processing_time_ms: int, transformation_method: str) -> float:
        """Evaluate processing time - simplified implementation"""
        if processing_time_ms < 1000:  # < 1 second
            return 1.0
        elif processing_time_ms < 5000:  # < 5 seconds
            return 0.9
        elif processing_time_ms < 30000:  # < 30 seconds
            return 0.7
        else:
            return 0.5
    
    def _get_transformation_method_reliability(self, transformation_method: str) -> float:
        """Get transformation method reliability - simplified implementation"""
        method_scores = {
            'template_saas': 0.95,
            'template_ecommerce': 0.9,
            'template_fintech': 0.9,
            'basic_normalization': 0.6,
            'manual_entry': 0.8
        }
        return method_scores.get(transformation_method, 0.7)
    
    def _get_template_specificity_score(self, template_id: str, data_point_type: str) -> float:
        """Get template specificity score - simplified implementation"""
        return 0.9  # Placeholder
    
    def _get_validation_results(self, data_point_id: str, company_id: Optional[int]) -> Optional[Dict]:
        """Get validation results - simplified implementation"""
        return None  # Placeholder
    
    def _calculate_validation_consensus(self, validation_results: Dict) -> float:
        """Calculate validation consensus - simplified implementation"""
        return 0.9  # Placeholder
    
    def _get_transformation_historical_performance(self, transformation_method: str, company_id: Optional[int]) -> Optional[Dict]:
        """Get transformation historical performance - simplified implementation"""
        return None  # Placeholder
    
    def _get_human_verification_data(self, data_point_id: str, company_id: Optional[int]) -> Optional[Dict]:
        """Get human verification data - simplified implementation"""
        return None  # Placeholder
    
    def _get_cross_validation_results(self, data_point_id: str, data_point_type: str, company_id: Optional[int]) -> Optional[Dict]:
        """Get cross validation results - simplified implementation"""
        return None  # Placeholder

# Global service instance
confidence_lineage_service = ConfidenceLineageService()

