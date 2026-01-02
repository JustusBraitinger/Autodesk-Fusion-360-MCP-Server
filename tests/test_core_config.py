#!/usr/bin/env python3
"""
Unit tests for Server/core/config.py

Tests the centralized configuration management system including
category-based endpoint organization and configuration validation.

Requirements: 7.1, 7.2, 7.4
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add Server directory to path for imports
server_path = os.path.join(os.path.dirname(__file__), "..", "Server")
if server_path not in sys.path:
    sys.path.insert(0, server_path)

from core import config


class TestConfigurationManager:
    """Test cases for the configuration manager."""
    
    def test_get_base_url(self):
        """Test that base URL is returned correctly."""
        base_url = config.get_base_url()
        assert base_url == "http://localhost:5001"
        assert isinstance(base_url, str)
        assert base_url.startswith("http")
    
    def test_get_headers(self):
        """Test that headers are returned correctly."""
        headers = config.get_headers()
        assert isinstance(headers, dict)
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        
        # Test that returned headers are a copy (not reference)
        headers["test"] = "value"
        new_headers = config.get_headers()
        assert "test" not in new_headers
    
    def test_get_timeout(self):
        """Test that timeout is returned correctly."""
        timeout = config.get_timeout()
        assert isinstance(timeout, int)
        assert timeout > 0
        assert timeout == 30
    
    def test_get_endpoints_all_categories(self):
        """Test getting all endpoints without category filter."""
        endpoints = config.get_endpoints()
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
        
        # Check that endpoints from all categories are included
        assert "draw_cylinder" in endpoints  # CAD
        assert "cam_toolpaths" in endpoints  # CAM
        assert "test_connection" in endpoints  # Utility
        
        # Verify all URLs are properly formatted
        for endpoint_name, url in endpoints.items():
            assert isinstance(url, str)
            assert url.startswith("http://localhost:5001")
    
    def test_get_endpoints_cad_category(self):
        """Test getting CAD category endpoints."""
        endpoints = config.get_endpoints("cad")
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
        
        # Check specific CAD endpoints
        expected_cad_endpoints = [
            "draw_cylinder", "draw_box", "draw_sphere",
            "draw2Dcircle", "extrude", "fillet_edges"
        ]
        for endpoint in expected_cad_endpoints:
            assert endpoint in endpoints
            
        # Ensure no CAM endpoints are included
        assert "cam_toolpaths" not in endpoints
        assert "cam_tools" not in endpoints
    
    def test_get_endpoints_cam_category(self):
        """Test getting CAM category endpoints."""
        endpoints = config.get_endpoints("cam")
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
        
        # Check specific CAM endpoints
        expected_cam_endpoints = [
            "cam_toolpaths", "cam_tools", "tool_libraries",
            "cam_toolpath_heights", "cam_toolpath_passes"
        ]
        for endpoint in expected_cam_endpoints:
            assert endpoint in endpoints
            
        # Ensure no CAD endpoints are included
        assert "draw_cylinder" not in endpoints
        assert "extrude" not in endpoints
    
    def test_get_endpoints_utility_category(self):
        """Test getting utility category endpoints."""
        endpoints = config.get_endpoints("utility")
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
        
        # Check specific utility endpoints
        expected_utility_endpoints = [
            "test_connection", "undo", "export_step", "export_stl"
        ]
        for endpoint in expected_utility_endpoints:
            assert endpoint in endpoints
    
    def test_get_endpoints_debug_category(self):
        """Test getting debug category endpoints."""
        endpoints = config.get_endpoints("debug")
        assert isinstance(endpoints, dict)
        # Debug category may be empty initially
        assert len(endpoints) >= 0
    
    def test_get_endpoints_case_insensitive(self):
        """Test that category names are case insensitive."""
        endpoints_lower = config.get_endpoints("cad")
        endpoints_upper = config.get_endpoints("CAD")
        endpoints_mixed = config.get_endpoints("CaD")
        
        assert endpoints_lower == endpoints_upper
        assert endpoints_lower == endpoints_mixed
    
    def test_get_endpoints_unknown_category(self):
        """Test handling of unknown category."""
        endpoints = config.get_endpoints("unknown_category")
        assert isinstance(endpoints, dict)
        assert len(endpoints) == 0
    
    def test_get_endpoints_returns_copy(self):
        """Test that get_endpoints returns a copy, not reference."""
        endpoints = config.get_endpoints("cad")
        endpoints["test_endpoint"] = "test_url"
        
        new_endpoints = config.get_endpoints("cad")
        assert "test_endpoint" not in new_endpoints
    
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        result = config.validate_configuration()
        assert result is True
    
    @patch('core.config._BASE_URL', '')
    def test_validate_configuration_empty_base_url(self):
        """Test validation failure with empty base URL."""
        result = config.validate_configuration()
        assert result is False
    
    @patch('core.config._REQUEST_TIMEOUT', 0)
    def test_validate_configuration_invalid_timeout(self):
        """Test validation failure with invalid timeout."""
        result = config.validate_configuration()
        assert result is False
    
    @patch('core.config._REQUEST_TIMEOUT', -5)
    def test_validate_configuration_negative_timeout(self):
        """Test validation failure with negative timeout."""
        result = config.validate_configuration()
        assert result is False
    
    @patch('core.config._HEADERS', {})
    def test_validate_configuration_empty_headers(self):
        """Test validation failure with empty headers."""
        result = config.validate_configuration()
        assert result is False
    
    @patch('core.config._ENDPOINTS', {"cad": "not_a_dict"})
    def test_validate_configuration_invalid_endpoints_structure(self):
        """Test validation failure with invalid endpoints structure."""
        result = config.validate_configuration()
        assert result is False
    
    def test_get_categories(self):
        """Test getting list of available categories."""
        categories = config.get_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        
        expected_categories = ["cad", "cam", "utility", "debug"]
        for category in expected_categories:
            assert category in categories
    
    def test_endpoint_url_consistency(self):
        """Test that all endpoint URLs are consistent with base URL."""
        base_url = config.get_base_url()
        all_endpoints = config.get_endpoints()
        
        for endpoint_name, url in all_endpoints.items():
            assert url.startswith(base_url), f"Endpoint {endpoint_name} URL doesn't start with base URL"
    
    def test_category_endpoint_isolation(self):
        """Test that category endpoints don't overlap."""
        cad_endpoints = set(config.get_endpoints("cad").keys())
        cam_endpoints = set(config.get_endpoints("cam").keys())
        utility_endpoints = set(config.get_endpoints("utility").keys())
        debug_endpoints = set(config.get_endpoints("debug").keys())
        
        # Check no overlap between categories
        assert len(cad_endpoints & cam_endpoints) == 0, "CAD and CAM endpoints overlap"
        assert len(cad_endpoints & utility_endpoints) == 0, "CAD and Utility endpoints overlap"
        assert len(cam_endpoints & utility_endpoints) == 0, "CAM and Utility endpoints overlap"
    
    def test_all_endpoints_sum_equals_categories(self):
        """Test that all endpoints equals sum of category endpoints."""
        all_endpoints = config.get_endpoints()
        
        category_endpoints = {}
        for category in config.get_categories():
            category_endpoints.update(config.get_endpoints(category))
        
        assert len(all_endpoints) == len(category_endpoints)
        assert set(all_endpoints.keys()) == set(category_endpoints.keys())


class TestConfigurationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_none_category_parameter(self):
        """Test passing None as category parameter."""
        endpoints = config.get_endpoints(None)
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
    
    def test_empty_string_category(self):
        """Test passing empty string as category."""
        endpoints = config.get_endpoints("")
        assert isinstance(endpoints, dict)
        assert len(endpoints) == 0
    
    def test_numeric_category(self):
        """Test passing numeric value as category."""
        endpoints = config.get_endpoints(123)
        assert isinstance(endpoints, dict)
        assert len(endpoints) == 0
    
    def test_special_characters_category(self):
        """Test passing special characters as category."""
        endpoints = config.get_endpoints("@#$%")
        assert isinstance(endpoints, dict)
        assert len(endpoints) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])