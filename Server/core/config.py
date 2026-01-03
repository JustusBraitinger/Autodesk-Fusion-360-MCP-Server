"""
Centralized configuration management with category support.

This module provides centralized configuration management for the modular server,
including category-based endpoint organization and configuration validation.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Base URL for Fusion 360 communication
_BASE_URL = "http://localhost:5001"

# Request timeout in seconds
_REQUEST_TIMEOUT = 30

# Standard HTTP headers
_HEADERS = {
    "Content-Type": "application/json"
}

# Category-based endpoint organization
_ENDPOINTS = {
    "cad": {
        # Geometry tools
        "draw_cylinder": f"{_BASE_URL}/draw_cylinder",
        "draw_box": f"{_BASE_URL}/Box",
        "draw_sphere": f"{_BASE_URL}/sphere",
        
        # Sketching tools
        "draw2Dcircle": f"{_BASE_URL}/create_circle",
        "draw_lines": f"{_BASE_URL}/draw_lines",
        "draw_one_line": f"{_BASE_URL}/draw_one_line",
        "draw_arc": f"{_BASE_URL}/arc",
        "spline": f"{_BASE_URL}/spline",
        "ellipsie": f"{_BASE_URL}/ellipsis",
        "draw_2d_rectangle": f"{_BASE_URL}/draw_2d_rectangle",
        "draw_text": f"{_BASE_URL}/draw_text",
        
        # Modeling tools
        "extrude": f"{_BASE_URL}/extrude_last_sketch",
        "extrude_thin": f"{_BASE_URL}/extrude_thin",
        "cut_extrude": f"{_BASE_URL}/cut_extrude",
        "revolve": f"{_BASE_URL}/revolve",
        "loft": f"{_BASE_URL}/loft",
        "sweep": f"{_BASE_URL}/sweep",
        "boolean_operation": f"{_BASE_URL}/boolean_operation",
        
        # Feature tools
        "fillet_edges": f"{_BASE_URL}/fillet_edges",
        "shell_body": f"{_BASE_URL}/shell_body",
        "holes": f"{_BASE_URL}/holes",
        "threaded": f"{_BASE_URL}/threaded",
        "circular_pattern": f"{_BASE_URL}/circular_pattern",
        "rectangular_pattern": f"{_BASE_URL}/rectangular_pattern",
        "move_body": f"{_BASE_URL}/move_body",
    },
    
    "cam": {
        # Toolpath management
        "cam_toolpaths": f"{_BASE_URL}/cam/toolpaths",
        "cam_toolpaths_heights": f"{_BASE_URL}/cam/toolpaths/heights",
        "cam_toolpath": f"{_BASE_URL}/cam/toolpath",
        "cam_toolpath_heights": f"{_BASE_URL}/cam/toolpath",  # /{id}/heights
        "cam_toolpath_parameter": f"{_BASE_URL}/cam/toolpath",
        "cam_toolpath_passes": f"{_BASE_URL}/cam/toolpath",  # /{id}/passes
        "cam_toolpath_linking": f"{_BASE_URL}/cam/toolpath",  # /{id}/linking
        "cam_setup_sequence": f"{_BASE_URL}/cam/setup",  # /{id}/sequence
        
        # Tool management
        "cam_tools": f"{_BASE_URL}/cam/tools",
        "cam_tool": f"{_BASE_URL}/cam/tool",
        
        # Tool library endpoints
        "tool_libraries": f"{_BASE_URL}/tool-libraries",
        "tool_library_tools": f"{_BASE_URL}/tool-libraries",  # /{library_id}/tools
        "tool_details": f"{_BASE_URL}/tools",  # /{tool_id}
        "tool_create": f"{_BASE_URL}/tool-libraries",  # /{library_id}/tools
        "tool_modify": f"{_BASE_URL}/tools",  # /{tool_id}
        "tool_duplicate": f"{_BASE_URL}/tools",  # /{tool_id}/duplicate
        "tool_delete": f"{_BASE_URL}/tools",  # /{tool_id}
        "tool_search": f"{_BASE_URL}/tools/search",
    },
    
    "utility": {
        # System operations
        "test_connection": f"{_BASE_URL}/test_connection",
        "undo": f"{_BASE_URL}/undo",
        "delete_everything": f"{_BASE_URL}/delete_everything",
        "destroy": f"{_BASE_URL}/destroy",
        
        # Export operations
        "export_step": f"{_BASE_URL}/Export_STEP",
        "export_stl": f"{_BASE_URL}/Export_STL",
        
        # Parameter management
        "count_parameters": f"{_BASE_URL}/count_parameters",
        "list_parameters": f"{_BASE_URL}/list_parameters",
        "change_parameter": f"{_BASE_URL}/set_parameter",
        
        # Legacy/special endpoints
        "witzenmann": f"{_BASE_URL}/Witzenmann",
    },
    
    "debug": {
        # Debug and development tools will be added here
    }
}


def get_base_url() -> str:
    """
    Returns the Fusion 360 base URL.
    
    Returns:
        str: Base URL for Fusion 360 communication
    """
    logger.debug("Getting base URL")
    return _BASE_URL


def get_endpoints(category: Optional[str] = None) -> Dict[str, str]:
    """
    Returns endpoints by category.
    
    Args:
        category: Optional category filter (cad, cam, utility, debug)
        
    Returns:
        dict: Dictionary of endpoint names to URLs
    """
    logger.debug(f"Getting endpoints for category: {category}")
    
    if category is None:
        # Return all endpoints flattened
        all_endpoints = {}
        for cat_endpoints in _ENDPOINTS.values():
            all_endpoints.update(cat_endpoints)
        return all_endpoints
    
    if not isinstance(category, str):
        logger.warning(f"Category must be a string, got {type(category)}: {category}")
        return {}
        
    category_lower = category.lower()
    if category_lower in _ENDPOINTS:
        return _ENDPOINTS[category_lower].copy()
    else:
        logger.warning(f"Unknown category: {category}")
        return {}


def get_headers() -> Dict[str, str]:
    """
    Returns HTTP headers for requests.
    
    Returns:
        dict: Standard HTTP headers
    """
    logger.debug("Getting HTTP headers")
    return _HEADERS.copy()


def get_timeout() -> int:
    """
    Returns request timeout value.
    
    Returns:
        int: Timeout in seconds
    """
    logger.debug("Getting request timeout")
    return _REQUEST_TIMEOUT


def validate_configuration() -> bool:
    """
    Validate configuration integrity.
    
    Returns:
        bool: True if configuration is valid
    """
    logger.info("Validating configuration")
    
    # Check base URL is set
    if not _BASE_URL:
        logger.error("Base URL is not configured")
        return False
    
    # Check timeout is positive
    if _REQUEST_TIMEOUT <= 0:
        logger.error("Request timeout must be positive")
        return False
    
    # Check headers are present
    if not _HEADERS:
        logger.error("Headers are not configured")
        return False
    
    # Check each category has endpoints
    for category, endpoints in _ENDPOINTS.items():
        if not isinstance(endpoints, dict):
            logger.error(f"Category {category} endpoints must be a dictionary")
            return False
    
    logger.info("Configuration validation passed")
    return True


def get_categories() -> list[str]:
    """
    Get list of available endpoint categories.
    
    Returns:
        list: List of category names
    """
    return list(_ENDPOINTS.keys())