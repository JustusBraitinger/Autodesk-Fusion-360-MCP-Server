"""
Model ID Research Script for Fusion 360

This script investigates model ID handling, validation, and integration between
the design workspace and CAM setup creation in Fusion 360.

This script should be run within Fusion 360 to access the adsk API.
"""

import adsk.core
import adsk.fusion
import adsk.cam
import json
from typing import Dict, Any, Optional, List


def research_model_id_handling() -> Dict[str, Any]:
    """
    Research model ID structure, validation, and integration patterns.
    
    Returns:
        dict: Comprehensive model ID research results
    """
    results = {
        "timestamp": "2025-01-03",
        "model_id_structure": {},
        "validation_methods": {},
        "design_workspace_integration": {},
        "geometry_reference_patterns": {},
        "entity_token_analysis": {},
        "cam_integration_patterns": {},
        "errors": []
    }
    
    try:
        app = adsk.core.Application.get()
        if not app:
            results["errors"].append("Cannot access Fusion 360 application")
            return results
        
        # Research model ID structure
        results["model_id_structure"] = _research_model_id_structure(app)
        
        # Research validation methods
        results["validation_methods"] = _research_validation_methods(app)
        
        # Research design workspace integration
        results["design_workspace_integration"] = _research_design_workspace_integration(app)
        
        # Research geometry reference patterns
        results["geometry_reference_patterns"] = _research_geometry_reference_patterns(app)
        
        # Research entity token analysis
        results["entity_token_analysis"] = _research_entity_token_analysis(app)
        
        # Research CAM integration patterns
        results["cam_integration_patterns"] = _research_cam_integration_patterns(app)
        
    except Exception as e:
        results["errors"].append(f"Top-level model ID research error: {str(e)}")
    
    return results


def _research_model_id_structure(app: adsk.core.Application) -> Dict[str, Any]:
    """Research the structure and format of model IDs."""
    model_structure = {
        "document_ids": {},
        "component_ids": {},
        "body_ids": {},
        "feature_ids": {},
        "id_patterns": {},
        "errors": []
    }
    
    try:
        # Get active document
        doc = app.activeDocument
        if not doc:
            model_structure["errors"].append("No active document")
            return model_structure
        
        # Document ID analysis
        model_structure["document_ids"] = {
            "name": doc.name,
            "entity_token": doc.entityToken if hasattr(doc, 'entityToken') else None,
            "data_file": doc.dataFile.name if hasattr(doc, 'dataFile') and doc.dataFile else None,
            "properties": _get_object_properties(doc)[:10]
        }
        
        # Get design product
        design = app.activeProduct
        if design and hasattr(design, 'rootComponent'):
            root_comp = design.rootComponent
            
            # Component ID analysis
            model_structure["component_ids"] = {
                "root_component": {
                    "name": root_comp.name,
                    "entity_token": root_comp.entityToken if hasattr(root_comp, 'entityToken') else None,
                    "properties": _get_object_properties(root_comp)[:10]
                },
                "child_components": []
            }
            
            # Analyze child components if any
            if hasattr(root_comp, 'occurrences'):
                occurrences = root_comp.occurrences
                if occurrences and occurrences.count > 0:
                    for i in range(min(3, occurrences.count)):  # Limit to first 3
                        occ = occurrences.item(i)
                        comp_data = {
                            "name": occ.name if hasattr(occ, 'name') else f"Component_{i}",
                            "entity_token": occ.entityToken if hasattr(occ, 'entityToken') else None,
                            "component_entity_token": occ.component.entityToken if hasattr(occ, 'component') and hasattr(occ.component, 'entityToken') else None
                        }
                        model_structure["component_ids"]["child_components"].append(comp_data)
            
            # Body ID analysis
            if hasattr(root_comp, 'bRepBodies'):
                bodies = root_comp.bRepBodies
                model_structure["body_ids"] = {
                    "total_count": bodies.count if bodies else 0,
                    "sample_bodies": []
                }
                
                if bodies and bodies.count > 0:
                    for i in range(min(3, bodies.count)):  # Limit to first 3
                        body = bodies.item(i)
                        body_data = {
                            "name": body.name if hasattr(body, 'name') else f"Body_{i}",
                            "entity_token": body.entityToken if hasattr(body, 'entityToken') else None,
                            "is_solid": body.isSolid if hasattr(body, 'isSolid') else None,
                            "volume": body.volume if hasattr(body, 'volume') else None,
                            "properties": _get_object_properties(body)[:5]
                        }
                        model_structure["body_ids"]["sample_bodies"].append(body_data)
            
            # Feature ID analysis
            if hasattr(root_comp, 'features'):
                features = root_comp.features
                model_structure["feature_ids"] = {
                    "total_count": _count_all_features(features) if features else 0,
                    "sample_features": []
                }
                
                # Sample different feature types
                feature_samples = _get_sample_features(features)
                model_structure["feature_ids"]["sample_features"] = feature_samples
        
        # Analyze ID patterns
        model_structure["id_patterns"] = _analyze_id_patterns(model_structure)
        
    except Exception as e:
        model_structure["errors"].append(f"Model ID structure research error: {str(e)}")
    
    return model_structure


