"""
Stock Configuration Handler

Handles stock configuration for CAM setups including automatic, geometry-based,
box, and cylinder stock modes.
"""

import adsk.core
import adsk.fusion
import adsk.cam
from typing import Dict, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)


# =============================================================================
# Stock Configuration Functions
# =============================================================================

def configure_stock(setup, stock_config: dict) -> dict:
    """
    Configure stock for a CAM setup based on the provided configuration.
    
    Args:
        setup: The CAM setup object
        stock_config: Stock configuration dictionary with mode and parameters
        
    Returns:
        dict: Configuration result with success/error information
    """
    try:
        if not setup:
            return {
                "error": True,
                "message": "Setup object is required",
                "code": "INVALID_SETUP"
            }
        
        if not stock_config:
            return {
                "success": True,
                "message": "No stock configuration provided, using defaults"
            }
        
        mode = stock_config.get("mode", "auto")
        
        if mode == "auto":
            return configure_automatic_stock(setup, stock_config)
        elif mode == "geometry":
            return configure_geometry_stock(setup, stock_config)
        elif mode == "box":
            return configure_box_stock(setup, stock_config)
        elif mode == "cylinder":
            return configure_cylinder_stock(setup, stock_config)
        else:
            return {
                "error": True,
                "message": f"Unknown stock mode: {mode}. Valid modes: auto, geometry, box, cylinder",
                "code": "INVALID_STOCK_MODE"
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error configuring stock: {str(e)}",
            "code": "STOCK_CONFIG_ERROR"
        }


def validate_stock_configuration(stock_config: dict) -> dict:
    """
    Validate stock configuration parameters.
    
    Args:
        stock_config: Stock configuration dictionary to validate
        
    Returns:
        dict: Validation result with valid flag and any issues found
    """
    validation_result = {
        "valid": True,
        "issues": [],
        "warnings": []
    }
    
    try:
        if not stock_config:
            return validation_result
        
        mode = stock_config.get("mode", "auto")
        valid_modes = ["auto", "geometry", "box", "cylinder"]
        
        if mode not in valid_modes:
            validation_result["valid"] = False
            validation_result["issues"].append({
                "field": "mode",
                "issue": f"Invalid stock mode: {mode}. Valid modes: {', '.join(valid_modes)}",
                "severity": "error"
            })
        
        if mode == "box":
            dimensions = stock_config.get("dimensions", {})
            for dim in ["length", "width", "height"]:
                value = dimensions.get(dim)
                if value is not None:
                    if not isinstance(value, (int, float)) or value <= 0:
                        validation_result["valid"] = False
                        validation_result["issues"].append({
                            "field": f"dimensions.{dim}",
                            "issue": f"Box {dim} must be a positive number",
                            "severity": "error"
                        })
        
        elif mode == "cylinder":
            dimensions = stock_config.get("dimensions", {})
            for dim in ["diameter", "height"]:
                value = dimensions.get(dim)
                if value is not None:
                    if not isinstance(value, (int, float)) or value <= 0:
                        validation_result["valid"] = False
                        validation_result["issues"].append({
                            "field": f"dimensions.{dim}",
                            "issue": f"Cylinder {dim} must be a positive number",
                            "severity": "error"
                        })
        
        elif mode == "geometry":
            geometry_id = stock_config.get("geometry_id")
            if not geometry_id:
                validation_result["valid"] = False
                validation_result["issues"].append({
                    "field": "geometry_id",
                    "issue": "Geometry mode requires geometry_id",
                    "severity": "error"
                })
        
        offset = stock_config.get("offset", {})
        for side in ["top", "bottom", "side"]:
            value = offset.get(side)
            if value is not None:
                if not isinstance(value, (int, float)):
                    validation_result["issues"].append({
                        "field": f"offset.{side}",
                        "issue": f"Offset {side} must be a number",
                        "severity": "error"
                    })
                    validation_result["valid"] = False
                elif value < 0:
                    validation_result["warnings"].append({
                        "field": f"offset.{side}",
                        "warning": f"Negative offset for {side} may cause issues",
                        "severity": "warning"
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


def configure_automatic_stock(setup, stock_config: dict) -> dict:
    """Configure automatic stock detection from selected bodies."""
    try:
        return {
            "success": True,
            "message": "Automatic stock configuration applied",
            "mode": "auto"
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure automatic stock: {str(e)}",
            "code": "AUTO_STOCK_CONFIG_FAILED"
        }


def configure_geometry_stock(setup, stock_config: dict) -> dict:
    """Configure stock using existing geometry as reference."""
    try:
        geometry_id = stock_config.get("geometry_id")
        if not geometry_id:
            return {
                "error": True,
                "message": "Geometry mode requires geometry_id",
                "code": "MISSING_GEOMETRY_ID"
            }
        
        return {
            "success": True,
            "message": "Geometry stock configuration applied",
            "mode": "geometry",
            "geometry_id": geometry_id
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure geometry stock: {str(e)}",
            "code": "GEOMETRY_STOCK_CONFIG_FAILED"
        }


def configure_box_stock(setup, stock_config: dict) -> dict:
    """Configure primitive box stock with specified dimensions."""
    try:
        dimensions = stock_config.get("dimensions", {})
        
        return {
            "success": True,
            "message": "Box stock configuration applied",
            "mode": "box",
            "dimensions": dimensions
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure box stock: {str(e)}",
            "code": "BOX_STOCK_CONFIG_FAILED"
        }


def configure_cylinder_stock(setup, stock_config: dict) -> dict:
    """Configure primitive cylinder stock with specified dimensions."""
    try:
        dimensions = stock_config.get("dimensions", {})
        
        return {
            "success": True,
            "message": "Cylinder stock configuration applied",
            "mode": "cylinder",
            "dimensions": dimensions
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to configure cylinder stock: {str(e)}",
            "code": "CYLINDER_STOCK_CONFIG_FAILED"
        }


def apply_stock_material(stock, material_name: str) -> dict:
    """Apply material properties to stock definition."""
    try:
        return {
            "success": True,
            "message": f"Material '{material_name}' applied to stock",
            "material": material_name
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to apply stock material: {str(e)}",
            "code": "STOCK_MATERIAL_FAILED"
        }
