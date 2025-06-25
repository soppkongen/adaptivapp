from flask import Blueprint, request, jsonify
import email
import json
import uuid
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
from src.models.elite_command import (
    db, DataSource, DataIngestionLog, RawDataEntry, 
    MetricSnapshot
)

email_processing_bp = Blueprint('email_processing', __name__)

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

@email_processing_bp.route('/email/ingest', methods=['POST'])
def ingest_email():
    """Main endpoint for email ingestion (e.g., report@elitecmd.io)"""
    try:
        # Get email data from request
        email_data = request.get_json()
        
        if not email_data:
            # Try to parse raw email if JSON not provided
            raw_email = request.get_data(as_text=True)
            if raw_email:
                email_data = parse_raw_email(raw_email)
            else:
                return jsonify({'error': 'No email data provided'}), 400
        
        # Extract email components
        sender = email_data.get('from', '')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        attachments = email_data.get('attachments', [])
        received_date = email_data.get('date', datetime.utcnow().isoformat())
        
        # Identify company/source based on sender or subject
        company_id, source_id = identify_email_source(sender, subject, body)
        
        if not company_id:
            return jsonify({
                'status': 'warning',
                'message': 'Could not identify company for email',
                'sender': sender,
                'subject': subject
            }), 200
        
        # Create or get email data source
        if not source_id:
            source_id = create_email_data_source(company_id, sender)
        
        # Start ingestion logging
        log_entry = DataIngestionLog(
            id=generate_uuid(),
            source_id=source_id,
            ingestion_type='email',
            status='processing',
            started_at=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        processed_count = 0
        
        try:
            # Create raw data entry for the email
            raw_entry = RawDataEntry(
                id=generate_uuid(),
                source_id=source_id,
                ingestion_log_id=log_entry.id,
                raw_data=json.dumps(email_data),
                data_type='email',
                source_timestamp=datetime.fromisoformat(received_date.replace('Z', '+00:00')) if 'T' in received_date else datetime.utcnow(),
                confidence_score=0.8,
                tags=json.dumps(['email', 'report', classify_email_type(subject, body)])
            )
            db.session.add(raw_entry)
            
            # Process email content
            metrics = process_email_content(subject, body, sender)
            if metrics:
                create_metric_snapshot(company_id, metrics, source_id)
                processed_count += 1
            
            # Process attachments
            for attachment in attachments:
                attachment_metrics = process_email_attachment(attachment, company_id, source_id, log_entry.id)
                if attachment_metrics:
                    processed_count += 1
            
            # Complete logging
            log_entry.status = 'success'
            log_entry.completed_at = datetime.utcnow()
            log_entry.processing_duration = (log_entry.completed_at - log_entry.started_at).total_seconds()
            log_entry.records_processed = 1
            log_entry.records_successful = processed_count
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Email processed successfully',
                'ingestion_id': log_entry.id,
                'records_processed': processed_count,
                'company_id': company_id,
                'source_id': source_id
            }), 200
            
        except Exception as e:
            # Complete logging with error
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            log_entry.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'message': 'Failed to process email',
                'error': str(e),
                'ingestion_id': log_entry.id
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Email ingestion failed',
            'error': str(e)
        }), 500

def parse_raw_email(raw_email):
    """Parse raw email content into structured data"""
    try:
        msg = email.message_from_string(raw_email)
        
        email_data = {
            'from': msg.get('From', ''),
            'to': msg.get('To', ''),
            'subject': msg.get('Subject', ''),
            'date': msg.get('Date', ''),
            'message_id': msg.get('Message-ID', ''),
            'body': '',
            'attachments': []
        }
        
        # Extract body content
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    email_data['body'] += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == 'text/html':
                    # Could add HTML parsing here
                    pass
                elif part.get_filename():
                    # Handle attachments
                    attachment = {
                        'filename': part.get_filename(),
                        'content_type': content_type,
                        'content': base64.b64encode(part.get_payload(decode=True)).decode('utf-8')
                    }
                    email_data['attachments'].append(attachment)
        else:
            email_data['body'] = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return email_data
        
    except Exception as e:
        print(f"Error parsing raw email: {e}")
        return None

