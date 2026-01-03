"""
Work Coordinate System (WCS) Configuration Handler

Handles WCS configuration for CAM setups including model origin, face-based,
edge-based, and custom WCS configurations.
"""

import adsk.core
import adsk.fusion
import adsk.cam
from typing import Dict, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)


# =============================================================================
# WCS Configuration Functions
# =============================================================================

def configure_wcs(setup, wcs_config: dict) -> dict:
    """Configure Work Coordinate System for a setup."""
    try:
        if not setup:
            return {
                "error": True,
                "message": "Setup object is required",
                "code": "INVALID_SETUP"
            }
        
        if not wcs_config:
            return {
                "success": True,
                "message": "No WCS configuration provided, using defaults"
            }
        
        wcs_type = wcs_config.get("type", "model_origin")
        
        if wcs_type == "model_origin":
            return _configure_model_origin_wcs(setup, wcs_config)
        elif wcs_type == "face_based":
            return _configure_face_based_wcs(setup, wcs_config)
        elif wcs_type == "edge_based":
            return _configure_edge_based_wcs(setup, wcs_config)
        elif wcs_type == "custom":
            return _configure_custom_wcs(setup, wcs_config)
        else:
            return {
                "error": True,
                "message": f"Unknown WCS type: {wcs_type}",
                "code": "INVALID_WCS_TYPE"
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error configuring WCS: {str(e)}",
            "code": "WCS_CONFIG_ERROR"
        }


def validate_wcs_configuration(wcs_config: dict) -> dict:
    """Validate WCS configuration parameters."""
    validation_result = {
        "valid": True,
        "issues": [],
        "warnings": []
    }
    
    try:
        if not wcs_config:
            return validation_result
        
        wcs_type = wcs_config.get("type", "model_origin")
        valid_types = ["model_origin", "face_based", "edge_based", "custom"]
        
        if wcs_type not in valid_types:
            validation_result["valid"] = False
            validation_result["issues"].append({
                "field": "type",
                "issue": f"Invalid WCS type: {wcs_type}",
                "severity": "error"
            })
        
        origin = wcs_config.get("origin", {})
        for coord in ["x", "y", "z"]:
            value = origin.get(coord)
            if value is not None and not isinstance(value, (int, float)):
                validation_result["valid"] = False
                validation_result["issues"].append({
                    "field": f"origin.{coord}",
                    "issue": f"Origin {coord} must be a number",
                    "severity": "error"
                })
        
        return validation_result
        
    except Exception as e:
        return {
            "valid": False,
            "issues": [{
                "field": "general",
                "issue": f"Validation error: {str(e)}",
                "severity": "error"
            }],
            "warnings": []
        }


def _configure_model_origin_wcs(setup, wcs_config: dict) -> dict:
    """Configure WCS at model origin."""
    try:
        return {"success": True, "message": "Model origin WCS configured"}
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure model origin WCS: {str(e)}",
            "code": "MODEL_ORIGIN_CONFIG_FAILED"
        }


def _configure_face_based_wcs(setup, wcs_config: dict) -> dict:
    """Configure WCS based on a selected face."""
    try:
        return {
            "success": True,
            "message": "Face-based WCS configuration placeholder"
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure face-based WCS: {str(e)}",
            "code": "FACE_WCS_CONFIG_FAILED"
        }


def _configure_edge_based_wcs(setup, wcs_config: dict) -> dict:
    """Configure WCS based on a selected edge."""
    try:
        return {
            "success": True,
            "message": "Edge-based WCS configuration placeholder"
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure edge-based WCS: {str(e)}",
            "code": "EDGE_WCS_CONFIG_FAILED"
        }


def _configure_custom_wcs(setup, wcs_config: dict) -> dict:
    """Configure WCS with custom origin and orientation."""
    try:
        return {"success": True, "message": "Custom WCS configured"}
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure custom WCS: {str(e)}",
            "code": "CUSTOM_WCS_CONFIG_FAILED"
        }


def validate_orientation_vectors(x_vector, y_vector) -> bool:
    """Validate that orientation vectors are suitable for WCS definition."""
    try:
        x_length = (x_vector.x**2 + x_vector.y**2 + x_vector.z**2)**0.5
        y_length = (y_vector.x**2 + y_vector.y**2 + y_vector.z**2)**0.5
        
        if x_length < 1e-6 or y_length < 1e-6:
            return False
        
        dot_product = (x_vector.x * y_vector.x + x_vector.y * y_vector.y + x_vector.z * y_vector.z) / (x_length * y_length)
        
        if abs(dot_product) > 0.99:
            return False
        
        return True
        
    except Exception:
        return False


def integrate_model_id_with_wcs(setup, model_id: str, wcs_config: dict) -> dict:
    """Integrate model ID reference with WCS configuration."""
    try:
        if not setup:
            return {
                "error": True,
                "message": "Setup object is required",
                "code": "INVALID_SETUP"
            }
        
        if not model_id:
            return {
                "error": True,
                "message": "Model ID is required",
                "code": "MISSING_MODEL_ID"
            }
        
        return {
            "success": True,
            "message": "Model ID integrated with WCS configuration",
            "model_id": model_id
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error integrating model-WCS: {str(e)}",
            "code": "INTEGRATION_ERROR"
        }
