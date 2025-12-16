# Multi-Turn Conversation: Memory & Prompt Management Guide

## Overview

This guide covers state-of-the-art (SOTA) approaches for managing multi-turn conversations with LLMs, addressing the challenge of growing token costs and context windows.

---

## The Problem

In simple implementations (like our `simple_agent.py`), the entire conversation history is sent to the model on each turn:

```python
# Turn 1: Send [user_msg_1] → Get response_1
# Turn 2: Send [user_msg_1, response_1, user_msg_2] → Get response_2
# Turn 3: Send [user_msg_1, response_1, user_msg_2, response_2, user_msg_3] → Get response_3
```

**Issues:**
- Token usage grows linearly with conversation length
- Higher costs for long conversations
- Potential API context limits
- Slower response times

**Example Token Growth:**
- Turn 1: ~50 tokens
- Turn 5: ~250 tokens (5x)
- Turn 10: ~500 tokens (10x)
- Turn 20: ~1,000 tokens (20x)

---

## SOTA Approaches

### 1. Sliding Window with Summarization ⭐ Most Common

Keep recent N turns and summarize older context.

```python
def manage_context(history, max_recent_turns=10):
    """Keep recent turns + summarize older context"""
    if len(history) <= max_recent_turns * 2:
        return history
    
    # Summarize older messages
    old_context = history[:-(max_recent_turns * 2)]
    summary = llm.generate(f"Summarize this conversation: {old_context}")
    
    # Return: summary + recent messages
    return [
        {"role": "system", "parts": [f"Previous context: {summary}"]},
        *history[-(max_recent_turns * 2):]
    ]
```

**Pros:**
- Simple to implement
- Maintains recent context fully
- Bounded token usage

**Cons:**
- Older details may be lost in summary
- Requires extra LLM call for summarization

**Used by:** ChatGPT, Claude, most production systems

---

### 2. RAG (Retrieval-Augmented Generation)

Store conversation in vector database, retrieve relevant parts semantically.

```python
from chromadb import Client

class ConversationMemory:
    def __init__(self):
        self.db = Client()
        self.collection = self.db.create_collection("conversations")
        self.turn_counter = 0
    
    def add_message(self, message, metadata=None):
        """Store message with semantic embedding"""
        self.turn_counter += 1
        self.collection.add(
            documents=[message],
            ids=[f"turn_{self.turn_counter}"],
            metadatas=[{"turn": self.turn_counter, **(metadata or {})}]
        )
    
    def retrieve_relevant(self, query, n=5):
        """Semantic search over conversation history"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n
        )
        return results
    
    def build_context(self, current_query, recent_n=5):
        """Build context with recent + relevant messages"""
        # Recent turns (last N) - always include
        recent = self.get_last_n_turns(recent_n)
        
        # Relevant older turns (semantic search)
        relevant = self.retrieve_relevant(current_query, n=3)
        
        return recent + relevant
```

**Pros:**
- Finds relevant context even from distant past
- Scales to very long conversations
- Can reference specific details

**Cons:**
- Requires vector database setup
- Embedding costs
- More complex architecture

**Used by:** Advanced chatbots, enterprise assistants, research tools

**Example Use Case:**
```
Turn 50: "What was that ML algorithm we discussed earlier?"
→ Retrieves Turn 5 about "Random Forest" even though it's 45 turns ago
```

---

### 3. Hierarchical Memory System

Inspired by human memory: working memory + episodic memory + semantic memory.