def identify_email_source(sender, subject, body):
    """Identify company and data source based on email content"""
    try:
        # Look for existing data sources with matching email patterns
        email_domain = sender.split('@')[-1] if '@' in sender else ''
        
        # Search for data sources with email configuration
        sources = DataSource.query.filter(
            DataSource.source_type == 'email',
            DataSource.is_active == True
        ).all()
        
        for source in sources:
            config = json.loads(source.config) if source.config else {}
            
            # Check if sender matches configured patterns
            allowed_senders = config.get('allowed_senders', [])
            allowed_domains = config.get('allowed_domains', [])
            
            if sender in allowed_senders or email_domain in allowed_domains:
                return source.company_id, source.id
            
            # Check subject patterns
            subject_patterns = config.get('subject_patterns', [])
            for pattern in subject_patterns:
                if re.search(pattern, subject, re.IGNORECASE):
                    return source.company_id, source.id
        
        # If no existing source found, try to identify company by domain or keywords
        company_id = identify_company_by_email(sender, subject, body)
        
        return company_id, None
        
    except Exception as e:
        print(f"Error identifying email source: {e}")
        return None, None

def identify_company_by_email(sender, subject, body):
    """Identify company based on email characteristics"""
    try:
        from src.models.elite_command import Company
        
        # Extract domain from sender
        email_domain = sender.split('@')[-1] if '@' in sender else ''
        
        # Look for companies with matching domain
        companies = Company.query.all()
        
        for company in companies:
            if company.domain and email_domain in company.domain:
                return company.id
            
            # Check if company name appears in subject or body
            if company.name.lower() in subject.lower() or company.name.lower() in body.lower():
                return company.id
        
        # Could implement more sophisticated matching here
        return None
        
    except Exception as e:
        print(f"Error identifying company by email: {e}")
        return None

def create_email_data_source(company_id, sender):
    """Create a new email data source for unrecognized sender"""
    try:
        email_domain = sender.split('@')[-1] if '@' in sender else 'unknown'
        
        source = DataSource(
            id=generate_uuid(),
            company_id=company_id,
            name=f"Email from {email_domain}",
            source_type='email',
            config=json.dumps({
                'allowed_senders': [sender],
                'allowed_domains': [email_domain],
                'auto_created': True
            }),
            is_active=True
        )
        
        db.session.add(source)
        db.session.commit()
        
        return source.id
        
    except Exception as e:
        print(f"Error creating email data source: {e}")
        return None

def classify_email_type(subject, body):
    """Classify email type based on content"""
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    # Financial report patterns
    financial_keywords = ['revenue', 'profit', 'loss', 'financial', 'earnings', 'income', 'expense']
    if any(keyword in subject_lower or keyword in body_lower for keyword in financial_keywords):
        return 'financial_report'
    
    # Operational update patterns
    operational_keywords = ['update', 'status', 'progress', 'metrics', 'kpi', 'performance']
    if any(keyword in subject_lower for keyword in operational_keywords):
        return 'operational_update'
    
    # Investor update patterns
    investor_keywords = ['investor', 'board', 'monthly', 'quarterly', 'update']
    if any(keyword in subject_lower for keyword in investor_keywords):
        return 'investor_update'
    
    # Alert/incident patterns
    alert_keywords = ['alert', 'urgent', 'incident', 'down', 'error', 'critical']
    if any(keyword in subject_lower for keyword in alert_keywords):
        return 'alert'
    
    return 'general'

