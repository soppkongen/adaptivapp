"""
Reflective Vault API Routes

REST endpoints for the personal AI research garden that captures and cultivates
executive thoughts over time through media ingestion, reflection, and output generation.
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import logging
import asyncio
import os
from werkzeug.utils import secure_filename

# Local imports
from src.services.reflective_vault_service import ReflectiveVaultService
from src.models.reflective_vault import (
    VaultEntryType, VaultPrivacyLevel, VaultOutputType,
    VaultRipenessLevel, VaultReflectionTrigger
)

# Create blueprint
vault_bp = Blueprint('reflective_vault', __name__, url_prefix='/api/vault')

# Initialize service
vault_service = ReflectiveVaultService()

# Allowed file extensions for media upload
ALLOWED_EXTENSIONS = {
    'audio': {'wav', 'mp3', 'ogg', 'm4a'},
    'video': {'mp4', 'avi', 'mov', 'webm'},
    'image': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'},
    'document': {'txt', 'md', 'pdf', 'doc', 'docx'}
}

def allowed_file(filename: str, file_type: str) -> bool:
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS.get(file_type, set())

@vault_bp.route('/session/start', methods=['POST'])
def start_vault_session():
    """Start a new vault session"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        session = vault_service.start_vault_session(user_id)
        
        return jsonify({
            "success": True,
            "session": {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "started_at": session.started_at.isoformat(),
                "status": "active"
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to start vault session: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/session/<session_id>/status', methods=['GET'])
def get_vault_session_status(session_id: str):
    """Get vault session status"""
    try:
        session = vault_service.get_vault_session(session_id)
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "success": True,
            "session": {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "started_at": session.started_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "current_entry_id": session.current_entry_id,
                "viewing_timeline": session.viewing_timeline,
                "entries_viewed": len(session.entries_viewed),
                "reflections_triggered": session.reflections_triggered,
                "outputs_generated": session.outputs_generated
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to get session status: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/ingest/text', methods=['POST'])
def ingest_text():
    """Ingest text content into the vault"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        content = data.get('content')
        title = data.get('title', '')
        description = data.get('description', '')
        privacy_level = VaultPrivacyLevel(data.get('privacy_level', 'reflective'))
        tags = data.get('tags', [])
        
        if not user_id or not content:
            return jsonify({"error": "user_id and content are required"}), 400
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        entry = loop.run_until_complete(
            vault_service.ingest_media(
                user_id=user_id,
                media_data=content,
                entry_type=VaultEntryType.TEXT_NOTE,
                title=title,
                description=description,
                privacy_level=privacy_level,
                tags=tags
            )
        )
        
        loop.close()
        
        return jsonify({
            "success": True,
            "entry": {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "created_at": entry.created_at.isoformat(),
                "entry_type": entry.entry_type.value,
                "privacy_level": entry.privacy_level.value,
                "ripeness_level": entry.ripeness_level.value,
                "ripeness_score": entry.ripeness_score,
                "semantic_analysis": {
                    "main_themes": entry.semantic_analysis.main_themes if entry.semantic_analysis else [],
                    "intended_purpose": entry.semantic_analysis.intended_purpose if entry.semantic_analysis else "",
                    "strategic_value": entry.semantic_analysis.strategic_value if entry.semantic_analysis else 0.0
                } if entry.semantic_analysis else None
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to ingest text: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/ingest/media', methods=['POST'])
def ingest_media():
    """Ingest media files (audio, video, image) into the vault"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get form data
        user_id = request.form.get('user_id')
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        privacy_level = VaultPrivacyLevel(request.form.get('privacy_level', 'reflective'))
        tags = json.loads(request.form.get('tags', '[]'))
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Determine file type and validate
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        entry_type = None
        if file_extension in ALLOWED_EXTENSIONS['audio']:
            entry_type = VaultEntryType.VOICE_MEMO
        elif file_extension in ALLOWED_EXTENSIONS['video']:
            entry_type = VaultEntryType.VIDEO_CAPTURE
        elif file_extension in ALLOWED_EXTENSIONS['image']:
            entry_type = VaultEntryType.IMAGE_UPLOAD
        else:
            return jsonify({"error": f"Unsupported file type: {file_extension}"}), 400
        
        # Save file temporarily
        temp_path = f"/tmp/vault_upload_{user_id}_{datetime.now().timestamp()}.{file_extension}"
        file.save(temp_path)
        
        try:
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            entry = loop.run_until_complete(
                vault_service.ingest_media(
                    user_id=user_id,
                    media_data=temp_path,
                    entry_type=entry_type,
                    title=title or filename,
                    description=description,
                    privacy_level=privacy_level,
                    tags=tags
                )
            )
            
            loop.close()
            
            return jsonify({
                "success": True,
                "entry": {
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "created_at": entry.created_at.isoformat(),
                    "entry_type": entry.entry_type.value,
                    "privacy_level": entry.privacy_level.value,
                    "ripeness_level": entry.ripeness_level.value,
                    "media_metadata": {
                        "file_type": entry.media_metadata.file_type if entry.media_metadata else None,
                        "file_size": entry.media_metadata.file_size if entry.media_metadata else None,
                        "duration": entry.media_metadata.duration if entry.media_metadata else None,
                        "transcription": entry.media_metadata.transcription if entry.media_metadata else None,
                        "visual_description": entry.media_metadata.visual_description if entry.media_metadata else None
                    } if entry.media_metadata else None,
                    "semantic_analysis": {
                        "main_themes": entry.semantic_analysis.main_themes if entry.semantic_analysis else [],
                        "intended_purpose": entry.semantic_analysis.intended_purpose if entry.semantic_analysis else "",
                        "strategic_value": entry.semantic_analysis.strategic_value if entry.semantic_analysis else 0.0
                    } if entry.semantic_analysis else None
                }
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        logging.error(f"Failed to ingest media: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/entries/<user_id>', methods=['GET'])
def get_user_entries(user_id: str):
    """Get all vault entries for a user"""
    try:
        # Get query parameters
        ripeness_filter = request.args.get('ripeness_level')
        privacy_filter = request.args.get('privacy_level')
        entry_type_filter = request.args.get('entry_type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Get user entries
        user_entries = [e for e in vault_service.vault_entries.values() if e.user_id == user_id]
        
        # Apply filters
        if ripeness_filter:
            user_entries = [e for e in user_entries if e.ripeness_level.value == ripeness_filter]
        if privacy_filter:
            user_entries = [e for e in user_entries if e.privacy_level.value == privacy_filter]
        if entry_type_filter:
            user_entries = [e for e in user_entries if e.entry_type.value == entry_type_filter]
        
        # Sort by creation date (newest first)
        user_entries.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total_entries = len(user_entries)
        user_entries = user_entries[offset:offset + limit]
        
        # Format response
        entries = []
        for entry in user_entries:
            entries.append({
                "entry_id": entry.entry_id,
                "title": entry.title,
                "description": entry.description,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
                "entry_type": entry.entry_type.value,
                "privacy_level": entry.privacy_level.value,
                "ripeness_level": entry.ripeness_level.value,
                "ripeness_score": entry.ripeness_score,
                "tags": entry.tags,
                "reflection_count": len(entry.reflections),
                "cross_link_count": len(entry.cross_links),
                "output_count": len(entry.generated_outputs),
                "harvest_ready": entry.harvest_ready,
                "last_reflection": entry.last_reflection.isoformat() if entry.last_reflection else None,
                "semantic_summary": {
                    "main_themes": entry.semantic_analysis.main_themes[:3] if entry.semantic_analysis else [],
                    "intended_purpose": entry.semantic_analysis.intended_purpose if entry.semantic_analysis else "",
                    "strategic_value": entry.semantic_analysis.strategic_value if entry.semantic_analysis else 0.0
                } if entry.semantic_analysis else None
            })
        
        return jsonify({
            "success": True,
            "entries": entries,
            "pagination": {
                "total": total_entries,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_entries
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to get user entries: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/entry/<entry_id>', methods=['GET'])
def get_entry_details(entry_id: str):
    """Get detailed information about a specific vault entry"""
    try:
        entry = vault_service.vault_entries.get(entry_id)
        
        if not entry:
            return jsonify({"error": "Entry not found"}), 404
        
        # Format detailed response
        entry_details = {
            "entry_id": entry.entry_id,
            "user_id": entry.user_id,
            "title": entry.title,
            "description": entry.description,
            "raw_content": entry.raw_content,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "entry_type": entry.entry_type.value,
            "privacy_level": entry.privacy_level.value,
            "ripeness_level": entry.ripeness_level.value,
            "ripeness_score": entry.ripeness_score,
            "tags": entry.tags,
            "harvest_ready": entry.harvest_ready,
            "harvest_suggestions": entry.harvest_suggestions,
            "last_reflection": entry.last_reflection.isoformat() if entry.last_reflection else None,
            "next_reflection": entry.next_reflection.isoformat() if entry.next_reflection else None,
            
            "media_metadata": {
                "file_path": entry.media_metadata.file_path if entry.media_metadata else None,
                "file_type": entry.media_metadata.file_type if entry.media_metadata else None,
                "file_size": entry.media_metadata.file_size if entry.media_metadata else None,
                "duration": entry.media_metadata.duration if entry.media_metadata else None,
                "dimensions": entry.media_metadata.dimensions if entry.media_metadata else None,
                "transcription": entry.media_metadata.transcription if entry.media_metadata else None,
                "visual_description": entry.media_metadata.visual_description if entry.media_metadata else None,
                "detected_objects": entry.media_metadata.detected_objects if entry.media_metadata else [],
                "detected_faces": entry.media_metadata.detected_faces if entry.media_metadata else [],
                "detected_emotions": entry.media_metadata.detected_emotions if entry.media_metadata else []
            } if entry.media_metadata else None,
            
            "semantic_analysis": {
                "main_themes": entry.semantic_analysis.main_themes if entry.semantic_analysis else [],
                "tone_emotion": entry.semantic_analysis.tone_emotion if entry.semantic_analysis else {},
                "intended_purpose": entry.semantic_analysis.intended_purpose if entry.semantic_analysis else "",
                "confidence_score": entry.semantic_analysis.confidence_score if entry.semantic_analysis else 0.0,
                "key_concepts": entry.semantic_analysis.key_concepts if entry.semantic_analysis else [],
                "sentiment_score": entry.semantic_analysis.sentiment_score if entry.semantic_analysis else 0.0,
                "urgency_level": entry.semantic_analysis.urgency_level if entry.semantic_analysis else 1,
                "complexity_level": entry.semantic_analysis.complexity_level if entry.semantic_analysis else 1,
                "strategic_value": entry.semantic_analysis.strategic_value if entry.semantic_analysis else 0.0,
                "related_domains": entry.semantic_analysis.related_domains if entry.semantic_analysis else []
            } if entry.semantic_analysis else None,
            
            "reflections": [
                {
                    "reflection_id": r.reflection_id,
                    "timestamp": r.timestamp.isoformat(),
                    "trigger": r.trigger.value,
                    "reflection_text": r.reflection_text,
                    "new_insights": r.new_insights,
                    "questions_generated": r.questions_generated,
                    "action_items": r.action_items,
                    "cross_links": r.cross_links,
                    "ripeness_delta": r.ripeness_delta,
                    "confidence_score": r.confidence_score
                }
                for r in entry.reflections
            ],
            
            "cross_links": [
                {
                    "target_id": link_id,
                    "target_entry": {
                        "title": vault_service.vault_entries[link_id].title,
                        "ripeness_level": vault_service.vault_entries[link_id].ripeness_level.value,
                        "created_at": vault_service.vault_entries[link_id].created_at.isoformat()
                    } if link_id in vault_service.vault_entries else None
                }
                for link_id in entry.cross_links
            ],
            
            "generated_outputs": entry.generated_outputs
        }
        
        return jsonify({
            "success": True,
            "entry": entry_details
        })
        
    except Exception as e:
        logging.error(f"Failed to get entry details: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/reflection/trigger', methods=['POST'])
def trigger_reflection():
    """Manually trigger a reflection on a vault entry"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        entry_id = data.get('entry_id')
        
        if not user_id or not entry_id:
            return jsonify({"error": "user_id and entry_id are required"}), 400
        
        # Verify entry exists and belongs to user
        entry = vault_service.vault_entries.get(entry_id)
        if not entry or entry.user_id != user_id:
            return jsonify({"error": "Entry not found or access denied"}), 404
        
        # Run async reflection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            vault_service._perform_reflection(entry_id, user_id)
        )
        
        loop.close()
        
        # Get updated entry
        updated_entry = vault_service.vault_entries[entry_id]
        latest_reflection = updated_entry.reflections[-1] if updated_entry.reflections else None
        
        return jsonify({
            "success": True,
            "reflection": {
                "reflection_id": latest_reflection.reflection_id if latest_reflection else None,
                "timestamp": latest_reflection.timestamp.isoformat() if latest_reflection else None,
                "new_insights": latest_reflection.new_insights if latest_reflection else [],
                "questions_generated": latest_reflection.questions_generated if latest_reflection else [],
                "ripeness_delta": latest_reflection.ripeness_delta if latest_reflection else 0.0
            } if latest_reflection else None,
            "updated_ripeness": {
                "ripeness_level": updated_entry.ripeness_level.value,
                "ripeness_score": updated_entry.ripeness_score,
                "harvest_ready": updated_entry.harvest_ready
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to trigger reflection: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/output/generate', methods=['POST'])
def generate_output():
    """Generate output from vault entries"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        entry_ids = data.get('entry_ids', [])
        output_type = VaultOutputType(data.get('output_type'))
        title = data.get('title', '')
        custom_prompt = data.get('custom_prompt', '')
        
        if not user_id or not entry_ids:
            return jsonify({"error": "user_id and entry_ids are required"}), 400
        
        # Run async output generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        output = loop.run_until_complete(
            vault_service.generate_output(
                user_id=user_id,
                entry_ids=entry_ids,
                output_type=output_type,
                title=title,
                custom_prompt=custom_prompt
            )
        )
        
        loop.close()
        
        return jsonify({
            "success": True,
            "output": {
                "output_id": output.output_id,
                "title": output.title,
                "content": output.content,
                "output_type": output.output_type.value,
                "generated_at": output.generated_at.isoformat(),
                "quality_score": output.quality_score,
                "source_entry_count": len(output.source_entry_ids)
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to generate output: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/timeline/<user_id>', methods=['GET'])
def get_vault_timeline(user_id: str):
    """Get timeline view of vault entries and reflections"""
    try:
        entry_id = request.args.get('entry_id')
        
        timeline = vault_service.get_vault_timeline(user_id, entry_id)
        
        return jsonify({
            "success": True,
            "timeline": timeline
        })
        
    except Exception as e:
        logging.error(f"Failed to get vault timeline: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/analytics/<user_id>', methods=['GET'])
def get_vault_analytics(user_id: str):
    """Get analytics for user's vault usage"""
    try:
        analytics = vault_service.get_vault_analytics(user_id)
        
        return jsonify({
            "success": True,
            "analytics": {
                "user_id": analytics.user_id,
                "period_start": analytics.period_start.isoformat(),
                "period_end": analytics.period_end.isoformat(),
                "total_entries": analytics.total_entries,
                "entries_by_type": analytics.entries_by_type,
                "entries_by_privacy_level": analytics.entries_by_privacy_level,
                "total_reflections": analytics.total_reflections,
                "avg_reflections_per_entry": analytics.avg_reflections_per_entry,
                "ripeness_progression": analytics.ripeness_progression,
                "total_outputs": analytics.total_outputs,
                "total_cross_links": analytics.total_cross_links,
                "avg_links_per_entry": analytics.avg_links_per_entry
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to get vault analytics: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/search', methods=['POST'])
def search_vault():
    """Search vault entries using semantic similarity"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        query = data.get('query')
        limit = data.get('limit', 10)
        
        if not user_id or not query:
            return jsonify({"error": "user_id and query are required"}), 400
        
        # Perform semantic search using ChromaDB
        if not vault_service.vault_collection:
            return jsonify({"error": "Search functionality not available"}), 503
        
        # Generate query embedding
        query_embedding = vault_service.sentence_model.encode([query])[0]
        
        # Search in vector database
        results = vault_service.vault_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit,
            where={"user_id": user_id}
        )
        
        # Format search results
        search_results = []
        for i, (entry_id, distance, document) in enumerate(zip(
            results['ids'][0], results['distances'][0], results['documents'][0]
        )):
            entry = vault_service.vault_entries.get(entry_id)
            if entry:
                search_results.append({
                    "entry_id": entry_id,
                    "title": entry.title,
                    "similarity_score": 1.0 - distance,
                    "ripeness_level": entry.ripeness_level.value,
                    "created_at": entry.created_at.isoformat(),
                    "snippet": document[:200] + "..." if len(document) > 200 else document,
                    "main_themes": entry.semantic_analysis.main_themes[:3] if entry.semantic_analysis else []
                })
        
        return jsonify({
            "success": True,
            "query": query,
            "results": search_results,
            "total_results": len(search_results)
        })
        
    except Exception as e:
        logging.error(f"Failed to search vault: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/entry/<entry_id>/privacy', methods=['PUT'])
def update_entry_privacy(entry_id: str):
    """Update privacy level of a vault entry"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_privacy_level = VaultPrivacyLevel(data.get('privacy_level'))
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Verify entry exists and belongs to user
        entry = vault_service.vault_entries.get(entry_id)
        if not entry or entry.user_id != user_id:
            return jsonify({"error": "Entry not found or access denied"}), 404
        
        # Update privacy level
        old_privacy_level = entry.privacy_level
        entry.privacy_level = new_privacy_level
        entry.updated_at = datetime.now()
        
        return jsonify({
            "success": True,
            "entry_id": entry_id,
            "old_privacy_level": old_privacy_level.value,
            "new_privacy_level": new_privacy_level.value,
            "updated_at": entry.updated_at.isoformat()
        })
        
    except Exception as e:
        logging.error(f"Failed to update entry privacy: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/entry/<entry_id>/tags', methods=['PUT'])
def update_entry_tags(entry_id: str):
    """Update tags for a vault entry"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_tags = data.get('tags', [])
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Verify entry exists and belongs to user
        entry = vault_service.vault_entries.get(entry_id)
        if not entry or entry.user_id != user_id:
            return jsonify({"error": "Entry not found or access denied"}), 404
        
        # Update tags
        old_tags = entry.tags.copy()
        entry.tags = new_tags
        entry.updated_at = datetime.now()
        
        return jsonify({
            "success": True,
            "entry_id": entry_id,
            "old_tags": old_tags,
            "new_tags": new_tags,
            "updated_at": entry.updated_at.isoformat()
        })
        
    except Exception as e:
        logging.error(f"Failed to update entry tags: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/harvest/suggestions/<user_id>', methods=['GET'])
def get_harvest_suggestions(user_id: str):
    """Get suggestions for entries ready to harvest"""
    try:
        # Get entries ready for harvest
        user_entries = [e for e in vault_service.vault_entries.values() if e.user_id == user_id]
        harvest_ready_entries = [e for e in user_entries if e.harvest_ready]
        
        # Sort by ripeness score (highest first)
        harvest_ready_entries.sort(key=lambda x: x.ripeness_score, reverse=True)
        
        suggestions = []
        for entry in harvest_ready_entries:
            suggestions.append({
                "entry_id": entry.entry_id,
                "title": entry.title,
                "ripeness_score": entry.ripeness_score,
                "ripeness_level": entry.ripeness_level.value,
                "harvest_suggestions": entry.harvest_suggestions,
                "main_themes": entry.semantic_analysis.main_themes if entry.semantic_analysis else [],
                "strategic_value": entry.semantic_analysis.strategic_value if entry.semantic_analysis else 0.0,
                "reflection_count": len(entry.reflections),
                "cross_link_count": len(entry.cross_links),
                "created_at": entry.created_at.isoformat(),
                "last_reflection": entry.last_reflection.isoformat() if entry.last_reflection else None
            })
        
        return jsonify({
            "success": True,
            "harvest_suggestions": suggestions,
            "total_ready": len(suggestions)
        })
        
    except Exception as e:
        logging.error(f"Failed to get harvest suggestions: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/cross-links/<entry_id>', methods=['GET'])
def get_entry_cross_links(entry_id: str):
    """Get cross-links for a specific entry"""
    try:
        entry = vault_service.vault_entries.get(entry_id)
        
        if not entry:
            return jsonify({"error": "Entry not found"}), 404
        
        # Get detailed cross-link information
        cross_links = []
        for link_id in entry.cross_links:
            linked_entry = vault_service.vault_entries.get(link_id)
            if linked_entry:
                cross_links.append({
                    "target_id": link_id,
                    "target_title": linked_entry.title,
                    "target_ripeness_level": linked_entry.ripeness_level.value,
                    "target_ripeness_score": linked_entry.ripeness_score,
                    "target_created_at": linked_entry.created_at.isoformat(),
                    "target_themes": linked_entry.semantic_analysis.main_themes if linked_entry.semantic_analysis else [],
                    "connection_strength": 0.8,  # Placeholder - could calculate actual strength
                    "connection_type": "semantic_similarity"  # Placeholder
                })
        
        return jsonify({
            "success": True,
            "entry_id": entry_id,
            "cross_links": cross_links,
            "total_links": len(cross_links)
        })
        
    except Exception as e:
        logging.error(f"Failed to get cross-links: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/reflection/schedule/<entry_id>', methods=['GET'])
def get_reflection_schedule(entry_id: str):
    """Get reflection schedule for an entry"""
    try:
        # Find schedule for this entry
        schedule = None
        for schedule_key, sched in vault_service.reflection_schedules.items():
            if sched.entry_id == entry_id:
                schedule = sched
                break
        
        if not schedule:
            return jsonify({"error": "No reflection schedule found"}), 404
        
        return jsonify({
            "success": True,
            "schedule": {
                "schedule_id": schedule.schedule_id,
                "entry_id": schedule.entry_id,
                "user_id": schedule.user_id,
                "reflection_interval_days": schedule.reflection_interval.days,
                "next_reflection": schedule.next_reflection.isoformat(),
                "current_reflection_count": schedule.current_reflection_count,
                "max_reflections": schedule.max_reflections,
                "active": schedule.active,
                "paused_until": schedule.paused_until.isoformat() if schedule.paused_until else None,
                "last_reflection": schedule.last_reflection.isoformat() if schedule.last_reflection else None
            }
        })
        
    except Exception as e:
        logging.error(f"Failed to get reflection schedule: {e}")
        return jsonify({"error": str(e)}), 500

@vault_bp.route('/help/commands', methods=['GET'])
def get_vault_help():
    """Get help information about vault commands and features"""
    try:
        help_info = {
            "vault_overview": {
                "description": "Personal AI research garden that captures and cultivates executive thoughts over time",
                "core_functions": [
                    "Media ingestion (voice, video, image, text)",
                    "Semantic decomposition and analysis",
                    "Time-based reflection engine",
                    "Cross-linking and connection discovery",
                    "Output generation (slides, prompts, action items)"
                ]
            },
            "entry_types": {
                "text_note": "Written thoughts and ideas",
                "voice_memo": "Audio recordings of spoken ideas",
                "video_capture": "Video recordings with visual and audio content",
                "image_upload": "Images, sketches, and visual references",
                "live_webcam": "Real-time webcam capture",
                "live_microphone": "Real-time audio capture"
            },
            "privacy_levels": {
                "locked": "No AI processing allowed - completely private",
                "reflective": "AI can analyze and reflect on content",
                "volatile": "AI can remix and transform content freely",
                "collaborative": "Can be shared with team members"
            },
            "ripeness_levels": {
                "seed": "Initial capture, raw idea",
                "sprouting": "First reflections and connections",
                "growing": "Multiple reflections, cross-links forming",
                "maturing": "Rich connections, actionable insights",
                "ripe": "Ready for harvest/implementation",
                "harvested": "Converted to actionable output"
            },
            "output_types": {
                "draft_slides": "Executive presentation slides",
                "concept_art": "Visual concept representations",
                "startup_ideas": "Business concept development",
                "journal_fragments": "Reflective writing pieces",
                "code_stubs": "Technical implementation sketches",
                "strategic_prompts": "Strategic thinking frameworks",
                "action_items": "Actionable task lists",
                "research_questions": "Investigation frameworks"
            },
            "api_endpoints": {
                "ingestion": [
                    "POST /api/vault/ingest/text - Ingest text content",
                    "POST /api/vault/ingest/media - Ingest media files"
                ],
                "management": [
                    "GET /api/vault/entries/{user_id} - List user entries",
                    "GET /api/vault/entry/{entry_id} - Get entry details",
                    "PUT /api/vault/entry/{entry_id}/privacy - Update privacy",
                    "PUT /api/vault/entry/{entry_id}/tags - Update tags"
                ],
                "reflection": [
                    "POST /api/vault/reflection/trigger - Trigger manual reflection",
                    "GET /api/vault/reflection/schedule/{entry_id} - Get schedule"
                ],
                "output": [
                    "POST /api/vault/output/generate - Generate output",
                    "GET /api/vault/harvest/suggestions/{user_id} - Get harvest suggestions"
                ],
                "analysis": [
                    "POST /api/vault/search - Semantic search",
                    "GET /api/vault/timeline/{user_id} - Get timeline view",
                    "GET /api/vault/analytics/{user_id} - Get usage analytics",
                    "GET /api/vault/cross-links/{entry_id} - Get cross-links"
                ]
            }
        }
        
        return jsonify({
            "success": True,
            "help": help_info
        })
        
    except Exception as e:
        logging.error(f"Failed to get vault help: {e}")
        return jsonify({"error": str(e)}), 500

