"""
Request Interceptor Module

Provides state management and logging functionality for intercepting
HTTP responses between the MCP Server and Fusion 360 Add-In.

Requirements: 1.1, 1.4, 4.1, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3
"""

import json
from typing import Any

import requests

# Global interceptor state - defaults to False (disabled)
_interceptor_enabled: bool = False


def is_interceptor_enabled() -> bool:
    """
    Check if the interceptor is currently enabled.
    
    Returns:
        bool: True if interceptor is enabled, False otherwise
    """
    return _interceptor_enabled


def set_interceptor_enabled(enabled: bool) -> None:
    """
    Enable or disable the interceptor at runtime.
    
    Args:
        enabled: True to enable interceptor, False to disable
    """
    global _interceptor_enabled
    _interceptor_enabled = enabled


def toggle_interceptor() -> bool:
    """
    Toggle the interceptor state and return the new state.
    
    Returns:
        bool: The new state after toggling (True if now enabled, False if now disabled)
    """
    global _interceptor_enabled
    _interceptor_enabled = not _interceptor_enabled
    return _interceptor_enabled


def log_response(endpoint: str, response_data: Any, method: str = "POST") -> None:
    """
    Log an HTTP response to the console with formatted output.
    
    Formats output with separator lines, endpoint URL, HTTP method,
    and indented JSON. Handles non-JSON data gracefully with error message.
    
    Args:
        endpoint: The URL that was called
        response_data: The response data (dict, list, or raw)
        method: HTTP method used (POST/GET), defaults to "POST"
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    # Top separator
    print("═" * 65)
    print(f"[INTERCEPTOR] {method} {endpoint}")
    # Middle separator
    print("─" * 65)
    
    try:
        # Attempt to format as indented JSON
        if isinstance(response_data, (dict, list)):
            formatted_json = json.dumps(response_data, indent=4)
            print(formatted_json)
        elif isinstance(response_data, str):
            # Try to parse string as JSON
            parsed = json.loads(response_data)
            formatted_json = json.dumps(parsed, indent=4)
            print(formatted_json)
        else:
            # For other types, try to convert to JSON
            formatted_json = json.dumps(response_data, indent=4)
            print(formatted_json)
    except (json.JSONDecodeError, TypeError) as e:
        # Handle non-JSON data gracefully
        print(f"[ERROR] Failed to parse JSON response: {e}")
        # Show raw response snippet (truncate if too long)
        raw_str = str(response_data)
        if len(raw_str) > 500:
            raw_str = raw_str[:500] + "..."
        print(f"Raw response: {raw_str}")
    
    # Bottom separator
    print("═" * 65)


def intercept_response(endpoint: str, response: requests.Response, method: str = "POST") -> Any:
    """
    Process a response, optionally logging it, and return the JSON data.
    
    Checks if the interceptor is enabled and logs the response if so.
    Parses and returns the JSON response data unchanged.
    
    Args:
        endpoint: The URL that was called
        response: The requests.Response object
        method: HTTP method used (POST/GET), defaults to "POST"
        
    Returns:
        The parsed JSON response data
        
    Requirements: 3.1, 3.2, 3.3
    """
    # Parse JSON response data
    try:
        response_data = response.json()
    except (json.JSONDecodeError, ValueError) as e:
        # If JSON parsing fails, log error if interceptor enabled and re-raise
        if is_interceptor_enabled():
            log_response(endpoint, f"Failed to parse: {response.text}", method)
        raise
    
    # Log response if interceptor is enabled
    if is_interceptor_enabled():
        log_response(endpoint, response_data, method)
    
    # Return the parsed data unchanged
    return response_data
