"""
CAM Tool Management

This module contains tools for cutting tool management:
- list_cam_tools: List all cutting tools
- get_tool_info: Get detailed tool information
- list_tool_libraries: List available tool libraries
- list_library_tools: List tools in a specific library
- get_tool_details: Get detailed tool specifications
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.config import get_endpoints, get_timeout
from core import interceptor

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register tool management tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(list_cam_tools)
    mcp.tool()(get_tool_info)
    mcp.tool()(list_tool_libraries)
    mcp.tool()(list_library_tools)
    mcp.tool()(get_tool_details)

def list_cam_tools():
    """
    You can list all cutting tools available in the CAM tool libraries.
    
    This shows all tools from all tool libraries in the current Fusion 360 document.
    Use this to discover available tools before getting detailed information with get_tool_info().
    
    Each tool includes: id, name, type, tool number, and basic geometry (diameter, length).
    Tools are organized by their parent library.
    
    IMPORTANT: If no tools are found, the document may not have any tool libraries loaded.
    
    Example response:
    {
        "libraries": [
            {
                "name": "My Tool Library",
                "id": "lib_001", 
                "tools": [
                    {
                        "id": "tool_001",
                        "name": "6mm Flat Endmill",
                        "type": "flat end mill",
                        "number": 1,
                        "diameter": 6.0,
                        "overall_length": 50.0
                    }
                ]
            }
        ],
        "total_count": 1,
        "message": null
    }
    
    Typical use cases: Discovering available tools, finding tool IDs for detailed inspection.
    """
    try:
        endpoint = get_endpoints("cam")["cam_tools"]
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
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
        logging.error("List CAM tools failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to list tools: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def get_tool_info(tool_id: str):
    """
    You can get usage information about a specific cutting tool across all operations.
    
    Use this to see which operations use a specific tool and get tool specifications.
    You get the tool_id from list_cam_tools() or from get_toolpath_details() (in the tool section).
    
    Returns tool usage data including:
    - Tool info: id, name, type, diameter, overall_length
    - Operations using this tool: list of operation names and IDs
    - Usage count across the document
    
    IMPORTANT: Tool dimensions are in the document's unit system (typically mm).
    Remember: In Fusion 360, 1 unit = 1 cm = 10 mm, so a 6mm tool shows as 0.6.
    
    Example:
    {
        "tool_id": "tool_001"
    }
    
    Example response:
    {
        "tool": {
            "id": "tool_001",
            "name": "6mm Flat Endmill",
            "type": "flat end mill",
            "diameter": 6.0,
            "overall_length": 50.0
        },
        "operations": [
            {"id": "op_001", "name": "Adaptive1", "setup": "Setup1"}
        ],
        "usage_count": 1
    }
    
    Typical use cases: Finding which operations use a tool, checking tool utilization.
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_tool_usage']}/{tool_id}/usage"
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
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
        logging.error("Get tool info failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to get tool info: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def list_tool_libraries():
    """
    List all accessible tool libraries in Fusion 360.
    
    Returns all tool libraries including local, cloud, and document libraries.
    This is typically the first tool you call when working with tool library data.
    
    Each library includes: id, name, type (local/cloud/document), tool_count, and is_writable.
    """
    try:
        endpoint = get_endpoints("cam")["tool_libraries"]
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
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
        logging.error("List tool libraries failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to list tool libraries: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def list_library_tools(library_id: str):
    """
    List all tools in a specific tool library.
    
    Use this after list_tool_libraries() to browse tools in a specific library.
    You need the library_id from the list_tool_libraries response.
    """
    try:
        endpoint = f"{get_endpoints('cam')['tool_library_tools']}/{library_id}/tools"
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
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
        logging.error("List library tools failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to list library tools: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def get_tool_details(tool_id: str):
    """
    Get detailed information about a specific cutting tool.
    
    Returns complete tool data including geometry, specifications, and cutting data presets.
    Use this to inspect full tool parameters before using or modifying a tool.
    """
    try:
        endpoint = f"{get_endpoints('cam')['tool_details']}/{tool_id}"
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
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
        logging.error("Get tool details failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to get tool details: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }