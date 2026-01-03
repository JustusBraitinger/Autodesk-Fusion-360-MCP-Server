"""
Height Parameter Management Handler

Handles height parameter management for CAM operations.
Contains actual business logic for height parameters (extracted from cam.py).
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
    get_operation_type
)

# Set up logging
logger = logging.getLogger(__name__)


# =============================================================================
# Height Validation Functions
# =============================================================================

def validate_height_value(param_name: str, value: Any, operation: adsk.cam.Operation = None) -> dict:
    """Validate a height parameter value against Fusion 360 constraints."""
    try:
        converted_value = value
        if isinstance(value, str):
            try:
                if '.' in value:
                    converted_value = float(value)
                else:
                    converted_value = int(value)
            except ValueError:
                pass
        
        if not isinstance(converted_value, (int, float, str)):
            return {
                "valid": False,
                "message": f"Height parameter '{param_name}' must be numeric or expression",
                "code": "INVALID_TYPE",
                "converted_value": value
            }
        
        if isinstance(converted_value, (int, float)):
            if converted_value < -10000 or converted_value > 10000:
                return {
                    "valid": False,
                    "message": f"Height value {converted_value} is outside reasonable range",
                    "code": "VALUE_OUT_OF_RANGE",
                    "converted_value": converted_value
                }
        
        return {
            "valid": True,
            "message": f"Height parameter '{param_name}' value is valid",
            "code": "VALID",
            "converted_value": converted_value
        }
        
    except Exception as e:
        return {
            "valid": False,
            "message": f"Error validating height parameter: {str(e)}",
            "code": "VALIDATION_ERROR",
            "converted_value": value
        }


def validate_height_hierarchy(height_values: dict, operation: adsk.cam.Operation = None) -> dict:
    """Validate height hierarchy rules (clearance > retract > feed)."""
    violations = []
    
    try:
        clearance = height_values.get('clearance_height')
        retract = height_values.get('retract_height')
        feed = height_values.get('feed_height')
        
        if clearance is not None and retract is not None:
            if isinstance(clearance, (int, float)) and isinstance(retract, (int, float)):
                if clearance <= retract:
                    violations.append({
                        "rule": "clearance_above_retract",
                        "message": f"Clearance height ({clearance}) must be above retract height ({retract})"
                    })
        
        if retract is not None and feed is not None:
            if isinstance(retract, (int, float)) and isinstance(feed, (int, float)):
                if retract <= feed:
                    violations.append({
                        "rule": "retract_above_feed",
                        "message": f"Retract height ({retract}) must be above feed height ({feed})"
                    })
        
        return {
            "valid": len(violations) == 0,
            "message": "Height hierarchy is valid" if len(violations) == 0 else "Height hierarchy violations found",
            "code": "VALID" if len(violations) == 0 else "HIERARCHY_VIOLATION",
            "violations": violations
        }
        
    except Exception as e:
        return {
            "valid": False,
            "message": f"Error validating height hierarchy: {str(e)}",
            "code": "VALIDATION_ERROR",
            "violations": []
        }


# =============================================================================
# Business Logic Functions (extracted from cam.py)
# =============================================================================

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
                            elif hasattr(param.value, 'isReadOnly'):
                                param_data["editable"] = not param.value.isReadOnly
                        except Exception:
                            param_data["editable"] = True
                        
                        try:
                            if hasattr(param, 'minimumValue') and param.minimumValue is not None:
                                param_data["min_value"] = param.minimumValue
                        except Exception:
                            pass
                        
                        try:
                            if hasattr(param, 'maximumValue') and param.maximumValue is not None:
                                param_data["max_value"] = param.maximumValue
                        except Exception:
                            pass
                        
                        heights[output_name] = param_data
                        
                except Exception:
                    continue
        
    except Exception:
        pass
    
    return heights


def get_detailed_heights_impl(cam: adsk.cam.CAM = None, toolpath_id: str = None) -> dict:
    """Extract comprehensive height information for a single toolpath."""
    if cam is None:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        cam = validation["cam_product"]
    
    if not toolpath_id:
        return {
            "error": True,
            "message": "Toolpath ID is required",
            "code": "MISSING_TOOLPATH_ID"
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
        try:
            if hasattr(operation, 'parentSetup') and operation.parentSetup:
                setup_name = operation.parentSetup.name
        except Exception:
            setup_name = "Unknown Setup"
        
        heights_data = _extract_heights_params(operation)
        
        result = {
            "id": toolpath_id,
            "name": operation.name,
            "type": get_operation_type(operation),
            "setup_name": setup_name,
            "heights": heights_data
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error extracting detailed heights: {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


# =============================================================================
# HTTP Handler Functions
# =============================================================================

def handle_get_detailed_heights(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comprehensive height information for a single toolpath."""
    try:
        toolpath_id = data.get("toolpath_id")
        if not toolpath_id:
            return {
                "status": 400,
                "error": True,
                "message": "toolpath_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        result = get_detailed_heights_impl(toolpath_id=toolpath_id)
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_get_detailed_heights: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_operation_heights(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get height parameters for a specific operation."""
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
                heights_data = _extract_heights_params(operation)
                result = {
                    "operation_id": operation_id,
                    "operation_name": operation.name,
                    "heights": heights_data
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
        logger.error(f"Error in handle_get_operation_heights: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_modify_height_parameter(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Modify a specific height parameter for an operation."""
    try:
        operation_id = data.get("operation_id")
        parameter_name = data.get("parameter_name")
        new_value = data.get("new_value")
        
        if not operation_id:
            return {
                "status": 400,
                "error": True,
                "message": "operation_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        if not parameter_name:
            return {
                "status": 400,
                "error": True,
                "message": "parameter_name parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        if new_value is None:
            return {
                "status": 400,
                "error": True,
                "message": "new_value parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        return {
            "status": 501,
            "error": True,
            "message": "Height parameter modification not yet implemented",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_modify_height_parameter: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_validate_height_values(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate height parameter values for safety and constraints."""
    try:
        operation_id = data.get("operation_id")
        height_values = data.get("height_values", {})
        
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
                current_heights = _extract_heights_params(operation)
                
                validation_results = {
                    "operation_id": operation_id,
                    "valid": True,
                    "issues": [],
                    "warnings": []
                }
                
                for param_name, new_value in height_values.items():
                    if param_name in current_heights:
                        param_info = current_heights[param_name]
                        
                        if not param_info.get("editable", True):
                            validation_results["issues"].append({
                                "parameter": param_name,
                                "issue": "Parameter is read-only",
                                "severity": "error"
                            })
                            validation_results["valid"] = False
                        
                        min_val = param_info.get("min_value")
                        max_val = param_info.get("max_value")
                        
                        if min_val is not None and new_value < min_val:
                            validation_results["issues"].append({
                                "parameter": param_name,
                                "issue": f"Value {new_value} is below minimum {min_val}",
                                "severity": "error"
                            })
                            validation_results["valid"] = False
                        
                        if max_val is not None and new_value > max_val:
                            validation_results["issues"].append({
                                "parameter": param_name,
                                "issue": f"Value {new_value} is above maximum {max_val}",
                                "severity": "error"
                            })
                            validation_results["valid"] = False
                    else:
                        validation_results["warnings"].append({
                            "parameter": param_name,
                            "warning": "Parameter not found in operation",
                            "severity": "warning"
                        })
                
                clearance = height_values.get("clearance_height")
                retract = height_values.get("retract_height")
                feed = height_values.get("feed_height")
                
                if clearance and retract and clearance <= retract:
                    validation_results["issues"].append({
                        "parameter": "clearance_height",
                        "issue": "Clearance height should be greater than retract height",
                        "severity": "warning"
                    })
                
                if retract and feed and retract <= feed:
                    validation_results["issues"].append({
                        "parameter": "retract_height",
                        "issue": "Retract height should be greater than feed height",
                        "severity": "warning"
                    })
                
                result = validation_results
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
        logger.error(f"Error in handle_validate_height_values: {str(e)}")
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
    """Register all height parameter handlers with the request router"""
    try:
        request_router.register_handler(
            "/cam/toolpaths/{toolpath_id}/heights",
            handle_get_detailed_heights,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.heights"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/heights",
            handle_get_operation_heights,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.heights"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/heights/{parameter_name}",
            handle_modify_height_parameter,
            methods=["PUT"],
            category="manufacture",
            module_name="manufacture.operations.heights"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/heights/validate",
            handle_validate_height_values,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.operations.heights"
        )
        
        logger.info("Registered height parameter handlers")
        
    except Exception as e:
        logger.error(f"Error registering height parameter handlers: {str(e)}")


register_handlers()