def _research_validation_methods(app: adsk.core.Application) -> Dict[str, Any]:
    """Research methods for validating model IDs."""
    validation = {
        "entity_token_validation": {},
        "geometry_validation": {},
        "reference_validation": {},
        "cam_validation": {},
        "errors": []
    }
    
    try:
        # Research entity token validation
        validation["entity_token_validation"] = _research_entity_token_validation(app)
        
        # Research geometry validation
        validation["geometry_validation"] = _research_geometry_validation(app)
        
        # Research reference validation
        validation["reference_validation"] = _research_reference_validation(app)
        
        # Research CAM-specific validation
        validation["cam_validation"] = _research_cam_validation(app)
        
    except Exception as e:
        validation["errors"].append(f"Validation methods research error: {str(e)}")
    
    return validation


def _research_design_workspace_integration(app: adsk.core.Application) -> Dict[str, Any]:
    """Research integration between design workspace and CAM setup creation."""
    integration = {
        "workspace_switching": {},
        "geometry_selection": {},
        "model_preparation": {},
        "cam_setup_prerequisites": {},
        "errors": []
    }
    
    try:
        # Research workspace switching
        integration["workspace_switching"] = {
            "current_workspace": app.activeWorkspace.name if app.activeWorkspace else "Unknown",
            "available_workspaces": [ws.name for ws in app.workspaces] if app.workspaces else [],
            "workspace_switching_methods": _get_object_properties(app.workspaces)[:5] if app.workspaces else []
        }
        
        # Research geometry selection patterns
        integration["geometry_selection"] = _research_geometry_selection_patterns(app)
        
        # Research model preparation requirements
        integration["model_preparation"] = _research_model_preparation_requirements(app)
        
        # Research CAM setup prerequisites
        integration["cam_setup_prerequisites"] = _research_cam_setup_prerequisites(app)
        
    except Exception as e:
        integration["errors"].append(f"Design workspace integration research error: {str(e)}")
    
    return integration


