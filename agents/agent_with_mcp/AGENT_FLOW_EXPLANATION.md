# Complete Flow: How MCP Tools Are Discovered and How Agent Generates Responses

## Part 1: MCP Tool Discovery and Registration

### Step 1: MCP Server Definition (weather_server.py)

```python
@mcp.tool()
def get_weather(location: str) -> dict:
    """
    Fetches the current weather for a specified location using the OpenWeatherMap API.
    
    Args:
        location: The city name and optional country code (e.g., "London,uk").
    
    Returns:
        A dictionary containing weather information or an error message.
    """
    # ... implementation ...
```

**What happens here:**
- `@mcp.tool()` decorator registers the function as an MCP tool
- FastMCP extracts metadata:
  - **Name**: `"get_weather"` (from function name)
  - **Description**: From docstring
  - **Input Schema**: From function signature (`location: str`)
  - **Return Type**: `dict`

### Step 2: MCP Server Startup (mcp_client.py lines 112-114)

```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
```

**What happens:**
1. Client starts weather_server.py as subprocess (line 42-45)
2. Establishes stdio communication channel
3. Initializes MCP protocol handshake
4. Server is now ready to receive MCP protocol requests

### Step 3: Tool Discovery (mcp_client.py line 66)

```python
tools = await load_mcp_tools(session)
```

**What `load_mcp_tools()` does internally:**

```
┌─────────────────┐
│  MCP Client     │
│  (mcp_client)   │
└────────┬────────┘
         │
         │ 1. Send MCP request: tools/list
         │
         ▼
┌─────────────────┐
│  MCP Server     │
│ (weather_server)│
└────────┬────────┘
         │
         │ 2. FastMCP responds with tool definitions:
         │    {
         │      "name": "get_weather",
         │      "description": "Fetches the current weather...",
         │      "inputSchema": {
         │        "type": "object",
         │        "properties": {
         │          "location": {"type": "string"}
         │        },
         │        "required": ["location"]
         │      }
         │    }
         │
         ▼
┌─────────────────┐
│  load_mcp_tools │
│  (converter)    │
└────────┬────────┘
         │
         │ 3. Converts MCP tool definition to LangChain Tool format
         │
         ▼
┌─────────────────┐
│  LangChain Tool │
│  (returned)     │
└─────────────────┘
```

**Result:** `tools` is a list of LangChain Tool objects with:
- Tool name
- Tool description (for LLM to understand when to use it)
- Tool schema (parameter definitions)
- Tool execution function (wraps MCP tool call)

### Step 4: Binding Tools to LLM (mcp_client.py line 74)

```python
llm_with_tools = llm.bind_tools(tools)
```

**What happens:**
- LangChain converts tools to function calling format
- LLM receives tool definitions as part of its context
- LLM can now see:
  - Available tools
  - Tool descriptions (to decide when to use them)
  - Tool parameters (to know what to pass)

**Important:** The LLM doesn't execute tools directly - it generates tool call requests!

---

## Part 2: How Agent Generates Final Response

### Complete Flow Diagram

