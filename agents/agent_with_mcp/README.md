# Simple MCP Agent with Weather Server

An MCP agent implementation that demonstrates how to use the Model Context Protocol (MCP) with LangGraph and LangChain. This agent connects to a FastMCP weather server to provide weather information.

## Table of Contents

1. [Complete Procedure: Making MCP Work for an Agent](#complete-procedure-making-mcp-work-for-an-agent)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Setup](#setup)
5. [Usage](#usage)
6. [How It Works](#how-it-works)
7. [Code Structure](#code-structure)
8. [Troubleshooting](#troubleshooting)
9. [Extending the Agent](#extending-the-agent)

---

## Complete Procedure: Making MCP Work for an Agent

This section provides a step-by-step guide on how to integrate MCP (Model Context Protocol) with an agent, using our weather MCP tool as a detailed example.

### Overview: What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol that allows AI agents to connect to external tools, data sources, and services. It provides:
- **Standardized communication** between agents and tools
- **Tool discovery** - agents can automatically discover available tools
- **Separation of concerns** - tools run as separate processes/servers
- **Reusability** - tools can be used by multiple agents

### Step-by-Step Procedure

#### Step 1: Create the MCP Server

The MCP server is a separate process that provides tools to the agent. In our example, we use **FastMCP** to create a weather server.

**File: `weather_server.py`**

**1.1: Import Required Libraries**

```1:5:weather_server.py
import os
import sys
import requests
import logging
from mcp.server.fastmcp import FastMCP
```

**1.2: Load Environment Variables (Optional)**

```7:19:weather_server.py
# Try to load from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Try to load .env from parent directory (where it's located)
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to current directory
        load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use environment variables only
```

**1.3: Initialize FastMCP Server**

```33:34:weather_server.py
# Initialize the FastMCP server
mcp = FastMCP("WeatherAssistant")
```

**1.4: Define MCP Tool with @mcp.tool() Decorator**

```36:46:weather_server.py
@mcp.tool()
def get_weather(location: str) -> dict:
    """
    Fetches the current weather for a specified location using the OpenWeatherMap API.

    Args:
        location: The city name and optional country code (e.g., "London,uk").

    Returns:
        A dictionary containing weather information or an error message.
    """
```

**1.5: Implement Tool Logic**

```47:79:weather_server.py
    if not OPENWEATHERMAP_API_KEY:
        error_msg = "OpenWeatherMap API key is not configured. Please set OPENWEATHERMAP_API_KEY environment variable."
        print(f"[Weather Server] ERROR: {error_msg}", file=sys.stderr)
        return {"error": error_msg}

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric"  # Use "imperial" for Fahrenheit
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        # Extracting relevant weather information
        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return {
            "location": data["name"],
            "weather": weather_description,
            "temperature_celsius": f"{temperature}°C",
            "feels_like_celsius": f"{feels_like}°C",
            "humidity": f"{humidity}%",
            "wind_speed_mps": f"{wind_speed} m/s"
        }
```

**1.6: Add Error Handling**

```81:93:weather_server.py
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return {"error": f"Could not find weather data for '{location}'. Please check the location name."}
        elif response.status_code == 401:
            return {"error": f"Authentication failed (401). API key used: {OPENWEATHERMAP_API_KEY[:10]}... The API key may be invalid or inactive."}
        else:
            return {"error": f"An HTTP error occurred: HTTP {response.status_code}: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"A network error occurred: {req_err}"}
    except KeyError:
        return {"error": "Received unexpected data format from the weather API."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
```

**1.7: Run the Server**

```96:99:weather_server.py
if __name__ == "__main__":
    logging.getLogger("mcp").setLevel(logging.WARNING)
    # The server will run and listen for requests from the client over stdio
    mcp.run(transport="stdio")
```

**Key Points:**
- `FastMCP("WeatherAssistant")` creates the server instance
- `@mcp.tool()` decorator exposes functions as MCP tools
- `transport="stdio"` enables communication via stdin/stdout
- The server runs as a separate subprocess when called by the client
- Tools must return dictionaries (for structured data) or handle errors gracefully

#### Step 2: Configure the MCP Client Connection

The agent needs to know how to connect to the MCP server. We use `StdioServerParameters` to configure a stdio-based connection.

**File: `mcp_client.py`**

**2.1: Import Required Libraries**

```1:5:mcp_client.py
import asyncio
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
```

**2.2: Load Environment Variables**

```7:21:mcp_client.py
# Try to load from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Try to load .env from parent directory (where it's located)
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        # Fallback to current directory
        load_dotenv(override=True)
except ImportError:
    pass  # python-dotenv not installed, use environment variables only
except Exception:
    pass  # Silently fail if .env loading has issues
```

**2.3: Determine Server Path**

```36:38:mcp_client.py
# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
WEATHER_SERVER_PATH = SCRIPT_DIR / "weather_server.py"
```

**2.4: Configure StdioServerParameters**

```40:46:mcp_client.py
# MCP server launch config
# Pass environment variables to the subprocess so it can access API keys
server_params = StdioServerParameters(
    command="python",
    args=[str(WEATHER_SERVER_PATH)],
    env=os.environ.copy()  # Pass environment variables to the subprocess
)
```

**Key Points:**
- `command="python"` - The command to execute (could be "npx", "node", etc.)
- `args=[str(WEATHER_SERVER_PATH)]` - Arguments passed to the command (the server script)
- `env=os.environ.copy()` - **Critical**: Passes environment variables to the subprocess so the server can access API keys
- The server will be started as a subprocess when the client connects

#### Step 3: Establish MCP Connection and Initialize Session

The agent establishes a connection to the MCP server and initializes the MCP protocol.

**File: `mcp_client.py`**

**3.1: Create stdio Connection and Start Server Subprocess**

```100:102:mcp_client.py
# Entry point
async def main():
    async with stdio_client(server_params) as (read, write):
```

**What happens:**
- `stdio_client(server_params)` creates a stdio connection
- Starts the weather server as a subprocess using the parameters from Step 2
- Returns `(read, write)` streams for bidirectional communication
- The server process is now running and waiting for MCP protocol messages

**3.2: Create MCP Client Session**

```103:103:mcp_client.py
        async with ClientSession(read, write) as session:
```

**What happens:**
- `ClientSession(read, write)` creates an MCP client session
- Uses the read/write streams to communicate with the server subprocess
- The session manages the MCP protocol state

**3.3: Initialize MCP Protocol Handshake**

```104:104:mcp_client.py
            await session.initialize()
```

**What happens:**
- Performs the MCP protocol initialization handshake
- Exchanges capabilities between client and server
- The server is now ready to receive tool discovery and execution requests

**Complete Connection Code:**

```100:108:mcp_client.py
# Entry point
async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            agent = await create_graph(session)
            
            print("Weather MCP agent is ready.")
```

**Key Points:**
- Use `async with` context managers to ensure proper cleanup
- The server subprocess starts when `stdio_client` is entered
- `session.initialize()` must be called before using the session
- The session is now ready to discover and call tools

#### Step 4: Load MCP Tools into LangChain

Use `langchain_mcp_adapters` to convert MCP tools into LangChain-compatible tools.

**File: `mcp_client.py`**

**4.1: Import langchain_mcp_adapters**

```34:34:mcp_client.py
from langchain_mcp_adapters.tools import load_mcp_tools
```

**4.2: Load Tools from MCP Server**

```53:55:mcp_client.py
async def create_graph(session):
    # Load tools from MCP server
    tools = await load_mcp_tools(session)
```

**What happens internally:**
1. `load_mcp_tools(session)` sends an MCP `tools/list` request to the server
2. The server responds with tool definitions (name, description, parameters schema)
3. The adapter converts MCP tool schemas to LangChain tool format
4. Returns a list of LangChain `StructuredTool` objects

**Example: The `get_weather` tool becomes:**
- **Name**: `get_weather`
- **Description**: "Fetches the current weather for a specified location..."
- **Parameters**: `{"location": str}`
- **LangChain Tool**: Can be bound to LLM and executed automatically

**Key Points:**
- Must be called with an initialized `session` from Step 3
- Returns LangChain-compatible tools that work with any LangChain LLM
- Tools are automatically discovered - no manual registration needed
- The `tools` list can contain multiple tools from one or more MCP servers

#### Step 5: Bind Tools to the LLM

Attach the MCP tools to your LLM so it can see and use them.

**File: `mcp_client.py`**

**5.1: Get API Key and Model Configuration**

```57:64:mcp_client.py
    # LLM configuration - get API key from environment
    # Check both GOOGLE_GEMINI_API_KEY and GEMINI_API_KEY for compatibility
    google_api_key = os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_GEMINI_API_KEY or GEMINI_API_KEY environment variable is not set")
    
    # Get model name from environment, default to gemini-1.5-flash (more reliable on free tier)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
```

**5.2: Create LLM Instance**

```66:70:mcp_client.py
    llm = ChatGoogleGenerativeAI(
        model=model_name, 
        temperature=0, 
        google_api_key=google_api_key
    )
```

**5.3: Bind Tools to LLM**

```71:71:mcp_client.py
    llm_with_tools = llm.bind_tools(tools)
```

**What happens:**
- `bind_tools(tools)` registers the MCP tools with the LLM
- The LLM receives tool schemas (name, description, parameters)
- The LLM can now see available tools and decide when to use them
- When the LLM wants to call a tool, it generates a function call request

**Key Points:**
- Tools must be bound before creating the prompt chain
- The LLM uses tool descriptions to decide when tools are needed
- Tool calling is automatic - the LLM decides based on the conversation
- Multiple tools can be bound at once

#### Step 6: Create LangGraph Agent with Tool Routing

Use LangGraph to create an agent that automatically routes between chat and tool execution.

**File: `mcp_client.py`**

**6.1: Define State Schema**

```48:50:mcp_client.py
# LangGraph state definition
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
```

**6.2: Create Prompt Template**

```73:77:mcp_client.py
    # Prompt template with user/assistant chat only
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that uses tools to get the current weather for a location."),
        MessagesPlaceholder("messages")
    ])
```

**6.3: Chain Prompt with LLM**

```79:79:mcp_client.py
    chat_llm = prompt_template | llm_with_tools
```

**6.4: Define Chat Node**

```81:84:mcp_client.py
    # Define chat node
    def chat_node(state: State) -> State:
        state["messages"] = chat_llm.invoke({"messages": state["messages"]})
        return state
```

**What happens in chat_node:**
- Receives conversation state with messages
- Invokes the LLM (which may decide to call tools)
- Returns updated state with LLM response (or tool call requests)

**6.5: Build LangGraph with Nodes and Edges**

```86:95:mcp_client.py
    # Build LangGraph with tool routing
    graph = StateGraph(State)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tool_node", ToolNode(tools=tools))
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition, {
        "tools": "tool_node",
        "__end__": END
    })
    graph.add_edge("tool_node", "chat_node")
```

**6.6: Compile Graph with Checkpointer**

```97:97:mcp_client.py
    return graph.compile(checkpointer=MemorySaver())
```

**Graph Structure:**
```
START
  │
  ▼
chat_node ──→ [tools_condition] ──→ tool_node ──→ chat_node
  │                │                                    │
  │                └──→ (no tools) ──→ END             │
  │                                                    │
  └───────────────────────────────────────────────────┘
                    (loop until no tools)
```

**How it works:**
1. **START** → **chat_node**: User message enters the graph
2. **chat_node**: LLM processes the message, may decide to call tools
3. **tools_condition**: Checks if LLM wants to call tools:
   - If yes → **tool_node** (executes tools)
   - If no → **END** (returns final response)
4. **tool_node**: Executes MCP tools via the session, adds tool results to state
5. **tool_node** → **chat_node**: Returns to chat with tool results
6. **chat_node**: LLM generates final response using tool results
7. Loop continues until no more tools are needed

**Key Components:**
- `ToolNode(tools=tools)` - Automatically executes tools when LLM requests them
- `tools_condition` - Pre-built condition that checks for tool calls
- `MemorySaver()` - Saves conversation state (enables multi-turn conversations)

#### Step 7: Execute the Agent

Run the agent and handle user interactions in a chat loop.

**File: `mcp_client.py`**

**7.1: Create Agent Graph (called from main)**

```106:106:mcp_client.py
            agent = await create_graph(session)
```

**7.2: Start Chat Loop**

```110:116:mcp_client.py
            while True:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in {"exit", "quit", "q"}:
                    break

                if not user_input:
                    continue
```

**7.3: Invoke Agent with User Message**

```118:123:mcp_client.py
                try:
                    # Create proper message format
                    response = await agent.ainvoke(
                        {"messages": [HumanMessage(content=user_input)]},
                        config={"configurable": {"thread_id": "weather-session"}}
                    )
```

**What happens during `ainvoke`:**
1. User message is added to state: `{"messages": [HumanMessage(...)]}`
2. Graph execution starts at `chat_node`
3. LLM processes the message and may generate tool calls
4. If tools are called:
   - `tool_node` executes tools via MCP session
   - Tool results are added to state
   - Returns to `chat_node` for final response
5. Final response is returned in `response["messages"]`

**7.4: Extract and Display Response**

```125:130:mcp_client.py
                    # Extract the last message content
                    last_message = response["messages"][-1]
                    if hasattr(last_message, 'content'):
                        print("AI:", last_message.content)
                    else:
                        print("AI:", str(last_message))
```

**7.5: Error Handling**

```131:134:mcp_client.py
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
```

**Complete Execution Flow Example:**

```
User: "What's the weather in San Diego?"
  │
  ▼
agent.ainvoke({"messages": [HumanMessage("What's the weather in San Diego?")]})
  │
  ▼
chat_node: LLM analyzes query → decides to call get_weather("San Diego")
  │
  ▼
tools_condition: Detects tool call → routes to tool_node
  │
  ▼
tool_node: Executes get_weather via MCP session
  │
  │ (MCP Protocol)
  ▼
weather_server.get_weather("San Diego")
  │
  │ (HTTP Request)
  ▼
OpenWeatherMap API → Returns weather data
  │
  │ (MCP Response)
  ▼
tool_node: Receives {"location": "San Diego", "temperature": "18.81°C", ...}
  │
  ▼
chat_node: LLM receives tool results → generates natural language response
  │
  ▼
Response: "The weather in San Diego is scattered clouds, 18.81°C..."
  │
  ▼
User sees: "AI: The weather in San Diego is scattered clouds, 18.81°C..."
```

**Key Points:**
- `thread_id` in config maintains conversation state across multiple turns
- `HumanMessage` wraps user input in proper LangChain message format
- The graph handles all tool routing automatically
- Tool execution is transparent to the user - they just see the final answer

### Complete Flow Diagram

```
User Query: "What's the weather in San Diego?"
    │
    ▼
┌─────────────────────────────────────┐
│  LangGraph Agent (mcp_client.py)   │
│  ┌───────────────────────────────┐ │
│  │ chat_node                     │ │
│  │ - LLM analyzes query          │ │
│  │ - Decides to use get_weather  │ │
│  └───────────┬───────────────────┘ │
│              │                       │
│              ▼                       │
│  ┌───────────────────────────────┐ │
│  │ tool_node                     │ │
│  │ - Calls get_weather tool      │ │
│  └───────────┬───────────────────┘ │
└──────────────┼───────────────────────┘
               │
               │ (MCP Protocol over stdio)
               ▼
┌─────────────────────────────────────┐
│  FastMCP Weather Server             │
│  (weather_server.py)                │
│  ┌───────────────────────────────┐ │
│  │ get_weather("San Diego")      │ │
│  │ - Calls OpenWeatherMap API    │ │
│  │ - Returns weather data        │ │
│  └───────────┬───────────────────┘ │
└──────────────┼───────────────────────┘
               │
               │ (weather data)
               ▼
┌─────────────────────────────────────┐
│  LangGraph Agent                     │
│  ┌───────────────────────────────┐ │
│  │ chat_node                     │ │
│  │ - Receives weather data      │ │
│  │ - Generates natural response  │ │
│  └───────────┬───────────────────┘ │
└──────────────┼───────────────────────┘
               │
               ▼
User receives: "The weather in San Diego is scattered clouds, 
                18.81°C, humidity 75%, wind speed 3.09 m/s."
```

### Key Implementation Details

#### 1. Environment Variable Handling

Both the agent and MCP server need access to API keys:

**Agent (`mcp_client.py`):**
```python:7:21:mcp_client.py
# Try to load from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Try to load .env from parent directory (where it's located)
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        # Fallback to current directory
        load_dotenv(override=True)
except ImportError:
    pass  # python-dotenv not installed, use environment variables only
except Exception:
    pass  # Silently fail if .env loading has issues
```

**MCP Server (`weather_server.py`):**
```python:7:19:weather_server.py
# Try to load from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Try to load .env from parent directory (where it's located)
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to current directory
        load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use environment variables only
```

**Important:** The MCP server runs as a subprocess, so environment variables must be passed explicitly via `env=os.environ.copy()` in `StdioServerParameters`.

#### 2. Tool Definition Best Practices

**Good Tool Definition:**
```python
@mcp.tool()
def get_weather(location: str) -> dict:
    """
    Fetches the current weather for a specified location.
    
    Args:
        location: The city name and optional country code (e.g., "London,uk").
    
    Returns:
        A dictionary containing weather information or an error message.
    """
    # Clear docstring helps LLM understand when to use the tool
    # Type hints help with validation
    # Return dict is flexible for structured data
```

**Key Points:**
- Clear docstrings help the LLM understand tool purpose
- Type hints enable automatic validation
- Return dictionaries for structured data
- Handle errors gracefully and return error dicts

#### 3. Error Handling

The weather server includes comprehensive error handling:

```python:81:93:weather_server.py
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return {"error": f"Could not find weather data for '{location}'. Please check the location name."}
        elif response.status_code == 401:
            return {"error": f"Authentication failed (401). API key used: {OPENWEATHERMAP_API_KEY[:10]}... The API key may be invalid or inactive."}
        else:
            return {"error": f"An HTTP error occurred: HTTP {response.status_code}: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"A network error occurred: {req_err}"}
    except KeyError:
        return {"error": "Received unexpected data format from the weather API."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
```

**Best Practices:**
- Always return error information in a consistent format
- Include helpful error messages
- Don't crash the server - return error dicts instead

### Testing Your MCP Integration

Use the provided test script to verify everything works:

```bash
python test_mcp_setup.py
```

This tests:
1. Environment variables are set
2. MCP server can start and connect
3. Tools are discoverable
4. Tool execution works
5. LangChain integration works

### Summary: The Complete Procedure

1. **Create MCP Server** - Use FastMCP to define tools with `@mcp.tool()`
2. **Configure Connection** - Use `StdioServerParameters` to specify how to run the server
3. **Establish Connection** - Use `stdio_client()` and `ClientSession` to connect
4. **Load Tools** - Use `load_mcp_tools()` to convert MCP tools to LangChain tools
5. **Bind to LLM** - Use `llm.bind_tools()` to make tools available
6. **Create Agent Graph** - Use LangGraph to route between chat and tools
7. **Execute** - Run the agent and handle user interactions

This procedure works for any MCP tool, not just weather. You can create MCP servers for filesystem operations, database queries, API integrations, and more!

---

**Main Implementation: `mcp_client.py`**
- Uses LangGraph for agent orchestration
- Uses LangChain for LLM integration
- Uses `langchain_mcp_adapters` for seamless MCP integration
- Automatic tool routing and state management

**Alternative: `mcp_client_simple.py`** (optional, minimal version)
- No LangChain/LangGraph dependencies
- Direct MCP SDK usage
- Good for learning or minimal setups

## Architecture

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      LangGraph Agent                │
│  (mcp_client.py)                    │
│  - Uses Google Gemini LLM           │
│  - Manages conversation state    │
└────────┬────────────────────────────┘
         │
         │ (MCP Protocol over stdio)
         ▼
┌─────────────────────────────────────┐
│      FastMCP Weather Server         │
│  (weather_server.py)                │
│  - Provides get_weather tool        │
│  - Connects to OpenWeatherMap API  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ OpenWeatherMap  │
│      API       │
└─────────────────┘
```

## Components

### 1. `mcp_client.py` - The Agent
- **Purpose**: Main agent that orchestrates conversations using LangGraph
- **LLM**: Google Gemini 2.0 Flash
- **Framework**: LangGraph for agent orchestration
- **MCP Integration**: Uses `langchain_mcp_adapters` to load tools from MCP server

### 2. `weather_server.py` - The MCP Server
- **Purpose**: FastMCP server that provides weather tools
- **Tool**: `get_weather(location: str)` - Fetches current weather for a location
- **API**: Uses OpenWeatherMap API

## Setup

### 1. Install Dependencies

```bash
pip install mcp langchain-google-genai langgraph langchain langchain-core langchain-mcp-adapters requests
```

### 2. Set Up API Keys

**You need two API keys:**
1. **Google Gemini API Key** - For the LLM
2. **OpenWeatherMap API Key** - For weather data

**Quick Setup (Option 1 - Environment Variables):**
```bash
export GOOGLE_GEMINI_API_KEY="your-gemini-api-key-here"
export OPENWEATHERMAP_API_KEY="your-openweathermap-api-key-here"
```

**Quick Setup (Option 2 - .env file):**
```bash
# Install python-dotenv (optional, but recommended)
pip install python-dotenv

# Create .env file
cat > .env << EOF
GOOGLE_GEMINI_API_KEY=your-gemini-api-key-here
OPENWEATHERMAP_API_KEY=your-openweathermap-api-key-here
EOF
```

**📖 For detailed setup instructions, see [SETUP.md](SETUP.md)**

**Quick Links:**
- Get Gemini API Key: https://aistudio.google.com/app/apikey
- Get OpenWeatherMap API Key: https://openweathermap.org/api

## Usage

### Running the Agent

```bash
cd agents/agent_with_mcp
python mcp_client.py
```

### Example Conversation

```
You: What's the weather in San Francisco?
AI: The current weather in San Francisco is 68°F (20°C) with partly cloudy skies. The humidity is 65% and wind speed is 5 m/s.

You: How about London?
AI: The current weather in London is 15°C with light rain. The humidity is 78% and wind speed is 3 m/s.

You: exit
```

## How It Works

### 1. Agent Initialization
- The agent starts and creates an MCP client connection
- Connects to the weather server via stdio (standard input/output)
- Loads available tools from the MCP server
- Initializes the LangGraph agent with the tools

### 2. User Query Processing
- User enters a query
- LangGraph processes the query through the chat node
- The LLM (Gemini) decides if it needs to use a tool

### 3. Tool Execution
- If weather information is needed, the LLM calls the `get_weather` tool
- The MCP client sends the tool call to the weather server
- The weather server queries OpenWeatherMap API
- Results are returned to the agent

### 4. Response Generation
- The LLM receives the weather data
- Generates a natural language response
- Returns the response to the user

## Code Structure

### Key Functions in `mcp_client.py`

- `create_graph(session)`: Creates the LangGraph agent with MCP tools
- `main()`: Entry point that manages the MCP connection and chat loop

### Key Functions in `weather_server.py`

- `get_weather(location: str)`: MCP tool that fetches weather data
- `mcp.run(transport="stdio")`: Starts the FastMCP server

## Troubleshooting

### Error: "GOOGLE_GEMINI_API_KEY environment variable is not set"
- **Solution**: Set the environment variable before running:
  ```bash
  export GOOGLE_GEMINI_API_KEY="your-key"
  ```

### Error: "OpenWeatherMap API key is not configured"
- **Solution**: Set the `OPENWEATHERMAP_API_KEY` environment variable

### Error: "Import langchain_mcp_adapters could not be resolved"
- **Solution**: Install the package:
  ```bash
  pip install langchain-mcp-adapters
  ```

### Error: Weather server not found
- **Solution**: Make sure `weather_server.py` is in the same directory as `mcp_client.py`

### Agent doesn't use weather tool
- **Check**: The system prompt guides the LLM to use weather tools
- **Check**: Make sure the MCP connection is established (you should see "Weather MCP agent is ready")

## Extending the Agent

### Adding More MCP Tools

1. Add new tools to `weather_server.py`:
```python
@mcp.tool()
def get_forecast(location: str, days: int) -> dict:
    """Get weather forecast for a location."""
    # Implementation here
    pass
```

2. The tools will automatically be available to the agent after restarting.

### Using Different MCP Servers

You can modify `server_params` in `mcp_client.py` to connect to different MCP servers:

```python
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-weather"]
)
```

## Why LangChain/LangGraph?

This implementation uses LangChain and LangGraph for several benefits:

1. **Automatic Tool Routing**: LangGraph's `tools_condition` automatically routes between chat and tool execution
2. **State Management**: Built-in conversation state management with checkpoints
3. **Tool Integration**: `langchain_mcp_adapters` seamlessly converts MCP tools to LangChain tools
4. **Extensibility**: Easy to add more nodes, conditional logic, and complex workflows
5. **Production Ready**: Better error handling, retry logic, and observability

## Alternative Approaches

**Simple version** (`mcp_client_simple.py` - optional):
- Direct MCP SDK + Google Gemini SDK
- Manual tool calling loop
- Minimal dependencies
- Good for learning or very simple use cases

**Google ADK approach** (used in other examples):
- Uses `google-adk` package with `MCPToolset`
- Automatic tool discovery and execution
- Tightly integrated with Gemini models
- Requires `google-adk` package

## Next Steps

- Add more MCP servers (filesystem, database, etc.)
- Implement conversation memory persistence
- Add streaming responses
- Create a web interface
- Add error recovery and retry logic

