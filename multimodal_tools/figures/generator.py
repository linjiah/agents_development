"""
Figure and Diagram Generation

Supports multiple diagram types:
1. Mermaid diagrams (flowchart, sequence, class, etc.)
2. ASCII art diagrams
3. PlantUML (future enhancement)
"""

def generate_flowchart_mermaid(description: str) -> str:
    """Generate a Mermaid flowchart."""
    return (
        "```mermaid\n"
        "flowchart TD\n"
        f"  A[Start] --> B[{description}]\n"
        "  B --> C[Process]\n"
        "  C --> D[Result]\n"
        "```"
    )

def generate_sequence_mermaid(description: str) -> str:
    """Generate a Mermaid sequence diagram."""
    return (
        "```mermaid\n"
        "sequenceDiagram\n"
        "    participant User\n"
        "    participant System\n"
        "    User->>System: Request\n"
        f"    System->>System: {description}\n"
        "    System-->>User: Response\n"
        "```"
    )

def generate_class_mermaid(description: str) -> str:
    """Generate a Mermaid class diagram."""
    return (
        "```mermaid\n"
        "classDiagram\n"
        "    class MainClass {\n"
        f"        +{description}\n"
        "    }\n"
        "```"
    )

def generate_figure(description: str, format: str = "mermaid", diagram_type: str = "flowchart") -> str:
    """
    Generate a figure/diagram based on description.
    
    Args:
        description: What to visualize
        format: Output format ("mermaid" or "ascii")
        diagram_type: Type of diagram ("flowchart", "sequence", "class")
    
    Returns:
        Diagram as text (Mermaid code or ASCII)
    
    Examples:
        >>> generate_figure("User login process", "mermaid", "flowchart")
        "```mermaid\nflowchart TD\n..."
    """
    if format == "mermaid":
        if diagram_type == "flowchart":
            return generate_flowchart_mermaid(description)
        elif diagram_type == "sequence":
            return generate_sequence_mermaid(description)
        elif diagram_type == "class":
            return generate_class_mermaid(description)
        else:
            # Default to flowchart
            return generate_flowchart_mermaid(description)
    
    elif format == "ascii":
        return (
            f"[ASCII Diagram]\n"
            f"┌─────────────────┐\n"
            f"│   {description:^15}   │\n"
            f"└─────────────────┘\n"
            f"        │\n"
            f"        ▼\n"
            f"┌─────────────────┐\n"
            f"│     Result      │\n"
            f"└─────────────────┘\n"
        )
    
    else:
        return f"[Figure]\nDescription: {description}\nFormat: {format}\n(Use a diagramming tool to render.)"

