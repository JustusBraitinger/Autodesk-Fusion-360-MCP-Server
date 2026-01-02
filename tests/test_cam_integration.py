"""
Test integration between existing CAM functionality and new pass/linking features.

This test ensures that:
- Pass/linking data works with existing height parameters
- Combined toolpath analysis workflows function correctly
- Error handling is consistent across all CAM endpoints
- Performance is acceptable with complex CAM documents
"""

import pytest
import requests
import json
import time
from typing import Dict, Any, List, Optional


def is_fusion_server_running():
    """Check if Fusion 360 add-in server is running."""
    try:
        response = requests.get("http://localhost:5001/test_connection", timeout=2)
        return response.status_code == 200
    except:
        return False


class TestCAMIntegration:
    """Test integration between existing and new CAM functionality."""
    
    BASE_URL = "http://localhost:5001"
    
    def test_combined_data_consistency(self):
        """
        Test that heights, passes, and linking data are consistent for the same toolpath.
        
        Verifies that when querying the same toolpath through different endpoints,
        the basic toolpath information (id, name, type) remains consistent.
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        # Get a toolpath ID
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        # Find first toolpath
        toolpath_id = None
        expected_name = None
        expected_type = None
        
        for setup in data["setups"]:
            for toolpath in setup["toolpaths"]:
                toolpath_id = toolpath["id"]
                expected_name = toolpath["name"]
                expected_type = toolpath["type"]
                break
            if toolpath_id:
                break
        
        assert toolpath_id is not None
        
        # Test all endpoints for the same toolpath
        endpoints = [
            f"/cam/toolpath/{toolpath_id}/heights",
            f"/cam/toolpath/{toolpath_id}/passes",
            f"/cam/toolpath/{toolpath_id}/linking"
        ]
        
        responses = {}
        for endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            if response.status_code == 200:
                responses[endpoint] = response.json()
        
        # Verify consistency across endpoints that returned data
        for endpoint, data in responses.items():
            if "id" in data:
                assert data["id"] == toolpath_id, f"ID mismatch in {endpoint}"
            if "name" in data:
                assert data["name"] == expected_name, f"Name mismatch in {endpoint}"
            if "type" in data:
                assert data["type"] == expected_type, f"Type mismatch in {endpoint}"
    
    def test_heights_with_passes_integration(self):
        """
        Test that toolpaths with both heights and passes data work correctly.
        
        Verifies that a toolpath can have both height parameters and pass
        configuration without conflicts.
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        # Get toolpaths with heights
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths/heights")
        assert response.status_code == 200
        
        data = response.json()
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths with heights available")
        
        # Find a toolpath with heights data
        test_toolpath = None
        for setup in data["setups"]:
            for toolpath in setup["toolpaths"]:
                if toolpath.get("heights"):
                    test_toolpath = toolpath
                    break
            if test_toolpath:
                break
        
        if not test_toolpath:
            pytest.skip("No toolpaths with heights data found")
        
        toolpath_id = test_toolpath["id"]
        
        # Get individual heights data
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/heights")
        assert response.status_code == 200
        heights_data = response.json()
        
        # Get passes data (may not exist for all toolpaths)
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/passes")
        if response.status_code == 200:
            passes_data = response.json()
            
            # Verify both datasets are for the same toolpath
            assert heights_data["id"] == passes_data["id"]
            assert heights_data["name"] == passes_data["name"]
            
            # Verify heights data is preserved
            assert "heights" in heights_data
            assert len(heights_data["heights"]) > 0
            
            # If passes exist, verify they don't interfere with heights
            if "passes" in passes_data:
                # Both should be present and non-empty
                assert isinstance(passes_data["passes"], dict)
    
    def test_error_handling_consistency(self):
        """
        Test that error handling is consistent across all CAM endpoints.
        
        Verifies that invalid requests return consistent error structures
        and that error codes are appropriate.
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        invalid_id = "invalid_toolpath_id_12345"
        
        endpoints = [
            f"/cam/toolpath/{invalid_id}/heights",
            f"/cam/toolpath/{invalid_id}/passes", 
            f"/cam/toolpath/{invalid_id}/linking"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            
            # Should return an error status
            assert response.status_code in [400, 404, 422], f"Unexpected status for {endpoint}: {response.status_code}"
            
            # Should return JSON error response
            try:
                error_data = response.json()
                # Should have error information
                assert "error" in error_data or "message" in error_data, f"No error info in {endpoint}"
            except json.JSONDecodeError:
                # Some endpoints might return HTML errors, which is also acceptable
                pass
    
    def test_performance_with_complex_workflows(self):
        """
        Test performance when combining multiple CAM operations.
        
        Simulates complex workflows that query multiple endpoints
        and verifies acceptable performance.
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        # Get all toolpaths
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        list_time = time.time() - start_time
        
        assert response.status_code == 200
        assert list_time < 5.0, f"Listing toolpaths took {list_time:.2f}s (too slow)"
        
        data = response.json()
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths available for performance testing")
        
        # Test sequential access to multiple toolpaths
        toolpath_ids = []
        for setup in data["setups"]:
            for toolpath in setup["toolpaths"][:3]:  # Limit to first 3 per setup
                toolpath_ids.append(toolpath["id"])
        
        if not toolpath_ids:
            pytest.skip("No toolpath IDs found")
        
        # Test accessing multiple endpoints for each toolpath
        total_requests = 0
        total_time = 0
        
        for toolpath_id in toolpath_ids[:5]:  # Limit to first 5 toolpaths
            endpoints = [
                f"/cam/toolpath/{toolpath_id}/heights",
                f"/cam/toolpath/{toolpath_id}/passes",
                f"/cam/toolpath/{toolpath_id}/linking"
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                response = requests.get(f"{self.BASE_URL}{endpoint}")
                request_time = time.time() - start_time
                
                total_requests += 1
                total_time += request_time
                
                # Individual request should complete quickly
                assert request_time < 3.0, f"Request to {endpoint} took {request_time:.2f}s"
        
        # Average request time should be reasonable
        avg_time = total_time / total_requests if total_requests > 0 else 0
        assert avg_time < 2.0, f"Average request time {avg_time:.2f}s is too slow"
    
    def test_setup_sequence_integration(self):
        """
        Test that setup sequence analysis integrates well with toolpath data.
        
        Verifies that sequence analysis provides consistent information
        about toolpaths that can also be queried individually.
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        # Get setups
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data["setups"]:
            pytest.skip("No setups available")
        
        setup_id = data["setups"][0]["id"]
        setup_toolpaths = data["setups"][0]["toolpaths"]
        
        # Get sequence analysis
        response = requests.get(f"{self.BASE_URL}/cam/setup/{setup_id}/sequence")
        if response.status_code != 200:
            pytest.skip("Setup sequence analysis not available")
        
        sequence_data = response.json()
        
        # Verify sequence data structure
        assert "setup_id" in sequence_data
        assert "execution_sequence" in sequence_data
        assert sequence_data["setup_id"] == setup_id
        
        # Verify toolpaths in sequence match setup toolpaths
        sequence_toolpaths = sequence_data["execution_sequence"]
        
        if sequence_toolpaths and setup_toolpaths:
            # Should have same number of toolpaths (or reasonable subset)
            assert len(sequence_toolpaths) <= len(setup_toolpaths)
            
            # Toolpath IDs in sequence should exist in setup
            sequence_ids = {tp["toolpath_id"] for tp in sequence_toolpaths}
            setup_ids = {tp["id"] for tp in setup_toolpaths}
            
            # All sequence IDs should be in setup IDs
            assert sequence_ids.issubset(setup_ids), "Sequence contains unknown toolpath IDs"
    
    def test_combined_analysis_workflow(self):
        """
        Test a complete analysis workflow combining all features.
        
        Simulates a realistic workflow where a user:
        1. Lists all toolpaths
        2. Gets heights for specific toolpaths
        3. Gets passes information
        4. Gets linking information
        5. Analyzes setup sequence
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        workflow_data = {}
        
        # Step 1: List all toolpaths
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        toolpaths_data = response.json()
        workflow_data["toolpaths"] = toolpaths_data
        
        if not toolpaths_data["setups"]:
            pytest.skip("No setups available for workflow test")
        
        # Step 2: Get heights for first toolpath
        first_setup = toolpaths_data["setups"][0]
        if not first_setup["toolpaths"]:
            pytest.skip("No toolpaths in first setup")
        
        first_toolpath_id = first_setup["toolpaths"][0]["id"]
        
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{first_toolpath_id}/heights")
        if response.status_code == 200:
            workflow_data["heights"] = response.json()
        
        # Step 3: Get passes information
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{first_toolpath_id}/passes")
        if response.status_code == 200:
            workflow_data["passes"] = response.json()
        
        # Step 4: Get linking information
        response = requests.get(f"{self.BASE_URL}/cam/toolpath/{first_toolpath_id}/linking")
        if response.status_code == 200:
            workflow_data["linking"] = response.json()
        
        # Step 5: Analyze setup sequence
        setup_id = first_setup["id"]
        response = requests.get(f"{self.BASE_URL}/cam/setup/{setup_id}/sequence")
        if response.status_code == 200:
            workflow_data["sequence"] = response.json()
        
        # Verify workflow data consistency
        if "heights" in workflow_data:
            assert workflow_data["heights"]["id"] == first_toolpath_id
        
        if "passes" in workflow_data:
            assert workflow_data["passes"]["id"] == first_toolpath_id
        
        if "linking" in workflow_data:
            assert workflow_data["linking"]["id"] == first_toolpath_id
        
        if "sequence" in workflow_data:
            assert workflow_data["sequence"]["setup_id"] == setup_id
        
        # Verify we got meaningful data from the workflow
        assert len(workflow_data) >= 1, "Workflow should collect at least toolpaths data"


class TestCAMDataIntegrity:
    """Test data integrity across different CAM endpoints."""
    
    BASE_URL = "http://localhost:5001"
    
    def test_toolpath_data_consistency_across_endpoints(self):
        """
        Test that the same toolpath returns consistent basic data across all endpoints.
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        # Get toolpaths with heights (includes basic toolpath info)
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths/heights")
        assert response.status_code == 200
        
        data = response.json()
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths available")
        
        # Get first toolpath
        test_toolpath = None
        for setup in data["setups"]:
            if setup["toolpaths"]:
                test_toolpath = setup["toolpaths"][0]
                break
        
        assert test_toolpath is not None
        toolpath_id = test_toolpath["id"]
        
        # Collect data from all endpoints
        endpoint_data = {}
        
        endpoints = [
            ("heights", f"/cam/toolpath/{toolpath_id}/heights"),
            ("passes", f"/cam/toolpath/{toolpath_id}/passes"),
            ("linking", f"/cam/toolpath/{toolpath_id}/linking")
        ]
        
        for name, endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            if response.status_code == 200:
                endpoint_data[name] = response.json()
        
        # Verify consistency of basic fields across endpoints
        basic_fields = ["id", "name", "type"]
        
        if len(endpoint_data) > 1:
            reference_data = list(endpoint_data.values())[0]
            
            for field in basic_fields:
                if field in reference_data:
                    reference_value = reference_data[field]
                    
                    for endpoint_name, data in endpoint_data.items():
                        if field in data:
                            assert data[field] == reference_value, \
                                f"Field '{field}' mismatch: {endpoint_name} has '{data[field]}', expected '{reference_value}'"
    
    def test_tool_data_consistency(self):
        """
        Test that tool information is consistent across different endpoints.
        """
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
        
        # Get toolpaths (includes tool info)
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data["setups"] or not any(setup["toolpaths"] for setup in data["setups"]):
            pytest.skip("No toolpaths available")
        
        # Find toolpath with tool data
        test_toolpath = None
        for setup in data["setups"]:
            for toolpath in setup["toolpaths"]:
                if toolpath.get("tool") and toolpath["tool"].get("name"):
                    test_toolpath = toolpath
                    break
            if test_toolpath:
                break
        
        if not test_toolpath:
            pytest.skip("No toolpaths with tool data found")
        
        toolpath_id = test_toolpath["id"]
        expected_tool_name = test_toolpath["tool"]["name"]
        
        # Check tool consistency in individual endpoints
        endpoints = [
            f"/cam/toolpath/{toolpath_id}/heights",
            f"/cam/toolpath/{toolpath_id}/passes"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                if "tool" in data and "name" in data["tool"]:
                    assert data["tool"]["name"] == expected_tool_name, \
                        f"Tool name mismatch in {endpoint}"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])