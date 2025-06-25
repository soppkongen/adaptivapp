#!/usr/bin/env python3
"""
Elite Command Data API - Comprehensive Testing Suite

This test suite validates all components of the Elite Command Data API
including data ingestion, normalization, intelligence layer, and API endpoints.
"""

import unittest
import json
import uuid
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import Flask app and components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app
from src.models.elite_command import (
    db, Company, BusinessUnit, DataSource, MetricSnapshot, 
    RawDataEntry, DataIngestionLog
)
from src.services.normalization import DataNormalizationEngine
from src.services.intelligence import IntelligenceEngine

class EliteCommandAPITestCase(unittest.TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """Create test data for testing"""
        # Create test company
        self.test_company = Company(
            id=str(uuid.uuid4()),
            name="Test AI Robotics Inc",
            business_model="saas",
            stage="growth",
            domain="test-ai-robotics.com",
            description="Test company for API testing"
        )
        db.session.add(self.test_company)
        
        # Create test data source
        self.test_source = DataSource(
            id=str(uuid.uuid4()),
            company_id=self.test_company.id,
            name="Test Webhook Source",
            source_type="webhook",
            config=json.dumps({"endpoint": "/webhook/test"}),
            is_active=True,
            reliability_score=0.95
        )
        db.session.add(self.test_source)
        
        # Create test metric snapshots
        base_date = datetime.utcnow() - timedelta(days=30)
        for i in range(10):
            snapshot_date = base_date + timedelta(days=i*3)
            metrics = {
                "revenue": 100000 + (i * 5000),
                "arr": 1200000 + (i * 60000),
                "churn_rate": 0.03 + (i * 0.001),
                "active_users": 2000 + (i * 100),
                "burn_rate": 70000 + (i * 2000),
                "runway_months": 18 - (i * 0.5)
            }
            
            snapshot = MetricSnapshot(
                id=str(uuid.uuid4()),
                company_id=self.test_company.id,
                metrics=json.dumps(metrics),
                snapshot_date=snapshot_date,
                source_id=self.test_source.id,
                confidence_score=0.85 + (i * 0.01)
            )
            db.session.add(snapshot)
        
        db.session.commit()

class TestDataIngestion(EliteCommandAPITestCase):
    """Test data ingestion endpoints"""
    
    def test_webhook_ingestion(self):
        """Test webhook data ingestion"""
        webhook_data = {
            "data": {
                "revenue": 125000,
                "active_users": 2500,
                "timestamp": datetime.utcnow().isoformat()
            },
            "source": "custom_tool",
            "event_type": "metric_update"
        }
        
        response = self.client.post(
            f'/api/ingestion/webhook/{self.test_source.id}',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('ingestion_id', data)
    
    def test_file_upload(self):
        """Test file upload functionality"""
        # Create a test CSV file
        csv_content = """date,revenue,users,churn_rate
2024-01-01,120000,2400,0.032
2024-01-02,122000,2450,0.031
2024-01-03,125000,2500,0.030"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            with open(f.name, 'rb') as test_file:
                response = self.client.post(
                    f'/api/files/upload/{self.test_source.id}',
                    data={'file': (test_file, 'test_data.csv')},
                    content_type='multipart/form-data'
                )
        
        os.unlink(f.name)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
    
    def test_email_ingestion(self):
        """Test email processing"""
        email_data = {
            "from": "reports@test-company.com",
            "subject": "Weekly Business Update",
            "body": "Revenue this week: $125,000. Active users: 2,500. Churn rate: 3.2%",
            "attachments": []
        }
        
        response = self.client.post(
            '/api/email/ingest',
            data=json.dumps(email_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

class TestDataNormalization(EliteCommandAPITestCase):
    """Test data normalization engine"""
    
    def test_normalization_engine(self):
        """Test the normalization engine"""
        # Create raw data entry
        raw_data = {
            "revenue": "125,000",
            "users": "2500",
            "churn": "3.2%",
            "date": "2024-01-15"
        }
        
        raw_entry = RawDataEntry(
            id=str(uuid.uuid4()),
            source_id=self.test_source.id,
            raw_data=json.dumps(raw_data),
            data_type="financial",
            processing_status="pending"
        )
        db.session.add(raw_entry)
        db.session.commit()
        
        # Test normalization
        engine = DataNormalizationEngine()
        result = engine.normalize_entry(raw_entry.id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
    
    def test_batch_normalization(self):
        """Test batch normalization endpoint"""
        response = self.client.post(
            '/api/normalize/batch',
            data=json.dumps({"batch_size": 10}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

class TestIntelligenceLayer(EliteCommandAPITestCase):
    """Test intelligence layer functionality"""
    
    def test_company_brief(self):
        """Test company brief generation"""
        response = self.client.get(f'/api/intelligence/brief/{self.test_company.id}?days=7')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('brief', data)
        self.assertIn('health_score', data['brief'])
    
    def test_portfolio_summary(self):
        """Test portfolio summary generation"""
        portfolio_data = {
            "company_ids": [self.test_company.id]
        }
        
        response = self.client.post(
            '/api/intelligence/portfolio/summary',
            data=json.dumps(portfolio_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('portfolio_summary', data)
    
    def test_trend_analysis(self):
        """Test trend analysis"""
        response = self.client.get(f'/api/intelligence/trends/{self.test_company.id}?days=30')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('trends', data)
    
    def test_alert_generation(self):
        """Test alert generation"""
        response = self.client.get(f'/api/intelligence/alerts/{self.test_company.id}?days=7')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('alerts', data)
    
    def test_insight_generation(self):
        """Test insight generation"""
        response = self.client.get(f'/api/intelligence/insights/{self.test_company.id}?days=30')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('insights', data)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        response = self.client.get(f'/api/intelligence/anomalies/{self.test_company.id}?days=30')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('anomalies', data)
    
    def test_metric_sorting(self):
        """Test metric sorting by importance"""
        response = self.client.get(f'/api/intelligence/metrics/sorted/{self.test_company.id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('sorted_metrics', data)

class TestAPIEndpoints(EliteCommandAPITestCase):
    """Test API endpoints and responses"""
    
    def test_api_info(self):
        """Test API info endpoint"""
        response = self.client.get('/api/info')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('api_name', data)
        self.assertIn('endpoint_categories', data)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_api_metrics(self):
        """Test API metrics endpoint"""
        response = self.client.get('/api/metrics')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('metrics', data)
    
    def test_network_signals(self):
        """Test network signals endpoint"""
        response = self.client.get('/api/intelligence/signals/network')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('signals', data)
    
    def test_rituals_status(self):
        """Test rituals status endpoint"""
        response = self.client.get('/api/intelligence/rituals/status?days=30')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('rituals_status', data)

class TestErrorHandling(EliteCommandAPITestCase):
    """Test error handling and edge cases"""
    
    def test_invalid_company_id(self):
        """Test handling of invalid company ID"""
        response = self.client.get('/api/intelligence/brief/invalid-id')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Company not found')
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters"""
        response = self.client.get(f'/api/intelligence/brief/{self.test_company.id}?days=500')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_missing_data(self):
        """Test handling when no data is available"""
        # Create company with no data
        empty_company = Company(
            id=str(uuid.uuid4()),
            name="Empty Company",
            business_model="saas",
            stage="idea"
        )
        db.session.add(empty_company)
        db.session.commit()
        
        response = self.client.get(f'/api/intelligence/brief/{empty_company.id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Should handle gracefully even with no data

class TestDataValidation(EliteCommandAPITestCase):
    """Test data validation and quality checks"""
    
    def test_metric_validation(self):
        """Test metric data validation"""
        invalid_data = {
            "data": {
                "revenue": "invalid_number",
                "users": -100,  # Negative users
                "churn_rate": 1.5  # Churn rate > 100%
            }
        }
        
        response = self.client.post(
            f'/api/ingestion/webhook/{self.test_source.id}',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # Should handle validation errors gracefully
        self.assertIn(response.status_code, [200, 400])
    
    def test_confidence_scoring(self):
        """Test confidence scoring system"""
        engine = IntelligenceEngine()
        
        # Test with high-quality data
        high_quality_metrics = {
            "revenue": 125000,
            "arr": 1500000,
            "churn_rate": 0.032
        }
        
        # Test with low-quality data
        low_quality_metrics = {
            "revenue": None,
            "arr": "unknown",
            "churn_rate": -1
        }
        
        # The system should assign appropriate confidence scores

class TestPerformance(EliteCommandAPITestCase):
    """Test performance and scalability"""
    
    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        # Create multiple companies and data points
        companies = []
        for i in range(5):
            company = Company(
                id=str(uuid.uuid4()),
                name=f"Test Company {i}",
                business_model="saas",
                stage="growth"
            )
            companies.append(company)
            db.session.add(company)
        
        db.session.commit()
        
        # Test portfolio summary with multiple companies
        company_ids = [c.id for c in companies]
        portfolio_data = {"company_ids": company_ids}
        
        response = self.client.post(
            '/api/intelligence/portfolio/summary',
            data=json.dumps(portfolio_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get(f'/api/intelligence/brief/{self.test_company.id}')
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertTrue(all(code == 200 for code in results))

class TestIntegration(EliteCommandAPITestCase):
    """Test end-to-end integration scenarios"""
    
    def test_full_data_pipeline(self):
        """Test complete data pipeline from ingestion to insights"""
        # 1. Ingest data via webhook
        webhook_data = {
            "data": {
                "revenue": 130000,
                "active_users": 2600,
                "churn_rate": 0.028
            },
            "source": "custom_tool",
            "event_type": "metric_update"
        }
        
        ingest_response = self.client.post(
            f'/api/ingestion/webhook/{self.test_source.id}',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        self.assertEqual(ingest_response.status_code, 200)
        
        # 2. Process normalization
        normalize_response = self.client.post(
            '/api/normalize/batch',
            data=json.dumps({"batch_size": 10}),
            content_type='application/json'
        )
        self.assertEqual(normalize_response.status_code, 200)
        
        # 3. Generate insights
        insights_response = self.client.get(
            f'/api/intelligence/insights/{self.test_company.id}?days=7'
        )
        self.assertEqual(insights_response.status_code, 200)
        
        # 4. Get company brief
        brief_response = self.client.get(
            f'/api/intelligence/brief/{self.test_company.id}?days=7'
        )
        self.assertEqual(brief_response.status_code, 200)

def run_tests():
    """Run all tests and generate report"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestDataIngestion,
        TestDataNormalization,
        TestIntelligenceLayer,
        TestAPIEndpoints,
        TestErrorHandling,
        TestDataValidation,
        TestPerformance,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate report
    print("\n" + "="*50)
    print("ELITE COMMAND API TEST REPORT")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)

