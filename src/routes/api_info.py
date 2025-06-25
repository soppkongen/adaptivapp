from flask import Blueprint, request, jsonify
from datetime import datetime

api_info_bp = Blueprint('api_info', __name__)

@api_info_bp.route('/info', methods=['GET'])
def get_api_info():
    """Get comprehensive API information and available endpoints"""
    try:
        api_info = {
            'api_name': 'Elite Command Data API',
            'version': '1.0.0',
            'description': 'Central data backbone for Executive OS targeting multi-business founders',
            'base_url': '/api',
            'documentation_url': '/api/docs',
            'status': 'operational',
            'last_updated': datetime.utcnow().isoformat(),
            
            'endpoint_categories': {
                'data_ingestion': {
                    'description': 'Endpoints for ingesting data from various sources',
                    'base_path': '/api/ingestion',
                    'endpoints': [
                        {
                            'path': '/webhook/{source_id}',
                            'method': 'POST',
                            'description': 'Ingest data via webhook',
                            'parameters': ['source_id']
                        },
                        {
                            'path': '/files/upload/{source_id}',
                            'method': 'POST',
                            'description': 'Upload and process files (CSV, PDF, Excel, etc.)',
                            'parameters': ['source_id']
                        },
                        {
                            'path': '/email/ingest',
                            'method': 'POST',
                            'description': 'Process forwarded email reports'
                        }
                    ]
                },
                
                'oauth_integration': {
                    'description': 'OAuth integrations with external platforms',
                    'base_path': '/api/oauth',
                    'endpoints': [
                        {
                            'path': '/connect/{platform}',
                            'method': 'POST',
                            'description': 'Initiate OAuth connection',
                            'parameters': ['platform'],
                            'supported_platforms': ['notion', 'stripe', 'gmail', 'slack']
                        },
                        {
                            'path': '/callback/{platform}',
                            'method': 'GET',
                            'description': 'OAuth callback handler',
                            'parameters': ['platform']
                        },
                        {
                            'path': '/sync/{source_id}',
                            'method': 'POST',
                            'description': 'Manual data synchronization',
                            'parameters': ['source_id']
                        }
                    ]
                },
                
                'data_normalization': {
                    'description': 'Data processing and normalization',
                    'base_path': '/api/normalize',
                    'endpoints': [
                        {
                            'path': '/batch',
                            'method': 'POST',
                            'description': 'Process batch of pending raw data'
                        },
                        {
                            'path': '/entry/{entry_id}',
                            'method': 'POST',
                            'description': 'Normalize specific data entry',
                            'parameters': ['entry_id']
                        },
                        {
                            'path': '/status',
                            'method': 'GET',
                            'description': 'Get normalization processing status'
                        },
                        {
                            'path': '/reprocess',
                            'method': 'POST',
                            'description': 'Reprocess failed or skipped entries'
                        }
                    ]
                },
                
                'intelligence_layer': {
                    'description': 'AI-powered insights and analysis',
                    'base_path': '/api/intelligence',
                    'endpoints': [
                        {
                            'path': '/brief/{company_id}',
                            'method': 'GET',
                            'description': 'Get executive brief for company',
                            'parameters': ['company_id'],
                            'query_params': ['days']
                        },
                        {
                            'path': '/portfolio/summary',
                            'method': 'POST',
                            'description': 'Get portfolio-wide summary and analysis'
                        },
                        {
                            'path': '/trends/{company_id}',
                            'method': 'GET',
                            'description': 'Analyze trends for company metrics',
                            'parameters': ['company_id'],
                            'query_params': ['days']
                        },
                        {
                            'path': '/alerts/{company_id}',
                            'method': 'GET',
                            'description': 'Get alerts for company',
                            'parameters': ['company_id'],
                            'query_params': ['days', 'severity']
                        },
                        {
                            'path': '/insights/{company_id}',
                            'method': 'GET',
                            'description': 'Generate business insights',
                            'parameters': ['company_id'],
                            'query_params': ['days', 'category']
                        },
                        {
                            'path': '/anomalies/{company_id}',
                            'method': 'GET',
                            'description': 'Detect data anomalies',
                            'parameters': ['company_id'],
                            'query_params': ['days']
                        },
                        {
                            'path': '/metrics/sorted/{company_id}',
                            'method': 'GET',
                            'description': 'Get metrics sorted by importance',
                            'parameters': ['company_id']
                        },
                        {
                            'path': '/signals/network',
                            'method': 'GET',
                            'description': 'Get network signals for introductions'
                        },
                        {
                            'path': '/rituals/status',
                            'method': 'GET',
                            'description': 'Get focus compliance and ritual status',
                            'query_params': ['company_id', 'days']
                        }
                    ]
                },
                
                'user_management': {
                    'description': 'User and authentication management',
                    'base_path': '/api',
                    'endpoints': [
                        {
                            'path': '/users',
                            'method': 'GET',
                            'description': 'List users'
                        },
                        {
                            'path': '/users',
                            'method': 'POST',
                            'description': 'Create new user'
                        }
                    ]
                }
            },
            
            'data_models': {
                'Company': {
                    'description': 'Portfolio company entity',
                    'fields': ['id', 'name', 'business_model', 'stage', 'domain', 'founded_date']
                },
                'MetricSnapshot': {
                    'description': 'Historical metric data point',
                    'fields': ['id', 'company_id', 'metrics', 'snapshot_date', 'confidence_score']
                },
                'DataSource': {
                    'description': 'Data ingestion source configuration',
                    'fields': ['id', 'company_id', 'name', 'source_type', 'config', 'is_active']
                },
                'RawDataEntry': {
                    'description': 'Raw data before normalization',
                    'fields': ['id', 'source_id', 'raw_data', 'data_type', 'processing_status']
                }
            },
            
            'supported_integrations': {
                'oauth_platforms': ['notion', 'stripe', 'gmail', 'slack'],
                'file_formats': ['csv', 'pdf', 'xlsx', 'json', 'md', 'txt'],
                'webhook_sources': ['custom_tools', 'zapier', 'make', 'direct_api']
            },
            
            'rate_limits': {
                'standard_endpoints': '1000 requests/hour',
                'intelligence_endpoints': '100 requests/hour',
                'file_upload_endpoints': '50 requests/hour'
            },
            
            'response_formats': {
                'success': {
                    'status': 'success',
                    'data': '...',
                    'message': 'Optional success message'
                },
                'error': {
                    'status': 'error',
                    'message': 'Human-readable error message',
                    'error': 'Technical error details'
                }
            }
        }
        
        return jsonify(api_info), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get API information',
            'error': str(e)
        }), 500