```
User Question: "What's the weather in San Diego?"
         │
         ▼
┌─────────────────────────────────────────┐
│  main() - Line 131                      │
│  agent.ainvoke({"messages": [...]})    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  LangGraph Agent Execution              │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  START                            │  │
│  └──────────┬───────────────────────┘  │
│             │                          │
│             ▼                          │
│  ┌──────────────────────────────────┐  │
│  │  chat_node (Line 85-88)          │  │
│  │                                   │  │
│  │  1. Receives:                     │  │
│  │     [HumanMessage("What's...")]  │  │
│  │                                   │  │
│  │  2. Formats with prompt_template: │  │
│  │     [SystemMessage("You are..."),│  │
│  │      HumanMessage("What's...")]  │  │
│  │                                   │  │
│  │  3. Sends to LLM (line 87):      │  │
│  │     chat_llm.invoke(...)         │  │
│  │                                   │  │
│  │  4. LLM decides:                 │  │
│  │     "I need weather data"        │  │
│  │     → Generates tool call:       │  │
│  │     AIMessage with tool_calls:   │  │
│  │     [{                           │  │
│  │       "name": "get_weather",     │  │
│  │       "args": {"location":       │  │
│  │                "San Diego"}      │  │
│  │     }]                           │  │
│  └──────────┬───────────────────────┘  │
│             │                          │
│             ▼                          │
│  ┌──────────────────────────────────┐  │
│  │  tools_condition (Line 97)       │  │
│  │  Checks: Are there tool calls?    │  │
│  │  → YES: Route to "tool_node"     │  │
│  │  → NO: Route to END              │  │
│  └──────────┬───────────────────────┘  │
│             │                          │
│             ▼ (tool calls detected)    │
│  ┌──────────────────────────────────┐  │
│  │  tool_node (Line 93)              │  │
│  │  ToolNode(tools=tools)            │  │
│  │                                   │  │
│  │  1. Extracts tool call from       │  │
│  │     AIMessage                     │  │
│  │                                   │  │
│  │  2. Executes tool:                │  │
│  │     - Calls MCP server via        │  │
│  │       session.call_tool()          │  │
│  │     - MCP server runs:            │  │
│  │       get_weather("San Diego")    │  │
│  │     - Gets result:                │  │
│  │       {                           │  │
│  │         "location": "San Diego",  │  │
│  │         "weather": "clear sky",   │  │
│  │         "temperature_celsius":    │  │
│  │         "22°C", ...               │  │
│  │       }                           │  │
│  │                                   │  │
│  │  3. Creates ToolMessage with      │  │
│  │     result                        │  │
│  └──────────┬───────────────────────┘  │
│             │                          │
│             ▼                          │
│  ┌──────────────────────────────────┐  │
│  │  Back to chat_node (Line 103)    │  │
│  │                                   │  │
│  │  Now state has:                   │  │
│  │  [                                │  │
│  │    HumanMessage("What's..."),    │  │
│  │    AIMessage(tool_calls=[...]),  │  │
│  │    ToolMessage(result={...})     │  │
│  │  ]                                │  │
│  │                                   │  │
│  │  LLM sees tool result and        │  │
│  │  generates final text response:  │  │
│  │  "The weather in San Diego is    │  │
│  │   clear sky with a temperature   │  │
│  │   of 22°C..."                    │  │
│  └──────────┬───────────────────────┘  │
│             │                          │
│             ▼                          │
│  ┌──────────────────────────────────┐  │
│  │  tools_condition                   │  │
│  │  Checks: Are there tool calls?     │  │
│  │  → NO: Route to END                │  │
│  └──────────┬───────────────────────┘  │
│             │                          │
│             ▼                          │
│  ┌──────────────────────────────────┐  │
│  │  END                               │  │
│  │  Returns final state with all     │  │
│  │  messages                          │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Extract Response (Lines 137-182)       │
│                                         │
│  1. Find last AIMessage (line 138-141) │
│  2. Extract text content (line 147-179)│
│  3. Print to user (line 182)           │
└─────────────────────────────────────────┘
```

### Detailed Step-by-Step Execution

#### Step 1: User Input (Line 122)
```python
user_input = input("You: ").strip()  # "What's the weather in San Diego?"
```

#### Step 2: Agent Invocation (Line 131-134)
```python
response = await agent.ainvoke(
    {"messages": [HumanMessage(content=user_input)]},
    config={"configurable": {"thread_id": "weather-session"}}
)
```

**State at this point:**
```python
{
    "messages": [
        HumanMessage(content="What's the weather in San Diego?")
    ]
}
```

#### Step 3: LangGraph Execution - First chat_node Call

**chat_node (Line 85-88):**
```python
def chat_node(state: State) -> State:
    state["messages"] = chat_llm.invoke({"messages": state["messages"]})
    return state
```

**What `chat_llm.invoke()` does:**
1. **Prompt Template** (line 77-80) formats messages:
   ```python
   [
       SystemMessage("You are a helpful assistant that uses tools..."),
       HumanMessage("What's the weather in San Diego?")
   ]
   ```

