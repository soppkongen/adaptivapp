from flask import Blueprint, request, jsonify, redirect, session
import requests
import json
import uuid
from datetime import datetime, timedelta
import base64
import hashlib
import hmac
from urllib.parse import urlencode, parse_qs
from src.models.elite_command import (
    db, DataSource, DataIngestionLog, RawDataEntry, 
    MetricSnapshot
)

oauth_bp = Blueprint('oauth', __name__)

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def encrypt_credentials(credentials):
    """Encrypt credentials for secure storage"""
    # In production, use proper encryption like Fernet
    import base64
    return base64.b64encode(json.dumps(credentials).encode()).decode()

def decrypt_credentials(encrypted_credentials):
    """Decrypt stored credentials"""
    # In production, use proper decryption
    import base64
    return json.loads(base64.b64decode(encrypted_credentials.encode()).decode())

@oauth_bp.route('/connect/<platform>', methods=['POST'])
def initiate_oauth_connection(platform):
    """Initiate OAuth connection for supported platforms"""
    try:
        data = request.get_json()
        company_id = data.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'company_id is required'}), 400
        
        # Platform-specific OAuth configurations
        oauth_configs = {
            'notion': {
                'auth_url': 'https://api.notion.com/v1/oauth/authorize',
                'scope': 'read',
                'response_type': 'code'
            },
            'stripe': {
                'auth_url': 'https://connect.stripe.com/oauth/authorize',
                'scope': 'read_only',
                'response_type': 'code'
            },
            'gmail': {
                'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'scope': 'https://www.googleapis.com/auth/gmail.readonly',
                'response_type': 'code'
            },
            'slack': {
                'auth_url': 'https://slack.com/oauth/v2/authorize',
                'scope': 'channels:read,chat:write,users:read',
                'response_type': 'code'
            }
        }
        
        if platform not in oauth_configs:
            return jsonify({'error': f'Platform {platform} not supported'}), 400
        
        config = oauth_configs[platform]
        
        # Generate state parameter for security
        state = generate_uuid()
        session[f'oauth_state_{platform}'] = {
            'state': state,
            'company_id': company_id,
            'platform': platform
        }
        
        # Build authorization URL
        auth_params = {
            'client_id': get_client_id(platform),
            'redirect_uri': get_redirect_uri(platform),
            'scope': config['scope'],
            'response_type': config['response_type'],
            'state': state
        }
        
        auth_url = f"{config['auth_url']}?{urlencode(auth_params)}"
        
        return jsonify({
            'status': 'success',
            'auth_url': auth_url,
            'state': state
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to initiate OAuth connection',
            'error': str(e)
        }), 500

