# Technical Deep Dive: Prompt Optimizer in Email Agent Design

## Overview

This document provides a comprehensive technical analysis of how the prompt optimizer is integrated into the email agent architecture, including data structures, interfaces, data flow, and implementation details.

---

## Part 1: Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Email Agent System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ Triage Router│      │Response Agent│                     │
│  │   (Node)     │─────▶│    (Node)    │                     │
│  └──────────────┘      └──────────────┘                     │
│         │                    │                               │
│         │                    │                               │
│         ▼                    ▼                               │
│  ┌─────────────────────────────────────┐                   │
│  │      InMemoryStore (Procedural)     │                   │
│  │  - agent_instructions                │                   │
│  │  - triage_ignore                     │                   │
│  │  - triage_notify                     │                   │
│  │  - triage_respond                    │                   │
│  └─────────────────────────────────────┘                   │
│         │                                                    │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────┐                   │
│  │   Prompt Optimizer (External)       │                   │
│  │   create_multi_prompt_optimizer     │                   │
│  └─────────────────────────────────────┘                   │
│         │                                                    │
│         │ Updates prompts based on feedback                 │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────┐                   │
│  │   Feedback Loop                     │                   │
│  │   update_agent_from_feedback()      │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Separation of Concerns**: Optimizer is separate from agent execution
2. **Lazy Initialization**: Prompts loaded from store on-demand
3. **Per-User Prompts**: Each user has isolated prompt space
4. **Feedback-Driven**: Updates only happen when user provides feedback
5. **Selective Updates**: Only relevant prompts are updated

---

## Part 2: Data Structures and Interfaces

### 2.1 Optimizer Initialization

```python
optimizer = create_multi_prompt_optimizer(
    "openai:gpt-4o",  # LLM model identifier
    kind="prompt_memory",  # Optimization type
)
```

**Parameters**:
- `model`: String identifier for LLM (e.g., "openai:gpt-4o", "anthropic:claude-3-5-sonnet-latest")
- `kind`: Type of optimization ("prompt_memory" for prompt optimization)

**Returns**: Optimizer object with `invoke()` method

### 2.2 Prompt Configuration Structure

```python
prompt_config = {
    "name": str,                    # Unique identifier
    "prompt": str,                  # Current prompt text
    "update_instructions": str,     # How to format updates
    "when_to_update": str           # Criteria for updating
}
```

**Example**:
```python
{
    "name": "main_agent",
    "prompt": "Use these tools when appropriate to help manage John's tasks efficiently.",
    "update_instructions": "keep the instructions short and to the point",
    "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails or schedule events"
}
```

**Field Purposes**:
- `name`: Maps to store keys (e.g., "main_agent" → "agent_instructions")
- `prompt`: The actual text the agent uses
- `update_instructions`: Guides how optimizer should modify the prompt
- `when_to_update`: Helps optimizer decide if this prompt is relevant to feedback

### 2.3 Trajectory Structure

```python
trajectory = (
    conversation_messages: List[BaseMessage],  # What happened
    feedback: str                               # What should change
)
```

**Example**:
```python
(
    [
        HumanMessage("Respond to the email {...}"),
        AIMessage("I'll draft a response..."),
        ToolMessage("Email sent to alice@company.com..."),
        AIMessage("I've sent a response to Alice...")
    ],
    "Always sign your emails `John Doe`"
)
```

**Components**:
- `conversation_messages`: Full conversation history (LangChain message objects)
- `feedback`: User's instruction/feedback (plain string)

### 2.4 Optimizer Input Structure

```python
optimizer_input = {
    "trajectories": List[Tuple[List[BaseMessage], str]],  # List of (messages, feedback)
    "prompts": List[Dict[str, Any]]                        # List of prompt configs
}
```

**Example**:
```python
{
    "trajectories": [
        (conversation_messages, "Always sign your emails `John Doe`")
    ],
    "prompts": [
        {
            "name": "main_agent",
            "prompt": "...",
            "update_instructions": "...",
            "when_to_update": "..."
        },
        # ... more prompts
    ]
}
```

