"""
FastAPI Backend for Super Personal Agent

This provides a REST API interface for your personal AI assistant.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import uuid
from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Dict, List

# Add parent directory to path to import agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from examples.multimodal_agent import MultimodalAgent

# Initialize FastAPI app
app = FastAPI(
    title="Orel AI API",
    description="REST API for Orel - Superintelligent AI Assistant with advanced multimodal capabilities",
    version="2.0.0"
)

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent (singleton)
agent = None
current_conversation_id = str(uuid.uuid4())  # Initialize with a conversation ID

def get_agent():
    """Get or create the agent instance."""
    global agent
    if agent is None:
        try:
            agent = MultimodalAgent()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")
    return agent

def reset_agent_conversation():
    """Reset the agent's conversation history (start new conversation)."""
    global agent, current_conversation_id
    if agent:
        agent.history = []
    current_conversation_id = str(uuid.uuid4())
    return current_conversation_id

# Request/Response models
class TextRequest(BaseModel):
    text: str
    image_path: Optional[str] = None

class TextResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: str = "realistic"

class ImageGenerationResponse(BaseModel):
    message: str
    image_path: Optional[str] = None
    image_url: Optional[str] = None

class AudioTranscriptionRequest(BaseModel):
    audio_path: str
    language: Optional[str] = None

class AudioTranscriptionResponse(BaseModel):
    transcript: str

class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"

class TTSResponse(BaseModel):
    message: str
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None

# Upload directories
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
UPLOAD_DIR_IMAGES = UPLOAD_DIR / "images"
UPLOAD_DIR_AUDIO = UPLOAD_DIR / "audio"
UPLOAD_DIR_IMAGES.mkdir(exist_ok=True)
UPLOAD_DIR_AUDIO.mkdir(exist_ok=True)

# Conversation history storage
HISTORY_DIR = Path(__file__).parent.parent / "conversation_history"
HISTORY_DIR.mkdir(exist_ok=True)
HISTORY_FILE = HISTORY_DIR / "conversations.json"

