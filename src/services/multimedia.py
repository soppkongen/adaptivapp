"""
Multimedia Analysis Service

This service handles video and audio processing for psychological analysis,
including file upload, preprocessing, and integration with wordsmimir analysis.
"""

import os
import uuid
import tempfile
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaType(Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"

class AudioFormat(Enum):
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    FLAC = "flac"
    OGG = "ogg"

class VideoFormat(Enum):
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"

@dataclass
class MediaMetadata:
    """Metadata extracted from media files."""
    duration_seconds: float
    file_size_bytes: int
    format: str
    codec: str
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    resolution: Optional[Tuple[int, int]] = None
    frame_rate: Optional[float] = None
    bitrate: Optional[int] = None

@dataclass
class AudioFeatures:
    """Audio features extracted for psychological analysis."""
    speech_segments: List[Dict[str, Any]]
    silence_segments: List[Dict[str, Any]]
    average_pitch: float
    pitch_variance: float
    speech_rate: float
    volume_statistics: Dict[str, float]
    spectral_features: Dict[str, Any]
    voice_activity_detection: List[Dict[str, Any]]

@dataclass
class VideoFeatures:
    """Video features extracted for psychological analysis."""
    face_detections: List[Dict[str, Any]]
    facial_landmarks: List[Dict[str, Any]]
    emotion_timeline: List[Dict[str, Any]]
    gaze_tracking: List[Dict[str, Any]]
    gesture_analysis: List[Dict[str, Any]]
    scene_changes: List[float]
    visual_attention_map: Dict[str, Any]

class MultimediaAnalysisService:
    """
    Service for processing audio and video files for psychological analysis.
    
    This service handles:
    - File upload and validation
    - Audio/video preprocessing
    - Feature extraction
    - Integration with wordsmimir analysis
    - Temporary file management
    """
    
    def __init__(self, upload_dir: str = "/tmp/elite_command_uploads", 
                 max_file_size: int = 500 * 1024 * 1024):  # 500MB
        self.upload_dir = upload_dir
        self.max_file_size = max_file_size
        self.supported_audio_formats = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
    def validate_media_file(self, file_path: str, media_type: MediaType) -> bool:
        """
        Validate media file format and size.
        
        Args:
            file_path: Path to the media file
            media_type: Type of media (audio/video)
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes (max: {self.max_file_size})")
                return False
            
            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if media_type == MediaType.AUDIO and ext not in self.supported_audio_formats:
                logger.error(f"Unsupported audio format: {ext}")
                return False
            elif media_type == MediaType.VIDEO and ext not in self.supported_video_formats:
                logger.error(f"Unsupported video format: {ext}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False
    
    def extract_media_metadata(self, file_path: str) -> Optional[MediaMetadata]:
        """
        Extract metadata from media file using ffprobe.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            MediaMetadata object or None if extraction fails
        """
        try:
            # Use ffprobe to extract metadata
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"ffprobe failed: {result.stderr}")
                return None
            
            metadata = json.loads(result.stdout)
            format_info = metadata.get('format', {})
            streams = metadata.get('streams', [])
            
            # Extract basic information
            duration = float(format_info.get('duration', 0))
            file_size = int(format_info.get('size', 0))
            format_name = format_info.get('format_name', 'unknown')
            
            # Find audio and video streams
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
            video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
            
            # Extract stream-specific metadata
            sample_rate = None
            channels = None
            resolution = None
            frame_rate = None
            codec = 'unknown'
            
            if audio_stream:
                sample_rate = int(audio_stream.get('sample_rate', 0)) or None
                channels = int(audio_stream.get('channels', 0)) or None
                codec = audio_stream.get('codec_name', 'unknown')
            
            if video_stream:
                width = int(video_stream.get('width', 0))
                height = int(video_stream.get('height', 0))
                if width and height:
                    resolution = (width, height)
                
                frame_rate_str = video_stream.get('r_frame_rate', '0/1')
                if '/' in frame_rate_str:
                    num, den = frame_rate_str.split('/')
                    if int(den) > 0:
                        frame_rate = float(num) / float(den)
                
                codec = video_stream.get('codec_name', 'unknown')
            
            return MediaMetadata(
                duration_seconds=duration,
                file_size_bytes=file_size,
                format=format_name,
                codec=codec,
                sample_rate=sample_rate,
                channels=channels,
                resolution=resolution,
                frame_rate=frame_rate,
                bitrate=int(format_info.get('bit_rate', 0)) or None
            )
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {str(e)}")
            return None
    
    def extract_audio_features(self, file_path: str) -> Optional[AudioFeatures]:
        """
        Extract audio features for psychological analysis.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioFeatures object or None if extraction fails
        """
        try:
            # Convert to WAV format for processing if needed
            wav_path = self._convert_to_wav(file_path)
            if not wav_path:
                return None
            
            # Extract basic audio features
            features = self._analyze_audio_content(wav_path)
            
            # Clean up temporary file if created
            if wav_path != file_path:
                os.unlink(wav_path)
            
            return features
            
        except Exception as e:
            logger.error(f"Audio feature extraction error: {str(e)}")
            return None
    
    def extract_video_features(self, file_path: str) -> Optional[VideoFeatures]:
        """
        Extract video features for psychological analysis.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            VideoFeatures object or None if extraction fails
        """
        try:
            # Extract frames for analysis
            frame_dir = self._extract_video_frames(file_path)
            if not frame_dir:
                return None
            
            # Analyze video content
            features = self._analyze_video_content(frame_dir, file_path)
            
            # Clean up temporary frames
            self._cleanup_directory(frame_dir)
            
            return features
            
        except Exception as e:
            logger.error(f"Video feature extraction error: {str(e)}")
            return None
    
    def process_uploaded_file(self, file_path: str, media_type: MediaType, 
                            individual_id: str, communication_id: str) -> Dict[str, Any]:
        """
        Process uploaded media file for psychological analysis.
        
        Args:
            file_path: Path to the uploaded file
            media_type: Type of media (audio/video)
            individual_id: Individual identifier
            communication_id: Communication identifier
            
        Returns:
            Dictionary containing processing results
        """
        try:
            # Validate file
            if not self.validate_media_file(file_path, media_type):
                return {
                    "success": False,
                    "error": "File validation failed",
                    "error_type": "validation_error"
                }
            
            # Extract metadata
            metadata = self.extract_media_metadata(file_path)
            if not metadata:
                return {
                    "success": False,
                    "error": "Metadata extraction failed",
                    "error_type": "metadata_error"
                }
            
            # Extract features based on media type
            features = None
            if media_type == MediaType.AUDIO:
                features = self.extract_audio_features(file_path)
            elif media_type == MediaType.VIDEO:
                features = self.extract_video_features(file_path)
            
            if not features:
                return {
                    "success": False,
                    "error": "Feature extraction failed",
                    "error_type": "feature_extraction_error"
                }
            
            # Generate public URL for wordsmimir analysis
            public_url = self._generate_public_url(file_path)
            
            return {
                "success": True,
                "metadata": metadata.__dict__,
                "features": features.__dict__ if hasattr(features, '__dict__') else features,
                "public_url": public_url,
                "media_type": media_type.value,
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "processing_error"
            }
    
    def _convert_to_wav(self, file_path: str) -> Optional[str]:
        """Convert audio file to WAV format for processing."""
        try:
            _, ext = os.path.splitext(file_path.lower())
            if ext == '.wav':
                return file_path
            
            # Create temporary WAV file
            temp_wav = os.path.join(self.upload_dir, f"{uuid.uuid4()}.wav")
            
            # Convert using ffmpeg
            cmd = [
                'ffmpeg', '-i', file_path, '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1', '-y', temp_wav
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"Audio conversion failed: {result.stderr}")
                return None
            
            return temp_wav
            
        except Exception as e:
            logger.error(f"Audio conversion error: {str(e)}")
            return None
    
    def _analyze_audio_content(self, wav_path: str) -> AudioFeatures:
        """Analyze audio content to extract psychological features."""
        # This is a simplified implementation
        # In a real system, you would use libraries like librosa, pyAudio, etc.
        
        # Placeholder implementation
        return AudioFeatures(
            speech_segments=[],
            silence_segments=[],
            average_pitch=150.0,
            pitch_variance=25.0,
            speech_rate=2.5,
            volume_statistics={"mean": 0.5, "std": 0.2, "max": 0.8, "min": 0.1},
            spectral_features={"mfcc": [], "spectral_centroid": 1500.0},
            voice_activity_detection=[]
        )
    
    def _extract_video_frames(self, file_path: str, fps: float = 1.0) -> Optional[str]:
        """Extract frames from video for analysis."""
        try:
            # Create temporary directory for frames
            frame_dir = os.path.join(self.upload_dir, f"frames_{uuid.uuid4()}")
            os.makedirs(frame_dir, exist_ok=True)
            
            # Extract frames using ffmpeg
            cmd = [
                'ffmpeg', '-i', file_path, '-vf', f'fps={fps}',
                '-y', os.path.join(frame_dir, 'frame_%04d.jpg')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"Frame extraction failed: {result.stderr}")
                self._cleanup_directory(frame_dir)
                return None
            
            return frame_dir
            
        except Exception as e:
            logger.error(f"Frame extraction error: {str(e)}")
            return None
    
    def _analyze_video_content(self, frame_dir: str, video_path: str) -> VideoFeatures:
        """Analyze video content to extract psychological features."""
        # This is a simplified implementation
        # In a real system, you would use computer vision libraries like OpenCV, dlib, etc.
        
        # Placeholder implementation
        return VideoFeatures(
            face_detections=[],
            facial_landmarks=[],
            emotion_timeline=[],
            gaze_tracking=[],
            gesture_analysis=[],
            scene_changes=[],
            visual_attention_map={}
        )
    
    def _generate_public_url(self, file_path: str) -> str:
        """Generate public URL for file access by wordsmimir."""
        # In a real implementation, you would upload to a CDN or cloud storage
        # For now, return a placeholder URL
        filename = os.path.basename(file_path)
        return f"https://api.elitecommand.io/media/{filename}"
    
    def _cleanup_directory(self, directory: str):
        """Clean up temporary directory and its contents."""
        try:
            import shutil
            if os.path.exists(directory):
                shutil.rmtree(directory)
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old uploaded files."""
        try:
            current_time = datetime.utcnow().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.unlink(file_path)
                        logger.info(f"Cleaned up old file: {filename}")
                        
        except Exception as e:
            logger.error(f"File cleanup error: {str(e)}")

# Factory function for creating multimedia analysis service
def create_multimedia_service(upload_dir: Optional[str] = None, 
                            max_file_size: Optional[int] = None) -> MultimediaAnalysisService:
    """
    Factory function to create a configured MultimediaAnalysisService instance.
    
    Args:
        upload_dir: Directory for temporary file uploads
        max_file_size: Maximum file size in bytes
        
    Returns:
        Configured MultimediaAnalysisService instance
    """
    kwargs = {}
    if upload_dir:
        kwargs['upload_dir'] = upload_dir
    if max_file_size:
        kwargs['max_file_size'] = max_file_size
    
    return MultimediaAnalysisService(**kwargs)

