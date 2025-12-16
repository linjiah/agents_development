"""
Simple Agent Example using Google ADK

This example demonstrates how to create and run a basic agent using Google ADK.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Setup compatibility fixes (handles Python 3.9 issues)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

import google.generativeai as genai

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()

# Configure API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("❌ ERROR: GEMINI_API_KEY not set. Get your key from: https://aistudio.google.com/")
    sys.exit(1)

genai.configure(api_key=api_key)

# System instruction for the agent
SYSTEM_INSTRUCTION = """You are a helpful AI assistant specialized in interview preparation.
Your capabilities include:
- Answering technical questions about machine learning, AI, and software engineering
- Explaining algorithms and data structures
- Helping with system design concepts
- Providing coding practice problems and solutions

Always be clear, concise, and provide examples when helpful."""

def create_agent():
    """Create an agent with automatic model fallback."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5")
    fallback_models = ["gemini-2.5", "gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
    
    for model in [model_name] + [m for m in fallback_models if m != model_name]:
        try:
            return genai.GenerativeModel(model_name=model, system_instruction=SYSTEM_INSTRUCTION)
        except Exception:
            continue
    
    raise ValueError(f"Could not create model. Tried: {', '.join([model_name] + fallback_models)}")

def generate_with_retry(agent, conversation_history, max_retries=3):
    """Generate response with automatic retry on rate limits."""
    for attempt in range(max_retries):
        try:
            response = agent.generate_content(conversation_history)
            return response.text
        except Exception as e:
            error_msg = str(e).lower()
            is_rate_limit = "429" in str(e) or "quota" in error_msg or "rate limit" in error_msg
            
            if is_rate_limit and attempt < max_retries - 1:
                wait_time = min(2.0 * (2 ** attempt), 60.0)
                print(f"⚠️  Rate limit. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                raise

def run_interactive():
    """Run the agent in interactive mode."""
    agent = create_agent()
    history = []
    
    print("🤖 Interview Prep Agent")
    print("=" * 50)
    print("Type 'quit' or 'exit' to end\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye! Good luck with your interview preparation!")
            break
        
        if not user_input:
            continue
        
        try:
            history.append({"role": "user", "parts": [user_input]})
            response_text = generate_with_retry(agent, history)
            history.append({"role": "model", "parts": [response_text]})
            print(f"\nAgent: {response_text}\n")
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                print(f"\n⚠️  Rate limit exceeded. Wait a minute and try again.")
                print("   Check usage: https://ai.dev/usage?tab=rate-limit\n")
            elif "API key" in error_msg:
                print(f"\n❌ API key error. Check your .env file.\n")
            else:
                print(f"\nError: {error_msg}\n")

def run_single_query(query: str):
    """Run the agent with a single query."""
    agent = create_agent()
    try:
        response = agent.generate_content(query)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        print(f"Response: {run_single_query(query)}")
    else:
        run_interactive()
