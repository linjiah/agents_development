"""
Simple MCP Agent - No LangChain Required

This is a minimal implementation using only:
- mcp package (MCP SDK)
- google-generativeai (Google's Gemini SDK)

No LangChain, LangGraph, or other heavy dependencies needed!
"""

import asyncio
import os
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
WEATHER_SERVER_PATH = SCRIPT_DIR / "weather_server.py"

# MCP server launch config
server_params = StdioServerParameters(
    command="python",
    args=[str(WEATHER_SERVER_PATH)]
)


def convert_mcp_tool_to_gemini(mcp_tool):
    """
    Convert an MCP tool definition to Gemini's function declaration format.
    
    Args:
        mcp_tool: Tool definition from MCP server
        
    Returns:
        Dictionary in Gemini's function declaration format
    """
    # MCP tools have inputSchema as a JSON schema
    input_schema = mcp_tool.inputSchema if hasattr(mcp_tool, 'inputSchema') else {}
    
    # Extract properties and required fields from the schema
    properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
    required = input_schema.get("required", []) if isinstance(input_schema, dict) else []
    
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }


async def execute_mcp_tool(session, tool_name, arguments):
    """
    Execute a tool on the MCP server.
    
    Args:
        session: MCP client session
        tool_name: Name of the tool to call
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Tool execution result
    """
    result = await session.call_tool(tool_name, arguments)
    return result.content[0].text if result.content else str(result)


async def main():
    # Configure Gemini API
    # Check both GOOGLE_GEMINI_API_KEY and GEMINI_API_KEY for compatibility
    google_api_key = os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_GEMINI_API_KEY or GEMINI_API_KEY environment variable is not set")
    
    genai.configure(api_key=google_api_key)
    
    # Connect to MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools from MCP server
            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools
            
            print(f"✅ Connected to MCP server. Found {len(mcp_tools)} tool(s).")
            
            # Convert MCP tools to Gemini format
            gemini_tools = []
            tool_executors = {}  # Map tool names to execution functions
            
            for tool in mcp_tools:
                gemini_tool = convert_mcp_tool_to_gemini(tool)
                gemini_tools.append(gemini_tool)
                tool_executors[tool.name] = tool
                print(f"  - {tool.name}: {tool.description or 'No description'}")
            
            # Create Gemini model with tools
            # Try gemini-1.5-flash first (more commonly available on free tier)
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            
            model = genai.GenerativeModel(
                model_name=model_name,
                tools=[{"function_declarations": gemini_tools}],
                system_instruction="You are a helpful assistant that uses tools to get weather information. When asked about weather, use the available weather tools."
            )
            
            print("\n🤖 Weather MCP agent is ready!")
            print("Type 'exit', 'quit', or 'q' to stop.\n")
            
            # Conversation history
            conversation = []
            
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in {"exit", "quit", "q"}:
                    break
                
                if not user_input:
                    continue
                
                try:
                    # Add user message to conversation
                    conversation.append({
                        "role": "user",
                        "parts": [{"text": user_input}]
                    })
                    
                    # Generate response
                    response = model.generate_content(conversation)
                    
                    # Check if the model wants to call a tool
                    if response.candidates and response.candidates[0].content.parts:
                        tool_calls_made = False
                        
                        for part in response.candidates[0].content.parts:
                            # Check if this part is a function call
                            if hasattr(part, 'function_call') and part.function_call:
                                tool_calls_made = True
                                function_call = part.function_call
                                tool_name = function_call.name
                                arguments = dict(function_call.args)
                                
                                print(f"\n🔧 Calling tool: {tool_name} with args: {arguments}")
                                
                                # Execute the tool via MCP
                                tool_result = await execute_mcp_tool(session, tool_name, arguments)
                                
                                print(f"✅ Tool result: {tool_result}\n")
                                
                                # Add function call to conversation
                                conversation.append({
                                    "role": "model",
                                    "parts": [{"function_call": function_call}]
                                })
                                
                                # Add function response to conversation
                                conversation.append({
                                    "role": "function",
                                    "parts": [{
                                        "function_response": {
                                            "name": tool_name,
                                            "response": tool_result if isinstance(tool_result, str) else json.dumps(tool_result)
                                        }
                                    }]
                                })
                                
                                # Generate final response with tool result
                                final_response = model.generate_content(conversation)
                                
                                # Extract text response
                                if final_response.candidates and final_response.candidates[0].content.parts:
                                    text_parts = [
                                        part.text for part in final_response.candidates[0].content.parts
                                        if hasattr(part, 'text') and part.text
                                    ]
                                    if text_parts:
                                        ai_response = " ".join(text_parts)
                                        print(f"AI: {ai_response}\n")
                                        
                                        # Add to conversation
                                        conversation.append({
                                            "role": "model",
                                            "parts": [{"text": ai_response}]
                                        })
                        
                        # If no tool calls, just show the text response
                        if not tool_calls_made:
                            text_parts = [
                                part.text for part in response.candidates[0].content.parts
                                if hasattr(part, 'text') and part.text
                            ]
                            if text_parts:
                                ai_response = " ".join(text_parts)
                                print(f"AI: {ai_response}\n")
                                
                                # Add to conversation
                                conversation.append({
                                    "role": "model",
                                    "parts": [{"text": ai_response}]
                                })
                
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

