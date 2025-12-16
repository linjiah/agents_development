# Quick Start Guide

Get up and running with Google ADK agents in 5 minutes!

## Step 1: Setup Environment

```bash
# Navigate to the agents_adk directory
cd /Users/linjia/cursor_ai_space/interview_preparation/ai_ml_interviews/machine_learning/agents_adk

# Activate your virtual environment (if using one)
source /Users/linjia/cursor_ai_space/interview_preparation/ml_interview_env/bin/activate

# Run the setup script
./setup.sh
```

Or manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
EOF
```

## Step 2: Get API Key

### Option A: Use the Setup Script (Easiest)

```bash
python setup_api_key.py
```

This interactive script will guide you through setting up your API key.

### Option B: Manual Setup

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy your API key
5. Edit the `.env` file and replace `your_api_key_here` with your actual key:
   ```bash
   GEMINI_API_KEY=your_actual_key_here
   ```

## Step 3: Run Your First Agent

### Option A: Simple Python Agent

```bash
python examples/simple_agent.py
```

Then type your questions interactively!

### Option B: Single Query

```bash
python examples/simple_agent.py "What is machine learning?"
```

### Option C: Tool-Enabled Agent

```bash
python examples/tool_agent.py
```

Try asking:
- "Calculate 25 * 4"
- "Get me a medium LeetCode problem"

### Option D: Multi-Agent System

```bash
python examples/multi_agent.py
```

Try:
- "Explain binary search algorithm" (routes to Technical Agent)
- "Tell me about a time you led a team" (routes to Behavioral Agent)
- "collaborate What makes a good system design?" (uses multiple agents)

## Step 4: Use ADK CLI (Advanced)

If you have `google-adk` installed with CLI support:

```bash
# Create a new agent configuration
adk create --type=config my_agent

# Edit my_agent/root_agent.yaml
# Add your API key to my_agent/.env

# Run the agent
adk run my_agent
```

## Example Interactions

### Simple Agent
```
You: What is the time complexity of quicksort?
Agent: Quicksort has an average time complexity of O(n log n)...
```

### Tool Agent
```
You: Calculate 15 * 23
Agent: 🔧 Calling tool: calculator with args: {'expression': '15 * 23'}
Tool result: 345
Agent: The result of 15 * 23 is 345.
```

### Multi-Agent
```
You: Explain how to implement a hash table
Agent: [Technical Agent response with detailed explanation]
```

## Troubleshooting

### "API key not valid" or "API_KEY_INVALID"
This means your API key is either:
- Not set (still has placeholder `your_api_key_here`)
- Invalid or expired
- Doesn't have proper permissions

**Solution:**
```bash
# Run the setup script
python setup_api_key.py

# Or manually edit .env file
# Make sure GEMINI_API_KEY=your_actual_key_here (not the placeholder)
```

Get a new API key from: https://aistudio.google.com/

### "GEMINI_API_KEY not found"
- Make sure you created the `.env` file
- Check that the API key is set correctly
- Verify the key is valid at [Google AI Studio](https://aistudio.google.com/)

### "Module not found"
- Make sure you installed dependencies: `pip install -r requirements.txt`
- Check that you're in the correct virtual environment

### Python Version Warnings
If you see warnings about Python 3.9 being past end of life:
- These are just warnings and won't prevent the code from running
- The code works with Python 3.9, but Python 3.10+ is recommended

### "Rate limit exceeded"
- You may have hit API rate limits
- Wait a few minutes and try again
- Consider upgrading your API plan

## Next Steps

1. **Explore Examples**: Check out all examples in `examples/` directory
2. **Create Custom Agents**: Edit YAML files in `agents/` directory
3. **Add Tools**: Create new tools in `tools/` directory
4. **Build Multi-Agent Systems**: Combine multiple agents for complex tasks

## Resources

- [Full README](README.md)
- [Google ADK Docs](https://google.github.io/adk-docs/)
- [Gemini API Docs](https://ai.google.dev/docs)

Happy agent building! 🚀

