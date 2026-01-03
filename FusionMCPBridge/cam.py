"""
CAM Module for Fusion 360 MCP Add-In

This module provides functions to access and manipulate CAM (Computer-Aided Manufacturing)
data in Fusion 360, including toolpaths, operations, and tool information.

Note: Tool lookup and serialization functions have been centralized in tool_library.py.
This module imports find_tool_by_id and serialize_tool from tool_library for consistency.
"""

import adsk.core
import adsk.fusion
import adsk.cam
from typing import Any, Optional

# Import centralized tool functions from tool_library module
from .tool_library import find_tool_by_id, serialize_tool


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


def validate_cam_product_with_details() -> dict:
    """
    Validate CAM product availability and provide detailed error information.
    
    Returns structured error responses for different failure modes including:
    - No active document
    - Document doesn't support CAM
    - No CAM data present
    - CAM workspace not active
    
    Returns:
        dict: Validation result with error details or success confirmation
            - valid: Boolean indicating if CAM product is available
            - cam_product: The CAM product instance if valid
            - error: Error information if validation fails
            - message: Clear error message for different failure modes
            - code: Error code for programmatic handling
    
    Requirements: 2.5
    """
    try:
        app = adsk.core.Application.get()
        if not app:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "Fusion 360 application is not available",
                "code": "NO_APPLICATION"
            }
        
        # Check for active document
        doc = app.activeDocument
        if not doc:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "No active document found. Please open a Fusion 360 document with CAM data",
                "code": "NO_DOCUMENT"
            }
        
        # Check if document has products
        products = doc.products
        if not products:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "Document does not support CAM operations. Please ensure this is a valid Fusion 360 design document",
                "code": "NO_PRODUCTS"
            }
        
        # Try to get the CAM product
        cam_product = products.itemByProductType('CAMProductType')
        if not cam_product:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "No CAM data present in the document. Please switch to the MANUFACTURE workspace and create CAM operations",
                "code": "NO_CAM_DATA"
            }
        
        # Cast to CAM product
        cam_instance = adsk.cam.CAM.cast(cam_product)
        if not cam_instance:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "CAM product exists but cannot be accessed. Please ensure CAM workspace is properly initialized",
                "code": "CAM_ACCESS_ERROR"
            }
        
        # Check if CAM has any setups (basic validation that CAM is usable)
        try:
            setups = cam_instance.setups
            if not setups:
                return {
                    "valid": False,
                    "cam_product": None,
                    "error": True,
                    "message": "CAM product exists but has no setups. Please create at least one CAM setup with toolpath operations",
                    "code": "NO_CAM_SETUPS"
                }
        except Exception:
            # If we can't access setups, CAM might not be fully initialized
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "CAM product exists but is not properly initialized. Please ensure you are in the MANUFACTURE workspace",
                "code": "CAM_NOT_INITIALIZED"
            }
        
        # All validations passed
        return {
            "valid": True,
            "cam_product": cam_instance,
            "error": False,
            "message": "CAM product is available and ready for operations",
            "code": "SUCCESS"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "cam_product": None,
            "error": True,
            "message": f"Unexpected error during CAM validation: {str(e)}",
            "code": "VALIDATION_ERROR"
        }


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
    
    Delegates to tool_library.serialize_tool() for consistent tool serialization
    across the codebase. Maintains the same return format for compatibility.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Tool data including name, id, type, diameter, overall_length, etc.
              Returns error info if tool cannot be accessed.
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
            return {"name": "No tool found", "id": None}
        
        # Delegate to centralized serialize_tool from tool_library module
        # This ensures consistent tool serialization across all endpoints
        return serialize_tool(tool)
        
    except Exception as e:
        return {"name": "Error accessing tool", "id": None, "error": str(e)}


