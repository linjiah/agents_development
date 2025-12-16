"""
Utility script to list available Gemini models.
"""

import os
import sys
from dotenv import load_dotenv

# Setup compatibility
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

import google.generativeai as genai

def list_available_models():
    """List all available Gemini models."""
    
    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=env_path)
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ GEMINI_API_KEY not set. Please set it in .env file.")
        return
    
    genai.configure(api_key=api_key)
    
    print("🔍 Listing available Gemini models...")
    print("=" * 50)
    
    try:
        models = genai.list_models()
        
        print("\nAvailable models:")
        print("-" * 50)
        
        for model in models:
            # Filter for generation models
            if 'generateContent' in model.supported_generation_methods:
                print(f"\n📌 {model.name}")
                print(f"   Display Name: {model.display_name}")
                print(f"   Description: {model.description}")
                print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
        
        print("\n" + "=" * 50)
        print("\n💡 Recommended model names to use:")
        print("   - 'gemini-pro' (if available)")
        print("   - 'gemini-1.5-pro' (if available)")
        print("   - 'gemini-1.5-flash' (if available)")
        print("\nUse the 'name' field (without 'models/' prefix) in your code.")
        
    except Exception as e:
        print(f"❌ Error listing models: {str(e)}")
        print("\nTrying common model names...")
        
        # Try common model names
        common_models = [
            "gemini-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash-exp",
        ]
        
        print("\nCommon model names to try:")
        for model_name in common_models:
            try:
                model = genai.GenerativeModel(model_name=model_name)
                print(f"   ✅ {model_name} - Available")
            except Exception as e:
                print(f"   ❌ {model_name} - Not available: {str(e)[:50]}")

if __name__ == "__main__":
    list_available_models()

