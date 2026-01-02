# Weather MCP Implementation Walkthrough

This document explains how the weather MCP (Model Context Protocol) is implemented in the Orel agent, step by step.

## Overview

The weather MCP integration allows Orel to access real-time weather information through an external MCP server. The implementation follows this flow:

```
Environment Config (.env) 
  → Backend Configuration (main.py)
  → Agent Initialization (multimodal_agent.py)
  → MCP Toolset Creation
  → Model Registration
  → Tool Execution (when user asks about weather)
```

---

## Step 1: Environment Configuration

**File:** `.env`

```bash
WEATHER_MCP_TYPE=stdio
```

This tells the system to use a **stdio-based** weather MCP server (the simplest option, no API keys needed).

**Alternative configurations:**
- `WEATHER_MCP_TYPE=sse` - For Server-Sent Events based server
- `WEATHER_MCP_TYPE=http` - For HTTP-based server

---

## Step 2: Backend Configuration

**File:** `super_personal_agent/backend/main.py`

**Location:** `get_agent()` function (lines 46-90)

```python
def get_agent():
    """Get or create the agent instance."""
    global agent
    if agent is None:
        try:
            # Check for MCP weather server configuration
            mcp_config = None
            weather_mcp_type = os.getenv("WEATHER_MCP_TYPE", "").strip().lower()
            
            if weather_mcp_type == "stdio":
                # Use stdio-based weather MCP server
                mcp_config = {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-weather"],
                    "env": {}
                }
                print("🌤️  Configuring weather MCP server (stdio)...")
            # ... (SSE and HTTP options)
            
            agent = MultimodalAgent(mcp_config=mcp_config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")
    return agent
```

**What happens here:**
1. Reads `WEATHER_MCP_TYPE` from environment variables
2. Creates an `mcp_config` dictionary with connection details
3. For `stdio` type:
   - Command: `npx` (Node.js package runner)
   - Args: `["-y", "@modelcontextprotocol/server-weather"]` (auto-install and run weather server)
   - This will execute: `npx -y @modelcontextprotocol/server-weather`
4. Passes `mcp_config` to `MultimodalAgent` constructor

---

## Step 3: MCP Availability Check

**File:** `examples/multimodal_agent.py`

**Location:** Lines 90-115

```python
# Check if MCP is available
try:
    from google.adk.tools.mcp_tool import MCPToolset
    # Try new API first, fallback to old API for compatibility
    try:
        from google.adk.tools.mcp_tool.mcp_session_manager import (
            SseServerParams,
            StreamableHTTPServerParams,
            StdioConnectionParams  # New recommended API
        )
        USE_NEW_MCP_API = True
    except ImportError:
        # Fallback to old API
        from google.adk.tools.mcp_tool.mcp_session_manager import (
            SseServerParams,
            StreamableHTTPServerParams,
            StdioServerParameters  # Old API (deprecated)
        )
        USE_NEW_MCP_API = False
    MCP_AVAILABLE = True
    print("✅ MCP support available")
except ImportError as e:
    MCP_AVAILABLE = False
    USE_NEW_MCP_API = False
    print(f"⚠️  MCP not available: {e}")
    print("   Continuing without MCP tools...")
```

**What happens here:**
1. Checks if `google-adk` package is installed (provides MCP support)
2. Tries to import the new API (`StdioConnectionParams`) first
3. Falls back to old API (`StdioServerParameters`) if new API not available
4. Sets `MCP_AVAILABLE` flag for later use

---

## Step 4: MCP Toolset Creation Functions

**File:** `examples/multimodal_agent.py`

**Location:** Lines 159-193

### Stdio Toolset Creation

```python
def create_mcp_toolset_stdio(command: str, args: list = None, env: Dict[str, str] = None) -> 'MCPToolset':
    """
    Create MCP toolset for stdio-based MCP server.
    
    Args:
        command: Command to run the MCP server (e.g., "npx", "python")
        args: Command arguments (e.g., ["-y", "@modelcontextprotocol/server-weather"])
        env: Environment variables for the server
    
    Returns:
        MCPToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available. Requires Python 3.10+ and google-adk package.")
    
    # Use new API if available, fallback to old API
    if USE_NEW_MCP_API:
        return MCPToolset(
            connection_params=StdioConnectionParams(
                command=command,
                args=args or [],
                env=env or {},
            )
        )
    else:
        # Fallback to old API (deprecated but still works)
        return MCPToolset(
            connection_params=StdioServerParameters(
                command=command,
                args=args or [],
                env=env or {},
            )
        )
```

**What happens here:**
1. Creates an `MCPToolset` object
2. Configures it with `StdioConnectionParams` (or `StdioServerParameters` for old API)
3. The `MCPToolset` will:
   - Start the MCP server process using the command and args
   - Establish a stdio (standard input/output) connection
   - Discover available tools from the server
   - Make those tools available to the agent

**Key Point:** The MCP server process is started automatically when the toolset is created, and communication happens via stdin/stdout.

---

## Step 5: Agent Initialization

**File:** `examples/multimodal_agent.py`

