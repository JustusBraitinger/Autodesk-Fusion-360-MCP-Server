# Design Document

## Overview

This design extends the existing Fusion 360 MCP integration to provide comprehensive access to toolpath passes and linking parameters. Building on the successful toolpath heights implementation, this solution adds deep inspection and modification capabilities for multi-pass operations and toolpath linking configurations. The design accounts for operation-specific parameters and organizes settings by their dialog sections as they appear in Fusion 360's interface.

## Architecture

The enhancement follows the established two-component architecture:

1. **MCP Server Extension** (`/Server/MCP_Server.py`): New tools for pass and linking analysis/modification
2. **Fusion Add-In Enhancement** (`/FusionMCPBridge/FusionMCPBridge.py`): New HTTP endpoints for pass/linking data
3. **CAM Module Enhancement** (`/FusionMCPBridge/cam.py`): New functions for pass and linking parameter extraction

### Communication Flow
```
AI Assistant → MCP Server → HTTP Request → Fusion Add-In → Enhanced CAM Functions → Fusion 360 API
```

## Components and Interfaces

### 1. MCP Server Tools (`/Server/MCP_Server.py`)

#### New Tool: `get_toolpath_passes(toolpath_id: str)`
- **Purpose**: Extract pass information for multi-pass operations
- **Parameters**: 
  - `toolpath_id` (required str): The toolpath identifier
- **Returns**: Pass configuration including roughing, semi-finishing, and finishing passes

#### New Tool: `get_toolpath_linking(toolpath_id: str)`
- **Purpose**: Extract linking and transition parameters organized by dialog sections
- **Parameters**:
  - `toolpath_id` (required str): The toolpath identifier
- **Returns**: Linking parameters organized by operation-specific sections

#### New Tool: `modify_toolpath_passes(toolpath_id: str, pass_config: dict)`
- **Purpose**: Modify pass configuration for multi-pass operations
- **Parameters**:
  - `toolpath_id` (required str): The toolpath identifier
  - `pass_config` (required dict): New pass configuration
- **Returns**: Modification result with validation details

#### New Tool: `modify_toolpath_linking(toolpath_id: str, linking_config: dict)`
- **Purpose**: Modify linking and transition parameters
- **Parameters**:
  - `toolpath_id` (required str): The toolpath identifier
  - `linking_config` (required dict): New linking configuration
- **Returns**: Modification result with validation details

#### New Tool: `analyze_toolpath_sequence(setup_id: str)`
- **Purpose**: Analyze toolpath execution sequence and dependencies
- **Parameters**:
  - `setup_id` (required str): The setup identifier
- **Returns**: Sequence analysis with optimization recommendations

### 2. HTTP Endpoints (`/FusionMCPBridge/FusionMCPBridge.py`)

#### New Endpoint: `GET /cam/toolpath/{id}/passes`
- **Purpose**: Get pass configuration for a specific toolpath
- **Response**: JSON object with pass details

#### New Endpoint: `GET /cam/toolpath/{id}/linking`
- **Purpose**: Get linking parameters for a specific toolpath
- **Response**: JSON object with linking configuration organized by sections

#### New Endpoint: `POST /cam/toolpath/{id}/passes`
- **Purpose**: Modify pass configuration
- **Request Body**: Pass configuration changes
- **Response**: Modification result

#### New Endpoint: `POST /cam/toolpath/{id}/linking`
- **Purpose**: Modify linking parameters
- **Request Body**: Linking configuration changes
- **Response**: Modification result

#### New Endpoint: `GET /cam/setup/{id}/sequence`
- **Purpose**: Analyze toolpath sequence in a setup
- **Response**: JSON object with sequence analysis

### 3. CAM Module Enhancements (`/FusionMCPBridge/cam.py`)

#### New Function: `_extract_pass_params(operation: adsk.cam.Operation)`
- **Purpose**: Extract multi-pass configuration from an operation
- **Returns**: Pass parameters including depths, stock-to-leave, finishing passes

#### New Function: `_extract_linking_params(operation: adsk.cam.Operation)`
- **Purpose**: Extract linking parameters organized by dialog sections
- **Returns**: Linking configuration specific to operation type

#### New Function: `get_toolpath_passes(cam: adsk.cam.CAM, toolpath_id: str)`
- **Purpose**: Get comprehensive pass information for a toolpath
- **Returns**: Complete pass configuration with metadata

#### New Function: `get_toolpath_linking(cam: adsk.cam.CAM, toolpath_id: str)`
- **Purpose**: Get linking parameters organized by sections
- **Returns**: Operation-specific linking configuration

#### New Function: `analyze_setup_sequence(cam: adsk.cam.CAM, setup_id: str)`
- **Purpose**: Analyze toolpath execution sequence and dependencies
- **Returns**: Sequence analysis with recommendations

## Data Models

