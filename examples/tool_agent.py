"""
Tool-Enabled Agent Example using Google ADK

This example demonstrates how to create an agent with custom tools.
"""

import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any

# Setup compatibility fixes (handles Python 3.9 issues)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

import google.generativeai as genai

# Load environment variables from the parent directory (where .env should be)
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()  # Also try current directory

# Configure the Gemini API
api_key = os.getenv("GEMINI_API_KEY")

# Validate API key
if not api_key or api_key == "your_api_key_here" or api_key.strip() == "":
    print("\n❌ ERROR: GEMINI_API_KEY not set or is placeholder!")
    print("\nTo fix this:")
    print("1. Run: python setup_api_key.py")
    print("2. Or edit .env file and add your API key")
    print("3. Get your API key from: https://aistudio.google.com/")
    raise ValueError("GEMINI_API_KEY not set correctly.")

try:
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"\n❌ ERROR: Failed to configure Gemini API: {str(e)}")
    print("Get a valid API key from: https://aistudio.google.com/")
    raise

# Custom tools for the agent
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        # Only allow safe mathematical operations
        allowed_chars = set("0123456789+-*/()., ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

def web_search(query: str, num_results: int = 5) -> str:
    """Search the web for information. Returns search results summary.
    
    Note: This uses DuckDuckGo search. For production, consider using:
    - Google Custom Search API (requires API key)
    - SerpAPI (requires API key)
    - Bing Search API (requires API key)
    """
    try:
        # Try to use DuckDuckGo (no API key required)
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                
                if not results:
                    return f"No search results found for: {query}"
                
                summary = f"Search results for '{query}':\n\n"
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'No title')
                    snippet = result.get('body', 'No description')
                    url = result.get('href', 'No URL')
                    summary += f"{i}. {title}\n   {snippet[:150]}...\n   URL: {url}\n\n"
                
                return summary.strip()
        except ImportError:
            # Fallback: Use requests to DuckDuckGo HTML (simpler but less reliable)
            import requests
            from urllib.parse import quote
            
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    return f"Web search performed for: {query}\n[Note: Install 'duckduckgo-search' package for better results: pip install duckduckgo-search]"
                else:
                    return f"Search completed for: {query} (Status: {response.status_code})"
            except Exception as e:
                return f"Web search attempted for: {query}\n[Error: {str(e)}. Install 'duckduckgo-search' for better results: pip install duckduckgo-search]"
    except Exception as e:
        return f"Error performing web search: {str(e)}"

def get_weather(location: str) -> str:
    """Get current weather information for a location.
    
    Note: This is a placeholder. For production, use:
    - OpenWeatherMap API (requires API key)
    - WeatherAPI (requires API key)
    """
    # Placeholder implementation
    # In production, integrate with a weather API like OpenWeatherMap
    return f"Weather information for {location}:\n" \
           f"- Temperature: [Use weather API to get real data]\n" \
           f"- Condition: [Use weather API to get real data]\n" \
           f"- Humidity: [Use weather API to get real data]\n\n" \
           f"To enable real weather data, integrate with OpenWeatherMap API or similar service."

