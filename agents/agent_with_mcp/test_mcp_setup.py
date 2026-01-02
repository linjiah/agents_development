#!/usr/bin/env python3
"""
Test script to verify MCP setup is working correctly.

This script tests:
1. Environment variables are set
2. MCP server can start and connect
3. Tools are discoverable
4. Tool execution works
5. Full agent integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for .env loading
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to load from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print("✅ Loaded .env file")
except ImportError:
    print("ℹ️  python-dotenv not installed, using environment variables only")
except Exception as e:
    print(f"⚠️  Could not load .env: {e}")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
WEATHER_SERVER_PATH = SCRIPT_DIR / "weather_server.py"


def test_environment_variables():
    """Test 1: Check if required environment variables are set"""
    print("\n" + "="*60)
    print("TEST 1: Environment Variables")
    print("="*60)
    
    # Check Gemini API key
    gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ GOOGLE_GEMINI_API_KEY/GEMINI_API_KEY: {gemini_key[:10]}...{gemini_key[-4:]}")
    else:
        print("❌ GOOGLE_GEMINI_API_KEY or GEMINI_API_KEY not set!")
        return False
    
    # Check OpenWeatherMap API key
    weather_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if weather_key and weather_key != "your-openweathermap-api-key-here":
        print(f"✅ OPENWEATHERMAP_API_KEY: {weather_key[:10]}...{weather_key[-4:]}")
    else:
        print("❌ OPENWEATHERMAP_API_KEY not set or still has placeholder value!")
        return False
    
    return True


async def test_mcp_connection():
    """Test 2: Test MCP server connection and tool discovery"""
    print("\n" + "="*60)
    print("TEST 2: MCP Server Connection & Tool Discovery")
    print("="*60)
    
    server_params = StdioServerParameters(
        command="python",
        args=[str(WEATHER_SERVER_PATH)]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ MCP server connection established")
                
                # List available tools
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"✅ Found {len(tools)} tool(s):")
                for tool in tools:
                    print(f"   - {tool.name}: {tool.description or 'No description'}")
                
                return True, session
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_tool_execution(session):
    """Test 3: Test tool execution"""
    print("\n" + "="*60)
    print("TEST 3: Tool Execution")
    print("="*60)
    
    if not session:
        print("❌ No session available, skipping tool execution test")
        return False
    
    try:
        # Test the get_weather tool with a known location
        test_location = "London,uk"
        print(f"🔧 Testing get_weather tool with location: {test_location}")
        
        result = await session.call_tool("get_weather", {"location": test_location})
        
        if result.content:
            content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            print(f"✅ Tool executed successfully!")
            print(f"   Result: {content[:200]}...")  # Show first 200 chars
            
            # Check if result contains error
            if "error" in content.lower():
                print(f"⚠️  Tool returned an error: {content}")
                return False
            else:
                return True
        else:
            print("❌ Tool returned no content")
            return False
            
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_langchain_integration():
    """Test 4: Test LangChain MCP adapter integration"""
    print("\n" + "="*60)
    print("TEST 4: LangChain MCP Adapter")
    print("="*60)
    
    try:
        from langchain_mcp_adapters.tools import load_mcp_tools
        print("✅ langchain_mcp_adapters imported successfully")
        
        # Test loading tools
        server_params = StdioServerParameters(
            command="python",
            args=[str(WEATHER_SERVER_PATH)]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await load_mcp_tools(session)
                print(f"✅ Loaded {len(tools)} tool(s) via langchain_mcp_adapters")
                
                for tool in tools:
                    print(f"   - {tool.name}: {tool.description or 'No description'}")
                
                return True
                
    except ImportError as e:
        print(f"❌ langchain_mcp_adapters not installed: {e}")
        print("   Install with: pip install langchain-mcp-adapters")
        return False
    except Exception as e:
        print(f"❌ Failed to load tools via langchain_mcp_adapters: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_agent():
    """Test 5: Test full agent (quick test)"""
    print("\n" + "="*60)
    print("TEST 5: Full Agent Integration (Quick Test)")
    print("="*60)
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        from langchain_mcp_adapters.tools import load_mcp_tools
        
        print("✅ All required imports successful")
        
        # This is a quick test - we won't actually run the full agent
        # but we'll verify all components are available
        gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if gemini_key:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0,
                google_api_key=gemini_key
            )
            print("✅ LangChain Gemini LLM initialized")
        else:
            print("❌ Cannot initialize LLM - API key missing")
            return False
        
        print("✅ All components ready for full agent test")
        print("   Run 'python mcp_client.py' to test the full agent interactively")
        
        return True
        
    except Exception as e:
        print(f"❌ Full agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 MCP Setup Verification Tests")
    print("="*60)
    
    results = {}
    
    # Test 1: Environment variables
    results['env'] = test_environment_variables()
    if not results['env']:
        print("\n❌ Environment variables test failed. Please set up your API keys first.")
        return
    
    # Test 2: MCP connection
    success, session = await test_mcp_connection()
    results['connection'] = success
    
    # Test 3: Tool execution
    if success:
        results['tool_exec'] = await test_tool_execution(session)
    else:
        results['tool_exec'] = False
    
    # Test 4: LangChain integration
    results['langchain'] = await test_langchain_integration()
    
    # Test 5: Full agent
    results['agent'] = await test_full_agent()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    test_names = {
        'env': 'Environment Variables',
        'connection': 'MCP Server Connection',
        'tool_exec': 'Tool Execution',
        'langchain': 'LangChain Integration',
        'agent': 'Full Agent Components'
    }
    
    for key, name in test_names.items():
        status = "✅ PASS" if results.get(key) else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Your MCP setup is working correctly.")
        print("\n🚀 Next step: Run the agent with:")
        print("   python mcp_client.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("   See SETUP.md for detailed setup instructions.")


if __name__ == "__main__":
    asyncio.run(main())

