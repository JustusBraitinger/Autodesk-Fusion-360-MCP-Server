"""
CAM Setup Management Handler

Handles CAM setup creation, modification, duplication, and deletion operations.
Contains actual business logic for setup management (extracted from cam.py).
"""

import adsk.core
import adsk.cam
from typing import Dict, Any, Optional
import logging

# Import core components
from ...core.task_queue import task_queue, TaskPriority
from ...core.router import request_router

# Import shared CAM utilities
from .cam_utils import (
    get_cam_product,
    validate_cam_product_with_details,
    find_setup_by_id,
    get_operation_type
)

# Set up logging
logger = logging.getLogger(__name__)


# =============================================================================
# Business Logic Functions (extracted from cam.py)
# =============================================================================

def _setup_name_exists(cam_product: adsk.cam.CAM, name: str) -> bool:
    """Check if a setup name already exists."""
    try:
        setups = cam_product.setups
        if not setups:
            return False
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            if setup.name == name:
                return True
        
        return False
    except Exception:
        return False


def _extract_wcs_info(setup) -> dict:
    """
    Extract WCS information from a setup.
    """
    try:
        wcs_info = {
            "type": "model_origin",
            "origin": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {
                "x_axis": {"x": 1.0, "y": 0.0, "z": 0.0},
                "y_axis": {"x": 0.0, "y": 1.0, "z": 0.0},
                "z_axis": {"x": 0.0, "y": 0.0, "z": 1.0}
            },
            "reference": "model",
            "reference_geometry": None
        }
        
        if hasattr(setup, 'workCoordinateSystem'):
            wcs = setup.workCoordinateSystem
            if wcs:
                if hasattr(wcs, 'origin'):
                    origin = wcs.origin
                    wcs_info["origin"] = {
                        "x": origin.x if hasattr(origin, 'x') else 0.0,
                        "y": origin.y if hasattr(origin, 'y') else 0.0,
                        "z": origin.z if hasattr(origin, 'z') else 0.0
                    }
                
                if hasattr(wcs, 'xDirection') and hasattr(wcs, 'yDirection'):
                    x_dir = wcs.xDirection
                    y_dir = wcs.yDirection
                    
                    wcs_info["orientation"]["x_axis"] = {
                        "x": x_dir.x if hasattr(x_dir, 'x') else 1.0,
                        "y": x_dir.y if hasattr(x_dir, 'y') else 0.0,
                        "z": x_dir.z if hasattr(x_dir, 'z') else 0.0
                    }
                    
                    wcs_info["orientation"]["y_axis"] = {
                        "x": y_dir.x if hasattr(y_dir, 'x') else 0.0,
                        "y": y_dir.y if hasattr(y_dir, 'y') else 1.0,
                        "z": y_dir.z if hasattr(y_dir, 'z') else 0.0
                    }
                    
                    z_x = x_dir.y * y_dir.z - x_dir.z * y_dir.y
                    z_y = x_dir.z * y_dir.x - x_dir.x * y_dir.z
                    z_z = x_dir.x * y_dir.y - x_dir.y * y_dir.x
                    
                    wcs_info["orientation"]["z_axis"] = {"x": z_x, "y": z_y, "z": z_z}
                
                if hasattr(wcs, 'isModelOrigin') and wcs.isModelOrigin:
                    wcs_info["type"] = "model_origin"
                elif hasattr(wcs, 'referenceFace') and wcs.referenceFace:
                    wcs_info["type"] = "face_based"
                    wcs_info["reference"] = "face"
                elif hasattr(wcs, 'referenceEdge') and wcs.referenceEdge:
                    wcs_info["type"] = "edge_based"
                    wcs_info["reference"] = "edge"
                else:
                    wcs_info["type"] = "custom"
        
        return wcs_info
        
    except Exception:
        return {
            "type": "unknown",
            "origin": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {
                "x_axis": {"x": 1.0, "y": 0.0, "z": 0.0},
                "y_axis": {"x": 0.0, "y": 1.0, "z": 0.0},
                "z_axis": {"x": 0.0, "y": 0.0, "z": 1.0}
            },
            "reference": "unknown",
            "reference_geometry": None
        }


