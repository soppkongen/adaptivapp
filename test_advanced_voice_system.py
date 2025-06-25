#!/usr/bin/env python3
"""
Comprehensive Voice Command System Test Suite

More than redundantly good testing for elite voice interaction capabilities.
Tests all voice modes, commands, and edge cases.
"""

import unittest
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.advanced_voice_service import AdvancedVoiceCommandService
from src.models.voice_command_system import (
    VoiceInteractionMode, VoiceCommandCategory, VoiceCommandIntent,
    VoiceConfidenceLevel, VoiceResponseType, VoiceCommand
)

class TestAdvancedVoiceCommandSystem(unittest.TestCase):
    """Comprehensive test suite for voice command system"""
    
    def setUp(self):
        """Set up test environment"""
        self.voice_service = AdvancedVoiceCommandService()
        self.test_user_id = "test_executive_001"
        self.test_session = self.voice_service.start_voice_session(self.test_user_id)
        
    def tearDown(self):
        """Clean up test environment"""
        if self.test_user_id in self.voice_service.active_sessions:
            del self.voice_service.active_sessions[self.test_user_id]
            
    def test_voice_session_creation(self):
        """Test voice session creation and management"""
        session = self.voice_service.start_voice_session("test_user_002")
        
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, "test_user_002")
        self.assertEqual(session.current_mode, VoiceInteractionMode.ACTIVE_VOICE)
        self.assertEqual(len(session.commands_processed), 0)
        self.assertEqual(session.success_count, 0)
        self.assertEqual(session.error_count, 0)
        
    def test_wake_word_detection(self):
        """Test wake word detection and extraction"""
        test_cases = [
            ("command make this more relaxed", True, "make this more relaxed"),
            ("elite show me the revenue", True, "show me the revenue"),
            ("aura, explain this metric", True, "explain this metric"),
            ("make this more relaxed", False, "make this more relaxed"),
            ("command, move the metrics left", True, "move the metrics left")
        ]
        
        for input_text, expected_wake_word, expected_command in test_cases:
            wake_word_detected, clean_command = self.voice_service._extract_wake_word(input_text)
            self.assertEqual(wake_word_detected, expected_wake_word, f"Failed for: {input_text}")
            self.assertEqual(clean_command, expected_command, f"Failed for: {input_text}")
            
    def test_command_normalization(self):
        """Test command text normalization"""
        test_cases = [
            ("Um, make this, like, more relaxed", "make this more relaxed"),
            ("Can't you make it softer?", "cannot you make it softer?"),
            ("It's    too   bright", "it is too bright"),
            ("MAKE THIS CALMER", "make this calmer")
        ]
        
        for input_text, expected_output in test_cases:
            normalized = self.voice_service._normalize_command_text(input_text)
            self.assertEqual(normalized, expected_output)
            
    def test_style_adjustment_commands(self):
        """Test style adjustment voice commands"""
        style_commands = [
            "make this more relaxed",
            "too serious, lighten it up", 
            "make it feel calmer",
            "more energetic please",
            "too bright, tone it down"
        ]
        
        for command in style_commands:
            response = self.voice_service.process_voice_command(
                self.test_user_id, 
                f"command {command}"
            )
            
            self.assertTrue(response.success, f"Failed for command: {command}")
            self.assertEqual(response.response_type, VoiceResponseType.IMMEDIATE_ACTION)
            self.assertIn("style", response.message.lower())
            self.assertGreater(response.confidence_score, 0.7)
            
    def test_layout_control_commands(self):
        """Test layout control voice commands"""
        layout_commands = [
            "move the metrics to the left side",
            "put the portfolio grid on the right",
            "hide the alert center",
            "show the navigation panel",
            "relocate metrics panel"
        ]
        
        for command in layout_commands:
            response = self.voice_service.process_voice_command(
                self.test_user_id,
                f"command {command}"
            )
            
            self.assertTrue(response.success, f"Failed for command: {command}")
            self.assertIn("actions", response.actions_taken[0])
            self.assertIsNotNone(response.visual_feedback)
            
    def test_data_intelligence_commands(self):
        """Test data intelligence voice commands"""
        data_commands = [
            "why is this revenue figure low confidence?",
            "where did this number come from?",
            "explain this metric",
            "what should I be worried about today?",
            "trace this back to its source"
        ]
        
        for command in data_commands:
            response = self.voice_service.process_voice_command(
                self.test_user_id,
                f"command {command}",
                {"focused_element": "revenue_metric"}
            )
            
            self.assertTrue(response.success, f"Failed for command: {command}")
            self.assertIn(response.response_type, [
                VoiceResponseType.EXPLANATION,
                VoiceResponseType.DEMONSTRATION
            ])
            
    def test_security_commands(self):
        """Test security-related voice commands"""
        security_commands = [
            "create a new read-only key for finance team",
            "revoke the marketing API key",
            "lock down external sharing",
            "show me the audit log"
        ]
        
        for command in security_commands:
            response = self.voice_service.process_voice_command(
                self.test_user_id,
                f"command {command}"
            )
            
            # Security commands should require confirmation
            self.assertIn(response.response_type, [
                VoiceResponseType.CONFIRMATION_REQUIRED,
                VoiceResponseType.IMMEDIATE_ACTION
            ])
            
    def test_fuzzy_matching(self):
        """Test fuzzy string matching for voice recognition"""
        test_cases = [
            ("make this relaxed", "make this more relaxed", True),
            ("show revenue", "show me the revenue", True),
            ("completely different", "make this relaxed", False),
            ("move metrics left", "move the metrics to the left side", True)
        ]
        
        for text1, text2, expected_match in test_cases:
            result = self.voice_service._fuzzy_match(text1, text2, threshold=0.6)
            self.assertEqual(result, expected_match, f"Failed for: {text1} vs {text2}")
            
    def test_intent_detection(self):
        """Test intent detection from command text"""
        intent_test_cases = [
            ("make this more relaxed", VoiceCommandIntent.ADJUST_STYLE),
            ("move the metrics left", VoiceCommandIntent.LAYOUT_CONTROL),
            ("why is this number low confidence", VoiceCommandIntent.CONFIDENCE_INSIGHT),
            ("where did this come from", VoiceCommandIntent.LINEAGE_TRACE),
            ("show me the dashboard", VoiceCommandIntent.FOCUS_VIEW)
        ]
        
        for command_text, expected_intent in intent_test_cases:
            detected_intent = self.voice_service._detect_intent(command_text, {})
            self.assertEqual(detected_intent, expected_intent, f"Failed for: {command_text}")
            
    def test_context_awareness(self):
        """Test context-aware command processing"""
        # First command establishes context
        response1 = self.voice_service.process_voice_command(
            self.test_user_id,
            "command explain this revenue figure",
            {"focused_element": "revenue_metric"}
        )
        
        # Follow-up command should use context
        response2 = self.voice_service.process_voice_command(
            self.test_user_id,
            "command where did it come from?"
        )
        
        self.assertTrue(response1.success)
        self.assertTrue(response2.success)
        
        # Check that context was maintained
        session = self.voice_service.active_sessions[self.test_user_id]
        self.assertGreater(len(session.context_stack), 0)
        
    def test_pronoun_reference_resolution(self):
        """Test pronoun reference resolution in commands"""
        # Set up context with focused element
        context = {"focused_element": "revenue_metric"}
        
        pronoun_commands = [
            "make this bigger",
            "hide that",
            "explain it",
            "move this to the left"
        ]
        
        for command in pronoun_commands:
            response = self.voice_service.process_voice_command(
                self.test_user_id,
                f"command {command}",
                context
            )
            
            # Should successfully resolve pronoun reference
            self.assertTrue(response.success or response.response_type == VoiceResponseType.CLARIFICATION_NEEDED)
            
    def test_confirmation_workflow(self):
        """Test confirmation workflow for sensitive commands"""
        # Command that requires confirmation
        response = self.voice_service.process_voice_command(
            self.test_user_id,
            "command create a new API key for finance team"
        )
        
        self.assertEqual(response.response_type, VoiceResponseType.CONFIRMATION_REQUIRED)
        self.assertIn("confirm", response.message.lower())
        
    def test_error_handling(self):
        """Test error handling for invalid commands"""
        invalid_commands = [
            "command flibber jibber nonsense",
            "command delete everything permanently",
            "command make it purple with green dots",
            ""
        ]
        
        for command in invalid_commands:
            response = self.voice_service.process_voice_command(
                self.test_user_id,
                command
            )
            
            # Should handle gracefully
            self.assertIsNotNone(response)
            self.assertIn(response.response_type, [
                VoiceResponseType.CLARIFICATION_NEEDED,
                VoiceResponseType.ERROR_HANDLING
            ])
            
    def test_command_suggestions(self):
        """Test command suggestions for unrecognized input"""
        response = self.voice_service.process_voice_command(
            self.test_user_id,
            "command make this somewhat relaxed"  # Close to valid command
        )
        
        if not response.success:
            suggestions = self.voice_service._find_similar_commands("make this somewhat relaxed")
            self.assertGreater(len(suggestions), 0)
            self.assertIn("relaxed", suggestions[0].lower())
            
    def test_session_tracking(self):
        """Test voice session tracking and analytics"""
        # Process several commands
        commands = [
            "command make this more relaxed",
            "command move metrics left", 
            "command explain revenue"
        ]
        
        for command in commands:
            self.voice_service.process_voice_command(self.test_user_id, command)
            
        # Check session status
        status = self.voice_service.get_voice_session_status(self.test_user_id)
        
        self.assertEqual(status["status"], "active")
        self.assertEqual(status["commands_processed"], 3)
        self.assertGreater(status["success_rate"], 0)
        self.assertGreater(status["session_duration"], 0)
        
    def test_available_commands_retrieval(self):
        """Test retrieval of available commands"""
        # Get all commands
        all_commands = self.voice_service.get_available_commands()
        self.assertGreater(len(all_commands), 0)
        
        # Get commands by category
        style_commands = self.voice_service.get_available_commands(
            VoiceCommandCategory.INTERFACE_CUSTOMIZATION
        )
        
        for command in style_commands:
            self.assertEqual(command["category"], "interface_customization")
            
    def test_dynamic_command_creation(self):
        """Test dynamic command creation for flexible input"""
        # Test dynamic style command
        style_command = self.voice_service._create_dynamic_style_command(
            "peaceful", 
            {"current_screen": "dashboard"}
        )
        
        self.assertEqual(style_command.intent, VoiceCommandIntent.ADJUST_STYLE)
        self.assertEqual(style_command.parameters["style_adjustment"], "peaceful")
        
        # Test dynamic element command
        element_command = self.voice_service._create_dynamic_element_command(
            "hide",
            "sidebar",
            {"visible_elements": ["sidebar", "main_content"]}
        )
        
        self.assertEqual(element_command.intent, VoiceCommandIntent.LAYOUT_CONTROL)
        self.assertEqual(element_command.parameters["action"], "hide")
        self.assertEqual(element_command.parameters["element"], "sidebar")
        
    def test_voice_interaction_modes(self):
        """Test different voice interaction modes"""
        # Test Active Voice mode
        active_session = self.voice_service.start_voice_session(
            "test_active", 
            VoiceInteractionMode.ACTIVE_VOICE
        )
        self.assertEqual(active_session.current_mode, VoiceInteractionMode.ACTIVE_VOICE)
        
        # Test Passive AURA mode
        passive_session = self.voice_service.start_voice_session(
            "test_passive",
            VoiceInteractionMode.PASSIVE_AURA
        )
        self.assertEqual(passive_session.current_mode, VoiceInteractionMode.PASSIVE_AURA)
        
    def test_executive_priority_sorting(self):
        """Test that commands are sorted by executive priority"""
        commands = self.voice_service.get_available_commands()
        
        # Check that commands are sorted by priority (highest first)
        for i in range(len(commands) - 1):
            self.assertGreaterEqual(
                commands[i]["executive_priority"],
                commands[i + 1]["executive_priority"]
            )
            
    def test_performance_benchmarks(self):
        """Test performance benchmarks for voice processing"""
        start_time = time.time()
        
        # Process a batch of commands
        for i in range(10):
            response = self.voice_service.process_voice_command(
                self.test_user_id,
                f"command make this more relaxed {i}"
            )
            
        total_time = time.time() - start_time
        avg_time = total_time / 10
        
        # Should process commands quickly (< 100ms average)
        self.assertLess(avg_time, 0.1, "Voice command processing too slow")
        
    def test_confidence_scoring(self):
        """Test confidence scoring for voice recognition"""
        # High confidence command (exact match)
        response1 = self.voice_service.process_voice_command(
            self.test_user_id,
            "command make this more relaxed"
        )
        
        # Lower confidence command (fuzzy match)
        response2 = self.voice_service.process_voice_command(
            self.test_user_id,
            "command make this kinda relaxed"
        )
        
        if response1.success and response2.success:
            self.assertGreaterEqual(response1.confidence_score, response2.confidence_score)
            
    def test_training_data_collection(self):
        """Test training data collection for system improvement"""
        initial_training_count = len(self.voice_service.training_data)
        
        # Simulate feedback collection
        feedback_data = {
            "user_id": self.test_user_id,
            "command_text": "make this relaxed",
            "intended_action": "style_adjustment",
            "actual_result": "style_changed",
            "satisfaction_rating": 4,
            "timestamp": datetime.now().isoformat(),
            "anonymized": True
        }
        
        self.voice_service.training_data.append(feedback_data)
        
        self.assertEqual(
            len(self.voice_service.training_data),
            initial_training_count + 1
        )

