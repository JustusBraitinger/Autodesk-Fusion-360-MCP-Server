#!/usr/bin/env python3
"""
Manual test script for backward compatibility verification.

This script can be run when Fusion 360 is running to verify that
existing endpoints continue to work correctly.

Usage:
    python tests/manual_compatibility_test.py
"""

import requests
import json
import sys


def test_endpoint(url: str, description: str) -> bool:
    """Test a single endpoint and return success status."""
    print(f"Testing {description}...")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response: Valid JSON ({len(json.dumps(data))} chars)")
                return True
            except json.JSONDecodeError:
                print("  Response: Invalid JSON")
                return False
        else:
            print(f"  Response: {response.text[:100]}...")
            return False
            
    except requests.RequestException as e:
        print(f"  Error: {e}")
        return False


def main():
    """Run manual compatibility tests."""
    print("=== Fusion 360 MCP Backward Compatibility Test ===\n")
    
    base_url = "http://localhost:5001"
    
    # Test connection first
    print("Checking Fusion 360 Add-In connection...")
    if not test_endpoint(f"{base_url}/test_connection", "Connection test"):
        print("\n❌ Fusion 360 Add-In is not running!")
        print("Please start Fusion 360 and ensure the FusionMCPBridge add-in is running.")
        sys.exit(1)
    
    print("✅ Fusion 360 Add-In is running\n")
    
    # Test existing endpoints
    tests = [
        (f"{base_url}/cam/toolpaths", "List all CAM toolpaths"),
        (f"{base_url}/cam/toolpaths/heights", "List toolpaths with heights"),
        (f"{base_url}/cam/tools", "List CAM tools"),
    ]
    
    results = []
    
    for url, description in tests:
        success = test_endpoint(url, description)
        results.append((description, success))
        print()
    
    # Test individual toolpath endpoints if we have toolpaths
    print("Getting toolpath ID for individual endpoint tests...")
    try:
        response = requests.get(f"{base_url}/cam/toolpaths", timeout=10)
        if response.status_code == 200:
            data = response.json()
            toolpath_id = None
            
            # Find first available toolpath ID
            for setup in data.get("setups", []):
                for toolpath in setup.get("toolpaths", []):
                    toolpath_id = toolpath.get("id")
                    break
                if toolpath_id:
                    break
            
            if toolpath_id:
                print(f"Found toolpath ID: {toolpath_id}")
                
                # Test individual endpoints
                individual_tests = [
                    (f"{base_url}/cam/toolpath/{toolpath_id}/heights", "Individual toolpath heights"),
                    (f"{base_url}/cam/toolpath/{toolpath_id}/passes", "Individual toolpath passes (new)"),
                    (f"{base_url}/cam/toolpath/{toolpath_id}/linking", "Individual toolpath linking (new)"),
                ]
                
                for url, description in individual_tests:
                    success = test_endpoint(url, description)
                    results.append((description, success))
                    print()
            else:
                print("No toolpaths found - skipping individual endpoint tests")
                print()
        
    except Exception as e:
        print(f"Error getting toolpath ID: {e}")
        print()
    
    # Test setup sequence endpoint if we have setups
    print("Getting setup ID for sequence endpoint test...")
    try:
        response = requests.get(f"{base_url}/cam/toolpaths", timeout=10)
        if response.status_code == 200:
            data = response.json()
            setup_id = None
            
            # Find first available setup ID
            for setup in data.get("setups", []):
                setup_id = setup.get("id")
                break
            
            if setup_id:
                print(f"Found setup ID: {setup_id}")
                success = test_endpoint(f"{base_url}/cam/setup/{setup_id}/sequence", "Setup sequence analysis (new)")
                results.append(("Setup sequence analysis (new)", success))
                print()
            else:
                print("No setups found - skipping setup sequence test")
                print()
        
    except Exception as e:
        print(f"Error getting setup ID: {e}")
        print()
    
    # Summary
    print("=== Test Results Summary ===")
    passed = 0
    failed = 0
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All backward compatibility tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} tests failed - backward compatibility issues detected!")
        sys.exit(1)


if __name__ == "__main__":
    main()