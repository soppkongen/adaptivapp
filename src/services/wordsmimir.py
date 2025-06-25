"""
Wordsmimir API Integration Service

This service handles all interactions with the wordsmimir.t-pip.no psychological
word analyzer API, providing Human Signal Intelligence capabilities.
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisMode(Enum):
    TEXT_ONLY = "text_only"
    AUDIO_ONLY = "audio_only"
    VIDEO_ONLY = "video_only"
    MULTIMODAL = "multimodal"
    FULL_HSI = "full_hsi"

@dataclass
class WordsmimirConfig:
    """Configuration for wordsmimir API integration."""
    base_url: str = "https://wordsmimir.t-pip.no/api/v1"
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour

@dataclass
class AnalysisRequest:
    """Request structure for psychological analysis."""
    content: str
    content_type: str  # text, audio_url, video_url, multimodal
    individual_id: str
    communication_id: str
    analysis_mode: AnalysisMode = AnalysisMode.TEXT_ONLY
    metadata: Optional[Dict] = None
    context: Optional[Dict] = None

@dataclass
class PsychologicalInsight:
    """Structured psychological insight from wordsmimir analysis."""
    insight_type: str
    confidence: float
    description: str
    evidence: List[str]
    recommendations: List[str]
    risk_level: str
    
class WordsmimirService:
    """
    Service class for integrating with wordsmimir.t-pip.no psychological analysis API.
    
    This service provides comprehensive psychological analysis capabilities including:
    - Text-based linguistic analysis
    - Audio paralinguistic analysis
    - Video facial expression analysis
    - Multi-modal congruence assessment
    - Behavioral pattern recognition
    """
    
    def __init__(self, config: WordsmimirConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'EliteCommand-API/1.0'
        })
        self._cache = {} if config.enable_caching else None
        
    def analyze_text(self, text: str, individual_id: str, communication_id: str, 
                    context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform comprehensive text-based psychological analysis.
        
        Args:
            text: The text content to analyze
            individual_id: Unique identifier for the individual
            communication_id: Unique identifier for this communication
            context: Additional context information
            
        Returns:
            Dictionary containing psychological analysis results
        """
        request_data = {
            "content": text,
            "analysis_type": "text",
            "individual_id": individual_id,
            "communication_id": communication_id,
            "context": context or {},
            "features": [
                "linguistic_complexity",
                "emotional_valence",
                "cognitive_load",
                "deception_indicators",
                "stress_markers",
                "personality_indicators",
                "authenticity_assessment"
            ]
        }
        
        try:
            response = self._make_request("/analyze/text", request_data)
            return self._process_text_response(response)
        except Exception as e:
            logger.error(f"Text analysis failed for communication {communication_id}: {str(e)}")
            return self._create_error_response("text_analysis_failed", str(e))
    
    def analyze_audio(self, audio_url: str, individual_id: str, communication_id: str,
                     context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform comprehensive audio-based psychological analysis.
        
        Args:
            audio_url: URL to the audio file to analyze
            individual_id: Unique identifier for the individual
            communication_id: Unique identifier for this communication
            context: Additional context information
            
        Returns:
            Dictionary containing audio psychological analysis results
        """
        request_data = {
            "audio_url": audio_url,
            "analysis_type": "audio",
            "individual_id": individual_id,
            "communication_id": communication_id,
            "context": context or {},
            "features": [
                "speech_rate_analysis",
                "pitch_variation",
                "volume_patterns",
                "pause_analysis",
                "filler_words",
                "voice_stress",
                "emotional_prosody",
                "authenticity_markers"
            ]
        }
        
        try:
            response = self._make_request("/analyze/audio", request_data)
            return self._process_audio_response(response)
        except Exception as e:
            logger.error(f"Audio analysis failed for communication {communication_id}: {str(e)}")
            return self._create_error_response("audio_analysis_failed", str(e))
    
    def analyze_video(self, video_url: str, individual_id: str, communication_id: str,
                     context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform comprehensive video-based psychological analysis.
        
        Args:
            video_url: URL to the video file to analyze
            individual_id: Unique identifier for the individual
            communication_id: Unique identifier for this communication
            context: Additional context information
            
        Returns:
            Dictionary containing video psychological analysis results
        """
        request_data = {
            "video_url": video_url,
            "analysis_type": "video",
            "individual_id": individual_id,
            "communication_id": communication_id,
            "context": context or {},
            "features": [
                "facial_expressions",
                "micro_expressions",
                "gaze_patterns",
                "attention_tracking",
                "stress_indicators",
                "authenticity_markers",
                "emotional_states",
                "engagement_levels"
            ]
        }
        
        try:
            response = self._make_request("/analyze/video", request_data)
            return self._process_video_response(response)
        except Exception as e:
            logger.error(f"Video analysis failed for communication {communication_id}: {str(e)}")
            return self._create_error_response("video_analysis_failed", str(e))
    
    def analyze_multimodal(self, text: str, audio_url: Optional[str] = None, 
                          video_url: Optional[str] = None, individual_id: str = "",
                          communication_id: str = "", context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform comprehensive multi-modal psychological analysis.
        
        This method combines text, audio, and video analysis to provide
        cross-modal congruence assessment and comprehensive psychological insights.
        
        Args:
            text: Text content to analyze
            audio_url: Optional URL to audio file
            video_url: Optional URL to video file
            individual_id: Unique identifier for the individual
            communication_id: Unique identifier for this communication
            context: Additional context information
            
        Returns:
            Dictionary containing comprehensive multi-modal analysis results
        """
        request_data = {
            "text": text,
            "audio_url": audio_url,
            "video_url": video_url,
            "analysis_type": "multimodal",
            "individual_id": individual_id,
            "communication_id": communication_id,
            "context": context or {},
            "features": [
                "cross_modal_congruence",
                "authenticity_assessment",
                "comprehensive_emotional_state",
                "stress_analysis",
                "deception_detection",
                "engagement_assessment",
                "psychological_profile_update"
            ]
        }
        
        try:
            response = self._make_request("/analyze/multimodal", request_data)
            return self._process_multimodal_response(response)
        except Exception as e:
            logger.error(f"Multimodal analysis failed for communication {communication_id}: {str(e)}")
            return self._create_error_response("multimodal_analysis_failed", str(e))
    
    def get_psychological_profile(self, individual_id: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive psychological profile for an individual.
        
        Args:
            individual_id: Unique identifier for the individual
            
        Returns:
            Dictionary containing psychological profile data
        """
        try:
            response = self._make_request(f"/profile/{individual_id}", method="GET")
            return response
        except Exception as e:
            logger.error(f"Profile retrieval failed for individual {individual_id}: {str(e)}")
            return self._create_error_response("profile_retrieval_failed", str(e))
    
    def update_psychological_profile(self, individual_id: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update psychological profile based on new analysis results.
        
        Args:
            individual_id: Unique identifier for the individual
            analysis_results: New analysis results to incorporate
            
        Returns:
            Dictionary containing updated profile information
        """
        request_data = {
            "individual_id": individual_id,
            "analysis_results": analysis_results,
            "update_timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = self._make_request(f"/profile/{individual_id}/update", request_data, method="PUT")
            return response
        except Exception as e:
            logger.error(f"Profile update failed for individual {individual_id}: {str(e)}")
            return self._create_error_response("profile_update_failed", str(e))
    
    def detect_behavioral_patterns(self, individual_id: str, time_range: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detect behavioral patterns for an individual over a specified time range.
        
        Args:
            individual_id: Unique identifier for the individual
            time_range: Optional time range for pattern analysis
            
        Returns:
            Dictionary containing detected behavioral patterns
        """
        request_data = {
            "individual_id": individual_id,
            "time_range": time_range or {"days": 30},
            "pattern_types": [
                "stress_response",
                "deception_indicators",
                "emotional_patterns",
                "communication_style",
                "authenticity_patterns"
            ]
        }
        
        try:
            response = self._make_request("/patterns/detect", request_data)
            return response
        except Exception as e:
            logger.error(f"Pattern detection failed for individual {individual_id}: {str(e)}")
            return self._create_error_response("pattern_detection_failed", str(e))
    
    def analyze_group_dynamics(self, participant_ids: List[str], session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze group psychological dynamics and interactions.
        
        Args:
            participant_ids: List of participant identifiers
            session_data: Data about the group session/meeting
            
        Returns:
            Dictionary containing group dynamics analysis
        """
        request_data = {
            "participant_ids": participant_ids,
            "session_data": session_data,
            "analysis_features": [
                "power_dynamics",
                "influence_patterns",
                "emotional_contagion",
                "group_cohesion",
                "conflict_indicators",
                "collaboration_effectiveness"
            ]
        }
        
        try:
            response = self._make_request("/analyze/group", request_data)
            return response
        except Exception as e:
            logger.error(f"Group dynamics analysis failed: {str(e)}")
            return self._create_error_response("group_analysis_failed", str(e))
    
    def generate_psychological_alerts(self, analysis_results: Dict[str, Any], 
                                    individual_id: str) -> List[Dict[str, Any]]:
        """
        Generate psychological alerts based on analysis results.
        
        Args:
            analysis_results: Results from psychological analysis
            individual_id: Individual identifier for context
            
        Returns:
            List of psychological alerts
        """
        alerts = []
        
        # Stress level alerts
        if 'stress_score' in analysis_results and analysis_results['stress_score'] > 0.7:
            alerts.append({
                "type": "high_stress",
                "severity": "high" if analysis_results['stress_score'] > 0.8 else "medium",
                "title": "Elevated Stress Detected",
                "description": f"Individual shows signs of elevated stress (score: {analysis_results['stress_score']:.2f})",
                "recommendations": [
                    "Consider scheduling a check-in conversation",
                    "Review recent workload and pressures",
                    "Provide additional support if needed"
                ]
            })
        
        # Authenticity alerts
        if 'authenticity_score' in analysis_results and analysis_results['authenticity_score'] < 0.4:
            alerts.append({
                "type": "authenticity_concern",
                "severity": "medium",
                "title": "Authenticity Indicators Detected",
                "description": f"Communication shows potential authenticity concerns (score: {analysis_results['authenticity_score']:.2f})",
                "recommendations": [
                    "Consider follow-up questions for clarification",
                    "Verify information through alternative sources",
                    "Approach with diplomatic inquiry"
                ]
            })
        
        # Deception indicators
        if 'deception_indicators' in analysis_results and analysis_results['deception_indicators']:
            deception_count = len(analysis_results['deception_indicators'])
            if deception_count > 2:
                alerts.append({
                    "type": "deception_indicators",
                    "severity": "high" if deception_count > 4 else "medium",
                    "title": "Multiple Deception Indicators Detected",
                    "description": f"Found {deception_count} potential deception indicators in communication",
                    "recommendations": [
                        "Request additional documentation or evidence",
                        "Schedule follow-up meeting for clarification",
                        "Consider independent verification of claims"
                    ]
                })
        
        # Emotional state alerts
        if 'emotional_valence' in analysis_results and analysis_results['emotional_valence'] < -0.6:
            alerts.append({
                "type": "negative_emotional_state",
                "severity": "medium",
                "title": "Negative Emotional State Detected",
                "description": f"Individual shows signs of negative emotional state (valence: {analysis_results['emotional_valence']:.2f})",
                "recommendations": [
                    "Approach with empathy and understanding",
                    "Consider addressing underlying concerns",
                    "Provide emotional support if appropriate"
                ]
            })
        
        return alerts
    
    def _make_request(self, endpoint: str, data: Optional[Dict] = None, 
                     method: str = "POST") -> Dict[str, Any]:
        """
        Make HTTP request to wordsmimir API with retry logic.
        
        Args:
            endpoint: API endpoint to call
            data: Request data (for POST/PUT requests)
            method: HTTP method
            
        Returns:
            Response data from API
        """
        url = f"{self.config.base_url}{endpoint}"
        request_id = str(uuid.uuid4())
        
        # Check cache for GET requests
        if method == "GET" and self._cache and url in self._cache:
            cache_entry = self._cache[url]
            if time.time() - cache_entry['timestamp'] < self.config.cache_ttl:
                logger.info(f"Cache hit for request {request_id}")
                return cache_entry['data']
        
        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = self.session.get(url, timeout=self.config.timeout)
                elif method == "POST":
                    response = self.session.post(url, json=data, timeout=self.config.timeout)
                elif method == "PUT":
                    response = self.session.put(url, json=data, timeout=self.config.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                duration = int((time.time() - start_time) * 1000)
                
                # Log the request
                self._log_api_request(request_id, endpoint, method, data, 
                                    response.status_code, response.json() if response.content else None, 
                                    duration)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Cache successful GET responses
                    if method == "GET" and self._cache:
                        self._cache[url] = {
                            'data': result,
                            'timestamp': time.time()
                        }
                    
                    return result
                elif response.status_code == 429:  # Rate limited
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise
        
        raise Exception(f"Failed to complete request after {self.config.max_retries} attempts")
    
    def _process_text_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize text analysis response."""
        return {
            "linguistic_complexity": response.get("linguistic_complexity", 0.0),
            "emotional_valence": response.get("emotional_valence", 0.0),
            "cognitive_load_score": response.get("cognitive_load", 0.0),
            "deception_indicators": response.get("deception_indicators", []),
            "stress_markers": response.get("stress_markers", []),
            "authenticity_score": response.get("authenticity_score", 0.0),
            "confidence": response.get("confidence", 0.0),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "wordsmimir_version": response.get("version", "unknown")
        }
    
    def _process_audio_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize audio analysis response."""
        return {
            "speech_rate": response.get("speech_rate", 0.0),
            "pitch_mean": response.get("pitch_statistics", {}).get("mean", 0.0),
            "pitch_variance": response.get("pitch_statistics", {}).get("variance", 0.0),
            "volume_variance": response.get("volume_statistics", {}).get("variance", 0.0),
            "pause_frequency": response.get("pause_analysis", {}).get("frequency", 0.0),
            "filler_word_count": response.get("filler_words", {}).get("count", 0),
            "voice_stress_score": response.get("stress_indicators", {}).get("overall_score", 0.0),
            "confidence": response.get("confidence", 0.0),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "wordsmimir_version": response.get("version", "unknown")
        }
    
    def _process_video_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize video analysis response."""
        return {
            "facial_expressions": response.get("facial_expressions", {}),
            "micro_expressions": response.get("micro_expressions", []),
            "gaze_patterns": response.get("gaze_analysis", {}),
            "attention_score": response.get("attention_metrics", {}).get("overall_score", 0.0),
            "visual_stress_indicators": response.get("stress_indicators", []),
            "confidence": response.get("confidence", 0.0),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "wordsmimir_version": response.get("version", "unknown")
        }
    
    def _process_multimodal_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize multimodal analysis response."""
        return {
            "authenticity_score": response.get("authenticity_assessment", {}).get("overall_score", 0.0),
            "congruence_score": response.get("cross_modal_congruence", {}).get("overall_score", 0.0),
            "overall_confidence": response.get("confidence", 0.0),
            "text_analysis": response.get("text_analysis", {}),
            "audio_analysis": response.get("audio_analysis", {}),
            "video_analysis": response.get("video_analysis", {}),
            "integrated_insights": response.get("integrated_insights", []),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "wordsmimir_version": response.get("version", "unknown")
        }
    
    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "error": True,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.0
        }
    
    def _log_api_request(self, request_id: str, endpoint: str, method: str, 
                        request_data: Optional[Dict], status_code: Optional[int],
                        response_data: Optional[Dict], duration_ms: int):
        """Log API request for monitoring and debugging."""
        log_entry = {
            "request_id": request_id,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log at appropriate level based on status
        if status_code and 200 <= status_code < 300:
            logger.info(f"Wordsmimir API success: {log_entry}")
        elif status_code and 400 <= status_code < 500:
            logger.warning(f"Wordsmimir API client error: {log_entry}")
        elif status_code and status_code >= 500:
            logger.error(f"Wordsmimir API server error: {log_entry}")
        else:
            logger.error(f"Wordsmimir API request failed: {log_entry}")

# Factory function for creating wordsmimir service
def create_wordsmimir_service(api_key: str, base_url: Optional[str] = None) -> WordsmimirService:
    """
    Factory function to create a configured WordsmimirService instance.
    
    Args:
        api_key: API key for wordsmimir service
        base_url: Optional custom base URL
        
    Returns:
        Configured WordsmimirService instance
    """
    config = WordsmimirConfig(
        api_key=api_key,
        base_url=base_url or "https://wordsmimir.t-pip.no/api/v1"
    )
    return WordsmimirService(config)