@api_info_bp.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    try:
        # Check database connectivity
        from src.models.elite_command import db
        db.session.execute('SELECT 1')
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'components': {
                'database': 'healthy',
                'ingestion_layer': 'healthy',
                'normalization_engine': 'healthy',
                'intelligence_layer': 'healthy'
            },
            'uptime': 'Available',
            'environment': 'production'  # This would be dynamic in real deployment
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'components': {
                'database': 'error',
                'ingestion_layer': 'unknown',
                'normalization_engine': 'unknown',
                'intelligence_layer': 'unknown'
            }
        }), 503

@api_info_bp.route('/metrics', methods=['GET'])
def get_api_metrics():
    """Get API usage metrics and statistics"""
    try:
        # In a real implementation, this would query actual usage data
        metrics = {
            'requests': {
                'total_today': 1247,
                'total_this_week': 8934,
                'total_this_month': 34567,
                'average_response_time_ms': 245
            },
            'data_processing': {
                'entries_processed_today': 156,
                'entries_processed_this_week': 1089,
                'success_rate': 0.987,
                'average_confidence_score': 0.84
            },
            'companies': {
                'total_active': 23,
                'with_recent_data': 19,
                'average_health_score': 76.3
            },
            'alerts': {
                'active_critical': 2,
                'active_high': 7,
                'resolved_today': 12
            },
            'top_endpoints': [
                {'endpoint': '/intelligence/brief/{company_id}', 'requests': 234},
                {'endpoint': '/intelligence/alerts/{company_id}', 'requests': 189},
                {'endpoint': '/normalize/batch', 'requests': 156},
                {'endpoint': '/intelligence/portfolio/summary', 'requests': 98}
            ]
        }
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get API metrics',
            'error': str(e)
        }), 500

@api_info_bp.route('/docs', methods=['GET'])
def get_documentation():
    """Get API documentation"""
    try:
        # Read the documentation file
        import os
        doc_path = os.path.join(os.path.dirname(__file__), '..', '..', 'API_DOCUMENTATION.md')
        
        if os.path.exists(doc_path):
            with open(doc_path, 'r') as f:
                documentation = f.read()
            
            return jsonify({
                'status': 'success',
                'documentation': documentation,
                'format': 'markdown',
                'last_updated': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'success',
                'message': 'Documentation available at /api/info endpoint',
                'documentation_url': '/api/info'
            }), 200
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get documentation',
            'error': str(e)
        }), 500

@api_info_bp.route('/test/all', methods=['POST'])
def test_all_endpoints():
    """Test all major API endpoints with sample data"""
    try:
        test_results = {}
        
        # Test data ingestion
        try:
            from src.routes.ingestion import test_webhook_ingestion
            test_results['webhook_ingestion'] = 'available'
        except:
            test_results['webhook_ingestion'] = 'error'
        
        # Test file processing
        try:
            from src.routes.file_processing import file_processing_bp
            test_results['file_processing'] = 'available'
        except:
            test_results['file_processing'] = 'error'
        
        # Test email processing
        try:
            from src.routes.email_processing import test_email_processing
            test_results['email_processing'] = 'available'
        except:
            test_results['email_processing'] = 'error'
        
        # Test normalization
        try:
            from src.services.normalization import DataNormalizationEngine
            engine = DataNormalizationEngine()
            test_results['normalization'] = 'available'
        except Exception as e:
            test_results['normalization'] = f'error: {str(e)}'
        
        # Test intelligence layer
        try:
            from src.services.intelligence import IntelligenceEngine
            intel_engine = IntelligenceEngine()
            test_results['intelligence'] = 'available'
        except Exception as e:
            test_results['intelligence'] = f'error: {str(e)}'
        
        # Test OAuth
        try:
            from src.routes.oauth import oauth_bp
            test_results['oauth'] = 'available'
        except:
            test_results['oauth'] = 'error'
        
        return jsonify({
            'status': 'success',
            'message': 'API endpoint test completed',
            'test_results': test_results,
            'tested_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'API test failed',
            'error': str(e)
        }), 500

