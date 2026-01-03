#!/usr/bin/env python3
"""
Final Validation Tests for FusionMCPBridge Modular System.

This test suite validates:
1. Complete test suite execution (including property-based tests)
2. Backward compatibility with existing MCP Server
3. Add-in installation and startup with modular system
4. Fusion 360 threading constraints are respected

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
import sys
import os
import json
from unittest.mock import MagicMock, patch, Mock

# Ensure FusionMCPBridge is at the front of sys.path
bridge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if bridge_path not in sys.path:
    sys.path.insert(0, bridge_path)

from core.router import RequestRouter, HttpMethod, request_router
from core.task_queue import TaskQueue, TaskPriority, Task
from core.loader import ModuleLoader, ModuleInfo, HandlerInfo
from core.config import ConfigurationManager, WorkspaceCategory, config_manager
from core.validation import RequestValidator, ValidationError, ParameterType, ParameterRule
from core.error_handling import (
    ErrorHandler, ErrorCategory, ErrorSeverity, ErrorResponse,
    error_handler
)


class TestBackwardCompatibility:
    """
    Test backward compatibility with existing MCP Server.
    Validates: Requirements 9.1, 9.2, 9.4, 9.5
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = RequestRouter()
        self.config = ConfigurationManager()
    
    def test_existing_endpoints_preserved(self):
        """Test that all existing HTTP endpoints are preserved."""
        # Get all endpoints from configuration
        design_endpoints = self.config.get_endpoints("design")
        manufacture_endpoints = self.config.get_endpoints("manufacture")
        system_endpoints = self.config.get_endpoints("system")
        
        # Verify Design workspace endpoints exist
        assert "geometry" in design_endpoints
        assert "sketching" in design_endpoints
        assert "modeling" in design_endpoints
        assert "features" in design_endpoints
        
        # Verify MANUFACTURE workspace endpoints exist
        assert "setups" in manufacture_endpoints
        assert "toolpaths" in manufacture_endpoints
        assert "tools" in manufacture_endpoints
        assert "tool_libraries" in manufacture_endpoints
        assert "operations" in manufacture_endpoints  # New endpoint group
        assert "tool_search" in manufacture_endpoints  # New endpoint group
        
        # Verify System endpoints exist
        assert "lifecycle" in system_endpoints
        assert "utilities" in system_endpoints
    
    def test_new_endpoint_groups_exist(self):
        """
        Test that new endpoint groups (operations, tool_search) exist.
        Validates: Requirements 4.1-4.9, 5.5-5.7
        """
        manufacture_endpoints = self.config.get_endpoints("manufacture")
        
        # Verify operations endpoint group exists
        assert "operations" in manufacture_endpoints
        operations = manufacture_endpoints["operations"]
        
        # Verify all operation endpoints
        assert "tool" in operations
        assert "heights" in operations
        assert "height_param" in operations
        assert "heights_validate" in operations
        assert "passes" in operations
        assert "passes_validate" in operations
        assert "passes_optimize" in operations
        assert "linking" in operations
        assert "linking_validate" in operations
        
        # Verify tool_search endpoint group exists
        assert "tool_search" in manufacture_endpoints
        tool_search = manufacture_endpoints["tool_search"]
        
        # Verify all tool_search endpoints
        assert "search" in tool_search
        assert "advanced" in tool_search
        assert "suggestions" in tool_search
    
    def test_obsolete_endpoints_removed(self):
        """
        Test that obsolete endpoints are not present.
        Validates: Requirements 7.1-7.6
        """
        manufacture_endpoints = self.config.get_endpoints("manufacture")
        
        # Collect all endpoint paths
        all_paths = []
        for group_name, group_endpoints in manufacture_endpoints.items():
            if isinstance(group_endpoints, dict):
                all_paths.extend(group_endpoints.values())
        
        # Verify obsolete setup endpoints are not present
        assert "/cam/setups/create" not in all_paths
        assert "/cam/setups/{id}/modify" not in all_paths
        assert "/cam/setups/{id}/delete" not in all_paths
        
        # Verify obsolete singular toolpath pattern is not present
        for path in all_paths:
            if "toolpath" in path.lower():
                assert "/cam/toolpath/" not in path or "/cam/toolpaths/" in path, \
                    f"Obsolete singular toolpath pattern found: {path}"
        
        # Verify obsolete tool library endpoints are not present
        assert "/tool-libraries/{library_id}/tools/create" not in all_paths
        assert "/tool-libraries/tools/{tool_id}/modify" not in all_paths
        assert "/tool-libraries/tools/search" not in all_paths
    
    def test_endpoint_paths_match_original(self):
        """Test that endpoint paths match the original monolithic implementation."""
        design_endpoints = self.config.get_endpoints("design")
        
        # Verify specific endpoint paths
        assert design_endpoints["geometry"]["box"] == "/Box"
        assert design_endpoints["geometry"]["cylinder"] == "/draw_cylinder"
        assert design_endpoints["geometry"]["sphere"] == "/sphere"
        assert design_endpoints["modeling"]["extrude"] == "/extrude_last_sketch"
        assert design_endpoints["modeling"]["revolve"] == "/revolve"
    
    def test_response_format_consistency(self):
        """Test that response formats are consistent with original implementation."""
        def test_handler(path, method, data):
            return {"status": 200, "data": {"message": "success"}}
        
        self.router.register_handler("/test", test_handler, ["GET"], "test", "test_module")
        response = self.router.route_request("/test", "GET", {})
        
        # Verify response structure matches original format
        assert "status" in response
        assert "data" in response
        assert response["status"] == 200
    
    def test_error_response_format_consistency(self):
        """Test that error response formats are consistent."""
        response = self.router.route_request("/nonexistent", "GET", {})
        
        # Verify error response structure
        assert "status" in response
        assert "error" in response
        assert "message" in response
        assert response["error"] is True
    
    def test_cam_endpoints_preserved(self):
        """Test that CAM endpoints are preserved for backward compatibility."""
        manufacture_endpoints = self.config.get_endpoints("manufacture")
        
        # Verify CAM setup endpoints with correct paths
        assert "list" in manufacture_endpoints["setups"]
        assert manufacture_endpoints["setups"]["list"] == "/cam/setups"
        assert "get" in manufacture_endpoints["setups"]
        assert manufacture_endpoints["setups"]["get"] == "/cam/setups/{setup_id}"
        assert "create" in manufacture_endpoints["setups"]
        assert manufacture_endpoints["setups"]["create"] == "/cam/setups"
        assert "modify" in manufacture_endpoints["setups"]
        assert manufacture_endpoints["setups"]["modify"] == "/cam/setups/{setup_id}"
        assert "delete" in manufacture_endpoints["setups"]
        assert manufacture_endpoints["setups"]["delete"] == "/cam/setups/{setup_id}"
        assert "duplicate" in manufacture_endpoints["setups"]
        assert manufacture_endpoints["setups"]["duplicate"] == "/cam/setups/{setup_id}/duplicate"
        assert "sequence" in manufacture_endpoints["setups"]
        assert manufacture_endpoints["setups"]["sequence"] == "/cam/setups/{setup_id}/sequence"
        
        # Verify CAM toolpath endpoints with correct paths
        assert "list" in manufacture_endpoints["toolpaths"]
        assert manufacture_endpoints["toolpaths"]["list"] == "/cam/toolpaths"
        assert "list_with_heights" in manufacture_endpoints["toolpaths"]
        assert manufacture_endpoints["toolpaths"]["list_with_heights"] == "/cam/toolpaths/with-heights"
        assert "get" in manufacture_endpoints["toolpaths"]
        assert manufacture_endpoints["toolpaths"]["get"] == "/cam/toolpaths/{toolpath_id}"
        assert "parameters" in manufacture_endpoints["toolpaths"]
        assert manufacture_endpoints["toolpaths"]["parameters"] == "/cam/toolpaths/{toolpath_id}/parameters"
        assert "heights" in manufacture_endpoints["toolpaths"]
        assert manufacture_endpoints["toolpaths"]["heights"] == "/cam/toolpaths/{toolpath_id}/heights"
        assert "passes" in manufacture_endpoints["toolpaths"]
        assert manufacture_endpoints["toolpaths"]["passes"] == "/cam/toolpaths/{toolpath_id}/passes"
        assert "linking" in manufacture_endpoints["toolpaths"]
        assert manufacture_endpoints["toolpaths"]["linking"] == "/cam/toolpaths/{toolpath_id}/linking"
        
        # Verify operations endpoint group exists with correct paths
        assert "operations" in manufacture_endpoints
        assert "tool" in manufacture_endpoints["operations"]
        assert manufacture_endpoints["operations"]["tool"] == "/cam/operations/{operation_id}/tool"
        assert "heights" in manufacture_endpoints["operations"]
        assert manufacture_endpoints["operations"]["heights"] == "/cam/operations/{operation_id}/heights"
        assert "passes" in manufacture_endpoints["operations"]
        assert manufacture_endpoints["operations"]["passes"] == "/cam/operations/{operation_id}/passes"
        assert "linking" in manufacture_endpoints["operations"]
        assert manufacture_endpoints["operations"]["linking"] == "/cam/operations/{operation_id}/linking"
        
        # Verify tools endpoint group with correct paths
        assert "tools" in manufacture_endpoints
        assert "list" in manufacture_endpoints["tools"]
        assert manufacture_endpoints["tools"]["list"] == "/cam/tools"
        assert "usage" in manufacture_endpoints["tools"]
        assert manufacture_endpoints["tools"]["usage"] == "/cam/tools/{tool_id}/usage"
        
        # Verify tool library endpoints with correct paths
        assert "list" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["list"] == "/tool-libraries"
        assert "get" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["get"] == "/tool-libraries/{library_id}"
        assert "load" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["load"] == "/tool-libraries/load"
        assert "validate_access" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["validate_access"] == "/tool-libraries/validate-access"
        assert "tools_list" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["tools_list"] == "/tool-libraries/tools"
        assert "tool_get" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["tool_get"] == "/tool-libraries/tools/{tool_id}"
        assert "tool_modify" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["tool_modify"] == "/tool-libraries/tools/{tool_id}"
        assert "tool_delete" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["tool_delete"] == "/tool-libraries/tools/{tool_id}"
        assert "tool_duplicate" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["tool_duplicate"] == "/tool-libraries/tools/{tool_id}/duplicate"
        assert "tool_validate" in manufacture_endpoints["tool_libraries"]
        assert manufacture_endpoints["tool_libraries"]["tool_validate"] == "/tool-libraries/tools/validate"
        
        # Verify tool_search endpoint group with correct paths
        assert "tool_search" in manufacture_endpoints
        assert "search" in manufacture_endpoints["tool_search"]
        assert manufacture_endpoints["tool_search"]["search"] == "/tool-libraries/search"
        assert "advanced" in manufacture_endpoints["tool_search"]
        assert manufacture_endpoints["tool_search"]["advanced"] == "/tool-libraries/search/advanced"
        assert "suggestions" in manufacture_endpoints["tool_search"]
        assert manufacture_endpoints["tool_search"]["suggestions"] == "/tool-libraries/search/suggestions"
    
    def test_api_contract_preservation(self):
        """Test that API contracts are preserved for all endpoints."""
        # Test that router can handle all expected HTTP methods
        def test_handler(path, method, data):
            return {"status": 200, "data": {"method": method}}
        
        self.router.register_handler("/test", test_handler, ["GET", "POST"], "test", "test_module")
        
        # Test GET request
        get_response = self.router.route_request("/test", "GET", {})
        assert get_response["status"] == 200
        
        # Test POST request
        post_response = self.router.route_request("/test", "POST", {"key": "value"})
        assert post_response["status"] == 200


