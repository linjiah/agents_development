# Enhanced Multi-Agent System Guide

## Overview

This enhanced multi-agent system implements a sophisticated personal assistant with advanced features:

1. ✅ **LLM-Based Routing** - RouterAgent uses LLM to intelligently decide which agent(s) to use
2. ✅ **Parallel Execution** - Multiple agents can work simultaneously
3. ✅ **Agent Communication** - Agents can consult each other
4. ✅ **Shared Context** - Conversation history shared across all agents
5. ✅ **Dynamic Agent Creation** - Create new agents on demand
6. ✅ **Tool Support** - Agents have access to tools (calculator, web_search, etc.)

## Architecture

```
User Query
    ↓
RouterAgent (LLM-based routing)
    ↓
    ├─→ ResearchAgent (with tools)
    ├─→ TaskAgent (with tools)
    ├─→ TechnicalAgent (with tools)
    └─→ CommunicationAgent
    ↓
Parallel or Sequential Execution
    ↓
Agent-to-Agent Consultation (if needed)
    ↓
Combined Response
```

## Features

### 1. LLM-Based Routing

The `RouterAgent` analyzes queries and decides:
- Which agent(s) should handle the query
- Whether to execute in parallel or sequentially
- Reasoning for the decision

**Example:**
```
User: "Search for Python best practices and create a note about it"

RouterAgent decides:
- Agents: ["ResearchAgent", "TaskAgent"]
- Parallel: true
- Reasoning: "Needs web search and note creation"
```

### 2. Parallel Agent Execution

Multiple agents can work simultaneously:

```python
# Parallel execution
result = orchestrator.route_and_execute(query)
# ResearchAgent and TaskAgent work at the same time
```

### 3. Agent-to-Agent Communication

Agents can consult each other:

```python
# Agent A can ask Agent B for help
response = agent_b.consult("Can you help with this?", from_agent="AgentA")
```

### 4. Shared Conversation History

All agents share conversation context:

```python
SHARED_HISTORY = [
    {"role": "user", "parts": ["..."], "agent": "ResearchAgent"},
    {"role": "model", "parts": ["..."], "agent": "ResearchAgent"},
    # All agents can see this history
]
```

### 5. Dynamic Agent Creation

Create new agents on the fly:

```
You: create CustomAgent You are a specialized agent for X
✅ Created new agent: CustomAgent
```

### 6. Tool Support

Agents have access to tools:
- **ResearchAgent**: web_search, get_weather
- **TaskAgent**: create_note, get_note, get_current_time
- **TechnicalAgent**: calculator, web_search

## Available Agents

### ResearchAgent
- **Purpose**: Information gathering and research
- **Tools**: web_search, get_weather
- **Use cases**: Web searches, fact-checking, current information

### TaskAgent
- **Purpose**: Task and schedule management
- **Tools**: create_note, get_note, get_current_time
- **Use cases**: Notes, reminders, scheduling

### TechnicalAgent
- **Purpose**: Technical questions and calculations
- **Tools**: calculator, web_search
- **Use cases**: Math, coding questions, technical explanations

### CommunicationAgent
- **Purpose**: Writing and communication
- **Tools**: None (writing-focused)
- **Use cases**: Emails, messages, content creation

## Usage

### Basic Usage

```bash
python examples/multi_agent.py
```

### Commands

- **Regular query**: Just type your question
- **`create <name> <instruction>`**: Create a new agent
- **`history`**: View shared conversation history
- **`agents`**: List all available agents
- **`quit`**: Exit

### Example Interactions

#### Single Agent
```
You: What is machine learning?
→ RouterAgent routes to ResearchAgent
→ ResearchAgent uses web_search tool
→ Returns comprehensive answer
```

#### Parallel Agents
```
You: Search for Python best practices and create a note
→ RouterAgent routes to [ResearchAgent, TaskAgent] in parallel
→ ResearchAgent searches web
→ TaskAgent creates note
→ Both responses returned
```

#### Agent Consultation
```
You: Write code to calculate fibonacci and explain it
→ RouterAgent routes to TechnicalAgent
→ TechnicalAgent generates code
→ If uncertain, consults CommunicationAgent for explanation
→ Returns combined response
```

#### Dynamic Agent Creation
```
You: create FinanceAgent You are an expert in personal finance and budgeting
✅ Created new agent: FinanceAgent

You: How should I budget my income?
→ RouterAgent can now route to FinanceAgent
```

## Routing Logic

The RouterAgent uses LLM to analyze queries and returns JSON:

```json
{
    "agents": ["ResearchAgent", "TaskAgent"],
    "reasoning": "Query needs both research and task management",
    "parallel": true
}
```

### Fallback Routing

If LLM routing fails, falls back to keyword-based routing:
- "search", "find" → ResearchAgent
- "task", "note", "schedule" → TaskAgent
- "code", "calculate" → TechnicalAgent
- "write", "email" → CommunicationAgent

## Agent Communication Flow

```
Agent A receives query
    ↓
Agent A generates response
    ↓
If uncertain or needs help:
    ↓
Agent A consults Agent B
    ↓
Agent B provides consultation
    ↓
Agent A integrates consultation into response
    ↓
Final response returned
```

## Shared History Structure

```python
SHARED_HISTORY = [
    {
        "role": "user",
        "parts": ["user message"],
        "agent": "agent_name"  # Which agent handled it
    },
    {
        "role": "model",
        "parts": ["agent response"],
        "agent": "agent_name"
    }
]
```

All agents can access the last 5 messages for context.

## Advanced Features

### Custom Agent Creation

```python
# In code
orchestrator.create_agent(
    name="CustomAgent",
    system_instruction="You are a specialized agent for X",
    tools=TOOLS  # Optional
)
```

### Agent Consultation

```python
# Agent A consults Agent B
response = agent_b.consult(
    question="Can you help with this technical question?",
    from_agent="AgentA"
)
```

### Context Sharing

```python
# Agents automatically get context from shared history
agent.generate(query, context=previous_agent_responses)
```

## Performance Considerations

### Parallel Execution
- Uses `ThreadPoolExecutor` for true parallelism
- Faster when multiple agents are needed
- Each agent runs in separate thread

### Sequential Execution
- Used when agents need to build on each other
- Consultation happens sequentially
- Better for complex multi-step tasks

## Error Handling

- Routing errors fall back to keyword-based routing
- Agent errors are caught and reported
- Tool execution errors are handled gracefully
- Consultation failures don't break the flow

## Example Session

```
🤖 Enhanced Multi-Agent Personal Assistant
============================================================
Available agents: ResearchAgent, TaskAgent, TechnicalAgent, CommunicationAgent

You: Search for latest AI news and create a note

🧭 Routing Decision:
   Agents: ResearchAgent, TaskAgent
   Reasoning: Query needs both web search and note creation
   Parallel: true

📊 Response (parallel mode):
============================================================

[ResearchAgent]:
Latest AI news: [Search results from web_search tool]...

[TaskAgent]:
Note created successfully!
- Title: Latest AI News
- Content: [Summary from ResearchAgent]
============================================================
```

## Next Steps

1. **Add more specialized agents** (FinanceAgent, HealthAgent, etc.)
2. **Improve routing prompts** for better decisions
3. **Add agent memory** for long-term context
4. **Implement agent chains** for complex workflows
5. **Add monitoring** for agent performance

