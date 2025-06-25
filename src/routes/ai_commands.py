from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import json

from ..services.ai_commands import ai_command_service
from ..models.ai_commands import (
    AICommand, CommandTemplate, ConversationSession, AutomationRule,
    CommandFeedback, CommandType, CommandStatus, CommandPriority, db
)

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
logger = logging.getLogger(__name__)

@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for AI command interface"""
    try:
        # Test database connectivity
        command_count = AICommand.query.count()
        session_count = ConversationSession.query.count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'AI-Powered Command Interface',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'total_commands': command_count,
                'active_sessions': session_count
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@ai_bp.route('/command', methods=['POST'])
def process_command():
    """Process a natural language command"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'command' not in data:
            return jsonify({'error': 'Missing required field: command'}), 400
        
        if 'user_id' not in data:
            return jsonify({'error': 'Missing required field: user_id'}), 400
        
        # Process the command
        command_id = ai_command_service.process_command(
            natural_language_input=data['command'],
            user_id=data['user_id'],
            company_id=data.get('company_id'),
            session_id=data.get('session_id')
        )
        
        # Get command status
        command_status = ai_command_service.get_command_status(command_id)
        
        return jsonify({
            'success': True,
            'command_id': command_id,
            'status': command_status['status'],
            'requires_approval': command_status['requires_approval'],
            'confidence_score': command_status['confidence_score'],
            'message': 'Command processed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/command/<command_id>/status', methods=['GET'])
def get_command_status(command_id):
    """Get status of a specific command"""
    try:
        status = ai_command_service.get_command_status(command_id)
        
        if not status:
            return jsonify({'error': 'Command not found'}), 404
        
        return jsonify({
            'success': True,
            'command': status
        })
        
    except Exception as e:
        logger.error(f"Error getting command status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/command/<command_id>/approve', methods=['POST'])
def approve_command(command_id):
    """Approve a command for execution"""
    try:
        data = request.get_json() or {}
        
        if 'approved_by' not in data:
            return jsonify({'error': 'Missing required field: approved_by'}), 400
        
        success = ai_command_service.approve_command(
            command_id=command_id,
            approved_by=data['approved_by']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Command approved and executed successfully'
            })
        else:
            return jsonify({'error': 'Failed to approve and execute command'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error approving command: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """Get conversation history for a session"""
    try:
        history = ai_command_service.get_conversation_history(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'conversation_history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/conversation/start', methods=['POST'])
def start_conversation():
    """Start a new conversation session"""
    try:
        data = request.get_json()
        
        if 'user_id' not in data:
            return jsonify({'error': 'Missing required field: user_id'}), 400
        
        # Create new conversation session
        session = ConversationSession(
            session_name=data.get('session_name', 'New Conversation'),
            user_id=data['user_id'],
            company_id=data.get('company_id'),
            conversation_history=json.dumps([]),
            context_data=json.dumps(data.get('context', {}))
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session.session_id,
            'message': 'Conversation session started'
        })
        
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/templates', methods=['GET'])
def get_command_templates():
    """Get available command templates"""
    try:
        company_id = request.args.get('company_id', type=int)
        category = request.args.get('category')
        
        query = CommandTemplate.query.filter(CommandTemplate.is_active == True)
        
        # Filter by company (public templates + company-specific)
        if company_id:
            query = query.filter(
                (CommandTemplate.is_public == True) | 
                (CommandTemplate.company_id == company_id)
            )
        else:
            query = query.filter(CommandTemplate.is_public == True)
        
        # Filter by category
        if category:
            query = query.filter(CommandTemplate.category == category)
        
        templates = query.order_by(CommandTemplate.usage_count.desc()).all()
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates],
            'count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/templates/create', methods=['POST'])
