#!/usr/bin/env python3
"""
Unit tests for FusionMCPBridge/core/router.py

Tests the HTTP request routing system for the Fusion 360 Add-In.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure FusionMCPBridge is at the front of sys.path
bridge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if bridge_path not in sys.path:
    sys.path.insert(0, bridge_path)

from core.router import (
    RequestRouter,
    RouteInfo,
    HttpMethod,
    request_router
)


class TestHttpMethod:
    """Test HttpMethod enum."""
    
    def test_http_methods_exist(self):
        """Test that all expected HTTP methods exist."""
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.DELETE.value == "DELETE"


class TestRequestRouter:
    """Test cases for the RequestRouter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = RequestRouter()
        
        # Create mock handler
        def mock_handler(path, method, data):
            return {"status": 200, "data": {"message": "success"}}
        
        self.mock_handler = mock_handler
    
    def test_initialization(self):
        """Test RequestRouter initialization."""
        assert self.router is not None
        assert self.router.routes == []
        assert self.router.error_handlers == {}
        assert self.router.middleware == []
        assert self.router.stats['requests_routed'] == 0
        assert self.router.stats['requests_failed'] == 0
        assert self.router.stats['routes_registered'] == 0
    
    def test_register_handler_basic(self):
        """Test basic handler registration."""
        self.router.register_handler(
            pattern="/test",
            handler=self.mock_handler,
            methods=["GET"],
            category="test",
            module_name="test_module"
        )
        
        assert len(self.router.routes) == 1
        assert self.router.stats['routes_registered'] == 1
    
    def test_register_handler_with_parameters(self):
        """Test handler registration with URL parameters."""
        self.router.register_handler(
            pattern="/test/{id}",
            handler=self.mock_handler,
            methods=["GET", "POST"],
            category="test",
            module_name="test_module"
        )
        
        assert len(self.router.routes) == 1
        route = self.router.routes[0]
        assert route.pattern == "/test/{id}"
    
    def test_register_handler_default_methods(self):
        """Test handler registration with default methods."""
        self.router.register_handler(
            pattern="/test",
            handler=self.mock_handler,
            category="test",
            module_name="test_module"
        )
        
        route = self.router.routes[0]
        assert HttpMethod.GET in route.methods
        assert HttpMethod.POST in route.methods
    
    def test_register_error_handler(self):
        """Test error handler registration."""
        def error_handler(status_code, message):
            return {"status": status_code, "error": True, "message": message}
        
        self.router.register_error_handler(404, error_handler)
        
        assert 404 in self.router.error_handlers
        assert self.router.error_handlers[404] == error_handler
    
    def test_add_middleware(self):
        """Test middleware registration."""
        def middleware(path, method, data):
            return data
        
        self.router.add_middleware(middleware)
        
        assert len(self.router.middleware) == 1
        assert self.router.middleware[0] == middleware
    
    def test_route_request_success(self):
        """Test successful request routing."""
        # Create a fresh router for this test
        router = RequestRouter()
        
        def mock_handler(path, method, data):
            return {"status": 200, "data": {"message": "success"}}
        
        router.register_handler(
            pattern="/test",
            handler=mock_handler,
            methods=["GET"],
            category="test",
            module_name="test_module"
        )
        
        # The router internally validates, so we test the full flow
        response = router.route_request("/test", "GET", {})
        
        assert response["status"] == 200
        assert router.stats['requests_routed'] == 1
    
    def test_route_request_not_found(self):
        """Test routing to non-existent route."""
        # Create a fresh router for this test
        router = RequestRouter()
        
        response = router.route_request("/nonexistent", "GET", {})
        
        assert response["status"] == 404
        assert response["error"] is True
        assert router.stats['requests_failed'] == 1
    
    def test_route_request_invalid_method(self):
        """Test routing with invalid HTTP method."""
        response = self.router.route_request("/test", "INVALID", {})
        
        assert response["status"] == 405
        assert response["error"] is True
    
    def test_route_request_with_path_params(self):
        """Test routing with path parameters."""
        # Create a fresh router for this test
        router = RequestRouter()
        
        def handler_with_params(path, method, data):
            return {"status": 200, "data": {"id": data.get("id")}}
        
        router.register_handler(
            pattern="/test/{id}",
            handler=handler_with_params,
            methods=["GET"],
            category="test",
            module_name="test_module"
        )
        
        response = router.route_request("/test/123", "GET", {})
        
        assert response["status"] == 200
        assert response["data"]["id"] == "123"
    
    def test_get_routes(self):
        """Test getting all registered routes."""
        self.router.register_handler(
            pattern="/test1",
            handler=self.mock_handler,
            methods=["GET"],
            category="test",
            module_name="test_module"
        )
        self.router.register_handler(
            pattern="/test2",
            handler=self.mock_handler,
            methods=["POST"],
            category="test",
            module_name="test_module"
        )
        
        routes = self.router.get_routes()
        
        assert len(routes) == 2
        assert routes[0]["pattern"] == "/test1"
        assert routes[1]["pattern"] == "/test2"
    
    def test_get_routes_by_category(self):
        """Test getting routes filtered by category."""
        self.router.register_handler(
            pattern="/design/test",
            handler=self.mock_handler,
            methods=["GET"],
            category="design",
            module_name="design_module"
        )
        self.router.register_handler(
            pattern="/manufacture/test",
            handler=self.mock_handler,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture_module"
        )
        
        design_routes = self.router.get_routes_by_category("design")
        manufacture_routes = self.router.get_routes_by_category("manufacture")
        
        assert len(design_routes) == 1
        assert len(manufacture_routes) == 1
        assert design_routes[0]["category"] == "design"
        assert manufacture_routes[0]["category"] == "manufacture"
    
    def test_get_stats(self):
        """Test getting router statistics."""
        stats = self.router.get_stats()
        
        assert isinstance(stats, dict)
        assert "requests_routed" in stats
        assert "requests_failed" in stats
        assert "routes_registered" in stats
    
    def test_validate_routes_no_issues(self):
        """Test route validation with no issues."""
        self.router.register_handler(
            pattern="/test1",
            handler=self.mock_handler,
            methods=["GET"],
            category="test",
            module_name="test_module"
        )
        
        issues = self.router.validate_routes()
        
        assert len(issues) == 0
    
    def test_validate_routes_duplicate_pattern(self):
        """Test route validation detects duplicate patterns."""
        self.router.register_handler(
            pattern="/test",
            handler=self.mock_handler,
            methods=["GET"],
            category="test",
            module_name="test_module"
        )
        self.router.register_handler(
            pattern="/test",
            handler=self.mock_handler,
            methods=["GET"],
            category="test",
            module_name="test_module2"
        )
        
        issues = self.router.validate_routes()
        
        assert len(issues) > 0
        assert any("Duplicate" in issue for issue in issues)


class TestGlobalRequestRouter:
    """Test the global request_router instance."""
    
    def test_global_instance_exists(self):
        """Test that global request_router instance exists."""
        assert request_router is not None
        assert isinstance(request_router, RequestRouter)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