### Pass Configuration Structure
```json
{
  "pass_type": "multiple_depths",
  "total_passes": 3,
  "passes": [
    {
      "pass_number": 1,
      "pass_type": "roughing",
      "depth": -5.0,
      "stock_to_leave": {
        "radial": 0.5,
        "axial": 0.2
      },
      "parameters": {
        "stepover": 60,
        "stepdown": 2.0,
        "feedrate": 2000
      }
    },
    {
      "pass_number": 2,
      "pass_type": "semi_finishing",
      "depth": -5.0,
      "stock_to_leave": {
        "radial": 0.1,
        "axial": 0.05
      },
      "parameters": {
        "stepover": 40,
        "stepdown": 1.0,
        "feedrate": 1500
      }
    },
    {
      "pass_number": 3,
      "pass_type": "finishing",
      "depth": -5.0,
      "stock_to_leave": {
        "radial": 0.0,
        "axial": 0.0
      },
      "parameters": {
        "stepover": 20,
        "stepdown": 0.5,
        "feedrate": 1000
      }
    }
  ],
  "spring_passes": 1,
  "finishing_enabled": true
}
```

### Linking Configuration Structure (Operation-Specific)
```json
{
  "operation_type": "2d_pocket",
  "sections": {
    "leads_and_transitions": {
      "lead_in": {
        "type": "arc",
        "arc_radius": 2.0,
        "arc_sweep": 90,
        "vertical_lead_in": false,
        "minimum_arc_radius": 0.1
      },
      "lead_out": {
        "type": "arc", 
        "arc_radius": 2.0,
        "arc_sweep": 90,
        "vertical_lead_out": false
      },
      "transitions": {
        "type": "stay_down",
        "lift_height": 1.0,
        "order_by_depth": true,
        "keep_tool_down": true
      }
    },
    "entry_positioning": {
      "clearance_height": 25.0,
      "feed_height": 2.0,
      "top_height": 0.0
    }
  },
  "editable_parameters": [
    "leads_and_transitions.lead_in.arc_radius",
    "leads_and_transitions.lead_out.arc_radius",
    "leads_and_transitions.transitions.type"
  ]
}
```

### 3D Operation Linking Structure
```json
{
  "operation_type": "3d_adaptive",
  "sections": {
    "linking": {
      "approach": {
        "type": "perpendicular",
        "distance": 5.0,
        "angle": 0.0
      },
      "retract": {
        "type": "perpendicular", 
        "distance": 5.0,
        "angle": 0.0
      },
      "clearance": {
        "height": 25.0,
        "type": "from_stock_top"
      }
    },
    "transitions": {
      "stay_down_distance": 2.0,
      "lift_height": 1.0,
      "order_optimization": "by_geometry"
    }
  }
}
```

### Sequence Analysis Structure
```json
{
  "setup_id": "setup_001",
  "setup_name": "Setup1",
  "total_toolpaths": 5,
  "execution_sequence": [
    {
      "order": 1,
      "toolpath_id": "op_001",
      "toolpath_name": "Adaptive Clearing",
      "tool_id": "tool_001",
      "estimated_time": "15:30",
      "dependencies": [],
      "pass_count": 1
    },
    {
      "order": 2,
      "toolpath_id": "op_002", 
      "toolpath_name": "Contour Finishing",
      "tool_id": "tool_002",
      "estimated_time": "8:45",
      "dependencies": ["op_001"],
      "pass_count": 2
    }
  ],
  "tool_changes": [
    {
      "after_toolpath": "op_001",
      "from_tool": "tool_001",
      "to_tool": "tool_002",
      "change_time": "2:00"
    }
  ],
  "optimization_recommendations": [
    {
      "type": "tool_change_reduction",
      "description": "Consider reordering operations to minimize tool changes",
      "potential_savings": "4:00"
    }
  ],
  "total_estimated_time": "26:15"
}
```

## 
## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Properties 1.1-1.5 (pass information extraction) can be combined into comprehensive pass data extraction properties
- Properties 2.1, 2.2, 2.4, 2.5 (toolpath linking analysis) can be combined into toolpath sequence analysis properties  
- Properties 3.1-3.5 (pass parameter analysis) can be combined into pass parameter validation properties
- Properties 4.1-4.5 (modification validation) can be combined into modification validation properties
- Properties 7.1-7.5 (operation-specific linking) can be combined into operation-specific parameter extraction properties
- Properties 8.1-8.5 (operation-specific passes) can be combined into operation-specific pass extraction properties

### Core Properties

**Property 1: Multi-pass information completeness**
*For any* toolpath with multiple passes, the system should return complete information about each pass including pass type, parameters, sequence order, and relationships between passes
**Validates: Requirements 1.1, 1.2, 1.5**

**Property 2: Tool change analysis accuracy**
*For any* pass sequence with different tool requirements, the system should correctly identify tool changes, their impact on machining time, and provide tool change sequence information
**Validates: Requirements 1.3, 2.4**

**Property 3: Parameter inheritance identification**
*For any* passes that share common parameters, the system should correctly identify parameter inheritance and overrides between passes
**Validates: Requirements 1.4**

**Property 4: Toolpath sequence extraction completeness**
*For any* linked toolpath sequence, the system should return the complete chain with execution order and correctly identify operation dependencies
**Validates: Requirements 2.1, 2.2**

**Property 5: Toolpath linking validation**
*For any* toolpath linking configuration, the system should validate linking integrity and identify broken or invalid links
**Validates: Requirements 2.5**

