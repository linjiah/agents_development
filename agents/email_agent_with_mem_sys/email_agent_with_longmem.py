"""
Email Assistant with Semantic + Episodic + Procedural Memory

This email assistant includes three types of long-term memory:
1. Semantic Memory - Few-shot examples for better triage classification
2. Episodic Memory - Conversation history and contact information
3. Procedural Memory - Dynamic prompt updates based on user feedback

Features:
- Classifies incoming messages (respond, ignore, notify)
- Uses human-in-the-loop to refine classification
- Drafts responses
- Schedules meetings
- Remembers details from previous emails
- Learns and adapts from user feedback

MEMORY MARKERS IN CODE:
========================
Throughout this code, you'll find markers indicating memory operations:

- ========== SEMANTIC MEMORY: CREATE/STORE ==========
  Store email examples with classifications for few-shot learning
  
- ========== SEMANTIC MEMORY: RETRIEVE/SEARCH ==========
  Search for similar email examples using vector similarity


- ========== EPISODIC MEMORY: CREATE/STORE ==========
  Store conversation history, contacts, preferences (via manage_memory_tool)

- ========== EPISODIC MEMORY: RETRIEVE/SEARCH ==========
  Search for past conversations and context (via search_memory_tool)


- ========== PROCEDURAL MEMORY: CREATE/STORE ==========
  Store or update agent instructions and triage rules

- ========== PROCEDURAL MEMORY: RETRIEVE ==========
  Retrieve agent instructions and triage rules from store
"""

import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal, Annotated
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.store.memory import InMemoryStore
from langgraph.graph import add_messages, StateGraph, START, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from langmem import create_manage_memory_tool, create_search_memory_tool, create_multi_prompt_optimizer
from prompts import triage_user_prompt

# Load API tokens for our 3rd party APIs
_ = load_dotenv()

# ============================================================================
# Setup: Profile, Prompt Instructions, and Example Email
# ============================================================================

profile = {
    "name": "John",
    "full_name": "John Doe",
    "user_profile_background": "Senior software engineer leading a team of 5 developers",
}

prompt_instructions = {
    "triage_rules": {
        "ignore": "Marketing newsletters, spam emails, mass company announcements",
        "notify": "Team member out sick, build system notifications, project status updates",
        "respond": "Direct questions from team members, meeting requests, critical bug reports",
    },
    "agent_instructions": "Use these tools when appropriate to help manage John's tasks efficiently."
}

# Example incoming email (for initial testing)
email = {
    "from": "Alice Smith <alice.smith@company.com>",
    "to": "John Doe <john.doe@company.com>",
    "subject": "Quick question about API documentation",
    "body": """
Hi John,

I was reviewing the API documentation for the new authentication service and noticed a few endpoints seem to be missing from the specs. Could you help clarify if this was intentional or if we should update the docs?

Specifically, I'm looking at:
- /auth/refresh
- /auth/validate

Thanks!
Alice""",
}

# ============================================================================
# Memory Store Setup
# ============================================================================

store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)
# Note: Ignore beta warning if it appears

# ============================================================================
# Semantic Memory: Few-Shot Examples Formatting
# ============================================================================

# ========== SEMANTIC MEMORY: CREATE/STORE Example ==========
# To store email examples for few-shot learning, use:
# 
# namespace = ("email_assistant", user_id, "examples")
# store.put(
#     namespace,
#     "example_1",  # unique key
#     {
#         "email": {
#             "subject": "API documentation question",
#             "author": "Alice Smith <alice@company.com>",
#             "to": "John Doe <john@company.com>",
#             "email_thread": "Hi John, can you help with missing endpoints?"
#         },
#         "label": "respond"  # Classification: "ignore", "notify", or "respond"
#     }
# )

# Template for formatting an example to put in prompt
template = """Email Subject: {subject}
Email From: {from_email}
Email To: {to_email}
Email Content: 
```
{content}
```
> Triage Result: {result}"""


