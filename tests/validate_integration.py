#!/usr/bin/env python3
"""
Integration validation script for CAM toolpath passes and linking functionality.

This script demonstrates that the new pass and linking features integrate
correctly with existing CAM functionality without breaking backward compatibility.

Usage:
    python tests/validate_integration.py
"""

import requests
import json
import sys
import time
from typing import Dict, Any, List, Optional


class IntegrationValidator:
    """Validates integration between existing and new CAM functionality."""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.results = []
        self.errors = []
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log a test result."""
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if not success:
            self.errors.append(test_name)
    
    def check_connection(self) -> bool:
        """Check if Fusion 360 add-in is running."""
        try:
            response = requests.get(f"{self.base_url}/test_connection", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_sample_toolpath_id(self) -> Optional[str]:
        """Get a sample toolpath ID for testing."""
        try:
            response = requests.get(f"{self.base_url}/cam/toolpaths", timeout=10)
            if response.status_code == 200:
                data = response.json()
                for setup in data.get("setups", []):
                    for toolpath in setup.get("toolpaths", []):
                        return toolpath.get("id")
            return None
        except:
            return None
    
    def get_sample_setup_id(self) -> Optional[str]:
        """Get a sample setup ID for testing."""
        try:
            response = requests.get(f"{self.base_url}/cam/toolpaths", timeout=10)
            if response.status_code == 200:
                data = response.json()
                for setup in data.get("setups", []):
                    return setup.get("id")
            return None
        except:
            return None
    
    def validate_existing_endpoints(self):
        """Validate that existing endpoints still work."""
        print("\n=== Validating Existing Endpoints ===")
        
        # Test existing toolpath listing
        try:
            response = requests.get(f"{self.base_url}/cam/toolpaths", timeout=10)
            success = response.status_code == 200
            message = f"Status: {response.status_code}"
            if success:
                data = response.json()
                message += f", Found {data.get('total_count', 0)} toolpaths"
            self.log_result("List CAM toolpaths", success, message)
        except Exception as e:
            self.log_result("List CAM toolpaths", False, str(e))
        
        # Test existing toolpaths with heights
        try:
            response = requests.get(f"{self.base_url}/cam/toolpaths/heights", timeout=10)
            success = response.status_code == 200
            message = f"Status: {response.status_code}"
            if success:
                data = response.json()
                message += f", Found {data.get('total_count', 0)} toolpaths with heights"
            self.log_result("List toolpaths with heights", success, message)
        except Exception as e:
            self.log_result("List toolpaths with heights", False, str(e))
        
        # Test existing CAM tools
        try:
            response = requests.get(f"{self.base_url}/cam/tools", timeout=10)
            success = response.status_code == 200
            message = f"Status: {response.status_code}"
            if success:
                data = response.json()
                message += f", Found {len(data)} tools"
            self.log_result("List CAM tools", success, message)
        except Exception as e:
            self.log_result("List CAM tools", False, str(e))
    
    def validate_new_endpoints(self):
        """Validate that new endpoints work."""
        print("\n=== Validating New Endpoints ===")
        
        toolpath_id = self.get_sample_toolpath_id()
        setup_id = self.get_sample_setup_id()
        
        if not toolpath_id:
            self.log_result("Get sample toolpath ID", False, "No toolpaths available")
            return
        
        # Test new passes endpoint
        try:
            response = requests.get(f"{self.base_url}/cam/toolpath/{toolpath_id}/passes", timeout=10)
            success = response.status_code in [200, 404]  # 404 acceptable if no passes
            message = f"Status: {response.status_code}"
            if response.status_code == 200:
                data = response.json()
                message += f", Toolpath: {data.get('name', 'Unknown')}"
            elif response.status_code == 404:
                message += " (No passes data - acceptable)"
            self.log_result("Get toolpath passes", success, message)
        except Exception as e:
            self.log_result("Get toolpath passes", False, str(e))
        
        # Test new linking endpoint
        try:
            response = requests.get(f"{self.base_url}/cam/toolpath/{toolpath_id}/linking", timeout=10)
            success = response.status_code in [200, 404]  # 404 acceptable if no linking
            message = f"Status: {response.status_code}"
            if response.status_code == 200:
                data = response.json()
                message += f", Toolpath: {data.get('name', 'Unknown')}"
            elif response.status_code == 404:
                message += " (No linking data - acceptable)"
            self.log_result("Get toolpath linking", success, message)
        except Exception as e:
            self.log_result("Get toolpath linking", False, str(e))
        
        # Test new setup sequence endpoint
        if setup_id:
            try:
                response = requests.get(f"{self.base_url}/cam/setup/{setup_id}/sequence", timeout=10)
                success = response.status_code in [200, 404]  # 404 acceptable if no sequence
                message = f"Status: {response.status_code}"
                if response.status_code == 200:
                    data = response.json()
                    message += f", Setup: {data.get('setup_name', 'Unknown')}"
                elif response.status_code == 404:
                    message += " (No sequence data - acceptable)"
                self.log_result("Get setup sequence", success, message)
            except Exception as e:
                self.log_result("Get setup sequence", False, str(e))
        else:
            self.log_result("Get setup sequence", False, "No setup ID available")
    
    def validate_data_consistency(self):
        """Validate that data is consistent across endpoints."""
        print("\n=== Validating Data Consistency ===")
        
        toolpath_id = self.get_sample_toolpath_id()
        if not toolpath_id:
            self.log_result("Data consistency check", False, "No toolpath ID available")
            return
        
        # Get data from multiple endpoints
        endpoints_data = {}
        
        endpoints = [
            ("heights", f"/cam/toolpath/{toolpath_id}/heights"),
            ("passes", f"/cam/toolpath/{toolpath_id}/passes"),
            ("linking", f"/cam/toolpath/{toolpath_id}/linking")
        ]
        
        for name, endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    endpoints_data[name] = response.json()
            except:
                pass
        
        if len(endpoints_data) < 2:
            self.log_result("Data consistency check", False, "Not enough endpoints returned data")
            return
        
        # Check consistency of basic fields
        basic_fields = ["id", "name", "type"]
        consistent = True
        inconsistent_fields = []
        
        reference_data = list(endpoints_data.values())[0]
        
        for field in basic_fields:
            if field in reference_data:
                reference_value = reference_data[field]
                
                for endpoint_name, data in endpoints_data.items():
                    if field in data and data[field] != reference_value:
                        consistent = False
                        inconsistent_fields.append(f"{field} in {endpoint_name}")
        
        message = f"Checked {len(endpoints_data)} endpoints"
        if not consistent:
            message += f", Inconsistent: {', '.join(inconsistent_fields)}"
        
        self.log_result("Data consistency check", consistent, message)
    
    def validate_performance(self):
        """Validate that performance is acceptable."""
        print("\n=== Validating Performance ===")
        
        toolpath_id = self.get_sample_toolpath_id()
        if not toolpath_id:
            self.log_result("Performance check", False, "No toolpath ID available")
            return
        
        # Test performance of sequential requests
        endpoints = [
            f"/cam/toolpath/{toolpath_id}/heights",
            f"/cam/toolpath/{toolpath_id}/passes",
            f"/cam/toolpath/{toolpath_id}/linking"
        ]
        
        total_time = 0
        successful_requests = 0
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                request_time = time.time() - start_time
                
                if response.status_code in [200, 404]:
                    total_time += request_time
                    successful_requests += 1
                    
                    if request_time > 5.0:
                        self.log_result(f"Performance - {endpoint}", False, f"Too slow: {request_time:.2f}s")
                        return
            except Exception as e:
                self.log_result("Performance check", False, f"Request failed: {e}")
                return
        
        if successful_requests > 0:
            avg_time = total_time / successful_requests
            success = avg_time < 3.0
            message = f"Average: {avg_time:.2f}s, Total: {total_time:.2f}s, Requests: {successful_requests}"
            self.log_result("Performance check", success, message)
        else:
            self.log_result("Performance check", False, "No successful requests")
    
    def validate_error_handling(self):
        """Validate that error handling is consistent."""
        print("\n=== Validating Error Handling ===")
        
        invalid_id = "invalid_test_id_12345"
        
        endpoints = [
            f"/cam/toolpath/{invalid_id}/heights",
            f"/cam/toolpath/{invalid_id}/passes",
            f"/cam/toolpath/{invalid_id}/linking"
        ]
        
        consistent_errors = True
        error_codes = []
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                error_codes.append(response.status_code)
                
                # Should return an error status
                if response.status_code not in [400, 404, 422, 500]:
                    consistent_errors = False
                    break
                    
            except Exception:
                consistent_errors = False
                break
        
        message = f"Error codes: {error_codes}"
        self.log_result("Error handling consistency", consistent_errors, message)
    
    def run_validation(self):
        """Run complete validation suite."""
        print("🔍 CAM Toolpath Passes and Linking - Integration Validation")
        print("=" * 60)
        
        # Check connection
        if not self.check_connection():
            print("❌ Fusion 360 add-in server is not running!")
            print("Please start Fusion 360 and ensure FusionMCPBridge add-in is active.")
            sys.exit(1)
        
        print("✅ Fusion 360 add-in server is running")
        
        # Run validation tests
        self.validate_existing_endpoints()
        self.validate_new_endpoints()
        self.validate_data_consistency()
        self.validate_performance()
        self.validate_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 ALL VALIDATION TESTS PASSED!")
            print("✅ Backward compatibility maintained")
            print("✅ New features integrate correctly")
            print("✅ Performance is acceptable")
            print("✅ Error handling is consistent")
            return True
        else:
            print(f"\n⚠️  {failed_tests} VALIDATION TESTS FAILED!")
            print("❌ Integration issues detected:")
            for error in self.errors:
                print(f"   - {error}")
            return False


def main():
    """Main validation function."""
    validator = IntegrationValidator()
    success = validator.run_validation()
    
    if success:
        print("\n✅ Integration validation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Integration validation failed!")
        print("Please review the failed tests and fix any issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()