```python
class HierarchicalMemory:
    def __init__(self):
        # Working memory: recent turns (like human short-term memory)
        self.working_memory = []  # Last ~5-10 turns
        
        # Episodic memory: important conversation segments
        self.episodic_memory = []  # Key moments/decisions
        
        # Semantic memory: extracted facts/entities
        self.semantic_memory = {}  # {"user_name": "John", "preferences": ["ML", "Python"]}
    
    def add_turn(self, user_msg, agent_msg):
        """Process and store a conversation turn"""
        # Add to working memory
        self.working_memory.append((user_msg, agent_msg))
        
        # Extract important facts
        facts = self.extract_facts(user_msg, agent_msg)
        self.semantic_memory.update(facts)
        
        # Identify important moments
        if self.is_important(user_msg, agent_msg):
            self.episodic_memory.append({
                "turn": len(self.working_memory),
                "user": user_msg,
                "agent": agent_msg,
                "reason": "decision_point"  # or "new_topic", "user_preference", etc.
            })
        
        # Maintain working memory size (forget old items)
        if len(self.working_memory) > 10:
            self.working_memory.pop(0)
    
    def extract_facts(self, user_msg, agent_msg):
        """Extract structured facts from conversation"""
        # Use NER, regex, or LLM to extract:
        # - User preferences
        # - Named entities
        # - Decisions made
        # - Important dates/numbers
        facts = {}
        # Example: simple keyword extraction
        if "my name is" in user_msg.lower():
            name = user_msg.lower().split("my name is")[1].strip().split()[0]
            facts["user_name"] = name
        return facts
    
    def is_important(self, user_msg, agent_msg):
        """Determine if this turn should be saved as episode"""
        # Heuristics:
        importance_signals = [
            len(user_msg) > 100,  # Long detailed message
            "important" in user_msg.lower(),
            "remember" in user_msg.lower(),
            "decision" in agent_msg.lower(),
        ]
        return any(importance_signals)
    
    def build_prompt(self, current_query):
        """Build context from all memory types"""
        context = []
        
        # 1. Semantic memory (facts) in system prompt
        if self.semantic_memory:
            context.append({
                "role": "system",
                "parts": [f"Known facts about user: {self.semantic_memory}"]
            })
        
        # 2. Key episodes (compressed)
        for episode in self.episodic_memory[-3:]:  # Last 3 important moments
            context.extend([
                {"role": "user", "parts": [f"[Episode] {episode['user']}"]},
                {"role": "model", "parts": [episode['agent']]}
            ])
        
        # 3. Recent working memory (full detail)
        for turn in self.working_memory:
            context.extend([
                {"role": "user", "parts": [turn[0]]},
                {"role": "model", "parts": [turn[1]]}
            ])
        
        return context
```

**Pros:**
- Most human-like memory structure
- Efficient context usage
- Preserves important details long-term

**Cons:**
- Complex implementation
- Requires importance scoring
- Fact extraction can be challenging

**Used by:** ChatGPT with memory feature, Claude Projects, Pi, Character.AI

**Example:**
```
Semantic Memory: {"user_name": "John", "expertise": "ML", "goal": "interview prep"}
Episodic Memory: [Turn 5: decided to focus on deep learning, Turn 23: preferred PyTorch]
Working Memory: [Last 10 turns of conversation]
```

---

### 4. Token Budget Management

Dynamically adjust context based on token limits.

```python
class TokenBudgetManager:
    def __init__(self, max_tokens=8000):
        self.max_tokens = max_tokens
        self.system_tokens = 500     # Reserve for system prompt
        self.output_tokens = 2000    # Reserve for response
        self.available = max_tokens - self.system_tokens - self.output_tokens
    
    def count_tokens(self, text):
        """Estimate token count (rough: 1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def build_context(self, history, system_prompt=""):
        """Build context that fits within token budget"""
        context = []
        token_count = self.count_tokens(system_prompt)
        
        # Start from most recent, work backwards
        for msg in reversed(history):
            msg_tokens = self.count_tokens(str(msg))
            
            if token_count + msg_tokens > self.available:
                # Stop adding older messages
                break
            
            context.insert(0, msg)
            token_count += msg_tokens
        
        return context, token_count
    
    def adaptive_context(self, history, system_prompt=""):
        """Build context with adaptive strategies based on available space"""
        context, token_count = self.build_context(history, system_prompt)
        
        if len(context) < len(history):
            # Didn't fit everything - add summary of missing context
            missing = history[:len(history) - len(context)]
            summary = self.summarize(missing)
            
            return [
                {"role": "system", "parts": [f"{system_prompt}\nEarlier context: {summary}"]},
                *context
            ]
        
        return context
```

**Pros:**
- Predictable costs
- No API limit surprises
- Can optimize for speed vs. context trade-off

**Cons:**
- May truncate important context
- Requires accurate token counting

**Used by:** OpenAI API wrappers, LangChain, production systems

---

### 5. Prompt Compression Techniques

