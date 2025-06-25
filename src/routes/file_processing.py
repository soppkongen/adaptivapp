from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import csv
import json
import uuid
import pandas as pd
from datetime import datetime
import PyPDF2
import io
from src.models.elite_command import (
    db, DataSource, DataIngestionLog, RawDataEntry, 
    MetricSnapshot
)

file_processing_bp = Blueprint('file_processing', __name__)

UPLOAD_FOLDER = '/tmp/elite_command_uploads'
ALLOWED_EXTENSIONS = {'csv', 'pdf', 'md', 'txt', 'xlsx', 'json'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@file_processing_bp.route('/upload/<source_id>', methods=['POST'])
def upload_file(source_id):
    """Upload and process files for a specific data source"""
    try:
        # Validate source exists
        data_source = DataSource.query.get(source_id)
        if not data_source:
            return jsonify({'error': 'Invalid source ID'}), 404
        
        if not data_source.is_active:
            return jsonify({'error': 'Data source is inactive'}), 403
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Start ingestion logging
        log_entry = log_ingestion_start(source_id, 'file_upload')
        
        try:
            # Save file securely
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, f"{generate_uuid()}_{filename}")
            file.save(file_path)
            
            # Process file based on extension
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            if file_extension == 'csv':
                processed_count = process_csv_file(data_source, file_path, log_entry.id)
            elif file_extension == 'pdf':
                processed_count = process_pdf_file(data_source, file_path, log_entry.id)
            elif file_extension == 'md':
                processed_count = process_markdown_file(data_source, file_path, log_entry.id)
            elif file_extension == 'xlsx':
                processed_count = process_excel_file(data_source, file_path, log_entry.id)
            elif file_extension == 'json':
                processed_count = process_json_file(data_source, file_path, log_entry.id)
            else:
                processed_count = process_text_file(data_source, file_path, log_entry.id)
            
            # Clean up file
            os.remove(file_path)
            
            # Update data source
            data_source.last_successful_sync = datetime.utcnow()
            data_source.error_count = 0
            db.session.commit()
            
            # Complete logging
            log_ingestion_complete(log_entry, 'success', 1, processed_count, 0)
            
            return jsonify({
                'status': 'success',
                'message': 'File uploaded and processed successfully',
                'filename': filename,
                'ingestion_id': log_entry.id,
                'records_processed': processed_count
            }), 200
            
        except Exception as e:
            # Clean up file if it exists
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            
            # Update error count
            data_source.error_count += 1
            db.session.commit()
            
            # Complete logging with error
            log_ingestion_complete(log_entry, 'error', 1, 0, 1, str(e))
            
            return jsonify({
                'status': 'error',
                'message': 'Failed to process file',
                'error': str(e),
                'ingestion_id': log_entry.id
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'File upload failed',
            'error': str(e)
        }), 500

def process_csv_file(data_source, file_path, ingestion_log_id):
    """Process CSV file and extract metrics"""
    processed_count = 0
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Create raw data entry for the entire file
        raw_entry = RawDataEntry(
            id=generate_uuid(),
            source_id=data_source.id,
            ingestion_log_id=ingestion_log_id,
            raw_data=df.to_json(orient='records'),
            data_type='tabular',
            source_timestamp=datetime.utcnow(),
            confidence_score=1.0,
            tags=json.dumps(['csv', 'file_upload'])
        )
        db.session.add(raw_entry)
        
        # Process each row as a potential metric snapshot
        for index, row in df.iterrows():
            try:
                # Convert row to dictionary and clean NaN values
                row_dict = row.to_dict()
                cleaned_dict = {k: v for k, v in row_dict.items() if pd.notna(v)}
                
                # Skip empty rows
                if not cleaned_dict:
                    continue
                
                # Add metadata
                cleaned_dict['row_index'] = index
                cleaned_dict['source_file'] = os.path.basename(file_path)
                cleaned_dict['timestamp'] = datetime.utcnow().isoformat()
                
                # Create metric snapshot
                create_metric_snapshot(data_source.company_id, cleaned_dict, data_source.id)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing CSV row {index}: {e}")
                continue
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return 0

