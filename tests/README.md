# CAM Toolpath Passes and Linking - Test Suite

This directory contains comprehensive tests for backward compatibility and integration of the new CAM toolpath passes and linking functionality.

## Test Structure

### 1. Backward Compatibility Tests (`test_backward_compatibility.py`)

Tests that ensure existing CAM APIs continue to work unchanged:

- **Code Structure Compatibility**: Verifies that all existing functions and endpoints are still present
- **API Response Structure**: Ensures response formats haven't changed
- **MCP Tool Compatibility**: Verifies existing MCP tools still work
- **Performance Regression**: Checks that new features haven't slowed down existing APIs

### 2. Integration Tests (`test_cam_integration.py`)

Tests that verify new features integrate properly with existing functionality:

- **Combined Data Consistency**: Ensures heights, passes, and linking data are consistent
- **Error Handling Consistency**: Verifies error responses are uniform across endpoints
- **Performance with Complex Workflows**: Tests performance when using multiple features
- **Complete Analysis Workflows**: Simulates realistic user workflows

### 3. Manual Test Script (`manual_compatibility_test.py`)

A standalone script for manual testing when Fusion 360 is running:

- Tests all existing endpoints
- Tests new endpoints
- Provides detailed output and summary
- Can be run independently of pytest

## Running Tests

### Prerequisites

1. **Install Dependencies**:
   ```bash
   uv add pytest requests
   ```

2. **For Full Integration Tests**: Fusion 360 must be running with the FusionMCPBridge add-in active

### Test Execution

#### 1. Quick Validation (Recommended)

Use the comprehensive validation runner:

```bash
# Run all available tests (structure + integration if Fusion available)
python tests/run_integration_validation.py

# Run with verbose output
python tests/run_integration_validation.py --verbose

# Run only structure tests (no Fusion 360 required)
python tests/run_integration_validation.py --structure-only
```

#### 2. Code Structure Tests (No Fusion 360 Required)

These tests verify that the code structure and imports are correct:

```bash
# Run only structure compatibility tests
python -m pytest tests/test_backward_compatibility.py::TestCodeStructureCompatibility -v

# Expected output: All tests should PASS
```

#### 3. Full Test Suite (Requires Fusion 360)

When Fusion 360 is running with CAM data:

```bash
# Run all tests
python -m pytest tests/ -v

# Run only backward compatibility tests
python -m pytest tests/test_backward_compatibility.py -v

# Run only integration tests  
python -m pytest tests/test_cam_integration.py -v

# Run end-to-end integration tests
python -m pytest tests/test_integration_end_to_end.py -v

# Run error scenario tests
python -m pytest tests/test_error_scenarios_edge_cases.py -v
```

#### 4. Manual Testing Script

For interactive testing and debugging:

```bash
# Run manual test script
python tests/manual_compatibility_test.py

# Run integration validation script
python tests/validate_integration.py
```

## Test Scenarios

### Scenario 1: Development Environment (No Fusion 360)

```bash
# Verify code structure is correct
python -m pytest tests/test_backward_compatibility.py::TestCodeStructureCompatibility -v
```

**Expected Result**: All structure tests pass, confirming that:
- All existing functions are present in the code
- New functions have been added correctly
- Configuration files contain all required endpoints
- No breaking changes to existing code structure

### Scenario 2: Fusion 360 Running (With CAM Data)

```bash
# First, verify Fusion 360 is accessible
curl http://localhost:5001/test_connection

# Run comprehensive test suite
python -m pytest tests/ -v

# Or run manual test for detailed output
python tests/manual_compatibility_test.py
```

**Expected Result**: All tests pass, confirming that:
- Existing endpoints work unchanged
- New endpoints function correctly
- Data consistency is maintained across endpoints
- Performance is acceptable
- Error handling is consistent

### Scenario 3: Fusion 360 Running (No CAM Data)

```bash
# Run tests - should skip appropriately
python -m pytest tests/ -v
```

**Expected Result**: Tests are skipped with appropriate messages when no CAM data is available.

## Test Coverage

### Existing Functionality Tested

- `/cam/toolpaths` - List all toolpaths
- `/cam/toolpaths/heights` - List toolpaths with heights
- `/cam/toolpath/{id}/heights` - Individual toolpath heights
- `/cam/tools` - List CAM tools
- MCP tools: `list_cam_toolpaths`, `get_toolpath_details`, etc.

### New Functionality Tested

