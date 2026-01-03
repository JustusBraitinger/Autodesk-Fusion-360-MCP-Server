# HTTP Request Router
# Routes HTTP requests to appropriate handler modules based on path patterns

import re
import json
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .error_handling import error_handler, ErrorCategory, ErrorSeverity, handle_request_error

# Set up module-specific logging
module_logger = error_handler.get_module_logger("core.router")

class HttpMethod(Enum):
    """Supported HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

@dataclass
class RouteInfo:
    """Information about a registered route"""
    pattern: str
    handler: Callable
    methods: List[HttpMethod]
    category: str
    module_name: str
    compiled_pattern: re.Pattern

class RequestRouter:
    """
    HTTP request routing system that routes requests to appropriate handler modules
    based on path patterns with method-specific routing and error handling.
    """
    
    def __init__(self):
        """Initialize the request router"""
        self.routes: List[RouteInfo] = []
        self.error_handlers: Dict[int, Callable] = {}
        self.middleware: List[Callable] = []
        self.stats = {
            'requests_routed': 0,
            'requests_failed': 0,
            'routes_registered': 0
        }
    
    def register_handler(self, pattern: str, handler: Callable, methods: List[str] = None,
                        category: str = "system", module_name: str = "unknown") -> None:
        """
        Register a path pattern handler with enhanced error handling
        
        Args:
            pattern: URL pattern (can include {param} placeholders)
            handler: Function to handle matching requests
            methods: List of HTTP methods this handler supports
            category: Category of the handler (design, manufacture, etc.)
            module_name: Name of the module registering the handler
        """
        try:
            if methods is None:
                methods = ["GET", "POST"]
            
            # Convert string methods to HttpMethod enums
            http_methods = []
            for method in methods:
                try:
                    http_methods.append(HttpMethod(method.upper()))
                except ValueError:
                    module_logger.warning(f"Invalid HTTP method: {method}")
            
            # Convert pattern to regex
            # Replace {param} with named capture groups
            regex_pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', pattern)
            regex_pattern = f"^{regex_pattern}$"
            
            try:
                compiled_pattern = re.compile(regex_pattern)
            except re.error as e:
                error_response = error_handler.handle_error(
                    error=e,
                    module_name="core.router",
                    function_name="register_handler",
                    category=ErrorCategory.CONFIGURATION,
                    severity=ErrorSeverity.HIGH,
                    additional_info={"pattern": pattern, "module": module_name}
                )
                module_logger.error(f"Invalid pattern: {pattern} - {error_response.message}")
                return
            
            route_info = RouteInfo(
                pattern=pattern,
                handler=handler,
                methods=http_methods,
                category=category,
                module_name=module_name,
                compiled_pattern=compiled_pattern
            )
            
            self.routes.append(route_info)
            self.stats['routes_registered'] += 1
            
            module_logger.debug(f"Registered route: {pattern} -> {module_name}.{handler.__name__} [{', '.join(methods)}]")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.router",
                function_name="register_handler",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                additional_info={"pattern": pattern, "module": module_name}
            )
            module_logger.error(f"Handler registration failed: {error_response.message}")
    
    def register_error_handler(self, status_code: int, handler: Callable) -> None:
        """
        Register an error handler for a specific HTTP status code
        
        Args:
            status_code: HTTP status code (e.g., 404, 500)
            handler: Function to handle the error
        """
        try:
            self.error_handlers[status_code] = handler
            module_logger.debug(f"Registered error handler for status code: {status_code}")
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.router",
                function_name="register_error_handler",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.MEDIUM
            )
            module_logger.error(f"Error handler registration failed: {error_response.message}")
    
    def add_middleware(self, middleware: Callable) -> None:
        """
        Add middleware function to be called before routing
        
        Args:
            middleware: Function that takes (path, method, data) and returns modified data or None to abort
        """
        try:
            self.middleware.append(middleware)
            module_logger.debug(f"Added middleware: {middleware.__name__}")
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.router",
                function_name="add_middleware",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.MEDIUM
            )
            module_logger.error(f"Middleware registration failed: {error_response.message}")
    
    def route_request(self, path: str, method: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route an HTTP request to the appropriate handler with comprehensive error handling
        
        Args:
            path: Request path
            method: HTTP method
            data: Request data (for POST/PUT requests)
            
        Returns:
            Response dictionary with status, data, and headers
        """
        if data is None:
            data = {}
        
        try:
            # Convert method to enum
            try:
                http_method = HttpMethod(method.upper())
            except ValueError:
                return self._create_error_response(405, f"Method not allowed: {method}")
            
            # Apply middleware with error handling
            for middleware_func in self.middleware:
                try:
                    result = middleware_func(path, method, data)
                    if result is None:
                        return self._create_error_response(403, "Request blocked by middleware")
                    data = result
                except Exception as e:
                    error_response = error_handler.handle_error(
                        error=e,
                        module_name="core.router",
                        function_name="route_request",
                        category=ErrorCategory.REQUEST_HANDLING,
                        severity=ErrorSeverity.MEDIUM,
                        request_path=path,
                        additional_info={"middleware": middleware_func.__name__}
                    )
                    module_logger.error(f"Middleware error: {error_response.message}")
                    return self._create_error_response(500, "Middleware error")
            
            # Validate request before routing
            try:
                from .validation import request_validator, ValidationError
                validated_data = request_validator.validate_request(path, method, data)
                data = validated_data
            except ValidationError as e:
                module_logger.warning(f"Request validation failed for {method} {path}: {e.message}")
                return self._create_error_response(400, e.message)
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    module_name="core.router",
                    function_name="route_request",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    request_path=path
                )
                module_logger.error(f"Validation error: {error_response.message}")
                return self._create_error_response(500, "Validation error")
            
            # Find matching route
            route_info, path_params = self._find_matching_route(path, http_method)
            
            if not route_info:
                self.stats['requests_failed'] += 1
                return self._create_error_response(404, f"No route found for: {method} {path}")
            
            # Execute handler with error isolation
            try:
                # Merge path parameters with request data
                if path_params:
                    data.update(path_params)
                
                result = route_info.handler(path, method, data)
                
                # Ensure result is a proper response dictionary
                if not isinstance(result, dict):
                    result = {"data": result}
                
                # Add default response fields if missing
                if "status" not in result:
                    result["status"] = 200
                if "headers" not in result:
                    result["headers"] = {"Content-Type": "application/json"}
                
                self.stats['requests_routed'] += 1
                module_logger.debug(f"Successfully routed: {method} {path} -> {route_info.module_name}")
                
                return result
                
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    module_name=route_info.module_name,
                    function_name=route_info.handler.__name__,
                    category=ErrorCategory.REQUEST_HANDLING,
                    severity=ErrorSeverity.HIGH,
                    request_path=path,
                    user_data=data
                )
                module_logger.error(f"Handler error for {method} {path}: {error_response.message}")
                self.stats['requests_failed'] += 1
                
                # Return detailed error response
                return {
                    "status": 500,
                    "error": True,
                    "message": error_response.message,
                    "code": error_response.code,
                    "module_context": error_response.module_context,
                    "details": error_response.details,
                    "recovery_suggestions": error_response.recovery_suggestions,
                    "headers": {"Content-Type": "application/json"}
                }
        
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.router",
                function_name="route_request",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                request_path=path,
                user_data=data
            )
            module_logger.critical(f"Router error: {error_response.message}")
            self.stats['requests_failed'] += 1
            return self._create_error_response(500, f"Router error: {error_response.message}")
    
    def _find_matching_route(self, path: str, method: HttpMethod) -> Tuple[Optional[RouteInfo], Dict[str, str]]:
        """
        Find a route that matches the given path and method
        
        Args:
            path: Request path
            method: HTTP method
            
        Returns:
            Tuple of (RouteInfo, path_parameters) or (None, {}) if no match
        """
        for route_info in self.routes:
            # Check if method is supported
            if method not in route_info.methods:
                continue
            
            # Check if pattern matches
            match = route_info.compiled_pattern.match(path)
            if match:
                path_params = match.groupdict()
                return route_info, path_params
        
        return None, {}
    
    def _create_error_response(self, status_code: int, message: str) -> Dict[str, Any]:
        """
        Create a standardized error response
        
        Args:
            status_code: HTTP status code
            message: Error message
            
        Returns:
            Error response dictionary
        """
        # Check if custom error handler exists
        if status_code in self.error_handlers:
            try:
                return self.error_handlers[status_code](status_code, message)
            except Exception as e:
                logger.error(f"Error handler failed: {str(e)}")
        
        # Default error response
        return {
            "status": status_code,
            "error": True,
            "message": message,
            "headers": {"Content-Type": "application/json"}
        }
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """
        Get all registered routes
        
        Returns:
            List of route information dictionaries
        """
        routes = []
        for route_info in self.routes:
            routes.append({
                "pattern": route_info.pattern,
                "methods": [method.value for method in route_info.methods],
                "category": route_info.category,
                "module_name": route_info.module_name,
                "handler_name": route_info.handler.__name__
            })
        return routes
    
    def get_routes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get routes filtered by category
        
        Args:
            category: Category to filter by
            
        Returns:
            List of route information dictionaries for the category
        """
        routes = []
        for route_info in self.routes:
            if route_info.category == category:
                routes.append({
                    "pattern": route_info.pattern,
                    "methods": [method.value for method in route_info.methods],
                    "category": route_info.category,
                    "module_name": route_info.module_name,
                    "handler_name": route_info.handler.__name__
                })
        return routes
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get router statistics
        
        Returns:
            Dictionary with router statistics
        """
        return self.stats.copy()
    
    def validate_routes(self) -> List[str]:
        """
        Validate all registered routes and return any issues
        
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for duplicate patterns with same methods
        pattern_methods = {}
        for route_info in self.routes:
            key = (route_info.pattern, tuple(sorted([m.value for m in route_info.methods])))
            if key in pattern_methods:
                issues.append(f"Duplicate route: {route_info.pattern} with methods {[m.value for m in route_info.methods]}")
            else:
                pattern_methods[key] = route_info
        
        # Check for invalid patterns
        for route_info in self.routes:
            try:
                # Test pattern compilation
                test_pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', route_info.pattern)
                re.compile(f"^{test_pattern}$")
            except re.error:
                issues.append(f"Invalid regex pattern: {route_info.pattern}")
        
        return issues

# Global request router instance
request_router = RequestRouter()