#### A. LLMLingua / Prompt Compression

```python
from llmlingua import PromptCompressor

class CompressedContextManager:
    def __init__(self):
        self.compressor = PromptCompressor()
    
    def compress_history(self, history, target_tokens=2000):
        """Compress history while preserving meaning"""
        # Convert history to text
        text = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in history])
        
        # Compress (removes less important tokens)
        compressed = self.compressor.compress_prompt(
            text,
            rate=0.5,  # 50% compression
            target_token=target_tokens
        )
        
        return compressed
```

**Compression Example:**
```
Original (100 tokens):
"Can you please help me understand what machine learning is and how it differs from traditional programming approaches?"

Compressed (50 tokens):
"Help understand machine learning differs traditional programming?"
```

**Pros:**
- Maintains semantic meaning
- Reduces token costs significantly
- Can compress by 50-70%

**Cons:**
- May lose nuance
- Requires additional processing
- Not always readable

---

#### B. Attention-Weighted Context

```python
def weighted_context(history, current_query, top_k=5, recent_n=10):
    """Select most relevant messages by similarity to current query"""
    scores = []
    
    for i, msg in enumerate(history[:-recent_n]):  # Exclude recent (always keep)
        # Score relevance to current query
        score = compute_similarity(msg, current_query)
        scores.append((i, msg, score))
    
    # Keep top-k most relevant + recent N
    top_relevant = sorted(scores, key=lambda x: x[2], reverse=True)[:top_k]
    recent = history[-recent_n:]
    
    # Combine and sort by chronological order
    selected = [msg for _, msg, _ in sorted(top_relevant, key=lambda x: x[0])]
    return selected + recent

def compute_similarity(msg, query):
    """Compute semantic similarity (can use embeddings)"""
    # Simple version: keyword overlap
    msg_words = set(msg['parts'][0].lower().split())
    query_words = set(query.lower().split())
    return len(msg_words & query_words) / len(query_words)
```

**Pros:**
- Query-specific context selection
- Includes most relevant information
- Bounded context size

**Cons:**
- May miss chronological dependencies
- Requires similarity computation

---

### 6. Streaming Context Windows (Large Context Models)

For models with very large context windows (Claude 200K, Gemini 1M+).

```python
class StreamingContextManager:
    def __init__(self, max_context=200000):
        self.full_history = []
        self.max_context = max_context
    
    def add_turn(self, turn):
        self.full_history.append(turn)
    
    def get_context(self):
        """Use full context if within limits, else intelligently truncate"""
        if self.estimate_tokens(self.full_history) < self.max_context:
            return self.full_history
        
        return self.smart_truncate()
    
    def smart_truncate(self):
        """Keep: system + first turn + recent + important middle turns"""
        system = [self.full_history[0]]  # System prompt
        first_turn = self.full_history[1:3]  # Initial context
        recent = self.full_history[-20:]  # Recent conversation
        
        # Extract important middle turns
        middle = self.full_history[3:-20]
        important = self.extract_important_turns(middle, max_turns=10)
        
        return system + first_turn + important + recent
    
    def extract_important_turns(self, turns, max_turns=10):
        """Extract most important turns from middle section"""
        # Score by: length, keywords, user feedback, etc.
        scored = [(turn, self.importance_score(turn)) for turn in turns]
        sorted_turns = sorted(scored, key=lambda x: x[1], reverse=True)
        return [turn for turn, _ in sorted_turns[:max_turns]]
```

**Strategy:**
```
[System Prompt]
[First Turn - Context Setting]
[Important Middle Turns - Compressed]
...
[Recent 20 Turns - Full Detail]
[Current Query]
```

**Used by:** Claude 3.5 (200K), Gemini 1.5/2.0 (1M-2M tokens)

---

### 7. Multi-Agent Memory Sharing

For systems with multiple specialized agents.

