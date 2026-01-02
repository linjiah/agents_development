# InMemoryStore Explained

## Overview

`InMemoryStore` is a **unified storage system** from LangGraph that provides both **key-value storage** and **vector similarity search** capabilities. It's the foundation for all three types of long-term memory in this email agent.

---

## What is InMemoryStore?

### Basic Definition

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)
```

**What it is**:
- A storage system that lives in memory (not persisted to disk)
- Provides both traditional key-value storage AND vector search
- Supports namespace-based organization
- Used by LangGraph agents for state and memory management

---

## The `index` Parameter Explained

### What Does `index={"embed": "openai:text-embedding-3-small"}` Mean?

```python
index={"embed": "openai:text-embedding-3-small"}
```

**Breakdown**:
- `"embed"`: The field name that will contain embeddings
- `"openai:text-embedding-3-small"`: The embedding model to use

**What it enables**:
- **Vector Embeddings**: Automatically creates embeddings for stored data
- **Semantic Search**: Enables similarity search using `store.search()`
- **Few-Shot Learning**: Allows finding similar examples

### How Embeddings Work

When you store data with an index:

```python
store.put(
    namespace,
    key,
    {"email": {...}, "label": "respond"}  # Data to store
)
```

**Behind the scenes**:
1. Store extracts the data
2. Creates embedding using `openai:text-embedding-3-small`
3. Stores both the data AND the embedding
4. Enables vector similarity search later

---

## Key Features

### 1. Key-Value Storage

**Basic Operations**:
```python
# Store data
store.put(namespace, key, value)

# Retrieve data
result = store.get(namespace, key)
data = result.value  # Access stored value

# Check if exists
result = store.get(namespace, key)
if result is None:
    # Key doesn't exist
```

**Example**:
```python
namespace = ("lance",)  # User-specific namespace
store.put(namespace, "agent_instructions", {"prompt": "..."})
result = store.get(namespace, "agent_instructions")
prompt = result.value['prompt']
```

### 2. Vector Similarity Search

**Search Operation**:
```python
# Search for similar items
results = store.search(
    namespace,
    query="text to search for",
    limit=5  # Top 5 results
)
```

**How it works**:
1. Creates embedding for the query text
2. Compares with stored embeddings
3. Returns most similar items

**Example**:
```python
namespace = ("email_assistant", "lance", "examples")
results = store.search(
    namespace,
    query=str({"email": email_input}),
    limit=3
)
# Returns 3 most similar email examples
```

### 3. Namespace Organization

**Structure**:
```python
namespace = (level1, level2, level3, ...)
```

**Examples in this agent**:
```python
# Procedural Memory (per-user prompts)
namespace = ("lance",)  # Single level: user ID

# Semantic Memory (email examples)
namespace = ("email_assistant", "lance", "examples")  # Three levels

# Episodic Memory (conversation history)
namespace = ("email_assistant", "lance", "collection")  # Three levels
```

**Benefits**:
- **Isolation**: Each user has separate memory space
- **Organization**: Different memory types in different namespaces
- **Scalability**: Easy to add more levels

---

## How It's Used in This Agent

### 1. Procedural Memory (Key-Value Storage)

**Storing prompts**:
```python
namespace = (user_id,)
store.put(namespace, "agent_instructions", {"prompt": "..."})
store.put(namespace, "triage_ignore", {"prompt": "..."})
```

**Retrieving prompts**:
```python
result = store.get(namespace, "agent_instructions")
prompt = result.value['prompt']
```

**No vector search needed** - just key-value lookups.

### 2. Semantic Memory (Vector Search)

**Storing email examples**:
```python
namespace = ("email_assistant", user_id, "examples")
store.put(
    namespace,
    "example_1",
    {
        "email": {
            "subject": "API question",
            "author": "alice@company.com",
            "to": "john@company.com",
            "email_thread": "..."
        },
        "label": "respond"
    }
)
```

**Searching for similar examples**:
```python
namespace = ("email_assistant", user_id, "examples")
examples = store.search(
    namespace,
    query=str({"email": state['email_input']}),
    limit=3
)
# Returns 3 most similar email examples for few-shot learning
```

**Vector search enables**:
- Finding similar emails for few-shot examples
- Improving triage classification accuracy
- Learning from past email patterns

### 3. Episodic Memory (Via Tools)

**Stored via tools** (not directly):
```python
# Created by langmem tools
manage_memory_tool = create_manage_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)

# Agent uses tool to store
manage_memory_tool.invoke({
    "content": "Alice prefers morning meetings",
    "metadata": {"contact": "alice@company.com"}
})
```

**Searched via tools**:
```python
search_memory_tool = create_search_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)

# Agent uses tool to search
results = search_memory_tool.invoke({
    "query": "What does Alice prefer?"
})
```

---

## Data Structure

### What Gets Stored

```python
# When you call:
store.put(namespace, "key", {"prompt": "Use tools..."})

