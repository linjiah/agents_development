"""
Tool-Enabled Agent with MCP Support - Google ADK

This example demonstrates how to create an agent with:
1. Native/custom tools (calculator, web_search, etc.)
2. MCP (Model Context Protocol) tools from external MCP servers

MCP Benefits:
- Standardized tool protocol
- Easy integration with existing MCP tools
- Community ecosystem
- Cleaner separation of concerns

Security Improvements:
- Calculator now uses CalculatorTool class for safer expression evaluation
- MCP tool results are properly extracted and handled
- Code duplication reduced by importing from tools module
"""

import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any, List
import time

# Setup compatibility fixes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

import google.generativeai as genai

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GEMINI_API_KEY")

if not api_key or api_key == "your_api_key_here" or api_key.strip() == "":
    print("\n❌ ERROR: GEMINI_API_KEY not set!")
    print("Run: python setup_api_key.py")
    raise ValueError("GEMINI_API_KEY not set correctly.")

try:
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"\n❌ ERROR: Failed to configure Gemini API: {str(e)}")
    raise

# ============================================================================
# NATIVE TOOLS - Import from tools module to avoid duplication
# ============================================================================

# Import calculator tool for safe evaluation
try:
    from tools.calculator import CalculatorTool
    _calc_tool = CalculatorTool()
    
    def calculator(expression: str) -> str:
        """Evaluate a mathematical expression safely using CalculatorTool."""
        result = _calc_tool.calculate(expression)
        return str(result)
except ImportError:
    # Fallback: safer eval with restricted environment
    import ast
    import operator
    
    def calculator(expression: str) -> str:
        """Evaluate a mathematical expression safely (fallback implementation)."""
        try:
            # Only allow numbers, operators, and parentheses
            allowed_chars = set("0123456789+-*/()., ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            # Use ast.literal_eval for simple numbers, but for expressions with operators,
            # we need a safer approach. For now, use eval with restricted environment.
            # In production, consider using a proper expression parser library.
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
            }
            safe_dict.update({k: v for k, v in operator.__dict__.items() if not k.startswith("_")})
            
            result = eval(expression, safe_dict, {})
            return str(result)
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"

def web_search(query: str, num_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            
            if not results:
                return f"No results found for: {query}"
            
            summary = f"Search results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                snippet = result.get('body', result.get('description', 'No description'))
                url = result.get('href', result.get('url', 'No URL'))
                summary += f"{i}. {title}\n   {snippet[:150]}...\n   URL: {url}\n\n"
            
            return summary.strip()
    except ImportError:
        return "Web search requires 'duckduckgo-search' package. Install: pip install duckduckgo-search"
    except Exception as e:
        return f"Error performing web search: {str(e)}"

def get_current_time(timezone: str = "UTC") -> str:
    """Get the current date and time for a specified timezone."""
    try:
        from datetime import datetime
        import pytz
        
        if timezone == "UTC":
            tz = pytz.UTC
        else:
            try:
                tz = pytz.timezone(timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                tz = pytz.UTC
                now = datetime.now(tz)
                return f"Unknown timezone '{timezone}'. Using UTC.\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        
        now = datetime.now(tz)
        return f"Current time in {timezone}:\n- Date: {now.strftime('%Y-%m-%d')}\n- Time: {now.strftime('%H:%M:%S')}\n- Day: {now.strftime('%A')}"
    except ImportError:
        from datetime import datetime
        now = datetime.now()
        return f"Current time (local): {now.strftime('%Y-%m-%d %H:%M:%S')}\n[Install 'pytz' for timezone support]"

# Native tool definitions for Gemini
NATIVE_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "calculator",
                "description": "Evaluate a mathematical expression. Use for arithmetic calculations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for current information. Use when you need real-time data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get the current date and time for a specified timezone.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone name (e.g., 'America/New_York', 'Asia/Tokyo'). Default: UTC"
                        }
                    },
                    "required": []
                }
            }
        ]
    }
]

# Native tool execution mapping
NATIVE_TOOL_FUNCTIONS = {
    "calculator": calculator,
    "web_search": web_search,
    "get_current_time": get_current_time,
}

# ============================================================================
# MCP INTEGRATION
# ============================================================================

# Check if MCP is available
try:
    from google.adk.tools.mcp_tool import MCPToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import (
        SseServerParams,
        StreamableHTTPServerParams,
        StdioServerParameters
    )
    MCP_AVAILABLE = True
    print("✅ MCP support available")
