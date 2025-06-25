from flask import Blueprint, request, jsonify
import json
from datetime import datetime
from src.models.elite_command import db, RawDataEntry, MetricSnapshot
from src.services.normalization import (
    DataNormalizationEngine, process_pending_data, normalize_single_entry
)

normalization_bp = Blueprint('normalization', __name__)

@normalization_bp.route('/normalize/batch', methods=['POST'])
def normalize_batch():
    """Process a batch of pending raw data entries"""
    try:
        data = request.get_json() or {}
        batch_size = data.get('batch_size', 100)
        
        # Validate batch size
        if batch_size < 1 or batch_size > 1000:
            return jsonify({'error': 'Batch size must be between 1 and 1000'}), 400
        
        # Process the batch
        results = process_pending_data(batch_size)
        
        return jsonify({
            'status': 'success',
            'message': f'Batch processing completed',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Batch normalization failed',
            'error': str(e)
        }), 500

@normalization_bp.route('/normalize/entry/<entry_id>', methods=['POST'])
def normalize_entry(entry_id):
    """Normalize a specific raw data entry"""
    try:
        # Check if entry exists
        entry = RawDataEntry.query.get(entry_id)
        if not entry:
            return jsonify({'error': 'Raw data entry not found'}), 404
        
        # Process the entry
        success = normalize_single_entry(entry_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Entry normalized successfully',
                'entry_id': entry_id
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to normalize entry',
                'entry_id': entry_id
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Entry normalization failed',
            'error': str(e)
        }), 500

