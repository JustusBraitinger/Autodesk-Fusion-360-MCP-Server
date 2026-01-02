"""
Debug Control Tools

This module contains debug control tools:
- toggle_response_interceptor: Toggle response interceptor for debugging
"""

import logging
from mcp.server.fastmcp import FastMCP
from core import interceptor

def register_tools(mcp_instance: FastMCP):
    """Register debug control tools with the MCP server."""
    # Register all tools in this module
    mcp_instance.tool()(toggle_response_interceptor)

def toggle_response_interceptor():
    """
    Toggle the response interceptor for debugging HTTP communication.
    
    When enabled, the interceptor logs all HTTP responses from Fusion 360 to the console
    with formatted JSON output, endpoint URLs, and HTTP methods. This is useful for
    debugging communication issues between the MCP Server and Fusion 360 Add-In.
    
    The interceptor is disabled by default. Each call toggles the state:
    - If disabled → becomes enabled
    - If enabled → becomes disabled
    
    Returns:
        dict: Contains the new state after toggling
            - enabled (bool): True if interceptor is now enabled, False if disabled
            - message (str): Human-readable status message
    
    Example response when enabling:
    {
        "enabled": true,
        "message": "Response interceptor enabled. HTTP responses will be logged to console."
    }
    
    Example response when disabling:
    {
        "enabled": false,
        "message": "Response interceptor disabled. HTTP responses will not be logged."
    }
    
    Requirements: 4.1, 4.2
    """
    new_state = interceptor.toggle_interceptor()
    
    if new_state:
        message = "Response interceptor enabled. HTTP responses will be logged to console."
    else:
        message = "Response interceptor disabled. HTTP responses will not be logged."
    
    return {
        "enabled": new_state,
        "message": message
    }