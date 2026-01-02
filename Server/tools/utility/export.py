"""
Utility Export Tools

This module contains export functionality tools:
- export_step: Export model as STEP file
- export_stl: Export model as STL file
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
    """Register export tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(export_step)
    mcp.tool()(export_stl)

def export_step(name : str):
    """Exportiert das Modell als STEP-Datei."""
    try:
        endpoint = get_endpoints("utility")["export_step"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STEP failed: %s", e)
        raise

def export_stl(name : str):
    """Exportiert das Modell als STL-Datei."""
    try:
        endpoint = get_endpoints("utility")["export_stl"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STL failed: %s", e)
        raise