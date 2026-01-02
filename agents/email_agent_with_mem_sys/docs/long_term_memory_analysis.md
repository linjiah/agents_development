# Long-Term Memory Implementation Analysis

## Overview

This document analyzes how three types of long-term memory have been added to the baseline email agent and what new features they enable.

---

## Table of Contents

1. [Memory Store Setup](#memory-store-setup)
2. [Semantic Memory - Few-Shot Examples](#semantic-memory---few-shot-examples)
3. [Episodic Memory - Conversation History](#episodic-memory---conversation-history)
4. [Procedural Memory - Dynamic Prompts](#procedural-memory---dynamic-prompts)
5. [Key Changes from Baseline](#key-changes-from-baseline)
6. [New Features Summary](#new-features-summary)

---

## Memory Store Setup

### Implementation (Cells 9-10)

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)
```

**What it does**:
- Creates a unified storage system for all three memory types
- Enables vector embeddings for semantic search
- Provides key-value storage for procedural memory
- Supports namespace-based organization

**Key Features**:
- **Vector Index**: `"embed": "openai:text-embedding-3-small"` enables semantic similarity search
- **Namespace Support**: Organizes memories by user/context (e.g., `("email_assistant", user_id, "collection")`)
- **Persistent Storage**: Memories survive across agent invocations

---

## Semantic Memory - Few-Shot Examples

### Purpose
Store and retrieve similar email examples to improve triage classification accuracy through few-shot learning.

### Implementation Details

#### 1. Template and Formatting (Cell 11)

```python
template = """Email Subject: {subject}
Email From: {from_email}
Email To: {to_email}
Email Content: 
```
{content}
```
> Triage Result: {result}"""

def format_few_shot_examples(examples):
    strs = ["Here are some previous examples:"]
    for eg in examples:
        strs.append(template.format(...))
    return "\n\n------------\n\n".join(strs)
```

**What it does**:
- Formats stored email examples into a readable prompt format
- Includes email metadata (subject, from, to) and classification result
- Prepares examples for inclusion in the triage prompt

#### 2. Integration in Triage Router (Cell 22)

```python
def triage_router(state: State, config, store) -> Command:
    # Semantic memory retrieval
    namespace = (
        "email_assistant",
        config['configurable']['langgraph_user_id'],
        "examples"
    )
    examples = store.search(
        namespace, 
        query=str({"email": state['email_input']})
    ) 
    examples = format_few_shot_examples(examples)
```

**How it works**:
1. **Vector Search**: Uses embedding similarity to find similar emails
2. **Namespace**: `("email_assistant", user_id, "examples")` organizes examples by user
3. **Query**: Searches using the current email as query
4. **Format**: Converts results into few-shot examples

#### 3. Prompt Integration (Cell 12, 22)

```python
triage_system_prompt = """
...
< Few shot examples >
Here are some examples of previous emails, and how they should be handled.
Follow these examples more than any instructions above
{examples}
</ Few shot examples >
"""

system_prompt = triage_system_prompt.format(
    ...,
    examples=examples  # Few-shot examples from semantic memory
)
```

**Key Benefits**:
- **Context-Aware Classification**: Uses similar past emails to guide decisions
- **Learning from History**: Improves accuracy by learning from previous classifications
- **Adaptive**: Automatically finds relevant examples for each email

### How to Store Examples

To populate semantic memory, you would store examples like:

```python
store.put(
    ("email_assistant", user_id, "examples"),
    "example_1",
    {
        "email": {
            "subject": "...",
            "author": "...",
            "to": "...",
            "email_thread": "..."
        },
        "label": "respond"  # or "ignore", "notify"
    }
)
```

---

## Episodic Memory - Conversation History

### Purpose
Remember details from previous email interactions, contacts, preferences, and conversations.

### Implementation Details

#### 1. Memory Tools Setup (Cells 28-29)

```python
from langmem import create_manage_memory_tool, create_search_memory_tool

manage_memory_tool = create_manage_memory_tool(
    namespace=(
        "email_assistant", 
        "{langgraph_user_id}",
        "collection"
    )
)
search_memory_tool = create_search_memory_tool(
    namespace=(
        "email_assistant",
        "{langgraph_user_id}",
        "collection"
    )
)
```

**What it does**:
- Creates tools that the agent can use to store and retrieve memories
- Namespace: `("email_assistant", user_id, "collection")` organizes episodic memories
- Dynamic user ID: `{langgraph_user_id}` allows per-user memory isolation

#### 2. Agent Integration (Cell 30, 35)

```python
agent_system_prompt_memory = """
< Tools >
...
4. manage_memory - Store any relevant information about contacts, actions, discussion, etc. in memory for future reference
5. search_memory - Search for any relevant information that may have been stored in memory
</ Tools >
"""

tools = [
    write_email,
    schedule_meeting,
    check_calendar_availability,
    manage_memory_tool,  # NEW: Store memories
    search_memory_tool   # NEW: Search memories
]

response_agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
    store=store  # Pass store to agent
)
```

**How it works**:
1. **Agent can store**: When processing emails, agent can call `manage_memory()` to save:
   - Contact information
   - Previous conversations
   - User preferences
   - Important details

2. **Agent can search**: Agent can call `search_memory()` to recall:
   - Past interactions with a contact
   - Previous email threads
   - User preferences
   - Context for current email

3. **Automatic Context**: Agent uses these tools during email processing to maintain context

### Example Usage

```python
# Agent automatically uses these tools:
# When processing email from Alice:
search_memory("email_assistant", user, "collection", query="Alice Jones")
# Returns: Previous interactions, preferences, etc.

# After processing:
manage_memory("email_assistant", user, "collection", 
              content="Alice prefers formal tone, works on API team")
```

**Key Benefits**:
- **Context Continuity**: Remembers past conversations
- **Personalization**: Recalls user preferences and contact details
- **Better Responses**: Uses historical context to craft appropriate responses

---

## Procedural Memory - Dynamic Prompts

### Purpose
Update agent instructions and triage rules based on user feedback, allowing the agent to learn and adapt.

### Implementation Details

#### 1. Storing Prompts in Memory (Cell 22, 32)

**Triage Router - Retrieving/Storing Triage Rules**:

```python
def triage_router(state: State, config, store) -> Command:
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id, )
    
    # Get or initialize triage_ignore
    result = store.get(namespace, "triage_ignore")
    if result is None:
        store.put(namespace, "triage_ignore", 
                  {"prompt": prompt_instructions["triage_rules"]["ignore"]})
        ignore_prompt = prompt_instructions["triage_rules"]["ignore"]
    else:
        ignore_prompt = result.value['prompt']  # Use stored version
    
    # Same for triage_notify and triage_respond
```

**Response Agent - Retrieving/Storing Instructions**:

```python
def create_prompt(state, config, store):
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id, )
    
    result = store.get(namespace, "agent_instructions")
    if result is None:
        store.put(namespace, "agent_instructions", 
                  {"prompt": prompt_instructions["agent_instructions"]})
        prompt = prompt_instructions["agent_instructions"]
    else:
        prompt = result.value['prompt']  # Use stored version
```

**What it does**:
- **Lazy Initialization**: Stores default prompts on first use
- **Persistent Storage**: Prompts survive across sessions
- **Per-User Prompts**: Each user can have customized prompts

#### 2. Prompt Optimizer (Cells 48-66)

```python
from langmem import create_multi_prompt_optimizer

optimizer = create_multi_prompt_optimizer(
    "openai:gpt-4o",
    kind="prompt_memory",
)

# User provides feedback
conversations = [
    (
        response['messages'],  # Previous conversation
        "Always sign your emails `John Doe`"  # User feedback
    )
]

# Define prompts to potentially update
prompts = [
    {
        "name": "main_agent",
        "prompt": store.get(("lance",), "agent_instructions").value['prompt'],
        "update_instructions": "keep the instructions short and to the point",
        "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails or schedule events"
    },
    {
        "name": "triage-ignore",
        "prompt": store.get(("lance",), "triage_ignore").value['prompt'],
        ...
    },
    # ... more prompts
]

# Optimizer analyzes and updates
updated = optimizer.invoke({
    "trajectories": conversations,
    "prompts": prompts
})
```

**How it works**:
1. **Feedback Collection**: User provides feedback on agent behavior
2. **Analysis**: Optimizer (LLM) analyzes conversation + feedback
3. **Smart Updates**: Determines which prompts need updating
4. **Prompt Refinement**: Updates prompts to incorporate feedback
5. **Storage**: Saves updated prompts back to store

#### 3. Updating Stored Prompts (Cell 56, 65)

```python
for i, updated_prompt in enumerate(updated):
    old_prompt = prompts[i]
    if updated_prompt['prompt'] != old_prompt['prompt']:
        name = old_prompt['name']
        print(f"updated {name}")
        
        if name == "main_agent":
            store.put(("lance",), "agent_instructions",
                     {"prompt": updated_prompt['prompt']})
        elif name == "triage-ignore":
            store.put(("lance",), "triage_ignore",
                     {"prompt": updated_prompt['prompt']})
        # ... handle other prompts
```

**What it does**:
- Compares old vs new prompts
- Only updates if prompt changed
- Saves updated prompts to store
- Future emails use updated prompts automatically

### Example Learning Loop

**Step 1: Initial Behavior**
```python
# Agent responds without signature
response = email_agent.invoke({"email_input": email_input}, config=config)
```

**Step 2: User Feedback**
```python
conversations = [
    (response['messages'], "Always sign your emails `John Doe`")
]
```

**Step 3: Prompt Update**
```python
updated = optimizer.invoke({"trajectories": conversations, "prompts": prompts})
# Optimizer updates: "Use these tools... Always sign emails with 'John Doe'."
```

**Step 4: Store Update**
```python
store.put(("lance",), "agent_instructions", {"prompt": updated_prompt['prompt']})
```

**Step 5: New Behavior**
```python
# Next email automatically includes signature
response = email_agent.invoke({"email_input": email_input}, config=config)
# Email now signed: "Best regards, John Doe"
```

**Key Benefits**:
- **Adaptive Learning**: Agent improves from user feedback
- **Personalization**: Instructions adapt to user preferences
- **Persistent Changes**: Updates survive across sessions
- **Multi-Prompt Updates**: Can update multiple prompts simultaneously

---

## Key Changes from Baseline

### 1. Triage Router Changes

**Baseline**:
```python
def triage_router(state: State) -> Command:
    # Hard-coded rules
    system_prompt = triage_system_prompt.format(
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
        examples=None  # No examples
    )
```

**With Memory**:
```python
def triage_router(state: State, config, store) -> Command:
    # 1. Get few-shot examples (semantic memory)
    examples = store.search(namespace, query=...)
    
    # 2. Get rules from store (procedural memory)
    ignore_prompt = store.get(namespace, "triage_ignore").value['prompt']
    notify_prompt = store.get(namespace, "triage_notify").value['prompt']
    respond_prompt = store.get(namespace, "triage_respond").value['prompt']
    
    # 3. Use in prompt
    system_prompt = triage_system_prompt.format(
        triage_no=ignore_prompt,      # From store
        triage_notify=notify_prompt,  # From store
        triage_email=respond_prompt,  # From store
        examples=examples             # From semantic search
    )
```

**Changes**:
- Added `config` and `store` parameters
- Retrieves rules from procedural memory
- Retrieves examples from semantic memory
- Rules can be updated dynamically

### 2. Response Agent Changes

**Baseline**:
```python
def create_prompt(state):
    return [{
        "role": "system",
        "content": agent_system_prompt.format(
            instructions=prompt_instructions["agent_instructions"],  # Hard-coded
            **profile
        )
    }] + state['messages']

tools = [write_email, schedule_meeting, check_calendar_availability]
agent = create_react_agent("openai:gpt-4o", tools=tools, prompt=create_prompt)
```

**With Memory**:
```python
def create_prompt(state, config, store):
    # Get instructions from store (procedural memory)
    result = store.get(namespace, "agent_instructions")
    prompt = result.value['prompt'] if result else default_prompt
    
    return [{
        "role": "system",
        "content": agent_system_prompt_memory.format(
            instructions=prompt,  # From store (can be updated)
            **profile
        )
    }] + state['messages']

tools = [
    write_email,
    schedule_meeting,
    check_calendar_availability,
    manage_memory_tool,  # NEW: Episodic memory
    search_memory_tool   # NEW: Episodic memory
]
agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
    store=store  # NEW: Pass store to agent
)
```

**Changes**:
- Added `config` and `store` parameters
- Instructions loaded from procedural memory
- Added memory tools for episodic memory
- Store passed to agent for tool access

### 3. Graph Compilation Changes

**Baseline**:
```python
email_agent = StateGraph(State)
email_agent = email_agent.add_node("triage_router", triage_router)
email_agent = email_agent.add_node("response_agent", agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile()
```

**With Memory**:
```python
email_agent = StateGraph(State)
email_agent = email_agent.add_node("triage_router", triage_router)
email_agent = email_agent.add_node("response_agent", response_agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile(store=store)  # NEW: Pass store
```

**Changes**:
- Store passed to `compile()` to enable memory access

### 4. Invocation Changes

**Baseline**:
```python
response = email_agent.invoke({"email_input": email_input})
```

**With Memory**:
```python
config = {"configurable": {"langgraph_user_id": "lance"}}
response = email_agent.invoke(
    {"email_input": email_input},
    config=config  # NEW: Required for user-specific memory
)
```

**Changes**:
- Must provide `config` with `langgraph_user_id` for user-specific memory

---

## New Features Summary

### 1. Semantic Memory Features

✅ **Few-Shot Learning**
- Retrieves similar email examples
- Improves classification accuracy
- Context-aware triage decisions

✅ **Vector Search**
- Uses embeddings for similarity
- Finds relevant examples automatically
- Scales to large example sets

### 2. Episodic Memory Features

✅ **Conversation History**
- Remembers past email interactions
- Recalls contact preferences
- Maintains context across sessions

✅ **Memory Tools**
- `manage_memory()`: Store information
- `search_memory()`: Retrieve information
- Agent uses automatically during processing

✅ **Personalization**
- Per-user memory isolation
- Remembers user-specific preferences
- Context-aware responses

### 3. Procedural Memory Features

✅ **Dynamic Prompt Updates**
- Instructions adapt from feedback
- Triage rules can be refined
- Multi-prompt optimization

✅ **Learning Loop**
- User provides feedback
- Optimizer analyzes and updates
- Changes persist across sessions

✅ **Per-User Customization**
- Each user has own prompts
- Isolated memory namespaces
- Personalized behavior

### 4. Overall System Features

✅ **Persistent Memory**
- All memories survive across sessions
- No need to re-train or re-configure
- Long-term learning

✅ **Unified Storage**
- Single store for all memory types
- Consistent API
- Easy to extend

✅ **User Isolation**
- Per-user memory namespaces
- Multi-user support
- Privacy by design

---

## Memory Type Comparison

| Memory Type | Storage Location | Update Method | Use Case |
|------------|-----------------|---------------|----------|
| **Semantic** | `("email_assistant", user_id, "examples")` | Manual storage of examples | Few-shot learning for triage |
| **Episodic** | `("email_assistant", user_id, "collection")` | Agent tools (automatic) | Conversation history, contacts |
| **Procedural** | `(user_id,)` | Prompt optimizer (feedback-driven) | Instructions, rules, preferences |

---

## Example Workflow

### Complete Learning Cycle

1. **Initial State**: Agent uses default prompts
2. **Process Email**: Agent classifies and responds
3. **User Feedback**: "Always sign emails with 'John Doe'"
4. **Optimizer**: Analyzes conversation + feedback
5. **Prompt Update**: Updates `agent_instructions` prompt
6. **Store Update**: Saves to procedural memory
7. **Next Email**: Automatically uses updated prompt
8. **Result**: All future emails signed correctly

### Memory Interaction Flow

```
Email Arrives
    ↓
Triage Router:
  - Searches semantic memory (few-shot examples)
  - Loads procedural memory (triage rules)
  - Classifies email
    ↓
Response Agent:
  - Loads procedural memory (agent instructions)
  - Searches episodic memory (past conversations)
  - Generates response
  - Stores to episodic memory (new information)
    ↓
User Feedback:
  - Optimizer analyzes conversation
  - Updates procedural memory (prompts)
    ↓
Next Email:
  - Uses updated memories
  - Better performance
```

---

## Key Takeaways

1. **Semantic Memory** enables few-shot learning for better triage
2. **Episodic Memory** maintains conversation context and personalization
3. **Procedural Memory** allows adaptive learning from feedback
4. **Unified Store** provides consistent memory management
5. **User Isolation** enables multi-user personalization
6. **Persistent Learning** improves over time without retraining

The agent has evolved from a static rule-based system to an adaptive, learning system that improves with use!

