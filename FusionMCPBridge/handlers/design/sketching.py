# Design Sketching Handler
# Handles 2D drawing operations (lines, circles, arcs, splines)

import json
from typing import Dict, Any

def handle_draw_lines(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle line drawing requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing points and plane
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    points = data.get('points', [])
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('draw_lines', points, plane))
    return {
        "status": 200,
        "data": {"message": "Lines werden erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_draw_one_line(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle single line drawing requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing start and end points
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    x1 = float(data.get('x1', 0))
    y1 = float(data.get('y1', 0))
    z1 = float(data.get('z1', 0))
    x2 = float(data.get('x2', 1))
    y2 = float(data.get('y2', 1))
    z2 = float(data.get('z2', 0))
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('draw_one_line', x1, y1, z1, x2, y2, z2, plane))
    return {
        "status": 200,
        "data": {"message": "Line wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_create_circle(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle circle creation requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing radius and position
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    radius = float(data.get('radius', 1.0))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('circle', radius, x, y, z, plane))
    return {
        "status": 200,
        "data": {"message": "Circle wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_arc(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle arc creation requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing three points for arc
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    point1 = data.get('point1', [0, 0])
    point2 = data.get('point2', [1, 1])
    point3 = data.get('point3', [2, 0])
    connect = bool(data.get('connect', False))
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('arc', point1, point2, point3, plane, connect))
    return {
        "status": 200,
        "data": {"message": "Arc wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_spline(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle spline creation requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing points for spline
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    points = data.get('points', [])
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('spline', points, plane))
    return {
        "status": 200,
        "data": {"message": "Spline wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_draw_2d_rectangle(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle 2D rectangle creation requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing corner points
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    x_1 = float(data.get('x_1', 0))
    y_1 = float(data.get('y_1', 0))
    z_1 = float(data.get('z_1', 0))
    x_2 = float(data.get('x_2', 1))
    y_2 = float(data.get('y_2', 1))
    z_2 = float(data.get('z_2', 0))
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('draw_2d_rectangle', x_1, y_1, z_1, x_2, y_2, z_2, plane))
    return {
        "status": 200,
        "data": {"message": "2D Rechteck wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_ellipsis(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ellipse creation requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing ellipse parameters
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    x_center = float(data.get('x_center', 0))
    y_center = float(data.get('y_center', 0))
    z_center = float(data.get('z_center', 0))
    x_major = float(data.get('x_major', 10))
    y_major = float(data.get('y_major', 0))
    z_major = float(data.get('z_major', 0))
    x_through = float(data.get('x_through', 5))
    y_through = float(data.get('y_through', 4))
    z_through = float(data.get('z_through', 0))
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    
    FusionMCPBridge.task_queue.put(('ellipsis', x_center, y_center, z_center,
                                   x_major, y_major, z_major, x_through, y_through, z_through, plane))
    return {
        "status": 200,
        "data": {"message": "Ellipsis wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_draw_text(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle text creation requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing text parameters
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    text = str(data.get('text', "Hello"))
    x_1 = float(data.get('x_1', 0))
    y_1 = float(data.get('y_1', 0))
    z_1 = float(data.get('z_1', 0))
    x_2 = float(data.get('x_2', 10))
    y_2 = float(data.get('y_2', 4))
    z_2 = float(data.get('z_2', 0))
    extrusion_value = float(data.get('extrusion_value', 1.0))
    plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
    thickness = float(data.get('thickness', 0.5))
    
    FusionMCPBridge.task_queue.put(('draw_text', text, thickness, x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane))
    return {
        "status": 200,
        "data": {"message": "Text wird erstellt"},
        "headers": {"Content-Type": "application/json"}
    }

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/draw_lines",
        "handler": handle_draw_lines,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/draw_one_line",
        "handler": handle_draw_one_line,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/create_circle",
        "handler": handle_create_circle,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/arc",
        "handler": handle_arc,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/spline",
        "handler": handle_spline,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/draw_2d_rectangle",
        "handler": handle_draw_2d_rectangle,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/ellipsis",
        "handler": handle_ellipsis,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/draw_text",
        "handler": handle_draw_text,
        "methods": ["POST"],
        "category": "design"
    }
]