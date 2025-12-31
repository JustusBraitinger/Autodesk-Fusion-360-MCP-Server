# Requirements Document

## Introduction

This feature extends the Fusion 360 MCP add-in to provide programmatic access to CAM (Computer-Aided Manufacturing) parameters and toolpath operations. An LLM can query the MCP server to list all toolpaths in a setup, inspect specific toolpath parameters, and optionally modify settings when requested. This enables AI assistants to provide contextual suggestions for machining strategies, feeds, speeds, and other CAM parameters based on the user's current manufacturing setup.

## Glossary

- **CAM**: Computer-Aided Manufacturing - the use of software to control machine tools for manufacturing
- **Toolpath**: A calculated path that a cutting tool follows to machine a part; includes operation type and all associated parameters
- **Setup**: A CAM container that defines the stock, work coordinate system, and contains one or more toolpath operations
- **Operation**: A specific machining strategy (e.g., Adaptive Clearing, Contour, Drilling) with its parameters
- **MCP Server**: The Model Context Protocol server that exposes Fusion 360 functionality to LLMs
- **Fusion Add-In**: The Python add-in running inside Fusion 360 that provides the HTTP API
- **Manufacturing Workspace**: The Fusion 360 environment for CAM operations including toolpaths, setups, and machining strategies
- **Feeds and Speeds**: Cutting parameters including spindle speed (RPM), feed rate, and plunge rate
- **Tool**: The cutting tool definition including geometry, material, and specifications
- **Tool Settings**: Preset cutting parameters stored with the tool definition in the tool library, including surface speed, feed per tooth, ramp spindle speed, and plunge spindle speed

## Requirements

### Requirement 1

**User Story:** As an LLM assistant, I want to list all toolpaths in the current CAM setup, so that I can understand what operations exist and let the user choose which one to inspect.

#### Acceptance Criteria

1. WHEN an LLM queries the toolpath list endpoint THEN the MCP Server SHALL return a JSON array containing all toolpath operations in the active document
2. WHEN returning the toolpath list THEN the MCP Server SHALL include for each toolpath: name, operation type, associated tool name, and a unique identifier
3. WHEN no CAM setup exists in the document THEN the MCP Server SHALL return an empty list with a descriptive message indicating no CAM data is present
4. WHEN multiple setups exist THEN the MCP Server SHALL organize toolpaths by their parent setup

### Requirement 2

**User Story:** As an LLM assistant, I want to inspect the parameters of a specific toolpath operation, so that I can provide suggestions for optimization.

#### Acceptance Criteria

1. WHEN an LLM queries a specific toolpath by identifier THEN the MCP Server SHALL return all parameters for that operation
2. WHEN returning toolpath parameters THEN the MCP Server SHALL include feeds and speeds (spindle speed, feed rate, plunge rate, ramp feed rate)
3. WHEN returning toolpath parameters THEN the MCP Server SHALL include geometry settings (stepover, stepdown, depths, tolerances)
4. WHEN returning toolpath parameters THEN the MCP Server SHALL include the tool definition (tool number, diameter, flute count, material)
5. WHEN the specified toolpath identifier does not exist THEN the MCP Server SHALL return an error message indicating the toolpath was not found
6. WHEN serializing toolpath parameters to JSON THEN the MCP Server SHALL encode all parameter types correctly and produce valid JSON
7. WHEN returning toolpath parameters THEN the MCP Server SHALL include tool settings (preset spindle speed, surface speed, feed per tooth, ramp spindle speed, plunge spindle speed)

### Requirement 3

**User Story:** As an LLM assistant, I want to know the parameter types and valid ranges, so that I can suggest appropriate values.

#### Acceptance Criteria

1. WHEN returning parameter information THEN the MCP Server SHALL include the parameter type (numeric, boolean, enum, etc.)
2. WHEN a parameter has constraints (min/max values, allowed units) THEN the MCP Server SHALL include these constraints in the response
3. WHEN a parameter has a unit type THEN the MCP Server SHALL include both the current value and the unit information
4. WHEN a parameter is an enumeration THEN the MCP Server SHALL include the list of valid options

### Requirement 4

**User Story:** As an LLM assistant, I want to modify toolpath parameters when the user requests it, so that I can help optimize their machining operations.

#### Acceptance Criteria

1. WHEN an LLM sends a valid value for a specific toolpath parameter THEN the MCP Server SHALL update that parameter
2. WHEN an LLM sends an invalid value (wrong type, out of range) THEN the MCP Server SHALL reject the update and return an error message describing the validation failure
3. WHEN attempting to modify a read-only parameter THEN the MCP Server SHALL return an error indicating the parameter cannot be modified
4. WHEN the specified toolpath does not exist THEN the MCP Server SHALL return an error indicating the toolpath was not found

### Requirement 5

**User Story:** As a developer, I want the CAM parameter access functionality exposed through the MCP protocol, so that any MCP-compatible LLM client can access it.

#### Acceptance Criteria

1. WHEN the MCP Server starts THEN the system SHALL register a tool for listing toolpaths
2. WHEN the MCP Server starts THEN the system SHALL register a tool for inspecting toolpath parameters
3. WHEN the MCP Server starts THEN the system SHALL register a tool for modifying toolpath parameters
4. WHEN an MCP tool is called THEN the system SHALL communicate with the Fusion Add-In via the existing HTTP API pattern
5. WHEN the Fusion Add-In is not running THEN the MCP Server SHALL return a connection error with retry guidance

### Requirement 6

**User Story:** As a user, I want to get information about the tools used in my CAM operations, so that the LLM can make informed suggestions about feeds and speeds.

#### Acceptance Criteria

1. WHEN an LLM queries tool information THEN the MCP Server SHALL return the tool library data for tools used in the document
2. WHEN returning tool information THEN the MCP Server SHALL include tool geometry (diameter, length, flute length, corner radius)
3. WHEN returning tool information THEN the MCP Server SHALL include tool specifications (flute count, material, coating if available)
4. WHEN a toolpath references a tool THEN the MCP Server SHALL include the tool identifier in the toolpath response