def create_command_template():
    """Create a new command template"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['template_name', 'natural_language_patterns', 
                          'command_type', 'code_template', 'created_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse command type
        try:
            command_type = CommandType(data['command_type'])
        except ValueError:
            return jsonify({'error': f'Invalid command type: {data["command_type"]}'}), 400
        
        # Create template
        template = CommandTemplate(
            template_name=data['template_name'],
            template_description=data.get('template_description'),
            natural_language_patterns=json.dumps(data['natural_language_patterns']),
            command_type=command_type,
            code_template=data['code_template'],
            category=data.get('category'),
            tags=json.dumps(data.get('tags', [])),
            is_public=data.get('is_public', True),
            requires_approval=data.get('requires_approval', False),
            allowed_roles=json.dumps(data.get('allowed_roles', [])),
            company_id=data.get('company_id'),
            created_by=data['created_by']
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'template_id': template.id,
            'message': 'Command template created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/automation/rules', methods=['GET'])
def get_automation_rules():
    """Get automation rules"""
    try:
        company_id = request.args.get('company_id', type=int)
        is_active = request.args.get('is_active', type=bool)
        
        query = AutomationRule.query
        
        if company_id:
            query = query.filter(AutomationRule.company_id == company_id)
        
        if is_active is not None:
            query = query.filter(AutomationRule.is_active == is_active)
        
        rules = query.order_by(AutomationRule.priority.asc()).all()
        
        return jsonify({
            'success': True,
            'rules': [rule.to_dict() for rule in rules],
            'count': len(rules)
        })
        
    except Exception as e:
        logger.error(f"Error getting automation rules: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/automation/rules/create', methods=['POST'])
def create_automation_rule():
    """Create a new automation rule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['rule_name', 'trigger_conditions', 'actions', 'created_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create automation rule
        rule_id = ai_command_service.create_automation_rule(
            command_id=data.get('command_id'),
            rule_name=data['rule_name'],
            trigger_conditions=data['trigger_conditions'],
            actions=data['actions'],
            created_by=data['created_by'],
            company_id=data.get('company_id')
        )
        
        return jsonify({
            'success': True,
            'rule_id': rule_id,
            'message': 'Automation rule created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating automation rule: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/feedback/submit', methods=['POST'])
def submit_command_feedback():
    """Submit feedback on command execution"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['command_id', 'feedback_type', 'submitted_by']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate rating if provided
        if data.get('rating') and (data['rating'] < 1 or data['rating'] > 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Create feedback
        feedback = CommandFeedback(
            command_id=data['command_id'],
            rating=data.get('rating'),
            feedback_type=data['feedback_type'],
            feedback_text=data.get('feedback_text'),
            was_helpful=data.get('was_helpful'),
            interpretation_correct=data.get('interpretation_correct'),
            result_accurate=data.get('result_accurate'),
            submitted_by=data['submitted_by']
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'feedback_id': feedback.id,
            'message': 'Feedback submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/dashboard', methods=['GET'])
def get_ai_dashboard():
    """Get AI command interface dashboard data"""
    try:
        company_id = request.args.get('company_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        # Get recent commands
        query = AICommand.query
        if company_id:
            query = query.filter(AICommand.company_id == company_id)
        
        recent_commands = query.filter(
            AICommand.submitted_at >= datetime.utcnow() - timedelta(days=days)
        ).order_by(AICommand.submitted_at.desc()).limit(10).all()
        
        # Get command statistics
        total_commands = query.count()
        pending_commands = query.filter(AICommand.status == CommandStatus.PENDING).count()
        successful_commands = query.filter(AICommand.status == CommandStatus.COMPLETED).count()
        failed_commands = query.filter(AICommand.status == CommandStatus.FAILED).count()
        
        # Get automation rules
        automation_query = AutomationRule.query
        if company_id:
            automation_query = automation_query.filter(AutomationRule.company_id == company_id)
        
        active_rules = automation_query.filter(AutomationRule.is_active == True).count()
        
        # Get average confidence score
        avg_confidence = db.session.query(db.func.avg(AICommand.confidence_score)).filter(
            AICommand.confidence_score.isnot(None)
        )
        if company_id:
            avg_confidence = avg_confidence.filter(AICommand.company_id == company_id)
        avg_confidence = avg_confidence.scalar() or 0.0
        
        return jsonify({
            'success': True,
            'dashboard': {
                'statistics': {
                    'total_commands': total_commands,
                    'pending_commands': pending_commands,
                    'successful_commands': successful_commands,
                    'failed_commands': failed_commands,
                    'success_rate': (successful_commands / max(total_commands, 1)) * 100,
                    'active_automation_rules': active_rules,
                    'average_confidence': round(avg_confidence, 2)
                },
                'recent_commands': [cmd.to_dict() for cmd in recent_commands]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting AI dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/commands/pending', methods=['GET'])
def get_pending_commands():
    """Get commands pending approval"""
    try:
        company_id = request.args.get('company_id', type=int)
        limit = request.args.get('limit', 20, type=int)
        
        query = AICommand.query.filter(
            AICommand.status == CommandStatus.PENDING,
            AICommand.requires_approval == True
        )
        
        if company_id:
            query = query.filter(AICommand.company_id == company_id)
        
        pending_commands = query.order_by(
            AICommand.priority.asc(),
            AICommand.submitted_at.asc()
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'pending_commands': [cmd.to_dict() for cmd in pending_commands],
            'count': len(pending_commands)
        })
        
    except Exception as e:
        logger.error(f"Error getting pending commands: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/examples', methods=['GET'])
def get_command_examples():
    """Get example commands for different categories"""
    try:
        examples = {
            'query': [
                "Show me all high-risk founders in Q4",
                "What companies have ARR above $1M?",
                "List founders with stress levels above 70%",
                "How many companies are in the SaaS category?",
                "Find portfolio companies with churn rate over 5%"
            ],
            'analysis': [
                "Analyze John's leadership potential",
                "Why did TechCorp's engagement score drop?",
                "Compare stress levels between Q3 and Q4",
                "Explain the correlation between burn rate and runway",
                "Predict which founders are at risk of burnout"
            ],
            'automation': [
                "Create an alert when confidence drops below 80%",
                "Notify me when any founder's stress level exceeds 75%",
                "Set up weekly reports for portfolio performance",
                "Automate risk assessments for new data",
                "Schedule monthly psychological health checks"
            ],
            'modification': [
                "Update Sarah's leadership score to 85",
                "Change TechCorp's business model to SaaS",
                "Set confidence threshold to 90% for financial data",
                "Add new metric definition for customer satisfaction",
                "Remove outdated validation rules"
            ],
            'reporting': [
                "Generate a portfolio health report",
                "Create a dashboard for founder wellness",
                "Export psychological profiles for Q4",
                "Summarize team dynamics for all companies",
                "Brief me on this month's key insights"
            ]
        }
        
        return jsonify({
            'success': True,
            'examples': examples
        })
        
    except Exception as e:
        logger.error(f"Error getting command examples: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/help', methods=['GET'])
def get_help():
    """Get help information for the AI command interface"""
    try:
        help_info = {
            'overview': 'The AI Command Interface allows you to interact with the Elite Command Data API using natural language.',
            'supported_commands': {
                'queries': 'Ask questions about your data using natural language (e.g., "Show me all high-risk founders")',
                'analysis': 'Request analysis and explanations (e.g., "Why did engagement scores drop?")',
                'automation': 'Create rules and alerts (e.g., "Notify me when stress levels are high")',
                'modifications': 'Update data and settings (e.g., "Change the confidence threshold")',
                'reporting': 'Generate reports and summaries (e.g., "Create a portfolio health report")'
            },
            'tips': [
                'Be specific about what you want to know or do',
                'Include company names, time periods, and metrics when relevant',
                'Use natural language - no need for technical syntax',
                'Commands that modify data will require approval',
                'You can reference previous commands in a conversation'
            ],
            'examples_endpoint': '/api/ai/examples'
        }
        
        return jsonify({
            'success': True,
            'help': help_info
        })
        
    except Exception as e:
        logger.error(f"Error getting help: {str(e)}")
        return jsonify({'error': str(e)}), 500