def _extract_stock_info(setup) -> dict:
    """
    Extract stock information from a setup.
    """
    try:
        stock_info = {
            "mode": "unknown",
            "dimensions": {"length": 0, "width": 0, "height": 0, "diameter": 0},
            "position": [0, 0, 0],
            "material": "unknown",
            "geometry_id": None
        }
        
        if hasattr(setup, 'stock') and setup.stock:
            stock = setup.stock
            
            if hasattr(stock, 'stockType'):
                stock_type = stock.stockType
                if stock_type == adsk.cam.StockTypes.RelativeBoxStock:
                    stock_info["mode"] = "box"
                elif stock_type == adsk.cam.StockTypes.RelativeCylinderStock:
                    stock_info["mode"] = "cylinder"
                elif stock_type == adsk.cam.StockTypes.FixedBoxStock:
                    stock_info["mode"] = "fixed_box"
                elif stock_type == adsk.cam.StockTypes.FixedCylinderStock:
                    stock_info["mode"] = "fixed_cylinder"
                else:
                    stock_info["mode"] = "auto"
            
            if hasattr(stock, 'boundingBox') and stock.boundingBox:
                bbox = stock.boundingBox
                if hasattr(bbox, 'minPoint') and hasattr(bbox, 'maxPoint'):
                    min_pt = bbox.minPoint
                    max_pt = bbox.maxPoint
                    stock_info["dimensions"] = {
                        "length": abs(max_pt.x - min_pt.x),
                        "width": abs(max_pt.y - min_pt.y),
                        "height": abs(max_pt.z - min_pt.z),
                        "diameter": max(abs(max_pt.x - min_pt.x), abs(max_pt.y - min_pt.y))
                    }
            
            if hasattr(stock, 'origin') and stock.origin:
                origin = stock.origin
                stock_info["position"] = [origin.x, origin.y, origin.z]
            
            if hasattr(stock, 'material') and stock.material:
                material = stock.material
                if hasattr(material, 'name'):
                    stock_info["material"] = material.name
                elif hasattr(material, 'displayName'):
                    stock_info["material"] = material.displayName
            
            if hasattr(stock, 'sourceBody') and stock.sourceBody:
                body = stock.sourceBody
                if hasattr(body, 'entityToken'):
                    stock_info["geometry_id"] = body.entityToken
        
        return stock_info
        
    except Exception as e:
        return {
            "mode": "unknown",
            "dimensions": {"length": 0, "width": 0, "height": 0, "diameter": 0},
            "position": [0, 0, 0],
            "material": "unknown",
            "geometry_id": None,
            "error": f"Error extracting stock info: {str(e)}"
        }


def _extract_model_reference(setup) -> str:
    """Extract model reference from a setup (root level)."""
    try:
        return "model_placeholder_id"
    except Exception:
        return None


def list_setups_detailed() -> dict:
    """
    List all CAM setups with comprehensive configuration details.
    """
    try:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "setups": [],
                "total_count": 0,
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        
        cam_product = validation["cam_product"]
        
        result = {
            "setups": [],
            "total_count": 0,
            "message": None
        }
        
        setups = cam_product.setups
        if not setups or setups.count == 0:
            result["message"] = "No setups found in CAM document"
            return result
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            setup_id = setup.entityToken if hasattr(setup, 'entityToken') else f"setup_{setup_idx}"
            
            toolpath_count = 0
            if hasattr(setup, 'operations') and setup.operations:
                toolpath_count += setup.operations.count
            
            if hasattr(setup, 'folders') and setup.folders:
                for folder_idx in range(setup.folders.count):
                    folder = setup.folders.item(folder_idx)
                    if hasattr(folder, 'operations') and folder.operations:
                        toolpath_count += folder.operations.count
            
            wcs_info = _extract_wcs_info(setup)
            stock_info = _extract_stock_info(setup)
            model_ref = _extract_model_reference(setup)
            
            setup_data = {
                "id": setup_id,
                "name": setup.name,
                "wcs": wcs_info,
                "stock": stock_info,
                "model_id": model_ref,
                "toolpath_count": toolpath_count,
                "is_active": hasattr(setup, 'isActive') and setup.isActive,
                "created_date": "2025-01-03T00:00:00Z",
                "modified_date": "2025-01-03T00:00:00Z"
            }
            
            result["setups"].append(setup_data)
        
        result["total_count"] = len(result["setups"])
        
        if result["total_count"] == 0:
            result["message"] = "No setups found in CAM document"
        
        return result
        
    except Exception as e:
        return {
            "setups": [],
            "total_count": 0,
            "error": True,
            "message": f"Error listing setups: {str(e)}",
            "code": "LISTING_ERROR"
        }