### 2.5 Optimizer Output Structure

```python
updated_prompts = [
    {
        "name": str,                    # Same as input
        "prompt": str,                  # Updated or unchanged
        "update_instructions": str,     # Same as input
        "when_to_update": str           # Same as input
    },
    # ... one entry per input prompt
]
```

**Important**: Output has same structure as input, but `prompt` field may be updated.

---

## Part 3: Complete Data Flow

### 3.1 Agent Execution → Feedback Collection

```
Step 1: Agent Processes Email
─────────────────────────────
email_input = {
    "author": "alice@company.com",
    "to": "john@company.com",
    "subject": "Meeting Request",
    "email_thread": "..."
}

response = email_agent.invoke(
    {"email_input": email_input},
    config=config
)

Result:
response = {
    "messages": [
        HumanMessage("Respond to the email {...}"),
        AIMessage("I'll draft a response..."),
        ToolMessage("Email sent..."),
        AIMessage("I've sent a response...")
    ],
    "email_input": {...}
}
```

### 3.2 Feedback Collection → Prompt Update

```
Step 2: User Provides Feedback
───────────────────────────────
feedback = "Always sign your emails `John Doe`"

Step 3: Prepare Optimizer Input
────────────────────────────────
conversations = [(response['messages'], feedback)]
# Creates: [([HumanMessage(...), AIMessage(...), ...], "Always sign...")]

prompts = create_prompts_config(store, user_id)
# Retrieves from store and formats:
# [
#   {
#     "name": "main_agent",
#     "prompt": "Use these tools...",
#     "update_instructions": "keep the instructions short and to the point",
#     "when_to_update": "Update when feedback on email writing"
#   },
#   ...
# ]

Step 4: Optimizer Invocation
─────────────────────────────
updated = optimizer.invoke({
    "trajectories": conversations,
    "prompts": prompts
})

Step 5: Store Updates
─────────────────────
updates_made = update_prompts_in_store(
    store, user_id, updated, prompts
)
# Compares old vs new, stores changes
```

### 3.3 Prompt Retrieval → Agent Usage

```
Step 6: Agent Uses Updated Prompts
───────────────────────────────────
# Next time agent runs, create_prompt() retrieves updated prompt:

def create_prompt(state, config, store):
    namespace = (config['configurable']['langgraph_user_id'],)
    result = store.get(namespace, "agent_instructions")
    prompt = result.value['prompt']  # Now includes "Always sign emails..."
    
    return [
        {
            "role": "system",
            "content": agent_system_prompt_memory.format(
                instructions=prompt,  # Updated prompt used here
                **profile
            )
        }
    ] + state['messages']
```

---

## Part 4: Implementation Details

### 4.1 Prompt Retrieval from Store

```python
def get_prompts_from_store(store, user_id):
    """Retrieve all prompts from store for a given user."""
    namespace = (user_id, )
    
    return {
        "main_agent": store.get(namespace, "agent_instructions").value['prompt'],
        "triage-ignore": store.get(namespace, "triage_ignore").value['prompt'],
        "triage-notify": store.get(namespace, "triage_notify").value['prompt'],
        "triage-respond": store.get(namespace, "triage_respond").value['prompt'],
    }
```

**Key Points**:
- Uses `user_id` as namespace for isolation
- Accesses `.value['prompt']` to get stored text
- Returns dictionary mapping names to prompt text

### 4.2 Prompt Configuration Creation

```python
def create_prompts_config(store, user_id):
    """Create prompts configuration for optimizer."""
    prompts_dict = get_prompts_from_store(store, user_id)
    
    return [
        {
            "name": "main_agent",
            "prompt": prompts_dict["main_agent"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails or schedule events"
        },
        # ... more prompts
    ]
```

**Key Points**:
- Adds metadata (`update_instructions`, `when_to_update`)
- Maintains `name` for mapping back to store
- Creates list format required by optimizer

