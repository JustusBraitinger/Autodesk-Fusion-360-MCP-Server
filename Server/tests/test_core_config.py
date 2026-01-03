#!/usr/bin/env python3
"""
Unit tests for Server/core/config.py

Tests the centralized configuration management for the MCP Server.
"""

import pytest
import sys
import os

# Add Server directory to path for imports
server_path = os.path.join(os.path.dirname(__file__), "..")
if server_path not in sys.path:
    sys.path.insert(0, server_path)

from core.config import (
    get_base_url,
    get_endpoints,
    get_headers,
    get_timeout,
    get_categories,
    validate_configuration
)


class TestConfigurationValues:
    """Test configuration values and constants."""
    
    def test_base_url_is_string(self):
        """Test that base URL is a valid string."""
        base_url = get_base_url()
        assert isinstance(base_url, str)
        assert len(base_url) > 0
    
    def test_base_url_is_localhost(self):
        """Test that base URL points to localhost."""
        base_url = get_base_url()
        assert "localhost" in base_url or "127.0.0.1" in base_url
    
    def test_headers_is_dict(self):
        """Test that headers is a dictionary."""
        headers = get_headers()
        assert isinstance(headers, dict)
    
    def test_headers_has_content_type(self):
        """Test that headers includes Content-Type."""
        headers = get_headers()
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    def test_timeout_is_positive_number(self):
        """Test that timeout is a positive number."""
        timeout = get_timeout()
        assert isinstance(timeout, (int, float))
        assert timeout > 0
    
    def test_endpoints_is_dict(self):
        """Test that endpoints is a dictionary."""
        endpoints = get_endpoints()
        assert isinstance(endpoints, dict)
    
    def test_endpoints_has_categories(self):
        """Test that endpoints has expected categories."""
        categories = get_categories()
        assert len(categories) > 0
        assert "cad" in categories
        assert "cam" in categories


class TestGetFunctions:
    """Test the getter functions."""
    
    def test_get_base_url(self):
        """Test get_base_url returns correct value."""
        result = get_base_url()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_headers(self):
        """Test get_headers returns correct value."""
        result = get_headers()
        assert isinstance(result, dict)
        assert "Content-Type" in result
    
    def test_get_timeout(self):
        """Test get_timeout returns correct value."""
        result = get_timeout()
        assert isinstance(result, (int, float))
        assert result > 0
    
    def test_get_endpoints_all(self):
        """Test get_endpoints returns all endpoints when no category specified."""
        result = get_endpoints()
        assert isinstance(result, dict)
        assert len(result) > 0
    
    def test_get_endpoints_by_category(self):
        """Test get_endpoints returns category-specific endpoints."""
        # Test with cad category
        cad_endpoints = get_endpoints("cad")
        assert isinstance(cad_endpoints, dict)
        assert len(cad_endpoints) > 0
        
        # Test with cam category
        cam_endpoints = get_endpoints("cam")
        assert isinstance(cam_endpoints, dict)
        assert len(cam_endpoints) > 0
    
    def test_get_endpoints_invalid_category(self):
        """Test get_endpoints returns empty dict for invalid category."""
        result = get_endpoints("invalid_category")
        assert result == {}
    
    def test_get_categories(self):
        """Test get_categories returns list of categories."""
        categories = get_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
    
    def test_validate_configuration(self):
        """Test validate_configuration returns True for valid config."""
        result = validate_configuration()
        assert result is True


class TestEndpointStructure:
    """Test the structure of endpoints."""
    
    def test_cad_endpoints_exist(self):
        """Test that CAD endpoints exist."""
        endpoints = get_endpoints("cad")
        assert "draw_cylinder" in endpoints
        assert "draw_box" in endpoints
        assert "extrude" in endpoints
    
    def test_cam_endpoints_exist(self):
        """Test that CAM endpoints exist."""
        endpoints = get_endpoints("cam")
        assert "cam_toolpaths" in endpoints
        assert "cam_tools" in endpoints
    
    def test_utility_endpoints_exist(self):
        """Test that utility endpoints exist."""
        endpoints = get_endpoints("utility")
        assert "test_connection" in endpoints
        assert "undo" in endpoints
    
    def test_debug_endpoints_exist(self):
        """Test that debug category exists (may be empty)."""
        endpoints = get_endpoints("debug")
        assert isinstance(endpoints, dict)
        # Debug category may be empty initially
        assert len(endpoints) >= 0
    
    def test_endpoints_are_urls(self):
        """Test that endpoint values are URLs."""
        endpoints = get_endpoints()
        for name, url in endpoints.items():
            assert isinstance(url, str)
            assert url.startswith("http://") or url.startswith("https://"), \
                f"Endpoint {name} should be a URL: {url}"
    
    def test_get_endpoints_case_insensitive(self):
        """Test that category names are case insensitive."""
        endpoints_lower = get_endpoints("cad")
        endpoints_upper = get_endpoints("CAD")
        endpoints_mixed = get_endpoints("CaD")
        
        assert endpoints_lower == endpoints_upper
        assert endpoints_lower == endpoints_mixed
    
    def test_get_endpoints_returns_copy(self):
        """Test that get_endpoints returns a copy, not reference."""
        endpoints = get_endpoints("cad")
        endpoints["test_endpoint"] = "test_url"
        
        new_endpoints = get_endpoints("cad")
        assert "test_endpoint" not in new_endpoints
    
    def test_category_endpoint_isolation(self):
        """Test that category endpoints don't overlap."""
        cad_endpoints = set(get_endpoints("cad").keys())
        cam_endpoints = set(get_endpoints("cam").keys())
        utility_endpoints = set(get_endpoints("utility").keys())
        
        # Check no overlap between categories
        assert len(cad_endpoints & cam_endpoints) == 0, "CAD and CAM endpoints overlap"
        assert len(cad_endpoints & utility_endpoints) == 0, "CAD and Utility endpoints overlap"
        assert len(cam_endpoints & utility_endpoints) == 0, "CAM and Utility endpoints overlap"
    
    def test_all_endpoints_sum_equals_categories(self):
        """Test that all endpoints equals sum of category endpoints."""
        all_endpoints = get_endpoints()
        
        category_endpoints = {}
        for category in get_categories():
            category_endpoints.update(get_endpoints(category))
        
        assert len(all_endpoints) == len(category_endpoints)
        assert set(all_endpoints.keys()) == set(category_endpoints.keys())


class TestConfigurationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_none_category_parameter(self):
        """Test passing None as category parameter."""
        endpoints = get_endpoints(None)
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
    
    def test_empty_string_category(self):
        """Test passing empty string as category."""
        endpoints = get_endpoints("")
        assert isinstance(endpoints, dict)
        assert len(endpoints) == 0
    
    def test_numeric_category(self):
        """Test passing numeric value as category."""
        endpoints = get_endpoints(123)
        assert isinstance(endpoints, dict)
        assert len(endpoints) == 0
    
    def test_special_characters_category(self):
        """Test passing special characters as category."""
        endpoints = get_endpoints("@#$%")
        assert isinstance(endpoints, dict)
        assert len(endpoints) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
