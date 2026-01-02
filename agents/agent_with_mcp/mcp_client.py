"""
MCP Agent Client with LangGraph

This agent uses LangGraph and LangChain to create an intelligent assistant
that can interact with MCP (Model Context Protocol) servers to access tools.

The agent automatically:
- Connects to MCP servers (e.g., weather server)
- Discovers available tools
- Routes between chat and tool execution
- Maintains conversation state
"""

import asyncio
import os
import shlex
import traceback
from pathlib import Path
from typing import Annotated, List
from typing_extensions import TypedDict

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools

# Configuration
# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Multi-Server MCP Architecture
# Following the pattern from Educative's multi-server architecture tutorial:
# Each capability (weather, tasks) is a separate, independent MCP server.
# This provides modularity, reusability, and easier maintenance.

# Paths to MCP server scripts (run as subprocesses)
WEATHER_SERVER_PATH = SCRIPT_DIR / "weather_server.py"
TASK_SERVER_PATH = SCRIPT_DIR / "task_server.py"

# MCP Server Configurations
# Each server is configured independently with its own StdioServerParameters
# StdioServerParameters tells the MCP client how to start and communicate with each server
# 
# How it works:
# 1. When stdio_client() is called, it automatically starts the server script as a subprocess
# 2. Communication happens via stdin/stdout (standard input/output streams)
# 3. No network ports needed - all communication is local through process streams
# 4. When the client exits, all server subprocesses are automatically terminated
#
# Parameters:
# - command: The executable to run (could be "python", "npx", "node", etc.)
# - args: Arguments passed to the command (the server script path)
# - env: Environment variables to pass to the subprocess
#        (Important: Must copy env vars so server can access API keys)

# Weather Server Configuration
weather_server_params = StdioServerParameters(
    command="python",
    args=[str(WEATHER_SERVER_PATH)],
    env=os.environ.copy()
)

# Task Management Server Configuration
task_server_params = StdioServerParameters(
    command="python",
    args=[str(TASK_SERVER_PATH)],
    env=os.environ.copy()
)


# LangGraph state definition
class State(TypedDict):
    """Conversation state managed by LangGraph."""
    messages: Annotated[List[AnyMessage], add_messages]


async def create_graph(sessions: List[ClientSession], server_names: List[str]):
    """
    Create and configure the LangGraph agent with MCP tools from multiple servers.
    
    This function aggregates tools from all connected MCP servers, following the
    multi-server architecture pattern where each server provides independent capabilities.
    
    Args:
        sessions: List of initialized MCP client sessions (one per server)
        server_names: List of server names for logging purposes
        
    Returns:
        Compiled LangGraph agent ready to use with all tools from all servers
    """
    all_tools = []
    
    print("\n" + "="*80)
    print("STEP 1: Fetching MCP Tool Definitions from All Servers")
    print("="*80)
    
    # Aggregate tools from all servers
    for session, server_name in zip(sessions, server_names):
        print(f"\n📡 Connecting to {server_name} server...")
        
        # Show raw MCP tools before conversion
        raw_tools_result = await session.list_tools()
        print(f"📋 {server_name} provides {len(raw_tools_result.tools)} tool(s):")
        for tool in raw_tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Convert to LangChain format
        server_tools = await load_mcp_tools(session)
        print(f"🔧 Converted to {len(server_tools)} LangChain Tool(s) from {server_name}")
        for tool in server_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        all_tools.extend(server_tools)
    
    print(f"\n✅ Total: {len(all_tools)} tool(s) aggregated from {len(sessions)} server(s)")
    
    # Configure LLM
    print("\n" + "="*80)
    print("STEP 2: Binding All Tools to LLM")
    print("="*80)
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0,
        google_api_key="AIzaSyC-Xol1PXPTOBKti3lCtfjilaCbqe493LY"
    )
    llm_with_tools = llm.bind_tools(all_tools)
    print(f"\n✅ All {len(all_tools)} tools bound to LLM")
    print("="*80 + "\n")

    # Create prompt template - updated to reflect multi-capability agent
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that can help with weather information and task management. "
                   "Use the available tools to answer user questions. "
                   "For weather: use get_weather tool. "
                   "For tasks: use create_task, list_tasks, complete_task, delete_task, or get_task tools."),
        MessagesPlaceholder("messages")
    ])

    chat_llm = prompt_template | llm_with_tools

    # Define chat node
    def chat_node(state: State) -> State:
        """Process user input and generate LLM response (may include tool calls)."""
        state["messages"] = chat_llm.invoke({"messages": state["messages"]})
        return state

    # Build LangGraph with automatic tool routing
    graph = StateGraph(State)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tool_node", ToolNode(tools=all_tools))
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges(
        "chat_node",
        tools_condition,
        {
        "tools": "tool_node",
        "__end__": END
        }
    )
    graph.add_edge("tool_node", "chat_node")

    return graph.compile(checkpointer=MemorySaver())