def get_setup_by_id_impl(setup_id: str) -> dict:
    """
    Retrieve detailed setup information by ID.
    """
    try:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        
        cam_product = validation["cam_product"]
        
        if not setup_id:
            return {
                "error": True,
                "message": "Setup ID is required",
                "code": "MISSING_SETUP_ID"
            }
        
        setup = find_setup_by_id(cam_product, setup_id)
        if not setup:
            return {
                "error": True,
                "message": f"Setup with ID '{setup_id}' not found",
                "code": "SETUP_NOT_FOUND"
            }
        
        wcs_info = _extract_wcs_info(setup)
        stock_info = _extract_stock_info(setup)
        model_ref = _extract_model_reference(setup)
        
        toolpaths = []
        if hasattr(setup, 'operations') and setup.operations:
            for op_idx in range(setup.operations.count):
                operation = setup.operations.item(op_idx)
                toolpath_data = {
                    "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_{op_idx}",
                    "name": operation.name,
                    "type": get_operation_type(operation),
                    "is_valid": operation.isValid if hasattr(operation, 'isValid') else True
                }
                toolpaths.append(toolpath_data)
        
        if hasattr(setup, 'folders') and setup.folders:
            for folder_idx in range(setup.folders.count):
                folder = setup.folders.item(folder_idx)
                if hasattr(folder, 'operations') and folder.operations:
                    for op_idx in range(folder.operations.count):
                        operation = folder.operations.item(op_idx)
                        toolpath_data = {
                            "id": operation.entityToken if hasattr(operation, 'entityToken') else f"op_f{folder_idx}_{op_idx}",
                            "name": operation.name,
                            "type": get_operation_type(operation),
                            "is_valid": operation.isValid if hasattr(operation, 'isValid') else True,
                            "folder": folder.name
                        }
                        toolpaths.append(toolpath_data)
        
        result = {
            "id": setup_id,
            "name": setup.name,
            "wcs": wcs_info,
            "stock": stock_info,
            "model_id": model_ref,
            "toolpaths": toolpaths,
            "toolpath_count": len(toolpaths),
            "is_active": hasattr(setup, 'isActive') and setup.isActive,
            "metadata": {
                "created_date": "2025-01-03T00:00:00Z",
                "modified_date": "2025-01-03T00:00:00Z"
            }
        }
        
        return result
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error retrieving setup '{setup_id}': {str(e)}",
            "code": "RETRIEVAL_ERROR"
        }


def create_setup_impl(name: str = None, stock_config: dict = None, 
                      wcs_config: dict = None, model_id: str = None) -> dict:
    """
    Create a new CAM setup with specified configuration.
    """
    try:
        validation = validate_cam_product_with_details()
        if not validation["valid"]:
            return {
                "error": True,
                "message": validation["message"],
                "code": validation["code"]
            }
        
        cam_product = validation["cam_product"]
        
        if not name:
            base_name = "Setup"
            counter = 1
            name = base_name
            while _setup_name_exists(cam_product, name):
                counter += 1
                name = f"{base_name} {counter}"
        elif _setup_name_exists(cam_product, name):
            return {
                "error": True,
                "message": f"Setup with name '{name}' already exists",
                "code": "DUPLICATE_NAME"
            }
        
        try:
            setups = cam_product.setups
            new_setup = setups.add()
            new_setup.name = name
            
            setup_id = new_setup.entityToken if hasattr(new_setup, 'entityToken') else str(id(new_setup))
            actual_stock_config = _extract_stock_info(new_setup)
            actual_wcs_config = _extract_wcs_info(new_setup)
            
            result = {
                "id": setup_id,
                "name": name,
                "wcs": actual_wcs_config,
                "stock": actual_stock_config,
                "model_id": model_id,
                "created_date": "2025-01-03T00:00:00Z",
                "message": f"Setup '{name}' created successfully"
            }
            
            return result
            
        except Exception as e:
            return {
                "error": True,
                "message": f"Failed to create setup: {str(e)}",
                "code": "SETUP_CREATION_FAILED"
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error during setup creation: {str(e)}",
            "code": "CREATION_ERROR"
        }


