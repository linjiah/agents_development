# PostgresStore Explained

## Overview

`PostgresStore` is a **persistent storage implementation** for LangGraph that uses PostgreSQL as the backend database. It provides the same interface as `InMemoryStore` but stores data in a PostgreSQL database, making it suitable for production deployments.

---

## Part 1: What is PostgresStore?

### Basic Definition

```python
from langgraph.store.postgres import PostgresStore

store = PostgresStore(
    connection_string="postgresql://user:password@localhost:5432/database",
    index={"embed": "openai:text-embedding-3-small"}
)
```

**What it is**:
- A LangGraph store implementation that uses PostgreSQL
- Provides same interface as `InMemoryStore`
- Stores data persistently in PostgreSQL database
- Supports vector search via pgvector extension
- Production-ready storage solution

### Key Characteristics

1. **Persistent**: Data stored in PostgreSQL database (survives restarts)
2. **Same Interface**: Works exactly like `InMemoryStore`
3. **Vector Search**: Supports semantic search via pgvector
4. **Scalable**: Can handle multiple processes/instances
5. **Production-Ready**: Suitable for production deployments

---

## Part 2: Comparison with InMemoryStore

### Side-by-Side Comparison

| Feature | InMemoryStore | PostgresStore |
|---------|---------------|---------------|
| **Storage Location** | RAM (memory) | PostgreSQL database (disk) |
| **Persistence** | ❌ No (lost on restart) | ✅ Yes (survives restarts) |
| **Speed** | ⚡ Very fast (RAM) | 🐌 Slower (disk I/O) |
| **Scalability** | ❌ Single process | ✅ Multiple processes |
| **Setup** | ✅ Simple (no setup) | ⚙️ Requires PostgreSQL |
| **Production Ready** | ❌ No | ✅ Yes |
| **Interface** | Same | Same |

### Code Comparison

**InMemoryStore**:
```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)
# Data in RAM - lost on restart
```

**PostgresStore**:
```python
from langgraph.store.postgres import PostgresStore

store = PostgresStore(
    connection_string="postgresql://user:pass@host:5432/db",
    index={"embed": "openai:text-embedding-3-small"}
)
# Data in PostgreSQL - persists across restarts
```

**Usage is identical**:
```python
# Both work the same way!
store.put(namespace, key, value)
result = store.get(namespace, key)
results = store.search(namespace, query="...", limit=5)
```

---

## Part 3: How PostgresStore Works

### 3.1 Architecture

```
┌─────────────────────────────────────────┐
│         Python Application               │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │      PostgresStore               │   │
│  │                                  │   │
│  │  - put()                         │   │
│  │  - get()                         │   │
│  │  - search()                      │   │
│  └──────────────────────────────────┘   │
│         │                                 │
│         │ SQL queries                    │
│         ▼                                 │
┌─────────────────────────────────────────┐
│      PostgreSQL Database                │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │      Tables                      │   │
│  │  - store_items (key-value)       │   │
│  │  - store_embeddings (vectors)    │   │
│  └──────────────────────────────────┘   │
│                                          │
│  (Data persisted on disk)                │
└─────────────────────────────────────────┘
```

### 3.2 Internal Storage Structure

**PostgresStore creates tables**:

**1. `store_items` table** (key-value storage):
```sql
CREATE TABLE store_items (
    namespace TEXT[],
    key TEXT,
    value JSONB,
    created_at TIMESTAMP,
    PRIMARY KEY (namespace, key)
);
```

**2. `store_embeddings` table** (vector search):
```sql
CREATE TABLE store_embeddings (
    namespace TEXT[],
    key TEXT,
    embedding vector(1536),  -- pgvector type
    metadata JSONB,
    PRIMARY KEY (namespace, key)
);
```

### 3.3 Operations

**Store Operation**:
```python
store.put(("lance",), "agent_instructions", {"prompt": "..."})
```

**Behind the scenes**:
```sql
INSERT INTO store_items (namespace, key, value)
VALUES (ARRAY['lance'], 'agent_instructions', '{"prompt": "..."}');
```

**Retrieve Operation**:
```python
result = store.get(("lance",), "agent_instructions")
```

**Behind the scenes**:
```sql
SELECT value FROM store_items
WHERE namespace = ARRAY['lance'] AND key = 'agent_instructions';
```

**Search Operation**:
```python
results = store.search(namespace, query="...", limit=5)
```

**Behind the scenes**:
```sql
-- 1. Create embedding for query
-- 2. Vector similarity search
SELECT key, value, embedding <-> query_embedding AS distance
FROM store_embeddings
WHERE namespace = ARRAY['email_assistant', 'lance', 'examples']
ORDER BY distance
LIMIT 5;
```

