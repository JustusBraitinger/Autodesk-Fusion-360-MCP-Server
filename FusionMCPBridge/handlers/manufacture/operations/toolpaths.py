"""
Toolpath Operations Handler

Handles toolpath listing, analysis, and parameter management.
Contains actual business logic for toolpath operations (extracted from cam.py).
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
    find_setup_by_id,
    get_operation_type,
    get_tool_type_string,
    get_param_value
)

# Import tool serialization from tool_library
from ....tool_library import serialize_tool

# Set up logging
logger = logging.getLogger(__name__)


# =============================================================================
# Business Logic Functions (extracted from cam.py)
# =============================================================================

def _get_tool_data_from_operation(operation: adsk.cam.Operation) -> dict:
    """Extract comprehensive tool data from an operation.
    
    Uses tool.parameters to get accurate tool information, as direct properties
    like tool.description are often empty for operation-assigned tools.
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
        
        # Initialize tool data with defaults
        tool_data = {
            "id": tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool)),
            "name": "Unnamed Tool",
            "type": get_tool_type_string(tool),
            "diameter": None,
            "diameter_unit": "mm",
            "overall_length": None,
            "tool_number": None
        }
        
        # Extract data from tool parameters (the reliable way)
        if hasattr(tool, 'parameters'):
            params = tool.parameters
            
            # Get tool_description (the actual tool name)
            desc_param = params.itemByName('tool_description')
            if desc_param and desc_param.expression:
                tool_data["name"] = desc_param.expression.strip("'\"")
            
            # Get tool_number
            num_param = params.itemByName('tool_number')
            if num_param:
                try:
                    tool_data["tool_number"] = int(num_param.value.value)
                except Exception:
                    pass
            
            # Get tool_diameter (in mm, converted from cm)
            diam_param = params.itemByName('tool_diameter')
            if diam_param:
                try:
                    # Fusion stores in cm, convert to mm
                    tool_data["diameter"] = float(diam_param.value.value) * 10
                except Exception:
                    pass
            
            # Get tool_overallLength (in mm, converted from cm)
            length_param = params.itemByName('tool_overallLength')
            if length_param:
                try:
                    # Fusion stores in cm, convert to mm
                    tool_data["overall_length"] = float(length_param.value.value) * 10
                except Exception:
                    pass
        
        # Fallback to direct properties if parameters didn't work
        if tool_data["name"] == "Unnamed Tool":
            if hasattr(tool, 'description') and tool.description:
                tool_data["name"] = tool.description
        
        if tool_data["diameter"] is None and hasattr(tool, 'diameter'):
            # Direct property is already in cm, convert to mm
            tool_data["diameter"] = tool.diameter * 10 if tool.diameter else None
        
        if tool_data["overall_length"] is None and hasattr(tool, 'bodyLength'):
            # Direct property is already in cm, convert to mm
            tool_data["overall_length"] = tool.bodyLength * 10 if tool.bodyLength else None
        
        if tool_data["tool_number"] is None and hasattr(tool, 'toolNumber'):
            tool_data["tool_number"] = tool.toolNumber
        
        return tool_data
        
    except Exception as e:
        return {"name": "Error accessing tool", "id": None, "error": str(e)}


def _extract_heights_params(operation: adsk.cam.Operation) -> dict:
    """Extract height parameters from an operation with comprehensive metadata."""
    heights = {}
    
    try:
        if hasattr(operation, 'parameters'):
            params = operation.parameters
            
            height_params = [
                ('clearanceHeight_value', 'clearance_height', 'mm'),
                ('retractHeight_value', 'retract_height', 'mm'),
                ('topHeight_value', 'top_height', 'mm'),
                ('bottomHeight_value', 'bottom_height', 'mm'),
            ]
            
            for param_name, output_name, default_unit in height_params:
                try:
                    param = params.itemByName(param_name)
                    if param:
                        param_data = {
                            "value": None,
                            "unit": default_unit,
                            "expression": None,
                            "type": "numeric",
                            "editable": True,
                            "min_value": None,
                            "max_value": None
                        }
                        
                        try:
                            if hasattr(param.value, 'value'):
                                param_data["value"] = param.value.value
                            else:
                                param_data["value"] = param.value
                        except Exception:
                            param_data["value"] = None
                        
                        try:
                            if hasattr(param, 'expression') and param.expression:
                                param_data["expression"] = param.expression
                            elif hasattr(param.value, 'expression') and param.value.expression:
                                param_data["expression"] = param.value.expression
                        except Exception:
                            pass
                        
                        try:
                            if hasattr(param.value, 'unit') and param.value.unit:
                                param_data["unit"] = param.value.unit
                            elif hasattr(param, 'unit') and param.unit:
                                param_data["unit"] = param.unit
                        except Exception:
                            pass
                        
                        try:
                            if hasattr(param, 'isReadOnly'):
                                param_data["editable"] = not param.isReadOnly
                        except Exception:
                            param_data["editable"] = True
                        
                        heights[output_name] = param_data
                        
                except Exception:
                    continue
        
    except Exception:
        pass
    
    return heights


