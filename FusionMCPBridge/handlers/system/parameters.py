# System Parameters Handler
# Handles system parameter management operations

import json
from typing import Dict, Any

def handle_count_parameters(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle count parameters requests
    
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
        FusionMCPBridge.task_queue.put(('count_parameters',))
        
        return {
            "status": 200,
            "data": {"message": "Parameter werden gezählt"},
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Count parameters error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_list_parameters(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle list parameters requests
    
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
        FusionMCPBridge.task_queue.put(('list_parameters',))
        
        return {
            "status": 200,
            "data": {"message": "Parameter werden aufgelistet"},
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"List parameters error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_set_parameter(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle set parameter requests
    
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
        
        name = data.get('name', '')
        value = data.get('value', '')
        
        FusionMCPBridge.task_queue.put(('set_parameter', name, value))
        
        return {
            "status": 200,
            "data": {"message": f"Parameter '{name}' wird auf '{value}' gesetzt"},
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Set parameter error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/count_parameters",
        "handler": handle_count_parameters,
        "methods": ["GET", "POST"],
        "category": "system"
    },
    {
        "pattern": "/list_parameters",
        "handler": handle_list_parameters,
        "methods": ["GET", "POST"],
        "category": "system"
    },
    {
        "pattern": "/set_parameter",
        "handler": handle_set_parameter,
        "methods": ["POST"],
        "category": "system"
    }
]