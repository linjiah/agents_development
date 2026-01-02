# MCP Connection Types - When to Use Each

## Quick Answer

**YES - If you want to use an MCP server, you MUST configure one of the three connection types:**

1. **Stdio** - For MCP servers that run as subprocesses (local tools)
2. **SSE** - For MCP servers running as web services with Server-Sent Events
3. **HTTP** - For MCP servers accessible via HTTP REST API

You **cannot** use an MCP server without specifying how to connect to it.

## The Three Connection Types

### 1. Stdio (Standard Input/Output)

**What it is:** Runs the MCP server as a subprocess and communicates via stdin/stdout.

**When to use:**
- ✅ Local MCP servers (filesystem, git, code analysis)
- ✅ MCP servers that are command-line tools
- ✅ Privacy-sensitive operations (code doesn't leave your machine)
- ✅ No network latency (runs locally)

**Configuration:**
```python
mcp_config = {
    "type": "stdio",
    "command": "npx",  # or "python", "node", etc.
    "args": ["-y", "@modelcontextprotocol/server-weather"],
    "env": {}  # Optional environment variables
}
```

**Example MCP servers:**
- `@modelcontextprotocol/server-weather` (weather)
- `@modelcontextprotocol/server-filesystem` (filesystem)
- Custom Python/Node.js MCP servers

**Requirements:**
- The command must be available in PATH (e.g., `npx`, `python`, `node`)
- The MCP server must support stdio communication

---

### 2. SSE (Server-Sent Events)

**What it is:** Connects to an MCP server running as a web service using Server-Sent Events for streaming.

**When to use:**
- ✅ MCP servers running as web services
- ✅ Real-time streaming updates needed
- ✅ Server is already running (you don't start it)
- ✅ Remote or local web-based MCP servers

**Configuration:**
```python
mcp_config = {
    "type": "sse",
    "url": "http://localhost:8001/sse",  # SSE endpoint URL
    "headers": {  # Optional HTTP headers
        "X-API-Key": "your-key"
    }
}
```

**Example scenarios:**
- Weather API running on `http://localhost:8001/sse`
- Trading MCP server on `https://trading-mcp.example.com/sse`
- Chat monitoring service with SSE endpoint

**Requirements:**
- MCP server must be running and accessible at the URL
- Server must support SSE (Server-Sent Events) protocol
- Network connectivity to the server

---

### 3. HTTP (REST API)

**What it is:** Connects to an MCP server via standard HTTP REST API calls.

**When to use:**
- ✅ MCP servers with REST API endpoints
- ✅ Cloud-based MCP services
- ✅ Services that don't support SSE
- ✅ Standard HTTP authentication needed

**Configuration:**
```python
mcp_config = {
    "type": "http",
    "url": "https://api.example.com/mcp/",  # Base URL
    "headers": {  # Optional HTTP headers
        "X-API-Key": "your-api-key",
        "Authorization": "Bearer token"
    }
}
```

**Example scenarios:**
- Salesforce MCP API: `https://api.salesforce.com/mcp/v1`
- Stripe MCP: `https://api.stripe.com/mcp`
- Google Drive MCP: `https://www.googleapis.com/drive/v3/mcp`
- Custom REST API MCP servers

**Requirements:**
- MCP server must be accessible via HTTP
- Server must implement MCP protocol over HTTP
- Network connectivity and proper authentication

---

## How to Choose

### Decision Tree:

```
Do you have an MCP server?
│
├─ No → Don't configure MCP (use native tools only)
│
└─ Yes → What type of MCP server?
    │
    ├─ Is it a command-line tool or local script?
    │   └─ YES → Use "stdio"
    │
    ├─ Is it a web service with SSE endpoint?
    │   └─ YES → Use "sse"
    │
    └─ Is it a REST API or cloud service?
        └─ YES → Use "http"
```

## Examples

### Example 1: Weather MCP (Stdio - Most Common)

```python
# Weather server runs via npx
mcp_config = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-weather"]
}
```

**Why stdio?** The weather server is a Node.js package that runs as a local command.

### Example 2: Filesystem MCP (Stdio)

```python
# Filesystem server runs via npx
mcp_config = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
}
```

**Why stdio?** Filesystem operations are local and private.

### Example 3: Remote Weather Service (SSE)

```python
# Weather service running on remote server
mcp_config = {
    "type": "sse",
    "url": "https://weather-mcp.company.com/sse",
    "headers": {
        "X-API-Key": "your-company-api-key"
    }
}
```

**Why SSE?** The service is already running as a web service with SSE support.

### Example 4: Cloud Database MCP (HTTP)

```python
# Database MCP via REST API
mcp_config = {
    "type": "http",
    "url": "https://api.database-mcp.com/v1/",
    "headers": {
        "Authorization": "Bearer your-token"
    }
}
```

**Why HTTP?** It's a cloud service with REST API.

## Important Notes

1. **You only configure ONE type per MCP server** - not all three
2. **The type depends on how the MCP server is set up** - not your preference
3. **Some MCP servers support multiple types** - choose the one that fits your setup
4. **You can use multiple MCP servers** - each with its own connection type

## Multiple MCP Servers

You can configure multiple MCP servers, each with its own connection type:

```python
mcp_config = {
    "servers": [
        {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-weather"]
        },
        {
            "type": "sse",
            "url": "http://localhost:8002/sse",
            "headers": {}
        },
        {
            "type": "http",
            "url": "https://api.example.com/mcp/",
            "headers": {"X-API-Key": "key"}
        }
    ]
}
```

## Summary

| Question | Answer |
|----------|--------|
| **Do I need to configure a connection type?** | YES - if you want to use an MCP server |
| **Can I use MCP without configuring a type?** | NO - you must specify stdio, sse, or http |
| **Do I configure all three types?** | NO - choose ONE type per MCP server |
| **How do I choose the type?** | Based on how the MCP server is set up (local command, web service, or REST API) |

## Bottom Line

**If you want to use an MCP server → You MUST configure one of the three connection types (stdio, sse, or http).**

The type you choose depends on how your MCP server is implemented and how you want to connect to it.

