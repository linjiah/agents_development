# Production Persistence Guide: Making Memories Persistent

## Overview

This guide explains how to make all three memory types (Semantic, Episodic, Procedural) persistent for production deployment of the email agent.

---

## Part 1: Current State vs Production Needs

### Current Implementation (Development)

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)
```

**Limitations**:
- ❌ Data lost on restart
- ❌ No persistence
- ❌ Single process only
- ❌ Not production-ready

### Production Requirements

✅ **Needs**:
- Data survives restarts
- Scalable across processes
- Reliable storage
- Vector search capability
- Fast retrieval

---

## Part 2: Persistent Storage Options

### Option 1: PostgreSQL with pgvector (Recommended)

**Best for**: Production applications with existing PostgreSQL infrastructure

**Features**:
- ✅ Full SQL database
- ✅ Vector search via pgvector extension
- ✅ ACID transactions
- ✅ Scalable
- ✅ Production-proven

### Option 2: SQLite with vector extension

**Best for**: Small to medium applications, single-server deployments

**Features**:
- ✅ Simple setup (file-based)
- ✅ No server required
- ✅ Vector search support
- ✅ Good for single-process apps

### Option 3: Cloud Vector Databases

**Best for**: Large-scale, distributed applications

**Options**:
- **Pinecone**: Managed vector database
- **Weaviate**: Open-source vector database
- **Qdrant**: High-performance vector database
- **Chroma**: Embedded vector database

**Features**:
- ✅ Managed service (Pinecone)
- ✅ High performance
- ✅ Built for vectors
- ✅ Scalable

### Option 4: Hybrid Approach

**Best for**: Complex requirements

**Strategy**:
- Procedural Memory → PostgreSQL (simple key-value)
- Semantic Memory → Vector DB (optimized for search)
- Episodic Memory → PostgreSQL or Vector DB

---

## Part 3: Implementation: PostgreSQL with pgvector

### 3.1 Setup

**Install Dependencies**:
```bash
pip install langgraph-store-postgres psycopg2-binary pgvector
```

**Database Setup**:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for vector storage (if needed)
-- LangGraph PostgresStore handles this automatically
```

### 3.2 Code Changes

**Replace InMemoryStore**:

```python
# OLD (Development)
from langgraph.store.memory import InMemoryStore
store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)

# NEW (Production)
from langgraph.store.postgres import PostgresStore

store = PostgresStore(
    connection_string="postgresql://user:password@localhost:5432/email_agent_db",
    index={"embed": "openai:text-embedding-3-small"}
)
```

**Complete Example**:

```python
import os
from langgraph.store.postgres import PostgresStore
from dotenv import load_dotenv

load_dotenv()

# Get connection string from environment
connection_string = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    "postgresql://user:password@localhost:5432/email_agent_db"
)

# Create persistent store
store = PostgresStore(
    connection_string=connection_string,
    index={"embed": "openai:text-embedding-3-small"}
)
```

### 3.3 Environment Variables

**`.env` file**:
```bash
POSTGRES_CONNECTION_STRING=postgresql://user:password@localhost:5432/email_agent_db
OPENAI_API_KEY=your_openai_key
```

### 3.4 All Memory Types Work Automatically

**No code changes needed for memory operations**:

```python
# Procedural Memory - works the same
namespace = (user_id,)
store.put(namespace, "agent_instructions", {"prompt": "..."})
result = store.get(namespace, "agent_instructions")

# Semantic Memory - works the same
namespace = ("email_assistant", user_id, "examples")
store.put(namespace, "example_1", {"email": {...}, "label": "respond"})
results = store.search(namespace, query="...", limit=5)

# Episodic Memory - tools work the same
manage_memory_tool = create_manage_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)
# Tool automatically uses persistent store
```

**Key Point**: The store interface is the same - only the implementation changes!

---

## Part 4: Implementation: SQLite with Vector Support

### 4.1 Setup

**Install Dependencies**:
```bash
pip install langgraph-store-sqlite
```

### 4.2 Code Changes

```python
# OLD
from langgraph.store.memory import InMemoryStore
store = InMemoryStore(index={"embed": "openai:text-embedding-3-small"})

# NEW
from langgraph.store.sqlite import SqliteStore

store = SqliteStore(
    path="./email_agent.db",  # File path
    index={"embed": "openai:text-embedding-3-small"}
)
```

