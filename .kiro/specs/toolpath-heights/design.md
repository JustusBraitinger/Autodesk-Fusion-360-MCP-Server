# Design Document

## Overview

This design extends the existing Fusion 360 MCP integration to provide comprehensive height parameter access when querying toolpaths. The solution builds upon the current CAM functionality in `FusionMCPBridge/cam.py` and adds new MCP tools to the server for streamlined height information retrieval.

## Architecture

The enhancement follows the established two-component architecture:

1. **MCP Server Extension** (`/Server/MCP_Server.py`): New tools for height-enabled toolpath queries
2. **Fusion Add-In Enhancement** (`/FusionMCPBridge/FusionMCPBridge.py`): New HTTP endpoints for height data
3. **CAM Module Enhancement** (`/FusionMCPBridge/cam.py`): Enhanced height parameter extraction

### Communication Flow
```
AI Assistant → MCP Server → HTTP Request → Fusion Add-In → Enhanced CAM Functions → Fusion 360 API
```

## Components and Interfaces

### 1. MCP Server Tools (`/Server/MCP_Server.py`)

#### New Tool: `list_toolpaths_with_heights()`
- **Purpose**: List all toolpaths with their height parameters in a single call
- **Parameters**: 
  - `include_details` (optional bool): Include full parameter details vs summary
- **Returns**: Toolpath list with embedded height information

#### New Tool: `get_toolpath_heights(toolpath_id: str)`
- **Purpose**: Get detailed height information for a specific toolpath
- **Parameters**:
  - `toolpath_id` (required str): The toolpath identifier
- **Returns**: Comprehensive height parameter data

### 2. HTTP Endpoints (`/FusionMCPBridge/FusionMCPBridge.py`)

#### New Endpoint: `GET /cam/toolpaths/heights`
- **Purpose**: List all toolpaths with height parameters
- **Response**: JSON array of toolpaths with embedded height data

#### New Endpoint: `GET /cam/toolpath/{id}/heights`
- **Purpose**: Get height parameters for specific toolpath
- **Response**: JSON object with detailed height information

### 3. CAM Module Enhancements (`/FusionMCPBridge/cam.py`)

#### Enhanced Function: `_extract_heights_params()`
The existing function will be enhanced to extract complete height information including:
- Expression values (e.g., "stockTop + 5mm")
- Evaluated numeric values
- Parameter metadata (editable, min/max constraints)
- Unit information

**Note**: Based on research of the current Fusion 360 API implementation, "from" reference points and offset values may not be directly accessible as separate properties. Height parameters appear to be stored as expressions (e.g., "stockTop + 5mm") where the reference and offset are embedded in the expression string.

#### New Function: `list_toolpaths_with_heights()`
- **Purpose**: Combine toolpath listing with height extraction
- **Returns**: Toolpaths with embedded height parameters

#### New Function: `get_detailed_heights()`
- **Purpose**: Extract comprehensive height information for a single toolpath
- **Returns**: Complete height parameter structure

## Data Models

### Height Parameter Structure
```json
{
  "clearance_height": {
    "value": 25.0,
    "unit": "mm",
    "expression": "stockTop + 5mm",
    "type": "numeric",
    "editable": true,
    "min_value": null,
    "max_value": null
  },
  "retract_height": {
    "value": 15.0,
    "unit": "mm", 
    "expression": "stockTop",
    "type": "numeric",
    "editable": true,
    "min_value": null,
    "max_value": null
  },
  "feed_height": {
    "value": 2.0,
    "unit": "mm",
    "expression": "stockTop - 3mm",
    "type": "numeric",
    "editable": true,
    "min_value": null,
    "max_value": null
  },
  "top_height": {
    "value": 0.0,
    "unit": "mm",
    "expression": "stockTop",
    "type": "numeric",
    "editable": true,
    "min_value": null,
    "max_value": null
  },
  "bottom_height": {
    "value": -10.0,
    "unit": "mm",
    "expression": "stockTop - 10mm",
    "type": "numeric",
    "editable": true,
    "min_value": null,
    "max_value": null
  }
}
```

### Enhanced Toolpath Structure
```json
{
  "id": "operation_123",
  "name": "Adaptive Clearing",
  "type": "adaptive",
  "setup_name": "Setup1",
  "tool": {
    "id": "tool_456",
    "name": "6mm End Mill",
    "diameter": 6.0
  },
  "heights": {
    // Height Parameter Structure (as above)
  },
  "is_valid": true
}
```

### Reference Point Enumeration
```json
{
  "reference_types": [
    "from_stock_top",
    "from_stock_bottom", 
    "from_model_top",
    "from_model_bottom",
    "from_setup_top",
    "from_setup_bottom",
    "from_previous_operation",
    "absolute_coordinate"
  ]
}
```

## 
## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Properties 3.1-3.4 (individual height parameter extraction) can be combined into a single comprehensive property about height parameter completeness
- Properties 4.2-4.3 (height ordering constraints) can be combined into a single property about height hierarchy validation
- Properties 2.3-2.4 (height parameter structure) can be combined into a single property about data completeness

