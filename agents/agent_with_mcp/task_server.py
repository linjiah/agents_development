"""
FastMCP Task Management Server

This MCP server provides task management capabilities (create, list, complete, delete tasks).
It runs as a subprocess started by the MCP client (not independently).

Following the multi-server architecture pattern, this server is independent and composable.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("TaskManager")

# In-memory task storage (in production, use a database)
# Format: {task_id: {"title": str, "description": str, "status": str, "created_at": str}}
_tasks = {}
_next_task_id = 1

# Task storage file path
SCRIPT_DIR = Path(__file__).parent.absolute()
TASKS_FILE = SCRIPT_DIR / "tasks.json"


def _load_tasks():
    """Load tasks from JSON file if it exists."""
    global _tasks, _next_task_id
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _tasks = data.get('tasks', {})
                _next_task_id = data.get('next_id', 1)
        except Exception as e:
            print(f"Error loading tasks: {e}")
            _tasks = {}
            _next_task_id = 1


def _save_tasks():
    """Save tasks to JSON file."""
    try:
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'tasks': _tasks,
                'next_id': _next_task_id
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving tasks: {e}")


# Load tasks on startup
_load_tasks()


@mcp.tool()
def create_task(title: str, description: Optional[str] = None) -> dict:
    """
    Creates a new task with the given title and optional description.
    
    Args:
        title: The title of the task (required).
        description: Optional description of the task.
    
    Returns:
        A dictionary containing the created task information or an error message.
    """
    global _tasks, _next_task_id
    
    if not title or not title.strip():
        return {"error": "Task title cannot be empty."}
    
    task_id = str(_next_task_id)
    _next_task_id += 1
    
    task = {
        "id": task_id,
        "title": title.strip(),
        "description": description.strip() if description else "",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    _tasks[task_id] = task
    _save_tasks()
    
    return {
        "success": True,
        "task": task,
        "message": f"Task '{title}' created successfully with ID {task_id}."
    }


@mcp.tool()
def list_tasks(status: Optional[str] = None) -> dict:
    """
    Lists all tasks, optionally filtered by status.
    
    Args:
        status: Optional filter by status ("pending", "completed", or None for all).
    
    Returns:
        A dictionary containing the list of tasks matching the filter.
    """
    if status:
        status = status.lower()
        if status not in ["pending", "completed"]:
            return {"error": f"Invalid status filter. Must be 'pending' or 'completed'."}
        
        # Filter tasks by status (status is always stored in lowercase)
        filtered_tasks = {
            task_id: task 
            for task_id, task in _tasks.items() 
            if task.get("status", "pending") == status
        }
        tasks_list = list(filtered_tasks.values())
    else:
        tasks_list = list(_tasks.values())
    
    # Sort by creation date (newest first)
    tasks_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "success": True,
        "count": len(tasks_list),
        "tasks": tasks_list,
        "message": f"Found {len(tasks_list)} task(s)" + (f" with status '{status}'" if status else "")
    }


@mcp.tool()
def complete_task(task_id: str) -> dict:
    """
    Marks a task as completed.
    
    Args:
        task_id: The ID of the task to complete.
    
    Returns:
        A dictionary containing the updated task information or an error message.
    """
    if task_id not in _tasks:
        return {"error": f"Task with ID '{task_id}' not found."}
    
    task = _tasks[task_id]
    
    if task.get("status") == "completed":
        return {"error": f"Task '{task.get('title')}' is already completed."}
    
    task["status"] = "completed"
    task["completed_at"] = datetime.now().isoformat()
    _save_tasks()
    
    return {
        "success": True,
        "task": task,
        "message": f"Task '{task.get('title')}' marked as completed."
    }


@mcp.tool()
def delete_task(task_id: str) -> dict:
    """
    Deletes a task by its ID.
    
    Args:
        task_id: The ID of the task to delete.
    
    Returns:
        A dictionary containing a success message or an error message.
    """
    if task_id not in _tasks:
        return {"error": f"Task with ID '{task_id}' not found."}
    
    task_title = _tasks[task_id].get("title", "Unknown")
    del _tasks[task_id]
    _save_tasks()
    
    return {
        "success": True,
        "message": f"Task '{task_title}' (ID: {task_id}) deleted successfully."
    }


@mcp.tool()
def get_task(task_id: str) -> dict:
    """
    Retrieves a specific task by its ID.
    
    Args:
        task_id: The ID of the task to retrieve.
    
    Returns:
        A dictionary containing the task information or an error message.
    """
    if task_id not in _tasks:
        return {"error": f"Task with ID '{task_id}' not found."}
    
    return {
        "success": True,
        "task": _tasks[task_id]
    }


@mcp.prompt()
def plan_trip_prompt(destination: str, duration_in_days: str) -> str:
    """
    Generates a comprehensive travel plan and creates tasks for each step.
    This is the best choice when a user wants to plan a trip to a specific destination.
    
    Args:
        destination: The destination city or location for the trip (e.g., "Paris").
        duration_in_days: The number of days for the trip (e.g., "5").
    """
    return f"""
    You are acting as a helpful travel planning assistant. Your goal is to create a comprehensive travel plan for a user and break it down into actionable tasks.

    The user wants to plan a trip to "{destination}" for {duration_in_days} days.

    To accomplish this, follow these steps:
    1. First, use your general knowledge to formulate a detailed {duration_in_days}-day itinerary for "{destination}". Consider:
       - Must-see attractions and landmarks
       - Local cuisine and restaurants
       - Cultural experiences
       - Transportation needs
       - Accommodation considerations
       - Budget planning
    
    2. Once you have the itinerary, break it down into specific, actionable tasks. For each major activity or preparation step, use the create_task tool to add it to the task list.
    
    3. Create tasks for:
       - Research and booking (flights, hotels, activities)
       - Preparation items (packing, documents, insurance)
       - Daily itinerary items (specific attractions, restaurants, experiences)
       - Post-trip tasks (photo organization, reviews, expense tracking)
    
    4. After creating all tasks, provide a summary of the travel plan and list all the tasks you've created so the user can track their trip planning progress.
    
    Remember: Use the create_task tool multiple times to create individual tasks for each step of the trip planning process.
    """


# Resource: Meeting Notes
# This resource exposes meeting notes as a discoverable data source
# The agent can read this file to get action items and create tasks from them
# Using absolute file path for file:// URI scheme
SCRIPT_DIR = Path(__file__).parent.absolute()
NOTES_FILE = SCRIPT_DIR / "meeting_notes.txt"
# Use absolute path in URI for proper file:// scheme format
meeting_notes_uri = f"file://{NOTES_FILE.as_posix()}"

@mcp.resource(meeting_notes_uri)
def get_meeting_notes() -> str:
    """
    Returns the contents of the meeting notes file.
    This file contains action items, decisions, and next steps from team meetings.
    The agent can use this to create tasks based on meeting action items.
    """
    
    try:
        if NOTES_FILE.exists():
            return NOTES_FILE.read_text(encoding="utf-8")
        else:
            return "Meeting notes file not found."
    except Exception as e:
        return f"Error reading meeting notes: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

