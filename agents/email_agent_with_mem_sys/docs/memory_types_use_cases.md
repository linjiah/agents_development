# Three Types of Long-Term Memory: Use Cases and Examples

## Overview

The email agent uses three distinct types of long-term memory, each serving a specific purpose in improving the agent's performance and adaptability.

---

## 1. Semantic Memory - Few-Shot Examples

### Purpose
Store and retrieve similar email examples to improve triage classification accuracy through few-shot learning.

### Use Case
When a new email arrives, the agent searches for similar past emails and their classifications to guide the current classification decision.

### Storage Location
```python
namespace = ("email_assistant", user_id, "examples")
```

### How It Works
1. **Store**: Save email examples with their classification labels
2. **Search**: Use vector similarity to find similar emails
3. **Use**: Include similar examples in the triage prompt as few-shot learning

### Example Content

#### Stored Example 1:
```python
{
    "email": {
        "subject": "API documentation missing endpoints",
        "author": "Alice Smith <alice.smith@company.com>",
        "to": "John Doe <john.doe@company.com>",
        "email_thread": "Hi John, I noticed some endpoints are missing from the API docs. Can you help?"
    },
    "label": "respond"  # Classification result
}
```

#### Stored Example 2:
```python
{
    "email": {
        "subject": "🔥 EXCLUSIVE OFFER: Limited Time Discount!",
        "author": "Marketing Team <marketing@amazingdeals.com>",
        "to": "John Doe <john.doe@company.com>",
        "email_thread": "Don't miss out on this INCREDIBLE opportunity! 80% OFF..."
    },
    "label": "ignore"  # Classification result
}
```

#### Stored Example 3:
```python
{
    "email": {
        "subject": "Build system notification: Deployment successful",
        "author": "CI/CD System <ci@company.com>",
        "to": "John Doe <john.doe@company.com>",
        "email_thread": "Deployment to production completed successfully at 2:30 PM."
    },
    "label": "notify"  # Classification result
}
```

### How It's Used

When a new email arrives:
```python
# Search for similar emails
examples = store.search(
    ("email_assistant", user_id, "examples"),
    query=str({"email": new_email})
)

# Format into few-shot examples
formatted = format_few_shot_examples(examples)

# Include in prompt
prompt = f"""
Here are some examples of previous emails:
{formatted}

Now classify this new email: {new_email}
"""
```

### Real-World Example

**Scenario**: New email arrives about "missing API documentation"

**Semantic Memory Retrieval**:
- Finds Example 1 (similar topic: "API documentation missing endpoints")
- Classification was "respond"
- Agent uses this to guide classification: "This is similar to a past email that needed a response"

**Result**: More accurate classification based on similar past cases

---

## 2. Episodic Memory - Conversation History

### Purpose
Remember details from previous email interactions, contacts, preferences, and conversations to provide context-aware responses.

### Use Case
The agent remembers:
- Past conversations with specific contacts
- Contact preferences and details
- Important information mentioned in previous emails
- User-specific context and history

### Storage Location
```python
namespace = ("email_assistant", user_id, "collection")
```

### How It Works
1. **Store**: Agent automatically stores relevant information during email processing
2. **Search**: Agent searches for relevant context before responding
3. **Use**: Context is used to personalize and improve responses

### Example Content

#### Contact Information:
```python
{
    "content": "Alice Smith works on the API team. She prefers formal communication style. Last discussed: API documentation issues on 2024-01-15.",
    "metadata": {
        "contact": "Alice Smith",
        "email": "alice.smith@company.com",
        "team": "API",
        "preference": "formal"
    }
}
```

#### Previous Conversation Context:
```python
{
    "content": "Discussed missing /auth/refresh and /auth/validate endpoints. John promised to update documentation by tomorrow.",
    "metadata": {
        "date": "2024-01-15",
        "topic": "API documentation",
        "action_items": ["Update docs with missing endpoints"]
    }
}
```

#### User Preferences:
```python
{
    "content": "John prefers meetings scheduled in the afternoon. He's usually available 2-4 PM on weekdays.",
    "metadata": {
        "type": "preference",
        "category": "scheduling"
    }
}
```

