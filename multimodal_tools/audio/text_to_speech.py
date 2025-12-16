"""
Text-to-Speech Implementation

Supports multiple TTS providers:
1. OpenAI TTS API (default, easiest, high quality)
2. Google Text-to-Speech
3. ElevenLabs (premium quality, optional)
"""

import os
import sys
import hashlib
from typing import Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Create output directory for generated audio
OUTPUT_DIR = Path(__file__).parent.parent.parent / "generated_audio"
OUTPUT_DIR.mkdir(exist_ok=True)

def text_to_speech_openai(text: str, voice: str = "alloy") -> str:
    """Generate speech using OpenAI TTS API."""
    try:
        import openai
    except ImportError:
        return (
            "❌ OpenAI TTS requires openai library.\n"
            "Install with: pip install openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "❌ OPENAI_API_KEY not set.\n"
            "Get your key from: https://platform.openai.com/api-keys"
        )
    
    # Valid voices: alloy, echo, fable, onyx, nova, shimmer
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if voice not in valid_voices:
        voice = "alloy"
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice=voice,
            input=text
        )
        
        # Generate filename
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        filename = f"tts_{text_hash}_{voice}.mp3"
        filepath = OUTPUT_DIR / filename
        
        # Save audio file
        response.stream_to_file(filepath)
        
        return (
            f"✅ Audio generated successfully!\n"
            f"- Text: {text[:50]}...\n"
            f"- Voice: {voice}\n"
            f"- Saved to: {filepath}"
        )
        
    except Exception as e:
        return f"❌ Error generating speech: {str(e)}"

def text_to_speech_google(text: str, voice: str = "en-US-Standard-D") -> str:
    """Generate speech using Google Text-to-Speech API."""
    try:
        from google.cloud import texttospeech
    except ImportError:
        return (
            "❌ Google TTS requires google-cloud-texttospeech library.\n"
            "Install with: pip install google-cloud-texttospeech"
        )
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_config = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config
        )
        
        # Generate filename
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        filename = f"tts_google_{text_hash}.mp3"
        filepath = OUTPUT_DIR / filename
        
        # Save audio file
        with open(filepath, "wb") as out:
            out.write(response.audio_content)
        
        return (
            f"✅ Audio generated successfully!\n"
            f"- Text: {text[:50]}...\n"
            f"- Voice: {voice}\n"
            f"- Saved to: {filepath}"
        )
        
    except Exception as e:
        return f"❌ Error generating speech with Google TTS: {str(e)}"

def text_to_speech(text: str, voice: str = "default", provider: str = "auto") -> str:
    """
    Generate speech audio from text.
    
    Args:
        text: Text to convert to speech
        voice: Voice name/style
            - For OpenAI: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
            - For Google: "en-US-Standard-D", "en-US-Wavenet-F", etc.
        provider: TTS provider ("openai", "google", or "auto")
    
    Returns:
        Result message with audio file location
    
    Examples:
        >>> text_to_speech("Hello, how are you?", "alloy")
        "✅ Audio generated successfully!..."
    """
    # Auto-select provider
    # Priority: Google TTS first (for consistency with Google ADK), then OpenAI
    if provider == "auto":
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            provider = "google"
            if voice == "default":
                voice = "en-US-Standard-D"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
            if voice == "default":
                voice = "alloy"
        else:
            return (
                "❌ No text-to-speech API key found.\n"
                "Please set one of:\n"
                "- GOOGLE_APPLICATION_CREDENTIALS (for Google TTS - recommended for Google ADK)\n"
                "- OPENAI_API_KEY (for OpenAI TTS)\n"
                "\n"
                "Recommended: Use Google Text-to-Speech for consistency with Google ADK:\n"
                "1. Set up Google Cloud Project\n"
                "2. Enable Text-to-Speech API\n"
                "3. Set GOOGLE_APPLICATION_CREDENTIALS\n"
                "\n"
                "Alternative: Use OpenAI TTS for easier setup:\n"
                "1. Get key from https://platform.openai.com/api-keys\n"
                "2. Set OPENAI_API_KEY in your .env file"
            )
    
    # Route to appropriate provider
    if provider == "openai":
        return text_to_speech_openai(text, voice)
    elif provider == "google":
        return text_to_speech_google(text, voice)
    else:
        return f"❌ Unknown provider: {provider}. Use 'openai' or 'google'"

