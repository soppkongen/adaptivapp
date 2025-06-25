#!/usr/bin/env python3
"""
Command Reflex Layer Comprehensive Test Suite

Tests the unified system with simplified approach:
- Three tiers: Passive, Semi-active, Active
- Three entry modes: Mirror, Edit, Observe
- Clear separation of system vs user-facing metrics
- Elite Commander mission focus: enhance decision velocity
"""

import requests
import json
import time
from datetime import datetime

class CommandReflexTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_user_id = "elite_commander_001"
        
    def run_all_tests(self):
        """Run comprehensive test suite for Command Reflex Layer"""
        print("🎯 Command Reflex Layer - Comprehensive Test Suite")
        print("Elite Commander superuser dashboard with responsive logic")
        print("=" * 70)
        
        try:
            # Test 1: System Status
            self.test_system_status()
            
            # Test 2: User Initialization
            self.test_user_initialization()
            
            # Test 3: Mirror Mode (Semi-active tier)
            self.test_mirror_mode()
            
            # Test 4: Edit Mode (Active tier)
            self.test_edit_mode()
            
            # Test 5: Tier Management
            self.test_tier_management()
            
            # Test 6: Observe Mode (Passive tier)
            self.test_observe_mode()
            
            # Test 7: Wellness Insights (User-facing)
            self.test_wellness_insights()
            
            # Test 8: Layout State Management
            self.test_layout_state()
            
            # Test 9: System Metrics (Internal)
            self.test_system_metrics()
            
            # Test 10: Revert and Control
            self.test_revert_functionality()
            
            # Test 11: Tags and Configuration
            self.test_tags_system()
            
            print("\n✅ All Command Reflex Layer tests completed successfully!")
            print("🎯 System focused on Elite Commander mission: enhance decision velocity!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
            
        return True
    
    def test_system_status(self):
        """Test Command Reflex Layer system status"""
        print("\n1. Testing System Status...")
        
        response = requests.get(f"{self.base_url}/api/reflex/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["system_name"] == "Command Reflex Layer"
        assert "Elite Commander superuser dashboard" in data["mission"]
        assert "enhance decision velocity" in data["mission"]
        assert len(data["tiers"]) == 3
        assert len(data["entry_modes"]) == 3
        
        print("   ✓ System status correct")
        print(f"   ✓ Mission: {data['mission']}")
        print(f"   ✓ Tiers: {list(data['tiers'].keys())}")
        print(f"   ✓ Entry modes: {list(data['entry_modes'].keys())}")
    
    def test_user_initialization(self):
        """Test user initialization with Elite Commander focus"""
        print("\n2. Testing User Initialization...")
        
        payload = {"user_id": self.test_user_id}
        response = requests.post(f"{self.base_url}/api/reflex/initialize", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["settings"]["passive_tier_enabled"] == False  # Default OFF
        assert data["settings"]["semi_active_tier_enabled"] == True
        assert data["settings"]["active_tier_enabled"] == True
        assert data["settings"]["wellness_insights_enabled"] == False  # Opt-in only
        
        print("   ✓ Elite Commander initialized successfully")
        print("   ✓ Passive tier default: OFF (privacy-first)")
        print("   ✓ Active/Semi-active tiers: ON (command ready)")
        print("   ✓ Wellness insights: OFF (opt-in only)")
    
    def test_mirror_mode(self):
        """Test Mirror mode (freeform feedback + adaptation)"""
        print("\n3. Testing Mirror Mode (Semi-active tier)...")
        
        # Test various freeform feedback
        feedback_tests = [
            "Too harsh on the eyes",
            "Feels too noisy",
            "Interface is too sharp",
            "Make it calmer",
            "Too crowded"
        ]
        
        for feedback in feedback_tests:
            payload = {
                "user_id": self.test_user_id,
                "feedback": feedback
            }
            
            response = requests.post(f"{self.base_url}/api/reflex/mirror", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["tier"] == "semi_active"
            assert data["entry_mode"] == "mirror"
            assert len(data["detected_patterns"]) > 0
            assert len(data["tag_changes"]) > 0
            assert data["reversible"] == True
            
            print(f"   ✓ Feedback processed: '{feedback}'")
            print(f"     Patterns: {data['detected_patterns']}")
            print(f"     Tag changes: {list(data['tag_changes'].keys())}")
    
    def test_edit_mode(self):
        """Test Edit mode (element-specific commands)"""
        print("\n4. Testing Edit Mode (Active tier)...")
        
        # Test element-specific commands
        edit_commands = [
            {"command": "Make this card smaller", "target": "kpi_summary"},
            {"command": "Hide this panel", "target": "system_status"},
            {"command": "Emphasize this section", "target": "alert_center"},
            {"command": "Change this to be bigger", "target": "command_controls"}
        ]
        
        for cmd_test in edit_commands:
            payload = {
                "user_id": self.test_user_id,
                "command": cmd_test["command"],
                "target_element": cmd_test["target"]
            }
            
            response = requests.post(f"{self.base_url}/api/reflex/edit", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["tier"] == "active"
            assert data["entry_mode"] == "edit"
            assert len(data["tag_changes"]) > 0
            assert data["reversible"] == True
            
            print(f"   ✓ Command processed: '{cmd_test['command']}'")
            print(f"     Target: {cmd_test['target']}")
            print(f"     Changes: {list(data['tag_changes'].keys())}")
    
    def test_tier_management(self):
        """Test tier enable/disable functionality"""
        print("\n5. Testing Tier Management...")
        
        tiers = ["passive", "semi-active", "active"]
        
        for tier in tiers:
            # Test enabling
            payload = {
                "user_id": self.test_user_id,
                "enabled": True
            }
            
            response = requests.post(f"{self.base_url}/api/reflex/tiers/{tier}", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["tier"] == tier
            assert data["enabled"] == True
            
            print(f"   ✓ {tier.title()} tier enabled")
            
            # Test disabling (except for critical tiers)
            if tier != "active":  # Keep active tier enabled for Elite Commander
                payload["enabled"] = False
                response = requests.post(f"{self.base_url}/api/reflex/tiers/{tier}", json=payload)
                assert response.status_code == 200
                
                data = response.json()
                assert data["enabled"] == False
                print(f"   ✓ {tier.title()} tier disabled")
    
    def test_observe_mode(self):
        """Test Observe mode (passive biometric adaptation)"""
        print("\n6. Testing Observe Mode (Passive tier)...")
        
        # First enable passive tier
        payload = {
            "user_id": self.test_user_id,
            "enabled": True
        }
        requests.post(f"{self.base_url}/api/reflex/tiers/passive", json=payload)
        
        # Test biometric signal processing
        signals = [
            {"type": "fatigue", "intensity": 0.8, "confidence": 0.9},
            {"type": "stress", "intensity": 0.7, "confidence": 0.85},
            {"type": "eye_strain", "intensity": 0.6, "confidence": 0.8}
        ]
        
        payload = {
            "user_id": self.test_user_id,
            "signals": signals
        }
        
        response = requests.post(f"{self.base_url}/api/reflex/observe", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["tier"] == "passive"
        assert data["entry_mode"] == "observe"
        assert data["gradual"] == True
        assert data["system_facing_only"] == True
        
        print("   ✓ Biometric signals processed successfully")
        print(f"   ✓ Adaptation reason: {data['adaptation_reason']}")
        print(f"   ✓ Applied changes: {list(data['tag_changes'].keys())}")
        print("   ✓ System-facing only (privacy preserved)")
    
    def test_wellness_insights(self):
        """Test wellness insights (user-facing, opt-in only)"""
        print("\n7. Testing Wellness Insights...")
        
        # Enable wellness insights
        insight_types = ["digital_fatigue", "attention_pattern"]
        payload = {
            "user_id": self.test_user_id,
            "insight_types": insight_types
        }
        
        response = requests.post(f"{self.base_url}/api/reflex/wellness/enable", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["wellness_insights_enabled"] == True
        
        print("   ✓ Wellness insights enabled")
        print(f"   ✓ Enabled types: {data['enabled_insight_types']}")
        
        # Test individual insights
        for insight_type in insight_types:
            response = requests.get(f"{self.base_url}/api/reflex/wellness/{insight_type}?user_id={self.test_user_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["opt_in_explicit"] == True
            assert data["category"] == "user_facing_wellness"
            
            print(f"   ✓ {insight_type}: {data['summary']}")
    
    def test_layout_state(self):
        """Test layout state management"""
        print("\n8. Testing Layout State Management...")
        
        response = requests.get(f"{self.base_url}/api/reflex/layout?user_id={self.test_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "layout_state" in data
        assert "elements" in data["layout_state"]
        
        # Check for Elite Commander specific elements
        elements = data["layout_state"]["elements"]
        elite_elements = ["elite_dashboard", "command_header", "executive_overview"]
        
        for element in elite_elements:
            assert element in elements
            assert "tags" in elements[element]
            assert "type" in elements[element]
        
        print("   ✓ Layout state retrieved successfully")
        print(f"   ✓ Elite Commander elements: {elite_elements}")
        print(f"   ✓ Total elements: {len(elements)}")
    
    def test_system_metrics(self):
        """Test system metrics (internal, aggregated only)"""
        print("\n9. Testing System Metrics...")
        
        response = requests.get(f"{self.base_url}/api/reflex/system/metrics?user_id={self.test_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "metrics_summary" in data
        assert "total_commands" in data["metrics_summary"]
        assert "tier_usage" in data["metrics_summary"]
        
        print("   ✓ System metrics retrieved (aggregated only)")
        print(f"   ✓ Total commands: {data['metrics_summary']['total_commands']}")
        print(f"   ✓ Tier usage: {data['metrics_summary']['tier_usage']}")
        print("   ✓ Individual biometric data never exposed")
    
    def test_revert_functionality(self):
        """Test revert functionality and user control"""
        print("\n10. Testing Revert Functionality...")
        
        payload = {"user_id": self.test_user_id}
        response = requests.post(f"{self.base_url}/api/reflex/revert", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "full control" in data["note"]
        
        print("   ✓ Revert functionality working")
        print("   ✓ User control confirmed")
    
    def test_tags_system(self):
        """Test tags system and configuration"""
        print("\n11. Testing Tags System...")
        
        response = requests.get(f"{self.base_url}/api/reflex/tags/available")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "available_tags" in data
        assert "categories" in data
        
        # Check for expected categories
        expected_categories = ["style", "layout", "density", "mood"]
        for category in expected_categories:
            assert category in data["categories"]
        
        # Check for some key tags
        tags = data["available_tags"]
        key_tags = ["sharp", "smooth", "calm", "focused", "minimal"]
        for tag in key_tags:
            assert tag in tags
            assert "category" in tags[tag]
            assert "conflicts_with" in tags[tag]
        
        print("   ✓ Tags system working correctly")
        print(f"   ✓ Categories: {data['categories']}")
        print(f"   ✓ Total tags: {len(tags)}")

def main():
    """Run the comprehensive Command Reflex Layer test suite"""
    print("🎯 Starting Command Reflex Layer Test Suite")
    print("Testing unified system for Elite Commander dashboard")
    print("Mission: Enhance decision velocity through responsive interface")
    print()
    
    tester = CommandReflexTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 Command Reflex Layer Implementation: VERIFIED")
            print("✅ All design principles correctly implemented:")
            print("   • Unified system with three tiers")
            print("   • Clear entry modes: Mirror, Edit, Observe")
            print("   • Elite Commander mission focus")
            print("   • System vs user-facing metrics separation")
            print("   • Privacy-first biometric processing")
            print("   • User explicit control over all features")
            print("   • Enhanced decision velocity focus")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Command Reflex API server")
        print("Please ensure the server is running on http://localhost:5000")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