def format_few_shot_examples(examples):
    """Format list of few-shot examples for the triage prompt."""
    strs = ["Here are some previous examples:"]
    for eg in examples:
        strs.append(
            template.format(
                subject=eg.value["email"]["subject"],
                to_email=eg.value["email"]["to"],
                from_email=eg.value["email"]["author"],
                content=eg.value["email"]["email_thread"][:400],
                result=eg.value["label"],
            )
        )
    return "\n\n------------\n\n".join(strs)

# ============================================================================
# Triage System Prompt
# ============================================================================

triage_system_prompt = """
< Role >
You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.
</ Role >

< Background >
{user_profile_background}. 
</ Background >

< Instructions >

{name} gets lots of emails. Your job is to categorize each email into one of three categories:

1. IGNORE - Emails that are not worth responding to or tracking
2. NOTIFY - Important information that {name} should know about but doesn't require a response
3. RESPOND - Emails that need a direct response from {name}

Classify the below email into one of these categories.

</ Instructions >

< Rules >
Emails that are not worth responding to:
{triage_no}

There are also other things that {name} should know about, but don't require an email response. For these, you should notify {name} (using the `notify` response). Examples of this include:
{triage_notify}

Emails that are worth responding to:
{triage_email}
</ Rules >

< Few shot examples >

Here are some examples of previous emails, and how they should be handled.
Follow these examples more than any instructions above

{examples}
</ Few shot examples >
"""

# ============================================================================
# Triage Router Setup
# ============================================================================

llm = init_chat_model("openai:gpt-4o-mini")


class Router(BaseModel):
    """Analyze the unread email and route it according to its content."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email: 'ignore' for irrelevant emails, "
        "'notify' for important information that doesn't need a response, "
        "'respond' for emails that need a reply",
    )


llm_router = llm.with_structured_output(Router)

# ============================================================================
# State Definition
# ============================================================================

class State(TypedDict):
    email_input: dict
    messages: Annotated[list, add_messages]

# ============================================================================
# Triage Router Node (with Memory Integration)
# ============================================================================

def triage_router(state: State, config, store) -> Command[
    Literal["response_agent", "__end__"]
]:
    """
    Route emails based on triage classification.
    
    Uses:
    - Semantic memory: Retrieves few-shot examples
    - Procedural memory: Loads triage rules from store
    """
    author = state['email_input']['author']
    to = state['email_input']['to']
    subject = state['email_input']['subject']
    email_thread = state['email_input']['email_thread']

    # ========== SEMANTIC MEMORY: RETRIEVE/SEARCH ==========
    # Search for similar email examples using vector similarity
    namespace = (
        "email_assistant",
        config['configurable']['langgraph_user_id'],
        "examples"
    )
    examples = store.search(
        namespace, 
        query=str({"email": state['email_input']})
    ) 
    examples = format_few_shot_examples(examples)
    # Note: To CREATE semantic memory, use: store.put(namespace, key, {"email": {...}, "label": "..."})

    # ========== PROCEDURAL MEMORY: RETRIEVE ==========
    # Get triage rules from store (or initialize if not exists)
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id, )

    # RETRIEVE: Get triage_ignore rule
    result = store.get(namespace, "triage_ignore")
    if result is None:
        # CREATE: Initialize triage_ignore if not exists
        store.put(
            namespace, 
            "triage_ignore", 
            {"prompt": prompt_instructions["triage_rules"]["ignore"]}
        )
        ignore_prompt = prompt_instructions["triage_rules"]["ignore"]
    else:
        # RETRIEVE: Use stored triage_ignore rule
        ignore_prompt = result.value['prompt']

    # RETRIEVE: Get triage_notify rule
    result = store.get(namespace, "triage_notify")
    if result is None:
        # CREATE: Initialize triage_notify if not exists
        store.put(
            namespace, 
            "triage_notify", 
            {"prompt": prompt_instructions["triage_rules"]["notify"]}
        )
        notify_prompt = prompt_instructions["triage_rules"]["notify"]
    else:
        # RETRIEVE: Use stored triage_notify rule
        notify_prompt = result.value['prompt']

    # RETRIEVE: Get triage_respond rule
    result = store.get(namespace, "triage_respond")
    if result is None:
        # CREATE: Initialize triage_respond if not exists
        store.put(
            namespace, 
            "triage_respond", 
            {"prompt": prompt_instructions["triage_rules"]["respond"]}
        )
        respond_prompt = prompt_instructions["triage_rules"]["respond"]
    else:
        # RETRIEVE: Use stored triage_respond rule
        respond_prompt = result.value['prompt']
    
    # Build system prompt with memory-enhanced content
    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=ignore_prompt,
        triage_notify=notify_prompt,
        triage_email=respond_prompt,
        examples=examples
    )
    user_prompt = triage_user_prompt.format(
        author=author, 
        to=to, 
        subject=subject, 
        email_thread=email_thread
    )
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    if result.classification == "respond":
        print("📧 Classification: RESPOND - This email requires a response")
        goto = "response_agent"
        update = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Respond to the email {state['email_input']}",
                }
            ]
        }
    elif result.classification == "ignore":
        print("🚫 Classification: IGNORE - This email can be safely ignored")
        update = None
        goto = END
    elif result.classification == "notify":
        print("🔔 Classification: NOTIFY - This email contains important information")
        update = None
        goto = END
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
    return Command(goto=goto, update=update)

# ============================================================================
# Response Agent Tools
# ============================================================================

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    # Placeholder response - in real app would send email
    return f"Email sent to {to} with subject '{subject}'"


@tool
def schedule_meeting(
    attendees: list[str], 
    subject: str, 
    duration_minutes: int, 
    preferred_day: str
) -> str:
    """Schedule a calendar meeting."""
    # Placeholder response - in real app would check calendar and schedule
    return f"Meeting '{subject}' scheduled for {preferred_day} with {len(attendees)} attendees"


@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability for a given day."""
    # Placeholder response - in real app would check actual calendar
    return f"Available times on {day}: 9:00 AM, 2:00 PM, 4:00 PM"

# ============================================================================
# Episodic Memory: Memory Tools
# ============================================================================

# ========== EPISODIC MEMORY: CREATE/STORE Tool ==========
# Agent uses this tool to STORE conversation history, contacts, preferences
manage_memory_tool = create_manage_memory_tool(
    namespace=(
        "email_assistant", 
        "{langgraph_user_id}",
        "collection"
    )
)

# ========== EPISODIC MEMORY: RETRIEVE/SEARCH Tool ==========
# Agent uses this tool to SEARCH for past conversations, contacts, context
search_memory_tool = create_search_memory_tool(
    namespace=(
        "email_assistant",
        "{langgraph_user_id}",
        "collection"
    )
)

# ============================================================================
# Response Agent Prompt (with Memory)
# ============================================================================

agent_system_prompt_memory = """
< Role >
You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.
</ Role >

< Tools >
You have access to the following tools to help manage {name}'s communications and schedule:

1. write_email(to, subject, content) - Send emails to specified recipients
2. schedule_meeting(attendees, subject, duration_minutes, preferred_day) - Schedule calendar meetings
3. check_calendar_availability(day) - Check available time slots for a given day
4. manage_memory - Store any relevant information about contacts, actions, discussion, etc. in memory for future reference
5. search_memory - Search for any relevant information that may have been stored in memory
</ Tools >

< Instructions >
{instructions}
</ Instructions >
"""

# ============================================================================
# Response Agent Prompt Function (with Procedural Memory)
# ============================================================================

def create_prompt(state, config, store):
    """
    Create prompt for response agent.
    
    Uses procedural memory to load agent instructions from store.
    """
    langgraph_user_id = config['configurable']['langgraph_user_id']
    namespace = (langgraph_user_id, )
    
    # ========== PROCEDURAL MEMORY: RETRIEVE ==========
    # Retrieve agent instructions from store
    result = store.get(namespace, "agent_instructions")
    if result is None:
        # ========== PROCEDURAL MEMORY: CREATE ==========
        # Initialize agent_instructions if not exists
        store.put(
            namespace, 
            "agent_instructions", 
            {"prompt": prompt_instructions["agent_instructions"]}
        )
        prompt = prompt_instructions["agent_instructions"]
    else:
        # ========== PROCEDURAL MEMORY: RETRIEVE ==========
        # Use stored agent_instructions
        prompt = result.value['prompt']
    
    return [
        {
            "role": "system", 
            "content": agent_system_prompt_memory.format(
                instructions=prompt, 
                **profile
            )
        }
    ] + state['messages']