def process_excel_file(data_source, file_path, ingestion_log_id):
    """Process Excel file and extract metrics"""
    processed_count = 0
    
    try:
        # Read Excel file (all sheets)
        excel_file = pd.ExcelFile(file_path)
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Create raw data entry for each sheet
            raw_entry = RawDataEntry(
                id=generate_uuid(),
                source_id=data_source.id,
                ingestion_log_id=ingestion_log_id,
                raw_data=df.to_json(orient='records'),
                data_type='tabular',
                source_timestamp=datetime.utcnow(),
                confidence_score=1.0,
                tags=json.dumps(['excel', 'file_upload', f'sheet_{sheet_name}'])
            )
            db.session.add(raw_entry)
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    row_dict = row.to_dict()
                    cleaned_dict = {k: v for k, v in row_dict.items() if pd.notna(v)}
                    
                    if not cleaned_dict:
                        continue
                    
                    cleaned_dict['sheet_name'] = sheet_name
                    cleaned_dict['row_index'] = index
                    cleaned_dict['source_file'] = os.path.basename(file_path)
                    cleaned_dict['timestamp'] = datetime.utcnow().isoformat()
                    
                    create_metric_snapshot(data_source.company_id, cleaned_dict, data_source.id)
                    processed_count += 1
                    
                except Exception as e:
                    print(f"Error processing Excel row {index} in sheet {sheet_name}: {e}")
                    continue
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return 0

def process_pdf_file(data_source, file_path, ingestion_log_id):
    """Process PDF file and extract text content"""
    processed_count = 0
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                full_text += f"\\n--- Page {page_num + 1} ---\\n{page_text}"
            
            # Create raw data entry
            raw_entry = RawDataEntry(
                id=generate_uuid(),
                source_id=data_source.id,
                ingestion_log_id=ingestion_log_id,
                raw_data=json.dumps({'text': full_text, 'page_count': len(pdf_reader.pages)}),
                data_type='document',
                source_timestamp=datetime.utcnow(),
                confidence_score=0.8,  # Lower confidence for extracted text
                tags=json.dumps(['pdf', 'file_upload', 'document'])
            )
            db.session.add(raw_entry)
            
            # Extract potential metrics from text
            metrics = extract_metrics_from_text(full_text)
            if metrics:
                metrics['source_file'] = os.path.basename(file_path)
                metrics['page_count'] = len(pdf_reader.pages)
                metrics['timestamp'] = datetime.utcnow().isoformat()
                
                create_metric_snapshot(data_source.company_id, metrics, data_source.id)
                processed_count = 1
            
            db.session.commit()
            return processed_count
            
    except Exception as e:
        print(f"Error processing PDF file: {e}")
        return 0

def process_markdown_file(data_source, file_path, ingestion_log_id):
    """Process Markdown file and extract structured content"""
    processed_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Create raw data entry
        raw_entry = RawDataEntry(
            id=generate_uuid(),
            source_id=data_source.id,
            ingestion_log_id=ingestion_log_id,
            raw_data=json.dumps({'content': content}),
            data_type='document',
            source_timestamp=datetime.utcnow(),
            confidence_score=0.9,
            tags=json.dumps(['markdown', 'file_upload', 'document'])
        )
        db.session.add(raw_entry)
        
        # Extract structured information from markdown
        structured_data = parse_markdown_content(content)
        if structured_data:
            structured_data['source_file'] = os.path.basename(file_path)
            structured_data['timestamp'] = datetime.utcnow().isoformat()
            
            create_metric_snapshot(data_source.company_id, structured_data, data_source.id)
            processed_count = 1
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error processing Markdown file: {e}")
        return 0

def process_json_file(data_source, file_path, ingestion_log_id):
    """Process JSON file and extract data"""
    processed_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Create raw data entry
        raw_entry = RawDataEntry(
            id=generate_uuid(),
            source_id=data_source.id,
            ingestion_log_id=ingestion_log_id,
            raw_data=json.dumps(data),
            data_type='structured',
            source_timestamp=datetime.utcnow(),
            confidence_score=1.0,
            tags=json.dumps(['json', 'file_upload', 'structured'])
        )
        db.session.add(raw_entry)
        
        # Process JSON data
        if isinstance(data, list):
            # Array of objects
            for index, item in enumerate(data):
                if isinstance(item, dict):
                    item['array_index'] = index
                    item['source_file'] = os.path.basename(file_path)
                    item['timestamp'] = datetime.utcnow().isoformat()
                    
                    create_metric_snapshot(data_source.company_id, item, data_source.id)
                    processed_count += 1
        elif isinstance(data, dict):
            # Single object
            data['source_file'] = os.path.basename(file_path)
            data['timestamp'] = datetime.utcnow().isoformat()
            
            create_metric_snapshot(data_source.company_id, data, data_source.id)
            processed_count = 1
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error processing JSON file: {e}")
        return 0

