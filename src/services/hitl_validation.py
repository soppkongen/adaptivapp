"""
Human-in-the-Loop Validation Service

This service implements the HITL validation system that routes low-confidence data
to human reviewers, creating a feedback loop that improves system accuracy over time.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app

from ..models.validation import (
    ValidationQueue, ValidationRule, ValidationFeedback, ValidationMetrics,
    ValidationStatus, ValidationPriority, db
)
from ..models.elite_command import Company, RawDataEntry

logger = logging.getLogger(__name__)

class HITLValidationService:
    """
    Human-in-the-Loop validation service for managing data quality and trust
    """
    
    def __init__(self):
        self.default_confidence_threshold = 0.85
        self.priority_thresholds = {
            ValidationPriority.CRITICAL: 0.3,
            ValidationPriority.HIGH: 0.5,
            ValidationPriority.MEDIUM: 0.7,
            ValidationPriority.LOW: 0.85
        }
    
    def should_validate(self, data_type: str, confidence_score: float, 
                       additional_context: Dict = None) -> Tuple[bool, ValidationPriority]:
        """
        Determine if data should be sent to validation queue based on confidence score and rules
        
        Args:
            data_type: Type of data ('metric', 'entity', 'normalization')
            confidence_score: Confidence score from 0.0 to 1.0
            additional_context: Additional context for rule evaluation
            
        Returns:
            Tuple of (should_validate, priority)
        """
        try:
            # Get active validation rules for this data type
            rules = ValidationRule.query.filter_by(
                data_type=data_type,
                is_active=True
            ).all()
            
            # If no specific rules, use default threshold
            if not rules:
                if confidence_score < self.default_confidence_threshold:
                    priority = self._determine_priority(confidence_score)
                    return True, priority
                return False, None
            
            # Evaluate each rule
            for rule in rules:
                if self._evaluate_rule(rule, confidence_score, additional_context):
                    priority = self._determine_priority_from_rule(rule, confidence_score)
                    return True, priority
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error in should_validate: {str(e)}")
            # Default to validation on error for safety
            return True, ValidationPriority.MEDIUM
    
    def queue_for_validation(self, data_type: str, source_data_id: str,
                           original_data: Dict, normalized_data: Dict,
                           confidence_score: float, confidence_breakdown: Dict = None,
                           company_id: int = None, suggested_corrections: Dict = None) -> ValidationQueue:
        """
        Add data to validation queue
        
        Args:
            data_type: Type of data being validated
            source_data_id: ID of the source data
            original_data: Original raw data
            normalized_data: Normalized/processed data
            confidence_score: Overall confidence score
            confidence_breakdown: Detailed confidence breakdown
            company_id: Associated company ID
            suggested_corrections: AI-suggested corrections
            
        Returns:
            ValidationQueue item
        """
        try:
            # Determine priority
            _, priority = self.should_validate(data_type, confidence_score)
            if priority is None:
                priority = self._determine_priority(confidence_score)
            
            # Create validation queue item
            validation_item = ValidationQueue(
                data_type=data_type,
                source_data_id=source_data_id,
                company_id=company_id,
                confidence_score=confidence_score,
                confidence_threshold=self.default_confidence_threshold,
                priority=priority,
                original_data=json.dumps(original_data),
                normalized_data=json.dumps(normalized_data),
                suggested_corrections=json.dumps(suggested_corrections) if suggested_corrections else None,
                confidence_breakdown=json.dumps(confidence_breakdown) if confidence_breakdown else None
            )
            
            db.session.add(validation_item)
            db.session.commit()
            
            logger.info(f"Queued {data_type} data for validation: {source_data_id}")
            
            # Update metrics
            self._update_queue_metrics()
            
            return validation_item
            
        except Exception as e:
            logger.error(f"Error queuing data for validation: {str(e)}")
            db.session.rollback()
            raise
    
    def get_validation_queue(self, status: ValidationStatus = None, 
                           priority: ValidationPriority = None,
                           assigned_to: int = None, limit: int = 50) -> List[ValidationQueue]:
        """
        Get items from validation queue with optional filters
        """
        try:
            query = ValidationQueue.query
            
            if status:
                query = query.filter_by(status=status)
            if priority:
                query = query.filter_by(priority=priority)
            if assigned_to:
                query = query.filter_by(assigned_to=assigned_to)
            
            # Order by priority and creation time
            priority_order = {
                ValidationPriority.CRITICAL: 1,
                ValidationPriority.HIGH: 2,
                ValidationPriority.MEDIUM: 3,
                ValidationPriority.LOW: 4
            }
            
            items = query.order_by(
                db.case(priority_order, value=ValidationQueue.priority),
                ValidationQueue.created_at.asc()
            ).limit(limit).all()
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting validation queue: {str(e)}")
            return []
    
    def assign_validation(self, validation_id: int, user_id: int) -> bool:
        """
        Assign validation item to a user
        """
        try:
            validation_item = ValidationQueue.query.get(validation_id)
            if not validation_item:
                return False
            
            validation_item.assigned_to = user_id
            validation_item.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Assigned validation {validation_id} to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning validation: {str(e)}")
            db.session.rollback()
            return False
    
    def submit_validation_decision(self, validation_id: int, reviewer_id: int,
                                 status: ValidationStatus, feedback: str = None,
                                 corrected_data: Dict = None, correction_reason: str = None) -> bool:
        """
        Submit validation decision and feedback
        """
        try:
            validation_item = ValidationQueue.query.get(validation_id)
            if not validation_item:
                return False
            
            # Update validation item
            validation_item.status = status
            validation_item.reviewed_by = reviewer_id
            validation_item.reviewed_at = datetime.utcnow()
            validation_item.reviewer_feedback = feedback
            validation_item.corrected_data = json.dumps(corrected_data) if corrected_data else None
            validation_item.correction_reason = correction_reason
            validation_item.updated_at = datetime.utcnow()
            
            # Create feedback record for learning
            feedback_data = {
                'original_confidence': validation_item.confidence_score,
                'decision': status.value,
                'had_corrections': corrected_data is not None,
                'feedback_text': feedback
            }
            
            feedback_record = ValidationFeedback(
                validation_id=validation_id,
                feedback_type='decision',
                feedback_data=json.dumps(feedback_data),
                use_for_training=True
            )
            
            db.session.add(feedback_record)
            db.session.commit()
            
            logger.info(f"Validation decision submitted for {validation_id}: {status.value}")
            
            # Update metrics
            self._update_review_metrics()
            
            # If approved or corrected, apply the data
            if status in [ValidationStatus.APPROVED, ValidationStatus.NEEDS_CORRECTION]:
                self._apply_validated_data(validation_item, corrected_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting validation decision: {str(e)}")
            db.session.rollback()
            return False
    
    def get_validation_metrics(self, days: int = 30) -> Dict:
        """
        Get validation system performance metrics
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get recent metrics
            metrics = ValidationMetrics.query.filter(
                ValidationMetrics.date >= start_date,
                ValidationMetrics.date <= end_date
            ).all()
            
            if not metrics:
                return self._calculate_current_metrics()
            
            # Aggregate metrics
            total_queued = sum(m.total_items_queued for m in metrics)
            total_reviewed = sum(m.total_items_reviewed for m in metrics)
            total_approved = sum(m.total_items_approved for m in metrics)
            total_rejected = sum(m.total_items_rejected for m in metrics)
            total_corrected = sum(m.total_items_corrected for m in metrics)
            
            avg_review_time = sum(m.average_review_time_minutes or 0 for m in metrics) / len(metrics)
            avg_accuracy = sum(m.accuracy_rate or 0 for m in metrics) / len(metrics)
            avg_confidence = sum(m.average_confidence_score or 0 for m in metrics) / len(metrics)
            
            return {
                'period_days': days,
                'total_items_queued': total_queued,
                'total_items_reviewed': total_reviewed,
                'total_items_approved': total_approved,
                'total_items_rejected': total_rejected,
                'total_items_corrected': total_corrected,
                'review_completion_rate': (total_reviewed / total_queued * 100) if total_queued > 0 else 0,
                'approval_rate': (total_approved / total_reviewed * 100) if total_reviewed > 0 else 0,
                'correction_rate': (total_corrected / total_reviewed * 100) if total_reviewed > 0 else 0,
                'average_review_time_minutes': avg_review_time,
                'average_accuracy_rate': avg_accuracy,
                'average_confidence_score': avg_confidence,
                'pending_items': self._get_pending_count()
            }
            
        except Exception as e:
            logger.error(f"Error getting validation metrics: {str(e)}")
            return {}
    
    def create_validation_rule(self, name: str, description: str, data_type: str,
                             confidence_threshold: float, conditions: Dict,
                             priority_mapping: Dict, created_by: int) -> ValidationRule:
        """
        Create a new validation rule
        """
        try:
            rule = ValidationRule(
                name=name,
                description=description,
                data_type=data_type,
                confidence_threshold=confidence_threshold,
                conditions=json.dumps(conditions),
                priority_mapping=json.dumps(priority_mapping),
                created_by=created_by
            )
            
            db.session.add(rule)
            db.session.commit()
            
            logger.info(f"Created validation rule: {name}")
            return rule
            
        except Exception as e:
            logger.error(f"Error creating validation rule: {str(e)}")
            db.session.rollback()
            raise
    
    def _determine_priority(self, confidence_score: float) -> ValidationPriority:
        """
        Determine validation priority based on confidence score
        """
        for priority, threshold in self.priority_thresholds.items():
            if confidence_score <= threshold:
                return priority
        return ValidationPriority.LOW
    
    def _determine_priority_from_rule(self, rule: ValidationRule, confidence_score: float) -> ValidationPriority:
        """
        Determine priority based on rule's priority mapping
        """
        try:
            priority_mapping = json.loads(rule.priority_mapping)
            
            for priority_name, threshold in priority_mapping.items():
                if confidence_score <= threshold:
                    return ValidationPriority(priority_name)
            
            return ValidationPriority.LOW
            
        except Exception:
            return self._determine_priority(confidence_score)
    
    def _evaluate_rule(self, rule: ValidationRule, confidence_score: float, 
                      additional_context: Dict = None) -> bool:
        """
        Evaluate if a validation rule applies to the current data
        """
        try:
            # Check confidence threshold
            if confidence_score >= rule.confidence_threshold:
                return False
            
            # Evaluate additional conditions
            conditions = json.loads(rule.conditions)
            
            # Simple condition evaluation (can be extended)
            for condition_key, condition_value in conditions.items():
                if additional_context and condition_key in additional_context:
                    if additional_context[condition_key] != condition_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
            return False
    
    def _apply_validated_data(self, validation_item: ValidationQueue, corrected_data: Dict = None):
        """
        Apply validated data back to the system
        """
        try:
            # This would integrate with the normalization engine
            # to apply approved or corrected data
            
            data_to_apply = corrected_data if corrected_data else json.loads(validation_item.normalized_data)
            
            # Update the original data entry with validated data
            # Implementation depends on specific data type and storage
            
            logger.info(f"Applied validated data for {validation_item.source_data_id}")
            
        except Exception as e:
            logger.error(f"Error applying validated data: {str(e)}")
    
    def _update_queue_metrics(self):
        """
        Update daily queue metrics
        """
        try:
            today = datetime.utcnow().date()
            
            # Get or create today's metrics
            metrics = ValidationMetrics.query.filter_by(date=today).first()
            if not metrics:
                metrics = ValidationMetrics(date=today)
                db.session.add(metrics)
            
            # Update queue count
            metrics.total_items_queued += 1
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating queue metrics: {str(e)}")
    
    def _update_review_metrics(self):
        """
        Update daily review metrics
        """
        try:
            today = datetime.utcnow().date()
            
            # Get or create today's metrics
            metrics = ValidationMetrics.query.filter_by(date=today).first()
            if not metrics:
                metrics = ValidationMetrics(date=today)
                db.session.add(metrics)
            
            # Update review count
            metrics.total_items_reviewed += 1
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating review metrics: {str(e)}")
    
    def _calculate_current_metrics(self) -> Dict:
        """
        Calculate current metrics from database
        """
        try:
            total_queued = ValidationQueue.query.count()
            total_reviewed = ValidationQueue.query.filter(
                ValidationQueue.status != ValidationStatus.PENDING
            ).count()
            
            pending_count = ValidationQueue.query.filter_by(
                status=ValidationStatus.PENDING
            ).count()
            
            return {
                'total_items_queued': total_queued,
                'total_items_reviewed': total_reviewed,
                'pending_items': pending_count,
                'review_completion_rate': (total_reviewed / total_queued * 100) if total_queued > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating current metrics: {str(e)}")
            return {}
    
    def _get_pending_count(self) -> int:
        """
        Get count of pending validation items
        """
        try:
            return ValidationQueue.query.filter_by(status=ValidationStatus.PENDING).count()
        except Exception:
            return 0

# Global service instance
hitl_service = HITLValidationService()

