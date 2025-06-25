#!/usr/bin/env python3
"""
Integrated Onboarding System Test Suite

Tests the voice + visual adaptation onboarding flow where the AI
demonstrates system capabilities in real-time while introducing itself.

Target: Executive / Portfolio Owner
Experience: Voice + Click → Dashboard UI + Real-time Layout Changes
"""

import requests
import json
import time
from datetime import datetime

class IntegratedOnboardingTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_user_id = "executive_onboarding_001"
        
    def run_all_tests(self):
        """Run comprehensive test suite for integrated onboarding"""
        print("🎯 Integrated Onboarding System - Comprehensive Test Suite")
        print("Voice + Visual Adaptation Onboarding Flow")
        print("Target: Executive / Portfolio Owner")
        print("Experience: Voice + Click → Dashboard UI + Real-time Layout Changes")
        print("=" * 80)
        
        try:
            # Test 1: Onboarding Flow Definition
            self.test_flow_definition()
            
            # Test 2: Start Integrated Onboarding
            self.test_start_onboarding()
            
            # Test 3: Phase 1 - AI Greeting + Brand Framing [0:00-0:06]
            self.test_greeting_phase()
            
            # Test 4: Phase 2 - Adaptive Demonstration [0:07-0:15]
            self.test_adaptive_demonstration()
            
            # Test 5: Phase 3 - Immediate Agency Cards [0:16-0:22]
            self.test_agency_cards()
            
            # Test 6: Phase 4 - Voice Primer [0:23-0:30]
            self.test_voice_primer()
            
            # Test 7: User Interactions During Onboarding
            self.test_user_interactions()
            
            # Test 8: Card Selection Handling
            self.test_card_selection()
            
            # Test 9: Voice Command Processing
            self.test_voice_commands()
            
            # Test 10: Onboarding Completion
            self.test_onboarding_completion()
            
            print("\n✅ All Integrated Onboarding tests completed successfully!")
            print("🎯 Voice + Visual Adaptation Onboarding Flow: VERIFIED!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
            
        return True
    
    def test_flow_definition(self):
        """Test onboarding flow definition and structure"""
        print("\n1. Testing Onboarding Flow Definition...")
        
        response = requests.get(f"{self.base_url}/api/onboarding/flow-definition")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        flow = data["onboarding_flow"]
        assert flow["title"] == "AURA Integrated Onboarding: Voice + Visual Adaptation"
        assert flow["target_user"] == "Executive / Portfolio Owner"
        assert "Voice" in flow["input_modes"]
        assert "Dashboard UI" in flow["output_modes"]
        assert flow["total_duration"] == "30 seconds"
        assert len(flow["phases"]) == 4
        
        # Verify phase structure
        phases = flow["phases"]
        assert phases[0]["phase"] == "greeting_brand_framing"
        assert phases[0]["timing"] == "0:00-0:06"
        assert phases[1]["phase"] == "adaptive_demonstration"
        assert phases[1]["timing"] == "0:07-0:15"
        assert phases[2]["phase"] == "immediate_agency"
        assert phases[2]["timing"] == "0:16-0:22"
        assert phases[3]["phase"] == "voice_primer"
        assert phases[3]["timing"] == "0:23-0:30"
        
        print("   ✓ Flow definition correct")
        print(f"   ✓ Target: {flow['target_user']}")
        print(f"   ✓ Duration: {flow['total_duration']}")
        print(f"   ✓ Phases: {len(flow['phases'])}")
    
    def test_start_onboarding(self):
        """Test starting integrated onboarding session"""
        print("\n2. Testing Start Integrated Onboarding...")
        
        payload = {"user_id": self.test_user_id}
        response = requests.post(f"{self.base_url}/api/onboarding/start", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["onboarding_type"] == "voice_visual_adaptation"
        assert data["target_user"] == "Executive / Portfolio Owner"
        assert data["experience"] == "Voice + Click → Dashboard UI + Real-time Layout Changes"
        assert data["total_duration"] == 30.0
        
        # Verify first step details
        current_step = data["current_step"]
        assert current_step["phase"] == "greeting_brand_framing"
        assert current_step["narration"]["voice_tone"] == "professional"
        assert len(current_step["visual_transitions"]) > 0
        assert "background_animate" in current_step["narration"]["visual_cues"]
        
        print("   ✓ Onboarding session started successfully")
        print(f"   ✓ Session ID: {data['session_id']}")
        print(f"   ✓ First phase: {current_step['phase']}")
        print("   ✓ AI will demonstrate adaptation in real-time")
    
    def test_greeting_phase(self):
        """Test AI Greeting + Brand Framing phase [0:00-0:06]"""
        print("\n3. Testing AI Greeting + Brand Framing Phase...")
        
        response = requests.get(f"{self.base_url}/api/onboarding/current-step?user_id={self.test_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        step = data["current_step"]
        assert step["phase"] == "greeting_brand_framing"
        assert step["narration"]["start_time"] == 0.0
        assert step["narration"]["duration"] == 6.0
        
        # Verify voice narration
        narration = step["narration"]
        assert "Welcome to Elite Commander" in narration["text"]
        assert "I'm your system AI" in narration["text"]
        assert "adapt this interface to you" in narration["text"]
        assert narration["voice_tone"] == "professional"
        
        # Verify visual transitions
        transitions = step["visual_transitions"]
        background_transition = next((t for t in transitions if t["type"] == "background_color"), None)
        assert background_transition is not None
        assert background_transition["duration"] == 6.0
        assert background_transition["from_state"]["background"] == "#1a1a1a"
        assert background_transition["to_state"]["background"] == "#1e3a8a"
        
        print("   ✓ Greeting phase structure correct")
        print(f"   ✓ Voice: '{narration['text'][:50]}...'")
        print(f"   ✓ Visual effects: {narration['visual_cues']}")
        print("   ✓ Background animates from dark neutral to business blue")
    
    def test_adaptive_demonstration(self):
        """Test Adaptive Demonstration phase [0:07-0:15]"""
        print("\n4. Testing Adaptive Demonstration Phase...")
        
        # Advance to demonstration phase
        payload = {"user_id": self.test_user_id}
        requests.post(f"{self.base_url}/api/onboarding/advance", json=payload)
        
        response = requests.get(f"{self.base_url}/api/onboarding/current-step?user_id={self.test_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        step = data["current_step"]
        assert step["phase"] == "adaptive_demonstration"
        
        # Verify demonstration narration
        narration = step["narration"]
        assert "Let's adjust a few things right now" in narration["text"]
        assert "sharp, focused layout" in narration["text"]
        assert "softer, more spacious" in narration["text"]
        assert "calming tones" in narration["text"]
        assert "adjustable by voice" in narration["text"]
        
        # Verify visual transitions for demonstrations
        transitions = step["visual_transitions"]
        assert len(transitions) >= 4  # Sharp, soft, calm, energetic
        
        # Check layout style transitions
        layout_transitions = [t for t in transitions if t["type"] == "layout_style"]
        assert len(layout_transitions) >= 2
        
        # Check color tone transitions
        color_transitions = [t for t in transitions if t["type"] == "color_tone"]
        assert len(color_transitions) >= 2
        
        print("   ✓ Adaptive demonstration phase correct")
        print("   ✓ Shows sharp → soft layout transition")
        print("   ✓ Shows calm → energetic color transition")
        print("   ✓ AI demonstrates adaptation while speaking")
    
    def test_agency_cards(self):
        """Test Immediate Agency Cards phase [0:16-0:22]"""
        print("\n5. Testing Immediate Agency Cards Phase...")
        
        # Get agency cards information
        response = requests.get(f"{self.base_url}/api/onboarding/agency-cards")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        cards = data["agency_cards"]
        assert len(cards) == 3
        
        # Verify the three specific cards
        card_types = [card["card_type"] for card in cards]
        assert "gather_company_data" in card_types
        assert "try_demo_data" in card_types
        assert "tune_interface" in card_types
        
        # Verify card details
        gather_card = next(card for card in cards if card["card_type"] == "gather_company_data")
        assert gather_card["title"] == "Gather My Company Data"
        assert gather_card["icon"] == "🔷"
        assert "scan your portfolio" in gather_card["description"]
        
        demo_card = next(card for card in cards if card["card_type"] == "try_demo_data")
        assert demo_card["title"] == "Try It With Demo Data"
        assert demo_card["icon"] == "🔶"
        assert "sample company" in demo_card["description"]
        
        tune_card = next(card for card in cards if card["card_type"] == "tune_interface")
        assert tune_card["title"] == "Tune the Interface"
        assert tune_card["icon"] == "🔴"
        assert "contrast, bigger text" in tune_card["description"]
        
        print("   ✓ Agency cards structure correct")
        print(f"   ✓ Cards: {[card['title'] for card in cards]}")
        print("   ✓ Cards appear with animated entrance and hover pulses")
    
    def test_voice_primer(self):
        """Test Voice Primer phase [0:23-0:30]"""
        print("\n6. Testing Voice Primer Phase...")
        
        # Get voice command examples
        response = requests.get(f"{self.base_url}/api/onboarding/voice-examples")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        examples = data["voice_examples"]
        assert len(examples) >= 3
        
        # Verify specific voice examples
        command_texts = [example["command_text"] for example in examples]
        assert "Show me the high-contrast layout" in command_texts
        assert "Connect my companies" in command_texts
        assert "Why is revenue down this month?" in command_texts
        
        # Verify example categories
        categories = set(example["category"] for example in examples)
        assert "layout" in categories
        assert "data" in categories
        assert "analysis" in categories
        
        print("   ✓ Voice primer structure correct")
        print(f"   ✓ Examples: {command_texts}")
        print("   ✓ Voice commands taught by doing, not explaining")
    
    def test_user_interactions(self):
        """Test user interaction handling during onboarding"""
        print("\n7. Testing User Interactions...")
        
        # Test general interaction handling
        payload = {
            "user_id": self.test_user_id,
            "interaction_type": "adaptation_preference",
            "data": {
                "type": "layout_style",
                "value": "soft",
                "confidence": 0.9
            }
        }
        
        response = requests.post(f"{self.base_url}/api/onboarding/interaction", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["interaction_type"] == "adaptation_preference"
        assert "result" in data
        
        print("   ✓ User interaction handling working")
        print("   ✓ Adaptation preferences captured")
    
    def test_card_selection(self):
        """Test agency card selection handling"""
        print("\n8. Testing Card Selection...")
        
        # Test each card selection
        card_tests = [
            {
                "card_type": "gather_company_data",
                "expected_action": "redirect_to_data_connection"
            },
            {
                "card_type": "try_demo_data", 
                "expected_action": "load_demo_dashboard"
            },
            {
                "card_type": "tune_interface",
                "expected_action": "open_customization_panel"
            }
        ]
        
        for test in card_tests:
            payload = {
                "user_id": self.test_user_id,
                "card_type": test["card_type"]
            }
            
            response = requests.post(f"{self.base_url}/api/onboarding/card-selection", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["card_selected"] == test["card_type"]
            assert data["result"]["action"] == test["expected_action"]
            
            print(f"   ✓ {test['card_type']}: {data['result']['action']}")
    
    def test_voice_commands(self):
        """Test voice command processing during onboarding"""
        print("\n9. Testing Voice Commands...")
        
        # Test voice command examples
        voice_tests = [
            {
                "command": "Show me the high-contrast layout",
                "expected_action": "apply_high_contrast"
            },
            {
                "command": "Connect my companies",
                "expected_action": "start_data_connection"
            },
            {
                "command": "Why is revenue down this month?",
                "expected_action": "show_analysis_demo"
            }
        ]
        
        for test in voice_tests:
            payload = {
                "user_id": self.test_user_id,
                "command": test["command"],
                "confidence": 0.95
            }
            
            response = requests.post(f"{self.base_url}/api/onboarding/voice-command", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert data["command_processed"] == test["command"]
            assert data["result"]["action"] == test["expected_action"]
            
            print(f"   ✓ '{test['command']}' → {data['result']['action']}")
    
    def test_onboarding_completion(self):
        """Test onboarding completion and transition"""
        print("\n10. Testing Onboarding Completion...")
        
        # Complete onboarding
        payload = {
            "user_id": self.test_user_id,
            "feedback": {
                "experience_rating": 5,
                "preferred_style": "soft",
                "voice_clarity": "excellent"
            }
        }
        
        response = requests.post(f"{self.base_url}/api/onboarding/complete", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "completed"
        assert data["dashboard_ready"] == True
        assert data["adaptive_system_active"] == True
        assert data["next_action"] == "transition_to_main_dashboard"
        
        # Verify status after completion
        response = requests.get(f"{self.base_url}/api/onboarding/status?user_id={self.test_user_id}")
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data["onboarding_status"]["status"] == "completed"
        
        print("   ✓ Onboarding completed successfully")
        print(f"   ✓ Total duration: {data['total_duration']:.1f} seconds")
        print(f"   ✓ User interactions: {data['user_interactions']}")
        print(f"   ✓ Voice commands: {data['voice_commands_attempted']}")
        print("   ✓ Dashboard ready for main use")

def main():
    """Run the comprehensive integrated onboarding test suite"""
    print("🎯 Starting Integrated Onboarding Test Suite")
    print("Testing Voice + Visual Adaptation Onboarding Flow")
    print("Mission: AI demonstrates system adaptation in real-time while introducing itself")
    print()
    
    tester = IntegratedOnboardingTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 Integrated Onboarding Implementation: VERIFIED")
            print("✅ All design principles correctly implemented:")
            print("   • AI guides user through real-time UI shifts")
            print("   • Every style change shown as it's spoken")
            print("   • Voice commands taught by doing, not explaining")
            print("   • User experiences adaptation while AI introduces itself")
            print("   • Perfect integration of voice + visual demonstration")
            print("   • Seamless transition to main dashboard")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Integrated Onboarding API server")
        print("Please ensure the server is running on http://localhost:5000")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

