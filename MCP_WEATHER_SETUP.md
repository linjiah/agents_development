# MCP Weather Server Setup for Orel

This guide explains how to set up a weather MCP server for the Orel multimodal agent.

## Overview

MCP (Model Context Protocol) allows Orel to connect to external tool servers. A weather MCP server provides real-time weather information and forecasts.

## Prerequisites

1. **Python 3.10+** (MCP requires Python 3.10 or above)
2. **google-adk** package installed (includes MCP support)
3. **Node.js and npx** (for stdio-based weather MCP server)

## Setup Options

### Option 1: Stdio-based Weather MCP Server (Recommended)

This uses the official `@modelcontextprotocol/server-weather` package via npx.

**Requirements:**
- Node.js installed (for `npx` command)
- No API keys needed

**Setup:**

1. Verify Node.js is installed:
   ```bash
   node --version
   npx --version
   ```

2. Set environment variable in `.env`:
   ```bash
   WEATHER_MCP_TYPE=stdio
   ```

3. The agent will automatically use:
   ```javascript
   npx -y @modelcontextprotocol/server-weather
   ```

**Usage:**
The weather MCP server will be automatically started when the agent initializes. Orel can then use weather tools like:
- `get_current_weather(location: string)` - Get current weather
- `get_weather_forecast(location: string, days: number)` - Get forecast

### Option 2: SSE-based Weather MCP Server

Use a weather MCP server running as a web service.

**Setup:**

1. Set environment variables in `.env`:
   ```bash
   WEATHER_MCP_TYPE=sse
   WEATHER_MCP_URL=http://localhost:8001/sse
   ```

2. Make sure your weather MCP server is running on the specified URL.

**Usage:**
The agent will connect to the SSE endpoint when initialized.

### Option 3: HTTP-based Weather MCP Server

Use a weather MCP server with HTTP API.

**Setup:**

1. Set environment variables in `.env`:
   ```bash
   WEATHER_MCP_TYPE=http
   WEATHER_MCP_URL=https://api.example.com/mcp/
   WEATHER_MCP_API_KEY=your-api-key-here  # Optional
   ```

2. Make sure your weather MCP server is running and accessible.

## Testing MCP Weather Integration

### Test 1: Check MCP Availability

```bash
cd /Users/linjia/cursor_ai_space/interview_preparation/ai_ml_interviews/machine_learning/agents_development
source activate_py312.sh
python -c "from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset; print('✅ MCP available!')"
```

### Test 2: Test Weather MCP Server Directly

```bash
# Test stdio weather server
npx -y @modelcontextprotocol/server-weather
```

### Test 3: Use Orel with Weather MCP

1. Set `WEATHER_MCP_TYPE=stdio` in `.env`
2. Start the web UI:
   ```bash
   cd super_personal_agent
   ./start.sh
   ```
3. Ask Orel: "What's the weather in San Francisco?"

## Available Weather Tools

When the weather MCP server is connected, Orel will have access to tools like:

- **get_current_weather(location)**: Get current weather conditions
- **get_weather_forecast(location, days)**: Get weather forecast
- **search_locations(query)**: Search for location names

The exact tool names depend on the MCP server implementation.

## Troubleshooting

### Issue: "MCP not available"
- **Solution**: Make sure you're using Python 3.10+ and have `google-adk` installed
- Check: `python --version` should show 3.10+
- Install: `pip install google-adk`

### Issue: "npx command not found"
- **Solution**: Install Node.js from https://nodejs.org/
- Verify: `npx --version`

### Issue: Weather tools not appearing
- **Solution**: Check that `WEATHER_MCP_TYPE` is set correctly in `.env`
- Restart the backend server after changing `.env`
- Check backend logs for MCP connection errors

### Issue: MCP server connection fails
- **Solution**: 
  - For stdio: Make sure `npx` can run `@modelcontextprotocol/server-weather`
  - For SSE/HTTP: Verify the server URL is correct and accessible
  - Check network connectivity

## Example Configuration

### `.env` file example:

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Weather MCP Server (stdio - recommended)
WEATHER_MCP_TYPE=stdio

# Alternative: SSE weather server
# WEATHER_MCP_TYPE=sse
# WEATHER_MCP_URL=http://localhost:8001/sse

# Alternative: HTTP weather server
# WEATHER_MCP_TYPE=http
# WEATHER_MCP_URL=https://api.example.com/mcp/
# WEATHER_MCP_API_KEY=your-api-key
```

## Code Example

You can also configure MCP programmatically:

```python
from examples.multimodal_agent import MultimodalAgent

# Weather MCP via stdio
agent = MultimodalAgent(mcp_config={
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-weather"],
    "env": {}
})

# Or multiple MCP servers
agent = MultimodalAgent(mcp_config={
    "servers": [
        {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-weather"]
        },
        # Add more MCP servers here
    ]
})
```

## Next Steps

- Try asking Orel weather-related questions
- Explore other MCP servers (filesystem, database, etc.)
- Check the [MCP Complete Guide](MCP_COMPLETE_GUIDE.md) for more details

