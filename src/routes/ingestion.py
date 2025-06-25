from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import uuid
import hashlib
import hmac
from src.models.elite_command import (
    db, DataSource, DataIngestionLog, RawDataEntry, 
    Company, MetricSnapshot
)

ingestion_bp = Blueprint('ingestion', __name__)

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def validate_webhook_signature(payload, signature, secret):
    """Validate webhook signature for security"""
    if not signature or not secret:
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def log_ingestion_start(source_id, ingestion_type):
    """Create an ingestion log entry"""
    log_entry = DataIngestionLog(
        id=generate_uuid(),
        source_id=source_id,
        ingestion_type=ingestion_type,
        status='processing',
        started_at=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry

def log_ingestion_complete(log_entry, status, records_processed=0, records_successful=0, records_failed=0, error_message=None):
    """Complete an ingestion log entry"""
    log_entry.status = status
    log_entry.completed_at = datetime.utcnow()
    log_entry.processing_duration = (log_entry.completed_at - log_entry.started_at).total_seconds()
    log_entry.records_processed = records_processed
    log_entry.records_successful = records_successful
    log_entry.records_failed = records_failed
    if error_message:
        log_entry.error_message = error_message
    db.session.commit()

@ingestion_bp.route('/webhook/<source_id>', methods=['POST'])
def receive_webhook(source_id):
    """Generic webhook endpoint for receiving data from various sources"""
    try:
        # Validate source exists
        data_source = DataSource.query.get(source_id)
        if not data_source:
            return jsonify({'error': 'Invalid source ID'}), 404
        
        if not data_source.is_active:
            return jsonify({'error': 'Data source is inactive'}), 403
        
        # Get webhook payload
        payload = request.get_data()
        headers = dict(request.headers)
        
        # Validate signature if configured
        config = json.loads(data_source.config) if data_source.config else {}
        webhook_secret = config.get('webhook_secret')
        signature = headers.get('X-Hub-Signature-256', '').replace('sha256=', '')
        
        if webhook_secret and not validate_webhook_signature(payload, signature, webhook_secret):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Start ingestion logging
        log_entry = log_ingestion_start(source_id, 'webhook')
        
        try:
            # Parse JSON payload
            data = request.get_json()
            if not data:
                raise ValueError("Invalid JSON payload")
            
            # Create raw data entry
            raw_entry = RawDataEntry(
                id=generate_uuid(),
                source_id=source_id,
                ingestion_log_id=log_entry.id,
                raw_data=json.dumps(data),
                data_type=detect_data_type(data),
                source_timestamp=datetime.utcnow(),
                confidence_score=1.0,
                tags=json.dumps(['webhook', data_source.name])
            )
            
            db.session.add(raw_entry)
            db.session.commit()
            
            # Process the data based on source type
            processed_count = process_webhook_data(data_source, data, raw_entry.id)
            
            # Update data source reliability
            data_source.last_successful_sync = datetime.utcnow()
            data_source.error_count = 0
            db.session.commit()
            
            # Complete logging
            log_ingestion_complete(log_entry, 'success', 1, processed_count, 0)
            
            return jsonify({
                'status': 'success',
                'message': 'Webhook data received and processed',
                'ingestion_id': log_entry.id,
                'records_processed': processed_count
            }), 200
            
        except Exception as e:
            # Update error count
            data_source.error_count += 1
            db.session.commit()
            
            # Complete logging with error
            log_ingestion_complete(log_entry, 'error', 1, 0, 1, str(e))
            
            return jsonify({
                'status': 'error',
                'message': 'Failed to process webhook data',
                'error': str(e),
                'ingestion_id': log_entry.id
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Webhook processing failed',
            'error': str(e)
        }), 500

def detect_data_type(data):
    """Detect the type of data based on content"""
    if isinstance(data, dict):
        # Check for common financial metrics
        financial_keys = ['revenue', 'arr', 'mrr', 'churn', 'ltv', 'cac', 'burn_rate']
        if any(key in str(data).lower() for key in financial_keys):
            return 'financial'
        
        # Check for operational metrics
        operational_keys = ['users', 'sessions', 'conversion', 'engagement', 'retention']
        if any(key in str(data).lower() for key in operational_keys):
            return 'operational'
        
        # Check for customer data
        customer_keys = ['customer', 'user', 'subscriber', 'account']
        if any(key in str(data).lower() for key in customer_keys):
            return 'customer'
        
        # Check for team/hr data
        team_keys = ['employee', 'team', 'headcount', 'hiring']
        if any(key in str(data).lower() for key in team_keys):
            return 'team'
    
    return 'general'

def process_webhook_data(data_source, data, raw_entry_id):
    """Process webhook data based on source configuration"""
    config = json.loads(data_source.config) if data_source.config else {}
    source_type = config.get('source_type', 'generic')
    
    processed_count = 0
    
    try:
        if source_type == 'stripe':
            processed_count = process_stripe_webhook(data_source, data, raw_entry_id)
        elif source_type == 'notion':
            processed_count = process_notion_webhook(data_source, data, raw_entry_id)
        elif source_type == 'slack':
            processed_count = process_slack_webhook(data_source, data, raw_entry_id)
        elif source_type == 'custom_metrics':
            processed_count = process_custom_metrics(data_source, data, raw_entry_id)
        else:
            # Generic processing
            processed_count = process_generic_webhook(data_source, data, raw_entry_id)
        
        return processed_count
        
    except Exception as e:
        print(f"Error processing webhook data: {e}")
        return 0

def process_stripe_webhook(data_source, data, raw_entry_id):
    """Process Stripe webhook data"""
    event_type = data.get('type', '')
    
    if event_type.startswith('invoice.'):
        # Process invoice events for revenue tracking
        invoice_data = data.get('data', {}).get('object', {})
        amount = invoice_data.get('amount_paid', 0) / 100  # Convert from cents
        
        if amount > 0:
            # Create metric snapshot
            metrics = {
                'revenue': amount,
                'currency': invoice_data.get('currency', 'usd'),
                'customer_id': invoice_data.get('customer'),
                'subscription_id': invoice_data.get('subscription'),
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            create_metric_snapshot(data_source.company_id, metrics, data_source.id)
            return 1
    
    elif event_type.startswith('customer.'):
        # Process customer events
        customer_data = data.get('data', {}).get('object', {})
        
        metrics = {
            'customer_event': event_type,
            'customer_id': customer_data.get('id'),
            'customer_email': customer_data.get('email'),
            'created': customer_data.get('created'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        create_metric_snapshot(data_source.company_id, metrics, data_source.id)
        return 1
    
    return 0

def process_notion_webhook(data_source, data, raw_entry_id):
    """Process Notion webhook data"""
    # Notion doesn't have native webhooks, but this handles custom integrations
    if 'page' in data or 'database' in data:
        metrics = {
            'notion_update': True,
            'object_type': data.get('object', 'unknown'),
            'last_edited_time': data.get('last_edited_time'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        create_metric_snapshot(data_source.company_id, metrics, data_source.id)
        return 1
    
    return 0

def process_slack_webhook(data_source, data, raw_entry_id):
    """Process Slack webhook data"""
    if data.get('type') == 'message':
        # Process team communication metrics
        metrics = {
            'slack_message': True,
            'channel': data.get('channel'),
            'user': data.get('user'),
            'timestamp': data.get('ts'),
            'message_type': data.get('subtype', 'normal')
        }
        
        create_metric_snapshot(data_source.company_id, metrics, data_source.id)
        return 1
    
    return 0

def process_custom_metrics(data_source, data, raw_entry_id):
    """Process custom metrics from business tools"""
    if 'metrics' in data:
        metrics = data['metrics']
        metrics['timestamp'] = datetime.utcnow().isoformat()
        metrics['source'] = 'custom'
        
        create_metric_snapshot(data_source.company_id, metrics, data_source.id)
        return 1
    
    return 0

def process_generic_webhook(data_source, data, raw_entry_id):
    """Generic webhook processing for unknown sources"""
    # Extract any numeric values that might be metrics
    metrics = {}
    
    def extract_metrics(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (int, float)) and value != 0:
                    metric_key = f"{prefix}{key}" if prefix else key
                    metrics[metric_key] = value
                elif isinstance(value, dict):
                    extract_metrics(value, f"{prefix}{key}_" if prefix else f"{key}_")
    
    extract_metrics(data)
    
    if metrics:
        metrics['timestamp'] = datetime.utcnow().isoformat()
        metrics['source'] = 'generic_webhook'
        
        create_metric_snapshot(data_source.company_id, metrics, data_source.id)
        return 1
    
    return 0

def create_metric_snapshot(company_id, metrics, source_id):
    """Create a metric snapshot from processed data"""
    snapshot = MetricSnapshot(
        id=generate_uuid(),
        company_id=company_id,
        metrics=json.dumps(metrics),
        snapshot_date=datetime.utcnow(),
        source_id=source_id,
        confidence_score=1.0
    )
    
    db.session.add(snapshot)
    db.session.commit()

@ingestion_bp.route('/webhook/<source_id>/test', methods=['POST'])
def test_webhook(source_id):
    """Test webhook endpoint for validation"""
    try:
        data_source = DataSource.query.get(source_id)
        if not data_source:
            return jsonify({'error': 'Invalid source ID'}), 404
        
        test_data = request.get_json() or {'test': True, 'timestamp': datetime.utcnow().isoformat()}
        
        return jsonify({
            'status': 'success',
            'message': 'Webhook test successful',
            'source_id': source_id,
            'source_name': data_source.name,
            'received_data': test_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Webhook test failed',
            'error': str(e)
        }), 500

@ingestion_bp.route('/sources', methods=['GET'])
def list_data_sources():
    """List all data sources"""
    try:
        sources = DataSource.query.all()
        return jsonify({
            'status': 'success',
            'sources': [source.to_dict() for source in sources]
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve data sources',
            'error': str(e)
        }), 500

@ingestion_bp.route('/sources', methods=['POST'])
def create_data_source():
    """Create a new data source"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['company_id', 'name', 'source_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new data source
        source = DataSource(
            id=generate_uuid(),
            company_id=data['company_id'],
            name=data['name'],
            source_type=data['source_type'],
            config=json.dumps(data.get('config', {})),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(source)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Data source created successfully',
            'source': source.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to create data source',
            'error': str(e)
        }), 500

@ingestion_bp.route('/sources/<source_id>', methods=['PUT'])
def update_data_source(source_id):
    """Update a data source"""
    try:
        source = DataSource.query.get(source_id)
        if not source:
            return jsonify({'error': 'Data source not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            source.name = data['name']
        if 'config' in data:
            source.config = json.dumps(data['config'])
        if 'is_active' in data:
            source.is_active = data['is_active']
        
        source.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Data source updated successfully',
            'source': source.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to update data source',
            'error': str(e)
        }), 500

@ingestion_bp.route('/logs', methods=['GET'])
def get_ingestion_logs():
    """Get ingestion logs with optional filtering"""
    try:
        # Get query parameters
        source_id = request.args.get('source_id')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = DataIngestionLog.query
        
        if source_id:
            query = query.filter(DataIngestionLog.source_id == source_id)
        if status:
            query = query.filter(DataIngestionLog.status == status)
        
        # Order by most recent and limit
        logs = query.order_by(DataIngestionLog.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'logs': [log.to_dict() for log in logs]
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve ingestion logs',
            'error': str(e)
        }), 500