def process_email_content(subject, body, sender):
    """Extract metrics and insights from email content"""
    try:
        metrics = {
            'email_type': classify_email_type(subject, body),
            'sender': sender,
            'subject': subject,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Extract numerical metrics from body
        extracted_metrics = extract_metrics_from_text(body)
        if extracted_metrics:
            metrics.update(extracted_metrics)
        
        # Extract dates and time periods
        time_periods = extract_time_periods(subject, body)
        if time_periods:
            metrics['reporting_period'] = time_periods
        
        # Extract sentiment and urgency
        sentiment = analyze_email_sentiment(subject, body)
        metrics['sentiment'] = sentiment
        
        urgency = assess_email_urgency(subject, body)
        metrics['urgency_level'] = urgency
        
        return metrics
        
    except Exception as e:
        print(f"Error processing email content: {e}")
        return None

def extract_metrics_from_text(text):
    """Extract numerical metrics from text content"""
    metrics = {}
    
    # Common business metrics patterns
    patterns = {
        'revenue': r'revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'arr': r'arr[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'mrr': r'mrr[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'churn': r'churn[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
        'users': r'(?:active\s+)?users?[:\s]+([0-9,]+)',
        'customers': r'customers?[:\s]+([0-9,]+)',
        'growth': r'growth[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
        'conversion': r'conversion[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
        'cac': r'cac[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'ltv': r'ltv[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'burn_rate': r'burn[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'runway': r'runway[:\s]+([0-9]+(?:\.[0-9]+)?)\s*months?'
    }
    
    text_lower = text.lower()
    
    for metric_name, pattern in patterns.items():
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            try:
                value_str = matches[0].replace(',', '')
                value = float(value_str)
                metrics[metric_name] = value
            except ValueError:
                continue
    
    # Extract percentage changes
    change_patterns = {
        'revenue_change': r'revenue.*?(?:up|down|increased?|decreased?)\s+([0-9]+(?:\.[0-9]+)?)%',
        'user_growth': r'users?.*?(?:up|down|increased?|decreased?)\s+([0-9]+(?:\.[0-9]+)?)%',
        'conversion_change': r'conversion.*?(?:up|down|increased?|decreased?)\s+([0-9]+(?:\.[0-9]+)?)%'
    }
    
    for metric_name, pattern in change_patterns.items():
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            try:
                value = float(matches[0])
                # Determine if it's positive or negative based on context
                if 'down' in text_lower or 'decreased' in text_lower:
                    value = -value
                metrics[metric_name] = value
            except ValueError:
                continue
    
    return metrics if metrics else None

def extract_time_periods(subject, body):
    """Extract time periods mentioned in email"""
    time_patterns = [
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
        r'q[1-4]\s+(\d{4})',
        r'(\d{1,2})/(\d{4})',
        r'week\s+of\s+(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4})-(\d{2})-(\d{2})'
    ]
    
    text = f"{subject} {body}".lower()
    periods = []
    
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        periods.extend(matches)
    
    return periods if periods else None

def analyze_email_sentiment(subject, body):
    """Analyze sentiment of email content"""
    positive_words = ['good', 'great', 'excellent', 'positive', 'growth', 'success', 'achievement', 'milestone']
    negative_words = ['bad', 'poor', 'negative', 'decline', 'loss', 'problem', 'issue', 'concern', 'urgent']
    
    text = f"{subject} {body}".lower()
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'

def assess_email_urgency(subject, body):
    """Assess urgency level of email"""
    urgent_words = ['urgent', 'critical', 'immediate', 'asap', 'emergency', 'alert']
    high_priority_words = ['important', 'priority', 'attention', 'action required']
    
    text = f"{subject} {body}".lower()
    
    if any(word in text for word in urgent_words):
        return 'urgent'
    elif any(word in text for word in high_priority_words):
        return 'high'
    else:
        return 'normal'

def process_email_attachment(attachment, company_id, source_id, ingestion_log_id):
    """Process email attachments"""
    try:
        filename = attachment.get('filename', '')
        content_type = attachment.get('content_type', '')
        content = attachment.get('content', '')
        
        # Decode base64 content
        try:
            decoded_content = base64.b64decode(content)
        except Exception:
            return None
        
        # Create raw data entry for attachment
        raw_entry = RawDataEntry(
            id=generate_uuid(),
            source_id=source_id,
            ingestion_log_id=ingestion_log_id,
            raw_data=json.dumps({
                'filename': filename,
                'content_type': content_type,
                'size': len(decoded_content)
            }),
            data_type='email_attachment',
            source_timestamp=datetime.utcnow(),
            confidence_score=0.7,
            tags=json.dumps(['email', 'attachment', content_type])
        )
        db.session.add(raw_entry)
        
        # Process based on file type
        if content_type == 'text/csv' or filename.endswith('.csv'):
            return process_csv_attachment(decoded_content, company_id, source_id)
        elif content_type == 'application/pdf' or filename.endswith('.pdf'):
            return process_pdf_attachment(decoded_content, company_id, source_id)
        elif 'spreadsheet' in content_type or filename.endswith(('.xlsx', '.xls')):
            return process_excel_attachment(decoded_content, company_id, source_id)
        
        return None
        
    except Exception as e:
        print(f"Error processing email attachment: {e}")
        return None

def process_csv_attachment(content, company_id, source_id):
    """Process CSV attachment content"""
    try:
        import io
        import pandas as pd
        
        # Read CSV from bytes
        csv_data = pd.read_csv(io.BytesIO(content))
        
        # Process each row as metrics
        for index, row in csv_data.iterrows():
            row_dict = row.to_dict()
            cleaned_dict = {k: v for k, v in row_dict.items() if pd.notna(v)}
            
            if cleaned_dict:
                cleaned_dict['source'] = 'email_csv_attachment'
                cleaned_dict['row_index'] = index
                cleaned_dict['timestamp'] = datetime.utcnow().isoformat()
                
                create_metric_snapshot(company_id, cleaned_dict, source_id)
        
        return len(csv_data)
        
    except Exception as e:
        print(f"Error processing CSV attachment: {e}")
        return None

def process_pdf_attachment(content, company_id, source_id):
    """Process PDF attachment content"""
    try:
        import PyPDF2
        import io
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()
        
        # Extract metrics from PDF text
        metrics = extract_metrics_from_text(full_text)
        if metrics:
            metrics['source'] = 'email_pdf_attachment'
            metrics['page_count'] = len(pdf_reader.pages)
            metrics['timestamp'] = datetime.utcnow().isoformat()
            
            create_metric_snapshot(company_id, metrics, source_id)
            return 1
        
        return None
        
    except Exception as e:
        print(f"Error processing PDF attachment: {e}")
        return None

def process_excel_attachment(content, company_id, source_id):
    """Process Excel attachment content"""
    try:
        import pandas as pd
        import io
        
        excel_data = pd.read_excel(io.BytesIO(content))
        
        # Process each row as metrics
        for index, row in excel_data.iterrows():
            row_dict = row.to_dict()
            cleaned_dict = {k: v for k, v in row_dict.items() if pd.notna(v)}
            
            if cleaned_dict:
                cleaned_dict['source'] = 'email_excel_attachment'
                cleaned_dict['row_index'] = index
                cleaned_dict['timestamp'] = datetime.utcnow().isoformat()
                
                create_metric_snapshot(company_id, cleaned_dict, source_id)
        
        return len(excel_data)
        
    except Exception as e:
        print(f"Error processing Excel attachment: {e}")
        return None

def create_metric_snapshot(company_id, metrics, source_id):
    """Create a metric snapshot from processed data"""
    snapshot = MetricSnapshot(
        id=generate_uuid(),
        company_id=company_id,
        metrics=json.dumps(metrics),
        snapshot_date=datetime.utcnow(),
        source_id=source_id,
        confidence_score=0.8
    )
    
    db.session.add(snapshot)

@email_processing_bp.route('/email/configure', methods=['POST'])
def configure_email_source():
    """Configure email processing for a company"""
    try:
        data = request.get_json()
        
        required_fields = ['company_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create email data source
        source = DataSource(
            id=generate_uuid(),
            company_id=data['company_id'],
            name=data['name'],
            source_type='email',
            config=json.dumps({
                'allowed_senders': data.get('allowed_senders', []),
                'allowed_domains': data.get('allowed_domains', []),
                'subject_patterns': data.get('subject_patterns', []),
                'auto_process_attachments': data.get('auto_process_attachments', True)
            }),
            is_active=True
        )
        
        db.session.add(source)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Email source configured successfully',
            'source': source.to_dict(),
            'email_endpoint': f'/api/email/ingest'
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to configure email source',
            'error': str(e)
        }), 500

@email_processing_bp.route('/email/test', methods=['POST'])
def test_email_processing():
    """Test email processing with sample data"""
    try:
        sample_email = {
            'from': 'reports@testcompany.com',
            'subject': 'Monthly Business Update - March 2024',
            'body': '''
            Hi team,
            
            Here's our monthly update:
            
            Revenue: $125,000 (up 15% from last month)
            Active Users: 2,500 (growth 8%)
            Churn Rate: 3.2%
            CAC: $45
            LTV: $850
            Burn Rate: $75,000
            Runway: 18 months
            
            Overall, we're seeing positive trends across all metrics.
            
            Best regards,
            Finance Team
            ''',
            'date': datetime.utcnow().isoformat(),
            'attachments': []
        }
        
        # Process the test email
        result = process_email_content(
            sample_email['subject'],
            sample_email['body'],
            sample_email['from']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Email processing test completed',
            'sample_email': sample_email,
            'extracted_metrics': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Email processing test failed',
            'error': str(e)
        }), 500