async def list_all_prompts(sessions: List[ClientSession], server_names: List[str]):
    """
    Lists all available prompts from all connected MCP servers.
    Following the tutorial pattern, this iterates through all configured servers
    to discover and display a formatted list of every available prompt.
    
    Args:
        sessions: List of MCP client sessions (one per server)
        server_names: List of server names for display purposes
    """
    all_prompts_found = False
    
    print("\n" + "="*80)
    print("Available Prompts from All Servers")
    print("="*80)
    
    for session, server_name in zip(sessions, server_names):
        try:
            prompt_response = await session.list_prompts()
            
            if prompt_response and prompt_response.prompts:
                all_prompts_found = True
                print(f"\n📡 {server_name} Server:")
                print("-" * 80)
                for p in prompt_response.prompts:
                    print(f"  Prompt: {p.name}")
                    if p.description:
                        print(f"    Description: {p.description}")
                    if p.arguments:
                        arg_list = [f"<{arg.name}: {arg.description or 'string'}>" for arg in p.arguments]
                        print(f"    Arguments: {' '.join(arg_list)}")
                    else:
                        print("    Arguments: None")
                    print()
        except Exception as e:
            print(f"  ⚠️  Error fetching prompts from {server_name}: {e}")
    
    if not all_prompts_found:
        print("\nNo prompts were found on any server.")
    else:
        print("\nUsage: /prompt <prompt_name> \"arg1\" \"arg2\" ...")
        print("="*80 + "\n")


async def handle_prompt_invocation(sessions: List[ClientSession], server_names: List[str], user_input: str) -> str:
    """
    Handles prompt invocation by parsing user input, finding the prompt across all servers,
    and fetching the prompt text from the correct server.
    
    Following the tutorial pattern, this function:
    1. Parses the user input to extract prompt name and arguments
    2. Searches all configured servers to find the prompt
    3. Fetches the prompt from the correct server with the provided arguments
    4. Returns the prompt text for the agent to use
    
    Args:
        sessions: List of MCP client sessions (one per server)
        server_names: List of server names for error messages
        user_input: User input starting with "/prompt"
        
    Returns:
        Prompt text string or None if error
    """
    try:
        # Parse: /prompt <prompt_name> "arg1" "arg2" ...
        parts = user_input.split(None, 1)  # Split on whitespace, max 1 split
        if len(parts) < 2:
            print("Error: Usage is /prompt <prompt_name> \"arg1\" \"arg2\" ...")
            return None
        
        prompt_name = parts[1].split()[0]  # Get prompt name (first word after /prompt)
        
        # Extract arguments (everything after prompt name)
        args_string = parts[1][len(prompt_name):].strip()
        
        # Search all servers to find the prompt
        prompt_def = None
        target_session = None
        target_server_name = None
        
        for session, server_name in zip(sessions, server_names):
            try:
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for p in prompts_response.prompts:
                        if p.name == prompt_name:
                            prompt_def = p
                            target_session = session
                            target_server_name = server_name
                            break
                if prompt_def:
                    break
            except Exception as e:
                print(f"  ⚠️  Error searching {server_name}: {e}")
                continue
        
        if not prompt_def or not target_session:
            print(f"Error: Prompt '{prompt_name}' not found on any server.")
            print("Use /prompts to see all available prompts.")
            return None
        
        # Parse quoted arguments
        args_list = []
        if args_string:
            try:
                args_list = shlex.split(args_string)
            except ValueError:
                print(f"Error: Invalid argument format. Use quotes for arguments with spaces.")
                return None
        
        # Map arguments to dictionary based on prompt definition
        arguments_dict = {}
        if prompt_def.arguments and args_list:
            if len(args_list) != len(prompt_def.arguments):
                print(f"Error: Prompt '{prompt_name}' expects {len(prompt_def.arguments)} argument(s), but {len(args_list)} provided.")
                print(f"Expected arguments: {[arg.name for arg in prompt_def.arguments]}")
                return None
            
            for i, arg_def in enumerate(prompt_def.arguments):
                if i < len(args_list):
                    arguments_dict[arg_def.name] = args_list[i]
        
        # Get prompt from the correct server with arguments as dictionary
        print(f"📡 Fetching prompt '{prompt_name}' from {target_server_name} server...")
        prompt_result = await target_session.get_prompt(prompt_name, arguments=arguments_dict if arguments_dict else None)
        
        if not prompt_result or not prompt_result.messages:
            print(f"Error: Prompt '{prompt_name}' returned no messages.")
            return None
        
        # Extract prompt text from messages
        # MCP prompts return PromptMessage objects with TextContent
        # Format: PromptMessage(role='user', content=TextContent(type='text', text='...'))
        prompt_text = ""
        for msg in prompt_result.messages:
            if hasattr(msg, 'content'):
                content = msg.content
                # Handle TextContent objects (from FastMCP)
                if hasattr(content, 'text') and content.text:
                    prompt_text += content.text + "\n"
                # Handle string content
                elif isinstance(content, str):
                    prompt_text += content + "\n"
                # Handle list of content parts
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, str):
                            prompt_text += part + "\n"
                        elif hasattr(part, 'text') and part.text:
                            prompt_text += part.text + "\n"
                        elif isinstance(part, dict):
                            if 'text' in part:
                                prompt_text += part['text'] + "\n"
            # Fallback: try direct text attribute
            elif hasattr(msg, 'text') and msg.text:
                prompt_text += msg.text + "\n"
        
        result = prompt_text.strip() if prompt_text else None
        if not result:
            print(f"⚠️  Warning: Prompt '{prompt_name}' returned empty content.")
            print(f"   Debug: prompt_result.messages = {prompt_result.messages}")
            if prompt_result.messages:
                msg = prompt_result.messages[0]
                print(f"   Debug: message type = {type(msg).__name__}")
                print(f"   Debug: has content = {hasattr(msg, 'content')}")
                if hasattr(msg, 'content'):
                    print(f"   Debug: content type = {type(msg.content).__name__}")
                    if hasattr(msg.content, 'text'):
                        print(f"   Debug: content.text exists = {msg.content.text is not None}")
        return result
        
    except Exception as e:
        print(f"Error handling prompt: {e}")
        traceback.print_exc()
        return None


