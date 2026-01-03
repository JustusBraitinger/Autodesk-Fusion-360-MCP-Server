# Implementation Plan

## Overview

This implementation plan converts the CAM Setup Management design into a series of actionable coding tasks. The plan follows an incremental approach, starting with API research and basic functionality, then building up to complete setup management capabilities with full integration to existing toolpath functionality.

## Task List

- [x] 1. API Research and Foundation
  - Research Fusion 360 WCS API structure and model ID handling
  - Document actual API patterns and data structures
  - Create foundation for setup management functionality
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 1.1 Research WCS API structure and capabilities
  - Investigate `adsk.cam.Setup` WCS properties and methods
  - Document available orientation options (model-based, face-based, etc.)
  - Research origin specification methods (model origin, geometry-based, custom)
  - Document model ID structure and how to reference design geometry
  - Create API documentation for WCS configuration
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 1.2 Research model ID handling and validation
  - Investigate how model IDs are obtained from design workspace
  - Document model ID validation methods
  - Research integration between CAM setup creation and design workspace
  - Test model ID resolution and geometry referencing
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 1.3 Create Fusion 360 business language steering file
  - Document WCS terminology instead of "coordinate_system"
  - Document model structure (root level, not nested under WCS)
  - Document Design vs CAD terminology alignment
  - Create consistency guidelines for future development
  - _Requirements: All requirements (terminology consistency)_

- [ ]* 1.4 Write property test for API research validation
  - **Property 12: Error handling robustness**
  - **Validates: Requirements 2.5, 3.5, 5.4, 6.5, 7.5, 9.5**

- [x] 2. Basic Setup Management Infrastructure
  - Create core setup management functions in Fusion Add-In
  - Implement basic setup creation, listing, and retrieval
  - Set up HTTP endpoints for setup operations
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3_

- [x] 2.1 Implement core setup functions in cam.py
  - Create `create_setup()` function with basic configuration
  - Implement `list_setups_detailed()` function
  - Create `get_setup_by_id()` function
  - Add setup validation and error handling
  - Use proper WCS terminology throughout
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3_

- [ ]* 2.2 Write property test for setup creation completeness
  - **Property 1: Setup creation completeness**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

- [x] 2.3 Add HTTP endpoints for basic setup operations
  - Add `POST /cam/setups` endpoint for setup creation
  - Add `GET /cam/setups` endpoint for setup listing
  - Add `GET /cam/setups/{id}` endpoint for setup details
  - Implement proper error handling and status codes
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3_

- [ ]* 2.4 Write property test for setup information retrieval
  - **Property 4: Setup information retrieval consistency**
  - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 3. WCS Configuration Implementation
  - Implement work coordinate system configuration based on API research
  - Add WCS validation and error handling
  - Support multiple WCS configuration methods
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3.1 Implement WCS configuration functions
  - Create WCS configuration logic based on API research findings
  - Implement origin positioning and orientation alignment
  - Add model ID integration for WCS reference
  - Include comprehensive WCS validation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 3.2 Write property test for WCS configuration consistency
  - **Property 2: WCS configuration consistency**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 4. Stock Configuration Implementation
  - Implement stock definition and configuration
  - Add support for multiple stock modes (auto, geometry, primitives)
  - Include stock validation and positioning
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4.1 Implement stock configuration functions
  - Create automatic stock detection from selected bodies
  - Implement geometry-based stock definition
  - Add primitive stock creation (box, cylinder)
  - Include stock positioning relative to WCS
  - Add material property application
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 4.2 Write property test for stock configuration accuracy
  - **Property 3: Stock configuration accuracy**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [x] 5. MCP Server Tools Implementation
  - Create MCP tools for setup management in Server/tools/cam/setups.py
  - Implement all setup management tools with proper validation
  - Add integration with existing CAM tool patterns
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3_

- [x] 5.1 Create setup management MCP tools
  - Implement `create_cam_setup()` tool
  - Create `list_cam_setups()` tool
  - Add `get_setup_details()` tool
  - Include proper error handling and validation
  - Follow existing CAM tool patterns
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3_

- [x] 5.2 Add setup configuration endpoints
  - Extend configuration with setup-specific endpoints
  - Update `Server/core/config.py` with new CAM setup endpoints
  - Ensure consistency with existing endpoint patterns
  - _Requirements: All setup management requirements_

- [x] 6. Setup Modification and Deletion
  - Implement setup modification with validation
  - Add setup deletion with proper safeguards
  - Include impact warnings for existing operations
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.1 Implement setup modification functions
  - Create `modify_setup()` function with validation
  - Add impact analysis for WCS and stock changes
  - Include operation preservation logic
  - Implement proper error handling and rollback
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 6.2 Write property test for setup modification preservation
  - **Property 5: Setup modification preservation**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.5**

