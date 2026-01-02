# Implementation Plan

- [x] 1. Enhance CAM module with pass parameter extraction
  - [x] 1.1 Create `_extract_pass_params()` function in `FusionMCPBridge/cam.py`
    - Extract multi-pass configuration from operations
    - Identify pass types (roughing, semi-finishing, finishing)
    - Extract pass-specific parameters (depths, stock-to-leave, stepover/stepdown)
    - Handle operations without pass configuration gracefully
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3_

  - [ ]* 1.2 Write property test for pass parameter extraction
    - **Property 1: Multi-pass information completeness**
    - **Validates: Requirements 1.1, 1.2, 1.5**

  - [x] 1.3 Create `_extract_linking_params()` function in `FusionMCPBridge/cam.py`
    - Extract linking parameters organized by dialog sections
    - Handle operation-specific parameter structures (2D Pocket, Trace, 3D)
    - Identify editable vs read-only linking parameters
    - Return parameters grouped by interface sections
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 1.4 Write property test for linking parameter extraction
    - **Property 14: Operation-specific linking parameter extraction**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.5**

  - [x] 1.5 Create `get_toolpath_passes()` function in `FusionMCPBridge/cam.py`
    - Combine pass extraction with toolpath lookup
    - Return comprehensive pass configuration with metadata
    - Handle missing toolpaths with structured errors
    - Include pass relationships and inheritance information
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 3.1, 3.2, 3.3_

  - [ ]* 1.6 Write property test for toolpath pass retrieval
    - **Property 3: Parameter inheritance identification**
    - **Validates: Requirements 1.4**

- [x] 2. Add linking parameter extraction capabilities
  - [x] 2.1 Create `get_toolpath_linking()` function in `FusionMCPBridge/cam.py`
    - Extract operation-specific linking parameters
    - Organize parameters by dialog sections
    - Return linking configuration with editability information
    - Handle different operation types appropriately
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 2.2 Write property test for operation-specific parameter extraction
    - **Property 16: Operation-specific pass parameter extraction**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

  - [x] 2.3 Create `analyze_setup_sequence()` function in `FusionMCPBridge/cam.py`
    - Analyze toolpath execution sequence and dependencies
    - Identify tool changes and their impact
    - Provide optimization recommendations
    - Calculate estimated machining times
    - _Requirements: 2.1, 2.2, 2.4, 3.4, 5.5_

  - [ ]* 2.4 Write property test for sequence analysis
    - **Property 4: Toolpath sequence extraction completeness**
    - **Validates: Requirements 2.1, 2.2**

- [x] 3. Add HTTP endpoints to Fusion Add-In
  - [x] 3.1 Add `GET /cam/toolpath/{id}/passes` endpoint in `FusionMCPBridge/FusionMCPBridge.py`
    - Route to `get_toolpath_passes()` function
    - Extract toolpath ID from URL path
    - Return JSON response with pass configuration
    - Handle missing toolpaths with 404 responses
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [x] 3.2 Add `GET /cam/toolpath/{id}/linking` endpoint in `FusionMCPBridge/FusionMCPBridge.py`
    - Route to `get_toolpath_linking()` function
    - Return operation-specific linking parameters
    - Organize response by dialog sections
    - Handle CAM product validation errors
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [x] 3.3 Add `GET /cam/setup/{id}/sequence` endpoint in `FusionMCPBridge/FusionMCPBridge.py`
    - Route to `analyze_setup_sequence()` function
    - Extract setup ID from URL path
    - Return sequence analysis with recommendations
    - Handle missing setups with appropriate errors
    - _Requirements: 2.1, 2.2, 2.4, 3.4_

  - [ ]* 3.4 Write property test for HTTP endpoint responses
    - **Property 5: Toolpath linking validation**
    - **Validates: Requirements 2.5**

- [-] 4. Update server configuration
  - [x] 4.1 Add new endpoints to `Server/config.py`
    - Add `cam_toolpath_passes` endpoint configuration
    - Add `cam_toolpath_linking` endpoint configuration  
    - Add `cam_setup_sequence` endpoint configuration
    - Maintain consistent naming with existing CAM endpoints
    - _Requirements: All requirements need server access_

- [x] 5. Add MCP tools to server
  - [x] 5.1 Add `get_toolpath_passes()` tool to `Server/MCP_Server.py`
    - Create MCP tool with toolpath_id parameter
    - Send HTTP request to `/cam/toolpath/{id}/passes` endpoint
    - Handle response parsing and error cases
    - Include German documentation for AI assistant
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 3.1, 3.2, 3.3_

  - [ ]* 5.2 Write property test for pass retrieval tool
    - **Property 6: Pass parameter type accuracy**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 5.3 Add `get_toolpath_linking()` tool to `Server/MCP_Server.py`
    - Create MCP tool with toolpath_id parameter
    - Send HTTP request to `/cam/toolpath/{id}/linking` endpoint
    - Handle operation-specific response structures
    - Include parameter validation and error handling
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 5.4 Write property test for linking retrieval tool
    - **Property 15: Linking parameter modification validation**
    - **Validates: Requirements 7.4**

  - [x] 5.5 Add `analyze_toolpath_sequence()` tool to `Server/MCP_Server.py`
    - Create MCP tool with setup_id parameter
    - Send HTTP request to `/cam/setup/{id}/sequence` endpoint
    - Handle sequence analysis response parsing
    - Include optimization recommendation processing
    - _Requirements: 2.1, 2.2, 2.4, 3.4, 5.5_

  - [ ]* 5.6 Write property test for sequence analysis tool
    - **Property 2: Tool change analysis accuracy**
    - **Validates: Requirements 1.3, 2.4**