**Complete Example**:

```python
from langgraph.store.sqlite import SqliteStore

store = SqliteStore(
    path="./data/email_agent.db",  # Persistent file
    index={"embed": "openai:text-embedding-3-small"}
)

# All memory operations work the same
# Data persists in the .db file
```

**Benefits**:
- ✅ Simple (file-based)
- ✅ No server needed
- ✅ Good for single-process apps
- ✅ Easy backup (just copy file)

**Limitations**:
- ❌ Single process only
- ❌ Not ideal for distributed systems

---

## Part 5: Implementation: Cloud Vector Database (Pinecone)

### 5.1 Setup

**Install Dependencies**:
```bash
pip install pinecone-client langchain-pinecone
```

**Pinecone Setup**:
1. Create account at pinecone.io
2. Create index with appropriate dimensions (1536 for text-embedding-3-small)
3. Get API key

### 5.2 Hybrid Approach

**Use Pinecone for Semantic/Episodic, PostgreSQL for Procedural**:

```python
from langgraph.store.postgres import PostgresStore
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

# Procedural Memory: PostgreSQL (simple key-value)
procedural_store = PostgresStore(
    connection_string="postgresql://...",
    # No index needed for simple key-value
)

# Semantic/Episodic Memory: Pinecone (vector search)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
vector_store = PineconeVectorStore(
    index=pc.Index("email-agent-memories"),
    embedding="openai:text-embedding-3-small"
)

# Custom wrapper to use both stores
class HybridStore:
    def __init__(self, procedural_store, vector_store):
        self.procedural = procedural_store
        self.vector = vector_store
    
    def get(self, namespace, key):
        # Procedural memory uses procedural store
        if len(namespace) == 1:  # (user_id,)
            return self.procedural.get(namespace, key)
        # Otherwise use vector store
        # ... implementation
    
    def put(self, namespace, key, value):
        # Similar logic
        ...
    
    def search(self, namespace, query, limit=5):
        # Use vector store
        return self.vector_store.similarity_search(query, k=limit)
```

**Note**: This requires more custom code. Simpler to use PostgresStore with pgvector.

---

## Part 6: Migration Strategy

### 6.1 Gradual Migration

**Step 1: Add Environment Variable**:

```python
import os
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore

# Choose store based on environment
USE_PERSISTENT_STORE = os.getenv("USE_PERSISTENT_STORE", "false").lower() == "true"

if USE_PERSISTENT_STORE:
    # Production: Use PostgreSQL
    connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
    store = PostgresStore(
        connection_string=connection_string,
        index={"embed": "openai:text-embedding-3-small"}
    )
else:
    # Development: Use InMemoryStore
    store = InMemoryStore(
        index={"embed": "openai:text-embedding-3-small"}
    )
```

**Step 2: Update Environment Files**:

**`.env.development`**:
```bash
USE_PERSISTENT_STORE=false
```

**`.env.production`**:
```bash
USE_PERSISTENT_STORE=true
POSTGRES_CONNECTION_STRING=postgresql://user:password@prod-db:5432/email_agent
```

### 6.2 Data Migration (If Needed)

**Export from InMemoryStore** (if you have existing data):

```python
def export_memories(inmemory_store):
    """Export all memories from InMemoryStore."""
    # This is a simplified example
    # InMemoryStore doesn't have a list_all() method
    # You'd need to track keys separately
    
    memories = {
        "procedural": {},
        "semantic": {},
        "episodic": {}
    }
    
    # Export procedural memories
    for user_id in known_user_ids:
        namespace = (user_id,)
        for key in ["agent_instructions", "triage_ignore", ...]:
            result = inmemory_store.get(namespace, key)
            if result:
                memories["procedural"][f"{user_id}/{key}"] = result.value
    
    return memories

def import_memories(persistent_store, memories):
    """Import memories to persistent store."""
    # Import procedural
    for key, value in memories["procedural"].items():
        user_id, prompt_key = key.split("/")
        namespace = (user_id,)
        persistent_store.put(namespace, prompt_key, value)
    
    # Import semantic and episodic similarly
    ...
```

---

## Part 7: Complete Production Example

### 7.1 Production Configuration

**`config/production.py`**:

