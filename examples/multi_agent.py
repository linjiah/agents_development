"""
Enhanced Multi-Agent System using Google ADK

This example demonstrates an advanced multi-agent system with:
- LLM-based intelligent routing
- Parallel agent execution
- Agent-to-agent communication
- Shared conversation history
- Dynamic agent creation
- Tool support
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Setup compatibility fixes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.compat import setup_compatibility
setup_compatibility()

import google.generativeai as genai

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("❌ ERROR: GEMINI_API_KEY not set. Get your key from: https://aistudio.google.com/")
    sys.exit(1)

genai.configure(api_key=api_key)

# Import tools from tool_agent
sys.path.insert(0, os.path.dirname(__file__))
try:
    from tool_agent import (
        calculator, web_search, get_weather, 
        get_current_time, create_note, get_note,
        TOOL_FUNCTIONS
    )
except ImportError:
    # Fallback if tool_agent not available
    def calculator(expression: str) -> str:
        try:
            allowed_chars = set("0123456789+-*/()., ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters"
            return str(eval(expression))
        except:
            return "Error in calculation"
    
    def web_search(query: str, num_results: int = 5) -> str:
        return f"Web search for: {query} (install duckduckgo-search for real results)"
    
    def get_weather(location: str) -> str:
        return f"Weather for {location} (placeholder)"
    
    def get_current_time(timezone: str = "UTC") -> str:
        from datetime import datetime
        return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    def create_note(title: str, content: str) -> str:
        return f"Note '{title}' created"
    
    def get_note(title: str) -> str:
        return f"Note '{title}' not found"
    
    TOOL_FUNCTIONS = {
        "calculator": calculator,
        "web_search": web_search,
        "get_weather": get_weather,
        "get_current_time": get_current_time,
        "create_note": create_note,
        "get_note": get_note,
    }

# Shared conversation history across all agents
SHARED_HISTORY = []

def _strip_agent_field(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Remove non-schema fields (like 'agent') before sending to the model."""
    return {k: v for k, v in msg.items() if k != "agent"}

# Tool definitions for agents
TOOLS = [
    {
        "function_declarations": [
            {
                "name": "calculator",
                "description": "Evaluate a mathematical expression.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Mathematical expression"}
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "description": "Number of results (default: 5)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get weather information for a location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "Location name"}
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get current date and time for a timezone.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {"type": "string", "description": "Timezone (default: UTC)"}
                    },
                    "required": []
                }
            },
            {
                "name": "create_note",
                "description": "Create and save a note.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"},
                        "content": {"type": "string", "description": "Note content"}
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "get_note",
                "description": "Retrieve a saved note.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"}
                    },
                    "required": ["title"]
                }
            }
        ]
    }
]

class BaseAgent:
    """Base agent class with tool support and communication."""
    
    def __init__(self, name: str, model_name: str, system_instruction: str, tools: Optional[List] = None):
        self.name = name
        self.model_name = os.getenv("GEMINI_MODEL", model_name)
        self.system_instruction = system_instruction
        self.tools = tools
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction,
            tools=tools if tools else None
        )
        self.conversation_history = []
    
    def generate(self, prompt: str, context: Optional[List[Dict]] = None) -> str:
        """Generate a response with optional context from other agents."""
        history = self.conversation_history.copy()
        
        # Add shared history context (strip 'agent' field not supported by API)
        if SHARED_HISTORY:
            shared = [_strip_agent_field(m) for m in SHARED_HISTORY[-5:]]  # Last 5 messages
            history.extend(shared)
        
        # Add agent communication context
        if context:
            history.append({
                "role": "user",
                "parts": [f"[Context from other agents: {json.dumps(context, default=str)}]"]
            })
        
        # Add current prompt
        history.append({"role": "user", "parts": [prompt]})
        
        try:
            response = self.model.generate_content(history)
            
            # Handle function calls if tools are available
            if self.tools:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        return self._handle_function_call(response, history, part.function_call)
            
            text = response.text if hasattr(response, 'text') else str(response)
            self.conversation_history.append({"role": "user", "parts": [prompt]})
            self.conversation_history.append({"role": "model", "parts": [text]})
            SHARED_HISTORY.append({"role": "user", "parts": [prompt], "agent": self.name})
            SHARED_HISTORY.append({"role": "model", "parts": [text], "agent": self.name})
            return text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _handle_function_call(self, response, history, function_call):
        """Handle function calls in agent responses."""
        function_name = function_call.name
        args = dict(function_call.args)
        
        if function_name in TOOL_FUNCTIONS:
            if function_name == "web_search" and "num_results" not in args:
                args["num_results"] = 5
            elif function_name == "get_current_time" and "timezone" not in args:
                args["timezone"] = "UTC"
            
            tool_result = TOOL_FUNCTIONS[function_name](**args)
            
            # Add function call and result to history
            history.append({"role": "model", "parts": [{"function_call": function_call}]})
            history.append({
                "role": "function",
                "parts": [{"function_response": {"name": function_name, "response": {"result": tool_result}}}]
            })
            
            # Get final response
            final_response = self.model.generate_content(history)
            text = final_response.text if hasattr(final_response, 'text') else str(final_response)
            
            self.conversation_history = history
            self.conversation_history.append({"role": "model", "parts": [text]})
            return text
        
        return f"Tool {function_name} not found"
    
    def consult(self, question: str, from_agent: str) -> str:
        """Allow this agent to be consulted by another agent."""
        context_msg = f"[Consultation request from {from_agent}]: {question}"
        return self.generate(context_msg)
    
    def get_recent_context(self, num_messages: int = 3) -> List[Dict]:
        """Get recent conversation context."""
        return self.conversation_history[-num_messages:] if self.conversation_history else []