def list_all_toolpaths_impl(cam: adsk.cam.CAM) -> dict:
    """Enumerate all setups and operations (toolpaths) in the CAM document."""
    result = {
        "setups": [],
        "total_count": 0,
        "message": None
    }
    
    if not cam:
        result["message"] = "No CAM data present in the document"
        return result
    
    try:
        setups = cam.setups
        if not setups or setups.count == 0:
            result["message"] = "No setups found in CAM document"
            return result
        
        total_count = 0
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            setup_data = {
                "id": setup.entityToken if hasattr(setup, 'entityToken') else f"setup_{setup_idx}",
                "name": setup.name,
                "toolpaths": []
            }
            
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    tool_data = _get_tool_data_from_operation(operation)
                    
                    toolpath_data = {
                        "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_{op_idx}",
                        "name": operation.name,
                        "type": get_operation_type(operation),
                        "tool": tool_data,
                        "is_valid": operation.isValid if hasattr(operation, 'isValid') else True
                    }
                    
                    setup_data["toolpaths"].append(toolpath_data)
                    total_count += 1
            
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
                                    tool_data = _get_tool_data_from_operation(operation)
                                    
                                    toolpath_data = {
                                        "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_f{folder_idx}_{op_idx}",
                                        "name": operation.name,
                                        "type": get_operation_type(operation),
                                        "tool": tool_data,
                                        "is_valid": operation.isValid if hasattr(operation, 'isValid') else True
                                    }
                                    
                                    setup_data["toolpaths"].append(toolpath_data)
                                    total_count += 1
            
            result["setups"].append(setup_data)
        
        result["total_count"] = total_count
        
        if total_count == 0:
            result["message"] = "No toolpath operations found in any setup"
        
        return result
        
    except Exception as e:
        result["message"] = f"Error listing toolpaths: {str(e)}"
        return result


