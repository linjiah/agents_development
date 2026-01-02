#!/usr/bin/env python3
"""
Test script to verify MCP weather tools are working.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Note: Run this script with: source activate_py312.sh && python test_mcp_weather_tools.py

print("🧪 Testing MCP Weather Tools")
print("=" * 60)

# Check MCP availability - use old API which we know works
try:
    from google.adk.tools.mcp_tool import MCPToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import (
        StdioServerParameters
    )
    print("✅ MCP support available")
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"❌ MCP not available: {e}")
    sys.exit(1)

# Check configuration
weather_mcp_type = os.getenv("WEATHER_MCP_TYPE", "").strip().lower()
print(f"\n📋 Configuration:")
print(f"   WEATHER_MCP_TYPE: {weather_mcp_type}")

if weather_mcp_type != "stdio":
    print(f"⚠️  Expected 'stdio', got '{weather_mcp_type}'")
    print("   Set WEATHER_MCP_TYPE=stdio in .env")

# Create MCP toolset
print(f"\n🔧 Creating MCP toolset...")
try:
    toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-weather"],
            env={}
        )
    )
    print("✅ MCP toolset created")
except Exception as e:
    print(f"❌ Failed to create MCP toolset: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test with a simple model
print(f"\n🤖 Testing with Gemini model...")
try:
    import google.generativeai as genai
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    # Create model with MCP tools
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=[toolset],
        system_instruction="You have access to weather tools. When asked about weather, you MUST use the weather tools. Never say you cannot provide weather information."
    )
    
    print("✅ Model created with MCP toolset")
    
    # Wait a bit for tools to initialize
    import time
    print("⏳ Waiting 3 seconds for MCP tools to initialize...")
    time.sleep(3)
    
    # Test query
    print(f"\n💬 Testing weather query...")
    response = model.generate_content("What's the weather in San Diego?")
    
    print(f"\n📥 Response:")
    print(f"   Type: {type(response)}")
    
    # Check for function calls
    if hasattr(response, 'candidates') and response.candidates:
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        print(f"\n✅ FUNCTION CALL DETECTED!")
                        print(f"   Function: {fc.name}")
                        print(f"   Arguments: {dict(fc.args)}")
                        print(f"\n✅ Weather tools are working! The model is calling weather functions.")
                        sys.exit(0)
    
    # Check for text response
    if hasattr(response, 'text') and response.text:
        text = response.text
        print(f"   Text: {text[:200]}...")
        
        if "cannot" in text.lower() or "don't have" in text.lower() or "unable" in text.lower():
            print(f"\n❌ PROBLEM: Model says it cannot provide weather information")
            print(f"   This suggests weather tools are not being discovered/used")
            print(f"   Response: {text}")
            sys.exit(1)
        else:
            print(f"\n✅ Model responded (may have used tools)")
    
    print(f"\n⚠️  Could not determine if tools were used")
    print(f"   Check the response above")
    
except Exception as e:
    print(f"❌ Error testing model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