class RouterAgent(BaseAgent):
    """LLM-based router agent that decides which agent(s) to use."""
    
    def __init__(self):
        super().__init__(
            name="RouterAgent",
            model_name="gemini-2.5",
            system_instruction="""You are an intelligent router for a multi-agent personal assistant system.

Your job is to analyze user queries and decide which specialized agent(s) should handle them.

Available agents:
1. ResearchAgent - Web searches, information gathering, fact-checking
2. TaskAgent - Task management, scheduling, reminders, notes
3. TechnicalAgent - Technical questions, coding, math, calculations
4. CommunicationAgent - Writing, communication, emails, messages

You can route to:
- Single agent: When one agent is clearly best suited
- Multiple agents (parallel): When the query needs multiple perspectives or capabilities

Respond in JSON format:
{
    "agents": ["agent_name1", "agent_name2"],
    "reasoning": "Why these agents were chosen",
    "parallel": true/false
}

Examples:
- "Search for Python best practices" → {"agents": ["ResearchAgent"], "parallel": false}
- "Write code and schedule a meeting" → {"agents": ["TechnicalAgent", "TaskAgent"], "parallel": true}
- "Calculate 25*4 and search for calculator reviews" → {"agents": ["TechnicalAgent", "ResearchAgent"], "parallel": true}"""
        )
    
    def route(self, query: str, available_agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Route query to appropriate agent(s) using LLM."""
        agent_list = ", ".join(available_agents.keys())
        routing_prompt = f"""User query: "{query}"

Available agents: {agent_list}

Analyze this query and decide which agent(s) should handle it. Respond in JSON format with:
- "agents": list of agent names to use
- "reasoning": brief explanation
- "parallel": true if agents should work in parallel, false if sequential"""
        
        try:
            response = self.model.generate_content(routing_prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                routing_decision = json.loads(json_str)
            else:
                # Fallback: simple keyword-based routing
                routing_decision = self._fallback_routing(query, available_agents)
            
            # Validate and fix routing decision
            if "agents" not in routing_decision:
                routing_decision = self._fallback_routing(query, available_agents)
            
            agents_to_use = routing_decision.get("agents", [])
            if not agents_to_use or not all(a in available_agents for a in agents_to_use):
                routing_decision = self._fallback_routing(query, available_agents)
            
            return {
                "agents": routing_decision.get("agents", ["ResearchAgent"]),
                "reasoning": routing_decision.get("reasoning", "Default routing"),
                "parallel": routing_decision.get("parallel", True)
            }
        except Exception as e:
            print(f"⚠️  Routing error: {e}, using fallback")
            return self._fallback_routing(query, available_agents)
    
    def _fallback_routing(self, query: str, available_agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Fallback keyword-based routing."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["search", "find", "information", "web", "lookup"]):
            return {"agents": ["ResearchAgent"], "reasoning": "Information search needed", "parallel": False}
        elif any(word in query_lower for word in ["task", "schedule", "reminder", "note", "todo"]):
            return {"agents": ["TaskAgent"], "reasoning": "Task management needed", "parallel": False}
        elif any(word in query_lower for word in ["code", "calculate", "algorithm", "technical", "math"]):
            return {"agents": ["TechnicalAgent"], "reasoning": "Technical question", "parallel": False}
        elif any(word in query_lower for word in ["write", "email", "message", "communication"]):
            return {"agents": ["CommunicationAgent"], "reasoning": "Communication task", "parallel": False}
        else:
            return {"agents": ["ResearchAgent"], "reasoning": "Default to research", "parallel": False}

class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering."""
    
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            model_name="gemini-2.5",
            system_instruction="""You are a research and information specialist.

Your capabilities:
- Web searches for current information
- Fact-checking and verification
- Information synthesis and summarization
- Answering questions with up-to-date data

Use web_search tool when you need current information or facts.
Provide clear, well-sourced answers.""",
            tools=TOOLS
        )