### 4.3 Update Detection and Storage

```python
def update_prompts_in_store(store, user_id, updated_prompts, original_prompts):
    """Update prompts in store based on optimizer output."""
    namespace = (user_id, )
    updates_made = []
    
    for i, updated_prompt in enumerate(updated_prompts):
        old_prompt = original_prompts[i]
        
        # Only update if prompt actually changed
        if updated_prompt['prompt'] != old_prompt['prompt']:
            name = old_prompt['name']
            print(f"✅ Updated {name}")
            updates_made.append(name)
            
            # Map name back to store key
            if name == "main_agent":
                store.put(namespace, "agent_instructions", 
                         {"prompt": updated_prompt['prompt']})
            elif name == "triage-ignore":
                store.put(namespace, "triage_ignore", 
                         {"prompt": updated_prompt['prompt']})
            # ... more mappings
    
    return updates_made
```

**Key Points**:
- **Change Detection**: Only stores if prompt text changed
- **Name Mapping**: Maps prompt names to store keys
- **Tracking**: Returns list of updated prompt names
- **Atomic Updates**: Each prompt updated independently

### 4.4 Feedback Processing

```python
def update_agent_from_feedback(store, user_id, conversation_messages, feedback):
    """
    Update agent prompts based on user feedback.
    """
    # Step 1: Package conversation + feedback
    conversations = [(conversation_messages, feedback)]
    
    # Step 2: Get current prompts from store
    prompts = create_prompts_config(store, user_id)
    
    # Step 3: Optimizer analyzes and updates
    updated = optimizer.invoke({
        "trajectories": conversations,
        "prompts": prompts
    })
    
    # Step 4: Store updated prompts
    updates_made = update_prompts_in_store(store, user_id, updated, prompts)
    
    return updates_made
```

**Key Points**:
- **Single Trajectory**: Currently handles one feedback at a time
- **Synchronous**: Blocks until optimizer completes
- **Returns**: List of updated prompt names for tracking

---

## Part 5: Integration with Agent Architecture

### 5.1 Prompt Loading in Response Agent

```python
def create_prompt(state, config, store):
    """
    Create prompt for response agent.
    Uses procedural memory to load agent instructions from store.
    """
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id, )
    
    # Retrieve agent instructions from store
    result = store.get(namespace, "agent_instructions")
    
    if result is None:
        # Initialize if not exists
        store.put(
            namespace, 
            "agent_instructions", 
            {"prompt": prompt_instructions["agent_instructions"]}
        )
        prompt = prompt_instructions["agent_instructions"]
    else:
        # Use stored version (may be updated by optimizer)
        prompt = result.value['prompt']
    
    # Format system prompt with retrieved instructions
    return [
        {
            "role": "system", 
            "content": agent_system_prompt_memory.format(
                instructions=prompt,  # ← Updated prompt used here
                **profile
            )
        }
    ] + state['messages']
```

**Key Points**:
- **Lazy Initialization**: Creates default if not exists
- **Dynamic Loading**: Always retrieves from store (may be updated)
- **Formatting**: Embeds prompt into system message template

### 5.2 Prompt Loading in Triage Router

```python
def triage_router(state: State) -> Command[...]:
    # ... email extraction ...
    
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id, )
    
    # Retrieve triage rules from store
    result = store.get(namespace, "triage_ignore")
    if result is None:
        # Initialize if not exists
        store.put(namespace, "triage_ignore", 
                 {"prompt": prompt_instructions["triage_rules"]["ignore"]})
        ignore_prompt = prompt_instructions["triage_rules"]["ignore"]
    else:
        # Use stored version (may be updated by optimizer)
        ignore_prompt = result.value['prompt']
    
    # Similar for triage_notify and triage_respond
    # ...
    
    # Use prompts in system prompt
    system_prompt = triage_system_prompt.format(
        # ... other fields ...
        triage_no=ignore_prompt,  # ← Updated prompt used here
        triage_notify=notify_prompt,
        triage_email=respond_prompt,
    )
```

