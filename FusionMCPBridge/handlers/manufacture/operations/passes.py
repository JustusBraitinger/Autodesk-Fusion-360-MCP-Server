"""
Multi-Pass Configuration Handler

Handles multi-pass configuration for CAM operations.
Contains actual business logic for pass configuration (extracted from cam.py).
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
# Business Logic Functions (extracted from cam.py)
# =============================================================================

def _extract_pass_params(operation: adsk.cam.Operation) -> dict:
    """Extract multi-pass configuration from an operation."""
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
        
        multiple_depths_enabled = False
        finishing_passes_enabled = False
        spring_passes_count = 0

        try:
            multiple_depths_param = params.itemByName("multipleDepths")
            if multiple_depths_param and hasattr(multiple_depths_param, 'value'):
                multiple_depths_enabled = multiple_depths_param.value
        except Exception:
            pass
        
        try:
            finishing_param = params.itemByName("useFinishingPasses")
            if finishing_param and hasattr(finishing_param, 'value'):
                finishing_passes_enabled = finishing_param.value
        except Exception:
            pass
        
        try:
            spring_param = params.itemByName("springPasses")
            if spring_param and hasattr(spring_param, 'value'):
                spring_passes_count = spring_param.value if isinstance(spring_param.value, int) else 0
        except Exception:
            pass
        
        maximum_stepdown = None
        finishing_stepdown = None
        stock_to_leave_radial = 0.0
        stock_to_leave_axial = 0.0
        
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
        
        if multiple_depths_enabled:
            pass_config["pass_type"] = "multiple_depths"
        elif finishing_passes_enabled:
            pass_config["pass_type"] = "finishing"
        
        pass_config["spring_passes"] = spring_passes_count
        pass_config["finishing_enabled"] = finishing_passes_enabled
        
        passes = []
        
        if multiple_depths_enabled and maximum_stepdown:
            passes.append({
                "pass_number": 1,
                "pass_type": "roughing",
                "depth": maximum_stepdown,
                "stock_to_leave": stock_to_leave_radial,
                "parameters": {
                    "stepover": stepover,
                    "radial_stock": stock_to_leave_radial,
                    "axial_stock": stock_to_leave_axial
                }
            })
        
        if finishing_passes_enabled:
            passes.append({
                "pass_number": len(passes) + 1,
                "pass_type": "finishing",
                "depth": finishing_stepdown,
                "stock_to_leave": 0,
                "parameters": {
                    "stepover": finishing_stepover
                }
            })
        
        if not passes:
            passes.append({
                "pass_number": 1,
                "pass_type": "single",
                "depth": maximum_stepdown,
                "stock_to_leave": stock_to_leave_radial,
                "parameters": {
                    "stepover": stepover
                }
            })
        
        pass_config["passes"] = passes
        pass_config["total_passes"] = len(passes) + spring_passes_count
        
        return pass_config
        
    except Exception:
        return pass_config


# =============================================================================
# HTTP Handler Functions
# =============================================================================

def handle_get_toolpath_passes(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get multi-pass configuration for a specific toolpath."""
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
            operation = find_operation_by_id(cam, toolpath_id)
            if operation:
                pass_config = _extract_pass_params(operation)
                result = {
                    "toolpath_id": toolpath_id,
                    "toolpath_name": operation.name,
                    "pass_configuration": pass_config
                }
            else:
                result = {
                    "error": True,
                    "message": f"Toolpath with ID '{toolpath_id}' not found",
                    "code": "TOOLPATH_NOT_FOUND"
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
        logger.error(f"Error in handle_get_toolpath_passes: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_modify_toolpath_passes(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Modify multi-pass configuration for a toolpath."""
    try:
        toolpath_id = data.get("toolpath_id")
        if not toolpath_id:
            return {
                "status": 400,
                "error": True,
                "message": "toolpath_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        return {
            "status": 501,
            "error": True,
            "message": "Pass configuration modification not yet implemented",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_modify_toolpath_passes: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_operation_passes(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get pass configuration for a specific operation."""
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
                pass_config = _extract_pass_params(operation)
                result = {
                    "operation_id": operation_id,
                    "operation_name": operation.name,
                    "pass_configuration": pass_config
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
        logger.error(f"Error in handle_get_operation_passes: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_validate_pass_configuration(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pass configuration parameters for an operation."""
    try:
        operation_id = data.get("operation_id")
        pass_config = data.get("pass_config", {})
        
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
                validation_results = {
                    "operation_id": operation_id,
                    "valid": True,
                    "issues": [],
                    "warnings": []
                }
                
                total_passes = pass_config.get("total_passes", 1)
                if total_passes < 1:
                    validation_results["issues"].append({
                        "parameter": "total_passes",
                        "issue": "Total passes must be at least 1",
                        "severity": "error"
                    })
                    validation_results["valid"] = False
                
                if total_passes > 10:
                    validation_results["warnings"].append({
                        "parameter": "total_passes",
                        "warning": "Large number of passes may increase machining time",
                        "severity": "warning"
                    })
                
                spring_passes = pass_config.get("spring_passes", 0)
                if spring_passes < 0:
                    validation_results["issues"].append({
                        "parameter": "spring_passes",
                        "issue": "Spring passes cannot be negative",
                        "severity": "error"
                    })
                    validation_results["valid"] = False
                
                if "passes" in pass_config:
                    for i, pass_info in enumerate(pass_config["passes"]):
                        pass_depth = pass_info.get("depth")
                        if pass_depth is not None and pass_depth <= 0:
                            validation_results["issues"].append({
                                "parameter": f"passes[{i}].depth",
                                "issue": "Pass depth must be positive",
                                "severity": "error"
                            })
                            validation_results["valid"] = False
                
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
        logger.error(f"Error in handle_validate_pass_configuration: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_optimize_pass_sequence(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Provide optimization recommendations for pass sequence."""
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
                pass_config = _extract_pass_params(operation)
                operation_type = get_operation_type(operation)
                
                recommendations = {
                    "operation_id": operation_id,
                    "operation_type": operation_type,
                    "current_passes": pass_config.get("total_passes", 1),
                    "recommendations": []
                }
                
                if pass_config.get("total_passes", 1) == 1:
                    if "adaptive" in operation_type.lower() or "pocket" in operation_type.lower():
                        recommendations["recommendations"].append({
                            "type": "multiple_passes",
                            "description": "Consider using multiple depth passes for better surface finish",
                            "benefit": "Improved surface quality and reduced tool wear"
                        })
                
                if not pass_config.get("finishing_enabled", False):
                    if "contour" in operation_type.lower() or "pocket" in operation_type.lower():
                        recommendations["recommendations"].append({
                            "type": "finishing_pass",
                            "description": "Add a finishing pass for better surface quality",
                            "benefit": "Improved surface finish and dimensional accuracy"
                        })
                
                result = recommendations
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
        logger.error(f"Error in handle_optimize_pass_sequence: {str(e)}")
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
    """Register all pass configuration handlers with the request router"""
    try:
        request_router.register_handler(
            "/cam/toolpaths/{toolpath_id}/passes",
            handle_get_toolpath_passes,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.passes"
        )
        
        request_router.register_handler(
            "/cam/toolpaths/{toolpath_id}/passes",
            handle_modify_toolpath_passes,
            methods=["PUT"],
            category="manufacture",
            module_name="manufacture.operations.passes"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/passes",
            handle_get_operation_passes,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.passes"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/passes/validate",
            handle_validate_pass_configuration,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.operations.passes"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/passes/optimize",
            handle_optimize_pass_sequence,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.passes"
        )
        
        logger.info("Registered pass configuration handlers")
        
    except Exception as e:
        logger.error(f"Error registering pass configuration handlers: {str(e)}")


register_handlers()