except ImportError as e:
    MCP_AVAILABLE = False
    print(f"⚠️  MCP not available: {e}")
    print("   Continuing with native tools only...")

def create_mcp_toolset_sse(server_url: str, headers: Dict[str, str] = None) -> 'MCPToolset':
    """
    Create MCP toolset for Server-Sent Events (SSE) server.
    
    Args:
        server_url: URL of the MCP server (e.g., "http://localhost:8001/sse")
        headers: Optional HTTP headers (e.g., for authentication)
    
    Returns:
        MCPToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available. Install: pip install google-adk")
    
    return MCPToolset(
        connection_params=SseServerParams(
            url=server_url,
            headers=headers or {},
        )
    )

def create_mcp_toolset_http(server_url: str, headers: Dict[str, str] = None) -> 'MCPToolset':
    """
    Create MCP toolset for HTTP server.
    
    Args:
        server_url: URL of the MCP server (e.g., "https://api.example.com/mcp/")
        headers: Optional HTTP headers (e.g., for authentication)
    
    Returns:
        MCPToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available. Install: pip install google-adk")
    
    return MCPToolset(
        connection_params=StreamableHTTPServerParams(
            url=server_url,
            headers=headers or {},
        )
    )

def create_mcp_toolset_stdio(command: str, args: List[str] = None, env: Dict[str, str] = None) -> 'MCPToolset':
    """
    Create MCP toolset for stdio-based MCP server.
    
    Args:
        command: Command to run the MCP server (e.g., "npx", "python")
        args: Command arguments (e.g., ["-y", "@modelcontextprotocol/server-filesystem"])
        env: Environment variables for the server
    
    Returns:
        MCPToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available. Install: pip install google-adk")
    
    return MCPToolset(
        connection_params=StdioServerParameters(
            command=command,
            args=args or [],
            env=env or {},
        )
    )

# ============================================================================
# AGENT CREATION
# ============================================================================

def create_agent_with_mcp(
    use_native_tools: bool = True,
    mcp_config: Dict[str, Any] = None
):
    """
    Create agent with native tools and/or MCP tools.
    
    Args:
        use_native_tools: Whether to include native tools (calculator, web_search, etc.)
        mcp_config: MCP configuration dict with keys:
            - type: "sse", "http", or "stdio"
            - url: Server URL (for sse/http)
            - command: Command to run (for stdio)
            - args: Command args (for stdio)
            - headers: HTTP headers (for sse/http)
    
    Returns:
        Configured GenerativeModel instance
    """
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5")
    
    tools = []
    
    # Add native tools
    if use_native_tools:
        tools.extend(NATIVE_TOOLS)
        print(f"✅ Loaded {len(NATIVE_TOOL_FUNCTIONS)} native tools")
    
    # Add MCP tools
    if mcp_config and MCP_AVAILABLE:
        try:
            mcp_type = mcp_config.get("type", "sse")
            
            if mcp_type == "sse":
                mcp_toolset = create_mcp_toolset_sse(
                    server_url=mcp_config["url"],
                    headers=mcp_config.get("headers")
                )
            elif mcp_type == "http":
                mcp_toolset = create_mcp_toolset_http(
                    server_url=mcp_config["url"],
                    headers=mcp_config.get("headers")
                )
            elif mcp_type == "stdio":
                mcp_toolset = create_mcp_toolset_stdio(
                    command=mcp_config["command"],
                    args=mcp_config.get("args"),
                    env=mcp_config.get("env")
                )
            else:
                raise ValueError(f"Unknown MCP type: {mcp_type}")
            
            tools.append(mcp_toolset)
            print(f"✅ Loaded MCP toolset from {mcp_config.get('url', mcp_config.get('command'))}")
        except Exception as e:
            print(f"⚠️  Failed to load MCP tools: {str(e)}")
            print("   Continuing with native tools only...")
    
    system_instruction = """You are a helpful personal assistant with access to various tools.

Available capabilities:
- Calculator: Mathematical calculations
- Web Search: Find current information on the internet
- Time: Get current date/time for any timezone
- MCP Tools: Additional tools from MCP servers (if available)

Tool Usage Rules:
1. Use web_search for current information, recent events, or data you don't have
2. Use calculator for mathematical expressions
3. Use get_current_time for date/time queries
4. Use MCP tools for specialized capabilities they provide