class TaskAgent(BaseAgent):
    """Agent specialized in task management and scheduling."""
    
    def __init__(self):
        super().__init__(
            name="TaskAgent",
            model_name="gemini-2.5",
            system_instruction="""You are a task management and scheduling specialist.

Your capabilities:
- Creating and managing notes/reminders
- Scheduling and time management
- Task prioritization
- Calendar and appointment management

Use create_note, get_note, and get_current_time tools to help users manage their tasks.
Be organized and proactive in suggesting task management strategies.""",
            tools=TOOLS
        )

class TechnicalAgent(BaseAgent):
    """Agent specialized in technical questions and calculations."""
    
    def __init__(self):
        super().__init__(
            name="TechnicalAgent",
            model_name="gemini-2.5",
            system_instruction="""You are a technical specialist.

Your capabilities:
- Answering technical questions
- Code explanations and examples
- Mathematical calculations
- Algorithm and data structure explanations
- System design concepts

Use calculator tool for mathematical operations.
Provide clear, detailed technical explanations with examples.""",
            tools=TOOLS
        )

class CommunicationAgent(BaseAgent):
    """Agent specialized in writing and communication."""
    
    def __init__(self):
        super().__init__(
            name="CommunicationAgent",
            model_name="gemini-2.5",
            system_instruction="""You are a communication and writing specialist.

Your capabilities:
- Writing emails, messages, and documents
- Communication strategy and tone
- Professional writing
- Content creation and editing

Help users craft clear, effective communications.
Adapt your writing style to the context and audience.""",
            tools=None  # No tools needed for writing
        )

class MultiAgentOrchestrator:
    """Orchestrates multiple agents with advanced features."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.router = RouterAgent()
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default specialized agents."""
        self.agents["ResearchAgent"] = ResearchAgent()
        self.agents["TaskAgent"] = TaskAgent()
        self.agents["TechnicalAgent"] = TechnicalAgent()
        self.agents["CommunicationAgent"] = CommunicationAgent()
    
    def create_agent(self, name: str, system_instruction: str, tools: Optional[List] = None) -> BaseAgent:
        """Dynamically create a new agent."""
        agent = BaseAgent(
            name=name,
            model_name="gemini-2.5",
            system_instruction=system_instruction,
            tools=tools
        )
        self.agents[name] = agent
        print(f"✅ Created new agent: {name}")
        return agent
    
    def route_and_execute(self, query: str, enable_consultation: bool = True) -> Dict[str, Any]:
        """Route query and execute with agent(s), supporting parallel execution and consultation."""
        # Get routing decision
        routing = self.router.route(query, self.agents)
        agent_names = routing["agents"]
        parallel = routing.get("parallel", True)
        
        print(f"\n🧭 Routing Decision:")
        print(f"   Agents: {', '.join(agent_names)}")
        print(f"   Reasoning: {routing.get('reasoning', 'N/A')}")
        print(f"   Parallel: {parallel}\n")
        
        if parallel and len(agent_names) > 1:
            # Parallel execution
            return self._execute_parallel(query, agent_names, enable_consultation)
        else:
            # Sequential execution (or single agent)
            return self._execute_sequential(query, agent_names, enable_consultation)
    
    def _execute_parallel(self, query: str, agent_names: List[str], enable_consultation: bool) -> Dict[str, Any]:
        """Execute multiple agents in parallel."""
        results = {}
        
        def execute_agent(agent_name: str):
            agent = self.agents[agent_name]
            response = agent.generate(query)
            
            # Allow consultation if enabled
            if enable_consultation and len(agent_names) > 1:
                # Get context from other agents
                other_agents = [a for a in agent_names if a != agent_name]
                context = []
                for other_name in other_agents:
                    if other_name in results:
                        context.append({
                            "agent": other_name,
                            "response": results[other_name]["response"]
                        })
                
                if context:
                    # Refine response with context
                    refined = agent.generate(
                        f"[Refining response with context from other agents] Original query: {query}",
                        context=context
                    )
                    return {"agent": agent_name, "response": refined, "original": response}
            
            return {"agent": agent_name, "response": response}
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=len(agent_names)) as executor:
            futures = {executor.submit(execute_agent, name): name for name in agent_names}
            
            for future in as_completed(futures):
                result = future.result()
                results[result["agent"]] = result
        
        return {
            "agents": agent_names,
            "responses": results,
            "mode": "parallel"
        }
    
    def _execute_sequential(self, query: str, agent_names: List[str], enable_consultation: bool) -> Dict[str, Any]:
        """Execute agents sequentially with consultation."""
        results = {}
        previous_responses = []
        
        for agent_name in agent_names:
            agent = self.agents[agent_name]
            
            # Build context from previous agents
            context = previous_responses if enable_consultation and previous_responses else None
            
            response = agent.generate(query, context=context)
            
            # Allow agent-to-agent consultation
            if enable_consultation and len(agent_names) > 1:
                # Check if this agent needs to consult others
                consultation_needed = self._needs_consultation(response, agent_name, agent_names)
                if consultation_needed:
                    consulted_agent = self.agents[consultation_needed]
                    consultation_response = consulted_agent.consult(
                        f"Can you help with: {query}",
                        from_agent=agent_name
                    )
                    # Integrate consultation into response
                    response = f"{response}\n\n[Consulted {consultation_needed}]: {consultation_response}"
            
            results[agent_name] = {"agent": agent_name, "response": response}
            previous_responses.append({"agent": agent_name, "response": response})
        
        return {
            "agents": agent_names,
            "responses": results,
            "mode": "sequential"
        }
    
    def _needs_consultation(self, response: str, current_agent: str, available_agents: List[str]) -> Optional[str]:
        """Determine if agent needs to consult another agent."""
        # Simple heuristic: if response is uncertain, consult
        uncertain_phrases = ["i'm not sure", "i don't know", "uncertain", "might need"]
        if any(phrase in response.lower() for phrase in uncertain_phrases):
            # Consult a different agent
            other_agents = [a for a in available_agents if a != current_agent]
            return other_agents[0] if other_agents else None
        return None
    
    def get_shared_history(self) -> List[Dict]:
        """Get shared conversation history."""
        return SHARED_HISTORY.copy()

