#!/usr/bin/env python3
"""
Quick test script to verify weather MCP setup for Orel agent.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()

print("🧪 Testing Weather MCP Setup for Orel")
print("=" * 60)

# Check Python version
python_version = sys.version_info
print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
if python_version < (3, 10):
    print("❌ ERROR: MCP requires Python 3.10+")
    sys.exit(1)

# Check MCP availability
print("\n1. Checking MCP support...")
try:
    from google.adk.tools.mcp_tool import MCPToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import (
        SseServerParams,
        StreamableHTTPServerParams,
        StdioServerParameters
    )
    print("✅ MCP support: Available")
except ImportError as e:
    print(f"❌ MCP not available: {e}")
    print("   Install: pip install google-adk")
    sys.exit(1)

# Check npx availability
print("\n2. Checking npx (for stdio weather server)...")
import shutil
npx_path = shutil.which("npx")
if npx_path:
    print(f"✅ npx found: {npx_path}")
    # Try to get version
    import subprocess
    try:
        result = subprocess.run(["npx", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   Version: {result.stdout.strip()}")
    except:
        pass
else:
    print("⚠️  npx not found - install Node.js for stdio weather MCP server")
    print("   Download: https://nodejs.org/")

# Check environment configuration
print("\n3. Checking environment configuration...")
weather_mcp_type = os.getenv("WEATHER_MCP_TYPE", "").strip().lower()
if weather_mcp_type:
    print(f"✅ WEATHER_MCP_TYPE: {weather_mcp_type}")
    
    if weather_mcp_type == "stdio":
        print("   Configuration: stdio-based weather MCP server")
        print("   Will use: npx -y @modelcontextprotocol/server-weather")
    elif weather_mcp_type == "sse":
        weather_url = os.getenv("WEATHER_MCP_URL", "http://localhost:8001/sse")
        print(f"   Configuration: SSE-based weather MCP server")
        print(f"   URL: {weather_url}")
    elif weather_mcp_type == "http":
        weather_url = os.getenv("WEATHER_MCP_URL", "https://api.example.com/mcp/")
        print(f"   Configuration: HTTP-based weather MCP server")
        print(f"   URL: {weather_url}")
else:
    print("⚠️  WEATHER_MCP_TYPE not set in .env")
    print("   To enable weather MCP, add to .env:")
    print("   WEATHER_MCP_TYPE=stdio")

# Test weather MCP server creation (if stdio)
if weather_mcp_type == "stdio" and npx_path:
    print("\n4. Testing weather MCP server creation...")
    try:
        from examples.multimodal_agent import create_mcp_toolset_stdio
        weather_toolset = create_mcp_toolset_stdio(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-weather"],
            env={}
        )
        print("✅ Weather MCP toolset created successfully!")
        print("   Note: The server will start when the agent initializes")
    except Exception as e:
        print(f"⚠️  Could not create weather MCP toolset: {e}")
        print("   This is okay - the server will be created when needed")

# Summary
print("\n" + "=" * 60)
print("📋 Setup Summary:")
print(f"   Python: {python_version.major}.{python_version.minor}.{python_version.micro} ✅")
print(f"   MCP Support: {'✅ Available' if 'MCPToolset' in dir() else '❌ Not available'}")
print(f"   npx: {'✅ Available' if npx_path else '⚠️  Not found'}")
print(f"   Weather MCP Config: {'✅ Set' if weather_mcp_type else '⚠️  Not set'}")

if weather_mcp_type == "stdio" and npx_path:
    print("\n✅ Ready to use weather MCP!")
    print("   Restart your backend server to activate weather MCP tools.")
    print("   Then ask Orel: 'What's the weather in San Francisco?'")
elif weather_mcp_type:
    print(f"\n✅ Weather MCP configured ({weather_mcp_type})")
    print("   Make sure your MCP server is running before using it.")
else:
    print("\n⚠️  Weather MCP not configured")
    print("   Add WEATHER_MCP_TYPE=stdio to .env to enable it.")

print("\n" + "=" * 60)