- `/cam/toolpath/{id}/passes` - Toolpath pass configuration
- `/cam/toolpath/{id}/linking` - Toolpath linking parameters
- `/cam/setup/{id}/sequence` - Setup sequence analysis
- MCP tools: `get_toolpath_passes`, `get_toolpath_linking`, etc.

### Integration Scenarios Tested

- Heights + Passes data consistency
- Heights + Linking data consistency
- Sequential endpoint access performance
- Combined workflow scenarios
- Error handling across all endpoints
- Tool data consistency across endpoints

### End-to-End Integration Tests (`test_integration_end_to_end.py`)

Complete MCP Server → HTTP → Fusion Add-In → Fusion 360 API chain validation:

- **Pass Data Extraction**: Real CAM documents with various operation types
- **Linking Data Extraction**: Operation-specific parameters (2D Pocket, Adaptive, Contour, Drill, Trace)
- **Sequence Analysis**: Complex toolpath dependencies and optimization recommendations
- **Parameter Modification**: Validation workflows with actual operations
- **Complete Workflows**: Realistic user scenarios combining all features
- **Data Consistency**: Cross-endpoint validation of toolpath information
- **Operation-Specific Testing**: Validation for different CAM operation types

### Error Scenarios and Edge Cases (`test_error_scenarios_edge_cases.py`)

Comprehensive error handling validation:

- **Invalid IDs**: Various invalid toolpath and setup ID formats
- **Missing Configuration**: Operations without pass or linking configuration
- **Read-Only Parameters**: Modification attempts on protected parameters
- **Malformed Requests**: Invalid JSON and request structures
- **Concurrent Modifications**: Multiple simultaneous modification attempts
- **Edge Case Values**: Boundary values, extreme values, special characters
- **Network Scenarios**: Timeout handling and performance validation
- **Error Consistency**: Consistent error messages across endpoints
- **Complex Scenarios**: Empty documents, large datasets, special characters

## Troubleshooting

### Common Issues

1. **"Fusion 360 add-in server not running"**
   - Start Fusion 360
   - Ensure FusionMCPBridge add-in is running (Scripts and Add-Ins panel)
   - Verify with: `curl http://localhost:5001/test_connection`

2. **"No toolpaths available for testing"**
   - Switch to MANUFACTURE workspace in Fusion 360
   - Create at least one CAM setup with toolpath operations
   - Ensure operations are valid and generated

3. **Tests fail with connection errors**
   - Check Fusion 360 add-in status
   - Restart the add-in if necessary
   - Verify no firewall blocking localhost:5001

4. **Import errors in tests**
   - Ensure pytest is installed: `uv add pytest`
   - Run from project root directory
   - Check Python path includes project directories

### Debug Mode

For detailed debugging, run tests with maximum verbosity:

```bash
python -m pytest tests/ -v -s --tb=long
```

Or use the manual test script for step-by-step verification:

```bash
python tests/manual_compatibility_test.py
```

## Continuous Integration

These tests are designed to work in CI environments:

- **Structure tests** can run without Fusion 360
- **Integration tests** are skipped when Fusion 360 is not available
- **Exit codes** indicate success/failure appropriately
- **Test output** is formatted for CI consumption

Example CI configuration:

```yaml
# Run structure tests (always)
- name: Test Code Structure
  run: python -m pytest tests/test_backward_compatibility.py::TestCodeStructureCompatibility -v

# Run integration tests (only if Fusion 360 available)
- name: Test Integration (if Fusion available)
  run: python -m pytest tests/ -v
  continue-on-error: true  # Don't fail CI if Fusion not available
```

## Contributing

When adding new CAM functionality:

1. **Add structure tests** to verify new functions exist
2. **Add integration tests** to verify compatibility with existing features
3. **Update manual test script** to include new endpoints
4. **Run full test suite** before submitting changes
5. **Document any new test scenarios** in this README

## Test Results Interpretation

### All Tests Pass ✅
- Backward compatibility is maintained
- Integration works correctly
- Ready for production use

### Structure Tests Pass, Integration Tests Skipped ⚠️
- Code structure is correct
- Integration tests need Fusion 360 to run
- Manual testing recommended before deployment

### Some Tests Fail ❌
- Backward compatibility issues detected
- Review failing tests for specific problems
- Fix issues before deployment

### All Tests Fail ❌
- Major compatibility issues
- Fusion 360 server may not be running
- Check prerequisites and troubleshooting guide