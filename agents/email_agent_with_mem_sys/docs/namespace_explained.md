# Namespace Usage in Memory Types: Complete Guide

## Overview

This document explains how namespaces are used to organize and isolate different types of memories in the email agent. Namespaces act like "folders" or "directories" in the storage system.

---

## Part 1: What is a Namespace?

### Basic Concept

A **namespace** is a tuple (ordered sequence) that acts like a path to organize data in the store:

```python
namespace = (level1, level2, level3, ...)
```

**Think of it like**:
- File system paths: `/home/user/documents/`
- Database schemas: `database.schema.table`
- Python packages: `package.module.function`

### Key Properties

1. **Hierarchical**: Multiple levels create a tree structure
2. **Isolation**: Different namespaces = separate data spaces
3. **Organization**: Groups related data together
4. **Scalable**: Easy to add more levels

---

## Part 2: Namespace Structure for Each Memory Type

### 2.1 Semantic Memory Namespace

**Code**:
```python
namespace = (
    "email_assistant",
    config['configurable']['langgraph_user_id'],
    "examples"
)
```

**Structure**:
```
email_assistant/
  └── lance/          (user_id)
      └── examples/    (memory type)
          ├── example_1
          ├── example_2
          └── example_3
```

**Example at Runtime**:
```python
# If user_id = "lance"
namespace = ("email_assistant", "lance", "examples")

# Stored items:
store.put(namespace, "example_1", {"email": {...}, "label": "respond"})
store.put(namespace, "example_2", {"email": {...}, "label": "ignore"})
```

**Why This Structure?**:
- **Level 1**: `"email_assistant"` - Identifies this application
- **Level 2**: `"lance"` - User-specific isolation
- **Level 3**: `"examples"` - Type of memory (semantic/few-shot)

### 2.2 Episodic Memory Namespace

**Code**:
```python
namespace = (
    "email_assistant",
    "{langgraph_user_id}",
    "collection"
)
```

**Structure**:
```
email_assistant/
  └── lance/          (user_id)
      └── collection/ (memory type)
          ├── memory_2024_01_15_123456
          ├── memory_2024_01_15_234567
          └── memory_2024_01_16_345678
```

**Example at Runtime**:
```python
# If user_id = "lance"
namespace = ("email_assistant", "lance", "collection")

# Stored items (via tools):
manage_memory_tool.invoke({
    "content": "Alice prefers morning meetings",
    "metadata": {...}
})
# Stores at: ("email_assistant", "lance", "collection") / "memory_xxx"
```

**Why This Structure?**:
- **Level 1**: `"email_assistant"` - Application identifier
- **Level 2**: `"lance"` - User-specific isolation
- **Level 3**: `"collection"` - Type of memory (episodic/conversations)

### 2.3 Procedural Memory Namespace

**Code**:
```python
namespace = (langgraph_user_id,)
```

**Structure**:
```
lance/                (user_id only)
  ├── agent_instructions
  ├── triage_ignore
  ├── triage_notify
  └── triage_respond
```

**Example at Runtime**:
```python
# If user_id = "lance"
namespace = ("lance",)

# Stored items:
store.put(namespace, "agent_instructions", {"prompt": "..."})
store.put(namespace, "triage_ignore", {"prompt": "..."})
store.put(namespace, "triage_notify", {"prompt": "..."})
store.put(namespace, "triage_respond", {"prompt": "..."})
```

**Why This Structure?**:
- **Level 1**: `"lance"` - User-specific only (simpler structure)
- **No application prefix**: Prompts are user-specific, not app-specific
- **Flat structure**: All prompts at same level

---

## Part 3: Visual Comparison

### Complete Namespace Tree

```
InMemoryStore
│
├── email_assistant/              (Application namespace)
│   │
│   ├── lance/                    (User namespace)
│   │   │
│   │   ├── examples/             (Semantic Memory)
│   │   │   ├── example_1
│   │   │   ├── example_2
│   │   │   └── example_3
│   │   │
│   │   └── collection/           (Episodic Memory)
│   │       ├── memory_2024_01_15_123456
│   │       ├── memory_2024_01_15_234567
│   │       └── memory_2024_01_16_345678
│   │
│   └── user2/                    (Another user)
│       ├── examples/
│       └── collection/
│
└── lance/                        (Procedural Memory - separate tree)
    ├── agent_instructions
    ├── triage_ignore
    ├── triage_notify
    └── triage_respond
```

