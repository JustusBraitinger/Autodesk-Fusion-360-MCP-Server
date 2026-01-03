"""
WCS API Research Script for Fusion 360

This script investigates the Work Coordinate System (WCS) API structure in Fusion 360
to understand how to programmatically create and configure CAM setups with proper
coordinate systems and model references.

This script should be run within Fusion 360 to access the adsk API.
"""

import adsk.core
import adsk.fusion
import adsk.cam
import json
from typing import Dict, Any, Optional, List


def research_wcs_api_structure() -> Dict[str, Any]:
    """
    Research the WCS API structure and document findings.
    
    Returns:
        dict: Comprehensive API research results
    """
    results = {
        "timestamp": "2025-01-03",
        "api_version": "Unknown",
        "setup_api": {},
        "wcs_api": {},
        "model_id_api": {},
        "wcs_options": {},
        "origin_specification_methods": {},
        "orientation_options": {},
        "errors": []
    }
    
    try:
        app = adsk.core.Application.get()
        if not app:
            results["errors"].append("Cannot access Fusion 360 application")
            return results
        
        results["api_version"] = app.version
        
        # Research Setup API structure
        results["setup_api"] = _research_setup_api(app)
        
        # Research WCS configuration options
        results["wcs_api"] = _research_wcs_configuration(app)
        
        # Research model ID handling
        results["model_id_api"] = _research_model_id_handling(app)
        
        # Research coordinate system options
        results["wcs_options"] = _research_wcs_options()
        
        # Research origin specification methods
        results["origin_specification_methods"] = _research_origin_specification()
        
        # Research orientation options
        results["orientation_options"] = _research_orientation_options()
        
    except Exception as e:
        results["errors"].append(f"Top-level research error: {str(e)}")
    
    return results


def _research_setup_api(app: adsk.core.Application) -> Dict[str, Any]:
    """Research the CAM Setup API structure."""
    setup_api = {
        "setup_class_properties": [],
        "setup_creation_methods": [],
        "setup_configuration_properties": [],
        "wcs_properties": [],
        "stock_properties": [],
        "errors": []
    }
    
    try:
        # Get active document and CAM product
        doc = app.activeDocument
        if not doc:
            setup_api["errors"].append("No active document")
            return setup_api
        
        products = doc.products
        cam_product = products.itemByProductType('CAMProductType')
        
        if not cam_product:
            setup_api["errors"].append("No CAM product found")
            return setup_api
        
        cam = adsk.cam.CAM.cast(cam_product)
        if not cam:
            setup_api["errors"].append("Cannot cast to CAM product")
            return setup_api
        
        # Research existing setups if any
        setups = cam.setups
        if setups and setups.count > 0:
            sample_setup = setups.item(0)
            setup_api["setup_class_properties"] = _get_object_properties(sample_setup)
            
            # Research WCS properties on existing setup
            if hasattr(sample_setup, 'workCoordinateSystem'):
                wcs = sample_setup.workCoordinateSystem
                setup_api["wcs_properties"] = _get_object_properties(wcs)
            elif hasattr(sample_setup, 'coordinateSystem'):
                cs = sample_setup.coordinateSystem
                setup_api["wcs_properties"] = _get_object_properties(cs)
            
            # Research stock properties
            if hasattr(sample_setup, 'stock'):
                stock = sample_setup.stock
                setup_api["stock_properties"] = _get_object_properties(stock)
        
        # Research setup creation methods
        setup_api["setup_creation_methods"] = _research_setup_creation_methods(cam)
        
    except Exception as e:
        setup_api["errors"].append(f"Setup API research error: {str(e)}")
    
    return setup_api