@oauth_bp.route('/callback/<platform>', methods=['GET'])
def oauth_callback(platform):
    """Handle OAuth callback and exchange code for tokens"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'status': 'error',
                'message': f'OAuth error: {error}'
            }), 400
        
        if not code or not state:
            return jsonify({
                'status': 'error',
                'message': 'Missing authorization code or state'
            }), 400
        
        # Verify state parameter
        session_key = f'oauth_state_{platform}'
        if session_key not in session or session[session_key]['state'] != state:
            return jsonify({
                'status': 'error',
                'message': 'Invalid state parameter'
            }), 400
        
        oauth_session = session[session_key]
        company_id = oauth_session['company_id']
        
        # Exchange code for access token
        token_data = exchange_code_for_token(platform, code)
        
        if not token_data:
            return jsonify({
                'status': 'error',
                'message': 'Failed to exchange code for token'
            }), 500
        
        # Create data source with OAuth credentials
        source = DataSource(
            id=generate_uuid(),
            company_id=company_id,
            name=f"{platform.title()} Integration",
            source_type='oauth',
            config=json.dumps({
                'platform': platform,
                'oauth_version': '2.0',
                'scopes': token_data.get('scope', '').split(',') if token_data.get('scope') else []
            }),
            credentials=encrypt_credentials(token_data),
            is_active=True
        )
        
        db.session.add(source)
        db.session.commit()
        
        # Clean up session
        del session[session_key]
        
        # Perform initial data sync
        sync_result = perform_initial_sync(source)
        
        return jsonify({
            'status': 'success',
            'message': f'{platform.title()} connected successfully',
            'source_id': source.id,
            'initial_sync': sync_result
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'OAuth callback failed',
            'error': str(e)
        }), 500

def get_client_id(platform):
    """Get OAuth client ID for platform"""
    # In production, these would be environment variables
    client_ids = {
        'notion': 'your_notion_client_id',
        'stripe': 'your_stripe_client_id',
        'gmail': 'your_google_client_id',
        'slack': 'your_slack_client_id'
    }
    return client_ids.get(platform)

def get_client_secret(platform):
    """Get OAuth client secret for platform"""
    # In production, these would be environment variables
    client_secrets = {
        'notion': 'your_notion_client_secret',
        'stripe': 'your_stripe_client_secret',
        'gmail': 'your_google_client_secret',
        'slack': 'your_slack_client_secret'
    }
    return client_secrets.get(platform)

def get_redirect_uri(platform):
    """Get OAuth redirect URI for platform"""
    base_url = 'https://your-domain.com'  # In production, use actual domain
    return f"{base_url}/api/oauth/callback/{platform}"

def exchange_code_for_token(platform, code):
    """Exchange authorization code for access token"""
    try:
        token_urls = {
            'notion': 'https://api.notion.com/v1/oauth/token',
            'stripe': 'https://connect.stripe.com/oauth/token',
            'gmail': 'https://oauth2.googleapis.com/token',
            'slack': 'https://slack.com/api/oauth.v2.access'
        }
        
        if platform not in token_urls:
            return None
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': get_redirect_uri(platform),
            'client_id': get_client_id(platform),
            'client_secret': get_client_secret(platform)
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        if platform == 'notion':
            # Notion requires basic auth
            auth_string = f"{get_client_id(platform)}:{get_client_secret(platform)}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            headers['Authorization'] = f'Basic {auth_bytes}'
        
        response = requests.post(token_urls[platform], data=token_data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Token exchange failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error exchanging code for token: {e}")
        return None

def perform_initial_sync(data_source):
    """Perform initial data synchronization for newly connected source"""
    try:
        config = json.loads(data_source.config)
        platform = config['platform']
        
        log_entry = DataIngestionLog(
            id=generate_uuid(),
            source_id=data_source.id,
            ingestion_type='initial_sync',
            status='processing',
            started_at=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        processed_count = 0
        
        if platform == 'notion':
            processed_count = sync_notion_data(data_source, log_entry.id)
        elif platform == 'stripe':
            processed_count = sync_stripe_data(data_source, log_entry.id)
        elif platform == 'gmail':
            processed_count = sync_gmail_data(data_source, log_entry.id)
        elif platform == 'slack':
            processed_count = sync_slack_data(data_source, log_entry.id)
        
        # Complete logging
        log_entry.status = 'success'
        log_entry.completed_at = datetime.utcnow()
        log_entry.processing_duration = (log_entry.completed_at - log_entry.started_at).total_seconds()
        log_entry.records_processed = processed_count
        log_entry.records_successful = processed_count
        
        data_source.last_successful_sync = datetime.utcnow()
        db.session.commit()
        
        return {
            'status': 'success',
            'records_synced': processed_count,
            'sync_id': log_entry.id
        }
        
    except Exception as e:
        log_entry.status = 'error'
        log_entry.error_message = str(e)
        log_entry.completed_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'status': 'error',
            'message': str(e),
            'sync_id': log_entry.id
        }

def sync_notion_data(data_source, ingestion_log_id):
    """Sync data from Notion"""
    try:
        credentials = decrypt_credentials(data_source.credentials)
        access_token = credentials['access_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        # Get list of databases
        response = requests.post(
            'https://api.notion.com/v1/search',
            headers=headers,
            json={'filter': {'property': 'object', 'value': 'database'}}
        )
        
        if response.status_code != 200:
            return 0
        
        databases = response.json().get('results', [])
        processed_count = 0
        
        for database in databases:
            # Query database for pages
            db_response = requests.post(
                f"https://api.notion.com/v1/databases/{database['id']}/query",
                headers=headers,
                json={'page_size': 100}
            )
            
            if db_response.status_code == 200:
                pages = db_response.json().get('results', [])
                
                for page in pages:
                    # Create raw data entry
                    raw_entry = RawDataEntry(
                        id=generate_uuid(),
                        source_id=data_source.id,
                        ingestion_log_id=ingestion_log_id,
                        raw_data=json.dumps(page),
                        data_type='notion_page',
                        source_timestamp=datetime.utcnow(),
                        confidence_score=1.0,
                        tags=json.dumps(['notion', 'page', database.get('title', [{}])[0].get('plain_text', 'untitled')])
                    )
                    db.session.add(raw_entry)
                    
                    # Extract metrics from page properties
                    metrics = extract_notion_metrics(page)
                    if metrics:
                        create_metric_snapshot(data_source.company_id, metrics, data_source.id)
                    
                    processed_count += 1
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error syncing Notion data: {e}")
        return 0

def sync_stripe_data(data_source, ingestion_log_id):
    """Sync data from Stripe"""
    try:
        credentials = decrypt_credentials(data_source.credentials)
        access_token = credentials['access_token']
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get recent charges
        response = requests.get(
            'https://api.stripe.com/v1/charges',
            headers=headers,
            params={'limit': 100, 'created[gte]': int((datetime.utcnow() - timedelta(days=30)).timestamp())}
        )
        
        if response.status_code != 200:
            return 0
        
        charges = response.json().get('data', [])
        processed_count = 0
        
        for charge in charges:
            # Create raw data entry
            raw_entry = RawDataEntry(
                id=generate_uuid(),
                source_id=data_source.id,
                ingestion_log_id=ingestion_log_id,
                raw_data=json.dumps(charge),
                data_type='stripe_charge',
                source_timestamp=datetime.fromtimestamp(charge['created']),
                confidence_score=1.0,
                tags=json.dumps(['stripe', 'charge', 'financial'])
            )
            db.session.add(raw_entry)
            
            # Extract financial metrics
            metrics = {
                'revenue': charge['amount'] / 100,  # Convert from cents
                'currency': charge['currency'],
                'customer_id': charge.get('customer'),
                'payment_method': charge.get('payment_method_details', {}).get('type'),
                'status': charge['status'],
                'timestamp': datetime.fromtimestamp(charge['created']).isoformat()
            }
            
            create_metric_snapshot(data_source.company_id, metrics, data_source.id)
            processed_count += 1
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error syncing Stripe data: {e}")
        return 0

def sync_gmail_data(data_source, ingestion_log_id):
    """Sync data from Gmail"""
    try:
        credentials = decrypt_credentials(data_source.credentials)
        access_token = credentials['access_token']
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get recent messages
        response = requests.get(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages',
            headers=headers,
            params={'maxResults': 50, 'q': 'is:unread'}
        )
        
        if response.status_code != 200:
            return 0
        
        messages = response.json().get('messages', [])
        processed_count = 0
        
        for message in messages[:10]:  # Limit to 10 for initial sync
            # Get message details
            msg_response = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message['id']}",
                headers=headers
            )
            
            if msg_response.status_code == 200:
                msg_data = msg_response.json()
                
                # Create raw data entry
                raw_entry = RawDataEntry(
                    id=generate_uuid(),
                    source_id=data_source.id,
                    ingestion_log_id=ingestion_log_id,
                    raw_data=json.dumps(msg_data),
                    data_type='gmail_message',
                    source_timestamp=datetime.utcnow(),
                    confidence_score=0.8,
                    tags=json.dumps(['gmail', 'email', 'communication'])
                )
                db.session.add(raw_entry)
                
                # Extract communication metrics
                headers_data = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                
                metrics = {
                    'email_received': True,
                    'sender': headers_data.get('From', ''),
                    'subject': headers_data.get('Subject', ''),
                    'thread_id': msg_data.get('threadId'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                create_metric_snapshot(data_source.company_id, metrics, data_source.id)
                processed_count += 1
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error syncing Gmail data: {e}")
        return 0

def sync_slack_data(data_source, ingestion_log_id):
    """Sync data from Slack"""
    try:
        credentials = decrypt_credentials(data_source.credentials)
        access_token = credentials['access_token']
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get channels
        response = requests.get(
            'https://slack.com/api/conversations.list',
            headers=headers,
            params={'types': 'public_channel,private_channel'}
        )
        
        if response.status_code != 200:
            return 0
        
        channels = response.json().get('channels', [])
        processed_count = 0
        
        for channel in channels[:5]:  # Limit to 5 channels for initial sync
            # Get recent messages from channel
            msg_response = requests.get(
                'https://slack.com/api/conversations.history',
                headers=headers,
                params={'channel': channel['id'], 'limit': 20}
            )
            
            if msg_response.status_code == 200:
                messages = msg_response.json().get('messages', [])
                
                for message in messages:
                    # Create raw data entry
                    raw_entry = RawDataEntry(
                        id=generate_uuid(),
                        source_id=data_source.id,
                        ingestion_log_id=ingestion_log_id,
                        raw_data=json.dumps(message),
                        data_type='slack_message',
                        source_timestamp=datetime.fromtimestamp(float(message.get('ts', 0))),
                        confidence_score=0.9,
                        tags=json.dumps(['slack', 'message', 'team_communication'])
                    )
                    db.session.add(raw_entry)
                    
                    # Extract team communication metrics
                    metrics = {
                        'slack_message': True,
                        'channel': channel['name'],
                        'user': message.get('user'),
                        'message_type': message.get('type'),
                        'has_attachments': bool(message.get('files')),
                        'timestamp': datetime.fromtimestamp(float(message.get('ts', 0))).isoformat()
                    }
                    
                    create_metric_snapshot(data_source.company_id, metrics, data_source.id)
                    processed_count += 1
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error syncing Slack data: {e}")
        return 0

def extract_notion_metrics(page):
    """Extract metrics from Notion page properties"""
    properties = page.get('properties', {})
    metrics = {}
    
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get('type')
        
        if prop_type == 'number':
            value = prop_data.get('number')
            if value is not None:
                metrics[prop_name.lower().replace(' ', '_')] = value
        elif prop_type == 'select':
            select_data = prop_data.get('select')
            if select_data:
                metrics[f"{prop_name.lower().replace(' ', '_')}_status"] = select_data.get('name')
        elif prop_type == 'date':
            date_data = prop_data.get('date')
            if date_data:
                metrics[f"{prop_name.lower().replace(' ', '_')}_date"] = date_data.get('start')
    
    if metrics:
        metrics['notion_page_id'] = page['id']
        metrics['timestamp'] = datetime.utcnow().isoformat()
    
    return metrics if metrics else None

def create_metric_snapshot(company_id, metrics, source_id):
    """Create a metric snapshot from processed data"""
    snapshot = MetricSnapshot(
        id=generate_uuid(),
        company_id=company_id,
        metrics=json.dumps(metrics),
        snapshot_date=datetime.utcnow(),
        source_id=source_id,
        confidence_score=0.9
    )
    
    db.session.add(snapshot)

@oauth_bp.route('/sync/<source_id>', methods=['POST'])
def manual_sync(source_id):
    """Manually trigger data synchronization for a source"""
    try:
        data_source = DataSource.query.get(source_id)
        if not data_source:
            return jsonify({'error': 'Data source not found'}), 404
        
        if data_source.source_type != 'oauth':
            return jsonify({'error': 'Source is not an OAuth integration'}), 400
        
        sync_result = perform_initial_sync(data_source)
        
        return jsonify({
            'status': 'success',
            'message': 'Manual sync completed',
            'result': sync_result
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Manual sync failed',
            'error': str(e)
        }), 500

@oauth_bp.route('/disconnect/<source_id>', methods=['DELETE'])
def disconnect_oauth_source(source_id):
    """Disconnect an OAuth integration"""
    try:
        data_source = DataSource.query.get(source_id)
        if not data_source:
            return jsonify({'error': 'Data source not found'}), 404
        
        # Revoke OAuth token if possible
        try:
            config = json.loads(data_source.config)
            platform = config['platform']
            credentials = decrypt_credentials(data_source.credentials)
            
            revoke_oauth_token(platform, credentials)
        except Exception as e:
            print(f"Error revoking OAuth token: {e}")
        
        # Deactivate the data source
        data_source.is_active = False
        data_source.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'OAuth integration disconnected successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to disconnect OAuth integration',
            'error': str(e)
        }), 500

def revoke_oauth_token(platform, credentials):
    """Revoke OAuth token for platform"""
    revoke_urls = {
        'gmail': 'https://oauth2.googleapis.com/revoke',
        'slack': 'https://slack.com/api/auth.revoke'
    }
    
    if platform in revoke_urls:
        access_token = credentials.get('access_token')
        if access_token:
            requests.post(revoke_urls[platform], data={'token': access_token})

