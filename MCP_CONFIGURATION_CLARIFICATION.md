# MCP Configuration - Do You Need It?

## Short Answer: **NO, MCP is OPTIONAL**

Orel works perfectly fine **without** MCP configuration. MCP is an **optional enhancement** that adds additional tools (like weather) to the agent.

## When Do You Need MCP?

You only need to configure MCP if you want:
- **Weather information** (via weather MCP server)
- **Filesystem access** (via filesystem MCP server)
- **Database queries** (via database MCP server)
- **Other specialized tools** from MCP servers

## Current Status

### Without MCP Configuration:
✅ Orel works with all native tools:
- Image analysis
- Image generation
- Speech-to-text
- Text-to-speech
- Web search
- Camera control
- Diagram generation

### With MCP Configuration:
✅ Orel gets **additional** tools from MCP servers:
- Weather information (if weather MCP server is configured)
- Filesystem operations (if filesystem MCP server is configured)
- Other MCP-provided tools

## Configuration Options

### Option 1: No MCP (Default - Works Out of the Box)
**Do nothing!** Orel works without any MCP configuration.

**What you get:**
- All native multimodal tools
- Web search
- Image/audio processing
- Camera control

**What you don't get:**
- Weather tools (but you can use web_search for weather)
- Filesystem MCP tools
- Other MCP server tools

### Option 2: Add Weather MCP (Optional Enhancement)

If you want weather-specific tools, configure **ONE** of these:

#### A. Stdio Weather Server (Easiest - Recommended)
```bash
# In .env file:
WEATHER_MCP_TYPE=stdio
```

**Requirements:**
- Node.js installed (for `npx` command)
- No API keys needed
- Automatically downloads and runs `@modelcontextprotocol/server-weather`

**What you get:**
- `get_current_weather(location)` tool
- `get_weather_forecast(location, days)` tool
- More accurate weather data than web search

#### B. SSE Weather Server
```bash
# In .env file:
WEATHER_MCP_TYPE=sse
WEATHER_MCP_URL=http://localhost:8001/sse
```

**Requirements:**
- A weather MCP server running on the specified URL
- Server must support SSE (Server-Sent Events)

#### C. HTTP Weather Server
```bash
# In .env file:
WEATHER_MCP_TYPE=http
WEATHER_MCP_URL=https://api.example.com/mcp/
WEATHER_MCP_API_KEY=your-api-key  # Optional
```

**Requirements:**
- A weather MCP server accessible via HTTP
- Optional API key for authentication

## Summary

| Configuration | Required? | What You Get |
|--------------|-----------|--------------|
| **No MCP config** | ❌ No | All native tools (image, audio, web search, camera) |
| **WEATHER_MCP_TYPE=stdio** | ✅ Yes (if you want weather) | Native tools + Weather MCP tools |
| **WEATHER_MCP_TYPE=sse** | ✅ Yes (if you want weather) | Native tools + Weather MCP tools (via SSE) |
| **WEATHER_MCP_TYPE=http** | ✅ Yes (if you want weather) | Native tools + Weather MCP tools (via HTTP) |

## Recommendation

1. **Start without MCP**: Use Orel as-is with native tools
2. **Add weather MCP later** (if needed): Set `WEATHER_MCP_TYPE=stdio` in `.env` when you want weather-specific tools
3. **Add more MCP servers** (optional): Configure additional MCP servers as needed

## Example: Using Orel Without MCP

```python
# Works perfectly - no MCP needed!
agent = MultimodalAgent()  # No mcp_config parameter

# Orel can still:
# - Answer questions
# - Analyze images
# - Generate images
# - Search the web (including weather via web_search)
# - Process audio
# - Control camera
```

## Example: Using Orel With Weather MCP

```python
# Optional: Add weather MCP for better weather tools
agent = MultimodalAgent(mcp_config={
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-weather"]
})

# Orel now has:
# - All native tools (image, audio, web search, camera)
# - Weather MCP tools (get_current_weather, get_weather_forecast)
```

## Bottom Line

**You don't need to configure MCP to use Orel.** MCP is an optional enhancement that adds specialized tools. Configure it only if you want those specific capabilities.

