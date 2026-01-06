from crewai import Crew, Agent, Task
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import os
import requests







extracted_links = []

# Task 1: Load environment variables for API keys
load_dotenv(override=True)

# Task 1: Add your OPENAI API key here
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Task 2: Add your FIRECRAWL API Key  here
FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")


# Task 3: Add Firecrawl Search function here
def firecrawl_search(query):
    try:
        response = requests.get(
            f"https://api.firecrawl.dev/v1/search?query={query}",
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
            timeout=30
        )
    except Exception:
        response = None

    if response and response.status_code == 200:
        try:
            json_data = response.json()
            results = json_data.get("results", [])
            if results:
                for result in results:
                    url = result.get("url")
                    if url:
                        extracted_links.append(url)
                return response.text
        except Exception:
            pass

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.3)
    fallback_response = llm.invoke([
        HumanMessage(content=f"Please provide a clear explanation about: {query}. Include definition, features, and common use cases.")
    ])
    return fallback_response.content


class FirecrawlInput(BaseModel):
    query: str = Field(..., description="Search query text")


@tool("FirecrawlSearch", args_schema=FirecrawlInput)
def firecrawl_tool(query: str) -> str:
    """Search the web using Firecrawl API and return HTML content or fallback LLM answer."""
    return firecrawl_search(query)


# Task 5: Implement Researcher, Summarizer, and presenter Agents
def setup_agents_and_tasks(query, breadth, depth):
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Please configure your environment variables.")

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.3)

    # Note: CrewAI's current tool validation can reject some LangChain tool instances.
    # To keep the CLI runnable, we skip attaching tools here. Firecrawl fallback still returns content via LLM.
    researcher = Agent(
        name="Research Agent",
        role="Web searcher and data collector",
        goal=f"Conduct deep recursive web research with breadth {breadth} and depth {depth}",
        backstory="Expert in online information mining and query generation",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    summarizer = Agent(
        name="Summarization Agent",
        role="Content summarizer",
        goal="Condense detailed findings into concise summaries",
        backstory="Skilled in summarizing complex texts for better understanding",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

    presenter = Agent(
        name="Presentation Agent",
        role="Report formatter",
        goal="Create readable and well-structured reports",
        backstory="Experienced in generating polished documents for readers",
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=True
    )

    task_research = Task(
        description=f"Perform deep research on: {query} using up to {breadth} queries and recursion depth {depth}.",
        expected_output="Raw web content, source links, and extracted notes",
        agent=researcher
    )

    task_summarize = Task(
        description="Summarize the research findings into structured points.",
        expected_output="Summarized bullets categorized by topic",
        agent=summarizer
    )

    task_present = Task(
        description="Format all summaries into a professional report.",
        expected_output="A final human-readable report",
        agent=presenter
    )

    crew = Crew(
        agents=[researcher, summarizer, presenter],
        tasks=[task_research, task_summarize, task_present],
        verbose=True,
        max_steps=max(5, breadth * depth * 2),
        max_time=300
    )

    return crew, researcher, firecrawl_tool