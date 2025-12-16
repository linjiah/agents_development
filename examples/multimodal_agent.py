"""
Multimodal Agent Example using Google ADK

This agent is a fully functional multimodal personal assistant with:
- Text: normal Q&A
- Image Analysis: analyze uploaded images using Gemini vision
- Image Generation: generate images using DALL-E (or other APIs)
- Figures/Diagrams: generate Mermaid diagrams
- Speech-to-Text: transcribe audio files using Whisper
- Text-to-Speech: generate speech audio using OpenAI TTS

Features:
- Real image generation (DALL-E integration)
- Real image analysis (Gemini vision)
- Real audio processing (Whisper + OpenAI TTS)
- Image/audio upload support in interactive mode
- Multimodal input (text + image together)
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Compatibility fixes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

import google.generativeai as genai

# Load env
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("❌ ERROR: GEMINI_API_KEY not set. Get your key from: https://aistudio.google.com/")
    sys.exit(1)

genai.configure(api_key=api_key)

# ----------------------------
# Import real tool implementations
# ----------------------------

try:
    from multimodal_tools import (
        generate_image,
        analyze_image,
        generate_figure,
        speech_to_text,
        text_to_speech
    )
    REAL_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import multimodal tools: {e}")
    print("   Using placeholder implementations...")
    REAL_TOOLS_AVAILABLE = False
    
    # Fallback placeholder implementations
    def generate_image(prompt: str, style: str = "realistic") -> str:
        return f"[Image Generation Placeholder]\nPrompt: {prompt}\nStyle: {style}"
    
    def analyze_image(image_path: str, question: Optional[str] = None) -> str:
        return f"[Image Analysis Placeholder]\nImage: {image_path}\nQuestion: {question}"
    
    def generate_figure(description: str, format: str = "mermaid") -> str:
        return f"[Figure Placeholder]\nDescription: {description}"
    
    def speech_to_text(audio_path: str) -> str:
        return f"[Speech-to-Text Placeholder]\nAudio: {audio_path}"
    
    def text_to_speech(text: str, voice: str = "default") -> str:
        return f"[Text-to-Speech Placeholder]\nText: {text}"

# ----------------------------
# Tool definitions (function calling)
# ----------------------------

TOOLS = [
    {
        "function_declarations": [
            {
                "name": "analyze_image",
                "description": "Analyze an uploaded image. Can describe the image, extract text (OCR), identify objects, answer questions about the image, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string", "description": "Path to the image file (local file path)"},
                        "question": {"type": "string", "description": "Optional question about the image. If not provided, provides a general description."}
                    },
                    "required": ["image_path"]
                }
            },
            {
                "name": "generate_image",
                "description": "Generate an image based on a prompt and style using DALL-E or other image generation APIs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Image description/prompt"},
                        "style": {"type": "string", "description": "Style (e.g., realistic, sketch, 3d, anime, oil painting, watercolor)"}
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "generate_figure",
                "description": "Generate a figure/diagram (Mermaid or ASCII). Use for flowcharts, sequence diagrams, class diagrams, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "What to visualize"},
                        "format": {"type": "string", "description": "Format: mermaid or ascii"},
                        "diagram_type": {"type": "string", "description": "Type of diagram: flowchart, sequence, or class"}
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "speech_to_text",
                "description": "Transcribe an audio file to text using Whisper or Google Speech-to-Text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "audio_path": {"type": "string", "description": "Path to audio file (local file path)"},
                        "language": {"type": "string", "description": "Optional language code (e.g., 'en', 'es', 'fr')"}
                    },
                    "required": ["audio_path"]
                }
            },
            {
                "name": "text_to_speech",
                "description": "Generate speech audio from text using OpenAI TTS or Google TTS.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to convert to speech"},
                        "voice": {"type": "string", "description": "Voice name (for OpenAI: alloy, echo, fable, onyx, nova, shimmer)"}
                    },
                    "required": ["text"]
                }
            }
        ]
    }
]

TOOL_FUNCTIONS = {
    "analyze_image": analyze_image,
    "generate_image": generate_image,
    "generate_figure": generate_figure,
    "speech_to_text": speech_to_text,
    "text_to_speech": text_to_speech,
}

# ----------------------------
# Agent implementation
# ----------------------------

SYSTEM_INSTRUCTION = """You are a multimodal personal assistant with real capabilities:

**Text**: Answer questions, explain concepts, summarize information.

**Image Analysis**: Use analyze_image to analyze uploaded images. You can:
- Describe what's in the image
- Extract text from images (OCR)
- Answer questions about the image
- Identify objects, people, scenes

**Image Generation**: Use generate_image to create images from text prompts. Supports various styles.

**Diagrams**: Use generate_figure to create flowcharts, sequence diagrams, class diagrams, etc. in Mermaid format.

**Audio Processing**:
- Use speech_to_text to transcribe audio files
- Use text_to_speech to convert text to speech audio

