"""
CAM Utilities Module

Shared utility functions for CAM operations used across MANUFACTURE handler modules.
This module contains common functions for accessing CAM products, finding operations,
and extracting parameter metadata.
"""

import adsk.core
import adsk.cam
from typing import Optional, Any


def get_cam_product() -> Optional[adsk.cam.CAM]:
    """
    Safely access the CAM product from the active Fusion 360 document.
    
    Returns:
        adsk.cam.CAM | None: The CAM product if available, None if no CAM data exists
        or if the document doesn't support CAM operations.
    """
    try:
        app = adsk.core.Application.get()
        if not app:
            return None
            
        doc = app.activeDocument
        if not doc:
            return None
        
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
    
    Returns:
        dict: Validation result with error details or success confirmation
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
        
        doc = app.activeDocument
        if not doc:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "No active document found. Please open a Fusion 360 document with CAM data",
                "code": "NO_DOCUMENT"
            }
        
        products = doc.products
        if not products:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "Document does not support CAM operations",
                "code": "NO_PRODUCTS"
            }
        
        cam_product = products.itemByProductType('CAMProductType')
        if not cam_product:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "No CAM data present. Please switch to MANUFACTURE workspace",
                "code": "NO_CAM_DATA"
            }
        
        cam_instance = adsk.cam.CAM.cast(cam_product)
        if not cam_instance:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "CAM product cannot be accessed",
                "code": "CAM_ACCESS_ERROR"
            }
        
        try:
            setups = cam_instance.setups
            if not setups:
                return {
                    "valid": False,
                    "cam_product": None,
                    "error": True,
                    "message": "CAM product has no setups. Please create a CAM setup",
                    "code": "NO_CAM_SETUPS"
                }
        except Exception:
            return {
                "valid": False,
                "cam_product": None,
                "error": True,
                "message": "CAM product not properly initialized",
                "code": "CAM_NOT_INITIALIZED"
            }
        
        return {
            "valid": True,
            "cam_product": cam_instance,
            "error": False,
            "message": "CAM product is available",
            "code": "SUCCESS"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "cam_product": None,
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "code": "VALIDATION_ERROR"
        }


def find_operation_by_id(cam: adsk.cam.CAM, toolpath_id: str) -> Optional[adsk.cam.Operation]:
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


def find_setup_by_id(cam: adsk.cam.CAM, setup_id: str) -> Optional[adsk.cam.Setup]:
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


def get_operation_type(operation: adsk.cam.Operation) -> str:
    """
    Get the operation type as a string.
    
    Args:
        operation: The CAM operation
        
    Returns:
        str: The operation type name
    """
    try:
        if hasattr(operation, 'strategy') and operation.strategy:
            return operation.strategy
        return "unknown"
    except Exception:
        return "unknown"


def get_tool_type_string(tool) -> str:
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


def get_param_value(param) -> Any:
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


def get_parameter_metadata(param) -> dict:
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
        
        if hasattr(param, 'expression'):
            metadata["type"] = "numeric"
            metadata["expression"] = param.expression
        
        if hasattr(param, 'unit') and param.unit:
            metadata["unit"] = param.unit
        
        if hasattr(param, 'isReadOnly'):
            metadata["editable"] = not param.isReadOnly
        
        if hasattr(param, 'minimumValue'):
            metadata["min"] = param.minimumValue
        if hasattr(param, 'maximumValue'):
            metadata["max"] = param.maximumValue
        
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
