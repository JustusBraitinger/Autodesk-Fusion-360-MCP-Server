# Implementation Plan

- [x] 1. Enhance CAM module height parameter extraction
  - [x] 1.1 Enhance `_extract_heights_params()` function in `FusionMCPBridge/cam.py`
    - Extract expression strings from height parameters
    - Add parameter metadata (editable, min/max constraints)
    - Include unit information from parameter objects
    - Handle missing parameters gracefully
    - _Requirements: 1.2, 2.3, 2.4, 3.5_

  - [ ]* 1.2 Write property test for enhanced height parameter extraction
    - **Property 2: Height parameter data structure completeness**
    - **Validates: Requirements 2.3, 2.4**

  - [x] 1.3 Create `list_toolpaths_with_heights()` function in `FusionMCPBridge/cam.py`
    - Combine existing `list_all_toolpaths()` with height extraction
    - Return toolpaths with embedded height parameter data
    - Handle CAM documents without height data
    - _Requirements: 1.1, 1.4, 2.1_

  - [ ]* 1.4 Write property test for toolpath listing with heights
    - **Property 1: Height-enabled toolpath response completeness**
    - **Validates: Requirements 1.1, 1.2**

  - [x] 1.5 Create `get_detailed_heights()` function in `FusionMCPBridge/cam.py`
    - Extract comprehensive height information for single toolpath
    - Include all available height parameters with metadata
    - Return structured error for missing toolpaths
    - _Requirements: 2.2, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 1.6 Write property test for detailed height extraction
    - **Property 5: Toolpath lookup accuracy**
    - **Validates: Requirements 2.2**

- [x] 2. Add HTTP endpoints to Fusion Add-In
  - [x] 2.1 Add `GET /cam/toolpaths/heights` endpoint in `FusionMCPBridge/FusionMCPBridge.py`
    - Route to `list_toolpaths_with_heights()` function
    - Return JSON response with toolpaths and height data
    - Handle CAM product validation errors
    - _Requirements: 1.1, 1.4, 2.1, 2.5_

  - [x] 2.2 Add `GET /cam/toolpath/{id}/heights` endpoint in `FusionMCPBridge/FusionMCPBridge.py`
    - Route to `get_detailed_heights()` function
    - Extract toolpath ID from URL path
    - Return 404 for missing toolpaths
    - _Requirements: 2.2, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 2.3 Write property test for HTTP endpoint responses
    - **Property 6: CAM product validation**
    - **Validates: Requirements 2.5**

- [ ] 3. Update server configuration
  - [x] 3.1 Add new endpoints to `Server/config.py`
    - Add `cam_toolpaths_heights` endpoint configuration
    - Add `cam_toolpath_heights` endpoint configuration
    - Maintain consistent naming with existing CAM endpoints
    - _Requirements: 1.5_

- [x] 4. Add MCP tools to server
  - [x] 4.1 Add `list_toolpaths_with_heights()` tool to `Server/MCP_Server.py`
    - Create MCP tool decorator and function
    - Send HTTP request to `/cam/toolpaths/heights` endpoint
    - Handle response parsing and error cases
    - Include German documentation for AI assistant
    - _Requirements: 1.1, 1.4, 2.1_

  - [ ]* 4.2 Write property test for MCP toolpath listing tool
    - **Property 4: Multiple toolpath height consistency**
    - **Validates: Requirements 1.4, 2.1**

  - [x] 4.3 Add `get_toolpath_heights()` tool to `Server/MCP_Server.py`
    - Create MCP tool with toolpath_id parameter
    - Send HTTP request to `/cam/toolpath/{id}/heights` endpoint
    - Handle 404 responses for missing toolpaths
    - Include parameter validation and error handling
    - _Requirements: 2.2, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 4.4 Write property test for specific toolpath height tool
    - **Property 5: Toolpath lookup accuracy**
    - **Validates: Requirements 2.2**

- [x] 5. Enhance error handling and validation
  - [x] 5.1 Add CAM product validation to height extraction functions
    - Check for active document with CAM data
    - Return structured error responses for missing CAM
    - Provide clear error messages for different failure modes
    - _Requirements: 2.5_

  - [ ]* 5.2 Write property test for error handling
    - **Property 3: Graceful degradation for missing height data**
    - **Validates: Requirements 1.3**

  - [x] 5.3 Add height parameter modification validation (optional enhancement)
    - Validate height values against Fusion 360 constraints
    - Enforce height hierarchy rules (clearance > retract > feed)
    - Check parameter editability before modifications
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.4 Write property test for height modification validation
    - **Property 7: Height parameter modification validation**
    - **Validates: Requirements 4.1**

  - [ ]* 5.5 Write property test for height hierarchy constraints
    - **Property 8: Height hierarchy constraints**
    - **Validates: Requirements 4.2, 4.3**

- [x] 6. Ensure backward compatibility
  - [x] 6.1 Verify existing toolpath APIs remain unchanged
    - Test existing `/cam/toolpaths` endpoint functionality
    - Ensure response structure is preserved
    - Validate that existing MCP tools continue working
    - _Requirements: 1.5_

  - [ ]* 6.2 Write property test for backward compatibility
    - **Property 11: Backward compatibility preservation**
    - **Validates: Requirements 1.5**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Integration testing and validation
  - [x] 8.1 Test complete MCP Server → HTTP → Fusion Add-In → Fusion 360 API chain
    - Verify height data extraction with real CAM documents
    - Test with various toolpath types (adaptive, contour, drill, etc.)
    - Validate height parameter accuracy across different operations
    - _Requirements: 1.1, 1.2, 2.1, 2.2_

  - [x] 8.2 Test error scenarios and edge cases
    - Documents without CAM data
    - Toolpaths with missing height parameters
    - Invalid toolpath IDs
    - Read-only height parameters
    - _Requirements: 1.3, 2.5, 4.5_

  - [ ]* 8.3 Write integration tests for end-to-end workflows
    - Test complete height extraction workflows
    - Validate MCP tool responses match HTTP endpoint data
    - Ensure consistent behavior across different CAM document types

- [x] 9. Final Checkpoint - Make sure all tests are passing
  - Ensure all tests pass, ask the user if questions arise.