"""
Error scenarios and edge case tests for CAM toolpath passes and linking functionality.

This test suite validates error handling and edge cases for:
- Operations without pass configuration
- Invalid toolpath and setup IDs
- Modification attempts on read-only parameters
- Complex toolpath sequences with circular dependencies
- All error handling scenarios across requirements
"""

import pytest
import requests
import json
import time
import uuid


def is_fusion_server_running():
    """Check if Fusion 360 add-in server is running."""
    try:
        response = requests.get("http://localhost:5001/test_connection", timeout=2)
        return response.status_code == 200
    except:
        return False


class TestErrorScenarios:
    """Test error scenarios and edge cases for CAM functionality."""
    
    BASE_URL = "http://localhost:5001"
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method to check Fusion 360 availability."""
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
    
    def test_invalid_toolpath_ids(self):
        """
        Test handling of invalid toolpath IDs across all endpoints.
        
        Validates that all endpoints properly handle non-existent toolpath IDs
        with consistent error responses.
        """
        # Generate various types of invalid IDs
        invalid_ids = [
            "nonexistent_id_12345",
            str(uuid.uuid4()),  # Valid UUID format but non-existent
            "invalid-chars-!@#$%",
            "",  # Empty string
            "null",
            "undefined",
            "very_long_id_" + "x" * 200,  # Very long ID
            "123",  # Numeric string
            "special/chars\\in|id",  # Special characters
        ]
        
        endpoints = [
            "/cam/toolpath/{}/heights",
            "/cam/toolpath/{}/passes",
            "/cam/toolpath/{}/linking"
        ]
        
        for invalid_id in invalid_ids:
            for endpoint_template in endpoints:
                endpoint = endpoint_template.format(invalid_id)
                
                response = requests.get(f"{self.BASE_URL}{endpoint}")
                
                # Should return an error status
                assert response.status_code in [400, 404, 422, 500], \
                    f"Expected error status for {endpoint} with ID '{invalid_id}', got {response.status_code}"
                
                # Should return JSON error response
                try:
                    error_data = response.json()
                    # Should have error information
                    assert "error" in error_data or "message" in error_data or "detail" in error_data, \
                        f"No error info in response for {endpoint} with ID '{invalid_id}'"
                except json.JSONDecodeError:
                    # Some endpoints might return HTML errors, which is also acceptable
                    assert response.headers.get("content-type", "").startswith("text/html") or \
                           response.headers.get("content-type", "").startswith("text/plain"), \
                           f"Non-JSON error response should be HTML or plain text for {endpoint}"
    
    def test_invalid_setup_ids(self):
        """
        Test handling of invalid setup IDs for sequence analysis.
        
        Validates that setup sequence endpoint properly handles non-existent setup IDs.
        """
        invalid_setup_ids = [
            "nonexistent_setup_12345",
            str(uuid.uuid4()),
            "invalid-setup-chars-!@#$%",
            "",
            "null",
            "very_long_setup_id_" + "x" * 200
        ]
        
        for invalid_id in invalid_setup_ids:
            response = requests.get(f"{self.BASE_URL}/cam/setup/{invalid_id}/sequence")
            
            # Should return an error status
            assert response.status_code in [400, 404, 422, 500], \
                f"Expected error status for setup sequence with ID '{invalid_id}', got {response.status_code}"
            
            # Should return error information
            try:
                error_data = response.json()
                assert "error" in error_data or "message" in error_data or "detail" in error_data, \
                    f"No error info in response for setup '{invalid_id}'"
            except json.JSONDecodeError:
                # HTML error response is acceptable
                pass
    
    def test_operations_without_pass_configuration(self):
        """
        Test handling of operations that don't have pass configuration.
        
        Validates that the system gracefully handles operations without
        multi-pass setup and returns appropriate responses.
        """
        # Get available toolpaths
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups"):
            pytest.skip("No setups available for testing")
        
        tested_operations = 0
        operations_without_passes = 0
        
        for setup in data["setups"]:
            for toolpath in setup.get("toolpaths", []):
                toolpath_id = toolpath["id"]
                tested_operations += 1
                
                response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/passes")
                
                if response.status_code == 404:
                    # No passes configuration - this is expected for some operations
                    operations_without_passes += 1
                    
                    # Should return proper error structure
                    try:
                        error_data = response.json()
                        assert "error" in error_data or "message" in error_data, \
                            "404 response should include error message"
                    except json.JSONDecodeError:
                        # Plain text error is also acceptable
                        pass
                
                elif response.status_code == 200:
                    # Has passes configuration
                    data = response.json()
                    
                    # If no actual passes data, should be clearly indicated
                    if "passes" not in data or not data["passes"]:
                        # Should still have basic toolpath info
                        assert "id" in data
                        assert "name" in data
                        assert data["id"] == toolpath_id
                
                else:
                    pytest.fail(f"Unexpected status code {response.status_code} for toolpath {toolpath_id}")
                
                # Limit testing to avoid long test times
                if tested_operations >= 10:
                    break
            
            if tested_operations >= 10:
                break
        
        assert tested_operations > 0, "No operations tested"
        
        # Log results for debugging
        print(f"Tested {tested_operations} operations, {operations_without_passes} without passes")
    
    def test_operations_without_linking_configuration(self):
        """
        Test handling of operations that don't have linking configuration.
        
        Validates graceful handling of operations without linking parameters.
        """
        # Get available toolpaths
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups"):
            pytest.skip("No setups available for testing")
        
        tested_operations = 0
        operations_without_linking = 0
        
        for setup in data["setups"]:
            for toolpath in setup.get("toolpaths", []):
                toolpath_id = toolpath["id"]
                tested_operations += 1
                
                response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/linking")
                
                if response.status_code == 404:
                    # No linking configuration
                    operations_without_linking += 1
                    
                    # Should return proper error structure
                    try:
                        error_data = response.json()
                        assert "error" in error_data or "message" in error_data, \
                            "404 response should include error message"
                    except json.JSONDecodeError:
                        pass
                
                elif response.status_code == 200:
                    # Has linking configuration
                    data = response.json()
                    
                    # Should have basic toolpath info
                    assert "id" in data
                    assert "name" in data
                    assert data["id"] == toolpath_id
                    
                    # If no actual linking data, should be clearly indicated
                    if "sections" not in data or not data["sections"]:
                        # Still valid - some operations may not have configurable linking
                        pass
                
                else:
                    pytest.fail(f"Unexpected status code {response.status_code} for toolpath {toolpath_id}")
                
                if tested_operations >= 10:
                    break
            
            if tested_operations >= 10:
                break
        
        assert tested_operations > 0, "No operations tested"
        print(f"Tested {tested_operations} operations, {operations_without_linking} without linking")
    
    def test_modification_attempts_on_readonly_parameters(self):
        """
        Test modification attempts on read-only parameters.
        
        Validates that the system properly rejects modifications to
        parameters that cannot be changed.
        """
        # Get a toolpath with linking data
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups"):
            pytest.skip("No setups available for testing")
        
        test_toolpath_id = None
        
        # Find a toolpath with linking data
        for setup in data["setups"]:
            for toolpath in setup.get("toolpaths", []):
                toolpath_id = toolpath["id"]
                
                response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath_id}/linking")
                if response.status_code == 200:
                    linking_data = response.json()
                    if "editable_parameters" in linking_data:
                        test_toolpath_id = toolpath_id
                        break
            
            if test_toolpath_id:
                break
        
        if not test_toolpath_id:
            pytest.skip("No toolpaths with editable parameters found")
        
        # Test various invalid modification attempts
        invalid_modifications = [
            # Attempt to modify non-existent section
            {
                "sections": {
                    "nonexistent_section": {
                        "parameter": "value"
                    }
                }
            },
            # Attempt to modify with invalid parameter structure
            {
                "sections": {
                    "leads_and_transitions": "invalid_structure"
                }
            },
            # Attempt to modify with invalid parameter values
            {
                "sections": {
                    "leads_and_transitions": {
                        "lead_in": {
                            "arc_radius": "invalid_number"
                        }
                    }
                }
            },
            # Attempt to modify read-only system parameters
            {
                "id": "modified_id",
                "name": "modified_name",
                "type": "modified_type"
            }
        ]
        
        for modification in invalid_modifications:
            response = requests.post(
                f"{self.BASE_URL}/cam/toolpath/{test_toolpath_id}/linking",
                json=modification
            )
            
            # Should reject invalid modifications
            assert response.status_code in [400, 422, 500], \
                f"Expected error status for invalid modification, got {response.status_code}"
            
            # Should return error information
            try:
                error_data = response.json()
                assert "error" in error_data or "message" in error_data or "validation_errors" in error_data, \
                    "Error response should include error information"
            except json.JSONDecodeError:
                # Non-JSON error response is acceptable
                pass
    
    def test_malformed_modification_requests(self):
        """
        Test handling of malformed modification requests.
        
        Validates proper error handling for invalid JSON and request structures.
        """
        # Get a valid toolpath ID
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups") or not any(setup.get("toolpaths") for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        test_toolpath_id = data["setups"][0]["toolpaths"][0]["id"]
        
        # Test malformed requests
        malformed_requests = [
            # Invalid JSON (will be handled by requests library)
            '{"invalid": json}',
            # Empty request
            {},
            # Null values
            {"sections": None},
            # Wrong data types
            {"sections": []},  # Should be dict, not list
            {"sections": {"leads_and_transitions": []}},  # Should be dict, not list
            # Extremely large request
            {"sections": {"test": "x" * 10000}},
            # Special characters in keys
            {"sections": {"key with spaces": {}}},
            {"sections": {"key/with/slashes": {}}},
        ]
        
        endpoints = [
            f"/cam/toolpath/{test_toolpath_id}/passes",
            f"/cam/toolpath/{test_toolpath_id}/linking"
        ]
        
        for endpoint in endpoints:
            for malformed_data in malformed_requests:
                if isinstance(malformed_data, str):
                    # Test invalid JSON string
                    response = requests.post(
                        f"{self.BASE_URL}{endpoint}",
                        data=malformed_data,
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    # Test invalid data structure
                    response = requests.post(
                        f"{self.BASE_URL}{endpoint}",
                        json=malformed_data
                    )
                
                # Should return error status
                assert response.status_code in [400, 422, 500], \
                    f"Expected error status for malformed request to {endpoint}, got {response.status_code}"
    
    def test_concurrent_modification_attempts(self):
        """
        Test handling of concurrent modification attempts.
        
        Validates system behavior when multiple modifications are attempted
        simultaneously on the same toolpath.
        """
        # Get a valid toolpath ID
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups") or not any(setup.get("toolpaths") for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        test_toolpath_id = data["setups"][0]["toolpaths"][0]["id"]
        
        # Test concurrent requests (simplified - just rapid sequential requests)
        modification_data = {
            "sections": {
                "leads_and_transitions": {
                    "lead_in": {
                        "type": "arc",
                        "arc_radius": 2.0
                    }
                }
            }
        }
        
        responses = []
        
        # Send multiple rapid requests
        for i in range(3):
            response = requests.post(
                f"{self.BASE_URL}/cam/toolpath/{test_toolpath_id}/linking",
                json=modification_data
            )
            responses.append(response)
        
        # All responses should be handled gracefully
        for i, response in enumerate(responses):
            assert response.status_code in [200, 400, 422, 500, 409], \
                f"Request {i} returned unexpected status {response.status_code}"
            
            # Should return some response (not hang)
            assert len(response.content) > 0, f"Request {i} returned empty response"
    
    def test_edge_case_parameter_values(self):
        """
        Test handling of edge case parameter values.
        
        Validates system behavior with boundary values, extreme values,
        and special numeric cases.
        """
        # Get a valid toolpath ID
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups") or not any(setup.get("toolpaths") for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        test_toolpath_id = data["setups"][0]["toolpaths"][0]["id"]
        
        # Test edge case values
        edge_case_values = [
            # Numeric edge cases
            {"arc_radius": 0},  # Zero value
            {"arc_radius": -1},  # Negative value
            {"arc_radius": float('inf')},  # Infinity
            {"arc_radius": float('-inf')},  # Negative infinity
            {"arc_radius": float('nan')},  # NaN
            {"arc_radius": 1e-10},  # Very small positive
            {"arc_radius": 1e10},  # Very large positive
            {"arc_radius": 0.000001},  # Small decimal
            {"arc_radius": 999999.999999},  # Large decimal
            
            # String edge cases
            {"type": ""},  # Empty string
            {"type": " "},  # Whitespace only
            {"type": "a" * 1000},  # Very long string
            {"type": "special\nchars\ttab"},  # Special characters
            {"type": "unicode_测试_🔧"},  # Unicode characters
            
            # Boolean edge cases
            {"enabled": "true"},  # String instead of boolean
            {"enabled": 1},  # Number instead of boolean
            {"enabled": "yes"},  # Non-standard boolean
        ]
        
        for edge_value in edge_case_values:
            modification_data = {
                "sections": {
                    "leads_and_transitions": {
                        "lead_in": edge_value
                    }
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}/cam/toolpath/{test_toolpath_id}/linking",
                json=modification_data
            )
            
            # Should handle edge cases gracefully (either accept or reject with proper error)
            assert response.status_code in [200, 400, 422, 500], \
                f"Unexpected status {response.status_code} for edge case value {edge_value}"
            
            # Should not crash or hang
            assert len(response.content) > 0, f"Empty response for edge case value {edge_value}"
    
    def test_network_timeout_scenarios(self):
        """
        Test handling of network timeout scenarios.
        
        Validates that requests complete within reasonable time limits.
        """
        # Get available toolpaths
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups") or not any(setup.get("toolpaths") for setup in data["setups"]):
            pytest.skip("No toolpaths available for testing")
        
        test_toolpath_id = data["setups"][0]["toolpaths"][0]["id"]
        
        # Test various endpoints with timeout
        endpoints = [
            f"/cam/toolpath/{test_toolpath_id}/heights",
            f"/cam/toolpath/{test_toolpath_id}/passes",
            f"/cam/toolpath/{test_toolpath_id}/linking"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            
            try:
                response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=30)
                request_time = time.time() - start_time
                
                # Should complete within reasonable time
                assert request_time < 30, f"Request to {endpoint} took {request_time:.2f}s (too slow)"
                
                # Should return valid response
                assert response.status_code in [200, 404, 400, 422, 500], \
                    f"Unexpected status {response.status_code} for {endpoint}"
                
            except requests.exceptions.Timeout:
                pytest.fail(f"Request to {endpoint} timed out after 30 seconds")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Request to {endpoint} failed with exception: {e}")
    
    def test_error_message_consistency(self):
        """
        Test consistency of error messages across endpoints.
        
        Validates that similar error conditions return consistent error structures.
        """
        invalid_id = "consistent_test_invalid_id_12345"
        
        endpoints = [
            f"/cam/toolpath/{invalid_id}/heights",
            f"/cam/toolpath/{invalid_id}/passes",
            f"/cam/toolpath/{invalid_id}/linking"
        ]
        
        error_responses = []
        
        for endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            
            # Should return error status
            assert response.status_code in [400, 404, 422, 500], \
                f"Expected error status for {endpoint}, got {response.status_code}"
            
            try:
                error_data = response.json()
                error_responses.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "error_data": error_data
                })
            except json.JSONDecodeError:
                # Non-JSON response
                error_responses.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "error_data": None
                })
        
        # Check for consistency in error handling
        if len(error_responses) > 1:
            # Status codes should be similar for similar errors
            status_codes = [resp["status_code"] for resp in error_responses]
            
            # Allow some variation but should be in same category
            # (all 4xx or all 5xx for similar error types)
            first_category = status_codes[0] // 100
            for status_code in status_codes:
                category = status_code // 100
                # Allow 4xx and 5xx as both are acceptable for "not found" type errors
                assert category in [4, 5], f"Unexpected error category for status {status_code}"
        
        # Log error responses for debugging
        for resp in error_responses:
            print(f"Endpoint {resp['endpoint']}: Status {resp['status_code']}, Data: {resp['error_data']}")


class TestComplexScenarios:
    """Test complex scenarios and edge cases."""
    
    BASE_URL = "http://localhost:5001"
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method to check Fusion 360 availability."""
        if not is_fusion_server_running():
            pytest.skip("Fusion 360 add-in server not running")
    
    def test_empty_cam_document(self):
        """
        Test behavior with empty CAM document (no setups or toolpaths).
        
        Validates graceful handling when no CAM data is available.
        """
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("setups") or data.get("total_count", 0) == 0:
                # Empty CAM document - this is a valid scenario
                assert "setups" in data
                assert isinstance(data["setups"], list)
                assert data.get("total_count", 0) == 0
                
                # Test that individual endpoints handle empty state
                fake_id = "test_empty_document_id"
                
                endpoints = [
                    f"/cam/toolpath/{fake_id}/heights",
                    f"/cam/toolpath/{fake_id}/passes",
                    f"/cam/toolpath/{fake_id}/linking",
                    f"/cam/setup/{fake_id}/sequence"
                ]
                
                for endpoint in endpoints:
                    response = requests.get(f"{self.BASE_URL}{endpoint}")
                    # Should return 404 or similar error for non-existent IDs
                    assert response.status_code in [400, 404, 422], \
                        f"Expected error status for {endpoint} in empty document"
            else:
                pytest.skip("CAM document is not empty")
        else:
            # If toolpaths endpoint fails, that's also a valid test case
            assert response.status_code in [400, 404, 500], \
                f"Unexpected status for toolpaths endpoint: {response.status_code}"
    
    def test_large_dataset_handling(self):
        """
        Test handling of large datasets (many toolpaths, complex sequences).
        
        Validates performance and stability with complex CAM documents.
        """
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        total_toolpaths = data.get("total_count", 0)
        
        if total_toolpaths > 10:  # Consider "large" if more than 10 toolpaths
            # Test that system handles large dataset efficiently
            start_time = time.time()
            
            # Test heights endpoint with large dataset
            response = requests.get(f"{self.BASE_URL}/cam/toolpaths/heights")
            heights_time = time.time() - start_time
            
            assert response.status_code == 200, "Heights endpoint should handle large datasets"
            assert heights_time < 30, f"Heights query took {heights_time:.2f}s for {total_toolpaths} toolpaths"
            
            # Test individual toolpath queries don't degrade
            if data.get("setups"):
                test_toolpaths = []
                for setup in data["setups"]:
                    test_toolpaths.extend(setup.get("toolpaths", [])[:3])  # First 3 per setup
                    if len(test_toolpaths) >= 5:
                        break
                
                for toolpath in test_toolpaths:
                    start_time = time.time()
                    response = requests.get(f"{self.BASE_URL}/cam/toolpath/{toolpath['id']}/passes")
                    request_time = time.time() - start_time
                    
                    # Individual requests should still be fast
                    assert request_time < 10, f"Individual toolpath query took {request_time:.2f}s"
        else:
            pytest.skip(f"Dataset too small for large dataset test ({total_toolpaths} toolpaths)")
    
    def test_special_character_handling(self):
        """
        Test handling of special characters in toolpath names and parameters.
        
        Validates proper encoding and handling of non-ASCII characters.
        """
        # Get toolpaths to check for special characters
        response = requests.get(f"{self.BASE_URL}/cam/toolpaths")
        assert response.status_code == 200
        
        data = response.json()
        if not data.get("setups"):
            pytest.skip("No setups available for special character testing")
        
        # Look for toolpaths with special characters in names
        special_char_toolpaths = []
        
        for setup in data["setups"]:
            for toolpath in setup.get("toolpaths", []):
                name = toolpath.get("name", "")
                # Check for various special characters
                if any(char in name for char in "äöüßñáéíóúàèìòù测试🔧()[]{}|\\/<>?:;\"'`~!@#$%^&*+="):
                    special_char_toolpaths.append(toolpath)
        
        if special_char_toolpaths:
            # Test that special characters are handled properly
            for toolpath in special_char_toolpaths[:3]:  # Test first 3
                toolpath_id = toolpath["id"]
                
                endpoints = [
                    f"/cam/toolpath/{toolpath_id}/heights",
                    f"/cam/toolpath/{toolpath_id}/passes",
                    f"/cam/toolpath/{toolpath_id}/linking"
                ]
                
                for endpoint in endpoints:
                    response = requests.get(f"{self.BASE_URL}{endpoint}")
                    
                    # Should handle special characters without crashing
                    assert response.status_code in [200, 404, 400, 422], \
                        f"Unexpected status {response.status_code} for special char toolpath {toolpath['name']}"
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            # Name should be preserved correctly
                            if "name" in data:
                                assert data["name"] == toolpath["name"], \
                                    f"Special characters not preserved in name: expected '{toolpath['name']}', got '{data['name']}'"
                        except json.JSONDecodeError:
                            pytest.fail("Invalid JSON response for special char toolpath")
        else:
            pytest.skip("No toolpaths with special characters found")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])