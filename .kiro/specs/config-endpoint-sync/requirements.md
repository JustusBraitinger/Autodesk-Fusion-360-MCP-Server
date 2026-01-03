# Requirements Document

## Introduction

The FusionMCPBridge configuration manager (`core/config.py`) contains an `_endpoints` dictionary that is significantly out of date compared to the actual handler registrations in the modular architecture. This feature synchronizes the configuration endpoints with the actual implemented handlers to ensure configuration accuracy, proper validation, and documentation consistency.

## Glossary

- **ConfigurationManager**: The centralized configuration class in `core/config.py` that manages HTTP endpoints, server settings, and module-specific configurations
- **Handler Registration**: The `register_handler()` calls in handler modules that define actual HTTP routes
- **Endpoint**: A URL path that maps to a specific HTTP handler function
- **Placeholder**: A URL path parameter like `{setup_id}` or `{toolpath_id}` that represents dynamic values
- **MANUFACTURE Workspace**: The official Fusion 360 workspace name for CAM operations

## Requirements

### Requirement 1

**User Story:** As a developer, I want the config.py endpoints to match actual handler registrations, so that configuration validation accurately reflects the system state.

#### Acceptance Criteria

1. WHEN the ConfigurationManager is initialized THEN the system SHALL contain endpoint definitions that match all registered handlers in the MANUFACTURE workspace
2. WHEN a developer queries endpoints for the "manufacture" category THEN the system SHALL return paths that match actual handler registrations
3. WHEN endpoint placeholders are defined THEN the system SHALL use consistent naming (`{setup_id}`, `{toolpath_id}`, `{operation_id}`, `{tool_id}`, `{library_id}`) matching handler registrations

### Requirement 2

**User Story:** As a developer, I want CAM setup endpoints correctly defined, so that setup management operations are properly documented in configuration.

#### Acceptance Criteria

1. WHEN the setups endpoint group is accessed THEN the system SHALL include `/cam/setups` for GET (list) and POST (create) operations
2. WHEN the setups endpoint group is accessed THEN the system SHALL include `/cam/setups/{setup_id}` for GET, PUT, and DELETE operations
3. WHEN the setups endpoint group is accessed THEN the system SHALL include `/cam/setups/{setup_id}/duplicate` for POST operation
4. WHEN the setups endpoint group is accessed THEN the system SHALL include `/cam/setups/{setup_id}/sequence` for GET operation

### Requirement 3

**User Story:** As a developer, I want toolpath endpoints correctly defined, so that toolpath operations are properly documented in configuration.

#### Acceptance Criteria

1. WHEN the toolpaths endpoint group is accessed THEN the system SHALL include `/cam/toolpaths` for listing toolpaths
2. WHEN the toolpaths endpoint group is accessed THEN the system SHALL include `/cam/toolpaths/with-heights` for listing toolpaths with height data
3. WHEN the toolpaths endpoint group is accessed THEN the system SHALL include `/cam/toolpaths/{toolpath_id}` for getting toolpath details
4. WHEN the toolpaths endpoint group is accessed THEN the system SHALL include `/cam/toolpaths/{toolpath_id}/parameters` for getting toolpath parameters
5. WHEN the toolpaths endpoint group is accessed THEN the system SHALL include `/cam/toolpaths/{toolpath_id}/heights` for height management
6. WHEN the toolpaths endpoint group is accessed THEN the system SHALL include `/cam/toolpaths/{toolpath_id}/passes` for pass configuration
7. WHEN the toolpaths endpoint group is accessed THEN the system SHALL include `/cam/toolpaths/{toolpath_id}/linking` for linking parameters

### Requirement 4

**User Story:** As a developer, I want operation-level endpoints defined, so that operation management is properly documented in configuration.

#### Acceptance Criteria

1. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/tool` for tool assignment
2. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/heights` for operation heights
3. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/heights/{parameter_name}` for modifying specific height parameters
4. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/heights/validate` for height validation
5. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/passes` for pass configuration
6. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/passes/validate` for pass validation
7. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/passes/optimize` for pass optimization
8. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/linking` for linking parameters
9. WHEN the operations endpoint group is accessed THEN the system SHALL include `/cam/operations/{operation_id}/linking/validate` for linking validation