# Load conversation history
def load_history() -> List[Dict]:
    """Load conversation history from file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Save conversation history
def save_history(history: List[Dict]):
    """Save conversation history to file."""
    try:
        # Ensure directory exists
        HISTORY_DIR.mkdir(exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(history)} conversations to {HISTORY_FILE}")
    except Exception as e:
        print(f"❌ Error saving history: {e}")
        import traceback
        traceback.print_exc()

# Add conversation entry
def add_conversation_entry(user_message: str, agent_response: str, image_path: Optional[str] = None, conversation_id: Optional[str] = None):
    """Add a conversation entry to history."""
    global current_conversation_id
    
    # Use provided conversation_id or current one
    if conversation_id is None:
        if current_conversation_id is None:
            current_conversation_id = str(uuid.uuid4())
        conversation_id = current_conversation_id
    
    history = load_history()
    entry = {
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,  # Group messages by conversation
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "agent_response": agent_response,
        "image_path": image_path
    }
    history.append(entry)
    # Keep only last 1000 conversations
    if len(history) > 1000:
        history = history[-1000:]
    save_history(history)
    return entry

# API Routes
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Orel AI API is running",
        "version": "2.0.0",
        "agent": "Orel"
    }

@app.get("/api/health")
async def health():
    """Health check for agent."""
    try:
        agent = get_agent()
        return {"status": "healthy", "agent_initialized": True}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/routes")
async def list_routes():
    """List all available API routes for debugging."""
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

# Agent-controlled camera capture
agent_camera_enabled = False
camera_capture_queue = []

@app.post("/api/agent/capture-photo")
async def agent_capture_photo():
    """
    Agent requests to capture a photo from the camera.
    Returns a signal that the frontend should capture a photo.
    """
    global agent_camera_enabled, camera_capture_queue
    
    if not agent_camera_enabled:
        return {
            "status": "error",
            "message": "Agent camera control is not enabled. Please enable it in the UI."
        }
    
    # Add capture request to queue
    capture_id = str(uuid.uuid4())
    camera_capture_queue.append({
        "id": capture_id,
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "status": "success",
        "capture_id": capture_id,
        "message": "Photo capture requested"
    }

@app.get("/api/agent/camera-status")
async def get_camera_status():
    """Get current camera status and any pending captures."""
    global agent_camera_enabled, camera_capture_queue
    
    return {
        "enabled": agent_camera_enabled,
        "pending_captures": len(camera_capture_queue),
        "queue": camera_capture_queue[-5:] if camera_capture_queue else []  # Last 5 requests
    }

class CameraControlRequest(BaseModel):
    enabled: bool = True

@app.post("/api/agent/enable-camera")
async def enable_agent_camera(request: CameraControlRequest):
    """Enable or disable agent camera control."""
    global agent_camera_enabled
    agent_camera_enabled = request.enabled
    return {
        "status": "success",
        "enabled": agent_camera_enabled,
        "message": f"Agent camera control {'enabled' if agent_camera_enabled else 'disabled'}"
    }

@app.get("/api/agent/poll-capture")
async def poll_capture():
    """Frontend polls this to check if agent requested a capture."""
    global camera_capture_queue
    
    if camera_capture_queue:
        capture = camera_capture_queue.pop(0)
        return {
            "status": "capture_requested",
            "capture_id": capture["id"]
        }
    
    return {
        "status": "no_capture"
    }

@app.post("/api/agent/capture-complete")
async def capture_complete(capture_id: str, image_path: str):
    """Frontend notifies backend that capture is complete."""
    return {
        "status": "success",
        "capture_id": capture_id,
        "image_path": image_path,
        "message": "Capture completed, ready for analysis"
    }

@app.post("/api/chat", response_model=TextResponse)
async def chat(request: TextRequest):
    """
    Chat with the agent (text only or text + image).
    
    - **text**: User's text message
    - **image_path**: Optional path to uploaded image (relative to uploads/images/)
    """
    try:
        print(f"[Chat] Received request - text: '{request.text[:100] if request.text else 'None'}...', image_path: {request.image_path}")
        
        agent = get_agent()
        print("[Chat] Agent retrieved successfully")
        
        # Handle image if provided
        image_path = None
        if request.image_path:
            # Try different path formats
            possible_paths = [
                UPLOAD_DIR_IMAGES / request.image_path,
                UPLOAD_DIR / request.image_path,
                Path(request.image_path)  # Absolute path
            ]
            
            for path in possible_paths:
                if path.exists():
                    image_path = str(path)
                    print(f"[Chat] Found image at: {image_path}")
                    break
            
            if not image_path:
                print(f"[Chat] Warning: Image not found. Tried paths: {possible_paths}")
        
        # Get response from agent
        print(f"[Chat] Calling agent.run()...")
        try:
            response = agent.run(request.text, image_path=image_path)
            print(f"[Chat] Agent response received, length: {len(response) if response else 0}")
        except Exception as agent_error:
            print(f"[Chat] Error in agent.run(): {agent_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=f"Agent error: {str(agent_error)}. Check backend logs for details."
            )
        
        # Check if response is empty
        if not response or not response.strip():
            print("[Chat] Warning: Agent returned empty response")
            response = "I received your message but couldn't generate a response. Please try again or check the console for errors."
        
        # Save to conversation history
        try:
            entry = add_conversation_entry(
                user_message=request.text,
                agent_response=response,
                image_path=request.image_path,
                conversation_id=current_conversation_id
            )
            print(f"✅ Conversation saved: {entry.get('id', 'unknown')}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to save conversation: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if saving fails
        
        return TextResponse(response=response)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Chat] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat: {str(e)}. Check backend logs for full traceback."
        )

@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image file for analysis.
    
    Returns the filename that can be used in chat requests.
    """
    try:
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR_IMAGES / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": unique_filename,
            "path": f"images/{unique_filename}",
            "message": "Image uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@app.post("/api/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file for transcription.
    
    Returns the filename that can be used in transcription requests.
    """
    try:
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR_AUDIO / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": unique_filename,
            "path": f"audio/{unique_filename}",
            "message": "Audio uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading audio: {str(e)}")

@app.post("/api/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """
    Generate an image using DALL-E or Imagen.
    
    - **prompt**: Image description
    - **style**: Image style (realistic, sketch, 3d, anime, etc.)
    """
    try:
        from multimodal_tools import generate_image
        
        result = generate_image(request.prompt, request.style)
        
        # Extract image path from result if available
        image_path = None
        image_url = None
        
        # Parse result message to extract file path
        if "Saved to:" in result:
            import re
            match = re.search(r'Saved to: (.+)', result)
            if match:
                image_path = match.group(1)
                # Create URL path
                rel_path = Path(image_path).relative_to(Path(__file__).parent.parent.parent)
                image_url = f"/api/files/{rel_path}"
        
        return ImageGenerationResponse(
            message=result,
            image_path=image_path,
            image_url=image_url
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

@app.post("/api/transcribe-audio", response_model=AudioTranscriptionResponse)
async def transcribe_audio(request: AudioTranscriptionRequest):
    """
    Transcribe an audio file to text.
    
    - **audio_path**: Path to audio file (relative to uploads/audio/)
    - **language**: Optional language code
    """
    try:
        from multimodal_tools import speech_to_text
        
        # Construct full path
        full_audio_path = UPLOAD_DIR_AUDIO / request.audio_path
        if not full_audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        transcript = speech_to_text(str(full_audio_path), language=request.language)
        
        return AudioTranscriptionResponse(transcript=transcript)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

@app.post("/api/text-to-speech", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech audio.
    
    - **text**: Text to convert
    - **voice**: Voice name (alloy, echo, fable, onyx, nova, shimmer for OpenAI)
    """
    try:
        from multimodal_tools import text_to_speech
        
        result = text_to_speech(request.text, voice=request.voice)
        
        # Extract audio path from result if available
        audio_path = None
        audio_url = None
        
        # Parse result message to extract file path
        if "Saved to:" in result:
            import re
            match = re.search(r'Saved to: (.+)', result)
            if match:
                audio_path = match.group(1)
                # Create URL path
                rel_path = Path(audio_path).relative_to(Path(__file__).parent.parent.parent)
                audio_url = f"/api/files/{rel_path}"
        
        return TTSResponse(
            message=result,
            audio_path=audio_path,
            audio_url=audio_url
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.post("/api/chat-with-voice")
async def chat_with_voice(
    audio: UploadFile = File(...),
    generate_audio: str = Form("true")
):
    """
    Complete voice conversation: speech-to-text -> chat -> text-to-speech.
    
    - **audio**: Audio file from microphone
    - **generate_audio**: Whether to generate TTS response (default: True)
    
    Returns both text transcript, agent response, and optional TTS audio.
    """
    try:
        agent = get_agent()
        
        # Save uploaded audio
        file_ext = Path(audio.filename).suffix or ".webm"
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        audio_path = UPLOAD_DIR_AUDIO / unique_filename
        
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Step 1: Transcribe audio
        from multimodal_tools import speech_to_text
        
        print(f"[Voice Chat] Audio saved to: {audio_path}")
        print(f"[Voice Chat] File size: {audio_path.stat().st_size} bytes")
        
        transcript = speech_to_text(str(audio_path))
        
        print(f"[Voice Chat] Transcript result: {transcript[:100] if transcript else 'None'}...")
        
        # Check for errors in transcription
        if not transcript:
            print("[Voice Chat] ERROR: Transcription returned empty result")
            return {
                "error": "Transcription returned empty result. Please check your API keys and try again.",
                "transcript": None,
                "response": None,
                "audio_url": None
            }
        
        if isinstance(transcript, str) and transcript.startswith("❌"):
            print(f"[Voice Chat] ERROR: {transcript}")
            return {
                "error": transcript,  # Return the full error message
                "transcript": None,
                "response": None,
                "audio_url": None
            }
        
        # Step 2: Get agent response
        response = agent.run(transcript)
        
        # Save to conversation history
        try:
            add_conversation_entry(
                user_message=transcript,
                agent_response=response,
                conversation_id=current_conversation_id
            )
        except Exception as e:
            print(f"Warning: Failed to save conversation: {e}")
        
        # Step 3: Generate TTS if requested
        audio_url = None
        generate_audio_bool = generate_audio.lower() in ("true", "1", "yes")
        if generate_audio_bool:
            try:
                from multimodal_tools import text_to_speech
                tts_result = text_to_speech(response, voice="alloy")
                
                print(f"[Voice Chat] TTS result: {tts_result[:200]}...")
                
                # Extract audio URL
                if "Saved to:" in tts_result:
                    import re
                    match = re.search(r'Saved to: (.+)', tts_result)
                    if match:
                        tts_path_str = match.group(1).strip()
                        tts_path = Path(tts_path_str)
                        
                        # Get base directory (agents_development)
                        # backend/main.py -> super_personal_agent/backend/ -> super_personal_agent/ -> agents_development/
                        base_dir = Path(__file__).parent.parent.parent
                        
                        print(f"[Voice Chat] TTS path string: {tts_path_str}")
                        print(f"[Voice Chat] TTS path object: {tts_path}")
                        print(f"[Voice Chat] Base dir: {base_dir}")
                        print(f"[Voice Chat] TTS path is absolute: {tts_path.is_absolute()}")
                        print(f"[Voice Chat] File exists: {tts_path.exists()}")
                        
                        # Convert to relative path
                        try:
                            # Try relative_to if paths are compatible
                            if tts_path.is_absolute() and str(tts_path).startswith(str(base_dir)):
                                rel_path = tts_path.relative_to(base_dir)
                            else:
                                # Extract just the filename and directory name
                                if "generated_audio" in str(tts_path):
                                    # Extract filename
                                    filename = tts_path.name
                                    rel_path = Path("generated_audio") / filename
                                else:
                                    # Fallback: use filename
                                    rel_path = Path("generated_audio") / tts_path.name
                            
                            audio_url = f"/api/files/{rel_path}"
                            print(f"[Voice Chat] Audio URL: {audio_url}")
                            print(f"[Voice Chat] Relative path: {rel_path}")
                            
                            # Verify the file will be accessible
                            full_serve_path = base_dir / rel_path
                            print(f"[Voice Chat] Full serve path: {full_serve_path}")
                            print(f"[Voice Chat] Serve path exists: {full_serve_path.exists()}")
                            
                        except Exception as e:
                            print(f"[Voice Chat] Error constructing path: {e}")
                            # Fallback: use filename only
                            if tts_path.name.startswith("tts_"):
                                audio_url = f"/api/files/generated_audio/{tts_path.name}"
                                print(f"[Voice Chat] Using filename fallback: {audio_url}")
                            else:
                                print(f"[Voice Chat] Could not construct audio URL")
                                audio_url = None
            except Exception as e:
                print(f"Warning: TTS generation failed: {e}")
                import traceback
                traceback.print_exc()
        
        return {
            "transcript": transcript,
            "response": response,
            "audio_url": audio_url,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice chat: {str(e)}")

@app.get("/api/files/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serve generated files (images, audio).
    
    - **file_path**: Relative path to file (e.g., generated_images/image.png)
    """
    try:
        # Construct full path
        base_dir = Path(__file__).parent.parent.parent
        full_path = base_dir / file_path
        
        print(f"[File Serve] Requested path: {file_path}")
        print(f"[File Serve] Base dir: {base_dir}")
        print(f"[File Serve] Full path: {full_path}")
        print(f"[File Serve] File exists: {full_path.exists()}")
        
        # Security check - ensure file is within allowed directories
        allowed_dirs = ["generated_images", "generated_audio"]
        if not any(file_path.startswith(d) for d in allowed_dirs):
            print(f"[File Serve] Access denied - path not in allowed dirs: {file_path}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            print(f"[File Serve] File not found: {full_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Determine content type
        content_type = "application/octet-stream"
        if file_path.endswith(".mp3"):
            content_type = "audio/mpeg"
        elif file_path.endswith(".png") or file_path.endswith(".jpg"):
            content_type = "image/png" if file_path.endswith(".png") else "image/jpeg"
        
        print(f"[File Serve] Serving file with content-type: {content_type}")
        return FileResponse(full_path, media_type=content_type)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[File Serve] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/api/files/uploads/{file_path:path}")
async def serve_uploaded_file(file_path: str):
    """
    Serve uploaded files (images, audio).
    
    - **file_path**: Path relative to uploads/ (e.g., images/abc123.jpg)
    """
    try:
        full_path = UPLOAD_DIR / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(full_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

# Conversation History Endpoints
@app.get("/api/conversations")
async def get_conversations(limit: int = 100, offset: int = 0):
    """
    Get conversation history.
    
    - **limit**: Number of conversations to return (default: 100)
    - **offset**: Number of conversations to skip (default: 0)
    """
    try:
        history = load_history()
        # Return in reverse chronological order (newest first)
        history.reverse()
        total = len(history)
        conversations = history[offset:offset + limit]
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading conversations: {str(e)}")

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation by ID."""
    try:
        history = load_history()
        for entry in history:
            if entry.get("id") == conversation_id:
                return entry
        raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading conversation: {str(e)}")

@app.delete("/api/conversations")
async def clear_conversations():
    """Clear all conversation history."""
    try:
        save_history([])
        return {"message": "All conversations cleared", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversations: {str(e)}")

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a specific conversation."""
    try:
        history = load_history()
        history = [h for h in history if h.get("id") != conversation_id]
        save_history(history)
        return {"message": "Conversation deleted", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """Get conversation statistics."""
    try:
        history = load_history()
        total_conversations = len(history)
        
        # Count unique conversation sessions
        unique_sessions = set()
        for entry in history:
            conv_id = entry.get("conversation_id")
            if conv_id:
                unique_sessions.add(conv_id)
        
        # Count by date
        by_date = {}
        for entry in history:
            date = entry.get("timestamp", "")[:10]  # Get date part
            by_date[date] = by_date.get(date, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "unique_sessions": len(unique_sessions),
            "conversations_by_date": by_date,
            "oldest_conversation": history[0].get("timestamp") if history else None,
            "newest_conversation": history[-1].get("timestamp") if history else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading stats: {str(e)}")

@app.post("/api/new-conversation")
async def new_conversation():
    """Start a new conversation (reset agent history)."""
    try:
        conversation_id = reset_agent_conversation()
        return {
            "message": "New conversation started",
            "conversation_id": conversation_id,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting new conversation: {str(e)}")

@app.get("/api/conversations/sessions")
async def get_conversation_sessions():
    """Get all conversation sessions (grouped conversations)."""
    try:
        history = load_history()
        
        # Group by conversation_id
        sessions = {}
        for entry in history:
            conv_id = entry.get("conversation_id", "unknown")
            if conv_id not in sessions:
                sessions[conv_id] = {
                    "conversation_id": conv_id,
                    "message_count": 0,
                    "first_message": entry.get("timestamp"),
                    "last_message": entry.get("timestamp"),
                    "messages": []
                }
            sessions[conv_id]["message_count"] += 1
            sessions[conv_id]["last_message"] = entry.get("timestamp")
            sessions[conv_id]["messages"].append(entry)
        
        # Convert to list and sort by last message
        sessions_list = list(sessions.values())
        sessions_list.sort(key=lambda x: x["last_message"] or "", reverse=True)
        
        return {
            "total_sessions": len(sessions_list),
            "sessions": sessions_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading sessions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