---

## Part 4: Requirements and Setup

### 4.1 Prerequisites

**1. PostgreSQL Database**:
- PostgreSQL 12+ installed
- Database created
- User with appropriate permissions

**2. pgvector Extension**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**3. Python Packages**:
```bash
pip install langgraph-store-postgres psycopg2-binary pgvector
```

### 4.2 Connection String Format

```python
connection_string = "postgresql://[user]:[password]@[host]:[port]/[database]"
```

**Examples**:
```python
# Local database
"postgresql://postgres:password@localhost:5432/email_agent"

# Remote database
"postgresql://user:pass@db.example.com:5432/email_agent"

# With SSL
"postgresql://user:pass@host:5432/db?sslmode=require"
```

### 4.3 Setup Steps

**Step 1: Install PostgreSQL**:
```bash
# macOS
brew install postgresql

# Ubuntu
sudo apt-get install postgresql postgresql-contrib

# Or use Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres
```

**Step 2: Create Database**:
```sql
CREATE DATABASE email_agent_db;
```

**Step 3: Enable pgvector**:
```sql
\c email_agent_db
CREATE EXTENSION IF NOT EXISTS vector;
```

**Step 4: Use in Code**:
```python
from langgraph.store.postgres import PostgresStore

store = PostgresStore(
    connection_string="postgresql://postgres:password@localhost:5432/email_agent_db",
    index={"embed": "openai:text-embedding-3-small"}
)
```

---

## Part 5: Features

### 5.1 Same Interface as InMemoryStore

**All operations work identically**:

```python
# Store
store.put(namespace, key, value)

# Retrieve
result = store.get(namespace, key)

# Search
results = store.search(namespace, query="...", limit=5)

# Check existence
result = store.get(namespace, key)
if result is None:
    # Key doesn't exist
```

### 5.2 Vector Search Support

**Automatic embedding creation and storage**:

```python
store = PostgresStore(
    connection_string="...",
    index={"embed": "openai:text-embedding-3-small"}
)

# Store with automatic embedding
store.put(
    ("email_assistant", "lance", "examples"),
    "example_1",
    {"email": {...}, "label": "respond"}
)
# Embedding automatically created and stored

# Search using vectors
results = store.search(
    ("email_assistant", "lance", "examples"),
    query="API documentation question",
    limit=3
)
# Uses pgvector for similarity search
```

### 5.3 Namespace Support

**Same namespace structure**:

```python
# Procedural Memory
namespace = ("lance",)
store.put(namespace, "agent_instructions", {...})

# Semantic Memory
namespace = ("email_assistant", "lance", "examples")
store.put(namespace, "example_1", {...})

# Episodic Memory
namespace = ("email_assistant", "lance", "collection")
# Used by tools automatically
```

### 5.4 Transaction Support

**ACID transactions** (automatic):

```python
# Operations are transactional
store.put(namespace, "key1", value1)
store.put(namespace, "key2", value2)
# Both succeed or both fail
```

---

## Part 6: Advantages

### 6.1 Persistence

✅ **Data survives restarts**:
```python
# Run 1: Store data
store.put(("lance",), "agent_instructions", {"prompt": "Updated..."})
# Application ends

# Run 2: Data still there!
result = store.get(("lance",), "agent_instructions")
print(result.value)  # ✅ Still has "Updated..."
```

### 6.2 Scalability

✅ **Multiple processes can share data**:
```python
# Process 1
store1 = PostgresStore(connection_string="...")
store1.put(("lance",), "key", "value1")

# Process 2 (different process, same database)
store2 = PostgresStore(connection_string="...")
result = store2.get(("lance",), "key")
print(result.value)  # ✅ "value1" - shared!
```

### 6.3 Reliability

✅ **Database features**:
- ACID transactions
- Backup and recovery
- Replication support
- Point-in-time recovery

### 6.4 Production Features

✅ **Enterprise-ready**:
- Connection pooling
- Query optimization
- Indexing support
- Monitoring and logging

---

## Part 7: Limitations and Considerations

### 7.1 Performance

⚠️ **Slower than InMemoryStore**:
- Disk I/O vs RAM access
- Network latency (if remote)
- Still fast enough for most use cases

### 7.2 Setup Complexity

⚠️ **Requires PostgreSQL setup**:
- Database installation
- Configuration
- Maintenance

### 7.3 Dependencies

⚠️ **Additional requirements**:
- PostgreSQL server
- pgvector extension
- Python packages

