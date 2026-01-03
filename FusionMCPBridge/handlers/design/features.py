# Design Features Handler
# Handles features (fillet, holes, patterns, threading)

import json
from typing import Dict, Any

def handle_fillet_edges(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle fillet edges operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing fillet radius
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    radius = float(data.get('radius', 0.3))
    
    FusionMCPBridge.task_queue.put(('fillet_edges', radius))
    return {
        "status": 200,
        "data": {"message": "Fillet edges started"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_holes(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle hole creation operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing hole parameters
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    points = data.get('points', [[0, 0]])
    width = float(data.get('width', 1.0))
    faceindex = int(data.get('faceindex', 0))
    distance = data.get('depth', None)
    if distance is not None:
        distance = float(distance)
    through = bool(data.get('through', False))
    
    FusionMCPBridge.task_queue.put(('holes', points, width, distance, faceindex))
    return {
        "status": 200,
        "data": {"message": "Loch wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_threaded(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle threaded feature creation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing thread parameters
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    inside = bool(data.get('inside', True))
    allsizes = int(data.get('allsizes', 30))
    
    FusionMCPBridge.task_queue.put(('threaded', inside, allsizes))
    return {
        "status": 200,
        "data": {"message": "Threaded Feature wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_circular_pattern(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle circular pattern creation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing pattern parameters
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    quantity = float(data.get('quantity'))
    axis = str(data.get('axis', "X"))
    plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('circular_pattern', quantity, axis, plane))
    return {
        "status": 200,
        "data": {"message": "Circular Pattern wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_rectangular_pattern(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle rectangular pattern creation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing pattern parameters
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    quantity_one = float(data.get('quantity_one', 2))
    distance_one = float(data.get('distance_one', 5))
    axis_one = str(data.get('axis_one', "X"))
    quantity_two = float(data.get('quantity_two', 2))
    distance_two = float(data.get('distance_two', 5))
    axis_two = str(data.get('axis_two', "Y"))
    plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
    
    # Parameter order: axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane
    FusionMCPBridge.task_queue.put(('rectangular_pattern', axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane))
    return {
        "status": 200,
        "data": {"message": "Rectangular Pattern wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/fillet_edges",
        "handler": handle_fillet_edges,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/holes",
        "handler": handle_holes,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/threaded",
        "handler": handle_threaded,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/circular_pattern",
        "handler": handle_circular_pattern,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/rectangular_pattern",
        "handler": handle_rectangular_pattern,
        "methods": ["POST"],
        "category": "design"
    }
]