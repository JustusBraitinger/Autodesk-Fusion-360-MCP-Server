# Requirements Document

## Introduction

This specification defines the requirements for CAM setup management functionality in the Fusion 360 MCP Server. CAM setups are fundamental organizational units in Fusion 360's manufacturing workspace that define machining operations, coordinate systems, stock definitions, and toolpath groupings. This feature will enable AI assistants to create, configure, and manage CAM setups through natural language commands, making CAM workflow setup more accessible and efficient.

## Glossary

- **CAM_Setup**: A CAM setup object in Fusion 360 that contains machining operations, coordinate system definitions, stock configuration, and toolpath organization
- **MCP_Server**: The Model Context Protocol server that bridges AI assistants with Fusion 360
- **Fusion_Add_In**: The HTTP server running inside Fusion 360 that executes CAM API operations
- **Work_Coordinate_System**: The coordinate system definition that establishes the origin and orientation for machining operations
- **Stock_Definition**: The material definition including dimensions, position, and material properties for the workpiece
- **Operation_Group**: A collection of related machining operations within a setup
- **Setup_Template**: A predefined configuration that can be applied to new setups for consistency

## Requirements

### Requirement 1

**User Story:** As a CAM programmer, I want to create new CAM setups with basic configuration, so that I can organize my machining operations efficiently.

#### Acceptance Criteria

1. WHEN a user requests to create a CAM setup with a name THEN the CAM_System SHALL create a new setup with the specified name
2. WHEN creating a setup THEN the CAM_System SHALL assign a default work coordinate system at the model origin
3. WHEN creating a setup THEN the CAM_System SHALL detect and configure stock automatically from the selected bodies
4. WHEN a setup is created THEN the CAM_System SHALL return the setup ID and confirmation details
5. WHEN no name is provided THEN the CAM_System SHALL generate a descriptive name based on the selected geometry

### Requirement 2

**User Story:** As a CAM programmer, I want to configure work coordinate systems for setups, so that I can establish proper machining origins and orientations.

#### Acceptance Criteria

1. WHEN a user specifies a coordinate system origin point THEN the CAM_System SHALL position the work coordinate system at that location
2. WHEN a user specifies orientation vectors THEN the CAM_System SHALL align the coordinate system axes accordingly
3. WHEN a user selects a face or plane for orientation THEN the CAM_System SHALL automatically calculate appropriate coordinate system alignment
4. WHEN coordinate system changes are made THEN the CAM_System SHALL validate that the system is properly defined
5. WHEN invalid coordinate system data is provided THEN the CAM_System SHALL reject the configuration and provide clear error messages

### Requirement 3

**User Story:** As a CAM programmer, I want to define and modify stock configuration for setups, so that I can accurately represent the raw material being machined.

#### Acceptance Criteria

1. WHEN a user specifies stock dimensions THEN the CAM_System SHALL create stock geometry with those dimensions
2. WHEN a user selects existing geometry as stock THEN the CAM_System SHALL use that geometry for stock definition
3. WHEN stock position is specified THEN the CAM_System SHALL position the stock relative to the work coordinate system
4. WHEN material properties are provided THEN the CAM_System SHALL apply those properties to the stock definition
5. WHEN stock configuration is invalid THEN the CAM_System SHALL prevent setup creation and provide validation errors

### Requirement 4

**User Story:** As a CAM programmer, I want to list and inspect existing CAM setups, so that I can understand the current manufacturing configuration.

#### Acceptance Criteria

1. WHEN a user requests setup listing THEN the CAM_System SHALL return all setups with their basic properties
2. WHEN a user requests detailed setup information THEN the CAM_System SHALL return comprehensive setup configuration including coordinate systems and stock
3. WHEN a user queries setup by ID THEN the CAM_System SHALL return the specific setup details or appropriate error if not found
4. WHEN no setups exist THEN the CAM_System SHALL return an empty list with appropriate messaging
5. WHEN setup data is corrupted THEN the CAM_System SHALL handle errors gracefully and report the issue

### Requirement 5

**User Story:** As a CAM programmer, I want to modify existing setup configurations, so that I can adapt setups as manufacturing requirements change.

#### Acceptance Criteria

1. WHEN a user modifies setup properties THEN the CAM_System SHALL update the setup and preserve existing operations where possible
2. WHEN coordinate system changes affect existing operations THEN the CAM_System SHALL warn about potential impacts
3. WHEN stock configuration changes THEN the CAM_System SHALL validate that existing operations remain valid
4. WHEN setup modifications are invalid THEN the CAM_System SHALL reject changes and maintain the current configuration
5. WHEN modifications are successful THEN the CAM_System SHALL return updated setup information

