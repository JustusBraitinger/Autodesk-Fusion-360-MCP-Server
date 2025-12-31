"""
CAM Module for Fusion 360 MCP Add-In

This module provides functions to access and manipulate CAM (Computer-Aided Manufacturing)
data in Fusion 360, including toolpaths, operations, and tool information.
"""

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
from typing import Any, Optional


def get_cam_product() -> Optional[adsk.cam.CAM]:
    """
    Safely access the CAM product from the active Fusion 360 document.
    
    Returns:
        adsk.cam.CAM | None: The CAM product if available, None if no CAM data exists
        or if the document doesn't support CAM operations.
    
    Requirements: 1.3
    """
    try:
        app = adsk.core.Application.get()
        if not app:
            return None
            
        # Get the active document
        doc = app.activeDocument
        if not doc:
            return None
        
        # Try to get the CAM product from the document's products
        products = doc.products
        cam_product = products.itemByProductType('CAMProductType')
        
        if cam_product:
            return adsk.cam.CAM.cast(cam_product)
        
        return None
        
    except Exception:
        return None


def _get_operation_type(operation: adsk.cam.Operation) -> str:
    """
    Get the operation type as a string.
    
    Args:
        operation: The CAM operation
        
    Returns:
        str: The operation type name
    """
    try:
        # Get the strategy name which represents the operation type
        if hasattr(operation, 'strategy') and operation.strategy:
            return operation.strategy
        return "unknown"
    except Exception:
        return "unknown"



def _get_tool_data_from_operation(operation: adsk.cam.Operation) -> dict:
    """
    Extract comprehensive tool data from an operation.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Tool data including name, id, diameter, length, etc.
    """
    try:
        # Try multiple ways to access the tool
        tool = None
        
        # Method 1: Direct tool property
        if hasattr(operation, 'tool') and operation.tool:
            tool = operation.tool
        
        # Method 2: Through parameters
        elif hasattr(operation, 'parameters'):
            params = operation.parameters
            for param_idx in range(params.count):
                param = params.item(param_idx)
                if param.name == "tool_tool" and hasattr(param, 'value'):
                    tool = param.value
                    break
        
        if not tool:
            return {"name": "No tool found", "id": None, "debug": "Tool object is None"}
        
        tool_data = {
            "name": getattr(tool, 'description', None) or getattr(tool, 'name', 'Unknown tool'),
            "id": getattr(tool, 'entityToken', None) or str(id(tool)),
            "type": getattr(tool, 'toolType', 'unknown'),
            "debug": f"Tool object type: {type(tool).__name__}"
        }
        
        # Add tool geometry if available
        if hasattr(tool, 'parameters'):
            params = tool.parameters
            if params:
                for param_idx in range(params.count):
                    param = params.item(param_idx)
                    param_name = param.name
                    if "diameter" in param_name.lower():
                        tool_data["diameter"] = getattr(param.value, 'value', param.value) if hasattr(param, 'value') else None
                    elif "length" in param_name.lower() and "body" in param_name.lower():
                        tool_data["length"] = getattr(param.value, 'value', param.value) if hasattr(param, 'value') else None
                    elif "flute" in param_name.lower():
                        tool_data["flute_length"] = getattr(param.value, 'value', param.value) if hasattr(param, 'value') else None
        
        return tool_data
    except Exception as e:
        return {"name": "Error accessing tool", "id": None, "error": str(e), "debug": f"Exception: {type(e).__name__}"}