**Location:** `MultimodalAgent.__init__()` (lines 620-717)

### 5.1: MCP Configuration Processing

```python
class MultimodalAgent:
    def __init__(self, model_name: str = None, mcp_config: Dict[str, Any] = None):
        # ... model setup ...
        
        # Setup MCP toolsets if configured
        mcp_toolsets = []
        if mcp_config and MCP_AVAILABLE:
            try:
                # Handle single server config
                if "type" in mcp_config:
                    mcp_toolset = self._create_mcp_toolset_from_config(mcp_config)
                    if mcp_toolset:
                        mcp_toolsets.append(mcp_toolset)
                # Handle multiple servers config
                elif "servers" in mcp_config:
                    for server_config in mcp_config["servers"]:
                        mcp_toolset = self._create_mcp_toolset_from_config(server_config)
                        if mcp_toolset:
                            mcp_toolsets.append(mcp_toolset)
            except Exception as e:
                print(f"⚠️  Error setting up MCP toolsets: {e}")
                print("   Continuing without MCP tools...")
```

**What happens here:**
1. Checks if `mcp_config` is provided and MCP is available
2. Handles single server config (our case) or multiple servers
3. Calls `_create_mcp_toolset_from_config()` to create the toolset

### 5.2: MCP Toolset Creation from Config

**Location:** Lines 719-756

```python
def _create_mcp_toolset_from_config(self, config: Dict[str, Any]) -> Optional['MCPToolset']:
    """
    Create an MCP toolset from a configuration dictionary.
    
    Args:
        config: MCP server configuration dict
    
    Returns:
        MCPToolset instance or None if creation fails
    """
    if not MCP_AVAILABLE:
        return None
    
    try:
        mcp_type = config.get("type", "").lower()
        
        if mcp_type == "stdio":
            return create_mcp_toolset_stdio(
                command=config.get("command", "npx"),
                args=config.get("args", []),
                env=config.get("env", {})
            )
        elif mcp_type == "sse":
            return create_mcp_toolset_sse(
                server_url=config.get("url", ""),
                headers=config.get("headers", {})
            )
        elif mcp_type == "http":
            return create_mcp_toolset_http(
                server_url=config.get("url", ""),
                headers=config.get("headers", {})
            )
        else:
            print(f"⚠️  Unknown MCP type: {mcp_type}. Supported: stdio, sse, http")
            return None
    except Exception as e:
        print(f"⚠️  Error creating MCP toolset: {e}")
        return None
```

**What happens here:**
1. Extracts the MCP type from config (`"stdio"` in our case)
2. Calls the appropriate creation function (`create_mcp_toolset_stdio`)
3. Passes command, args, and env from config
4. Returns the `MCPToolset` instance

### 5.3: Tools List Creation

**Location:** Lines 689-690

```python
# Create tools list with MCP toolsets
tools = create_tools_list(mcp_toolsets) if mcp_toolsets else TOOLS
```

**Location:** `create_tools_list()` function (lines 439-570)

```python
def create_tools_list(mcp_toolsets: List['MCPToolset'] = None) -> List:
    """
    Create the list of tools for the agent.
    
    Args:
        mcp_toolsets: List of MCPToolset instances to add
    
    Returns:
        List of tools (function declarations + MCP toolsets)
    """
    tools = [
        {
            "function_declarations": [
                # ... native tools (analyze_image, generate_image, etc.) ...
            ]
        }
    ]
    
    # Add MCP toolsets
    if mcp_toolsets:
        for toolset in mcp_toolsets:
            tools.append(toolset)
            print(f"✅ Added MCP toolset: {type(toolset).__name__}")
    
    return tools
```

**What happens here:**
1. Creates a list starting with native function declarations
2. Appends MCP toolsets to the list
3. The `MCPToolset` objects are added directly (Google ADK handles them specially)
4. Returns the combined tools list

### 5.4: Model Initialization with Tools

**Location:** Lines 692-717

```python
self.model = genai.GenerativeModel(
    model_name=m,
    system_instruction=SYSTEM_INSTRUCTION,
    tools=tools  # Includes MCP toolsets!
)
```

**What happens here:**
1. Creates a Gemini model instance
2. Registers all tools (native + MCP toolsets)
3. Google ADK automatically:
   - Connects to the MCP server (starts the process for stdio)
   - Discovers available tools from the server
   - Makes them available to the LLM
   - Handles tool execution when the LLM requests it

---

## Step 6: System Instruction

**File:** `examples/multimodal_agent.py`

**Location:** Lines 582-586

```python
**Weather Information**: If MCP weather tools are available, use them to get current weather conditions, forecasts, and weather-related information. Weather tools provide accurate, real-time weather data. Use weather tools when:
- User asks about current weather conditions
- User asks for weather forecasts
- User asks about weather in a specific location
- User needs weather-related information
```

**What happens here:**
- Guides the LLM on when to use weather tools
- The LLM sees this instruction and knows to use MCP weather tools for weather queries

---

## Step 7: Tool Execution Flow

