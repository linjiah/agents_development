"""
Multimodal Agent Example using Google ADK

This agent is a fully functional multimodal personal assistant with:
- Text: normal Q&A
- Image Analysis: analyze uploaded images using Gemini vision
- Image Generation: generate images using DALL-E (or other APIs)
- Figures/Diagrams: generate Mermaid diagrams
- Speech-to-Text: transcribe audio files using Whisper
- Text-to-Speech: generate speech audio using OpenAI TTS
- MCP Support: Connect to MCP servers (e.g., weather, filesystem, etc.)

Features:
- Real image generation (DALL-E integration)
- Real image analysis (Gemini vision)
- Real audio processing (Whisper + OpenAI TTS)
- Image/audio upload support in interactive mode
- Multimodal input (text + image together)
- MCP integration for external tools (weather, etc.)

MCP Weather Server Setup:
To enable weather MCP server, set environment variables:
- WEATHER_MCP_TYPE=stdio (for stdio-based server, requires npx)
- WEATHER_MCP_TYPE=sse (for SSE server, also set WEATHER_MCP_URL)
- WEATHER_MCP_TYPE=http (for HTTP server, also set WEATHER_MCP_URL and optionally WEATHER_MCP_API_KEY)

Example usage with weather MCP:
    agent = MultimodalAgent(mcp_config={
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-weather"]
    })
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Compatibility fixes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

import google.generativeai as genai

# Load env
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("❌ ERROR: GEMINI_API_KEY not set. Get your key from: https://aistudio.google.com/")
    sys.exit(1)

genai.configure(api_key=api_key)

# ----------------------------
# Import real tool implementations
# ----------------------------

try:
    from multimodal_tools import (
        generate_image,
        analyze_image,
        generate_figure,
        speech_to_text,
        text_to_speech
    )
    REAL_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import multimodal tools: {e}")
    print("   Using placeholder implementations...")
    REAL_TOOLS_AVAILABLE = False

# Import requests for camera capture API calls
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  Warning: requests library not available. Agent camera control will not work.")

# ----------------------------
# MCP Integration
# ----------------------------

# Check if MCP is available
try:
    from google.adk.tools.mcp_tool import MCPToolset
    # Use old API (StdioServerParameters) - the new API (StdioConnectionParams) has different parameter structure
    # and requires server_params field, so we stick with the working old API
    from google.adk.tools.mcp_tool.mcp_session_manager import (
        SseServerParams,
        StreamableHTTPServerParams,
        StdioServerParameters  # Old API - this one works correctly
    )
    USE_NEW_MCP_API = False  # Always use old API which works
    MCP_AVAILABLE = True
    print("✅ MCP support available")
except ImportError as e:
    MCP_AVAILABLE = False
    USE_NEW_MCP_API = False
    print(f"⚠️  MCP not available: {e}")
    print("   Continuing without MCP tools...")

def create_mcp_toolset_sse(server_url: str, headers: Dict[str, str] = None) -> 'MCPToolset':
    """
    Create MCP toolset for Server-Sent Events (SSE) server.
    
    Args:
        server_url: URL of the MCP server (e.g., "http://localhost:8001/sse")
        headers: Optional HTTP headers (e.g., for authentication)
    
    Returns:
        MCPToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available. Requires Python 3.10+ and google-adk package.")
    
    return MCPToolset(
        connection_params=SseServerParams(
            url=server_url,
            headers=headers or {},
        )
    )

