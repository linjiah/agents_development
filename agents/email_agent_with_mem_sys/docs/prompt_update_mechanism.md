# Deep Dive: How Prompt Updates Work

## Overview

This document explains the detailed mechanism of how prompts are updated based on user feedback using the `update_agent_from_feedback()` function and the prompt optimizer.

---

## Complete Update Flow

### Step-by-Step Process

```
User Feedback
    ↓
update_agent_from_feedback()
    ↓
1. Prepare Input (conversations + prompts)
    ↓
2. Optimizer Analyzes (LLM-based)
    ↓
3. Optimizer Updates Prompts
    ↓
4. Store Updated Prompts
    ↓
5. Return Updated Prompt Names
```

---

## Detailed Breakdown

### Step 1: Function Call

```python
updates = update_agent_from_feedback(
    store,                                    # Memory store
    config['configurable']['langgraph_user_id'],  # User ID: "lance"
    response['messages'],                     # Conversation from Test 1
    feedback                                 # "Always sign your emails `John Doe`"
)
```

**Input Parameters**:
- `store`: The InMemoryStore containing all prompts
- `user_id`: "lance" (for user-specific prompts)
- `conversation_messages`: All messages from the agent's previous response
- `feedback`: User's instruction/feedback

---

### Step 2: Inside `update_agent_from_feedback()`

```python
def update_agent_from_feedback(store, user_id, conversation_messages, feedback):
    # Step 2a: Package conversation + feedback
    conversations = [(conversation_messages, feedback)]
    # Creates: [([all messages], "Always sign your emails `John Doe`")]
    
    # Step 2b: Get current prompts from store
    prompts = create_prompts_config(store, user_id)
    
    # Step 2c: Optimizer analyzes and updates
    updated = optimizer.invoke({
        "trajectories": conversations,
        "prompts": prompts
    })
    
    # Step 2d: Store updated prompts
    updates_made = update_prompts_in_store(store, user_id, updated, prompts)
    return updates_made
```

---

### Step 2a: Package Conversation + Feedback

```python
conversations = [(conversation_messages, feedback)]
```

**What this creates**:
```python
[
    (
        [
            HumanMessage("Respond to the email {...}"),
            AIMessage("I'll draft a response..."),
            ToolMessage("Email sent to alice@company.com..."),
            AIMessage("I've sent a response to Alice...")
        ],
        "Always sign your emails `John Doe`"  # Feedback
    )
]
```

**Purpose**: Tells the optimizer:
- **What happened**: The agent's conversation
- **What's wrong**: User feedback about what should change

---

### Step 2b: Get Current Prompts Configuration

```python
prompts = create_prompts_config(store, user_id)
```

**What `create_prompts_config()` does**:

1. **Retrieves all prompts from store**:
```python
def get_prompts_from_store(store, user_id):
    namespace = (user_id, )  # ("lance",)
    return {
        "main_agent": store.get(namespace, "agent_instructions").value['prompt'],
        "triage-ignore": store.get(namespace, "triage_ignore").value['prompt'],
        "triage-notify": store.get(namespace, "triage_notify").value['prompt'],
        "triage-respond": store.get(namespace, "triage_respond").value['prompt'],
    }
```

2. **Creates configuration for optimizer**:
```python
def create_prompts_config(store, user_id):
    prompts_dict = get_prompts_from_store(store, user_id)
    return [
        {
            "name": "main_agent",
            "prompt": "Use these tools when appropriate to help manage John's tasks efficiently.",
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails or schedule events"
        },
        {
            "name": "triage-ignore",
            "prompt": "Marketing newsletters, spam emails, mass company announcements",
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails should be ignored"
        },
        # ... more prompts
    ]
```

**Key Fields**:
- `name`: Identifier for the prompt
- `prompt`: Current prompt text
- `update_instructions`: How to format updates
- `when_to_update`: Criteria for when this prompt should be updated

---

### Step 2c: Optimizer Analysis (The Magic Happens Here)

```python
updated = optimizer.invoke({
    "trajectories": conversations,  # What happened + feedback
    "prompts": prompts              # All current prompts
})
```

**What the Optimizer (LLM) Does Internally**:

#### Phase 1: Classification

The optimizer first decides **which prompts need updating**:

```python
# Internal LLM call (simplified)
classification_prompt = f"""
Analyze the following trajectories and decide which prompts 
ought to be updated to improve performance on future trajectories:

Trajectory:
{conversation_messages}

Feedback: {feedback}

Available Prompts:
{list of all prompts with their "when_to_update" criteria}

Return JSON with "which": [...], listing the names of prompts that need updates.
"""

result = llm.invoke(classification_prompt)
# Returns: {"which": ["main_agent"]}  # Only main_agent needs updating
```

#### Phase 2: Update Generation

For each prompt that needs updating, the optimizer generates an improved version:

