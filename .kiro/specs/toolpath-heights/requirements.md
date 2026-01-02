# Requirements Document

## Introduction

This feature enhances the existing Fusion 360 MCP integration to provide direct access to toolpath height parameters when querying toolpaths. Currently, users can list toolpaths and get detailed parameters separately, but there's no streamlined way to access height information directly when asking about toolpaths. This enhancement will enable AI assistants to provide comprehensive toolpath information including critical height parameters in a single query.

## Glossary

- **Toolpath**: A CAM operation that defines the path a cutting tool follows during machining
- **Height Parameters**: CAM parameters that control vertical positioning including clearance height, retract height, feed height, top height, and bottom height
- **MCP Server**: The Model Context Protocol server that exposes Fusion 360 functionality to AI assistants
- **CAM Product**: The Computer-Aided Manufacturing component within Fusion 360
- **Operation**: A specific machining operation within a CAM setup

## Requirements

### Requirement 1

**User Story:** As an AI assistant user, I want to get toolpath height information when asking about toolpaths, so that I can understand the complete machining setup without making separate queries.

#### Acceptance Criteria

1. WHEN a user requests toolpath information with heights, THE MCP Server SHALL return both basic toolpath data and height parameters in a single response
2. WHEN height parameters are requested, THE MCP Server SHALL include clearance height, retract height, feed height, top height, and bottom height values with their units, expressions, and parameter metadata
3. WHEN height parameters are not available for a toolpath, THE MCP Server SHALL indicate which parameters are missing rather than failing completely
4. WHEN multiple toolpaths are queried with heights, THE MCP Server SHALL return height information for each toolpath that has height parameters defined
5. THE MCP Server SHALL maintain backward compatibility with existing toolpath listing functionality

### Requirement 2

**User Story:** As an AI assistant, I want to access height parameters through a simple tool call, so that I can provide comprehensive machining advice without complex multi-step queries.

#### Acceptance Criteria

1. WHEN the list_toolpaths_with_heights tool is called, THE MCP Server SHALL return all toolpaths with their associated height parameters
2. WHEN a specific toolpath ID is provided, THE MCP Server SHALL return detailed height information for that specific toolpath
3. WHEN height parameters include units, THE MCP Server SHALL return the numeric value, unit information, and expression string that may contain reference points and calculations
4. WHEN height parameters are expressions, THE MCP Server SHALL return both the expression string and the evaluated numeric value
5. THE MCP Server SHALL validate that the CAM product exists before attempting to extract height information

### Requirement 3

**User Story:** As a machinist using the AI assistant, I want to understand toolpath safety heights, so that I can verify my machining setup will avoid collisions.

#### Acceptance Criteria

1. WHEN clearance height is requested, THE MCP Server SHALL return the safe travel height above all obstacles including its expression and evaluated value
2. WHEN retract height is requested, THE MCP Server SHALL return the height for rapid positioning moves including its expression and evaluated value
3. WHEN feed height is requested, THE MCP Server SHALL return the height where feed rate machining begins including its expression and evaluated value
4. WHEN top and bottom heights are requested, THE MCP Server SHALL return the material boundaries for the operation including their expressions and evaluated values
5. THE MCP Server SHALL indicate if any height parameter is read-only and provide parameter constraint information when available

### Requirement 4

**User Story:** As a CAM programmer, I want to modify toolpath heights through the AI assistant, so that I can optimize machining parameters conversationally.

#### Acceptance Criteria

1. WHEN a height parameter modification is requested, THE MCP Server SHALL validate the new value against Fusion 360 constraints
2. WHEN modifying clearance height, THE MCP Server SHALL ensure the value is above the retract height
3. WHEN modifying retract height, THE MCP Server SHALL ensure the value is above the feed height
4. WHEN height modifications are successful, THE MCP Server SHALL return the previous and new values for confirmation
5. THE MCP Server SHALL prevent modification of read-only height parameters and provide clear error messages

### Requirement 5

**User Story:** As an AI assistant, I want to provide contextual height recommendations, so that I can suggest optimal machining parameters based on the toolpath type and material.

#### Acceptance Criteria

1. WHEN analyzing toolpath heights, THE MCP Server SHALL provide context about whether heights are appropriate for the operation type
2. WHEN height values seem unusual, THE MCP Server SHALL flag potential issues such as insufficient clearance
3. WHEN comparing multiple toolpaths, THE MCP Server SHALL identify height inconsistencies that might cause machining problems
4. THE MCP Server SHALL provide height parameter metadata including recommended ranges when available
5. THE MCP Server SHALL indicate which height parameters are most critical for each operation type