**Key Points**:
- **Per-Rule Loading**: Each triage rule loaded separately
- **Consistent Pattern**: Same lazy initialization pattern
- **Immediate Effect**: Updated prompts used in next triage

---

## Part 6: Optimizer Internal Process (Inferred)

### 6.1 Classification Phase

The optimizer likely performs:

```python
# Internal classification prompt (inferred)
classification_prompt = f"""
You are analyzing agent performance to improve prompts.

Trajectory:
{format_messages(conversation_messages)}

Feedback:
{feedback}

Available Prompts:
{format_prompts_with_criteria(prompts)}

Based on the feedback and trajectory, which prompts should be updated?
Consider the "when_to_update" criteria for each prompt.

Return JSON: {{"which": ["prompt_name1", "prompt_name2"]}}
"""

classification_result = llm.invoke(classification_prompt)
prompts_to_update = classification_result["which"]
```

**Decision Logic**:
- Matches feedback against `when_to_update` criteria
- Considers conversation context
- Selects relevant prompts only

### 6.2 Update Generation Phase

For each selected prompt:

```python
# Internal update prompt (inferred)
for prompt_name in prompts_to_update:
    prompt_config = find_prompt(prompts, prompt_name)
    
    update_prompt = f"""
    Current Prompt:
    {prompt_config['prompt']}
    
    Context:
    - Trajectory: {format_messages(conversation_messages)}
    - Feedback: {feedback}
    - Update Instructions: {prompt_config['update_instructions']}
    - When to Update: {prompt_config['when_to_update']}
    
    Generate an updated version of this prompt that:
    1. Incorporates the feedback naturally
    2. Maintains the original intent
    3. Follows the update instructions
    
    Return only the updated prompt text.
    """
    
    updated_text = llm.invoke(update_prompt)
    prompt_config['prompt'] = updated_text
```

**Update Logic**:
- Incorporates feedback into prompt text
- Maintains original structure and intent
- Follows `update_instructions` guidelines
- Generates natural, readable updates

---

## Part 7: Data Flow Diagram

### Complete Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Agent Execution                                          │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ email_input
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Triage Router                                            │
│    - Loads triage prompts from store                        │
│    - Uses prompts in classification                         │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ classification: "respond"
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Response Agent                                            │
│    - Loads agent_instructions from store                     │
│    - Uses prompt in system message                           │
│    - Executes tools, generates response                      │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ response['messages']
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. User Feedback                                            │
│    feedback = "Always sign emails..."                       │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ (messages, feedback)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Feedback Processing                                      │
│    update_agent_from_feedback()                             │
│    ├─ Package: conversations = [(messages, feedback)]        │
│    ├─ Retrieve: prompts = get_prompts_from_store()         │
│    └─ Format: prompts = create_prompts_config()            │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ {trajectories, prompts}
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Optimizer Analysis                                        │
│    optimizer.invoke()                                        │
│    ├─ Classification: Which prompts need updating?          │
│    └─ Generation: How to update each prompt?                │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ updated_prompts
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Store Updates                                            │
│    update_prompts_in_store()                                │
│    ├─ Compare: old vs new                                   │
│    ├─ Filter: Only changed prompts                          │
│    └─ Store: Save to procedural memory                       │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ (prompts updated in store)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Next Agent Execution                                     │
│    - Agent loads updated prompts from store                  │
│    - Uses new prompts automatically                           │
│    - Behavior reflects feedback                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 8: Key Design Patterns

### 8.1 Lazy Initialization Pattern

```python
result = store.get(namespace, key)
if result is None:
    # Initialize with default
    store.put(namespace, key, default_value)
    value = default_value
else:
    # Use stored value
    value = result.value['prompt']
```

**Benefits**:
- No upfront initialization needed
- Defaults provided on first use
- Allows for prompt updates later

### 8.2 Name Mapping Pattern

