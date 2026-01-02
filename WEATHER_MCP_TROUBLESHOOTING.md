# Weather MCP Troubleshooting Guide

## Issue: Agent says "I cannot provide weather information"

If you're getting this response even though MCP weather tools are configured, follow these steps:

### 1. Check Backend Logs

When you start the backend server, you should see these messages:

```
🌤️  Configuring weather MCP server (stdio)...
🔧 Creating MCP toolset (type: stdio)...
✅ Created stdio MCP toolset: npx -y @modelcontextprotocol/server-weather
✅ MCP toolset created successfully
✅ Added MCP toolset: MCPToolset
📦 Total tools to register: 2
   - 1 MCP toolsets
   - 7 native tools
🔄 Initializing model gemini-1.5-flash with 2 tools...
⏳ Waiting 5 seconds for MCP server to start and discover tools...
✅ MCP tools should now be available to the model
✅ Initialized model: gemini-1.5-flash with 2 tools
```

**If you DON'T see these messages:**
- Check that `WEATHER_MCP_TYPE=stdio` is in `.env`
- Check that the backend is reading the `.env` file
- Restart the backend server

### 2. Verify MCP Server Starts

The weather MCP server should start automatically when the toolset is created. Check if `npx` is available:

```bash
which npx
npx --version
```

### 3. Test MCP Toolset Creation

Run the test script:

```bash
cd /Users/linjia/cursor_ai_space/interview_preparation/ai_ml_interviews/machine_learning/agents_development
source activate_py312.sh
python test_weather_mcp.py
```

### 4. Check System Instruction

The system instruction should include strong directives about using weather tools. Check that it says:

- "You MUST call the weather tool"
- "NEVER say 'I cannot provide weather information'"
- "ALWAYS use the weather tools"

### 5. Common Issues

#### Issue: MCP tools not discovered
**Symptom:** Backend logs show toolset created but agent doesn't use tools
**Solution:** 
- Increase wait time (already set to 5 seconds)
- Check that npx can run `@modelcontextprotocol/server-weather`
- Try manually: `npx -y @modelcontextprotocol/server-weather`

#### Issue: Tools not in tools list
**Symptom:** Backend logs show "Total tools to register: 1" (should be 2+)
**Solution:**
- Check that `mcp_toolsets` list is not empty
- Verify `create_tools_list()` is being called with `mcp_toolsets`
- Check for errors in `_create_mcp_toolset_from_config()`

#### Issue: Model doesn't see tools
**Symptom:** Agent says it cannot provide weather even with tools registered
**Solution:**
- The system instruction is already very strong
- Try asking: "Use the get_current_weather tool to get weather in San Diego"
- Check backend logs for function call attempts

### 6. Debug Steps

1. **Restart backend server** - This ensures fresh initialization
2. **Check logs** - Look for MCP-related messages
3. **Try explicit request** - Ask: "Call get_current_weather for San Diego"
4. **Check .env** - Verify `WEATHER_MCP_TYPE=stdio` is set
5. **Verify Python environment** - Make sure you're using Python 3.12+ with google-adk

### 7. Manual Test

Try creating the agent manually to see if tools are discovered:

```python
from examples.multimodal_agent import MultimodalAgent
import os
os.environ["WEATHER_MCP_TYPE"] = "stdio"

agent = MultimodalAgent(mcp_config={
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-weather"],
    "env": {}
})

# Try a weather query
response = agent.run("What's the weather in San Diego?")
print(response)
```

### 8. If Still Not Working

If the agent still says it cannot provide weather:

1. **Check if MCP server is actually running:**
   - Look for npx processes: `ps aux | grep npx`
   - Check if weather server process exists

2. **Verify tool discovery:**
   - MCP tools are discovered asynchronously
   - The 5-second wait should be enough, but you can increase it

3. **Check model initialization:**
   - Make sure no errors occurred during model init
   - Check that tools list includes MCPToolset object

4. **Try different approach:**
   - Use SSE or HTTP MCP server instead of stdio
   - Or manually test with a simple MCP server

### Next Steps

If none of these work, the issue might be:
- MCP server not starting correctly
- Tool discovery timing issue
- Model not recognizing MCP tools as available

In that case, we may need to:
- Add explicit tool listing in system instruction
- Use a different MCP server implementation
- Add manual tool verification before model initialization