#### Project Context:
```python
{
    "content": "Current project: Authentication service v2. Team members: Alice (API), Bob (Backend), Carol (Frontend). Deadline: 2024-02-01.",
    "metadata": {
        "project": "Auth Service v2",
        "team": ["Alice", "Bob", "Carol"]
    }
}
```

### How It's Used

**During Email Processing**:
```python
# Agent automatically searches for context
search_memory(
    "email_assistant",
    user_id,
    "collection",
    query="Alice Smith previous conversations"
)

# Returns: Past interactions, preferences, context

# Agent uses this to craft personalized response:
# "Hi Alice, following up on our previous discussion about the API docs..."
```

**After Email Processing**:
```python
# Agent stores new information
manage_memory(
    "email_assistant",
    user_id,
    "collection",
    content="Alice mentioned she's working on a new feature. Will need API support next week."
)
```

### Real-World Example

**Scenario**: Email from Alice asking about API endpoints

**Episodic Memory Search**:
- Finds: "Alice prefers formal communication"
- Finds: "Previous discussion about missing endpoints"
- Finds: "John promised to update docs by tomorrow"

**Agent Response**:
```
"Dear Alice,

Thank you for your inquiry. As we discussed previously, I'm working on updating 
the documentation to include the missing endpoints. I'll have this completed 
by tomorrow as promised.

Best regards,
John Doe"
```

**After Response**:
- Stores: "Responded to Alice about API docs. She confirmed the endpoints are needed."

---

## 3. Procedural Memory - Dynamic Prompts

### Purpose
Store and update agent instructions and triage rules based on user feedback, allowing the agent to learn and adapt.

### Use Case
When the user provides feedback on agent behavior, the system updates the stored prompts to incorporate the feedback for future interactions.

### Storage Location
```python
namespace = (user_id,)  # Simple namespace for user-specific prompts
```

### Example Content

#### Agent Instructions:
```python
# Initial (default)
{
    "prompt": "Use these tools when appropriate to help manage John's tasks efficiently."
}

# After feedback: "Always sign your emails `John Doe`"
{
    "prompt": "Use these tools when appropriate to help manage John's tasks efficiently. Always sign emails with 'John Doe'."
}

# After more feedback: "Be more concise in responses"
{
    "prompt": "Use these tools when appropriate to help manage John's tasks efficiently. Always sign emails with 'John Doe'. Keep responses concise and to the point."
}
```

#### Triage Ignore Rules:
```python
# Initial (default)
{
    "prompt": "Marketing newsletters, spam emails, mass company announcements"
}

# After feedback: "Ignore any emails from Alice Jones"
{
    "prompt": "Marketing newsletters, spam emails, mass company announcements, emails from Alice Jones"
}

# After more feedback: "Also ignore emails about company events"
{
    "prompt": "Marketing newsletters, spam emails, mass company announcements, emails from Alice Jones, company event announcements"
}
```

#### Triage Notify Rules:
```python
# Initial (default)
{
    "prompt": "Team member out sick, build system notifications, project status updates"
}

# After feedback: "Also notify about security alerts"
{
    "prompt": "Team member out sick, build system notifications, project status updates, security alerts"
}
```

#### Triage Respond Rules:
```python
# Initial (default)
{
    "prompt": "Direct questions from team members, meeting requests, critical bug reports"
}

# After feedback: "Always respond to emails from the CEO"
{
    "prompt": "Direct questions from team members, meeting requests, critical bug reports, emails from CEO"
}
```

### How It's Used

**Initialization** (First time):
```python
# Store default prompts
store.put((user_id,), "agent_instructions", {
    "prompt": "Use these tools when appropriate..."
})
```

**Retrieval** (Every email):
```python
# Get current instructions
result = store.get((user_id,), "agent_instructions")
instructions = result.value['prompt']

# Use in agent prompt
prompt = f"""
You are John's assistant.
Instructions: {instructions}
"""
```

**Update** (After feedback):
```python
# User provides feedback
feedback = "Always sign your emails `John Doe`"

# Optimizer analyzes and updates
updated = optimizer.invoke({
    "trajectories": [(conversation, feedback)],
    "prompts": [current_prompts]
})

# Store updated prompt
store.put((user_id,), "agent_instructions", {
    "prompt": updated['prompt']
})

# Next email automatically uses new instructions
```

### Real-World Example

