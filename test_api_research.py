#!/usr/bin/env python3
"""
Test script to call the API research endpoints.

This script calls both the WCS API and Model ID research endpoints 
and saves the results for analysis.
"""

import requests
import json
import sys
from datetime import datetime


def test_api_research():
    """Test both API research endpoints."""
    
    print("Testing API Research Endpoints")
    print("=" * 40)
    
    # Fusion 360 Add-In HTTP server URL
    base_url = "http://localhost:5001"
    
    # Test both research endpoints
    endpoints = {
        "WCS API Research": f"{base_url}/research/wcs-api",
        "Model ID Research": f"{base_url}/research/model-id"
    }
    
    results = {}
    
    for research_type, endpoint in endpoints.items():
        print(f"\n{research_type}")
        print("-" * len(research_type))
        
        try:
            print(f"Calling: {endpoint}")
            
            # Make the request
            response = requests.get(endpoint, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                # Parse the JSON response
                research_data = response.json()
                
                # Save to file with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{research_type.lower().replace(' ', '_')}_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(research_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ {research_type} completed successfully!")
                print(f"📄 Results saved to: {filename}")
                
                # Print summary
                print(f"📊 Summary:")
                if research_type == "WCS API Research":
                    print(f"   API Version: {research_data.get('api_version', 'Unknown')}")
                    setup_api = research_data.get('setup_api', {})
                    print(f"   Setup Properties: {len(setup_api.get('setup_class_properties', []))}")
                    print(f"   WCS Properties: {len(setup_api.get('wcs_properties', []))}")
                    print(f"   Stock Properties: {len(setup_api.get('stock_properties', []))}")
                elif research_type == "Model ID Research":
                    model_structure = research_data.get('model_id_structure', {})
                    print(f"   Document IDs: {'Yes' if model_structure.get('document_ids') else 'No'}")
                    print(f"   Component IDs: {'Yes' if model_structure.get('component_ids') else 'No'}")
                    print(f"   Body IDs: {'Yes' if model_structure.get('body_ids') else 'No'}")
                    print(f"   Feature IDs: {'Yes' if model_structure.get('feature_ids') else 'No'}")
                
                errors = research_data.get('errors', [])
                if errors:
                    print(f"   ⚠️  Errors: {len(errors)}")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"      - {error}")
                else:
                    print("   ✅ No errors")
                
                results[research_type] = {"success": True, "filename": filename}
                
            else:
                print(f"❌ Request failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"Response: {response.text}")
                results[research_type] = {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Is Fusion 360 running with the add-in active?")
            print("   Make sure:")
            print("   1. Fusion 360 is open")
            print("   2. FusionMCPBridge add-in is running")
            print("   3. HTTP server is listening on localhost:5001")
            results[research_type] = {"success": False, "error": "Connection failed"}
            
        except requests.exceptions.Timeout:
            print("❌ Request timed out. The research may take some time to complete.")
            results[research_type] = {"success": False, "error": "Timeout"}
            
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            results[research_type] = {"success": False, "error": str(e)}
    
    # Print overall summary
    print("\n" + "=" * 40)
    print("Overall Results:")
    successful = sum(1 for result in results.values() if result["success"])
    total = len(results)
    print(f"✅ Successful: {successful}/{total}")
    
    if successful > 0:
        print("\n📁 Generated Files:")
        for research_type, result in results.items():
            if result["success"]:
                print(f"   - {result['filename']}")
    
    return successful == total


if __name__ == "__main__":
    success = test_api_research()
    sys.exit(0 if success else 1)