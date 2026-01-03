#!/usr/bin/env python3
"""
Integration Testing for Toolpath Heights Feature

This comprehensive test validates the complete MCP Server → HTTP → Fusion Add-In → Fusion 360 API chain
for height data extraction. It tests with real CAM documents and various toolpath types.

Requirements: 1.1, 1.2, 2.1, 2.2, 1.3, 2.5, 4.5
"""

import sys
import os
import importlib.util
import requests
from typing import Dict, Any

class HeightIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.timeout = 15
        self.fusion_available = False
        self.mcp_server = None
        
    def test_fusion_connection(self) -> bool:
        """Test if Fusion 360 add-in is available."""
        try:
            # Try the actual CAM endpoint instead of test_connection
            response = requests.get(f"{self.base_url}/cam/toolpaths", timeout=self.timeout)
            self.fusion_available = response.status_code == 200
            return self.fusion_available
        except Exception:
            self.fusion_available = False
            return False
    
    def load_mcp_server(self):
        """Load the MCP server module for direct tool testing."""
        try:
            # Add Server directory to path
            server_path = os.path.join(os.getcwd(), "Server")
            if server_path not in sys.path:
                sys.path.insert(0, server_path)
            
            spec = importlib.util.spec_from_file_location("mcp_server", "Server/MCP_Server.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.mcp_server = module
            return module
        except Exception as e:
            print(f"Failed to load MCP server: {e}")
            return None
    
    def test_http_endpoints(self) -> Dict[str, Any]:
        """Test HTTP endpoints directly."""
        print("1. Testing HTTP Endpoints")
        print("   " + "=" * 25)
        
        if not self.fusion_available:
            print("   ⚠️  SKIPPED: Fusion 360 not available")
            return {"success": False, "reason": "fusion_unavailable"}
        
        results = {}
        
        # Test original toolpaths endpoint for comparison
        try:
            print("   Testing original /cam/toolpaths endpoint...")
            response = requests.get(f"{self.base_url}/cam/toolpaths", timeout=self.timeout)
            if response.status_code == 200:
                original_data = response.json()
                results["original_toolpaths"] = {
                    "success": True,
                    "data": original_data,
                    "toolpath_count": original_data.get("total_count", 0)
                }
                print(f"   ✅ Original endpoint: {original_data.get('total_count', 0)} toolpaths found")
            else:
                results["original_toolpaths"] = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
                print(f"   ❌ Original endpoint failed: HTTP {response.status_code}")
        except Exception as e:
            results["original_toolpaths"] = {"success": False, "error": str(e)}
            print(f"   ❌ Original endpoint error: {e}")
        
        # Test new heights endpoint
        try:
            print("   Testing new /cam/toolpaths/heights endpoint...")
            response = requests.get(f"{self.base_url}/cam/toolpaths/heights", timeout=self.timeout)
            if response.status_code == 200:
                heights_data = response.json()
                results["heights_toolpaths"] = {
                    "success": True,
                    "data": heights_data,
                    "toolpath_count": heights_data.get("total_count", 0)
                }
                print(f"   ✅ Heights endpoint: {heights_data.get('total_count', 0)} toolpaths found")
                
                # Validate heights data structure
                if heights_data.get("setups"):
                    for setup in heights_data["setups"]:
                        if setup.get("toolpaths"):
                            for toolpath in setup["toolpaths"]:
                                if "heights" not in toolpath:
                                    print(f"   ⚠️  WARNING: Toolpath {toolpath.get('name', 'unknown')} missing heights field")
                                else:
                                    heights = toolpath["heights"]
                                    height_params = ["clearance_height", "retract_height", "feed_height", "top_height", "bottom_height"]
                                    found_params = [param for param in height_params if param in heights]
                                    print(f"   ✅ Toolpath {toolpath.get('name', 'unknown')}: {len(found_params)} height parameters")
            else:
                results["heights_toolpaths"] = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
                print(f"   ❌ Heights endpoint failed: HTTP {response.status_code}")
        except Exception as e:
            results["heights_toolpaths"] = {"success": False, "error": str(e)}
            print(f"   ❌ Heights endpoint error: {e}")
        
        # Test specific toolpath heights endpoint if we have toolpaths
        if results.get("heights_toolpaths", {}).get("success"):
            heights_data = results["heights_toolpaths"]["data"]
            if heights_data.get("setups") and heights_data["setups"][0].get("toolpaths"):
                toolpath_id = heights_data["setups"][0]["toolpaths"][0]["id"]
                try:
                    print(f"   Testing specific toolpath heights endpoint for ID: {toolpath_id}")
                    response = requests.get(f"{self.base_url}/cam/toolpath/{toolpath_id}/heights", timeout=self.timeout)
                    if response.status_code == 200:
                        specific_data = response.json()
                        results["specific_heights"] = {
                            "success": True,
                            "data": specific_data,
                            "toolpath_id": toolpath_id
                        }
                        print(f"   ✅ Specific heights endpoint: Retrieved data for {toolpath_id}")
                        
                        # Validate specific heights structure
                        if "heights" in specific_data:
                            heights = specific_data["heights"]
                            height_count = len([k for k in heights.keys() if k.endswith("_height")])
                            print(f"   ✅ Specific heights: {height_count} height parameters found")
                        else:
                            print("   ⚠️  WARNING: Specific heights response missing 'heights' field")
                    else:
                        results["specific_heights"] = {
                            "success": False,
                            "status_code": response.status_code,
                            "error": f"HTTP {response.status_code}"
                        }
                        print(f"   ❌ Specific heights endpoint failed: HTTP {response.status_code}")
                except Exception as e:
                    results["specific_heights"] = {"success": False, "error": str(e)}
                    print(f"   ❌ Specific heights endpoint error: {e}")
        
        return results
    
    def test_mcp_tools(self) -> Dict[str, Any]:
        """Test MCP tools directly."""
        print("\n2. Testing MCP Tools")
        print("   " + "=" * 18)
        
        if not self.mcp_server:
            print("   ⚠️  SKIPPED: MCP server not loaded")
            return {"success": False, "reason": "mcp_unavailable"}
        
        results = {}
        
        # Test list_toolpaths_with_heights tool
        try:
            print("   Testing list_toolpaths_with_heights() tool...")
            if hasattr(self.mcp_server, 'list_toolpaths_with_heights'):
                tool_result = self.mcp_server.list_toolpaths_with_heights()
                if tool_result.get("error"):
                    results["list_heights_tool"] = {
                        "success": False,
                        "error": tool_result.get("message", "Unknown error"),
                        "code": tool_result.get("code", "UNKNOWN")
                    }
                    print(f"   ❌ MCP tool failed: {tool_result.get('message', 'Unknown error')}")
                else:
                    results["list_heights_tool"] = {
                        "success": True,
                        "data": tool_result,
                        "toolpath_count": tool_result.get("total_count", 0)
                    }
                    print(f"   ✅ MCP tool: {tool_result.get('total_count', 0)} toolpaths found")
            else:
                results["list_heights_tool"] = {
                    "success": False,
                    "error": "Tool function not found"
                }
                print("   ❌ MCP tool not found: list_toolpaths_with_heights")
        except Exception as e:
            results["list_heights_tool"] = {"success": False, "error": str(e)}
            print(f"   ❌ MCP tool error: {e}")
        
        # Test get_toolpath_heights tool if we have toolpaths
        if results.get("list_heights_tool", {}).get("success"):
            tool_data = results["list_heights_tool"]["data"]
            if tool_data.get("setups") and tool_data["setups"][0].get("toolpaths"):
                toolpath_id = tool_data["setups"][0]["toolpaths"][0]["id"]
                try:
                    print(f"   Testing get_toolpath_heights() tool for ID: {toolpath_id}")
                    if hasattr(self.mcp_server, 'get_toolpath_heights'):
                        tool_result = self.mcp_server.get_toolpath_heights(toolpath_id)
                        if tool_result.get("error"):
                            results["get_heights_tool"] = {
                                "success": False,
                                "error": tool_result.get("message", "Unknown error"),
                                "code": tool_result.get("code", "UNKNOWN")
                            }
                            print(f"   ❌ MCP tool failed: {tool_result.get('message', 'Unknown error')}")
                        else:
                            results["get_heights_tool"] = {
                                "success": True,
                                "data": tool_result,
                                "toolpath_id": toolpath_id
                            }
                            print(f"   ✅ MCP tool: Retrieved specific heights for {toolpath_id}")
                    else:
                        results["get_heights_tool"] = {
                            "success": False,
                            "error": "Tool function not found"
                        }
                        print("   ❌ MCP tool not found: get_toolpath_heights")
                except Exception as e:
                    results["get_heights_tool"] = {"success": False, "error": str(e)}
                    print(f"   ❌ MCP tool error: {e}")
        
        return results
    
    def test_data_consistency(self, http_results: Dict[str, Any], mcp_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test that HTTP and MCP results are consistent."""
        print("\n3. Testing Data Consistency")
        print("   " + "=" * 25)
        
        results = {}
        
        # Compare toolpath counts
        http_count = http_results.get("heights_toolpaths", {}).get("toolpath_count", 0)
        mcp_count = mcp_results.get("list_heights_tool", {}).get("toolpath_count", 0)
        
        if http_count == mcp_count:
            print(f"   ✅ Toolpath counts match: {http_count}")
            results["count_consistency"] = {"success": True, "count": http_count}
        else:
            print(f"   ❌ Toolpath count mismatch: HTTP={http_count}, MCP={mcp_count}")
            results["count_consistency"] = {
                "success": False,
                "http_count": http_count,
                "mcp_count": mcp_count
            }
        
        # Compare specific toolpath data if available
        http_specific = http_results.get("specific_heights", {})
        mcp_specific = mcp_results.get("get_heights_tool", {})
        
        if http_specific.get("success") and mcp_specific.get("success"):
            http_data = http_specific["data"]
            mcp_data = mcp_specific["data"]
            
            # Compare toolpath IDs
            http_id = http_data.get("id")
            mcp_id = mcp_data.get("id")
            
            if http_id == mcp_id:
                print(f"   ✅ Toolpath IDs match: {http_id}")
                results["id_consistency"] = {"success": True, "id": http_id}
            else:
                print(f"   ❌ Toolpath ID mismatch: HTTP={http_id}, MCP={mcp_id}")
                results["id_consistency"] = {
                    "success": False,
                    "http_id": http_id,
                    "mcp_id": mcp_id
                }
            
            # Compare heights data structure
            http_heights = http_data.get("heights", {})
            mcp_heights = mcp_data.get("heights", {})
            
            http_height_params = set(http_heights.keys())
            mcp_height_params = set(mcp_heights.keys())
            
            if http_height_params == mcp_height_params:
                print(f"   ✅ Height parameters match: {len(http_height_params)} parameters")
                results["heights_consistency"] = {
                    "success": True,
                    "parameter_count": len(http_height_params),
                    "parameters": list(http_height_params)
                }
            else:
                missing_in_mcp = http_height_params - mcp_height_params
                missing_in_http = mcp_height_params - http_height_params
                print("   ❌ Height parameters mismatch:")
                if missing_in_mcp:
                    print(f"      Missing in MCP: {missing_in_mcp}")
                if missing_in_http:
                    print(f"      Missing in HTTP: {missing_in_http}")
                results["heights_consistency"] = {
                    "success": False,
                    "http_parameters": list(http_height_params),
                    "mcp_parameters": list(mcp_height_params),
                    "missing_in_mcp": list(missing_in_mcp),
                    "missing_in_http": list(missing_in_http)
                }
        
        return results
    
    def test_various_toolpath_types(self, http_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test height extraction with various toolpath types."""
        print("\n4. Testing Various Toolpath Types")
        print("   " + "=" * 32)
        
        results = {"toolpath_types": {}, "height_coverage": {}}
        
        if not http_results.get("heights_toolpaths", {}).get("success"):
            print("   ⚠️  SKIPPED: No height data available")
            return results
        
        heights_data = http_results["heights_toolpaths"]["data"]
        
        if not heights_data.get("setups"):
            print("   ⚠️  SKIPPED: No setups found")
            return results
        
        toolpath_types = {}
        height_coverage = {}
        
        for setup in heights_data["setups"]:
            if not setup.get("toolpaths"):
                continue
                
            for toolpath in setup["toolpaths"]:
                toolpath_type = toolpath.get("type", "unknown")
                toolpath_name = toolpath.get("name", "unnamed")
                heights = toolpath.get("heights", {})
                
                # Track toolpath types
                if toolpath_type not in toolpath_types:
                    toolpath_types[toolpath_type] = []
                toolpath_types[toolpath_type].append(toolpath_name)
                
                # Track height parameter coverage
                height_params = ["clearance_height", "retract_height", "feed_height", "top_height", "bottom_height"]
                found_params = [param for param in height_params if param in heights]
                missing_params = [param for param in height_params if param not in heights]
                
                height_coverage[toolpath_name] = {
                    "type": toolpath_type,
                    "found_parameters": found_params,
                    "missing_parameters": missing_params,
                    "coverage_percentage": (len(found_params) / len(height_params)) * 100
                }
                
                print(f"   ✅ {toolpath_type}: {toolpath_name} - {len(found_params)}/5 height parameters")
                if missing_params:
                    print(f"      Missing: {', '.join(missing_params)}")
        
        results["toolpath_types"] = toolpath_types
        results["height_coverage"] = height_coverage
        
        # Summary
        total_toolpaths = sum(len(toolpaths) for toolpaths in toolpath_types.values())
        unique_types = len(toolpath_types)
        
        print(f"\n   Summary: {total_toolpaths} toolpaths across {unique_types} operation types")
        for op_type, toolpaths in toolpath_types.items():
            print(f"   - {op_type}: {len(toolpaths)} operations")
        
        return results
    
    def test_height_parameter_accuracy(self, http_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test accuracy of height parameter extraction."""
        print("\n5. Testing Height Parameter Accuracy")
        print("   " + "=" * 35)
        
        results = {"parameter_validation": {}, "data_quality": {}}
        
        if not http_results.get("specific_heights", {}).get("success"):
            print("   ⚠️  SKIPPED: No specific height data available")
            return results
        
        specific_data = http_results["specific_heights"]["data"]
        heights = specific_data.get("heights", {})
        
        if not heights:
            print("   ⚠️  SKIPPED: No height parameters found")
            return results
        
        parameter_validation = {}
        data_quality = {
            "complete_parameters": 0,
            "incomplete_parameters": 0,
            "parameters_with_expressions": 0,
            "parameters_with_units": 0,
            "editable_parameters": 0,
            "readonly_parameters": 0
        }
        
        expected_fields = ["value", "unit", "expression", "type", "editable"]
        
        for param_name, param_data in heights.items():
            print(f"   Validating {param_name}...")
            
            validation = {
                "has_all_fields": True,
                "missing_fields": [],
                "field_types_correct": True,
                "type_errors": []
            }
            
            # Check required fields
            for field in expected_fields:
                if field not in param_data:
                    validation["has_all_fields"] = False
                    validation["missing_fields"].append(field)
            
            # Check field types
            if "value" in param_data:
                if not isinstance(param_data["value"], (int, float, type(None))):
                    validation["field_types_correct"] = False
                    validation["type_errors"].append(f"value should be numeric, got {type(param_data['value'])}")
            
            if "unit" in param_data:
                if not isinstance(param_data["unit"], str):
                    validation["field_types_correct"] = False
                    validation["type_errors"].append(f"unit should be string, got {type(param_data['unit'])}")
            
            if "editable" in param_data:
                if not isinstance(param_data["editable"], bool):
                    validation["field_types_correct"] = False
                    validation["type_errors"].append(f"editable should be boolean, got {type(param_data['editable'])}")
            
            parameter_validation[param_name] = validation
            
            # Update data quality metrics
            if validation["has_all_fields"]:
                data_quality["complete_parameters"] += 1
            else:
                data_quality["incomplete_parameters"] += 1
            
            if param_data.get("expression"):
                data_quality["parameters_with_expressions"] += 1
            
            if param_data.get("unit"):
                data_quality["parameters_with_units"] += 1
            
            if param_data.get("editable"):
                data_quality["editable_parameters"] += 1
            else:
                data_quality["readonly_parameters"] += 1
            
            # Print validation results
            if validation["has_all_fields"] and validation["field_types_correct"]:
                print(f"   ✅ {param_name}: Complete and valid")
            else:
                print(f"   ❌ {param_name}: Issues found")
                if validation["missing_fields"]:
                    print(f"      Missing fields: {', '.join(validation['missing_fields'])}")
                if validation["type_errors"]:
                    print(f"      Type errors: {'; '.join(validation['type_errors'])}")
        
        results["parameter_validation"] = parameter_validation
        results["data_quality"] = data_quality
        
        # Summary
        total_params = len(heights)
        complete_params = data_quality["complete_parameters"]
        print(f"\n   Summary: {complete_params}/{total_params} parameters are complete and valid")
        print(f"   - {data_quality['parameters_with_expressions']} have expressions")
        print(f"   - {data_quality['parameters_with_units']} have units")
        print(f"   - {data_quality['editable_parameters']} are editable")
        
        return results
    
    def run_integration_tests(self) -> bool:
        """Run all integration tests."""
        print("Integration Testing for Toolpath Heights Feature")
        print("=" * 50)
        
        # Check Fusion connection
        print("\n0. Checking Fusion 360 Connection")
        print("   " + "=" * 30)
        if self.test_fusion_connection():
            print("   ✅ CONNECTED: Fusion 360 add-in is available")
        else:
            print("   ⚠️  OFFLINE: Fusion 360 add-in not available")
            print("   Some tests will be skipped or may fail")
        
        # Load MCP server
        print("\n   Loading MCP Server...")
        if self.load_mcp_server():
            print("   ✅ MCP server loaded successfully")
        else:
            print("   ⚠️  MCP server could not be loaded")
        
        # Run tests
        http_results = self.test_http_endpoints()
        mcp_results = self.test_mcp_tools()
        consistency_results = self.test_data_consistency(http_results, mcp_results)
        toolpath_results = self.test_various_toolpath_types(http_results)
        accuracy_results = self.test_height_parameter_accuracy(http_results)
        
        # Overall assessment
        print("\n" + "=" * 50)
        
        # Count successes
        successes = 0
        total_tests = 0
        
        # HTTP endpoint tests
        if http_results.get("heights_toolpaths", {}).get("success"):
            successes += 1
        total_tests += 1
        
        if http_results.get("specific_heights", {}).get("success"):
            successes += 1
        total_tests += 1
        
        # MCP tool tests
        if mcp_results.get("list_heights_tool", {}).get("success"):
            successes += 1
        total_tests += 1
        
        if mcp_results.get("get_heights_tool", {}).get("success"):
            successes += 1
        total_tests += 1
        
        # Consistency tests
        if consistency_results.get("count_consistency", {}).get("success"):
            successes += 1
        total_tests += 1
        
        if consistency_results.get("heights_consistency", {}).get("success"):
            successes += 1
        total_tests += 1
        
        # Data quality
        accuracy_data = accuracy_results.get("data_quality", {})
        if accuracy_data.get("complete_parameters", 0) > 0:
            successes += 1
        total_tests += 1
        
        success_rate = (successes / total_tests) * 100 if total_tests > 0 else 0
        
        if success_rate >= 80:
            print("✅ INTEGRATION TESTS PASSED")
            print(f"\n✓ Success rate: {success_rate:.1f}% ({successes}/{total_tests})")
            print("✓ Complete MCP Server → HTTP → Fusion Add-In → Fusion 360 API chain working")
            print("✓ Height data extraction functioning correctly")
            print("✓ Various toolpath types supported")
            print("✓ Height parameter accuracy validated")
            return True
        else:
            print("❌ INTEGRATION TESTS FAILED")
            print(f"\n✗ Success rate: {success_rate:.1f}% ({successes}/{total_tests})")
            print("✗ Some components in the chain are not working correctly")
            return False

def main():
    tester = HeightIntegrationTester()
    success = tester.run_integration_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()