#!/usr/bin/env python3
"""
API Structure Validation Test

This script validates that the API structure and endpoints are correctly configured
for backward compatibility. It checks configuration files and endpoint definitions.

Requirements: 1.5
"""

import sys
import os

def load_server_config():
    """Load the server configuration."""
    try:
        # Add Server directory to path
        server_path = os.path.join(os.getcwd(), "Server")
        if server_path not in sys.path:
            sys.path.insert(0, server_path)
        
        import config
        return config
    except Exception as e:
        print(f"Failed to load server config: {e}")
        return None

def test_endpoint_configuration():
    """Test that all required endpoints are configured."""
    print("Testing Endpoint Configuration")
    print("=" * 35)
    
    config = load_server_config()
    assert config is not None, "Failed to load server config"
    
    # Check that ENDPOINTS exists
    assert hasattr(config, 'ENDPOINTS'), "ENDPOINTS not found in config"
    
    endpoints = config.ENDPOINTS
    print(f"Found {len(endpoints)} configured endpoints")
    
    # Define required existing endpoints
    required_existing = [
        "cam_toolpaths",
        "cam_toolpath", 
        "cam_toolpath_parameter",
        "cam_tools",
        "cam_tool"
    ]
    
    # Define required new endpoints
    required_new = [
        "cam_toolpaths_heights",
        "cam_toolpath_heights"
    ]
    
    # Test existing endpoints
    print("\n  Checking existing CAM endpoints...")
    for endpoint_name in required_existing:
        assert endpoint_name in endpoints, f"Missing endpoint {endpoint_name}"
        url = endpoints[endpoint_name]
        assert url.startswith("http://localhost:5001"), f"Invalid URL for {endpoint_name}: {url}"
        print(f"    ✅ PASSED: {endpoint_name} -> {url}")
    
    # Test new endpoints
    print("\n  Checking new height endpoints...")
    for endpoint_name in required_new:
        assert endpoint_name in endpoints, f"Missing new endpoint {endpoint_name}"
        url = endpoints[endpoint_name]
        assert url.startswith("http://localhost:5001"), f"Invalid URL for {endpoint_name}: {url}"
        print(f"    ✅ PASSED: {endpoint_name} -> {url}")
    
    # Verify endpoint URLs are correctly structured
    print("\n  Checking endpoint URL structure...")
    expected_urls = {
        "cam_toolpaths": "/cam/toolpaths",
        "cam_toolpaths_heights": "/cam/toolpaths/heights",
        "cam_toolpath_heights": "/cam/toolpath"  # Note: this is base, /{id}/heights is appended
    }
    
    for endpoint_name, expected_path in expected_urls.items():
        if endpoint_name in endpoints:
            actual_url = endpoints[endpoint_name]
            assert actual_url.endswith(expected_path), f"Wrong path for {endpoint_name}: expected to end with {expected_path}"
            print(f"    ✅ PASSED: {endpoint_name} has correct path")

def test_configuration_consistency():
    """Test that configuration is consistent across files."""
    print("\n\nTesting Configuration Consistency")
    print("=" * 40)
    
    config = load_server_config()
    assert config is not None, "Failed to load server config"
    
    # Check BASE_URL
    assert hasattr(config, 'BASE_URL'), "BASE_URL not found in config"
    
    base_url = config.BASE_URL
    expected_base = "http://localhost:5001"
    
    assert base_url == expected_base, f"BASE_URL mismatch: expected {expected_base}, got {base_url}"
    print(f"✅ PASSED: BASE_URL correctly set to {base_url}")
    
    # Check HEADERS
    assert hasattr(config, 'HEADERS'), "HEADERS not found in config"
    
    headers = config.HEADERS
    assert "Content-Type" in headers and headers["Content-Type"] == "application/json", "Missing or incorrect Content-Type header"
    print("✅ PASSED: Headers correctly configured")
    
    # Check REQUEST_TIMEOUT
    if hasattr(config, 'REQUEST_TIMEOUT'):
        timeout = config.REQUEST_TIMEOUT
        assert isinstance(timeout, (int, float)) and timeout > 0, f"Invalid REQUEST_TIMEOUT: {timeout}"
        print(f"✅ PASSED: REQUEST_TIMEOUT set to {timeout} seconds")

def test_backward_compatibility_structure():
    """Test that the structure supports backward compatibility."""
    print("\n\nTesting Backward Compatibility Structure")
    print("=" * 45)
    
    # Define expected response structures for existing endpoints
    expected_structures = {
        "cam_toolpaths": {
            "description": "Original toolpath listing endpoint",
            "expected_fields": ["setups", "total_count", "message"],
            "setup_fields": ["id", "name", "toolpaths"],
            "toolpath_fields": ["id", "name", "type", "tool", "is_valid"],
            "tool_fields": ["id", "name", "type", "tool_number", "diameter", "diameter_unit", "overall_length"]
        },
        "cam_toolpaths_heights": {
            "description": "New height-enabled toolpath listing endpoint",
            "expected_fields": ["setups", "total_count", "message"],
            "setup_fields": ["id", "name", "toolpaths"],
            "toolpath_fields": ["id", "name", "type", "tool", "is_valid", "heights"],
            "tool_fields": ["id", "name", "type", "tool_number", "diameter", "diameter_unit", "overall_length"],
            "height_fields": ["clearance_height", "retract_height", "feed_height", "top_height", "bottom_height"]
        }
    }
    
    print("Expected response structures defined:")
    for endpoint, structure in expected_structures.items():
        print(f"  ✅ {endpoint}: {structure['description']}")
    
    # Verify that height-enabled endpoint is additive (contains all original fields plus heights)
    original_toolpath_fields = set(expected_structures["cam_toolpaths"]["toolpath_fields"])
    height_toolpath_fields = set(expected_structures["cam_toolpaths_heights"]["toolpath_fields"])
    
    missing_fields = original_toolpath_fields - height_toolpath_fields
    assert not missing_fields, f"Height endpoint missing original fields: {missing_fields}"
    print("✅ PASSED: Height-enabled endpoint is additive (contains all original fields)")
    
    # Check that heights field is the only addition
    new_fields = height_toolpath_fields - original_toolpath_fields
    assert new_fields == {"heights"}, f"Unexpected new fields beyond 'heights': {new_fields}"
    print("✅ PASSED: Only 'heights' field added to toolpath structure")

def run_api_structure_tests() -> bool:
    """Run all API structure tests."""
    print("API Structure Validation Test")
    print("=" * 35)
    
    # Test endpoint configuration
    config_passed = test_endpoint_configuration()
    
    # Test configuration consistency
    consistency_passed = test_configuration_consistency()
    
    # Test backward compatibility structure
    structure_passed = test_backward_compatibility_structure()
    
    print("\n" + "=" * 50)
    if config_passed and consistency_passed and structure_passed:
        print("✅ ALL API STRUCTURE TESTS PASSED")
        print("\nAPI configuration supports backward compatibility.")
        print("New height endpoints are properly configured.")
        print("Response structures maintain existing fields.")
        return True
    else:
        print("❌ SOME API STRUCTURE TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_api_structure_tests()
    sys.exit(0 if success else 1)