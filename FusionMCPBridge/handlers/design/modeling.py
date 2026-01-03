# Design Modeling Handler
# Handles 3D operations (extrude, revolve, loft, sweep, boolean operations)

import json
from typing import Dict, Any

def handle_extrude_last_sketch(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle extrusion of the last sketch
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing extrusion parameters
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    value = float(data.get('value', 1.0))
    taperangle = float(data.get('taperangle', 0.0))
    
    FusionMCPBridge.task_queue.put(('extrude_last_sketch', value, taperangle))
    return {
        "status": 200,
        "data": {"message": "Letzter Sketch wird extrudiert"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_cut_extrude(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle cut extrusion operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing cut depth
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    depth = float(data.get('depth', 1.0))
    
    FusionMCPBridge.task_queue.put(('cut_extrude', depth))
    return {
        "status": 200,
        "data": {"message": "Cut Extrude wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_extrude_thin(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle thin extrusion operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing thickness and distance
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    thickness = float(data.get('thickness', 0.5))
    distance = float(data.get('distance', 1.0))
    
    FusionMCPBridge.task_queue.put(('extrude_thin', thickness, distance))
    return {
        "status": 200,
        "data": {"message": "Thin Extrude wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_revolve(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle revolve operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing revolve angle
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    angle = float(data.get('angle', 360))
    
    FusionMCPBridge.task_queue.put(('revolve_profile', angle))
    return {
        "status": 200,
        "data": {"message": "Profil wird revolviert"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_loft(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle loft operation between sketches
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing sketch count
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    sketchcount = int(data.get('sketchcount', 2))
    
    FusionMCPBridge.task_queue.put(('loft', sketchcount))
    return {
        "status": 200,
        "data": {"message": "Loft wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_sweep(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle sweep operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (sweep uses last two sketches)
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    FusionMCPBridge.task_queue.put(('sweep',))
    return {
        "status": 200,
        "data": {"message": "Sweep wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_boolean_operation(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle boolean operations (join, cut, intersect)
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing operation type
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    operation = data.get('operation', 'join')  # 'join', 'cut', 'intersect'
    
    FusionMCPBridge.task_queue.put(('boolean_operation', operation))
    return {
        "status": 200,
        "data": {"message": "Boolean Operation wird ausgeführt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_shell_body(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle shell body operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing thickness and face index
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    thickness = float(data.get('thickness', 0.5))
    faceindex = int(data.get('faceindex', 0))
    
    FusionMCPBridge.task_queue.put(('shell_body', thickness, faceindex))
    return {
        "status": 200,
        "data": {"message": "Shell body wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_move_body(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle body movement operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing movement vector
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    
    FusionMCPBridge.task_queue.put(('move_body', x, y, z))
    return {
        "status": 200,
        "data": {"message": "Body wird verschoben"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_offsetplane(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle offset plane creation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing offset and plane
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    offset = float(data.get('offset', 0.0))
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('offsetplane', offset, plane))
    return {
        "status": 200,
        "data": {"message": "Offset Plane wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/extrude_last_sketch",
        "handler": handle_extrude_last_sketch,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/cut_extrude",
        "handler": handle_cut_extrude,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/extrude_thin",
        "handler": handle_extrude_thin,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/revolve",
        "handler": handle_revolve,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/loft",
        "handler": handle_loft,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/sweep",
        "handler": handle_sweep,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/boolean_operation",
        "handler": handle_boolean_operation,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/shell_body",
        "handler": handle_shell_body,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/move_body",
        "handler": handle_move_body,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/offsetplane",
        "handler": handle_offsetplane,
        "methods": ["POST"],
        "category": "design"
    }
]