2. **LLM with Tools** (line 74) receives formatted messages:
   - Sees system prompt
   - Sees user question
   - Has access to `get_weather` tool (from `bind_tools`)
   - Decides: "I need to call get_weather tool"
   - Generates: `AIMessage` with `tool_calls` attribute

**State after chat_node:**
```python
{
    "messages": [
        HumanMessage("What's the weather in San Diego?"),
        AIMessage(
            content="",  # No text yet
            tool_calls=[{
                "name": "get_weather",
                "args": {"location": "San Diego"},
                "id": "call_123"
            }]
        )
    ]
}
```

#### Step 4: Tool Routing (Line 95-102)

**tools_condition** checks if there are tool calls:
- **YES** → Route to `tool_node`
- **NO** → Route to `END`

In this case: **Route to tool_node**

#### Step 5: Tool Execution (Line 93)

**ToolNode** (LangGraph built-in):
1. Extracts tool call from `AIMessage`
2. Finds corresponding tool in `tools` list
3. Executes tool:
   ```python
   # Internally calls MCP server
   result = await session.call_tool(
       name="get_weather",
       arguments={"location": "San Diego"}
   )
   ```
4. MCP server executes `get_weather("San Diego")` in weather_server.py
5. Returns result:
   ```python
   {
       "location": "San Diego",
       "weather": "clear sky",
       "temperature_celsius": "22°C",
       "feels_like_celsius": "21°C",
       "humidity": "65%",
       "wind_speed_mps": "3.5 m/s"
   }
   ```
6. Creates `ToolMessage` with result

**State after tool_node:**
```python
{
    "messages": [
        HumanMessage("What's the weather in San Diego?"),
        AIMessage(tool_calls=[...]),
        ToolMessage(
            content='{"location": "San Diego", "weather": "clear sky", ...}',
            tool_call_id="call_123"
        )
    ]
}
```

#### Step 6: Back to chat_node (Line 103)

**chat_node** is called again with updated state:
- LLM now sees:
  - Original user question
  - Its previous tool call request
  - Tool execution result
- LLM generates final text response:
  ```python
  AIMessage(
      content="The weather in San Diego is clear sky with a temperature of 22°C. It feels like 21°C with 65% humidity and wind speed of 3.5 m/s."
  )
  ```

**State after second chat_node:**
```python
{
    "messages": [
        HumanMessage("What's the weather in San Diego?"),
        AIMessage(tool_calls=[...]),  # First response
        ToolMessage(content='{...}'),  # Tool result
        AIMessage(content="The weather in San Diego is...")  # Final response
    ]
}
```

#### Step 7: Final Routing

**tools_condition** checks again:
- No new tool calls → Route to `END`

#### Step 8: Response Extraction (Lines 137-182)

```python
# Find last AIMessage (the final text response)
last_ai_message = None
for msg in reversed(response["messages"]):
    if isinstance(msg, AIMessage):
        last_ai_message = msg
        break

# Extract text content
response_text = extract_text_from_message(last_ai_message)
print(f"AI: {response_text}")
```

**Output:**
```
AI: The weather in San Diego is clear sky with a temperature of 22°C. It feels like 21°C with 65% humidity and wind speed of 3.5 m/s.
```

---

## Key Points

### 1. Tool Discovery is Automatic
- MCP server defines tools with `@mcp.tool()`
- Client discovers via `load_mcp_tools()` → sends `tools/list` request
- No manual registration needed

### 2. Tool Scope is Defined by:
- **Function docstring** → Tool description (what it does)
- **Function signature** → Parameter schema (what it needs)
- **System prompt** → Usage guidance (when to use it)

### 3. Agent Response Generation:
- **First LLM call**: Decides if tools are needed → generates tool call
- **Tool execution**: Runs actual tool → gets result
- **Second LLM call**: Sees tool result → generates final text response

### 4. LangGraph Handles Routing:
- `tools_condition` automatically detects tool calls
- Routes to `tool_node` when tools needed
- Routes to `END` when response is complete

### 5. The Loop Continues:
- If user asks follow-up, the cycle repeats
- Previous messages are in state (via MemorySaver)
- Agent maintains conversation context