- [x] 6.3 Implement setup deletion functions
  - Create `delete_setup()` function with confirmation
  - Add toolpath impact warnings
  - Implement complete setup and operation removal
  - Include proper error handling for edge cases
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 6.4 Write property test for setup deletion completeness
  - **Property 6: Setup deletion completeness**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [x] 6.5 Add modification and deletion MCP tools
  - Implement `modify_setup_configuration()` tool
  - Create `delete_cam_setup()` tool with confirmation
  - Add corresponding HTTP endpoints
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 7. Setup Duplication
  - Implement setup duplication with complete configuration copying
  - Add name generation and conflict resolution
  - Include validation and error handling
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.1 Implement setup duplication functions
  - Create `duplicate_setup()` function
  - Copy WCS, stock, and operation configurations
  - Implement automatic name generation for duplicates
  - Add validation and error handling
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 7.2 Write property test for setup duplication fidelity
  - **Property 7: Setup duplication fidelity**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 7.3 Add duplication MCP tool and endpoint
  - Implement `duplicate_cam_setup()` tool
  - Add `POST /cam/setups/{id}/duplicate` endpoint
  - Include proper validation and error responses
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [-] 8. Multi-Setup Document Management
  - Implement multi-setup support with unique identification
  - Add setup conflict resolution and resource management
  - Include document state consistency maintenance
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [-] 8.1 Implement multi-setup management functions
  - Add unique setup identification and naming validation
  - Implement setup conflict resolution for name collisions
  - Create resource allocation management for shared geometry
  - Add document state consistency checks across setups
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 8.2 Write property test for multi-setup document consistency
  - **Property 8: Multi-setup document consistency**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

- [ ] 9. Setup-Toolpath Integration
  - Implement bidirectional setup-toolpath relationships
  - Add toolpath context and setup association
  - Create helper functions for relationship management
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 9.1 Implement setup-toolpath relationship functions in cam.py
  - Create `get_toolpaths_for_setup()` function using existing toolpath functionality
  - Implement `find_setup_for_toolpath()` helper function
  - Add `validate_setup_toolpath_relationship()` function
  - Include setup context in toolpath responses
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.5_

- [ ]* 9.2 Write property test for toolpath-setup association integrity
  - **Property 9: Toolpath-setup association integrity**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [ ] 9.3 Implement bidirectional relationship helper functions
  - Create comprehensive setup-toolpath mapping functions
  - Add toolpath movement between setups (if supported by API)
  - Implement consistent ID mapping maintenance
  - Include detailed error context for relationship operations
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 9.4 Write property test for existing functionality integration
  - **Property 10: Existing functionality integration**
  - **Validates: Requirements 10.1, 10.2, 10.3, 10.5**

- [ ]* 9.5 Write property test for bidirectional relationship consistency
  - **Property 11: Bidirectional relationship consistency**
  - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

- [ ] 9.6 Add setup-toolpath integration MCP tools and HTTP endpoints
  - Implement `get_setup_toolpaths()` MCP tool in Server/tools/cam/setups.py
  - Create `find_toolpath_setup()` MCP tool
  - Add HTTP handlers in FusionMCPBridge/handlers/manufacture/setups.py
  - Update Server/core/config.py with new endpoints
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 10. Wire Handler Integration for Modify/Duplicate/Delete
  - Connect HTTP handlers to cam.py functions for modify, duplicate, and delete
  - Currently handlers return 501 Not Implemented - need to wire to actual functions
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10.1 Wire handle_modify_setup to modify_setup function
  - Update FusionMCPBridge/handlers/manufacture/setups.py handle_modify_setup
  - Import and call cam.modify_setup() with proper task queue integration
  - Handle response formatting and error codes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 10.2 Wire handle_duplicate_setup to duplicate_setup function
  - Update FusionMCPBridge/handlers/manufacture/setups.py handle_duplicate_setup
  - Import and call cam.duplicate_setup() with proper task queue integration
  - Handle response formatting and error codes
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10.3 Wire handle_delete_setup to delete_setup function
  - Update FusionMCPBridge/handlers/manufacture/setups.py handle_delete_setup
  - Import and call cam.delete_setup() with proper task queue integration
  - Handle response formatting and error codes
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Integration Testing and Documentation
  - Create comprehensive integration tests
  - Update documentation and examples
  - Validate end-to-end functionality
  - _Requirements: All requirements_

- [ ] 12.1 Create integration tests
  - Test complete setup management workflows
  - Validate integration with existing toolpath functionality
  - Test error scenarios and edge cases
  - Include multi-setup document testing
  - _Requirements: All requirements_

- [ ]* 12.2 Write comprehensive unit tests
  - Create unit tests for all setup management functions
  - Test WCS configuration and validation
  - Test stock configuration and positioning
  - Test setup modification and deletion
  - Test setup-toolpath relationship functions
  - _Requirements: All requirements_

- [ ] 12.3 Update documentation and examples
  - Document new setup management tools and endpoints
  - Create usage examples for common workflows
  - Update API documentation with setup functionality
  - Include troubleshooting guide for setup operations
  - _Requirements: All requirements_

- [ ] 13. Final Checkpoint - Make sure all tests are passing
  - Ensure all tests pass, ask the user if questions arise.