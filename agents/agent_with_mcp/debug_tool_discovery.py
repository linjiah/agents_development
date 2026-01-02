"""
Debug Script: Show How MCP Tool Definitions Are Fetched and Passed to LLM

This script demonstrates the complete flow of:
1. Connecting to MCP server
2. Discovering tools
3. Converting to LangChain format
4. Binding to LLM
"""

import asyncio
import json
from pathlib import Path
import os

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools

# Configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
WEATHER_SERVER_PATH = SCRIPT_DIR / "weather_server.py"

server_params = StdioServerParameters(
    command="python",
    args=[str(WEATHER_SERVER_PATH)],
    env=os.environ.copy()
)


async def show_raw_mcp_tools(session: ClientSession):
    """Show raw MCP tool definitions from server."""
    print("\n" + "="*80)
    print("STEP 1: Fetching Raw MCP Tool Definitions from Server")
    print("="*80)
    
    # Use MCP protocol directly to list tools
    tools_result = await session.list_tools()
    
    print(f"\n📋 Found {len(tools_result.tools)} tool(s) from MCP server:\n")
    
    for tool in tools_result.tools:
        print(f"Tool Name: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Input Schema:")
        print(json.dumps(tool.inputSchema, indent=2))
        print("-" * 80)
    
    return tools_result.tools


async def show_langchain_tools(tools):
    """Show how MCP tools are converted to LangChain format."""
    print("\n" + "="*80)
    print("STEP 2: Converting MCP Tools to LangChain Format")
    print("="*80)
    
    print(f"\n🔧 Converted to {len(tools)} LangChain Tool(s):\n")
    
    for i, tool in enumerate(tools, 1):
        print(f"Tool #{i}:")
        print(f"  Name: {tool.name}")
        print(f"  Description: {tool.description}")
        
        # Show the tool's schema
        if hasattr(tool, 'args_schema'):
            print(f"  Args Schema:")
            schema = tool.args_schema
            if schema:
                print(f"    Type: {schema.__name__ if hasattr(schema, '__name__') else type(schema)}")
                if hasattr(schema, 'model_fields'):
                    print(f"    Fields:")
                    for field_name, field_info in schema.model_fields.items():
                        print(f"      - {field_name}: {field_info.annotation}")
        
        # Show tool metadata
        if hasattr(tool, 'metadata'):
            print(f"  Metadata: {tool.metadata}")
        
        print("-" * 80)
    
    return tools


async def show_llm_tool_binding(tools):
    """Show how tools are bound to LLM."""
    print("\n" + "="*80)
    print("STEP 3: Binding Tools to LLM")
    print("="*80)
    
    # Configure LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0,
        google_api_key="AIzaSyC-Xol1PXPTOBKti3lCtfjilaCbqe493LY"
    )
    
    print("\n🤖 LLM before binding tools:")
    print(f"  Model: {llm.model_name}")
    print(f"  Bound tools: {llm.bindings if hasattr(llm, 'bindings') else 'None'}")
    
    # Bind tools
    llm_with_tools = llm.bind_tools(tools)
    
    print("\n🔗 After binding tools:")
    print(f"  Tools bound: {len(tools)}")
    
    # Try to show what the LLM sees
    if hasattr(llm_with_tools, 'bound_tools'):
        print(f"  Bound tools attribute: {llm_with_tools.bound_tools}")
    
    # Show tool schemas that LLM will receive
    print("\n📝 Tool Schemas Passed to LLM:")
    for tool in tools:
        # LangChain tools have a schema that gets passed to LLM
        if hasattr(tool, 'name') and hasattr(tool, 'description'):
            tool_schema = {
                "name": tool.name,
                "description": tool.description,
            }
            
            # Get parameter schema
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema
                if hasattr(schema, 'model_json_schema'):
                    tool_schema["parameters"] = schema.model_json_schema()
                elif hasattr(schema, 'schema'):
                    tool_schema["parameters"] = schema.schema()
            
            print(f"\n  Tool: {tool.name}")
            print(f"  Schema sent to LLM:")
            print(json.dumps(tool_schema, indent=4))
    
    return llm_with_tools


async def show_llm_tool_usage(llm_with_tools):
    """Show how LLM uses tools when generating response."""
    print("\n" + "="*80)
    print("STEP 4: LLM Tool Usage Example")
    print("="*80)
    
    from langchain_core.messages import HumanMessage
    
    print("\n💬 Sending test message to LLM:")
    test_message = "What's the weather in San Diego?"
    print(f"  User: {test_message}")
    
    try:
        # Invoke LLM with tools
        response = await llm_with_tools.ainvoke([HumanMessage(content=test_message)])
        
        print("\n🤖 LLM Response:")
        print(f"  Type: {type(response)}")
        
        # Check if LLM wants to call a tool
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"\n  🔧 LLM decided to call {len(response.tool_calls)} tool(s):")
            for tool_call in response.tool_calls:
                print(f"    - Tool: {tool_call.get('name', 'unknown')}")
                print(f"      Args: {tool_call.get('args', {})}")
        elif hasattr(response, 'content'):
            print(f"  📝 LLM generated text response: {response.content[:100]}...")
        else:
            print(f"  Response: {response}")
            
    except Exception as e:
        print(f"\n  ⚠️  Error: {e}")
        print("  (This is expected if API key/quota issues)")


async def main():
    """Main function to demonstrate tool discovery flow."""
    print("\n" + "="*80)
    print("MCP TOOL DISCOVERY AND LLM BINDING DEMONSTRATION")
    print("="*80)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Step 1: Show raw MCP tools
            raw_tools = await show_raw_mcp_tools(session)
            
            # Step 2: Convert to LangChain format
            langchain_tools = await load_mcp_tools(session)
            await show_langchain_tools(langchain_tools)
            
            # Step 3: Bind to LLM
            llm_with_tools = await show_llm_tool_binding(langchain_tools)
            
            # Step 4: Show LLM usage
            await show_llm_tool_usage(llm_with_tools)
            
            print("\n" + "="*80)
            print("DEMONSTRATION COMPLETE")
            print("="*80)
            print("\nSummary:")
            print(f"  1. MCP Server provides {len(raw_tools)} tool definition(s)")
            print(f"  2. Converted to {len(langchain_tools)} LangChain tool(s)")
            print(f"  3. Bound to LLM for function calling")
            print(f"  4. LLM can now use tools when generating responses")


if __name__ == "__main__":
    asyncio.run(main())