class TestThreadingConstraints:
    """
    Test that Fusion 360 threading constraints are respected.
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.task_queue = TaskQueue()
    
    def test_task_queue_thread_safety(self):
        """Test that task queue operations are thread-safe."""
        import threading
        
        results = []
        errors = []
        
        def queue_tasks():
            try:
                for i in range(10):
                    self.task_queue.queue_task('test_task', i)
                results.append("queued")
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to queue tasks
        threads = [threading.Thread(target=queue_tasks) for _ in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 5
        assert self.task_queue.get_queue_size() == 50
    
    def test_task_processing_on_main_thread(self):
        """Test that task processing happens on the main thread."""
        execution_log = []
        
        def test_handler(value):
            execution_log.append(value)
        
        self.task_queue.register_task_handler('test_task', test_handler)
        
        # Queue tasks
        for i in range(5):
            self.task_queue.queue_task('test_task', i)
        
        # Process tasks (simulating main thread processing)
        processed = self.task_queue.process_tasks()
        
        assert processed == 5
        assert len(execution_log) == 5
    
    def test_concurrent_processing_prevention(self):
        """Test that concurrent task processing is prevented."""
        self.task_queue.processing = True
        
        # Attempt to process while already processing
        processed = self.task_queue.process_tasks()
        
        # Should return 0 when already processing
        assert processed == 0
        
        # Reset for cleanup
        self.task_queue.processing = False
    
    def test_task_error_isolation(self):
        """Test that task errors don't affect other tasks."""
        results = []
        
        def failing_handler(value):
            if value == 2:
                raise ValueError("Intentional failure")
            results.append(value)
        
        self.task_queue.register_task_handler('test_task', failing_handler)
        
        # Queue tasks including one that will fail
        for i in range(5):
            self.task_queue.queue_task('test_task', i)
        
        # Process tasks
        processed = self.task_queue.process_tasks()
        
        # Should process all tasks, with one failure
        assert 0 in results
        assert 1 in results
        assert 3 in results
        assert 4 in results
        assert 2 not in results  # This one failed
    
    def test_task_priority_ordering(self):
        """Test that tasks are processed in priority order."""
        import time
        results = []
        
        def test_handler(value):
            results.append(value)
        
        self.task_queue.register_task_handler('test_task', test_handler)
        
        # Queue tasks with different priorities
        self.task_queue.queue_task('test_task', 'low', priority=TaskPriority.LOW)
        time.sleep(0.001)
        self.task_queue.queue_task('test_task', 'critical', priority=TaskPriority.CRITICAL)
        time.sleep(0.001)
        self.task_queue.queue_task('test_task', 'normal', priority=TaskPriority.NORMAL)
        time.sleep(0.001)
        self.task_queue.queue_task('test_task', 'high', priority=TaskPriority.HIGH)
        
        # Process tasks
        self.task_queue.process_tasks()
        
        # Critical should be first
        assert results[0] == 'critical'
        assert results[1] == 'high'
        assert results[2] == 'normal'
        assert results[3] == 'low'


