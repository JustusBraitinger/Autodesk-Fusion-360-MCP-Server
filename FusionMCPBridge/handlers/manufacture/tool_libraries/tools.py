# Tool Library Tools Handler
# Handles tool CRUD operations within tool libraries

import adsk.core
import adsk.cam
from typing import Dict, Any, Optional
import logging

# Import core components
from ....core.task_queue import task_queue, TaskPriority
from ....core.router import request_router

# Set up logging
logger = logging.getLogger(__name__)

def handle_list_tools(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    List tools in library catalogs.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (optional library_id to filter)
        
    Returns:
        Response with tools list or error information
    """
    try:
        library_id = data.get("library_id")
        
        result = {}
        
        def execute_list_tools():
            nonlocal result
            try:
                from ....tool_library import list_tools_in_libraries
                if library_id:
                    result = list_tools_in_libraries(library_id=library_id)
                else:
                    result = list_tools_in_libraries()
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error listing tools: {str(e)}",
                    "code": "TOOLS_LIST_ERROR"
                }
        
        task_queue.queue_task(
            "list_tools_in_libraries",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.tool_libraries.tools",
            callback=execute_list_tools
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_list_tools: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_get_tool(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get detailed information about a specific tool from library catalogs.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (should contain tool_id)
        
    Returns:
        Response with tool details or error information
    """
    try:
        tool_id = data.get("tool_id")
        if not tool_id:
            return {
                "status": 400,
                "error": True,
                "message": "tool_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        result = {}
        
        def execute_get_tool():
            nonlocal result
            try:
                from ....tool_library import find_tool_by_id, serialize_tool
                tool = find_tool_by_id(tool_id)
                if tool:
                    result = serialize_tool(tool)
                else:
                    result = {
                        "error": True,
                        "message": f"Tool with ID '{tool_id}' not found",
                        "code": "TOOL_NOT_FOUND"
                    }
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error getting tool: {str(e)}",
                    "code": "TOOL_GET_ERROR"
                }
        
        task_queue.queue_task(
            "get_tool_from_library",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.tool_libraries.tools",
            callback=execute_get_tool
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_get_tool: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_create_tool(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new tool in a library catalog.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data with tool specifications
        
    Returns:
        Response with created tool information or error
    """
    try:
        library_id = data.get("library_id")
        tool_spec = data.get("tool_spec", {})
        
        if not library_id:
            return {
                "status": 400,
                "error": True,
                "message": "library_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        # For now, return not implemented as this requires additional CAM API research
        return {
            "status": 501,
            "error": True,
            "message": "Tool creation in libraries not yet implemented - requires additional CAM API research",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_create_tool: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_modify_tool(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modify an existing tool in a library catalog.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data with tool modifications
        
    Returns:
        Response with modified tool information or error
    """
    try:
        tool_id = data.get("tool_id")
        modifications = data.get("modifications", {})
        
        if not tool_id:
            return {
                "status": 400,
                "error": True,
                "message": "tool_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        # For now, return not implemented as this requires additional CAM API research
        return {
            "status": 501,
            "error": True,
            "message": "Tool modification in libraries not yet implemented - requires additional CAM API research",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_modify_tool: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_delete_tool(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete a tool from a library catalog.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (should contain tool_id)
        
    Returns:
        Response confirming deletion or error
    """
    try:
        tool_id = data.get("tool_id")
        if not tool_id:
            return {
                "status": 400,
                "error": True,
                "message": "tool_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        # For now, return not implemented as this requires additional CAM API research
        return {
            "status": 501,
            "error": True,
            "message": "Tool deletion from libraries not yet implemented - requires additional CAM API research",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_delete_tool: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_duplicate_tool(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Duplicate a tool within library catalogs.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (should contain tool_id and optional new_name)
        
    Returns:
        Response with duplicated tool information or error
    """
    try:
        tool_id = data.get("tool_id")
        new_name = data.get("new_name")
        target_library_id = data.get("target_library_id")
        
        if not tool_id:
            return {
                "status": 400,
                "error": True,
                "message": "tool_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        # For now, return not implemented as this requires additional CAM API research
        return {
            "status": 501,
            "error": True,
            "message": "Tool duplication in libraries not yet implemented - requires additional CAM API research",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_duplicate_tool: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_validate_tool_specification(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate tool specification parameters.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (should contain tool_spec)
        
    Returns:
        Response with validation results or error
    """
    try:
        tool_spec = data.get("tool_spec", {})
        
        result = {}
        
        def execute_validate_tool_specification():
            nonlocal result
            try:
                validation_results = {
                    "valid": True,
                    "issues": [],
                    "warnings": []
                }
                
                # Validate required fields
                required_fields = ["name", "type", "diameter"]
                for field in required_fields:
                    if field not in tool_spec or not tool_spec[field]:
                        validation_results["issues"].append({
                            "field": field,
                            "issue": f"Required field '{field}' is missing or empty",
                            "severity": "error"
                        })
                        validation_results["valid"] = False
                
                # Validate diameter
                diameter = tool_spec.get("diameter")
                if diameter is not None:
                    if not isinstance(diameter, (int, float)) or diameter <= 0:
                        validation_results["issues"].append({
                            "field": "diameter",
                            "issue": "Diameter must be a positive number",
                            "severity": "error"
                        })
                        validation_results["valid"] = False
                
                # Validate overall length
                overall_length = tool_spec.get("overall_length")
                if overall_length is not None:
                    if not isinstance(overall_length, (int, float)) or overall_length <= 0:
                        validation_results["issues"].append({
                            "field": "overall_length",
                            "issue": "Overall length must be a positive number",
                            "severity": "error"
                        })
                        validation_results["valid"] = False
                
                # Validate flute count
                flute_count = tool_spec.get("flute_count")
                if flute_count is not None:
                    if not isinstance(flute_count, int) or flute_count <= 0:
                        validation_results["issues"].append({
                            "field": "flute_count",
                            "issue": "Flute count must be a positive integer",
                            "severity": "error"
                        })
                        validation_results["valid"] = False
                
                # Validate tool number
                tool_number = tool_spec.get("tool_number")
                if tool_number is not None:
                    if not isinstance(tool_number, int) or tool_number < 0:
                        validation_results["issues"].append({
                            "field": "tool_number",
                            "issue": "Tool number must be a non-negative integer",
                            "severity": "error"
                        })
                        validation_results["valid"] = False
                
                # Validate cutting parameters
                cutting_params = tool_spec.get("cutting_parameters", {})
                if cutting_params:
                    spindle_speed = cutting_params.get("spindle_speed")
                    if spindle_speed is not None and (not isinstance(spindle_speed, (int, float)) or spindle_speed <= 0):
                        validation_results["warnings"].append({
                            "field": "cutting_parameters.spindle_speed",
                            "warning": "Spindle speed should be a positive number",
                            "severity": "warning"
                        })
                    
                    feed_rate = cutting_params.get("feed_rate")
                    if feed_rate is not None and (not isinstance(feed_rate, (int, float)) or feed_rate <= 0):
                        validation_results["warnings"].append({
                            "field": "cutting_parameters.feed_rate",
                            "warning": "Feed rate should be a positive number",
                            "severity": "warning"
                        })
                
                result = validation_results
                
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error validating tool specification: {str(e)}",
                    "code": "TOOL_VALIDATION_ERROR"
                }
        
        task_queue.queue_task(
            "validate_tool_specification",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.tool_libraries.tools",
            callback=execute_validate_tool_specification
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_validate_tool_specification: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

# Register handlers with the router
def register_handlers():
    """Register all tool library tool handlers with the request router"""
    try:
        request_router.register_handler(
            "/tool-libraries/tools",
            handle_list_tools,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.tool_libraries.tools"
        )
        
        request_router.register_handler(
            "/tool-libraries/tools/{tool_id}",
            handle_get_tool,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.tool_libraries.tools"
        )
        
        request_router.register_handler(
            "/tool-libraries/tools",
            handle_create_tool,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.tool_libraries.tools"
        )
        
        request_router.register_handler(
            "/tool-libraries/tools/{tool_id}",
            handle_modify_tool,
            methods=["PUT"],
            category="manufacture",
            module_name="manufacture.tool_libraries.tools"
        )
        
        request_router.register_handler(
            "/tool-libraries/tools/{tool_id}",
            handle_delete_tool,
            methods=["DELETE"],
            category="manufacture",
            module_name="manufacture.tool_libraries.tools"
        )
        
        request_router.register_handler(
            "/tool-libraries/tools/{tool_id}/duplicate",
            handle_duplicate_tool,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.tool_libraries.tools"
        )
        
        request_router.register_handler(
            "/tool-libraries/tools/validate",
            handle_validate_tool_specification,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.tool_libraries.tools"
        )
        
        logger.info("Registered tool library tool handlers")
        
    except Exception as e:
        logger.error(f"Error registering tool library tool handlers: {str(e)}")

# Auto-register handlers when module is imported
register_handlers()