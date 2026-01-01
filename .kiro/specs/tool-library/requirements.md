# Requirements Document

## Introduction

This feature extends the Fusion MCP Integration to provide comprehensive access to Fusion 360's Tool Library system. The Tool Library is where cutting tools are defined, organized, and stored for use in CAM operations. This feature enables AI assistants to read existing tools, create new tools, and modify tool definitions - supporting workflows like setting up machining operations, standardizing tool libraries across projects, and automating tool management.

## Glossary

- **Tool Library**: A collection of cutting tool definitions stored in Fusion 360, either locally, in the cloud, or as part of a document
- **Tool**: A cutting tool definition containing geometry (diameter, length, flutes), material properties, and cutting parameters
- **Tool Type**: The category of cutting tool (e.g., flat end mill, ball end mill, drill, tap, face mill, chamfer mill)
- **Tool Geometry**: Physical dimensions of the tool including diameter, overall length, flute length, shaft diameter, corner radius
- **Cutting Data**: Preset machining parameters stored with the tool including spindle speed, feed rates, and surface speed
- **Tool Preset**: A saved set of cutting parameters for a specific tool and material combination
- **Local Library**: Tool library stored on the user's computer
- **Cloud Library**: Tool library stored in Autodesk's cloud, accessible across devices
- **Document Library**: Tools embedded within a specific Fusion 360 document
- **MCP Server**: The FastMCP server that exposes tools to AI assistants
- **Fusion Add-In**: The HTTP server running inside Fusion 360 that executes operations

## Requirements

### Requirement 1

**User Story:** As a CAM programmer, I want to list all available tool libraries, so that I can see what tool collections are accessible in my Fusion 360 environment.

#### Acceptance Criteria

1. WHEN an AI assistant requests the list of tool libraries THEN the MCP Server SHALL return all accessible libraries including local, cloud, and document libraries
2. WHEN returning library information THEN the MCP Server SHALL include library name, type (local/cloud/document), and tool count for each library
3. WHEN no tool libraries are available THEN the MCP Server SHALL return an empty list with an informative message

### Requirement 2

**User Story:** As a CAM programmer, I want to list all tools in a specific library, so that I can browse available cutting tools for my operations.

#### Acceptance Criteria

1. WHEN an AI assistant requests tools from a specific library THEN the MCP Server SHALL return all tools in that library
2. WHEN returning tool list THEN the MCP Server SHALL include tool id, name, type, tool number, and basic geometry (diameter, length) for each tool
3. WHEN the specified library does not exist THEN the MCP Server SHALL return an error with code LIBRARY_NOT_FOUND
4. WHEN a library contains no tools THEN the MCP Server SHALL return an empty list with an informative message

### Requirement 3

**User Story:** As a CAM programmer, I want to get detailed information about a specific tool, so that I can understand its geometry and cutting parameters before using it.

#### Acceptance Criteria

1. WHEN an AI assistant requests tool details THEN the MCP Server SHALL return complete tool geometry including diameter, overall length, flute length, shaft diameter, and corner radius
2. WHEN returning tool details THEN the MCP Server SHALL include tool specifications including flute count, material, and coating
3. WHEN returning tool details THEN the MCP Server SHALL include cutting data presets (spindle speed, feed per tooth, surface speed) if available
4. WHEN the specified tool does not exist THEN the MCP Server SHALL return an error with code TOOL_NOT_FOUND

### Requirement 4

**User Story:** As a CAM programmer, I want to create a new tool in a library, so that I can add custom tools for my specific machining needs.

#### Acceptance Criteria

1. WHEN an AI assistant requests to create a tool THEN the MCP Server SHALL create the tool with the specified type and geometry
2. WHEN creating a tool THEN the MCP Server SHALL require tool type, diameter, and overall length as mandatory parameters
3. WHEN creating a tool THEN the MCP Server SHALL accept optional parameters including flute count, flute length, shaft diameter, corner radius, material, and coating
4. WHEN creating a tool THEN the MCP Server SHALL accept optional cutting data presets including spindle speed, feed per tooth, and surface speed
5. WHEN the target library is read-only THEN the MCP Server SHALL return an error with code LIBRARY_READ_ONLY
6. WHEN tool creation succeeds THEN the MCP Server SHALL return the new tool's id and confirmation message