def list_all_toolpaths(cam: adsk.cam.CAM) -> dict:
    """
    Enumerate all setups and operations (toolpaths) in the CAM document.
    
    Returns structured data with id, name, type, tool_name for each toolpath,
    organized by parent setup.
    
    Args:
        cam: The CAM product instance
        
    Returns:
        dict: A dictionary containing:
            - setups: List of setup dictionaries, each containing:
                - id: Unique setup identifier
                - name: Setup name
                - toolpaths: List of toolpath dictionaries with id, name, type, tool_name, tool_id, is_valid
            - total_count: Total number of toolpaths
            - message: Optional message (e.g., when no CAM data exists)
    
    Requirements: 1.1, 1.2, 1.4
    """
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
            
            # Get all operations in this setup
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    
                    tool_data = _get_tool_data_from_operation(operation)
                    
                    toolpath_data = {
                        "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_{op_idx}",
                        "name": operation.name,
                        "type": _get_operation_type(operation),
                        "tool": tool_data,
                        "is_valid": operation.isValid if hasattr(operation, 'isValid') else True
                    }
                    
                    setup_data["toolpaths"].append(toolpath_data)
                    total_count += 1
            
            # Also check for nested folders containing operations
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
                                        "type": _get_operation_type(operation),
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



def _find_operation_by_id(cam: adsk.cam.CAM, toolpath_id: str) -> Optional[adsk.cam.Operation]:
    """
    Find an operation by its ID across all setups.
    
    Args:
        cam: The CAM product instance
        toolpath_id: The unique identifier of the toolpath
        
    Returns:
        adsk.cam.Operation | None: The operation if found, None otherwise
    """
    if not cam:
        return None
    
    try:
        setups = cam.setups
        if not setups:
            return None
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            # Check direct operations
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    op_id = operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_{op_idx}"
                    if op_id == toolpath_id:
                        return operation
            
            # Check folder operations
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
                                    op_id = operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_f{folder_idx}_{op_idx}"
                                    if op_id == toolpath_id:
                                        return operation
        
        return None
        
    except Exception:
        return None


def _get_parameter_metadata(param) -> dict:
    """
    Extract metadata from a CAM parameter.
    
    Args:
        param: A CAM parameter object
        
    Returns:
        dict: Parameter metadata including type, unit, constraints, editable flag
    """
    metadata = {
        "type": "unknown",
        "editable": True
    }
    
    try:
        # Determine parameter type
        if hasattr(param, 'value'):
            value = param.value
            if isinstance(value, bool):
                metadata["type"] = "boolean"
            elif isinstance(value, (int, float)):
                metadata["type"] = "numeric"
            elif isinstance(value, str):
                metadata["type"] = "string"
            else:
                metadata["type"] = "object"
        
        # Check if parameter has expression (indicates it's a value parameter)
        if hasattr(param, 'expression'):
            metadata["type"] = "numeric"
            metadata["expression"] = param.expression
        
        # Get unit information
        if hasattr(param, 'unit') and param.unit:
            metadata["unit"] = param.unit
        
        # Check for read-only status
        if hasattr(param, 'isReadOnly'):
            metadata["editable"] = not param.isReadOnly
        
        # Get min/max constraints if available
        if hasattr(param, 'minimumValue'):
            metadata["min"] = param.minimumValue
        if hasattr(param, 'maximumValue'):
            metadata["max"] = param.maximumValue
        
        # For enum parameters, get valid options
        if hasattr(param, 'listItems'):
            items = param.listItems
            if items:
                metadata["type"] = "enum"
                metadata["options"] = []
                for i in range(items.count):
                    item = items.item(i)
                    metadata["options"].append(item.name if hasattr(item, 'name') else str(item))
        
    except Exception:
        pass
    
    return metadata