---

## Part 4: Why Different Structures?

### 4.1 Semantic Memory: 3 Levels

```python
namespace = ("email_assistant", user_id, "examples")
```

**Reasoning**:
- **Application-level**: `"email_assistant"` - Could have multiple apps
- **User-level**: `user_id` - Each user has own examples
- **Type-level**: `"examples"` - Distinguishes from other semantic data

**Benefits**:
- Can add more semantic types: `("email_assistant", user_id, "templates")`
- Clear organization
- Easy to query all examples for a user

### 4.2 Episodic Memory: 3 Levels

```python
namespace = ("email_assistant", user_id, "collection")
```

**Reasoning**:
- **Application-level**: `"email_assistant"` - App-specific memories
- **User-level**: `user_id` - User isolation
- **Type-level**: `"collection"` - Distinguishes episodic from semantic

**Benefits**:
- Consistent with semantic memory structure
- Can add more episodic types: `("email_assistant", user_id, "contacts")`
- Clear separation from other memory types

### 4.3 Procedural Memory: 1 Level

```python
namespace = (user_id,)
```

**Reasoning**:
- **User-level only**: Prompts are user-specific
- **No app prefix**: Prompts might be shared across apps
- **Simpler**: Fewer levels = simpler code

**Benefits**:
- Simpler namespace resolution
- Faster lookups
- Less nesting

---

## Part 5: Namespace Resolution at Runtime

### 5.1 Semantic Memory

```python
def triage_router(state: State, config, store):
    # Namespace resolution
    namespace = (
        "email_assistant",
        config['configurable']['langgraph_user_id'],  # e.g., "lance"
        "examples"
    )
    
    # Actual namespace: ("email_assistant", "lance", "examples")
    examples = store.search(namespace, query=...)
```

**Step-by-Step**:
1. `"email_assistant"` - Fixed string
2. `config['configurable']['langgraph_user_id']` - Resolved to `"lance"`
3. `"examples"` - Fixed string
4. Result: `("email_assistant", "lance", "examples")`

### 5.2 Episodic Memory

```python
# Tool creation (at setup time)
manage_memory_tool = create_manage_memory_tool(
    namespace=(
        "email_assistant",
        "{langgraph_user_id}",  # Placeholder
        "collection"
    )
)

# Tool usage (at runtime)
# Tool internally resolves:
# 1. Gets user_id from config: "lance"
# 2. Replaces "{langgraph_user_id}" with "lance"
# 3. Result: ("email_assistant", "lance", "collection")
```

**Step-by-Step**:
1. `"email_assistant"` - Fixed string
2. `"{langgraph_user_id}"` - Placeholder, resolved at runtime to `"lance"`
3. `"collection"` - Fixed string
4. Result: `("email_assistant", "lance", "collection")`

### 5.3 Procedural Memory

```python
def create_prompt(state, config, store):
    # Namespace resolution
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id,)  # e.g., ("lance",)
    
    # Actual namespace: ("lance",)
    result = store.get(namespace, "agent_instructions")
```

**Step-by-Step**:
1. Get `user_id` from config: `"lance"`
2. Create tuple: `("lance",)`
3. Result: `("lance",)`

---

## Part 6: Isolation and Organization

### 6.1 User Isolation

**Different users have separate namespaces**:

```python
# User "lance"
namespace_lance = ("email_assistant", "lance", "examples")
store.put(namespace_lance, "example_1", {...})

# User "alice"
namespace_alice = ("email_assistant", "alice", "examples")
store.put(namespace_alice, "example_1", {...})

# These are completely separate!
# lance's example_1 ≠ alice's example_1
```

**Visual**:
```
email_assistant/
  ├── lance/
  │   └── examples/
  │       └── example_1  ← Lance's data
  └── alice/
      └── examples/
          └── example_1  ← Alice's data (different!)
```