```python
# For "main_agent" prompt
update_prompt = f"""
Current Prompt: "Use these tools when appropriate to help manage John's tasks efficiently."

Context:
- Conversation: {conversation_messages}
- Feedback: "Always sign your emails `John Doe`"
- Update Instructions: "keep the instructions short and to the point"
- When to Update: "Update this prompt whenever there is feedback on how the agent should write emails or schedule events"

Generate an updated version of this prompt that incorporates the feedback while maintaining the original intent.
Keep it short and to the point.
"""

updated_prompt = llm.invoke(update_prompt)
# Returns: "Use these tools when appropriate to help manage John's tasks efficiently. Always sign emails with 'John Doe'."
```

#### Phase 3: Return Updated Prompts

The optimizer returns a list of all prompts (updated or unchanged):

```python
[
    {
        "name": "main_agent",
        "prompt": "Use these tools when appropriate to help manage John's tasks efficiently. Always sign emails with 'John Doe'.",
        "update_instructions": "keep the instructions short and to the point",
        "when_to_update": "..."
    },
    {
        "name": "triage-ignore",
        "prompt": "Marketing newsletters, spam emails, mass company announcements",  # Unchanged
        ...
    },
    # ... other prompts (unchanged)
]
```

---

### Step 2d: Store Updated Prompts

```python
updates_made = update_prompts_in_store(store, user_id, updated, prompts)
```

**What `update_prompts_in_store()` does**:

```python
def update_prompts_in_store(store, user_id, updated_prompts, original_prompts):
    namespace = (user_id, )
    updates_made = []
    
    # Compare each updated prompt with original
    for i, updated_prompt in enumerate(updated_prompts):
        old_prompt = original_prompts[i]
        
        # Check if prompt actually changed
        if updated_prompt['prompt'] != old_prompt['prompt']:
            name = old_prompt['name']
            print(f"✅ Updated {name}")
            updates_made.append(name)
            
            # Store the updated prompt
            if name == "main_agent":
                store.put(namespace, "agent_instructions", 
                         {"prompt": updated_prompt['prompt']})
            elif name == "triage-ignore":
                store.put(namespace, "triage_ignore", 
                         {"prompt": updated_prompt['prompt']})
            # ... handle other prompts
```

**Process**:
1. **Compare**: Check if each prompt changed
2. **Filter**: Only store prompts that actually changed
3. **Store**: Save updated prompts to procedural memory
4. **Return**: List of which prompts were updated

---

## Complete Example Walkthrough

### Input

```python
feedback = "Always sign your emails `John Doe`"
conversation_messages = [
    HumanMessage("Respond to the email {...}"),
    AIMessage("I'll draft a response..."),
    ToolMessage("Email sent..."),
    AIMessage("I've sent a response...")
]
```

### Step-by-Step Execution

#### 1. Package Input
```python
conversations = [(
    [HumanMessage(...), AIMessage(...), ...],
    "Always sign your emails `John Doe`"
)]
```

#### 2. Get Current Prompts
```python
prompts = [
    {
        "name": "main_agent",
        "prompt": "Use these tools when appropriate to help manage John's tasks efficiently.",
        "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails..."
    },
    # ... other prompts
]
```

#### 3. Optimizer Analysis

**LLM receives**:
```
Trajectory:
- Human: "Respond to the email..."
- AI: "I'll draft a response..."
- Tool: "Email sent..."
- AI: "I've sent a response..."

Feedback: "Always sign your emails `John Doe`"

Prompts to consider:
1. main_agent: "Use these tools..." 
   → Update when: "feedback on how the agent should write emails"
2. triage-ignore: "Marketing newsletters..."
   → Update when: "feedback on which emails should be ignored"
...
```

**LLM decides**:
- ✅ `main_agent` needs updating (feedback is about email writing)
- ❌ `triage-ignore` doesn't need updating (not relevant)
- ❌ `triage-notify` doesn't need updating (not relevant)
- ❌ `triage-respond` doesn't need updating (not relevant)

**LLM generates update**:
```
Original: "Use these tools when appropriate to help manage John's tasks efficiently."
Updated:  "Use these tools when appropriate to help manage John's tasks efficiently. Always sign emails with 'John Doe'."
```

#### 4. Return Updated Prompts
```python
updated = [
    {
        "name": "main_agent",
        "prompt": "Use these tools... Always sign emails with 'John Doe'."  # Changed!
    },
    {
        "name": "triage-ignore",
        "prompt": "Marketing newsletters..."  # Unchanged
    },
    # ... others unchanged
]
```

#### 5. Store Updates
```python
# Compare
updated[0]['prompt'] != prompts[0]['prompt']  # True → Changed!

# Store
store.put(("lance",), "agent_instructions", 
         {"prompt": "Use these tools... Always sign emails with 'John Doe'."})

# Return
updates_made = ["main_agent"]
```

---

## Key Components Explained

### 1. `conversations` Format

```python
conversations = [(conversation_messages, feedback)]
```

**Structure**: List of tuples
- **Tuple[0]**: List of messages (what happened)
- **Tuple[1]**: Feedback string (what should change)