Always explain what you're doing and provide helpful responses."""
    
    model = genai.GenerativeModel(
        model_name=model_name,
        tools=tools,
        system_instruction=system_instruction
    )
    
    return model

def is_native_tool(function_name: str) -> bool:
    """Check if a function name is a native tool."""
    return function_name in NATIVE_TOOL_FUNCTIONS

def execute_tool(function_name: str, args: Dict[str, Any]) -> str:
    """Execute a native tool function."""
    if function_name in NATIVE_TOOL_FUNCTIONS:
        func = NATIVE_TOOL_FUNCTIONS[function_name]
        try:
            # Handle optional parameters
            if function_name == "web_search" and "num_results" not in args:
                args["num_results"] = 5
            elif function_name == "get_current_time" and "timezone" not in args:
                args["timezone"] = "UTC"
            
            return func(**args)
        except TypeError as e:
            return f"Error executing {function_name}: {str(e)}"
    return f"Error: Tool '{function_name}' not found in native tools"

# ============================================================================
# INTERACTIVE AGENT
# ============================================================================

def run_agent_interactive(
    use_native_tools: bool = True,
    mcp_config: Dict[str, Any] = None,
    debug: bool = False
):
    """Run the agent in interactive mode."""
    
    print("="*60)
    print("🤖 Personal Assistant with MCP Support")
    print("="*60)
    
    # Create agent
    agent = create_agent_with_mcp(
        use_native_tools=use_native_tools,
        mcp_config=mcp_config
    )
    
    print("\nType 'quit' or 'exit' to end")
    print("Type 'debug' to toggle debug mode")
    print("Type 'config' to see current configuration\n")
    
    conversation_history = []
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if user_input.lower() == 'debug':
            debug = not debug
            print(f"\n🐛 Debug mode: {'ON' if debug else 'OFF'}\n")
            continue
        
        if user_input.lower() == 'config':
            print("\n📋 Configuration:")
            print(f"   Native tools: {use_native_tools}")
            print(f"   MCP config: {mcp_config}")
            print(f"   Debug: {debug}\n")
            continue
        
        if not user_input:
            continue
        
        try:
            # Add user message
            user_msg = {"role": "user", "parts": [user_input]}
            conversation_history.append(user_msg)
            
            if debug:
                print(f"\n📤 Sending to model...")
            
            # Generate response
            response = agent.generate_content(conversation_history)
            
            # Check for function calls
            function_call = None
            text_parts = []
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    if debug:
                        print(f"\n🔧 FUNCTION CALL DETECTED: {function_call.name}")
                        print(f"   Arguments: {dict(function_call.args)}")
                elif hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            if function_call:
                # Execute function call
                function_name = function_call.name
                args = dict(function_call.args)
                
                print(f"\n{'='*60}")
                print(f"🔧 TOOL EXECUTION")
                print(f"{'='*60}")
                print(f"Tool: {function_name}")
                print(f"Arguments: {args}")
                print(f"{'='*60}")
                
                # Check if it's a native tool or MCP tool
                if is_native_tool(function_name):
                    # Native tool - execute manually
                    tool_result = execute_tool(function_name, args)
                    print(f"✅ Tool Result: {tool_result}")
                    
                    # Add function call to conversation
                    model_function_msg = {
                        "role": "model",
                        "parts": [{"function_call": function_call}]
                    }
                    conversation_history.append(model_function_msg)
                    
                    # Add function response
                    function_response_msg = {
                        "role": "function",
                        "parts": [{
                            "function_response": {
                                "name": function_name,
                                "response": {"result": tool_result}
                            }
                        }]
                    }
                    conversation_history.append(function_response_msg)
                    
                    # Get final response
                    final_response = agent.generate_content(conversation_history)
                    response_text = final_response.text if hasattr(final_response, 'text') else str(final_response)
                    
                    # Add final response to history
                    model_text_msg = {"role": "model", "parts": [response_text]}
                    conversation_history.append(model_text_msg)
                    
                    print(f"{'='*60}\n")
                    print(f"\nAgent: {response_text}\n")
                else:
                    # MCP tool - ADK handles execution automatically
                    # Add function call to conversation and let ADK handle execution
                    model_function_msg = {
                        "role": "model",
                        "parts": [{"function_call": function_call}]
                    }
                    conversation_history.append(model_function_msg)
                    
                    if debug:
                        print(f"🔄 MCP tool execution handled by ADK...")
                    
                    try:
                        # Call generate_content - ADK will execute MCP tool and return result
                        # The response should contain the tool result integrated into the text
                        final_response = agent.generate_content(conversation_history)
                        
                        # Extract response text
                        response_text = final_response.text if hasattr(final_response, 'text') else str(final_response)
                        
                        # Check if there's a function_response in the response (some MCP tools might return this)
                        function_response_found = False
                        if hasattr(final_response, 'candidates') and final_response.candidates:
                            for part in final_response.candidates[0].content.parts:
                                if hasattr(part, 'function_response') and part.function_response:
                                    # MCP tool returned a function_response
                                    fr = part.function_response
                                    tool_result = fr.response if hasattr(fr, 'response') else str(fr)
                                    print(f"✅ MCP Tool Result: {tool_result}")
                                    function_response_found = True
                                    
                                    # Add function response to history
                                    function_response_msg = {
                                        "role": "function",
                                        "parts": [{
                                            "function_response": {
                                                "name": function_name,
                                                "response": tool_result if isinstance(tool_result, dict) else {"result": str(tool_result)}
                                            }
                                        }]
                                    }
                                    conversation_history.append(function_response_msg)
                                    
                                    # Get final response after function response
                                    final_response = agent.generate_content(conversation_history)
                                    response_text = final_response.text if hasattr(final_response, 'text') else str(final_response)
                                    break
                        
                        if not function_response_found:
                            # MCP tool result is already integrated in the response text
                            print(f"✅ MCP tool executed (result integrated in response)")
                        
                        # Add final response to history
                        model_text_msg = {"role": "model", "parts": [response_text]}
                        conversation_history.append(model_text_msg)
                        
                        print(f"{'='*60}\n")
                        print(f"\nAgent: {response_text}\n")
                    except Exception as e:
                        error_msg = f"Error executing MCP tool '{function_name}': {str(e)}"
                        print(f"❌ {error_msg}")
                        if debug:
                            import traceback
                            traceback.print_exc()
                        
                        # Add error to conversation and get response
                        error_response_msg = {
                            "role": "function",
                            "parts": [{
                                "function_response": {
                                    "name": function_name,
                                    "response": {"error": error_msg}
                                }
                            }]
                        }
                        conversation_history.append(error_response_msg)
                        
                        try:
                            error_response = agent.generate_content(conversation_history)
                            error_text = error_response.text if hasattr(error_response, 'text') else str(error_response)
                            conversation_history.append({"role": "model", "parts": [error_text]})
                            print(f"\nAgent: {error_text}\n")
                        except Exception as e2:
                            print(f"\n❌ Failed to get error response: {str(e2)}\n")
            
            else:
                # No function call, direct response
                response_text = "".join(text_parts) if text_parts else response.text
                model_msg = {"role": "model", "parts": [response_text]}
                conversation_history.append(model_msg)
                print(f"\nAgent: {response_text}\n")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            if debug:
                import traceback
                traceback.print_exc()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tool Agent with MCP Support")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-native", action="store_true", help="Disable native tools")
    parser.add_argument("--mcp-url", type=str, help="MCP server URL (SSE)")
    parser.add_argument("--mcp-type", type=str, choices=["sse", "http", "stdio"], default="sse", help="MCP server type")
    parser.add_argument("--mcp-command", type=str, help="MCP server command (for stdio)")
    
    args = parser.parse_args()
    
    # Build MCP config
    mcp_config = None
    if args.mcp_url:
        mcp_config = {
            "type": args.mcp_type,
            "url": args.mcp_url,
        }
    elif args.mcp_command:
        mcp_config = {
            "type": "stdio",
            "command": args.mcp_command,
        }
    
    # Example MCP configurations (commented out):
    
    # Example 1: Local MCP server (SSE)
    # mcp_config = {
    #     "type": "sse",
    #     "url": "http://localhost:8001/sse"
    # }
    
    # Example 2: Remote MCP server with auth
    # mcp_config = {
    #     "type": "http",
    #     "url": "https://api.example.com/mcp/",
    #     "headers": {
    #         "Authorization": f"Bearer {os.getenv('MCP_API_KEY')}"
    #     }
    # }
    
    # Example 3: Stdio-based MCP server (e.g., filesystem)
    # mcp_config = {
    #     "type": "stdio",
    #     "command": "npx",
    #     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
    # }
    
    # Run agent
    run_agent_interactive(
        use_native_tools=not args.no_native,
        mcp_config=mcp_config,
        debug=args.debug
    )

