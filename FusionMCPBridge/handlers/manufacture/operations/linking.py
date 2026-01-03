"""
Linking Parameter Management Handler

Handles linking parameter management for CAM operations.
Contains actual business logic for linking parameters (extracted from cam.py).
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
    get_param_value
)

# Set up logging
logger = logging.getLogger(__name__)


# =============================================================================
# Business Logic Functions (extracted from cam.py)
# =============================================================================

def _extract_2d_linking_params(params, linking_config: dict) -> dict:
    """Extract linking parameters for 2D operations (Pocket, etc.)."""
    try:
        leads_transitions = {}
        
        lead_in = {}
        try:
            lead_in_type_param = params.itemByName("leadInType")
            if lead_in_type_param:
                lead_in["type"] = get_param_value(lead_in_type_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_in.type")
        except Exception:
            pass
        
        try:
            lead_in_radius_param = params.itemByName("leadInRadius")
            if lead_in_radius_param:
                lead_in["arc_radius"] = get_param_value(lead_in_radius_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_in.arc_radius")
        except Exception:
            pass
        
        lead_out = {}
        try:
            lead_out_type_param = params.itemByName("leadOutType")
            if lead_out_type_param:
                lead_out["type"] = get_param_value(lead_out_type_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_out.type")
        except Exception:
            pass
        
        try:
            lead_out_radius_param = params.itemByName("leadOutRadius")
            if lead_out_radius_param:
                lead_out["arc_radius"] = get_param_value(lead_out_radius_param)
                linking_config["editable_parameters"].append("leads_and_transitions.lead_out.arc_radius")
        except Exception:
            pass
        
        transitions = {}
        try:
            transition_type_param = params.itemByName("transitionType")
            if transition_type_param:
                transitions["type"] = get_param_value(transition_type_param)
                linking_config["editable_parameters"].append("leads_and_transitions.transitions.type")
        except Exception:
            pass
        
        try:
            lift_height_param = params.itemByName("liftHeight")
            if lift_height_param:
                transitions["lift_height"] = get_param_value(lift_height_param)
                linking_config["editable_parameters"].append("leads_and_transitions.transitions.lift_height")
        except Exception:
            pass
        
        if lead_in:
            leads_transitions["lead_in"] = lead_in
        if lead_out:
            leads_transitions["lead_out"] = lead_out
        if transitions:
            leads_transitions["transitions"] = transitions
        
        if leads_transitions:
            linking_config["sections"]["leads_and_transitions"] = leads_transitions
        
    except Exception:
        pass
    
    return linking_config


def _extract_3d_linking_params(params, linking_config: dict) -> dict:
    """Extract linking parameters for 3D operations."""
    try:
        linking_section = {}
        
        approach = {}
        try:
            approach_type_param = params.itemByName("approachType")
            if approach_type_param:
                approach["type"] = get_param_value(approach_type_param)
                linking_config["editable_parameters"].append("linking.approach.type")
        except Exception:
            pass
        
        try:
            approach_distance_param = params.itemByName("approachDistance")
            if approach_distance_param:
                approach["distance"] = get_param_value(approach_distance_param)
                linking_config["editable_parameters"].append("linking.approach.distance")
        except Exception:
            pass
        
        retract = {}
        try:
            retract_type_param = params.itemByName("retractType")
            if retract_type_param:
                retract["type"] = get_param_value(retract_type_param)
                linking_config["editable_parameters"].append("linking.retract.type")
        except Exception:
            pass
        
        try:
            retract_distance_param = params.itemByName("retractDistance")
            if retract_distance_param:
                retract["distance"] = get_param_value(retract_distance_param)
                linking_config["editable_parameters"].append("linking.retract.distance")
        except Exception:
            pass
        
        if approach:
            linking_section["approach"] = approach
        if retract:
            linking_section["retract"] = retract
        
        if linking_section:
            linking_config["sections"]["linking"] = linking_section
        
        transitions = {}
        try:
            stay_down_distance_param = params.itemByName("stayDownDistance")
            if stay_down_distance_param:
                transitions["stay_down_distance"] = get_param_value(stay_down_distance_param)
                linking_config["editable_parameters"].append("transitions.stay_down_distance")
        except Exception:
            pass
        
        try:
            lift_height_param = params.itemByName("liftHeight")
            if lift_height_param:
                transitions["lift_height"] = get_param_value(lift_height_param)
                linking_config["editable_parameters"].append("transitions.lift_height")
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
        drill_cycle = {}
        try:
            cycle_type_param = params.itemByName("cycleType")
            if cycle_type_param:
                drill_cycle["cycle_type"] = get_param_value(cycle_type_param)
                linking_config["editable_parameters"].append("drill_cycle.cycle_type")
        except Exception:
            pass
        
        try:
            peck_depth_param = params.itemByName("peckDepth")
            if peck_depth_param:
                drill_cycle["peck_depth"] = get_param_value(peck_depth_param)
                linking_config["editable_parameters"].append("drill_cycle.peck_depth")
        except Exception:
            pass
        
        try:
            dwell_time_param = params.itemByName("dwellTime")
            if dwell_time_param:
                drill_cycle["dwell_time"] = get_param_value(dwell_time_param)
                linking_config["editable_parameters"].append("drill_cycle.dwell_time")
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
        generic_linking = {}
        
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
                    generic_linking[output_name] = get_param_value(param)
                    linking_config["editable_parameters"].append(f"generic_linking.{output_name}")
            except Exception:
                continue
        
        if generic_linking:
            linking_config["sections"]["generic_linking"] = generic_linking
        
    except Exception:
        pass
    
    return linking_config


def _extract_linking_params(operation: adsk.cam.Operation) -> dict:
    """Extract linking parameters organized by dialog sections."""
    linking_config = {
        "operation_type": "unknown",
        "sections": {},
        "editable_parameters": []
    }
    
    try:
        if not operation or not hasattr(operation, 'parameters'):
            return linking_config
        
        operation_type = get_operation_type(operation).lower()
        linking_config["operation_type"] = operation_type
        
        params = operation.parameters
        
        if "pocket" in operation_type or "2d" in operation_type:
            linking_config = _extract_2d_linking_params(params, linking_config)
        elif "3d" in operation_type or "adaptive" in operation_type or "parallel" in operation_type:
            linking_config = _extract_3d_linking_params(params, linking_config)
        elif "drill" in operation_type:
            linking_config = _extract_drill_linking_params(params, linking_config)
        else:
            linking_config = _extract_generic_linking_params(params, linking_config)
        
        return linking_config
        
    except Exception:
        return {
            "operation_type": "unknown",
            "sections": {},
            "editable_parameters": []
        }


def get_toolpath_linking_impl(cam: adsk.cam.CAM, toolpath_id: str) -> dict:
    """Get linking parameters organized by sections for a specific toolpath."""
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
        
        linking_config = _extract_linking_params(operation)
        
        result = {
            "id": toolpath_id,
            "name": operation.name,
            "type": get_operation_type(operation),
            "setup_name": setup_name,
            "linking": linking_config
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error extracting linking parameters: {str(e)}",
            "code": "EXTRACTION_ERROR"
        }


# =============================================================================
# HTTP Handler Functions
# =============================================================================

def handle_get_toolpath_linking(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get linking parameters organized by sections for a specific toolpath."""
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
        result = get_toolpath_linking_impl(cam, toolpath_id)
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_get_toolpath_linking: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_modify_toolpath_linking(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Modify linking parameters for a toolpath."""
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
            "message": "Linking parameter modification not yet implemented",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_modify_toolpath_linking: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_operation_linking(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Get linking parameters for a specific operation."""
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
                linking_config = _extract_linking_params(operation)
                result = {
                    "operation_id": operation_id,
                    "operation_name": operation.name,
                    "linking_configuration": linking_config
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
        logger.error(f"Error in handle_get_operation_linking: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_validate_linking_configuration(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate linking configuration parameters for an operation."""
    try:
        operation_id = data.get("operation_id")
        linking_config = data.get("linking_config", {})
        
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
                operation_type = get_operation_type(operation)
                
                validation_results = {
                    "operation_id": operation_id,
                    "operation_type": operation_type,
                    "valid": True,
                    "issues": [],
                    "warnings": []
                }
                
                # Validate common linking parameters
                generic_linking = linking_config.get("sections", {}).get("generic_linking", {})
                
                if "clearance_height" in generic_linking:
                    clearance = generic_linking["clearance_height"]
                    if clearance <= 0:
                        validation_results["warnings"].append({
                            "parameter": "clearance_height",
                            "warning": "Clearance height should be positive",
                            "severity": "warning"
                        })
                
                if "retract_height" in generic_linking:
                    retract = generic_linking["retract_height"]
                    if retract <= 0:
                        validation_results["warnings"].append({
                            "parameter": "retract_height",
                            "warning": "Retract height should be positive",
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
        logger.error(f"Error in handle_validate_linking_configuration: {str(e)}")
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
    """Register all linking parameter handlers with the request router"""
    try:
        request_router.register_handler(
            "/cam/toolpaths/{toolpath_id}/linking",
            handle_get_toolpath_linking,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.linking"
        )
        
        request_router.register_handler(
            "/cam/toolpaths/{toolpath_id}/linking",
            handle_modify_toolpath_linking,
            methods=["PUT"],
            category="manufacture",
            module_name="manufacture.operations.linking"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/linking",
            handle_get_operation_linking,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.operations.linking"
        )
        
        request_router.register_handler(
            "/cam/operations/{operation_id}/linking/validate",
            handle_validate_linking_configuration,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.operations.linking"
        )
        
        logger.info("Registered linking parameter handlers")
        
    except Exception as e:
        logger.error(f"Error registering linking parameter handlers: {str(e)}")


register_handlers()