def _extract_feeds_speeds(operation: adsk.cam.Operation) -> dict:
    """
    Extract feeds and speeds parameters from an operation.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Feeds and speeds parameters with metadata
    """
    feeds_speeds = {}
    
    try:
        # Try to access operation parameters
        if hasattr(operation, 'parameters'):
            params = operation.parameters
            
            # Common feeds/speeds parameter names
            feed_speed_params = [
                ('tool_spindleSpeed', 'spindle_speed', 'rpm'),
                ('tool_feedCutting', 'cutting_feedrate', 'mm/min'),
                ('tool_feedPlunge', 'plunge_feedrate', 'mm/min'),
                ('tool_feedRamp', 'ramp_feedrate', 'mm/min'),
                ('tool_feedRetract', 'retract_feedrate', 'mm/min'),
                ('tool_feedEntry', 'entry_feedrate', 'mm/min'),
                ('tool_feedExit', 'exit_feedrate', 'mm/min'),
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
                        
                        # Get unit
                        if hasattr(param.value, 'unit') and param.value.unit:
                            param_data["unit"] = param.value.unit
                        else:
                            param_data["unit"] = default_unit
                        
                        feeds_speeds[output_name] = param_data
                except Exception:
                    continue
        
        # Fallback: try direct tool access for spindle speed
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
    """
    Extract geometry parameters from an operation.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Geometry parameters with metadata
    """
    geometry = {}
    
    try:
        if hasattr(operation, 'parameters'):
            params = operation.parameters
            
            # Common geometry parameter names
            geometry_params = [
                ('stepover', 'stepover', '%'),
                ('stepdown', 'stepdown', 'mm'),
                ('optimalLoad', 'optimal_load', 'mm'),
                ('tolerance', 'tolerance', 'mm'),
                ('stockToLeave', 'stock_to_leave', 'mm'),
                ('radialStockToLeave', 'radial_stock_to_leave', 'mm'),
                ('axialStockToLeave', 'axial_stock_to_leave', 'mm'),
                ('finishingStepover', 'finishing_stepover', 'mm'),
                ('finishingStepdown', 'finishing_stepdown', 'mm'),
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


def _extract_heights_params(operation: adsk.cam.Operation) -> dict:
    """
    Extract height parameters from an operation.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Height parameters with metadata
    """
    heights = {}
    
    try:
        if hasattr(operation, 'parameters'):
            params = operation.parameters
            
            # Common height parameter names
            height_params = [
                ('clearanceHeight_value', 'clearance_height', 'mm'),
                ('retractHeight_value', 'retract_height', 'mm'),
                ('feedHeight_value', 'feed_height', 'mm'),
                ('topHeight_value', 'top_height', 'mm'),
                ('bottomHeight_value', 'bottom_height', 'mm'),
            ]
            
            for param_name, output_name, default_unit in height_params:
                try:
                    param = params.itemByName(param_name)
                    if param:
                        param_data = {
                            "value": param.value.value if hasattr(param.value, 'value') else param.value,
                            "type": "numeric",
                            "editable": True,
                            "unit": default_unit
                        }
                        
                        heights[output_name] = param_data
                except Exception:
                    continue
        
    except Exception:
        pass
    
    return heights


def _extract_tool_reference(operation: adsk.cam.Operation) -> dict:
    """
    Extract tool reference information from an operation.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Tool reference data
    """
    tool_ref = {}
    
    try:
        tool = operation.tool
        if tool:
            tool_ref = {
                "id": tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool)),
                "name": tool.description if tool.description else tool.name,
                "diameter": tool.diameter if hasattr(tool, 'diameter') else None,
                "diameter_unit": "mm"
            }
    except Exception:
        pass
    
    return tool_ref