- [x] 6. Implement pass modification capabilities
  - [x] 6.1 Create pass modification validation functions in `FusionMCPBridge/cam.py`
    - Validate pass parameter changes against constraints
    - Ensure logical pass sequence ordering (rough before finish)
    - Check tool compatibility with pass parameters
    - Handle dependent parameter updates automatically
    - _Requirements: 4.1, 4.2, 4.3, 3.5_

  - [ ]* 6.2 Write property test for pass modification validation
    - **Property 10: Pass modification validation**
    - **Validates: Requirements 4.1**

  - [ ]* 6.3 Write property test for pass sequence ordering
    - **Property 11: Pass sequence logical ordering**
    - **Validates: Requirements 4.2**

  - [x] 6.4 Add `POST /cam/toolpath/{id}/passes` endpoint in `FusionMCPBridge/FusionMCPBridge.py`
    - Handle pass configuration modification requests
    - Validate modifications before applying changes
    - Return modification results with previous/new values
    - Handle validation errors with structured responses
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [ ]* 6.5 Write property test for dependent parameter updates
    - **Property 12: Dependent parameter updates**
    - **Validates: Requirements 4.3**

- [x] 7. Implement linking modification capabilities
  - [x] 7.1 Create linking modification validation functions in `FusionMCPBridge/cam.py`
    - Validate linking parameter changes against operation constraints
    - Check parameter compatibility with operation type
    - Ensure linking integrity is maintained
    - Handle operation-specific validation rules
    - _Requirements: 7.4, 4.4, 4.5_

  - [ ]* 7.2 Write property test for linking modification validation
    - **Property 13: Toolpath link modification validation**
    - **Validates: Requirements 4.4, 4.5**

  - [x] 7.3 Add `POST /cam/toolpath/{id}/linking` endpoint in `FusionMCPBridge/FusionMCPBridge.py`
    - Handle linking parameter modification requests
    - Validate changes against operation-specific constraints
    - Return modification results with validation details
    - Handle invalid modifications with clear error messages
    - _Requirements: 7.4, 4.4, 4.5_

  - [x] 7.4 Add `modify_toolpath_passes()` tool to `Server/MCP_Server.py`
    - Create MCP tool with toolpath_id and pass_config parameters
    - Send HTTP request to `/cam/toolpath/{id}/passes` endpoint
    - Handle modification validation and response processing
    - Include comprehensive error handling and user feedback
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [x] 7.5 Add `modify_toolpath_linking()` tool to `Server/MCP_Server.py`
    - Create MCP tool with toolpath_id and linking_config parameters
    - Send HTTP request to `/cam/toolpath/{id}/linking` endpoint
    - Handle operation-specific modification validation
    - Include detailed error messages for invalid modifications
    - _Requirements: 7.4, 4.4, 4.5_

- [x] 8. Add efficiency analysis and optimization features
  - [x] 8.1 Create efficiency analysis functions in `FusionMCPBridge/cam.py`
    - Calculate estimated machining times for passes
    - Analyze material removal rates and efficiency
    - Identify tool change optimization opportunities
    - Provide stock-to-leave calculation validation
    - _Requirements: 3.4, 5.5, 3.3, 6.2_

  - [ ]* 8.2 Write property test for efficiency metrics
    - **Property 8: Pass efficiency metrics provision**
    - **Validates: Requirements 3.4, 5.5**

  - [ ]* 8.3 Write property test for stock-to-leave calculations
    - **Property 7: Stock-to-leave calculation accuracy**
    - **Validates: Requirements 3.3, 6.2**

  - [x] 8.4 Create conflict detection functions in `FusionMCPBridge/cam.py`
    - Identify conflicts between pass parameters and tool capabilities
    - Validate tool compatibility across pass sequences
    - Check for parameter inconsistencies within passes
    - Provide recommendations for conflict resolution
    - _Requirements: 3.5_

  - [ ]* 8.5 Write property test for conflict detection
    - **Property 9: Pass-tool conflict identification**
    - **Validates: Requirements 3.5**

- [x] 9. Ensure backward compatibility and integration
  - [x] 9.1 Verify existing toolpath APIs remain unchanged
    - Test existing `/cam/toolpaths` endpoint functionality
    - Ensure response structures are preserved
    - Validate that existing MCP tools continue working
    - Test integration with toolpath heights functionality
    - _Requirements: Maintain existing functionality_

  - [ ]* 9.2 Write property test for backward compatibility
    - **Property 17: Backward compatibility preservation**
    - **Validates: Existing functionality preservation**

  - [x] 9.3 Test integration with existing CAM functionality
    - Verify pass/linking data works with existing height parameters
    - Test combined toolpath analysis workflows
    - Ensure consistent error handling across all CAM endpoints
    - Validate performance with complex CAM documents
    - _Requirements: Integration with existing features_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Integration testing and validation
  - [x] 11.1 Test complete MCP Server → HTTP → Fusion Add-In → Fusion 360 API chain
    - Verify pass and linking data extraction with real CAM documents
    - Test with various operation types (2D Pocket, Adaptive, Contour, Drill, Trace)
    - Validate parameter modification workflows with actual operations
    - Test sequence analysis with complex toolpath dependencies
    - _Requirements: All requirements need end-to-end validation_

  - [x] 11.2 Test error scenarios and edge cases
    - Operations without pass configuration
    - Invalid toolpath and setup IDs
    - Modification attempts on read-only parameters
    - Complex toolpath sequences with circular dependencies
    - _Requirements: Error handling for all scenarios_

  - [ ]* 11.3 Write integration tests for end-to-end workflows
    - Test complete pass analysis and modification workflows
    - Validate MCP tool responses match HTTP endpoint data
    - Ensure consistent behavior across different operation types

- [x] 12. Final Checkpoint - Make sure all tests are passing
  - Ensure all tests pass, ask the user if questions arise.