### 6.2 Memory Type Isolation

**Different memory types have separate namespaces**:

```python
# Semantic Memory
namespace_semantic = ("email_assistant", "lance", "examples")
store.put(namespace_semantic, "example_1", {...})

# Episodic Memory
namespace_episodic = ("email_assistant", "lance", "collection")
manage_memory_tool.invoke({...})  # Stores in collection namespace

# These are completely separate!
# examples/example_1 ≠ collection/memory_xxx
```

**Visual**:
```
email_assistant/
  └── lance/
      ├── examples/
      │   └── example_1  ← Semantic memory
      └── collection/
          └── memory_xxx  ← Episodic memory (different!)
```

### 6.3 Application Isolation

**Different applications can have separate namespaces**:

```python
# Email Assistant
namespace_email = ("email_assistant", "lance", "examples")

# Calendar Assistant (hypothetical)
namespace_calendar = ("calendar_assistant", "lance", "events")

# These are completely separate!
```

**Visual**:
```
email_assistant/
  └── lance/
      └── examples/

calendar_assistant/
  └── lance/
      └── events/
```

---

## Part 7: Code Examples

### 7.1 Storing in Semantic Memory

```python
# Namespace construction
namespace = (
    "email_assistant",
    config['configurable']['langgraph_user_id'],  # "lance"
    "examples"
)
# Result: ("email_assistant", "lance", "examples")

# Store example
store.put(
    namespace,
    "example_1",  # Key
    {
        "email": {
            "subject": "API question",
            "author": "alice@company.com",
            ...
        },
        "label": "respond"
    }
)

# Full path: ("email_assistant", "lance", "examples") / "example_1"
```

### 7.2 Searching in Semantic Memory

```python
# Same namespace
namespace = ("email_assistant", "lance", "examples")

# Search
results = store.search(
    namespace,
    query=str({"email": email_input}),
    limit=3
)

# Searches only in: ("email_assistant", "lance", "examples")
# Won't find items in other namespaces
```

### 7.3 Storing in Episodic Memory

```python
# Tool created with namespace template
manage_memory_tool = create_manage_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)

# At runtime, tool resolves namespace:
# 1. Gets user_id from config: "lance"
# 2. Replaces "{langgraph_user_id}": ("email_assistant", "lance", "collection")
# 3. Stores memory

# Agent calls tool
manage_memory_tool.invoke({
    "content": "Alice prefers morning meetings",
    "metadata": {...}
})

# Stored at: ("email_assistant", "lance", "collection") / "memory_xxx"
```

### 7.4 Storing in Procedural Memory

```python
# Namespace construction
langgraph_user_id = config['configurable']['langgraph_user_id']  # "lance"
namespace = (langgraph_user_id,)  # ("lance",)

# Store prompt
store.put(
    namespace,
    "agent_instructions",  # Key
    {"prompt": "Use these tools..."}
)

# Full path: ("lance",) / "agent_instructions"
```

### 7.5 Retrieving from Procedural Memory

```python
# Same namespace
namespace = ("lance",)

# Retrieve
result = store.get(namespace, "agent_instructions")
prompt = result.value['prompt']

# Retrieves from: ("lance",) / "agent_instructions"
# Won't find items in other namespaces
```

---

## Part 8: Namespace Patterns

### Pattern 1: Application → User → Type

```python
namespace = ("email_assistant", user_id, "examples")
```

**Use Case**: When data is:
- App-specific
- User-specific
- Type-specific

**Examples**:
- Semantic memory: `("email_assistant", "lance", "examples")`
- Episodic memory: `("email_assistant", "lance", "collection")`

### Pattern 2: User Only

```python
namespace = (user_id,)
```

**Use Case**: When data is:
- User-specific
- Not app-specific
- Simple structure needed

**Examples**:
- Procedural memory: `("lance",)`
- User preferences: `("lance",)`

### Pattern 3: Application → Type

```python
namespace = ("email_assistant", "global_settings")
```

**Use Case**: When data is:
- App-specific
- Not user-specific (global)
- Type-specific

