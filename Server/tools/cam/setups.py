"""
CAM Setup Management Tools

This module contains tools for CAM setup management:
- create_cam_setup: Create new CAM setups with configuration
- list_cam_setups: List all CAM setups with details
- get_setup_details: Get detailed setup information
- modify_setup_configuration: Modify existing setup configuration
- delete_cam_setup: Delete CAM setups with confirmation
- duplicate_cam_setup: Duplicate existing setups
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.config import get_endpoints, get_timeout
from core.request_handler import send_request, send_get_request

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register setup management tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(create_cam_setup)
    mcp.tool()(list_cam_setups)
    mcp.tool()(get_setup_details)
    mcp.tool()(modify_setup_configuration)
    mcp.tool()(delete_cam_setup)
    mcp.tool()(duplicate_cam_setup)

def create_cam_setup(name: str = None, stock_mode: str = "auto", wcs_config: dict = None, model_id: str = None) -> dict:
    """
    Create a new CAM setup with specified configuration.
    
    This tool creates a new CAM setup in Fusion 360 with the specified name, stock configuration,
    and work coordinate system (WCS) settings. The setup serves as a container for machining
    operations and defines the coordinate system and stock material for manufacturing.
    
    Args:
        name: Optional setup name. If not provided, a descriptive name will be generated
              based on the selected geometry or a default pattern
        stock_mode: Stock configuration mode. Options:
                   - "auto": Automatically detect stock from selected bodies (default)
                   - "geometry": Use existing geometry as stock reference
                   - "box": Create primitive box stock with specified dimensions
                   - "cylinder": Create primitive cylinder stock with specified dimensions
        wcs_config: Optional Work Coordinate System configuration. If not provided,
                   defaults to model origin with standard orientation. Structure:
                   {
                       "origin": {"x": 0.0, "y": 0.0, "z": 0.0},  # Origin point
                       "orientation": "model_based",  # or "face_based", "custom"
                       "reference_geometry": "geometry_id"  # For face-based orientation
                   }
        model_id: Optional model ID reference for geometry selection. If not provided,
                 the system will use the active design model
    
    Returns:
        dict: Setup creation result with setup details or error information
              Success response includes:
              - setup_id: Unique identifier for the created setup
              - name: Final setup name (generated or specified)
              - wcs: Work coordinate system configuration
              - stock: Stock configuration details
              - created_date: Setup creation timestamp
              
              Error response includes:
              - error: True
              - message: Human-readable error description
              - code: Error code (SETUP_CREATION_FAILED, INVALID_CONFIG, etc.)
    
    Example usage:
        # Create setup with automatic stock detection
        create_cam_setup(name="Roughing Setup", stock_mode="auto")
        
        # Create setup with custom WCS and box stock
        create_cam_setup(
            name="Finishing Setup",
            stock_mode="box",
            wcs_config={
                "origin": {"x": 10.0, "y": 5.0, "z": 0.0},
                "orientation": "model_based"
            }
        )
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5 (Setup creation with basic configuration)
    """
    try:
        endpoint = get_endpoints("cam")["cam_setups"]
        payload = {
            "name": name,
            "stock_mode": stock_mode,
            "wcs_config": wcs_config,
            "model_id": model_id
        }
        return send_request(endpoint, payload)
    except Exception as e:
        logging.error("Create CAM setup failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to create CAM setup: {str(e)}",
            "code": "SETUP_CREATION_FAILED"
        }

def list_cam_setups(include_toolpaths: bool = True) -> dict:
    """
    List all CAM setups with comprehensive configuration details.
    
    This tool returns all CAM setups in the current Fusion 360 document with detailed
    information including WCS configuration, stock definition, toolpath count, and
    setup metadata. Uses proper Fusion 360 WCS terminology throughout.
    
    Args:
        include_toolpaths: Whether to include toolpath information for each setup.
                          Default is True. When False, only setup configuration is returned.
    
    Returns:
        dict: List of all setups with detailed information
              Success response includes:
              - setups: Array of setup objects with:
                - id: Unique setup identifier
                - name: Setup name
                - wcs: Work coordinate system configuration
                - stock: Stock definition and positioning
                - toolpaths: Array of contained toolpaths (if include_toolpaths=True)
                - created_date: Setup creation timestamp
                - modified_date: Last modification timestamp
              - total_count: Total number of setups
              - message: Status message or null
              
              Error response includes:
              - error: True
              - message: Human-readable error description
              - code: Error code (CAM_NOT_AVAILABLE, CONNECTION_ERROR, etc.)
    
    Example response:
        {
            "setups": [
                {
                    "id": "setup_001",
                    "name": "Roughing Setup",
                    "wcs": {
                        "origin": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "orientation": "model_based"
                    },
                    "stock": {
                        "mode": "auto",
                        "dimensions": {"length": 100.0, "width": 50.0, "height": 25.0}
                    },
                    "toolpaths": [
                        {
                            "id": "op_001",
                            "name": "Adaptive Clearing",
                            "type": "adaptive",
                            "tool_name": "6mm Flat Endmill",
                            "is_valid": true
                        }
                    ],
                    "created_date": "2025-01-03T10:30:00Z"
                }
            ],
            "total_count": 1,
            "message": null
        }
    
    Typical use cases:
    - Getting overview of all manufacturing setups
    - Finding setup IDs for detailed inspection
    - Understanding setup organization and toolpath distribution
    
    Requirements: 4.1, 4.2 (Setup listing with basic and detailed properties)
    """
    try:
        endpoint = get_endpoints("cam")["cam_setups"]
        params = {"include_toolpaths": include_toolpaths}
        return send_get_request(endpoint, params=params)
    except Exception as e:
        logging.error("List CAM setups failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to list CAM setups: {str(e)}",
            "code": "SETUP_LIST_FAILED"
        }

def get_setup_details(setup_id: str) -> dict:
    """
    Get detailed information about a specific CAM setup.
    
    This tool retrieves comprehensive configuration details for a specific setup,
    including WCS configuration, stock definition, contained toolpaths, and metadata.
    Use this after list_cam_setups() to inspect the full configuration of a specific setup.
    
    Args:
        setup_id: Unique identifier of the setup to retrieve. Must match exactly
                 what was returned by list_cam_setups()
    
    Returns:
        dict: Detailed setup information or error
              Success response includes:
              - id: Setup identifier
              - name: Setup name
              - model_id: Model reference (root level)
              - wcs: Complete Work Coordinate System configuration
              - stock: Complete stock definition and positioning
              - toolpaths: Array of all contained toolpaths with details
              - created_date: Setup creation timestamp
              - modified_date: Last modification timestamp
              - operation_count: Number of machining operations
              - is_valid: Whether setup configuration is valid
              
              Error response includes:
              - error: True
              - message: Human-readable error description
              - code: Error code (SETUP_NOT_FOUND, CAM_NOT_AVAILABLE, etc.)
    
    Example usage:
        get_setup_details("setup_001")
    
    Example response:
        {
            "id": "setup_001",
            "name": "Roughing Setup",
            "model_id": "model_123",
            "wcs": {
                "origin": {"x": 0.0, "y": 0.0, "z": 0.0},
                "orientation": "model_based",
                "x_axis": {"x": 1.0, "y": 0.0, "z": 0.0},
                "y_axis": {"x": 0.0, "y": 1.0, "z": 0.0},
                "z_axis": {"x": 0.0, "y": 0.0, "z": 1.0}
            },
            "stock": {
                "mode": "auto",
                "geometry_id": "body_456",
                "dimensions": {"length": 100.0, "width": 50.0, "height": 25.0},
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "material": "Aluminum 6061"
            },
            "toolpaths": [...],
            "created_date": "2025-01-03T10:30:00Z",
            "modified_date": "2025-01-03T11:15:00Z",
            "operation_count": 3,
            "is_valid": true
        }
    
    Requirements: 4.3 (Query setup by ID with specific details or error)
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_setup']}/{setup_id}"
        return send_get_request(endpoint)
    except Exception as e:
        logging.error("Get setup details failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to get setup details: {str(e)}",
            "code": "SETUP_DETAILS_FAILED"
        }

