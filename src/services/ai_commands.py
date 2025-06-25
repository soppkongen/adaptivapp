"""
AI-Powered Command Interface Service

This service provides natural language command processing for the Elite Command Data API.
It interprets executive commands, generates appropriate code/queries, and executes them safely.
"""

import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import uuid

from ..models.ai_commands import (
    AICommand, CommandTemplate, ConversationSession, AutomationRule, 
    CommandFeedback, CommandType, CommandStatus, CommandPriority, db
)

logger = logging.getLogger(__name__)

class AICommandService:
    """
    Core service for AI-powered command processing
    """
    
    def __init__(self):
        self.command_patterns = self._initialize_command_patterns()
        self.safety_keywords = self._initialize_safety_keywords()
        
    def _initialize_command_patterns(self) -> Dict[str, List[str]]:
        """Initialize natural language command patterns"""
        return {
            'query': [
                r'show me (?P<target>.*)',
                r'what (?:is|are) (?P<target>.*)',
                r'find (?P<target>.*)',
                r'list (?P<target>.*)',
                r'get (?P<target>.*)',
                r'display (?P<target>.*)',
                r'how many (?P<target>.*)',
                r'which (?P<target>.*)',
                r'who (?P<target>.*)'
            ],
            'modification': [
                r'update (?P<target>.*) (?:to|with) (?P<value>.*)',
                r'change (?P<target>.*) (?:to|from) (?P<value>.*)',
                r'set (?P<target>.*) (?:to|as) (?P<value>.*)',
                r'modify (?P<target>.*)',
                r'edit (?P<target>.*)',
                r'delete (?P<target>.*)',
                r'remove (?P<target>.*)',
                r'add (?P<target>.*)',
                r'create (?P<target>.*)'
            ],
            'automation': [
                r'create (?:a )?rule (?:to|that) (?P<action>.*)',
                r'automate (?P<action>.*)',
                r'set up (?:an )?alert (?:for|when) (?P<condition>.*)',
                r'notify me (?:when|if) (?P<condition>.*)',
                r'schedule (?P<action>.*)',
                r'trigger (?P<action>.*) when (?P<condition>.*)'
            ],
            'analysis': [
                r'analyze (?P<target>.*)',
                r'explain (?P<target>.*)',
                r'why (?:is|did|does) (?P<target>.*)',
                r'compare (?P<target1>.*) (?:with|to|and) (?P<target2>.*)',
                r'correlate (?P<target>.*)',
                r'predict (?P<target>.*)',
                r'forecast (?P<target>.*)'
            ],
            'configuration': [
                r'configure (?P<target>.*)',
                r'setup (?P<target>.*)',
                r'enable (?P<target>.*)',
                r'disable (?P<target>.*)',
                r'install (?P<target>.*)',
                r'initialize (?P<target>.*)'
            ],
            'reporting': [
                r'generate (?:a )?report (?:on|for) (?P<target>.*)',
                r'create (?:a )?dashboard (?:for|showing) (?P<target>.*)',
                r'export (?P<target>.*)',
                r'summarize (?P<target>.*)',
                r'brief me on (?P<target>.*)'
            ]
        }
    
    def _initialize_safety_keywords(self) -> List[str]:
        """Initialize keywords that require approval"""
        return [
            'delete', 'remove', 'drop', 'truncate', 'destroy',
            'modify', 'update', 'change', 'alter', 'edit',
            'create', 'add', 'insert', 'new',
            'configure', 'setup', 'install', 'enable', 'disable',
            'automate', 'schedule', 'trigger'
        ]
    
    def process_command(self, natural_language_input: str, user_id: int, 
                       company_id: Optional[int] = None, 
                       session_id: Optional[str] = None) -> str:
        """
        Process a natural language command
        
        Args:
            natural_language_input: The natural language command
            user_id: ID of the user submitting the command
            company_id: Optional company context
            session_id: Optional conversation session ID
            
        Returns:
            Command ID for tracking
        """
        try:
            # Parse the command intent
            parsed_intent = self._parse_command_intent(natural_language_input)
            
            # Determine command type
            command_type = self._determine_command_type(parsed_intent)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(parsed_intent, command_type)
            
            # Check if approval is required
            requires_approval = self._requires_approval(natural_language_input, command_type)
            
            # Generate execution plan
            execution_plan = self._generate_execution_plan(parsed_intent, command_type)
            
            # Create command record
            command = AICommand(
                natural_language_input=natural_language_input,
                parsed_intent=json.dumps(parsed_intent),
                command_type=command_type,
                confidence_score=confidence_score,
                submitted_by=user_id,
                company_id=company_id,
                session_id=session_id or str(uuid.uuid4()),
                requires_approval=requires_approval,
                execution_plan=json.dumps(execution_plan)
            )
            
            db.session.add(command)
            db.session.commit()
            
            # Execute immediately if no approval required and confidence is high
            if not requires_approval and confidence_score > 0.8:
                self._execute_command(command.command_id)
            
            return command.command_id
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            raise
    
    def _parse_command_intent(self, natural_language_input: str) -> Dict[str, Any]:
        """Parse natural language input to extract intent"""
        intent = {
            'original_text': natural_language_input,
            'entities': {},
            'action': None,
            'target': None,
            'conditions': [],
            'parameters': {}
        }
        
        # Normalize input
        text = natural_language_input.lower().strip()
        
        # Extract entities using pattern matching
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    intent['action'] = command_type
                    intent['entities'].update(match.groupdict())
                    break
            if intent['action']:
                break
        
        # Extract business entities
        intent['entities'].update(self._extract_business_entities(text))
        
        # Extract time references
        intent['entities'].update(self._extract_time_references(text))
        
        # Extract metrics and thresholds
        intent['entities'].update(self._extract_metrics_and_thresholds(text))
        
        return intent
    
    def _extract_business_entities(self, text: str) -> Dict[str, Any]:
        """Extract business-specific entities from text"""
        entities = {}
        
        # Company names (simplified - in production would use NER)
        company_patterns = [
            r'company (?P<company_name>\w+)',
            r'(?P<company_name>\w+) company',
            r'portfolio company (?P<company_name>\w+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                entities['company_name'] = match.group('company_name')
                break
        
        # Founder/people names
        people_patterns = [
            r'founder (?P<person_name>\w+(?:\s+\w+)?)',
            r'(?P<person_name>\w+(?:\s+\w+)?)(?:\'s|s) (?:profile|data|metrics)',
            r'ceo (?P<person_name>\w+(?:\s+\w+)?)'
        ]
        
        for pattern in people_patterns:
            match = re.search(pattern, text)
            if match:
                entities['person_name'] = match.group('person_name')
                break
        
        # Business metrics
        metric_keywords = [
            'arr', 'revenue', 'churn', 'burn', 'runway', 'growth',
            'engagement', 'retention', 'conversion', 'ltv', 'cac',
            'stress', 'leadership', 'personality', 'risk'
        ]
        
        for keyword in metric_keywords:
            if keyword in text:
                if 'metrics' not in entities:
                    entities['metrics'] = []
                entities['metrics'].append(keyword)
        
        return entities
    
    def _extract_time_references(self, text: str) -> Dict[str, Any]:
        """Extract time references from text"""
        entities = {}
        
        # Time periods
        time_patterns = [
            r'(?P<time_period>last (?:week|month|quarter|year))',
            r'(?P<time_period>this (?:week|month|quarter|year))',
            r'(?P<time_period>next (?:week|month|quarter|year))',
            r'(?P<time_period>q[1-4])',
            r'(?P<time_period>\d{4})',  # Year
            r'(?P<time_period>yesterday|today|tomorrow)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                entities['time_period'] = match.group('time_period')
                break
        
        return entities
    
    def _extract_metrics_and_thresholds(self, text: str) -> Dict[str, Any]:
        """Extract metrics and threshold values from text"""
        entities = {}
        
        # Threshold patterns
        threshold_patterns = [
            r'(?:above|over|greater than|>) (?P<threshold>\d+(?:\.\d+)?)',
            r'(?:below|under|less than|<) (?P<threshold>\d+(?:\.\d+)?)',
            r'(?:equals?|=) (?P<threshold>\d+(?:\.\d+)?)',
            r'(?P<threshold>\d+(?:\.\d+)?)%'
        ]
        
        for pattern in threshold_patterns:
            match = re.search(pattern, text)
            if match:
                entities['threshold'] = float(match.group('threshold'))
                break
        
        # Risk levels
        risk_patterns = [
            r'(?P<risk_level>high|medium|low) risk',
            r'risk (?:level )?(?P<risk_level>high|medium|low)'
        ]
        
        for pattern in risk_patterns:
            match = re.search(pattern, text)
            if match:
                entities['risk_level'] = match.group('risk_level')
                break
        
        return entities
    
    def _determine_command_type(self, parsed_intent: Dict[str, Any]) -> CommandType:
        """Determine the type of command based on parsed intent"""
        action = parsed_intent.get('action')
        
        if action:
            return CommandType(action)
        
        # Fallback logic based on keywords
        text = parsed_intent['original_text'].lower()
        
        if any(word in text for word in ['show', 'list', 'get', 'find', 'what', 'how many']):
            return CommandType.QUERY
        elif any(word in text for word in ['update', 'change', 'set', 'modify', 'delete']):
            return CommandType.MODIFICATION
        elif any(word in text for word in ['automate', 'alert', 'notify', 'schedule']):
            return CommandType.AUTOMATION
        elif any(word in text for word in ['analyze', 'explain', 'why', 'compare']):
            return CommandType.ANALYSIS
        elif any(word in text for word in ['configure', 'setup', 'enable', 'disable']):
            return CommandType.CONFIGURATION
        elif any(word in text for word in ['report', 'dashboard', 'export', 'summarize']):
            return CommandType.REPORTING
        
        return CommandType.QUERY  # Default fallback
    
    def _calculate_confidence(self, parsed_intent: Dict[str, Any], 
                            command_type: CommandType) -> float:
        """Calculate confidence score for command interpretation"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if we found clear action
        if parsed_intent.get('action'):
            confidence += 0.3
        
        # Boost confidence if we found entities
        entities = parsed_intent.get('entities', {})
        if entities:
            confidence += 0.1 * min(len(entities), 3)  # Max 0.3 boost
        
        # Boost confidence if we found business-specific terms
        business_terms = ['company', 'founder', 'revenue', 'metrics', 'portfolio']
        text = parsed_intent['original_text'].lower()
        business_term_count = sum(1 for term in business_terms if term in text)
        confidence += 0.05 * business_term_count
        
        return min(confidence, 1.0)
    
    def _requires_approval(self, natural_language_input: str, 
                          command_type: CommandType) -> bool:
        """Determine if command requires approval"""
        text = natural_language_input.lower()
        
        # Always require approval for modifications and configurations
        if command_type in [CommandType.MODIFICATION, CommandType.CONFIGURATION]:
            return True
        
        # Require approval for automation that affects data
        if command_type == CommandType.AUTOMATION:
            return True
        
        # Check for safety keywords
        if any(keyword in text for keyword in self.safety_keywords):
            return True
        
        return False
    
    def _generate_execution_plan(self, parsed_intent: Dict[str, Any], 
                               command_type: CommandType) -> Dict[str, Any]:
        """Generate execution plan for the command"""
        plan = {
            'steps': [],
            'estimated_time_ms': 1000,
            'requires_database_access': False,
            'requires_external_api': False,
            'safety_checks': []
        }
        
        entities = parsed_intent.get('entities', {})
        
        if command_type == CommandType.QUERY:
            plan['steps'] = [
                {'action': 'validate_query_parameters', 'parameters': entities},
                {'action': 'execute_database_query', 'parameters': {}},
                {'action': 'format_results', 'parameters': {}}
            ]
            plan['requires_database_access'] = True
            plan['estimated_time_ms'] = 500
            
        elif command_type == CommandType.MODIFICATION:
            plan['steps'] = [
                {'action': 'validate_modification_permissions', 'parameters': entities},
                {'action': 'backup_current_data', 'parameters': {}},
                {'action': 'execute_modification', 'parameters': entities},
                {'action': 'verify_modification', 'parameters': {}}
            ]
            plan['requires_database_access'] = True
            plan['estimated_time_ms'] = 2000
            plan['safety_checks'] = ['backup_verification', 'rollback_capability']
            
        elif command_type == CommandType.AUTOMATION:
            plan['steps'] = [
                {'action': 'validate_automation_rules', 'parameters': entities},
                {'action': 'create_automation_rule', 'parameters': entities},
                {'action': 'test_automation_rule', 'parameters': {}},
                {'action': 'activate_automation_rule', 'parameters': {}}
            ]
            plan['requires_database_access'] = True
            plan['estimated_time_ms'] = 1500
            plan['safety_checks'] = ['rule_validation', 'impact_assessment']
            
        elif command_type == CommandType.ANALYSIS:
            plan['steps'] = [
                {'action': 'gather_analysis_data', 'parameters': entities},
                {'action': 'perform_analysis', 'parameters': {}},
                {'action': 'generate_insights', 'parameters': {}},
                {'action': 'format_analysis_results', 'parameters': {}}
            ]
            plan['requires_database_access'] = True
            plan['requires_external_api'] = True  # May need AI analysis
            plan['estimated_time_ms'] = 3000
            
        return plan
    
    def _execute_command(self, command_id: str) -> bool:
        """Execute a command"""
        try:
            command = AICommand.query.filter_by(command_id=command_id).first()
            if not command:
                raise ValueError(f"Command {command_id} not found")
            
            # Update status
            command.status = CommandStatus.PROCESSING
            command.started_at = datetime.utcnow()
            db.session.commit()
            
            # Parse execution plan
            execution_plan = json.loads(command.execution_plan)
            
            # Execute steps
            results = []
            for step in execution_plan['steps']:
                step_result = self._execute_step(step, command)
                results.append(step_result)
            
            # Update command with results
            command.status = CommandStatus.COMPLETED
            command.completed_at = datetime.utcnow()
            command.execution_time_ms = int((command.completed_at - command.started_at).total_seconds() * 1000)
            command.execution_result = json.dumps({
                'success': True,
                'results': results,
                'summary': self._generate_result_summary(results, command)
            })
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error executing command {command_id}: {str(e)}")
            
            # Update command with error
            if command:
                command.status = CommandStatus.FAILED
                command.completed_at = datetime.utcnow()
                command.error_message = str(e)
                db.session.commit()
            
            return False
    
    def _execute_step(self, step: Dict[str, Any], command: AICommand) -> Dict[str, Any]:
        """Execute a single step in the execution plan"""
        action = step['action']
        parameters = step.get('parameters', {})
        
        # This is a simplified implementation
        # In production, this would route to appropriate services
        
        if action == 'validate_query_parameters':
            return {'action': action, 'status': 'success', 'message': 'Parameters validated'}
        
        elif action == 'execute_database_query':
            # Generate and execute appropriate database query
            query_result = self._generate_and_execute_query(command)
            return {'action': action, 'status': 'success', 'data': query_result}
        
        elif action == 'format_results':
            return {'action': action, 'status': 'success', 'message': 'Results formatted'}
        
        else:
            return {'action': action, 'status': 'not_implemented', 'message': f'Action {action} not implemented'}
    
    def _generate_and_execute_query(self, command: AICommand) -> Dict[str, Any]:
        """Generate and execute database query based on command"""
        # This is a simplified implementation
        # In production, this would generate actual SQL/API calls
        
        parsed_intent = json.loads(command.parsed_intent)
        entities = parsed_intent.get('entities', {})
        
        # Example query generation
        if 'company_name' in entities:
            return {
                'query_type': 'company_lookup',
                'company': entities['company_name'],
                'results': [
                    {'id': 1, 'name': entities['company_name'], 'status': 'active'}
                ]
            }
        
        return {'query_type': 'general', 'results': []}
    
    def _generate_result_summary(self, results: List[Dict[str, Any]], 
                                command: AICommand) -> str:
        """Generate human-readable summary of execution results"""
        if not results:
            return "No results generated."
        
        successful_steps = sum(1 for r in results if r.get('status') == 'success')
        total_steps = len(results)
        
        summary = f"Executed {successful_steps}/{total_steps} steps successfully."
        
        # Add specific insights based on command type
        if command.command_type == CommandType.QUERY:
            data_results = [r for r in results if 'data' in r]
            if data_results:
                summary += f" Found {len(data_results)} data results."
        
        return summary
    
    def approve_command(self, command_id: str, approved_by: int) -> bool:
        """Approve a command for execution"""
        try:
            command = AICommand.query.filter_by(command_id=command_id).first()
            if not command:
                raise ValueError(f"Command {command_id} not found")
            
            if command.status != CommandStatus.PENDING:
                raise ValueError(f"Command {command_id} is not pending approval")
            
            command.approved_by = approved_by
            db.session.commit()
            
            # Execute the approved command
            return self._execute_command(command_id)
            
        except Exception as e:
            logger.error(f"Error approving command {command_id}: {str(e)}")
            return False
    
    def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a command"""
        command = AICommand.query.filter_by(command_id=command_id).first()
        if not command:
            return None
        
        return command.to_dict()
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        session = ConversationSession.query.filter_by(session_id=session_id).first()
        if not session:
            return []
        
        history = json.loads(session.conversation_history) if session.conversation_history else []
        return history
    
    def create_automation_rule(self, command_id: str, rule_name: str, 
                             trigger_conditions: Dict[str, Any], 
                             actions: Dict[str, Any], created_by: int,
                             company_id: Optional[int] = None) -> str:
        """Create an automation rule from a command"""
        try:
            rule = AutomationRule(
                rule_name=rule_name,
                trigger_conditions=json.dumps(trigger_conditions),
                actions=json.dumps(actions),
                created_by_command=command_id,
                created_by=created_by,
                company_id=company_id
            )
            
            db.session.add(rule)
            db.session.commit()
            
            return rule.rule_id
            
        except Exception as e:
            logger.error(f"Error creating automation rule: {str(e)}")
            raise

# Global service instance
ai_command_service = AICommandService()