def _research_geometry_reference_patterns(app: adsk.core.Application) -> Dict[str, Any]:
    """Research patterns for referencing geometry in CAM setups."""
    geometry_ref = {
        "body_references": {},
        "face_references": {},
        "edge_references": {},
        "point_references": {},
        "wcs_references": {},
        "errors": []
    }
    
    try:
        design = app.activeProduct
        if design and hasattr(design, 'rootComponent'):
            root_comp = design.rootComponent
            
            # Research body references
            if hasattr(root_comp, 'bRepBodies'):
                bodies = root_comp.bRepBodies
                if bodies and bodies.count > 0:
                    sample_body = bodies.item(0)
                    geometry_ref["body_references"] = {
                        "reference_methods": _get_object_properties(sample_body)[:10],
                        "entity_token": sample_body.entityToken if hasattr(sample_body, 'entityToken') else None,
                        "selection_methods": _research_body_selection_methods(sample_body)
                    }
                    
                    # Research face references
                    if hasattr(sample_body, 'faces'):
                        faces = sample_body.faces
                        if faces and faces.count > 0:
                            sample_face = faces.item(0)
                            geometry_ref["face_references"] = {
                                "reference_methods": _get_object_properties(sample_face)[:10],
                                "entity_token": sample_face.entityToken if hasattr(sample_face, 'entityToken') else None,
                                "geometry_properties": _research_face_geometry_properties(sample_face)
                            }
                    
                    # Research edge references
                    if hasattr(sample_body, 'edges'):
                        edges = sample_body.edges
                        if edges and edges.count > 0:
                            sample_edge = edges.item(0)
                            geometry_ref["edge_references"] = {
                                "reference_methods": _get_object_properties(sample_edge)[:10],
                                "entity_token": sample_edge.entityToken if hasattr(sample_edge, 'entityToken') else None
                            }
            
            # Research Work Coordinate System references
            if hasattr(root_comp, 'coordinateSystems'):
                wcs_systems = root_comp.coordinateSystems
                if wcs_systems and wcs_systems.count > 0:
                    sample_wcs = wcs_systems.item(0)
                    geometry_ref["wcs_references"] = {
                        "reference_methods": _get_object_properties(sample_wcs)[:10],
                        "entity_token": sample_wcs.entityToken if hasattr(sample_wcs, 'entityToken') else None
                    }
        
    except Exception as e:
        geometry_ref["errors"].append(f"Geometry reference patterns research error: {str(e)}")
    
    return geometry_ref


def _research_entity_token_analysis(app: adsk.core.Application) -> Dict[str, Any]:
    """Research entity token structure and usage patterns."""
    token_analysis = {
        "token_format": {},
        "token_persistence": {},
        "token_uniqueness": {},
        "token_validation": {},
        "errors": []
    }
    
    try:
        # Collect sample entity tokens
        sample_tokens = []
        
        design = app.activeProduct
        if design and hasattr(design, 'rootComponent'):
            root_comp = design.rootComponent
            
            # Collect tokens from different entity types
            if hasattr(root_comp, 'entityToken'):
                sample_tokens.append({
                    "type": "Component",
                    "name": root_comp.name,
                    "token": root_comp.entityToken
                })
            
            if hasattr(root_comp, 'bRepBodies'):
                bodies = root_comp.bRepBodies
                if bodies and bodies.count > 0:
                    for i in range(min(3, bodies.count)):
                        body = bodies.item(i)
                        if hasattr(body, 'entityToken'):
                            sample_tokens.append({
                                "type": "Body",
                                "name": body.name if hasattr(body, 'name') else f"Body_{i}",
                                "token": body.entityToken
                            })
        
        # Analyze token patterns
        token_analysis["token_format"] = _analyze_token_format(sample_tokens)
        token_analysis["sample_tokens"] = sample_tokens[:10]  # Limit output
        
        # Research token persistence and validation
        token_analysis["token_persistence"] = {
            "notes": [
                "Entity tokens should persist across sessions",
                "Tokens may change if geometry is modified",
                "Need to test token validity before use"
            ]
        }
        
        token_analysis["token_validation"] = {
            "validation_methods": [
                "Check if entity still exists in document",
                "Verify entity type matches expected type",
                "Confirm entity is accessible from current context"
            ]
        }
        
    except Exception as e:
        token_analysis["errors"].append(f"Entity token analysis error: {str(e)}")
    
    return token_analysis