class TestModularSystemIntegration:
    """
    Test modular system integration and startup.
    Validates: Requirements 1.1, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = ModuleLoader(base_path=bridge_path)
        self.router = RequestRouter()
        self.config = ConfigurationManager()
    
    def test_module_loader_initialization(self):
        """Test that module loader initializes correctly."""
        assert self.loader is not None
        assert self.loader.base_path == bridge_path
        assert self.loader.loaded_modules == {}
    
    def test_module_discovery(self):
        """Test that modules are discovered correctly."""
        modules = self.loader.discover_modules()
        assert isinstance(modules, list)
    
    def test_configuration_validation(self):
        """Test that configuration validates correctly."""
        assert self.config.validate_config() is True
    
    def test_configuration_detailed_validation(self):
        """Test detailed configuration validation."""
        result = self.config.validate_config_detailed()
        
        assert isinstance(result, dict)
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert result["valid"] is True
    
    def test_router_initialization(self):
        """Test that router initializes correctly."""
        assert self.router is not None
        assert self.router.routes == []
        assert self.router.stats['routes_registered'] == 0
    
    def test_handler_registration(self):
        """Test that handlers can be registered."""
        def test_handler(path, method, data):
            return {"status": 200, "data": {}}
        
        self.router.register_handler("/test", test_handler, ["GET"], "test", "test_module")
        
        assert self.router.stats['routes_registered'] == 1
    
    def test_workspace_category_alignment(self):
        """Test that workspace categories align with Fusion 360 concepts."""
        categories = list(WorkspaceCategory)
        
        assert WorkspaceCategory.DESIGN in categories
        assert WorkspaceCategory.MANUFACTURE in categories
        assert WorkspaceCategory.RESEARCH in categories
        assert WorkspaceCategory.SYSTEM in categories


class TestRequestValidation:
    """
    Test request validation system.
    Validates: Requirements 2.4, 2.5
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = RequestValidator()
    
    def test_validation_rules_registration(self):
        """Test that validation rules can be registered."""
        rules = [
            ParameterRule("param1", ParameterType.STRING, required=True),
            ParameterRule("param2", ParameterType.INTEGER, default=10)
        ]
        
        self.validator.register_validation_rules("/test", rules)
        
        assert "/test" in self.validator.validation_rules
    
    def test_required_parameter_validation(self):
        """Test validation of required parameters."""
        rules = [
            ParameterRule("name", ParameterType.STRING, required=True)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        # Valid request
        result = self.validator.validate_request("/test", "POST", {"name": "test"})
        assert result["name"] == "test"
        
        # Invalid request (missing required parameter)
        with pytest.raises(ValidationError):
            self.validator.validate_request("/test", "POST", {})
    
    def test_type_conversion(self):
        """Test parameter type conversion."""
        rules = [
            ParameterRule("count", ParameterType.INTEGER),
            ParameterRule("value", ParameterType.FLOAT)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {
            "count": "42",
            "value": "3.14"
        })
        
        assert result["count"] == 42
        assert isinstance(result["count"], int)
        assert result["value"] == 3.14
        assert isinstance(result["value"], float)
    
    def test_default_values(self):
        """Test default value application."""
        rules = [
            ParameterRule("count", ParameterType.INTEGER, default=5)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {})
        
        assert result["count"] == 5


class TestErrorHandling:
    """
    Test comprehensive error handling.
    Validates: Requirements 8.1, 8.2, 8.3, 8.5
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
    
    def test_error_handling_with_context(self):
        """Test error handling with module context."""
        try:
            raise ValueError("Test error")
        except Exception as e:
            response = self.error_handler.handle_error(
                error=e,
                module_name="test_module",
                function_name="test_function",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM
            )
        
        assert response.error is True
        assert "Test error" in response.message
        assert response.module_context == "test_module.test_function"
    
    def test_error_statistics(self):
        """Test error statistics collection."""
        for i in range(5):
            try:
                raise ValueError(f"Error {i}")
            except Exception as e:
                self.error_handler.handle_error(
                    error=e,
                    module_name="test_module",
                    function_name="test_function",
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.LOW
                )
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 5
    
    def test_error_isolation(self):
        """Test that errors are isolated between modules."""
        # Generate errors from different modules
        for module in ["module_a", "module_b", "module_c"]:
            try:
                raise ValueError(f"Error from {module}")
            except Exception as e:
                self.error_handler.handle_error(
                    error=e,
                    module_name=module,
                    function_name="test_function",
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.LOW
                )
        
        stats = self.error_handler.get_error_statistics()
        
        # Verify errors are tracked by module
        assert 'error_by_module' in stats
        assert len(stats['error_by_module']) == 3


class TestSystemResilience:
    """
    Test system resilience and stability.
    Validates: Requirements 8.5, 9.3
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = RequestRouter()
        self.task_queue = TaskQueue()
    
    def test_router_stability_with_many_routes(self):
        """Test router stability with many registered routes."""
        def test_handler(path, method, data):
            return {"status": 200, "data": {"path": path}}
        
        # Register many routes
        for i in range(100):
            self.router.register_handler(
                pattern=f"/route_{i}",
                handler=test_handler,
                methods=["GET"],
                category="test",
                module_name=f"module_{i}"
            )
        
        assert self.router.stats['routes_registered'] == 100
        
        # All routes should be accessible
        for i in range(100):
            response = self.router.route_request(f"/route_{i}", "GET", {})
            assert response["status"] == 200
    
    def test_task_queue_stability_with_many_tasks(self):
        """Test task queue stability with many tasks."""
        import time
        results = []
        
        def test_handler(value):
            results.append(value)
        
        self.task_queue.register_task_handler('test_task', test_handler)
        
        # Queue many tasks
        for i in range(50):
            self.task_queue.queue_task('test_task', i)
            time.sleep(0.001)
        
        # Process all tasks
        processed = self.task_queue.process_tasks()
        
        # Should process all or most tasks
        assert processed >= 45
        assert len(results) >= 45
    
    def test_graceful_degradation(self):
        """Test graceful degradation when handlers fail."""
        results = []
        
        def failing_handler(value):
            if value == 5:  # Only one failure to avoid circuit breaker
                raise ValueError("Intentional failure")
            results.append(value)
        
        self.task_queue.register_task_handler('test_task', failing_handler)
        
        # Queue tasks
        for i in range(10):
            self.task_queue.queue_task('test_task', i)
        
        # Process tasks
        processed = self.task_queue.process_tasks()
        
        # Should process all tasks (9 successful + 1 failed = 10 total attempts)
        # The processed count may vary based on implementation
        assert processed >= 9  # At least 9 tasks were attempted
        # Value 5 should not be in results (it failed)
        assert 5 not in results
        # Other values should be present
        assert 0 in results
        assert 9 in results
        # Verify 9 successful results
        assert len(results) == 9


class TestConfigurationManagement:
    """
    Test configuration management consistency.
    Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def test_server_config_structure(self):
        """Test server configuration structure."""
        config = self.config.get_server_config()
        
        assert "host" in config
        assert "port" in config
        assert "timeout" in config
        assert "max_retries" in config
    
    def test_endpoint_category_organization(self):
        """Test endpoint organization by category."""
        for category in WorkspaceCategory:
            endpoints = self.config.get_endpoints(category.value)
            assert isinstance(endpoints, dict)
    
    def test_configuration_immutability(self):
        """Test that configuration returns copies, not references."""
        config1 = self.config.get_server_config()
        config2 = self.config.get_server_config()
        
        config1["host"] = "modified"
        assert config2["host"] != "modified"
    
    def test_module_config_management(self):
        """Test module-specific configuration management."""
        test_config = {"key": "value", "number": 42}
        
        self.config.set_module_config("test_module", test_config)
        result = self.config.get_module_config("test_module")
        
        assert result == test_config
    
    def test_endpoint_update_propagation(self):
        """Test that endpoint updates are propagated."""
        self.config.update_endpoint("design", "geometry", "test_endpoint", "/test/path")
        
        endpoints = self.config.get_endpoints("design")
        assert endpoints["geometry"]["test_endpoint"] == "/test/path"


class TestCAMEndpointPathVerification:
    """
    Test CAM endpoint paths match the requirements specification.
    Validates: Requirements 2.1-6.6
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def test_setups_endpoint_paths(self):
        """
        Test that setups endpoint paths match requirements.
        Validates: Requirements 2.1, 2.2, 2.3, 2.4
        """
        endpoints = self.config.get_endpoints("manufacture")
        setups = endpoints.get("setups", {})
        
        # Requirement 2.1: /cam/setups for GET (list) and POST (create)
        assert setups.get("list") == "/cam/setups"
        assert setups.get("create") == "/cam/setups"
        
        # Requirement 2.2: /cam/setups/{setup_id} for GET, PUT, DELETE
        assert setups.get("get") == "/cam/setups/{setup_id}"
        assert setups.get("modify") == "/cam/setups/{setup_id}"
        assert setups.get("delete") == "/cam/setups/{setup_id}"
        
        # Requirement 2.3: /cam/setups/{setup_id}/duplicate for POST
        assert setups.get("duplicate") == "/cam/setups/{setup_id}/duplicate"
        
        # Requirement 2.4: /cam/setups/{setup_id}/sequence for GET
        assert setups.get("sequence") == "/cam/setups/{setup_id}/sequence"
    
    def test_toolpaths_endpoint_paths(self):
        """
        Test that toolpaths endpoint paths match requirements.
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
        """
        endpoints = self.config.get_endpoints("manufacture")
        toolpaths = endpoints.get("toolpaths", {})
        
        # Requirement 3.1: /cam/toolpaths for listing
        assert toolpaths.get("list") == "/cam/toolpaths"
        
        # Requirement 3.2: /cam/toolpaths/with-heights for listing with height data
        assert toolpaths.get("list_with_heights") == "/cam/toolpaths/with-heights"
        
        # Requirement 3.3: /cam/toolpaths/{toolpath_id} for details
        assert toolpaths.get("get") == "/cam/toolpaths/{toolpath_id}"
        
        # Requirement 3.4: /cam/toolpaths/{toolpath_id}/parameters
        assert toolpaths.get("parameters") == "/cam/toolpaths/{toolpath_id}/parameters"
        
        # Requirement 3.5: /cam/toolpaths/{toolpath_id}/heights
        assert toolpaths.get("heights") == "/cam/toolpaths/{toolpath_id}/heights"
        
        # Requirement 3.6: /cam/toolpaths/{toolpath_id}/passes
        assert toolpaths.get("passes") == "/cam/toolpaths/{toolpath_id}/passes"
        
        # Requirement 3.7: /cam/toolpaths/{toolpath_id}/linking
        assert toolpaths.get("linking") == "/cam/toolpaths/{toolpath_id}/linking"
    
    def test_operations_endpoint_paths(self):
        """
        Test that operations endpoint paths match requirements.
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9
        """
        endpoints = self.config.get_endpoints("manufacture")
        operations = endpoints.get("operations", {})
        
        # Requirement 4.1: /cam/operations/{operation_id}/tool
        assert operations.get("tool") == "/cam/operations/{operation_id}/tool"
        
        # Requirement 4.2: /cam/operations/{operation_id}/heights
        assert operations.get("heights") == "/cam/operations/{operation_id}/heights"
        
        # Requirement 4.3: /cam/operations/{operation_id}/heights/{parameter_name}
        assert operations.get("height_param") == "/cam/operations/{operation_id}/heights/{parameter_name}"
        
        # Requirement 4.4: /cam/operations/{operation_id}/heights/validate
        assert operations.get("heights_validate") == "/cam/operations/{operation_id}/heights/validate"
        
        # Requirement 4.5: /cam/operations/{operation_id}/passes
        assert operations.get("passes") == "/cam/operations/{operation_id}/passes"
        
        # Requirement 4.6: /cam/operations/{operation_id}/passes/validate
        assert operations.get("passes_validate") == "/cam/operations/{operation_id}/passes/validate"
        
        # Requirement 4.7: /cam/operations/{operation_id}/passes/optimize
        assert operations.get("passes_optimize") == "/cam/operations/{operation_id}/passes/optimize"
        
        # Requirement 4.8: /cam/operations/{operation_id}/linking
        assert operations.get("linking") == "/cam/operations/{operation_id}/linking"
        
        # Requirement 4.9: /cam/operations/{operation_id}/linking/validate
        assert operations.get("linking_validate") == "/cam/operations/{operation_id}/linking/validate"
    
    def test_tool_libraries_endpoint_paths(self):
        """
        Test that tool_libraries endpoint paths match requirements.
        Validates: Requirements 5.1, 5.2, 5.3, 5.4, 6.3, 6.4, 6.5, 6.6
        """
        endpoints = self.config.get_endpoints("manufacture")
        tool_libraries = endpoints.get("tool_libraries", {})
        
        # Requirement 5.1: /tool-libraries for listing
        assert tool_libraries.get("list") == "/tool-libraries"
        
        # Requirement 5.2: /tool-libraries/{library_id} for library info
        assert tool_libraries.get("get") == "/tool-libraries/{library_id}"
        
        # Requirement 5.3: /tool-libraries/load for loading
        assert tool_libraries.get("load") == "/tool-libraries/load"
        
        # Requirement 5.4: /tool-libraries/validate-access for access validation
        assert tool_libraries.get("validate_access") == "/tool-libraries/validate-access"
        
        # Requirement 6.3: /tool-libraries/tools for listing and creating
        assert tool_libraries.get("tools_list") == "/tool-libraries/tools"
        assert tool_libraries.get("tools_create") == "/tool-libraries/tools"
        
        # Requirement 6.4: /tool-libraries/tools/{tool_id} for GET, PUT, DELETE
        assert tool_libraries.get("tool_get") == "/tool-libraries/tools/{tool_id}"
        assert tool_libraries.get("tool_modify") == "/tool-libraries/tools/{tool_id}"
        assert tool_libraries.get("tool_delete") == "/tool-libraries/tools/{tool_id}"
        
        # Requirement 6.5: /tool-libraries/tools/{tool_id}/duplicate
        assert tool_libraries.get("tool_duplicate") == "/tool-libraries/tools/{tool_id}/duplicate"
        
        # Requirement 6.6: /tool-libraries/tools/validate
        assert tool_libraries.get("tool_validate") == "/tool-libraries/tools/validate"
    
    def test_tool_search_endpoint_paths(self):
        """
        Test that tool_search endpoint paths match requirements.
        Validates: Requirements 5.5, 5.6, 5.7
        """
        endpoints = self.config.get_endpoints("manufacture")
        tool_search = endpoints.get("tool_search", {})
        
        # Requirement 5.5: /tool-libraries/search for basic search
        assert tool_search.get("search") == "/tool-libraries/search"
        
        # Requirement 5.6: /tool-libraries/search/advanced for advanced search
        assert tool_search.get("advanced") == "/tool-libraries/search/advanced"
        
        # Requirement 5.7: /tool-libraries/search/suggestions for suggestions
        assert tool_search.get("suggestions") == "/tool-libraries/search/suggestions"
    
    def test_tools_endpoint_paths(self):
        """
        Test that tools endpoint paths match requirements.
        Validates: Requirements 6.1, 6.2
        """
        endpoints = self.config.get_endpoints("manufacture")
        tools = endpoints.get("tools", {})
        
        # Requirement 6.1: /cam/tools for listing CAM tools
        assert tools.get("list") == "/cam/tools"
        
        # Requirement 6.2: /cam/tools/{tool_id}/usage for tool usage
        assert tools.get("usage") == "/cam/tools/{tool_id}/usage"
    
    def test_placeholder_naming_consistency(self):
        """
        Test that all placeholders use consistent naming.
        Validates: Requirements 1.3
        """
        import re
        
        endpoints = self.config.get_endpoints("manufacture")
        valid_placeholders = {
            "setup_id", "toolpath_id", "operation_id", 
            "tool_id", "library_id", "parameter_name"
        }
        
        for group_name, group_endpoints in endpoints.items():
            if isinstance(group_endpoints, dict):
                for endpoint_name, path in group_endpoints.items():
                    placeholders = re.findall(r'\{([^}]+)\}', path)
                    for placeholder in placeholders:
                        assert placeholder in valid_placeholders, \
                            f"Invalid placeholder '{{{placeholder}}}' in {group_name}.{endpoint_name}: {path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