def process_text_file(data_source, file_path, ingestion_log_id):
    """Process plain text file"""
    processed_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Create raw data entry
        raw_entry = RawDataEntry(
            id=generate_uuid(),
            source_id=data_source.id,
            ingestion_log_id=ingestion_log_id,
            raw_data=json.dumps({'content': content}),
            data_type='text',
            source_timestamp=datetime.utcnow(),
            confidence_score=0.7,
            tags=json.dumps(['text', 'file_upload'])
        )
        db.session.add(raw_entry)
        
        # Extract metrics from text
        metrics = extract_metrics_from_text(content)
        if metrics:
            metrics['source_file'] = os.path.basename(file_path)
            metrics['timestamp'] = datetime.utcnow().isoformat()
            
            create_metric_snapshot(data_source.company_id, metrics, data_source.id)
            processed_count = 1
        
        db.session.commit()
        return processed_count
        
    except Exception as e:
        print(f"Error processing text file: {e}")
        return 0

def extract_metrics_from_text(text):
    """Extract potential metrics from text content"""
    import re
    
    metrics = {}
    
    # Common business metrics patterns
    patterns = {
        'revenue': r'revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'arr': r'arr[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'mrr': r'mrr[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)',
        'churn': r'churn[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
        'users': r'users?[:\s]+([0-9,]+)',
        'customers': r'customers?[:\s]+([0-9,]+)',
        'growth': r'growth[:\s]+([0-9]+(?:\.[0-9]+)?)%?',
        'conversion': r'conversion[:\s]+([0-9]+(?:\.[0-9]+)?)%?'
    }
    
    text_lower = text.lower()
    
    for metric_name, pattern in patterns.items():
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            try:
                # Take the first match and clean it
                value_str = matches[0].replace(',', '')
                value = float(value_str)
                metrics[metric_name] = value
            except ValueError:
                continue
    
    return metrics if metrics else None

def parse_markdown_content(content):
    """Parse markdown content for structured data"""
    import re
    
    structured_data = {}
    
    # Extract headers
    headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
    if headers:
        structured_data['headers'] = headers
    
    # Extract lists
    lists = re.findall(r'^[\*\-\+]\s+(.+)$', content, re.MULTILINE)
    if lists:
        structured_data['list_items'] = lists
    
    # Extract links
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    if links:
        structured_data['links'] = [{'text': text, 'url': url} for text, url in links]
    
    # Extract potential metrics
    metrics = extract_metrics_from_text(content)
    if metrics:
        structured_data.update(metrics)
    
    return structured_data if structured_data else None

def create_metric_snapshot(company_id, metrics, source_id):
    """Create a metric snapshot from processed data"""
    snapshot = MetricSnapshot(
        id=generate_uuid(),
        company_id=company_id,
        metrics=json.dumps(metrics),
        snapshot_date=datetime.utcnow(),
        source_id=source_id,
        confidence_score=0.8  # Default confidence for file uploads
    )
    
    db.session.add(snapshot)

@file_processing_bp.route('/upload/batch/<source_id>', methods=['POST'])
def upload_multiple_files(source_id):
    """Upload and process multiple files"""
    try:
        data_source = DataSource.query.get(source_id)
        if not data_source:
            return jsonify({'error': 'Invalid source ID'}), 404
        
        if not data_source.is_active:
            return jsonify({'error': 'Data source is inactive'}), 403
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        results = []
        total_processed = 0
        
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': 'File type not allowed'
                })
                continue
            
            try:
                # Process individual file (reuse single file upload logic)
                # This is a simplified version - in production, you'd want to optimize this
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, f"{generate_uuid()}_{filename}")
                file.save(file_path)
                
                log_entry = log_ingestion_start(source_id, 'batch_file_upload')
                
                file_extension = filename.rsplit('.', 1)[1].lower()
                
                if file_extension == 'csv':
                    processed_count = process_csv_file(data_source, file_path, log_entry.id)
                elif file_extension == 'pdf':
                    processed_count = process_pdf_file(data_source, file_path, log_entry.id)
                elif file_extension == 'md':
                    processed_count = process_markdown_file(data_source, file_path, log_entry.id)
                elif file_extension == 'xlsx':
                    processed_count = process_excel_file(data_source, file_path, log_entry.id)
                elif file_extension == 'json':
                    processed_count = process_json_file(data_source, file_path, log_entry.id)
                else:
                    processed_count = process_text_file(data_source, file_path, log_entry.id)
                
                os.remove(file_path)
                log_ingestion_complete(log_entry, 'success', 1, processed_count, 0)
                
                results.append({
                    'filename': filename,
                    'status': 'success',
                    'records_processed': processed_count,
                    'ingestion_id': log_entry.id
                })
                
                total_processed += processed_count
                
            except Exception as e:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
                
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'Batch upload completed. {total_processed} total records processed.',
            'results': results,
            'total_processed': total_processed
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Batch upload failed',
            'error': str(e)
        }), 500