```python
class SharedMemoryPool:
    def __init__(self):
        self.global_context = []           # Shared across all agents
        self.agent_contexts = {}           # Per-agent private memory
        self.cross_agent_events = []       # Agent collaboration history
    
    def add_to_global(self, message, agent_id):
        """Add message to global shared memory"""
        self.global_context.append({
            "message": message,
            "agent": agent_id,
            "timestamp": time.time()
        })
    
    def add_to_agent(self, agent_id, message):
        """Add to agent-specific memory"""
        if agent_id not in self.agent_contexts:
            self.agent_contexts[agent_id] = []
        self.agent_contexts[agent_id].append(message)
    
    def log_cross_agent_event(self, from_agent, to_agent, message):
        """Log agent-to-agent communication"""
        self.cross_agent_events.append({
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "timestamp": time.time()
        })
    
    def get_agent_context(self, agent_id, current_query):
        """Build context for specific agent"""
        context = []
        
        # 1. Compressed global context (what all agents know)
        global_summary = self.summarize(self.global_context[-50:])  # Last 50 global events
        context.append({
            "role": "system",
            "parts": [f"Shared context: {global_summary}"]
        })
        
        # 2. Agent-specific history (full detail)
        agent_history = self.agent_contexts.get(agent_id, [])
        context.extend(agent_history[-10:])  # Last 10 agent-specific turns
        
        # 3. Relevant cross-agent communications
        relevant_cross_agent = [
            event for event in self.cross_agent_events
            if event["to"] == agent_id or event["from"] == agent_id
        ]
        context.extend(relevant_cross_agent[-5:])  # Last 5 relevant communications
        
        # 4. Semantic search for relevant past interactions
        if len(self.global_context) > 100:
            relevant_global = self.semantic_search(current_query, self.global_context)
            context.extend(relevant_global[:3])  # Top 3 relevant
        
        return context
    
    def summarize(self, messages):
        """Summarize a list of messages"""
        # Use LLM or extractive summarization
        text = "\n".join([str(m) for m in messages])
        return f"Summary of {len(messages)} messages: {text[:200]}..."
    
    def semantic_search(self, query, messages):
        """Find semantically relevant messages"""
        # Use embeddings + vector search
        # Placeholder implementation
        return []
```

**Example Flow:**
```
User: "Help me with ML deployment"
  ↓
Orchestrator checks global context:
  - TechnicalAgent recently discussed Docker
  - ResearchAgent found relevant papers
  ↓
Routes to TechnicalAgent with context:
  - Global: "User interested in ML, discussed Docker"
  - Agent-specific: Last 10 TechnicalAgent conversations
  - Cross-agent: ResearchAgent found paper on "ML in Production"
```

**Used by:** AutoGPT, MetaGPT, LangGraph multi-agent systems

---

## Best Practices & Recommendations

### 1. Hybrid Approach (Production Standard)

Combine multiple techniques:

```python
class ProductionContextManager:
    def __init__(self):
        self.full_history = []
        self.semantic_memory = {}  # Extracted facts
        self.vector_store = None   # For RAG (optional)
        self.episodic_memory = []  # Important moments
    
    def build_context(self, current_query, strategy="adaptive"):
        """Build context using hybrid approach"""
        
        # Determine strategy based on conversation length
        if len(self.full_history) < 20:
            # Short conversation: use everything
            return self.full_history
        
        elif len(self.full_history) < 100:
            # Medium conversation: sliding window + facts
            return self._sliding_with_facts()
        
        else:
            # Long conversation: RAG + compression
            return self._rag_compressed(current_query)
    
    def _sliding_with_facts(self):
        """Sliding window with extracted facts"""
        context = []
        
        # Add facts as system message
        if self.semantic_memory:
            context.append({
                "role": "system",
                "parts": [f"User profile: {self.semantic_memory}"]
            })
        
        # Add recent history
        context.extend(self.full_history[-20:])
        return context
    
    def _rag_compressed(self, query):
        """RAG with compression for long conversations"""
        # Recent messages (full)
        recent = self.full_history[-10:]
        
        # Relevant older messages (RAG)
        relevant = self.vector_store.search(query, k=5)
        
        # Important episodes
        episodes = self.episodic_memory[-3:]
        
        # Combine
        return [
            {"role": "system", "parts": [f"Facts: {self.semantic_memory}"]},
            *episodes,
            *relevant,
            *recent
        ]
```

**Strategy Selection:**
```
Conversation Length → Strategy
0-20 turns         → Full history
20-100 turns       → Sliding window + facts
100-500 turns      → RAG + compression
500+ turns         → RAG + episodes + facts
```