def _research_cam_integration_patterns(app: adsk.core.Application) -> Dict[str, Any]:
    """Research patterns for integrating model references with CAM setup creation."""
    cam_integration = {
        "setup_creation_workflow": {},
        "model_reference_requirements": {},
        "geometry_selection_for_cam": {},
        "stock_definition_patterns": {},
        "errors": []
    }
    
    try:
        # Research CAM product access
        doc = app.activeDocument
        if doc:
            products = doc.products
            cam_product = products.itemByProductType('CAMProductType')
            
            if cam_product:
                cam = adsk.cam.CAM.cast(cam_product)
                if cam:
                    # Research existing setup patterns
                    setups = cam.setups
                    if setups and setups.count > 0:
                        sample_setup = setups.item(0)
                        cam_integration["setup_creation_workflow"] = {
                            "existing_setup_properties": _get_object_properties(sample_setup)[:15],
                            "setup_creation_methods": _research_setup_creation_workflow(cam)
                        }
                        
                        # Research model reference requirements
                        cam_integration["model_reference_requirements"] = _research_model_reference_requirements(sample_setup)
                        
                        # Research stock definition patterns
                        cam_integration["stock_definition_patterns"] = _research_stock_definition_patterns(sample_setup)
                    else:
                        cam_integration["setup_creation_workflow"] = {
                            "note": "No existing setups found",
                            "setup_collection_methods": _get_object_properties(setups)[:10] if setups else []
                        }
                else:
                    cam_integration["errors"].append("Cannot cast to CAM product")
            else:
                cam_integration["errors"].append("No CAM product found - document may not have CAM data")
        
        # Research geometry selection for CAM
        cam_integration["geometry_selection_for_cam"] = _research_geometry_selection_for_cam(app)
        
    except Exception as e:
        cam_integration["errors"].append(f"CAM integration patterns research error: {str(e)}")
    
    return cam_integration


# Helper functions for detailed research

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
        
        return properties
    
    except Exception:
        return ["Error accessing object properties"]


def _count_all_features(features) -> int:
    """Count all features in the features collection."""
    try:
        total = 0
        for attr in dir(features):
            if not attr.startswith('_') and hasattr(features, attr):
                feature_collection = getattr(features, attr)
                if hasattr(feature_collection, 'count'):
                    total += feature_collection.count
        return total
    except Exception:
        return 0


def _get_sample_features(features) -> List[Dict[str, Any]]:
    """Get sample features from different feature collections."""
    samples = []
    
    try:
        # Common feature types to sample
        feature_types = [
            'extrudeFeatures',
            'revolveFeatures', 
            'filletFeatures',
            'holeFeatures',
            'patternFeatures'
        ]
        
        for feature_type in feature_types:
            if hasattr(features, feature_type):
                feature_collection = getattr(features, feature_type)
                if feature_collection and hasattr(feature_collection, 'count') and feature_collection.count > 0:
                    sample_feature = feature_collection.item(0)
                    feature_data = {
                        "type": feature_type,
                        "name": sample_feature.name if hasattr(sample_feature, 'name') else f"Feature_0",
                        "entity_token": sample_feature.entityToken if hasattr(sample_feature, 'entityToken') else None,
                        "properties": _get_object_properties(sample_feature)[:5]
                    }
                    samples.append(feature_data)
                    
                    if len(samples) >= 5:  # Limit samples
                        break
    
    except Exception:
        pass
    
    return samples


