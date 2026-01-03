# System Utilities Handler
# Handles system utility operations like undo and delete operations

import json
from typing import Dict, Any

def handle_undo(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle undo requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    try:
        import queue
        # Try to import the main module
        import sys
        import os
        
        # Add the parent directory to sys.path to find FusionMCPBridge
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Import the main module
        import FusionMCPBridge
        FusionMCPBridge.task_queue.put(('undo',))
        
        return {
            "status": 200,
            "data": {"message": "Undo wird ausgeführt"},
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Undo error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_delete_everything(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle delete everything requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    try:
        import queue
        # Try to import the main module
        import sys
        import os
        
        # Add the parent directory to sys.path to find FusionMCPBridge
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Import the main module
        import FusionMCPBridge
        FusionMCPBridge.task_queue.put(('delete_everything',))
        
        return {
            "status": 200,
            "data": {"message": "Alle Bodies werden gelöscht"},
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Delete everything error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_move_body(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle move body requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    try:
        import queue
        # Try to import the main module
        import sys
        import os
        
        # Add the parent directory to sys.path to find FusionMCPBridge
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Import the main module
        import FusionMCPBridge
        
        x = float(data.get('x', 0))
        y = float(data.get('y', 0))
        z = float(data.get('z', 0))
        
        FusionMCPBridge.task_queue.put(('move_body', x, y, z))
        
        return {
            "status": 200,
            "data": {"message": "Body wird verschoben"},
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Move body error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_offset_plane(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle offset plane requests
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    try:
        import queue
        # Try to import the main module
        import sys
        import os
        
        # Add the parent directory to sys.path to find FusionMCPBridge
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Import the main module
        import FusionMCPBridge
        
        offset = float(data.get('offset', 0.0))
        plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
        
        FusionMCPBridge.task_queue.put(('offsetplane', offset, plane))
        
        return {
            "status": 200,
            "data": {"message": "Offset Plane wird erstellt"},
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Offset plane error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/undo",
        "handler": handle_undo,
        "methods": ["POST"],
        "category": "system"
    },
    {
        "pattern": "/delete_everything",
        "handler": handle_delete_everything,
        "methods": ["POST"],
        "category": "system"
    },
    {
        "pattern": "/move_body",
        "handler": handle_move_body,
        "methods": ["POST"],
        "category": "system"
    },
    {
        "pattern": "/offsetplane",
        "handler": handle_offset_plane,
        "methods": ["POST"],
        "category": "system"
    }
]