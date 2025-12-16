"""
Compatibility utilities for Google ADK agents.

This module handles Python version compatibility issues, particularly for Python 3.9.
"""

import sys
import warnings

def setup_compatibility():
    """
    Set up compatibility fixes for Python 3.9 and suppress warnings.
    
    This function should be called at the start of any script that uses
    google-generativeai to avoid importlib.metadata errors and warnings.
    """
    # Suppress warnings for Python 3.9 compatibility
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*urllib3.*")
    warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")
    
    # Handle importlib.metadata compatibility issue for Python 3.9
    if sys.version_info < (3, 10):
        try:
            import importlib.metadata
            if not hasattr(importlib.metadata, 'packages_distributions'):
                # Workaround for Python 3.9
                try:
                    import importlib_metadata
                    importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
                except ImportError:
                    # importlib_metadata not installed, but that's okay
                    # The error will be caught and handled gracefully
                    pass
        except (ImportError, AttributeError):
            # If there's an issue, continue anyway
            pass