**Scenario 1: Email Signature Feedback**

**Before**:
- Agent responds without signature
- User feedback: "Always sign your emails `John Doe`"
- Optimizer updates `agent_instructions` prompt
- New prompt: "... Always sign emails with 'John Doe'."

**After**:
- All future emails automatically include: "Best regards, John Doe"

**Scenario 2: Ignore Specific Sender**

**Before**:
- Email from Alice Jones → Classified as "respond"
- User feedback: "Ignore any emails from Alice Jones"
- Optimizer updates `triage_ignore` prompt
- New prompt: "... emails from Alice Jones"

**After**:
- Next email from Alice Jones → Automatically classified as "ignore"

**Scenario 3: Response Style**

**Before**:
- Agent writes long, detailed responses
- User feedback: "Be more concise in responses"
- Optimizer updates `agent_instructions` prompt
- New prompt: "... Keep responses concise and to the point."

**After**:
- All future responses are shorter and more direct

---

## Comparison Table

| Memory Type | What It Stores | When It's Used | Update Method | Example |
|------------|---------------|----------------|---------------|---------|
| **Semantic** | Email examples with classifications | During triage classification | Manual storage of examples | Similar past emails for few-shot learning |
| **Episodic** | Conversation history, contacts, context | During email processing | Automatic (agent tools) | "Alice prefers formal communication" |
| **Procedural** | Agent instructions, triage rules | Every email (prompt generation) | Feedback-driven (optimizer) | "Always sign emails with 'John Doe'" |

---

## Complete Workflow Example

### Email Processing with All Three Memories

**1. New Email Arrives**:
```
From: Alice Smith
Subject: Quick question about API documentation
Content: "Hi John, can you help with the missing endpoints?"
```

**2. Semantic Memory** (Few-Shot Examples):
```python
# Search for similar emails
similar_emails = store.search(
    ("email_assistant", user_id, "examples"),
    query="API documentation question"
)

# Found: Previous email about "API documentation missing endpoints" → classified as "respond"
# Result: Include this example in triage prompt
```

**3. Procedural Memory** (Triage Rules):
```python
# Get current triage rules
ignore_rule = store.get((user_id,), "triage_ignore").value['prompt']
# "Marketing newsletters, spam, emails from Alice Jones"  # Updated from feedback!

respond_rule = store.get((user_id,), "triage_respond").value['prompt']
# "Direct questions from team members, meeting requests..."
```

**4. Triage Classification**:
- Uses semantic memory examples
- Uses procedural memory rules
- Classifies: "respond" (similar to past example + matches respond rule)

**5. Episodic Memory** (Context Retrieval):
```python
# Search for Alice's context
alice_context = search_memory(
    "email_assistant", user_id, "collection",
    query="Alice Smith previous conversations"
)

# Found: 
# - "Alice prefers formal communication"
# - "Last discussed API docs on 2024-01-15"
# - "She's on the API team"
```

**6. Procedural Memory** (Agent Instructions):
```python
# Get current instructions
instructions = store.get((user_id,), "agent_instructions").value['prompt']
# "Use tools efficiently. Always sign emails with 'John Doe'. Keep responses concise."
```

**7. Response Generation**:
- Uses episodic memory: "Dear Alice" (formal, as preferred)
- Uses procedural memory: Includes signature "John Doe"
- Uses procedural memory: Keeps response concise
- References past conversation: "Following up on our previous discussion..."

**8. Store New Information** (Episodic Memory):
```python
# After response, store new context
manage_memory(
    "email_assistant", user_id, "collection",
    content="Responded to Alice about API docs. She confirmed endpoints are needed."
)
```

---

## Key Takeaways

1. **Semantic Memory**: "What similar emails looked like and how they were classified"
   - Example: Past email about "API docs" → classified as "respond"

2. **Episodic Memory**: "What happened in past conversations and who said what"
   - Example: "Alice prefers formal communication" or "Last discussed API docs yesterday"

3. **Procedural Memory**: "How should I behave based on user feedback"
   - Example: "Always sign emails with 'John Doe'" or "Ignore emails from Alice Jones"

Together, these three memory types create an agent that:
- Learns from similar past cases (Semantic)
- Remembers conversation context (Episodic)
- Adapts behavior from feedback (Procedural)