### Requirement 5

**User Story:** As a CAM programmer, I want to modify an existing tool's properties, so that I can update tool geometry or cutting parameters as needed.

#### Acceptance Criteria

1. WHEN an AI assistant requests to modify a tool THEN the MCP Server SHALL update the specified properties
2. WHEN modifying a tool THEN the MCP Server SHALL allow updating geometry properties (diameter, length, flute length, corner radius)
3. WHEN modifying a tool THEN the MCP Server SHALL allow updating specifications (flute count, material, coating)
4. WHEN modifying a tool THEN the MCP Server SHALL allow updating cutting data presets
5. WHEN the tool is in a read-only library THEN the MCP Server SHALL return an error with code TOOL_READ_ONLY
6. WHEN the specified tool does not exist THEN the MCP Server SHALL return an error with code TOOL_NOT_FOUND
7. WHEN modification succeeds THEN the MCP Server SHALL return the updated tool properties

### Requirement 6

**User Story:** As a CAM programmer, I want to duplicate an existing tool, so that I can create variations of tools without starting from scratch.

#### Acceptance Criteria

1. WHEN an AI assistant requests to duplicate a tool THEN the MCP Server SHALL create a copy of the tool in the specified target library
2. WHEN duplicating a tool THEN the MCP Server SHALL allow specifying a new name for the duplicated tool
3. WHEN duplicating a tool THEN the MCP Server SHALL copy all geometry, specifications, and cutting data from the source tool
4. WHEN the target library is read-only THEN the MCP Server SHALL return an error with code LIBRARY_READ_ONLY
5. WHEN duplication succeeds THEN the MCP Server SHALL return the new tool's id

### Requirement 7

**User Story:** As a CAM programmer, I want to delete a tool from a library, so that I can remove obsolete or incorrect tool definitions.

#### Acceptance Criteria

1. WHEN an AI assistant requests to delete a tool THEN the MCP Server SHALL remove the tool from its library
2. WHEN the tool is currently in use by CAM operations THEN the MCP Server SHALL return an error with code TOOL_IN_USE
3. WHEN the tool is in a read-only library THEN the MCP Server SHALL return an error with code TOOL_READ_ONLY
4. WHEN the specified tool does not exist THEN the MCP Server SHALL return an error with code TOOL_NOT_FOUND
5. WHEN deletion succeeds THEN the MCP Server SHALL return a confirmation message

### Requirement 8

**User Story:** As a CAM programmer, I want to search for tools by criteria, so that I can quickly find tools matching specific requirements.

#### Acceptance Criteria

1. WHEN an AI assistant searches for tools THEN the MCP Server SHALL accept search criteria including tool type, diameter range, and material
2. WHEN searching by diameter range THEN the MCP Server SHALL return tools with diameter between the specified minimum and maximum values
3. WHEN searching by tool type THEN the MCP Server SHALL return only tools matching the specified type
4. WHEN no tools match the search criteria THEN the MCP Server SHALL return an empty list with an informative message
5. WHEN search succeeds THEN the MCP Server SHALL return matching tools with id, name, type, and diameter

### Requirement 9

**User Story:** As a developer, I want tool data to be serialized and deserialized correctly, so that tool information is accurately transmitted between the MCP Server and Fusion Add-In.

#### Acceptance Criteria

1. WHEN tool data is transmitted THEN the MCP Server SHALL serialize tool objects to JSON format
2. WHEN tool data is received THEN the MCP Server SHALL deserialize JSON to tool objects preserving all properties
3. WHEN serializing and deserializing tool data THEN the round-trip SHALL produce equivalent tool objects