**Property 6: Pass parameter type accuracy**
*For any* pass type (roughing, finishing), the system should return parameters appropriate for that pass type (aggressive for roughing, precision for finishing)
**Validates: Requirements 3.1, 3.2**

**Property 7: Stock-to-leave calculation accuracy**
*For any* passes with stock-to-leave values, the system should correctly calculate remaining material for subsequent passes
**Validates: Requirements 3.3, 6.2**

**Property 8: Pass efficiency metrics provision**
*For any* pass configuration, the system should provide estimated machining times, material removal rates, and efficiency metrics
**Validates: Requirements 3.4, 5.5**

**Property 9: Pass-tool conflict identification**
*For any* pass parameters and tool combination, the system should identify potential conflicts between pass parameters and tool capabilities
**Validates: Requirements 3.5**

**Property 10: Pass modification validation**
*For any* pass parameter modification request, the system should validate changes against toolpath constraints and dependencies
**Validates: Requirements 4.1**

**Property 11: Pass sequence logical ordering**
*For any* pass sequence modification, the system should ensure logical machining progression (roughing before finishing) is maintained
**Validates: Requirements 4.2**

**Property 12: Dependent parameter updates**
*For any* pass addition or removal, the system should automatically update dependent toolpath parameters correctly
**Validates: Requirements 4.3**

**Property 13: Toolpath link modification validation**
*For any* toolpath link modification, the system should validate that the new sequence maintains machining integrity and prevent invalid modifications
**Validates: Requirements 4.4, 4.5**

**Property 14: Operation-specific linking parameter extraction**
*For any* operation type (2D Pocket, Trace, 3D), the system should return linking settings organized under the correct dialog sections with operation-specific parameters
**Validates: Requirements 7.1, 7.2, 7.3, 7.5**

**Property 15: Linking parameter modification validation**
*For any* linking setting modification, the system should validate values against operation-specific constraints and available options for that operation type
**Validates: Requirements 7.4**

**Property 16: Operation-specific pass parameter extraction**
*For any* operation type (2D Pocket, Adaptive, Contour, Drill), the system should return pass-specific parameters appropriate for that operation type with correct parameter identification
**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

## Error Handling

### Pass Configuration Errors
- Handle operations without pass configuration gracefully
- Validate pass sequence integrity before modifications
- Manage conflicts between pass parameters and tool capabilities
- Handle missing or incomplete pass data

### Linking Parameter Errors
- Validate operation-specific linking parameters
- Handle missing linking configuration sections
- Manage invalid linking parameter combinations
- Validate linking modifications against operation constraints

### Sequence Analysis Errors
- Handle setups without toolpath sequences
- Manage circular dependencies in toolpath links
- Validate toolpath execution order constraints
- Handle missing dependency information

### Modification Validation Errors
- Prevent modifications that break pass sequence logic
- Validate parameter changes against tool constraints
- Handle concurrent modification conflicts
- Manage rollback of failed modifications

## Testing Strategy

### Unit Testing Approach
Unit tests will focus on:
- Individual pass parameter extraction functions
- Linking parameter extraction by operation type
- Pass sequence validation logic
- Parameter modification validation
- Error handling for missing or invalid data

### Property-Based Testing Approach
Property-based tests will verify universal properties using **fast-check** (JavaScript) library with minimum 100 iterations per test:

- **Property 1**: Generate toolpaths with multiple passes and verify complete information extraction
- **Property 2**: Generate pass sequences with tool changes and verify tool change analysis
- **Property 3**: Generate passes with shared parameters and verify inheritance identification
- **Property 4**: Generate linked toolpath sequences and verify complete chain extraction
- **Property 5**: Generate valid and invalid toolpath links and verify validation
- **Property 6**: Generate different pass types and verify appropriate parameter extraction
- **Property 7**: Generate passes with stock-to-leave and verify calculation accuracy
- **Property 8**: Generate pass configurations and verify efficiency metrics provision
- **Property 9**: Generate pass/tool combinations and verify conflict identification
- **Property 10**: Generate pass modification requests and verify validation
- **Property 11**: Generate pass sequence modifications and verify logical ordering
- **Property 12**: Generate pass additions/removals and verify parameter updates
- **Property 13**: Generate toolpath link modifications and verify validation
- **Property 14**: Generate different operation types and verify linking parameter extraction
- **Property 15**: Generate linking modifications and verify operation-specific validation
- **Property 16**: Generate different operation types and verify pass parameter extraction

Each property-based test will be tagged with comments referencing the specific correctness property from this design document using the format: **Feature: toolpath-passes-linking, Property {number}: {property_text}**

### Integration Testing
- End-to-end testing of pass and linking parameter extraction
- Testing with real Fusion 360 CAM documents containing various operation types
- Validation of modification workflows with actual CAM operations
- Testing sequence analysis with complex toolpath dependencies

### Test Data Requirements
- CAM documents with multi-pass operations (2D Pocket, Adaptive, Contour)
- Operations with various linking configurations
- Toolpath sequences with dependencies and tool changes
- Documents with different operation types for parameter validation testing