**Guidelines**:
- When user uploads an image, use analyze_image to understand it
- When user asks for an image, use generate_image
- When user asks for a diagram/flowchart, use generate_figure
- When user provides audio, use speech_to_text
- When user wants text spoken, use text_to_speech
- Be clear about what you're doing and what capabilities you're using
"""

class MultimodalAgent:
    def __init__(self, model_name: str = None):
        # Model fallback list (most available first)
        fallback_models = [
            model_name or os.getenv("GEMINI_MODEL", "").strip() or "gemini-pro",
            "gemini-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        self.history = []

        last_error = None
        self.model = None
        tried = []
        for m in fallback_models:
            if not m:
                continue
            tried.append(m)
            try:
                self.model = genai.GenerativeModel(
                    model_name=m,
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=TOOLS
                )
                if m != fallback_models[0]:
                    print(f"ℹ️ Using fallback model: {m}")
                break
            except Exception as e:
                last_error = e
                continue

        if not self.model:
            raise RuntimeError(f"Could not initialize model. Tried: {tried}. Last error: {last_error}")

    def run(self, user_input: str, image_path: Optional[str] = None) -> str:
        """
        Process user input, optionally with an image.
        
        Args:
            user_input: Text input from user
            image_path: Optional path to image file for multimodal input
        """
        # Handle multimodal input (text + image)
        if image_path and os.path.exists(image_path):
            try:
                from PIL import Image
                img = Image.open(image_path)
                # Gemini can handle multimodal input natively!
                self.history.append({"role": "user", "parts": [user_input, img]})
            except Exception as e:
                # If image loading fails, fall back to text only
                self.history.append({"role": "user", "parts": [f"{user_input}\n[Note: Could not load image: {e}]"]})
        else:
            self.history.append({"role": "user", "parts": [user_input]})
        
        response = self.model.generate_content(self.history)

        # Handle function calls
        fc = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                break

        if fc:
            fn = fc.name
            args = dict(fc.args)
            if fn in TOOL_FUNCTIONS:
                # Add defaults
                if fn == "generate_image" and "style" not in args:
                    args["style"] = "realistic"
                if fn == "generate_figure" and "format" not in args:
                    args["format"] = "mermaid"
                if fn == "text_to_speech" and "voice" not in args:
                    args["voice"] = "default"

                tool_result = TOOL_FUNCTIONS[fn](**args)

                # Extend history with function call and result
                self.history.append({"role": "model", "parts": [{"function_call": fc}]})
                self.history.append({"role": "function", "parts": [{"function_response": {"name": fn, "response": {"result": tool_result}}}]})

                final_response = self.model.generate_content(self.history)
                final_text = final_response.text if hasattr(final_response, "text") else str(final_response)
                self.history.append({"role": "model", "parts": [final_text]})
                return final_text

        # No function call; normal text response
        text = response.text if hasattr(response, "text") else str(response)
        self.history.append({"role": "model", "parts": [text]})
        return text


def run_multimodal_interactive():
    agent = MultimodalAgent()
    print("🎨 Multimodal Personal Assistant")
    print("=" * 60)
    print("Capabilities:")
    print("  ✅ Text: Q&A, explanations, summaries")
    print("  ✅ Image Analysis: Analyze uploaded images (Gemini vision)")
    print("  ✅ Image Generation: Generate images (DALL-E)")
    print("  ✅ Diagrams: Mermaid flowcharts, sequence diagrams")
    print("  ✅ Speech-to-Text: Transcribe audio (Whisper)")
    print("  ✅ Text-to-Speech: Generate speech audio (OpenAI TTS)")
    print("\nCommands:")
    print("  - Type normally for text queries")
    print("  - Type 'image: <path>' to analyze an image")
    print("  - Type 'audio: <path>' to transcribe audio")
    print("  - Type 'quit' or 'exit' to end")
    print("=" * 60)
    print()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nGoodbye!")
            break
        if not user_input:
            continue

        try:
            # Handle special commands
            image_path = None
            audio_path = None
            
            if user_input.startswith("image: "):
                image_path = user_input[7:].strip()
                if os.path.exists(image_path):
                    question = input("Question about image (or press Enter for general description): ").strip()
                    if question:
                        result = agent.run(question, image_path=image_path)
                    else:
                        result = agent.run("Describe this image in detail.", image_path=image_path)
                else:
                    result = f"❌ Image file not found: {image_path}"
            elif user_input.startswith("audio: "):
                audio_path = user_input[7:].strip()
                if os.path.exists(audio_path):
                    # Transcribe audio first
                    transcript = speech_to_text(audio_path)
                    print(f"\n📝 Audio Transcript: {transcript}\n")
                    # Then process the transcript
                    follow_up = input("What would you like to do with this transcript? (or press Enter to continue): ").strip()
                    if follow_up:
                        result = agent.run(f"{follow_up}\n\nContext from audio: {transcript}")
                    else:
                        result = f"Audio transcribed successfully:\n{transcript}"
                else:
                    result = f"❌ Audio file not found: {audio_path}"
            else:
                # Normal text input
                result = agent.run(user_input)
            
            print(f"\nAgent: {result}\n")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            if os.getenv("DEBUG"):
                traceback.print_exc()


if __name__ == "__main__":
    run_multimodal_interactive()

