# Why MCP Has Three Components: Tools, Prompts, and Resources

## The Three MCP Components

MCP servers expose three distinct types of capabilities:

1. **Tools** - For **action** (executable functions)
2. **Prompts** - For **guidance** (reasoning workflows)
3. **Resources** - For **context** (read-only data)

## Why This Design?

### The Problem: Different Needs Require Different Solutions

An AI agent needs to:
- **Do things** (actions) → Tools
- **Think through complex problems** (reasoning) → Prompts
- **Know things** (context) → Resources

Each need is fundamentally different and requires a different approach.

## Component-by-Component Analysis

### 1. Tools: "Do Something"

**What they are:**
- Executable functions that perform actions
- Called by the agent when it decides action is needed
- Return results that the agent uses

**Example from our server:**
```python
@mcp.tool()
def get_weather(location: str) -> dict:
    """Fetches weather data from API"""
    # Executes HTTP request, returns data
```

**Why separate?**
- **Agent-driven**: Agent decides when to call
- **Stateless**: Each call is independent
- **Action-oriented**: Performs actual work
- **Reusable**: Same tool can be called multiple times with different inputs

**Use case:**
- Agent needs weather → calls `get_weather("San Diego")`
- Agent gets result → uses it in response

---

### 2. Prompts: "Guide the Reasoning"

**What they are:**
- Pre-written instruction templates
- Orchestrate multi-step reasoning workflows
- User-initiated (not agent-initiated)

**Example from our server:**
```python
@mcp.prompt()
def compare_weather_prompt(location_a: str, location_b: str) -> str:
    """Returns instructions for comparing weather"""
    return """
    You are a weather analyst. Compare weather between {location_a} and {location_b}.
    1. Get weather for both cities
    2. Compare the results
    3. Present in a structured format
    """
```

**Why separate?**
- **User-driven**: User explicitly requests a workflow
- **Complex reasoning**: Guides multi-step processes
- **Template-based**: Reusable reasoning patterns
- **Orchestration**: Coordinates multiple tool calls

**Use case:**
- User wants comparison → invokes prompt
- Prompt guides agent through: get data → analyze → format
- Agent follows the structured workflow

**Key difference from tools:**
- Tool: Agent calls it when needed
- Prompt: User requests it, agent follows the instructions

---

### 3. Resources: "Provide Context"

**What they are:**
- Read-only data sources
- Discoverable information the agent can consult
- Passive (not executed, just read)

**Example from our server:**
```python
@mcp.resource("delivery_log://delivery_log.txt")
def get_delivery_log() -> str:
    """Returns delivery log file contents"""
    return file.read_text()
```

**Why separate?**
- **Contextual**: Provides background information
- **Read-only**: No side effects, just data
- **Discoverable**: Agent can see what's available
- **Persistent**: Data exists independently of agent actions

**Use case:**
- Agent needs delivery cities → reads resource
- Agent uses resource content to inform its actions
- Agent can then call tools for each city in the log

**Key difference:**
- Tool: Does something (action)
- Resource: Is something (data)

---

## The Design Philosophy

### Separation of Concerns

Each component has a **single, clear responsibility**:

```
┌─────────────────────────────────────────┐
│         Agent Needs                     │
├─────────────────────────────────────────┤
│  "I need to DO something"               │ → Tools
│  "I need to THINK through this"         │ → Prompts  
│  "I need to KNOW something"             │ → Resources
└─────────────────────────────────────────┘
```

### Why Not Just Tools?

**If everything was a tool:**

❌ **Problems:**
- Complex workflows would require many tool calls
- No way to guide multi-step reasoning
- No way to provide contextual data
- Agent would need to figure out everything itself

**Example problem:**
```
User: "Compare weather in all cities from the delivery log"

Without resources/prompts:
1. Agent doesn't know about delivery log
2. Agent doesn't know how to structure comparison
3. Agent has to figure out the workflow itself
4. Result: Inefficient, error-prone

With resources/prompts:
1. Agent reads delivery_log resource → knows cities
2. Agent uses compare_weather_prompt → knows workflow
3. Agent calls get_weather tool for each city
4. Result: Efficient, structured, reliable
```

---

## Real-World Analogy

Think of a **restaurant**:

### Tools = Kitchen Actions
- "Cook a steak" (action)
- "Make a salad" (action)
- Discrete, executable tasks

### Prompts = Recipe Cards
- "How to make a 3-course meal" (guidance)
- Step-by-step instructions
- Orchestrates multiple kitchen actions

### Resources = Ingredient List
- "What ingredients do we have?" (context)
- Read-only information
- Informs what actions are possible

**You need all three:**
- Can't cook without actions (tools)
- Can't make complex dishes without recipes (prompts)
- Can't plan without knowing ingredients (resources)

---

## How They Work Together

### Example: Weather Comparison Workflow

```
User: "Compare weather for all cities in the delivery log"

1. RESOURCE: Agent reads delivery_log.txt
   → Discovers: San Diego, New York, London, Tokyo, Seattle, Paris

2. PROMPT: User invokes compare_weather_prompt
   → Agent receives: "Compare weather between two cities using this workflow..."

3. TOOLS: Agent calls get_weather() for each city
   → Gets actual weather data

4. Agent synthesizes: Resource (cities) + Prompt (workflow) + Tools (data)
   → Produces comprehensive comparison
```

**Without this design:**
- Agent would need one giant "compare_all_weather" tool
- Or agent would need to figure out the workflow itself
- Or agent wouldn't know about the delivery log

**With this design:**
- Resource provides context (cities)
- Prompt provides workflow (how to compare)
- Tools provide data (weather)
- Each component does one thing well

---

## Benefits of This Design

### 1. **Modularity**
- Each component can be developed independently
- Easy to add new tools, prompts, or resources
- Clear boundaries between concerns

### 2. **Reusability**
- Same tool can be used in different workflows
- Same prompt can work with different data
- Same resource can inform multiple actions

### 3. **Composability**
- Combine resources + prompts + tools for complex tasks
- Build sophisticated workflows from simple components
- Agent can mix and match as needed

### 4. **Discoverability**
- Agent can discover what's available
- User can see what workflows are possible
- Clear API for each component type

### 5. **Separation of Concerns**
- Tools: Server developer writes action code
- Prompts: Server developer writes reasoning guidance
- Resources: Server developer exposes data sources
- Each has a clear, distinct purpose

---

## Comparison Table

| Aspect | Tools | Prompts | Resources |
|--------|-------|---------|-----------|
| **Purpose** | Execute actions | Guide reasoning | Provide context |
| **When used** | Agent decides | User requests | Agent or user reads |
| **Returns** | Action results | Instructions | Data content |
| **State** | Stateless | Stateless | Read-only |
| **Initiator** | Agent | User | Agent/User |
| **Complexity** | Simple functions | Multi-step workflows | Data sources |
| **Example** | `get_weather()` | `compare_weather_prompt()` | `delivery_log.txt` |

---

## Summary

MCP uses three components because **agents need three different things**:

1. **Tools** → "I need to DO something"
2. **Prompts** → "I need to THINK through this"  
3. **Resources** → "I need to KNOW something"

This design provides:
- ✅ Clear separation of concerns
- ✅ Modular, reusable components
- ✅ Composability for complex workflows
- ✅ Discoverability for agents and users
- ✅ Flexibility to handle diverse use cases

**The three components work together** to enable sophisticated agent capabilities that would be difficult or impossible with just one component type.

