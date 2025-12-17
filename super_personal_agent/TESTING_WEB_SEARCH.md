# Testing Web Search

## Quick Start

Yes! Use `./start.sh` to test everything:

```bash
cd super_personal_agent
./start.sh
```

This will:
1. ✅ Install backend dependencies (if needed)
2. ✅ Start FastAPI backend on port 8000
3. ✅ Start frontend server on port 8080
4. ✅ Open http://localhost:8080 in your browser

## Testing Web Search

### Step 1: Start the Application

```bash
cd super_personal_agent
./start.sh
```

### Step 2: Open the Web UI

Open your browser and go to: **http://localhost:8080**

### Step 3: Test Web Search

Try asking these questions in the chat:

1. **"What's the latest news about artificial intelligence?"**
2. **"Search for information about Python 3.12 new features"**
3. **"What are the current trends in machine learning?"**
4. **"Find recent articles about neural networks"**

### What to Look For

When you ask a question that needs current information, you should see:

1. **In the chat**: The agent will automatically use web search
2. **In backend terminal**: You'll see the search being performed
3. **In the response**: Current information from web search results

### Example Interaction

```
You: What's the latest news about AI?

Agent: [Automatically calls web_search tool]
       [Gets results from DuckDuckGo]
       [Summarizes the information]
       
       "Based on recent search results, here's what's happening in AI..."
```

## Troubleshooting

### Web search not working?

1. **Check backend terminal** for errors
2. **Verify duckduckgo-search is installed**:
   ```bash
   python3 -c "from duckduckgo_search import DDGS; print('✅ Installed')"
   ```

3. **If not installed**:
   ```bash
   python3 -m pip install duckduckgo-search
   ```

### Agent not using web search?

- Make your questions more specific about current events
- Try: "What's the latest news about..." or "Search for..."
- The agent should automatically detect when web search is needed

## Manual Testing (Backend Only)

If you want to test just the backend:

```bash
cd super_personal_agent/backend
python3 main.py
```

Then test via API:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the latest news about AI?"}'
```

---

**Ready to test! Run `./start.sh` and start asking questions!** 🚀