---

### 2. Quality Over Quantity

**Principle:** 5 relevant messages > 50 irrelevant messages

**Priority Order:**
1. **Recent** (last 5-10 turns) - Always include
2. **Relevant** (semantic search) - Query-specific
3. **Important** (episodic memory) - Key decisions/moments
4. **Facts** (semantic memory) - User preferences/entities

---

### 3. Cost Optimization

Calculate cost per strategy:

```python
strategies = {
    "full_history": {
        "quality": 10,
        "cost": 10,
        "latency": "high",
        "use_case": "short conversations"
    },
    "sliding_window": {
        "quality": 8,
        "cost": 5,
        "latency": "medium",
        "use_case": "medium conversations"
    },
    "rag": {
        "quality": 9,
        "cost": 7,
        "latency": "medium",
        "use_case": "long conversations, need specific recall"
    },
    "compression": {
        "quality": 7,
        "cost": 3,
        "latency": "low",
        "use_case": "cost-sensitive applications"
    },
    "hierarchical": {
        "quality": 9,
        "cost": 6,
        "latency": "low",
        "use_case": "personalized assistants"
    }
}
```

---

### 4. Context Window Utilization

Different models have different context windows:

| Model | Context Window | Strategy |
|-------|----------------|----------|
| GPT-4 Turbo | 128K tokens | Can use full history for most conversations |
| Claude 3.5 Sonnet | 200K tokens | Full history + smart truncation |
| Gemini 1.5/2.0 Pro | 1M-2M tokens | Full history, minimal management needed |
| GPT-3.5 | 16K tokens | Aggressive truncation required |
| Open-source LLMs | 4K-8K tokens | Heavy compression needed |

**Rule of thumb:**
- Use 50% for input context
- Reserve 25% for system prompt
- Reserve 25% for output

---

## Industry Examples

### ChatGPT (OpenAI)
- **Approach:** Sliding window + summarization + fact extraction
- **Context:** 128K (GPT-4 Turbo)
- **Features:** 
  - Automatic summarization of old context
  - "Memory" feature extracts and stores facts
  - Prioritizes recent conversation

### Claude (Anthropic)
- **Approach:** Full context with intelligent truncation
- **Context:** 200K tokens
- **Features:**
  - "Projects" for persistent memory
  - Smart truncation when exceeding limits
  - Preserves important context

### Gemini (Google)
- **Approach:** Massive context window
- **Context:** 1M-2M tokens
- **Features:**
  - Minimal management needed for most uses
  - Can handle entire codebases or documents
  - Grounding with Google Search

### Character.AI
- **Approach:** Hierarchical memory with personality
- **Context:** Effectively unlimited (stored in DB)
- **Features:**
  - Long-term character memory
  - Emotional memory tracking
  - Relationship development over time

### Pi (Inflection AI)
- **Approach:** Emotional + semantic memory
- **Context:** Conversation-based
- **Features:**
  - Remembers user preferences deeply
  - Emotional connection tracking
  - Natural conversation flow

---

## Implementation Roadmap

### Phase 1: Basic (Current - simple_agent.py)
```python
# Full history approach
history.append(user_message)
response = agent.generate_content(history)
history.append(response)
```

**Good for:** Testing, short conversations, demos

---

### Phase 2: Sliding Window
```python
# Keep last N turns
MAX_TURNS = 20
if len(history) > MAX_TURNS:
    history = history[-MAX_TURNS:]
```

**Good for:** Medium-length conversations, cost control

---

### Phase 3: Facts + Sliding Window
```python
# Extract facts + recent context
facts = extract_facts(history)
recent = history[-20:]
context = [system_prompt_with_facts] + recent
```

**Good for:** Personalized assistants, user preferences

---

### Phase 4: RAG + Hierarchical
```python
# Full memory system
facts = semantic_memory
episodes = episodic_memory[-5:]
relevant = vector_search(query, k=5)
recent = history[-10:]
context = facts + episodes + relevant + recent
```

**Good for:** Production systems, long conversations

---

## Metrics to Track

1. **Token Usage**
   - Input tokens per turn
   - Total conversation tokens
   - Cost per conversation

2. **Context Quality**
   - Relevant messages included (%)
   - Important context preserved (%)
   - User satisfaction

