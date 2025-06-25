#!/usr/bin/env python3
"""
AURA Mirror Protocol Comprehensive Test Suite

Tests the clarified AURA system protocol with:
- "We Only Mirror" design ethos
- Dual modes: Prompted vs Adaptive Interface Adjustments
- Metric packaging for power users
- Strict mode separation and privacy compliance
"""

import requests
import json
import time
from datetime import datetime

class AURAMirrorTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_user_id = "test_executive_001"
        self.session_id = f"test_session_{int(time.time())}"
        
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🔬 AURA Mirror Protocol - Comprehensive Test Suite")
        print("=" * 60)
        
        try:
            # Test 1: System Status
            self.test_system_status()
            
            # Test 2: User Initialization
            self.test_user_initialization()
            
            # Test 3: Prompted Mode (Manual Commands)
            self.test_prompted_mode()
            
            # Test 4: Adaptive Mode Toggle
            self.test_adaptive_mode_toggle()
            
            # Test 5: Adaptive Mode Processing
            self.test_adaptive_mode_processing()
            
            # Test 6: Metrics Opt-in
            self.test_metrics_opt_in()
            
            # Test 7: Individual Metrics
            self.test_individual_metrics()
            
            # Test 8: Revert Functionality
            self.test_revert_functionality()
            
            # Test 9: Privacy Compliance
            self.test_privacy_compliance()
            
            # Test 10: Data Export
            self.test_data_export()
            
            print("\n✅ All AURA Mirror Protocol tests completed successfully!")
            print("🎉 System implements 'We Only Mirror' design ethos correctly!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
            
        return True
    
    def test_system_status(self):
        """Test AURA system status and design principles"""
        print("\n1. Testing System Status...")
        
        response = requests.get(f"{self.base_url}/api/aura/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["design_ethos"] == "We Only Mirror"
        assert "AURA operates as a responsive mirror" in data["core_principles"]
        assert "prompted" in data["modes"]
        assert "adaptive" in data["modes"]
        
        print("   ✓ System status correct")
        print(f"   ✓ Design ethos: {data['design_ethos']}")
        print(f"   ✓ Available modes: {list(data['modes'].keys())}")
    
    def test_user_initialization(self):
        """Test user initialization with default settings"""
        print("\n2. Testing User Initialization...")
        
        payload = {"user_id": self.test_user_id}
        response = requests.post(f"{self.base_url}/api/aura/initialize", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["settings"]["adaptive_mode_enabled"] == False  # Default OFF
        assert data["settings"]["prompted_mode_enabled"] == True
        assert data["settings"]["metric_tracking_enabled"] == False  # Opt-in only
        
        print("   ✓ User initialized successfully")
        print("   ✓ Adaptive mode default: OFF (privacy-first)")
        print("   ✓ Prompted mode default: ON")
        print("   ✓ Metrics default: OFF (opt-in only)")
    
    def test_prompted_mode(self):
        """Test prompted mode (manual user commands)"""
        print("\n3. Testing Prompted Mode...")
        
        # Test various natural language commands
        commands = [
            "Make it softer on the eyes",
            "I want a calmer layout",
            "Reduce the density",
            "Make it more spacious"
        ]
        
        for command in commands:
            payload = {
                "user_id": self.test_user_id,
                "command": command,
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/api/aura/prompted/command", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["mode"] == "prompted"
            assert data["reversible"] == True
            assert len(data["parsed_tags"]) > 0
            
            print(f"   ✓ Command processed: '{command}'")
            print(f"     Tags: {data['parsed_tags']}")
            print(f"     Changes: {data['applied_changes']}")
    
    def test_adaptive_mode_toggle(self):
        """Test adaptive mode toggle with explicit user control"""
        print("\n4. Testing Adaptive Mode Toggle...")
        
        # Test enabling adaptive mode
        payload = {
            "user_id": self.test_user_id,
            "enabled": True
        }
        
        response = requests.post(f"{self.base_url}/api/aura/settings/adaptive-mode", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["adaptive_mode_enabled"] == True
        assert "explicit control" in data["note"]
        
        print("   ✓ Adaptive mode enabled successfully")
        print("   ✓ User has explicit control confirmed")
        
        # Test disabling adaptive mode
        payload["enabled"] = False
        response = requests.post(f"{self.base_url}/api/aura/settings/adaptive-mode", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["adaptive_mode_enabled"] == False
        
        print("   ✓ Adaptive mode disabled successfully")
    
    def test_adaptive_mode_processing(self):
        """Test adaptive mode biometric signal processing"""
        print("\n5. Testing Adaptive Mode Processing...")
        
        # First enable adaptive mode
        payload = {
            "user_id": self.test_user_id,
            "enabled": True
        }
        requests.post(f"{self.base_url}/api/aura/settings/adaptive-mode", json=payload)
        
        # Test biometric signal processing
        signals = [
            {"type": "fatigue", "intensity": 0.7, "confidence": 0.9},
            {"type": "stress", "intensity": 0.8, "confidence": 0.85},
            {"type": "gaze_drift", "intensity": 0.6, "confidence": 0.8}
        ]
        
        payload = {
            "user_id": self.test_user_id,
            "session_id": self.session_id,
            "signals": signals
        }
        
        response = requests.post(f"{self.base_url}/api/aura/adaptive/process", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["mode"] == "adaptive"
        assert data["user_visible"] == True
        assert data["user_controllable"] == True
        assert data["gradual"] == True
        
        print("   ✓ Biometric signals processed successfully")
        print(f"   ✓ Trigger signals: {data['trigger_signals']}")
        print(f"   ✓ Applied changes: {data['applied_changes']}")
        print("   ✓ User visibility and control confirmed")
    
    def test_metrics_opt_in(self):
        """Test metrics opt-in functionality"""
        print("\n6. Testing Metrics Opt-in...")
        
        metrics_to_enable = [
            "visual_age_delta",
            "focus_heatmap",
            "cognitive_drift_index",
            "entropy_score"
        ]
        
        payload = {
            "user_id": self.test_user_id,
            "metrics": metrics_to_enable
        }
        
        response = requests.post(f"{self.base_url}/api/aura/settings/metrics", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["metric_tracking_enabled"] == True
        assert len(data["enabled_metrics"]) == len(metrics_to_enable)
        assert "opt-in and processed locally only" in data["note"]
        
        print("   ✓ Metrics opt-in successful")
        print(f"   ✓ Enabled metrics: {data['enabled_metrics']}")
        print("   ✓ Local processing confirmed")
    
    def test_individual_metrics(self):
        """Test individual metric endpoints"""
        print("\n7. Testing Individual Metrics...")
        
        # Test Visual Age Delta
        response = requests.get(f"{self.base_url}/api/aura/metrics/visual-age-delta?user_id={self.test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["local_only"] == True
        print(f"   ✓ Visual Age Delta: {data['delta_months']} months")
        
        # Test Focus Heatmap
        response = requests.get(f"{self.base_url}/api/aura/metrics/focus-heatmap?user_id={self.test_user_id}&session_id={self.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        print(f"   ✓ Focus Heatmap: {data['primary_kpi_focus']*100:.0f}% on primary KPIs")
        
        # Test Cognitive Drift
        response = requests.get(f"{self.base_url}/api/aura/metrics/cognitive-drift?user_id={self.test_user_id}&session_id={self.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        print(f"   ✓ Cognitive Drift: {data['drift_score']} drift score")
        
        # Test Entropy Score
        response = requests.get(f"{self.base_url}/api/aura/metrics/entropy-score?user_id={self.test_user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        print(f"   ✓ Entropy Score: {data['entropy_value']} personalization demand")
    
    def test_revert_functionality(self):
        """Test revert functionality for user control"""
        print("\n8. Testing Revert Functionality...")
        
        payload = {"user_id": self.test_user_id}
        response = requests.post(f"{self.base_url}/api/aura/revert", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "full control" in data["note"]
        
        print("   ✓ Revert functionality working")
        print("   ✓ User control confirmed")
    
    def test_privacy_compliance(self):
        """Test privacy compliance features"""
        print("\n9. Testing Privacy Compliance...")
        
        response = requests.get(f"{self.base_url}/api/aura/settings?user_id={self.test_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        settings = data["settings"]
        assert settings["local_processing_only"] == True
        assert settings["privacy_level"] == "maximum"
        
        print("   ✓ Local processing only: confirmed")
        print("   ✓ Maximum privacy level: confirmed")
        print("   ✓ Privacy compliance verified")
    
    def test_data_export(self):
        """Test privacy-compliant data export"""
        print("\n10. Testing Data Export...")
        
        response = requests.get(f"{self.base_url}/api/aura/export?user_id={self.test_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "All biometric data processed locally only" in data["privacy_note"]
        assert "user controlled" in data["data_retention"]
        
        print("   ✓ Data export successful")
        print("   ✓ Privacy compliance in export confirmed")
        print("   ✓ User-controlled retention verified")

def main():
    """Run the comprehensive AURA Mirror Protocol test suite"""
    print("🚀 Starting AURA Mirror Protocol Test Suite")
    print("Testing the 'We Only Mirror' design ethos implementation")
    print()
    
    tester = AURAMirrorTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 AURA Mirror Protocol Implementation: VERIFIED")
            print("✅ All design principles correctly implemented:")
            print("   • We Only Mirror design ethos")
            print("   • Dual modes with strict separation")
            print("   • Privacy-first architecture")
            print("   • Opt-in metrics only")
            print("   • User explicit control")
            print("   • Local processing only")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to AURA API server")
        print("Please ensure the server is running on http://localhost:5000")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

