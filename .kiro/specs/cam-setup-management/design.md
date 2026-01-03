# CAM Setup Management Design Document

## Overview

The CAM Setup Management feature extends the Fusion 360 MCP Server to provide comprehensive setup creation, configuration, and management capabilities. This feature bridges the gap between basic CAM operations and the organizational structure that setups provide, enabling AI assistants to create and manage manufacturing workflows through natural language commands.

The design leverages the existing modular architecture, adding new tools to the `Server/tools/cam/` directory while extending the Fusion Add-In with setup-specific functionality. The implementation maintains consistency with existing CAM tools and integrates seamlessly with current toolpath management capabilities.

## Architecture

### Component Overview

The CAM Setup Management feature follows the established two-tier architecture:

1. **MCP Server Layer** (`Server/tools/cam/setups.py`)
   - Exposes setup management tools to AI assistants
   - Handles request validation and error formatting
   - Integrates with existing CAM tool patterns

2. **Fusion Add-In Layer** (`FusionMCPBridge/cam.py` extensions)
   - Implements Fusion 360 API interactions
   - Manages setup creation, modification, and deletion
   - Provides helper functions for setup-toolpath relationships
   - **May require Design workspace integration** for model selection and geometry updates

### Integration Points

- **Existing Toolpath Tools**: Setup tools will enhance existing toolpath listing by providing setup context
- **CAM Validation**: Leverages existing `validate_cam_product_with_details()` function
- **Error Handling**: Uses established error codes and HTTP status mapping
- **Configuration**: Extends existing CAM endpoint configuration in `Server/core/config.py`
- **Design Workspace Integration**: May require integration with design tools for model selection and geometry updates
- **Naming Convention Updates**: Update references from "CAD" to "Design" throughout the codebase

## Components and Interfaces

### MCP Server Tools (`Server/tools/cam/setups.py`)

#### Core Setup Management Tools

```python
@mcp.tool()
def create_cam_setup(name: str = None, stock_mode: str = "auto", coordinate_system: dict = None) -> dict:
    """Create a new CAM setup with specified configuration."""

@mcp.tool()
def list_cam_setups(include_toolpaths: bool = True) -> dict:
    """List all CAM setups with optional toolpath information."""

@mcp.tool()
def get_setup_details(setup_id: str) -> dict:
    """Get detailed information about a specific setup."""

@mcp.tool()
def modify_setup_configuration(setup_id: str, updates: dict) -> dict:
    """Modify existing setup configuration."""

@mcp.tool()
def delete_cam_setup(setup_id: str, confirm: bool = False) -> dict:
    """Delete a CAM setup with confirmation."""

@mcp.tool()
def duplicate_cam_setup(setup_id: str, new_name: str = None) -> dict:
    """Create a duplicate of an existing setup."""
```

#### Setup-Toolpath Integration Tools

```python
@mcp.tool()
def get_setup_toolpaths(setup_id: str) -> dict:
    """Get all toolpaths within a specific setup using existing toolpath functionality."""

@mcp.tool()
def find_toolpath_setup(toolpath_id: str) -> dict:
    """Find which setup contains a specific toolpath."""

@mcp.tool()
def move_toolpath_to_setup(toolpath_id: str, target_setup_id: str) -> dict:
    """Move a toolpath from one setup to another."""
```

### Fusion Add-In Extensions (`FusionMCPBridge/cam.py`)

#### Setup Management Functions

```python
def create_setup(name: str, stock_config: dict, coordinate_system: dict) -> dict:
    """Create a new CAM setup with specified configuration."""

def list_setups_detailed() -> dict:
    """List all setups with comprehensive configuration details."""

def get_setup_by_id(setup_id: str) -> dict:
    """Retrieve detailed setup information by ID."""

def modify_setup(setup_id: str, updates: dict) -> dict:
    """Update setup configuration with validation."""

def delete_setup(setup_id: str) -> dict:
    """Remove a setup and handle dependent operations."""

def duplicate_setup(source_id: str, new_name: str) -> dict:
    """Create a copy of an existing setup."""
```

#### Helper Functions

```python
def get_toolpaths_for_setup(setup_id: str) -> dict:
    """Get toolpaths within a setup using existing toolpath serialization."""

def find_setup_for_toolpath(toolpath_id: str) -> Optional[str]:
    """Find the parent setup ID for a given toolpath."""

def validate_setup_toolpath_relationship(setup_id: str, toolpath_id: str) -> bool:
    """Validate that a toolpath belongs to a specific setup."""
```

### HTTP Endpoints

New endpoints will be added to the Fusion Add-In HTTP server:

- `POST /cam/setups` - Create new setup
- `GET /cam/setups` - List all setups
- `GET /cam/setups/{id}` - Get setup details
- `PUT /cam/setups/{id}` - Modify setup
- `DELETE /cam/setups/{id}` - Delete setup
- `POST /cam/setups/{id}/duplicate` - Duplicate setup
- `GET /cam/setups/{id}/toolpaths` - Get setup toolpaths
- `GET /cam/toolpaths/{id}/setup` - Get toolpath's setup

