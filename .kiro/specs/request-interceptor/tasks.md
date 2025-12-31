# Implementation Plan

- [x] 1. Create interceptor module with state management
  - [x] 1.1 Create `Server/interceptor.py` with global state variable `_interceptor_enabled` defaulting to `False`
    - Implement `is_interceptor_enabled()`, `set_interceptor_enabled(enabled: bool)`, and `toggle_interceptor()` functions
    - _Requirements: 1.1, 1.4, 4.1_
  - [ ]* 1.2 Write property test for runtime toggle immediacy
    - **Property 5: Runtime toggle immediacy**
    - **Validates: Requirements 4.2**

- [x] 2. Implement response logging function
  - [x] 2.1 Add `log_response(endpoint: str, response_data: any, method: str)` function to `interceptor.py`
    - Format output with separator lines, endpoint URL, HTTP method, and indented JSON
    - Handle non-JSON data gracefully with error message
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 2.2 Write property test for output format correctness
    - **Property 4: Output format correctness**
    - **Validates: Requirements 2.2, 2.3, 2.4**

- [x] 3. Implement interceptor wrapper function
  - [x] 3.1 Add `intercept_response(endpoint: str, response: requests.Response, method: str)` function
    - Check if interceptor is enabled, call `log_response` if so
    - Parse and return JSON response data unchanged
    - _Requirements: 3.1, 3.2, 3.3_
  - [ ]* 3.2 Write property test for interceptor transparency
    - **Property 1: Interceptor transparency**
    - **Validates: Requirements 3.3**
  - [ ]* 3.3 Write property test for logging when enabled
    - **Property 2: Logging occurs when enabled**
    - **Validates: Requirements 1.2, 2.1**
  - [ ]* 3.4 Write property test for no logging when disabled
    - **Property 3: No logging when disabled**
    - **Validates: Requirements 1.3**

- [x] 4. Integrate interceptor into MCP_Server.py
  - [x] 4.1 Modify `send_request` function to use `intercept_response` for POST requests
    - Import interceptor module
    - Replace direct `response.json()` call with `intercept_response(endpoint, response, "POST")`
    - _Requirements: 3.1_
  - [x] 4.2 Modify CAM tool GET requests to use `intercept_response`
    - Update `list_cam_toolpaths`, `get_toolpath_details`, `get_tool_info` to use interceptor
    - _Requirements: 3.2_

- [x] 5. Add MCP tool for runtime toggle
  - [x] 5.1 Create `toggle_response_interceptor` MCP tool in `MCP_Server.py`
    - Expose `toggle_interceptor()` as an MCP tool for AI assistants to enable/disable debugging
    - Return current state after toggle
    - _Requirements: 4.1, 4.2_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