# Internally stored as:
{
    "key": "key",
    "value": {"prompt": "Use tools..."},
    "embedding": [0.123, -0.456, ...],  # Vector embedding (if indexed)
    "namespace": ("lance",)
}
```

### Retrieval Result

```python
result = store.get(namespace, "key")
# Returns Item object:
# result.key = "key"
# result.value = {"prompt": "Use tools..."}
# result.namespace = ("lance",)
```

---

## Why Use InMemoryStore?

### Advantages

1. **Unified Interface**: One store for all memory types
2. **Vector Search**: Built-in semantic search capability
3. **Namespace Support**: Easy organization and isolation
4. **LangGraph Integration**: Works seamlessly with LangGraph
5. **Simple API**: Easy to use

### Limitations

1. **In-Memory Only**: Data lost when process ends (not persisted)
2. **Single Process**: Can't share across processes
3. **No Persistence**: Not suitable for production without persistence layer

### When to Use

✅ **Good for**:
- Development and testing
- Prototyping
- Learning and experimentation
- Single-process applications

❌ **Not ideal for**:
- Production systems (need persistence)
- Multi-process applications
- Large-scale deployments
- Data that must survive restarts

---

## Comparison with Other Storage Options

### InMemoryStore vs Database

| Feature | InMemoryStore | Database (e.g., PostgreSQL) |
|---------|---------------|----------------------------|
| **Persistence** | No (in-memory) | Yes (disk) |
| **Vector Search** | Built-in | Requires extension (pgvector) |
| **Speed** | Very fast | Slower (disk I/O) |
| **Scalability** | Limited (RAM) | High (disk) |
| **Complexity** | Simple | More complex |

### InMemoryStore vs Vector Database

| Feature | InMemoryStore | Vector DB (e.g., Pinecone) |
|---------|---------------|----------------------------|
| **Persistence** | No | Yes |
| **Scalability** | Limited | High |
| **Cost** | Free | Paid service |
| **Setup** | Simple | Requires account |
| **Use Case** | Development | Production |

---

## Code Examples

### Example 1: Basic Key-Value Storage

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# Store
namespace = ("user1",)
store.put(namespace, "name", {"value": "John Doe"})

# Retrieve
result = store.get(namespace, "name")
print(result.value['value'])  # "John Doe"
```

### Example 2: Vector Search

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)

# Store items
namespace = ("examples",)
store.put(namespace, "doc1", {"text": "Python programming tutorial"})
store.put(namespace, "doc2", {"text": "Machine learning basics"})
store.put(namespace, "doc3", {"text": "Data science guide"})

# Search for similar
results = store.search(namespace, query="How to learn Python?", limit=2)
# Returns doc1 and doc3 (most similar)
```

### Example 3: Multi-Level Namespace

```python
# User-specific, type-specific organization
user_id = "lance"
memory_type = "examples"

namespace = ("email_assistant", user_id, memory_type)

store.put(
    namespace,
    "example_1",
    {"email": {...}, "label": "respond"}
)

# Each user has isolated memory
namespace_user2 = ("email_assistant", "user2", memory_type)
# Separate storage for user2
```

---

## Integration with LangGraph

### How LangGraph Uses It

```python
# Create graph with store
email_agent = StateGraph(State)
email_agent = email_agent.add_node("triage_router", triage_router)
email_agent = email_agent.compile(store=store)  # ← Store passed here

# Store is available in nodes
def triage_router(state: State, config, store):
    # store is automatically passed by LangGraph
    result = store.get(namespace, "triage_ignore")
    # ...
```

**Key Points**:
- Store passed to `compile(store=store)`
- Automatically available in node functions
- Shared across all nodes in the graph

---

## The Embedding Model: `openai:text-embedding-3-small`

### What It Is

- **Model**: OpenAI's text-embedding-3-small
- **Purpose**: Converts text to numerical vectors
- **Size**: 1536 dimensions
- **Cost**: Lower cost than larger models
- **Quality**: Good balance of quality and cost

### How It Works

```python
# Text input
text = "API documentation question"

# Embedding (simplified)
embedding = embed_model.encode(text)
# Returns: [0.123, -0.456, 0.789, ...]  # 1536 numbers

# Similarity calculation
similarity = cosine_similarity(embedding1, embedding2)
# Higher similarity = more similar text
```

### Why This Model?

- **Cost-Effective**: Cheaper than larger models
- **Good Quality**: Sufficient for semantic search
- **Fast**: Quick embedding generation
- **Standard**: Commonly used in production

---

## Memory Lifecycle

### 1. Initialization

```python
store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)
# Store is empty, ready to use
```

### 2. First Use (Lazy Initialization)

```python
# Agent tries to retrieve
result = store.get(namespace, "agent_instructions")

if result is None:
    # First time - initialize with default
    store.put(namespace, "agent_instructions", default_prompt)
    prompt = default_prompt
else:
    # Already exists - use stored version
    prompt = result.value['prompt']
```

### 3. Updates

```python
# Optimizer updates prompt
updated_prompt = "Use tools... Always sign emails with 'John Doe'."
store.put(namespace, "agent_instructions", {"prompt": updated_prompt})
```

### 4. Retrieval

```python
# Agent retrieves on next execution
result = store.get(namespace, "agent_instructions")
prompt = result.value['prompt']  # Now includes update
```

---

## Summary

### What InMemoryStore Is

- **Unified storage** for key-value and vector search
- **In-memory** (not persisted)
- **Namespace-based** organization
- **LangGraph integration** built-in

### What the `index` Parameter Does

- **Enables vector embeddings** for stored data
- **Allows semantic search** via `store.search()`
- **Uses OpenAI embedding model** for vectorization

### How It's Used in This Agent

1. **Procedural Memory**: Key-value storage for prompts
2. **Semantic Memory**: Vector search for email examples
3. **Episodic Memory**: Storage via langmem tools

### Key Takeaway

`InMemoryStore` is the **foundation** that enables all three types of long-term memory in this agent, providing both simple key-value storage and advanced vector similarity search in a single, unified interface.