def get_current_time(timezone: str = "UTC") -> str:
    """Get the current date and time for a specified timezone.
    
    Args:
        timezone: Timezone name (e.g., 'UTC', 'America/New_York', 'Asia/Tokyo')
    """
    try:
        from datetime import datetime
        import pytz
        
        if timezone == "UTC":
            tz = pytz.UTC
        else:
            try:
                tz = pytz.timezone(timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                tz = pytz.UTC
                now = datetime.now(tz)
                return f"Unknown timezone '{timezone}'. Using UTC instead.\n" \
                       f"Current time in UTC:\n" \
                       f"- Date: {now.strftime('%Y-%m-%d')}\n" \
                       f"- Time: {now.strftime('%H:%M:%S')}\n" \
                       f"- Day: {now.strftime('%A')}\n" \
                       f"- Full: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        
        now = datetime.now(tz)
        return f"Current time in {timezone}:\n" \
               f"- Date: {now.strftime('%Y-%m-%d')}\n" \
               f"- Time: {now.strftime('%H:%M:%S')}\n" \
               f"- Day: {now.strftime('%A')}\n" \
               f"- Full: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    except ImportError:
        # Fallback without pytz
        from datetime import datetime
        now = datetime.now()
        return f"Current time (local):\n" \
               f"- Date: {now.strftime('%Y-%m-%d')}\n" \
               f"- Time: {now.strftime('%H:%M:%S')}\n" \
               f"- Day: {now.strftime('%A')}\n" \
               f"[Note: Install 'pytz' for timezone support: pip install pytz]"

def create_note(title: str, content: str) -> str:
    """Create and save a note with a title and content.
    
    Note: This is a simple in-memory storage. For production, use a database or file system.
    """
    # Simple in-memory storage (resets when program restarts)
    if not hasattr(create_note, 'notes'):
        create_note.notes = {}
    
    from datetime import datetime
    create_note.notes[title] = {
        'content': content,
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return f"Note created successfully!\n" \
           f"- Title: {title}\n" \
           f"- Content: {content[:100]}{'...' if len(content) > 100 else ''}\n" \
           f"- Total notes saved: {len(create_note.notes)}"

def get_note(title: str) -> str:
    """Retrieve a saved note by title."""
    if not hasattr(create_note, 'notes'):
        create_note.notes = {}
    
    if title in create_note.notes:
        note = create_note.notes[title]
        return f"Note: {title}\n" \
               f"Content: {note['content']}\n" \
               f"Created: {note.get('created', 'Unknown')}"
    else:
        available = list(create_note.notes.keys()) if create_note.notes else []
        return f"Note '{title}' not found.\n" \
               f"Available notes: {', '.join(available) if available else 'None'}"

# Tool definitions for Gemini
TOOLS = [
    {
        "function_declarations": [
            {
                "name": "calculator",
                "description": "Evaluate a mathematical expression. Input should be a valid Python expression.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for information on any topic. Use this when you need current information, facts, or data from the internet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query or question to search for on the web"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of search results to return (default: 5, max: 10)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get current weather information for a specific location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location name (e.g., 'New York', 'London', 'Tokyo')"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get the current date and time for a specified timezone. Useful for scheduling, reminders, or time-sensitive queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone name (e.g., 'UTC', 'America/New_York', 'Asia/Tokyo', 'Europe/London'). Default is UTC if not provided."
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "create_note",
                "description": "Create and save a note with a title and content. Useful for reminders, to-do items, or storing information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title or name of the note"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content or body of the note"
                        }
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "get_note",
                "description": "Retrieve a previously saved note by its title.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the note to retrieve"
                        }
                    },
                    "required": ["title"]
                }
            }
        ]
    }
]

# Tool execution mapping
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "web_search": web_search,
    "get_weather": get_weather,
    "get_current_time": get_current_time,
    "create_note": create_note,
    "get_note": get_note,
}

def create_tool_agent():
    """Create an agent with tools."""
    # Use model from env or default to gemini-2.5
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5")
    
    model = genai.GenerativeModel(
        model_name=model_name,
        tools=TOOLS,
        system_instruction="""You are a helpful personal assistant with access to various tools.
        
        You can help users with:
        - Calculations using the calculator tool
        - Web searches for current information, facts, or data
        - Weather information for any location
        - Current date and time for any timezone
        - Creating and retrieving notes/reminders
        
        When a user asks for:
        - Math calculations → use calculator tool
        - Current information, facts, or web data → use web_search tool
        - Weather updates → use get_weather tool
        - Date/time information → use get_current_time tool
        - Saving information or reminders → use create_note tool
        - Retrieving saved information → use get_note tool
        
        Always explain what you're doing and provide helpful, clear responses."""
    )
    return model

def execute_tool(function_name: str, args: Dict[str, Any]) -> str:
    """Execute a tool function."""
    if function_name in TOOL_FUNCTIONS:
        func = TOOL_FUNCTIONS[function_name]
        try:
            # Handle optional parameters with defaults
            if function_name == "web_search" and "num_results" not in args:
                args["num_results"] = 5
            elif function_name == "get_current_time" and "timezone" not in args:
                args["timezone"] = "UTC"
            
            return func(**args)
        except TypeError as e:
            # Handle missing required arguments gracefully
            return f"Error executing {function_name}: {str(e)}"
    return f"Error: Tool '{function_name}' not found"

def print_debug_info(step_name, data, debug_mode=False):
    """Print debugging information if debug mode is enabled."""
    if not debug_mode:
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 DEBUG: {step_name}")
    print(f"{'='*60}")
    if isinstance(data, dict):
        import json
        print(json.dumps(data, indent=2, default=str))
    else:
        print(str(data))
    print(f"{'='*60}\n")

