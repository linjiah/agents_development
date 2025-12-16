# Google ADK Agent Development

A comprehensive collection of AI agents built using Google's Agent Development Kit (ADK), featuring multimodal capabilities, tool integration, multi-agent systems, and MCP support.

## What is Google ADK?

Google ADK (Agent Development Kit) is a framework for building AI agents powered by Google's Gemini models. It provides:
- Simple YAML-based agent configuration
- Built-in support for tool calling and function execution
- Multi-agent orchestration capabilities
- Easy integration with Google's Gemini API

## Setup

### 1. Install Dependencies

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get API Key

#### Option A: Use Setup Script (Recommended)

```bash
python setup_api_key.py
```

This interactive script will guide you through the process.

#### Option B: Manual Setup

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Generate an API key for Gemini
3. Copy the key
4. Edit `.env` file and replace `your_api_key_here` with your actual key

### 3. Configure Environment

The `.env` file should be in the project root directory with:
```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Create Your First Agent

#### Option A: Using ADK CLI (Recommended)

```bash
# Create a new agent configuration
adk create --type=config my_agent

# This creates:
# - my_agent/root_agent.yaml (agent configuration)
# - my_agent/.env (environment variables)
```

#### Option B: Manual Setup

Edit `agents/simple_agent.yaml` and configure your agent.

### 5. Run Your Agent

```bash
# Using ADK CLI
adk run my_agent

# Or using Python
python examples/simple_agent.py
```

## Project Structure

```
agents_development/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── agents/                   # Agent configurations (YAML)
│   ├── simple_agent.yaml     # Basic agent example
│   └── research_agent.yaml   # Research assistant agent
├── examples/                 # Example Python implementations
│   ├── simple_agent.py       # Basic agent in Python
│   ├── tool_agent.py         # Agent with tools
│   └── multi_agent.py        # Multi-agent system
└── tools/                    # Custom tools for agents
    ├── web_search.py         # Web search tool
    └── calculator.py         # Calculator tool
```

## Quick Start Example

### Simple Agent (YAML)

```yaml
# agents/simple_agent.yaml
name: assistant_agent
model: gemini-2.0-flash-exp
description: A helpful assistant agent
instruction: |
  You are a helpful AI assistant. 
  Answer questions clearly and concisely.
  If you don't know something, say so.
```

### Simple Agent (Python)

```python
# examples/simple_agent.py
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="SimpleAgent",
    model="gemini-2.0-flash-exp",
    description="A simple assistant agent",
    instruction="You are a helpful AI assistant."
)

if __name__ == "__main__":
    response = agent.run("What is machine learning?")
    print(response)
```

## Agent Types

### 1. Simple LLM Agent
Basic conversational agent using Gemini models.

### 2. Tool-Enabled Agent
Agent with access to external tools (web search, calculator, etc.).

### 3. Multi-Agent System
Multiple agents working together on complex tasks.

### 4. Specialized Agents
- Research Agent: Literature search and summarization
- Code Agent: Code generation and review
- Analysis Agent: Data analysis and visualization

## Advanced Topics

### Multi-Turn Conversation Management

Learn about state-of-the-art approaches for managing conversation history and context:

📖 **[Context Management Guide](CONTEXT_MANAGEMENT_GUIDE.md)** - Comprehensive guide covering:
- 7 SOTA approaches (Sliding Window, RAG, Hierarchical Memory, etc.)
- Token optimization strategies
- Production best practices
- Code examples ready to integrate
- Industry implementations (ChatGPT, Claude, Gemini)

### Multi-Agent Systems

Learn about building systems with multiple specialized agents:

📖 **[Multi-Agent Guide](MULTI_AGENT_GUIDE.md)** - Covers:
- Agent orchestration and routing
- Agent-to-agent communication
- Dynamic agent creation
- Tool support for specialized agents

### Tool Integration & Management

Learn how LLMs discover, select, and execute tools:

📖 **[Tools Management Guide](TOOLS_MANAGEMENT_GUIDE.md)** - Comprehensive guide covering:
- How LLMs learn about tools (schemas, system instructions, training)
- Complete tool interaction flow with Mermaid diagram
- The two LLM calls pattern explained
- Tool definitions and implementations
- Production integration (web search, weather, notes)
- Debugging and testing strategies
- Interview talking points
- Optimization techniques

### MCP Integration (Model Context Protocol)

Learn about integrating standardized MCP tools with Google ADK:

📖 **[MCP Complete Guide](MCP_COMPLETE_GUIDE.md)** - Comprehensive MCP integration covering:
- What is MCP and why use it
- MCP vs Native tools comparison
- Three types of MCP servers (SSE, HTTP, Stdio)
- Integration examples (Filesystem, GitHub, Database)
- Available MCP servers (official & community)
- Best practices and troubleshooting
- Real-world use cases
- Python version requirements (3.10+)

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Samples Repository](https://github.com/google/adk-samples)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)

## Interview Preparation Use Cases

This agent setup can be used for:
- **Technical Interview Practice**: Code review, algorithm explanations
- **System Design**: Agent architecture discussions
- **ML Concepts**: Explaining ML/AI concepts
- **Research Assistant**: Finding and summarizing interview resources

## Troubleshooting

### Python 3.9 Compatibility Issues

If you encounter errors like:
```
module 'importlib.metadata' has no attribute 'packages_distributions'
```

**Solution**: The code includes automatic compatibility fixes. Make sure you have `importlib-metadata` installed:

```bash
pip install importlib-metadata
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

