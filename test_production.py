#!/usr/bin/env python3
"""
Elite Command Data API - Production Testing Suite

Comprehensive testing script to validate production readiness of the
Elite Command Data API with Human Signal Intelligence.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import concurrent.futures
import threading

class ProductionTester:
    """Comprehensive production testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv('ELITE_COMMAND_API_KEY', 'test-api-key')
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_result(self, test_name: str, success: bool, message: str, duration: float = 0):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message} ({duration:.2f}s)")
        
    def test_basic_connectivity(self) -> bool:
        """Test basic API connectivity"""
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api/info", timeout=10)
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Basic Connectivity", True, 
                              f"API accessible, version: {data.get('version', 'unknown')}", duration)
                return True
            else:
                self.log_result("Basic Connectivity", False, 
                              f"HTTP {response.status_code}: {response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Connection failed: {str(e)}")
            return False
    
    def test_health_endpoints(self) -> bool:
        """Test all health check endpoints"""
        health_endpoints = [
            '/api/info',
            '/api/ingestion/health',
            '/api/normalization/health',
            '/api/intelligence/health',
            '/api/psychological/health',
            '/api/hsi/health',
            '/api/profiling/health',
            '/api/hitl/health',
            '/api/templates/health',
            '/api/confidence/health',
            '/api/corrections/health',
            '/api/ai/health',
            '/api/security/health'
        ]
        
        all_healthy = True
        for endpoint in health_endpoints:
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      headers=self.headers, timeout=5)
                duration = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    self.log_result(f"Health Check {endpoint}", True, 
                                  f"Status: {status}", duration)
                else:
                    self.log_result(f"Health Check {endpoint}", False, 
                                  f"HTTP {response.status_code}", duration)
                    all_healthy = False
                    
            except Exception as e:
                self.log_result(f"Health Check {endpoint}", False, f"Error: {str(e)}")
                all_healthy = False
                
        return all_healthy
    
    def test_authentication(self) -> bool:
        """Test API key authentication"""
        # Test with valid API key
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api/companies", 
                                  headers=self.headers, timeout=5)
            duration = time.time() - start
            
            if response.status_code in [200, 404]:  # 404 is OK if no companies exist
                self.log_result("Authentication (Valid Key)", True, 
                              "Valid API key accepted", duration)
                valid_auth = True
            else:
                self.log_result("Authentication (Valid Key)", False, 
                              f"HTTP {response.status_code}", duration)
                valid_auth = False
                
        except Exception as e:
            self.log_result("Authentication (Valid Key)", False, f"Error: {str(e)}")
            valid_auth = False
        
        # Test with invalid API key
        try:
            start = time.time()
            invalid_headers = {'Content-Type': 'application/json', 'X-API-Key': 'invalid-key'}
            response = requests.get(f"{self.base_url}/api/companies", 
                                  headers=invalid_headers, timeout=5)
            duration = time.time() - start
            
            if response.status_code == 401:
                self.log_result("Authentication (Invalid Key)", True, 
                              "Invalid API key rejected", duration)
                invalid_auth = True
            else:
                self.log_result("Authentication (Invalid Key)", False, 
                              f"Expected 401, got {response.status_code}", duration)
                invalid_auth = False
                
        except Exception as e:
            self.log_result("Authentication (Invalid Key)", False, f"Error: {str(e)}")
            invalid_auth = False
            
        return valid_auth and invalid_auth
    
    def test_data_ingestion(self) -> bool:
        """Test data ingestion endpoints"""
        # Test webhook ingestion
        test_data = {
            "source": "test_webhook",
            "company_id": "test_company_001",
            "data": {
                "metric": "ARR",
                "value": 1000000,
                "period": "2024-Q4"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            start = time.time()
            response = requests.post(f"{self.base_url}/api/ingest/webhook", 
                                   headers=self.headers, 
                                   json=test_data, timeout=10)
            duration = time.time() - start
            
            if response.status_code in [200, 201]:
                self.log_result("Data Ingestion (Webhook)", True, 
                              "Webhook data ingested successfully", duration)
                return True
            else:
                self.log_result("Data Ingestion (Webhook)", False, 
                              f"HTTP {response.status_code}: {response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("Data Ingestion (Webhook)", False, f"Error: {str(e)}")
            return False
    
    def test_hsi_functionality(self) -> bool:
        """Test Human Signal Intelligence functionality"""
        # Test text analysis
        test_text = {
            "text": "I am feeling very confident about our Q4 performance. The team is motivated and we're hitting all our targets.",
            "user_id": "test_user_001",
            "context": "quarterly_update"
        }
        
        try:
            start = time.time()
            response = requests.post(f"{self.base_url}/api/psychological/analyze/text", 
                                   headers=self.headers, 
                                   json=test_text, timeout=15)
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if 'psychological_profile' in data:
                    self.log_result("HSI Text Analysis", True, 
                                  "Psychological analysis completed", duration)
                    return True
                else:
                    self.log_result("HSI Text Analysis", False, 
                                  "Missing psychological profile in response", duration)
                    return False
            else:
                self.log_result("HSI Text Analysis", False, 
                              f"HTTP {response.status_code}: {response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("HSI Text Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_ai_commands(self) -> bool:
        """Test AI-powered command interface"""
        test_command = {
            "command": "Show me all companies with high risk scores",
            "user_id": "test_user_001",
            "context": "executive_dashboard"
        }
        
        try:
            start = time.time()
            response = requests.post(f"{self.base_url}/api/ai/command", 
                                   headers=self.headers, 
                                   json=test_command, timeout=10)
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if 'command_id' in data:
                    self.log_result("AI Commands", True, 
                                  "AI command processed successfully", duration)
                    return True
                else:
                    self.log_result("AI Commands", False, 
                                  "Missing command_id in response", duration)
                    return False
            else:
                self.log_result("AI Commands", False, 
                              f"HTTP {response.status_code}: {response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("AI Commands", False, f"Error: {str(e)}")
            return False
    
    def test_performance(self) -> bool:
        """Test API performance under load"""
        def make_request():
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}/api/info", 
                                      headers=self.headers, timeout=5)
                duration = time.time() - start
                return response.status_code == 200, duration
            except:
                return False, 5.0
        
        # Run 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            start = time.time()
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            total_duration = time.time() - start
        
        successful_requests = sum(1 for success, _ in results if success)
        avg_response_time = sum(duration for _, duration in results) / len(results)
        
        if successful_requests >= 45 and avg_response_time < 2.0:
            self.log_result("Performance Test", True, 
                          f"{successful_requests}/50 requests successful, avg: {avg_response_time:.2f}s", 
                          total_duration)
            return True
        else:
            self.log_result("Performance Test", False, 
                          f"Only {successful_requests}/50 successful, avg: {avg_response_time:.2f}s", 
                          total_duration)
            return False
    
    def test_security_features(self) -> bool:
        """Test security features"""
        # Test rate limiting
        rate_limit_passed = True
        try:
            # Make rapid requests to trigger rate limiting
            for i in range(20):
                response = requests.get(f"{self.base_url}/api/info", 
                                      headers=self.headers, timeout=1)
                if response.status_code == 429:  # Too Many Requests
                    self.log_result("Rate Limiting", True, 
                                  f"Rate limiting triggered after {i+1} requests")
                    break
            else:
                self.log_result("Rate Limiting", False, 
                              "Rate limiting not triggered after 20 requests")
                rate_limit_passed = False
                
        except Exception as e:
            self.log_result("Rate Limiting", False, f"Error: {str(e)}")
            rate_limit_passed = False
        
        # Test input validation
        validation_passed = True
        try:
            malicious_data = {
                "company_name": "'; DROP TABLE companies; --",
                "description": "<script>alert('xss')</script>"
            }
            
            response = requests.post(f"{self.base_url}/api/companies", 
                                   headers=self.headers, 
                                   json=malicious_data, timeout=5)
            
            # Should either reject the input or sanitize it
            if response.status_code in [400, 422]:
                self.log_result("Input Validation", True, 
                              "Malicious input properly rejected")
            else:
                self.log_result("Input Validation", False, 
                              f"Malicious input not rejected: {response.status_code}")
                validation_passed = False
                
        except Exception as e:
            self.log_result("Input Validation", False, f"Error: {str(e)}")
            validation_passed = False
            
        return rate_limit_passed and validation_passed
    
    def run_all_tests(self) -> Dict:
        """Run all production tests"""
        print("🚀 Starting Elite Command Data API Production Testing Suite")
        print(f"Target URL: {self.base_url}")
        print(f"Start Time: {self.start_time.isoformat()}")
        print("=" * 80)
        
        # Run tests in order
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Health Endpoints", self.test_health_endpoints),
            ("Authentication", self.test_authentication),
            ("Data Ingestion", self.test_data_ingestion),
            ("HSI Functionality", self.test_hsi_functionality),
            ("AI Commands", self.test_ai_commands),
            ("Performance", self.test_performance),
            ("Security Features", self.test_security_features)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test_name, False, f"Test failed with exception: {str(e)}")
        
        # Generate summary
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 PRODUCTION TESTING SUMMARY")
        print("=" * 80)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"End Time: {end_time.isoformat()}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED - REVIEW REQUIRED")
        
        return {
            'passed': passed_tests,
            'total': total_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'duration': total_duration,
            'results': self.test_results,
            'production_ready': passed_tests == total_tests
        }

def main():
    """Main testing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Elite Command Data API Production Testing')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the API (default: http://localhost:5000)')
    parser.add_argument('--api-key', default=None,
                       help='API key for authentication (default: from environment)')
    parser.add_argument('--output', default=None,
                       help='Output file for test results (JSON format)')
    
    args = parser.parse_args()
    
    # Run tests
    tester = ProductionTester(base_url=args.url, api_key=args.api_key)
    results = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results['production_ready'] else 1)

if __name__ == "__main__":
    main()

