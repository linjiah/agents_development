"""
Calculator Tool for Agents

This module provides a safe calculator tool that can be used by agents.
"""

import re
from typing import Union

class CalculatorTool:
    """Tool for performing mathematical calculations."""
    
    def __init__(self):
        """Initialize the calculator tool."""
        # Allowed operations and functions
        self.allowed_names = {
            k: v for k, v in __builtins__.items()
        }
        self.allowed_names.update({
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        })
    
    def calculate(self, expression: str) -> Union[float, int, str]:
        """
        Safely evaluate a mathematical expression.
        
        Args:
            expression: Mathematical expression as a string
            
        Returns:
            Result of the calculation or error message
        """
        try:
            # Remove whitespace
            expression = expression.strip()
            
            # Basic validation - only allow numbers, operators, and parentheses
            if not re.match(r'^[0-9+\-*/().\s]+$', expression):
                return "Error: Invalid characters in expression. Only numbers and basic operators (+, -, *, /) are allowed."
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, self.allowed_names)
            
            # Return as integer if it's a whole number
            if isinstance(result, float) and result.is_integer():
                return int(result)
            
            return result
            
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def format_result(self, expression: str, result: Union[float, int, str]) -> str:
        """Format the calculation result for display."""
        if isinstance(result, str) and result.startswith("Error"):
            return result
        
        return f"{expression} = {result}"

# Example usage
if __name__ == "__main__":
    calc = CalculatorTool()
    
    test_expressions = [
        "2 + 2",
        "10 * 5",
        "100 / 4",
        "2 ** 8",
        "sqrt(16)",  # This will fail - sqrt not in allowed functions
    ]
    
    for expr in test_expressions:
        result = calc.calculate(expr)
        print(calc.format_result(expr, result))