```python
# Prompt name → Store key mapping
name_to_key = {
    "main_agent": "agent_instructions",
    "triage-ignore": "triage_ignore",
    "triage-notify": "triage_notify",
    "triage-respond": "triage_respond"
}

# Store update
if name == "main_agent":
    store.put(namespace, "agent_instructions", {...})
```

**Benefits**:
- Decouples prompt names from store keys
- Allows flexible naming
- Centralized mapping logic

### 8.3 Change Detection Pattern

```python
if updated_prompt['prompt'] != old_prompt['prompt']:
    # Only update if changed
    store.put(...)
```

**Benefits**:
- Avoids unnecessary writes
- Efficient storage usage
- Clear tracking of what changed

### 8.4 Metadata-Driven Updates

```python
{
    "when_to_update": "Update when feedback on email writing",
    # Optimizer uses this to decide relevance
}
```

**Benefits**:
- Declarative update criteria
- Flexible and extensible
- Self-documenting

---

## Part 9: Edge Cases and Error Handling

### 9.1 Missing Prompts in Store

**Handled by**: Lazy initialization
```python
result = store.get(namespace, "agent_instructions")
if result is None:
    # Initialize with default
    store.put(namespace, "agent_instructions", default)
```

### 9.2 No Changes Detected

**Handled by**: Change detection
```python
if updated_prompt['prompt'] != old_prompt['prompt']:
    # Only update if changed
    updates_made.append(name)
```

### 9.3 Multiple Feedback Points

**Current Design**: Handles one feedback at a time
```python
conversations = [(conversation_messages, feedback)]
# Could be extended to:
# conversations = [(msg1, feedback1), (msg2, feedback2), ...]
```

### 9.4 Optimizer Failure

**Not Explicitly Handled**: Would raise exception
**Recommendation**: Add try/except with fallback

---

## Part 10: Performance Considerations

### 10.1 LLM API Calls

**Cost**: Each optimization requires LLM calls
- Classification phase: 1 call
- Update generation: 1 call per prompt to update
- Total: 1-5 calls per feedback (depending on prompts updated)

**Latency**: 
- Each LLM call: 1-5 seconds
- Total optimization: 2-25 seconds

### 10.2 Store Operations

**Reads**: 
- `get_prompts_from_store()`: 4 reads (one per prompt)
- `create_prompt()`: 1 read per agent execution
- `triage_router()`: 3 reads per triage

**Writes**:
- Only when prompts actually change
- Typically 1 write per feedback

### 10.3 Optimization Strategies

1. **Batch Updates**: Process multiple feedbacks together
2. **Caching**: Cache optimizer results for similar feedback
3. **Async Processing**: Make optimizer calls async
4. **Selective Updates**: Only update when necessary (already done)

---

## Part 11: Testing and Validation

### 11.1 Test Flow

```python
# Test 1: Initial execution
response = email_agent.invoke(...)

# Test 2: Check default prompts
print(store.get(namespace, "agent_instructions").value['prompt'])

# Test 3: Provide feedback
updates = update_agent_from_feedback(store, user_id, 
                                     response['messages'], 
                                     "Always sign emails...")

# Test 4: Verify updates
print(store.get(namespace, "agent_instructions").value['prompt'])
# Should include "Always sign emails..."

# Test 5: Execute again with updated prompts
response2 = email_agent.invoke(...)
# Should now sign emails automatically
```

### 11.2 Validation Points

1. **Prompt Retrieval**: Verify prompts loaded correctly
2. **Optimizer Input**: Verify correct format
3. **Optimizer Output**: Verify updates are reasonable
4. **Store Updates**: Verify only changed prompts updated
5. **Agent Behavior**: Verify agent uses updated prompts

---

## Part 12: Extensibility

### 12.1 Adding New Prompts