def _extract_tool_settings(operation: adsk.cam.Operation) -> dict:
    """
    Extract tool settings (preset cutting parameters) from an operation's tool.
    
    Extracts preset spindle speed, surface speed, feed per tooth, ramp spindle speed,
    plunge spindle speed, and feed per revolution from the tool definition.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Tool settings parameters with metadata including:
            - preset_spindle_speed: Preset spindle speed from tool library
            - surface_speed: Surface speed (cutting speed)
            - feed_per_tooth: Feed per tooth value
            - ramp_spindle_speed: Spindle speed for ramping moves
            - plunge_spindle_speed: Spindle speed for plunge moves
            - feed_per_revolution: Feed per revolution value
    
    Requirements: 2.7
    """
    tool_settings = {}
    
    try:
        tool = operation.tool
        if not tool:
            return tool_settings
        
        # Extract preset spindle speed
        if hasattr(tool, 'spindleSpeed'):
            tool_settings['preset_spindle_speed'] = {
                "value": tool.spindleSpeed,
                "unit": "rpm",
                "type": "numeric"
            }
        
        # Extract surface speed (cutting speed)
        if hasattr(tool, 'surfaceSpeed'):
            tool_settings['surface_speed'] = {
                "value": tool.surfaceSpeed,
                "unit": "m/min",
                "type": "numeric"
            }
        
        # Extract feed per tooth
        if hasattr(tool, 'feedPerTooth'):
            tool_settings['feed_per_tooth'] = {
                "value": tool.feedPerTooth,
                "unit": "mm",
                "type": "numeric"
            }
        
        # Extract ramp spindle speed
        if hasattr(tool, 'rampSpindleSpeed'):
            tool_settings['ramp_spindle_speed'] = {
                "value": tool.rampSpindleSpeed,
                "unit": "rpm",
                "type": "numeric"
            }
        
        # Extract plunge spindle speed
        if hasattr(tool, 'plungeSpindleSpeed'):
            tool_settings['plunge_spindle_speed'] = {
                "value": tool.plungeSpindleSpeed,
                "unit": "rpm",
                "type": "numeric"
            }
        
        # Extract feed per revolution
        if hasattr(tool, 'feedPerRevolution'):
            tool_settings['feed_per_revolution'] = {
                "value": tool.feedPerRevolution,
                "unit": "mm/rev",
                "type": "numeric"
            }
        
        # Try alternative property names that may exist in Fusion 360 API
        # Some tools use different property naming conventions
        
        # Try to get cutting data from tool presets if direct properties not available
        if hasattr(tool, 'presets') and tool.presets:
            try:
                presets = tool.presets
                if presets.count > 0:
                    # Use the first preset (default)
                    preset = presets.item(0)
                    
                    if 'preset_spindle_speed' not in tool_settings and hasattr(preset, 'spindleSpeed'):
                        tool_settings['preset_spindle_speed'] = {
                            "value": preset.spindleSpeed,
                            "unit": "rpm",
                            "type": "numeric"
                        }
                    
                    if 'surface_speed' not in tool_settings and hasattr(preset, 'surfaceSpeed'):
                        tool_settings['surface_speed'] = {
                            "value": preset.surfaceSpeed,
                            "unit": "m/min",
                            "type": "numeric"
                        }
                    
                    if 'feed_per_tooth' not in tool_settings and hasattr(preset, 'feedPerTooth'):
                        tool_settings['feed_per_tooth'] = {
                            "value": preset.feedPerTooth,
                            "unit": "mm",
                            "type": "numeric"
                        }
                    
                    if 'ramp_spindle_speed' not in tool_settings and hasattr(preset, 'rampSpindleSpeed'):
                        tool_settings['ramp_spindle_speed'] = {
                            "value": preset.rampSpindleSpeed,
                            "unit": "rpm",
                            "type": "numeric"
                        }
                    
                    if 'plunge_spindle_speed' not in tool_settings and hasattr(preset, 'plungeSpindleSpeed'):
                        tool_settings['plunge_spindle_speed'] = {
                            "value": preset.plungeSpindleSpeed,
                            "unit": "rpm",
                            "type": "numeric"
                        }
                    
                    if 'feed_per_revolution' not in tool_settings and hasattr(preset, 'feedPerRevolution'):
                        tool_settings['feed_per_revolution'] = {
                            "value": preset.feedPerRevolution,
                            "unit": "mm/rev",
                            "type": "numeric"
                        }
            except Exception:
                pass
        
    except Exception:
        pass
    
    return tool_settings


