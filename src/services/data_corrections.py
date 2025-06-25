"""
User-Driven Data Correction and Annotation Service

This service provides comprehensive functionality for user-driven data corrections,
annotations, and feedback management to improve data quality over time.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app

from ..models.corrections import (
    DataCorrection, DataAnnotation, CorrectionWorkflow, UserFeedback,
    CorrectionImpact, CorrectionType, CorrectionStatus, AnnotationType, db
)
from ..models.confidence_lineage import DataLineage, ConfidenceScore

logger = logging.getLogger(__name__)

class DataCorrectionService:
    """
    Service for managing user-driven data corrections and annotations
    """
    
    def __init__(self):
        self.default_workflows = {
            'high_impact': {
                'requires_approval': True,
                'auto_approve_threshold': None,
                'implementation_delay_hours': 24
            },
            'medium_impact': {
                'requires_approval': True,
                'auto_approve_threshold': 0.1,
                'implementation_delay_hours': 4
            },
            'low_impact': {
                'requires_approval': False,
                'auto_approve_threshold': 0.05,
                'implementation_delay_hours': 0
            }
        }
    
    def submit_correction(self, data_point_id: str, data_point_type: str,
                         correction_type: CorrectionType, corrected_value: Any,
                         correction_reason: str, submitted_by: int,
                         field_name: Optional[str] = None,
                         original_value: Optional[Any] = None,
                         business_impact: Optional[str] = None,
                         urgency: str = 'medium',
                         company_id: Optional[int] = None,
                         lineage_id: Optional[str] = None) -> str:
        """
        Submit a data correction request
        
        Returns:
            correction_id: Unique identifier for the correction
        """
        try:
            # Get original value if not provided
            if original_value is None:
                original_value = self._get_current_value(data_point_id, field_name)
            
            # Estimate confidence impact
            confidence_impact = self._estimate_confidence_impact(
                data_point_id, data_point_type, correction_type, original_value, corrected_value
            )
            
            # Determine business impact if not provided
            if business_impact is None:
                business_impact = self._assess_business_impact(
                    data_point_id, data_point_type, confidence_impact
                )
            
            # Get applicable workflow
            workflow = self._get_applicable_workflow(
                data_point_type, correction_type, business_impact, confidence_impact, company_id
            )
            
            # Create correction record
            correction = DataCorrection(
                data_point_id=data_point_id,
                data_point_type=data_point_type,
                field_name=field_name,
                correction_type=correction_type,
                original_value=json.dumps(original_value) if original_value is not None else None,
                corrected_value=json.dumps(corrected_value),
                correction_reason=correction_reason,
                confidence_impact=confidence_impact,
                business_impact=business_impact,
                urgency=urgency,
                requires_approval=workflow.get('requires_approval', True),
                submitted_by=submitted_by,
                company_id=company_id,
                lineage_id=lineage_id
            )
            
            # Auto-approve if applicable
            if self._should_auto_approve(correction, workflow):
                correction.status = CorrectionStatus.APPROVED
                correction.approved_by = submitted_by
                correction.approved_at = datetime.utcnow()
            
            db.session.add(correction)
            db.session.commit()
            
            # Send notifications
            self._send_correction_notifications(correction, workflow)
            
            # Auto-implement if applicable
            if correction.status == CorrectionStatus.APPROVED and workflow.get('auto_implement', False):
                self._schedule_implementation(correction, workflow.get('implementation_delay_hours', 0))
            
            logger.info(f"Submitted correction {correction.correction_id} for {data_point_id}")
            return correction.correction_id
            
        except Exception as e:
            logger.error(f"Error submitting correction: {str(e)}")
            db.session.rollback()
            raise
    
    def approve_correction(self, correction_id: str, approved_by: int,
                          implementation_notes: Optional[str] = None) -> bool:
        """
        Approve a data correction
        
        Returns:
            success: Whether the approval was successful
        """
        try:
            correction = DataCorrection.query.filter_by(correction_id=correction_id).first()
            if not correction:
                raise ValueError(f"Correction {correction_id} not found")
            
            if correction.status != CorrectionStatus.PENDING:
                raise ValueError(f"Correction {correction_id} is not pending approval")
            
            correction.status = CorrectionStatus.APPROVED
            correction.approved_by = approved_by
            correction.approved_at = datetime.utcnow()
            if implementation_notes:
                correction.implementation_notes = implementation_notes
            
            db.session.commit()
            
            # Check if auto-implementation is enabled
            workflow = self._get_correction_workflow(correction)
            if workflow and workflow.get('auto_implement', False):
                self._schedule_implementation(correction, workflow.get('implementation_delay_hours', 0))
            
            logger.info(f"Approved correction {correction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving correction: {str(e)}")
            db.session.rollback()
            raise
    
    def implement_correction(self, correction_id: str, implemented_by: int) -> bool:
        """
        Implement a data correction
        
        Returns:
            success: Whether the implementation was successful
        """
        try:
            correction = DataCorrection.query.filter_by(correction_id=correction_id).first()
            if not correction:
                raise ValueError(f"Correction {correction_id} not found")
            
            if correction.status != CorrectionStatus.APPROVED:
                raise ValueError(f"Correction {correction_id} is not approved for implementation")
            
            # Create backup data for rollback
            rollback_data = self._create_rollback_data(correction)
            
            # Apply the correction
            success = self._apply_correction(correction)
            
            if success:
                correction.status = CorrectionStatus.IMPLEMENTED
                correction.implemented_by = implemented_by
                correction.implemented_at = datetime.utcnow()
                correction.rollback_data = json.dumps(rollback_data)
                
                # Measure impact
                self._measure_correction_impact(correction)
                
                # Update confidence scores
                self._update_confidence_scores(correction)
                
                db.session.commit()
                
                logger.info(f"Implemented correction {correction_id}")
                return True
            else:
                logger.error(f"Failed to apply correction {correction_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error implementing correction: {str(e)}")
            db.session.rollback()
            raise
    
    def create_annotation(self, data_point_id: str, data_point_type: str,
                         annotation_type: AnnotationType, title: str, content: str,
                         created_by: int, field_name: Optional[str] = None,
                         visibility: str = 'company', priority: str = 'medium',
                         tags: Optional[List[str]] = None,
                         company_id: Optional[int] = None,
                         lineage_id: Optional[str] = None,
                         expires_at: Optional[datetime] = None) -> str:
        """
        Create a data annotation
        
        Returns:
            annotation_id: Unique identifier for the annotation
        """
        try:
            annotation = DataAnnotation(
                data_point_id=data_point_id,
                data_point_type=data_point_type,
                field_name=field_name,
                annotation_type=annotation_type,
                title=title,
                content=content,
                visibility=visibility,
                priority=priority,
                tags=json.dumps(tags) if tags else None,
                created_by=created_by,
                company_id=company_id,
                lineage_id=lineage_id,
                expires_at=expires_at
            )
            
            db.session.add(annotation)
            db.session.commit()
            
            logger.info(f"Created annotation {annotation.annotation_id} for {data_point_id}")
            return annotation.annotation_id
            
        except Exception as e:
            logger.error(f"Error creating annotation: {str(e)}")
            db.session.rollback()
            raise
    
    def submit_feedback(self, target_type: str, target_id: str, feedback_type: str,
                       title: str, description: str, submitted_by: int,
                       rating: Optional[int] = None, severity: str = 'medium',
                       category: Optional[str] = None, tags: Optional[List[str]] = None,
                       company_id: Optional[int] = None) -> str:
        """
        Submit user feedback
        
        Returns:
            feedback_id: Unique identifier for the feedback
        """
        try:
            feedback = UserFeedback(
                target_type=target_type,
                target_id=target_id,
                feedback_type=feedback_type,
                rating=rating,
                title=title,
                description=description,
                severity=severity,
                category=category,
                tags=json.dumps(tags) if tags else None,
                submitted_by=submitted_by,
                company_id=company_id
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            logger.info(f"Submitted feedback {feedback.feedback_id} for {target_type}:{target_id}")
            return feedback.feedback_id
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            db.session.rollback()
            raise
    
    def get_corrections_queue(self, company_id: Optional[int] = None,
                             status: Optional[str] = None,
                             urgency: Optional[str] = None,
                             limit: int = 50) -> List[Dict]:
        """
        Get corrections queue for review
        """
        try:
            query = DataCorrection.query
            
            if company_id:
                query = query.filter(DataCorrection.company_id == company_id)
            
            if status:
                query = query.filter(DataCorrection.status == CorrectionStatus(status))
            
            if urgency:
                query = query.filter(DataCorrection.urgency == urgency)
            
            corrections = query.order_by(
                DataCorrection.urgency.desc(),
                DataCorrection.submitted_at.asc()
            ).limit(limit).all()
            
            return [correction.to_dict() for correction in corrections]
            
        except Exception as e:
            logger.error(f"Error getting corrections queue: {str(e)}")
            return []
    
    def get_data_annotations(self, data_point_id: str,
                           annotation_type: Optional[str] = None,
                           visibility: Optional[str] = None) -> List[Dict]:
        """
        Get annotations for a data point
        """
        try:
            query = DataAnnotation.query.filter(
                DataAnnotation.data_point_id == data_point_id,
                DataAnnotation.is_active == True
            )
            
            if annotation_type:
                query = query.filter(DataAnnotation.annotation_type == AnnotationType(annotation_type))
            
            if visibility:
                query = query.filter(DataAnnotation.visibility == visibility)
            
            annotations = query.order_by(
                DataAnnotation.is_pinned.desc(),
                DataAnnotation.priority.desc(),
                DataAnnotation.created_at.desc()
            ).all()
            
            return [annotation.to_dict() for annotation in annotations]
            
        except Exception as e:
            logger.error(f"Error getting data annotations: {str(e)}")
            return []
    
    def get_correction_impact_analysis(self, company_id: Optional[int] = None,
                                     days: int = 30) -> Dict:
        """
        Get correction impact analysis
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get corrections with impacts
            query = db.session.query(DataCorrection, CorrectionImpact).join(
                CorrectionImpact, DataCorrection.correction_id == CorrectionImpact.correction_id
            ).filter(DataCorrection.implemented_at >= start_date)
            
            if company_id:
                query = query.filter(DataCorrection.company_id == company_id)
            
            results = query.all()
            
            # Calculate statistics
            total_corrections = len(results)
            total_confidence_improvement = sum(
                impact.confidence_improvement for _, impact in results 
                if impact.confidence_improvement
            )
            avg_confidence_improvement = (
                total_confidence_improvement / total_corrections if total_corrections > 0 else 0
            )
            
            # Group by correction type
            type_analysis = {}
            for correction, impact in results:
                correction_type = correction.correction_type.value
                if correction_type not in type_analysis:
                    type_analysis[correction_type] = {
                        'count': 0,
                        'total_confidence_improvement': 0,
                        'avg_confidence_improvement': 0
                    }
                
                type_analysis[correction_type]['count'] += 1
                if impact.confidence_improvement:
                    type_analysis[correction_type]['total_confidence_improvement'] += impact.confidence_improvement
            
            # Calculate averages
            for correction_type in type_analysis:
                analysis = type_analysis[correction_type]
                if analysis['count'] > 0:
                    analysis['avg_confidence_improvement'] = (
                        analysis['total_confidence_improvement'] / analysis['count']
                    )
            
            return {
                'time_range_days': days,
                'total_corrections': total_corrections,
                'total_confidence_improvement': total_confidence_improvement,
                'avg_confidence_improvement': avg_confidence_improvement,
                'type_analysis': type_analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting correction impact analysis: {str(e)}")
            return {}
    
    # Helper methods
    
    def _get_current_value(self, data_point_id: str, field_name: Optional[str]) -> Any:
        """Get current value of a data point - simplified implementation"""
        # This would integrate with the actual data storage system
        return None
    
    def _estimate_confidence_impact(self, data_point_id: str, data_point_type: str,
                                  correction_type: CorrectionType, original_value: Any,
                                  corrected_value: Any) -> float:
        """Estimate confidence impact of a correction - simplified implementation"""
        # This would use ML models to estimate impact
        impact_scores = {
            CorrectionType.VALUE_CORRECTION: 0.15,
            CorrectionType.CLASSIFICATION_CORRECTION: 0.25,
            CorrectionType.RELATIONSHIP_CORRECTION: 0.20,
            CorrectionType.METADATA_CORRECTION: 0.10,
            CorrectionType.DELETION: 0.30,
            CorrectionType.ADDITION: 0.20
        }
        return impact_scores.get(correction_type, 0.15)
    
    def _assess_business_impact(self, data_point_id: str, data_point_type: str,
                              confidence_impact: float) -> str:
        """Assess business impact of a correction - simplified implementation"""
        if confidence_impact >= 0.3:
            return 'high'
        elif confidence_impact >= 0.15:
            return 'medium'
        else:
            return 'low'
    
    def _get_applicable_workflow(self, data_point_type: str, correction_type: CorrectionType,
                               business_impact: str, confidence_impact: float,
                               company_id: Optional[int]) -> Dict:
        """Get applicable workflow for a correction"""
        try:
            # Try to find company-specific workflow
            if company_id:
                workflow = CorrectionWorkflow.query.filter(
                    CorrectionWorkflow.company_id == company_id,
                    CorrectionWorkflow.is_active == True,
                    db.or_(
                        CorrectionWorkflow.data_type_pattern.is_(None),
                        CorrectionWorkflow.data_type_pattern == data_point_type
                    ),
                    db.or_(
                        CorrectionWorkflow.correction_type.is_(None),
                        CorrectionWorkflow.correction_type == correction_type
                    )
                ).order_by(CorrectionWorkflow.priority.asc()).first()
                
                if workflow:
                    return {
                        'requires_approval': workflow.requires_approval,
                        'auto_approve_threshold': workflow.auto_approve_threshold,
                        'auto_implement': workflow.auto_implement,
                        'implementation_delay_hours': workflow.implementation_delay_hours,
                        'approval_roles': json.loads(workflow.approval_roles) if workflow.approval_roles else [],
                        'notification_roles': json.loads(workflow.notification_roles) if workflow.notification_roles else []
                    }
            
            # Fall back to default workflows
            return self.default_workflows.get(business_impact, self.default_workflows['medium_impact'])
            
        except Exception as e:
            logger.error(f"Error getting applicable workflow: {str(e)}")
            return self.default_workflows['medium_impact']
    
    def _should_auto_approve(self, correction: DataCorrection, workflow: Dict) -> bool:
        """Determine if a correction should be auto-approved"""
        if not workflow.get('auto_approve_threshold'):
            return False
        
        return (correction.confidence_impact or 0) <= workflow['auto_approve_threshold']
    
    def _send_correction_notifications(self, correction: DataCorrection, workflow: Dict):
        """Send notifications for a correction - simplified implementation"""
        # This would integrate with notification system
        logger.info(f"Sending notifications for correction {correction.correction_id}")
    
    def _schedule_implementation(self, correction: DataCorrection, delay_hours: int):
        """Schedule correction implementation - simplified implementation"""
        # This would integrate with task scheduler
        logger.info(f"Scheduling implementation of correction {correction.correction_id} in {delay_hours} hours")
    
    def _get_correction_workflow(self, correction: DataCorrection) -> Optional[Dict]:
        """Get workflow for an existing correction"""
        return self._get_applicable_workflow(
            correction.data_point_type,
            correction.correction_type,
            correction.business_impact,
            correction.confidence_impact,
            correction.company_id
        )
    
    def _create_rollback_data(self, correction: DataCorrection) -> Dict:
        """Create rollback data for a correction - simplified implementation"""
        return {
            'data_point_id': correction.data_point_id,
            'field_name': correction.field_name,
            'original_value': json.loads(correction.original_value) if correction.original_value else None,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _apply_correction(self, correction: DataCorrection) -> bool:
        """Apply a correction to the data - simplified implementation"""
        # This would integrate with the actual data storage system
        logger.info(f"Applying correction {correction.correction_id}")
        return True
    
    def _measure_correction_impact(self, correction: DataCorrection):
        """Measure the impact of a correction"""
        try:
            # Get confidence scores before and after
            confidence_before = self._get_confidence_before_correction(correction)
            confidence_after = self._get_confidence_after_correction(correction)
            
            impact = CorrectionImpact(
                correction_id=correction.correction_id,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                confidence_improvement=confidence_after - confidence_before if confidence_before and confidence_after else None,
                affected_data_points=self._count_affected_data_points(correction),
                affected_calculations=self._count_affected_calculations(correction),
                affected_reports=self._count_affected_reports(correction)
            )
            
            db.session.add(impact)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error measuring correction impact: {str(e)}")
    
    def _update_confidence_scores(self, correction: DataCorrection):
        """Update confidence scores after correction - simplified implementation"""
        # This would trigger confidence score recalculation
        logger.info(f"Updating confidence scores for correction {correction.correction_id}")
    
    def _get_confidence_before_correction(self, correction: DataCorrection) -> Optional[float]:
        """Get confidence score before correction - simplified implementation"""
        return 0.7  # Placeholder
    
    def _get_confidence_after_correction(self, correction: DataCorrection) -> Optional[float]:
        """Get confidence score after correction - simplified implementation"""
        return 0.85  # Placeholder
    
    def _count_affected_data_points(self, correction: DataCorrection) -> int:
        """Count data points affected by correction - simplified implementation"""
        return 1  # Placeholder
    
    def _count_affected_calculations(self, correction: DataCorrection) -> int:
        """Count calculations affected by correction - simplified implementation"""
        return 0  # Placeholder
    
    def _count_affected_reports(self, correction: DataCorrection) -> int:
        """Count reports affected by correction - simplified implementation"""
        return 0  # Placeholder

# Global service instance
data_correction_service = DataCorrectionService()

