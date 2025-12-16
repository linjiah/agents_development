"""
Speech-to-Text Implementation

Supports multiple STT providers:
1. OpenAI Whisper API (default, easiest)
2. Google Speech-to-Text
3. Local Whisper (for privacy)
"""

import os
import sys
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def speech_to_text_whisper(audio_path: str, language: Optional[str] = None) -> str:
    """Transcribe audio using OpenAI Whisper API."""
    try:
        import openai
    except ImportError:
        return (
            "❌ Whisper requires openai library.\n"
            "Install with: pip install openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "❌ OPENAI_API_KEY not set.\n"
            "Get your key from: https://platform.openai.com/api-keys"
        )
    
    if not os.path.exists(audio_path):
        return f"❌ Error: Audio file not found: {audio_path}"
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,  # Optional: "en", "es", "fr", etc.
                response_format="text"
            )
        
        return transcript
        
    except Exception as e:
        return f"❌ Error transcribing audio: {str(e)}"

def speech_to_text_google(audio_path: str, language: str = "en-US") -> str:
    """Transcribe audio using Google Speech-to-Text API."""
    try:
        from google.cloud import speech
    except ImportError:
        return (
            "❌ Google Speech-to-Text requires google-cloud-speech library.\n"
            "Install with: pip install google-cloud-speech"
        )
    
    if not os.path.exists(audio_path):
        return f"❌ Error: Audio file not found: {audio_path}"
    
    try:
        client = speech.SpeechClient()
        
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language,
        )
        
        response = client.recognize(config=config, audio=audio)
        
        if response.results:
            return response.results[0].alternatives[0].transcript
        else:
            return "❌ No transcription results found."
        
    except Exception as e:
        return f"❌ Error transcribing with Google STT: {str(e)}"

def speech_to_text(audio_path: str, provider: str = "auto", language: Optional[str] = None) -> str:
    """
    Transcribe an audio file to text.
    
    Args:
        audio_path: Path to audio file (local file path)
        provider: STT provider ("whisper", "google", or "auto")
        language: Language code (optional, e.g., "en", "es", "fr")
    
    Returns:
        Transcribed text
    
    Examples:
        >>> speech_to_text("recording.mp3")
        "Hello, this is a transcription..."
    """
    # Auto-select provider
    # Priority: Google Speech-to-Text first (for consistency with Google ADK), then OpenAI
    if provider == "auto":
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            provider = "google"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "whisper"
        else:
            return (
                "❌ No speech-to-text API key found.\n"
                "Please set one of:\n"
                "- GOOGLE_APPLICATION_CREDENTIALS (for Google STT - recommended for Google ADK)\n"
                "- OPENAI_API_KEY (for Whisper)\n"
                "\n"
                "Recommended: Use Google Speech-to-Text for consistency with Google ADK:\n"
                "1. Set up Google Cloud Project\n"
                "2. Enable Speech-to-Text API\n"
                "3. Set GOOGLE_APPLICATION_CREDENTIALS\n"
                "\n"
                "Alternative: Use Whisper for easier setup:\n"
                "1. Get key from https://platform.openai.com/api-keys\n"
                "2. Set OPENAI_API_KEY in your .env file"
            )
    
    # Route to appropriate provider
    if provider == "whisper":
        return speech_to_text_whisper(audio_path, language)
    elif provider == "google":
        return speech_to_text_google(audio_path, language or "en-US")
    else:
        return f"❌ Unknown provider: {provider}. Use 'whisper' or 'google'"