**Why this format?**:
- Allows multiple feedback points
- Links feedback to specific conversations
- Optimizer can see context

### 2. `prompts` Configuration

Each prompt has:
- **`name`**: Identifier
- **`prompt`**: Current text
- **`update_instructions`**: How to format updates
- **`when_to_update`**: Criteria for updating

**Why these fields?**:
- `when_to_update`: Helps optimizer decide relevance
- `update_instructions`: Guides how to incorporate feedback
- `name`: Maps updates back to store keys

### 3. Optimizer's Decision Process

The optimizer uses the `when_to_update` field to decide:

```python
# Example decision logic (simplified)
for prompt in prompts:
    if feedback_matches(prompt['when_to_update'], feedback):
        # This prompt should be updated
        updated_prompt = incorporate_feedback(prompt, feedback)
    else:
        # Keep unchanged
        updated_prompt = prompt
```

**Example**:
- Feedback: "Always sign emails"
- `main_agent.when_to_update`: "feedback on how the agent should write emails"
- ✅ Match! → Update `main_agent`

- Feedback: "Always sign emails"
- `triage-ignore.when_to_update`: "feedback on which emails should be ignored"
- ❌ No match → Don't update

### 4. Change Detection

```python
if updated_prompt['prompt'] != old_prompt['prompt']:
    # Store the update
```

**Why check?**:
- Avoids unnecessary store writes
- Only updates what actually changed
- Efficient memory usage

---

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ update_agent_from_feedback()                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Package Input                                        │
│ conversations = [(messages, feedback)]                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Get Current Prompts                                  │
│ prompts = create_prompts_config(store, user_id)             │
│   → Retrieves: main_agent, triage-ignore, etc.             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Optimizer Analysis (LLM)                            │
│                                                              │
│ optimizer.invoke({                                          │
│   "trajectories": conversations,                            │
│   "prompts": prompts                                        │
│ })                                                           │
│                                                              │
│ Internal Process:                                            │
│ 1. Classify: Which prompts need updating?                   │
│    → Analyzes feedback + when_to_update criteria            │
│    → Decides: ["main_agent"]                                │
│                                                              │
│ 2. Generate: How to update?                                  │
│    → Incorporates feedback into prompt                      │
│    → "Use tools... Always sign emails with 'John Doe'."     │
│                                                              │
│ 3. Return: All prompts (updated + unchanged)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Store Updates                                        │
│                                                              │
│ update_prompts_in_store()                                   │
│   → Compare: old vs new                                     │
│   → Filter: Only changed prompts                            │
│   → Store: Save to procedural memory                        │
│   → Return: ["main_agent"]                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Result: Updated Prompts in Store                            │
│                                                              │
│ store.get(("lance",), "agent_instructions")                 │
│ → "Use tools... Always sign emails with 'John Doe'."        │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Design?

### 1. LLM-Based Updates (Not Simple String Replacement)

**Why use an LLM?**:
- **Context Understanding**: Understands what feedback means
- **Smart Integration**: Incorporates feedback naturally
- **Multi-Prompt Coordination**: Can update related prompts together
- **Quality Control**: Generates well-formatted prompts

**Example**:
- Simple replacement: "Add 'Always sign emails' to prompt"
- LLM update: "Use tools... Always sign emails with 'John Doe'." (natural, contextual)

### 2. Selective Updates

**Why not update all prompts?**:
- **Efficiency**: Only update what's relevant
- **Safety**: Don't break unrelated prompts
- **Precision**: Feedback applies to specific aspects

### 3. Metadata-Driven

**Why `when_to_update` field?**:
- **Guidance**: Tells optimizer when to update
- **Flexibility**: Different prompts have different criteria
- **Maintainability**: Easy to adjust update logic

---

## Example: Multiple Prompts Updated

If feedback is: "Ignore any emails from Alice Jones"

**Optimizer Analysis**:
- Feedback: About email classification
- `triage-ignore.when_to_update`: "feedback on which emails should be ignored"
- ✅ Match! → Update `triage-ignore`

**Result**:
```python
updated = [
    {
        "name": "triage-ignore",
        "prompt": "Marketing newsletters, spam emails, mass company announcements, emails from Alice Jones"
    },
    # ... others unchanged
]

updates_made = ["triage-ignore"]
```

---

## Key Takeaways

1. **Two-Phase Process**:
   - Phase 1: Classify which prompts need updating
   - Phase 2: Generate updated versions

2. **Intelligent Updates**:
   - Uses `when_to_update` criteria to decide relevance
   - Incorporates feedback naturally into prompts
   - Maintains prompt quality and formatting

3. **Selective Storage**:
   - Only stores prompts that actually changed
   - Efficient memory usage
   - Clear update tracking

4. **Persistent Changes**:
   - Updated prompts stored in procedural memory
   - Future emails automatically use new prompts
   - No code changes needed

This mechanism enables the agent to learn and adapt from user feedback automatically!

