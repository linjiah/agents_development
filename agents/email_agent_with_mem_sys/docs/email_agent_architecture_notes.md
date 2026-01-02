# Email Agent Architecture Notes

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Triage System Deep Dive](#triage-system-deep-dive)
4. [Pydantic Models Explained](#pydantic-models-explained)
5. [Graph Node Structure](#graph-node-structure)
6. [Data Flow](#data-flow)
7. [Design Patterns](#design-patterns)
8. [Key Concepts](#key-concepts)
9. [LangGraph Core Concepts: State and StateGraph](#langgraph-core-concepts-state-and-stategraph)

---

## Architecture Overview

The email agent uses a **two-stage pipeline** built with LangGraph:

```
Email Input → Triage Router → [Ignore/Notify/Respond] → Response Agent (if needed) → End
```

### High-Level Flow

1. **Email arrives** → Stored in `email_input` state
2. **Triage Router** → Classifies email (ignore/notify/respond)
3. **Conditional Routing**:
   - If **ignore/notify** → End (no action)
   - If **respond** → Response Agent → Generate response → End

---

## Core Components

### 1. Configuration Layer

**Location**: Lines 30-62 in `email_agent_baseline.py`

```python
profile = {
    "name": "John",
    "full_name": "John Doe",
    "user_profile_background": "Senior software engineer leading a team of 5 developers",
}

prompt_instructions = {
    "triage_rules": {
        "ignore": "Marketing newsletters, spam emails, mass company announcements",
        "notify": "Team member out sick, build system notifications, project status updates",
        "respond": "Direct questions from team members, meeting requests, critical bug reports",
    },
    "agent_instructions": "Use these tools when appropriate to help manage John's tasks efficiently."
}
```

**Purpose**:
- `profile`: User context for personalization
- `prompt_instructions`: Rules for triage classification and agent behavior

### 2. Triage System

**Location**: Lines 64-115 (setup) and 192-244 (actual node)

**Components**:
- **LLM**: `gpt-4o-mini` for classification
- **Router Model**: Pydantic schema for structured output
- **Triage Router Function**: Graph node that performs classification

**Classification Categories**:
- `ignore`: Irrelevant emails (spam, newsletters)
- `notify`: Important but no response needed (status updates)
- `respond`: Requires a reply (questions, meeting requests)

### 3. Tools Layer

**Location**: Lines 121-144

Three tools available to the response agent:

1. **`write_email(to, subject, content)`**: Send email responses
2. **`schedule_meeting(attendees, subject, duration_minutes, preferred_day)`**: Schedule meetings
3. **`check_calendar_availability(day)`**: Check available time slots

**Note**: Currently placeholder implementations. In production, these would integrate with real email/calendar APIs.

### 4. Response Agent

**Location**: Lines 150-181

- Uses **ReAct pattern** (`create_react_agent`)
- Dynamically builds prompts from state
- Can call tools in a loop until it has an answer
- Uses `gpt-4o` for more complex reasoning

### 5. State Management

**Location**: Lines 187-189

```python
class State(TypedDict):
    email_input: dict
    messages: Annotated[list, add_messages]
```

**State Components**:
- `email_input`: Original email data (author, to, subject, email_thread)
- `messages`: Conversation history (automatically merged with `add_messages`)

### 6. Graph Assembly

**Location**: Lines 250-254

```python
email_agent = StateGraph(State)
email_agent = email_agent.add_node("triage_router", triage_router)
email_agent = email_agent.add_node("response_agent", agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile()
```

**Graph Flow**:
1. `START` → `triage_router`
2. `triage_router` → `response_agent` (if respond) OR `END` (if ignore/notify)
3. `response_agent` → `END` (after response)

---

## Triage System Deep Dive

### Setup Code vs. Graph Node

**Important Distinction**:

#### Setup Code (Lines 68-115)
- **NOT a graph node** - runs once at import time
- Creates reusable components:
  - `llm`: Base LLM instance
  - `Router`: Pydantic schema definition
  - `llm_router`: LLM configured for structured output
- Lines 91-115: Test code (can be moved to `if __name__ == "__main__"`)

#### Graph Node (Lines 192-244)
- **Actual routing node** - runs every time an email arrives
- Function: `triage_router(state: State) -> Command`
- Uses `llm_router` from setup
- Returns `Command` to control graph flow

### Triage Router Function

```python
def triage_router(state: State) -> Command[
    Literal["response_agent", "__end__"]
]:
    """Route emails based on triage classification."""
    # 1. Extract email from state
    author = state['email_input']['author']
    to = state['email_input']['to']
    subject = state['email_input']['subject']
    email_thread = state['email_input']['email_thread']

    # 2. Build prompts
    system_prompt = triage_system_prompt.format(...)
    user_prompt = triage_user_prompt.format(...)

    # 3. Classify email
    result = llm_router.invoke([...])

    # 4. Route based on classification
    if result.classification == "respond":
        return Command(goto="response_agent", update={...})
    elif result.classification == "ignore":
        return Command(goto=END, update=None)
    elif result.classification == "notify":
        return Command(goto=END, update=None)
```

**Key Points**:
- Takes `State` as input
- Returns `Command` object
- `Command.goto`: Next node to execute
- `Command.update`: State updates to apply

---

## Pydantic Models Explained

### What is Pydantic?

**Pydantic** is a Python library for data validation using Python type annotations. It ensures data matches expected types and constraints.

### Router Model

```python
class Router(BaseModel):
    """Analyze the unread email and route it according to its content."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email: 'ignore' for irrelevant emails, "
        "'notify' for important information that doesn't need a response, "
        "'respond' for emails that need a reply",
    )
```

**What This Does**:
1. **Defines Schema**: Specifies required fields and types
2. **Validates Output**: Ensures LLM returns valid data
3. **Enables Structured Output**: Forces LLM to return specific format

### Benefits of Pydantic

1. **Type Safety**: Prevents invalid values
2. **IDE Support**: Autocomplete and type hints
3. **Validation**: Catches errors early
4. **Documentation**: Schema documents expected output
5. **LLM Constraint**: Guides model to return correct format

### Example: Without vs. With Pydantic

**Without Pydantic** (unstructured):
```python
# LLM might return:
"respond"  # Just a string - could be anything!
"I think this should be responded to"  # Wrong format!
{"action": "reply"}  # Wrong keys!
```

**With Pydantic** (structured):
```python
# LLM MUST return a Router object:
Router(
    reasoning="This is a direct question from a team member...",
    classification="respond"  # Must be one of: "ignore", "respond", "notify"
)
```

---

## How Pydantic Validation Works

### Validation Process

```
1. LLM Returns Raw Text/JSON
   ↓
2. LangChain Converts to Dictionary
   ↓
3. Pydantic Validates (THIS IS WHERE VALIDATION HAPPENS)
   ↓
4. Success or Failure
```

### Step-by-Step

1. **LLM Response**: Returns JSON string like `{"reasoning": "...", "classification": "respond"}`

2. **LangChain Parsing**: Converts JSON to Python dictionary

3. **Pydantic Validation** (when creating Router instance):
   ```python
   router_instance = Router(**llm_response_dict)
   ```
   
   Pydantic checks:
   - ✓ All required fields present?
   - ✓ Types match? (str, Literal values)
   - ✓ Values valid? (classification in allowed list)

4. **Result**:
   - **Success**: Returns Router object
   - **Failure**: Raises ValidationError (LangChain can retry)

### Who Validates?

- **Pydantic library** performs validation automatically
- **When**: During object creation (when `Router(**dict)` is called)
- **How**: Based on type hints and Field definitions in your class

### Validation Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. You call: llm_router.invoke([...])                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. LangChain sends request to LLM with structured output   │
│    prompt (asks for JSON matching Router schema)            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. LLM returns JSON string:                                 │
│    {"reasoning": "...", "classification": "respond"}        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. LangChain parses JSON → Python dict                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. LangChain tries: Router(**dict)                          │
│    ═══════════════════════════════════════════════════       │
│    THIS IS WHERE PYDANTIC VALIDATES!                        │
│    ═══════════════════════════════════════════════════       │
│    Pydantic checks:                                          │
│    ✓ All required fields present?                           │
│    ✓ Types match? (str, Literal values)                     │
│    ✓ Values valid? (classification in allowed list)          │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ Validation OK   │  │ Validation FAILS │
        └──────────────────┘  └──────────────────┘
                    │                 │
                    ▼                 ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ Return Router    │  │ LangChain retries│
        │ object to you    │  │ or raises error  │
        └──────────────────┘  └──────────────────┘
```

---

## Graph Node Structure

### Command Pattern

The `triage_router` function returns a `Command` object that controls graph flow:

```python
Command(goto="response_agent", update={...})  # Go to response agent
Command(goto=END, update=None)                # End the graph
```

**Command Components**:
- `goto`: Next node to execute (`"response_agent"` or `END`)
- `update`: State updates to apply (adds messages if responding)

### Node Registration

```python
email_agent = StateGraph(State)
email_agent = email_agent.add_node("triage_router", triage_router)
email_agent = email_agent.add_node("response_agent", agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile()
```

**Flow**:
1. `START` → `triage_router` (always)
2. `triage_router` → `response_agent` (if respond) OR `END` (if ignore/notify)
3. `response_agent` → `END` (after response)

---

## Data Flow

### Example: Email Requiring Response

1. **Email arrives**:
   ```python
   email_input = {
       "author": "Alice Smith <alice.smith@company.com>",
       "to": "John Doe <john.doe@company.com>",
       "subject": "Quick question about API documentation",
       "email_thread": "Hi John, ..."
   }
   ```

2. **State created**:
   ```python
   state = {
       "email_input": email_input,
       "messages": []
   }
   ```

3. **Triage router classifies** → `"respond"`

4. **State updated**:
   ```python
   state["messages"] = [{
       "role": "user",
       "content": f"Respond to the email {email_input}"
   }]
   ```

5. **Response agent processes**:
   - Reads email from messages
   - Calls `write_email` tool
   - Generates response

6. **Final state**:
   ```python
   {
       "email_input": {...},
       "messages": [
           {"role": "user", "content": "..."},
           {"role": "assistant", "content": "..."},
           {"role": "tool", "content": "Email sent..."}
       ]
   }
   ```

---

## Design Patterns

### 1. Separation of Concerns

- **Triage**: Only classification, no action
- **Response**: Action generation, uses tools

### 2. Structured Output

- Pydantic models ensure reliable LLM output
- Type safety and validation

### 3. State-Based Routing

- `Command` pattern for conditional flow
- State updates control graph execution

### 4. Modular Prompts

- Prompts in separate file (`prompts.py`)
- Easy to update and maintain

---

## Key Concepts

### LangGraph Concepts

- **StateGraph**: Graph that operates on a state object
- **Node**: Function that processes state and returns updates
- **Command**: Return type that controls graph flow (goto + update)
- **Edge**: Connection between nodes

### Pydantic Concepts

- **BaseModel**: Base class for data validation
- **Field**: Field definition with validation rules
- **Literal**: Type that restricts to specific values
- **Validation**: Automatic checking when creating instances

### LLM Integration

- **Structured Output**: Forcing LLM to return specific format
- **with_structured_output()**: LangChain method to enable structured output
- **ReAct Pattern**: Reasoning + Acting loop for tool use

---

## LangGraph Core Concepts: State and StateGraph

### What is State?

**State** is the data container that flows through your agent graph. It's like a shared memory that all nodes can read from and write to.

#### State Definition in Your Code

```python
class State(TypedDict):
    email_input: dict
    messages: Annotated[list, add_messages]
```

**Components**:
- `email_input`: The incoming email data (author, to, subject, email_thread)
- `messages`: Conversation history (automatically merged with `add_messages`)

#### How State Works

State is like a **shared dictionary** that gets passed from node to node:

```python
# Initial state when you invoke the agent
state = {
    "email_input": {
        "author": "Alice <alice@company.com>",
        "to": "John <john@company.com>",
        "subject": "Question about API",
        "email_thread": "Hi John, ..."
    },
    "messages": []  # Empty initially
}
```

#### State Flow Through Nodes

```
Node 1 (triage_router) receives state:
  state = {
    "email_input": {...},
    "messages": []
  }
  
Node 1 processes and updates state:
  update = {
    "messages": [{"role": "user", "content": "..."}]
  }
  
Node 2 (response_agent) receives UPDATED state:
  state = {
    "email_input": {...},  # Still there (unchanged)
    "messages": [{"role": "user", "content": "..."}]  # Updated!
  }
```

**Key Points**:
- State persists across all nodes
- Nodes can read any part of the state
- Nodes can update state (selectively)
- State is immutable between nodes (updates create new state)

### What is StateGraph?

**StateGraph** is the graph structure that operates on State. It defines:
- Which nodes exist
- How nodes are connected
- How state flows between nodes
- The execution order

#### StateGraph Construction in Your Code

```python
email_agent = StateGraph(State)
email_agent = email_agent.add_node("triage_router", triage_router)
email_agent = email_agent.add_node("response_agent", agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile()
```

#### Step-by-Step Graph Construction

1. **Create Graph**: `StateGraph(State)`
   - Creates an empty graph that works with State objects
   - Tells LangGraph: "This graph will operate on State"

2. **Add Nodes**: `add_node(name, function)`
   - Adds functions that process state
   - Each node is a function that receives State and returns updates

3. **Add Edges**: `add_edge(from_node, to_node)`
   - Defines connections between nodes
   - `START` is a special node that begins execution

4. **Compile**: `compile()`
   - Makes the graph executable
   - Validates the graph structure

#### Visual Representation

```
┌─────────────────────────────────────────────────────────────┐
│                    StateGraph Structure                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START                                                       │
│    │                                                         │
│    ▼                                                         │
│  ┌─────────────────┐                                         │
│  │ triage_router  │  ← Node function                       │
│  │                 │     Receives: State                     │
│  │                 │     Returns: Command                    │
│  └─────────────────┘                                         │
│    │                                                         │
│    ├─── "respond" ────► ┌─────────────────┐                │
│    │                     │ response_agent  │                │
│    │                     │                 │                │
│    │                     └─────────────────┘                │
│    │                                                         │
│    └─── "ignore/notify" ────► END                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘

State flows through:
  START → triage_router → (response_agent OR END)
  
Each node:
  - Receives State
  - Processes it
  - Updates State (optionally)
  - Returns Command (where to go next)
```

### How State and StateGraph Work Together

#### Complete Execution Flow

```python
# 1. You invoke the agent with initial state
result = email_agent.invoke({
    "email_input": {
        "author": "Alice <alice@company.com>",
        "to": "John <john@company.com>",
        "subject": "Question",
        "email_thread": "Hi..."
    },
    "messages": []
})

# 2. StateGraph starts at START node
#    State = {"email_input": {...}, "messages": []}

# 3. Goes to triage_router node
#    triage_router(state) is called
#    - Reads: state['email_input']
#    - Processes: Classifies email
#    - Updates: state['messages'] = [...]
#    - Returns: Command(goto="response_agent", update={...})

# 4. StateGraph updates state with the update
#    New state = {"email_input": {...}, "messages": [...]}

# 5. Goes to response_agent node (based on Command)
#    response_agent(state) is called
#    - Reads: state['messages']
#    - Processes: Generates response
#    - Updates: state['messages'] = [..., new messages]
#    - Returns: (implicitly goes to END)

# 6. Final state is returned
```

### Node Functions

Node functions in LangGraph follow this pattern:

```python
def node_function(state: State) -> Command:
    # 1. READ from state
    data = state['some_field']
    
    # 2. PROCESS
    result = do_something(data)
    
    # 3. DECIDE what to update and where to go
    update = {"messages": [...]}  # State updates
    goto = "next_node"             # Where to go next
    
    # 4. RETURN Command
    return Command(goto=goto, update=update)
```

#### Example: Triage Router Node

```python
def triage_router(state: State) -> Command:
    # 1. READ from state
    author = state['email_input']['author']
    subject = state['email_input']['subject']
    
    # 2. PROCESS (classify email)
    result = llm_router.invoke([...])
    
    # 3. DECIDE what to update and where to go
    if result.classification == "respond":
        update = {"messages": [...]}  # Update state
        goto = "response_agent"        # Where to go next
    else:
        update = None                  # No update
        goto = END                     # End the graph
    
    # 4. RETURN Command (tells StateGraph what to do)
    return Command(goto=goto, update=update)
```

### Command Pattern

The `Command` return type controls graph flow:

```python
Command(goto="response_agent", update={...})  # Go to response agent
Command(goto=END, update=None)                # End the graph
```

**Command Components**:
- `goto`: Next node to execute (`"response_agent"` or `END`)
- `update`: State updates to apply (dictionary or None)

### Annotated Fields

```python
messages: Annotated[list, add_messages]
```

**What `Annotated` does**:
- `Annotated[type, reducer]` tells LangGraph how to merge updates
- `add_messages` automatically merges message lists (appends new messages)
- Without `Annotated`, updates would replace the entire list

**Example**:
```python
# Initial state
state = {"messages": [msg1, msg2]}

# Node returns update
update = {"messages": [msg3]}

# With add_messages: Final state = [msg1, msg2, msg3] (merged)
# Without: Final state = [msg3] (replaced)
```

### Key Concepts Summary

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| **State** | Data container that flows through graph | A shared notebook that nodes can read/write |
| **StateGraph** | Graph structure that manages nodes and routing | A flowchart that defines the process |
| **Node** | Function that processes state | A step in the flowchart |
| **Command** | Return value that controls flow | Instructions for next step |
| **Annotated** | Tells LangGraph how to merge updates | Merge strategy for state updates |

### Common Patterns

#### Pattern 1: Conditional Routing

```python
def router_node(state: State) -> Command:
    result = process(state)
    if result == "option_a":
        return Command(goto="node_a", update={...})
    else:
        return Command(goto="node_b", update={...})
```

#### Pattern 2: State Updates

```python
def update_node(state: State) -> Command:
    # Update specific fields
    update = {
        "messages": [...],
        "status": "processed"
    }
    return Command(goto="next_node", update=update)
```

#### Pattern 3: End Early

```python
def check_node(state: State) -> Command:
    if should_end(state):
        return Command(goto=END, update=None)
    return Command(goto="continue_node", update={...})
```

### In Simple Terms

- **State** = The data (like a shared variable)
- **StateGraph** = The workflow (like a flowchart)
- **Node** = A step in the workflow
- **Command** = Instructions for what to do next

Together, they create a graph that processes data step by step, with each node reading and updating the shared state before passing it to the next node.

---

## Current Limitations (Baseline Version)

1. **No Memory**: Each email handled independently
2. **Hard-coded Rules**: Triage rules are static
3. **No Learning**: Doesn't improve over time
4. **Placeholder Tools**: Tools don't actually send emails/schedule meetings

**These will be addressed in later lessons with**:
- Semantic memory (vector stores)
- Episodic memory (conversation history)
- Procedural memory (dynamic rule updates)

---

## File Structure

```
email_agent_with_mem_sys/
├── email_agent_baseline.py    # Main agent implementation
├── prompts.py                  # Prompt templates
├── email_agent_baseline.ipynb  # Jupyter notebook version
└── docs/
    └── email_agent_architecture_notes.md  # This file
```

---

## Summary

The email agent is a **two-stage pipeline**:
1. **Triage**: Classifies emails using Pydantic-validated LLM output
2. **Response**: Generates responses using ReAct agent with tools

**Key Technologies**:
- **LangGraph**: For building the agent graph
- **Pydantic**: For structured output validation
- **LangChain**: For LLM integration and tool management

**Next Steps**: Add memory systems (semantic, episodic, procedural) to make the agent learn and improve over time.