```python
import os
from langgraph.store.postgres import PostgresStore
from dotenv import load_dotenv

load_dotenv()

def create_production_store():
    """Create persistent store for production."""
    connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
    
    if not connection_string:
        raise ValueError("POSTGRES_CONNECTION_STRING not set")
    
    return PostgresStore(
        connection_string=connection_string,
        index={"embed": "openai:text-embedding-3-small"}
    )

# Create store
store = create_production_store()
```

### 7.2 Updated Agent Code

**`email_agent_with_longmem.py`** (updated):

```python
import os
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore

# ... other imports ...

# ============================================================================
# Memory Store Setup (Production-Ready)
# ============================================================================

def create_store():
    """Create store based on environment."""
    use_persistent = os.getenv("USE_PERSISTENT_STORE", "false").lower() == "true"
    
    if use_persistent:
        # Production: PostgreSQL
        connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("POSTGRES_CONNECTION_STRING required for persistent store")
        
        store = PostgresStore(
            connection_string=connection_string,
            index={"embed": "openai:text-embedding-3-small"}
        )
        print("✅ Using persistent PostgreSQL store")
    else:
        # Development: InMemoryStore
        store = InMemoryStore(
            index={"embed": "openai:text-embedding-3-small"}
        )
        print("⚠️  Using in-memory store (data will be lost on restart)")
    
    return store

store = create_store()

# Rest of code remains the same!
# All memory operations work identically
```

### 7.3 Environment Configuration

**`.env.production`**:
```bash
# Storage
USE_PERSISTENT_STORE=true
POSTGRES_CONNECTION_STRING=postgresql://user:password@db-host:5432/email_agent

# API Keys
OPENAI_API_KEY=your_openai_key
```

**`.env.development`**:
```bash
# Storage
USE_PERSISTENT_STORE=false

# API Keys
OPENAI_API_KEY=your_openai_key
```

---

## Part 8: Testing Persistent Storage

### 8.1 Test Script

```python
import os
from langgraph.store.postgres import PostgresStore

# Setup
connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
store = PostgresStore(
    connection_string=connection_string,
    index={"embed": "openai:text-embedding-3-small"}
)

# Test 1: Procedural Memory
print("Test 1: Procedural Memory")
namespace = ("test_user",)
store.put(namespace, "agent_instructions", {"prompt": "Test prompt"})
result = store.get(namespace, "agent_instructions")
print(f"Stored: {result.value}")

# Test 2: Semantic Memory
print("\nTest 2: Semantic Memory")
namespace = ("email_assistant", "test_user", "examples")
store.put(namespace, "example_1", {
    "email": {"subject": "Test", "author": "test@example.com"},
    "label": "respond"
})
results = store.search(namespace, query="test email", limit=1)
print(f"Found: {len(results)} results")

# Test 3: Restart Simulation
print("\nTest 3: Restart Simulation")
# Simulate restart by creating new store instance
store2 = PostgresStore(
    connection_string=connection_string,
    index={"embed": "openai:text-embedding-3-small"}
)
result = store2.get(("test_user",), "agent_instructions")
if result:
    print(f"✅ Data persisted: {result.value}")
else:
    print("❌ Data lost")

print("\n✅ All tests passed!")
```

---

## Part 9: Production Checklist

### 9.1 Setup Checklist

- [ ] Choose persistent storage solution (PostgreSQL recommended)
- [ ] Install required packages (`langgraph-store-postgres`, `pgvector`)
- [ ] Set up database with pgvector extension
- [ ] Configure connection string in environment variables
- [ ] Update code to use persistent store
- [ ] Test all three memory types
- [ ] Set up database backups
- [ ] Configure connection pooling
- [ ] Set up monitoring/alerting
- [ ] Document connection string format

### 9.2 Security Checklist

- [ ] Use environment variables for credentials
- [ ] Never commit credentials to code
- [ ] Use SSL/TLS for database connections
- [ ] Restrict database access (firewall, IP whitelist)
- [ ] Use strong passwords
- [ ] Rotate credentials regularly
- [ ] Enable database logging/auditing

### 9.3 Performance Checklist

