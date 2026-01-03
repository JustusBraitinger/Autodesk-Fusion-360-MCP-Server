"""
Utility System Tools

This module contains system operation tools:
- test_connection: Test connection to Fusion 360
- delete_all: Delete all objects in current session
- undo: Undo last operation
- move_latest_body: Move the latest body
- list_available_prompts: List all available prompts
- get_prompt_content: Get content of a specific prompt
"""

import logging
from mcp.server.fastmcp import FastMCP
from core.request_handler import send_request
from core.config import get_endpoints, get_headers
from prompts.registry import get_prompt_registry

def register_tools(mcp_instance: FastMCP):
    """Register system tools with the MCP server."""
    # Register all tools in this module
    mcp_instance.tool()(test_connection)
    mcp_instance.tool()(delete_all)
    mcp_instance.tool()(undo)
    mcp_instance.tool()(move_latest_body)
    mcp_instance.tool()(list_available_prompts)
    mcp_instance.tool()(get_prompt_content)

def test_connection():
    """Testes die Verbindung zum Fusion 360 Server."""
    try:
        endpoint = get_endpoints("utility")["test_connection"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Test connection failed: %s", e)
        raise

def delete_all():
    """Löscht alle Objekte in der aktuellen Fusion 360-Sitzung."""
    try:
        endpoint = get_endpoints("utility")["delete_everything"]
        headers = get_headers()
        send_request(endpoint, {}, headers)
    except Exception as e:
        logging.error("Delete failed: %s", e)
        raise

def undo():
    """Macht die letzte Aktion rückgängig."""
    try:
        endpoint = get_endpoints("utility")["undo"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Undo failed: %s", e)
        raise

def move_latest_body(x : float,y:float,z:float):
    """
    Du kannst den letzten Körper in Fusion 360 verschieben in x,y und z Richtung
    
    """
    endpoint = get_endpoints("utility")["move_body"]
    payload = {
        "x": x,
        "y": y,
        "z": z
    }
    headers = get_headers()
    return send_request(endpoint, payload, headers)

def list_available_prompts():
    """
    List all available prompts in the system.
    
    Returns information about all registered prompts including their names,
    descriptions, categories, and dependencies. Useful for debugging and
    discovering available prompt templates.
    
    Returns:
        dict: Contains prompt information organized by category
    """
    try:
        registry = get_prompt_registry()
        
        result = {
            "total_prompts": len(registry.list_prompts()),
            "categories": registry.get_categories(),
            "prompts": {}
        }
        
        # Organize prompts by category
        for category in registry.get_categories():
            result["prompts"][category] = []
            
            for prompt_name in registry.list_prompts():
                prompt_info = registry.get_prompt_info(prompt_name)
                if prompt_info and prompt_info.category == category:
                    result["prompts"][category].append({
                        "name": prompt_name,
                        "description": prompt_info.description,
                        "dependencies": prompt_info.dependencies
                    })
        
        return result
        
    except Exception as e:
        logging.error("List available prompts failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to list prompts: {str(e)}",
            "code": "PROMPT_LIST_ERROR"
        }

def get_prompt_content(prompt_name: str):
    """
    Get the content of a specific prompt by name.
    
    Use this tool to retrieve the full content of a prompt template.
    Useful for debugging prompt content or understanding what a prompt does.
    
    Args:
        prompt_name: Name of the prompt to retrieve
        
    Returns:
        dict: Contains prompt content and metadata
    """
    try:
        registry = get_prompt_registry()
        
        prompt_info = registry.get_prompt_info(prompt_name)
        if not prompt_info:
            return {
                "error": True,
                "message": f"Prompt '{prompt_name}' not found",
                "code": "PROMPT_NOT_FOUND",
                "available_prompts": registry.list_prompts()
            }
        
        prompt_content = registry.get_prompt(prompt_name)
        
        return {
            "name": prompt_name,
            "description": prompt_info.description,
            "category": prompt_info.category,
            "dependencies": prompt_info.dependencies,
            "content": prompt_content
        }
        
    except Exception as e:
        logging.error("Get prompt content failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to get prompt content: {str(e)}",
            "code": "PROMPT_CONTENT_ERROR"
        }