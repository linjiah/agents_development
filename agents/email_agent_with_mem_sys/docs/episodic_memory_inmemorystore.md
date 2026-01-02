# Episodic Memory with InMemoryStore: Deep Dive

## Overview

This document explains how episodic memory works with `InMemoryStore` in the email agent. Episodic memory stores conversation history, contact information, and preferences that the agent can recall later.

---

## Part 1: Architecture Overview

### How Episodic Memory Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Execution                           │
│                                                               │
│  Agent processes email                                       │
│    ↓                                                          │
│  Agent decides to store/retrieve information                │
│    ↓                                                          │
│  Agent calls tool: manage_memory_tool or search_memory_tool  │
│    ↓                                                          │
│  Tool interacts with InMemoryStore                           │
│    ↓                                                          │
│  Data stored/retrieved from store                            │
│    ↓                                                          │
│  Agent uses information in response                         │
└─────────────────────────────────────────────────────────────┘
```

**Key Point**: The agent doesn't directly access `InMemoryStore`. Instead, it uses **tools** (`manage_memory_tool` and `search_memory_tool`) that handle the store interactions.

---

## Part 2: Tool Creation

### 2.1 Store Tool Setup

```python
from langmem import create_manage_memory_tool, create_search_memory_tool

# ========== EPISODIC MEMORY: CREATE/STORE Tool ==========
manage_memory_tool = create_manage_memory_tool(
    namespace=(
        "email_assistant", 
        "{langgraph_user_id}",
        "collection"
    )
)

# ========== EPISODIC MEMORY: RETRIEVE/SEARCH Tool ==========
search_memory_tool = create_search_memory_tool(
    namespace=(
        "email_assistant",
        "{langgraph_user_id}",
        "collection"
    )
)
```

**What These Tools Do**:
- `create_manage_memory_tool`: Creates a tool for **storing** memories
- `create_search_memory_tool`: Creates a tool for **searching** memories
- Both tools are configured with the same namespace

### 2.2 Namespace Structure

```python
namespace = (
    "email_assistant",      # Level 1: Application identifier
    "{langgraph_user_id}", # Level 2: User ID (dynamic, e.g., "lance")
    "collection"            # Level 3: Memory type (episodic memories)
)
```

**Namespace Breakdown**:
- **Level 1**: `"email_assistant"` - Identifies this as email assistant memories
- **Level 2**: `"{langgraph_user_id}"` - User-specific (replaced at runtime)
- **Level 3**: `"collection"` - Type of memory (episodic/collection)

**At Runtime**:
```python
# If user_id = "lance"
actual_namespace = ("email_assistant", "lance", "collection")
```

**Why This Structure?**:
- **Isolation**: Each user has separate memory space
- **Organization**: Different memory types in different namespaces
- **Scalability**: Easy to add more levels or types

---

## Part 3: Tool Integration with Agent

### 3.1 Adding Tools to Agent

```python
tools = [
    write_email, 
    schedule_meeting,
    check_calendar_availability,
    manage_memory_tool,  # ← Episodic memory: STORE
    search_memory_tool   # ← Episodic memory: SEARCH
]

response_agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
    store=store  # ← Store passed to agent
)
```

**Key Points**:
- Tools are added to agent's tool list
- Agent can call these tools during execution
- Store is passed to agent (tools use it internally)

### 3.2 Agent Prompt Mentions Tools

```python
agent_system_prompt_memory = """
< Tools >
...
4. manage_memory - Store any relevant information about contacts, actions, discussion, etc. in memory for future reference
5. search_memory - Search for any relevant information that may have been stored in memory
</ Tools >
"""
```

**What This Does**:
- Tells agent these tools exist
- Explains when to use them
- Agent decides autonomously when to store/retrieve

---

## Part 4: How Tools Interact with InMemoryStore

### 4.1 Store Tool (`manage_memory_tool`)

**What It Does**:
- Agent calls tool with content to store
- Tool stores data in `InMemoryStore`
- Uses vector embeddings for semantic search

**Internal Process** (simplified):

```python
# When agent calls: manage_memory_tool.invoke({"content": "...", "metadata": {...}})

def manage_memory_tool_internal(content, metadata, store, config):
    # 1. Resolve namespace
    user_id = config['configurable']['langgraph_user_id']
    namespace = ("email_assistant", user_id, "collection")
    
    # 2. Generate unique key (or use provided)
    key = generate_unique_key()  # e.g., "memory_2024_01_15_123456"
    
    # 3. Prepare data
    value = {
        "content": content,
        "metadata": metadata,
        "timestamp": datetime.now()
    }
    
    # 4. Store in InMemoryStore
    store.put(namespace, key, value)
    
    # Note: Because store has index={"embed": "openai:text-embedding-3-small"},
    # the content is automatically embedded for vector search
    
    return f"Stored memory: {key}"
```

**What Gets Stored**:
```python
{
    "content": "Alice prefers morning meetings",
    "metadata": {"contact": "alice@company.com", "type": "preference"},
    "timestamp": "2024-01-15T10:30:00"
}
```

**Storage Details**:
- **Key**: Auto-generated unique identifier
- **Value**: Content + metadata + timestamp
- **Embedding**: Automatically created from content (for search)

### 4.2 Search Tool (`search_memory_tool`)

**What It Does**:
- Agent calls tool with search query
- Tool searches `InMemoryStore` using vector similarity
- Returns most relevant memories

**Internal Process** (simplified):

```python
# When agent calls: search_memory_tool.invoke({"query": "What does Alice prefer?"})

def search_memory_tool_internal(query, store, config, limit=5):
    # 1. Resolve namespace
    user_id = config['configurable']['langgraph_user_id']
    namespace = ("email_assistant", user_id, "collection")
    
    # 2. Vector similarity search
    results = store.search(
        namespace,
        query=query,  # Search query
        limit=limit   # Top N results
    )
    
    # 3. Format results
    formatted = []
    for result in results:
        formatted.append({
            "content": result.value['content'],
            "metadata": result.value['metadata'],
            "timestamp": result.value['timestamp']
        })
    
    return formatted
```

**How Vector Search Works**:
1. Query text is embedded: `"What does Alice prefer?"` → `[0.123, -0.456, ...]`
2. Stored memories have embeddings: `"Alice prefers morning meetings"` → `[0.234, -0.345, ...]`
3. Cosine similarity calculated between query and all stored memories
4. Top N most similar memories returned

---

## Part 5: Complete Data Flow

### 5.1 Storing a Memory

```
Step 1: Agent Processing Email
───────────────────────────────
Agent receives email from Alice:
"Can we schedule a meeting? I prefer mornings."

Step 2: Agent Decision
──────────────────────
Agent thinks: "This is important information about Alice's preference.
I should store this for future reference."

Step 3: Agent Calls Tool
────────────────────────
Agent calls: manage_memory_tool.invoke({
    "content": "Alice prefers morning meetings",
    "metadata": {
        "contact": "alice@company.com",
        "type": "preference",
        "source": "email"
    }
})

Step 4: Tool Processes
───────────────────────
manage_memory_tool:
  1. Resolves namespace: ("email_assistant", "lance", "collection")
  2. Generates key: "memory_2024_01_15_123456"
  3. Creates embedding from content
  4. Stores in InMemoryStore:
     store.put(
         ("email_assistant", "lance", "collection"),
         "memory_2024_01_15_123456",
         {
             "content": "Alice prefers morning meetings",
             "metadata": {...},
             "timestamp": "2024-01-15T10:30:00"
         }
     )

Step 5: Tool Response
─────────────────────
Returns: "Stored memory: memory_2024_01_15_123456"

Step 6: Agent Continues
────────────────────────
Agent uses this information to schedule meeting in morning
```

### 5.2 Retrieving a Memory

```
Step 1: Agent Processing New Email
──────────────────────────────────
Agent receives email from Alice:
"Can we schedule another meeting?"

Step 2: Agent Decision
──────────────────────
Agent thinks: "I should check if I know anything about Alice's preferences."

Step 3: Agent Calls Tool
────────────────────────
Agent calls: search_memory_tool.invoke({
    "query": "What are Alice's meeting preferences?"
})

Step 4: Tool Processes
──────────────────────
search_memory_tool:
  1. Resolves namespace: ("email_assistant", "lance", "collection")
  2. Creates embedding from query: "What are Alice's meeting preferences?"
  3. Searches store:
     results = store.search(
         ("email_assistant", "lance", "collection"),
         query="What are Alice's meeting preferences?",
         limit=3
     )
  4. Finds: "Alice prefers morning meetings" (high similarity)
  5. Returns formatted results

Step 5: Tool Response
─────────────────────
Returns: [
    {
        "content": "Alice prefers morning meetings",
        "metadata": {"contact": "alice@company.com", ...},
        "timestamp": "2024-01-15T10:30:00"
    }
]

Step 6: Agent Uses Information
──────────────────────────────
Agent schedules meeting in morning, referencing stored preference
```

---

## Part 6: What Gets Stored

### 6.1 Types of Episodic Memories

**1. Contact Information**:
```python
manage_memory_tool.invoke({
    "content": "Alice Smith is the lead designer on the UX team",
    "metadata": {
        "contact": "alice@company.com",
        "type": "contact_info",
        "role": "lead designer"
    }
})
```

**2. Preferences**:
```python
manage_memory_tool.invoke({
    "content": "Alice prefers morning meetings and async communication",
    "metadata": {
        "contact": "alice@company.com",
        "type": "preference"
    }
})
```

**3. Past Conversations**:
```python
manage_memory_tool.invoke({
    "content": "Discussed API documentation issues. Alice mentioned missing endpoints: /auth/refresh, /auth/validate",
    "metadata": {
        "contact": "alice@company.com",
        "type": "conversation",
        "topic": "API documentation"
    }
})
```

**4. Important Details**:
```python
manage_memory_tool.invoke({
    "content": "Alice is working on authentication service redesign, deadline is end of month",
    "metadata": {
        "contact": "alice@company.com",
        "type": "project_info",
        "deadline": "2024-01-31"
    }
})
```

### 6.2 Storage Structure in InMemoryStore

**What's Actually Stored**:
```python
# In InMemoryStore:
namespace = ("email_assistant", "lance", "collection")
key = "memory_2024_01_15_123456"
value = {
    "content": "Alice prefers morning meetings",
    "metadata": {
        "contact": "alice@company.com",
        "type": "preference",
        "source": "email"
    },
    "timestamp": "2024-01-15T10:30:00"
}

# Plus automatically:
embedding = [0.123, -0.456, 0.789, ...]  # Vector embedding of content
```

---

## Part 7: Search Mechanism

### 7.1 Vector Similarity Search

**How It Works**:

```python
# 1. Query embedding
query = "What does Alice prefer?"
query_embedding = embed_model.encode(query)
# Result: [0.123, -0.456, 0.789, ...] (1536 dimensions)

# 2. Stored memory embeddings
memory_1_embedding = [0.234, -0.345, 0.567, ...]  # "Alice prefers morning meetings"
memory_2_embedding = [0.111, -0.222, 0.333, ...]  # "Bob likes afternoon meetings"
memory_3_embedding = [0.999, -0.888, 0.777, ...]  # "Project deadline is end of month"

# 3. Similarity calculation
similarity_1 = cosine_similarity(query_embedding, memory_1_embedding)  # 0.85 (high!)
similarity_2 = cosine_similarity(query_embedding, memory_2_embedding)  # 0.45 (low)
similarity_3 = cosine_similarity(query_embedding, memory_3_embedding)  # 0.12 (very low)

# 4. Results sorted by similarity
results = [
    (memory_1, similarity_1),  # Most relevant
    (memory_2, similarity_2),
    (memory_3, similarity_3)
]
```

**Key Points**:
- **Semantic Search**: Finds memories by meaning, not exact text match
- **Cosine Similarity**: Measures angle between vectors (0-1, higher = more similar)
- **Top-K Results**: Returns most similar memories

### 7.2 Example Searches

**Query**: `"What does Alice prefer?"`
**Finds**:
- ✅ "Alice prefers morning meetings" (high similarity)
- ✅ "Alice likes async communication" (medium similarity)
- ❌ "Bob prefers afternoon meetings" (low similarity - different person)

**Query**: `"When is the project deadline?"`
**Finds**:
- ✅ "Project deadline is end of month" (high similarity)
- ✅ "Alice is working on authentication service redesign, deadline is end of month" (high similarity)
- ❌ "Alice prefers morning meetings" (low similarity - different topic)

---

## Part 8: Integration with LangGraph Store

### 8.1 Store Passing

```python
# Store created
store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)

# Store passed to agent
response_agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
    store=store  # ← Store passed here
)

# Store passed to graph
email_agent = StateGraph(State)
email_agent = email_agent.compile(store=store)  # ← Store passed here
```

**Why This Matters**:
- Tools need access to store
- Store is shared across all nodes
- Tools can access store through LangGraph context

### 8.2 Tool Access to Store

**How Tools Get Store**:
```python
# Tools created by langmem automatically:
# 1. Receive store from LangGraph context
# 2. Use store for put/get/search operations
# 3. Handle namespace resolution automatically

