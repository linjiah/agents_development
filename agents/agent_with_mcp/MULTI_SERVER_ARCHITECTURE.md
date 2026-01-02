# Multi-Server MCP Architecture

This implementation follows the multi-server architecture pattern from [Educative's MCP tutorial](https://www.educative.io/module/page/P1vxGOtNzNBPX5PJY/10370001/6570833957748736/6383148319244288), where each capability is implemented as an independent, composable MCP server.

## Architecture Overview

Instead of a monolithic server with all capabilities, we use **multiple independent servers**:

```
┌─────────────────────────────────────────┐
│         MCP Client (Agent)              │
│  (mcp_client.py)                        │
│                                         │
│  - Connects to multiple servers         │
│  - Aggregates tools from all servers   │
│  - Routes to appropriate tools          │
└─────────────┬───────────────────────────┘
              │
      ┌───────┴────────┐
      │                │
      ▼                ▼
┌──────────┐      ┌──────────┐
│ Weather  │      │   Task   │
│  Server  │      │  Server  │
│          │      │          │
│ - get_   │      │ - create_│
│   weather│      │   task   │
│          │      │ - list_  │
│ - compare│      │   tasks  │
│   weather│      │ - complete│
│   prompt │      │   _task  │
│          │      │ - delete_│
│ - delivery│     │   task   │
│   log    │      │ - get_   │
│   resource│     │   task   │
└──────────┘      ┌──────────┘
```

## Benefits of Multi-Server Architecture

### 1. **Modularity**
Each server handles one specific job, making it easier to:
- Develop in isolation
- Test independently
- Debug without affecting other capabilities

### 2. **Reusability**
Servers can be:
- Reused across different agents
- Shared between projects
- Composed in different combinations

### 3. **Maintainability**
- Changes to weather functionality don't affect task management
- Each server has its own dependencies
- Clear separation of concerns

### 4. **Scalability**
- Add new capabilities by creating new servers
- No need to modify existing servers
- Easy to enable/disable specific capabilities

## Implementation Details

### Server Structure

#### Weather Server (`weather_server.py`)
- **Purpose**: Weather information and delivery log resources
- **Tools**: `get_weather`
- **Prompts**: `compare_weather_prompt`
- **Resources**: `file://delivery_log.txt`

#### Task Server (`task_server.py`)
- **Purpose**: Task management
- **Tools**: 
  - `create_task` - Create new tasks
  - `list_tasks` - List all tasks (with optional status filter)
  - `complete_task` - Mark tasks as completed
  - `delete_task` - Delete tasks
  - `get_task` - Get a specific task by ID

### Client Configuration

The client connects to multiple servers using nested context managers:

```python
# Each server has its own configuration
weather_server_params = StdioServerParameters(
    command="python",
    args=[str(WEATHER_SERVER_PATH)],
    env=os.environ.copy()
)

task_server_params = StdioServerParameters(
    command="python",
    args=[str(TASK_SERVER_PATH)],
    env=os.environ.copy()
)

# Connect to all servers
async with stdio_client(weather_server_params) as (weather_read, weather_write):
    async with stdio_client(task_server_params) as (task_read, task_write):
        async with ClientSession(weather_read, weather_write) as weather_session:
            async with ClientSession(task_read, task_write) as task_session:
                # Initialize and aggregate tools from all servers
                sessions = [weather_session, task_session]
                server_names = ["Weather", "Task"]
                agent = await create_graph(sessions, server_names)
```

### Tool Aggregation

The `create_graph` function aggregates tools from all connected servers:

```python
async def create_graph(sessions: List[ClientSession], server_names: List[str]):
    all_tools = []
    
    for session, server_name in zip(sessions, server_names):
        # Load tools from each server
        server_tools = await load_mcp_tools(session)
        all_tools.extend(server_tools)
    
    # Bind all tools to LLM
    llm_with_tools = llm.bind_tools(all_tools)
    # ... rest of agent setup
```

## Usage Examples

### Weather Queries
```
You: What's the weather in San Francisco?
AI: [Uses get_weather tool from Weather Server]
```

### Task Management
```
You: Create a task to review the quarterly report
AI: [Uses create_task tool from Task Server]

You: List all my pending tasks
AI: [Uses list_tasks tool from Task Server with status="pending"]

You: Complete task 1
AI: [Uses complete_task tool from Task Server]
```

### Combined Workflows
```
You: Check the weather in all cities from the delivery log and create tasks for cities with rain
AI: [Uses resources from Weather Server, then creates tasks using Task Server]
```

## Adding New Servers

To add a new server:

1. **Create the server file** (e.g., `calendar_server.py`):
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calendar")

@mcp.tool()
def get_calendar_events(date: str) -> dict:
    """Get calendar events for a date."""
    # Implementation
    pass

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

2. **Add server configuration** in `mcp_client.py`:
```python
CALENDAR_SERVER_PATH = SCRIPT_DIR / "calendar_server.py"

calendar_server_params = StdioServerParameters(
    command="python",
    args=[str(CALENDAR_SERVER_PATH)],
    env=os.environ.copy()
)
```

3. **Connect in main()**:
```python
async with stdio_client(weather_server_params) as (weather_read, weather_write):
    async with stdio_client(task_server_params) as (task_read, task_write):
        async with stdio_client(calendar_server_params) as (calendar_read, calendar_write):
            # Add calendar_session to sessions list
            sessions = [weather_session, task_session, calendar_session]
            server_names = ["Weather", "Task", "Calendar"]
```

## File Structure

```
agent_with_mcp/
├── mcp_client.py          # Main agent client (connects to all servers)
├── weather_server.py       # Weather MCP server
├── task_server.py          # Task management MCP server
├── tasks.json              # Task storage (created by task_server)
├── delivery_log.txt        # Delivery log resource
└── MULTI_SERVER_ARCHITECTURE.md  # This file
```

## Key Takeaways

1. **Each server is independent** - No shared state or dependencies
2. **Client aggregates tools** - All tools available to the agent
3. **Easy to extend** - Add new servers without modifying existing ones
4. **Follows microservices pattern** - Each server is a focused service

This architecture makes the system more maintainable, testable, and scalable as you add more capabilities to your agent.