def run_tool_agent_interactive(debug=False):
    """Run the tool-enabled agent in interactive mode.
    
    Args:
        debug: If True, show detailed debugging information about tool usage
    """
    agent = create_tool_agent()
    conversation_history = []
    
    print("🤖 Personal Assistant Agent")
    print("=" * 50)
    print("Available tools: calculator, web_search, get_weather, get_current_time, create_note, get_note")
    if debug:
        print("🐛 DEBUG MODE: Detailed tool usage will be shown")
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'debug' to toggle debug mode")
    print("Type 'history' to see conversation history\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if user_input.lower() == 'debug':
            debug = not debug
            print(f"\n🐛 Debug mode: {'ON' if debug else 'OFF'}\n")
            continue
        
        if user_input.lower() == 'history':
            print("\n📜 Conversation History:")
            print("=" * 50)
            for i, msg in enumerate(conversation_history, 1):
                role = msg.get('role', 'unknown')
                parts = msg.get('parts', [])
                print(f"\n{i}. [{role.upper()}]")
                for part in parts:
                    if isinstance(part, str):
                        print(f"   Text: {part[:100]}...")
                    elif isinstance(part, dict):
                        if 'function_call' in part:
                            fc = part['function_call']
                            print(f"   Function Call: {fc.name}")
                            print(f"   Args: {dict(fc.args)}")
                        elif 'function_response' in part:
                            fr = part['function_response']
                            print(f"   Function Response: {fr.get('name', 'unknown')}")
                            print(f"   Result: {str(fr.get('response', {}))[:100]}...")
            print("\n")
            continue
        
        if not user_input:
            continue
        
        try:
            # Add user message to conversation
            user_msg = {"role": "user", "parts": [user_input]}
            conversation_history.append(user_msg)
            
            if debug:
                print(f"\n📤 Sending to model:")
                print(f"   User: {user_input}")
                print_debug_info("Conversation History Before Request", conversation_history, debug)
            
            # Generate response
            response = agent.generate_content(conversation_history)
            
            if debug:
                print(f"\n📥 Raw Response from Model:")
                print(f"   Response type: {type(response)}")
                print(f"   Candidates: {len(response.candidates)}")
                print_debug_info("Response Object", {
                    "candidates_count": len(response.candidates),
                    "first_candidate_parts": [str(p) for p in response.candidates[0].content.parts[:3]]
                }, debug)
            
            # Check for function calls in response
            function_call = None
            text_parts = []
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    if debug:
                        print(f"\n🔧 FUNCTION CALL DETECTED!")
                        print(f"   Function: {function_call.name}")
                        print(f"   Arguments: {dict(function_call.args)}")
                elif hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            if function_call:
                # Execute function call
                function_name = function_call.name
                args = dict(function_call.args)
                
                print(f"\n{'='*60}")
                print(f"🔧 TOOL EXECUTION")
                print(f"{'='*60}")
                print(f"Tool: {function_name}")
                print(f"Arguments: {args}")
                print(f"{'='*60}")
                
                # Execute the tool
                tool_result = execute_tool(function_name, args)
                print(f"✅ Tool Result: {tool_result}")
                print(f"{'='*60}\n")
                
                # Add model's function call to conversation
                model_function_msg = {
                    "role": "model",
                    "parts": [{"function_call": function_call}]
                }
                conversation_history.append(model_function_msg)
                
                if debug:
                    print_debug_info("Added Function Call to History", model_function_msg, debug)
                
                # Add function response to conversation
                function_response_msg = {
                    "role": "function",
                    "parts": [{
                        "function_response": {
                            "name": function_name,
                            "response": {"result": tool_result}
                        }
                    }]
                }
                conversation_history.append(function_response_msg)
                
                if debug:
                    print_debug_info("Added Function Response to History", function_response_msg, debug)
                    print(f"\n🔄 Sending tool result back to model for final response...")
                
                # Get final response with tool result
                final_response = agent.generate_content(conversation_history)
                
                if debug:
                    print(f"\n📥 Final Response from Model:")
                    print(f"   Has text: {hasattr(final_response, 'text')}")
                    if hasattr(final_response, 'text'):
                        print(f"   Text length: {len(final_response.text)}")
                
                # Add final response to conversation
                final_text = final_response.text if hasattr(final_response, 'text') else ""
                final_model_msg = {
                    "role": "model",
                    "parts": [final_text] if final_text else []
                }
                conversation_history.append(final_model_msg)
                
                print(f"\n💬 Agent: {final_text}\n")
                
                if debug:
                    print_debug_info("Final Conversation State", conversation_history[-3:], debug)
            else:
                # Regular text response (no function calls)
                response_text = " ".join(text_parts) if text_parts else (response.text if hasattr(response, 'text') else "")
                
                if debug:
                    print(f"\n📝 TEXT RESPONSE (No tools used)")
                    print(f"   Response: {response_text[:200]}...")
                
                model_msg = {
                    "role": "model",
                    "parts": [response_text] if response_text else []
                }
                conversation_history.append(model_msg)
                print(f"\n💬 Agent: {response_text}\n")
                
        except Exception as e:
            error_msg = str(e)
            if "function_call" in error_msg.lower() or "could not convert" in error_msg.lower():
                print(f"\n⚠️  Error: Model returned a function call but couldn't process it.")
                print(f"   Details: {error_msg}")
                print("   Try rephrasing your query.\n")
            else:
                print(f"\nError: {error_msg}\n")

if __name__ == "__main__":
    import sys
    # Enable debug mode with --debug flag
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    run_tool_agent_interactive(debug=debug_mode)