async def list_all_resources(sessions: List[ClientSession], server_names: List[str]):
    """
    Lists all available resources from all connected MCP servers.
    Following the tutorial pattern, this iterates through all configured servers
    to discover and display a formatted list of every available resource.
    
    Args:
        sessions: List of MCP client sessions (one per server)
        server_names: List of server names for display purposes
    """
    all_resources_found = False
    
    print("\n" + "="*80)
    print("Available Resources from All Servers")
    print("="*80)
    
    for session, server_name in zip(sessions, server_names):
        try:
            resources_response = await session.list_resources()
            
            if resources_response and resources_response.resources:
                all_resources_found = True
                print(f"\n📡 {server_name} Server:")
                print("-" * 80)
                for resource in resources_response.resources:
                    print(f"  Resource URI: {resource.uri}")
                    print(f"    (Use: /resource {resource.uri})")
                    if resource.name:
                        print(f"    Name: {resource.name}")
                    if resource.description:
                        print(f"    Description: {resource.description}")
                    if resource.mimeType:
                        print(f"    MIME Type: {resource.mimeType}")
                    print()
        except Exception as e:
            print(f"  ⚠️  Error fetching resources from {server_name}: {e}")
    
    if not all_resources_found:
        print("\nNo resources were found on any server.")
    else:
        print("\nUsage: /resource <resource_uri>")
        print("Example: /resource file://delivery_log.txt")
        print("="*80 + "\n")


