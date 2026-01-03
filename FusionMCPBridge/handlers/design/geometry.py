# Design Geometry Handler
# Handles basic 3D shape creation (box, cylinder, sphere) with comprehensive error handling
# Routes requests to the centralized task queue for execution on Fusion 360's main thread

import json
from typing import Dict, Any

# Import error handling system
from ...core.error_handling import error_handler_decorator, ErrorCategory, ErrorSeverity
from ...core.task_queue import task_queue


@error_handler_decorator("design.geometry", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.MEDIUM)
def handle_box(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle box creation requests with error handling
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    try:
        height = float(data.get('height', 5))
        width = float(data.get('width', 5))
        depth = float(data.get('depth', 5))
        x = float(data.get('x', 0))
        y = float(data.get('y', 0))
        z = float(data.get('z', 0))
        plane = data.get('plane', 'XY')
        
        # Validate parameters
        if height <= 0 or width <= 0 or depth <= 0:
            return {
                "status": 400,
                "error": True,
                "message": "Box dimensions must be positive values",
                "code": "INVALID_DIMENSIONS",
                "headers": {"Content-Type": "application/json"}
            }
        
        task_queue.queue_task('draw_box', height, width, depth, x, y, z, plane)
        return {
            "status": 200,
            "data": {"message": "Box wird erstellt"},
            "headers": {"Content-Type": "application/json"}
        }
    except ValueError as e:
        return {
            "status": 400,
            "error": True,
            "message": f"Invalid parameter values: {str(e)}",
            "code": "PARAMETER_CONVERSION_ERROR",
            "headers": {"Content-Type": "application/json"}
        }

@error_handler_decorator("design.geometry", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.MEDIUM)
def handle_cylinder(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle cylinder creation requests with error handling
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    try:
        radius = float(data.get('radius', 2.5))
        height = float(data.get('height', 5))
        x = float(data.get('x', 0))
        y = float(data.get('y', 0))
        z = float(data.get('z', 0))
        plane = data.get('plane', 'XY')
        
        # Validate parameters
        if radius <= 0 or height <= 0:
            return {
                "status": 400,
                "error": True,
                "message": "Cylinder radius and height must be positive values",
                "code": "INVALID_DIMENSIONS",
                "headers": {"Content-Type": "application/json"}
            }
        
        task_queue.queue_task('draw_cylinder', radius, height, x, y, z, plane)
        return {
            "status": 200,
            "data": {"message": "Cylinder wird erstellt"},
            "headers": {"Content-Type": "application/json"}
        }
    except ValueError as e:
        return {
            "status": 400,
            "error": True,
            "message": f"Invalid parameter values: {str(e)}",
            "code": "PARAMETER_CONVERSION_ERROR",
            "headers": {"Content-Type": "application/json"}
        }

@error_handler_decorator("design.geometry", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.MEDIUM)
def handle_sphere(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle sphere creation requests with error handling
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    try:
        radius = float(data.get('radius', 5.0))
        x = float(data.get('x', 0))
        y = float(data.get('y', 0))
        z = float(data.get('z', 0))
        
        # Validate parameters
        if radius <= 0:
            return {
                "status": 400,
                "error": True,
                "message": "Sphere radius must be a positive value",
                "code": "INVALID_DIMENSIONS",
                "headers": {"Content-Type": "application/json"}
            }
        
        task_queue.queue_task('draw_sphere', radius, x, y, z)
        return {
            "status": 200,
            "data": {"message": "Sphere wird erstellt"},
            "headers": {"Content-Type": "application/json"}
        }
    except ValueError as e:
        return {
            "status": 400,
            "error": True,
            "message": f"Invalid parameter values: {str(e)}",
            "code": "PARAMETER_CONVERSION_ERROR",
            "headers": {"Content-Type": "application/json"}
        }

@error_handler_decorator("design.geometry", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.MEDIUM)
def handle_witzenmann(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Witzenmann logo creation requests with error handling
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    try:
        scale = data.get('scale', 1.0)
        z = float(data.get('z', 0))
        
        # Validate parameters
        if scale <= 0:
            return {
                "status": 400,
                "error": True,
                "message": "Scale must be a positive value",
                "code": "INVALID_SCALE",
                "headers": {"Content-Type": "application/json"}
            }
        
        task_queue.queue_task('draw_witzenmann', scale, z)
        return {
            "status": 200,
            "data": {"message": "Witzenmann-Logo wird erstellt"},
            "headers": {"Content-Type": "application/json"}
        }
    except ValueError as e:
        return {
            "status": 400,
            "error": True,
            "message": f"Invalid parameter values: {str(e)}",
            "code": "PARAMETER_CONVERSION_ERROR",
            "headers": {"Content-Type": "application/json"}
        }

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/Box",
        "handler": handle_box,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/draw_cylinder",
        "handler": handle_cylinder,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/sphere",
        "handler": handle_sphere,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/Witzenmann",
        "handler": handle_witzenmann,
        "methods": ["POST"],
        "category": "design"
    }
]