def modify_setup_configuration(setup_id: str, updates: dict) -> dict:
    """
    Modify existing CAM setup configuration.
    
    This tool updates the configuration of an existing setup while preserving
    existing operations where possible. It validates changes and provides warnings
    when modifications might affect existing toolpaths.
    
    Args:
        setup_id: Unique identifier of the setup to modify
        updates: Dictionary containing the configuration updates. Supported fields:
                - name: New setup name
                - wcs: Work coordinate system updates
                - stock: Stock configuration updates
                - model_id: Model reference updates
                
                Example updates structure:
                {
                    "name": "Updated Setup Name",
                    "wcs": {
                        "origin": {"x": 10.0, "y": 5.0, "z": 0.0}
                    },
                    "stock": {
                        "mode": "box",
                        "dimensions": {"length": 120.0, "width": 60.0, "height": 30.0}
                    }
                }
    
    Returns:
        dict: Modification result with updated setup information or error
              Success response includes:
              - setup_id: Setup identifier
              - updated_fields: List of fields that were modified
              - warnings: Array of warnings about potential impacts on operations
              - setup: Updated setup configuration
              - modified_date: Timestamp of modification
              
              Error response includes:
              - error: True
              - message: Human-readable error description
              - code: Error code (SETUP_NOT_FOUND, INVALID_UPDATES, etc.)
    
    Example usage:
        modify_setup_configuration("setup_001", {
            "name": "Revised Roughing Setup",
            "stock": {
                "mode": "box",
                "dimensions": {"length": 110.0, "width": 55.0, "height": 28.0}
            }
        })
    
    Requirements: 5.1, 5.2, 5.3, 5.5 (Modify setup properties with validation and warnings)
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_setup']}/{setup_id}"
        payload = {"updates": updates}
        return send_request(endpoint, payload, method="PUT")
    except Exception as e:
        logging.error("Modify setup configuration failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to modify setup configuration: {str(e)}",
            "code": "SETUP_MODIFICATION_FAILED"
        }

def delete_cam_setup(setup_id: str, confirm: bool = False) -> dict:
    """
    Delete a CAM setup with confirmation and impact warnings.
    
    This tool removes a CAM setup and all associated operations. It provides warnings
    about data loss when the setup contains active toolpaths and requires explicit
    confirmation for deletion.
    
    Args:
        setup_id: Unique identifier of the setup to delete
        confirm: Explicit confirmation flag. Must be True to proceed with deletion.
                If False, returns impact analysis without deleting.
    
    Returns:
        dict: Deletion result or impact analysis
              When confirm=False (impact analysis):
              - setup_id: Setup identifier
              - setup_name: Setup name
              - toolpath_count: Number of toolpaths that will be deleted
              - operation_count: Number of operations that will be deleted
              - warnings: Array of warnings about data loss
              - requires_confirmation: True
              
              When confirm=True (actual deletion):
              - deleted: True
              - setup_id: Deleted setup identifier
              - setup_name: Name of deleted setup
              - deleted_operations: Count of deleted operations
              - deleted_toolpaths: Count of deleted toolpaths
              - deletion_date: Timestamp of deletion
              
              Error response includes:
              - error: True
              - message: Human-readable error description
              - code: Error code (SETUP_NOT_FOUND, DELETION_FAILED, etc.)
    
    Example usage:
        # First, get impact analysis
        delete_cam_setup("setup_001", confirm=False)
        
        # Then, confirm deletion
        delete_cam_setup("setup_001", confirm=True)
    
    Requirements: 6.1, 6.2, 6.3 (Delete setup with warnings and confirmation)
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_setup']}/{setup_id}"
        payload = {"confirm": confirm}
        return send_request(endpoint, payload, method="DELETE")
    except Exception as e:
        logging.error("Delete CAM setup failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to delete CAM setup: {str(e)}",
            "code": "SETUP_DELETION_FAILED"
        }