def get_toolpath_parameters(cam: adsk.cam.CAM, toolpath_id: str) -> dict:
    """
    Extract all parameters from a toolpath operation.
    
    Includes feeds/speeds, geometry settings, heights, tool reference, and tool settings.
    Each parameter includes metadata (type, unit, constraints, editable flag).
    
    Args:
        cam: The CAM product instance
        toolpath_id: The unique identifier of the toolpath
        
    Returns:
        dict: Complete toolpath parameters including:
            - id, name, type, setup_name
            - tool: Tool reference information
            - tool_settings: Preset cutting parameters from tool library including:
                - preset_spindle_speed: Preset spindle speed from tool library
                - surface_speed: Surface speed (cutting speed)
                - feed_per_tooth: Feed per tooth value
                - ramp_spindle_speed: Spindle speed for ramping moves
                - plunge_spindle_speed: Spindle speed for plunge moves
                - feed_per_revolution: Feed per revolution value
            - parameters: Organized by category (feeds_and_speeds, geometry, heights)
            - error: Error information if toolpath not found
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 3.1, 3.2, 3.3, 3.4
    """
    result = {}
    
    if not cam:
        return {
            "error": True,
            "message": "No CAM data present in the document",
            "code": "NO_CAM_DATA"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Get parent setup name
        setup_name = ""
        if hasattr(operation, 'parentSetup') and operation.parentSetup:
            setup_name = operation.parentSetup.name
        
        result = {
            "id": toolpath_id,
            "name": operation.name,
            "type": _get_operation_type(operation),
            "setup_name": setup_name,
            "tool": _extract_tool_reference(operation),
            "tool_settings": _extract_tool_settings(operation),
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



def _find_tool_by_id(cam: adsk.cam.CAM, tool_id: str) -> Optional[adsk.cam.Tool]:
    """
    Find a tool by its ID across all setups and operations.
    
    Args:
        cam: The CAM product instance
        tool_id: The unique identifier of the tool
        
    Returns:
        adsk.cam.Tool | None: The tool if found, None otherwise
    """
    if not cam:
        return None
    
    try:
        setups = cam.setups
        if not setups:
            return None
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            # Check operations for tools
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    if hasattr(operation, 'tool') and operation.tool:
                        tool = operation.tool
                        current_id = tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool))
                        if current_id == tool_id:
                            return tool
            
            # Check folder operations
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
                                        current_id = tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool))
                                        if current_id == tool_id:
                                            return tool
        
        return None
        
    except Exception:
        return None


