"""
Elite Command API: Comprehensive Voice Command Service

More than redundantly good voice interaction service for elite executives.
Implements advanced NLP, context awareness, and multi-modal responses.
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
import asyncio

from ..models.voice_command_system import (
    VoiceInteractionMode, VoiceCommandCategory, VoiceCommandIntent,
    VoiceConfidenceLevel, VoiceResponseType, VoiceCommand, VoiceActionMap,
    UIElementTag, VoiceSession, VoiceResponse, VoiceTrainingData,
    VoiceCommandProcessor, VOICE_COMMAND_REGISTRY, UI_ELEMENT_REGISTRY
)

class AdvancedVoiceCommandService:
    """
    Comprehensive voice command service with advanced NLP and context awareness.
    Designed for elite executives requiring sophisticated voice interaction.
    """
    
    def __init__(self):
        self.processor = VoiceCommandProcessor()
        self.active_sessions = {}
        self.command_history = {}
        self.context_memory = {}
        self.user_preferences = {}
        self.training_data = []
        
        # Initialize command registry
        for command_id, command in VOICE_COMMAND_REGISTRY.items():
            self.processor.register_command(command)
            
        # Initialize UI element registry
        for element_id, element in UI_ELEMENT_REGISTRY.items():
            self.processor.register_ui_element(element)
            
        # Advanced NLP patterns
        self.intent_patterns = self._build_intent_patterns()
        self.context_patterns = self._build_context_patterns()
        self.style_mappings = self._build_style_mappings()
        
    def start_voice_session(self, user_id: str, mode: VoiceInteractionMode = VoiceInteractionMode.ACTIVE_VOICE) -> VoiceSession:
        """Start a new voice interaction session"""
        session = VoiceSession(
            session_id=f"voice_{user_id}_{int(time.time())}",
            user_id=user_id,
            start_time=datetime.now(),
            current_mode=mode,
            commands_processed=[],
            context_stack=[],
            user_preferences=self.user_preferences.get(user_id, {}),
            confidence_scores=[],
            error_count=0,
            success_count=0
        )
        
        self.active_sessions[user_id] = session
        return session
    
    def process_voice_command(self, user_id: str, command_text: str, context: Dict[str, Any] = None) -> VoiceResponse:
        """
        Process a voice command with advanced NLP and context awareness
        """
        session = self.active_sessions.get(user_id)
        if not session:
            session = self.start_voice_session(user_id)
            
        # Clean and normalize input
        normalized_text = self._normalize_command_text(command_text)
        
        # Extract wake word and command
        wake_word_detected, clean_command = self._extract_wake_word(normalized_text)
        
        # Parse command with context
        parsed_command = self._parse_command_with_context(clean_command, session, context or {})
        
        if not parsed_command:
            return self._handle_unrecognized_command(clean_command, session)
            
        # Execute command
        response = self._execute_command(parsed_command, session, context or {})
        
        # Update session
        self._update_session(session, command_text, parsed_command, response)
        
        return response
    
    def _normalize_command_text(self, text: str) -> str:
        """Normalize voice command text for better processing"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove filler words
        filler_words = ["um", "uh", "like", "you know", "actually", "basically"]
        for filler in filler_words:
            text = re.sub(rf"\\b{filler}\\b", "", text)
            
        # Normalize contractions
        contractions = {
            "don't": "do not",
            "can't": "cannot", 
            "won't": "will not",
            "it's": "it is",
            "that's": "that is"
        }
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
            
        # Clean up extra spaces
        text = re.sub(r"\\s+", " ", text).strip()
        
        return text
    
    def _extract_wake_word(self, text: str) -> Tuple[bool, str]:
        """Extract wake word and return clean command"""
        wake_words = ["command", "elite", "aura"]
        
        for wake_word in wake_words:
            if text.startswith(wake_word):
                # Remove wake word and comma/pause
                clean_command = text[len(wake_word):].lstrip(", ")
                return True, clean_command
                
        # Check for wake word anywhere in the text
        for wake_word in wake_words:
            if wake_word in text:
                parts = text.split(wake_word, 1)
                if len(parts) > 1:
                    clean_command = parts[1].lstrip(", ")
                    return True, clean_command
                    
        return False, text
    
    def _parse_command_with_context(self, command_text: str, session: VoiceSession, context: Dict[str, Any]) -> Optional[VoiceCommand]:
        """Parse command using advanced NLP with context awareness"""
        
        # Try exact phrase matching first
        for command_id, command in VOICE_COMMAND_REGISTRY.items():
            for phrase in command.example_phrases:
                if self._fuzzy_match(command_text, phrase.lower(), threshold=0.85):
                    return command
                    
        # Try intent-based matching
        detected_intent = self._detect_intent(command_text, context)
        if detected_intent:
            return self._find_command_by_intent(detected_intent, context)
            
        # Try pattern-based matching
        pattern_match = self._match_patterns(command_text, context)
        if pattern_match:
            return pattern_match
            
        # Try contextual inference
        contextual_match = self._infer_from_context(command_text, session, context)
        if contextual_match:
            return contextual_match
            
        return None
    
    def _fuzzy_match(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching for voice command recognition"""
        # Simple Levenshtein distance-based matching
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
    
    def _detect_intent(self, command_text: str, context: Dict[str, Any]) -> Optional[VoiceCommandIntent]:
        """Detect user intent from command text"""
        
        # Style adjustment intents
        style_keywords = {
            "relaxed": ["relaxed", "calm", "softer", "lighter", "gentle"],
            "energetic": ["energetic", "bright", "vibrant", "intense", "bold"],
            "professional": ["professional", "formal", "business", "corporate"],
            "minimal": ["minimal", "clean", "simple", "less", "reduce"]
        }
        
        for style, keywords in style_keywords.items():
            if any(keyword in command_text for keyword in keywords):
                return VoiceCommandIntent.ADJUST_STYLE
                
        # Data intelligence intents
        if any(word in command_text for word in ["why", "explain", "what", "how"]):
            if any(word in command_text for word in ["confidence", "score", "reliable"]):
                return VoiceCommandIntent.CONFIDENCE_INSIGHT
            elif any(word in command_text for word in ["source", "from", "lineage", "trace"]):
                return VoiceCommandIntent.LINEAGE_TRACE
            elif any(word in command_text for word in ["metric", "number", "data"]):
                return VoiceCommandIntent.EXPLAIN_METRIC
                
        # Layout control intents
        if any(word in command_text for word in ["move", "shift", "relocate", "position"]):
            return VoiceCommandIntent.LAYOUT_CONTROL
            
        # Navigation intents
        if any(word in command_text for word in ["show", "open", "display", "focus"]):
            return VoiceCommandIntent.FOCUS_VIEW
            
        return None
    
    def _find_command_by_intent(self, intent: VoiceCommandIntent, context: Dict[str, Any]) -> Optional[VoiceCommand]:
        """Find best command matching the detected intent"""
        matching_commands = [
            cmd for cmd in VOICE_COMMAND_REGISTRY.values()
            if cmd.intent == intent
        ]
        
        if not matching_commands:
            return None
            
        # Sort by executive priority and context relevance
        matching_commands.sort(key=lambda x: (-x.executive_priority, -self._calculate_context_relevance(x, context)))
        
        return matching_commands[0]
    
    def _calculate_context_relevance(self, command: VoiceCommand, context: Dict[str, Any]) -> float:
        """Calculate how relevant a command is to the current context"""
        relevance_score = 0.0
        
        # Check if target elements are currently visible/active
        visible_elements = context.get("visible_elements", [])
        for element in command.target_elements:
            if element in visible_elements:
                relevance_score += 0.3
                
        # Check if command category matches current screen/mode
        current_screen = context.get("current_screen", "")
        if command.category.value in current_screen:
            relevance_score += 0.4
            
        # Check user's recent command history
        recent_categories = context.get("recent_categories", [])
        if command.category in recent_categories:
            relevance_score += 0.2
            
        return relevance_score
    
    def _match_patterns(self, command_text: str, context: Dict[str, Any]) -> Optional[VoiceCommand]:
        """Match command using predefined patterns"""
        
        # Pattern for style adjustments
        style_pattern = r"make (this|it|everything) (more |less )?(\\w+)"
        style_match = re.search(style_pattern, command_text)
        if style_match:
            style_word = style_match.group(3)
            return self._create_dynamic_style_command(style_word, context)
            
        # Pattern for element manipulation
        element_pattern = r"(move|shift|hide|show|resize) (the )?(\\w+)"
        element_match = re.search(element_pattern, command_text)
        if element_match:
            action = element_match.group(1)
            element = element_match.group(3)
            return self._create_dynamic_element_command(action, element, context)
            
        # Pattern for data queries
        data_pattern = r"(what|why|how|where) (is|are|did|does) (.*)"
        data_match = re.search(data_pattern, command_text)
        if data_match:
            question_type = data_match.group(1)
            subject = data_match.group(3)
            return self._create_dynamic_data_command(question_type, subject, context)
            
        return None
    
    def _create_dynamic_style_command(self, style_word: str, context: Dict[str, Any]) -> VoiceCommand:
        """Create a dynamic style adjustment command"""
        return VoiceCommand(
            command_id=f"dynamic_style_{style_word}",
            category=VoiceCommandCategory.INTERFACE_CUSTOMIZATION,
            intent=VoiceCommandIntent.ADJUST_STYLE,
            example_phrases=[f"make it {style_word}"],
            wake_word_required=True,
            mode=VoiceInteractionMode.ACTIVE_VOICE,
            confidence_threshold=0.7,
            response_type=VoiceResponseType.IMMEDIATE_ACTION,
            target_elements=["global_theme"],
            api_endpoint="/api/reflex/mirror",
            parameters={"style_adjustment": style_word},
            fallback_commands=["show style options"],
            context_sensitive=True,
            executive_priority=3
        )
    
    def _create_dynamic_element_command(self, action: str, element: str, context: Dict[str, Any]) -> VoiceCommand:
        """Create a dynamic element manipulation command"""
        return VoiceCommand(
            command_id=f"dynamic_{action}_{element}",
            category=VoiceCommandCategory.INTERFACE_CUSTOMIZATION,
            intent=VoiceCommandIntent.LAYOUT_CONTROL,
            example_phrases=[f"{action} {element}"],
            wake_word_required=True,
            mode=VoiceInteractionMode.ACTIVE_VOICE,
            confidence_threshold=0.8,
            response_type=VoiceResponseType.IMMEDIATE_ACTION,
            target_elements=[element],
            api_endpoint="/api/reflex/edit",
            parameters={"action": action, "element": element},
            fallback_commands=[f"show {element} options"],
            context_sensitive=True,
            executive_priority=3
        )
    
    def _infer_from_context(self, command_text: str, session: VoiceSession, context: Dict[str, Any]) -> Optional[VoiceCommand]:
        """Infer command from conversation context"""
        
        # Check if this is a follow-up to a previous command
        if session.context_stack:
            last_context = session.context_stack[-1]
            
            # Handle confirmation responses
            if command_text in ["yes", "confirm", "do it", "proceed"]:
                return self._get_pending_confirmation_command(session)
                
            # Handle clarification responses
            if "clarification_needed" in last_context:
                return self._resolve_clarification(command_text, last_context, context)
                
        # Check for pronoun references
        if any(pronoun in command_text for pronoun in ["this", "that", "it"]):
            focused_element = context.get("focused_element")
            if focused_element:
                return self._create_pronoun_reference_command(command_text, focused_element, context)
                
        return None
    
    def _execute_command(self, command: VoiceCommand, session: VoiceSession, context: Dict[str, Any]) -> VoiceResponse:
        """Execute a parsed voice command"""
        
        start_time = time.time()
        
        try:
            # Check if confirmation is required
            if command.response_type == VoiceResponseType.CONFIRMATION_REQUIRED:
                return self._request_confirmation(command, session)
                
            # Check if clarification is needed
            if self._needs_clarification(command, context):
                return self._request_clarification(command, session, context)
                
            # Execute the command
            if command.response_type == VoiceResponseType.IMMEDIATE_ACTION:
                result = self._execute_immediate_action(command, context)
            elif command.response_type == VoiceResponseType.DEMONSTRATION:
                result = self._execute_demonstration(command, context)
            elif command.response_type == VoiceResponseType.EXPLANATION:
                result = self._execute_explanation(command, context)
            else:
                result = self._execute_default_action(command, context)
                
            execution_time = time.time() - start_time
            
            return VoiceResponse(
                response_id=f"resp_{int(time.time())}",
                command_id=command.command_id,
                response_type=command.response_type,
                message=result.get("message", "Command executed successfully"),
                actions_taken=result.get("actions", []),
                visual_feedback=result.get("visual_feedback", {}),
                audio_feedback=result.get("audio_feedback"),
                confidence_score=0.95,
                execution_time=execution_time,
                success=True,
                error_details=None
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return VoiceResponse(
                response_id=f"resp_error_{int(time.time())}",
                command_id=command.command_id,
                response_type=VoiceResponseType.ERROR_HANDLING,
                message=f"I encountered an error: {str(e)}",
                actions_taken=[],
                visual_feedback={},
                audio_feedback=None,
                confidence_score=0.0,
                execution_time=execution_time,
                success=False,
                error_details=str(e)
            )
    
    def _execute_immediate_action(self, command: VoiceCommand, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute immediate action commands"""
        
        if command.intent == VoiceCommandIntent.ADJUST_STYLE:
            return self._adjust_interface_style(command.parameters, context)
        elif command.intent == VoiceCommandIntent.LAYOUT_CONTROL:
            return self._control_layout(command.parameters, context)
        elif command.intent == VoiceCommandIntent.TYPOGRAPHY:
            return self._adjust_typography(command.parameters, context)
        elif command.intent == VoiceCommandIntent.THEME:
            return self._change_theme(command.parameters, context)
        else:
            return self._generic_action_execution(command, context)
    
    def _adjust_interface_style(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust interface style based on voice command"""
        
        style_adjustment = parameters.get("style_adjustment", "neutral")
        intensity = parameters.get("intensity", "medium")
        
        # Map style words to specific CSS changes
        style_mappings = {
            "relaxed": {
                "border_radius": "12px",
                "padding": "20px",
                "colors": {"primary": "#6b7280", "accent": "#9ca3af"},
                "font_weight": "300",
                "spacing": "loose"
            },
            "energetic": {
                "border_radius": "4px", 
                "padding": "12px",
                "colors": {"primary": "#f59e0b", "accent": "#ef4444"},
                "font_weight": "600",
                "spacing": "tight"
            },
            "professional": {
                "border_radius": "6px",
                "padding": "16px", 
                "colors": {"primary": "#1e40af", "accent": "#3b82f6"},
                "font_weight": "500",
                "spacing": "normal"
            },
            "minimal": {
                "border_radius": "8px",
                "padding": "24px",
                "colors": {"primary": "#374151", "accent": "#6b7280"},
                "font_weight": "400",
                "spacing": "spacious"
            }
        }
        
        style_config = style_mappings.get(style_adjustment, style_mappings["professional"])
        
        return {
            "message": f"Adjusting interface to feel more {style_adjustment}",
            "actions": [
                {
                    "type": "style_update",
                    "target": "global_theme",
                    "changes": style_config
                }
            ],
            "visual_feedback": {
                "animation": "smooth_transition",
                "duration": 800,
                "highlight_changed_elements": True
            },
            "audio_feedback": f"Interface adjusted to {style_adjustment} style"
        }
    
    def _control_layout(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Control layout elements based on voice command"""
        
        action = parameters.get("action", "move")
        element = parameters.get("element", "")
        position = parameters.get("position", "")
        
        return {
            "message": f"Moving {element} to {position} side",
            "actions": [
                {
                    "type": "layout_change",
                    "action": action,
                    "element": element,
                    "new_position": position
                }
            ],
            "visual_feedback": {
                "animation": "slide_transition",
                "duration": 600,
                "show_grid_guides": True
            },
            "audio_feedback": f"{element} moved to {position}"
        }
    
    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for intent recognition"""
        return {
            "style_adjustment": [
                r"make (this|it|everything) (more |less )?(\\w+)",
                r"(too|very) (\\w+), (\\w+) it",
                r"(soften|harden|lighten|darken) (the )?(\\w+)"
            ],
            "layout_control": [
                r"(move|shift|relocate) (the )?(\\w+) to (the )?(\\w+)",
                r"put (the )?(\\w+) on (the )?(\\w+)",
                r"(hide|show|display) (the )?(\\w+)"
            ],
            "data_query": [
                r"(what|why|how|where) (is|are|did|does) (.*)",
                r"explain (the )?(\\w+)",
                r"show me (the )?(\\w+)"
            ]
        }
    
    def _build_context_patterns(self) -> Dict[str, Any]:
        """Build context-aware patterns"""
        return {
            "follow_up_indicators": ["also", "and", "then", "next"],
            "confirmation_phrases": ["yes", "confirm", "do it", "proceed", "go ahead"],
            "negation_phrases": ["no", "cancel", "stop", "never mind", "abort"],
            "clarification_requests": ["what do you mean", "explain", "how", "which one"]
        }
    
    def _build_style_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive style mappings"""
        return {
            "emotional_styles": {
                "calm": {"colors": "cool", "spacing": "loose", "animation": "slow"},
                "energetic": {"colors": "warm", "spacing": "tight", "animation": "fast"},
                "focused": {"colors": "monochrome", "spacing": "minimal", "animation": "none"},
                "creative": {"colors": "vibrant", "spacing": "varied", "animation": "playful"}
            },
            "professional_styles": {
                "corporate": {"formality": "high", "colors": "conservative", "typography": "serif"},
                "startup": {"formality": "low", "colors": "modern", "typography": "sans-serif"},
                "consulting": {"formality": "medium", "colors": "professional", "typography": "clean"}
            }
        }
    
    def _handle_unrecognized_command(self, command_text: str, session: VoiceSession) -> VoiceResponse:
        """Handle unrecognized voice commands gracefully"""
        
        # Try to suggest similar commands
        suggestions = self._find_similar_commands(command_text)
        
        message = "I didn't quite understand that command."
        if suggestions:
            message += f" Did you mean: {', '.join(suggestions[:3])}?"
        else:
            message += " Try saying 'Command, show me what I can do' for help."
            
        return VoiceResponse(
            response_id=f"unrecognized_{int(time.time())}",
            command_id="unrecognized",
            response_type=VoiceResponseType.CLARIFICATION_NEEDED,
            message=message,
            actions_taken=[],
            visual_feedback={"show_help_hints": True},
            audio_feedback=message,
            confidence_score=0.0,
            execution_time=0.1,
            success=False,
            error_details="Command not recognized"
        )
    
    def _find_similar_commands(self, command_text: str) -> List[str]:
        """Find similar commands for suggestions"""
        suggestions = []
        
        for command in VOICE_COMMAND_REGISTRY.values():
            for phrase in command.example_phrases:
                if self._fuzzy_match(command_text, phrase.lower(), threshold=0.6):
                    suggestions.append(phrase)
                    break
                    
        return suggestions[:5]  # Return top 5 suggestions
    
    def _update_session(self, session: VoiceSession, command_text: str, command: VoiceCommand, response: VoiceResponse):
        """Update voice session with command and response"""
        
        session.commands_processed.append({
            "timestamp": datetime.now().isoformat(),
            "command_text": command_text,
            "command_id": command.command_id if command else "unknown",
            "response_id": response.response_id,
            "success": response.success,
            "confidence": response.confidence_score
        })
        
        session.confidence_scores.append(response.confidence_score)
        
        if response.success:
            session.success_count += 1
        else:
            session.error_count += 1
            
        # Update context stack
        session.context_stack.append({
            "command": command_text,
            "intent": command.intent.value if command else "unknown",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 5 context items
        if len(session.context_stack) > 5:
            session.context_stack = session.context_stack[-5:]
    
    def get_voice_session_status(self, user_id: str) -> Dict[str, Any]:
        """Get current voice session status"""
        session = self.active_sessions.get(user_id)
        
        if not session:
            return {"status": "no_active_session"}
            
        avg_confidence = sum(session.confidence_scores) / len(session.confidence_scores) if session.confidence_scores else 0
        
        return {
            "status": "active",
            "session_id": session.session_id,
            "current_mode": session.current_mode.value,
            "commands_processed": len(session.commands_processed),
            "success_rate": session.success_count / (session.success_count + session.error_count) if (session.success_count + session.error_count) > 0 else 0,
            "average_confidence": avg_confidence,
            "session_duration": (datetime.now() - session.start_time).total_seconds(),
            "context_items": len(session.context_stack)
        }
    
    def get_available_commands(self, category: Optional[VoiceCommandCategory] = None) -> List[Dict[str, Any]]:
        """Get list of available voice commands"""
        commands = []
        
        for command in VOICE_COMMAND_REGISTRY.values():
            if category is None or command.category == category:
                commands.append({
                    "command_id": command.command_id,
                    "category": command.category.value,
                    "intent": command.intent.value,
                    "example_phrases": command.example_phrases,
                    "wake_word_required": command.wake_word_required,
                    "executive_priority": command.executive_priority,
                    "description": f"{command.category.value.replace('_', ' ').title()} - {command.intent.value.replace('_', ' ').title()}"
                })
                
        # Sort by executive priority
        commands.sort(key=lambda x: -x["executive_priority"])
        
        return commands