When a user asks: **"What's the weather in San Francisco?"**

### 7.1: User Query Processing

**File:** `examples/multimodal_agent.py`

**Location:** `run()` method (lines 758-850)

```python
def run(self, user_input: str, image_path: Optional[str] = None) -> str:
    # Add user message to history
    self.history.append({"role": "user", "parts": [user_input]})
    
    # Generate response
    response = self.model.generate_content(self.history)
```

### 7.2: LLM Decides to Use Weather Tool

The LLM (Gemini) analyzes the query and:
1. Recognizes it's a weather question (from system instruction)
2. Sees available weather tools from the MCP toolset
3. Decides to call a weather tool (e.g., `get_current_weather`)
4. Generates a function call request

### 7.3: Tool Execution

Google ADK handles the execution:
1. Receives the function call from the LLM
2. Identifies it's an MCP tool (not a native Python function)
3. Sends the request to the MCP server via stdio
4. MCP server processes the request (queries weather API)
5. Returns weather data
6. Google ADK passes the result back to the LLM

### 7.4: Final Response Generation

The LLM:
1. Receives weather data from the tool
2. Synthesizes a natural language response
3. Returns: *"The current weather in San Francisco is 68°F (20°C) with partly cloudy skies..."*

---

## Architecture Diagram

```
┌─────────────────┐
│   User Query    │
│ "Weather in SF?"│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     MultimodalAgent.run()           │
│  - Adds query to history            │
│  - Calls model.generate_content()   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Gemini Model (genai.Generative)   │
│  - Sees weather tools from MCP      │
│  - Decides to call get_current_weather│
│  - Generates function call          │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      Google ADK (MCPToolset)        │
│  - Receives function call           │
│  - Routes to MCP server             │
└────────┬────────────────────────────┘
         │
         │ (stdio communication)
         ▼
┌─────────────────────────────────────┐
│   Weather MCP Server Process        │
│   (npx @modelcontextprotocol/       │
│    server-weather)                  │
│  - Receives get_current_weather()  │
│  - Queries weather API              │
│  - Returns weather data             │
└────────┬────────────────────────────┘
         │
         │ (weather data)
         ▼
┌─────────────────────────────────────┐
│      Google ADK (MCPToolset)        │
│  - Receives weather data            │
│  - Passes to LLM                    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Gemini Model                      │
│  - Receives weather data            │
│  - Generates natural response       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Final Response │
│ "SF: 68°F..."   │
└─────────────────┘
```

---

## Key Components Summary

| Component | Purpose | Location |
|-----------|---------|----------|
| `.env` | Configuration (WEATHER_MCP_TYPE) | Project root |
| `main.py` | Reads config, creates mcp_config dict | `super_personal_agent/backend/` |
| `MCPToolset` | Google ADK class for MCP integration | `google.adk.tools.mcp_tool` |
| `create_mcp_toolset_stdio()` | Creates stdio-based MCP toolset | `multimodal_agent.py:159` |
| `_create_mcp_toolset_from_config()` | Converts config dict to toolset | `multimodal_agent.py:719` |
| `create_tools_list()` | Combines native + MCP tools | `multimodal_agent.py:439` |
| `MultimodalAgent.__init__()` | Initializes agent with MCP tools | `multimodal_agent.py:620` |
| Weather MCP Server | External process providing weather tools | `@modelcontextprotocol/server-weather` |

---

## Important Points

1. **Automatic Process Management**: The MCP server process is started automatically when the toolset is created. You don't need to manually start it.

2. **Stdio Communication**: For stdio type, communication happens via standard input/output pipes. The MCP server runs as a subprocess.

3. **Tool Discovery**: Google ADK automatically discovers what tools the MCP server provides and makes them available to the LLM.

4. **Transparent to LLM**: The LLM doesn't know the difference between native Python tools and MCP tools. It just sees "available tools" and uses them.

5. **Error Handling**: If MCP setup fails, the agent continues without MCP tools (graceful degradation).

6. **Multiple MCP Servers**: The code supports multiple MCP servers (though we're only using one for weather).

---

## Testing the Implementation

1. **Check Configuration:**
   ```bash
   cat .env | grep WEATHER_MCP
   # Should show: WEATHER_MCP_TYPE=stdio
   ```

2. **Start Backend:**
   ```bash
   cd super_personal_agent
   ./start.sh
   ```
   Look for: `🌤️  Configuring weather MCP server (stdio)...`

3. **Test Query:**
   Ask Orel: "What's the weather in San Francisco?"
   
4. **Check Logs:**
   The backend logs will show MCP tool execution if you enable debug logging.

---

## Troubleshooting

- **MCP not available**: Make sure Python 3.10+ and `google-adk` package are installed
- **npx not found**: Install Node.js (required for stdio weather server)
- **Weather server fails**: Check that `@modelcontextprotocol/server-weather` can be installed via npx
- **No weather response**: Check backend logs for MCP connection errors

---

This implementation provides a clean, modular way to integrate external MCP servers into the agent, making it easy to add more MCP servers in the future (filesystem, database, etc.).

