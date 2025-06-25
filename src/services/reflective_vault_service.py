"""
Reflective Vault Service

A personal AI research garden that captures and cultivates executive thoughts over time.
Implements media ingestion, semantic analysis, time-based reflection, and output generation.
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union, Tuple
import uuid
import logging
from pathlib import Path

# Media processing imports
import whisper
import cv2
import numpy as np
from PIL import Image
import ffmpeg

# ML and NLP imports
import torch
from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Local imports
from src.models.reflective_vault import (
    VaultEntry, VaultEntryType, VaultPrivacyLevel, VaultRipenessLevel,
    VaultMediaMetadata, VaultSemanticAnalysis, VaultReflection,
    VaultCrossLink, VaultOutput, VaultOutputType, VaultReflectionTrigger,
    VaultReflectionSchedule, VaultSession, VaultAnalytics,
    REFLECTION_PROMPTS, OUTPUT_TEMPLATES
)

class ReflectiveVaultService:
    """
    Core service for the Reflective Vault system.
    Handles media ingestion, semantic analysis, reflection cycles, and output generation.
    """
    
    def __init__(self, vault_directory: str = "/tmp/reflective_vault"):
        """Initialize the Reflective Vault service"""
        self.vault_directory = Path(vault_directory)
        self.vault_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize media processing models
        self._init_media_models()
        
        # Initialize semantic analysis models
        self._init_semantic_models()
        
        # Initialize vector database for semantic search
        self._init_vector_database()
        
        # Storage for vault entries and sessions
        self.vault_entries: Dict[str, VaultEntry] = {}
        self.active_sessions: Dict[str, VaultSession] = {}
        self.reflection_schedules: Dict[str, VaultReflectionSchedule] = {}
        
        # Background reflection engine
        self.reflection_engine_active = False
        
        # Analytics tracking
        self.analytics_data: Dict[str, VaultAnalytics] = {}
        
        logging.info("Reflective Vault Service initialized")
    
    def _init_media_models(self):
        """Initialize models for media processing"""
        try:
            # Whisper for speech transcription
            self.whisper_model = whisper.load_model("base")
            
            # Face detection and emotion recognition
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Emotion recognition pipeline
            self.emotion_analyzer = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logging.info("Media processing models initialized")
            
        except Exception as e:
            logging.warning(f"Some media models failed to load: {e}")
            self.whisper_model = None
            self.emotion_analyzer = None
    
    def _init_semantic_models(self):
        """Initialize models for semantic analysis"""
        try:
            # Sentence transformer for semantic embeddings
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Text analysis pipelines
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            
            self.topic_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Predefined topic categories for executives
            self.executive_topics = [
                "strategy", "finance", "operations", "marketing", "technology",
                "leadership", "innovation", "risk_management", "partnerships",
                "market_analysis", "competitive_intelligence", "product_development",
                "customer_insights", "organizational_development", "investment"
            ]
            
            logging.info("Semantic analysis models initialized")
            
        except Exception as e:
            logging.warning(f"Some semantic models failed to load: {e}")
            self.sentence_model = None
            self.sentiment_analyzer = None
    
    def _init_vector_database(self):
        """Initialize ChromaDB for semantic search and cross-linking"""
        try:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.vault_directory / "chroma_db")
            ))
            
            # Create collection for vault entries
            self.vault_collection = self.chroma_client.get_or_create_collection(
                name="vault_entries",
                metadata={"description": "Semantic embeddings for vault entries"}
            )
            
            logging.info("Vector database initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize vector database: {e}")
            self.chroma_client = None
            self.vault_collection = None
    
    async def ingest_media(
        self,
        user_id: str,
        media_data: Union[str, bytes],
        entry_type: VaultEntryType,
        title: str = "",
        description: str = "",
        privacy_level: VaultPrivacyLevel = VaultPrivacyLevel.REFLECTIVE,
        tags: List[str] = None
    ) -> VaultEntry:
        """
        Ingest media into the vault with comprehensive analysis.
        
        Args:
            user_id: ID of the user creating the entry
            media_data: File path or binary data
            entry_type: Type of media being ingested
            title: Optional title for the entry
            description: Optional description
            privacy_level: Privacy level for the entry
            tags: Optional tags for categorization
            
        Returns:
            VaultEntry: The created vault entry
        """
        try:
            # Create new vault entry
            entry = VaultEntry(
                user_id=user_id,
                entry_type=entry_type,
                title=title or f"Vault Entry {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description=description,
                privacy_level=privacy_level,
                tags=tags or []
            )
            
            # Process media based on type
            if entry_type in [VaultEntryType.VOICE_MEMO, VaultEntryType.LIVE_MICROPHONE]:
                entry.media_metadata = await self._process_audio(media_data, entry.entry_id)
                entry.raw_content = entry.media_metadata.transcription or ""
                
            elif entry_type in [VaultEntryType.VIDEO_CAPTURE, VaultEntryType.LIVE_WEBCAM]:
                entry.media_metadata = await self._process_video(media_data, entry.entry_id)
                entry.raw_content = entry.media_metadata.transcription or ""
                
            elif entry_type in [VaultEntryType.IMAGE_UPLOAD, VaultEntryType.SKETCH_UPLOAD]:
                entry.media_metadata = await self._process_image(media_data, entry.entry_id)
                entry.raw_content = entry.media_metadata.visual_description or ""
                
            elif entry_type == VaultEntryType.TEXT_NOTE:
                entry.raw_content = media_data if isinstance(media_data, str) else media_data.decode()
                
            # Perform semantic analysis if privacy allows
            if privacy_level != VaultPrivacyLevel.LOCKED:
                entry.semantic_analysis = await self._analyze_semantics(entry.raw_content)
                
                # Add to vector database for cross-linking
                if self.vault_collection and entry.raw_content:
                    embedding = self.sentence_model.encode([entry.raw_content])[0]
                    self.vault_collection.add(
                        embeddings=[embedding.tolist()],
                        documents=[entry.raw_content],
                        metadatas=[{
                            "entry_id": entry.entry_id,
                            "user_id": user_id,
                            "created_at": entry.created_at.isoformat(),
                            "entry_type": entry_type.value
                        }],
                        ids=[entry.entry_id]
                    )
            
            # Store the entry
            self.vault_entries[entry.entry_id] = entry
            
            # Schedule first reflection
            if privacy_level in [VaultPrivacyLevel.REFLECTIVE, VaultPrivacyLevel.VOLATILE]:
                await self._schedule_reflection(entry.entry_id, user_id)
            
            # Find initial cross-links
            if privacy_level != VaultPrivacyLevel.LOCKED:
                await self._discover_cross_links(entry.entry_id)
            
            logging.info(f"Media ingested successfully: {entry.entry_id}")
            return entry
            
        except Exception as e:
            logging.error(f"Failed to ingest media: {e}")
            raise
    
    async def _process_audio(self, audio_data: Union[str, bytes], entry_id: str) -> VaultMediaMetadata:
        """Process audio file and extract metadata"""
        try:
            # Save audio file
            audio_path = self.vault_directory / "media" / f"{entry_id}.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(audio_data, str):
                # Copy from existing file
                import shutil
                shutil.copy2(audio_data, audio_path)
            else:
                # Save binary data
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
            
            # Get file metadata
            file_size = audio_path.stat().st_size
            
            # Get duration using ffmpeg
            try:
                probe = ffmpeg.probe(str(audio_path))
                duration = float(probe['streams'][0]['duration'])
            except:
                duration = None
            
            # Transcribe audio using Whisper
            transcription = ""
            if self.whisper_model:
                try:
                    result = self.whisper_model.transcribe(str(audio_path))
                    transcription = result["text"]
                except Exception as e:
                    logging.warning(f"Transcription failed: {e}")
            
            # Analyze audio quality (simple volume-based metric)
            audio_quality = 0.8  # Placeholder - could implement actual quality analysis
            
            return VaultMediaMetadata(
                file_path=str(audio_path),
                file_type="audio/wav",
                file_size=file_size,
                duration=duration,
                transcription=transcription,
                audio_quality=audio_quality
            )
            
        except Exception as e:
            logging.error(f"Audio processing failed: {e}")
            raise
    
    async def _process_video(self, video_data: Union[str, bytes], entry_id: str) -> VaultMediaMetadata:
        """Process video file and extract metadata"""
        try:
            # Save video file
            video_path = self.vault_directory / "media" / f"{entry_id}.mp4"
            video_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(video_data, str):
                import shutil
                shutil.copy2(video_data, video_path)
            else:
                with open(video_path, 'wb') as f:
                    f.write(video_data)
            
            # Get file metadata
            file_size = video_path.stat().st_size
            
            # Get video metadata using ffmpeg
            try:
                probe = ffmpeg.probe(str(video_path))
                video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
                duration = float(probe['format']['duration'])
                dimensions = (int(video_stream['width']), int(video_stream['height']))
            except:
                duration = None
                dimensions = None
            
            # Extract audio and transcribe
            transcription = ""
            try:
                # Extract audio track
                audio_path = video_path.with_suffix('.wav')
                ffmpeg.input(str(video_path)).output(str(audio_path)).run(overwrite_output=True, quiet=True)
                
                # Transcribe extracted audio
                if self.whisper_model:
                    result = self.whisper_model.transcribe(str(audio_path))
                    transcription = result["text"]
                    
                # Clean up temporary audio file
                audio_path.unlink()
                
            except Exception as e:
                logging.warning(f"Video transcription failed: {e}")
            
            # Analyze first frame for visual content
            visual_description = ""
            detected_faces = []
            detected_emotions = []
            
            try:
                cap = cv2.VideoCapture(str(video_path))
                ret, frame = cap.read()
                if ret:
                    # Detect faces
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    for (x, y, w, h) in faces:
                        detected_faces.append({
                            "x": int(x), "y": int(y), 
                            "width": int(w), "height": int(h)
                        })
                    
                    # Simple visual description
                    visual_description = f"Video frame with {len(detected_faces)} detected face(s)"
                    
                cap.release()
                
            except Exception as e:
                logging.warning(f"Video analysis failed: {e}")
            
            return VaultMediaMetadata(
                file_path=str(video_path),
                file_type="video/mp4",
                file_size=file_size,
                duration=duration,
                dimensions=dimensions,
                transcription=transcription,
                visual_description=visual_description,
                detected_faces=detected_faces,
                detected_emotions=detected_emotions,
                video_quality=0.8  # Placeholder
            )
            
        except Exception as e:
            logging.error(f"Video processing failed: {e}")
            raise
    
    async def _process_image(self, image_data: Union[str, bytes], entry_id: str) -> VaultMediaMetadata:
        """Process image file and extract metadata"""
        try:
            # Save image file
            image_path = self.vault_directory / "media" / f"{entry_id}.jpg"
            image_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(image_data, str):
                import shutil
                shutil.copy2(image_data, image_path)
            else:
                with open(image_path, 'wb') as f:
                    f.write(image_data)
            
            # Get file metadata
            file_size = image_path.stat().st_size
            
            # Open image and get dimensions
            with Image.open(image_path) as img:
                dimensions = img.size
                
            # Detect faces and analyze image
            detected_faces = []
            detected_objects = []
            visual_description = ""
            
            try:
                # Load image with OpenCV
                img_cv = cv2.imread(str(image_path))
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, w, h) in faces:
                    detected_faces.append({
                        "x": int(x), "y": int(y),
                        "width": int(w), "height": int(h)
                    })
                
                # Simple visual description
                visual_description = f"Image ({dimensions[0]}x{dimensions[1]}) with {len(detected_faces)} detected face(s)"
                
                # Could add more sophisticated object detection here
                detected_objects = ["face"] if detected_faces else []
                
            except Exception as e:
                logging.warning(f"Image analysis failed: {e}")
            
            return VaultMediaMetadata(
                file_path=str(image_path),
                file_type="image/jpeg",
                file_size=file_size,
                dimensions=dimensions,
                visual_description=visual_description,
                detected_faces=detected_faces,
                detected_objects=detected_objects
            )
            
        except Exception as e:
            logging.error(f"Image processing failed: {e}")
            raise
    
    async def _analyze_semantics(self, content: str) -> VaultSemanticAnalysis:
        """Perform comprehensive semantic analysis of content"""
        try:
            analysis = VaultSemanticAnalysis()
            
            if not content or not content.strip():
                return analysis
            
            # Sentiment analysis
            if self.sentiment_analyzer:
                try:
                    sentiment_result = self.sentiment_analyzer(content)[0]
                    analysis.sentiment_score = sentiment_result['score'] if sentiment_result['label'] == 'POSITIVE' else -sentiment_result['score']
                except Exception as e:
                    logging.warning(f"Sentiment analysis failed: {e}")
            
            # Topic classification
            if self.topic_classifier:
                try:
                    topic_result = self.topic_classifier(content, self.executive_topics)
                    analysis.main_themes = [
                        label for label, score in zip(topic_result['labels'], topic_result['scores'])
                        if score > 0.3
                    ][:5]  # Top 5 themes
                    analysis.confidence_score = max(topic_result['scores'][:3])  # Confidence in top 3
                except Exception as e:
                    logging.warning(f"Topic classification failed: {e}")
            
            # Emotion analysis
            if self.emotion_analyzer:
                try:
                    emotion_result = self.emotion_analyzer(content)[0]
                    analysis.tone_emotion = {emotion_result['label']: emotion_result['score']}
                except Exception as e:
                    logging.warning(f"Emotion analysis failed: {e}")
            
            # Extract key concepts (simple keyword extraction)
            words = content.lower().split()
            # Filter for meaningful words (could be improved with NER)
            key_concepts = [word for word in words if len(word) > 4 and word.isalpha()]
            analysis.key_concepts = list(set(key_concepts))[:10]  # Top 10 unique concepts
            
            # Determine intended purpose based on content patterns
            content_lower = content.lower()
            if any(word in content_lower for word in ['idea', 'concept', 'think', 'maybe']):
                analysis.intended_purpose = "brainstorm"
            elif any(word in content_lower for word in ['remember', 'note', 'remind']):
                analysis.intended_purpose = "reminder"
            elif any(word in content_lower for word in ['question', 'how', 'why', 'what']):
                analysis.intended_purpose = "question"
            elif any(word in content_lower for word in ['strategy', 'plan', 'goal']):
                analysis.intended_purpose = "strategic_planning"
            else:
                analysis.intended_purpose = "general_note"
            
            # Calculate urgency and complexity (heuristic-based)
            urgency_indicators = ['urgent', 'asap', 'immediately', 'critical', 'emergency']
            analysis.urgency_level = min(5, 1 + sum(1 for word in urgency_indicators if word in content_lower))
            
            complexity_indicators = ['complex', 'difficult', 'challenging', 'multiple', 'various']
            analysis.complexity_level = min(5, 1 + sum(1 for word in complexity_indicators if word in content_lower))
            
            # Strategic value assessment (based on business keywords)
            strategic_keywords = ['revenue', 'growth', 'market', 'competitive', 'innovation', 'customer']
            analysis.strategic_value = min(1.0, len([word for word in strategic_keywords if word in content_lower]) / 10)
            
            # Related domains
            domain_mapping = {
                'finance': ['revenue', 'cost', 'profit', 'budget', 'investment'],
                'marketing': ['customer', 'brand', 'campaign', 'market', 'promotion'],
                'technology': ['system', 'software', 'data', 'platform', 'digital'],
                'operations': ['process', 'efficiency', 'workflow', 'production', 'supply'],
                'strategy': ['vision', 'goal', 'objective', 'plan', 'direction']
            }
            
            for domain, keywords in domain_mapping.items():
                if any(keyword in content_lower for keyword in keywords):
                    analysis.related_domains.append(domain)
            
            return analysis
            
        except Exception as e:
            logging.error(f"Semantic analysis failed: {e}")
            return VaultSemanticAnalysis()
    
    async def _schedule_reflection(self, entry_id: str, user_id: str):
        """Schedule automatic reflection for a vault entry"""
        try:
            # Create reflection schedule
            schedule = VaultReflectionSchedule(
                user_id=user_id,
                entry_id=entry_id,
                next_reflection=datetime.now() + timedelta(hours=24)  # First reflection after 24 hours
            )
            
            self.reflection_schedules[f"{entry_id}_{user_id}"] = schedule
            
            # Start reflection engine if not already running
            if not self.reflection_engine_active:
                asyncio.create_task(self._run_reflection_engine())
            
            logging.info(f"Reflection scheduled for entry: {entry_id}")
            
        except Exception as e:
            logging.error(f"Failed to schedule reflection: {e}")
    
    async def _run_reflection_engine(self):
        """Background engine that runs reflection cycles"""
        self.reflection_engine_active = True
        
        try:
            while self.reflection_engine_active:
                current_time = datetime.now()
                
                # Check all scheduled reflections
                for schedule_key, schedule in list(self.reflection_schedules.items()):
                    if (schedule.active and 
                        schedule.next_reflection <= current_time and
                        (not schedule.paused_until or schedule.paused_until <= current_time)):
                        
                        # Run reflection
                        await self._perform_reflection(schedule.entry_id, schedule.user_id)
                        
                        # Update schedule
                        schedule.current_reflection_count += 1
                        schedule.last_reflection = current_time
                        schedule.next_reflection = current_time + schedule.reflection_interval
                        
                        # Check if max reflections reached
                        if (schedule.max_reflections and 
                            schedule.current_reflection_count >= schedule.max_reflections):
                            schedule.active = False
                
                # Sleep for 1 hour before next check
                await asyncio.sleep(3600)
                
        except Exception as e:
            logging.error(f"Reflection engine error: {e}")
        finally:
            self.reflection_engine_active = False
    
    async def _perform_reflection(self, entry_id: str, user_id: str):
        """Perform a reflection cycle on a vault entry"""
        try:
            entry = self.vault_entries.get(entry_id)
            if not entry or entry.privacy_level == VaultPrivacyLevel.LOCKED:
                return
            
            # Create new reflection
            reflection = VaultReflection(
                trigger=VaultReflectionTrigger.TIME_BASED
            )
            
            # Generate reflection based on current ripeness level
            ripeness_level = entry.ripeness_level
            prompts = REFLECTION_PROMPTS.get(ripeness_level, REFLECTION_PROMPTS[VaultRipenessLevel.SEED])
            
            # Simulate AI reflection (in real implementation, would use LLM)
            reflection.reflection_text = f"Reflecting on: {entry.title}. "
            reflection.reflection_text += f"Current themes: {', '.join(entry.semantic_analysis.main_themes if entry.semantic_analysis else [])}"
            
            # Generate insights and questions
            reflection.new_insights = [
                f"This idea connects to {entry.semantic_analysis.intended_purpose if entry.semantic_analysis else 'general business'} domain",
                f"Strategic value appears to be {entry.semantic_analysis.strategic_value if entry.semantic_analysis else 'moderate'}"
            ]
            
            reflection.questions_generated = prompts[:2]  # Use first 2 prompts as questions
            
            # Update ripeness score
            ripeness_delta = 0.1  # Gradual increase with each reflection
            entry.ripeness_score = min(1.0, entry.ripeness_score + ripeness_delta)
            reflection.ripeness_delta = ripeness_delta
            
            # Update ripeness level based on score
            if entry.ripeness_score >= 0.8:
                entry.ripeness_level = VaultRipenessLevel.RIPE
            elif entry.ripeness_score >= 0.6:
                entry.ripeness_level = VaultRipenessLevel.MATURING
            elif entry.ripeness_score >= 0.4:
                entry.ripeness_level = VaultRipenessLevel.GROWING
            elif entry.ripeness_score >= 0.2:
                entry.ripeness_level = VaultRipenessLevel.SPROUTING
            
            # Add reflection to entry
            entry.reflections.append(reflection)
            entry.last_reflection = datetime.now()
            entry.updated_at = datetime.now()
            
            # Check if ready for harvest
            if entry.ripeness_level == VaultRipenessLevel.RIPE and not entry.harvest_ready:
                entry.harvest_ready = True
                entry.harvest_suggestions = [
                    "Generate strategic presentation slides",
                    "Create action item list",
                    "Develop concept prototype"
                ]
            
            logging.info(f"Reflection completed for entry: {entry_id}")
            
        except Exception as e:
            logging.error(f"Reflection failed for entry {entry_id}: {e}")
    
    async def _discover_cross_links(self, entry_id: str):
        """Discover cross-links between vault entries"""
        try:
            if not self.vault_collection:
                return
            
            entry = self.vault_entries.get(entry_id)
            if not entry or not entry.raw_content:
                return
            
            # Query similar entries
            embedding = self.sentence_model.encode([entry.raw_content])[0]
            results = self.vault_collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=5,
                where={"user_id": entry.user_id}  # Only link within same user
            )
            
            # Create cross-links for similar entries
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                if doc_id != entry_id and distance < 0.7:  # Similarity threshold
                    
                    # Determine connection type based on similarity
                    if distance < 0.3:
                        connection_type = "highly_similar"
                    elif distance < 0.5:
                        connection_type = "related_theme"
                    else:
                        connection_type = "loosely_connected"
                    
                    # Create cross-link
                    cross_link = VaultCrossLink(
                        source_entry_id=entry_id,
                        target_entry_id=doc_id,
                        connection_type=connection_type,
                        strength=1.0 - distance,
                        description=f"Semantic similarity: {1.0 - distance:.2f}"
                    )
                    
                    # Add to both entries
                    if doc_id not in entry.cross_links:
                        entry.cross_links.append(doc_id)
                    
                    target_entry = self.vault_entries.get(doc_id)
                    if target_entry and entry_id not in target_entry.cross_links:
                        target_entry.cross_links.append(entry_id)
            
            logging.info(f"Cross-links discovered for entry: {entry_id}")
            
        except Exception as e:
            logging.error(f"Cross-link discovery failed: {e}")
    
    async def generate_output(
        self,
        user_id: str,
        entry_ids: List[str],
        output_type: VaultOutputType,
        title: str = "",
        custom_prompt: str = ""
    ) -> VaultOutput:
        """Generate output from vault entries"""
        try:
            # Validate entries
            entries = [self.vault_entries.get(eid) for eid in entry_ids]
            entries = [e for e in entries if e and e.user_id == user_id]
            
            if not entries:
                raise ValueError("No valid entries found")
            
            # Combine content from all entries
            combined_content = "\\n\\n".join([
                f"Entry: {e.title}\\n{e.raw_content}" for e in entries
            ])
            
            # Get output template
            template = OUTPUT_TEMPLATES.get(output_type, {})
            
            # Generate output based on type
            output = VaultOutput(
                source_entry_ids=entry_ids,
                output_type=output_type,
                title=title or f"{output_type.value.replace('_', ' ').title()}",
                user_id=user_id
            )
            
            # Generate content based on output type
            if output_type == VaultOutputType.DRAFT_SLIDES:
                output.content = self._generate_slide_content(combined_content, template)
            elif output_type == VaultOutputType.STRATEGIC_PROMPTS:
                output.content = self._generate_strategic_prompts(combined_content, template)
            elif output_type == VaultOutputType.ACTION_ITEMS:
                output.content = self._generate_action_items(combined_content, template)
            elif output_type == VaultOutputType.JOURNAL_FRAGMENTS:
                output.content = self._generate_journal_fragments(combined_content)
            else:
                output.content = f"Generated {output_type.value} from {len(entries)} vault entries:\\n\\n{combined_content}"
            
            # Calculate quality score (heuristic)
            output.quality_score = min(1.0, len(output.content) / 1000 * 0.8 + len(entries) / 10 * 0.2)
            
            # Mark entries as having generated output
            for entry in entries:
                entry.generated_outputs.append({
                    "output_id": output.output_id,
                    "output_type": output_type.value,
                    "generated_at": output.generated_at.isoformat()
                })
            
            logging.info(f"Output generated: {output.output_id}")
            return output
            
        except Exception as e:
            logging.error(f"Output generation failed: {e}")
            raise
    
    def _generate_slide_content(self, content: str, template: Dict) -> str:
        """Generate slide presentation content"""
        structure = template.get("structure", ["Title", "Content", "Conclusion"])
        
        slides = []
        slides.append("# Executive Presentation\\n")
        
        for section in structure:
            slides.append(f"## {section}\\n")
            if section == "Title":
                slides.append("- Key insights from vault analysis")
            elif section == "Problem":
                slides.append("- Challenges identified in vault entries")
            elif section == "Solution":
                slides.append("- Proposed solutions and strategies")
            else:
                slides.append(f"- Content for {section.lower()}")
            slides.append("")
        
        return "\\n".join(slides)
    
    def _generate_strategic_prompts(self, content: str, template: Dict) -> str:
        """Generate strategic prompts and questions"""
        prompts = [
            "## Strategic Analysis\\n",
            "### Key Questions:",
            "- What are the strategic implications of these insights?",
            "- How do these ideas align with current business objectives?",
            "- What resources would be required for implementation?",
            "- What are the potential risks and mitigation strategies?",
            "",
            "### Recommendations:",
            "- Prioritize ideas based on strategic value and feasibility",
            "- Develop pilot programs for high-potential concepts",
            "- Establish metrics for measuring success",
            "",
            "### Next Steps:",
            "- Schedule stakeholder review meeting",
            "- Conduct market research on key concepts",
            "- Develop detailed implementation timeline"
        ]
        
        return "\\n".join(prompts)
    
    def _generate_action_items(self, content: str, template: Dict) -> str:
        """Generate actionable items from vault content"""
        actions = [
            "## Action Items\\n",
            "### Immediate Actions (Next 7 days):",
            "- [ ] Review and validate key assumptions",
            "- [ ] Identify required resources and stakeholders",
            "- [ ] Schedule initial planning meeting",
            "",
            "### Short-term Actions (Next 30 days):",
            "- [ ] Develop detailed project plan",
            "- [ ] Conduct feasibility analysis",
            "- [ ] Create initial prototypes or mockups",
            "",
            "### Long-term Actions (Next 90 days):",
            "- [ ] Execute pilot program",
            "- [ ] Measure and analyze results",
            "- [ ] Scale successful initiatives"
        ]
        
        return "\\n".join(actions)
    
    def _generate_journal_fragments(self, content: str) -> str:
        """Generate journal-style thought fragments"""
        fragments = [
            "## Reflective Journal\\n",
            f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\\n",
            "### Key Insights:",
            "The vault entries reveal several interesting patterns and connections...",
            "",
            "### Emerging Themes:",
            "- Strategic thinking around innovation and growth",
            "- Focus on operational efficiency and optimization",
            "- Consideration of market dynamics and competitive positioning",
            "",
            "### Questions for Further Reflection:",
            "- How do these ideas fit into the broader strategic vision?",
            "- What would success look like for these initiatives?",
            "- Who are the key stakeholders that need to be involved?",
            "",
            "### Personal Notes:",
            "These ideas feel promising and worth exploring further. The cross-connections suggest there might be a larger strategic framework emerging."
        ]
        
        return "\\n".join(fragments)
    
    def get_vault_timeline(self, user_id: str, entry_id: Optional[str] = None) -> Dict[str, Any]:
        """Get timeline view of vault entries and reflections"""
        try:
            if entry_id:
                # Timeline for specific entry
                entry = self.vault_entries.get(entry_id)
                if not entry or entry.user_id != user_id:
                    return {"error": "Entry not found"}
                
                timeline = {
                    "entry": {
                        "id": entry.entry_id,
                        "title": entry.title,
                        "created_at": entry.created_at.isoformat(),
                        "ripeness_level": entry.ripeness_level.value,
                        "ripeness_score": entry.ripeness_score
                    },
                    "reflections": [
                        {
                            "id": r.reflection_id,
                            "timestamp": r.timestamp.isoformat(),
                            "trigger": r.trigger.value,
                            "insights": r.new_insights,
                            "questions": r.questions_generated,
                            "ripeness_delta": r.ripeness_delta
                        }
                        for r in entry.reflections
                    ],
                    "cross_links": [
                        {
                            "target_id": link_id,
                            "target_title": self.vault_entries.get(link_id, {}).title if self.vault_entries.get(link_id) else "Unknown"
                        }
                        for link_id in entry.cross_links
                    ],
                    "outputs": entry.generated_outputs
                }
                
            else:
                # Timeline for all user entries
                user_entries = [e for e in self.vault_entries.values() if e.user_id == user_id]
                user_entries.sort(key=lambda x: x.created_at, reverse=True)
                
                timeline = {
                    "entries": [
                        {
                            "id": e.entry_id,
                            "title": e.title,
                            "created_at": e.created_at.isoformat(),
                            "updated_at": e.updated_at.isoformat(),
                            "ripeness_level": e.ripeness_level.value,
                            "ripeness_score": e.ripeness_score,
                            "reflection_count": len(e.reflections),
                            "cross_link_count": len(e.cross_links),
                            "output_count": len(e.generated_outputs),
                            "harvest_ready": e.harvest_ready
                        }
                        for e in user_entries
                    ]
                }
            
            return timeline
            
        except Exception as e:
            logging.error(f"Failed to get vault timeline: {e}")
            return {"error": str(e)}
    
    def get_vault_analytics(self, user_id: str) -> VaultAnalytics:
        """Get analytics for user's vault usage"""
        try:
            user_entries = [e for e in self.vault_entries.values() if e.user_id == user_id]
            
            analytics = VaultAnalytics(
                user_id=user_id,
                period_start=min(e.created_at for e in user_entries) if user_entries else datetime.now(),
                period_end=datetime.now()
            )
            
            # Entry statistics
            analytics.total_entries = len(user_entries)
            analytics.entries_by_type = {}
            analytics.entries_by_privacy_level = {}
            
            for entry in user_entries:
                entry_type = entry.entry_type.value
                privacy_level = entry.privacy_level.value
                
                analytics.entries_by_type[entry_type] = analytics.entries_by_type.get(entry_type, 0) + 1
                analytics.entries_by_privacy_level[privacy_level] = analytics.entries_by_privacy_level.get(privacy_level, 0) + 1
            
            # Reflection statistics
            all_reflections = [r for e in user_entries for r in e.reflections]
            analytics.total_reflections = len(all_reflections)
            analytics.avg_reflections_per_entry = analytics.total_reflections / max(1, analytics.total_entries)
            
            # Ripeness progression
            analytics.ripeness_progression = {}
            for entry in user_entries:
                level = entry.ripeness_level.value
                analytics.ripeness_progression[level] = analytics.ripeness_progression.get(level, 0) + 1
            
            # Output statistics
            all_outputs = [o for e in user_entries for o in e.generated_outputs]
            analytics.total_outputs = len(all_outputs)
            
            # Cross-linking statistics
            all_cross_links = [link for e in user_entries for link in e.cross_links]
            analytics.total_cross_links = len(all_cross_links)
            analytics.avg_links_per_entry = analytics.total_cross_links / max(1, analytics.total_entries)
            
            return analytics
            
        except Exception as e:
            logging.error(f"Failed to get vault analytics: {e}")
            return VaultAnalytics(user_id=user_id)
    
    def start_vault_session(self, user_id: str) -> VaultSession:
        """Start a new vault session for a user"""
        session = VaultSession(user_id=user_id)
        self.active_sessions[session.session_id] = session
        return session
    
    def get_vault_session(self, session_id: str) -> Optional[VaultSession]:
        """Get an active vault session"""
        return self.active_sessions.get(session_id)
    
    def end_vault_session(self, session_id: str):
        """End a vault session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