def create_mcp_toolset_http(server_url: str, headers: Dict[str, str] = None) -> 'MCPToolset':
    """
    Create MCP toolset for HTTP server.
    
    Args:
        server_url: URL of the MCP server (e.g., "https://api.example.com/mcp/")
        headers: Optional HTTP headers (e.g., for authentication)
    
    Returns:
        MCPToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available. Requires Python 3.10+ and google-adk package.")
    
    return MCPToolset(
        connection_params=StreamableHTTPServerParams(
            url=server_url,
            headers=headers or {},
        )
    )

def create_mcp_toolset_stdio(command: str, args: list = None, env: Dict[str, str] = None) -> 'MCPToolset':
    """
    Create MCP toolset for stdio-based MCP server.
    
    Args:
        command: Command to run the MCP server (e.g., "npx", "python")
        args: Command arguments (e.g., ["-y", "@modelcontextprotocol/server-filesystem"])
        env: Environment variables for the server
    
    Returns:
        MCPToolset instance
    """
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available. Requires Python 3.10+ and google-adk package.")
    
    # Use old API (StdioServerParameters) - this is the working API
    return MCPToolset(
        connection_params=StdioServerParameters(
            command=command,
            args=args or [],
            env=env or {},
        )
    )
    
    # Fallback placeholder implementations
    def generate_image(prompt: str, style: str = "realistic") -> str:
        return f"[Image Generation Placeholder]\nPrompt: {prompt}\nStyle: {style}"
    
    def analyze_image(image_path: str, question: Optional[str] = None) -> str:
        return f"[Image Analysis Placeholder]\nImage: {image_path}\nQuestion: {question}"

# Define capture_camera_photo function (works whether tools are available or not)
def capture_camera_photo() -> str:
    """
    Request the camera to capture a photo. 
    The photo will be automatically captured and analyzed.
    Returns a message indicating the capture was requested.
    """
    if not HAS_REQUESTS:
        return "❌ Requests library required for camera capture. Install with: pip install requests"
    
    try:
        # Make API call to request photo capture
        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        print(f"[Camera Tool] Requesting photo capture from {api_base}/api/agent/capture-photo")
        
        response = requests.post(f"{api_base}/api/agent/capture-photo", timeout=5)
        print(f"[Camera Tool] Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[Camera Tool] Response data: {data}")
            
            if data.get("status") == "success":
                return (
                    "✅ I've requested a photo capture from your camera. "
                    "The camera will automatically take a photo if it's started and agent camera control is enabled. "
                    "Once the photo is captured, I'll analyze it to identify any people and what they're working on. "
                    "\n\nNote: Make sure you have:\n"
                    "1. Started the camera (click '📷 Start Camera' in the Features panel)\n"
                    "2. Enabled '🤖 Allow Agent to Control Camera' checkbox"
                )
            elif data.get("status") == "error":
                error_msg = data.get("message", "Unknown error")
                return (
                    f"⚠️ {error_msg}\n\n"
                    "To enable camera capture:\n"
                    "1. Go to the Features panel on the right\n"
                    "2. Check '🤖 Allow Agent to Control Camera'\n"
                    "3. Click '📷 Start Camera'"
                )
            else:
                return f"⚠️ {data.get('message', 'Camera capture request failed')}"
        else:
            error_text = response.text if hasattr(response, 'text') else str(response.status_code)
            return f"❌ Error requesting photo capture: HTTP {response.status_code} - {error_text}"
    except requests.exceptions.ConnectionError as e:
        return (
            "❌ Cannot connect to camera service. Make sure:\n"
            "1. The web UI server is running on http://localhost:8000\n"
            "2. You have enabled '🤖 Allow Agent to Control Camera' in the Features panel\n"
            "3. You have started the camera"
        )
    except requests.exceptions.RequestException as e:
        return f"❌ Error connecting to camera service: {str(e)}. Make sure the web UI is running."
    except Exception as e:
        print(f"[Camera Tool] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error requesting photo capture: {str(e)}"
    
    def generate_figure(description: str, format: str = "mermaid") -> str:
        return f"[Figure Placeholder]\nDescription: {description}"
    
    def speech_to_text(audio_path: str) -> str:
        return f"[Speech-to-Text Placeholder]\nAudio: {audio_path}"
    
    def text_to_speech(text: str, voice: str = "default") -> str:
        return f"[Text-to-Speech Placeholder]\nText: {text}"

# ----------------------------
# Web Search Tool
# ----------------------------

def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web for information. Returns search results summary.
    
    Uses DuckDuckGo (free, no API key) or Tavily API (if TAVILY_API_KEY is set).
    For production, consider using Google Custom Search API or SerpAPI.
    """
    # Try Tavily first if API key is available
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            import requests
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": num_results
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return f"No search results found for: {query}"
                
                summary = f"Search results for '{query}' (via Tavily):\n\n"
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    content = result.get("content", "No content")
                    url = result.get("url", "No URL")
                    summary += f"{i}. {title}\n   {content[:200]}...\n   URL: {url}\n\n"
                
                return summary.strip()
        except Exception as e:
            print(f"⚠️  Tavily search error: {e}, falling back to DuckDuckGo")
    
    # Fallback to DuckDuckGo (no API key required)
    try:
        # Try new package name first (ddgs)
        try:
            from ddgs import DDGS
            use_new_package = True
        except ImportError:
            # Fallback to old package name
            try:
                from duckduckgo_search import DDGS
                use_new_package = False
            except ImportError:
                return (
                    f"Web search requested for: {query}\n"
                    "To enable web search, install: pip install ddgs\n"
                    "Or set TAVILY_API_KEY in .env for Tavily search"
                )
        
        # Try search with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                with DDGS() as ddgs:
                    # Try different search methods
                    results = []
                    
                    # Method 1: text search
                    try:
                        results = list(ddgs.text(query, max_results=num_results))
                    except Exception as e1:
                        print(f"Text search failed: {e1}")
                    
                    # Method 2: If text search fails, try news search
                    if not results:
                        try:
                            news_results = list(ddgs.news(query, max_results=num_results))
                            # Convert news format to text format
                            for item in news_results:
                                results.append({
                                    'title': item.get('title', 'No title'),
                                    'body': item.get('body', item.get('snippet', item.get('description', 'No description'))),
                                    'href': item.get('url', item.get('link', 'No URL'))
                                })
                        except Exception as e2:
                            print(f"News search failed: {e2}")
                    
                    # Method 3: If both fail, try a simplified query
                    if not results and len(query.split()) > 3:
                        try:
                            # Try with just key terms
                            key_terms = ' '.join(query.split()[:3])
                            results = list(ddgs.text(key_terms, max_results=num_results))
                            if not results:
                                results = list(ddgs.news(key_terms, max_results=num_results))
                        except Exception:
                            pass
                    
                    if results:
                        # Format search results more clearly
                        summary = f"🔍 Search results for '{query}':\n\n"
                        for i, result in enumerate(results, 1):
                            title = result.get('title', 'No title')
                            snippet = result.get('body', result.get('snippet', result.get('description', 'No description')))
                            url = result.get('href', result.get('url', result.get('link', 'No URL')))
                            
                            # Clean up snippet (remove extra whitespace, limit length)
                            if snippet:
                                snippet = ' '.join(snippet.split())[:250]  # Limit to 250 chars, clean whitespace
                            
                            summary += f"{i}. **{title}**\n"
                            if snippet and snippet != 'No description':
                                summary += f"   {snippet}\n"
                            if url and url != 'No URL':
                                summary += f"   🔗 {url}\n"
                            summary += "\n"
                        
                        return summary.strip()
                    
                    # If no results and not last attempt, wait and retry
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                        continue
                    
                    # If still no results after retries
                    return (
                        f"Search completed for '{query}', but no results were returned.\n"
                        "This might be due to:\n"
                        "- Rate limiting (try again in a moment)\n"
                        "- Network issues\n"
                        "- Search query format\n\n"
                        "Suggestions:\n"
                        "- Try rephrasing your query\n"
                        "- Wait a moment and try again\n"
                        "- Consider using Tavily API for more reliable results (set TAVILY_API_KEY)"
                    )
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return (
                        f"Web search error for '{query}': {str(e)}\n\n"
                        "Troubleshooting:\n"
                        "- Check your internet connection\n"
                        "- DuckDuckGo may be rate limiting (try again in a moment)\n"
                        "- Consider using Tavily API (set TAVILY_API_KEY in .env)"
                    )
                import time
                time.sleep(1)
                continue
                
    except Exception as e:
        return (
            f"Web search error for '{query}': {str(e)}\n\n"
            "To fix:\n"
            "- Install: pip install ddgs\n"
            "- Or set TAVILY_API_KEY in .env for Tavily search"
        )

