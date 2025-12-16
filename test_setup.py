#!/usr/bin/env python3
"""
Quick test script to verify your Google ADK setup is working correctly.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

from dotenv import load_dotenv
import google.generativeai as genai

def test_setup():
    """Test if the setup is working correctly."""
    
    print("🧪 Testing Google ADK Setup")
    print("=" * 50)
    print()
    
    # Test 1: Check .env file
    print("1. Checking .env file...")
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        print(f"   ✅ Found .env file at: {env_path}")
    else:
        print(f"   ❌ .env file not found at: {env_path}")
        return False
    
    # Test 2: Load environment variables
    print("\n2. Loading environment variables...")
    load_dotenv(dotenv_path=env_path)
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("   ❌ GEMINI_API_KEY not found in environment")
        return False
    
    if api_key == "your_api_key_here" or api_key.strip() == "":
        print("   ❌ GEMINI_API_KEY is still set to placeholder value")
        return False
    
    print(f"   ✅ API key found (starts with: {api_key[:4]}...)")
    
    # Test 3: Configure Gemini API
    print("\n3. Configuring Gemini API...")
    try:
        genai.configure(api_key=api_key)
        print("   ✅ Gemini API configured successfully")
    except Exception as e:
        print(f"   ❌ Failed to configure Gemini API: {str(e)}")
        return False
    
    # Test 4: Test API connection with a simple query
    print("\n4. Testing API connection...")
    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
        response = model.generate_content("Say 'Hello' in one word.")
        
        if response and response.text:
            print(f"   ✅ API connection successful!")
            print(f"   Response: {response.text.strip()}")
            return True
        else:
            print("   ⚠️  API responded but no text returned")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "API_KEY" in error_msg:
            print(f"   ❌ API key error: {error_msg}")
            print("   💡 Your API key may be invalid or expired")
            print("   💡 Get a new key from: https://aistudio.google.com/")
        else:
            print(f"   ❌ API connection failed: {error_msg}")
        return False

if __name__ == "__main__":
    success = test_setup()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Your setup is working correctly.")
        print("\nYou can now run:")
        print("  python examples/simple_agent.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