# ============================================================================
# Response Agent Setup
# ============================================================================

tools = [
    write_email, 
    schedule_meeting,
    check_calendar_availability,
    manage_memory_tool,  # ========== EPISODIC MEMORY: CREATE/STORE ==========
    search_memory_tool   # ========== EPISODIC MEMORY: RETRIEVE/SEARCH ==========
]

response_agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
    # Use this to ensure the store is passed to the agent 
    store=store
)

# ============================================================================
# Email Agent Graph Assembly
# ============================================================================

email_agent = StateGraph(State)
email_agent = email_agent.add_node("triage_router", triage_router)
email_agent = email_agent.add_node("response_agent", response_agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile(store=store)

# ============================================================================
# Procedural Memory: Prompt Optimizer Setup
# ============================================================================

optimizer = create_multi_prompt_optimizer(
    "openai:gpt-4o",  # Can also use "anthropic:claude-3-5-sonnet-latest"
    kind="prompt_memory",
)

# ============================================================================
# Helper Functions for Prompt Updates
# ============================================================================

def get_prompts_from_store(store, user_id):
    """Retrieve all prompts from store for a given user."""
    namespace = (user_id, )
    # ========== PROCEDURAL MEMORY: RETRIEVE ==========
    # Retrieve all stored prompts for optimizer
    return {
        "main_agent": store.get(namespace, "agent_instructions").value['prompt'],
        "triage-ignore": store.get(namespace, "triage_ignore").value['prompt'],
        "triage-notify": store.get(namespace, "triage_notify").value['prompt'],
        "triage-respond": store.get(namespace, "triage_respond").value['prompt'],
    }


def create_prompts_config(store, user_id):
    """Create prompts configuration for optimizer."""
    prompts_dict = get_prompts_from_store(store, user_id)
    return [
        {
            "name": "main_agent",
            "prompt": prompts_dict["main_agent"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails or schedule events"
        },
        {
            "name": "triage-ignore", 
            "prompt": prompts_dict["triage-ignore"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails should be ignored"
        },
        {
            "name": "triage-notify", 
            "prompt": prompts_dict["triage-notify"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails the user should be notified of"
        },
        {
            "name": "triage-respond", 
            "prompt": prompts_dict["triage-respond"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails should be responded to"
        },
    ]


def update_prompts_in_store(store, user_id, updated_prompts, original_prompts):
    """Update prompts in store based on optimizer output."""
    namespace = (user_id, )
    updates_made = []
    
    for i, updated_prompt in enumerate(updated_prompts):
        old_prompt = original_prompts[i]
        if updated_prompt['prompt'] != old_prompt['prompt']:
            name = old_prompt['name']
            print(f"✅ Updated {name}")
            updates_made.append(name)
            
            # ========== PROCEDURAL MEMORY: CREATE/UPDATE ==========
            # Store updated prompts based on user feedback
            if name == "main_agent":
                store.put(namespace, "agent_instructions", {"prompt": updated_prompt['prompt']})
            elif name == "triage-ignore":
                store.put(namespace, "triage_ignore", {"prompt": updated_prompt['prompt']})
            elif name == "triage-notify":
                store.put(namespace, "triage_notify", {"prompt": updated_prompt['prompt']})
            elif name == "triage-respond":
                store.put(namespace, "triage_respond", {"prompt": updated_prompt['prompt']})
    
    return updates_made


def update_agent_from_feedback(store, user_id, conversation_messages, feedback):
    """
    Update agent prompts based on user feedback.
    
    Args:
        store: Memory store
        user_id: User identifier
        conversation_messages: Previous conversation messages
        feedback: User feedback string
    
    Returns:
        List of updated prompt names
    """
    conversations = [(conversation_messages, feedback)]
    prompts = create_prompts_config(store, user_id)
    
    updated = optimizer.invoke({
        "trajectories": conversations,
        "prompts": prompts
    })
    
    updates_made = update_prompts_in_store(store, user_id, updated, prompts)
    return updates_made

# ============================================================================
# Test Examples
# ============================================================================

if __name__ == "__main__":
    # Configuration
    config = {"configurable": {"langgraph_user_id": "linjia"}}
    
    # Test email
    email_input = {
        "author": "Alice Jones <alice.jones@bar.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Quick question about API documentation",
        "email_thread": """Hi John,

Urgent issue - your service is down. Is there a reason why""",
    }
    
    ######################## TEST 1: Process Email ########################
    print("\n\n\n" + "=" * 60)
    print("Test 1: Process Email")
    print("=" * 60)
    
    # Process email
    # here, we use the orginal/default agent first. 
    response = email_agent.invoke(
        {"email_input": email_input},
        config=config
    )
    
    print("\nResponse Messages:")
    # print the response messages in a nice format with longchain built-in 
    # function pretty_print
    for m in response["messages"]:
        m.pretty_print()
    
    ######################## TEST 2: Check Current Prompts ########################
    print("\n\n\n" + "=" * 60)
    print("Test 2: Check Current Prompts")
    print("=" * 60)
    
    # Check current prompts, these are the default prompts that the agent will use
    namespace = (config['configurable']['langgraph_user_id'], )
    # ========== PROCEDURAL MEMORY: RETRIEVE ==========
    print("\nAgent Instructions:")
    print(store.get(namespace, "agent_instructions").value['prompt'])
    
    print("\nTriage Rules:")
    print("Ignore:", store.get(namespace, "triage_ignore").value['prompt'])
    print("Notify:", store.get(namespace, "triage_notify").value['prompt'])
    print("Respond:", store.get(namespace, "triage_respond").value['prompt'])
    
    # Note: store.get() returns an Item object, not a message object
    # So we access the value directly instead of using pretty_print()
    # The prompts are already printed above in a readable format
    
    
    ######################## TEST 3: Update Prompts from Feedback ########################
    # update the prompt through the prompt optimizer
    print("\n\n\n" + "=" * 60)
    print("Test 3: Update Prompts from Feedback")
    print("=" * 60)
    
    # Update from feedback
    feedback = "Always sign your emails `John Doe`"
    print(f"\nFeedback: {feedback}")
    
    # print the main agent's prompt before the update
    print("\nMain Agent Prompt Before Update:")
    print(store.get(namespace, "agent_instructions").value['prompt'])
    
    
    updates = update_agent_from_feedback(
        store, 
        config['configurable']['langgraph_user_id'],
        response['messages'],
        feedback
    )
    
    print(f"\nUpdated prompts: {updates}")
    
    # print the main agent's prompt after the update
    print("\nMain Agent Prompt After Update:")
    print(store.get(namespace, "agent_instructions").value['prompt'])
    
    
    print("\n" + "=" * 60)
    print("Test 4: Process Email Again (with Updated Prompts)")
    print("=" * 60)
    
    # Process again with updated prompts
    response2 = email_agent.invoke(
        {"email_input": email_input},
        config=config
    )
    
    print("\nResponse Messages:")
    for m in response2["messages"]:
        m.pretty_print()
    
    print("\n" + "=" * 60)
    print("Test 5: Update Triage Rules")
    print("=" * 60)
    
    # Update triage rules
    feedback2 = "Ignore any emails from Alice Jones"
    print(f"\nFeedback: {feedback2}")
    
    updates2 = update_agent_from_feedback(
        store,
        config['configurable']['langgraph_user_id'],
        response2['messages'],
        feedback2
    )
    
    print(f"\nUpdated prompts: {updates2}")
    
    print("\n" + "=" * 60)
    print("Test 6: Process Email Again (Alice Jones should be ignored)")
    print("=" * 60)
    
    # Process again - should now ignore Alice Jones
    response3 = email_agent.invoke(
        {"email_input": email_input},
        config=config
    )
    
    print("\n" + "=" * 60)
    print("Final Triage Ignore Rule:")
    print("=" * 60)
    # ========== PROCEDURAL MEMORY: RETRIEVE ==========
    print(store.get(namespace, "triage_ignore").value['prompt'])