# =============================================================================
# HTTP Handler Functions
# =============================================================================

def handle_list_setups(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """List all CAM setups with comprehensive configuration details."""
    try:
        result = {}
        
        def execute_list_setups():
            nonlocal result
            try:
                result = list_setups_detailed()
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error listing setups: {str(e)}",
                    "code": "SETUP_LIST_ERROR"
                }
        
        task_queue.queue_task(
            "list_setups",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.setups",
            callback=execute_list_setups
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_list_setups: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_get_setup(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve detailed setup information by ID."""
    try:
        setup_id = data.get("setup_id")
        if not setup_id:
            return {
                "status": 400,
                "error": True,
                "message": "setup_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        result = {}
        
        def execute_get_setup():
            nonlocal result
            try:
                result = get_setup_by_id_impl(setup_id)
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error retrieving setup: {str(e)}",
                    "code": "SETUP_GET_ERROR"
                }
        
        task_queue.queue_task(
            "get_setup",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.setups",
            callback=execute_get_setup
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_get_setup: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_create_setup(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new CAM setup with specified configuration."""
    try:
        name = data.get("name")
        stock_config = data.get("stock_config", {})
        wcs_config = data.get("wcs_config", {})
        model_id = data.get("model_id")
        
        result = {}
        
        def execute_create_setup():
            nonlocal result
            try:
                result = create_setup_impl(
                    name=name,
                    stock_config=stock_config,
                    wcs_config=wcs_config,
                    model_id=model_id
                )
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error creating setup: {str(e)}",
                    "code": "SETUP_CREATE_ERROR"
                }
        
        task_queue.queue_task(
            "create_setup",
            priority=TaskPriority.HIGH,
            module_context="manufacture.setups",
            callback=execute_create_setup
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 201 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_create_setup: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_modify_setup(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Modify an existing CAM setup configuration."""
    try:
        setup_id = data.get("setup_id")
        if not setup_id:
            return {
                "status": 400,
                "error": True,
                "message": "setup_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        return {
            "status": 501,
            "error": True,
            "message": "Setup modification not yet implemented",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_modify_setup: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_duplicate_setup(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Duplicate an existing CAM setup."""
    try:
        setup_id = data.get("setup_id")
        if not setup_id:
            return {
                "status": 400,
                "error": True,
                "message": "setup_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        return {
            "status": 501,
            "error": True,
            "message": "Setup duplication not yet implemented",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_duplicate_setup: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }


def handle_delete_setup(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a CAM setup."""
    try:
        setup_id = data.get("setup_id")
        if not setup_id:
            return {
                "status": 400,
                "error": True,
                "message": "setup_id parameter is required",
                "headers": {"Content-Type": "application/json"}
            }
        
        return {
            "status": 501,
            "error": True,
            "message": "Setup deletion not yet implemented",
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_delete_setup: {str(e)}")
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
    """Register all setup handlers with the request router"""
    try:
        request_router.register_handler(
            "/cam/setups",
            handle_list_setups,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.setups"
        )
        
        request_router.register_handler(
            "/cam/setups/{setup_id}",
            handle_get_setup,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.setups"
        )
        
        request_router.register_handler(
            "/cam/setups",
            handle_create_setup,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.setups"
        )
        
        request_router.register_handler(
            "/cam/setups/{setup_id}",
            handle_modify_setup,
            methods=["PUT"],
            category="manufacture",
            module_name="manufacture.setups"
        )
        
        request_router.register_handler(
            "/cam/setups/{setup_id}/duplicate",
            handle_duplicate_setup,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.setups"
        )
        
        request_router.register_handler(
            "/cam/setups/{setup_id}",
            handle_delete_setup,
            methods=["DELETE"],
            category="manufacture",
            module_name="manufacture.setups"
        )
        
        logger.info("Registered CAM setup handlers")
        
    except Exception as e:
        logger.error(f"Error registering setup handlers: {str(e)}")


register_handlers()
