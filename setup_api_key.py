#!/usr/bin/env python3
"""
Helper script to set up your Gemini API key.

This script helps you configure your API key for the Google ADK agents.
"""

import os
import sys

def setup_api_key():
    """Interactive script to set up the API key."""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, '.env')
    
    print("🔑 Gemini API Key Setup")
    print("=" * 50)
    print()
    
    # Check if .env exists
    if os.path.exists(env_file):
        print(f"✅ Found .env file at: {env_file}")
        
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check if API key is already set (not placeholder)
        if 'GEMINI_API_KEY=' in content:
            lines = content.split('\n')
            for line in lines:
                if line.startswith('GEMINI_API_KEY='):
                    current_key = line.split('=', 1)[1].strip()
                    if current_key and current_key != 'your_api_key_here':
                        print(f"⚠️  API key is already set (starts with: {current_key[:4]}...)")
                        response = input("Do you want to update it? (y/n): ").strip().lower()
                        if response != 'y':
                            print("Keeping existing API key.")
                            return
                    break
    else:
        print(f"📝 Creating new .env file at: {env_file}")
    
    print()
    print("To get your API key:")
    print("1. Visit: https://aistudio.google.com/")
    print("2. Sign in with your Google account")
    print("3. Click 'Get API Key'")
    print("4. Copy your API key")
    print()
    
    api_key = input("Paste your Gemini API key here: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    # Validate format (Gemini keys typically start with "AIza")
    if not api_key.startswith("AIza"):
        print("⚠️  Warning: API key format looks unusual.")
        print("Gemini API keys typically start with 'AIza'")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return
    
    # Update or create .env file
    env_content = f"""# Google Gemini API Key
# Get your API key from: https://aistudio.google.com/
GEMINI_API_KEY={api_key}

# Optional: Model configuration
GEMINI_MODEL=gemini-2.0-flash-exp

# Optional: Project settings
PROJECT_NAME=interview_prep_agent
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print()
        print("✅ API key saved successfully!")
        print(f"   Location: {env_file}")
        print()
        print("You can now run the agents:")
        print("  python examples/simple_agent.py")
        print()
        
    except Exception as e:
        print(f"❌ Error saving API key: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_api_key()