```python
# 1. Add to get_prompts_from_store()
def get_prompts_from_store(store, user_id):
    return {
        # ... existing prompts ...
        "new_prompt": store.get(namespace, "new_prompt_key").value['prompt'],
    }

# 2. Add to create_prompts_config()
def create_prompts_config(store, user_id):
    return [
        # ... existing configs ...
        {
            "name": "new_prompt",
            "prompt": prompts_dict["new_prompt"],
            "update_instructions": "...",
            "when_to_update": "..."
        }
    ]

# 3. Add to update_prompts_in_store()
if name == "new_prompt":
    store.put(namespace, "new_prompt_key", {"prompt": updated_prompt['prompt']})
```

### 12.2 Custom Update Logic

```python
# Could add custom update handlers
def custom_update_handler(prompt_name, old_prompt, feedback):
    if prompt_name == "special_prompt":
        # Custom logic
        return custom_updated_prompt
    return None
```

---

## Part 13: Summary

### Key Technical Points

1. **Architecture**: Optimizer is separate component, integrated via feedback loop
2. **Data Flow**: Agent → Feedback → Optimizer → Store → Agent (cycle)
3. **Storage**: Prompts stored in procedural memory, loaded on-demand
4. **Updates**: Selective, change-detection based, metadata-driven
5. **Integration**: Seamless - agent automatically uses updated prompts

### Design Strengths

- ✅ **Separation of Concerns**: Optimizer separate from agent execution
- ✅ **Lazy Loading**: Prompts loaded when needed
- ✅ **Selective Updates**: Only relevant prompts updated
- ✅ **Metadata-Driven**: Flexible update criteria
- ✅ **Change Detection**: Efficient storage usage

### Areas for Improvement

- ⚠️ **Error Handling**: Add try/except for optimizer failures
- ⚠️ **Batch Processing**: Support multiple feedbacks at once
- ⚠️ **Caching**: Cache optimizer results
- ⚠️ **Async**: Make optimizer calls async
- ⚠️ **Validation**: Add prompt validation before storing

---

## Part 14: Code References

### Key Functions

```504:507:email_agent_with_longmem.py
optimizer = create_multi_prompt_optimizer(
    "openai:gpt-4o",  # Can also use "anthropic:claude-3-5-sonnet-latest"
    kind="prompt_memory",
)
```

```583:605:email_agent_with_longmem.py
def update_agent_from_feedback(store, user_id, conversation_messages, feedback):
    """
    Update agent prompts based on user feedback.
    
    Args:
        store: Memory store
        user_id: User identifier
        conversation_messages: Previous conversation messages
        feedback: User feedback string
    
    Returns:
        List of updated prompt names
    """
    conversations = [(conversation_messages, feedback)]
    prompts = create_prompts_config(store, user_id)
    
    updated = optimizer.invoke({
        "trajectories": conversations,
        "prompts": prompts
    })
    
    updates_made = update_prompts_in_store(store, user_id, updated, prompts)
    return updates_made
```

```434:468:email_agent_with_longmem.py
def create_prompt(state, config, store):
    """
    Create prompt for response agent.
    
    Uses procedural memory to load agent instructions from store.
    """
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id, )
    
    # ========== PROCEDURAL MEMORY: RETRIEVE ==========
    # Retrieve agent instructions from store
    result = store.get(namespace, "agent_instructions")
    if result is None:
        # ========== PROCEDURAL MEMORY: CREATE ==========
        # Initialize agent_instructions if not exists
        store.put(
            namespace, 
            "agent_instructions", 
            {"prompt": prompt_instructions["agent_instructions"]}
        )
        prompt = prompt_instructions["agent_instructions"]
    else:
        # ========== PROCEDURAL MEMORY: RETRIEVE ==========
        # Use stored agent_instructions
        prompt = result.value['prompt']
    
    return [
        {
            "role": "system", 
            "content": agent_system_prompt_memory.format(
                instructions=prompt, 
                **profile
            )
        }
    ] + state['messages']
```

---

This technical analysis provides a complete understanding of how the prompt optimizer is integrated into the email agent design, from data structures to implementation details to design patterns.

