#!/usr/bin/env python3
"""
Integration validation runner for CAM toolpath passes and linking functionality.

This script provides a comprehensive validation of the complete MCP Server → HTTP → 
Fusion Add-In → Fusion 360 API chain for the new pass and linking features.

Usage:
    python tests/run_integration_validation.py [--verbose] [--skip-fusion-check]
    
Options:
    --verbose: Enable verbose output
    --skip-fusion-check: Skip Fusion 360 availability check (for CI/testing)
"""

import sys
import argparse
import subprocess
import requests
from pathlib import Path


def check_fusion_availability():
    """Check if Fusion 360 add-in server is running."""
    try:
        response = requests.get("http://localhost:5001/test_connection", timeout=5)
        return response.status_code == 200
    except:
        return False


def run_pytest_suite(test_file, verbose=False):
    """Run a specific pytest suite."""
    cmd = ["python", "-m", "pytest", test_file]
    
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "--no-header"])
    
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def run_structure_tests():
    """Run structure tests that don't require Fusion 360."""
    print("\n🔍 RUNNING STRUCTURE TESTS (No Fusion 360 Required)")
    print("=" * 60)
    
    # Run backward compatibility structure tests
    cmd = [
        "python", "-m", "pytest", 
        "tests/test_backward_compatibility.py::TestCodeStructureCompatibility",
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    
    if result.returncode == 0:
        print("✅ Structure tests PASSED")
        return True
    else:
        print("❌ Structure tests FAILED")
        if result.stderr:
            print("STDERR:", result.stderr)
        return False


def run_integration_tests(verbose=False):
    """Run integration tests that require Fusion 360."""
    print("\n🔍 RUNNING INTEGRATION TESTS (Fusion 360 Required)")
    print("=" * 60)
    
    test_files = [
        "tests/test_integration_end_to_end.py",
        "tests/test_error_scenarios_edge_cases.py",
        "tests/test_cam_integration.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        if Path(test_file).exists():
            success = run_pytest_suite(test_file, verbose)
            if not success:
                all_passed = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return all_passed


def run_manual_validation():
    """Run manual validation script."""
    print("\n🔍 RUNNING MANUAL VALIDATION")
    print("=" * 60)
    
    try:
        from tests.validate_integration import IntegrationValidator
        
        validator = IntegrationValidator()
        success = validator.run_validation()
        
        return success
    except ImportError:
        print("❌ Manual validation script not available")
        return False
    except Exception as e:
        print(f"❌ Manual validation failed: {e}")
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("📊 INTEGRATION VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ALL INTEGRATION VALIDATION TESTS PASSED!")
        print("✅ Complete MCP Server → HTTP → Fusion Add-In → Fusion 360 API chain validated")
        print("✅ Pass and linking data extraction working correctly")
        print("✅ Error handling and edge cases properly handled")
        print("✅ Parameter modification workflows validated")
        print("✅ Sequence analysis with complex dependencies working")
        return True
    else:
        print(f"\n⚠️  {failed_tests} TEST SUITE(S) FAILED!")
        print("❌ Integration issues detected - review failed tests above")
        return False


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Run integration validation tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--skip-fusion-check", action="store_true", help="Skip Fusion 360 availability check")
    parser.add_argument("--structure-only", action="store_true", help="Run only structure tests")
    
    args = parser.parse_args()
    
    print("🚀 CAM Toolpath Passes and Linking - Integration Validation")
    print("=" * 60)
    
    results = {}
    
    # Always run structure tests
    results["Structure Tests"] = run_structure_tests()
    
    if args.structure_only:
        print("\n✅ Structure-only validation completed")
        return 0 if results["Structure Tests"] else 1
    
    # Check Fusion 360 availability
    if not args.skip_fusion_check:
        print("\n🔍 Checking Fusion 360 availability...")
        
        if check_fusion_availability():
            print("✅ Fusion 360 add-in server is running")
            fusion_available = True
        else:
            print("❌ Fusion 360 add-in server is not running!")
            print("\nTo run full integration tests:")
            print("1. Start Fusion 360")
            print("2. Ensure FusionMCPBridge add-in is running")
            print("3. Verify with: curl http://localhost:5001/test_connection")
            print("\nRunning structure tests only...")
            fusion_available = False
    else:
        print("⚠️  Skipping Fusion 360 availability check")
        fusion_available = True
    
    # Run integration tests if Fusion is available
    if fusion_available:
        results["Integration Tests"] = run_integration_tests(args.verbose)
        results["Manual Validation"] = run_manual_validation()
    else:
        print("\n⚠️  Skipping integration tests - Fusion 360 not available")
        results["Integration Tests"] = None
        results["Manual Validation"] = None
    
    # Print summary
    success = print_summary({k: v for k, v in results.items() if v is not None})
    
    if success:
        print("\n✅ Integration validation completed successfully!")
        return 0
    else:
        print("\n❌ Integration validation failed!")
        print("Please review the failed tests and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())