### Requirement 5

**User Story:** As a developer, I want tool library endpoints correctly defined, so that tool library operations are properly documented in configuration.

#### Acceptance Criteria

1. WHEN the tool_libraries endpoint group is accessed THEN the system SHALL include `/tool-libraries` for listing libraries
2. WHEN the tool_libraries endpoint group is accessed THEN the system SHALL include `/tool-libraries/{library_id}` for getting library info
3. WHEN the tool_libraries endpoint group is accessed THEN the system SHALL include `/tool-libraries/load` for loading libraries
4. WHEN the tool_libraries endpoint group is accessed THEN the system SHALL include `/tool-libraries/validate-access` for access validation
5. WHEN the tool_libraries endpoint group is accessed THEN the system SHALL include `/tool-libraries/search` for basic tool search
6. WHEN the tool_libraries endpoint group is accessed THEN the system SHALL include `/tool-libraries/search/advanced` for advanced search
7. WHEN the tool_libraries endpoint group is accessed THEN the system SHALL include `/tool-libraries/search/suggestions` for search suggestions

### Requirement 6

**User Story:** As a developer, I want tool management endpoints correctly defined, so that tool CRUD operations are properly documented in configuration.

#### Acceptance Criteria

1. WHEN the tools endpoint group is accessed THEN the system SHALL include `/cam/tools` for listing CAM tools
2. WHEN the tools endpoint group is accessed THEN the system SHALL include `/cam/tools/{tool_id}/usage` for tool usage information
3. WHEN the tools endpoint group is accessed THEN the system SHALL include `/tool-libraries/tools` for listing and creating tools
4. WHEN the tools endpoint group is accessed THEN the system SHALL include `/tool-libraries/tools/{tool_id}` for GET, PUT, and DELETE operations
5. WHEN the tools endpoint group is accessed THEN the system SHALL include `/tool-libraries/tools/{tool_id}/duplicate` for tool duplication
6. WHEN the tools endpoint group is accessed THEN the system SHALL include `/tool-libraries/tools/validate` for tool specification validation

### Requirement 7

**User Story:** As a developer, I want obsolete endpoints removed from configuration, so that the configuration accurately reflects available functionality.

#### Acceptance Criteria

1. WHEN the configuration is validated THEN the system SHALL not contain the obsolete endpoint `/cam/setups/create`
2. WHEN the configuration is validated THEN the system SHALL not contain the obsolete endpoint `/cam/setups/{id}/modify`
3. WHEN the configuration is validated THEN the system SHALL not contain the obsolete endpoint `/cam/setups/{id}/delete`
4. WHEN the configuration is validated THEN the system SHALL not contain the obsolete endpoint `/cam/toolpath/{id}` (singular form)
5. WHEN the configuration is validated THEN the system SHALL not contain the obsolete endpoint `/tool-libraries/{library_id}/tools/create`
6. WHEN the configuration is validated THEN the system SHALL not contain the obsolete endpoint `/tool-libraries/tools/{tool_id}/modify`

### Requirement 8

**User Story:** As a developer, I want configuration validation to detect endpoint mismatches, so that I can identify configuration drift.

#### Acceptance Criteria

1. WHEN validate_config_detailed() is called THEN the system SHALL report any endpoints with incorrect URL patterns
2. WHEN validate_config_detailed() is called THEN the system SHALL report any endpoints with inconsistent placeholder naming
3. WHEN validate_config_detailed() is called THEN the system SHALL provide resolution guidance for detected issues

### Requirement 9

**User Story:** As a developer, I want a steering file that enforces config.py synchronization with handler registrations, so that configuration drift is prevented in future development.

#### Acceptance Criteria

1. WHEN a new handler is registered THEN the steering file SHALL instruct developers to update the corresponding endpoint in config.py
2. WHEN a handler endpoint path is modified THEN the steering file SHALL instruct developers to update the matching config.py endpoint
3. WHEN a handler is removed THEN the steering file SHALL instruct developers to remove the corresponding endpoint from config.py
4. WHEN the steering file is created THEN the system SHALL include a checklist for endpoint synchronization during code reviews
5. WHEN the steering file is created THEN the system SHALL document the mapping between handler modules and config.py endpoint groups