**Examples**:
- Global templates: `("email_assistant", "templates")`
- System configuration: `("email_assistant", "config")`

---

## Part 9: Common Operations

### 9.1 Getting All Items in a Namespace

```python
# Semantic Memory: Get all examples for a user
namespace = ("email_assistant", "lance", "examples")
# Note: InMemoryStore doesn't have list_all(), but you can:
# - Store with known keys
# - Use search with broad query
```

### 9.2 Checking if Namespace Exists

```python
# Try to get any key in namespace
namespace = ("email_assistant", "lance", "examples")
result = store.get(namespace, "example_1")
if result is None:
    # Namespace might be empty or doesn't exist
    # Initialize first item
    store.put(namespace, "example_1", {...})
```

### 9.3 Cross-Namespace Queries

```python
# You CANNOT query across namespaces directly
# Each namespace is isolated

# This searches only in semantic memory:
namespace_semantic = ("email_assistant", "lance", "examples")
results = store.search(namespace_semantic, query="...")

# This searches only in episodic memory:
namespace_episodic = ("email_assistant", "lance", "collection")
results = store.search(namespace_episodic, query="...")

# To search both, you need two separate queries
```

---

## Part 10: Namespace Best Practices

### 10.1 Consistent Structure

**Good**:
```python
# All episodic memories use same structure
namespace = ("email_assistant", user_id, "collection")
```

**Bad**:
```python
# Inconsistent structures
namespace1 = ("email_assistant", user_id, "collection")
namespace2 = (user_id, "episodic")  # Different structure!
```

### 10.2 Clear Naming

**Good**:
```python
namespace = ("email_assistant", user_id, "examples")  # Clear: examples
namespace = ("email_assistant", user_id, "collection")  # Clear: collection
```

**Bad**:
```python
namespace = ("email_assistant", user_id, "data")  # Unclear: what data?
namespace = ("email_assistant", user_id, "stuff")  # Unclear: what stuff?
```

### 10.3 User Isolation

**Good**:
```python
# Always include user_id for user-specific data
namespace = ("email_assistant", user_id, "examples")
```

**Bad**:
```python
# Missing user_id - data shared across users!
namespace = ("email_assistant", "examples")
```

---

## Part 11: Summary Table

| Memory Type | Namespace Structure | Levels | Example |
|------------|---------------------|--------|---------|
| **Semantic** | `("email_assistant", user_id, "examples")` | 3 | `("email_assistant", "lance", "examples")` |
| **Episodic** | `("email_assistant", user_id, "collection")` | 3 | `("email_assistant", "lance", "collection")` |
| **Procedural** | `(user_id,)` | 1 | `("lance",)` |

### Key Differences

1. **Semantic & Episodic**: 3 levels (app → user → type)
2. **Procedural**: 1 level (user only)
3. **All**: User isolation at some level
4. **Semantic & Episodic**: Same structure, different type level

---

## Part 12: Visual Summary

```
InMemoryStore
│
├── email_assistant/                    ← Application namespace
│   │
│   ├── lance/                          ← User namespace
│   │   │
│   │   ├── examples/                  ← Semantic Memory (3 levels)
│   │   │   └── example_1
│   │   │
│   │   └── collection/                 ← Episodic Memory (3 levels)
│   │       └── memory_xxx
│   │
│   └── alice/                          ← Another user
│       ├── examples/
│       └── collection/
│
└── lance/                              ← Procedural Memory (1 level)
    ├── agent_instructions
    ├── triage_ignore
    ├── triage_notify
    └── triage_respond
```

---

## Part 13: Key Takeaways

1. **Namespace = Path**: Like file system paths, organize data hierarchically
2. **Isolation**: Different namespaces = completely separate data
3. **Structure Varies**: Different memory types use different structures
4. **User Isolation**: All memory types isolate by user
5. **Runtime Resolution**: User IDs resolved at runtime from config

### Quick Reference

- **Semantic**: `("email_assistant", user_id, "examples")` - 3 levels
- **Episodic**: `("email_assistant", user_id, "collection")` - 3 levels  
- **Procedural**: `(user_id,)` - 1 level

All provide user isolation, but with different organizational structures!

