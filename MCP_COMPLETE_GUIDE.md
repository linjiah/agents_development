# Complete MCP (Model Context Protocol) Guide for Google ADK

A comprehensive guide to integrating and using MCP with Google ADK agents, covering everything from basics to advanced use cases.

## Table of Contents

1. [Introduction](#introduction)
2. [Python Version Requirements](#python-version-requirements)
3. [How MCP Works with Google ADK](#how-mcp-works-with-google-adk)
4. [Connection Types: SSE, HTTP, and Stdio](#connection-types-sse-http-and-stdio)
5. [Real-World Use Cases](#real-world-use-cases)
6. [Specific Query Examples](#specific-query-examples)
7. [Integration Examples](#integration-examples)
8. [Code Walkthrough](#code-walkthrough)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Resources](#resources)

---

## Introduction

### What is MCP?

**Model Context Protocol (MCP)** is an open standard that defines how AI assistants connect to:
- External tools and APIs
- Data sources and databases
- File systems and documents
- Third-party services

**Created by:** Anthropic (open-sourced)  
**Adoption:** Supported by Google ADK, Claude, and growing ecosystem

### Key Components

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   LLM Agent │ ◄─────► │  MCP Client │ ◄─────► │  MCP Server │
│   (ADK)     │         │   (ADK)     │         │  (External) │
└─────────────┘         └─────────────┘         └─────────────┘
                                                       │
                                                       ▼
                                                 ┌──────────────┐
                                                 │  Tools/Data  │
                                                 │  Resources   │
                                                 └──────────────┘
```

### Why Use MCP?

| Aspect | MCP Advantage |
|--------|---------------|
| **Standardization** | Single protocol for all tools across different LLMs |
| **Ecosystem** | Growing library of pre-built MCP servers |
| **Separation** | Clean separation between agent logic and tool implementation |
| **Reusability** | Write once, use with multiple AI systems |
| **Community** | Open-source tools and contributions |
| **Security** | Standardized authentication and permissions |

### MCP vs Native Tools

**Native Tools** (Current approach):
- ✅ Simple and direct
- ✅ Full control over implementation
- ✅ No external dependencies
- ❌ Tied to specific LLM API format
- ❌ No reusability across systems

**MCP Tools**:
- ✅ Standardized protocol
- ✅ Use existing MCP servers
- ✅ Works across different LLMs
- ✅ Community contributions
- ❌ External dependency (MCP server)
- ❌ Requires network/process communication

**Recommendation: Hybrid Approach**
- Native tools for core, simple operations (calculator, basic utils)
- MCP for external services, complex integrations, community tools

---

## Python Version Requirements

### ⚠️ Critical Requirement

**MCP requires Python 3.10 or above.**

If you're using Python 3.9, you'll see:
```
MCP requires Python 3.10 or above. Please upgrade your Python version in order to use it.
```

### What Works on Python 3.9

✅ **Fully Supported:**
- Native tools (calculator, web_search, get_current_time, etc.)
- All basic agent functionality
- Tool calling and function execution
- Multi-agent systems
- Multimodal agents
- Everything in `tool_agent.py`, `simple_agent.py`, `multi_agent.py`

### What Requires Python 3.10+

❌ **Not Available:**
- MCP toolsets
- `tool_agent_with_mcp.py` MCP features
- External MCP server integration

### Solutions

**Option 1: Continue with Native Tools (Recommended for Python 3.9)**
- All agent functionality works perfectly
- No need to upgrade just for MCP
- All core concepts covered

**Option 2: Upgrade to Python 3.10+ (For MCP Support)**

```bash
# Install Python 3.11 (or 3.10, 3.12)
brew install python@3.11  # macOS
# or
sudo apt install python3.11 python3.11-venv  # Ubuntu/Debian

# Create new virtual environment
python3.11 -m venv ml_interview_env_py311
source ml_interview_env_py311/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install google-adk

# Verify MCP is available
python -c "from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset; print('✅ MCP available!')"
```

### Why MCP Requires Python 3.10+

1. **Pattern Matching** (Python 3.10+)
   - MCP SDK uses structural pattern matching
   - New syntax: `match/case` statements

2. **Type Hints** (Python 3.10+)
   - Union types: `X | Y` instead of `Union[X, Y]`
   - More expressive type annotations

3. **Dependencies**
   - MCP SDK dependencies require 3.10+
   - Modern async/await features

---

## How MCP Works with Google ADK

### Overview

MCP (Model Context Protocol) is a standardized protocol that allows AI agents to connect to external tool servers. In this implementation:

- **Native Tools**: Custom Python functions (calculator, web_search, get_current_time) defined directly in the code
- **MCP Tools**: Tools provided by external MCP servers, discovered and executed through the MCP protocol

The agent can use both types of tools seamlessly, with the LLM deciding which tool to call based on the user's request.

### Step 1: MCP Detection & Import

```python
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
```

**What happens**:
- Attempts to import MCP components from `google-adk` package
- Sets `MCP_AVAILABLE` flag to control MCP functionality
- If import fails, continues with native tools only

**Key Component**: `MCPToolset` - The main class that wraps MCP server connections and provides tools to the agent.

### Step 2: MCP Toolset Creation

Three factory functions create MCP toolsets for different connection types:

#### SSE (Server-Sent Events) Connection
```python
def create_mcp_toolset_sse(server_url: str, headers: Dict[str, str] = None):
    return MCPToolset(
        connection_params=SseServerParams(
            url=server_url,
            headers=headers or {},
        )
    )
```

#### HTTP Connection
```python
def create_mcp_toolset_http(server_url: str, headers: Dict[str, str] = None):
    return MCPToolset(
        connection_params=StreamableHTTPServerParams(
            url=server_url,
            headers=headers or {},
        )
    )
```

#### Stdio Connection
```python
def create_mcp_toolset_stdio(command: str, args: List[str] = None, env: Dict[str, str] = None):
    return MCPToolset(
        connection_params=StdioServerParameters(
            command=command,
            args=args or [],
            env=env or {},
        )
    )
```

### Step 3: Agent Registration

```python
def create_agent_with_mcp(use_native_tools: bool = True, mcp_config: Dict[str, Any] = None):
    tools = []
    
    # Add native tools (if enabled)
    if use_native_tools:
        tools.extend(NATIVE_TOOLS)  # Native tool schemas
    
    # Add MCP tools (if configured)
    if mcp_config and MCP_AVAILABLE:
        mcp_toolset = create_mcp_toolset_*(...)  # Based on type
        tools.append(mcp_toolset)  # ← MCP toolset added here
    
    # Create agent with all tools
    model = genai.GenerativeModel(
        model_name=model_name,
        tools=tools,  # ← Both native and MCP tools
        system_instruction=system_instruction
    )
```

**What happens**:
1. **Native tools** are added as function declaration schemas (JSON-like structures)
2. **MCP toolset** is added as a tool object (not a schema - it's a live connection)
3. The `GenerativeModel` receives both types in the `tools` parameter
4. Google ADK automatically:
   - Connects to the MCP server (if not already connected)
   - Discovers available tools from the MCP server
   - Converts MCP tool schemas to Gemini function declarations
   - Makes all tools available to the LLM

**Key Insight**: The LLM sees both native and MCP tools as function declarations, but they're executed differently:
- Native tools: Executed by your Python code
- MCP tools: Executed by the MCP server via ADK

### Step 4: Tool Discovery

**What happens** (behind the scenes):
1. When `MCPToolset` is added to the agent, ADK connects to the MCP server
2. ADK sends an MCP protocol request: `tools/list` to discover available tools
3. The MCP server responds with tool definitions (name, description, parameters)
4. ADK converts these MCP tool definitions to Gemini function declarations
5. The LLM receives a combined list of:
   - Native tool function declarations (from `NATIVE_TOOLS`)
   - MCP tool function declarations (from MCP server)

**Example**: If an MCP server provides a `read_file` tool, the LLM will see:
```json
{
  "name": "read_file",
  "description": "Read contents of a file",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {"type": "string", "description": "File path"}
    }
  }
}
```

The LLM doesn't know (or care) whether this is a native tool or an MCP tool - it just sees available functions.

### Step 5: Tool Execution Flow

#### 5.1 LLM Decides to Use a Tool

When the user asks a question, the LLM:
1. Analyzes the request
2. Decides which tool to call (native or MCP)
3. Generates a function call with tool name and arguments

```python
response = agent.generate_content(conversation_history)

# Check for function calls in response
for part in response.candidates[0].content.parts:
    if hasattr(part, 'function_call') and part.function_call:
        function_call = part.function_call
        function_name = function_call.name  # e.g., "read_file" or "calculator"
```

#### 5.2 Native Tool Execution (Manual)

```python
if is_native_tool(function_name):
    # 1. Execute the Python function
    tool_result = execute_tool(function_name, args)
    
    # 2. Add function call to conversation history
    conversation_history.append({
        "role": "model",
        "parts": [{"function_call": function_call}]
    })
    
    # 3. Add function response to conversation history
    conversation_history.append({
        "role": "function",
        "parts": [{
            "function_response": {
                "name": function_name,
                "response": {"result": tool_result}
            }
        }]
    })
    
    # 4. Get final LLM response with tool result
    final_response = agent.generate_content(conversation_history)
```

**Flow**:
1. Your code executes the Python function
2. You manually add function call + response to conversation history
3. You call the LLM again to synthesize the final response

#### 5.3 MCP Tool Execution (ADK Handles It)

```python
else:
    # MCP tool - ADK handles execution automatically
    # 1. Add function call to conversation history
    conversation_history.append({
        "role": "model",
        "parts": [{"function_call": function_call}]
    })
    
    # 2. Call generate_content - ADK automatically:
    #    - Sends tool call to MCP server via MCP protocol
    #    - Waits for MCP server response
    #    - Integrates result into conversation
    final_response = agent.generate_content(conversation_history)
    
    # 3. Extract response (may already include tool result)
    response_text = final_response.text
```

**Flow**:
1. You add the function call to conversation history
2. **ADK automatically**:
   - Detects this is an MCP tool (via `MCPToolset`)
   - Sends MCP protocol request: `tools/call` with tool name and arguments
   - MCP server executes the tool and returns result
   - ADK adds the function response to the conversation
   - ADK calls the LLM to synthesize the final response
3. You receive the final response (may already include tool result integrated)

**Key Difference**: With MCP tools, ADK handles the entire execution cycle automatically. You don't manually execute the tool or add the function response.

### Complete Execution Flow Diagram

```
User Query
    ↓
LLM Analyzes (sees all tools: native + MCP)
    ↓
LLM Decides: "I need to call tool X"
    ↓
    ├─→ Native Tool? ──→ Execute Python function ──→ Add to history ──→ LLM synthesizes
    │
    └─→ MCP Tool? ──→ ADK sends MCP request ──→ MCP server executes ──→ 
                      ADK receives result ──→ ADK adds to history ──→ LLM synthesizes
    ↓
Final Response to User
```

### Key Differences: Native vs MCP Tools

| Aspect | Native Tools | MCP Tools |
|--------|-------------|-----------|
| **Definition** | Python functions in your code | Tools from external MCP server |
| **Registration** | Function declaration schemas | `MCPToolset` object |
| **Discovery** | Static (defined in code) | Dynamic (from MCP server) |
| **Execution** | Manual (your code calls function) | Automatic (ADK via MCP protocol) |
| **Protocol** | Direct function call | MCP protocol (JSON-RPC-like) |
| **Error Handling** | Your code handles errors | ADK + MCP server handle errors |
| **Response Handling** | You add function_response manually | ADK adds it automatically |

---

## Connection Types: SSE, HTTP, and Stdio

MCP supports three different **transport mechanisms** for communicating with MCP servers. Think of them as three different "languages" or "channels" your agent can use to talk to MCP servers:

1. **SSE (Server-Sent Events)**: HTTP connection with real-time streaming
2. **HTTP**: Standard HTTP requests/responses
3. **Stdio**: Direct subprocess communication via stdin/stdout

**Important**: All three use the **same MCP protocol** - they just differ in **how** the messages are sent and received.

### 1. SSE (Server-Sent Events)

#### What It Is
SSE is an HTTP-based protocol where the server can push data to the client in real-time. It's like a one-way radio channel where the server broadcasts updates.

#### How It Works

```
Your Agent (Client)                    MCP Server
     |                                        |
     |--- HTTP GET /sse -------------------->|
     |                                        |
     |<-- HTTP 200 OK (keep connection open) -|
     |                                        |
     |<-- data: {"method": "tools/list"} ----|  (Server pushes data)
     |                                        |
     |--- POST /sse (tool call) ------------>|
     |                                        |
     |<-- data: {"result": "..."} -----------|  (Server pushes result)
```

**Technical Details**:
- Client opens a long-lived HTTP connection to the server
- Server keeps connection open and can send multiple messages
- Client can send requests via HTTP POST
- Server responds by pushing data through the open connection
- Connection stays alive for the session duration

#### When to Use SSE

✅ **Use SSE when**:
- MCP server is running as a web service (remote or local)
- You need real-time updates or streaming responses
- Server supports SSE protocol
- You want efficient, persistent connection

❌ **Don't use SSE when**:
- Server doesn't support SSE
- You need simple request/response (use HTTP instead)
- Server is a local subprocess (use stdio instead)

#### Code Example

```python
mcp_config = {
    "type": "sse",
    "url": "http://localhost:8001/sse",
    "headers": {
        "Authorization": f"Bearer {api_key}"
    }
}
```

### 2. HTTP (Streamable HTTP)

#### What It Is
Standard HTTP requests/responses - like REST API calls. Each tool call is a separate HTTP request.

#### How It Works

```
Your Agent (Client)                    MCP Server
     |                                        |
     |--- POST /mcp/tools/list ------------>|
     |                                        |
     |<-- 200 OK {"tools": [...]} ----------|
     |                                        |
     |--- POST /mcp/tools/call ------------>|
     |    {"tool": "read_file", "args": {...}}
     |                                        |
     |<-- 200 OK {"result": "..."} ----------|
```

**Technical Details**:
- Each MCP operation is a separate HTTP request
- Standard request/response pattern (no persistent connection)
- Can use any HTTP method (typically POST)
- Full control over headers, authentication, etc.
- Stateless - each request is independent

#### When to Use HTTP

✅ **Use HTTP when**:
- MCP server is a standard REST API
- You want simple request/response pattern
- Server doesn't support SSE
- You need full control over HTTP headers
- You're integrating with existing HTTP services

❌ **Don't use HTTP when**:
- You need real-time streaming (use SSE)
- Server is a local subprocess (use stdio)
- You want persistent connection efficiency (use SSE)

#### Code Example

```python
mcp_config = {
    "type": "http",
    "url": "https://api.example.com/mcp/",
    "headers": {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
}
```

### 3. Stdio (Standard Input/Output)

#### What It Is
Runs the MCP server as a **subprocess** (child process) and communicates via **stdin/stdout** - the same way you'd run a command-line tool.

#### How It Works

```
Your Agent (Parent Process)
     |
     |--- spawns subprocess ---> MCP Server (Child Process)
     |                              |
     |--- writes to stdin -------->|  (JSON-RPC messages)
     |                              |
     |<-- reads from stdout -------|  (JSON-RPC responses)
     |                              |
     |--- writes to stdin -------->|
     |                              |
     |<-- reads from stdout -------|
```

**Technical Details**:
- Agent spawns MCP server as a subprocess (like running `python script.py`)
- Communication happens via stdin (input) and stdout (output)
- Messages are JSON-RPC format sent as text lines
- Process stays alive for the session
- No network involved - all local communication

#### When to Use Stdio

✅ **Use Stdio when**:
- MCP server is a local tool/script
- Server runs as a command-line program
- You want to run server on-demand (not as a service)
- No network setup needed
- Server is Node.js, Python, or any executable

❌ **Don't use Stdio when**:
- Server is already running as a web service (use SSE/HTTP)
- Server is remote (use SSE/HTTP)
- You need to connect to existing service (use SSE/HTTP)

#### Code Example

```python
mcp_config = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
}
```

### Comparison Table

| Aspect | SSE | HTTP | Stdio |
|--------|-----|------|-------|
| **Transport** | HTTP with persistent connection | Standard HTTP requests | Subprocess stdin/stdout |
| **Connection** | Long-lived, persistent | Stateless, per-request | Process lifetime |
| **Network** | Yes (local or remote) | Yes (local or remote) | No (local only) |
| **Server Type** | Web service with SSE endpoint | REST API | Command-line program |
| **Setup** | Server must be running | Server must be running | Server runs on-demand |
| **Real-time** | ✅ Yes (streaming) | ❌ No | ❌ No |
| **Efficiency** | ✅ High (persistent) | ⚠️ Medium (per-request) | ✅ High (direct) |
| **Authentication** | HTTP headers | HTTP headers | Environment variables |
| **Use Case** | Cloud services, streaming | REST APIs, web services | Local tools, CLIs |
| **Example** | `http://localhost:8001/sse` | `https://api.com/mcp/` | `npx @mcp/server` |

### Decision Tree

```
Is the MCP server already running as a service?
│
├─ YES → Is it a web service?
│        │
│        ├─ YES → Does it support SSE?
│        │        │
│        │        ├─ YES → Use SSE (better for streaming)
│        │        └─ NO  → Use HTTP (standard REST)
│        │
│        └─ NO → Use HTTP (if it's a REST API)
│
└─ NO → Is it a command-line tool or script?
         │
         ├─ YES → Use Stdio (runs on-demand)
         └─ NO  → Start it as a service, then use SSE/HTTP
```

---

## Real-World Use Cases

### SSE Use Cases

#### 1. Real-Time Stock Trading Agent
**Scenario**: Monitor stock prices and execute trades in real-time.

```python
mcp_config = {
    "type": "sse",
    "url": "https://trading-mcp.example.com/sse",
    "headers": {"Authorization": f"Bearer {trading_api_key}"}
}
```

**Why SSE?**: Need real-time price updates (streaming), efficient persistent connection.

#### 2. Live Chat Support Agent
**Scenario**: Monitor multiple chat channels and respond to customer messages in real-time.

```python
mcp_config = {
    "type": "sse",
    "url": "https://chat-mcp.company.com/sse",
    "headers": {"Authorization": f"Bearer {support_token}"}
}
```

**Why SSE?**: Need to receive messages as they arrive (streaming), multiple channels need simultaneous monitoring.

#### 3. IoT Device Monitoring Agent
**Scenario**: Smart home agent that monitors sensors and controls devices in real-time.

```python
mcp_config = {
    "type": "sse",
    "url": "http://localhost:8080/iot/sse"
}
```

**Why SSE?**: Sensors send updates continuously, need immediate alerts.

### HTTP Use Cases

#### 1. Enterprise CRM Integration
**Scenario**: Sales agent that accesses customer data from Salesforce via REST API.

```python
mcp_config = {
    "type": "http",
    "url": "https://api.salesforce.com/mcp/v1",
    "headers": {
        "Authorization": f"Bearer {salesforce_token}",
        "X-API-Version": "58.0"
    }
}
```

**Why HTTP?**: CRM is already a REST API, standard request/response pattern.

#### 2. Payment Processing Agent
**Scenario**: E-commerce agent that processes payments through Stripe API.

```python
mcp_config = {
    "type": "http",
    "url": "https://api.stripe.com/mcp",
    "headers": {
        "Authorization": f"Bearer {stripe_secret_key}",
        "Stripe-Version": "2023-10-16"
    }
}
```

**Why HTTP?**: Payment APIs are standard REST, need full control over security headers.

#### 3. Cloud Storage Agent
**Scenario**: Agent that manages files in Google Drive via REST API.

```python
mcp_config = {
    "type": "http",
    "url": "https://www.googleapis.com/drive/v3/mcp",
    "headers": {"Authorization": f"Bearer {google_oauth_token}"}
}
```

**Why HTTP?**: Cloud storage APIs are REST-based, need OAuth tokens in headers.

### Stdio Use Cases

#### 1. Local File Management Agent
**Scenario**: Personal assistant that helps manage files on your local computer.

```python
mcp_config = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/documents"]
}
```

**Why Stdio?**: Runs locally, no network needed, direct file system access.

#### 2. Local Database Agent
**Scenario**: Agent that queries a local SQLite database (personal notes, todos).

```python
mcp_config = {
    "type": "stdio",
    "command": "python",
    "args": ["/path/to/sqlite_mcp_server.py"],
    "env": {"DB_PATH": "/Users/me/data/personal.db"}
}
```

**Why Stdio?**: Database is local file, privacy (data stays local), no network overhead.

#### 3. Code Analysis Agent
**Scenario**: Developer agent that analyzes your codebase for bugs and security issues.

```python
mcp_config = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-code-analysis", "/path/to/project"]
}
```

**Why Stdio?**: Analyzes local code, privacy (code doesn't leave your machine), fast (no network latency).

#### 4. Local Git Operations Agent
**Scenario**: Agent that helps with Git operations on your local repository.

```python
mcp_config = {
    "type": "stdio",
    "command": "python",
    "args": ["/path/to/git_mcp_server.py"],
    "env": {"GIT_REPO_PATH": "/Users/me/projects/myapp"}
}
```

**Why Stdio?**: Git operations are local, direct repository access, privacy (repo stays local).

---

## Specific Query Examples

### SSE Query Examples

#### Example 1: Real-Time Stock Monitoring
**User Query**: "Monitor AAPL stock price and alert me when it drops below $150"

**What Happens**:
1. LLM calls MCP tool: `monitor_stock_price(symbol="AAPL", threshold=150)`
2. SSE Connection: Agent connects to stock MCP server via SSE
3. Server streams price updates: `data: {"symbol": "AAPL", "price": 152.30}`
4. When price hits $149.95, server pushes alert
5. Agent immediately responds: "⚠️ Alert: AAPL dropped to $149.95!"

**Why SSE?**: Need continuous real-time updates, not just one-time query.

#### Example 2: Live Chat Support
**User Query**: "Monitor the support chat and respond to any customer asking about refunds"

**What Happens**:
1. LLM calls MCP tool: `monitor_chat_channel(channel="support", keywords=["refund"])`
2. SSE Connection: Agent connects to chat MCP server
3. Server streams new messages as they arrive
4. Agent detects "refund" keyword and responds automatically

**Why SSE?**: Need to receive messages as they arrive, not poll repeatedly.

### HTTP Query Examples

#### Example 1: CRM Customer Lookup
**User Query**: "Show me all customers from California who bought products in the last 30 days"

**What Happens**:
1. LLM calls MCP tool: `query_customers(state="California", date_range="last_30_days")`
2. HTTP Connection: Agent sends HTTP POST to CRM MCP server
3. Server executes SOQL query, returns JSON response
4. Agent formats and presents results

**Why HTTP?**: Standard REST API query, one-time request/response.

#### Example 2: Payment Processing
**User Query**: "Process a payment of $99.99 for order #12345"

**What Happens**:
1. LLM calls MCP tool: `process_payment(amount=99.99, order_id="12345")`
2. HTTP Connection: Agent sends HTTP POST to Stripe API
3. Stripe processes payment, returns transaction result
4. Agent confirms payment to user

**Why HTTP?**: Payment APIs are standard REST, need secure headers.

### Stdio Query Examples

#### Example 1: Local File Reading
**User Query**: "Read the file config.json in my project folder and tell me what database it uses"

**What Happens**:
1. LLM calls MCP tool: `read_file(path="/Users/me/projects/myapp/config.json")`
2. Stdio Connection: ADK spawns subprocess `npx -y @modelcontextprotocol/server-filesystem`
3. Process reads file, returns via stdout
4. Agent parses JSON, responds: "The config.json file uses PostgreSQL database on localhost:5432"

**Why Stdio?**: File is local, no network needed, direct file system access.

#### Example 2: Local Database Query
**User Query**: "Show me all my todos that are due this week"

**What Happens**:
1. LLM calls MCP tool: `query_todos(date_range="this_week")`
2. Stdio Connection: ADK spawns Python script that queries SQLite
3. Script returns results via stdout
4. Agent formats and presents to user

**Why Stdio?**: Database is local SQLite file, privacy (data stays local).

### Query Pattern Recognition

**SSE Queries** (Real-time, Streaming):
- "Monitor [something] in real-time"
- "Alert me when [event] happens"
- "Keep me updated on [live data]"
- "Watch for [changes/events]"

**HTTP Queries** (Standard API):
- "Show me [data] from [service]"
- "Query [database/CRM/system]"
- "Get [information] from [API]"
- "Process [transaction] via [service]"

**Stdio Queries** (Local Access):
- "Read [file] from my [local path]"
- "Query my local [database]"
- "Analyze my [local code/files]"
- "Check my [local system/git/files]"

---

## Integration Examples

### Example 1: Filesystem MCP Server

Access local filesystem via MCP:

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters
import google.generativeai as genai

# Create filesystem MCP toolset
filesystem_tools = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "/Users/username/documents"
        ]
    )
)

# Create agent
agent = genai.GenerativeModel(
    model_name="gemini-2.5",
    tools=[filesystem_tools],
    system_instruction="You are a file management assistant."
)

# Run
response = agent.generate_content("Read the file notes.txt")
print(response.text)
```

**Available operations**:
- `read_file(path)` - Read file contents
- `list_directory(path)` - List files in directory
- `search_files(pattern)` - Search for files matching pattern

### Example 2: Combining Native + MCP Tools

Best of both worlds:

```python
import google.generativeai as genai
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

# Native tools (simple, core functionality)
NATIVE_TOOLS = [{
    "function_declarations": [{
        "name": "calculator",
        "description": "Calculate mathematical expressions",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    }]
}]

# MCP tools (complex integrations)
github_mcp = MCPToolset(
    connection_params=SseServerParams(url="http://localhost:8001/sse")
)

slack_mcp = MCPToolset(
    connection_params=SseServerParams(url="http://localhost:8002/sse")
)

# Combine in agent
agent = genai.GenerativeModel(
    model_name="gemini-2.5",
    tools=NATIVE_TOOLS + [github_mcp, slack_mcp],
    system_instruction="""You are a development assistant with:
    - Calculator for quick math
    - GitHub integration for code management
    - Slack integration for team communication
    
    Help developers with their workflow."""
)
```

### Example 3: Database MCP Server

Query databases via MCP:

```python
db_tools = MCPToolset(
    connection_params=SseServerParams(
        url="http://localhost:8002/mcp/sse",
        headers={
            "X-Database": "production",
            "X-API-Key": os.getenv("DB_MCP_KEY")
        }
    )
)

agent = genai.GenerativeModel(
    model_name="gemini-2.5",
    tools=[db_tools],
    system_instruction="""You are a data analyst assistant.
    You can query the database, analyze data, and create reports.
    Always explain queries in plain language before running them."""
)
```

**Available operations**:
- `query_database(sql_query)`
- `get_table_schema(table_name)`
- `list_tables()`

---

## Code Walkthrough

### Key Code Sections in `tool_agent_with_mcp.py`

#### 1. MCP Import & Availability Check (Lines 211-224)

```python
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
```

**What to understand**:
- `MCPToolset` is the main class that wraps MCP server connections
- Connection parameters differ by transport type (SSE, HTTP, stdio)
- If import fails, the code gracefully degrades to native tools only

#### 2. Agent Creation with MCP (Lines 295-375)

```python
def create_agent_with_mcp(use_native_tools: bool = True, mcp_config: Dict[str, Any] = None):
    tools = []
    
    # Add native tools
    if use_native_tools:
        tools.extend(NATIVE_TOOLS)  # ← Function declaration schemas
        print(f"✅ Loaded {len(NATIVE_TOOL_FUNCTIONS)} native tools")
    
    # Add MCP tools
    if mcp_config and MCP_AVAILABLE:
        # ... create mcp_toolset based on type ...
        tools.append(mcp_toolset)  # ← MCPToolset object (not a schema!)
        print(f"✅ Loaded MCP toolset from ...")
    
    model = genai.GenerativeModel(
        model_name=model_name,
        tools=tools,  # ← Contains both native schemas AND MCPToolset
        system_instruction=system_instruction
    )
```

**Critical understanding**:
- **Native tools**: Added as **schemas** (JSON function declarations)
- **MCP tools**: Added as **MCPToolset object** (live connection)
- Both go into the same `tools` list, but ADK handles them differently

#### 3. Tool Execution: Detection (Lines 457-469)

```python
response = agent.generate_content(conversation_history)

# Check for function calls
function_call = None
text_parts = []

for part in response.candidates[0].content.parts:
    if hasattr(part, 'function_call') and part.function_call:
        function_call = part.function_call  # ← Tool call detected
        if debug:
            print(f"\n🔧 FUNCTION CALL DETECTED: {function_call.name}")
            print(f"   Arguments: {dict(function_call.args)}")
    elif hasattr(part, 'text') and part.text:
        text_parts.append(part.text)
```

**What to understand**:
- LLM response can contain: text, function_call, or both
- Function call includes: `name` (tool name) and `args` (parameters)
- We need to check which type of tool was called

#### 4. Tool Execution: Native vs MCP (Lines 483-600)

**Native Tool Execution** (Manual):
```python
if is_native_tool(function_name):
    # 1. Execute the Python function
    tool_result = execute_tool(function_name, args)
    
    # 2. Add function call to conversation history
    conversation_history.append({
        "role": "model",
        "parts": [{"function_call": function_call}]
    })
    
    # 3. Add function response to conversation history
    conversation_history.append({
        "role": "function",
        "parts": [{
            "function_response": {
                "name": function_name,
                "response": {"result": tool_result}
            }
        }]
    })
    
    # 4. Get final LLM response
    final_response = agent.generate_content(conversation_history)
```

**MCP Tool Execution** (Automatic):
```python
else:
    # MCP tool - ADK handles execution automatically
    # 1. Add function call to conversation history
    conversation_history.append({
        "role": "model",
        "parts": [{"function_call": function_call}]
    })
    
    # 2. Call generate_content - ADK automatically:
    #    - Detects MCP tool (via MCPToolset)
    #    - Sends MCP protocol request to server
    #    - Receives tool result
    #    - Adds function_response to conversation
    #    - Calls LLM to synthesize response
    final_response = agent.generate_content(conversation_history)
    
    # 3. Extract response (may already include tool result)
    response_text = final_response.text
```

**Key Difference**: With MCP, you don't manually execute the tool or add the function_response - ADK does it automatically.

---

## Best Practices

### 1. Security

```python
# ✅ DO: Use environment variables for credentials
mcp_tools = MCPToolset(
    connection_params=SseServerParams(
        url=os.getenv("MCP_SERVER_URL"),
        headers={
            "Authorization": f"Bearer {os.getenv('MCP_API_KEY')}"
        }
    )
)

# ❌ DON'T: Hardcode credentials
mcp_tools = MCPToolset(
    connection_params=SseServerParams(
        url="http://localhost:8001/sse",
        headers={"Authorization": "Bearer abc123"}  # BAD!
    )
)
```

### 2. Error Handling

```python
def create_mcp_tools(url: str):
    """Create MCP toolset with error handling"""
    try:
        mcp_tools = MCPToolset(
            connection_params=SseServerParams(url=url)
        )
        print(f"✅ Connected to MCP server at {url}")
        return mcp_tools
    except ConnectionError as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        print("   Continuing without MCP tools...")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
        return None
```

### 3. Fallback to Native Tools

```python
def create_agent_with_fallback():
    """Create agent with MCP, falling back to native tools"""
    tools = []
    
    # Try MCP first
    mcp_tools = create_mcp_tools(os.getenv("MCP_SERVER_URL"))
    if mcp_tools:
        tools.append(mcp_tools)
    else:
        # Fallback to native tools
        print("Using native tools instead")
        tools.extend(NATIVE_TOOLS)
    
    return genai.GenerativeModel(model_name="gemini-2.5", tools=tools)
```

### 4. Connection Pooling

```python
# Reuse MCP connections
class MCPManager:
    def __init__(self):
        self._connections = {}
    
    def get_toolset(self, server_id: str, url: str):
        """Get or create MCP toolset with connection reuse"""
        if server_id not in self._connections:
            self._connections[server_id] = MCPToolset(
                connection_params=SseServerParams(url=url)
            )
        return self._connections[server_id]
    
    def close_all(self):
        """Close all MCP connections"""
        for conn in self._connections.values():
            conn.close()

# Usage
mcp_manager = MCPManager()
github_tools = mcp_manager.get_toolset("github", "http://localhost:8001/sse")
slack_tools = mcp_manager.get_toolset("slack", "http://localhost:8002/sse")
```

### 5. Monitoring & Logging

```python
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_agent")

def create_monitored_agent():
    """Create agent with MCP monitoring"""
    try:
        mcp_tools = MCPToolset(
            connection_params=SseServerParams(url=os.getenv("MCP_URL"))
        )
        logger.info(f"✅ MCP connection established")
        
        # Log available tools
        logger.info(f"Available MCP tools: {mcp_tools.list_tools()}")
        
        return genai.GenerativeModel(
            model_name="gemini-2.5",
            tools=[mcp_tools],
        )
    except Exception as e:
        logger.error(f"❌ MCP connection failed: {e}")
        raise
```

---

## Troubleshooting

### Issue 1: "MCP not available" Error

```
⚠️  MCP not available. Install with: pip install google-adk
```

**Solution:**
```bash
# Install Google ADK
pip install google-adk

# Verify
python -c "from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset; print('OK')"
```

**If still fails**: Check Python version (must be 3.10+)

### Issue 2: Connection Refused

```
❌ Failed to connect to MCP server: Connection refused
```

**Solutions:**
1. Check if MCP server is running:
   ```bash
   ps aux | grep mcp
   lsof -i :8001
   ```

2. Start MCP server:
   ```bash
   npx -y @modelcontextprotocol/server-filesystem /path/to/dir
   ```

3. Verify URL:
   ```python
   import requests
   response = requests.get("http://localhost:8001/health")
   print(response.status_code)  # Should be 200
   ```

### Issue 3: Authentication Failed

```
❌ 401 Unauthorized
```

**Solutions:**
1. Check API key:
   ```python
   import os
   print(os.getenv("MCP_API_KEY"))  # Should not be None
   ```

2. Verify header format:
   ```python
   # Correct format
   headers = {"Authorization": f"Bearer {api_key}"}
   
   # NOT
   headers = {"Authorization": api_key}  # Missing "Bearer"
   ```

3. Check token expiration:
   ```python
   import jwt
   token = os.getenv("MCP_API_KEY")
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(f"Expires: {decoded['exp']}")
   ```

### Issue 4: MCP Tools Not Appearing

**Symptoms:** Agent doesn't use MCP tools

**Solutions:**
1. Verify tools are loaded:
   ```python
   print(f"Tools: {agent.tools}")
   # Should show MCP toolset
   ```

2. Check system instruction:
   ```python
   instruction = """
   You have access to:
   - Native tools (calculator, etc.)
   - MCP tools from external servers
   
   Use appropriate tools for each task.
   """
   ```

3. Test MCP server directly:
   ```bash
   curl -X POST http://localhost:8001/mcp/ \
        -H "Content-Type: application/json" \
        -d '{"method": "tools/list"}'
   ```

### Issue 5: Stdio Server Crashes

**Symptoms:** Stdio-based MCP server exits unexpectedly

**Solutions:**
1. Check logs:
   ```python
   mcp_tools = MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path"],
            env={"DEBUG": "true"}  # Enable debug logging
        )
    )
   ```

2. Test command manually:
   ```bash
   npx -y @modelcontextprotocol/server-filesystem /path/to/dir
   # Should start without errors
   ```

3. Check permissions:
   ```bash
   ls -la /path/to/dir
   ```

---

## Resources

### Documentation
- [Google ADK MCP Docs](https://google.github.io/adk-docs/mcp/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Anthropic MCP Guide](https://docs.anthropic.com/claude/docs/model-context-protocol)

### MCP Server Registry
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Community Servers List](https://modelcontextprotocol.io/servers)

### Tools
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) - Debug MCP servers
- [MCP SDK](https://github.com/modelcontextprotocol/sdk) - Build custom servers

### Available MCP Servers

#### Official MCP Servers (by Anthropic)

1. **Filesystem Server**
   ```bash
   npx -y @modelcontextprotocol/server-filesystem /path/to/directory
   ```
   - Read/write files
   - List directories
   - Search files

2. **GitHub Server**
   ```bash
   npx -y @modelcontextprotocol/server-github
   ```
   - Repository management
   - Issue tracking
   - Pull requests

3. **PostgreSQL Server**
   ```bash
   npx -y @modelcontextprotocol/server-postgres
   ```
   - SQL queries
   - Schema inspection
   - Data analysis

4. **Slack Server**
   ```bash
   npx -y @modelcontextprotocol/server-slack
   ```
   - Channel management
   - Message posting
   - User queries

#### Community MCP Servers
- **AWS Server** - AWS service integration
- **Google Drive Server** - Drive file access
- **MongoDB Server** - MongoDB operations
- **Redis Server** - Redis cache operations
- **Email Server** - Email sending/receiving

---

## Summary

MCP integration in Google ADK enables:
- ✅ **Standardized** tool integration across AI systems
- ✅ **Reusable** tools from community ecosystem
- ✅ **Scalable** architecture for complex agents
- ✅ **Flexible** combination of native + MCP tools

**Key Takeaways**:
1. **MCPToolset** is the bridge between your agent and MCP servers
2. **Registration**: Add `MCPToolset` to the `tools` list (not a schema, but an object)
3. **Discovery**: ADK automatically discovers MCP tools when the toolset is registered
4. **Execution**: ADK automatically handles MCP protocol communication
5. **Transparency**: From the LLM's perspective, MCP tools look like native tools

**Next Steps**:
1. Try `tool_agent_with_mcp.py` example
2. Set up a local MCP server (e.g., filesystem)
3. Explore community MCP servers
4. Build your own custom MCP server

MCP is the future of AI tool integration - embrace it early!

---

**Last Updated:** December 2025  
**Version:** 1.0  
**Author:** Created for ADK Agents Project

