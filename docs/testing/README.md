# CAM Toolpath Passes and Linking - Test Suite

This directory contains comprehensive tests for backward compatibility and integration of the CAM toolpath functionality.

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
   uv sync
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
   - Ensure pytest is installed: `uv sync`
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
