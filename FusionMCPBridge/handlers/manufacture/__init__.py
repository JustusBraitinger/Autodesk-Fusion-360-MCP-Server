"""
MANUFACTURE Workspace Handler Package

This package provides the interface to MANUFACTURE workspace (CAM) functionality.
Business logic is organized into modular submodules:

- cam_utils.py - Shared CAM utilities
- setups.py - Setup management
- stock.py - Stock configuration
- wcs.py - Work Coordinate System configuration
- operations/ - Operation-level functionality
  - toolpaths.py - Toolpath operations
  - heights.py - Height parameters and validation
  - passes.py - Multi-pass configuration
  - linking.py - Linking parameters
  - tools.py - Operation tools and settings
- tool_libraries/ - Tool library management

This __init__.py re-exports commonly used functions for convenient access.
"""

# Import submodules to ensure handler registration
from . import setups
from . import operations
from . import tool_libraries
from . import stock
from . import wcs
from . import cam_utils

# =============================================================================
# Re-export from cam_utils
# =============================================================================
from .cam_utils import (
    get_cam_product,
    validate_cam_product_with_details,
    find_operation_by_id,
    find_setup_by_id,
    get_operation_type,
    get_tool_type_string,
    get_param_value,
    get_parameter_metadata,
)

# =============================================================================
# Re-export from toolpaths handler
# =============================================================================
from .operations.toolpaths import (
    list_all_toolpaths_impl as list_all_toolpaths,
    list_toolpaths_with_heights_impl as list_toolpaths_with_heights,
    get_toolpath_parameters_impl as get_toolpath_parameters,
    analyze_setup_sequence_impl as analyze_setup_sequence,
)

# =============================================================================
# Re-export from heights handler
# =============================================================================
from .operations.heights import (
    get_detailed_heights_impl as get_detailed_heights,
    validate_height_value,
    validate_height_hierarchy,
)

# =============================================================================
# Re-export from linking handler
# =============================================================================
from .operations.linking import (
    get_toolpath_linking_impl as get_toolpath_linking,
)

# =============================================================================
# Re-export from tools handler
# =============================================================================
from .operations.tools import (
    list_all_tools_impl as list_all_tools,
    extract_tool_settings,
)

# =============================================================================
# Re-export from setups handler
# =============================================================================
from .setups import (
    list_setups_detailed,
    get_setup_by_id_impl as get_setup_by_id,
    create_setup_impl as create_setup,
)

# =============================================================================
# Re-export from stock handler
# =============================================================================
from .stock import (
    configure_stock,
    validate_stock_configuration,
    configure_automatic_stock,
    configure_geometry_stock,
    configure_box_stock,
    configure_cylinder_stock,
    apply_stock_material,
)

# =============================================================================
# Re-export from WCS handler
# =============================================================================
from .wcs import (
    configure_wcs,
    validate_wcs_configuration,
    integrate_model_id_with_wcs,
    validate_orientation_vectors,
)

__all__ = [
    # Submodules
    'setups',
    'operations',
    'tool_libraries',
    'stock',
    'wcs',
    'cam_utils',
    # CAM utilities
    'get_cam_product',
    'validate_cam_product_with_details',
    'find_operation_by_id',
    'find_setup_by_id',
    'get_operation_type',
    'get_tool_type_string',
    'get_param_value',
    'get_parameter_metadata',
    # Toolpaths
    'list_all_toolpaths',
    'list_toolpaths_with_heights',
    'get_toolpath_parameters',
    'analyze_setup_sequence',
    # Heights
    'get_detailed_heights',
    'validate_height_value',
    'validate_height_hierarchy',
    # Linking
    'get_toolpath_linking',
    # Tools
    'list_all_tools',
    'extract_tool_settings',
    # Setups
    'list_setups_detailed',
    'get_setup_by_id',
    'create_setup',
    # Stock
    'configure_stock',
    'validate_stock_configuration',
    'configure_automatic_stock',
    'configure_geometry_stock',
    'configure_box_stock',
    'configure_cylinder_stock',
    'apply_stock_material',
    # WCS
    'configure_wcs',
    'validate_wcs_configuration',
    'integrate_model_id_with_wcs',
    'validate_orientation_vectors',
]