The compatibility fixes are automatically applied when you run the example scripts.

### Python Version Warnings

If you see warnings about Python 3.9 being past end of life:
- These are just warnings and won't prevent the code from running
- For best experience, consider upgrading to Python 3.10+
- The code works with Python 3.9, but Google recommends Python 3.10+

### API Key Issues

**Error**: `API key not valid` or `API_KEY_INVALID`
- Your API key is either not set, invalid, or expired
- Run: `python setup_api_key.py` to set it up interactively
- Or manually edit `.env` and make sure `GEMINI_API_KEY=your_actual_key_here` (not the placeholder)
- Get a new API key from [Google AI Studio](https://aistudio.google.com/)

**Error**: `GEMINI_API_KEY not found`
- Make sure you created a `.env` file in the project root directory
- Verify the key is set: `GEMINI_API_KEY=your_actual_key_here` (not `your_api_key_here`)
- Run `python setup_api_key.py` for interactive setup

### Rate Limit / Quota Errors

**Error**: `429 You exceeded your current quota` or `Quota exceeded`
- You've hit the free tier rate limits for the Gemini API
- **Solution 1**: Wait for the quota to reset (usually 1 minute)
- **Solution 2**: Switch to a free-tier model (already done - using `gemini-1.5-flash`)
- **Solution 3**: Check your usage at [Google AI Usage Dashboard](https://ai.dev/usage?tab=rate-limit)
- **Solution 4**: Upgrade your plan if you need higher limits

**Model Recommendations**:
- ✅ `gemini-2.5` - **Latest model** (default in examples)
- ✅ `gemini-pro` - Widely available, stable
- ✅ `gemini-1.5-pro` - Available with limited free tier access
- ✅ `gemini-1.5-flash` - Fast, may be available depending on region/account

To change the model, set in `.env`:
```bash
GEMINI_MODEL=gemini-2.5
```

**Note**: If you get a "model not found" error, the code will automatically try fallback models (`gemini-2.5`, `gemini-pro`, `gemini-1.5-pro`, `gemini-1.5-flash`).

The code includes automatic retry logic with exponential backoff for rate limit errors.

### Module Not Found Errors

**Error**: `ModuleNotFoundError: No module named 'google.generativeai'`
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're in the correct virtual environment

## Debugging Agents

To see how agents use tools and debug their behavior:

```bash
# Run with debug mode
python examples/tool_agent.py --debug

# Or toggle debug mode during conversation
# Type 'debug' to toggle, 'history' to see conversation history
```

See [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) for detailed debugging instructions.

## Next Steps

1. Explore the example agents in `examples/`
2. Create your own agent configuration
3. Add custom tools in `tools/`
4. Build multi-agent systems for complex tasks
5. Use debug mode to understand tool usage