### Requirement 6

**User Story:** As a CAM programmer, I want to delete CAM setups that are no longer needed, so that I can maintain a clean manufacturing workspace.

#### Acceptance Criteria

1. WHEN a user requests setup deletion THEN the CAM_System SHALL remove the setup and all associated operations
2. WHEN a setup contains active toolpaths THEN the CAM_System SHALL warn about data loss before deletion
3. WHEN setup deletion is confirmed THEN the CAM_System SHALL permanently remove the setup and return confirmation
4. WHEN attempting to delete a non-existent setup THEN the CAM_System SHALL return appropriate error messaging
5. WHEN deletion fails due to system constraints THEN the CAM_System SHALL report the specific failure reason

### Requirement 7

**User Story:** As a CAM programmer, I want to duplicate existing setups, so that I can create similar configurations efficiently.

#### Acceptance Criteria

1. WHEN a user requests setup duplication THEN the CAM_System SHALL create a new setup with identical configuration
2. WHEN duplicating a setup THEN the CAM_System SHALL copy coordinate systems, stock definitions, and operation templates
3. WHEN a new name is provided for duplication THEN the CAM_System SHALL use that name for the duplicated setup
4. WHEN no name is provided THEN the CAM_System SHALL generate a unique name based on the original setup
5. WHEN duplication fails THEN the CAM_System SHALL report the error and maintain the original setup unchanged

### Requirement 8

**User Story:** As a CAM programmer, I want to manage multiple setups within a single CAM document, so that I can organize complex manufacturing workflows with different orientations and configurations.

#### Acceptance Criteria

1. WHEN multiple setups exist in a document THEN the CAM_System SHALL list all setups with their unique identifiers
2. WHEN creating additional setups THEN the CAM_System SHALL ensure unique naming and prevent conflicts
3. WHEN switching between setups THEN the CAM_System SHALL maintain context and provide clear setup identification
4. WHEN setups share common resources THEN the CAM_System SHALL manage resource allocation appropriately
5. WHEN setup operations affect document state THEN the CAM_System SHALL maintain consistency across all setups

### Requirement 9

**User Story:** As a CAM programmer, I want toolpaths to always know which setup they belong to, so that I can maintain proper context and organization.

#### Acceptance Criteria

1. WHEN querying toolpath information THEN the CAM_System SHALL include the parent setup ID in the response
2. WHEN toolpaths are created within a setup THEN the CAM_System SHALL automatically associate them with that setup
3. WHEN toolpath operations are performed THEN the CAM_System SHALL validate setup context and permissions
4. WHEN toolpaths are moved between setups THEN the CAM_System SHALL update setup associations accordingly
5. WHEN setup context is invalid THEN the CAM_System SHALL prevent toolpath operations and provide clear error messages

### Requirement 10

**User Story:** As a CAM programmer, I want setups to list their contained toolpaths using existing toolpath functionality, so that I can leverage current capabilities while maintaining setup organization.

#### Acceptance Criteria

1. WHEN requesting toolpaths for a specific setup THEN the CAM_System SHALL use existing toolpath listing functions filtered by setup ID
2. WHEN setup toolpath queries are made THEN the CAM_System SHALL return toolpaths with full details using current toolpath serialization
3. WHEN toolpath operations are performed within setup context THEN the CAM_System SHALL use existing toolpath modification functions
4. WHEN setup-filtered toolpath lists are empty THEN the CAM_System SHALL return appropriate messaging indicating no toolpaths in the setup
5. WHEN existing toolpath functions are called THEN the CAM_System SHALL provide setup context as additional metadata

### Requirement 11

**User Story:** As a CAM programmer, I want helper functions that bridge setup and toolpath functionality, so that I can work seamlessly between setup management and toolpath operations.

#### Acceptance Criteria

1. WHEN helper functions are called THEN the CAM_System SHALL provide bidirectional setup-toolpath relationship queries
2. WHEN toolpath context is needed THEN the CAM_System SHALL provide functions to resolve setup from toolpath ID
3. WHEN setup context is needed THEN the CAM_System SHALL provide functions to list toolpaths within a setup
4. WHEN cross-referencing is required THEN the CAM_System SHALL maintain consistent ID mapping between setups and toolpaths
5. WHEN helper functions encounter errors THEN the CAM_System SHALL provide detailed error information including both setup and toolpath context