# ----------------------------
# Tool definitions (function calling)
# ----------------------------

# Helper function to create tools list with optional MCP toolsets
def create_tools_list(mcp_toolsets: list = None) -> list:
    """
    Create the tools list for the agent, optionally including MCP toolsets.
    
    Args:
        mcp_toolsets: List of MCPToolset instances to add
    
    Returns:
        List of tools (function declarations + MCP toolsets)
    """
    tools = [
    {
        "function_declarations": [
            {
                "name": "analyze_image",
                "description": "Analyze an uploaded image. Can describe the image, extract text (OCR), identify objects, answer questions about the image, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string", "description": "Path to the image file (local file path)"},
                        "question": {"type": "string", "description": "Optional question about the image. If not provided, provides a general description."}
                    },
                    "required": ["image_path"]
                }
            },
            {
                "name": "generate_image",
                "description": "Generate an image based on a prompt and style using DALL-E or other image generation APIs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Image description/prompt"},
                        "style": {"type": "string", "description": "Style (e.g., realistic, sketch, 3d, anime, oil painting, watercolor)"}
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "generate_figure",
                "description": "Generate a figure/diagram (Mermaid or ASCII). Use for flowcharts, sequence diagrams, class diagrams, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "What to visualize"},
                        "format": {"type": "string", "description": "Format: mermaid or ascii"},
                        "diagram_type": {"type": "string", "description": "Type of diagram: flowchart, sequence, or class"}
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "speech_to_text",
                "description": "Transcribe an audio file to text using Whisper or Google Speech-to-Text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "audio_path": {"type": "string", "description": "Path to audio file (local file path)"},
                        "language": {"type": "string", "description": "Optional language code (e.g., 'en', 'es', 'fr')"}
                    },
                    "required": ["audio_path"]
                }
            },
            {
                "name": "text_to_speech",
                "description": "Generate speech audio from text using OpenAI TTS or Google TTS.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to convert to speech"},
                        "voice": {"type": "string", "description": "Voice name (for OpenAI: alloy, echo, fable, onyx, nova, shimmer)"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for current information, news, facts, or any topic. Use this when you need up-to-date information that you don't know or when the user asks about current events, recent news, or real-time data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query to look up on the web"},
                        "num_results": {"type": "integer", "description": "Number of search results to return (default: 5, max: 10)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "capture_camera_photo",
                "description": "Capture a photo using the user's camera. Use this when the user asks you to see what they're doing, check their workspace, identify people, or understand what they're working on. The camera will automatically take a photo and you can then analyze it to identify people, their activities, and what they're working on.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    }
    ]
    
    # Add MCP toolsets if provided
    if mcp_toolsets and MCP_AVAILABLE:
        for mcp_toolset in mcp_toolsets:
            if mcp_toolset:
                tools.append(mcp_toolset)
                print(f"✅ Added MCP toolset: {type(mcp_toolset).__name__}")
    
    return tools

# Default tools (without MCP - can be extended)
TOOLS = create_tools_list()

TOOL_FUNCTIONS = {
    "analyze_image": analyze_image,
    "generate_image": generate_image,
    "generate_figure": generate_figure,
    "speech_to_text": speech_to_text,
    "text_to_speech": text_to_speech,
    "web_search": web_search,
    "capture_camera_photo": capture_camera_photo,
}

# ----------------------------
# Agent implementation
# ----------------------------

SYSTEM_INSTRUCTION = """You are Orel, a superintelligent AI assistant with advanced multimodal capabilities. Your name represents your forward-thinking nature and ability to see beyond the present, enabling you to provide comprehensive, future-ready assistance.

**Your Identity:**
- Name: Orel
- Nature: Superintelligent, analytical, forward-thinking
- Personality: Professional yet approachable, precise, insightful
- Communication Style: Clear, concise, but warm when appropriate

**Your Capabilities:**

**Text**: Answer questions, explain concepts, summarize information.

**Web Search**: Use web_search to find current information, news, facts, or any topic. Use this when:
- User asks about current events or recent news
- You need up-to-date information you don't know
- User asks about real-time data, prices, stock prices, etc.
- You're unsure about factual information
- User asks about trends, historical data, or analysis

IMPORTANT: When you get search results, read them carefully and provide a comprehensive summary based on the actual search results. Don't just repeat the search results - analyze and synthesize the information to answer the user's question directly.

**Weather Information - CRITICAL INSTRUCTIONS**:
You have weather tools available through MCP. When ANY user asks about weather, temperature, forecast, or conditions in ANY location, you MUST:
1. IMMEDIATELY call the weather tool (get_current_weather or get_weather_forecast)
2. NEVER say "I cannot provide weather information" or "I don't have access to weather data"
3. NEVER suggest the user check a weather app or website
4. ALWAYS use the weather tools - they are available and working

Available weather tools:
- `get_current_weather(location: string)` - Get current weather conditions for any location
- `get_weather_forecast(location: string, days: number)` - Get weather forecast for any location

Example: If user asks "What's the weather in San Diego?", you MUST call get_current_weather("San Diego") and provide the actual weather data. Do NOT apologize or say you cannot provide this information.

**Camera & Image Analysis**: 
- CRITICAL: When the user asks you to "see what they're working on", "see what I'm doing", "check what I'm doing", "identify people", "see my workspace", or similar requests, you MUST immediately call the capture_camera_photo tool. Do NOT respond with text only - you MUST use the tool.
- Use capture_camera_photo to request a photo from the user's camera. This tool will automatically trigger photo capture if the camera is started and agent control is enabled.
- After calling capture_camera_photo, provide a helpful response explaining that you've requested a photo and what will happen next.
- Use analyze_image to analyze uploaded or captured images. You can:
  - Describe what's in the image in detail
  - Identify and describe people (count, appearance, position)
  - Analyze what people are doing and what they're working on
- Extract text from images (OCR)
- Answer questions about the image
  - Identify objects, scenes, and activities
- IMPORTANT: When user asks "can you see what I'm working on?" or "what am I doing?", you MUST call capture_camera_photo tool - do not just respond with text

**Image Generation**: Use generate_image to create images from text prompts. Supports various styles.

**Diagrams**: Use generate_figure to create flowcharts, sequence diagrams, class diagrams, etc. in Mermaid format.

**Audio Processing**:
- Use speech_to_text to transcribe audio files
- Use text_to_speech to convert text to speech audio

**Guidelines**:
- When user asks about current events or needs up-to-date info, use web_search
- When user uploads an image, use analyze_image to understand it
- When user asks for an image, use generate_image
- When user asks for a diagram/flowchart, use generate_figure
- When user provides audio, use speech_to_text
- When user wants text spoken, use text_to_speech
- Be clear about what you're doing and what capabilities you're using
- Always use web_search when you need current or real-time information
"""

class MultimodalAgent:
    def __init__(self, model_name: str = None, mcp_config: Dict[str, Any] = None):
        """
        Initialize the multimodal agent.
        
        Args:
            model_name: Optional Gemini model name (defaults to gemini-1.5-flash)
            mcp_config: Optional MCP configuration dict. Examples:
                # Weather MCP server (stdio - requires npx and @modelcontextprotocol/server-weather)
                {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-weather"],
                    "env": {}
                }
                
                # Weather MCP server (HTTP/SSE - if you have a weather API)
                {
                    "type": "sse",
                    "url": "http://localhost:8001/sse",
                    "headers": {"X-API-Key": "your-key"}
                }
                
                # Multiple MCP servers
                {
                    "servers": [
                        {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-weather"]},
                        {"type": "sse", "url": "http://localhost:8002/sse"}
                    ]
                }
        """
        # Model fallback list - prioritize free tier models
        # Free tier models: gemini-1.5-flash (best), gemini-1.5-pro (limited)
        # Avoid: gemini-2.5-flash, gemini-2.0-flash-exp (may not be on free tier)
        default_model = model_name or os.getenv("GEMINI_MODEL", "").strip() or "gemini-1.5-flash"
        
        fallback_models = [
            default_model,
            "gemini-1.5-flash",  # Best free tier option - 20 requests/day
            "gemini-1.5-pro",     # Free tier with limits
            "gemini-pro",         # Older free tier
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        fallback_models = [m for m in fallback_models if m and (m not in seen and not seen.add(m))]
        
        self.history = []
        self.model_name = None  # Track which model we're using
        
        # Setup MCP toolsets if configured
        mcp_toolsets = []
        if mcp_config and MCP_AVAILABLE:
            try:
                # Handle single server config
                if "type" in mcp_config:
                    print(f"🌤️  Creating MCP toolset (type: {mcp_config.get('type')})...")
                    mcp_toolset = self._create_mcp_toolset_from_config(mcp_config)
                    if mcp_toolset:
                        mcp_toolsets.append(mcp_toolset)
                        print(f"✅ MCP toolset created successfully")
                    else:
                        print(f"⚠️  MCP toolset creation returned None")
                # Handle multiple servers config
                elif "servers" in mcp_config:
                    for server_config in mcp_config["servers"]:
                        mcp_toolset = self._create_mcp_toolset_from_config(server_config)
                        if mcp_toolset:
                            mcp_toolsets.append(mcp_toolset)
            except Exception as e:
                print(f"⚠️  Error setting up MCP toolsets: {e}")
                import traceback
                traceback.print_exc()
                print("   Continuing without MCP tools...")
        elif mcp_config and not MCP_AVAILABLE:
            print(f"⚠️  MCP config provided but MCP not available")
        elif not mcp_config:
            print(f"ℹ️  No MCP config provided - running without MCP tools")
        
        # Create tools list with MCP toolsets
        tools = create_tools_list(mcp_toolsets) if mcp_toolsets else TOOLS
        
        # Log tool information
        print(f"📦 Total tools to register: {len(tools)}")
        if mcp_toolsets:
            print(f"   - {len(mcp_toolsets)} MCP toolsets")
        native_tool_count = len(TOOL_FUNCTIONS)
        print(f"   - {native_tool_count} native tools")

        last_error = None
        self.model = None
        tried = []
        for m in fallback_models:
            if not m:
                continue
            tried.append(m)
            try:
                print(f"🔄 Initializing model {m} with {len(tools)} tools...")
                self.model = genai.GenerativeModel(
                    model_name=m,
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=tools
                )
                self.model_name = m
                
                # Give MCP tools time to initialize and discover tools (for stdio servers)
                if mcp_toolsets:
                    import time
                    print(f"⏳ Waiting 5 seconds for MCP server to start and discover tools...")
                    time.sleep(5)  # Increased wait time for tool discovery
                    print(f"✅ MCP tools should now be available to the model")
                    
                    # Try to verify tools are available (this is informational only)
                    try:
                        # The model should now have access to MCP tools
                        # We can't directly query the model for available tools, but we've waited
                        print(f"ℹ️  MCP toolset registered. Tools will be available when the model makes requests.")
                    except Exception as e:
                        print(f"⚠️  Could not verify MCP tools: {e}")
                
                if m != fallback_models[0]:
                    print(f"ℹ️ Using fallback model: {m}")
                else:
                    print(f"✅ Initialized model: {m} with {len(tools)} tools")
                break
            except Exception as e:
                last_error = e
                print(f"⚠️ Failed to initialize {m}: {str(e)[:100]}")
                continue

        if not self.model:
            raise RuntimeError(f"Could not initialize model. Tried: {tried}. Last error: {last_error}")
    
    def _create_mcp_toolset_from_config(self, config: Dict[str, Any]) -> Optional['MCPToolset']:
        """
        Create an MCP toolset from a configuration dictionary.
        
        Args:
            config: MCP server configuration dict
        
        Returns:
            MCPToolset instance or None if creation fails
        """
        if not MCP_AVAILABLE:
            print("⚠️  MCP not available - cannot create toolset")
            return None
        
        try:
            mcp_type = config.get("type", "").lower()
            print(f"🔧 Creating MCP toolset (type: {mcp_type})...")
            
            toolset = None
            if mcp_type == "stdio":
                toolset = create_mcp_toolset_stdio(
                    command=config.get("command", "npx"),
                    args=config.get("args", []),
                    env=config.get("env", {})
                )
                print(f"✅ Created stdio MCP toolset: {config.get('command')} {' '.join(config.get('args', []))}")
            elif mcp_type == "sse":
                toolset = create_mcp_toolset_sse(
                    server_url=config.get("url", ""),
                    headers=config.get("headers", {})
                )
                print(f"✅ Created SSE MCP toolset: {config.get('url')}")
            elif mcp_type == "http":
                toolset = create_mcp_toolset_http(
                    server_url=config.get("url", ""),
                    headers=config.get("headers", {})
                )
                print(f"✅ Created HTTP MCP toolset: {config.get('url')}")
            else:
                print(f"⚠️  Unknown MCP type: {mcp_type}. Supported: stdio, sse, http")
                return None
            
            if toolset:
                print(f"✅ MCP toolset created successfully")
            return toolset
        except Exception as e:
            print(f"❌ Error creating MCP toolset: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run(self, user_input: str, image_path: Optional[str] = None) -> str:
        """
        Process user input, optionally with an image.
        
        Args:
            user_input: Text input from user
            image_path: Optional path to image file for multimodal input
        """
        # Handle multimodal input (text + image)
        if image_path and os.path.exists(image_path):
            try:
                from PIL import Image
                img = Image.open(image_path)
                print(f"[Agent] Loading image from: {image_path}")
                print(f"[Agent] Image size: {img.size}, mode: {img.mode}")
                # Gemini can handle multimodal input natively!
                self.history.append({"role": "user", "parts": [user_input, img]})
                print(f"[Agent] Added image to history, user input: '{user_input[:50]}...'")
            except Exception as e:
                print(f"[Agent] Error loading image: {e}")
                import traceback
                traceback.print_exc()
                # If image loading fails, fall back to text only
                self.history.append({"role": "user", "parts": [f"{user_input}\n[Note: Could not load image: {e}]"]})
        else:
            if image_path:
                print(f"[Agent] Warning: Image path provided but file doesn't exist: {image_path}")
            self.history.append({"role": "user", "parts": [user_input]})
        
        print(f"[Agent] Generating response with history length: {len(self.history)}")
        
        # Try with retry logic for rate limits
        max_retries = 3
        last_error = None
        response = None
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(self.history)
                print(f"[Agent] Response received, has text: {hasattr(response, 'text')}")
                print(f"[Agent] Response type: {type(response)}")
                if hasattr(response, 'candidates'):
                    print(f"[Agent] Response has {len(response.candidates)} candidates")
                break  # Success, exit retry loop
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                is_rate_limit = (
                    "429" in str(e) or
                    "quota" in error_str or
                    "rate limit" in error_str or
                    "exceeded" in error_str
                )
                
                if is_rate_limit and attempt < max_retries - 1:
                    # Extract retry delay from error if available
                    import re
                    retry_match = re.search(r'retry.*?(\d+)\s*seconds?', error_str, re.IGNORECASE)
                    if retry_match:
                        wait_time = float(retry_match.group(1)) + 2  # Add buffer
                    else:
                        # Exponential backoff: 5s, 15s, 30s
                        wait_time = min(5.0 * (3 ** attempt), 30.0)
                    
                    print(f"[Agent] Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f}s...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    # Not a rate limit or last attempt
                    print(f"[Agent] Error generating response: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    if is_rate_limit:
                        # Rate limit error - provide helpful message
                        return (
                            "⚠️ **Rate Limit Exceeded**\n\n"
                            "I've hit the free tier quota limit for the Gemini API. "
                            "The free tier allows 20 requests per day per model.\n\n"
                            "**Options:**\n"
                            "1. Wait a few minutes and try again (quota resets periodically)\n"
                            "2. Check your usage: https://ai.dev/usage?tab=rate-limit\n"
                            "3. Consider upgrading your Google Cloud plan for higher limits\n\n"
                            f"Error details: {str(e)[:200]}"
                        )
                    else:
                        return f"Error generating response: {str(e)}"
        
        if last_error:
            # All retries failed
            return f"Error after {max_retries} attempts: {str(last_error)}"

        # Handle function calls
        fc = None
        if hasattr(response, 'candidates') and response.candidates:
            try:
                first_candidate = response.candidates[0]
                if hasattr(first_candidate, 'content') and hasattr(first_candidate.content, 'parts'):
                    for part in first_candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            break
                else:
                    print("[Agent] Warning: First candidate has no content or parts")
            except (IndexError, AttributeError) as e:
                print(f"[Agent] Warning: Error accessing candidates: {e}")
        else:
            print("[Agent] Warning: Response has no candidates")
        
        # If we have a function call, handle it (both native and MCP tools)

        if fc:
            fn = fc.name
            args = dict(fc.args)
            
            # Check if this is a native tool or MCP tool
            is_native_tool = fn in TOOL_FUNCTIONS
            
            if is_native_tool:
                # Native tool - execute manually
                # Add defaults
                if fn == "generate_image" and "style" not in args:
                    args["style"] = "realistic"
                if fn == "generate_figure" and "format" not in args:
                    args["format"] = "mermaid"
                if fn == "text_to_speech" and "voice" not in args:
                    args["voice"] = "default"
                if fn == "web_search" and "num_results" not in args:
                    args["num_results"] = 5

                tool_result = TOOL_FUNCTIONS[fn](**args)

                # Extend history with function call and result
                self.history.append({"role": "model", "parts": [{"function_call": fc}]})
                self.history.append({"role": "function", "parts": [{"function_response": {"name": fn, "response": {"result": tool_result}}}]})

                print(f"[Agent] Native tool {fn} executed, result: {tool_result[:100] if tool_result else 'None'}...")
                print(f"[Agent] Generating final response after tool call...")
                
            else:
                # MCP tool - ADK handles execution automatically
                # Just add function call to history, ADK will execute it when we call generate_content
                self.history.append({"role": "model", "parts": [{"function_call": fc}]})
                print(f"[Agent] MCP tool {fn} detected - ADK will handle execution automatically")
                print(f"[Agent] Generating response (ADK will execute MCP tool)...")
            
            # Retry logic for final response (works for both native and MCP tools)
            max_retries = 3
            final_error = None
            
            for attempt in range(max_retries):
                try:
                    final_response = self.model.generate_content(self.history)
                    print(f"[Agent] Final response received, has text: {hasattr(final_response, 'text')}")
                    break
                except Exception as e:
                    final_error = e
                    error_str = str(e).lower()
                    is_rate_limit = (
                        "429" in str(e) or
                        "quota" in error_str or
                        "rate limit" in error_str or
                        "exceeded" in error_str
                    )
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        import re
                        retry_match = re.search(r'retry.*?(\d+)\s*seconds?', error_str, re.IGNORECASE)
                        if retry_match:
                            wait_time = float(retry_match.group(1)) + 2
                        else:
                            wait_time = min(5.0 * (3 ** attempt), 30.0)
                        
                        print(f"[Agent] Rate limit on final response (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f}s...")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
            
            if final_error:
                # Return tool result as fallback if final response fails (only for native tools)
                if is_native_tool:
                    return tool_result if tool_result else f"Error generating final response: {str(final_error)}"
                else:
                    return f"Error generating final response: {str(final_error)}"
            
            try:
                # Extract final response text
                # IMPORTANT: Don't access .text directly if response might have function_call parts
                # This can cause "Could not convert part.function_call to text" error
                final_text = ""
                
                if hasattr(final_response, "candidates") and final_response.candidates:
                    # Extract text from candidates, skipping function_call parts
                    for candidate in final_response.candidates:
                        if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                            for part in candidate.content.parts:
                                # Only extract text parts, skip function_call
                                if hasattr(part, "text") and part.text:
                                    final_text += part.text
                                elif isinstance(part, str):
                                    final_text += part
                                # Explicitly skip function_call parts to avoid errors
                                elif hasattr(part, "function_call"):
                                    print(f"[Agent] Skipping function_call part in final response")
                                    continue
                
                # Fallback: try .text property (but catch errors)
                if not final_text:
                    try:
                        if hasattr(final_response, "text") and final_response.text:
                            final_text = final_response.text
                    except Exception as text_error:
                        print(f"[Agent] Warning: Could not access .text property: {text_error}")
                        # If .text fails, try string conversion
                        if not final_text:
                            final_text = str(final_response)
                
                # Last resort: string conversion
                if not final_text:
                    final_text = str(final_response)
                
                if not final_text or not final_text.strip():
                    print("[Agent] Warning: Final response is empty after tool call")
                    # Return the tool result as fallback (only for native tools)
                    if is_native_tool:
                        final_text = tool_result if tool_result else "I've processed your request. Please check if the camera is started and agent camera control is enabled."
                    else:
                        final_text = f"I've executed the {fn} tool, but didn't receive a response. Please try again."
                
                print(f"[Agent] Returning final response: '{final_text[:100]}...'")
                self.history.append({"role": "model", "parts": [final_text]})
                return final_text
            except Exception as e:
                print(f"[Agent] Error generating final response: {e}")
                import traceback
                traceback.print_exc()
                # Return tool result as fallback (only for native tools)
                if is_native_tool:
                    return tool_result if tool_result else f"Error: {str(e)}"
                else:
                    return f"Error processing MCP tool {fn}: {str(e)}"

        # No function call; normal text response
        # IMPORTANT: Don't access .text directly - it might throw error if response has function_call parts
        text = ""
        
        if hasattr(response, "candidates") and response.candidates:
            # Extract text from candidates, skipping function_call parts
            for candidate in response.candidates:
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        # Only extract text parts
                        if hasattr(part, "text") and part.text:
                            text += part.text
                        elif isinstance(part, str):
                            text += part
                        # Skip function_call parts (shouldn't happen here, but be safe)
                        elif hasattr(part, "function_call"):
                            print(f"[Agent] Warning: Found function_call in non-function-call path")
                            continue
        
        # Fallback: try .text property (but catch errors)
        if not text:
            try:
                if hasattr(response, "text") and response.text:
                    text = response.text
            except Exception as text_error:
                # This is where "Could not convert part.function_call to text" might occur
                error_msg = str(text_error)
                if "function_call" in error_msg.lower() or "could not convert" in error_msg.lower():
                    print(f"[Agent] Error: Response contains function_call that couldn't be converted to text")
                    print(f"[Agent] This might be an MCP tool response. Trying to handle it...")
                    # Try to extract text from parts again more carefully
                    if hasattr(response, "candidates") and response.candidates:
                        for candidate in response.candidates:
                            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                                for part in candidate.content.parts:
                                    if hasattr(part, "text") and part.text:
                                        text += part.text
                else:
                    print(f"[Agent] Warning: Could not access .text property: {text_error}")
        
        # Last resort: string conversion
        if not text:
            text = str(response)
        
        if not text or not text.strip():
            print("[Agent] Warning: Empty response text, returning default message")
            text = "I processed your request but didn't receive a response. Please try again."
        
        print(f"[Agent] Returning response: '{text[:100]}...'")
        self.history.append({"role": "model", "parts": [text]})
        return text


def run_multimodal_interactive():
    agent = MultimodalAgent()
    print("🎨 Multimodal Personal Assistant")
    print("=" * 60)
    print("Capabilities:")
    print("  ✅ Text: Q&A, explanations, summaries")
    print("  ✅ Image Analysis: Analyze uploaded images (Gemini vision)")
    print("  ✅ Image Generation: Generate images (DALL-E)")
    print("  ✅ Diagrams: Mermaid flowcharts, sequence diagrams")
    print("  ✅ Speech-to-Text: Transcribe audio (Whisper)")
    print("  ✅ Text-to-Speech: Generate speech audio (OpenAI TTS)")
    print("\nCommands:")
    print("  - Type normally for text queries")
    print("  - Type 'image: <path>' to analyze an image")
    print("  - Type 'audio: <path>' to transcribe audio")
    print("  - Type 'quit' or 'exit' to end")
    print("=" * 60)
    print()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nGoodbye!")
            break
        if not user_input:
            continue

        try:
            # Handle special commands
            image_path = None
            audio_path = None
            
            if user_input.startswith("image: "):
                image_path = user_input[7:].strip()
                if os.path.exists(image_path):
                    question = input("Question about image (or press Enter for general description): ").strip()
                    if question:
                        result = agent.run(question, image_path=image_path)
                    else:
                        result = agent.run("Describe this image in detail.", image_path=image_path)
                else:
                    result = f"❌ Image file not found: {image_path}"
            elif user_input.startswith("audio: "):
                audio_path = user_input[7:].strip()
                if os.path.exists(audio_path):
                    # Transcribe audio first
                    transcript = speech_to_text(audio_path)
                    print(f"\n📝 Audio Transcript: {transcript}\n")
                    # Then process the transcript
                    follow_up = input("What would you like to do with this transcript? (or press Enter to continue): ").strip()
                    if follow_up:
                        result = agent.run(f"{follow_up}\n\nContext from audio: {transcript}")
                    else:
                        result = f"Audio transcribed successfully:\n{transcript}"
                else:
                    result = f"❌ Audio file not found: {audio_path}"
            else:
                # Normal text input
                result = agent.run(user_input)
            
            print(f"\nAgent: {result}\n")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            if os.getenv("DEBUG"):
                traceback.print_exc()


if __name__ == "__main__":
    run_multimodal_interactive()