def run_multi_agent_interactive():
    """Run enhanced multi-agent system in interactive mode."""
    orchestrator = MultiAgentOrchestrator()
    
    print("🤖 Enhanced Multi-Agent Personal Assistant")
    print("=" * 60)
    print("Available agents: ResearchAgent, TaskAgent, TechnicalAgent, CommunicationAgent")
    print("\nCommands:")
    print("  - 'create <name> <instruction>' - Create a new agent")
    print("  - 'history' - View shared conversation history")
    print("  - 'agents' - List all agents")
    print("  - 'quit' or 'exit' - End conversation\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if user_input.lower() == 'history':
            history = orchestrator.get_shared_history()
            print("\n📜 Shared Conversation History:")
            print("=" * 60)
            for i, msg in enumerate(history[-10:], 1):  # Last 10 messages
                agent = msg.get('agent', 'user')
                role = msg.get('role', 'unknown')
                parts = msg.get('parts', [])
                text = ' '.join([p for p in parts if isinstance(p, str)])
                print(f"{i}. [{agent}] ({role}): {text[:100]}...")
            print()
            continue
        
        if user_input.lower() == 'agents':
            print("\n🤖 Available Agents:")
            print("=" * 60)
            for name, agent in orchestrator.agents.items():
                print(f"  - {name}: {agent.system_instruction[:80]}...")
            print()
            continue
        
        if user_input.lower().startswith('create '):
            parts = user_input[7:].split(' ', 1)
            if len(parts) == 2:
                name, instruction = parts
                orchestrator.create_agent(name, instruction)
            else:
                print("Usage: create <agent_name> <system_instruction>")
            continue
        
        if not user_input:
            continue
        
        try:
            # Route and execute
            result = orchestrator.route_and_execute(user_input, enable_consultation=True)
            
            print(f"\n📊 Response ({result['mode']} mode):")
            print("=" * 60)
            
            for agent_name, agent_result in result['responses'].items():
                response = agent_result.get('response', 'No response')
                print(f"\n[{agent_name}]:")
                print(f"{response}\n")
            
            print("=" * 60)
            print()
            
        except Exception as e:
            print(f"\nError: {str(e)}\n")
            import traceback
            traceback.print_exc()
            
if __name__ == "__main__":
    run_multi_agent_interactive()