def _research_wcs_configuration(app: adsk.core.Application) -> Dict[str, Any]:
    """Research WCS configuration options and methods."""
    wcs_api = {
        "wcs_creation_methods": [],
        "wcs_types": [],
        "origin_methods": [],
        "orientation_methods": [],
        "model_reference_methods": [],
        "errors": []
    }
    
    try:
        # Research coordinate system creation in design workspace
        design = app.activeProduct
        if design and hasattr(design, 'rootComponent'):
            root_comp = design.rootComponent
            
            # Research construction planes and coordinate systems
            if hasattr(root_comp, 'constructionPlanes'):
                planes = root_comp.constructionPlanes
                wcs_api["construction_planes_available"] = planes.count if planes else 0
            
            if hasattr(root_comp, 'coordinateSystems'):
                wcs_systems = root_comp.coordinateSystems
                wcs_api["wcs_available"] = wcs_systems.count if wcs_systems else 0
                
                # If Work Coordinate Systems exist, research their properties
                if wcs_systems and wcs_systems.count > 0:
                    sample_wcs = wcs_systems.item(0)
                    wcs_api["wcs_properties"] = _get_object_properties(sample_wcs)
        
        # Research MANUFACTURE-specific Work Coordinate System options
        wcs_api["manufacture_wcs_options"] = _research_manufacture_wcs_systems()
        
    except Exception as e:
        wcs_api["errors"].append(f"WCS configuration research error: {str(e)}")
    
    return wcs_api


def _research_model_id_handling(app: adsk.core.Application) -> Dict[str, Any]:
    """Research model ID structure and validation methods."""
    model_api = {
        "model_id_structure": {},
        "model_selection_methods": [],
        "geometry_reference_methods": [],
        "design_workspace_integration": {},
        "errors": []
    }
    
    try:
        # Research active design and its components
        design = app.activeProduct
        if design:
            model_api["design_type"] = type(design).__name__
            
            if hasattr(design, 'rootComponent'):
                root_comp = design.rootComponent
                model_api["root_component_properties"] = _get_object_properties(root_comp)
                
                # Research entity tokens and IDs
                if hasattr(root_comp, 'entityToken'):
                    model_api["root_component_id"] = root_comp.entityToken
                
                # Research bodies and their IDs
                if hasattr(root_comp, 'bRepBodies'):
                    bodies = root_comp.bRepBodies
                    if bodies and bodies.count > 0:
                        sample_body = bodies.item(0)
                        model_api["body_id_structure"] = {
                            "entity_token": sample_body.entityToken if hasattr(sample_body, 'entityToken') else None,
                            "name": sample_body.name if hasattr(sample_body, 'name') else None,
                            "properties": _get_object_properties(sample_body)[:10]  # Limit to first 10
                        }
                
                # Research features and their IDs
                if hasattr(root_comp, 'features'):
                    features = root_comp.features
                    model_api["features_available"] = _get_object_properties(features)[:5]  # Limit output
        
        # Research model selection in CAM context
        model_api["cam_model_selection"] = _research_cam_model_selection()
        
    except Exception as e:
        model_api["errors"].append(f"Model ID research error: {str(e)}")
    
    return model_api


def _research_wcs_options() -> Dict[str, Any]:
    """Research available Work Coordinate System configuration options."""
    return {
        "fusion_360_wcs_types": [
            "model_based",
            "face_based", 
            "edge_based",
            "point_based",
            "custom_wcs"
        ],
        "typical_orientations": [
            "xy_plane",
            "xz_plane", 
            "yz_plane",
            "custom_orientation"
        ],
        "origin_types": [
            "model_origin",
            "geometry_center",
            "geometry_corner",
            "custom_point"
        ],
        "notes": [
            "These are typical options found in Fusion 360 UI",
            "Actual API may use different naming conventions",
            "Need to verify through actual API exploration"
        ]
    }


def _research_origin_specification() -> Dict[str, Any]:
    """Research origin specification methods."""
    return {
        "common_methods": [
            "model_origin",
            "geometry_based_origin",
            "custom_point_origin",
            "face_center_origin",
            "edge_midpoint_origin"
        ],
        "coordinate_specification": [
            "absolute_coordinates",
            "relative_to_geometry",
            "parametric_positioning"
        ],
        "notes": [
            "Origin specification likely involves Point3D objects",
            "May require geometry selection for reference-based origins",
            "Custom origins may need coordinate input"
        ]
    }


def _research_orientation_options() -> Dict[str, Any]:
    """Research orientation specification methods."""
    return {
        "orientation_methods": [
            "face_normal_alignment",
            "edge_direction_alignment", 
            "vector_specification",
            "plane_alignment",
            "wcs_alignment"
        ],
        "axis_definitions": [
            "x_axis_direction",
            "y_axis_direction", 
            "z_axis_direction",
            "primary_and_secondary_axis"
        ],
        "notes": [
            "Orientation likely uses Vector3D objects",
            "May support both primary axis and secondary axis definition",
            "Face-based orientation probably uses face normal vectors"
        ]
    }