## Data Models

### Setup Configuration Model

```python
{
    "id": "string",           # Unique setup identifier
    "name": "string",         # Setup name
    "model_id": "string",     # Model ID reference (root level, not under WCS)
    "wcs": {                  # Work Coordinate System (using Fusion 360 terminology)
        # NOTE: This structure needs to be determined through API research
        # Based on Fusion 360 UI, this should include:
        # - Orientation options (model-based, face-based, etc.)
        # - Origin selection (model origin, geometry-based, custom point)
        # - Axis alignment options
        "type": "string",     # To be determined from API investigation
        "origin": {},         # Structure TBD from API research
        "orientation": {},    # Structure TBD from API research
    },
    "stock": {
        "mode": "string",     # "auto", "geometry", "box", "cylinder"
        "geometry_id": "string",  # Reference to stock geometry
        "dimensions": {       # For primitive stock
            "length": float,
            "width": float,
            "height": float,
            "diameter": float  # For cylindrical stock
        },
        "position": [x, y, z], # Stock position relative to WCS
        "material": "string"   # Material name
    },
    "toolpaths": [           # List of contained toolpaths
        {
            "id": "string",
            "name": "string",
            "type": "string",
            "tool_name": "string",
            "is_valid": boolean
        }
    ],
    "created_date": "string",
    "modified_date": "string"
}
```

### Setup Creation Request Model

```python
{
    "name": "string",        # Optional - auto-generated if not provided
    "model_id": "string",    # Model ID reference (root level)
    "stock_mode": "string",  # "auto", "geometry", "box", "cylinder"
    "stock_config": {
        "geometry_id": "string",    # For geometry mode
        "dimensions": {...},        # For primitive modes
        "position": [x, y, z],     # Optional positioning
        "material": "string"        # Optional material
    },
    "wcs": {                 # Work Coordinate System (Fusion 360 terminology)
        # NOTE: Structure to be determined through API research
        # Must support Fusion 360's actual WCS configuration options:
        # - Orientation selection methods
        # - Origin specification methods  
        "config": {}         # Structure TBD from API investigation
    }
}
```

### Fusion 360 Business Language Requirements

The implementation must use Fusion 360's actual business terminology:
- **WCS** instead of "coordinate_system" 
- **Model** at root level, not nested under WCS
- Other Fusion 360 specific terms as discovered during API research

**Note**: This terminology consistency should be documented in steering files to ensure all future development follows Fusion 360's business language.

### Research Requirements

Before implementation, the following API research is required:

1. **Work Coordinate System API Investigation**
   - Examine `adsk.cam.Setup` WCS properties and methods
   - Understand available orientation options (model-based, face-based, etc.)
   - Determine origin specification methods (model origin, geometry-based, custom)
   - **Investigate model selection API - likely returns model IDs rather than predefined options**
   - Document actual API structure and available options

2. **WCS Configuration Methods**
   - Research how to programmatically set WCS orientation
   - Understand origin positioning API
   - Investigate axis alignment and reference selection
   - **Research model ID resolution and validation**
   - Document required parameters and data structures

3. **Model Selection and Design Integration**
   - **Investigate how model IDs are obtained and validated**
   - Determine if design workspace modifications are required for setup creation
   - Research integration between CAM setup creation and design workspace operations
   - **Document model ID structure and how to reference design geometry**
   - Document any required design geometry updates or modifications

4. **Fusion 360 Business Language Alignment**
   - Use "WCS" instead of "coordinate_system" throughout implementation
   - Place model references at root level, not nested under WCS
   - Update terminology from "CAD" to "Design" to match Fusion 360 workspace naming
   - **Create steering file documentation for Fusion 360 business language consistency**
   - Review existing code for terminology that should be updated

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Properties 1.1, 1.4, and 1.5 can be combined into a comprehensive setup creation property
- Properties 2.1, 2.2, and 2.3 can be combined into coordinate system configuration property
- Properties 4.1, 4.2, and 4.3 can be combined into setup information retrieval property
- Properties 9.1, 9.2, and 10.5 can be combined into toolpath-setup association property
- Properties 11.1, 11.2, and 11.3 can be combined into bidirectional relationship property

### Core Properties

**Property 1: Setup creation completeness**
*For any* valid setup creation request, the system should create a setup with correct name (specified or auto-generated), default coordinate system, automatic stock detection, and return complete setup details including ID
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

**Property 2: WCS configuration consistency**
*For any* valid WCS specification (following actual Fusion 360 WCS API structure), the system should configure the work coordinate system correctly according to the specified orientation, origin, and model reference options
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

**Note**: This property requires API research to determine the actual structure and validation rules for Fusion 360 WCS.

**Property 3: Stock configuration accuracy**
*For any* valid stock specification (dimensions, geometry, position, material), the system should create stock that matches the specification and position it correctly relative to the work coordinate system
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