async def handle_resource_invocation(sessions: List[ClientSession], server_names: List[str], user_input: str) -> str:
    """
    Handles resource invocation by parsing user input, finding the resource across all servers,
    and reading the resource content from the correct server.
    
    Following the tutorial pattern, this function:
    1. Parses the user input to extract resource URI
    2. Searches all configured servers to find the resource
    3. Reads the resource from the correct server
    4. Returns the resource content for the agent to use
    
    Args:
        sessions: List of MCP client sessions (one per server)
        server_names: List of server names for error messages
        user_input: User input starting with "/resource"
        
    Returns:
        Resource content string or None if error
    """
    try:
        # Parse: /resource <resource_uri>
        parts = user_input.split(None, 1)  # Split on whitespace, max 1 split
        if len(parts) < 2:
            print("Error: Usage is /resource <resource_uri>")
            print("Example: /resource file://delivery_log.txt")
            print("Use /resources to see all available resources.")
            return None
        
        resource_uri = parts[1].strip()
        
        # Search all servers to find and read the resource
        target_session = None
        target_server_name = None
        
        for session, server_name in zip(sessions, server_names):
            try:
                # First, check if this server has the resource
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        # Debug: print available URIs
                        # print(f"  Debug: Checking {server_name} - URI: '{resource.uri}' vs requested: '{resource_uri}'")
                        if resource.uri == resource_uri:
                            target_session = session
                            target_server_name = server_name
                            break
                if target_session:
                    break
            except Exception as e:
                print(f"  ⚠️  Error searching {server_name}: {e}")
                continue
        
        if not target_session:
            print(f"Error: Resource '{resource_uri}' not found on any server.")
            print("\nAvailable resources:")
            # Show available resources for debugging
            for session, server_name in zip(sessions, server_names):
                try:
                    resources_response = await session.list_resources()
                    if resources_response and resources_response.resources:
                        for resource in resources_response.resources:
                            print(f"  - {resource.uri} (from {server_name} server)")
                except:
                    pass
            print("\nUse /resources to see all available resources with details.")
            return None
        
        # Read resource from the correct server
        print(f"📡 Reading resource '{resource_uri}' from {target_server_name} server...")
        resource_result = await target_session.read_resource(resource_uri)
        
        if not resource_result or not resource_result.contents:
            print(f"Error: Resource '{resource_uri}' returned no content.")
            return None
        
        # Extract content from resource
        # Resources return contents, we need to combine them
        resource_text = ""
        for content in resource_result.contents:
            # Handle TextContent objects (from FastMCP)
            if hasattr(content, 'text') and content.text:
                resource_text += content.text + "\n"
            # Handle string content
            elif isinstance(content, str):
                resource_text += content + "\n"
            # Handle dict format
            elif isinstance(content, dict):
                if 'text' in content:
                    resource_text += content['text'] + "\n"
            # Handle URI reference
            elif hasattr(content, 'uri'):
                resource_text += f"Resource URI: {content.uri}\n"
        
        result = resource_text.strip() if resource_text else None
        if not result:
            print(f"⚠️  Warning: Resource '{resource_uri}' returned empty content.")
        return result
        
    except Exception as e:
        print(f"Error handling resource: {e}")
        traceback.print_exc()
        return None


