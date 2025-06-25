#!/usr/bin/env python3
"""
Comprehensive Test Suite for Reflective Vault System

Tests all aspects of the personal AI research garden including:
- Media ingestion and processing
- Semantic analysis and decomposition
- Time-based reflection engine
- Cross-linking and connection discovery
- Output generation and harvesting
- Privacy and security features
"""

import unittest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.reflective_vault_service import ReflectiveVaultService
from src.models.reflective_vault import (
    VaultEntry, VaultEntryType, VaultPrivacyLevel, VaultRipenessLevel,
    VaultOutputType, VaultReflectionTrigger, VaultSession
)

class TestReflectiveVaultService(unittest.TestCase):
    """Test suite for the Reflective Vault Service"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.vault_service = ReflectiveVaultService(vault_directory=self.test_dir)
        self.test_user_id = "test_executive_001"
        
        # Mock external dependencies
        self.vault_service.whisper_model = Mock()
        self.vault_service.emotion_analyzer = Mock()
        self.vault_service.sentiment_analyzer = Mock()
        self.vault_service.topic_classifier = Mock()
        self.vault_service.sentence_model = Mock()
        
        # Mock vector database
        self.vault_service.vault_collection = Mock()
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_text_ingestion(self):
        """Test text content ingestion and analysis"""
        print("\\n🧪 Testing text ingestion...")
        
        # Mock semantic analysis responses
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.8}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['strategy', 'innovation', 'technology'],
            'scores': [0.9, 0.7, 0.6]
        }
        self.vault_service.emotion_analyzer.return_value = [{'label': 'optimism', 'score': 0.85}]
        self.vault_service.sentence_model.encode.return_value = [[0.1] * 384]  # Mock embedding
        
        # Test text ingestion
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        entry = loop.run_until_complete(
            self.vault_service.ingest_media(
                user_id=self.test_user_id,
                media_data="I have an innovative idea for revolutionizing our customer engagement strategy using AI-powered personalization.",
                entry_type=VaultEntryType.TEXT_NOTE,
                title="AI Strategy Innovation",
                description="Strategic thinking about customer engagement",
                privacy_level=VaultPrivacyLevel.REFLECTIVE,
                tags=["strategy", "ai", "customer"]
            )
        )
        
        loop.close()
        
        # Verify entry creation
        self.assertIsNotNone(entry)
        self.assertEqual(entry.user_id, self.test_user_id)
        self.assertEqual(entry.entry_type, VaultEntryType.TEXT_NOTE)
        self.assertEqual(entry.privacy_level, VaultPrivacyLevel.REFLECTIVE)
        self.assertEqual(entry.ripeness_level, VaultRipenessLevel.SEED)
        self.assertGreater(entry.ripeness_score, 0)
        
        # Verify semantic analysis
        self.assertIsNotNone(entry.semantic_analysis)
        self.assertIn("strategy", entry.semantic_analysis.main_themes)
        self.assertEqual(entry.semantic_analysis.intended_purpose, "strategic_planning")
        self.assertGreater(entry.semantic_analysis.strategic_value, 0)
        
        # Verify storage
        self.assertIn(entry.entry_id, self.vault_service.vault_entries)
        
        print(f"✅ Text ingestion successful: {entry.entry_id}")
        print(f"   Themes: {entry.semantic_analysis.main_themes}")
        print(f"   Strategic Value: {entry.semantic_analysis.strategic_value:.2f}")
    
    def test_audio_ingestion(self):
        """Test audio file ingestion and transcription"""
        print("\\n🎤 Testing audio ingestion...")
        
        # Mock Whisper transcription
        self.vault_service.whisper_model.transcribe.return_value = {
            "text": "This is a test audio memo about quarterly revenue projections and market expansion opportunities."
        }
        
        # Mock semantic analysis
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.7}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['finance', 'strategy', 'market'],
            'scores': [0.8, 0.6, 0.5]
        }
        self.vault_service.sentence_model.encode.return_value = [[0.2] * 384]
        
        # Create a dummy audio file
        audio_path = os.path.join(self.test_dir, "test_audio.wav")
        with open(audio_path, 'wb') as f:
            f.write(b"dummy audio data")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        entry = loop.run_until_complete(
            self.vault_service.ingest_media(
                user_id=self.test_user_id,
                media_data=audio_path,
                entry_type=VaultEntryType.VOICE_MEMO,
                title="Revenue Projections Memo",
                privacy_level=VaultPrivacyLevel.REFLECTIVE
            )
        )
        
        loop.close()
        
        # Verify entry creation
        self.assertIsNotNone(entry)
        self.assertEqual(entry.entry_type, VaultEntryType.VOICE_MEMO)
        self.assertIsNotNone(entry.media_metadata)
        self.assertIsNotNone(entry.media_metadata.transcription)
        self.assertIn("revenue", entry.media_metadata.transcription.lower())
        
        print(f"✅ Audio ingestion successful: {entry.entry_id}")
        print(f"   Transcription: {entry.media_metadata.transcription[:100]}...")
    
    def test_reflection_engine(self):
        """Test the time-based reflection engine"""
        print("\\n🔄 Testing reflection engine...")
        
        # Create a test entry
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock semantic analysis
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.8}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['innovation', 'technology'],
            'scores': [0.9, 0.7]
        }
        self.vault_service.sentence_model.encode.return_value = [[0.3] * 384]
        
        entry = loop.run_until_complete(
            self.vault_service.ingest_media(
                user_id=self.test_user_id,
                media_data="Revolutionary blockchain integration for supply chain transparency",
                entry_type=VaultEntryType.TEXT_NOTE,
                title="Blockchain Innovation",
                privacy_level=VaultPrivacyLevel.REFLECTIVE
            )
        )
        
        # Trigger manual reflection
        initial_ripeness = entry.ripeness_score
        initial_reflection_count = len(entry.reflections)
        
        loop.run_until_complete(
            self.vault_service._perform_reflection(entry.entry_id, self.test_user_id)
        )
        
        loop.close()
        
        # Verify reflection results
        updated_entry = self.vault_service.vault_entries[entry.entry_id]
        self.assertGreater(updated_entry.ripeness_score, initial_ripeness)
        self.assertGreater(len(updated_entry.reflections), initial_reflection_count)
        
        latest_reflection = updated_entry.reflections[-1]
        self.assertEqual(latest_reflection.trigger, VaultReflectionTrigger.TIME_BASED)
        self.assertIsNotNone(latest_reflection.reflection_text)
        self.assertGreater(len(latest_reflection.new_insights), 0)
        self.assertGreater(len(latest_reflection.questions_generated), 0)
        
        print(f"✅ Reflection engine successful")
        print(f"   Ripeness: {initial_ripeness:.2f} → {updated_entry.ripeness_score:.2f}")
        print(f"   New insights: {len(latest_reflection.new_insights)}")
        print(f"   Questions: {len(latest_reflection.questions_generated)}")
    
    def test_cross_linking(self):
        """Test cross-linking between related entries"""
        print("\\n🔗 Testing cross-linking...")
        
        # Mock vector database responses
        self.vault_service.vault_collection.query.return_value = {
            'ids': [['entry_2', 'entry_3']],
            'distances': [[0.4, 0.6]],
            'documents': [['Related content 1', 'Related content 2']]
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock semantic analysis
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.8}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['strategy', 'innovation'],
            'scores': [0.8, 0.7]
        }
        self.vault_service.sentence_model.encode.return_value = [[0.4] * 384]
        
        # Create first entry
        entry1 = loop.run_until_complete(
            self.vault_service.ingest_media(
                user_id=self.test_user_id,
                media_data="AI-powered customer analytics for better decision making",
                entry_type=VaultEntryType.TEXT_NOTE,
                title="AI Analytics Strategy",
                privacy_level=VaultPrivacyLevel.REFLECTIVE
            )
        )
        
        # Create related entries in the vault
        entry2 = VaultEntry(
            user_id=self.test_user_id,
            entry_type=VaultEntryType.TEXT_NOTE,
            title="Customer Data Platform",
            raw_content="Building unified customer data platform for analytics"
        )
        entry2.entry_id = "entry_2"
        
        entry3 = VaultEntry(
            user_id=self.test_user_id,
            entry_type=VaultEntryType.TEXT_NOTE,
            title="Decision Support Systems",
            raw_content="Executive decision support using machine learning"
        )
        entry3.entry_id = "entry_3"
        
        self.vault_service.vault_entries["entry_2"] = entry2
        self.vault_service.vault_entries["entry_3"] = entry3
        
        # Test cross-link discovery
        loop.run_until_complete(
            self.vault_service._discover_cross_links(entry1.entry_id)
        )
        
        loop.close()
        
        # Verify cross-links were created
        updated_entry = self.vault_service.vault_entries[entry1.entry_id]
        self.assertGreater(len(updated_entry.cross_links), 0)
        
        print(f"✅ Cross-linking successful")
        print(f"   Links created: {len(updated_entry.cross_links)}")
        print(f"   Linked entries: {updated_entry.cross_links}")
    
    def test_output_generation(self):
        """Test output generation from vault entries"""
        print("\\n📄 Testing output generation...")
        
        # Create test entries
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock semantic analysis
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.8}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['strategy', 'innovation'],
            'scores': [0.8, 0.7]
        }
        self.vault_service.sentence_model.encode.return_value = [[0.5] * 384]
        
        entry1 = loop.run_until_complete(
            self.vault_service.ingest_media(
                user_id=self.test_user_id,
                media_data="Market expansion strategy for Q4 focusing on enterprise clients",
                entry_type=VaultEntryType.TEXT_NOTE,
                title="Q4 Market Strategy",
                privacy_level=VaultPrivacyLevel.REFLECTIVE
            )
        )
        
        entry2 = loop.run_until_complete(
            self.vault_service.ingest_media(
                user_id=self.test_user_id,
                media_data="Enterprise sales team needs better CRM integration and training",
                entry_type=VaultEntryType.TEXT_NOTE,
                title="Sales Team Enhancement",
                privacy_level=VaultPrivacyLevel.REFLECTIVE
            )
        )
        
        # Test different output types
        output_types = [
            VaultOutputType.DRAFT_SLIDES,
            VaultOutputType.STRATEGIC_PROMPTS,
            VaultOutputType.ACTION_ITEMS,
            VaultOutputType.JOURNAL_FRAGMENTS
        ]
        
        for output_type in output_types:
            output = loop.run_until_complete(
                self.vault_service.generate_output(
                    user_id=self.test_user_id,
                    entry_ids=[entry1.entry_id, entry2.entry_id],
                    output_type=output_type,
                    title=f"Generated {output_type.value}"
                )
            )
            
            # Verify output
            self.assertIsNotNone(output)
            self.assertEqual(output.output_type, output_type)
            self.assertEqual(output.user_id, self.test_user_id)
            self.assertGreater(len(output.content), 0)
            self.assertGreater(output.quality_score, 0)
            
            print(f"   ✅ {output_type.value}: {len(output.content)} chars, quality: {output.quality_score:.2f}")
        
        loop.close()
        
        print(f"✅ Output generation successful for all types")
    
    def test_privacy_levels(self):
        """Test different privacy levels and their behavior"""
        print("\\n🔒 Testing privacy levels...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        privacy_levels = [
            VaultPrivacyLevel.LOCKED,
            VaultPrivacyLevel.REFLECTIVE,
            VaultPrivacyLevel.VOLATILE,
            VaultPrivacyLevel.COLLABORATIVE
        ]
        
        for privacy_level in privacy_levels:
            # Mock semantic analysis for non-locked entries
            if privacy_level != VaultPrivacyLevel.LOCKED:
                self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.8}]
                self.vault_service.topic_classifier.return_value = {
                    'labels': ['strategy'],
                    'scores': [0.8]
                }
                self.vault_service.sentence_model.encode.return_value = [[0.6] * 384]
            
            entry = loop.run_until_complete(
                self.vault_service.ingest_media(
                    user_id=self.test_user_id,
                    media_data=f"Test content for {privacy_level.value} privacy level",
                    entry_type=VaultEntryType.TEXT_NOTE,
                    title=f"Privacy Test {privacy_level.value}",
                    privacy_level=privacy_level
                )
            )
            
            # Verify privacy behavior
            if privacy_level == VaultPrivacyLevel.LOCKED:
                self.assertIsNone(entry.semantic_analysis)
                print(f"   ✅ {privacy_level.value}: No semantic analysis (as expected)")
            else:
                self.assertIsNotNone(entry.semantic_analysis)
                print(f"   ✅ {privacy_level.value}: Semantic analysis performed")
        
        loop.close()
        
        print(f"✅ Privacy level testing successful")
    
    def test_vault_analytics(self):
        """Test vault analytics and metrics"""
        print("\\n📊 Testing vault analytics...")
        
        # Create multiple entries for analytics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock semantic analysis
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.8}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['strategy', 'innovation'],
            'scores': [0.8, 0.7]
        }
        self.vault_service.sentence_model.encode.return_value = [[0.7] * 384]
        
        # Create entries of different types
        entry_types = [
            VaultEntryType.TEXT_NOTE,
            VaultEntryType.VOICE_MEMO,
            VaultEntryType.IMAGE_UPLOAD
        ]
        
        created_entries = []
        for i, entry_type in enumerate(entry_types):
            if entry_type == VaultEntryType.VOICE_MEMO:
                # Mock audio processing
                self.vault_service.whisper_model.transcribe.return_value = {
                    "text": f"Audio content {i}"
                }
                # Create dummy audio file
                audio_path = os.path.join(self.test_dir, f"test_audio_{i}.wav")
                with open(audio_path, 'wb') as f:
                    f.write(b"dummy audio data")
                media_data = audio_path
            elif entry_type == VaultEntryType.IMAGE_UPLOAD:
                # Create dummy image file
                image_path = os.path.join(self.test_dir, f"test_image_{i}.jpg")
                with open(image_path, 'wb') as f:
                    f.write(b"dummy image data")
                media_data = image_path
            else:
                media_data = f"Text content for entry {i}"
            
            entry = loop.run_until_complete(
                self.vault_service.ingest_media(
                    user_id=self.test_user_id,
                    media_data=media_data,
                    entry_type=entry_type,
                    title=f"Analytics Test Entry {i}",
                    privacy_level=VaultPrivacyLevel.REFLECTIVE
                )
            )
            created_entries.append(entry)
        
        # Trigger some reflections
        for entry in created_entries[:2]:
            loop.run_until_complete(
                self.vault_service._perform_reflection(entry.entry_id, self.test_user_id)
            )
        
        loop.close()
        
        # Get analytics
        analytics = self.vault_service.get_vault_analytics(self.test_user_id)
        
        # Verify analytics
        self.assertEqual(analytics.user_id, self.test_user_id)
        self.assertEqual(analytics.total_entries, len(created_entries))
        self.assertGreater(analytics.total_reflections, 0)
        self.assertGreater(analytics.avg_reflections_per_entry, 0)
        
        # Verify entry type breakdown
        for entry_type in entry_types:
            self.assertIn(entry_type.value, analytics.entries_by_type)
        
        print(f"✅ Analytics successful")
        print(f"   Total entries: {analytics.total_entries}")
        print(f"   Total reflections: {analytics.total_reflections}")
        print(f"   Avg reflections per entry: {analytics.avg_reflections_per_entry:.2f}")
        print(f"   Entry types: {analytics.entries_by_type}")
    
    def test_vault_session_management(self):
        """Test vault session management"""
        print("\\n🎯 Testing session management...")
        
        # Start a new session
        session = self.vault_service.start_vault_session(self.test_user_id)
        
        # Verify session creation
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, self.test_user_id)
        self.assertIsNotNone(session.session_id)
        self.assertIn(session.session_id, self.vault_service.active_sessions)
        
        # Get session
        retrieved_session = self.vault_service.get_vault_session(session.session_id)
        self.assertEqual(retrieved_session.session_id, session.session_id)
        
        # End session
        self.vault_service.end_vault_session(session.session_id)
        self.assertNotIn(session.session_id, self.vault_service.active_sessions)
        
        print(f"✅ Session management successful")
        print(f"   Session ID: {session.session_id}")
    
    def test_timeline_generation(self):
        """Test timeline view generation"""
        print("\\n📅 Testing timeline generation...")
        
        # Create entries and reflections
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock semantic analysis
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.8}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['strategy'],
            'scores': [0.8]
        }
        self.vault_service.sentence_model.encode.return_value = [[0.8] * 384]
        
        entry = loop.run_until_complete(
            self.vault_service.ingest_media(
                user_id=self.test_user_id,
                media_data="Timeline test content",
                entry_type=VaultEntryType.TEXT_NOTE,
                title="Timeline Test Entry",
                privacy_level=VaultPrivacyLevel.REFLECTIVE
            )
        )
        
        # Add reflection
        loop.run_until_complete(
            self.vault_service._perform_reflection(entry.entry_id, self.test_user_id)
        )
        
        loop.close()
        
        # Get timeline for specific entry
        entry_timeline = self.vault_service.get_vault_timeline(self.test_user_id, entry.entry_id)
        
        # Verify timeline structure
        self.assertIn('entry', entry_timeline)
        self.assertIn('reflections', entry_timeline)
        self.assertIn('cross_links', entry_timeline)
        self.assertIn('outputs', entry_timeline)
        
        # Get timeline for all entries
        user_timeline = self.vault_service.get_vault_timeline(self.test_user_id)
        
        # Verify user timeline
        self.assertIn('entries', user_timeline)
        self.assertGreater(len(user_timeline['entries']), 0)
        
        print(f"✅ Timeline generation successful")
        print(f"   Entry timeline keys: {list(entry_timeline.keys())}")
        print(f"   User timeline entries: {len(user_timeline['entries'])}")

class TestReflectiveVaultIntegration(unittest.TestCase):
    """Integration tests for the complete Reflective Vault system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.vault_service = ReflectiveVaultService(vault_directory=self.test_dir)
        self.test_user_id = "integration_test_user"
        
        # Mock external dependencies for integration tests
        self.vault_service.whisper_model = Mock()
        self.vault_service.emotion_analyzer = Mock()
        self.vault_service.sentiment_analyzer = Mock()
        self.vault_service.topic_classifier = Mock()
        self.vault_service.sentence_model = Mock()
        self.vault_service.vault_collection = Mock()
    
    def tearDown(self):
        """Clean up integration test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_complete_vault_workflow(self):
        """Test complete workflow from ingestion to output generation"""
        print("\\n🔄 Testing complete vault workflow...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock all semantic analysis
        self.vault_service.sentiment_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.9}]
        self.vault_service.topic_classifier.return_value = {
            'labels': ['strategy', 'innovation', 'technology'],
            'scores': [0.9, 0.8, 0.7]
        }
        self.vault_service.emotion_analyzer.return_value = [{'label': 'excitement', 'score': 0.85}]
        self.vault_service.sentence_model.encode.return_value = [[0.9] * 384]
        
        # Mock cross-linking
        self.vault_service.vault_collection.query.return_value = {
            'ids': [[]],
            'distances': [[]],
            'documents': [[]]
        }
        
        # Step 1: Ingest multiple related entries
        entries = []
        contents = [
            "Revolutionary AI strategy for transforming customer experience and driving growth",
            "Implementation roadmap for AI-powered personalization across all touchpoints",
            "Budget allocation and resource planning for AI transformation initiative"
        ]
        
        for i, content in enumerate(contents):
            entry = loop.run_until_complete(
                self.vault_service.ingest_media(
                    user_id=self.test_user_id,
                    media_data=content,
                    entry_type=VaultEntryType.TEXT_NOTE,
                    title=f"AI Strategy Part {i+1}",
                    privacy_level=VaultPrivacyLevel.REFLECTIVE,
                    tags=["ai", "strategy", "transformation"]
                )
            )
            entries.append(entry)
        
        # Step 2: Trigger reflections to mature the ideas
        for entry in entries:
            for _ in range(3):  # Multiple reflection cycles
                loop.run_until_complete(
                    self.vault_service._perform_reflection(entry.entry_id, self.test_user_id)
                )
        
        # Step 3: Generate various outputs
        output_types = [
            VaultOutputType.DRAFT_SLIDES,
            VaultOutputType.STRATEGIC_PROMPTS,
            VaultOutputType.ACTION_ITEMS
        ]
        
        outputs = []
        for output_type in output_types:
            output = loop.run_until_complete(
                self.vault_service.generate_output(
                    user_id=self.test_user_id,
                    entry_ids=[e.entry_id for e in entries],
                    output_type=output_type,
                    title=f"AI Strategy {output_type.value}"
                )
            )
            outputs.append(output)
        
        loop.close()
        
        # Verify complete workflow
        # Check entries matured
        for entry in entries:
            updated_entry = self.vault_service.vault_entries[entry.entry_id]
            self.assertGreater(updated_entry.ripeness_score, 0.5)  # Should be well-matured
            self.assertGreater(len(updated_entry.reflections), 2)  # Multiple reflections
        
        # Check outputs generated
        self.assertEqual(len(outputs), len(output_types))
        for output in outputs:
            self.assertGreater(len(output.content), 100)  # Substantial content
            self.assertGreater(output.quality_score, 0.5)  # Good quality
        
        # Check analytics
        analytics = self.vault_service.get_vault_analytics(self.test_user_id)
        self.assertEqual(analytics.total_entries, len(entries))
        self.assertEqual(analytics.total_outputs, len(outputs))
        self.assertGreater(analytics.total_reflections, len(entries) * 2)
        
        print(f"✅ Complete workflow successful")
        print(f"   Entries created: {len(entries)}")
        print(f"   Total reflections: {analytics.total_reflections}")
        print(f"   Outputs generated: {len(outputs)}")
        print(f"   Average ripeness: {sum(e.ripeness_score for e in entries) / len(entries):.2f}")

def run_comprehensive_tests():
    """Run all Reflective Vault tests"""
    print("🧪 Starting Comprehensive Reflective Vault Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add service tests
    service_tests = [
        'test_text_ingestion',
        'test_audio_ingestion',
        'test_reflection_engine',
        'test_cross_linking',
        'test_output_generation',
        'test_privacy_levels',
        'test_vault_analytics',
        'test_vault_session_management',
        'test_timeline_generation'
    ]
    
    for test_name in service_tests:
        test_suite.addTest(TestReflectiveVaultService(test_name))
    
    # Add integration tests
    integration_tests = [
        'test_complete_vault_workflow'
    ]
    
    for test_name in integration_tests:
        test_suite.addTest(TestReflectiveVaultIntegration(test_name))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\\n" + "=" * 60)
    print("🎯 Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\\n🎉 All tests passed! Reflective Vault system is ready for deployment.")
    else:
        print("\\n⚠️  Some tests failed. Please review and fix issues before deployment.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)