3. **Performance**
   - Response latency
   - Context retrieval time
   - Memory overhead

4. **Effectiveness**
   - Can reference past information (%)
   - Maintains conversation coherence
   - Handles topic switches

---

## Future Trends

### 1. Infinite Context Windows
- Models like Gemini already at 2M tokens
- Trend toward "just send everything"
- But: still need smart selection for quality

### 2. Native Memory APIs
- OpenAI "Memory" feature
- Anthropic "Projects"
- Model-managed context

### 3. Multimodal Memory
- Remember images, audio, video
- Cross-modal retrieval
- Context that includes non-text

### 4. Federated Memory
- Privacy-preserving memory storage
- On-device + cloud hybrid
- User-controlled memory

---

## Recommended Approach for ADK Agents

For your Google ADK agents, I recommend:

**Phase 1 (Now):** Keep current full-history approach
- ✅ Simple
- ✅ Works for demos
- ✅ Easy to debug

**Phase 2 (Next):** Add sliding window + facts
- Limit to last 20 turns
- Extract user preferences
- Add to system prompt

**Phase 3 (Advanced):** Implement hierarchical memory
- Working memory (recent)
- Episodic memory (important)
- Semantic memory (facts)

**Phase 4 (Production):** Add RAG if needed
- Vector store for long conversations
- Semantic search over history
- Query-specific context

---

## Code Examples for ADK

### Example 1: Sliding Window

```python
# In simple_agent.py
def run_interactive():
    agent = create_agent()
    history = []
    MAX_HISTORY = 20  # Last 20 messages (10 turns)
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
        
        history.append({"role": "user", "parts": [user_input]})
        
        # Trim history
        if len(history) > MAX_HISTORY:
            # Keep first message (context) + recent messages
            history = [history[0]] + history[-(MAX_HISTORY-1):]
        
        response_text = generate_with_retry(agent, history)
        history.append({"role": "model", "parts": [response_text]})
        print(f"\nAgent: {response_text}\n")
```

### Example 2: With Facts

```python
class ContextManager:
    def __init__(self):
        self.history = []
        self.facts = {}
    
    def add_turn(self, user_msg, agent_msg):
        self.history.append({"role": "user", "parts": [user_msg]})
        self.history.append({"role": "model", "parts": [agent_msg]})
        
        # Extract facts
        self._update_facts(user_msg)
    
    def _update_facts(self, message):
        """Simple fact extraction"""
        msg_lower = message.lower()
        if "my name is" in msg_lower:
            name = msg_lower.split("my name is")[1].strip().split()[0]
            self.facts["name"] = name
        if "i like" in msg_lower:
            interest = msg_lower.split("i like")[1].strip().split()[0]
            if "interests" not in self.facts:
                self.facts["interests"] = []
            self.facts["interests"].append(interest)
    
    def get_context(self):
        """Build context with facts + recent history"""
        context = []
        
        # Add facts to system prompt
        if self.facts:
            context.append({
                "role": "system",
                "parts": [f"Known about user: {self.facts}"]
            })
        
        # Add recent history
        context.extend(self.history[-20:])
        return context
```

---

## Resources & References

### Papers
- "Lost in the Middle: How Language Models Use Long Contexts" (2023)
- "LLMLingua: Compressing Prompts for Accelerated Inference" (2023)
- "MemGPT: Towards LLMs as Operating Systems" (2023)

### Tools & Libraries
- **LangChain:** Memory components
- **LlamaIndex:** Context management
- **ChromaDB:** Vector storage for RAG
- **LLMLingua:** Prompt compression

### APIs with Memory Features
- OpenAI Memory API
- Anthropic Projects
- Google Gemini with grounding

---

## Conclusion

Multi-turn conversation management is crucial for production LLM applications. The key is to:

1. **Start simple:** Full history for short conversations
2. **Optimize gradually:** Add sliding window → facts → RAG
3. **Measure constantly:** Track tokens, costs, quality
4. **Choose wisely:** Match strategy to use case

The future is trending toward larger context windows, but intelligent context management remains important for quality and cost optimization.

---

**Last Updated:** December 2025  
**Version:** 1.0  
**Author:** Created for ADK Agents Project

