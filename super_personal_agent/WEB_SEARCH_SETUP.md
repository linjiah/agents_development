# Web Search Setup

## Overview

The multimodal agent now supports web search! It can search the web for current information, news, facts, and any topic.

## Search Providers

### 1. DuckDuckGo (Default - Free, No API Key)

**Status**: ✅ Already configured  
**Requires**: `duckduckgo-search` package (already in requirements.txt)

**Installation**:
```bash
pip install duckduckgo-search
```

**Usage**: Works automatically, no configuration needed!

### 2. Tavily API (Optional - Better Quality)

**Status**: Optional, requires API key  
**Requires**: `TAVILY_API_KEY` in `.env` file

**Setup**:
1. Get API key from [Tavily](https://tavily.com/)
2. Add to `.env`:
   ```bash
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

**Benefits**:
- Higher quality search results
- Better for research and factual queries
- More reliable API

## How It Works

The agent automatically uses:
1. **Tavily** (if `TAVILY_API_KEY` is set)
2. **DuckDuckGo** (fallback, always available)

## Usage Examples

The agent will automatically use web search when you ask:

- "What's the latest news about AI?"
- "Search for information about Python 3.12 features"
- "What's the current weather in San Francisco?"
- "Find recent articles about machine learning"
- "What happened in the tech industry this week?"

## Testing

Try asking the agent:
```
"What are the latest developments in AI?"
```

The agent should automatically:
1. Call the `web_search` tool
2. Get search results
3. Summarize the information for you

## Troubleshooting

### "No module named 'duckduckgo_search'"
```bash
pip install duckduckgo-search
```

### Search not working
- Check if `duckduckgo-search` is installed
- If using Tavily, verify `TAVILY_API_KEY` is set correctly
- Check backend logs for errors

### Poor search results
- Try using Tavily API for better quality
- Make your search queries more specific

---

**Web search is now enabled!** The agent will automatically search the web when it needs current information. 🔍