### Core Properties

**Property 1: Height-enabled toolpath response completeness**
*For any* toolpath request that includes height parameters, the response should contain both basic toolpath data (id, name, type, tool) and height parameter data (clearance, retract, feed, top, bottom heights with units, references, and offsets)
**Validates: Requirements 1.1, 1.2**

**Property 2: Height parameter data structure completeness**
*For any* height parameter returned by the system, it should include numeric value, unit, expression, type, editability flag, and constraint information (min/max values) when available
**Validates: Requirements 2.3, 2.4**

**Property 3: Graceful degradation for missing height data**
*For any* toolpath that lacks complete height parameter data, the system should return available parameters and clearly indicate which parameters are missing rather than failing completely
**Validates: Requirements 1.3**

**Property 4: Multiple toolpath height consistency**
*For any* collection of toolpaths queried with heights, each toolpath that has height parameters defined should have its height information included in the response
**Validates: Requirements 1.4, 2.1**

**Property 5: Toolpath lookup accuracy**
*For any* valid toolpath ID provided to the height extraction system, the returned height information should correspond exactly to that specific toolpath
**Validates: Requirements 2.2**

**Property 6: CAM product validation**
*For any* height information request, the system should validate CAM product existence before attempting extraction and return appropriate error messages when CAM data is unavailable
**Validates: Requirements 2.5**

**Property 7: Height parameter modification validation**
*For any* height parameter modification request, the system should validate the new value against Fusion 360 constraints and return validation errors for invalid values
**Validates: Requirements 4.1**

**Property 8: Height hierarchy constraints**
*For any* height parameter modification, the system should enforce logical ordering (clearance > retract > feed) and reject modifications that violate these constraints
**Validates: Requirements 4.2, 4.3**

**Property 9: Modification confirmation response**
*For any* successful height parameter modification, the system should return both the previous value and new value for confirmation
**Validates: Requirements 4.4**

**Property 10: Read-only parameter protection**
*For any* attempt to modify a read-only height parameter, the system should prevent the modification and return a clear error message indicating the parameter cannot be changed
**Validates: Requirements 4.5**

**Property 11: Backward compatibility preservation**
*For any* existing toolpath listing API call, the response structure and behavior should remain unchanged when height functionality is added
**Validates: Requirements 1.5**

## Error Handling

### CAM Product Validation
- Check for active document with CAM data before processing requests
- Return structured error responses with appropriate HTTP status codes
- Provide clear error messages for missing CAM workspace or data

### Height Parameter Extraction Errors
- Handle missing height parameters gracefully by indicating unavailable data
- Manage Fusion 360 API exceptions during parameter access
- Validate parameter types and units before returning data

### Height Modification Validation
- Validate height values against Fusion 360 constraints (min/max values)
- Enforce height hierarchy rules (clearance > retract > feed)
- Check parameter editability before allowing modifications
- Handle concurrent modification conflicts

### HTTP Transport Errors
- Implement proper error status codes (400, 404, 500)
- Provide structured JSON error responses
- Log errors for debugging while maintaining user-friendly messages

## Testing Strategy

### Unit Testing Approach
Unit tests will focus on:
- Individual height parameter extraction functions
- Height data structure validation
- Error handling for missing CAM data
- HTTP endpoint request/response handling
- Parameter modification validation logic

### Property-Based Testing Approach
Property-based tests will verify universal properties using **fast-check** (JavaScript) library with minimum 100 iterations per test:

- **Property 1**: Generate random toolpath data and verify height-enabled responses contain both basic and height data
- **Property 2**: Generate various height parameters and verify all required fields are present
- **Property 3**: Generate toolpaths with missing height data and verify graceful degradation
- **Property 4**: Generate collections of toolpaths and verify height consistency
- **Property 5**: Generate toolpath IDs and verify lookup accuracy
- **Property 6**: Test CAM product validation across various document states
- **Property 7**: Generate height modification requests and verify validation
- **Property 8**: Test height hierarchy constraints with various value combinations
- **Property 9**: Verify modification confirmation responses
- **Property 10**: Test read-only parameter protection
- **Property 11**: Verify backward compatibility with existing API calls

Each property-based test will be tagged with comments referencing the specific correctness property from this design document using the format: **Feature: toolpath-heights, Property {number}: {property_text}**

### Integration Testing
- End-to-end testing of MCP Server → HTTP → Fusion Add-In → Fusion 360 API chain
- Testing with real Fusion 360 CAM documents containing various toolpath types
- Validation of height parameter extraction across different operation types
- Testing height modification workflows with actual CAM operations

### Test Data Requirements
- CAM documents with various toolpath types (adaptive, contour, drill, etc.)
- Toolpaths with different height parameter configurations
- Operations with both automatic and manual height settings
- Documents with missing or incomplete CAM data for error testing