def list_toolpaths_with_heights_impl(cam: adsk.cam.CAM = None) -> dict:
    """List all toolpaths with embedded height parameter data."""
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "setups": [],
                "total_count": 0,
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    result = {
        "setups": [],
        "total_count": 0,
        "message": None
    }
    
    try:
        setups = cam.setups
        if not setups or setups.count == 0:
            result["message"] = "No setups found in CAM document"
            return result
        
        total_count = 0
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            setup_data = {
                "id": setup.entityToken if hasattr(setup, 'entityToken') else f"setup_{setup_idx}",
                "name": setup.name,
                "toolpaths": []
            }
            
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    tool_data = _get_tool_data_from_operation(operation)
                    heights_data = _extract_heights_params(operation)
                    
                    toolpath_data = {
                        "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_{op_idx}",
                        "name": operation.name,
                        "type": get_operation_type(operation),
                        "tool": tool_data,
                        "heights": heights_data,
                        "is_valid": operation.isValid if hasattr(operation, 'isValid') else True
                    }
                    
                    setup_data["toolpaths"].append(toolpath_data)
                    total_count += 1
            
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
                                    tool_data = _get_tool_data_from_operation(operation)
                                    heights_data = _extract_heights_params(operation)
                                    
                                    toolpath_data = {
                                        "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_f{folder_idx}_{op_idx}",
                                        "name": operation.name,
                                        "type": get_operation_type(operation),
                                        "tool": tool_data,
                                        "heights": heights_data,
                                        "is_valid": operation.isValid if hasattr(operation, 'isValid') else True
                                    }
                                    
                                    setup_data["toolpaths"].append(toolpath_data)
                                    total_count += 1
            
            result["setups"].append(setup_data)
        
        result["total_count"] = total_count
        
        if total_count == 0:
            result["message"] = "No toolpath operations found in any setup"
        
        return result
        
    except Exception as e:
        return {
            "setups": [],
            "total_count": 0,
            "error": True,
            "message": f"Error listing toolpaths with heights: {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


def _extract_feeds_speeds(operation: adsk.cam.Operation) -> dict:
    """Extract feeds and speeds parameters from an operation."""
    feeds_speeds = {}
    
    try:
        if hasattr(operation, 'parameters'):
            params = operation.parameters
            
            feed_speed_params = [
                ('tool_spindleSpeed', 'spindle_speed', 'rpm'),
                ('tool_feedCutting', 'cutting_feedrate', 'mm/min'),
                ('tool_feedPlunge', 'plunge_feedrate', 'mm/min'),
                ('tool_feedRamp', 'ramp_feedrate', 'mm/min'),
                ('tool_feedRetract', 'retract_feedrate', 'mm/min'),
            ]
            
            for param_name, output_name, default_unit in feed_speed_params:
                try:
                    param = params.itemByName(param_name)
                    if param:
                        param_data = {
                            "value": param.value.value if hasattr(param.value, 'value') else param.value,
                            "type": "numeric",
                            "editable": True
                        }
                        
                        if hasattr(param.value, 'unit') and param.value.unit:
                            param_data["unit"] = param.value.unit
                        else:
                            param_data["unit"] = default_unit
                        
                        feeds_speeds[output_name] = param_data
                except Exception:
                    continue
        
        if 'spindle_speed' not in feeds_speeds and hasattr(operation, 'tool'):
            tool = operation.tool
            if tool and hasattr(tool, 'spindleSpeed'):
                feeds_speeds['spindle_speed'] = {
                    "value": tool.spindleSpeed,
                    "unit": "rpm",
                    "type": "numeric",
                    "editable": True
                }
        
    except Exception:
        pass
    
    return feeds_speeds


def _extract_geometry_params(operation: adsk.cam.Operation) -> dict:
    """Extract geometry parameters from an operation."""
    geometry = {}
    
    try:
        if hasattr(operation, 'parameters'):
            params = operation.parameters
            
            geometry_params = [
                ('stepover', 'stepover', '%'),
                ('stepdown', 'stepdown', 'mm'),
                ('optimalLoad', 'optimal_load', 'mm'),
                ('tolerance', 'tolerance', 'mm'),
                ('stockToLeave', 'stock_to_leave', 'mm'),
            ]
            
            for param_name, output_name, default_unit in geometry_params:
                try:
                    param = params.itemByName(param_name)
                    if param:
                        param_data = {
                            "value": param.value.value if hasattr(param.value, 'value') else param.value,
                            "type": "numeric",
                            "editable": True
                        }
                        
                        if hasattr(param.value, 'unit') and param.value.unit:
                            param_data["unit"] = param.value.unit
                        else:
                            param_data["unit"] = default_unit
                        
                        geometry[output_name] = param_data
                except Exception:
                    continue
        
    except Exception:
        pass
    
    return geometry


def _extract_tool_reference(operation: adsk.cam.Operation) -> dict:
    """Extract tool reference information from an operation.
    
    Uses serialize_tool from tool_library for proper name extraction
    from tool_description parameter.
    """
    try:
        tool = operation.tool
        if tool:
            # Use serialize_tool for consistent tool data extraction
            return serialize_tool(tool)
    except Exception:
        pass
    
    return {}


def get_toolpath_parameters_impl(cam: adsk.cam.CAM, toolpath_id: str) -> dict:
    """Extract all parameters from a toolpath operation."""
    if not cam:
        return {
            "error": True,
            "message": "No CAM data present in the document",
            "code": "NO_CAM_DATA"
        }
    
    try:
        operation = find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        setup_name = ""
        if hasattr(operation, 'parentSetup') and operation.parentSetup:
            setup_name = operation.parentSetup.name
        
        result = {
            "id": toolpath_id,
            "name": operation.name,
            "type": get_operation_type(operation),
            "setup_name": setup_name,
            "tool": _extract_tool_reference(operation),
            "parameters": {
                "feeds_and_speeds": _extract_feeds_speeds(operation),
                "geometry": _extract_geometry_params(operation),
                "heights": _extract_heights_params(operation)
            }
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error extracting toolpath parameters: {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


def _estimate_operation_time(operation: adsk.cam.Operation) -> int:
    """Estimate machining time for an operation in minutes."""
    try:
        op_type = get_operation_type(operation).lower()
        
        base_times = {
            "adaptive": 15,
            "pocket": 10,
            "contour": 8,
            "parallel": 12,
            "scallop": 10,
            "pencil": 6,
            "drill": 3,
            "tap": 4,
            "bore": 5,
            "face": 8,
            "trace": 6
        }
        
        estimated_time = 5
        for op_key, time in base_times.items():
            if op_key in op_type:
                estimated_time = time
                break
        
        return max(1, estimated_time)
        
    except Exception:
        return 5


def _generate_optimization_recommendations(execution_sequence: list, tool_changes: list, tool_change_count: int) -> list:
    """Generate optimization recommendations based on sequence analysis."""
    recommendations = []
    
    try:
        if tool_change_count > 3:
            potential_savings = tool_change_count * 2
            recommendations.append({
                "type": "tool_change_reduction",
                "description": f"Consider reordering operations to minimize tool changes. Currently {tool_change_count} tool changes detected.",
                "potential_savings": f"{potential_savings}:00"
            })
        
        tool_groups = {}
        for op in execution_sequence:
            tool_id = op["tool_id"]
            if tool_id not in tool_groups:
                tool_groups[tool_id] = []
            tool_groups[tool_id].append(op)
        
        scattered_tools = []
        for tool_id, ops in tool_groups.items():
            if len(ops) > 1:
                orders = [op["order"] for op in ops]
                if max(orders) - min(orders) > len(ops):
                    scattered_tools.append((tool_id, ops[0]["tool_name"], len(ops)))
        
        if scattered_tools:
            recommendations.append({
                "type": "operation_grouping",
                "description": "Consider grouping operations by tool to reduce tool changes",
                "potential_savings": f"{len(scattered_tools) * 2}:00"
            })
    
    except Exception:
        pass
    
    return recommendations


def analyze_setup_sequence_impl(cam: adsk.cam.CAM, setup_id: str) -> dict:
    """Analyze toolpath execution sequence and dependencies within a setup."""
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    if not setup_id:
        return {
            "error": True,
            "message": "Setup ID is required",
            "code": "MISSING_SETUP_ID"
        }
    
    try:
        setup = find_setup_by_id(cam, setup_id)
        
        if not setup:
            return {
                "error": True,
                "message": f"Setup with ID '{setup_id}' not found",
                "code": "SETUP_NOT_FOUND"
            }
        
        result = {
            "setup_id": setup_id,
            "setup_name": setup.name,
            "total_toolpaths": 0,
            "execution_sequence": [],
            "tool_changes": [],
            "optimization_recommendations": [],
            "total_estimated_time": "0:00"
        }
        
        operations = []
        
        if hasattr(setup, 'operations') and setup.operations:
            for op_idx in range(setup.operations.count):
                operation = setup.operations.item(op_idx)
                operations.append((operation, op_idx, None))
        
        if hasattr(setup, 'folders') and setup.folders:
            for folder_idx in range(setup.folders.count):
                folder = setup.folders.item(folder_idx)
                if hasattr(folder, 'operations') and folder.operations:
                    for op_idx in range(folder.operations.count):
                        operation = folder.operations.item(op_idx)
                        operations.append((operation, op_idx, folder.name))
        
        result["total_toolpaths"] = len(operations)
        
        if len(operations) == 0:
            result["optimization_recommendations"].append({
                "type": "no_operations",
                "description": "Setup contains no toolpath operations",
                "potential_savings": "N/A"
            })
            return result
        
        total_time_minutes = 0
        previous_tool_id = None
        tool_change_count = 0
        
        for order, (operation, op_idx, folder_name) in enumerate(operations, 1):
            try:
                op_id = operation.entityToken if hasattr(operation, 'entityToken') else f"op_{order}"
                op_name = operation.name
                op_type = get_operation_type(operation)
                
                tool_data = _get_tool_data_from_operation(operation)
                tool_id = tool_data.get("id")
                
                estimated_time = _estimate_operation_time(operation)
                total_time_minutes += estimated_time
                
                dependencies = []
                
                sequence_entry = {
                    "order": order,
                    "toolpath_id": op_id,
                    "toolpath_name": op_name,
                    "operation_type": op_type,
                    "tool_id": tool_id,
                    "tool_name": tool_data.get("name", "Unknown Tool"),
                    "estimated_time": f"{estimated_time//60}:{estimated_time%60:02d}",
                    "dependencies": dependencies,
                    "folder": folder_name
                }
                
                result["execution_sequence"].append(sequence_entry)
                
                if previous_tool_id is not None and tool_id != previous_tool_id:
                    tool_change_count += 1
                    change_time = 2
                    total_time_minutes += change_time
                    
                    tool_change = {
                        "after_toolpath": result["execution_sequence"][-2]["toolpath_id"] if len(result["execution_sequence"]) > 1 else None,
                        "from_tool": previous_tool_id,
                        "to_tool": tool_id,
                        "to_tool_name": tool_data.get("name", "Unknown Tool"),
                        "change_time": f"{change_time}:00",
                        "order": order
                    }
                    result["tool_changes"].append(tool_change)
                
                previous_tool_id = tool_id
                
            except Exception:
                continue
        
        result["total_estimated_time"] = f"{total_time_minutes//60}:{total_time_minutes%60:02d}"
        
        result["optimization_recommendations"] = _generate_optimization_recommendations(
            result["execution_sequence"],
            result["tool_changes"],
            tool_change_count
        )
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error analyzing setup sequence: {str(e)}",
            "code": "ANALYSIS_ERROR"
        }


# =============================================================================
# HTTP Handler Functions
# =============================================================================

def handle_list_toolpaths(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """List all toolpaths in the CAM document."""
    try:
        cam = get_cam_product()
        if cam:
            result = list_all_toolpaths_impl(cam)
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
        logger.error(f"Error in handle_list_toolpaths: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_list_toolpaths_with_heights(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """List all toolpaths with embedded height parameter data."""
    try:
        result = list_toolpaths_with_heights_impl()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_list_toolpaths_with_heights: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_toolpath_details(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed information for a specific toolpath."""
    try:
        toolpath_id = data.get("toolpath_id")
        if not toolpath_id:
            return {
                "status": 400,
                "error": True,
                "message": "toolpath_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        cam = get_cam_product()
        if cam:
            result = get_toolpath_parameters_impl(cam, toolpath_id)
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
        logger.error(f"Error in handle_get_toolpath_details: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_toolpath_parameters(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get all parameters for a specific toolpath."""
    try:
        toolpath_id = data.get("toolpath_id")
        if not toolpath_id:
            return {
                "status": 400,
                "error": True,
                "message": "toolpath_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        cam = get_cam_product()
        if cam:
            result = get_toolpath_parameters_impl(cam, toolpath_id)
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
        logger.error(f"Error in handle_get_toolpath_parameters: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_analyze_setup_sequence(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze toolpath execution sequence and dependencies within a setup."""
    try:
        setup_id = data.get("setup_id")
        if not setup_id:
            return {
                "status": 400,
                "error": True,
                "message": "setup_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        cam = get_cam_product()
        if cam:
            result = analyze_setup_sequence_impl(cam, setup_id)
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
        logger.error(f"Error in handle_analyze_setup_sequence: {str(e)}")
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
    """Register all toolpath handlers with the request router"""
    try:
        request_router.register_handler(
            "/cam/toolpaths",
            handle_list_toolpaths,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.toolpaths"
        )
        
        request_router.register_handler(
            "/cam/toolpaths/with-heights",
            handle_list_toolpaths_with_heights,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.toolpaths"
        )
        
        request_router.register_handler(
            "/cam/toolpaths/{toolpath_id}",
            handle_get_toolpath_details,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.toolpaths"
        )
        
        request_router.register_handler(
            "/cam/toolpaths/{toolpath_id}/parameters",
            handle_get_toolpath_parameters,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.toolpaths"
        )
        
        request_router.register_handler(
            "/cam/setups/{setup_id}/sequence",
            handle_analyze_setup_sequence,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.toolpaths"
        )
        
        logger.info("Registered toolpath operation handlers")
        
    except Exception as e:
        logger.error(f"Error registering toolpath handlers: {str(e)}")


register_handlers()