- [ ] Set up connection pooling
- [ ] Index frequently queried fields
- [ ] Monitor query performance
- [ ] Set up database replication (if needed)
- [ ] Configure appropriate timeouts
- [ ] Monitor memory usage
- [ ] Set up caching (if applicable)

---

## Part 10: Code Example - Complete Production Setup

### 10.1 Store Factory

**`store_factory.py`**:

```python
"""Store factory for creating appropriate store based on environment."""
import os
from typing import Union
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import BaseStore

def create_store() -> BaseStore:
    """
    Create store based on environment configuration.
    
    Returns:
        BaseStore: InMemoryStore for development, PostgresStore for production
    """
    use_persistent = os.getenv("USE_PERSISTENT_STORE", "false").lower() == "true"
    
    if use_persistent:
        connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
        if not connection_string:
            raise ValueError(
                "USE_PERSISTENT_STORE=true requires POSTGRES_CONNECTION_STRING"
            )
        
        store = PostgresStore(
            connection_string=connection_string,
            index={"embed": "openai:text-embedding-3-small"}
        )
        print("✅ Using persistent PostgreSQL store")
        return store
    else:
        store = InMemoryStore(
            index={"embed": "openai:text-embedding-3-small"}
        )
        print("⚠️  Using in-memory store (data will be lost on restart)")
        return store
```

### 10.2 Updated Main File

**`email_agent_with_longmem.py`** (key changes):

```python
# ... existing imports ...
from store_factory import create_store

# ============================================================================
# Memory Store Setup
# ============================================================================

store = create_store()  # ← Changed: Uses factory

# Rest of code remains EXACTLY the same!
# All memory operations work identically regardless of store type
```

---

## Part 11: Comparison Table

| Feature | InMemoryStore | PostgresStore | SQLiteStore | Pinecone |
|---------|---------------|---------------|-------------|----------|
| **Persistence** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Vector Search** | ✅ Yes | ✅ Yes (pgvector) | ✅ Yes | ✅ Yes |
| **Setup Complexity** | ⭐ Simple | ⭐⭐ Medium | ⭐ Simple | ⭐⭐ Medium |
| **Scalability** | ❌ Single process | ✅ High | ⭐⭐ Medium | ✅ High |
| **Cost** | 💰 Free | 💰 Self-hosted | 💰 Free | 💰 Paid |
| **Production Ready** | ❌ No | ✅ Yes | ⚠️ Limited | ✅ Yes |
| **Best For** | Development | Production | Small apps | Large scale |

---

## Part 12: Recommendations

### For Production

**Recommended**: PostgreSQL with pgvector

**Why**:
- ✅ Production-proven
- ✅ Full SQL database
- ✅ Vector search support
- ✅ Scalable
- ✅ Open source
- ✅ Good performance

**Setup**:
```python
store = PostgresStore(
    connection_string="postgresql://user:pass@host:5432/db",
    index={"embed": "openai:text-embedding-3-small"}
)
```

### For Small Applications

**Alternative**: SQLite with vector support

**Why**:
- ✅ Simple (file-based)
- ✅ No server needed
- ✅ Good for single-process apps

**Setup**:
```python
store = SqliteStore(
    path="./email_agent.db",
    index={"embed": "openai:text-embedding-3-small"}
)
```

### For Large Scale

**Alternative**: Cloud vector database (Pinecone, Weaviate)

**Why**:
- ✅ Managed service
- ✅ High performance
- ✅ Built for vectors
- ✅ Auto-scaling

---

## Part 13: Summary

### Key Points

1. **Replace InMemoryStore**: Use `PostgresStore` or `SqliteStore`
2. **Same Interface**: All memory operations work the same
3. **Environment-Based**: Use environment variables to switch
4. **All Memory Types**: Work automatically with persistent store
5. **Production Ready**: PostgreSQL recommended for production

### Migration Path

```
Development (InMemoryStore)
    ↓
Add environment variable
    ↓
Use PostgresStore in production
    ↓
All memory types persist automatically
```

### Code Changes Required

**Minimal!** Only change the store creation:

```python
# OLD
store = InMemoryStore(index={"embed": "..."})

# NEW
store = PostgresStore(
    connection_string=os.getenv("POSTGRES_CONNECTION_STRING"),
    index={"embed": "..."}
)
```

**Everything else stays the same!**

---

This guide provides everything needed to make all three memory types persistent for production deployment.