---

## Part 8: Usage Example

### 8.1 Complete Example

```python
import os
from langgraph.store.postgres import PostgresStore
from dotenv import load_dotenv

load_dotenv()

# Create store
store = PostgresStore(
    connection_string=os.getenv("POSTGRES_CONNECTION_STRING"),
    index={"embed": "openai:text-embedding-3-small"}
)

# Procedural Memory
namespace = ("lance",)
store.put(namespace, "agent_instructions", {"prompt": "Use tools..."})
result = store.get(namespace, "agent_instructions")
print(result.value['prompt'])

# Semantic Memory
namespace = ("email_assistant", "lance", "examples")
store.put(namespace, "example_1", {
    "email": {"subject": "API question", "author": "alice@company.com"},
    "label": "respond"
})
results = store.search(namespace, query="API documentation", limit=3)
print(f"Found {len(results)} similar examples")

# Episodic Memory (via tools - works automatically)
# Tools use the same store instance
```

### 8.2 Environment-Based Configuration

```python
import os
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore

def create_store():
    """Create store based on environment."""
    use_persistent = os.getenv("USE_PERSISTENT_STORE", "false").lower() == "true"
    
    if use_persistent:
        return PostgresStore(
            connection_string=os.getenv("POSTGRES_CONNECTION_STRING"),
            index={"embed": "openai:text-embedding-3-small"}
        )
    else:
        return InMemoryStore(
            index={"embed": "openai:text-embedding-3-small"}
        )

store = create_store()
```

---

## Part 9: Migration from InMemoryStore

### 9.1 Simple Migration

**Step 1: Install packages**:
```bash
pip install langgraph-store-postgres psycopg2-binary pgvector
```

**Step 2: Set up PostgreSQL**:
```sql
CREATE DATABASE email_agent_db;
CREATE EXTENSION vector;
```

**Step 3: Update code**:
```python
# Change this:
from langgraph.store.memory import InMemoryStore
store = InMemoryStore(index={"embed": "..."})

# To this:
from langgraph.store.postgres import PostgresStore
store = PostgresStore(
    connection_string="postgresql://...",
    index={"embed": "..."}
)
```

**Step 4: Everything else stays the same!**

### 9.2 No Code Changes Needed

**All memory operations work identically**:
- ✅ Procedural memory: Same code
- ✅ Semantic memory: Same code
- ✅ Episodic memory: Same code (tools work automatically)

---

## Part 10: Best Practices

### 10.1 Connection String Management

✅ **Use environment variables**:
```python
import os
connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
```

❌ **Don't hardcode**:
```python
# Bad!
connection_string = "postgresql://user:password@host/db"
```

### 10.2 Connection Pooling

✅ **Use connection pooling** (PostgresStore handles this):
```python
# PostgresStore automatically uses connection pooling
store = PostgresStore(connection_string="...")
```

### 10.3 Error Handling

✅ **Handle connection errors**:
```python
try:
    store = PostgresStore(connection_string="...")
    result = store.get(namespace, key)
except Exception as e:
    print(f"Database error: {e}")
    # Fallback or retry logic
```

### 10.4 Backup Strategy

✅ **Set up database backups**:
```bash
# PostgreSQL backup
pg_dump email_agent_db > backup.sql

# Restore
psql email_agent_db < backup.sql
```

---

## Part 11: Summary

### What PostgresStore Is

- **Persistent storage** for LangGraph using PostgreSQL
- **Same interface** as InMemoryStore
- **Production-ready** solution
- **Vector search** support via pgvector

### Key Differences from InMemoryStore

| Aspect | InMemoryStore | PostgresStore |
|--------|---------------|---------------|
| **Storage** | RAM | PostgreSQL database |
| **Persistence** | ❌ No | ✅ Yes |
| **Speed** | ⚡ Very fast | 🐌 Slower (but still fast) |
| **Scalability** | ❌ Single process | ✅ Multiple processes |
| **Setup** | ✅ Simple | ⚙️ Requires PostgreSQL |

### When to Use

✅ **Use PostgresStore for**:
- Production deployments
- Data that must persist
- Multi-process applications
- Scalable systems

❌ **Use InMemoryStore for**:
- Development and testing
- Prototyping
- Single-process applications
- Temporary data

### Key Takeaway

`PostgresStore` is a **drop-in replacement** for `InMemoryStore` that provides persistence. The interface is identical, so you can switch between them with minimal code changes. For production, `PostgresStore` is the recommended choice.

---

This document provides a complete understanding of PostgresStore and how it enables persistent storage for all three memory types in the email agent.