def _research_setup_creation_methods(cam: adsk.cam.CAM) -> List[str]:
    """Research methods available for creating CAM setups."""
    methods = []
    
    try:
        setups = cam.setups
        if setups:
            # Check for creation methods
            if hasattr(setups, 'add'):
                methods.append("setups.add()")
            if hasattr(setups, 'addByType'):
                methods.append("setups.addByType()")
            if hasattr(setups, 'create'):
                methods.append("setups.create()")
            
            # Get all available methods
            setup_methods = [method for method in dir(setups) if not method.startswith('_')]
            methods.extend([f"setups.{method}()" for method in setup_methods if 'add' in method.lower() or 'create' in method.lower()])
    
    except Exception:
        methods.append("Error accessing setup creation methods")
    
    return methods


def _research_manufacture_wcs_systems() -> Dict[str, Any]:
    """Research MANUFACTURE-specific Work Coordinate System options."""
    return {
        "cam_wcs_properties": [
            "Investigate adsk.cam.Setup.workCoordinateSystem",
            "Check for coordinateSystem property",
            "Look for origin and orientation properties",
            "Research model reference properties"
        ],
        "potential_api_patterns": [
            "setup.workCoordinateSystem.origin = Point3D",
            "setup.workCoordinateSystem.xAxis = Vector3D", 
            "setup.workCoordinateSystem.yAxis = Vector3D",
            "setup.workCoordinateSystem.zAxis = Vector3D"
        ],
        "notes": [
            "Need to examine actual Setup objects to confirm API structure",
            "WCS configuration may be done through setup creation parameters",
            "May require separate WCS creation before setup creation"
        ]
    }


def _research_cam_model_selection() -> Dict[str, Any]:
    """Research model selection methods in CAM context."""
    return {
        "model_selection_approaches": [
            "Body selection from design workspace",
            "Component selection",
            "Feature selection",
            "Entity token reference"
        ],
        "integration_points": [
            "Design workspace to MANUFACTURE workspace",
            "Body reference in setup creation",
            "Model geometry for stock definition",
            "Work Coordinate System reference geometry"
        ],
        "notes": [
            "Model selection likely happens in design workspace first",
            "CAM setup creation may require pre-selected geometry",
            "Entity tokens probably used for persistent references"
        ]
    }


def _get_object_properties(obj) -> List[str]:
    """Get properties and methods of an object for API research."""
    if not obj:
        return ["Object is None"]
    
    try:
        properties = []
        for attr in dir(obj):
            if not attr.startswith('_'):
                try:
                    value = getattr(obj, attr)
                    if callable(value):
                        properties.append(f"{attr}() - method")
                    else:
                        properties.append(f"{attr} - property ({type(value).__name__})")
                except Exception:
                    properties.append(f"{attr} - property (access error)")
        
        return properties[:20]  # Limit to first 20 to avoid overwhelming output
    
    except Exception:
        return ["Error accessing object properties"]


def save_research_results(results: Dict[str, Any], filename: str = "wcs_api_research_results.json"):
    """Save research results to a JSON file."""
    try:
        import os
        
        # Save to the FusionMCPBridge directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return f"Research results saved to: {filepath}"
    
    except Exception as e:
        return f"Error saving results: {str(e)}"


def run_wcs_api_research():
    """
    Main function to run the WCS API research.
    
    This function should be called from within Fusion 360 to access the adsk API.
    """
    print("Starting WCS API Research...")
    print("=" * 50)
    
    # Perform the research
    results = research_wcs_api_structure()
    
    # Save results to file
    save_message = save_research_results(results)
    print(f"\n{save_message}")
    
    # Print summary
    print("\nResearch Summary:")
    print(f"- API Version: {results.get('api_version', 'Unknown')}")
    print(f"- Setup API properties found: {len(results.get('setup_api', {}).get('setup_class_properties', []))}")
    print(f"- WCS properties found: {len(results.get('setup_api', {}).get('wcs_properties', []))}")
    print(f"- Model ID structure documented: {'Yes' if results.get('model_id_api', {}).get('model_id_structure') else 'No'}")
    print(f"- Errors encountered: {len(results.get('errors', []))}")
    
    if results.get('errors'):
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\nResearch complete. Check the JSON file for detailed results.")
    return results


# If running as a script within Fusion 360
if __name__ == "__main__":
    run_wcs_api_research()