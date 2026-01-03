# Design Utilities Handler
# Handles design utilities (parameters, selection, export)

import adsk.core
import adsk.fusion
import json
from typing import Dict, Any, Optional


# =============================================================================
# Body Lookup Functions
# =============================================================================

def find_body_by_id(body_id: str) -> Optional[adsk.fusion.BRepBody]:
    """Find a body in the design workspace by its entity token ID."""
    try:
        app = adsk.core.Application.get()
        if not app:
            return None
        
        doc = app.activeDocument
        if not doc:
            return None
        
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        if not design:
            return None
        
        root_comp = design.rootComponent
        if not root_comp:
            return None
        
        for body_idx in range(root_comp.bRepBodies.count):
            body = root_comp.bRepBodies.item(body_idx)
            if hasattr(body, 'entityToken') and body.entityToken == body_id:
                return body
        
        return None
        
    except Exception:
        return None


# =============================================================================
# HTTP Handler Functions
# =============================================================================

def handle_set_parameter(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle parameter setting operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing parameter name and value
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    name = data.get('name')
    value = data.get('value')
    
    if name and value:
        FusionMCPBridge.task_queue.put(('set_parameter', name, value))
        return {
            "status": 200,
            "data": {"message": f"Parameter {name} wird gesetzt"},
            "headers": {"Content-Type": "application/json"}
        }
    else:
        return {
            "status": 400,
            "data": {"error": True, "message": "Name and value are required"},
            "headers": {"Content-Type": "application/json"}
        }

def handle_list_parameters(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle parameter listing operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (not used)
        
    Returns:
        Response dictionary with parameter list
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    return {
        "status": 200,
        "data": {"ModelParameter": FusionMCPBridge.ModelParameterSnapshot},
        "headers": {"Content-Type": "application/json"}
    }

def handle_count_parameters(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle parameter count operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (not used)
        
    Returns:
        Response dictionary with parameter count
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    return {
        "status": 200,
        "data": {"user_parameter_count": len(FusionMCPBridge.ModelParameterSnapshot)},
        "headers": {"Content-Type": "application/json"}
    }

def handle_select_body(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle body selection operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing body name
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    name = str(data.get('name', ''))
    
    FusionMCPBridge.task_queue.put(('select_body', name))
    return {
        "status": 200,
        "data": {"message": "Body wird ausgewählt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_select_sketch(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle sketch selection operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing sketch name
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    name = str(data.get('name', ''))
    
    FusionMCPBridge.task_queue.put(('select_sketch', name))
    return {
        "status": 200,
        "data": {"message": "Sketch wird ausgewählt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_export_step(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle STEP export operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing export name
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    name = str(data.get('name', 'Test.step'))
    
    FusionMCPBridge.task_queue.put(('export_step', name))
    return {
        "status": 200,
        "data": {"message": "STEP Export gestartet"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_export_stl(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle STL export operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data containing export name
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    name = str(data.get('Name', 'Test.stl'))
    
    FusionMCPBridge.task_queue.put(('export_stl', name))
    return {
        "status": 200,
        "data": {"message": "STL Export gestartet"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_undo(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle undo operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (not used)
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    FusionMCPBridge.task_queue.put(('undo',))
    return {
        "status": 200,
        "data": {"message": "Undo wird ausgeführt"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_delete_everything(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle delete everything operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (not used)
        
    Returns:
        Response dictionary
    """
    # Import here to avoid circular imports
    from ... import FusionMCPBridge
    
    FusionMCPBridge.task_queue.put(('delete_everything',))
    return {
        "status": 200,
        "data": {"message": "Alle Bodies werden gelöscht"},
        "headers": {"Content-Type": "application/json"}
    }

def handle_test_connection(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle test connection operation
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (not used)
        
    Returns:
        Response dictionary
    """
    return {
        "status": 200,
        "data": {"message": "Verbindung erfolgreich"},
        "headers": {"Content-Type": "application/json"}
    }

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/set_parameter",
        "handler": handle_set_parameter,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/list_parameters",
        "handler": handle_list_parameters,
        "methods": ["GET"],
        "category": "design"
    },
    {
        "pattern": "/count_parameters",
        "handler": handle_count_parameters,
        "methods": ["GET"],
        "category": "design"
    },
    {
        "pattern": "/select_body",
        "handler": handle_select_body,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/select_sketch",
        "handler": handle_select_sketch,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/Export_STEP",
        "handler": handle_export_step,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/Export_STL",
        "handler": handle_export_stl,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/undo",
        "handler": handle_undo,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/delete_everything",
        "handler": handle_delete_everything,
        "methods": ["POST"],
        "category": "design"
    },
    {
        "pattern": "/test_connection",
        "handler": handle_test_connection,
        "methods": ["POST"],
        "category": "design"
    }
]