async def main():
    """
    Main entry point: Connect to multiple MCP servers and run interactive chat loop.
    
    Following the multi-server architecture pattern, this connects to:
    - Weather server (weather information)
    - Task server (task management)
    
    All tools from all servers are aggregated and made available to the agent.
    """
    # Multi-Server Connection Setup
    # Each server runs as an independent subprocess
    # We use nested context managers to manage all connections
    
    async with stdio_client(weather_server_params) as (weather_read, weather_write):
        async with stdio_client(task_server_params) as (task_read, task_write):
            # Create MCP client sessions for each server
            async with ClientSession(weather_read, weather_write) as weather_session:
                async with ClientSession(task_read, task_write) as task_session:
                    # Initialize all sessions (MCP protocol handshake)
                    await weather_session.initialize()
                    await task_session.initialize()
                    
                    # Aggregate sessions and server names
                    sessions = [weather_session, task_session]
                    server_names = ["Weather", "Task"]
                    
                    # Step 4: Create the LangGraph agent with tools from all servers
                    # This loads and aggregates tools from all connected servers
                    agent = await create_graph(sessions, server_names)
            
                    print("Multi-Server MCP Agent is ready!")
                    print("Connected to: Weather Server + Task Server")
                    print("\nCapabilities:")
                    print("  🌤️  Weather: Get current weather for any location")
                    print("  ✅ Tasks: Create, list, complete, and delete tasks")
                    print("  🗺️  Prompts: Plan trips, compare weather")
                    print("  📚 Resources: Access delivery logs, meeting notes")
                    print("\nCommands:")
                    print("  /prompts                           - to list available prompts")
                    print("  /prompt <prompt_name> \"args\"...  - to run a specific prompt")
                    print("  /resources                         - to list available resources")
                    print("  /resource <resource_uri>           - to read a specific resource")
                    print("  'exit', 'quit', or 'q'            - to stop")
                    print("\n⚠️  Note: Commands MUST start with '/' (e.g., /resources, not resources)")
                    print("💡 Tip: Use /resources first to see exact resource URIs, then use /resource with the full URI\n")

                    while True:
                        try:
                            # This variable will hold the final message to be sent to the agent
                            message_to_agent = ""
                            
                            user_input = input("You: ").strip()
                            
                            if user_input.lower() in {"exit", "quit", "q"}:
                                break

                            if not user_input:
                                continue

                            # --- Command Handling Logic ---
                            # Handle commands that start with / (or common typos without /)
                            user_input_lower = user_input.lower()
                            
                            # Auto-correct common typos (missing leading /)
                            if user_input_lower in {"resources", "prompts"}:
                                user_input = "/" + user_input
                                user_input_lower = user_input.lower()
                            elif user_input_lower.startswith("resource ") or user_input_lower.startswith("prompt "):
                                user_input = "/" + user_input
                                user_input_lower = user_input.lower()
                            
                            if user_input.startswith("/"):
                                if user_input_lower == "/prompts":
                                    # List prompts from all servers (following tutorial pattern)
                                    await list_all_prompts(sessions, server_names)
                                    continue  # Command is done, loop back for next input

                                elif user_input_lower == "/resources":
                                    # List resources from all servers (following tutorial pattern)
                                    await list_all_resources(sessions, server_names)
                                    continue  # Command is done, loop back for next input

                                elif user_input_lower.startswith("/prompt"):
                                    # The handle_prompt_invocation function searches all servers
                                    # and returns the prompt text or None
                                    prompt_text = await handle_prompt_invocation(sessions, server_names, user_input)
                                    if prompt_text:
                                        print(f"\n✅ Prompt fetched successfully. Sending to agent...\n")
                                        message_to_agent = prompt_text
                                    else:
                                        # If prompt fetching failed, loop back for next input
                                        print("❌ Failed to fetch prompt. Please check the prompt name and arguments.")
                                        continue

                                elif user_input_lower.startswith("/resource"):
                                    # The handle_resource_invocation function searches all servers
                                    # and returns the resource content or None
                                    resource_content = await handle_resource_invocation(sessions, server_names, user_input)
                                    if resource_content:
                                        print(f"\n✅ Resource loaded successfully. Including in agent context...\n")
                                        # Include resource content in the message to the agent
                                        message_to_agent = f"Here is the content from the resource:\n\n{resource_content}\n\nPlease use this information to help answer the user's questions."
                                    else:
                                        # If resource fetching failed, loop back for next input
                                        print("❌ Failed to load resource. Please check the resource URI.")
                                        continue
                                else:
                                    # Unknown command starting with /
                                    print(f"Unknown command: {user_input}")
                                    print("Available commands: /prompts, /resources, /prompt <name> \"args\", /resource <uri>")
                                    continue
                            
                            else:
                                # For a normal chat message, the message is just the user's input
                                message_to_agent = user_input

                            # Final agent invocation
                            # All paths (regular chat or successful prompt) now lead to this single block
                            if message_to_agent:
                                try:
                                    response = await agent.ainvoke(
                                        {"messages": [HumanMessage(content=message_to_agent)]},
                                        config={"configurable": {"thread_id": "multi-server-session"}}
                                    )
                                except Exception as e:
                                    print(f"\n❌ Error invoking agent: {e}")
                                    traceback.print_exc()
                                    continue
                            
                                # Extract and display response
                                last_ai_message = None
                                for msg in reversed(response["messages"]):
                                    if isinstance(msg, AIMessage):
                                        last_ai_message = msg
                                        break
                                
                                if last_ai_message is None:
                                    last_ai_message = response["messages"][-1]
                                
                                # Extract text content from message
                                def extract_text_from_message(msg):
                                    """Extract text content from a LangChain message."""
                                    if hasattr(msg, 'text'):
                                        try:
                                            if msg.text:
                                                return msg.text
                                        except Exception:
                                            pass
                                    
                                    if hasattr(msg, 'content'):
                                        try:
                                            content = msg.content
                                            if isinstance(content, str):
                                                return content
                                            if isinstance(content, list):
                                                text_parts = []
                                                for part in content:
                                                    if isinstance(part, str):
                                                        text_parts.append(part)
                                                    elif isinstance(part, dict) and 'text' in part:
                                                        text_parts.append(part['text'])
                                                    elif hasattr(part, 'text'):
                                                        try:
                                                            if part.text:
                                                                text_parts.append(part.text)
                                                        except Exception:
                                                            pass
                                                if text_parts:
                                                    return ' '.join(text_parts)
                                        except Exception:
                                            pass
                                    
                                    return str(msg)
                                
                                response_text = extract_text_from_message(last_ai_message)
                                print(f"AI: {response_text}" if response_text else "AI: [No response text]")
                                    
                        except KeyboardInterrupt:
                            print("\n\nExiting...")
                            break
                        except Exception as e:
                            print(f"\n❌ Error: {e}")
                            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())