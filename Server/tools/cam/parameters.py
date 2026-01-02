"""
CAM Parameter Tools

This module contains tools for parameter modification:
- modify_toolpath_parameter: Modify toolpath parameters
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.request_handler import send_request
from core.config import get_endpoints, get_headers, get_timeout

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register parameter tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(modify_toolpath_parameter)

def modify_toolpath_parameter(toolpath_id: str, parameter_name: str, value: str):
    """
    You can modify a parameter value for a specific CAM toolpath operation.
    
    Use this to update feeds, speeds, geometry settings, or other editable parameters.
    Always check get_toolpath_details first to see which parameters are editable!
    
    CRITICAL: 
    - The parameter must be marked as editable (editable: true in get_toolpath_details)
    - The value must be within the min/max constraints if they exist
    - Read-only parameters will return a READ_ONLY error
    
    Common parameter names you can modify:
    - spindle_speed: Spindle RPM (e.g., "12000")
    - cutting_feedrate: Feed rate in mm/min (e.g., "1500")
    - plunge_feedrate: Plunge feed rate (e.g., "500")
    - stepover: Stepover percentage or distance (e.g., "40" for 40%)
    - stepdown: Axial depth of cut (e.g., "2.0")
    
    Example:
    {
        "toolpath_id": "op_001",
        "parameter_name": "spindle_speed",
        "value": "12000"
    }
    
    Possible errors:
    - TOOLPATH_NOT_FOUND: The toolpath_id doesn't exist
    - INVALID_VALUE: Value is wrong type or outside valid range
    - READ_ONLY: Parameter cannot be modified
    - PARAMETER_NOT_FOUND: The parameter_name doesn't exist for this operation
    
    Typical use cases: Optimizing feeds and speeds, adjusting stepover/stepdown for better surface finish.
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_toolpath_parameter']}/{toolpath_id}/parameter"
        payload = {
            "parameter_name": parameter_name,
            "value": value
        }
        headers = get_headers()
        response = requests.post(endpoint, json=payload, headers=headers, timeout=get_timeout())
        return response.json()
    except requests.ConnectionError:
        return {
            "error": True,
            "message": "Cannot connect to Fusion 360. Ensure the add-in is running.",
            "code": "CONNECTION_ERROR"
        }
    except requests.Timeout:
        return {
            "error": True,
            "message": "Request to Fusion 360 timed out. The add-in may be busy.",
            "code": "TIMEOUT_ERROR"
        }
    except Exception as e:
        logging.error("Modify toolpath parameter failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to modify parameter: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }