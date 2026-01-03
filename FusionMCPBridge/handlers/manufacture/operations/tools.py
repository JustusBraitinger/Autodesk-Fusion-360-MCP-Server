"""
Operation Tools Handler

Handles tools assigned to operations and operation-specific tool management.
Contains actual business logic for operation tools (extracted from cam.py).
"""

import adsk.core
import adsk.cam
from typing import Dict, Any, Optional
import logging

# Import core components
from ....core.router import request_router

# Import shared CAM utilities
from ..cam_utils import (
    get_cam_product,
    validate_cam_product_with_details,
    find_operation_by_id,
    get_operation_type,
    get_tool_type_string
)

# Import tool serialization from tool_library
from ....tool_library import serialize_tool

# Set up logging
logger = logging.getLogger(__name__)


# =============================================================================
# Tool Settings Extraction
# =============================================================================

def extract_tool_settings(operation: adsk.cam.Operation) -> dict:
    """Extract tool settings (preset cutting parameters) from an operation's tool."""
    tool_settings = {}
    
    try:
        if not operation or not hasattr(operation, 'tool'):
            return tool_settings
        
        tool = operation.tool
        if not tool:
            return tool_settings
        
        if hasattr(tool, 'presets') and tool.presets:
            presets = tool.presets
            if presets.count > 0:
                preset = presets.item(0)
                
                if hasattr(preset, 'spindleSpeed'):
                    tool_settings['preset_spindle_speed'] = {
                        "value": preset.spindleSpeed,
                        "unit": "rpm",
                        "type": "numeric"
                    }
                
                if hasattr(preset, 'surfaceSpeed'):
                    tool_settings['surface_speed'] = {
                        "value": preset.surfaceSpeed,
                        "unit": "m/min",
                        "type": "numeric"
                    }
                
                if hasattr(preset, 'feedPerTooth'):
                    tool_settings['feed_per_tooth'] = {
                        "value": preset.feedPerTooth,
                        "unit": "mm",
                        "type": "numeric"
                    }
        
    except Exception:
        pass
    
    return tool_settings


# =============================================================================
# Business Logic Functions (extracted from cam.py)
# =============================================================================

def _get_tool_data_from_operation(operation: adsk.cam.Operation) -> dict:
    """Extract comprehensive tool data from an operation.
    
    Uses serialize_tool from tool_library which properly extracts tool name
    from tool_description parameter instead of the often-empty tool.description.
    """
    try:
        tool = None
        
        if hasattr(operation, 'tool') and operation.tool:
            tool = operation.tool
        elif hasattr(operation, 'parameters'):
            params = operation.parameters
            for param_idx in range(params.count):
                param = params.item(param_idx)
                if param.name == "tool_tool" and hasattr(param, 'value'):
                    tool = param.value
                    break
        
        if not tool:
            return {"name": "No tool found", "id": None}
        
        # Use the proper serialize_tool function from tool_library
        # which extracts name from tool_description parameter
        return serialize_tool(tool)
        
    except Exception as e:
        return {"name": "Error accessing tool", "id": None, "error": str(e)}


def list_all_tools_impl(cam: adsk.cam.CAM) -> dict:
    """List all tools used in the CAM document."""
    result = {
        "tools": [],
        "total_count": 0,
        "message": None
    }
    
    if not cam:
        result["message"] = "No CAM data present in the document"
        return result
    
    try:
        seen_tools = set()
        tools_list = []
        
        setups = cam.setups
        if not setups or setups.count == 0:
            result["message"] = "No setups found in CAM document"
            return result
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    if hasattr(operation, 'tool') and operation.tool:
                        tool = operation.tool
                        tool_id = tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool))
                        
                        if tool_id not in seen_tools:
                            seen_tools.add(tool_id)
                            # Use serialize_tool for proper name extraction
                            tools_list.append(serialize_tool(tool))
            
            if hasattr(setup, 'folders'):
                folders = setup.folders
                if folders:
                    for folder_idx in range(folders.count):
                        folder = folders.item(folder_idx)
                        if hasattr(folder, 'operations'):
                            folder_ops = folder.operations
                            if folder_ops:
                                for op_idx in range(folder_ops.count):
                                    operation = folder_ops.item(op_idx)
                                    if hasattr(operation, 'tool') and operation.tool:
                                        tool = operation.tool
                                        tool_id = tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool))
                                        
                                        if tool_id not in seen_tools:
                                            seen_tools.add(tool_id)
                                            # Use serialize_tool for proper name extraction
                                            tools_list.append(serialize_tool(tool))
        
        result["tools"] = tools_list
        result["total_count"] = len(tools_list)
        
        if len(tools_list) == 0:
            result["message"] = "No tools found in CAM document"
        
        return result
        
    except Exception as e:
        result["message"] = f"Error listing tools: {str(e)}"
        return result


# =============================================================================
# HTTP Handler Functions
# =============================================================================

def handle_list_cam_tools(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """List all tools assigned to operations in the CAM document."""
    try:
        cam = get_cam_product()
        if cam:
            result = list_all_tools_impl(cam)
        else:
            result = {
                "error": True,
                "message": "No CAM data present in the document",
                "code": "NO_CAM_DATA"
            }
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_list_cam_tools: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_operation_tool(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get tool information for a specific operation."""
    try:
        operation_id = data.get("operation_id")
        if not operation_id:
            return {
                "status": 400,
                "error": True,
                "message": "operation_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        cam = get_cam_product()
        if cam:
            operation = find_operation_by_id(cam, operation_id)
            if operation:
                tool_data = _get_tool_data_from_operation(operation)
                result = {
                    "operation_id": operation_id,
                    "operation_name": operation.name,
                    "tool": tool_data
                }
            else:
                result = {
                    "error": True,
                    "message": f"Operation with ID '{operation_id}' not found",
                    "code": "OPERATION_NOT_FOUND"
                }
        else:
            result = {
                "error": True,
                "message": "No CAM data present in the document",
                "code": "NO_CAM_DATA"
            }
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_get_operation_tool: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_assign_tool_to_operation(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Assign a tool to a specific operation."""
    try:
        operation_id = data.get("operation_id")
        tool_id = data.get("tool_id")
        
        if not operation_id:
            return {
                "status": 400,
                "error": True,
                "message": "operation_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        if not tool_id:
            return {
                "status": 400,
                "error": True,
                "message": "tool_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        return {
            "status": 501,
            "error": True,
            "message": "Tool assignment to operations not yet implemented",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_assign_tool_to_operation: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_tool_usage(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get usage information for a specific tool across all operations."""
    try:
        tool_id = data.get("tool_id")
        if not tool_id:
            return {
                "status": 400,
                "error": True,
                "message": "tool_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        cam = get_cam_product()
        if cam:
            setups = cam.setups
            tool_usage = {
                "tool_id": tool_id,
                "operations": [],
                "total_operations": 0
            }
            
            if setups:
                for setup_idx in range(setups.count):
                    setup = setups.item(setup_idx)
                    setup_id = setup.entityToken if hasattr(setup, 'entityToken') else f"setup_{setup_idx}"
                    
                    operations = setup.operations
                    if operations:
                        for op_idx in range(operations.count):
                            operation = operations.item(op_idx)
                            tool_data = _get_tool_data_from_operation(operation)
                            if tool_data.get("id") == tool_id:
                                tool_usage["operations"].append({
                                    "operation_id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{op_idx}",
                                    "operation_name": operation.name,
                                    "operation_type": get_operation_type(operation),
                                    "setup_name": setup.name,
                                    "setup_id": setup_id
                                })
            
            tool_usage["total_operations"] = len(tool_usage["operations"])
            result = tool_usage
        else:
            result = {
                "error": True,
                "message": "No CAM data present in the document",
                "code": "NO_CAM_DATA"
            }
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_get_tool_usage: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


# =============================================================================
# Handler Registration
# =============================================================================

def register_handlers():
    """Register all operation tool handlers with the request router"""
    try:
        request_router.register_handler(
            "/cam/tools",
            handle_list_cam_tools,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.tools"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/tool",
            handle_get_operation_tool,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.tools"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/tool",
            handle_assign_tool_to_operation,
            methods=["PUT"],
            category="manufacture",
            module_name="manufacture.operations.tools"
        )
        
        request_router.register_handler(
            "/cam/tools/{tool_id}/usage",
            handle_get_tool_usage,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.tools"
        )
        
        logger.info("Registered operation tool handlers")
        
    except Exception as e:
        logger.error(f"Error registering operation tool handlers: {str(e)}")


register_handlers()
