"""
FastMCP Weather Server

This MCP server provides weather information via the OpenWeatherMap API.
It runs as a subprocess started by the MCP client (not independently).
"""

import requests
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# OpenWeatherMap API key
OPENWEATHERMAP_API_KEY = "8eb362c1f846790838c8783a06310718"

# Initialize FastMCP server
mcp = FastMCP("WeatherAssistant")


@mcp.tool()
def get_weather(location: str) -> dict:
    """
    Fetches the current weather for a specified location using the OpenWeatherMap API.

    Args:
        location: The city name and optional country code (e.g., "London,uk").

    Returns:
        A dictionary containing weather information or an error message.
    """
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "location": data["name"],
            "weather": data["weather"][0]["description"],
            "temperature_celsius": f"{data['main']['temp']}°C",
            "feels_like_celsius": f"{data['main']['feels_like']}°C",
            "humidity": f"{data['main']['humidity']}%",
            "wind_speed_mps": f"{data['wind']['speed']} m/s"
        }

    except requests.exceptions.HTTPError as http_err:
        status_code = response.status_code
        if status_code == 404:
            return {"error": f"Could not find weather data for '{location}'. Please check the location name."}
        elif status_code == 401:
            return {"error": "Authentication failed. The API key may be invalid or inactive."}
        return {"error": f"HTTP error {status_code}: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Network error: {req_err}"}
    except (KeyError, IndexError) as e:
        return {"error": f"Unexpected API response format: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


@mcp.prompt()
def compare_weather_prompt(location_a: str, location_b: str) -> str:
    """
    Generates a clear, comparative summary of the weather between two specified locations.
    This is the best choice when a user asks to compare, contrast, or see the difference in weather between two places.
    
    Args:
        location_a: The first city for comparison (e.g., "London").
        location_b: The second city for comparison (e.g., "Paris").
    """
    return f"""
    You are acting as a helpful weather analyst. Your goal is to provide a clear and easy-to-read comparison of the weather in two different locations for a user.

    The user wants to compare the weather between "{location_a}" and "{location_b}".

    To accomplish this, follow these steps:
    1.  First, gather the necessary weather data for both "{location_a}" and "{location_b}".
    2.  Once you have the weather data for both locations, DO NOT simply list the raw results.
    3.  Instead, synthesize the information into a concise summary. Your final response should highlight the key differences, focusing on temperature, the general conditions (e.g., 'sunny' vs 'rainy'), and wind speed.
    4.  Present the comparison in a structured format, like a markdown table or a clear bulleted list, to make it easy for the user to understand at a glance.
    """


# Resource: Delivery Log
# This resource exposes a delivery log file as a discoverable data source
# The agent can read this file to get order information and destination cities
# Using absolute file path for file:// URI scheme
script_dir = Path(__file__).parent.absolute()
log_file = script_dir / "delivery_log.txt"
# Use absolute path in URI for proper file:// scheme format
delivery_log_uri = f"file://{log_file.as_posix()}"

@mcp.resource(delivery_log_uri)
def get_delivery_log() -> str:
    """
    Returns the contents of the delivery log file.
    This file contains order numbers and their delivery destinations (cities).
    Format: "Order #XXXXX: Delivered to [City]"
    """
    
    try:
        if log_file.exists():
            return log_file.read_text(encoding="utf-8")
        else:
            return "Delivery log file not found."
    except Exception as e:
        return f"Error reading delivery log: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")