@normalization_bp.route('/normalize/status', methods=['GET'])
def get_normalization_status():
    """Get the current status of data normalization"""
    try:
        # Count entries by processing status
        pending_count = RawDataEntry.query.filter(
            RawDataEntry.processing_status == 'pending'
        ).count()
        
        processed_count = RawDataEntry.query.filter(
            RawDataEntry.processing_status == 'processed'
        ).count()
        
        error_count = RawDataEntry.query.filter(
            RawDataEntry.processing_status == 'error'
        ).count()
        
        skipped_count = RawDataEntry.query.filter(
            RawDataEntry.processing_status == 'skipped'
        ).count()
        
        total_count = pending_count + processed_count + error_count + skipped_count
        
        # Get recent metric snapshots
        recent_snapshots = MetricSnapshot.query.order_by(
            MetricSnapshot.snapshot_date.desc()
        ).limit(10).all()
        
        return jsonify({
            'status': 'success',
            'normalization_status': {
                'total_entries': total_count,
                'pending': pending_count,
                'processed': processed_count,
                'errors': error_count,
                'skipped': skipped_count,
                'processing_rate': processed_count / total_count if total_count > 0 else 0
            },
            'recent_snapshots': [
                {
                    'id': snapshot.id,
                    'company_id': snapshot.company_id,
                    'snapshot_date': snapshot.snapshot_date.isoformat(),
                    'confidence_score': snapshot.confidence_score,
                    'metric_count': len(json.loads(snapshot.metrics))
                }
                for snapshot in recent_snapshots
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get normalization status',
            'error': str(e)
        }), 500

@normalization_bp.route('/normalize/auto', methods=['POST'])
def enable_auto_normalization():
    """Enable automatic normalization for new data"""
    try:
        data = request.get_json() or {}
        enabled = data.get('enabled', True)
        interval_minutes = data.get('interval_minutes', 5)
        
        # Validate interval
        if interval_minutes < 1 or interval_minutes > 60:
            return jsonify({'error': 'Interval must be between 1 and 60 minutes'}), 400
        
        # In a production system, this would configure a background task
        # For now, we'll just return the configuration
        
        return jsonify({
            'status': 'success',
            'message': f'Auto-normalization {"enabled" if enabled else "disabled"}',
            'config': {
                'enabled': enabled,
                'interval_minutes': interval_minutes,
                'next_run': datetime.utcnow().isoformat() if enabled else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to configure auto-normalization',
            'error': str(e)
        }), 500

@normalization_bp.route('/normalize/metrics/summary', methods=['GET'])
def get_metrics_summary():
    """Get a summary of normalized metrics by type"""
    try:
        # Get query parameters
        company_id = request.args.get('company_id')
        days = int(request.args.get('days', 30))
        
        # Build base query
        query = MetricSnapshot.query
        
        if company_id:
            query = query.filter(MetricSnapshot.company_id == company_id)
        
        # Filter by date range
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(MetricSnapshot.snapshot_date >= start_date)
        
        # Get snapshots
        snapshots = query.order_by(MetricSnapshot.snapshot_date.desc()).all()
        
        # Analyze metrics
        metric_types = {}
        total_metrics = 0
        avg_confidence = 0
        
        for snapshot in snapshots:
            metrics = json.loads(snapshot.metrics)
            total_metrics += len(metrics)
            avg_confidence += snapshot.confidence_score
            
            # Categorize metrics
            for metric_name in metrics.keys():
                category = categorize_metric(metric_name)
                if category not in metric_types:
                    metric_types[category] = 0
                metric_types[category] += 1
        
        avg_confidence = avg_confidence / len(snapshots) if snapshots else 0
        
        return jsonify({
            'status': 'success',
            'summary': {
                'total_snapshots': len(snapshots),
                'total_metrics': total_metrics,
                'average_confidence': round(avg_confidence, 3),
                'metric_types': metric_types,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': datetime.utcnow().isoformat(),
                    'days': days
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get metrics summary',
            'error': str(e)
        }), 500

@normalization_bp.route('/normalize/test', methods=['POST'])
def test_normalization():
    """Test the normalization engine with sample data"""
    try:
        data = request.get_json()
        
        if not data:
            # Use default test data
            data = {
                'test_data': {
                    'revenue': '$125,000',
                    'arr': '$1,500,000',
                    'mrr': '$125,000',
                    'churn_rate': '3.2%',
                    'active_users': '2,500',
                    'cac': '$45',
                    'ltv': '$850',
                    'burn_rate': '$75,000',
                    'runway': '18 months'
                }
            }
        
        # Create a test normalization engine
        engine = DataNormalizationEngine()
        
        # Test each normalizer
        results = {}
        
        # Test financial normalizer
        financial_normalizer = engine.metric_normalizers['financial']
        financial_result = financial_normalizer.normalize(data.get('test_data', {}), None)
        results['financial'] = financial_result
        
        # Test operational normalizer
        operational_normalizer = engine.metric_normalizers['operational']
        operational_result = operational_normalizer.normalize(data.get('test_data', {}), None)
        results['operational'] = operational_result
        
        # Test customer normalizer
        customer_normalizer = engine.metric_normalizers['customer']
        customer_result = customer_normalizer.normalize(data.get('test_data', {}), None)
        results['customer'] = customer_result
        
        # Test general normalizer
        general_normalizer = engine.metric_normalizers['general']
        general_result = general_normalizer.normalize(data.get('test_data', {}), None)
        results['general'] = general_result
        
        return jsonify({
            'status': 'success',
            'message': 'Normalization test completed',
            'input_data': data.get('test_data', {}),
            'normalized_results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Normalization test failed',
            'error': str(e)
        }), 500

def categorize_metric(metric_name):
    """Categorize a metric by its name"""
    metric_name_lower = metric_name.lower()
    
    # Financial metrics
    financial_keywords = ['revenue', 'arr', 'mrr', 'profit', 'loss', 'cost', 'expense', 'margin', 'ebitda', 'burn', 'runway', 'cac', 'ltv']
    if any(keyword in metric_name_lower for keyword in financial_keywords):
        return 'financial'
    
    # Operational metrics
    operational_keywords = ['users', 'sessions', 'conversion', 'engagement', 'performance', 'uptime', 'response']
    if any(keyword in metric_name_lower for keyword in operational_keywords):
        return 'operational'
    
    # Customer metrics
    customer_keywords = ['customer', 'subscriber', 'churn', 'retention', 'account']
    if any(keyword in metric_name_lower for keyword in customer_keywords):
        return 'customer'
    
    # Team metrics
    team_keywords = ['headcount', 'employee', 'team', 'staff', 'hiring']
    if any(keyword in metric_name_lower for keyword in team_keywords):
        return 'team'
    
    return 'general'

@normalization_bp.route('/normalize/reprocess', methods=['POST'])
def reprocess_entries():
    """Reprocess entries that failed or were skipped"""
    try:
        data = request.get_json() or {}
        status_filter = data.get('status', 'error')  # 'error' or 'skipped'
        batch_size = data.get('batch_size', 50)
        
        # Validate inputs
        if status_filter not in ['error', 'skipped']:
            return jsonify({'error': 'Status must be "error" or "skipped"'}), 400
        
        if batch_size < 1 or batch_size > 500:
            return jsonify({'error': 'Batch size must be between 1 and 500'}), 400
        
        # Get entries to reprocess
        entries = RawDataEntry.query.filter(
            RawDataEntry.processing_status == status_filter
        ).limit(batch_size).all()
        
        if not entries:
            return jsonify({
                'status': 'success',
                'message': f'No {status_filter} entries found to reprocess',
                'processed': 0
            }), 200
        
        # Reset status to pending for reprocessing
        for entry in entries:
            entry.processing_status = 'pending'
            entry.processed_at = None
        
        db.session.commit()
        
        # Process the batch
        results = process_pending_data(len(entries))
        
        return jsonify({
            'status': 'success',
            'message': f'Reprocessed {len(entries)} {status_filter} entries',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Reprocessing failed',
            'error': str(e)
        }), 500

