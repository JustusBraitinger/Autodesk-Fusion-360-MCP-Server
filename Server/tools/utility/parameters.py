"""
Utility Parameter Management Tools

This module contains parameter management tools:
- count: Count parameters in current model
- list_parameters: List all parameters in current model
- change_parameter: Change parameter value
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.request_handler import send_request
from core.config import get_endpoints, get_headers

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register parameter management tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(count)
    mcp.tool()(list_parameters)
    mcp.tool()(change_parameter)

def count():
    """Zählt die Parameter im aktuellen Modell."""
    try:
        endpoint = get_endpoints("utility")["count_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Count failed: %s", e)
        raise

def list_parameters():
    """Listet alle Parameter im aktuellen Modell auf."""
    try:
        endpoint = get_endpoints("utility")["list_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("List parameters failed: %s", e)
        raise

def change_parameter(name: str, value: str):
    """Ändert den Wert eines Parameters."""
    try:
        endpoint = get_endpoints("utility")["change_parameter"]
        payload = {
            "name": name,
            "value": value
        }
        headers = get_headers()
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Change parameter failed: %s", e)
        raise