def get_tool_info(cam: adsk.cam.CAM, tool_id: str) -> dict:
    """
    Extract tool geometry and specifications from a tool.
    
    Includes diameter, length, flute count, material, coating.
    
    Args:
        cam: The CAM product instance
        tool_id: The unique identifier of the tool
        
    Returns:
        dict: Tool information including:
            - id, name, type
            - geometry: diameter, overall_length, flute_length, shaft_diameter, corner_radius
            - specifications: flute_count, material, coating
            - tool_number
            - error: Error information if tool not found
    
    Requirements: 6.1, 6.2, 6.3, 6.4
    """
    if not cam:
        return {
            "error": True,
            "message": "No CAM data present in the document",
            "code": "NO_CAM_DATA"
        }
    
    try:
        tool = _find_tool_by_id(cam, tool_id)
        
        if not tool:
            return {
                "error": True,
                "message": f"Tool with ID '{tool_id}' not found",
                "code": "TOOL_NOT_FOUND"
            }
        
        # Extract tool type
        tool_type = "unknown"
        if hasattr(tool, 'type'):
            tool_type_enum = tool.type
            # Map enum to string
            type_map = {
                0: "flat end mill",
                1: "ball end mill",
                2: "bull nose end mill",
                3: "chamfer mill",
                4: "face mill",
                5: "slot mill",
                6: "radius mill",
                7: "dovetail mill",
                8: "tapered mill",
                9: "lollipop mill",
                10: "drill",
                11: "center drill",
                12: "spot drill",
                13: "tap",
                14: "reamer",
                15: "boring bar",
                16: "counter bore",
                17: "counter sink",
                18: "thread mill",
                19: "form mill",
                20: "engrave",
                21: "turning general",
                22: "turning boring",
                23: "turning threading",
                24: "turning grooving",
            }
            tool_type = type_map.get(tool_type_enum, str(tool_type_enum))
        
        # Extract geometry
        geometry = {
            "diameter": None,
            "diameter_unit": "mm",
            "overall_length": None,
            "flute_length": None,
            "shaft_diameter": None,
            "corner_radius": None
        }
        
        if hasattr(tool, 'diameter'):
            geometry["diameter"] = tool.diameter
        if hasattr(tool, 'bodyLength'):
            geometry["overall_length"] = tool.bodyLength
        if hasattr(tool, 'fluteLength'):
            geometry["flute_length"] = tool.fluteLength
        if hasattr(tool, 'shaftDiameter'):
            geometry["shaft_diameter"] = tool.shaftDiameter
        if hasattr(tool, 'cornerRadius'):
            geometry["corner_radius"] = tool.cornerRadius
        
        # Extract specifications
        specifications = {
            "flute_count": None,
            "material": None,
            "coating": None
        }
        
        if hasattr(tool, 'numberOfFlutes'):
            specifications["flute_count"] = tool.numberOfFlutes
        if hasattr(tool, 'material'):
            specifications["material"] = tool.material
        if hasattr(tool, 'coating'):
            specifications["coating"] = tool.coating
        
        # Get tool number
        tool_number = None
        if hasattr(tool, 'toolNumber'):
            tool_number = tool.toolNumber
        
        result = {
            "id": tool_id,
            "name": tool.description if hasattr(tool, 'description') and tool.description else tool.name,
            "type": tool_type,
            "geometry": geometry,
            "specifications": specifications,
            "tool_number": tool_number
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error extracting tool information: {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


def list_all_tools(cam: adsk.cam.CAM) -> dict:
    """
    List all tools used in the CAM document.
    
    Args:
        cam: The CAM product instance
        
    Returns:
        dict: A dictionary containing:
            - tools: List of tool summaries with id, name, type, diameter
            - total_count: Total number of unique tools
            - message: Optional message
    
    Requirements: 6.1
    """
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
            
            # Check operations for tools
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    if hasattr(operation, 'tool') and operation.tool:
                        tool = operation.tool
                        tool_id = tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool))
                        
                        if tool_id not in seen_tools:
                            seen_tools.add(tool_id)
                            tools_list.append({
                                "id": tool_id,
                                "name": tool.description if hasattr(tool, 'description') and tool.description else tool.name,
                                "type": _get_tool_type_string(tool),
                                "diameter": tool.diameter if hasattr(tool, 'diameter') else None,
                                "tool_number": tool.toolNumber if hasattr(tool, 'toolNumber') else None
                            })
            
            # Check folder operations
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
                                            tools_list.append({
                                                "id": tool_id,
                                                "name": tool.description if hasattr(tool, 'description') and tool.description else tool.name,
                                                "type": _get_tool_type_string(tool),
                                                "diameter": tool.diameter if hasattr(tool, 'diameter') else None,
                                                "tool_number": tool.toolNumber if hasattr(tool, 'toolNumber') else None
                                            })
        
        result["tools"] = tools_list
        result["total_count"] = len(tools_list)
        
        if len(tools_list) == 0:
            result["message"] = "No tools found in CAM document"
        
        return result
        
    except Exception as e:
        result["message"] = f"Error listing tools: {str(e)}"
        return result


def _get_tool_type_string(tool) -> str:
    """
    Get the tool type as a string.
    
    Args:
        tool: The CAM tool
        
    Returns:
        str: The tool type name
    """
    try:
        if hasattr(tool, 'type'):
            tool_type_enum = tool.type
            type_map = {
                0: "flat end mill",
                1: "ball end mill",
                2: "bull nose end mill",
                3: "chamfer mill",
                4: "face mill",
                5: "slot mill",
                6: "radius mill",
                7: "dovetail mill",
                8: "tapered mill",
                9: "lollipop mill",
                10: "drill",
                11: "center drill",
                12: "spot drill",
                13: "tap",
                14: "reamer",
                15: "boring bar",
                16: "counter bore",
                17: "counter sink",
                18: "thread mill",
                19: "form mill",
                20: "engrave",
            }
            return type_map.get(tool_type_enum, "unknown")
        return "unknown"
    except Exception:
        return "unknown"



