# Debugging Guide for Google ADK Agents

This guide shows you how to debug and inspect agent behavior, especially tool usage.

## Quick Start

### Enable Debug Mode

Run the tool agent with debug mode enabled:

```bash
python examples/tool_agent.py --debug
# or
python examples/tool_agent.py -d
```

### Toggle Debug Mode During Conversation

While the agent is running, type:
- `debug` - Toggle debug mode on/off
- `history` - View the full conversation history

## What Debug Mode Shows

### 1. **Tool Detection**
When the model decides to use a tool, you'll see:
```
🔧 FUNCTION CALL DETECTED!
   Function: get_leetcode_problem
   Arguments: {'difficulty': 'medium'}
```

### 2. **Tool Execution**
Detailed information about tool execution:
```
============================================================
🔧 TOOL EXECUTION
============================================================
Tool: get_leetcode_problem
Arguments: {'difficulty': 'medium'}
============================================================
✅ Tool Result: Longest Substring Without Repeating Characters...
============================================================
```

### 3. **Conversation Flow**
Shows the conversation history being built:
- User messages
- Model function calls
- Function responses
- Final model responses

### 4. **Raw Response Inspection**
See the raw response structure from the model:
- Response type
- Number of candidates
- Parts breakdown

## Example Debug Output

```
You: get me a medium LeetCode problem

📤 Sending to model:
   User: get me a medium LeetCode problem

============================================================
🔍 DEBUG: Conversation History Before Request
============================================================
[
  {
    "role": "user",
    "parts": ["get me a medium LeetCode problem"]
  }
]
============================================================

📥 Raw Response from Model:
   Response type: <class 'google.generativeai.types.GenerateContentResponse'>
   Candidates: 1

🔧 FUNCTION CALL DETECTED!
   Function: get_leetcode_problem
   Arguments: {'difficulty': 'medium'}

============================================================
🔧 TOOL EXECUTION
============================================================
Tool: get_leetcode_problem
Arguments: {'difficulty': 'medium'}
============================================================
✅ Tool Result: Longest Substring Without Repeating Characters - Find the length...
============================================================

🔄 Sending tool result back to model for final response...

📥 Final Response from Model:
   Has text: True
   Text length: 245

💬 Agent: Here's a medium LeetCode problem for you: Longest Substring...
```

## Understanding the Flow

### Step 1: User Input
```
User: "Calculate 25 * 4"
```

### Step 2: Model Decides to Use Tool
```
Model thinks: "I need to calculate, so I'll use the calculator tool"
→ Returns function_call instead of text
```

### Step 3: Tool Execution
```
Function: calculator
Arguments: {'expression': '25 * 4'}
Result: '100'
```

### Step 4: Model Gets Tool Result
```
Model receives: "Tool result: 100"
Model thinks: "The calculation result is 100"
→ Returns final text response
```

### Step 5: Final Response
```
Agent: "The result of 25 * 4 is 100."
```

## Conversation History Structure

The conversation history follows this pattern:

```python
[
    {"role": "user", "parts": ["user message"]},
    {"role": "model", "parts": [{"function_call": {...}}]},  # Model wants to use tool
    {"role": "function", "parts": [{"function_response": {...}}]},  # Tool result
    {"role": "model", "parts": ["final response text"]}  # Model's final answer
]
```

## Commands

| Command | Description |
|---------|-------------|
| `debug` | Toggle debug mode on/off |
| `history` | Show full conversation history |
| `quit` / `exit` | End the conversation |

## Tips for Debugging

1. **Start with Debug Mode**: Always start with `--debug` to see what's happening
2. **Check Tool Arguments**: Verify the arguments passed to tools are correct
3. **Inspect Tool Results**: Make sure tools return expected results
4. **Watch Conversation History**: Use `history` command to see the full flow
5. **Compare with Expected**: Check if the model is using tools when you expect it to

## Common Issues

### Tool Not Being Called

If the model isn't using a tool when you expect it to:
- Check tool descriptions are clear
- Verify tool names match exactly
- Ensure the user query clearly indicates tool usage is needed

### Tool Called with Wrong Arguments

If arguments are incorrect:
- Review tool parameter descriptions
- Check enum values if using enums
- Verify required vs optional parameters

### Function Call Error

If you see "Could not convert `part.function_call` to text":
- The code now handles this automatically
- Check that function responses are properly formatted
- Verify conversation history structure

## Advanced Debugging

### View Raw API Responses

In debug mode, you can see:
- Raw response objects
- Response candidates
- Part types (text vs function_call)

### Inspect Tool Definitions

Check the tool definitions in the code:
```python
TOOLS = [
    {
        "function_declarations": [
            {
                "name": "calculator",
                "description": "...",
                "parameters": {...}
            }
        ]
    }
]
```

### Monitor Conversation State

Use the `history` command to see how the conversation evolves:
- Each turn adds to the history
- Function calls are preserved
- Tool results are stored
- Final responses complete the cycle

## Example Session

```bash
$ python examples/tool_agent.py --debug

🤖 Tool-Enabled Interview Prep Agent
==================================================
Available tools: calculator, get_leetcode_problem
🐛 DEBUG MODE: Detailed tool usage will be shown
Type 'quit' or 'exit' to end the conversation
Type 'debug' to toggle debug mode
Type 'history' to see conversation history

You: calculate 10 * 5

📤 Sending to model:
   User: calculate 10 * 5

🔧 FUNCTION CALL DETECTED!
   Function: calculator
   Arguments: {'expression': '10 * 5'}

============================================================
🔧 TOOL EXECUTION
============================================================
Tool: calculator
Arguments: {'expression': '10 * 5'}
============================================================
✅ Tool Result: 50
============================================================

💬 Agent: The result of 10 * 5 is 50.

You: history

📜 Conversation History:
==================================================

1. [USER]
   Text: calculate 10 * 5

2. [MODEL]
   Function Call: calculator
   Args: {'expression': '10 * 5'}

3. [FUNCTION]
   Function Response: calculator
   Result: {'result': '50'}

4. [MODEL]
   Text: The result of 10 * 5 is 50.
```

This gives you complete visibility into how the agent uses tools!