# When agent calls tool:
manage_memory_tool.invoke({
    "content": "...",
    "metadata": {...}
})

# Tool internally:
# - Gets store from LangGraph context
# - Resolves namespace using config
# - Calls store.put() or store.search()
```

---

## Part 9: Real-World Example

### Complete Flow: Storing and Retrieving

```python
# ============================================================
# Scenario: Agent learns about Alice's preferences
# ============================================================

# Email 1: Alice sends email
email_1 = {
    "author": "alice@company.com",
    "subject": "Meeting request",
    "email_thread": "Can we schedule a meeting? I prefer mornings."
}

# Agent processes email
response_1 = email_agent.invoke(
    {"email_input": email_1},
    config={"configurable": {"langgraph_user_id": "lance"}}
)

# During processing, agent calls:
manage_memory_tool.invoke({
    "content": "Alice prefers morning meetings",
    "metadata": {
        "contact": "alice@company.com",
        "type": "preference"
    }
})

# Memory stored in:
# namespace = ("email_assistant", "lance", "collection")
# key = "memory_2024_01_15_123456"
# value = {"content": "Alice prefers morning meetings", ...}

# ============================================================
# Later: Agent receives another email from Alice
# ============================================================

# Email 2: Alice sends another email
email_2 = {
    "author": "alice@company.com",
    "subject": "Another meeting",
    "email_thread": "Can we schedule another meeting?"
}

# Agent processes email
response_2 = email_agent.invoke(
    {"email_input": email_2},
    config={"configurable": {"langgraph_user_id": "lance"}}
)

# During processing, agent calls:
search_memory_tool.invoke({
    "query": "What are Alice's meeting preferences?"
})

# Tool searches and finds:
# "Alice prefers morning meetings" (high similarity)

# Agent uses this information:
# - Schedules meeting in morning
# - References stored preference in response
```

---

## Part 10: Key Differences from Other Memory Types

### Episodic vs Semantic Memory

| Aspect | Episodic Memory | Semantic Memory |
|--------|----------------|-----------------|
| **Storage** | Via tools (manage_memory_tool) | Direct (store.put) |
| **Search** | Via tools (search_memory_tool) | Direct (store.search) |
| **Content** | Conversations, contacts, preferences | Email examples with labels |
| **Namespace** | `("email_assistant", user_id, "collection")` | `("email_assistant", user_id, "examples")` |
| **Use Case** | Remember past interactions | Few-shot learning |

### Episodic vs Procedural Memory

| Aspect | Episodic Memory | Procedural Memory |
|--------|----------------|-------------------|
| **Storage** | Via tools | Direct (store.put) |
| **Content** | Dynamic (agent decides) | Fixed (prompts) |
| **Namespace** | `("email_assistant", user_id, "collection")` | `(user_id,)` |
| **Use Case** | Remember facts | Store instructions |

---

## Part 11: Advantages and Limitations

### Advantages

1. **Agent-Driven**: Agent decides what to store/retrieve
2. **Semantic Search**: Finds memories by meaning
3. **Automatic Embeddings**: No manual embedding creation
4. **User Isolation**: Each user has separate memory space
5. **Flexible**: Can store any type of information

### Limitations

1. **In-Memory Only**: Data lost when process ends
2. **No Persistence**: Not suitable for production without persistence
3. **Tool Dependency**: Requires agent to call tools (not automatic)
4. **Cost**: Embedding generation costs (API calls)

---

## Part 12: Summary

### How Episodic Memory Works with InMemoryStore

1. **Tools Created**: `create_manage_memory_tool` and `create_search_memory_tool`
2. **Tools Added to Agent**: Agent can call these tools during execution
3. **Store Interaction**: Tools interact with `InMemoryStore` internally
4. **Storage**: Data stored with embeddings for semantic search
5. **Retrieval**: Vector similarity search finds relevant memories
6. **Namespace**: `("email_assistant", user_id, "collection")` organizes memories

### Key Points

- **Indirect Access**: Agent uses tools, not direct store access
- **Vector Search**: Semantic search enabled by embeddings
- **User Isolation**: Namespace ensures per-user memory
- **Automatic**: Embeddings created automatically by store

### Data Flow

```
Agent → Tool → InMemoryStore → Embeddings → Vector Search → Results → Agent
```

---

This document provides a complete understanding of how episodic memory integrates with InMemoryStore through the langmem tools.