def set_toolpath_parameter(cam: adsk.cam.CAM, toolpath_id: str, param_name: str, value: Any) -> dict:
    """
    Modify a parameter value for a specific toolpath operation.
    
    Validates parameter type and range before modification.
    Returns error for read-only or invalid parameters.
    
    Args:
        cam: The CAM product instance
        toolpath_id: The unique identifier of the toolpath
        param_name: The name of the parameter to modify
        value: The new value for the parameter
        
    Returns:
        dict: Result of the modification including:
            - success: Boolean indicating if modification succeeded
            - message: Description of the result
            - previous_value: The value before modification (if successful)
            - new_value: The new value (if successful)
            - error: Error information if modification failed
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    if not cam:
        return {
            "error": True,
            "message": "No CAM data present in the document",
            "code": "NO_CAM_DATA"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Check if operation has parameters
        if not hasattr(operation, 'parameters'):
            return {
                "error": True,
                "message": "Operation does not support parameter modification",
                "code": "NO_PARAMETERS"
            }
        
        params = operation.parameters
        
        # Map common parameter names to internal names
        param_name_map = {
            "spindle_speed": "tool_spindleSpeed",
            "cutting_feedrate": "tool_feedCutting",
            "plunge_feedrate": "tool_feedPlunge",
            "ramp_feedrate": "tool_feedRamp",
            "retract_feedrate": "tool_feedRetract",
            "stepover": "stepover",
            "stepdown": "stepdown",
            "optimal_load": "optimalLoad",
            "tolerance": "tolerance",
            "stock_to_leave": "stockToLeave",
            "clearance_height": "clearanceHeight_value",
            "retract_height": "retractHeight_value",
            "feed_height": "feedHeight_value",
            "top_height": "topHeight_value",
            "bottom_height": "bottomHeight_value",
        }
        
        # Get the internal parameter name
        internal_name = param_name_map.get(param_name, param_name)
        
        # Try to find the parameter
        param = None
        try:
            param = params.itemByName(internal_name)
        except Exception:
            pass
        
        if not param:
            return {
                "error": True,
                "message": f"Parameter '{param_name}' not found in toolpath",
                "code": "PARAMETER_NOT_FOUND"
            }
        
        # Check if parameter is read-only
        if hasattr(param, 'isReadOnly') and param.isReadOnly:
            return {
                "error": True,
                "message": f"Parameter '{param_name}' is read-only and cannot be modified",
                "code": "READ_ONLY"
            }
        
        # Get the current value for reporting
        previous_value = None
        try:
            if hasattr(param.value, 'value'):
                previous_value = param.value.value
            else:
                previous_value = param.value
        except Exception:
            pass
        
        # Validate and convert the value
        try:
            # Handle numeric values
            if isinstance(value, str):
                # Try to parse as number
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    # Keep as string for expression-based values
                    pass
            
            # Check for min/max constraints
            if hasattr(param, 'minimumValue') and param.minimumValue is not None:
                if isinstance(value, (int, float)) and value < param.minimumValue:
                    return {
                        "error": True,
                        "message": f"Value '{value}' is below minimum allowed value of {param.minimumValue} for parameter '{param_name}'",
                        "code": "INVALID_VALUE"
                    }
            
            if hasattr(param, 'maximumValue') and param.maximumValue is not None:
                if isinstance(value, (int, float)) and value > param.maximumValue:
                    return {
                        "error": True,
                        "message": f"Value '{value}' exceeds maximum allowed value of {param.maximumValue} for parameter '{param_name}'",
                        "code": "INVALID_VALUE"
                    }
            
            # Set the value
            if hasattr(param, 'expression'):
                # For expression-based parameters
                param.expression = str(value)
            elif hasattr(param.value, 'value'):
                # For value objects
                param.value.value = value
            else:
                # Direct value assignment
                param.value = value
            
            # Get the new value for confirmation
            new_value = None
            try:
                if hasattr(param.value, 'value'):
                    new_value = param.value.value
                else:
                    new_value = param.value
            except Exception:
                new_value = value
            
            return {
                "success": True,
                "message": f"Parameter '{param_name}' updated successfully",
                "previous_value": previous_value,
                "new_value": new_value
            }
            
        except Exception as e:
            return {
                "error": True,
                "message": f"Value '{value}' is invalid for parameter '{param_name}': {str(e)}",
                "code": "INVALID_VALUE"
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error modifying parameter: {str(e)}",
            "code": "MODIFICATION_ERROR"
        }