**Property 4: Setup information retrieval consistency**
*For any* setup query (list all, get details, query by ID), the system should return accurate and complete setup information including all configuration details
**Validates: Requirements 4.1, 4.2, 4.3**

**Property 5: Setup modification preservation**
*For any* valid setup modification, the system should update the specified properties while preserving existing operations and providing warnings when changes affect operations
**Validates: Requirements 5.1, 5.2, 5.3, 5.5**

**Property 6: Setup deletion completeness**
*For any* setup deletion request, the system should remove the setup and all associated operations, provide warnings for active toolpaths, and return appropriate confirmation or error messages
**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

**Property 7: Setup duplication fidelity**
*For any* setup duplication request, the system should create a new setup with identical configuration (coordinate systems, stock, operations) and proper naming (specified or auto-generated unique name)
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

**Property 8: Multi-setup document consistency**
*For any* document with multiple setups, the system should maintain unique identifiers, prevent naming conflicts, manage shared resources appropriately, and maintain document state consistency
**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

**Property 9: Toolpath-setup association integrity**
*For any* toolpath operation, the system should maintain correct setup association, include setup context in responses, validate setup permissions, and update associations when toolpaths are moved
**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

**Property 10: Existing functionality integration**
*For any* setup-related toolpath query, the system should use existing toolpath functions with setup filtering and return full toolpath details using current serialization while providing setup context
**Validates: Requirements 10.1, 10.2, 10.3, 10.5**

**Property 11: Bidirectional relationship consistency**
*For any* setup-toolpath relationship query, the system should provide accurate bidirectional mapping (setup-to-toolpaths and toolpath-to-setup) with consistent ID mapping and detailed error context
**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

**Property 12: Error handling robustness**
*For any* invalid input (coordinate systems, stock configurations, setup modifications, non-existent IDs), the system should reject the operation, provide clear error messages, and maintain system state integrity
**Validates: Requirements 2.5, 3.5, 5.4, 6.5, 7.5, 9.5**

## Error Handling

### Error Categories

1. **Validation Errors**
   - Invalid coordinate system specifications
   - Invalid stock configurations
   - Invalid setup modifications
   - Malformed request parameters

2. **Resource Errors**
   - Setup not found
   - Toolpath not found
   - CAM document not available
   - Insufficient permissions

3. **State Errors**
   - Setup deletion with active toolpaths
   - Coordinate system changes affecting operations
   - Resource conflicts between setups
   - Document state inconsistencies

4. **System Errors**
   - Fusion 360 API failures
   - CAM workspace not active
   - Document access issues
   - Internal processing errors

### Error Response Format

All errors follow the established pattern:

```python
{
    "error": True,
    "message": "Human-readable error description",
    "code": "ERROR_CODE_CONSTANT",
    "context": {
        "setup_id": "string",      # When applicable
        "toolpath_id": "string",   # When applicable
        "operation": "string"      # Operation being performed
    }
}
```

### Error Codes

- `SETUP_NOT_FOUND` - Requested setup does not exist
- `INVALID_SETUP_CONFIG` - Setup configuration is invalid
- `SETUP_HAS_TOOLPATHS` - Cannot delete setup with active toolpaths
- `COORDINATE_SYSTEM_INVALID` - Invalid coordinate system specification
- `STOCK_CONFIG_INVALID` - Invalid stock configuration
- `TOOLPATH_SETUP_MISMATCH` - Toolpath does not belong to specified setup
- `SETUP_NAME_CONFLICT` - Setup name already exists
- `SETUP_MODIFICATION_FAILED` - Setup modification could not be applied
- `DUPLICATION_FAILED` - Setup duplication failed

## Testing Strategy

### Unit Testing Approach

Unit tests will focus on:
- Setup creation with various configurations
- Coordinate system validation and positioning
- Stock configuration and validation
- Setup modification and state preservation
- Error handling for invalid inputs
- Integration with existing toolpath functions

### Property-Based Testing Approach

The implementation will use **Hypothesis** for Python property-based testing. Each correctness property will be implemented as a property-based test with a minimum of 100 iterations.

Property-based tests will:
- Generate random valid setup configurations
- Test setup creation, modification, and deletion operations
- Verify coordinate system and stock configuration accuracy
- Test toolpath-setup relationship integrity
- Validate error handling with invalid inputs

### Test Tagging

Each property-based test will be tagged with:
```python
# **Feature: cam-setup-management, Property 1: Setup creation completeness**
```

### Integration Testing

Integration tests will verify:
- End-to-end setup management workflows
- Integration with existing CAM toolpath functionality
- HTTP endpoint functionality
- MCP tool registration and execution
- Error propagation through the system layers

### Test Data Management

Tests will use:
- Generated test CAM documents with various configurations
- Mock Fusion 360 API responses for edge cases
- Predefined setup configurations for consistency testing
- Invalid input datasets for error handling validation
