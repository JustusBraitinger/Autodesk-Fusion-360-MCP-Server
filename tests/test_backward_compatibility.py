"""
Test backward compatibility of existing CAM toolpath APIs.

This test ensures that the new pass and linking functionality does not break
existing toolpath APIs and that response structures remain unchanged.
"""

import pytest
import requests
import json


def is_fusion_server_running():
    """Check if Fusion 360 add-in server is running."""
    try:
        response = requests.get("http://localhost:5001/test_connection", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.mark.skipif(not is_fusion_server_running(), reason="Fusion 360 add-in server not running")
class TestBackwardCompatibility:
    """Test suite for backward compatibility of existing CAM APIs."""
    
    BASE_URL = "http://localhost:5001"
    
    def test_cam_toolpaths_endpoint_structure(self):
        """
        Test that /cam/toolpaths endpoint maintains its original structure.
        
        Verifies:
        - Endpoint is accessible
        - Response contains expected fields
        - Response structure matches original format
        """
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        
        # Should return 200 OK
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify top-level structure
        assert "setups" in data
        assert "total_count" in data
        assert isinstance(data["setups"], list)
        assert isinstance(data["total_count"], int)
        
        # If there are setups, verify their structure
        if data["setups"]:
            setup = data["setups"][0]
            assert "id" in setup
            assert "name" in setup
            assert "toolpaths" in setup
            assert isinstance(setup["toolpaths"], list)
            
            # If there are toolpaths, verify their structure
            if setup["toolpaths"]:
                toolpath = setup["toolpaths"][0]
                required_fields = ["id", "name", "type", "tool", "is_valid"]
                for field in required_fields:
                    assert field in toolpath, f"Missing required field: {field}"
                
                # Verify tool structure
                tool = toolpath["tool"]
                assert isinstance(tool, dict)
                assert "name" in tool
    
    def test_cam_toolpaths_heights_endpoint_structure(self):
        """
        Test that /cam/toolpaths/heights endpoint maintains its original structure.
        
        Verifies:
        - Endpoint is accessible
        - Response contains expected fields including heights data
        - Heights data structure is preserved
        """
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths/heights")
        
        # Should return 200 OK
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify top-level structure
        assert "setups" in data
        assert "total_count" in data
        assert isinstance(data["setups"], list)
        assert isinstance(data["total_count"], int)
        
        # If there are setups with toolpaths, verify heights structure
        if data["setups"]:
            setup = data["setups"][0]
            if setup["toolpaths"]:
                toolpath = setup["toolpaths"][0]
                
                # Verify heights field exists
                assert "heights" in toolpath
                heights = toolpath["heights"]
                assert isinstance(heights, dict)
                
                # Common height parameters that should be present
                expected_height_params = [
                    "clearance_height", "retract_height", "feed_height", 
                    "top_height", "bottom_height"
                ]
                
                # At least some height parameters should be present
                height_params_found = [param for param in expected_height_params if param in heights]
                assert len(height_params_found) > 0, "No expected height parameters found"
                
                # Verify height parameter structure
                for param_name in height_params_found:
                    param = heights[param_name]
                    assert isinstance(param, dict)
                    assert "value" in param
                    assert "type" in param
    
    def test_individual_toolpath_heights_endpoint(self):
        """
        Test that individual toolpath heights endpoint works correctly.
        
        First gets a toolpath ID, then tests the individual endpoint.
        """
        # First get a list of toolpaths to get an ID
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        
        # Skip test if no toolpaths available
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        # Get first available toolpath ID
        toolpath_id = None
        for setup in data["setups"]:
            if setup["toolpaths"]:
                toolpath_id = setup["toolpaths"][0]["id"]
                break
        
        assert toolpath_id is not None, "Could not find a toolpath ID"
        
        # Test individual toolpath heights endpoint
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/heights")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "name" in data
        assert "type" in data
        assert "heights" in data
        assert data["id"] == toolpath_id
        
        # Verify heights structure
        heights = data["heights"]
        assert isinstance(heights, dict)
    
    def test_cam_tools_endpoint_structure(self):
        """
        Test that /cam/tools endpoint maintains its original structure.
        """
        response = requests.get(f"{self.BASE_URL}/cam/tools")
        
        # Should return 200 OK
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        
        # If there are tools, verify their structure
        if data:
            tool = data[0]
            assert isinstance(tool, dict)
            # Tools should have at least a name or description
            assert "name" in tool or "description" in tool
    
    def test_response_format_consistency(self):
        """
        Test that response formats are consistent across endpoints.
        
        Verifies:
        - JSON responses are properly formatted
        - Error responses follow consistent structure
        - Content-Type headers are correct
        """
        endpoints = [
            "/cam/toolpaths",
            "/cam/toolpaths/heights", 
            "/cam/tools"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            
            # Should return valid JSON
            assert response.headers.get("content-type", "").startswith("application/json")
            
            # Should be parseable as JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                pytest.fail(f"Endpoint {endpoint} returned invalid JSON")
            
            # Should not be empty response
            assert data is not None
    
    def test_error_handling_consistency(self):
        """
        Test that error handling remains consistent.
        
        Tests invalid toolpath IDs and ensures error responses are structured.
        """
        # Test invalid toolpath ID
        invalid_id = "invalid_toolpath_id_12345"
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{invalid_id}/heights")
        
        # Should return an error (404 or structured error response)
        if response.status_code == 404:
            # 404 is acceptable for missing resources
            pass
        else:
            # If not 404, should be a structured error response
            data = response.json()
            assert "error" in data or "message" in data
    
    def test_existing_mcp_tools_compatibility(self):
        """
        Test that existing MCP tools continue to work.
        
        This is a placeholder test that would be run with the MCP server.
        In a real test environment, this would verify that:
        - list_cam_toolpaths() still works
        - get_toolpath_details() still works  
        - list_toolpaths_with_heights() still works
        - get_toolpath_heights() still works
        """
        # This test would require the MCP server to be running
        # For now, we'll just verify the HTTP endpoints they depend on
        
        # Test the HTTP endpoints that MCP tools use
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths/heights")
        assert response.status_code == 200
        
        response = requests.get(f"{self.BASE_URL}/cam/tools")
        assert response.status_code == 200
    
    def test_performance_regression(self):
        """
        Test that performance has not regressed significantly.
        
        Measures response times for existing endpoints to ensure
        new functionality hasn't slowed down existing APIs.
        """
        import time
        
        endpoints = [
            "/cam/toolpaths",
            "/cam/toolpaths/heights",
            "/cam/tools"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
            end_time = time.time()
            
            # Should complete within reasonable time (10 seconds max)
            response_time = end_time - start_time
            assert response_time < 10.0, f"Endpoint {endpoint} took {response_time:.2f}s (too slow)"
            
            # Should return successful response
            assert response.status_code == 200


@pytest.mark.skipif(not is_fusion_server_running(), reason="Fusion 360 add-in server not running")
class TestToolpathHeightsIntegration:
    """Test integration between heights functionality and new pass/linking features."""
    
    BASE_URL = "http://localhost:5001"
    
    def test_heights_data_preserved_with_passes(self):
        """
        Test that heights data is preserved when pass data is also present.
        
        Verifies that toolpaths with both heights and passes data
        maintain both sets of information correctly.
        """
        # Get toolpaths with heights
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths/heights")
        assert response.status_code == 200
        
        data = response.json()
        
        # Skip if no toolpaths
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        # Find a toolpath with heights data
        toolpath_with_heights = None
        for setup in data["setups"]:
            for toolpath in setup["toolpaths"]:
                if toolpath.get("heights"):
                    toolpath_with_heights = toolpath
                    break
            if toolpath_with_heights:
                break
        
        if not toolpath_with_heights:
            pytest.skip("No toolpaths with heights data found")
        
        toolpath_id = toolpath_with_heights["id"]
        
        # Test that individual heights endpoint still works
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/heights")
        assert response.status_code == 200
        
        heights_data = response.json()
        assert "heights" in heights_data
        
        # Test that passes endpoint works (may return empty if no passes)
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/passes")
        # Should not error, even if no passes data
        assert response.status_code in [200, 404]  # 404 acceptable if no passes
    
    def test_combined_workflow_compatibility(self):
        """
        Test that combined workflows (heights + passes + linking) work together.
        
        Simulates a typical workflow where a user might query heights,
        then passes, then linking for the same toolpath.
        """
        # Get a toolpath ID
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        toolpath_id = None
        for setup in data["setups"]:
            if setup["toolpaths"]:
                toolpath_id = setup["toolpaths"][0]["id"]
                break
        
        assert toolpath_id is not None
        
        # Test sequential access to all endpoints for same toolpath
        endpoints = [
            f"/cam/toolpath/{toolpath_id}/heights",
            f"/cam/toolpath/{toolpath_id}/passes", 
            f"/cam/toolpath/{toolpath_id}/linking"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            # Should not cause server errors
            assert response.status_code in [200, 404], f"Endpoint {endpoint} failed with {response.status_code}"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])


class TestCodeStructureCompatibility:
    """Test that code structure and imports remain compatible."""
    
    def test_cam_module_imports(self):
        """Test that CAM module can be imported and has expected functions."""
        # Test that we can import the module structure
        import sys
        import os
        
        # Add the FusionMCPBridge path for testing
        bridge_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "FusionMCPBridge")
        if bridge_path not in sys.path:
            sys.path.insert(0, bridge_path)
        
        # We can't actually import cam.py because it requires adsk modules
        # But we can verify the file exists and has the expected structure
        cam_file = os.path.join(bridge_path, "cam.py")
        assert os.path.exists(cam_file), "cam.py module not found"
        
        # Read the file and verify key functions exist
        with open(cam_file, 'r') as f:
            content = f.read()
        
        # Verify existing functions are still present
        existing_functions = [
            "def list_toolpaths_with_heights",
            "def get_detailed_heights", 
            "def list_all_toolpaths",
            "def get_cam_product",
            "def validate_cam_product_with_details"
        ]
        
        for func in existing_functions:
            assert func in content, f"Function {func} not found in cam.py"
        
        # Verify new functions are present
        new_functions = [
            "def get_toolpath_passes",
            "def get_toolpath_linking",
            "def analyze_setup_sequence"
        ]
        
        for func in new_functions:
            assert func in content, f"New function {func} not found in cam.py"
    
    def test_server_config_compatibility(self):
        """Test that server configuration maintains existing endpoints."""
        import sys
        import os
        
        # Add the Server path for testing
        server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Server")
        if server_path not in sys.path:
            sys.path.insert(0, server_path)
        
        # Import config module
        try:
            import config
        except ImportError:
            pytest.skip("Cannot import config module (requires proper Python path)")
        
        # Verify existing endpoints are still present
        existing_endpoints = [
            "cam_toolpaths",
            "cam_toolpaths_heights", 
            "cam_toolpath_heights",
            "cam_tools"
        ]
        
        for endpoint in existing_endpoints:
            assert endpoint in config.ENDPOINTS, f"Existing endpoint {endpoint} not found"
        
        # Verify new endpoints are present
        new_endpoints = [
            "cam_toolpath_passes",
            "cam_toolpath_linking",
            "cam_setup_sequence"
        ]
        
        for endpoint in new_endpoints:
            assert endpoint in config.ENDPOINTS, f"New endpoint {endpoint} not found"
    
    def test_mcp_server_tools_compatibility(self):
        """Test that MCP server maintains existing tools."""
        import sys
        import os
        import asyncio
        
        # Add Server directory to path
        server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Server")
        if server_path not in sys.path:
            sys.path.insert(0, server_path)
        
        try:
            # Import the server initialization function
            from Server.MCP_Server import initialize_server
            
            # Initialize the modular server (this will load all modules)
            mcp = initialize_server()
            
            # Get all registered tools
            tools_list = asyncio.run(mcp.list_tools())
            tool_names = [tool.name for tool in tools_list]
            
            # Verify existing MCP tools are still present
            existing_tools = [
                "list_cam_toolpaths",
                "get_toolpath_details", 
                "list_cam_tools",
                "list_toolpaths_with_heights",
                "get_toolpath_heights"
            ]
            
            for tool in existing_tools:
                assert tool in tool_names, f"Existing MCP tool {tool} not found in registered tools"
            
            # Verify new MCP tools are present
            new_tools = [
                "get_toolpath_passes",
                "get_toolpath_linking",
                "analyze_toolpath_sequence"
            ]
            
            for tool in new_tools:
                assert tool in tool_names, f"New MCP tool {tool} not found in registered tools"
                
        except Exception as e:
            self.fail(f"Failed to initialize modular server or verify tools: {e}")
    
    def test_fusion_bridge_endpoints_compatibility(self):
        """Test that Fusion bridge maintains existing HTTP endpoints."""
        import os
        
        bridge_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "FusionMCPBridge", "FusionMCPBridge.py")
        assert os.path.exists(bridge_file), "FusionMCPBridge.py not found"
        
        with open(bridge_file, 'r') as f:
            content = f.read()
        
        # Verify existing HTTP endpoints are still present
        existing_endpoints = [
            "/cam/toolpaths",
            "/cam/toolpaths/heights",
            "/cam/toolpath",  # for individual heights
            "/cam/tools"
        ]
        
        for endpoint in existing_endpoints:
            assert endpoint in content, f"Existing HTTP endpoint {endpoint} not found"
        
        # Verify new HTTP endpoints are present
        new_endpoints = [
            "/passes",  # for toolpath passes
            "/linking", # for toolpath linking
            "/sequence" # for setup sequence
        ]
        
        for endpoint in new_endpoints:
            assert endpoint in content, f"New HTTP endpoint {endpoint} not found"