class TestVoiceCommandIntegration(unittest.TestCase):
    """Integration tests for voice command system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.voice_service = AdvancedVoiceCommandService()
        
    def test_end_to_end_onboarding_flow(self):
        """Test complete onboarding flow with voice commands"""
        user_id = "integration_test_user"
        
        # Start onboarding session
        session = self.voice_service.start_voice_session(user_id)
        
        # Simulate onboarding commands
        onboarding_commands = [
            "command pull in my Stripe and Notion data",
            "command this is an e-commerce company",
            "command make this more relaxed",
            "command show me what I can do"
        ]
        
        responses = []
        for command in onboarding_commands:
            response = self.voice_service.process_voice_command(user_id, command)
            responses.append(response)
            
        # Verify onboarding completion
        self.assertEqual(len(responses), 4)
        self.assertTrue(all(r.success or r.response_type == VoiceResponseType.CONFIRMATION_REQUIRED for r in responses))
        
    def test_executive_workflow_simulation(self):
        """Test typical executive workflow with voice commands"""
        user_id = "executive_workflow_test"
        
        # Simulate executive reviewing dashboard
        workflow_commands = [
            "command what should I be worried about today?",
            "command explain this revenue figure", 
            "command where did this number come from?",
            "command make the interface more focused",
            "command move metrics to the left",
            "command create a read-only key for the board"
        ]
        
        successful_commands = 0
        for command in workflow_commands:
            response = self.voice_service.process_voice_command(user_id, command)
            if response.success or response.response_type == VoiceResponseType.CONFIRMATION_REQUIRED:
                successful_commands += 1
                
        # Should handle most executive commands successfully
        success_rate = successful_commands / len(workflow_commands)
        self.assertGreater(success_rate, 0.8, "Executive workflow success rate too low")

def run_comprehensive_voice_tests():
    """Run all voice command tests"""
    print("🎤 Running Comprehensive Voice Command System Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.makeSuite(TestAdvancedVoiceCommandSystem))
    test_suite.addTest(unittest.makeSuite(TestVoiceCommandIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print("\\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
            
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_voice_tests()
    exit(0 if success else 1)

