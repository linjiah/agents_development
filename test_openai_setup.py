"""
Quick test script to verify OpenAI setup for multimodal agent.

Run this to check if your OpenAI API key is configured correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()

print("=" * 60)
print("OpenAI Setup Verification")
print("=" * 60)
print()

# Check API keys
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

print("📋 API Keys Status:")
print(f"   GEMINI_API_KEY: {'✅ Set' if gemini_key and gemini_key != 'your_api_key_here' else '❌ Not set'}")
print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
print()

# Check required libraries
print("📦 Required Libraries:")
try:
    import google.generativeai
    print("   ✅ google-generativeai")
except ImportError:
    print("   ❌ google-generativeai (install: pip install google-generativeai)")

try:
    import openai
    print("   ✅ openai")
except ImportError:
    print("   ❌ openai (install: pip install openai)")

try:
    from PIL import Image
    print("   ✅ Pillow")
except ImportError:
    print("   ❌ Pillow (install: pip install Pillow)")

print()

# Check multimodal tools
print("🔧 Multimodal Tools:")
try:
    from multimodal_tools import generate_image, analyze_image, speech_to_text, text_to_speech
    print("   ✅ multimodal_tools package")
except ImportError as e:
    print(f"   ❌ multimodal_tools package: {e}")

print()

# Summary
print("=" * 60)
print("Summary:")
print("=" * 60)

if gemini_key and gemini_key != 'your_api_key_here':
    print("✅ Image Analysis: Ready (Gemini vision)")
else:
    print("❌ Image Analysis: Need GEMINI_API_KEY")

if openai_key:
    print("✅ Image Generation: Ready (DALL-E)")
    print("✅ Speech-to-Text: Ready (Whisper)")
    print("✅ Text-to-Speech: Ready (OpenAI TTS)")
else:
    print("❌ Image Generation: Need OPENAI_API_KEY")
    print("❌ Speech-to-Text: Need OPENAI_API_KEY")
    print("❌ Text-to-Speech: Need OPENAI_API_KEY")

print()

if openai_key and gemini_key and gemini_key != 'your_api_key_here':
    print("🎉 All set! You can run: python examples/multimodal_agent.py")
else:
    print("⚠️  Setup incomplete. See OPENAI_SETUP_QUICKSTART.md for instructions.")

print("=" * 60)

