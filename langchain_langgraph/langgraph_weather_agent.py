import os
import time
import requests
from pathlib import Path
from requests.exceptions import RequestException, Timeout
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from dotenv import load_dotenv

# --- Configuration & Constants ---
WEATHER_CODE_MAP = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    75: "Heavy snow", 95: "Thunderstorm", 99: "Thunderstorm with hail"
}

OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HTTP_TIMEOUT_SECS = 8
RETRY_ATTEMPTS = 2
RETRY_BACKOFF_SECS = 0.6

# --- Network Resilience Logic ---
def _request_with_retries(method: str, url: str, **kwargs) -> requests.Response:
    """Make an HTTP request with retries and backoff."""
    last_exc = None
    for attempt in range(RETRY_ATTEMPTS + 1):
        try:
            return requests.request(method, url, timeout=HTTP_TIMEOUT_SECS, **kwargs)
        except (RequestException, Timeout) as exc:
            last_exc = exc
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECS * (attempt + 1))
            else:
                raise last_exc

# --- Tools ---
def geocode_city(name: str) -> dict:
    """Look up latitude/longitude for a city using Open-Meteo."""
    params = {"name": name, "count": 1, "format": "json"}
    resp = _request_with_retries("GET", OPEN_METEO_GEOCODE_URL, params=params)
    data = resp.json()
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Could not geocode city '{name}'.")
    r0 = results[0]
    return {"city": r0["name"], "lat": r0["latitude"], "lon": r0["longitude"]}

def current_weather(lat: float, lon: float) -> dict:
    """Fetch current weather for coordinates using Open-Meteo."""
    params = {
        "latitude": lat, "longitude": lon,
        "current": ["temperature_2m", "weather_code", "wind_speed_10m"],
        "timezone": "auto",
    }
    resp = _request_with_retries("GET", OPEN_METEO_FORECAST_URL, params=params)
    data = resp.json()
    cur = data.get("current")
    if not cur:
        raise ValueError("No weather data returned.")
    return {
        "temperature": cur["temperature_2m"],
        "weather_code": cur["weather_code"],
        "windspeed": cur["wind_speed_10m"]
    }

# --- Formatting ---
def format_weather_summary(city: str, payload: dict) -> str:
    """Decodes weather codes and returns a human-readable one-liner."""
    code = payload["weather_code"]
    desc = WEATHER_CODE_MAP.get(code, f"Unknown weather code {code}")
    temp_c = payload["temperature"]
    wind = payload["windspeed"]
    return f"{city}: {desc}, {round(temp_c)}°C, wind {round(wind, 1)} m/s"

# --- LangGraph Nodes & State ---
class MyMessagesState(MessagesState):
    pass

# Load .env located alongside this file
project_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=project_dir / ".env")
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not set in environment or .env file.")

llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
llm_with_tools = llm.bind_tools([geocode_city, current_weather])

def tool_calling_llm(state: MyMessagesState):
    system = SystemMessage(content=(
        "You are a helpful weather assistant. "
        "When the user mentions cities, call geocode_city for each city, then call current_weather. "
        "Prefer Celsius unless the user explicitly requests Fahrenheit/imperial."
    ))
    response = llm_with_tools.invoke([system] + state["messages"])
    return {"messages": [response]}

def compose_final_answer(state: MyMessagesState):
    system = SystemMessage(content=(
        "Summarize any fetched weather results in plain language. "
        "Output one line per city, with condition, temperature, and wind. "
        "If any city failed, acknowledge it clearly instead of guessing."
    ))
    response = llm.invoke([system] + state["messages"])
    return {"messages": [response]}

# --- Graph Construction ---
builder = StateGraph(MyMessagesState)

builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([geocode_city, current_weather]))
builder.add_node("compose_final", compose_final_answer)

builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges(
    "tool_calling_llm",
    tools_condition,
    {"tools": "tools", END: "compose_final"}
)
builder.add_edge("tools", "tool_calling_llm")  # Cyclic loop for sequential tool calls
builder.add_edge("compose_final", END)

graph = builder.compile()

# --- Visualization Helpers ---
def visualize_graph():
    """
    Print graph structure in ASCII and Mermaid (for markdown).
    If graphviz is available, also render a PNG.
    """
    g = graph.get_graph()

    print("\n--- Graph (ASCII) ---")
    print(g.draw_ascii())

    print("\n--- Graph (Mermaid) ---")
    print(g.draw_mermaid())

    # Optional: render PNG if graphviz is installed
    try:
        g.draw_mermaid_png("langgraph_weather_agent.png")
        print("\nSaved PNG to langgraph_weather_agent.png")
    except Exception as exc:  # graphviz may be missing
        print(f"\nPNG not generated (graphviz likely missing): {exc}")


# --- Execution Function ---
def run_case(prompt: str, title: str):
    print("\n" + "=" * 65)
    print(title)
    print("=" * 65)
    res = graph.invoke({"messages": [HumanMessage(content=prompt)]})
    for m in res["messages"]:
        if isinstance(m, AIMessage) and not m.tool_calls:
            print(f"[ASSISTANT] {m.content}")

if __name__ == "__main__":
    run_case("Weather in Paris and London please.", "Test: Multi-city request")
    visualize_graph()