"""
Retry utilities for handling rate limits and API errors.
"""

import time
import random
from typing import Callable, Any, Optional
from functools import wraps

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Check if it's a rate limit/quota error
                    is_rate_limit = (
                        "429" in str(e) or
                        "quota" in error_msg or
                        "rate limit" in error_msg or
                        "retry" in error_msg
                    )
                    
                    # Only retry on rate limit errors or if it's the last attempt
                    if not is_rate_limit and attempt < max_retries:
                        raise
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        if jitter:
                            # Add random jitter (0 to 1 second)
                            actual_delay = delay + random.uniform(0, 1)
                        else:
                            actual_delay = delay
                        
                        actual_delay = min(actual_delay, max_delay)
                        
                        print(f"⚠️  Rate limit hit. Retrying in {actual_delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(actual_delay)
                        
                        # Increase delay for next attempt
                        delay *= exponential_base
                    else:
                        # Last attempt failed
                        raise
                        
        return wrapper
    return decorator