def duplicate_cam_setup(setup_id: str, new_name: str = None) -> dict:
    """
    Create a duplicate of an existing CAM setup.
    
    This tool creates a complete copy of an existing setup including WCS configuration,
    stock definition, and operation templates. The duplicate setup will have identical
    configuration but a unique name and identifier.
    
    Args:
        setup_id: Unique identifier of the setup to duplicate
        new_name: Optional name for the duplicated setup. If not provided,
                 a unique name will be generated based on the original setup name
                 (e.g., "Original Setup Copy", "Original Setup Copy 2", etc.)
    
    Returns:
        dict: Duplication result with new setup information or error
              Success response includes:
              - original_setup_id: ID of the source setup
              - new_setup_id: ID of the created duplicate
              - new_setup_name: Name of the duplicated setup
              - copied_elements: List of configuration elements that were copied
              - duplication_date: Timestamp of duplication
              - setup: Complete configuration of the new setup
              
              Error response includes:
              - error: True
              - message: Human-readable error description
              - code: Error code (SETUP_NOT_FOUND, DUPLICATION_FAILED, etc.)
    
    Example usage:
        # Duplicate with automatic name generation
        duplicate_cam_setup("setup_001")
        
        # Duplicate with custom name
        duplicate_cam_setup("setup_001", new_name="Finishing Setup")
    
    Example response:
        {
            "original_setup_id": "setup_001",
            "new_setup_id": "setup_002",
            "new_setup_name": "Roughing Setup Copy",
            "copied_elements": ["wcs", "stock", "operations"],
            "duplication_date": "2025-01-03T12:00:00Z",
            "setup": {
                "id": "setup_002",
                "name": "Roughing Setup Copy",
                "wcs": {...},
                "stock": {...}
            }
        }
    
    Requirements: 7.1, 7.2, 7.3, 7.4 (Duplicate setup with identical configuration and naming)
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_setup_duplicate']}/{setup_id}/duplicate"
        payload = {"new_name": new_name}
        return send_request(endpoint, payload)
    except Exception as e:
        logging.error("Duplicate CAM setup failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to duplicate CAM setup: {str(e)}",
            "code": "SETUP_DUPLICATION_FAILED"
        }