def list_toolpaths_with_heights(cam: adsk.cam.CAM = None) -> dict:
    """
    List all toolpaths with embedded height parameter data.
    
    Combines existing toolpath listing with height extraction to provide
    comprehensive toolpath information including height parameters in a single call.
    Handles CAM documents without height data gracefully.
    
    Args:
        cam: The CAM product instance (optional, will be validated if None)
        
    Returns:
        dict: A dictionary containing:
            - setups: List of setup dictionaries, each containing:
                - id: Unique setup identifier
                - name: Setup name
                - toolpaths: List of toolpath dictionaries with id, name, type, tool, heights, is_valid
            - total_count: Total number of toolpaths
            - message: Optional message (e.g., when no CAM data exists)
            - error: Error information if CAM validation fails
    
    Requirements: 1.1, 1.4, 2.1, 2.5
    """
    # Validate CAM product if not provided
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
            
            # Get all operations in this setup
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    
                    tool_data = _get_tool_data_from_operation(operation)
                    
                    # Extract height parameters for this toolpath
                    heights_data = _extract_heights_params(operation)
                    
                    toolpath_data = {
                        "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_{op_idx}",
                        "name": operation.name,
                        "type": _get_operation_type(operation),
                        "tool": tool_data,
                        "heights": heights_data,
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
                                    
                                    # Extract height parameters for this toolpath
                                    heights_data = _extract_heights_params(operation)
                                    
                                    toolpath_data = {
                                        "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{setup_idx}_f{folder_idx}_{op_idx}",
                                        "name": operation.name,
                                        "type": _get_operation_type(operation),
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


def get_detailed_heights(cam: adsk.cam.CAM = None, toolpath_id: str = None) -> dict:
    """
    Extract comprehensive height information for a single toolpath.
    
    Provides detailed height parameter data including all available height parameters
    with complete metadata (expressions, units, constraints, editability).
    Returns structured error for missing toolpaths.
    
    Args:
        cam: The CAM product instance (optional, will be validated if None)
        toolpath_id: The unique identifier of the toolpath
        
    Returns:
        dict: Detailed height information including:
            - id: Toolpath identifier
            - name: Toolpath name
            - type: Operation type
            - setup_name: Parent setup name
            - heights: Complete height parameter data with metadata
            - error: Error information if toolpath not found or CAM validation fails
    
    Requirements: 2.2, 3.1, 3.2, 3.3, 3.4, 2.5
    """
    # Validate CAM product if not provided
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate toolpath_id parameter
    if not toolpath_id:
        return {
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found. Please verify the toolpath ID exists in the current CAM document",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Get parent setup name
        setup_name = ""
        try:
            if hasattr(operation, 'parentSetup') and operation.parentSetup:
                setup_name = operation.parentSetup.name
        except Exception:
            # If we can't get setup name, continue without it
            setup_name = "Unknown Setup"
        
        # Extract comprehensive height information
        heights_data = _extract_heights_params(operation)
        
        result = {
            "id": toolpath_id,
            "name": operation.name,
            "type": _get_operation_type(operation),
            "setup_name": setup_name,
            "heights": heights_data
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error extracting detailed heights for toolpath '{toolpath_id}': {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


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
    Extract height parameters from an operation with comprehensive metadata.
    
    Extracts expression strings, parameter metadata (editable, min/max constraints),
    unit information, and handles missing parameters gracefully.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Height parameters with complete metadata including:
            - value: Evaluated numeric value
            - unit: Parameter unit (extracted from parameter object)
            - expression: Expression string (e.g., "stockTop + 5mm")
            - type: Parameter type ("numeric")
            - editable: Whether parameter can be modified
            - min_value: Minimum allowed value (if available)
            - max_value: Maximum allowed value (if available)
    
    Requirements: 1.2, 2.3, 2.4, 3.5
    """
    heights = {}
    
    try:
        if hasattr(operation, 'parameters'):
            params = operation.parameters
            
            # Common height parameter names with their display names and default units
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
                        # Initialize parameter data structure
                        param_data = {
                            "value": None,
                            "unit": default_unit,
                            "expression": None,
                            "type": "numeric",
                            "editable": True,
                            "min_value": None,
                            "max_value": None
                        }
                        
                        # Extract numeric value
                        try:
                            if hasattr(param.value, 'value'):
                                param_data["value"] = param.value.value
                            else:
                                param_data["value"] = param.value
                        except Exception:
                            param_data["value"] = None
                        
                        # Extract expression string
                        try:
                            if hasattr(param, 'expression') and param.expression:
                                param_data["expression"] = param.expression
                            elif hasattr(param.value, 'expression') and param.value.expression:
                                param_data["expression"] = param.value.expression
                        except Exception:
                            pass
                        
                        # Extract unit information from parameter object
                        try:
                            if hasattr(param.value, 'unit') and param.value.unit:
                                param_data["unit"] = param.value.unit
                            elif hasattr(param, 'unit') and param.unit:
                                param_data["unit"] = param.unit
                        except Exception:
                            # Keep default unit if extraction fails
                            pass
                        
                        # Extract editability flag
                        try:
                            if hasattr(param, 'isReadOnly'):
                                param_data["editable"] = not param.isReadOnly
                            elif hasattr(param.value, 'isReadOnly'):
                                param_data["editable"] = not param.value.isReadOnly
                        except Exception:
                            # Default to editable if cannot determine
                            param_data["editable"] = True
                        
                        # Extract min/max constraints
                        try:
                            if hasattr(param, 'minimumValue') and param.minimumValue is not None:
                                param_data["min_value"] = param.minimumValue
                            elif hasattr(param.value, 'minimumValue') and param.value.minimumValue is not None:
                                param_data["min_value"] = param.value.minimumValue
                        except Exception:
                            pass
                        
                        try:
                            if hasattr(param, 'maximumValue') and param.maximumValue is not None:
                                param_data["max_value"] = param.maximumValue
                            elif hasattr(param.value, 'maximumValue') and param.value.maximumValue is not None:
                                param_data["max_value"] = param.value.maximumValue
                        except Exception:
                            pass
                        
                        heights[output_name] = param_data
                        
                except Exception:
                    # Handle missing parameters gracefully by continuing to next parameter
                    # This ensures partial height data is still returned even if some parameters fail
                    continue
        
    except Exception:
        # Handle case where operation has no parameters at all
        # Return empty dict rather than failing completely
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
                "name": tool.description if hasattr(tool, 'description') and tool.description else "Unnamed Tool",
                "diameter": tool.diameter if hasattr(tool, 'diameter') else None,
                "diameter_unit": "mm"
            }
    except Exception:
        pass
    
    return tool_ref


def _extract_linking_params(operation: adsk.cam.Operation) -> dict:
    """
    Extract linking parameters organized by dialog sections.
    
    Handles operation-specific parameter structures (2D Pocket, Trace, 3D) and
    identifies editable vs read-only linking parameters. Returns parameters
    grouped by interface sections as they appear in Fusion 360.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Linking configuration including:
            - operation_type: Type of operation (2d_pocket, trace, 3d_adaptive, etc.)
            - sections: Dictionary of dialog sections with their parameters
            - editable_parameters: List of parameter paths that can be modified
    
    Requirements: 7.1, 7.2, 7.3, 7.5, 8.1, 8.2, 8.3, 8.4
    """
    linking_config = {
        "operation_type": "unknown",
        "sections": {},
        "editable_parameters": []
    }
    
    try:
        if not operation or not hasattr(operation, 'parameters'):
            return linking_config
        
        # Determine operation type
        operation_type = _get_operation_type(operation).lower()
        linking_config["operation_type"] = operation_type
        
        params = operation.parameters
        
        # Extract parameters based on operation type
        if "pocket" in operation_type or "2d" in operation_type:
            linking_config = _extract_2d_linking_params(params, linking_config)
        elif "trace" in operation_type or "contour" in operation_type:
            linking_config = _extract_trace_linking_params(params, linking_config)
        elif "3d" in operation_type or "adaptive" in operation_type or "parallel" in operation_type:
            linking_config = _extract_3d_linking_params(params, linking_config)
        elif "drill" in operation_type:
            linking_config = _extract_drill_linking_params(params, linking_config)
        else:
            # Generic linking parameter extraction
            linking_config = _extract_generic_linking_params(params, linking_config)
        
        return linking_config
        
    except Exception:
        # Return default configuration on error
        return {
            "operation_type": "unknown",
            "sections": {},
            "editable_parameters": []
        }


def _extract_2d_linking_params(params, linking_config: dict) -> dict:
    """Extract linking parameters for 2D operations (Pocket, etc.)."""
    try:
        # Leads & Transitions section
        leads_transitions = {}
        
        # Lead-in parameters
        lead_in = {}
        try:
            lead_in_type_param = params.itemByName("leadInType")
            if lead_in_type_param:
                lead_in["type"] = _get_param_value(lead_in_type_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_in.type")
        except Exception:
            pass
        
        try:
            lead_in_radius_param = params.itemByName("leadInRadius")
            if lead_in_radius_param:
                lead_in["arc_radius"] = _get_param_value(lead_in_radius_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_in.arc_radius")
        except Exception:
            pass
        
        try:
            lead_in_sweep_param = params.itemByName("leadInSweepAngle")
            if lead_in_sweep_param:
                lead_in["arc_sweep"] = _get_param_value(lead_in_sweep_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_in.arc_sweep")
        except Exception:
            pass
        
        try:
            vertical_lead_in_param = params.itemByName("verticalLeadIn")
            if vertical_lead_in_param:
                lead_in["vertical_lead_in"] = _get_param_value(vertical_lead_in_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_in.vertical_lead_in")
        except Exception:
            pass
        
        # Lead-out parameters
        lead_out = {}
        try:
            lead_out_type_param = params.itemByName("leadOutType")
            if lead_out_type_param:
                lead_out["type"] = _get_param_value(lead_out_type_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_out.type")
        except Exception:
            pass
        
        try:
            lead_out_radius_param = params.itemByName("leadOutRadius")
            if lead_out_radius_param:
                lead_out["arc_radius"] = _get_param_value(lead_out_radius_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_out.arc_radius")
        except Exception:
            pass
        
        try:
            lead_out_sweep_param = params.itemByName("leadOutSweepAngle")
            if lead_out_sweep_param:
                lead_out["arc_sweep"] = _get_param_value(lead_out_sweep_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_out.arc_sweep")
        except Exception:
            pass
        
        # Transitions parameters
        transitions = {}
        try:
            transition_type_param = params.itemByName("transitionType")
            if transition_type_param:
                transitions["type"] = _get_param_value(transition_type_param)
                linking_config["editable_parameters"].append("leads_and_transitions.transitions.type")
        except Exception:
            pass
        
        try:
            lift_height_param = params.itemByName("liftHeight")
            if lift_height_param:
                transitions["lift_height"] = _get_param_value(lift_height_param)
                linking_config["editable_parameters"].append("leads_and_transitions.transitions.lift_height")
        except Exception:
            pass
        
        try:
            order_by_depth_param = params.itemByName("orderByDepth")
            if order_by_depth_param:
                transitions["order_by_depth"] = _get_param_value(order_by_depth_param)
                linking_config["editable_parameters"].append("leads_and_transitions.transitions.order_by_depth")
        except Exception:
            pass
        
        try:
            keep_tool_down_param = params.itemByName("keepToolDown")
            if keep_tool_down_param:
                transitions["keep_tool_down"] = _get_param_value(keep_tool_down_param)
                linking_config["editable_parameters"].append("leads_and_transitions.transitions.keep_tool_down")
        except Exception:
            pass
        
        # Build leads & transitions section
        if lead_in:
            leads_transitions["lead_in"] = lead_in
        if lead_out:
            leads_transitions["lead_out"] = lead_out
        if transitions:
            leads_transitions["transitions"] = transitions
        
        if leads_transitions:
            linking_config["sections"]["leads_and_transitions"] = leads_transitions
        
        # Entry positioning section
        entry_positioning = {}
        try:
            clearance_height_param = params.itemByName("clearanceHeight_value")
            if clearance_height_param:
                entry_positioning["clearance_height"] = _get_param_value(clearance_height_param)
        except Exception:
            pass
        
        try:
            feed_height_param = params.itemByName("feedHeight_value")
            if feed_height_param:
                entry_positioning["feed_height"] = _get_param_value(feed_height_param)
        except Exception:
            pass
        
        try:
            top_height_param = params.itemByName("topHeight_value")
            if top_height_param:
                entry_positioning["top_height"] = _get_param_value(top_height_param)
        except Exception:
            pass
        
        if entry_positioning:
            linking_config["sections"]["entry_positioning"] = entry_positioning
        
    except Exception:
        pass
    
    return linking_config


def _extract_trace_linking_params(params, linking_config: dict) -> dict:
    """Extract linking parameters for Trace operations."""
    try:
        # Contact point section
        contact_point = {}
        try:
            contact_point_param = params.itemByName("contactPoint")
            if contact_point_param:
                contact_point["type"] = _get_param_value(contact_point_param)
                linking_config["editable_parameters"].append("contact_point.type")
        except Exception:
            pass
        
        try:
            contact_distance_param = params.itemByName("contactDistance")
            if contact_distance_param:
                contact_point["distance"] = _get_param_value(contact_distance_param)
                linking_config["editable_parameters"].append("contact_point.distance")
        except Exception:
            pass
        
        if contact_point:
            linking_config["sections"]["contact_point"] = contact_point
        
        # Approach/Retract section
        approach_retract = {}
        try:
            approach_distance_param = params.itemByName("approachDistance")
            if approach_distance_param:
                approach_retract["approach_distance"] = _get_param_value(approach_distance_param)
                linking_config["editable_parameters"].append("approach_retract.approach_distance")
        except Exception:
            pass
        
        try:
            retract_distance_param = params.itemByName("retractDistance")
            if retract_distance_param:
                approach_retract["retract_distance"] = _get_param_value(retract_distance_param)
                linking_config["editable_parameters"].append("approach_retract.retract_distance")
        except Exception:
            pass
        
        if approach_retract:
            linking_config["sections"]["approach_retract"] = approach_retract
        
        # Transitions section (similar to 2D operations)
        transitions = {}
        try:
            transition_type_param = params.itemByName("transitionType")
            if transition_type_param:
                transitions["type"] = _get_param_value(transition_type_param)
                linking_config["editable_parameters"].append("transitions.type")
        except Exception:
            pass
        
        if transitions:
            linking_config["sections"]["transitions"] = transitions
        
    except Exception:
        pass
    
    return linking_config


def _extract_3d_linking_params(params, linking_config: dict) -> dict:
    """Extract linking parameters for 3D operations."""
    try:
        # Linking section
        linking_section = {}
        
        # Approach parameters
        approach = {}
        try:
            approach_type_param = params.itemByName("approachType")
            if approach_type_param:
                approach["type"] = _get_param_value(approach_type_param)
                linking_config["editable_parameters"].append("linking.approach.type")
        except Exception:
            pass
        
        try:
            approach_distance_param = params.itemByName("approachDistance")
            if approach_distance_param:
                approach["distance"] = _get_param_value(approach_distance_param)
                linking_config["editable_parameters"].append("linking.approach.distance")
        except Exception:
            pass
        
        try:
            approach_angle_param = params.itemByName("approachAngle")
            if approach_angle_param:
                approach["angle"] = _get_param_value(approach_angle_param)
                linking_config["editable_parameters"].append("linking.approach.angle")
        except Exception:
            pass
        
        # Retract parameters
        retract = {}
        try:
            retract_type_param = params.itemByName("retractType")
            if retract_type_param:
                retract["type"] = _get_param_value(retract_type_param)
                linking_config["editable_parameters"].append("linking.retract.type")
        except Exception:
            pass
        
        try:
            retract_distance_param = params.itemByName("retractDistance")
            if retract_distance_param:
                retract["distance"] = _get_param_value(retract_distance_param)
                linking_config["editable_parameters"].append("linking.retract.distance")
        except Exception:
            pass
        
        try:
            retract_angle_param = params.itemByName("retractAngle")
            if retract_angle_param:
                retract["angle"] = _get_param_value(retract_angle_param)
                linking_config["editable_parameters"].append("linking.retract.angle")
        except Exception:
            pass
        
        # Clearance parameters
        clearance = {}
        try:
            clearance_height_param = params.itemByName("clearanceHeight_value")
            if clearance_height_param:
                clearance["height"] = _get_param_value(clearance_height_param)
        except Exception:
            pass
        
        try:
            clearance_type_param = params.itemByName("clearanceType")
            if clearance_type_param:
                clearance["type"] = _get_param_value(clearance_type_param)
        except Exception:
            pass
        
        # Build linking section
        if approach:
            linking_section["approach"] = approach
        if retract:
            linking_section["retract"] = retract
        if clearance:
            linking_section["clearance"] = clearance
        
        if linking_section:
            linking_config["sections"]["linking"] = linking_section
        
        # Transitions section
        transitions = {}
        try:
            stay_down_distance_param = params.itemByName("stayDownDistance")
            if stay_down_distance_param:
                transitions["stay_down_distance"] = _get_param_value(stay_down_distance_param)
                linking_config["editable_parameters"].append("transitions.stay_down_distance")
        except Exception:
            pass
        
        try:
            lift_height_param = params.itemByName("liftHeight")
            if lift_height_param:
                transitions["lift_height"] = _get_param_value(lift_height_param)
                linking_config["editable_parameters"].append("transitions.lift_height")
        except Exception:
            pass
        
        try:
            order_optimization_param = params.itemByName("orderOptimization")
            if order_optimization_param:
                transitions["order_optimization"] = _get_param_value(order_optimization_param)
                linking_config["editable_parameters"].append("transitions.order_optimization")
        except Exception:
            pass
        
        if transitions:
            linking_config["sections"]["transitions"] = transitions
        
    except Exception:
        pass
    
    return linking_config


def _extract_drill_linking_params(params, linking_config: dict) -> dict:
    """Extract linking parameters for Drill operations."""
    try:
        # Drill cycle section
        drill_cycle = {}
        try:
            cycle_type_param = params.itemByName("cycleType")
            if cycle_type_param:
                drill_cycle["cycle_type"] = _get_param_value(cycle_type_param)
                linking_config["editable_parameters"].append("drill_cycle.cycle_type")
        except Exception:
            pass
        
        try:
            peck_depth_param = params.itemByName("peckDepth")
            if peck_depth_param:
                drill_cycle["peck_depth"] = _get_param_value(peck_depth_param)
                linking_config["editable_parameters"].append("drill_cycle.peck_depth")
        except Exception:
            pass
        
        try:
            dwell_time_param = params.itemByName("dwellTime")
            if dwell_time_param:
                drill_cycle["dwell_time"] = _get_param_value(dwell_time_param)
                linking_config["editable_parameters"].append("drill_cycle.dwell_time")
        except Exception:
            pass
        
        try:
            retract_behavior_param = params.itemByName("retractBehavior")
            if retract_behavior_param:
                drill_cycle["retract_behavior"] = _get_param_value(retract_behavior_param)
                linking_config["editable_parameters"].append("drill_cycle.retract_behavior")
        except Exception:
            pass
        
        if drill_cycle:
            linking_config["sections"]["drill_cycle"] = drill_cycle
        
    except Exception:
        pass
    
    return linking_config


def _extract_generic_linking_params(params, linking_config: dict) -> dict:
    """Extract generic linking parameters for unknown operation types."""
    try:
        # Generic linking section
        generic_linking = {}
        
        # Common linking parameters that might exist
        common_params = [
            ("clearanceHeight_value", "clearance_height"),
            ("retractHeight_value", "retract_height"),
            ("feedHeight_value", "feed_height"),
            ("approachDistance", "approach_distance"),
            ("retractDistance", "retract_distance"),
            ("liftHeight", "lift_height")
        ]
        
        for param_name, output_name in common_params:
            try:
                param = params.itemByName(param_name)
                if param:
                    generic_linking[output_name] = _get_param_value(param)
                    linking_config["editable_parameters"].append(f"generic_linking.{output_name}")
            except Exception:
                continue
        
        if generic_linking:
            linking_config["sections"]["generic_linking"] = generic_linking
        
    except Exception:
        pass
    
    return linking_config


def _get_param_value(param) -> any:
    """Extract value from a parameter object."""
    try:
        if hasattr(param, 'value'):
            if hasattr(param.value, 'value'):
                return param.value.value
            else:
                return param.value
        return None
    except Exception:
        return None


def _extract_pass_params(operation: adsk.cam.Operation) -> dict:
    """
    Extract multi-pass configuration from an operation.
    
    Identifies pass types (roughing, semi-finishing, finishing) and extracts
    pass-specific parameters including depths, stock-to-leave, stepover/stepdown.
    Handles operations without pass configuration gracefully.
    
    Args:
        operation: The CAM operation
        
    Returns:
        dict: Pass configuration including:
            - pass_type: Type of pass configuration (single, multiple_depths, finishing)
            - total_passes: Number of passes
            - passes: List of pass dictionaries with pass_number, pass_type, depth, 
                     stock_to_leave, and parameters
            - spring_passes: Number of spring passes
            - finishing_enabled: Whether finishing passes are enabled
    
    Requirements: 1.1, 1.2, 3.1, 3.2, 3.3
    """
    pass_config = {
        "pass_type": "single",
        "total_passes": 1,
        "passes": [],
        "spring_passes": 0,
        "finishing_enabled": False
    }
    
    try:
        if not operation or not hasattr(operation, 'parameters'):
            return pass_config
        
        params = operation.parameters
        
        # Check for multiple depths configuration
        multiple_depths_enabled = False
        finishing_passes_enabled = False
        spring_passes_count = 0
        
        try:
            # Check for multiple depths parameter
            multiple_depths_param = params.itemByName("multipleDepths")
            if multiple_depths_param and hasattr(multiple_depths_param, 'value'):
                multiple_depths_enabled = multiple_depths_param.value
        except Exception:
            pass
        
        try:
            # Check for finishing passes parameter
            finishing_param = params.itemByName("useFinishingPasses")
            if finishing_param and hasattr(finishing_param, 'value'):
                finishing_passes_enabled = finishing_param.value
        except Exception:
            pass
        
        try:
            # Check for spring passes parameter
            spring_param = params.itemByName("springPasses")
            if spring_param and hasattr(spring_param, 'value'):
                spring_passes_count = spring_param.value if isinstance(spring_param.value, int) else 0
        except Exception:
            pass
        
        # Extract depth-related parameters
        maximum_stepdown = None
        finishing_stepdown = None
        stock_to_leave_radial = 0.0
        stock_to_leave_axial = 0.0
        finishing_stock_radial = 0.0
        finishing_stock_axial = 0.0
        
        try:
            stepdown_param = params.itemByName("stepdown")
            if stepdown_param and hasattr(stepdown_param, 'value'):
                maximum_stepdown = stepdown_param.value.value if hasattr(stepdown_param.value, 'value') else stepdown_param.value
        except Exception:
            pass
        
        try:
            finishing_stepdown_param = params.itemByName("finishingStepdown")
            if finishing_stepdown_param and hasattr(finishing_stepdown_param, 'value'):
                finishing_stepdown = finishing_stepdown_param.value.value if hasattr(finishing_stepdown_param.value, 'value') else finishing_stepdown_param.value
        except Exception:
            pass
        
        try:
            radial_stock_param = params.itemByName("radialStockToLeave")
            if radial_stock_param and hasattr(radial_stock_param, 'value'):
                stock_to_leave_radial = radial_stock_param.value.value if hasattr(radial_stock_param.value, 'value') else radial_stock_param.value
        except Exception:
            pass
        
        try:
            axial_stock_param = params.itemByName("axialStockToLeave")
            if axial_stock_param and hasattr(axial_stock_param, 'value'):
                stock_to_leave_axial = axial_stock_param.value.value if hasattr(axial_stock_param.value, 'value') else axial_stock_param.value
        except Exception:
            pass
        
        try:
            finishing_radial_param = params.itemByName("finishingRadialStockToLeave")
            if finishing_radial_param and hasattr(finishing_radial_param, 'value'):
                finishing_stock_radial = finishing_radial_param.value.value if hasattr(finishing_radial_param.value, 'value') else finishing_radial_param.value
        except Exception:
            pass
        
        try:
            finishing_axial_param = params.itemByName("finishingAxialStockToLeave")
            if finishing_axial_param and hasattr(finishing_axial_param, 'value'):
                finishing_stock_axial = finishing_axial_param.value.value if hasattr(finishing_axial_param.value, 'value') else finishing_axial_param.value
        except Exception:
            pass
        
        # Extract stepover parameters
        stepover = None
        finishing_stepover = None
        
        try:
            stepover_param = params.itemByName("stepover")
            if stepover_param and hasattr(stepover_param, 'value'):
                stepover = stepover_param.value.value if hasattr(stepover_param.value, 'value') else stepover_param.value
        except Exception:
            pass
        
        try:
            finishing_stepover_param = params.itemByName("finishingStepover")
            if finishing_stepover_param and hasattr(finishing_stepover_param, 'value'):
                finishing_stepover = finishing_stepover_param.value.value if hasattr(finishing_stepover_param.value, 'value') else finishing_stepover_param.value
        except Exception:
            pass
        
        # Extract feedrate parameters
        cutting_feedrate = None
        finishing_feedrate = None
        
        try:
            feed_param = params.itemByName("tool_feedCutting")
            if feed_param and hasattr(feed_param, 'value'):
                cutting_feedrate = feed_param.value.value if hasattr(feed_param.value, 'value') else feed_param.value
        except Exception:
            pass
        
        try:
            finishing_feed_param = params.itemByName("finishingFeedrate")
            if finishing_feed_param and hasattr(finishing_feed_param, 'value'):
                finishing_feedrate = finishing_feed_param.value.value if hasattr(finishing_feed_param.value, 'value') else finishing_feed_param.value
        except Exception:
            pass
        
        # Get total cutting depth
        total_depth = None
        try:
            # Try to get depth from bottom height parameter
            bottom_param = params.itemByName("bottomHeight_value")
            top_param = params.itemByName("topHeight_value")
            if bottom_param and top_param:
                bottom_val = bottom_param.value.value if hasattr(bottom_param.value, 'value') else bottom_param.value
                top_val = top_param.value.value if hasattr(top_param.value, 'value') else top_param.value
                total_depth = abs(top_val - bottom_val)
        except Exception:
            pass
        
        # Build pass configuration based on detected parameters
        passes = []
        pass_count = 1
        
        if multiple_depths_enabled and maximum_stepdown and total_depth:
            # Calculate number of roughing passes needed
            roughing_depth = total_depth
            if finishing_passes_enabled:
                # Reserve material for finishing pass
                roughing_depth = total_depth - max(finishing_stock_axial, 0.1)
            
            roughing_passes = max(1, int(roughing_depth / maximum_stepdown))
            pass_count = roughing_passes
            
            # Create roughing passes
            for i in range(roughing_passes):
                pass_depth = min(maximum_stepdown, roughing_depth - (i * maximum_stepdown))
                
                pass_data = {
                    "pass_number": i + 1,
                    "pass_type": "roughing" if roughing_passes > 1 else "single",
                    "depth": pass_depth,
                    "stock_to_leave": {
                        "radial": stock_to_leave_radial,
                        "axial": stock_to_leave_axial
                    },
                    "parameters": {
                        "stepover": stepover,
                        "stepdown": maximum_stepdown,
                        "feedrate": cutting_feedrate
                    }
                }
                passes.append(pass_data)
            
            # Add finishing pass if enabled
            if finishing_passes_enabled:
                pass_count += 1
                finishing_pass = {
                    "pass_number": pass_count,
                    "pass_type": "finishing",
                    "depth": total_depth,
                    "stock_to_leave": {
                        "radial": finishing_stock_radial,
                        "axial": finishing_stock_axial
                    },
                    "parameters": {
                        "stepover": finishing_stepover or stepover,
                        "stepdown": finishing_stepdown or maximum_stepdown,
                        "feedrate": finishing_feedrate or cutting_feedrate
                    }
                }
                passes.append(finishing_pass)
            
            pass_config["pass_type"] = "multiple_depths"
            pass_config["total_passes"] = pass_count
            
        elif finishing_passes_enabled:
            # Single roughing pass + finishing pass
            roughing_pass = {
                "pass_number": 1,
                "pass_type": "roughing",
                "depth": total_depth or 0,
                "stock_to_leave": {
                    "radial": stock_to_leave_radial,
                    "axial": stock_to_leave_axial
                },
                "parameters": {
                    "stepover": stepover,
                    "stepdown": maximum_stepdown,
                    "feedrate": cutting_feedrate
                }
            }
            passes.append(roughing_pass)
            
            finishing_pass = {
                "pass_number": 2,
                "pass_type": "finishing",
                "depth": total_depth or 0,
                "stock_to_leave": {
                    "radial": finishing_stock_radial,
                    "axial": finishing_stock_axial
                },
                "parameters": {
                    "stepover": finishing_stepover or stepover,
                    "stepdown": finishing_stepdown or maximum_stepdown,
                    "feedrate": finishing_feedrate or cutting_feedrate
                }
            }
            passes.append(finishing_pass)
            
            pass_config["pass_type"] = "roughing_finishing"
            pass_config["total_passes"] = 2
            
        else:
            # Single pass operation
            single_pass = {
                "pass_number": 1,
                "pass_type": "single",
                "depth": total_depth or 0,
                "stock_to_leave": {
                    "radial": stock_to_leave_radial,
                    "axial": stock_to_leave_axial
                },
                "parameters": {
                    "stepover": stepover,
                    "stepdown": maximum_stepdown,
                    "feedrate": cutting_feedrate
                }
            }
            passes.append(single_pass)
        
        pass_config["passes"] = passes
        pass_config["spring_passes"] = spring_passes_count
        pass_config["finishing_enabled"] = finishing_passes_enabled
        
        return pass_config
        
    except Exception:
        # Return default single pass configuration on any error
        return {
            "pass_type": "single",
            "total_passes": 1,
            "passes": [{
                "pass_number": 1,
                "pass_type": "single",
                "depth": 0,
                "stock_to_leave": {"radial": 0.0, "axial": 0.0},
                "parameters": {"stepover": None, "stepdown": None, "feedrate": None}
            }],
            "spring_passes": 0,
            "finishing_enabled": False
        }


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


# NOTE: _find_tool_by_id has been removed and is now imported from tool_library module.
# The centralized find_tool_by_id function provides the same functionality.


def list_all_tools(cam: adsk.cam.CAM) -> dict:
    """
    List all tools available in the CAM tool libraries.
    
    Args:
        cam: The CAM product instance
        
    Returns:
        dict: A dictionary containing:
            - libraries: List of tool library dictionaries with tools
            - total_count: Total number of tools across all libraries
            - message: Optional message if no tools found
    """
    result = {
        "libraries": [],
        "total_count": 0,
        "message": None
    }
    
    if not cam:
        result["message"] = "No CAM data present in the document"
        return result
    
    try:
        if not hasattr(cam, 'toolLibraries'):
            result["message"] = "No tool libraries available"
            return result
            
        tool_libraries = cam.toolLibraries
        if not tool_libraries or tool_libraries.count == 0:
            result["message"] = "No tool libraries found"
            return result
        
        total_count = 0
        
        for lib_idx in range(tool_libraries.count):
            library = tool_libraries.item(lib_idx)
            
            library_data = {
                "name": library.name if hasattr(library, 'name') else f"Library {lib_idx}",
                "id": library.entityToken if hasattr(library, 'entityToken') else f"lib_{lib_idx}",
                "tools": []
            }
            
            if hasattr(library, 'tools'):
                tools = library.tools
                if tools:
                    for tool_idx in range(tools.count):
                        tool = tools.item(tool_idx)
                        
                        tool_data = {
                            "id": tool.entityToken if hasattr(tool, 'entityToken') else f"tool_{lib_idx}_{tool_idx}",
                            "name": getattr(tool, 'description', None) or getattr(tool, 'name', f'Tool {tool_idx}'),
                            "type": _get_tool_type_string(tool),
                            "number": getattr(tool, 'number', None)
                        }
                        
                        # Add basic geometry if available
                        if hasattr(tool, 'parameters'):
                            params = tool.parameters
                            for param_idx in range(params.count):
                                param = params.item(param_idx)
                                param_name = param.name.lower()
                                if "diameter" in param_name:
                                    tool_data["diameter"] = getattr(param.value, 'value', param.value) if hasattr(param, 'value') else None
                                elif "length" in param_name and "overall" in param_name:
                                    tool_data["overall_length"] = getattr(param.value, 'value', param.value) if hasattr(param, 'value') else None
                        
                        library_data["tools"].append(tool_data)
                        total_count += 1
            
            result["libraries"].append(library_data)
        
        result["total_count"] = total_count
        
        if total_count == 0:
            result["message"] = "No tools found in any library"
        
        return result
        
    except Exception as e:
        return {
            "libraries": [],
            "total_count": 0,
            "message": f"Error accessing tool libraries: {str(e)}"
        }


def _get_tool_type_string(tool) -> str:
    """Extract tool type as string from tool object."""
    try:
        if hasattr(tool, 'type'):
            tool_type_enum = tool.type
            # Map common tool types
            type_map = {
                0: "flat end mill",
                1: "ball end mill", 
                2: "bull nose end mill",
                3: "chamfer mill",
                4: "face mill",
                5: "drill",
                6: "center drill",
                7: "countersink",
                8: "counterbore",
                9: "reamer",
                10: "tap",
                11: "thread mill",
                12: "boring bar",
                13: "probe"
            }
            return type_map.get(tool_type_enum, f"type_{tool_type_enum}")
        return "unknown"
    except Exception:
        return "unknown"
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
        # Use centralized find_tool_by_id from tool_library module
        tool = find_tool_by_id(tool_id)
        
        if not tool:
            return {
                "error": True,
                "message": f"Tool with ID '{tool_id}' not found",
                "code": "TOOL_NOT_FOUND"
            }
        
        # Extract tool type
        tool_type = _get_tool_type_string(tool)

        
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
            "name": tool.description if hasattr(tool, 'description') and tool.description else "Unnamed Tool",
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
                            # Use the same serialization as tool libraries
                            from . import tool_library
                            tool_data = tool_library.serialize_tool(tool)
                            tools_list.append(tool_data)
            
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
                                                "name": tool.description if hasattr(tool, 'description') and tool.description else "Unnamed Tool",
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



def analyze_setup_sequence(cam: adsk.cam.CAM, setup_id: str) -> dict:
    """
    Analyze toolpath execution sequence and dependencies within a setup.
    
    Analyzes toolpath execution sequence and dependencies, identifies tool changes
    and their impact, provides optimization recommendations, and calculates estimated
    machining times for the setup.
    
    Args:
        cam: The CAM product instance (optional, will be validated if None)
        setup_id: The unique identifier of the setup
        
    Returns:
        dict: Sequence analysis including:
            - setup_id: Setup identifier
            - setup_name: Setup name
            - total_toolpaths: Number of toolpaths in setup
            - execution_sequence: List of toolpaths in execution order with metadata
            - tool_changes: List of tool change points with timing impact
            - optimization_recommendations: List of optimization suggestions
            - total_estimated_time: Total estimated machining time
            - error: Error information if setup not found or CAM validation fails
    
    Requirements: 2.1, 2.2, 2.4, 3.4, 5.5
    """
    # Validate CAM product if not provided
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate setup_id parameter
    if not setup_id:
        return {
            "error": True,
            "message": "Setup ID is required",
            "code": "MISSING_SETUP_ID"
        }
    
    try:
        setup = _find_setup_by_id(cam, setup_id)
        
        if not setup:
            return {
                "error": True,
                "message": f"Setup with ID '{setup_id}' not found. Please verify the setup ID exists in the current CAM document",
                "code": "SETUP_NOT_FOUND"
            }
        
        # Initialize result structure
        result = {
            "setup_id": setup_id,
            "setup_name": setup.name,
            "total_toolpaths": 0,
            "execution_sequence": [],
            "tool_changes": [],
            "optimization_recommendations": [],
            "total_estimated_time": "0:00"
        }
        
        # Collect all operations in execution order
        operations = []
        
        # Get direct operations
        if hasattr(setup, 'operations') and setup.operations:
            for op_idx in range(setup.operations.count):
                operation = setup.operations.item(op_idx)
                operations.append((operation, op_idx, None))  # (operation, index, folder_name)
        
        # Get operations from folders
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
        
        # Analyze execution sequence
        total_time_minutes = 0
        previous_tool_id = None
        tool_change_count = 0
        
        for order, (operation, op_idx, folder_name) in enumerate(operations, 1):
            try:
                # Get operation details
                op_id = operation.entityToken if hasattr(operation, 'entityToken') else f"op_{order}"
                op_name = operation.name
                op_type = _get_operation_type(operation)
                
                # Get tool information
                tool_data = _get_tool_data_from_operation(operation)
                tool_id = tool_data.get("id")
                
                # Estimate machining time (simplified calculation)
                estimated_time = _estimate_operation_time(operation)
                total_time_minutes += estimated_time
                
                # Get pass count from operation
                pass_config = _extract_pass_params(operation)
                pass_count = pass_config.get("total_passes", 1)
                
                # Check for dependencies (simplified - based on tool changes and operation types)
                dependencies = []
                if order > 1:
                    # Finishing operations typically depend on roughing operations
                    if "finish" in op_type.lower() or "contour" in op_type.lower():
                        # Find previous roughing operations
                        for prev_order, (prev_op, _, _) in enumerate(operations[:order-1], 1):
                            prev_type = _get_operation_type(prev_op)
                            if "adaptive" in prev_type.lower() or "pocket" in prev_type.lower():
                                prev_id = prev_op.entityToken if hasattr(prev_op, 'entityToken') else f"op_{prev_order}"
                                dependencies.append(prev_id)
                
                # Build sequence entry
                sequence_entry = {
                    "order": order,
                    "toolpath_id": op_id,
                    "toolpath_name": op_name,
                    "operation_type": op_type,
                    "tool_id": tool_id,
                    "tool_name": tool_data.get("name", "Unknown Tool"),
                    "estimated_time": f"{estimated_time//60}:{estimated_time%60:02d}",
                    "dependencies": dependencies,
                    "pass_count": pass_count,
                    "folder": folder_name
                }
                
                result["execution_sequence"].append(sequence_entry)
                
                # Track tool changes
                if previous_tool_id is not None and tool_id != previous_tool_id:
                    tool_change_count += 1
                    change_time = 2  # Assume 2 minutes per tool change
                    total_time_minutes += change_time
                    
                    tool_change = {
                        "after_toolpath": result["execution_sequence"][-2]["toolpath_id"] if len(result["execution_sequence"]) > 1 else None,
                        "from_tool": previous_tool_id,
                        "from_tool_name": result["execution_sequence"][-2]["tool_name"] if len(result["execution_sequence"]) > 1 else "Unknown",
                        "to_tool": tool_id,
                        "to_tool_name": tool_data.get("name", "Unknown Tool"),
                        "change_time": f"{change_time}:00",
                        "order": order
                    }
                    result["tool_changes"].append(tool_change)
                
                previous_tool_id = tool_id
                
            except Exception:
                # Continue processing other operations if one fails
                continue
        
        # Set total estimated time
        result["total_estimated_time"] = f"{total_time_minutes//60}:{total_time_minutes%60:02d}"
        
        # Generate optimization recommendations
        result["optimization_recommendations"] = _generate_optimization_recommendations(
            result["execution_sequence"], 
            result["tool_changes"], 
            tool_change_count
        )
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error analyzing setup sequence for setup '{setup_id}': {str(e)}",
            "code": "ANALYSIS_ERROR"
        }


def _find_setup_by_id(cam: adsk.cam.CAM, setup_id: str) -> Optional[adsk.cam.Setup]:
    """
    Find a setup by its ID.
    
    Args:
        cam: The CAM product instance
        setup_id: The unique identifier of the setup
        
    Returns:
        adsk.cam.Setup | None: The setup if found, None otherwise
    """
    if not cam:
        return None
    
    try:
        setups = cam.setups
        if not setups:
            return None
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            setup_id_check = setup.entityToken if hasattr(setup, 'entityToken') else f"setup_{setup_idx}"
            if setup_id_check == setup_id:
                return setup
        
        return None
        
    except Exception:
        return None


def _estimate_operation_time(operation: adsk.cam.Operation) -> int:
    """
    Estimate machining time for an operation in minutes (simplified calculation).
    
    Args:
        operation: The CAM operation
        
    Returns:
        int: Estimated time in minutes
    """
    try:
        # This is a simplified estimation - in reality, this would require
        # complex calculations based on toolpath geometry, feeds/speeds, etc.
        
        op_type = _get_operation_type(operation).lower()
        
        # Base time estimates by operation type (in minutes)
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
        
        # Find matching operation type
        estimated_time = 5  # Default fallback
        for op_key, time in base_times.items():
            if op_key in op_type:
                estimated_time = time
                break
        
        # Adjust for multiple passes
        pass_config = _extract_pass_params(operation)
        pass_count = pass_config.get("total_passes", 1)
        if pass_count > 1:
            # Multiple passes take longer, but not linearly
            estimated_time = int(estimated_time * (1 + (pass_count - 1) * 0.7))
        
        # Adjust for finishing operations (typically take longer due to precision)
        if "finish" in op_type or pass_config.get("finishing_enabled", False):
            estimated_time = int(estimated_time * 1.3)
        
        return max(1, estimated_time)  # Minimum 1 minute
        
    except Exception:
        return 5  # Default fallback


def _generate_optimization_recommendations(execution_sequence: list, tool_changes: list, tool_change_count: int) -> list:
    """
    Generate optimization recommendations based on sequence analysis.
    
    Args:
        execution_sequence: List of operations in execution order
        tool_changes: List of tool change points
        tool_change_count: Total number of tool changes
        
    Returns:
        list: List of optimization recommendation dictionaries
    """
    recommendations = []
    
    try:
        # Analyze tool change patterns
        if tool_change_count > 3:
            potential_savings = tool_change_count * 2  # 2 minutes per tool change
            recommendations.append({
                "type": "tool_change_reduction",
                "description": f"Consider reordering operations to minimize tool changes. Currently {tool_change_count} tool changes detected.",
                "potential_savings": f"{potential_savings}:00"
            })
        
        # Analyze operation sequencing
        tool_groups = {}
        for op in execution_sequence:
            tool_id = op["tool_id"]
            if tool_id not in tool_groups:
                tool_groups[tool_id] = []
            tool_groups[tool_id].append(op)
        
        # Check for scattered tool usage
        scattered_tools = []
        for tool_id, ops in tool_groups.items():
            if len(ops) > 1:
                # Check if operations with same tool are scattered
                orders = [op["order"] for op in ops]
                if max(orders) - min(orders) > len(ops):
                    scattered_tools.append((tool_id, ops[0]["tool_name"], len(ops)))
        
        if scattered_tools:
            tool_names = [name for _, name, _ in scattered_tools]
            recommendations.append({
                "type": "operation_grouping",
                "description": f"Group operations using the same tool together: {', '.join(tool_names)}",
                "potential_savings": f"{len(scattered_tools) * 2}:00"
            })
        
        # Check for roughing/finishing sequence
        roughing_ops = []
        finishing_ops = []
        
        for op in execution_sequence:
            op_type = op["operation_type"].lower()
            if "adaptive" in op_type or "pocket" in op_type:
                roughing_ops.append(op)
            elif "contour" in op_type or "finish" in op_type or op["pass_count"] > 1:
                finishing_ops.append(op)
        
        # Check if finishing operations come before roughing
        if roughing_ops and finishing_ops:
            min_roughing_order = min(op["order"] for op in roughing_ops)
            min_finishing_order = min(op["order"] for op in finishing_ops)
            
            if min_finishing_order < min_roughing_order:
                recommendations.append({
                    "type": "sequence_optimization",
                    "description": "Consider performing roughing operations before finishing operations for better surface quality",
                    "potential_savings": "Quality improvement"
                })
        
        # Check for excessive pass counts
        high_pass_ops = [op for op in execution_sequence if op["pass_count"] > 3]
        if high_pass_ops:
            recommendations.append({
                "type": "pass_optimization",
                "description": f"Review operations with high pass counts ({len(high_pass_ops)} operations) for potential consolidation",
                "potential_savings": "Efficiency improvement"
            })
        
        # If no specific recommendations, provide general advice
        if not recommendations:
            recommendations.append({
                "type": "general",
                "description": "Sequence appears well-optimized. Consider reviewing feeds and speeds for further improvements.",
                "potential_savings": "N/A"
            })
        
    except Exception:
        recommendations.append({
            "type": "analysis_error",
            "description": "Unable to generate detailed recommendations due to analysis error",
            "potential_savings": "N/A"
        })
    
    return recommendations


def get_toolpath_linking(cam: adsk.cam.CAM, toolpath_id: str) -> dict:
    """
    Get linking parameters organized by sections for a specific toolpath.
    
    Extracts operation-specific linking parameters and organizes them by dialog sections
    as they appear in Fusion 360's interface. Returns linking configuration with 
    editability information and handles different operation types appropriately.
    
    Args:
        cam: The CAM product instance (optional, will be validated if None)
        toolpath_id: The unique identifier of the toolpath
        
    Returns:
        dict: Operation-specific linking configuration including:
            - id: Toolpath identifier
            - name: Toolpath name
            - type: Operation type
            - setup_name: Parent setup name
            - operation_type: Specific operation type for parameter organization
            - sections: Dictionary of dialog sections with their parameters
            - editable_parameters: List of parameter paths that can be modified
            - error: Error information if toolpath not found or CAM validation fails
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    # Validate CAM product if not provided
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate toolpath_id parameter
    if not toolpath_id:
        return {
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found. Please verify the toolpath ID exists in the current CAM document",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Get parent setup name
        setup_name = ""
        try:
            if hasattr(operation, 'parentSetup') and operation.parentSetup:
                setup_name = operation.parentSetup.name
        except Exception:
            setup_name = "Unknown Setup"
        
        # Extract linking parameters using existing helper function
        linking_config = _extract_linking_params(operation)
        
        # Build comprehensive result
        result = {
            "id": toolpath_id,
            "name": operation.name,
            "type": _get_operation_type(operation),
            "setup_name": setup_name,
            "operation_type": linking_config["operation_type"],
            "sections": linking_config["sections"],
            "editable_parameters": linking_config["editable_parameters"]
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error extracting linking parameters for toolpath '{toolpath_id}': {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


def validate_height_value(param_name: str, value: Any, operation: adsk.cam.Operation = None) -> dict:
    """
    Validate a height parameter value against Fusion 360 constraints.
    
    Checks parameter type, range constraints, and Fusion 360 specific limitations.
    
    Args:
        param_name: The name of the height parameter (e.g., 'clearance_height')
        value: The proposed new value
        operation: The CAM operation (optional, for context-specific validation)
        
    Returns:
        dict: Validation result including:
            - valid: Boolean indicating if value is valid
            - message: Description of validation result or error
            - code: Error code for programmatic handling
            - converted_value: The value converted to appropriate type
    
    Requirements: 4.1
    """
    try:
        # Convert string values to numeric if possible
        converted_value = value
        if isinstance(value, str):
            try:
                if '.' in value:
                    converted_value = float(value)
                else:
                    converted_value = int(value)
            except ValueError:
                # Keep as string for expression-based values
                pass
        
        # Basic type validation
        if not isinstance(converted_value, (int, float, str)):
            return {
                "valid": False,
                "message": f"Height parameter '{param_name}' must be a numeric value or expression string",
                "code": "INVALID_TYPE",
                "converted_value": value
            }
        
        # For numeric values, check reasonable ranges
        if isinstance(converted_value, (int, float)):
            # Height values should be reasonable (not extremely large or small)
            if converted_value < -10000 or converted_value > 10000:
                return {
                    "valid": False,
                    "message": f"Height value {converted_value} is outside reasonable range (-10000 to 10000 mm)",
                    "code": "VALUE_OUT_OF_RANGE",
                    "converted_value": converted_value
                }
            
            # Specific validation for different height types
            if param_name in ['clearance_height', 'retract_height'] and converted_value < 0:
                return {
                    "valid": False,
                    "message": f"{param_name.replace('_', ' ').title()} should typically be positive (above stock/model)",
                    "code": "NEGATIVE_SAFETY_HEIGHT",
                    "converted_value": converted_value
                }
        
        # If we have operation context, check against existing parameter constraints
        if operation and hasattr(operation, 'parameters'):
            try:
                # Map parameter names to internal names
                param_name_map = {
                    "clearance_height": "clearanceHeight_value",
                    "retract_height": "retractHeight_value",
                    "feed_height": "feedHeight_value",
                    "top_height": "topHeight_value",
                    "bottom_height": "bottomHeight_value",
                }
                
                internal_name = param_name_map.get(param_name, param_name)
                params = operation.parameters
                param = params.itemByName(internal_name)
                
                if param:
                    # Check min/max constraints if available
                    if hasattr(param, 'minimumValue') and param.minimumValue is not None:
                        if isinstance(converted_value, (int, float)) and converted_value < param.minimumValue:
                            return {
                                "valid": False,
                                "message": f"Value {converted_value} is below minimum allowed value of {param.minimumValue}",
                                "code": "BELOW_MINIMUM",
                                "converted_value": converted_value
                            }
                    
                    if hasattr(param, 'maximumValue') and param.maximumValue is not None:
                        if isinstance(converted_value, (int, float)) and converted_value > param.maximumValue:
                            return {
                                "valid": False,
                                "message": f"Value {converted_value} exceeds maximum allowed value of {param.maximumValue}",
                                "code": "ABOVE_MAXIMUM",
                                "converted_value": converted_value
                            }
            except Exception:
                # If we can't check parameter constraints, continue with basic validation
                pass
        
        return {
            "valid": True,
            "message": f"Height value {converted_value} is valid for parameter '{param_name}'",
            "code": "VALID",
            "converted_value": converted_value
        }
        
    except Exception as e:
        return {
            "valid": False,
            "message": f"Error validating height value: {str(e)}",
            "code": "VALIDATION_ERROR",
            "converted_value": value
        }


def validate_height_hierarchy(height_values: dict, operation: adsk.cam.Operation = None) -> dict:
    """
    Validate height hierarchy rules (clearance > retract > feed).
    
    Enforces logical ordering constraints between different height parameters
    to prevent machining collisions and ensure safe toolpath execution.
    
    Args:
        height_values: Dictionary of height parameter names and values
        operation: The CAM operation (optional, for getting current values)
        
    Returns:
        dict: Validation result including:
            - valid: Boolean indicating if hierarchy is valid
            - message: Description of validation result or violations
            - code: Error code for programmatic handling
            - violations: List of specific hierarchy violations found
    
    Requirements: 4.2, 4.3
    """
    violations = []
    
    try:
        # Get current height values from operation if available
        current_heights = {}
        if operation:
            try:
                current_heights = _extract_heights_params(operation)
                # Convert to simple value dict for comparison
                for key, param_data in current_heights.items():
                    if isinstance(param_data, dict) and 'value' in param_data:
                        current_heights[key] = param_data['value']
            except Exception:
                pass
        
        # Merge current values with proposed changes
        all_heights = current_heights.copy()
        all_heights.update(height_values)
        
        # Extract numeric values for comparison
        clearance = None
        retract = None
        feed = None
        top = None
        bottom = None
        
        for param_name, value in all_heights.items():
            if isinstance(value, (int, float)):
                if param_name == 'clearance_height':
                    clearance = value
                elif param_name == 'retract_height':
                    retract = value
                elif param_name == 'feed_height':
                    feed = value
                elif param_name == 'top_height':
                    top = value
                elif param_name == 'bottom_height':
                    bottom = value
        
        # Check hierarchy rules
        # Rule 1: Clearance height should be above retract height
        if clearance is not None and retract is not None:
            if clearance <= retract:
                violations.append({
                    "rule": "clearance_above_retract",
                    "message": f"Clearance height ({clearance}) must be above retract height ({retract})",
                    "clearance": clearance,
                    "retract": retract
                })
        
        # Rule 2: Retract height should be above feed height
        if retract is not None and feed is not None:
            if retract <= feed:
                violations.append({
                    "rule": "retract_above_feed",
                    "message": f"Retract height ({retract}) must be above feed height ({feed})",
                    "retract": retract,
                    "feed": feed
                })
        
        # Rule 3: Feed height should be above top height (material surface)
        if feed is not None and top is not None:
            if feed < top:
                violations.append({
                    "rule": "feed_above_top",
                    "message": f"Feed height ({feed}) should typically be at or above top height ({top})",
                    "feed": feed,
                    "top": top
                })
        
        # Rule 4: Top height should be above bottom height
        if top is not None and bottom is not None:
            if top <= bottom:
                violations.append({
                    "rule": "top_above_bottom",
                    "message": f"Top height ({top}) must be above bottom height ({bottom})",
                    "top": top,
                    "bottom": bottom
                })
        
        # Rule 5: Check for reasonable spacing between safety heights
        if clearance is not None and retract is not None:
            spacing = clearance - retract
            if spacing < 0.1:  # Less than 0.1mm spacing
                violations.append({
                    "rule": "insufficient_clearance_spacing",
                    "message": f"Insufficient spacing ({spacing:.3f}mm) between clearance and retract heights",
                    "spacing": spacing
                })
        
        if retract is not None and feed is not None:
            spacing = retract - feed
            if spacing < 0.1:  # Less than 0.1mm spacing
                violations.append({
                    "rule": "insufficient_retract_spacing",
                    "message": f"Insufficient spacing ({spacing:.3f}mm) between retract and feed heights",
                    "spacing": spacing
                })
        
        # Determine overall validation result
        if violations:
            return {
                "valid": False,
                "message": f"Height hierarchy validation failed with {len(violations)} violation(s)",
                "code": "HIERARCHY_VIOLATIONS",
                "violations": violations
            }
        else:
            return {
                "valid": True,
                "message": "Height hierarchy is valid",
                "code": "VALID_HIERARCHY",
                "violations": []
            }
        
    except Exception as e:
        return {
            "valid": False,
            "message": f"Error validating height hierarchy: {str(e)}",
            "code": "VALIDATION_ERROR",
            "violations": []
        }


def check_parameter_editability(operation: adsk.cam.Operation, param_name: str) -> dict:
    """
    Check if a height parameter can be modified.
    
    Verifies parameter exists, is accessible, and is not read-only.
    
    Args:
        operation: The CAM operation
        param_name: The name of the parameter to check
        
    Returns:
        dict: Editability check result including:
            - editable: Boolean indicating if parameter can be modified
            - message: Description of editability status
            - code: Status code for programmatic handling
            - parameter_info: Additional parameter information if available
    
    Requirements: 4.5
    """
    try:
        if not operation or not hasattr(operation, 'parameters'):
            return {
                "editable": False,
                "message": "Operation does not support parameter modification",
                "code": "NO_PARAMETERS",
                "parameter_info": None
            }
        
        # Map parameter names to internal names
        param_name_map = {
            "clearance_height": "clearanceHeight_value",
            "retract_height": "retractHeight_value",
            "feed_height": "feedHeight_value",
            "top_height": "topHeight_value",
            "bottom_height": "bottomHeight_value",
        }
        
        internal_name = param_name_map.get(param_name, param_name)
        params = operation.parameters
        
        # Try to find the parameter
        param = None
        try:
            param = params.itemByName(internal_name)
        except Exception:
            pass
        
        if not param:
            return {
                "editable": False,
                "message": f"Parameter '{param_name}' not found in operation",
                "code": "PARAMETER_NOT_FOUND",
                "parameter_info": None
            }
        
        # Check if parameter is read-only
        is_read_only = False
        try:
            if hasattr(param, 'isReadOnly'):
                is_read_only = param.isReadOnly
            elif hasattr(param.value, 'isReadOnly'):
                is_read_only = param.value.isReadOnly
        except Exception:
            # If we can't determine read-only status, assume it's editable
            pass
        
        if is_read_only:
            return {
                "editable": False,
                "message": f"Parameter '{param_name}' is read-only and cannot be modified",
                "code": "READ_ONLY",
                "parameter_info": {
                    "name": param_name,
                    "internal_name": internal_name,
                    "read_only": True
                }
            }
        
        # Get additional parameter information
        param_info = {
            "name": param_name,
            "internal_name": internal_name,
            "read_only": is_read_only
        }
        
        # Try to get current value and constraints
        try:
            if hasattr(param.value, 'value'):
                param_info["current_value"] = param.value.value
            else:
                param_info["current_value"] = param.value
        except Exception:
            pass
        
        try:
            if hasattr(param, 'minimumValue') and param.minimumValue is not None:
                param_info["min_value"] = param.minimumValue
        except Exception:
            pass
        
        try:
            if hasattr(param, 'maximumValue') and param.maximumValue is not None:
                param_info["max_value"] = param.maximumValue
        except Exception:
            pass
        
        return {
            "editable": True,
            "message": f"Parameter '{param_name}' can be modified",
            "code": "EDITABLE",
            "parameter_info": param_info
        }
        
    except Exception as e:
        return {
            "editable": False,
            "message": f"Error checking parameter editability: {str(e)}",
            "code": "CHECK_ERROR",
            "parameter_info": None
        }
def validate_multiple_height_parameters(cam: adsk.cam.CAM = None, toolpath_id: str = None, height_changes: dict = None) -> dict:
    """
    Validate multiple height parameter changes simultaneously.
    
    Checks individual parameter validity and overall height hierarchy constraints
    when multiple height parameters are being modified together.
    
    Args:
        cam: The CAM product instance (optional, will be validated if None)
        toolpath_id: The unique identifier of the toolpath
        height_changes: Dictionary of parameter names and proposed values
        
    Returns:
        dict: Comprehensive validation result including:
            - valid: Boolean indicating if all changes are valid
            - message: Overall validation summary
            - individual_validations: Results for each parameter
            - hierarchy_validation: Height hierarchy check result
            - editability_checks: Editability status for each parameter
    
    Requirements: 4.1, 4.2, 4.3, 4.5
    """
    # Validate CAM product if not provided
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "valid": False,
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate required parameters
    if not toolpath_id:
        return {
            "valid": False,
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
        }
    
    if not height_changes or not isinstance(height_changes, dict):
        return {
            "valid": False,
            "error": True,
            "message": "Height changes dictionary is required",
            "code": "MISSING_HEIGHT_CHANGES"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "valid": False,
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        individual_validations = {}
        editability_checks = {}
        all_valid = True
        
        # Validate each parameter individually
        for param_name, value in height_changes.items():
            # Check editability
            editability_check = check_parameter_editability(operation, param_name)
            editability_checks[param_name] = editability_check
            
            if not editability_check["editable"]:
                individual_validations[param_name] = {
                    "valid": False,
                    "message": editability_check["message"],
                    "code": editability_check["code"]
                }
                all_valid = False
                continue
            
            # Validate value
            value_validation = validate_height_value(param_name, value, operation)
            individual_validations[param_name] = value_validation
            
            if not value_validation["valid"]:
                all_valid = False
        
        # If any individual validation failed, return early
        if not all_valid:
            failed_params = [name for name, result in individual_validations.items() if not result.get("valid", False)]
            return {
                "valid": False,
                "message": f"Validation failed for parameters: {', '.join(failed_params)}",
                "code": "INDIVIDUAL_VALIDATION_FAILED",
                "individual_validations": individual_validations,
                "editability_checks": editability_checks,
                "hierarchy_validation": None
            }
        
        # Validate height hierarchy with all proposed changes
        converted_changes = {}
        for param_name, value in height_changes.items():
            if param_name in individual_validations:
                converted_changes[param_name] = individual_validations[param_name].get("converted_value", value)
        
        hierarchy_validation = validate_height_hierarchy(converted_changes, operation)
        
        if not hierarchy_validation["valid"]:
            return {
                "valid": False,
                "message": f"Height hierarchy validation failed: {hierarchy_validation['message']}",
                "code": "HIERARCHY_VIOLATION",
                "individual_validations": individual_validations,
                "editability_checks": editability_checks,
                "hierarchy_validation": hierarchy_validation
            }
        
        # All validations passed
        return {
            "valid": True,
            "message": f"All {len(height_changes)} height parameter changes are valid",
            "code": "ALL_VALID",
            "individual_validations": individual_validations,
            "editability_checks": editability_checks,
            "hierarchy_validation": hierarchy_validation
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": True,
            "message": f"Error validating height parameters: {str(e)}",
            "code": "VALIDATION_ERROR"
        }


def get_toolpath_passes(cam: adsk.cam.CAM, toolpath_id: str) -> dict:
    """
    Get comprehensive pass information for a toolpath.
    
    Combines pass extraction with toolpath lookup and returns comprehensive
    pass configuration with metadata. Handles missing toolpaths with structured
    errors and includes pass relationships and inheritance information.
    
    Args:
        cam: The CAM product instance
        toolpath_id: The unique identifier of the toolpath
        
    Returns:
        dict: Comprehensive pass configuration including:
            - id: Toolpath identifier
            - name: Toolpath name
            - type: Operation type
            - setup_name: Parent setup name
            - tool: Tool reference information
            - pass_configuration: Complete pass data from _extract_pass_params
            - pass_relationships: Information about pass inheritance and dependencies
            - error: Error information if toolpath not found or CAM validation fails
    
    Requirements: 1.1, 1.2, 1.4, 1.5, 3.1, 3.2, 3.3
    """
    # Validate CAM product
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate toolpath_id parameter
    if not toolpath_id:
        return {
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found. Please verify the toolpath ID exists in the current CAM document",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Get parent setup name
        setup_name = ""
        try:
            if hasattr(operation, 'parentSetup') and operation.parentSetup:
                setup_name = operation.parentSetup.name
        except Exception:
            setup_name = "Unknown Setup"
        
        # Extract tool information
        tool_data = _get_tool_data_from_operation(operation)
        
        # Extract pass configuration
        pass_configuration = _extract_pass_params(operation)
        
        # Analyze pass relationships and inheritance
        pass_relationships = _analyze_pass_relationships(operation, pass_configuration)
        
        # Build comprehensive result
        result = {
            "id": toolpath_id,
            "name": operation.name,
            "type": _get_operation_type(operation),
            "setup_name": setup_name,
            "tool": tool_data,
            "pass_configuration": pass_configuration,
            "pass_relationships": pass_relationships
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error extracting toolpath passes for '{toolpath_id}': {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


def _analyze_pass_relationships(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Analyze pass relationships and inheritance information.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration from _extract_pass_params
        
    Returns:
        dict: Pass relationships including inheritance and dependencies
    """
    relationships = {
        "inheritance_chain": [],
        "parameter_inheritance": {},
        "dependencies": [],
        "optimization_opportunities": []
    }
    
    try:
        passes = pass_config.get("passes", [])
        
        if len(passes) <= 1:
            # Single pass - no relationships to analyze
            return relationships
        
        # Build inheritance chain
        for i, pass_data in enumerate(passes):
            pass_info = {
                "pass_number": pass_data.get("pass_number", i + 1),
                "pass_type": pass_data.get("pass_type", "unknown"),
                "inherits_from": None,
                "inherited_parameters": []
            }
            
            # Check if this pass inherits parameters from previous passes
            if i > 0:
                previous_pass = passes[i - 1]
                inherited_params = []
                
                # Check for parameter inheritance
                current_params = pass_data.get("parameters", {})
                previous_params = previous_pass.get("parameters", {})
                
                for param_name, param_value in current_params.items():
                    if param_name in previous_params:
                        if param_value == previous_params[param_name] or param_value is None:
                            inherited_params.append(param_name)
                
                if inherited_params:
                    pass_info["inherits_from"] = previous_pass.get("pass_number", i)
                    pass_info["inherited_parameters"] = inherited_params
            
            relationships["inheritance_chain"].append(pass_info)
        
        # Analyze parameter inheritance patterns
        param_inheritance = {}
        for pass_info in relationships["inheritance_chain"]:
            for param in pass_info.get("inherited_parameters", []):
                if param not in param_inheritance:
                    param_inheritance[param] = []
                param_inheritance[param].append({
                    "pass_number": pass_info["pass_number"],
                    "inherits_from": pass_info["inherits_from"]
                })
        
        relationships["parameter_inheritance"] = param_inheritance
        
        # Identify dependencies
        dependencies = []
        for i, pass_data in enumerate(passes):
            pass_type = pass_data.get("pass_type", "unknown")
            
            if pass_type == "finishing":
                # Finishing passes depend on roughing passes
                roughing_passes = [p for p in passes if p.get("pass_type") == "roughing"]
                for roughing_pass in roughing_passes:
                    dependencies.append({
                        "dependent_pass": pass_data.get("pass_number", i + 1),
                        "depends_on": roughing_pass.get("pass_number", 1),
                        "dependency_type": "material_removal",
                        "description": "Finishing pass requires roughing pass to remove bulk material"
                    })
            
            elif pass_type == "semi_finishing":
                # Semi-finishing depends on roughing
                roughing_passes = [p for p in passes if p.get("pass_type") == "roughing"]
                for roughing_pass in roughing_passes:
                    dependencies.append({
                        "dependent_pass": pass_data.get("pass_number", i + 1),
                        "depends_on": roughing_pass.get("pass_number", 1),
                        "dependency_type": "material_removal",
                        "description": "Semi-finishing pass requires roughing pass to remove bulk material"
                    })
        
        relationships["dependencies"] = dependencies
        
        # Identify optimization opportunities
        optimization_opportunities = []
        
        # Check for redundant parameters
        if len(passes) > 1:
            common_params = set(passes[0].get("parameters", {}).keys())
            for pass_data in passes[1:]:
                common_params &= set(pass_data.get("parameters", {}).keys())
            
            if common_params:
                optimization_opportunities.append({
                    "type": "parameter_consolidation",
                    "description": f"Parameters {list(common_params)} are common across passes and could be consolidated",
                    "affected_parameters": list(common_params)
                })
        
        # Check for inefficient stock-to-leave progression
        stock_progression = []
        for pass_data in passes:
            stock = pass_data.get("stock_to_leave", {})
            radial_stock = stock.get("radial", 0)
            axial_stock = stock.get("axial", 0)
            stock_progression.append((radial_stock, axial_stock))
        
        # Check if stock-to-leave decreases properly
        for i in range(1, len(stock_progression)):
            prev_radial, prev_axial = stock_progression[i - 1]
            curr_radial, curr_axial = stock_progression[i]
            
            if curr_radial > prev_radial or curr_axial > prev_axial:
                optimization_opportunities.append({
                    "type": "stock_progression_issue",
                    "description": f"Pass {i + 1} has more stock-to-leave than pass {i}, which may be inefficient",
                    "affected_passes": [i, i + 1]
                })
        
        relationships["optimization_opportunities"] = optimization_opportunities
        
    except Exception:
        # Return basic relationships structure on error
        pass
    
    return relationships


def set_toolpath_parameter(cam: adsk.cam.CAM = None, toolpath_id: str = None, param_name: str = None, value: Any = None) -> dict:
    """
    Modify a parameter value for a specific toolpath operation.
    
    Validates parameter type, range, and height hierarchy before modification.
    Returns error for read-only or invalid parameters.
    
    Args:
        cam: The CAM product instance (optional, will be validated if None)
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
            - validation_details: Details about validation checks performed
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Validate CAM product if not provided
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate required parameters
    if not toolpath_id:
        return {
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
        }
    
    if not param_name:
        return {
            "error": True,
            "message": "Parameter name is required",
            "code": "MISSING_PARAMETER_NAME"
        }
    
    if value is None:
        return {
            "error": True,
            "message": "Parameter value is required",
            "code": "MISSING_VALUE"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Check parameter editability
        editability_check = check_parameter_editability(operation, param_name)
        if not editability_check["editable"]:
            return {
                "error": True,
                "message": editability_check["message"],
                "code": editability_check["code"],
                "validation_details": {
                    "editability_check": editability_check
                }
            }
        
        # Validate the proposed value
        value_validation = validate_height_value(param_name, value, operation)
        if not value_validation["valid"]:
            return {
                "error": True,
                "message": value_validation["message"],
                "code": value_validation["code"],
                "validation_details": {
                    "value_validation": value_validation,
                    "editability_check": editability_check
                }
            }
        
        # For height parameters, validate hierarchy
        hierarchy_validation = None
        if param_name in ['clearance_height', 'retract_height', 'feed_height', 'top_height', 'bottom_height']:
            # Create a dict with the proposed change to check hierarchy
            proposed_changes = {param_name: value_validation["converted_value"]}
            hierarchy_validation = validate_height_hierarchy(proposed_changes, operation)
            
            if not hierarchy_validation["valid"]:
                return {
                    "error": True,
                    "message": f"Height hierarchy validation failed: {hierarchy_validation['message']}",
                    "code": "HIERARCHY_VIOLATION",
                    "validation_details": {
                        "value_validation": value_validation,
                        "hierarchy_validation": hierarchy_validation,
                        "editability_check": editability_check
                    }
                }
        
        # All validations passed, proceed with modification
        params = operation.parameters
        
        # Map parameter names to internal names
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
        
        internal_name = param_name_map.get(param_name, param_name)
        param = params.itemByName(internal_name)
        
        # Get the current value for reporting
        previous_value = None
        try:
            if hasattr(param.value, 'value'):
                previous_value = param.value.value
            else:
                previous_value = param.value
        except Exception:
            pass
        
        # Set the new value
        converted_value = value_validation["converted_value"]
        try:
            if hasattr(param, 'expression'):
                # For expression-based parameters
                param.expression = str(converted_value)
            elif hasattr(param.value, 'value'):
                # For value objects
                param.value.value = converted_value
            else:
                # Direct value assignment
                param.value = converted_value
            
            # Get the new value for confirmation
            new_value = None
            try:
                if hasattr(param.value, 'value'):
                    new_value = param.value.value
                else:
                    new_value = param.value
            except Exception:
                new_value = converted_value
            
            return {
                "success": True,
                "message": f"Parameter '{param_name}' updated successfully from {previous_value} to {new_value}",
                "previous_value": previous_value,
                "new_value": new_value,
                "validation_details": {
                    "value_validation": value_validation,
                    "hierarchy_validation": hierarchy_validation,
                    "editability_check": editability_check
                }
            }
            
        except Exception as e:
            return {
                "error": True,
                "message": f"Failed to set parameter value: {str(e)}",
                "code": "SET_VALUE_ERROR",
                "validation_details": {
                    "value_validation": value_validation,
                    "hierarchy_validation": hierarchy_validation,
                    "editability_check": editability_check
                }
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error modifying parameter: {str(e)}",
            "code": "MODIFICATION_ERROR"
        }


def validate_pass_modification(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Validate pass parameter changes against constraints.
    
    Ensures logical pass sequence ordering (rough before finish), checks tool 
    compatibility with pass parameters, and handles dependent parameter updates 
    automatically.
    
    Args:
        operation: The CAM operation
        pass_config: Dictionary containing pass configuration changes
        
    Returns:
        dict: Validation result including:
            - valid: Boolean indicating if modification is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
            - dependent_updates: List of parameters that need automatic updates
            - tool_compatibility: Tool compatibility analysis
    
    Requirements: 4.1, 4.2, 4.3, 3.5
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "dependent_updates": [],
        "tool_compatibility": {"compatible": True, "issues": []}
    }
    
    try:
        if not operation or not pass_config:
            validation_result["valid"] = False
            validation_result["errors"].append("Operation and pass configuration are required")
            return validation_result
        
        # Extract current pass configuration
        current_passes = _extract_pass_params(operation)
        
        # Validate pass sequence ordering
        sequence_validation = _validate_pass_sequence_ordering(pass_config, current_passes)
        if not sequence_validation["valid"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(sequence_validation["errors"])
        
        # Validate tool compatibility
        tool_validation = _validate_tool_compatibility(operation, pass_config)
        validation_result["tool_compatibility"] = tool_validation
        if not tool_validation["compatible"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(tool_validation["issues"])
        
        # Check for dependent parameter updates
        dependent_updates = _identify_dependent_parameter_updates(pass_config, current_passes)
        validation_result["dependent_updates"] = dependent_updates
        
        # Validate parameter constraints
        constraint_validation = _validate_pass_parameter_constraints(operation, pass_config)
        if not constraint_validation["valid"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(constraint_validation["errors"])
        validation_result["warnings"].extend(constraint_validation.get("warnings", []))
        
        return validation_result
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "dependent_updates": [],
            "tool_compatibility": {"compatible": False, "issues": [f"Validation failed: {str(e)}"]}
        }


def _validate_pass_sequence_ordering(pass_config: dict, current_passes: dict) -> dict:
    """
    Ensure logical pass sequence ordering (rough before finish).
    
    Args:
        pass_config: New pass configuration
        current_passes: Current pass configuration
        
    Returns:
        dict: Validation result with valid flag and errors list
    """
    validation = {"valid": True, "errors": []}
    
    try:
        # Get passes from new configuration or current configuration
        new_passes = pass_config.get("passes", current_passes.get("passes", []))
        
        if not new_passes:
            return validation
        
        # Check pass type ordering
        pass_types = [pass_data.get("pass_type", "unknown") for pass_data in new_passes]
        
        # Define valid ordering rules
        valid_sequences = [
            ["roughing", "finishing"],
            ["roughing", "semi_finishing", "finishing"],
            ["single"],
            ["roughing"],
            ["finishing"]
        ]
        
        # Check if the sequence matches any valid pattern
        sequence_valid = False
        for valid_seq in valid_sequences:
            if len(pass_types) == len(valid_seq) and all(pt == vs for pt, vs in zip(pass_types, valid_seq)):
                sequence_valid = True
                break
        
        if not sequence_valid:
            validation["valid"] = False
            validation["errors"].append(f"Invalid pass sequence: {pass_types}. Valid sequences are: {valid_sequences}")
        
        # Check stock-to-leave progression (should decrease from rough to finish)
        for i in range(len(new_passes) - 1):
            current_pass = new_passes[i]
            next_pass = new_passes[i + 1]
            
            current_radial = current_pass.get("stock_to_leave", {}).get("radial", 0)
            next_radial = next_pass.get("stock_to_leave", {}).get("radial", 0)
            
            if current_radial < next_radial:
                validation["errors"].append(
                    f"Pass {i+1} has less radial stock-to-leave ({current_radial}) than pass {i+2} ({next_radial}). "
                    "Stock-to-leave should decrease from roughing to finishing passes."
                )
                validation["valid"] = False
        
        return validation
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Pass sequence validation error: {str(e)}"]
        }


def _validate_tool_compatibility(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Check tool compatibility with pass parameters.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration to validate
        
    Returns:
        dict: Tool compatibility analysis with compatible flag and issues list
    """
    compatibility = {"compatible": True, "issues": []}
    
    try:
        tool = operation.tool if hasattr(operation, 'tool') else None
        if not tool:
            compatibility["compatible"] = False
            compatibility["issues"].append("No tool assigned to operation")
            return compatibility
        
        # Get tool properties
        tool_diameter = getattr(tool, 'diameter', None)
        tool_length = getattr(tool, 'bodyLength', None)
        
        # Check passes for tool compatibility
        passes = pass_config.get("passes", [])
        for i, pass_data in enumerate(passes):
            pass_params = pass_data.get("parameters", {})
            
            # Check stepover vs tool diameter
            stepover = pass_params.get("stepover")
            if stepover and tool_diameter:
                if isinstance(stepover, (int, float)):
                    stepover_mm = stepover * tool_diameter / 100  # Convert percentage to mm
                elif stepover > tool_diameter * 2:  # Assume mm if > 200% of diameter
                    stepover_mm = stepover
                else:
                    stepover_mm = stepover
                
                if stepover_mm > tool_diameter * 1.5:
                    compatibility["issues"].append(
                        f"Pass {i+1}: Stepover ({stepover_mm:.2f}mm) is too large for tool diameter ({tool_diameter:.2f}mm)"
                    )
            
            # Check stepdown vs tool length
            stepdown = pass_data.get("depth") or pass_params.get("stepdown")
            if stepdown and tool_length:
                if stepdown > tool_length:
                    compatibility["issues"].append(
                        f"Pass {i+1}: Stepdown ({stepdown:.2f}mm) exceeds tool length ({tool_length:.2f}mm)"
                    )
            
            # Check feedrate vs tool capabilities
            feedrate = pass_params.get("feedrate")
            if feedrate and hasattr(tool, 'feedPerTooth'):
                # Basic feedrate sanity check
                if feedrate > 10000:  # Very high feedrate
                    compatibility["issues"].append(
                        f"Pass {i+1}: Feedrate ({feedrate} mm/min) may be too high for this tool"
                    )
        
        if compatibility["issues"]:
            compatibility["compatible"] = False
        
        return compatibility
        
    except Exception as e:
        return {
            "compatible": False,
            "issues": [f"Tool compatibility check error: {str(e)}"]
        }


def _identify_dependent_parameter_updates(pass_config: dict, current_passes: dict) -> list:
    """
    Handle dependent parameter updates automatically.
    
    Args:
        pass_config: New pass configuration
        current_passes: Current pass configuration
        
    Returns:
        list: List of dependent parameter updates needed
    """
    dependent_updates = []
    
    try:
        new_passes = pass_config.get("passes", [])
        current_pass_list = current_passes.get("passes", [])
        
        # Check if number of passes changed
        if len(new_passes) != len(current_pass_list):
            dependent_updates.append({
                "parameter": "total_passes",
                "old_value": len(current_pass_list),
                "new_value": len(new_passes),
                "reason": "Pass count changed"
            })
        
        # Check if finishing passes were added/removed
        new_has_finishing = any(p.get("pass_type") == "finishing" for p in new_passes)
        current_has_finishing = any(p.get("pass_type") == "finishing" for p in current_pass_list)
        
        if new_has_finishing != current_has_finishing:
            dependent_updates.append({
                "parameter": "finishing_enabled",
                "old_value": current_has_finishing,
                "new_value": new_has_finishing,
                "reason": "Finishing pass configuration changed"
            })
        
        # Check for stock-to-leave adjustments needed
        for i, new_pass in enumerate(new_passes):
            if i < len(current_pass_list):
                current_pass = current_pass_list[i]
                new_stock = new_pass.get("stock_to_leave", {})
                current_stock = current_pass.get("stock_to_leave", {})
                
                if new_stock != current_stock:
                    dependent_updates.append({
                        "parameter": f"pass_{i+1}_stock_to_leave",
                        "old_value": current_stock,
                        "new_value": new_stock,
                        "reason": f"Stock-to-leave changed for pass {i+1}"
                    })
        
        return dependent_updates
        
    except Exception:
        return []


def _validate_pass_parameter_constraints(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Validate parameter constraints within passes.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration to validate
        
    Returns:
        dict: Validation result with valid flag, errors, and warnings
    """
    validation = {"valid": True, "errors": [], "warnings": []}
    
    try:
        passes = pass_config.get("passes", [])
        
        for i, pass_data in enumerate(passes):
            pass_params = pass_data.get("parameters", {})
            stock_to_leave = pass_data.get("stock_to_leave", {})
            
            # Validate stepover range
            stepover = pass_params.get("stepover")
            if stepover is not None:
                if stepover <= 0:
                    validation["errors"].append(f"Pass {i+1}: Stepover must be positive")
                    validation["valid"] = False
                elif stepover > 100:
                    validation["warnings"].append(f"Pass {i+1}: Stepover ({stepover}%) is very high")
            
            # Validate stepdown
            stepdown = pass_params.get("stepdown")
            if stepdown is not None:
                if stepdown <= 0:
                    validation["errors"].append(f"Pass {i+1}: Stepdown must be positive")
                    validation["valid"] = False
                elif stepdown > 50:
                    validation["warnings"].append(f"Pass {i+1}: Stepdown ({stepdown}mm) is very large")
            
            # Validate feedrate
            feedrate = pass_params.get("feedrate")
            if feedrate is not None:
                if feedrate <= 0:
                    validation["errors"].append(f"Pass {i+1}: Feedrate must be positive")
                    validation["valid"] = False
                elif feedrate > 15000:
                    validation["warnings"].append(f"Pass {i+1}: Feedrate ({feedrate} mm/min) is very high")
            
            # Validate stock-to-leave values
            radial_stock = stock_to_leave.get("radial", 0)
            axial_stock = stock_to_leave.get("axial", 0)
            
            if radial_stock < 0:
                validation["errors"].append(f"Pass {i+1}: Radial stock-to-leave cannot be negative")
                validation["valid"] = False
            elif radial_stock > 10:
                validation["warnings"].append(f"Pass {i+1}: Radial stock-to-leave ({radial_stock}mm) is very large")
            
            if axial_stock < 0:
                validation["errors"].append(f"Pass {i+1}: Axial stock-to-leave cannot be negative")
                validation["valid"] = False
            elif axial_stock > 10:
                validation["warnings"].append(f"Pass {i+1}: Axial stock-to-leave ({axial_stock}mm) is very large")
        
        return validation
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Parameter constraint validation error: {str(e)}"],
            "warnings": []
        }


def modify_toolpath_passes(cam: adsk.cam.CAM, toolpath_id: str, pass_config: dict) -> dict:
    """
    Modify pass configuration for a toolpath operation.
    
    Validates modifications before applying changes, returns modification results 
    with previous/new values, and handles validation errors with structured responses.
    
    Args:
        cam: The CAM product instance
        toolpath_id: The unique identifier of the toolpath
        pass_config: New pass configuration to apply
        
    Returns:
        dict: Modification result including:
            - success: Boolean indicating if modification succeeded
            - message: Success or error message
            - previous_config: Previous pass configuration
            - new_config: New pass configuration after modification
            - validation_result: Detailed validation information
            - applied_changes: List of changes that were applied
            - error: Error information if modification failed
    
    Requirements: 4.1, 4.2, 4.3, 4.5
    """
    # Validate CAM product
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "success": False,
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate toolpath_id parameter
    if not toolpath_id:
        return {
            "success": False,
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
        }
    
    if not pass_config:
        return {
            "success": False,
            "error": True,
            "message": "Pass configuration is required",
            "code": "MISSING_PASS_CONFIG"
        }
    
    try:
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "success": False,
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Get current pass configuration
        previous_config = _extract_pass_params(operation)
        
        # Validate the modification
        validation_result = validate_pass_modification(operation, pass_config)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": True,
                "message": "Pass configuration validation failed",
                "code": "VALIDATION_FAILED",
                "validation_result": validation_result,
                "previous_config": previous_config
            }
        
        # Apply the changes
        applied_changes = []
        
        try:
            # Apply pass modifications to operation parameters
            if hasattr(operation, 'parameters'):
                params = operation.parameters
                
                # Apply dependent updates first
                for update in validation_result["dependent_updates"]:
                    try:
                        param_name = update["parameter"]
                        new_value = update["new_value"]
                        
                        # Map logical parameter names to Fusion parameter names
                        param_mapping = {
                            "total_passes": "multipleDepths",
                            "finishing_enabled": "useFinishingPasses"
                        }
                        
                        fusion_param_name = param_mapping.get(param_name, param_name)
                        param = params.itemByName(fusion_param_name)
                        
                        if param:
                            if hasattr(param, 'value'):
                                param.value = new_value
                            applied_changes.append({
                                "parameter": param_name,
                                "previous_value": update["old_value"],
                                "new_value": new_value,
                                "type": "dependent_update"
                            })
                    except Exception:
                        # Log but don't fail for dependent updates
                        pass
                
                # Apply pass-specific changes
                passes = pass_config.get("passes", [])
                for i, pass_data in enumerate(passes):
                    pass_params = pass_data.get("parameters", {})
                    
                    # Apply stepover changes
                    if "stepover" in pass_params:
                        try:
                            stepover_param = params.itemByName("stepover")
                            if stepover_param:
                                old_value = stepover_param.value.value if hasattr(stepover_param.value, 'value') else stepover_param.value
                                stepover_param.value.value = pass_params["stepover"]
                                applied_changes.append({
                                    "parameter": f"pass_{i+1}_stepover",
                                    "previous_value": old_value,
                                    "new_value": pass_params["stepover"],
                                    "type": "pass_parameter"
                                })
                        except Exception:
                            pass
                    
                    # Apply stepdown changes
                    if "stepdown" in pass_params:
                        try:
                            stepdown_param = params.itemByName("stepdown")
                            if stepdown_param:
                                old_value = stepdown_param.value.value if hasattr(stepdown_param.value, 'value') else stepdown_param.value
                                stepdown_param.value.value = pass_params["stepdown"]
                                applied_changes.append({
                                    "parameter": f"pass_{i+1}_stepdown",
                                    "previous_value": old_value,
                                    "new_value": pass_params["stepdown"],
                                    "type": "pass_parameter"
                                })
                        except Exception:
                            pass
                    
                    # Apply feedrate changes
                    if "feedrate" in pass_params:
                        try:
                            feedrate_param = params.itemByName("tool_feedCutting")
                            if feedrate_param:
                                old_value = feedrate_param.value.value if hasattr(feedrate_param.value, 'value') else feedrate_param.value
                                feedrate_param.value.value = pass_params["feedrate"]
                                applied_changes.append({
                                    "parameter": f"pass_{i+1}_feedrate",
                                    "previous_value": old_value,
                                    "new_value": pass_params["feedrate"],
                                    "type": "pass_parameter"
                                })
                        except Exception:
                            pass
                
                # Apply stock-to-leave changes
                for i, pass_data in enumerate(passes):
                    stock_to_leave = pass_data.get("stock_to_leave", {})
                    
                    if "radial" in stock_to_leave:
                        try:
                            radial_param = params.itemByName("radialStockToLeave")
                            if radial_param:
                                old_value = radial_param.value.value if hasattr(radial_param.value, 'value') else radial_param.value
                                radial_param.value.value = stock_to_leave["radial"]
                                applied_changes.append({
                                    "parameter": f"pass_{i+1}_radial_stock",
                                    "previous_value": old_value,
                                    "new_value": stock_to_leave["radial"],
                                    "type": "stock_to_leave"
                                })
                        except Exception:
                            pass
                    
                    if "axial" in stock_to_leave:
                        try:
                            axial_param = params.itemByName("axialStockToLeave")
                            if axial_param:
                                old_value = axial_param.value.value if hasattr(axial_param.value, 'value') else axial_param.value
                                axial_param.value.value = stock_to_leave["axial"]
                                applied_changes.append({
                                    "parameter": f"pass_{i+1}_axial_stock",
                                    "previous_value": old_value,
                                    "new_value": stock_to_leave["axial"],
                                    "type": "stock_to_leave"
                                })
                        except Exception:
                            pass
            
            # Get new configuration after changes
            new_config = _extract_pass_params(operation)
            
            return {
                "success": True,
                "message": f"Pass configuration modified successfully for toolpath '{toolpath_id}'",
                "previous_config": previous_config,
                "new_config": new_config,
                "validation_result": validation_result,
                "applied_changes": applied_changes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": True,
                "message": f"Failed to apply pass configuration changes: {str(e)}",
                "code": "APPLICATION_ERROR",
                "validation_result": validation_result,
                "previous_config": previous_config
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": True,
            "message": f"Error modifying toolpath passes: {str(e)}",
            "code": "MODIFICATION_ERROR"
        }


def validate_linking_modification(operation: adsk.cam.Operation, linking_config: dict) -> dict:
    """
    Validate linking parameter changes against operation constraints.
    
    Checks parameter compatibility with operation type, ensures linking integrity 
    is maintained, and handles operation-specific validation rules.
    
    Args:
        operation: The CAM operation
        linking_config: Dictionary containing linking configuration changes
        
    Returns:
        dict: Validation result including:
            - valid: Boolean indicating if modification is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
            - operation_constraints: Operation-specific constraint analysis
            - parameter_compatibility: Parameter compatibility analysis
    
    Requirements: 7.4, 4.4, 4.5
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "operation_constraints": {"compatible": True, "issues": []},
        "parameter_compatibility": {"compatible": True, "issues": []}
    }
    
    try:
        if not operation or not linking_config:
            validation_result["valid"] = False
            validation_result["errors"].append("Operation and linking configuration are required")
            return validation_result
        
        # Get operation type for validation
        operation_type = _get_operation_type(operation).lower()
        
        # Extract current linking configuration
        current_linking = _extract_linking_params(operation)
        
        # Validate operation-specific constraints
        constraint_validation = _validate_operation_specific_constraints(operation_type, linking_config, current_linking)
        validation_result["operation_constraints"] = constraint_validation
        if not constraint_validation["compatible"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(constraint_validation["issues"])
        
        # Validate parameter compatibility
        compatibility_validation = _validate_linking_parameter_compatibility(operation, linking_config)
        validation_result["parameter_compatibility"] = compatibility_validation
        if not compatibility_validation["compatible"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(compatibility_validation["issues"])
        
        # Validate linking integrity
        integrity_validation = _validate_linking_integrity(linking_config, current_linking)
        if not integrity_validation["valid"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(integrity_validation["errors"])
        validation_result["warnings"].extend(integrity_validation.get("warnings", []))
        
        # Validate parameter values against constraints
        value_validation = _validate_linking_parameter_values(operation, linking_config)
        if not value_validation["valid"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(value_validation["errors"])
        validation_result["warnings"].extend(value_validation.get("warnings", []))
        
        return validation_result
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "operation_constraints": {"compatible": False, "issues": [f"Validation failed: {str(e)}"]},
            "parameter_compatibility": {"compatible": False, "issues": [f"Validation failed: {str(e)}"]}
        }


def _validate_operation_specific_constraints(operation_type: str, linking_config: dict, current_linking: dict) -> dict:
    """
    Validate linking parameter changes against operation-specific constraints.
    
    Args:
        operation_type: Type of operation (2d_pocket, trace, 3d_adaptive, etc.)
        linking_config: New linking configuration
        current_linking: Current linking configuration
        
    Returns:
        dict: Constraint validation result with compatible flag and issues list
    """
    validation = {"compatible": True, "issues": []}
    
    try:
        sections = linking_config.get("sections", {})
        
        # Validate 2D operation constraints
        if "pocket" in operation_type or "2d" in operation_type:
            validation = _validate_2d_operation_constraints(sections, validation)
        
        # Validate Trace operation constraints
        elif "trace" in operation_type or "contour" in operation_type:
            validation = _validate_trace_operation_constraints(sections, validation)
        
        # Validate 3D operation constraints
        elif "3d" in operation_type or "adaptive" in operation_type or "parallel" in operation_type:
            validation = _validate_3d_operation_constraints(sections, validation)
        
        # Validate Drill operation constraints
        elif "drill" in operation_type:
            validation = _validate_drill_operation_constraints(sections, validation)
        
        return validation
        
    except Exception as e:
        return {"compatible": False, "issues": [f"Constraint validation error: {str(e)}"]}


def _validate_2d_operation_constraints(sections: dict, validation: dict) -> dict:
    """Validate constraints specific to 2D operations (Pocket, etc.)."""
    try:
        # Validate leads & transitions section
        leads_transitions = sections.get("leads_and_transitions", {})
        
        if leads_transitions:
            # Validate lead-in parameters
            lead_in = leads_transitions.get("lead_in", {})
            if lead_in:
                # Arc radius must be positive
                arc_radius = lead_in.get("arc_radius")
                if arc_radius is not None and arc_radius <= 0:
                    validation["compatible"] = False
                    validation["issues"].append("Lead-in arc radius must be positive")
                
                # Arc sweep must be between 0 and 360 degrees
                arc_sweep = lead_in.get("arc_sweep")
                if arc_sweep is not None and (arc_sweep < 0 or arc_sweep > 360):
                    validation["compatible"] = False
                    validation["issues"].append("Lead-in arc sweep must be between 0 and 360 degrees")
            
            # Validate lead-out parameters
            lead_out = leads_transitions.get("lead_out", {})
            if lead_out:
                # Arc radius must be positive
                arc_radius = lead_out.get("arc_radius")
                if arc_radius is not None and arc_radius <= 0:
                    validation["compatible"] = False
                    validation["issues"].append("Lead-out arc radius must be positive")
                
                # Arc sweep must be between 0 and 360 degrees
                arc_sweep = lead_out.get("arc_sweep")
                if arc_sweep is not None and (arc_sweep < 0 or arc_sweep > 360):
                    validation["compatible"] = False
                    validation["issues"].append("Lead-out arc sweep must be between 0 and 360 degrees")
            
            # Validate transitions parameters
            transitions = leads_transitions.get("transitions", {})
            if transitions:
                # Lift height must be positive
                lift_height = transitions.get("lift_height")
                if lift_height is not None and lift_height < 0:
                    validation["compatible"] = False
                    validation["issues"].append("Transition lift height must be non-negative")
        
        # Validate entry positioning section
        entry_positioning = sections.get("entry_positioning", {})
        if entry_positioning:
            # Heights must be in logical order: clearance > feed > top
            clearance_height = entry_positioning.get("clearance_height")
            feed_height = entry_positioning.get("feed_height")
            top_height = entry_positioning.get("top_height")
            
            if clearance_height is not None and feed_height is not None:
                if clearance_height <= feed_height:
                    validation["compatible"] = False
                    validation["issues"].append("Clearance height must be greater than feed height")
            
            if feed_height is not None and top_height is not None:
                if feed_height <= top_height:
                    validation["compatible"] = False
                    validation["issues"].append("Feed height must be greater than top height")
        
    except Exception:
        pass
    
    return validation


def _validate_trace_operation_constraints(sections: dict, validation: dict) -> dict:
    """Validate constraints specific to Trace operations."""
    try:
        # Validate contact point section
        contact_point = sections.get("contact_point", {})
        if contact_point:
            # Contact distance must be positive
            distance = contact_point.get("distance")
            if distance is not None and distance <= 0:
                validation["compatible"] = False
                validation["issues"].append("Contact point distance must be positive")
        
        # Validate approach/retract section
        approach_retract = sections.get("approach_retract", {})
        if approach_retract:
            # Approach distance must be positive
            approach_distance = approach_retract.get("approach_distance")
            if approach_distance is not None and approach_distance <= 0:
                validation["compatible"] = False
                validation["issues"].append("Approach distance must be positive")
            
            # Retract distance must be positive
            retract_distance = approach_retract.get("retract_distance")
            if retract_distance is not None and retract_distance <= 0:
                validation["compatible"] = False
                validation["issues"].append("Retract distance must be positive")
        
    except Exception:
        pass
    
    return validation


def _validate_3d_operation_constraints(sections: dict, validation: dict) -> dict:
    """Validate constraints specific to 3D operations."""
    try:
        # Validate linking section
        linking_section = sections.get("linking", {})
        if linking_section:
            # Validate approach parameters
            approach = linking_section.get("approach", {})
            if approach:
                # Approach distance must be positive
                distance = approach.get("distance")
                if distance is not None and distance <= 0:
                    validation["compatible"] = False
                    validation["issues"].append("Approach distance must be positive")
                
                # Approach angle must be between -90 and 90 degrees
                angle = approach.get("angle")
                if angle is not None and (angle < -90 or angle > 90):
                    validation["compatible"] = False
                    validation["issues"].append("Approach angle must be between -90 and 90 degrees")
            
            # Validate retract parameters
            retract = linking_section.get("retract", {})
            if retract:
                # Retract distance must be positive
                distance = retract.get("distance")
                if distance is not None and distance <= 0:
                    validation["compatible"] = False
                    validation["issues"].append("Retract distance must be positive")
                
                # Retract angle must be between -90 and 90 degrees
                angle = retract.get("angle")
                if angle is not None and (angle < -90 or angle > 90):
                    validation["compatible"] = False
                    validation["issues"].append("Retract angle must be between -90 and 90 degrees")
            
            # Validate clearance parameters
            clearance = linking_section.get("clearance", {})
            if clearance:
                # Clearance height must be positive
                height = clearance.get("height")
                if height is not None and height <= 0:
                    validation["compatible"] = False
                    validation["issues"].append("Clearance height must be positive")
        
        # Validate transitions section
        transitions = sections.get("transitions", {})
        if transitions:
            # Stay down distance must be positive
            stay_down_distance = transitions.get("stay_down_distance")
            if stay_down_distance is not None and stay_down_distance < 0:
                validation["compatible"] = False
                validation["issues"].append("Stay down distance must be non-negative")
            
            # Lift height must be positive
            lift_height = transitions.get("lift_height")
            if lift_height is not None and lift_height < 0:
                validation["compatible"] = False
                validation["issues"].append("Lift height must be non-negative")
        
    except Exception:
        pass
    
    return validation


def _validate_drill_operation_constraints(sections: dict, validation: dict) -> dict:
    """Validate constraints specific to Drill operations."""
    try:
        # Validate drill cycle section
        drill_cycle = sections.get("drill_cycle", {})
        if drill_cycle:
            # Peck depth must be positive
            peck_depth = drill_cycle.get("peck_depth")
            if peck_depth is not None and peck_depth <= 0:
                validation["compatible"] = False
                validation["issues"].append("Peck depth must be positive")
            
            # Dwell time must be non-negative
            dwell_time = drill_cycle.get("dwell_time")
            if dwell_time is not None and dwell_time < 0:
                validation["compatible"] = False
                validation["issues"].append("Dwell time must be non-negative")
        
    except Exception:
        pass
    
    return validation


def _validate_linking_parameter_compatibility(operation: adsk.cam.Operation, linking_config: dict) -> dict:
    """
    Validate parameter compatibility with operation type.
    
    Args:
        operation: The CAM operation
        linking_config: New linking configuration
        
    Returns:
        dict: Compatibility validation result with compatible flag and issues list
    """
    validation = {"compatible": True, "issues": []}
    
    try:
        if not operation or not hasattr(operation, 'parameters'):
            validation["compatible"] = False
            validation["issues"].append("Operation parameters not accessible")
            return validation
        
        params = operation.parameters
        sections = linking_config.get("sections", {})
        
        # Check if requested parameters exist in the operation
        for section_name, section_data in sections.items():
            if isinstance(section_data, dict):
                for param_group, param_data in section_data.items():
                    if isinstance(param_data, dict):
                        for param_name, param_value in param_data.items():
                            # Try to find corresponding parameter in operation
                            fusion_param_name = _map_linking_param_to_fusion(section_name, param_group, param_name)
                            if fusion_param_name:
                                try:
                                    param = params.itemByName(fusion_param_name)
                                    if not param:
                                        validation["compatible"] = False
                                        validation["issues"].append(f"Parameter '{param_name}' not available for this operation type")
                                except Exception:
                                    validation["compatible"] = False
                                    validation["issues"].append(f"Parameter '{param_name}' not accessible for this operation")
        
        return validation
        
    except Exception as e:
        return {"compatible": False, "issues": [f"Parameter compatibility check failed: {str(e)}"]}


def _validate_linking_integrity(linking_config: dict, current_linking: dict) -> dict:
    """
    Ensure linking integrity is maintained.
    
    Args:
        linking_config: New linking configuration
        current_linking: Current linking configuration
        
    Returns:
        dict: Integrity validation result with valid flag, errors, and warnings
    """
    validation = {"valid": True, "errors": [], "warnings": []}
    
    try:
        sections = linking_config.get("sections", {})
        current_sections = current_linking.get("sections", {})
        
        # Check for conflicting parameter combinations
        for section_name, section_data in sections.items():
            if isinstance(section_data, dict):
                # Check for internal consistency within sections
                if section_name == "leads_and_transitions":
                    validation = _validate_leads_transitions_integrity(section_data, validation)
                elif section_name == "linking":
                    validation = _validate_linking_section_integrity(section_data, validation)
                elif section_name == "approach_retract":
                    validation = _validate_approach_retract_integrity(section_data, validation)
        
        # Warn about significant changes from current configuration
        for section_name, section_data in sections.items():
            current_section = current_sections.get(section_name, {})
            if current_section and isinstance(section_data, dict):
                for param_group, param_data in section_data.items():
                    current_param_group = current_section.get(param_group, {})
                    if current_param_group and isinstance(param_data, dict):
                        for param_name, param_value in param_data.items():
                            current_value = current_param_group.get(param_name)
                            if current_value is not None and current_value != param_value:
                                # Check for significant changes that might affect machining
                                if param_name in ["arc_radius", "distance", "height"] and isinstance(param_value, (int, float)):
                                    if abs(param_value - current_value) > current_value * 0.5:  # 50% change
                                        validation["warnings"].append(f"Significant change in {param_name}: {current_value} → {param_value}")
        
        return validation
        
    except Exception as e:
        return {"valid": False, "errors": [f"Integrity validation error: {str(e)}"], "warnings": []}


def _validate_leads_transitions_integrity(section_data: dict, validation: dict) -> dict:
    """Validate integrity of leads & transitions section."""
    try:
        lead_in = section_data.get("lead_in", {})
        lead_out = section_data.get("lead_out", {})
        
        # Check for consistent arc settings between lead-in and lead-out
        if lead_in.get("type") == "arc" and lead_out.get("type") == "arc":
            lead_in_radius = lead_in.get("arc_radius")
            lead_out_radius = lead_out.get("arc_radius")
            
            if lead_in_radius is not None and lead_out_radius is not None:
                if abs(lead_in_radius - lead_out_radius) > max(lead_in_radius, lead_out_radius) * 0.5:
                    validation["warnings"].append("Large difference between lead-in and lead-out arc radii may cause inconsistent tool paths")
        
    except Exception:
        pass
    
    return validation


def _validate_linking_section_integrity(section_data: dict, validation: dict) -> dict:
    """Validate integrity of linking section."""
    try:
        approach = section_data.get("approach", {})
        retract = section_data.get("retract", {})
        
        # Check for consistent approach/retract settings
        if approach.get("type") == retract.get("type"):
            approach_distance = approach.get("distance")
            retract_distance = retract.get("distance")
            
            if approach_distance is not None and retract_distance is not None:
                if abs(approach_distance - retract_distance) > max(approach_distance, retract_distance) * 0.3:
                    validation["warnings"].append("Different approach and retract distances may cause inconsistent tool movements")
        
    except Exception:
        pass
    
    return validation


def _validate_approach_retract_integrity(section_data: dict, validation: dict) -> dict:
    """Validate integrity of approach/retract section."""
    try:
        approach_distance = section_data.get("approach_distance")
        retract_distance = section_data.get("retract_distance")
        
        # Check for reasonable approach/retract distance relationship
        if approach_distance is not None and retract_distance is not None:
            if approach_distance > retract_distance * 3:
                validation["warnings"].append("Approach distance is much larger than retract distance, which may increase cycle time")
            elif retract_distance > approach_distance * 3:
                validation["warnings"].append("Retract distance is much larger than approach distance, which may be inefficient")
        
    except Exception:
        pass
    
    return validation


def _validate_linking_parameter_values(operation: adsk.cam.Operation, linking_config: dict) -> dict:
    """
    Validate parameter values against constraints.
    
    Args:
        operation: The CAM operation
        linking_config: New linking configuration
        
    Returns:
        dict: Value validation result with valid flag, errors, and warnings
    """
    validation = {"valid": True, "errors": [], "warnings": []}
    
    try:
        if not operation or not hasattr(operation, 'parameters'):
            validation["valid"] = False
            validation["errors"].append("Operation parameters not accessible")
            return validation
        
        params = operation.parameters
        sections = linking_config.get("sections", {})
        
        # Validate parameter values against Fusion 360 constraints
        for section_name, section_data in sections.items():
            if isinstance(section_data, dict):
                for param_group, param_data in section_data.items():
                    if isinstance(param_data, dict):
                        for param_name, param_value in param_data.items():
                            # Get corresponding Fusion parameter
                            fusion_param_name = _map_linking_param_to_fusion(section_name, param_group, param_name)
                            if fusion_param_name:
                                try:
                                    param = params.itemByName(fusion_param_name)
                                    if param:
                                        # Check min/max constraints
                                        if hasattr(param, 'minimumValue') and param.minimumValue is not None:
                                            if isinstance(param_value, (int, float)) and param_value < param.minimumValue:
                                                validation["valid"] = False
                                                validation["errors"].append(f"Parameter '{param_name}' value {param_value} is below minimum {param.minimumValue}")
                                        
                                        if hasattr(param, 'maximumValue') and param.maximumValue is not None:
                                            if isinstance(param_value, (int, float)) and param_value > param.maximumValue:
                                                validation["valid"] = False
                                                validation["errors"].append(f"Parameter '{param_name}' value {param_value} is above maximum {param.maximumValue}")
                                        
                                        # Check if parameter is read-only
                                        if hasattr(param, 'isReadOnly') and param.isReadOnly:
                                            validation["valid"] = False
                                            validation["errors"].append(f"Parameter '{param_name}' is read-only and cannot be modified")
                                except Exception:
                                    pass
        
        return validation
        
    except Exception as e:
        return {"valid": False, "errors": [f"Value validation error: {str(e)}"], "warnings": []}


def _map_linking_param_to_fusion(section_name: str, param_group: str, param_name: str) -> str:
    """
    Map linking parameter names to Fusion 360 parameter names.
    
    Args:
        section_name: Section name (e.g., "leads_and_transitions")
        param_group: Parameter group (e.g., "lead_in")
        param_name: Parameter name (e.g., "arc_radius")
        
    Returns:
        str: Fusion 360 parameter name or None if not found
    """
    # Mapping table for common linking parameters
    param_mapping = {
        ("leads_and_transitions", "lead_in", "type"): "leadInType",
        ("leads_and_transitions", "lead_in", "arc_radius"): "leadInRadius",
        ("leads_and_transitions", "lead_in", "arc_sweep"): "leadInSweepAngle",
        ("leads_and_transitions", "lead_in", "vertical_lead_in"): "verticalLeadIn",
        ("leads_and_transitions", "lead_out", "type"): "leadOutType",
        ("leads_and_transitions", "lead_out", "arc_radius"): "leadOutRadius",
        ("leads_and_transitions", "lead_out", "arc_sweep"): "leadOutSweepAngle",
        ("leads_and_transitions", "transitions", "type"): "transitionType",
        ("leads_and_transitions", "transitions", "lift_height"): "liftHeight",
        ("leads_and_transitions", "transitions", "order_by_depth"): "orderByDepth",
        ("leads_and_transitions", "transitions", "keep_tool_down"): "keepToolDown",
        ("entry_positioning", "", "clearance_height"): "clearanceHeight_value",
        ("entry_positioning", "", "feed_height"): "feedHeight_value",
        ("entry_positioning", "", "top_height"): "topHeight_value",
        ("contact_point", "", "type"): "contactPoint",
        ("contact_point", "", "distance"): "contactDistance",
        ("approach_retract", "", "approach_distance"): "approachDistance",
        ("approach_retract", "", "retract_distance"): "retractDistance",
        ("linking", "approach", "type"): "approachType",
        ("linking", "approach", "distance"): "approachDistance",
        ("linking", "approach", "angle"): "approachAngle",
        ("linking", "retract", "type"): "retractType",
        ("linking", "retract", "distance"): "retractDistance",
        ("linking", "retract", "angle"): "retractAngle",
        ("linking", "clearance", "height"): "clearanceHeight_value",
        ("linking", "clearance", "type"): "clearanceType",
        ("transitions", "", "stay_down_distance"): "stayDownDistance",
        ("transitions", "", "lift_height"): "liftHeight",
        ("transitions", "", "order_optimization"): "orderOptimization",
        ("drill_cycle", "", "cycle_type"): "cycleType",
        ("drill_cycle", "", "peck_depth"): "peckDepth",
        ("drill_cycle", "", "dwell_time"): "dwellTime",
        ("drill_cycle", "", "retract_behavior"): "retractBehavior"
    }
    
    return param_mapping.get((section_name, param_group, param_name))


def modify_toolpath_linking(cam: adsk.cam.CAM, toolpath_id: str, linking_config: dict) -> dict:
    """
    Modify linking parameters for a specific toolpath.
    
    Validates changes against operation-specific constraints, applies modifications,
    and returns modification results with validation details. Handles invalid 
    modifications with clear error messages.
    
    Args:
        cam: The CAM product instance
        toolpath_id: The unique identifier of the toolpath
        linking_config: Dictionary containing linking configuration changes
        
    Returns:
        dict: Modification result including:
            - success: Boolean indicating if modification was successful
            - message: Human-readable result message
            - previous_config: Linking configuration before changes
            - new_config: Linking configuration after changes
            - validation_result: Detailed validation information
            - applied_changes: List of parameters that were actually modified
            - error: Error information if modification fails
    
    Requirements: 7.4, 4.4, 4.5
    """
    # Validate CAM product
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "success": False,
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    # Validate toolpath_id parameter
    if not toolpath_id:
        return {
            "success": False,
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
        }
    
    # Validate linking_config parameter
    if not linking_config:
        return {
            "success": False,
            "error": True,
            "message": "Linking configuration is required",
            "code": "MISSING_LINKING_CONFIG"
        }
    
    try:
        # Find the operation
        operation = _find_operation_by_id(cam, toolpath_id)
        
        if not operation:
            return {
                "success": False,
                "error": True,
                "message": f"Toolpath with ID '{toolpath_id}' not found. Please verify the toolpath ID exists in the current CAM document",
                "code": "TOOLPATH_NOT_FOUND"
            }
        
        # Get current linking configuration before changes
        previous_config = _extract_linking_params(operation)
        
        # Validate the modification
        validation_result = validate_linking_modification(operation, linking_config)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": True,
                "message": f"Linking configuration validation failed: {'; '.join(validation_result['errors'])}",
                "code": "VALIDATION_FAILED",
                "validation_result": validation_result,
                "previous_config": previous_config
            }
        
        # Apply the linking configuration changes
        try:
            applied_changes = []
            
            if not hasattr(operation, 'parameters'):
                return {
                    "success": False,
                    "error": True,
                    "message": "Operation parameters not accessible",
                    "code": "PARAMETERS_NOT_ACCESSIBLE",
                    "validation_result": validation_result,
                    "previous_config": previous_config
                }
            
            params = operation.parameters
            sections = linking_config.get("sections", {})
            
            # Apply changes section by section
            for section_name, section_data in sections.items():
                if isinstance(section_data, dict):
                    for param_group, param_data in section_data.items():
                        if isinstance(param_data, dict):
                            for param_name, param_value in param_data.items():
                                # Map to Fusion parameter name
                                fusion_param_name = _map_linking_param_to_fusion(section_name, param_group, param_name)
                                if fusion_param_name:
                                    try:
                                        param = params.itemByName(fusion_param_name)
                                        if param:
                                            # Get old value
                                            old_value = _get_param_value(param)
                                            
                                            # Apply new value
                                            if hasattr(param, 'value'):
                                                if hasattr(param.value, 'value'):
                                                    param.value.value = param_value
                                                else:
                                                    param.value = param_value
                                            else:
                                                # For some parameter types, set directly
                                                param = param_value
                                            
                                            applied_changes.append({
                                                "parameter": f"{section_name}.{param_group}.{param_name}" if param_group else f"{section_name}.{param_name}",
                                                "fusion_parameter": fusion_param_name,
                                                "previous_value": old_value,
                                                "new_value": param_value,
                                                "type": "linking"
                                            })
                                    except Exception as e:
                                        # Log parameter application error but continue with other parameters
                                        applied_changes.append({
                                            "parameter": f"{section_name}.{param_group}.{param_name}" if param_group else f"{section_name}.{param_name}",
                                            "fusion_parameter": fusion_param_name,
                                            "error": f"Failed to apply: {str(e)}",
                                            "type": "linking"
                                        })
            
            # Get new configuration after changes
            new_config = _extract_linking_params(operation)
            
            return {
                "success": True,
                "message": f"Linking configuration modified successfully for toolpath '{toolpath_id}'",
                "previous_config": previous_config,
                "new_config": new_config,
                "validation_result": validation_result,
                "applied_changes": applied_changes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": True,
                "message": f"Failed to apply linking configuration changes: {str(e)}",
                "code": "APPLICATION_ERROR",
                "validation_result": validation_result,
                "previous_config": previous_config
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": True,
            "message": f"Error modifying toolpath linking: {str(e)}",
            "code": "MODIFICATION_ERROR"
        }


def calculate_pass_machining_time(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Calculate estimated machining times for passes.
    
    Analyzes pass parameters, tool settings, and geometry to estimate machining
    time for each pass. Considers cutting feedrates, rapid moves, tool changes,
    and material removal volumes.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration with pass details
        
    Returns:
        dict: Machining time analysis including:
            - total_time: Total estimated machining time in minutes
            - pass_times: List of time estimates for each pass
            - cutting_time: Time spent in cutting moves
            - rapid_time: Time spent in rapid moves
            - tool_change_time: Time for tool changes (if applicable)
            - breakdown: Detailed time breakdown by operation type
    
    Requirements: 3.4, 5.5
    """
    time_analysis = {
        "total_time": 0.0,
        "pass_times": [],
        "cutting_time": 0.0,
        "rapid_time": 0.0,
        "tool_change_time": 0.0,
        "breakdown": {}
    }
    
    try:
        if not operation or not pass_config:
            return time_analysis
        
        # Get operation parameters
        params = operation.parameters if hasattr(operation, 'parameters') else None
        if not params:
            return time_analysis
        
        # Extract key parameters for time calculation
        cutting_feedrate = _get_parameter_value(params, "tool_feedCutting", 1000.0)  # mm/min
        rapid_feedrate = _get_parameter_value(params, "tool_feedRapid", 10000.0)  # mm/min
        plunge_feedrate = _get_parameter_value(params, "tool_feedPlunge", 500.0)  # mm/min
        
        # Get tool information
        tool_data = _get_tool_data_from_operation(operation)
        tool_diameter = tool_data.get("diameter", 10.0)  # mm
        
        # Get geometry parameters
        stepover = _get_parameter_value(params, "stepover", 50.0)  # %
        stepdown = _get_parameter_value(params, "stepdown", 2.0)  # mm
        
        # Estimate cutting path length based on operation type
        operation_type = _get_operation_type(operation).lower()
        estimated_path_length = _estimate_cutting_path_length(operation, operation_type, tool_diameter, stepover)
        
        # Calculate times for each pass
        passes = pass_config.get("passes", [])
        total_cutting_time = 0.0
        total_rapid_time = 0.0
        
        for pass_info in passes:
            pass_time_data = {
                "pass_number": pass_info.get("pass_number", 1),
                "pass_type": pass_info.get("pass_type", "unknown"),
                "cutting_time": 0.0,
                "rapid_time": 0.0,
                "plunge_time": 0.0,
                "total_time": 0.0
            }
            
            # Adjust cutting parameters based on pass type
            pass_feedrate = cutting_feedrate
            pass_stepdown = stepdown
            
            if pass_info.get("pass_type") == "roughing":
                # Roughing passes typically use higher feedrates and stepdowns
                pass_feedrate = cutting_feedrate * 1.2
                pass_stepdown = stepdown * 1.5
            elif pass_info.get("pass_type") == "finishing":
                # Finishing passes use lower feedrates for better surface quality
                pass_feedrate = cutting_feedrate * 0.7
                pass_stepdown = stepdown * 0.5
            
            # Calculate cutting time for this pass
            pass_cutting_length = estimated_path_length
            
            # Adjust for stock to leave - less material means shorter cutting time
            stock_to_leave = pass_info.get("stock_to_leave", {})
            radial_stock = stock_to_leave.get("radial", 0.0)
            if radial_stock > 0:
                # Reduce cutting length based on stock to leave
                reduction_factor = max(0.1, 1.0 - (radial_stock / tool_diameter))
                pass_cutting_length *= reduction_factor
            
            pass_time_data["cutting_time"] = pass_cutting_length / pass_feedrate
            
            # Estimate plunge time (depth / plunge feedrate)
            depth = abs(pass_info.get("depth", stepdown))
            pass_time_data["plunge_time"] = depth / plunge_feedrate
            
            # Estimate rapid moves (approach, retract, positioning)
            rapid_distance = _estimate_rapid_distance(operation, pass_info)
            pass_time_data["rapid_time"] = rapid_distance / rapid_feedrate
            
            # Total time for this pass
            pass_time_data["total_time"] = (pass_time_data["cutting_time"] + 
                                          pass_time_data["plunge_time"] + 
                                          pass_time_data["rapid_time"])
            
            time_analysis["pass_times"].append(pass_time_data)
            total_cutting_time += pass_time_data["cutting_time"] + pass_time_data["plunge_time"]
            total_rapid_time += pass_time_data["rapid_time"]
        
        # Add tool change time if multiple passes with different tools
        tool_change_time = 0.0
        if len(passes) > 1:
            # Assume 2 minutes per tool change (conservative estimate)
            tool_change_time = (len(passes) - 1) * 2.0
        
        # Calculate totals
        time_analysis["cutting_time"] = total_cutting_time
        time_analysis["rapid_time"] = total_rapid_time
        time_analysis["tool_change_time"] = tool_change_time
        time_analysis["total_time"] = total_cutting_time + total_rapid_time + tool_change_time
        
        # Create detailed breakdown
        time_analysis["breakdown"] = {
            "operation_type": operation_type,
            "number_of_passes": len(passes),
            "estimated_path_length_mm": estimated_path_length,
            "average_cutting_feedrate": cutting_feedrate,
            "average_rapid_feedrate": rapid_feedrate,
            "tool_diameter_mm": tool_diameter,
            "efficiency_rating": _calculate_efficiency_rating(time_analysis, pass_config)
        }
        
        return time_analysis
        
    except Exception as e:
        time_analysis["error"] = f"Error calculating machining time: {str(e)}"
        return time_analysis


def analyze_material_removal_efficiency(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Analyze material removal rates and efficiency for passes.
    
    Calculates material removal rate (MRR), cutting efficiency, and identifies
    opportunities for optimization based on tool capabilities and pass parameters.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration with pass details
        
    Returns:
        dict: Material removal analysis including:
            - total_volume_removed: Estimated total material volume removed (mm³)
            - material_removal_rate: Average MRR in mm³/min
            - pass_efficiency: Efficiency analysis for each pass
            - optimization_opportunities: List of efficiency improvement suggestions
            - tool_utilization: How well the tool capabilities are being used
    
    Requirements: 3.4, 5.5
    """
    efficiency_analysis = {
        "total_volume_removed": 0.0,
        "material_removal_rate": 0.0,
        "pass_efficiency": [],
        "optimization_opportunities": [],
        "tool_utilization": {}
    }
    
    try:
        if not operation or not pass_config:
            return efficiency_analysis
        
        # Get operation parameters
        params = operation.parameters if hasattr(operation, 'parameters') else None
        if not params:
            return efficiency_analysis
        
        # Get tool information
        tool_data = _get_tool_data_from_operation(operation)
        tool_diameter = tool_data.get("diameter", 10.0)  # mm
        tool_length = tool_data.get("overall_length", 50.0)  # mm
        
        # Extract cutting parameters
        cutting_feedrate = _get_parameter_value(params, "tool_feedCutting", 1000.0)  # mm/min
        spindle_speed = _get_parameter_value(params, "tool_spindleSpeed", 5000.0)  # rpm
        stepover = _get_parameter_value(params, "stepover", 50.0)  # %
        stepdown = _get_parameter_value(params, "stepdown", 2.0)  # mm
        
        # Calculate actual stepover distance
        stepover_distance = (tool_diameter * stepover) / 100.0  # mm
        
        # Analyze each pass
        passes = pass_config.get("passes", [])
        total_volume = 0.0
        total_time = 0.0
        
        for pass_info in passes:
            pass_efficiency = {
                "pass_number": pass_info.get("pass_number", 1),
                "pass_type": pass_info.get("pass_type", "unknown"),
                "volume_removed": 0.0,
                "removal_rate": 0.0,
                "efficiency_score": 0.0,
                "recommendations": []
            }
            
            # Estimate volume removed for this pass
            depth = abs(pass_info.get("depth", stepdown))
            
            # Calculate cutting volume based on operation type
            operation_type = _get_operation_type(operation).lower()
            cutting_volume = _estimate_cutting_volume(operation, operation_type, 
                                                    tool_diameter, stepover_distance, depth)
            
            # Adjust for stock to leave
            stock_to_leave = pass_info.get("stock_to_leave", {})
            radial_stock = stock_to_leave.get("radial", 0.0)
            axial_stock = stock_to_leave.get("axial", 0.0)
            
            # Reduce volume based on stock to leave
            if radial_stock > 0 or axial_stock > 0:
                volume_reduction = 1.0 - ((radial_stock + axial_stock) / (tool_diameter + depth))
                cutting_volume *= max(0.1, volume_reduction)
            
            pass_efficiency["volume_removed"] = cutting_volume
            
            # Calculate material removal rate (MRR)
            # MRR = cutting_feedrate * stepover_distance * stepdown
            theoretical_mrr = cutting_feedrate * stepover_distance * stepdown
            
            # Adjust MRR based on pass type
            if pass_info.get("pass_type") == "roughing":
                # Roughing can achieve higher MRR
                actual_mrr = theoretical_mrr * 0.9
            elif pass_info.get("pass_type") == "finishing":
                # Finishing typically has lower MRR due to precision requirements
                actual_mrr = theoretical_mrr * 0.6
            else:
                actual_mrr = theoretical_mrr * 0.8
            
            pass_efficiency["removal_rate"] = actual_mrr
            
            # Calculate efficiency score (0-100)
            # Based on tool utilization, feedrate optimization, and cutting parameters
            efficiency_score = _calculate_pass_efficiency_score(
                cutting_feedrate, spindle_speed, stepover, stepdown,
                tool_diameter, pass_info.get("pass_type", "unknown")
            )
            pass_efficiency["efficiency_score"] = efficiency_score
            
            # Generate recommendations for this pass
            recommendations = _generate_pass_efficiency_recommendations(
                cutting_feedrate, spindle_speed, stepover, stepdown,
                tool_diameter, pass_info.get("pass_type", "unknown"), efficiency_score
            )
            pass_efficiency["recommendations"] = recommendations
            
            efficiency_analysis["pass_efficiency"].append(pass_efficiency)
            total_volume += cutting_volume
            
            # Estimate time for this pass (simplified)
            estimated_time = cutting_volume / actual_mrr if actual_mrr > 0 else 0
            total_time += estimated_time
        
        # Calculate overall metrics
        efficiency_analysis["total_volume_removed"] = total_volume
        efficiency_analysis["material_removal_rate"] = total_volume / total_time if total_time > 0 else 0
        
        # Analyze tool utilization
        efficiency_analysis["tool_utilization"] = _analyze_tool_utilization(
            tool_diameter, tool_length, cutting_feedrate, spindle_speed, stepover, stepdown
        )
        
        # Generate overall optimization opportunities
        efficiency_analysis["optimization_opportunities"] = _generate_overall_optimization_opportunities(
            efficiency_analysis["pass_efficiency"], efficiency_analysis["tool_utilization"]
        )
        
        return efficiency_analysis
        
    except Exception as e:
        efficiency_analysis["error"] = f"Error analyzing material removal efficiency: {str(e)}"
        return efficiency_analysis


def identify_tool_change_optimization_opportunities(cam: adsk.cam.CAM, setup_id: str = None) -> dict:
    """
    Identify tool change optimization opportunities within a setup or across setups.
    
    Analyzes tool usage patterns, identifies redundant tool changes, and suggests
    reordering strategies to minimize tool changes and improve efficiency.
    
    Args:
        cam: The CAM product instance
        setup_id: Optional setup ID to analyze (if None, analyzes all setups)
        
    Returns:
        dict: Tool change optimization analysis including:
            - current_tool_changes: Number of tool changes in current sequence
            - optimized_tool_changes: Number of tool changes after optimization
            - time_savings: Estimated time savings in minutes
            - optimization_strategies: List of specific optimization recommendations
            - tool_usage_analysis: Analysis of tool usage patterns
            - reordering_suggestions: Specific toolpath reordering suggestions
    
    Requirements: 5.5
    """
    optimization_analysis = {
        "current_tool_changes": 0,
        "optimized_tool_changes": 0,
        "time_savings": 0.0,
        "optimization_strategies": [],
        "tool_usage_analysis": {},
        "reordering_suggestions": []
    }
    
    try:
        if not cam:
            return optimization_analysis
        
        # Get setups to analyze
        setups_to_analyze = []
        if setup_id:
            setup = _find_setup_by_id(cam, setup_id)
            if setup:
                setups_to_analyze.append(setup)
        else:
            # Analyze all setups
            setups = cam.setups
            if setups:
                for i in range(setups.count):
                    setups_to_analyze.append(setups.item(i))
        
        if not setups_to_analyze:
            return optimization_analysis
        
        # Analyze each setup
        total_current_changes = 0
        total_optimized_changes = 0
        all_strategies = []
        all_suggestions = []
        tool_usage_data = {}
        
        for setup in setups_to_analyze:
            setup_analysis = _analyze_setup_tool_changes(setup)
            
            total_current_changes += setup_analysis["current_tool_changes"]
            total_optimized_changes += setup_analysis["optimized_tool_changes"]
            all_strategies.extend(setup_analysis["strategies"])
            all_suggestions.extend(setup_analysis["reordering_suggestions"])
            
            # Merge tool usage data
            for tool_id, usage_data in setup_analysis["tool_usage"].items():
                if tool_id in tool_usage_data:
                    tool_usage_data[tool_id]["usage_count"] += usage_data["usage_count"]
                    tool_usage_data[tool_id]["operations"].extend(usage_data["operations"])
                else:
                    tool_usage_data[tool_id] = usage_data.copy()
        
        # Calculate time savings (assume 2 minutes per tool change saved)
        tool_changes_saved = total_current_changes - total_optimized_changes
        time_savings = tool_changes_saved * 2.0  # minutes
        
        # Generate optimization strategies
        optimization_strategies = _generate_tool_change_strategies(
            total_current_changes, total_optimized_changes, tool_usage_data
        )
        
        optimization_analysis.update({
            "current_tool_changes": total_current_changes,
            "optimized_tool_changes": total_optimized_changes,
            "time_savings": time_savings,
            "optimization_strategies": optimization_strategies,
            "tool_usage_analysis": tool_usage_data,
            "reordering_suggestions": all_suggestions
        })
        
        return optimization_analysis
        
    except Exception as e:
        optimization_analysis["error"] = f"Error identifying tool change optimization opportunities: {str(e)}"
        return optimization_analysis


def validate_stock_to_leave_calculations(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Provide stock-to-leave calculation validation.
    
    Validates that stock-to-leave values are appropriate for the operation,
    tool, and subsequent finishing operations. Checks for adequate material
    for finishing passes and identifies potential issues.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration with stock-to-leave values
        
    Returns:
        dict: Stock-to-leave validation including:
            - valid: Boolean indicating if stock-to-leave values are valid
            - issues: List of validation issues found
            - warnings: List of potential concerns
            - recommendations: Suggestions for stock-to-leave optimization
            - finishing_adequacy: Analysis of material left for finishing
    
    Requirements: 3.3, 6.2
    """
    validation_result = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "recommendations": [],
        "finishing_adequacy": {}
    }
    
    try:
        if not operation or not pass_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Operation or pass configuration not provided")
            return validation_result
        
        # Get tool information
        tool_data = _get_tool_data_from_operation(operation)
        tool_diameter = tool_data.get("diameter", 10.0)  # mm
        
        # Get operation parameters
        params = operation.parameters if hasattr(operation, 'parameters') else None
        if not params:
            validation_result["valid"] = False
            validation_result["issues"].append("Operation parameters not accessible")
            return validation_result
        
        # Analyze each pass
        passes = pass_config.get("passes", [])
        finishing_passes = [p for p in passes if p.get("pass_type") == "finishing"]
        roughing_passes = [p for p in passes if p.get("pass_type") == "roughing"]
        
        # Validate stock-to-leave values for each pass
        for i, pass_info in enumerate(passes):
            pass_number = pass_info.get("pass_number", i + 1)
            stock_to_leave = pass_info.get("stock_to_leave", {})
            radial_stock = stock_to_leave.get("radial", 0.0)
            axial_stock = stock_to_leave.get("axial", 0.0)
            pass_type = pass_info.get("pass_type", "unknown")
            
            # Validate radial stock to leave
            if radial_stock < 0:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Pass {pass_number}: Radial stock to leave cannot be negative ({radial_stock}mm)")
            
            if radial_stock > tool_diameter * 0.5:
                validation_result["warnings"].append(f"Pass {pass_number}: Radial stock to leave ({radial_stock}mm) is more than 50% of tool diameter")
            
            # Validate axial stock to leave
            if axial_stock < 0:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Pass {pass_number}: Axial stock to leave cannot be negative ({axial_stock}mm)")
            
            # Check for appropriate stock-to-leave based on pass type
            if pass_type == "roughing":
                if radial_stock < 0.1:
                    validation_result["warnings"].append(f"Pass {pass_number}: Very small radial stock to leave for roughing pass ({radial_stock}mm)")
                if radial_stock > 2.0:
                    validation_result["warnings"].append(f"Pass {pass_number}: Large radial stock to leave for roughing pass ({radial_stock}mm) may be inefficient")
            
            elif pass_type == "finishing":
                if radial_stock > 0.1:
                    validation_result["warnings"].append(f"Pass {pass_number}: Finishing pass has stock to leave ({radial_stock}mm) - typically should be 0")
                if axial_stock > 0.05:
                    validation_result["warnings"].append(f"Pass {pass_number}: Finishing pass has axial stock to leave ({axial_stock}mm) - typically should be 0")
        
        # Validate pass sequence stock-to-leave progression
        for i in range(len(passes) - 1):
            current_pass = passes[i]
            next_pass = passes[i + 1]
            
            current_radial = current_pass.get("stock_to_leave", {}).get("radial", 0.0)
            next_radial = next_pass.get("stock_to_leave", {}).get("radial", 0.0)
            
            if next_radial > current_radial:
                validation_result["warnings"].append(
                    f"Pass {i + 2} has more radial stock to leave ({next_radial}mm) than previous pass ({current_radial}mm)"
                )
        
        # Analyze finishing adequacy
        if finishing_passes and roughing_passes:
            last_roughing = roughing_passes[-1]
            first_finishing = finishing_passes[0]
            
            roughing_radial = last_roughing.get("stock_to_leave", {}).get("radial", 0.0)
            roughing_axial = last_roughing.get("stock_to_leave", {}).get("axial", 0.0)
            
            validation_result["finishing_adequacy"] = {
                "material_available_radial": roughing_radial,
                "material_available_axial": roughing_axial,
                "adequate_for_finishing": True,
                "recommended_finishing_passes": 1
            }
            
            # Check if there's adequate material for finishing
            if roughing_radial < 0.05:
                validation_result["finishing_adequacy"]["adequate_for_finishing"] = False
                validation_result["issues"].append("Insufficient radial stock left by roughing for finishing operation")
            
            if roughing_axial < 0.02:
                validation_result["finishing_adequacy"]["adequate_for_finishing"] = False
                validation_result["issues"].append("Insufficient axial stock left by roughing for finishing operation")
            
            # Recommend number of finishing passes based on stock to leave
            if roughing_radial > 0.5:
                validation_result["finishing_adequacy"]["recommended_finishing_passes"] = 2
                validation_result["recommendations"].append("Consider multiple finishing passes due to large stock to leave")
        
        # Generate general recommendations
        if not finishing_passes and any(p.get("stock_to_leave", {}).get("radial", 0) > 0.1 for p in passes):
            validation_result["recommendations"].append("Consider adding finishing passes to remove remaining stock")
        
        if len(passes) == 1 and passes[0].get("stock_to_leave", {}).get("radial", 0) > 0:
            validation_result["recommendations"].append("Single pass with stock to leave - consider if finishing operation is planned")
        
        # Check tool compatibility with stock-to-leave values
        max_radial_stock = max((p.get("stock_to_leave", {}).get("radial", 0) for p in passes), default=0)
        if max_radial_stock > tool_diameter * 0.3:
            validation_result["warnings"].append(f"Maximum radial stock to leave ({max_radial_stock}mm) is large relative to tool diameter ({tool_diameter}mm)")
        
        return validation_result
        
    except Exception as e:
        validation_result["valid"] = False
        validation_result["issues"].append(f"Error validating stock-to-leave calculations: {str(e)}")
        return validation_result


# Helper functions for efficiency analysis

def _get_parameter_value(params, param_name: str, default_value: float) -> float:
    """
    Get parameter value with fallback to default.
    
    Args:
        params: Operation parameters collection
        param_name: Name of the parameter to retrieve
        default_value: Default value if parameter not found
        
    Returns:
        float: Parameter value or default
    """
    try:
        param = params.itemByName(param_name)
        if param and hasattr(param, 'value'):
            if hasattr(param.value, 'value'):
                return float(param.value.value)
            else:
                return float(param.value)
        return default_value
    except Exception:
        return default_value


def _estimate_cutting_path_length(operation: adsk.cam.Operation, operation_type: str, tool_diameter: float, stepover: float) -> float:
    """
    Estimate cutting path length based on operation type and parameters.
    
    Args:
        operation: The CAM operation
        operation_type: Type of operation (pocket, contour, etc.)
        tool_diameter: Tool diameter in mm
        stepover: Stepover percentage
        
    Returns:
        float: Estimated cutting path length in mm
    """
    try:
        # Base estimates for different operation types (simplified)
        if "pocket" in operation_type:
            # Pocket operations typically have longer paths due to area clearing
            return 500.0 * (100.0 / stepover)  # Longer paths with smaller stepover
        elif "contour" in operation_type or "trace" in operation_type:
            # Contour operations follow part geometry
            return 200.0
        elif "adaptive" in operation_type:
            # Adaptive clearing has efficient paths
            return 300.0 * (100.0 / stepover)
        elif "drill" in operation_type:
            # Drilling has minimal lateral movement
            return 50.0
        else:
            # Default estimate
            return 250.0
    except Exception:
        return 250.0


def _estimate_rapid_distance(operation: adsk.cam.Operation, pass_info: dict) -> float:
    """
    Estimate rapid move distance for a pass.
    
    Args:
        operation: The CAM operation
        pass_info: Pass information dictionary
        
    Returns:
        float: Estimated rapid distance in mm
    """
    try:
        # Base rapid distance includes approach, retract, and positioning moves
        base_rapid = 100.0  # mm
        
        # Add extra rapid moves for finishing passes (more precise positioning)
        if pass_info.get("pass_type") == "finishing":
            base_rapid += 50.0
        
        # Add clearance height moves
        depth = abs(pass_info.get("depth", 5.0))
        clearance_moves = depth * 2  # Up and down moves
        
        return base_rapid + clearance_moves
    except Exception:
        return 150.0


def _estimate_cutting_volume(operation: adsk.cam.Operation, operation_type: str, tool_diameter: float, stepover_distance: float, depth: float) -> float:
    """
    Estimate cutting volume for a pass.
    
    Args:
        operation: The CAM operation
        operation_type: Type of operation
        tool_diameter: Tool diameter in mm
        stepover_distance: Stepover distance in mm
        depth: Cutting depth in mm
        
    Returns:
        float: Estimated cutting volume in mm³
    """
    try:
        if "pocket" in operation_type:
            # Pocket: assume rectangular area
            area = 2500.0  # mm² (50mm x 50mm default)
            return area * depth
        elif "contour" in operation_type:
            # Contour: volume based on tool path and depth
            path_length = 200.0  # mm
            cutting_width = tool_diameter * 0.8  # Effective cutting width
            return path_length * cutting_width * depth
        elif "adaptive" in operation_type:
            # Adaptive: efficient material removal
            area = 2000.0  # mm²
            return area * depth
        elif "drill" in operation_type:
            # Drill: cylindrical volume
            radius = tool_diameter / 2.0
            return 3.14159 * radius * radius * depth
        else:
            # Default volume calculation
            return tool_diameter * stepover_distance * depth * 10.0
    except Exception:
        return 1000.0  # Default volume


def _calculate_efficiency_rating(time_analysis: dict, pass_config: dict) -> float:
    """
    Calculate overall efficiency rating (0-100).
    
    Args:
        time_analysis: Time analysis results
        pass_config: Pass configuration
        
    Returns:
        float: Efficiency rating from 0-100
    """
    try:
        cutting_time = time_analysis.get("cutting_time", 0.0)
        total_time = time_analysis.get("total_time", 1.0)
        
        # Efficiency based on cutting time vs total time
        cutting_efficiency = (cutting_time / total_time) * 100.0 if total_time > 0 else 0.0
        
        # Adjust for number of passes (fewer passes generally more efficient)
        num_passes = len(pass_config.get("passes", []))
        pass_efficiency = max(50.0, 100.0 - (num_passes - 1) * 10.0)
        
        # Combined efficiency rating
        overall_efficiency = (cutting_efficiency * 0.7) + (pass_efficiency * 0.3)
        
        return min(100.0, max(0.0, overall_efficiency))
    except Exception:
        return 50.0


def _calculate_pass_efficiency_score(cutting_feedrate: float, spindle_speed: float, stepover: float, stepdown: float, tool_diameter: float, pass_type: str) -> float:
    """
    Calculate efficiency score for a single pass.
    
    Args:
        cutting_feedrate: Cutting feedrate in mm/min
        spindle_speed: Spindle speed in rpm
        stepover: Stepover percentage
        stepdown: Stepdown in mm
        tool_diameter: Tool diameter in mm
        pass_type: Type of pass (roughing, finishing, etc.)
        
    Returns:
        float: Efficiency score from 0-100
    """
    try:
        score = 50.0  # Base score
        
        # Feedrate efficiency (higher is generally better for roughing)
        if pass_type == "roughing":
            if cutting_feedrate > 1500:
                score += 20
            elif cutting_feedrate > 1000:
                score += 10
        elif pass_type == "finishing":
            if 800 <= cutting_feedrate <= 1200:
                score += 15  # Optimal range for finishing
        
        # Spindle speed efficiency
        if 3000 <= spindle_speed <= 8000:
            score += 15  # Good spindle speed range
        
        # Stepover efficiency
        if pass_type == "roughing":
            if stepover >= 60:
                score += 10  # Aggressive stepover for roughing
        elif pass_type == "finishing":
            if 20 <= stepover <= 40:
                score += 10  # Conservative stepover for finishing
        
        # Stepdown efficiency
        if stepdown > 0.5 and stepdown <= tool_diameter * 0.3:
            score += 10  # Reasonable stepdown
        
        return min(100.0, max(0.0, score))
    except Exception:
        return 50.0


def _generate_pass_efficiency_recommendations(cutting_feedrate: float, spindle_speed: float, stepover: float, stepdown: float, tool_diameter: float, pass_type: str, efficiency_score: float) -> list:
    """
    Generate efficiency recommendations for a pass.
    
    Args:
        cutting_feedrate: Cutting feedrate in mm/min
        spindle_speed: Spindle speed in rpm
        stepover: Stepover percentage
        stepdown: Stepdown in mm
        tool_diameter: Tool diameter in mm
        pass_type: Type of pass
        efficiency_score: Current efficiency score
        
    Returns:
        list: List of recommendation strings
    """
    recommendations = []
    
    try:
        if efficiency_score < 60:
            recommendations.append("Consider optimizing cutting parameters for better efficiency")
        
        if pass_type == "roughing":
            if cutting_feedrate < 1000:
                recommendations.append("Consider increasing cutting feedrate for roughing operations")
            if stepover < 50:
                recommendations.append("Consider increasing stepover for more aggressive roughing")
        
        elif pass_type == "finishing":
            if cutting_feedrate > 1500:
                recommendations.append("Consider reducing cutting feedrate for better surface finish")
            if stepover > 50:
                recommendations.append("Consider reducing stepover for better surface quality")
        
        if spindle_speed < 2000:
            recommendations.append("Consider increasing spindle speed for better cutting performance")
        elif spindle_speed > 10000:
            recommendations.append("Very high spindle speed - ensure tool and machine can handle this")
        
        if stepdown > tool_diameter * 0.5:
            recommendations.append("Large stepdown relative to tool diameter - consider reducing for tool life")
        
    except Exception:
        pass
    
    return recommendations


def _analyze_tool_utilization(tool_diameter: float, tool_length: float, cutting_feedrate: float, spindle_speed: float, stepover: float, stepdown: float) -> dict:
    """
    Analyze how well tool capabilities are being utilized.
    
    Args:
        tool_diameter: Tool diameter in mm
        tool_length: Tool length in mm
        cutting_feedrate: Cutting feedrate in mm/min
        spindle_speed: Spindle speed in rpm
        stepover: Stepover percentage
        stepdown: Stepdown in mm
        
    Returns:
        dict: Tool utilization analysis
    """
    utilization = {
        "diameter_utilization": 0.0,
        "length_utilization": 0.0,
        "speed_utilization": 0.0,
        "overall_utilization": 0.0,
        "recommendations": []
    }
    
    try:
        # Diameter utilization based on stepover
        utilization["diameter_utilization"] = min(100.0, stepover)
        
        # Length utilization based on stepdown vs available length
        if tool_length > 0:
            utilization["length_utilization"] = min(100.0, (stepdown / (tool_length * 0.7)) * 100.0)
        
        # Speed utilization (assume optimal range is 3000-8000 rpm)
        if 3000 <= spindle_speed <= 8000:
            utilization["speed_utilization"] = 100.0
        elif spindle_speed < 3000:
            utilization["speed_utilization"] = (spindle_speed / 3000.0) * 100.0
        else:
            utilization["speed_utilization"] = max(50.0, 100.0 - ((spindle_speed - 8000) / 2000.0) * 25.0)
        
        # Overall utilization
        utilization["overall_utilization"] = (
            utilization["diameter_utilization"] * 0.4 +
            utilization["length_utilization"] * 0.3 +
            utilization["speed_utilization"] * 0.3
        )
        
        # Generate recommendations
        if utilization["diameter_utilization"] < 50:
            utilization["recommendations"].append("Tool diameter is underutilized - consider increasing stepover")
        
        if utilization["length_utilization"] < 30:
            utilization["recommendations"].append("Tool length is underutilized - consider increasing stepdown")
        
        if utilization["speed_utilization"] < 70:
            utilization["recommendations"].append("Spindle speed could be optimized for better performance")
        
    except Exception:
        pass
    
    return utilization


def _generate_overall_optimization_opportunities(pass_efficiency: list, tool_utilization: dict) -> list:
    """
    Generate overall optimization opportunities.
    
    Args:
        pass_efficiency: List of pass efficiency analyses
        tool_utilization: Tool utilization analysis
        
    Returns:
        list: List of optimization opportunity strings
    """
    opportunities = []
    
    try:
        # Analyze pass efficiency scores
        if pass_efficiency:
            avg_efficiency = sum(p.get("efficiency_score", 0) for p in pass_efficiency) / len(pass_efficiency)
            
            if avg_efficiency < 60:
                opportunities.append("Overall pass efficiency is low - review cutting parameters")
            
            # Check for inconsistent efficiency across passes
            efficiency_scores = [p.get("efficiency_score", 0) for p in pass_efficiency]
            if len(efficiency_scores) > 1:
                efficiency_range = max(efficiency_scores) - min(efficiency_scores)
                if efficiency_range > 30:
                    opportunities.append("Large efficiency variation between passes - consider parameter harmonization")
        
        # Tool utilization opportunities
        overall_utilization = tool_utilization.get("overall_utilization", 0)
        if overall_utilization < 60:
            opportunities.append("Tool capabilities are underutilized - consider more aggressive parameters")
        
        # Add tool utilization recommendations
        opportunities.extend(tool_utilization.get("recommendations", []))
        
        # Check for finishing pass optimization
        finishing_passes = [p for p in pass_efficiency if p.get("pass_type") == "finishing"]
        if len(finishing_passes) > 1:
            opportunities.append("Multiple finishing passes detected - consider consolidation if surface quality allows")
        
    except Exception:
        pass
    
    return opportunities


def _analyze_setup_tool_changes(setup) -> dict:
    """
    Analyze tool changes within a setup.
    
    Args:
        setup: CAM setup object
        
    Returns:
        dict: Tool change analysis for the setup
    """
    analysis = {
        "current_tool_changes": 0,
        "optimized_tool_changes": 0,
        "strategies": [],
        "reordering_suggestions": [],
        "tool_usage": {}
    }
    
    try:
        if not setup or not hasattr(setup, 'operations'):
            return analysis
        
        operations = setup.operations
        if not operations:
            return analysis
        
        # Analyze current tool sequence
        tool_sequence = []
        tool_usage = {}
        
        for i in range(operations.count):
            operation = operations.item(i)
            tool_data = _get_tool_data_from_operation(operation)
            tool_id = tool_data.get("id", f"tool_{i}")
            tool_name = tool_data.get("name", "Unknown Tool")
            
            tool_sequence.append({
                "operation_index": i,
                "operation_name": operation.name,
                "tool_id": tool_id,
                "tool_name": tool_name
            })
            
            # Track tool usage
            if tool_id not in tool_usage:
                tool_usage[tool_id] = {
                    "tool_name": tool_name,
                    "usage_count": 0,
                    "operations": []
                }
            
            tool_usage[tool_id]["usage_count"] += 1
            tool_usage[tool_id]["operations"].append({
                "index": i,
                "name": operation.name
            })
        
        # Count current tool changes
        current_changes = 0
        for i in range(1, len(tool_sequence)):
            if tool_sequence[i]["tool_id"] != tool_sequence[i-1]["tool_id"]:
                current_changes += 1
        
        # Calculate optimized tool changes (group by tool)
        unique_tools = list(tool_usage.keys())
        optimized_changes = max(0, len(unique_tools) - 1)
        
        # Generate optimization strategies
        strategies = []
        if current_changes > optimized_changes:
            strategies.append(f"Group operations by tool to reduce changes from {current_changes} to {optimized_changes}")
        
        # Generate reordering suggestions
        reordering_suggestions = []
        for tool_id, usage_data in tool_usage.items():
            if usage_data["usage_count"] > 1:
                op_indices = [op["index"] for op in usage_data["operations"]]
                if max(op_indices) - min(op_indices) > usage_data["usage_count"]:
                    reordering_suggestions.append(
                        f"Group {usage_data['tool_name']} operations together (currently at positions {op_indices})"
                    )
        
        analysis.update({
            "current_tool_changes": current_changes,
            "optimized_tool_changes": optimized_changes,
            "strategies": strategies,
            "reordering_suggestions": reordering_suggestions,
            "tool_usage": tool_usage
        })
        
    except Exception:
        pass
    
    return analysis


def _generate_tool_change_strategies(current_changes: int, optimized_changes: int, tool_usage_data: dict) -> list:
    """
    Generate tool change optimization strategies.
    
    Args:
        current_changes: Current number of tool changes
        optimized_changes: Optimized number of tool changes
        tool_usage_data: Tool usage analysis data
        
    Returns:
        list: List of optimization strategy strings
    """
    strategies = []
    
    try:
        if current_changes > optimized_changes:
            savings = current_changes - optimized_changes
            strategies.append(f"Reorder operations to save {savings} tool changes")
        
        # Identify frequently used tools
        frequent_tools = [(tool_id, data) for tool_id, data in tool_usage_data.items() if data["usage_count"] > 2]
        if frequent_tools:
            strategies.append("Consider grouping operations for frequently used tools")
        
        # Identify single-use tools
        single_use_tools = [(tool_id, data) for tool_id, data in tool_usage_data.items() if data["usage_count"] == 1]
        if len(single_use_tools) > 3:
            strategies.append("Consider consolidating single-use tools if possible")
        
        # Tool change time optimization
        if current_changes > 5:
            strategies.append("High number of tool changes - consider tool change time in scheduling")
        
    except Exception:
        pass
    
    return strategies


def detect_pass_tool_conflicts(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Identify conflicts between pass parameters and tool capabilities.
    
    Analyzes pass parameters against tool specifications to identify potential
    conflicts that could cause machining issues, tool breakage, or poor results.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration with pass details
        
    Returns:
        dict: Conflict detection results including:
            - conflicts_found: Boolean indicating if conflicts were detected
            - critical_conflicts: List of critical conflicts that must be resolved
            - warnings: List of potential issues that should be reviewed
            - tool_compatibility: Analysis of tool compatibility with each pass
            - recommendations: Suggestions for resolving conflicts
    
    Requirements: 3.5
    """
    conflict_analysis = {
        "conflicts_found": False,
        "critical_conflicts": [],
        "warnings": [],
        "tool_compatibility": [],
        "recommendations": []
    }
    
    try:
        if not operation or not pass_config:
            return conflict_analysis
        
        # Get tool information
        tool_data = _get_tool_data_from_operation(operation)
        tool_diameter = tool_data.get("diameter", 10.0)  # mm
        tool_length = tool_data.get("overall_length", 50.0)  # mm
        tool_type = tool_data.get("type", "unknown")
        
        # Get operation parameters
        params = operation.parameters if hasattr(operation, 'parameters') else None
        if not params:
            conflict_analysis["critical_conflicts"].append("Operation parameters not accessible")
            conflict_analysis["conflicts_found"] = True
            return conflict_analysis
        
        # Extract key parameters
        cutting_feedrate = _get_parameter_value(params, "tool_feedCutting", 1000.0)
        spindle_speed = _get_parameter_value(params, "tool_spindleSpeed", 5000.0)
        stepover = _get_parameter_value(params, "stepover", 50.0)
        stepdown = _get_parameter_value(params, "stepdown", 2.0)
        
        # Analyze each pass for conflicts
        passes = pass_config.get("passes", [])
        
        for pass_info in passes:
            pass_compatibility = {
                "pass_number": pass_info.get("pass_number", 1),
                "pass_type": pass_info.get("pass_type", "unknown"),
                "compatible": True,
                "issues": [],
                "warnings": []
            }
            
            # Check stepdown vs tool length
            depth = abs(pass_info.get("depth", stepdown))
            if depth > tool_length * 0.8:
                conflict_analysis["critical_conflicts"].append(
                    f"Pass {pass_compatibility['pass_number']}: Cutting depth ({depth}mm) exceeds safe tool length ({tool_length * 0.8}mm)"
                )
                pass_compatibility["compatible"] = False
                pass_compatibility["issues"].append("Excessive cutting depth for tool length")
                conflict_analysis["conflicts_found"] = True
            
            # Check stepover vs tool diameter
            stepover_distance = (tool_diameter * stepover) / 100.0
            if stepover_distance > tool_diameter * 1.2:
                conflict_analysis["critical_conflicts"].append(
                    f"Pass {pass_compatibility['pass_number']}: Stepover distance ({stepover_distance:.2f}mm) exceeds tool diameter ({tool_diameter}mm)"
                )
                pass_compatibility["compatible"] = False
                pass_compatibility["issues"].append("Stepover exceeds tool diameter")
                conflict_analysis["conflicts_found"] = True
            
            # Check feedrate vs tool capabilities
            pass_type = pass_info.get("pass_type", "unknown")
            if pass_type == "finishing" and cutting_feedrate > 2000:
                conflict_analysis["warnings"].append(
                    f"Pass {pass_compatibility['pass_number']}: High feedrate ({cutting_feedrate}mm/min) for finishing pass may affect surface quality"
                )
                pass_compatibility["warnings"].append("High feedrate for finishing operation")
            
            elif pass_type == "roughing" and cutting_feedrate < 500:
                conflict_analysis["warnings"].append(
                    f"Pass {pass_compatibility['pass_number']}: Low feedrate ({cutting_feedrate}mm/min) for roughing pass may be inefficient"
                )
                pass_compatibility["warnings"].append("Low feedrate for roughing operation")
            
            # Check spindle speed vs tool diameter
            surface_speed = (3.14159 * tool_diameter * spindle_speed) / 1000.0  # m/min
            if surface_speed > 300:  # High surface speed
                conflict_analysis["warnings"].append(
                    f"Pass {pass_compatibility['pass_number']}: High surface speed ({surface_speed:.1f}m/min) - ensure tool can handle this"
                )
                pass_compatibility["warnings"].append("High surface speed")
            
            # Check stock to leave vs tool precision
            stock_to_leave = pass_info.get("stock_to_leave", {})
            radial_stock = stock_to_leave.get("radial", 0.0)
            
            if pass_type == "finishing" and radial_stock > 0.05:
                conflict_analysis["warnings"].append(
                    f"Pass {pass_compatibility['pass_number']}: Finishing pass with stock to leave ({radial_stock}mm) may not achieve final dimensions"
                )
                pass_compatibility["warnings"].append("Stock to leave in finishing pass")
            
            # Check tool type compatibility with operation
            operation_type = _get_operation_type(operation).lower()
            tool_operation_conflicts = _check_tool_operation_compatibility(tool_type, operation_type, pass_type)
            if tool_operation_conflicts:
                conflict_analysis["warnings"].extend(tool_operation_conflicts)
                pass_compatibility["warnings"].extend(tool_operation_conflicts)
            
            conflict_analysis["tool_compatibility"].append(pass_compatibility)
        
        # Generate recommendations for resolving conflicts
        if conflict_analysis["conflicts_found"]:
            conflict_analysis["recommendations"].extend(_generate_conflict_resolution_recommendations(
                conflict_analysis["critical_conflicts"], tool_data, passes
            ))
        
        # Add general recommendations for warnings
        if conflict_analysis["warnings"]:
            conflict_analysis["recommendations"].extend(_generate_warning_recommendations(
                conflict_analysis["warnings"], tool_data
            ))
        
        return conflict_analysis
        
    except Exception as e:
        conflict_analysis["critical_conflicts"].append(f"Error detecting pass-tool conflicts: {str(e)}")
        conflict_analysis["conflicts_found"] = True
        return conflict_analysis


def validate_tool_compatibility_across_passes(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Validate tool compatibility across pass sequences.
    
    Ensures that the same tool can effectively handle all passes in the sequence
    and identifies where tool changes might be beneficial.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration with multiple passes
        
    Returns:
        dict: Tool compatibility validation including:
            - compatible: Boolean indicating overall compatibility
            - compatibility_issues: List of compatibility problems
            - pass_analysis: Detailed analysis for each pass
            - tool_change_recommendations: Suggestions for tool changes
            - sequence_optimization: Recommendations for pass sequence optimization
    
    Requirements: 3.5
    """
    compatibility_analysis = {
        "compatible": True,
        "compatibility_issues": [],
        "pass_analysis": [],
        "tool_change_recommendations": [],
        "sequence_optimization": []
    }
    
    try:
        if not operation or not pass_config:
            return compatibility_analysis
        
        # Get tool information
        tool_data = _get_tool_data_from_operation(operation)
        tool_diameter = tool_data.get("diameter", 10.0)
        tool_type = tool_data.get("type", "unknown")
        
        passes = pass_config.get("passes", [])
        if len(passes) < 2:
            # Single pass - no sequence compatibility issues
            return compatibility_analysis
        
        # Analyze compatibility between consecutive passes
        for i in range(len(passes)):
            current_pass = passes[i]
            pass_analysis = {
                "pass_number": current_pass.get("pass_number", i + 1),
                "pass_type": current_pass.get("pass_type", "unknown"),
                "tool_suitable": True,
                "issues": [],
                "recommendations": []
            }
            
            # Check if tool is suitable for this pass type
            pass_type = current_pass.get("pass_type", "unknown")
            
            if pass_type == "roughing":
                # Roughing passes need robust tools
                if tool_diameter < 3.0:
                    pass_analysis["tool_suitable"] = False
                    pass_analysis["issues"].append("Small tool diameter may not be suitable for roughing")
                    compatibility_analysis["compatible"] = False
                    compatibility_analysis["compatibility_issues"].append(
                        f"Pass {pass_analysis['pass_number']}: Tool too small for roughing operation"
                    )
            
            elif pass_type == "finishing":
                # Finishing passes need precise tools
                if tool_diameter > 20.0:
                    pass_analysis["issues"].append("Large tool diameter may limit finishing precision")
                    compatibility_analysis["compatibility_issues"].append(
                        f"Pass {pass_analysis['pass_number']}: Large tool may affect finishing quality"
                    )
            
            # Check stock to leave progression
            if i > 0:
                previous_pass = passes[i - 1]
                current_stock = current_pass.get("stock_to_leave", {}).get("radial", 0.0)
                previous_stock = previous_pass.get("stock_to_leave", {}).get("radial", 0.0)
                
                if current_stock > previous_stock:
                    pass_analysis["tool_suitable"] = False
                    pass_analysis["issues"].append("Stock to leave increases from previous pass")
                    compatibility_analysis["compatible"] = False
                    compatibility_analysis["compatibility_issues"].append(
                        f"Pass {pass_analysis['pass_number']}: Stock to leave progression is incorrect"
                    )
                
                # Check if tool can remove the required material
                material_to_remove = previous_stock - current_stock
                if material_to_remove > tool_diameter * 0.4:
                    pass_analysis["issues"].append("Large material removal may stress tool")
                    compatibility_analysis["compatibility_issues"].append(
                        f"Pass {pass_analysis['pass_number']}: Excessive material removal for single pass"
                    )
            
            compatibility_analysis["pass_analysis"].append(pass_analysis)
        
        # Generate tool change recommendations
        if not compatibility_analysis["compatible"]:
            compatibility_analysis["tool_change_recommendations"] = _generate_tool_change_recommendations(
                passes, tool_data, compatibility_analysis["compatibility_issues"]
            )
        
        # Generate sequence optimization recommendations
        compatibility_analysis["sequence_optimization"] = _generate_sequence_optimization_recommendations(
            passes, tool_data, compatibility_analysis["pass_analysis"]
        )
        
        return compatibility_analysis
        
    except Exception as e:
        compatibility_analysis["compatible"] = False
        compatibility_analysis["compatibility_issues"].append(f"Error validating tool compatibility: {str(e)}")
        return compatibility_analysis


def check_parameter_inconsistencies_within_passes(operation: adsk.cam.Operation, pass_config: dict) -> dict:
    """
    Check for parameter inconsistencies within passes.
    
    Identifies conflicting or inconsistent parameters within individual passes
    that could cause machining problems or unexpected results.
    
    Args:
        operation: The CAM operation
        pass_config: Pass configuration to validate
        
    Returns:
        dict: Parameter consistency analysis including:
            - consistent: Boolean indicating if parameters are consistent
            - inconsistencies: List of parameter inconsistencies found
            - pass_validation: Detailed validation for each pass
            - severity_levels: Categorization of issues by severity
            - correction_suggestions: Specific parameter corrections
    
    Requirements: 3.5
    """
    consistency_analysis = {
        "consistent": True,
        "inconsistencies": [],
        "pass_validation": [],
        "severity_levels": {
            "critical": [],
            "warning": [],
            "info": []
        },
        "correction_suggestions": []
    }
    
    try:
        if not operation or not pass_config:
            return consistency_analysis
        
        # Get operation parameters for reference
        params = operation.parameters if hasattr(operation, 'parameters') else None
        if not params:
            consistency_analysis["consistent"] = False
            consistency_analysis["inconsistencies"].append("Operation parameters not accessible")
            return consistency_analysis
        
        # Get tool information
        tool_data = _get_tool_data_from_operation(operation)
        tool_diameter = tool_data.get("diameter", 10.0)
        
        passes = pass_config.get("passes", [])
        
        for pass_info in passes:
            pass_validation = {
                "pass_number": pass_info.get("pass_number", 1),
                "pass_type": pass_info.get("pass_type", "unknown"),
                "consistent": True,
                "issues": []
            }
            
            # Check internal parameter consistency
            stock_to_leave = pass_info.get("stock_to_leave", {})
            radial_stock = stock_to_leave.get("radial", 0.0)
            axial_stock = stock_to_leave.get("axial", 0.0)
            depth = abs(pass_info.get("depth", 0.0))
            
            # Check stock to leave consistency
            if radial_stock < 0 or axial_stock < 0:
                issue = f"Pass {pass_validation['pass_number']}: Negative stock to leave values"
                pass_validation["consistent"] = False
                pass_validation["issues"].append(issue)
                consistency_analysis["inconsistencies"].append(issue)
                consistency_analysis["severity_levels"]["critical"].append(issue)
                consistency_analysis["consistent"] = False
            
            # Check if stock to leave is reasonable for pass type
            pass_type = pass_info.get("pass_type", "unknown")
            if pass_type == "finishing":
                if radial_stock > 0.1 or axial_stock > 0.1:
                    issue = f"Pass {pass_validation['pass_number']}: Finishing pass with significant stock to leave"
                    pass_validation["issues"].append(issue)
                    consistency_analysis["inconsistencies"].append(issue)
                    consistency_analysis["severity_levels"]["warning"].append(issue)
            
            elif pass_type == "roughing":
                if radial_stock == 0.0 and axial_stock == 0.0:
                    issue = f"Pass {pass_validation['pass_number']}: Roughing pass with no stock to leave for finishing"
                    pass_validation["issues"].append(issue)
                    consistency_analysis["inconsistencies"].append(issue)
                    consistency_analysis["severity_levels"]["warning"].append(issue)
            
            # Check depth vs stock to leave consistency
            if axial_stock > depth:
                issue = f"Pass {pass_validation['pass_number']}: Axial stock to leave ({axial_stock}mm) exceeds cutting depth ({depth}mm)"
                pass_validation["consistent"] = False
                pass_validation["issues"].append(issue)
                consistency_analysis["inconsistencies"].append(issue)
                consistency_analysis["severity_levels"]["critical"].append(issue)
                consistency_analysis["consistent"] = False
            
            # Check radial stock vs tool diameter
            if radial_stock > tool_diameter * 0.5:
                issue = f"Pass {pass_validation['pass_number']}: Radial stock to leave ({radial_stock}mm) is large relative to tool diameter ({tool_diameter}mm)"
                pass_validation["issues"].append(issue)
                consistency_analysis["inconsistencies"].append(issue)
                consistency_analysis["severity_levels"]["warning"].append(issue)
            
            # Check pass parameters against operation parameters
            pass_parameters = pass_info.get("parameters", {})
            if pass_parameters:
                # Check stepover consistency
                pass_stepover = pass_parameters.get("stepover")
                if pass_stepover is not None:
                    if pass_stepover <= 0 or pass_stepover > 100:
                        issue = f"Pass {pass_validation['pass_number']}: Invalid stepover value ({pass_stepover}%)"
                        pass_validation["consistent"] = False
                        pass_validation["issues"].append(issue)
                        consistency_analysis["inconsistencies"].append(issue)
                        consistency_analysis["severity_levels"]["critical"].append(issue)
                        consistency_analysis["consistent"] = False
                
                # Check stepdown consistency
                pass_stepdown = pass_parameters.get("stepdown")
                if pass_stepdown is not None:
                    if pass_stepdown <= 0:
                        issue = f"Pass {pass_validation['pass_number']}: Invalid stepdown value ({pass_stepdown}mm)"
                        pass_validation["consistent"] = False
                        pass_validation["issues"].append(issue)
                        consistency_analysis["inconsistencies"].append(issue)
                        consistency_analysis["severity_levels"]["critical"].append(issue)
                        consistency_analysis["consistent"] = False
                    
                    elif pass_stepdown > tool_diameter:
                        issue = f"Pass {pass_validation['pass_number']}: Stepdown ({pass_stepdown}mm) exceeds tool diameter ({tool_diameter}mm)"
                        pass_validation["issues"].append(issue)
                        consistency_analysis["inconsistencies"].append(issue)
                        consistency_analysis["severity_levels"]["warning"].append(issue)
                
                # Check feedrate consistency
                pass_feedrate = pass_parameters.get("feedrate")
                if pass_feedrate is not None:
                    if pass_feedrate <= 0:
                        issue = f"Pass {pass_validation['pass_number']}: Invalid feedrate value ({pass_feedrate}mm/min)"
                        pass_validation["consistent"] = False
                        pass_validation["issues"].append(issue)
                        consistency_analysis["inconsistencies"].append(issue)
                        consistency_analysis["severity_levels"]["critical"].append(issue)
                        consistency_analysis["consistent"] = False
            
            consistency_analysis["pass_validation"].append(pass_validation)
        
        # Check consistency across passes
        if len(passes) > 1:
            cross_pass_issues = _check_cross_pass_consistency(passes, tool_diameter)
            consistency_analysis["inconsistencies"].extend(cross_pass_issues["issues"])
            consistency_analysis["severity_levels"]["warning"].extend(cross_pass_issues["warnings"])
            if cross_pass_issues["critical"]:
                consistency_analysis["severity_levels"]["critical"].extend(cross_pass_issues["critical"])
                consistency_analysis["consistent"] = False
        
        # Generate correction suggestions
        consistency_analysis["correction_suggestions"] = _generate_parameter_correction_suggestions(
            consistency_analysis["inconsistencies"], consistency_analysis["severity_levels"], tool_data
        )
        
        return consistency_analysis
        
    except Exception as e:
        consistency_analysis["consistent"] = False
        consistency_analysis["inconsistencies"].append(f"Error checking parameter consistency: {str(e)}")
        return consistency_analysis


def provide_conflict_resolution_recommendations(conflict_analysis: dict, compatibility_analysis: dict, consistency_analysis: dict) -> dict:
    """
    Provide recommendations for conflict resolution.
    
    Combines results from conflict detection, compatibility validation, and
    consistency checking to provide comprehensive recommendations for resolving
    all identified issues.
    
    Args:
        conflict_analysis: Results from detect_pass_tool_conflicts
        compatibility_analysis: Results from validate_tool_compatibility_across_passes
        consistency_analysis: Results from check_parameter_inconsistencies_within_passes
        
    Returns:
        dict: Comprehensive conflict resolution recommendations including:
            - priority_actions: High-priority actions that must be taken
            - optimization_suggestions: Suggestions for improvement
            - parameter_adjustments: Specific parameter changes recommended
            - tool_recommendations: Tool selection or change recommendations
            - sequence_modifications: Pass sequence modification suggestions
    
    Requirements: 3.5
    """
    resolution_recommendations = {
        "priority_actions": [],
        "optimization_suggestions": [],
        "parameter_adjustments": [],
        "tool_recommendations": [],
        "sequence_modifications": []
    }
    
    try:
        # Process critical conflicts first
        if conflict_analysis.get("conflicts_found", False):
            critical_conflicts = conflict_analysis.get("critical_conflicts", [])
            for conflict in critical_conflicts:
                resolution_recommendations["priority_actions"].append({
                    "type": "critical_conflict",
                    "description": conflict,
                    "action": "Must be resolved before machining"
                })
        
        # Process compatibility issues
        if not compatibility_analysis.get("compatible", True):
            compatibility_issues = compatibility_analysis.get("compatibility_issues", [])
            for issue in compatibility_issues:
                resolution_recommendations["priority_actions"].append({
                    "type": "compatibility_issue",
                    "description": issue,
                    "action": "Review tool selection or pass parameters"
                })
        
        # Process consistency issues
        if not consistency_analysis.get("consistent", True):
            critical_inconsistencies = consistency_analysis.get("severity_levels", {}).get("critical", [])
            for inconsistency in critical_inconsistencies:
                resolution_recommendations["priority_actions"].append({
                    "type": "parameter_inconsistency",
                    "description": inconsistency,
                    "action": "Correct parameter values"
                })
        
        # Collect optimization suggestions
        optimization_sources = [
            conflict_analysis.get("recommendations", []),
            compatibility_analysis.get("tool_change_recommendations", []),
            compatibility_analysis.get("sequence_optimization", []),
            consistency_analysis.get("correction_suggestions", [])
        ]
        
        for source in optimization_sources:
            for suggestion in source:
                if isinstance(suggestion, str):
                    resolution_recommendations["optimization_suggestions"].append(suggestion)
                elif isinstance(suggestion, dict):
                    resolution_recommendations["optimization_suggestions"].append(suggestion.get("description", str(suggestion)))
        
        # Generate specific parameter adjustments
        parameter_adjustments = _generate_specific_parameter_adjustments(
            conflict_analysis, compatibility_analysis, consistency_analysis
        )
        resolution_recommendations["parameter_adjustments"] = parameter_adjustments
        
        # Generate tool recommendations
        tool_recommendations = _generate_specific_tool_recommendations(
            conflict_analysis, compatibility_analysis
        )
        resolution_recommendations["tool_recommendations"] = tool_recommendations
        
        # Generate sequence modifications
        sequence_modifications = _generate_specific_sequence_modifications(
            compatibility_analysis, consistency_analysis
        )
        resolution_recommendations["sequence_modifications"] = sequence_modifications
        
        return resolution_recommendations
        
    except Exception as e:
        resolution_recommendations["priority_actions"].append({
            "type": "error",
            "description": f"Error generating conflict resolution recommendations: {str(e)}",
            "action": "Review analysis results manually"
        })
        return resolution_recommendations


# Helper functions for conflict detection

def _check_tool_operation_compatibility(tool_type: str, operation_type: str, pass_type: str) -> list:
    """
    Check compatibility between tool type and operation/pass type.
    
    Args:
        tool_type: Type of tool (end mill, drill, etc.)
        operation_type: Type of operation (pocket, contour, etc.)
        pass_type: Type of pass (roughing, finishing, etc.)
        
    Returns:
        list: List of compatibility warnings
    """
    warnings = []
    
    try:
        tool_type_lower = tool_type.lower()
        operation_type_lower = operation_type.lower()
        pass_type_lower = pass_type.lower()
        
        # Check drill tools in non-drilling operations
        if "drill" in tool_type_lower and "drill" not in operation_type_lower:
            warnings.append(f"Drill tool used in {operation_type} operation - may not be optimal")
        
        # Check end mills in drilling operations
        if "mill" in tool_type_lower and "drill" in operation_type_lower:
            warnings.append("End mill used in drilling operation - consider drill tool")
        
        # Check ball mills for roughing
        if "ball" in tool_type_lower and pass_type_lower == "roughing":
            warnings.append("Ball mill used for roughing - may be inefficient for material removal")
        
        # Check flat mills for finishing curved surfaces
        if ("flat" in tool_type_lower or "square" in tool_type_lower) and pass_type_lower == "finishing":
            if "3d" in operation_type_lower or "surface" in operation_type_lower:
                warnings.append("Flat end mill for 3D finishing - consider ball mill for better surface quality")
        
    except Exception:
        pass
    
    return warnings


def _generate_conflict_resolution_recommendations(critical_conflicts: list, tool_data: dict, passes: list) -> list:
    """
    Generate recommendations for resolving critical conflicts.
    
    Args:
        critical_conflicts: List of critical conflict descriptions
        tool_data: Tool information
        passes: List of pass configurations
        
    Returns:
        list: List of resolution recommendations
    """
    recommendations = []
    
    try:
        tool_diameter = tool_data.get("diameter", 10.0)
        
        for conflict in critical_conflicts:
            if "cutting depth" in conflict.lower() and "tool length" in conflict.lower():
                recommendations.append("Reduce cutting depth or use longer tool")
                recommendations.append("Consider multiple passes with smaller stepdowns")
            
            elif "stepover" in conflict.lower() and "tool diameter" in conflict.lower():
                recommendations.append(f"Reduce stepover to maximum {tool_diameter * 0.8:.1f}mm")
                recommendations.append("Consider using larger diameter tool if possible")
            
            elif "stock to leave" in conflict.lower():
                recommendations.append("Correct stock to leave progression between passes")
                recommendations.append("Ensure finishing passes have minimal stock to leave")
        
        # General recommendations based on number of conflicts
        if len(critical_conflicts) > 3:
            recommendations.append("Multiple critical conflicts detected - consider redesigning pass strategy")
        
    except Exception:
        pass
    
    return recommendations


def _generate_warning_recommendations(warnings: list, tool_data: dict) -> list:
    """
    Generate recommendations for addressing warnings.
    
    Args:
        warnings: List of warning descriptions
        tool_data: Tool information
        
    Returns:
        list: List of recommendations for warnings
    """
    recommendations = []
    
    try:
        for warning in warnings:
            if "high feedrate" in warning.lower() and "finishing" in warning.lower():
                recommendations.append("Reduce feedrate for finishing passes to improve surface quality")
            
            elif "low feedrate" in warning.lower() and "roughing" in warning.lower():
                recommendations.append("Increase feedrate for roughing passes to improve efficiency")
            
            elif "high surface speed" in warning.lower():
                recommendations.append("Reduce spindle speed or verify tool specifications")
            
            elif "stock to leave" in warning.lower() and "finishing" in warning.lower():
                recommendations.append("Remove stock to leave from finishing passes")
        
    except Exception:
        pass
    
    return recommendations


def _generate_tool_change_recommendations(passes: list, tool_data: dict, compatibility_issues: list) -> list:
    """
    Generate tool change recommendations based on compatibility issues.
    
    Args:
        passes: List of pass configurations
        tool_data: Current tool information
        compatibility_issues: List of compatibility issues
        
    Returns:
        list: List of tool change recommendations
    """
    recommendations = []
    
    try:
        tool_diameter = tool_data.get("diameter", 10.0)
        
        # Analyze pass types
        roughing_passes = [p for p in passes if p.get("pass_type") == "roughing"]
        finishing_passes = [p for p in passes if p.get("pass_type") == "finishing"]
        
        if roughing_passes and finishing_passes:
            if tool_diameter < 6.0:
                recommendations.append("Consider larger tool for roughing passes, then change to current tool for finishing")
            elif tool_diameter > 15.0:
                recommendations.append("Consider smaller tool for finishing passes to improve precision")
        
        # Check for specific compatibility issues
        for issue in compatibility_issues:
            if "tool too small" in issue.lower():
                recommendations.append("Use larger diameter tool for roughing operations")
            elif "large tool" in issue.lower() and "finishing" in issue.lower():
                recommendations.append("Change to smaller tool for finishing operations")
        
    except Exception:
        pass
    
    return recommendations


def _generate_sequence_optimization_recommendations(passes: list, tool_data: dict, pass_analysis: list) -> list:
    """
    Generate pass sequence optimization recommendations.
    
    Args:
        passes: List of pass configurations
        tool_data: Tool information
        pass_analysis: Analysis results for each pass
        
    Returns:
        list: List of sequence optimization recommendations
    """
    recommendations = []
    
    try:
        # Check for stock to leave progression issues
        stock_progression_issues = [p for p in pass_analysis if "stock to leave progression" in str(p.get("issues", []))]
        if stock_progression_issues:
            recommendations.append("Reorder passes to ensure decreasing stock to leave progression")
        
        # Check for tool suitability issues
        unsuitable_passes = [p for p in pass_analysis if not p.get("tool_suitable", True)]
        if len(unsuitable_passes) > 1:
            recommendations.append("Consider splitting passes between multiple tools")
        
        # Check for excessive material removal
        excessive_removal_passes = [p for p in pass_analysis if "excessive material removal" in str(p.get("issues", []))]
        if excessive_removal_passes:
            recommendations.append("Add intermediate passes to reduce material removal per pass")
        
    except Exception:
        pass
    
    return recommendations


def _check_cross_pass_consistency(passes: list, tool_diameter: float) -> dict:
    """
    Check consistency across multiple passes.
    
    Args:
        passes: List of pass configurations
        tool_diameter: Tool diameter in mm
        
    Returns:
        dict: Cross-pass consistency analysis
    """
    analysis = {
        "issues": [],
        "warnings": [],
        "critical": []
    }
    
    try:
        # Check stock to leave progression
        for i in range(1, len(passes)):
            current_pass = passes[i]
            previous_pass = passes[i - 1]
            
            current_radial = current_pass.get("stock_to_leave", {}).get("radial", 0.0)
            previous_radial = previous_pass.get("stock_to_leave", {}).get("radial", 0.0)
            
            if current_radial > previous_radial:
                analysis["critical"].append(f"Pass {i + 1}: Stock to leave increases from previous pass")
        
        # Check depth progression
        depths = [abs(p.get("depth", 0.0)) for p in passes]
        if len(set(depths)) == 1 and len(passes) > 1:
            analysis["warnings"].append("All passes have same depth - consider varying depths for efficiency")
        
        # Check pass type sequence
        pass_types = [p.get("pass_type", "unknown") for p in passes]
        if "finishing" in pass_types and "roughing" in pass_types:
            finishing_index = pass_types.index("finishing")
            roughing_indices = [i for i, pt in enumerate(pass_types) if pt == "roughing"]
            
            if any(ri > finishing_index for ri in roughing_indices):
                analysis["warnings"].append("Roughing pass after finishing pass - consider reordering")
        
    except Exception:
        pass
    
    return analysis


def _generate_parameter_correction_suggestions(inconsistencies: list, severity_levels: dict, tool_data: dict) -> list:
    """
    Generate specific parameter correction suggestions.
    
    Args:
        inconsistencies: List of inconsistency descriptions
        severity_levels: Categorized severity levels
        tool_data: Tool information
        
    Returns:
        list: List of specific correction suggestions
    """
    suggestions = []
    
    try:
        tool_diameter = tool_data.get("diameter", 10.0)
        
        # Handle critical issues first
        for critical in severity_levels.get("critical", []):
            if "negative stock to leave" in critical.lower():
                suggestions.append("Set all stock to leave values to positive numbers")
            
            elif "exceeds cutting depth" in critical.lower():
                suggestions.append("Reduce axial stock to leave to be less than cutting depth")
            
            elif "invalid stepover" in critical.lower():
                suggestions.append("Set stepover between 10% and 90%")
            
            elif "invalid stepdown" in critical.lower():
                suggestions.append(f"Set stepdown between 0.1mm and {tool_diameter * 0.5:.1f}mm")
            
            elif "invalid feedrate" in critical.lower():
                suggestions.append("Set feedrate to positive value (typically 500-3000 mm/min)")
        
        # Handle warnings
        for warning in severity_levels.get("warning", []):
            if "large relative to tool diameter" in warning.lower():
                suggestions.append(f"Consider reducing radial stock to leave to less than {tool_diameter * 0.3:.1f}mm")
            
            elif "finishing pass with significant stock" in warning.lower():
                suggestions.append("Reduce stock to leave in finishing passes to 0.05mm or less")
            
            elif "roughing pass with no stock" in warning.lower():
                suggestions.append("Add 0.2-0.5mm radial stock to leave for roughing passes")
        
    except Exception:
        pass
    
    return suggestions


def _generate_specific_parameter_adjustments(conflict_analysis: dict, compatibility_analysis: dict, consistency_analysis: dict) -> list:
    """
    Generate specific parameter adjustment recommendations.
    
    Args:
        conflict_analysis: Conflict detection results
        compatibility_analysis: Compatibility validation results
        consistency_analysis: Consistency checking results
        
    Returns:
        list: List of specific parameter adjustments
    """
    adjustments = []
    
    try:
        # Extract tool compatibility issues
        tool_compatibility = conflict_analysis.get("tool_compatibility", [])
        for pass_compat in tool_compatibility:
            if not pass_compat.get("compatible", True):
                pass_num = pass_compat.get("pass_number", 1)
                issues = pass_compat.get("issues", [])
                
                for issue in issues:
                    if "excessive cutting depth" in issue.lower():
                        adjustments.append(f"Pass {pass_num}: Reduce cutting depth by 50%")
                    elif "stepover exceeds" in issue.lower():
                        adjustments.append(f"Pass {pass_num}: Reduce stepover to 60% or less")
        
        # Extract consistency issues
        pass_validation = consistency_analysis.get("pass_validation", [])
        for pass_val in pass_validation:
            if not pass_val.get("consistent", True):
                pass_num = pass_val.get("pass_number", 1)
                issues = pass_val.get("issues", [])
                
                for issue in issues:
                    if "negative stock to leave" in issue.lower():
                        adjustments.append(f"Pass {pass_num}: Set stock to leave values to 0 or positive")
                    elif "invalid stepover" in issue.lower():
                        adjustments.append(f"Pass {pass_num}: Set stepover between 20-80%")
        
    except Exception:
        pass
    
    return adjustments


def _generate_specific_tool_recommendations(conflict_analysis: dict, compatibility_analysis: dict) -> list:
    """
    Generate specific tool selection recommendations.
    
    Args:
        conflict_analysis: Conflict detection results
        compatibility_analysis: Compatibility validation results
        
    Returns:
        list: List of specific tool recommendations
    """
    recommendations = []
    
    try:
        # Check for tool size issues
        critical_conflicts = conflict_analysis.get("critical_conflicts", [])
        for conflict in critical_conflicts:
            if "tool too small" in conflict.lower():
                recommendations.append("Use tool with diameter ≥ 6mm for roughing operations")
            elif "large tool" in conflict.lower() and "finishing" in conflict.lower():
                recommendations.append("Use tool with diameter ≤ 10mm for finishing operations")
        
        # Check compatibility recommendations
        tool_change_recs = compatibility_analysis.get("tool_change_recommendations", [])
        recommendations.extend(tool_change_recs)
        
    except Exception:
        pass
    
    return recommendations


def _generate_specific_sequence_modifications(compatibility_analysis: dict, consistency_analysis: dict) -> list:
    """
    Generate specific pass sequence modification recommendations.
    
    Args:
        compatibility_analysis: Compatibility validation results
        consistency_analysis: Consistency checking results
        
    Returns:
        list: List of specific sequence modifications
    """
    modifications = []
    
    try:
        # Check sequence optimization recommendations
        sequence_opts = compatibility_analysis.get("sequence_optimization", [])
        modifications.extend(sequence_opts)
        
        # Check for cross-pass consistency issues
        inconsistencies = consistency_analysis.get("inconsistencies", [])
        for inconsistency in inconsistencies:
            if "stock to leave progression" in inconsistency.lower():
                modifications.append("Reorder passes to ensure each pass leaves less stock than the previous")
            elif "roughing pass after finishing" in inconsistency.lower():
                modifications.append("Move all roughing passes before finishing passes")
        
    except Exception:
        pass
    
    return modifications