def _analyze_id_patterns(model_structure: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze patterns in entity IDs and tokens."""
    patterns = {
        "token_characteristics": [],
        "naming_patterns": [],
        "id_structure_analysis": {}
    }
    
    try:
        # Collect all tokens for analysis
        all_tokens = []
        
        # Document tokens
        doc_ids = model_structure.get("document_ids", {})
        if doc_ids.get("entity_token"):
            all_tokens.append(doc_ids["entity_token"])
        
        # Component tokens
        comp_ids = model_structure.get("component_ids", {})
        root_comp = comp_ids.get("root_component", {})
        if root_comp.get("entity_token"):
            all_tokens.append(root_comp["entity_token"])
        
        # Body tokens
        body_ids = model_structure.get("body_ids", {})
        for body in body_ids.get("sample_bodies", []):
            if body.get("entity_token"):
                all_tokens.append(body["entity_token"])
        
        # Analyze token characteristics
        if all_tokens:
            patterns["token_characteristics"] = [
                f"Sample token count: {len(all_tokens)}",
                f"Average token length: {sum(len(str(token)) for token in all_tokens) / len(all_tokens):.1f}",
                f"Token format appears to be: {_infer_token_format(all_tokens)}"
            ]
        
        patterns["id_structure_analysis"] = {
            "entity_tokens_found": len(all_tokens),
            "token_uniqueness": len(set(all_tokens)) == len(all_tokens) if all_tokens else True,
            "sample_tokens": all_tokens[:5]  # First 5 tokens as examples
        }
        
    except Exception:
        patterns["token_characteristics"] = ["Error analyzing ID patterns"]
    
    return patterns


def _infer_token_format(tokens: List[str]) -> str:
    """Infer the format pattern of entity tokens."""
    if not tokens:
        return "No tokens to analyze"
    
    try:
        sample_token = str(tokens[0])
        
        # Check for common patterns
        if len(sample_token) > 20 and '-' in sample_token:
            return "UUID-like format with hyphens"
        elif sample_token.isdigit():
            return "Numeric ID"
        elif len(sample_token) > 10:
            return "Long alphanumeric string"
        else:
            return "Short identifier"
    
    except Exception:
        return "Unknown format"


def _research_entity_token_validation(app: adsk.core.Application) -> Dict[str, Any]:
    """Research entity token validation methods."""
    return {
        "validation_approaches": [
            "Use app.findEntityByToken(token) method",
            "Check if returned entity is not None",
            "Verify entity type matches expected type",
            "Test entity accessibility in current context"
        ],
        "error_handling": [
            "Handle invalid token gracefully",
            "Provide meaningful error messages",
            "Fall back to alternative selection methods"
        ]
    }


def _research_geometry_validation(app: adsk.core.Application) -> Dict[str, Any]:
    """Research geometry validation methods."""
    return {
        "validation_methods": [
            "Check geometry existence in document",
            "Verify geometry type (body, face, edge, etc.)",
            "Validate geometry is suitable for CAM operations",
            "Check geometry is not suppressed or hidden"
        ],
        "geometry_requirements": [
            "Bodies must be solid for machining operations",
            "Faces must be accessible for Work Coordinate System definition",
            "Geometry must be in active component"
        ]
    }


def _research_reference_validation(app: adsk.core.Application) -> Dict[str, Any]:
    """Research reference validation methods."""
    return {
        "reference_types": [
            "Entity token references",
            "Name-based references", 
            "Index-based references",
            "Geometric property references"
        ],
        "validation_strategies": [
            "Prefer entity tokens for persistence",
            "Validate references before use",
            "Provide fallback selection methods",
            "Cache valid references for performance"
        ]
    }


def _research_cam_validation(app: adsk.core.Application) -> Dict[str, Any]:
    """Research CAM-specific validation methods."""
    return {
        "cam_requirements": [
            "Document must have CAM product",
            "MANUFACTURE workspace must be accessible",
            "Geometry must be suitable for machining",
            "Model must be prepared for CAM operations"
        ],
        "validation_workflow": [
            "Check CAM product availability",
            "Validate geometry selection",
            "Verify model preparation state",
            "Confirm setup creation prerequisites"
        ]
    }


def _research_geometry_selection_patterns(app: adsk.core.Application) -> Dict[str, Any]:
    """Research geometry selection patterns for CAM."""
    return {
        "selection_methods": [
            "Interactive selection in UI",
            "Programmatic selection by entity token",
            "Selection by name or properties",
            "Bulk selection of related geometry"
        ],
        "selection_context": [
            "Selection must happen in design workspace",
            "Selected geometry persists across workspace switches",
            "Selection state affects CAM setup creation",
            "Multiple selection types may be required"
        ]
    }


def _research_model_preparation_requirements(app: adsk.core.Application) -> Dict[str, Any]:
    """Research model preparation requirements for CAM."""
    return {
        "preparation_steps": [
            "Ensure model is fully defined",
            "Check for modeling errors or warnings",
            "Verify geometry is suitable for machining",
            "Prepare stock geometry if needed"
        ],
        "common_issues": [
            "Incomplete or invalid geometry",
            "Missing or inaccessible bodies",
            "Geometry not suitable for selected CAM operations",
            "Model Work Coordinate System not properly defined"
        ]
    }


def _research_cam_setup_prerequisites(app: adsk.core.Application) -> Dict[str, Any]:
    """Research prerequisites for CAM setup creation."""
    return {
        "prerequisites": [
            "Active document with valid geometry",
            "CAM product initialized in document",
            "Appropriate workspace context",
            "Geometry selection completed"
        ],
        "setup_requirements": [
            "Model geometry for machining operations",
            "Stock definition (automatic or manual)",
            "Work coordinate system definition",
            "Tool library access"
        ]
    }


def _research_body_selection_methods(body) -> Dict[str, Any]:
    """Research methods for selecting and referencing bodies."""
    return {
        "selection_methods": _get_object_properties(body)[:8],
        "reference_properties": [
            "entityToken for persistent reference",
            "name for user-friendly identification", 
            "volume and other geometric properties",
            "parent component relationship"
        ]
    }


def _research_face_geometry_properties(face) -> Dict[str, Any]:
    """Research face geometry properties for Work Coordinate System definition."""
    properties = {}
    
    try:
        if hasattr(face, 'geometry'):
            geometry = face.geometry
            properties["geometry_type"] = type(geometry).__name__
            properties["geometry_properties"] = _get_object_properties(geometry)[:5]
        
        if hasattr(face, 'normal'):
            properties["has_normal"] = True
        
        if hasattr(face, 'centroid'):
            properties["has_centroid"] = True
            
    except Exception:
        properties["error"] = "Error accessing face properties"
    
    return properties


def _analyze_token_format(tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the format and characteristics of entity tokens."""
    analysis = {
        "token_count": len(tokens),
        "token_characteristics": [],
        "format_patterns": []
    }
    
    if tokens:
        # Analyze token lengths and formats
        token_strings = [str(token["token"]) for token in tokens if token.get("token")]
        
        if token_strings:
            lengths = [len(token) for token in token_strings]
            analysis["token_characteristics"] = [
                f"Token count: {len(token_strings)}",
                f"Average length: {sum(lengths) / len(lengths):.1f}",
                f"Length range: {min(lengths)} - {max(lengths)}"
            ]
            
            # Look for common patterns
            if all('-' in token for token in token_strings):
                analysis["format_patterns"].append("All tokens contain hyphens (UUID-like)")
            
            if all(len(token) > 20 for token in token_strings):
                analysis["format_patterns"].append("All tokens are long strings (>20 chars)")
    
    return analysis


def _research_setup_creation_workflow(cam) -> Dict[str, Any]:
    """Research the workflow for creating CAM setups."""
    return {
        "setup_collection_methods": _get_object_properties(cam.setups)[:10] if hasattr(cam, 'setups') else [],
        "creation_workflow": [
            "Access cam.setups collection",
            "Use appropriate creation method (add, create, etc.)",
            "Configure setup properties (WCS, stock, etc.)",
            "Validate setup configuration"
        ],
        "configuration_requirements": [
            "Work coordinate system definition",
            "Stock geometry and material",
            "Model geometry selection",
            "Setup naming and organization"
        ]
    }


def _research_model_reference_requirements(setup) -> Dict[str, Any]:
    """Research model reference requirements for CAM setups."""
    requirements = {
        "setup_properties": _get_object_properties(setup)[:15],
        "model_reference_methods": [],
        "geometry_requirements": []
    }
    
    try:
        # Look for model-related properties
        if hasattr(setup, 'models'):
            requirements["model_reference_methods"].append("setup.models property")
        
        if hasattr(setup, 'stock'):
            stock = setup.stock
            requirements["stock_properties"] = _get_object_properties(stock)[:10]
        
        if hasattr(setup, 'workCoordinateSystem'):
            wcs = setup.workCoordinateSystem
            requirements["wcs_properties"] = _get_object_properties(wcs)[:10]
        elif hasattr(setup, 'coordinateSystem'):
            cs = setup.coordinateSystem
            requirements["wcs_properties"] = _get_object_properties(cs)[:10]
        
    except Exception:
        requirements["error"] = "Error accessing setup properties"
    
    return requirements


def _research_stock_definition_patterns(setup) -> Dict[str, Any]:
    """Research stock definition patterns in CAM setups."""
    patterns = {
        "stock_configuration": {},
        "stock_types": [],
        "model_integration": {}
    }
    
    try:
        if hasattr(setup, 'stock'):
            stock = setup.stock
            patterns["stock_configuration"] = {
                "properties": _get_object_properties(stock)[:10],
                "stock_type": type(stock).__name__ if stock else "No stock"
            }
            
            # Research stock model integration
            if hasattr(stock, 'models'):
                patterns["model_integration"]["stock_models"] = "Stock has models property"
            
            if hasattr(stock, 'geometry'):
                patterns["model_integration"]["stock_geometry"] = "Stock has geometry property"
        
    except Exception:
        patterns["error"] = "Error accessing stock properties"
    
    return patterns


def _research_geometry_selection_for_cam(app: adsk.core.Application) -> Dict[str, Any]:
    """Research geometry selection patterns specific to CAM operations."""
    return {
        "selection_requirements": [
            "Geometry must be selected before CAM setup creation",
            "Selection context affects available CAM operations",
            "Multiple geometry types may need selection",
            "Selection state persists across workspace switches"
        ],
        "selection_methods": [
            "Interactive selection in design workspace",
            "Programmatic selection using entity tokens",
            "Bulk selection of related geometry",
            "Selection validation before CAM operations"
        ],
        "integration_patterns": [
            "Design workspace selection → CAM setup creation",
            "Geometry validation → Setup configuration",
            "Model preparation → CAM operation definition"
        ]
    }


def save_model_id_research_results(results: Dict[str, Any], filename: str = "model_id_research_results.json"):
    """Save model ID research results to a JSON file."""
    try:
        import os
        
        # Save to the FusionMCPBridge directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return f"Model ID research results saved to: {filepath}"
    
    except Exception as e:
        return f"Error saving results: {str(e)}"


def run_model_id_research():
    """
    Main function to run the model ID research.
    
    This function should be called from within Fusion 360 to access the adsk API.
    """
    print("Starting Model ID Research...")
    print("=" * 50)
    
    # Perform the research
    results = research_model_id_handling()
    
    # Save results to file
    save_message = save_model_id_research_results(results)
    print(f"\n{save_message}")
    
    # Print summary
    print("\nModel ID Research Summary:")
    print(f"- Timestamp: {results.get('timestamp', 'Unknown')}")
    print(f"- Model ID structure documented: {'Yes' if results.get('model_id_structure') else 'No'}")
    print(f"- Validation methods found: {'Yes' if results.get('validation_methods') else 'No'}")
    print(f"- Design integration patterns: {'Yes' if results.get('design_workspace_integration') else 'No'}")
    print(f"- CAM integration patterns: {'Yes' if results.get('cam_integration_patterns') else 'No'}")
    print(f"- Errors encountered: {len(results.get('errors', []))}")
    
    if results.get('errors'):
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\nModel ID research complete. Check the JSON file for detailed results.")
    return results


# If running as a script within Fusion 360
if __name__ == "__main__":
    run_model_id_research()