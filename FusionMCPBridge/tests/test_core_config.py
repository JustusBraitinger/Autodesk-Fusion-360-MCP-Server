#!/usr/bin/env python3
"""
Unit tests for FusionMCPBridge/core/config.py

Tests the centralized configuration management for the Fusion 360 Add-In.
"""

import pytest
import sys
import os

# Ensure FusionMCPBridge is at the front of sys.path
bridge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if bridge_path not in sys.path:
    sys.path.insert(0, bridge_path)

from core.config import (
    ConfigurationManager,
    WorkspaceCategory,
    config_manager
)


class TestWorkspaceCategory:
    """Test WorkspaceCategory enum."""
    
    def test_workspace_categories_exist(self):
        """Test that all expected workspace categories exist."""
        assert WorkspaceCategory.DESIGN.value == "design"
        assert WorkspaceCategory.MANUFACTURE.value == "manufacture"
        assert WorkspaceCategory.RESEARCH.value == "research"
        assert WorkspaceCategory.SYSTEM.value == "system"
    
    def test_workspace_category_count(self):
        """Test that we have the expected number of categories."""
        categories = list(WorkspaceCategory)
        assert len(categories) == 4


class TestConfigurationManager:
    """Test cases for the ConfigurationManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def test_initialization(self):
        """Test ConfigurationManager initialization."""
        assert self.config is not None
        assert self.config._server_config is not None
        assert self.config._headers is not None
        assert self.config._endpoints is not None
    
    def test_get_server_config(self):
        """Test get_server_config returns correct structure."""
        config = self.config.get_server_config()
        
        assert isinstance(config, dict)
        assert "host" in config
        assert "port" in config
        assert "timeout" in config
        assert "max_retries" in config
    
    def test_get_server_config_returns_copy(self):
        """Test that get_server_config returns a copy, not the original."""
        config1 = self.config.get_server_config()
        config2 = self.config.get_server_config()
        
        config1["host"] = "modified"
        assert config2["host"] != "modified"
    
    def test_get_headers(self):
        """Test get_headers returns correct structure."""
        headers = self.config.get_headers()
        
        assert isinstance(headers, dict)
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    def test_get_headers_returns_copy(self):
        """Test that get_headers returns a copy, not the original."""
        headers1 = self.config.get_headers()
        headers2 = self.config.get_headers()
        
        headers1["Content-Type"] = "modified"
        assert headers2["Content-Type"] != "modified"
    
    def test_get_timeout(self):
        """Test get_timeout returns positive number."""
        timeout = self.config.get_timeout()
        
        assert isinstance(timeout, (int, float))
        assert timeout > 0
    
    def test_get_max_retries(self):
        """Test get_max_retries returns positive integer."""
        retries = self.config.get_max_retries()
        
        assert isinstance(retries, int)
        assert retries > 0
    
    def test_get_endpoints_all(self):
        """Test get_endpoints returns all endpoints when no category specified."""
        endpoints = self.config.get_endpoints()
        
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
    
    def test_get_endpoints_by_category_design(self):
        """Test get_endpoints returns Design workspace endpoints."""
        endpoints = self.config.get_endpoints("design")
        
        assert isinstance(endpoints, dict)
        assert "geometry" in endpoints
        assert "sketching" in endpoints
        assert "modeling" in endpoints
    
    def test_get_endpoints_by_category_manufacture(self):
        """Test get_endpoints returns MANUFACTURE workspace endpoints."""
        endpoints = self.config.get_endpoints("manufacture")
        
        assert isinstance(endpoints, dict)
        assert "setups" in endpoints
        assert "toolpaths" in endpoints
        assert "tools" in endpoints
    
    def test_get_endpoints_by_category_system(self):
        """Test get_endpoints returns system endpoints."""
        endpoints = self.config.get_endpoints("system")
        
        assert isinstance(endpoints, dict)
        assert "lifecycle" in endpoints
        assert "utilities" in endpoints
    
    def test_get_endpoints_invalid_category(self):
        """Test get_endpoints raises error for invalid category."""
        with pytest.raises(ValueError):
            self.config.get_endpoints("invalid_category")
    
    def test_validate_config_success(self):
        """Test validate_config returns True for valid config."""
        result = self.config.validate_config()
        assert result is True
    
    def test_validate_config_detailed(self):
        """Test validate_config_detailed returns detailed validation."""
        result = self.config.validate_config_detailed()
        
        assert isinstance(result, dict)
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "conflicts" in result
        assert "resolution_guidance" in result
    
    def test_set_and_get_module_config(self):
        """Test setting and getting module configuration."""
        test_config = {"key": "value", "number": 42}
        
        self.config.set_module_config("test_module", test_config)
        result = self.config.get_module_config("test_module")
        
        assert result == test_config
    
    def test_get_module_config_nonexistent(self):
        """Test getting config for nonexistent module returns empty dict."""
        result = self.config.get_module_config("nonexistent_module")
        assert result == {}
    
    def test_update_endpoint(self):
        """Test updating an endpoint."""
        self.config.update_endpoint("design", "geometry", "test_endpoint", "/test/path")
        
        endpoints = self.config.get_endpoints("design")
        assert endpoints["geometry"]["test_endpoint"] == "/test/path"
    
    def test_update_endpoint_invalid_category(self):
        """Test updating endpoint with invalid category raises error."""
        with pytest.raises(ValueError):
            self.config.update_endpoint("invalid", "group", "endpoint", "/path")
    
    def test_add_category_configuration(self):
        """Test adding category-specific configuration."""
        test_config = {"setting": "value"}
        
        self.config.add_category_configuration("design", test_config)
        result = self.config.get_category_configuration("design")
        
        assert result == test_config
    
    def test_get_category_configuration_invalid(self):
        """Test getting config for invalid category returns empty dict."""
        result = self.config.get_category_configuration("invalid")
        assert result == {}


class TestGlobalConfigManager:
    """Test the global config_manager instance."""
    
    def test_global_instance_exists(self):
        """Test that global config_manager instance exists."""
        assert config_manager is not None
        assert isinstance(config_manager, ConfigurationManager)
    
    def test_global_instance_is_valid(self):
        """Test that global config_manager has valid configuration."""
        assert config_manager.validate_config() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# =============================================================================
# Property-Based Tests for Config-Handler Endpoint Consistency
# =============================================================================

try:
    from hypothesis import given, strategies as st, settings
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False


# Define the expected handler registrations based on actual handler modules
# This serves as the source of truth for what endpoints should exist
EXPECTED_MANUFACTURE_ENDPOINTS = {
    "setups": {
        "/cam/setups": ["GET", "POST"],
        "/cam/setups/{setup_id}": ["GET", "PUT", "DELETE"],
        "/cam/setups/{setup_id}/duplicate": ["POST"],
        "/cam/setups/{setup_id}/sequence": ["GET"],
    },
    "toolpaths": {
        "/cam/toolpaths": ["GET"],
        "/cam/toolpaths/with-heights": ["GET"],
        "/cam/toolpaths/{toolpath_id}": ["GET"],
        "/cam/toolpaths/{toolpath_id}/parameters": ["GET"],
        "/cam/toolpaths/{toolpath_id}/heights": ["GET"],
        "/cam/toolpaths/{toolpath_id}/passes": ["GET", "PUT"],
        "/cam/toolpaths/{toolpath_id}/linking": ["GET", "PUT"],
    },
    "operations": {
        "/cam/operations/{operation_id}/tool": ["GET", "PUT"],
        "/cam/operations/{operation_id}/heights": ["GET"],
        "/cam/operations/{operation_id}/heights/{parameter_name}": ["PUT"],
        "/cam/operations/{operation_id}/heights/validate": ["POST"],
        "/cam/operations/{operation_id}/passes": ["GET"],
        "/cam/operations/{operation_id}/passes/validate": ["POST"],
        "/cam/operations/{operation_id}/passes/optimize": ["GET"],
        "/cam/operations/{operation_id}/linking": ["GET"],
        "/cam/operations/{operation_id}/linking/validate": ["POST"],
    },
    "tools": {
        "/cam/tools": ["GET"],
        "/cam/tools/{tool_id}/usage": ["GET"],
    },
    "tool_libraries": {
        "/tool-libraries": ["GET"],
        "/tool-libraries/{library_id}": ["GET"],
        "/tool-libraries/load": ["POST"],
        "/tool-libraries/validate-access": ["GET"],
        "/tool-libraries/tools": ["GET", "POST"],
        "/tool-libraries/tools/{tool_id}": ["GET", "PUT", "DELETE"],
        "/tool-libraries/tools/{tool_id}/duplicate": ["POST"],
        "/tool-libraries/tools/validate": ["POST"],
    },
    "tool_search": {
        "/tool-libraries/search": ["GET", "POST"],
        "/tool-libraries/search/advanced": ["POST"],
        "/tool-libraries/search/suggestions": ["GET"],
    },
}


class TestConfigHandlerEndpointConsistency:
    """
    Property-based tests for Config-Handler Endpoint Consistency.
    
    **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
    **Validates: Requirements 1.1, 1.2**
    
    *For any* endpoint path defined in the ConfigurationManager's `_endpoints` 
    dictionary for the MANUFACTURE workspace, there SHALL exist a corresponding 
    `register_handler()` call in the handler modules with a matching path pattern.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def test_manufacture_endpoint_groups_exist(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        Test that all expected endpoint groups exist in MANUFACTURE workspace.
        """
        endpoints = self.config.get_endpoints("manufacture")
        
        expected_groups = ["setups", "toolpaths", "operations", "tools", "tool_libraries", "tool_search"]
        for group in expected_groups:
            assert group in endpoints, f"Missing endpoint group: {group}"
    
    def test_setups_endpoints_match_handlers(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        Test that setups endpoint paths match handler registrations.
        """
        endpoints = self.config.get_endpoints("manufacture")
        setups = endpoints.get("setups", {})
        
        # Verify all expected paths are present
        expected_paths = [
            "/cam/setups",
            "/cam/setups/{setup_id}",
            "/cam/setups/{setup_id}/duplicate",
            "/cam/setups/{setup_id}/sequence",
        ]
        
        config_paths = list(setups.values())
        for path in expected_paths:
            assert path in config_paths, f"Missing setups endpoint: {path}"
    
    def test_toolpaths_endpoints_match_handlers(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        Test that toolpaths endpoint paths match handler registrations.
        """
        endpoints = self.config.get_endpoints("manufacture")
        toolpaths = endpoints.get("toolpaths", {})
        
        expected_paths = [
            "/cam/toolpaths",
            "/cam/toolpaths/with-heights",
            "/cam/toolpaths/{toolpath_id}",
            "/cam/toolpaths/{toolpath_id}/parameters",
            "/cam/toolpaths/{toolpath_id}/heights",
            "/cam/toolpaths/{toolpath_id}/passes",
            "/cam/toolpaths/{toolpath_id}/linking",
        ]
        
        config_paths = list(toolpaths.values())
        for path in expected_paths:
            assert path in config_paths, f"Missing toolpaths endpoint: {path}"
    
    def test_operations_endpoints_match_handlers(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        Test that operations endpoint paths match handler registrations.
        """
        endpoints = self.config.get_endpoints("manufacture")
        operations = endpoints.get("operations", {})
        
        expected_paths = [
            "/cam/operations/{operation_id}/tool",
            "/cam/operations/{operation_id}/heights",
            "/cam/operations/{operation_id}/heights/{parameter_name}",
            "/cam/operations/{operation_id}/heights/validate",
            "/cam/operations/{operation_id}/passes",
            "/cam/operations/{operation_id}/passes/validate",
            "/cam/operations/{operation_id}/passes/optimize",
            "/cam/operations/{operation_id}/linking",
            "/cam/operations/{operation_id}/linking/validate",
        ]
        
        config_paths = list(operations.values())
        for path in expected_paths:
            assert path in config_paths, f"Missing operations endpoint: {path}"
    
    def test_tools_endpoints_match_handlers(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        Test that tools endpoint paths match handler registrations.
        """
        endpoints = self.config.get_endpoints("manufacture")
        tools = endpoints.get("tools", {})
        
        expected_paths = [
            "/cam/tools",
            "/cam/tools/{tool_id}/usage",
        ]
        
        config_paths = list(tools.values())
        for path in expected_paths:
            assert path in config_paths, f"Missing tools endpoint: {path}"
    
    def test_tool_libraries_endpoints_match_handlers(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        Test that tool_libraries endpoint paths match handler registrations.
        """
        endpoints = self.config.get_endpoints("manufacture")
        tool_libraries = endpoints.get("tool_libraries", {})
        
        expected_paths = [
            "/tool-libraries",
            "/tool-libraries/{library_id}",
            "/tool-libraries/load",
            "/tool-libraries/validate-access",
            "/tool-libraries/tools",
            "/tool-libraries/tools/{tool_id}",
            "/tool-libraries/tools/{tool_id}/duplicate",
            "/tool-libraries/tools/validate",
        ]
        
        config_paths = list(tool_libraries.values())
        for path in expected_paths:
            assert path in config_paths, f"Missing tool_libraries endpoint: {path}"
    
    def test_tool_search_endpoints_match_handlers(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        Test that tool_search endpoint paths match handler registrations.
        """
        endpoints = self.config.get_endpoints("manufacture")
        tool_search = endpoints.get("tool_search", {})
        
        expected_paths = [
            "/tool-libraries/search",
            "/tool-libraries/search/advanced",
            "/tool-libraries/search/suggestions",
        ]
        
        config_paths = list(tool_search.values())
        for path in expected_paths:
            assert path in config_paths, f"Missing tool_search endpoint: {path}"
    
    def test_all_config_endpoints_have_handler_counterparts(self):
        """
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        
        *For any* endpoint path defined in config, verify it matches expected handler paths.
        """
        endpoints = self.config.get_endpoints("manufacture")
        
        # Collect all expected paths from handler registrations
        all_expected_paths = set()
        for group_paths in EXPECTED_MANUFACTURE_ENDPOINTS.values():
            all_expected_paths.update(group_paths.keys())
        
        # Collect all config paths
        all_config_paths = set()
        for group_name, group_endpoints in endpoints.items():
            if isinstance(group_endpoints, dict):
                all_config_paths.update(group_endpoints.values())
        
        # Verify config paths are subset of expected paths
        for config_path in all_config_paths:
            assert config_path in all_expected_paths, \
                f"Config endpoint '{config_path}' has no corresponding handler registration"


if HYPOTHESIS_AVAILABLE:
    class TestConfigEndpointPropertyBased:
        """
        Property-based tests using Hypothesis for endpoint consistency.
        
        **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
        **Validates: Requirements 1.1, 1.2**
        """
        
        def setup_method(self):
            """Set up test fixtures."""
            self.config = ConfigurationManager()
        
        @given(st.sampled_from(list(EXPECTED_MANUFACTURE_ENDPOINTS.keys())))
        @settings(max_examples=100)
        def test_endpoint_group_paths_match_handlers(self, group_name):
            """
            **Feature: config-endpoint-sync, Property 1: Config-Handler Endpoint Consistency**
            **Validates: Requirements 1.1, 1.2**
            
            *For any* endpoint group in MANUFACTURE workspace, all paths should 
            match expected handler registrations.
            """
            endpoints = self.config.get_endpoints("manufacture")
            
            if group_name in endpoints:
                config_group = endpoints[group_name]
                expected_paths = set(EXPECTED_MANUFACTURE_ENDPOINTS[group_name].keys())
                config_paths = set(config_group.values())
                
                # All config paths should be in expected paths
                for path in config_paths:
                    assert path in expected_paths, \
                        f"Unexpected path '{path}' in group '{group_name}'"


# =============================================================================
# Property-Based Tests for Placeholder Naming Consistency
# =============================================================================

# Define the expected placeholder naming conventions
PLACEHOLDER_CONVENTIONS = {
    "setup": "{setup_id}",
    "toolpath": "{toolpath_id}",
    "operation": "{operation_id}",
    "tool": "{tool_id}",
    "library": "{library_id}",
    "parameter": "{parameter_name}",
}

# Define invalid placeholder patterns that should NOT be used
INVALID_PLACEHOLDER_PATTERNS = [
    "{id}",           # Generic - should use entity-specific names
    "{setup}",        # Missing _id suffix
    "{toolpath}",     # Missing _id suffix
    "{operation}",    # Missing _id suffix
    "{tool}",         # Missing _id suffix
    "{library}",      # Missing _id suffix
    "{param}",        # Should be {parameter_name}
    "{name}",         # Too generic
]


class TestPlaceholderNamingConsistency:
    """
    Property-based tests for Placeholder Naming Consistency.
    
    **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
    **Validates: Requirements 1.3**
    
    *For any* endpoint path containing a placeholder (pattern `{...}`), the 
    placeholder name SHALL match the entity type convention: `{setup_id}` for 
    setups, `{toolpath_id}` for toolpaths, `{operation_id}` for operations, 
    `{tool_id}` for tools, `{library_id}` for libraries.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def _extract_placeholders(self, path: str) -> list:
        """Extract all placeholders from a path."""
        import re
        return re.findall(r'\{([^}]+)\}', path)
    
    def _get_all_endpoint_paths(self) -> list:
        """Get all endpoint paths from all categories."""
        all_paths = []
        for category in WorkspaceCategory:
            endpoints = self.config.get_endpoints(category.value)
            for group_name, group_endpoints in endpoints.items():
                if isinstance(group_endpoints, dict):
                    for endpoint_name, path in group_endpoints.items():
                        all_paths.append((category.value, group_name, endpoint_name, path))
        return all_paths
    
    def test_no_generic_id_placeholder(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        Test that no endpoint uses the generic {id} placeholder.
        """
        all_paths = self._get_all_endpoint_paths()
        
        for category, group, name, path in all_paths:
            placeholders = self._extract_placeholders(path)
            assert "id" not in placeholders, \
                f"Generic {{id}} placeholder found in {category}.{group}.{name}: {path}. " \
                f"Use entity-specific placeholder like {{setup_id}}, {{toolpath_id}}, etc."
    
    def test_setup_endpoints_use_setup_id(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        Test that setup endpoints use {setup_id} placeholder.
        """
        endpoints = self.config.get_endpoints("manufacture")
        setups = endpoints.get("setups", {})
        
        for name, path in setups.items():
            if "{" in path and "setup" in path.lower():
                placeholders = self._extract_placeholders(path)
                # If path contains a setup-related placeholder, it should be setup_id
                setup_placeholders = [p for p in placeholders if "setup" in p.lower()]
                for placeholder in setup_placeholders:
                    assert placeholder == "setup_id", \
                        f"Setup endpoint '{name}' uses incorrect placeholder: {{{placeholder}}}. " \
                        f"Should use {{setup_id}}"
    
    def test_toolpath_endpoints_use_toolpath_id(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        Test that toolpath endpoints use {toolpath_id} placeholder.
        """
        endpoints = self.config.get_endpoints("manufacture")
        toolpaths = endpoints.get("toolpaths", {})
        
        for name, path in toolpaths.items():
            if "{" in path and "toolpath" in path.lower():
                placeholders = self._extract_placeholders(path)
                toolpath_placeholders = [p for p in placeholders if "toolpath" in p.lower()]
                for placeholder in toolpath_placeholders:
                    assert placeholder == "toolpath_id", \
                        f"Toolpath endpoint '{name}' uses incorrect placeholder: {{{placeholder}}}. " \
                        f"Should use {{toolpath_id}}"
    
    def test_operation_endpoints_use_operation_id(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        Test that operation endpoints use {operation_id} placeholder.
        """
        endpoints = self.config.get_endpoints("manufacture")
        operations = endpoints.get("operations", {})
        
        for name, path in operations.items():
            if "{" in path and "operation" in path.lower():
                placeholders = self._extract_placeholders(path)
                operation_placeholders = [p for p in placeholders if "operation" in p.lower()]
                for placeholder in operation_placeholders:
                    assert placeholder == "operation_id", \
                        f"Operation endpoint '{name}' uses incorrect placeholder: {{{placeholder}}}. " \
                        f"Should use {{operation_id}}"
    
    def test_tool_endpoints_use_tool_id(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        Test that tool endpoints use {tool_id} placeholder.
        """
        endpoints = self.config.get_endpoints("manufacture")
        
        # Check tools group
        tools = endpoints.get("tools", {})
        for name, path in tools.items():
            if "{" in path:
                placeholders = self._extract_placeholders(path)
                tool_placeholders = [p for p in placeholders if "tool" in p.lower() and "toolpath" not in p.lower()]
                for placeholder in tool_placeholders:
                    assert placeholder == "tool_id", \
                        f"Tool endpoint '{name}' uses incorrect placeholder: {{{placeholder}}}. " \
                        f"Should use {{tool_id}}"
        
        # Check tool_libraries group for tool-related placeholders
        tool_libraries = endpoints.get("tool_libraries", {})
        for name, path in tool_libraries.items():
            if "{" in path and "/tools/" in path:
                placeholders = self._extract_placeholders(path)
                tool_placeholders = [p for p in placeholders if "tool" in p.lower() and "toolpath" not in p.lower()]
                for placeholder in tool_placeholders:
                    assert placeholder == "tool_id", \
                        f"Tool library endpoint '{name}' uses incorrect placeholder: {{{placeholder}}}. " \
                        f"Should use {{tool_id}}"
    
    def test_library_endpoints_use_library_id(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        Test that library endpoints use {library_id} placeholder.
        """
        endpoints = self.config.get_endpoints("manufacture")
        tool_libraries = endpoints.get("tool_libraries", {})
        
        for name, path in tool_libraries.items():
            if "{" in path and "library" in path.lower():
                placeholders = self._extract_placeholders(path)
                library_placeholders = [p for p in placeholders if "library" in p.lower()]
                for placeholder in library_placeholders:
                    assert placeholder == "library_id", \
                        f"Library endpoint '{name}' uses incorrect placeholder: {{{placeholder}}}. " \
                        f"Should use {{library_id}}"
    
    def test_no_invalid_placeholder_patterns(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        Test that no endpoint uses invalid placeholder patterns.
        """
        all_paths = self._get_all_endpoint_paths()
        
        for category, group, name, path in all_paths:
            for invalid_pattern in INVALID_PLACEHOLDER_PATTERNS:
                # Extract the placeholder name without braces
                invalid_name = invalid_pattern[1:-1]
                placeholders = self._extract_placeholders(path)
                
                assert invalid_name not in placeholders, \
                    f"Invalid placeholder {invalid_pattern} found in {category}.{group}.{name}: {path}. " \
                    f"Use entity-specific placeholder names."
    
    def test_all_placeholders_follow_convention(self):
        """
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        
        *For any* endpoint path with placeholders, verify all placeholders follow 
        the naming convention.
        """
        all_paths = self._get_all_endpoint_paths()
        
        # Valid placeholder names
        valid_placeholders = {
            "setup_id", "toolpath_id", "operation_id", 
            "tool_id", "library_id", "parameter_name"
        }
        
        for category, group, name, path in all_paths:
            placeholders = self._extract_placeholders(path)
            
            for placeholder in placeholders:
                assert placeholder in valid_placeholders, \
                    f"Non-standard placeholder '{{{placeholder}}}' found in " \
                    f"{category}.{group}.{name}: {path}. " \
                    f"Valid placeholders are: {valid_placeholders}"


if HYPOTHESIS_AVAILABLE:
    class TestPlaceholderNamingPropertyBased:
        """
        Property-based tests using Hypothesis for placeholder naming consistency.
        
        **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
        **Validates: Requirements 1.3**
        """
        
        def setup_method(self):
            """Set up test fixtures."""
            self.config = ConfigurationManager()
        
        def _extract_placeholders(self, path: str) -> list:
            """Extract all placeholders from a path."""
            import re
            return re.findall(r'\{([^}]+)\}', path)
        
        @given(st.sampled_from(["setups", "toolpaths", "operations", "tools", "tool_libraries", "tool_search"]))
        @settings(max_examples=100)
        def test_manufacture_group_placeholders_valid(self, group_name):
            """
            **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
            **Validates: Requirements 1.3**
            
            *For any* endpoint group in MANUFACTURE workspace, all placeholders 
            should follow the naming convention.
            """
            valid_placeholders = {
                "setup_id", "toolpath_id", "operation_id", 
                "tool_id", "library_id", "parameter_name"
            }
            
            endpoints = self.config.get_endpoints("manufacture")
            
            if group_name in endpoints:
                group_endpoints = endpoints[group_name]
                for endpoint_name, path in group_endpoints.items():
                    placeholders = self._extract_placeholders(path)
                    for placeholder in placeholders:
                        assert placeholder in valid_placeholders, \
                            f"Invalid placeholder '{{{placeholder}}}' in {group_name}.{endpoint_name}: {path}"
        
        @given(st.sampled_from(list(WorkspaceCategory)))
        @settings(max_examples=100)
        def test_all_category_placeholders_valid(self, category):
            """
            **Feature: config-endpoint-sync, Property 2: Placeholder Naming Consistency**
            **Validates: Requirements 1.3**
            
            *For any* workspace category, all endpoint placeholders should follow 
            the naming convention (no generic {id} placeholders).
            """
            endpoints = self.config.get_endpoints(category.value)
            
            for group_name, group_endpoints in endpoints.items():
                if isinstance(group_endpoints, dict):
                    for endpoint_name, path in group_endpoints.items():
                        placeholders = self._extract_placeholders(path)
                        
                        # No generic {id} placeholder
                        assert "id" not in placeholders, \
                            f"Generic {{id}} found in {category.value}.{group_name}.{endpoint_name}: {path}"



# =============================================================================
# Property-Based Tests for Validation Detection Completeness
# =============================================================================

class TestValidationDetectionCompleteness:
    """
    Property-based tests for Validation Detection Completeness.
    
    **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
    **Validates: Requirements 8.1, 8.2**
    
    *For any* configuration with an endpoint path that does not match the expected 
    pattern (e.g., singular vs plural, wrong placeholder name), the 
    `validate_config_detailed()` method SHALL include that path in the validation 
    errors or warnings.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def test_detects_singular_path_pattern(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects singular path patterns that should be plural.
        """
        # Create a config with a singular path pattern
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setup/{setup_id}")
        
        result = test_config.validate_config_detailed()
        
        # Should detect the singular 'setup' instead of 'setups'
        all_messages = result['errors'] + result['warnings']
        singular_detected = any("singular" in msg.lower() or "setup/" in msg.lower() for msg in all_messages)
        assert singular_detected, \
            f"Validation should detect singular path '/cam/setup/' but got: {all_messages}"
    
    def test_detects_generic_id_placeholder(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects generic {id} placeholder.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setups/{id}")
        
        result = test_config.validate_config_detailed()
        
        # Should detect the generic {id} placeholder
        all_messages = result['errors'] + result['warnings']
        id_detected = any("{id}" in msg or "non-standard placeholder" in msg.lower() for msg in all_messages)
        assert id_detected, \
            f"Validation should detect generic {{id}} placeholder but got: {all_messages}"
    
    def test_detects_missing_id_suffix_placeholder(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects placeholders missing _id suffix.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setups/{setup}")
        
        result = test_config.validate_config_detailed()
        
        # Should detect {setup} instead of {setup_id}
        all_messages = result['errors'] + result['warnings']
        detected = any("{setup}" in msg or "non-standard" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect {{setup}} placeholder but got: {all_messages}"
    
    def test_detects_toolpath_singular_pattern(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects singular toolpath pattern.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/toolpath/{toolpath_id}")
        
        result = test_config.validate_config_detailed()
        
        # Should detect singular 'toolpath' instead of 'toolpaths'
        all_messages = result['errors'] + result['warnings']
        detected = any("singular" in msg.lower() or "toolpath/" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect singular '/cam/toolpath/' but got: {all_messages}"
    
    def test_detects_operation_singular_pattern(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects singular operation pattern.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/operation/{operation_id}/tool")
        
        result = test_config.validate_config_detailed()
        
        # Should detect singular 'operation' instead of 'operations'
        all_messages = result['errors'] + result['warnings']
        detected = any("singular" in msg.lower() or "operation/" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect singular '/cam/operation/' but got: {all_messages}"
    
    def test_detects_tool_library_singular_pattern(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects singular tool-library pattern.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/tool-library/{library_id}")
        
        result = test_config.validate_config_detailed()
        
        # Should detect singular 'tool-library' instead of 'tool-libraries'
        all_messages = result['errors'] + result['warnings']
        detected = any("singular" in msg.lower() or "tool-library/" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect singular '/tool-library/' but got: {all_messages}"
    
    def test_detects_wrong_toolpath_placeholder(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects wrong placeholder for toolpath.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/toolpaths/{toolpath}")
        
        result = test_config.validate_config_detailed()
        
        # Should detect {toolpath} instead of {toolpath_id}
        all_messages = result['errors'] + result['warnings']
        detected = any("{toolpath}" in msg or "non-standard" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect {{toolpath}} placeholder but got: {all_messages}"
    
    def test_detects_wrong_operation_placeholder(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects wrong placeholder for operation.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/operations/{operation}/tool")
        
        result = test_config.validate_config_detailed()
        
        # Should detect {operation} instead of {operation_id}
        all_messages = result['errors'] + result['warnings']
        detected = any("{operation}" in msg or "non-standard" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect {{operation}} placeholder but got: {all_messages}"
    
    def test_detects_wrong_tool_placeholder(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects wrong placeholder for tool.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/tools/{tool}/usage")
        
        result = test_config.validate_config_detailed()
        
        # Should detect {tool} instead of {tool_id}
        all_messages = result['errors'] + result['warnings']
        detected = any("{tool}" in msg or "non-standard" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect {{tool}} placeholder but got: {all_messages}"
    
    def test_detects_wrong_library_placeholder(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that validation detects wrong placeholder for library.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/tool-libraries/{library}")
        
        result = test_config.validate_config_detailed()
        
        # Should detect {library} instead of {library_id}
        all_messages = result['errors'] + result['warnings']
        detected = any("{library}" in msg or "non-standard" in msg.lower() for msg in all_messages)
        assert detected, \
            f"Validation should detect {{library}} placeholder but got: {all_messages}"
    
    def test_valid_config_has_no_pattern_errors(self):
        """
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        
        Test that valid configuration has no pattern-related errors.
        """
        # The default config should be valid
        result = self.config.validate_config_detailed()
        
        # Check that there are no errors related to patterns
        pattern_errors = [e for e in result['errors'] if 'placeholder' in e.lower() or 'singular' in e.lower()]
        assert len(pattern_errors) == 0, \
            f"Valid config should have no pattern errors but got: {pattern_errors}"


if HYPOTHESIS_AVAILABLE:
    class TestValidationDetectionPropertyBased:
        """
        Property-based tests using Hypothesis for validation detection completeness.
        
        **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
        **Validates: Requirements 8.1, 8.2**
        """
        
        def setup_method(self):
            """Set up test fixtures."""
            self.config = ConfigurationManager()
        
        # Define invalid patterns that should be detected
        INVALID_SINGULAR_PATTERNS = [
            "/cam/setup/{setup_id}",
            "/cam/toolpath/{toolpath_id}",
            "/cam/operation/{operation_id}",
            "/cam/tool/{tool_id}",
            "/tool-library/{library_id}",
        ]
        
        INVALID_PLACEHOLDER_PATTERNS = [
            ("/cam/setups/{id}", "{id}"),
            ("/cam/setups/{setup}", "{setup}"),
            ("/cam/toolpaths/{toolpath}", "{toolpath}"),
            ("/cam/operations/{operation}", "{operation}"),
            ("/cam/tools/{tool}", "{tool}"),
            ("/tool-libraries/{library}", "{library}"),
            ("/cam/operations/{operation_id}/heights/{param}", "{param}"),
        ]
        
        @given(st.sampled_from(INVALID_SINGULAR_PATTERNS))
        @settings(max_examples=100)
        def test_detects_all_singular_patterns(self, invalid_path):
            """
            **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
            **Validates: Requirements 8.1, 8.2**
            
            *For any* endpoint path with singular form, validation should detect it.
            """
            test_config = ConfigurationManager()
            test_config.update_endpoint("manufacture", "test_group", "test_endpoint", invalid_path)
            
            result = test_config.validate_config_detailed()
            
            all_messages = result['errors'] + result['warnings']
            detected = any("singular" in msg.lower() for msg in all_messages)
            assert detected, \
                f"Validation should detect singular pattern in '{invalid_path}' but got: {all_messages}"
        
        @given(st.sampled_from(INVALID_PLACEHOLDER_PATTERNS))
        @settings(max_examples=100)
        def test_detects_all_invalid_placeholders(self, path_and_placeholder):
            """
            **Feature: config-endpoint-sync, Property 3: Validation Detection Completeness**
            **Validates: Requirements 8.1, 8.2**
            
            *For any* endpoint path with invalid placeholder, validation should detect it.
            """
            invalid_path, expected_placeholder = path_and_placeholder
            test_config = ConfigurationManager()
            test_config.update_endpoint("manufacture", "test_group", "test_endpoint", invalid_path)
            
            result = test_config.validate_config_detailed()
            
            all_messages = result['errors'] + result['warnings']
            detected = any(expected_placeholder in msg or "non-standard" in msg.lower() for msg in all_messages)
            assert detected, \
                f"Validation should detect invalid placeholder '{expected_placeholder}' in '{invalid_path}' but got: {all_messages}"



# =============================================================================
# Property-Based Tests for Validation Guidance Provision
# =============================================================================

class TestValidationGuidanceProvision:
    """
    Property-based tests for Validation Guidance Provision.
    
    **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
    **Validates: Requirements 8.3**
    
    *For any* validation error or warning detected by `validate_config_detailed()`, 
    the result SHALL include a non-empty resolution guidance string that describes 
    how to fix the issue.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def test_singular_pattern_has_guidance(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that singular path pattern detection includes resolution guidance.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setup/{setup_id}")
        
        result = test_config.validate_config_detailed()
        
        # Should have guidance for the singular pattern issue
        assert len(result['resolution_guidance']) > 0, \
            "Validation should provide resolution guidance for singular pattern"
        
        # Guidance should mention the correct plural form
        guidance_text = ' '.join(result['resolution_guidance'])
        assert "setups" in guidance_text.lower() or "plural" in guidance_text.lower(), \
            f"Guidance should mention correct plural form but got: {result['resolution_guidance']}"
    
    def test_generic_id_placeholder_has_guidance(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that generic {id} placeholder detection includes resolution guidance.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setups/{id}")
        
        result = test_config.validate_config_detailed()
        
        # Should have guidance for the generic id placeholder
        assert len(result['resolution_guidance']) > 0, \
            "Validation should provide resolution guidance for generic {id} placeholder"
        
        # Guidance should mention entity-specific placeholders
        guidance_text = ' '.join(result['resolution_guidance'])
        has_specific_guidance = any(
            placeholder in guidance_text 
            for placeholder in ["setup_id", "toolpath_id", "operation_id", "tool_id", "library_id"]
        )
        assert has_specific_guidance, \
            f"Guidance should mention entity-specific placeholders but got: {result['resolution_guidance']}"
    
    def test_missing_id_suffix_has_guidance(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that missing _id suffix detection includes resolution guidance.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setups/{setup}")
        
        result = test_config.validate_config_detailed()
        
        # Should have guidance for the missing _id suffix
        assert len(result['resolution_guidance']) > 0, \
            "Validation should provide resolution guidance for missing _id suffix"
        
        # Guidance should mention the correct placeholder
        guidance_text = ' '.join(result['resolution_guidance'])
        assert "setup_id" in guidance_text, \
            f"Guidance should mention {{setup_id}} but got: {result['resolution_guidance']}"
    
    def test_guidance_includes_example_for_singular_pattern(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that guidance includes example of correct path for singular patterns.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setup/{setup_id}")
        
        result = test_config.validate_config_detailed()
        
        # Guidance should include an example with the correct path
        guidance_text = ' '.join(result['resolution_guidance'])
        assert "/cam/setups/" in guidance_text, \
            f"Guidance should include example with correct plural path but got: {result['resolution_guidance']}"
    
    def test_guidance_is_non_empty_for_all_errors(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that all errors have corresponding non-empty guidance.
        """
        test_config = ConfigurationManager()
        # Add multiple invalid patterns
        test_config.update_endpoint("manufacture", "test1", "endpoint1", "/cam/setup/{id}")
        test_config.update_endpoint("manufacture", "test2", "endpoint2", "/cam/toolpath/{toolpath}")
        
        result = test_config.validate_config_detailed()
        
        # Should have at least as many guidance items as errors
        error_count = len(result['errors'])
        guidance_count = len(result['resolution_guidance'])
        
        assert guidance_count >= error_count, \
            f"Should have at least {error_count} guidance items but got {guidance_count}"
        
        # All guidance items should be non-empty strings
        for guidance in result['resolution_guidance']:
            assert isinstance(guidance, str), f"Guidance should be string but got {type(guidance)}"
            assert len(guidance.strip()) > 0, "Guidance should not be empty"
    
    def test_guidance_is_non_empty_for_all_warnings(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that all warnings have corresponding non-empty guidance.
        """
        test_config = ConfigurationManager()
        # Add patterns that generate warnings (singular forms)
        test_config.update_endpoint("manufacture", "test1", "endpoint1", "/cam/setup/{setup_id}")
        test_config.update_endpoint("manufacture", "test2", "endpoint2", "/cam/toolpath/{toolpath_id}")
        
        result = test_config.validate_config_detailed()
        
        # Should have guidance for warnings
        warning_count = len(result['warnings'])
        if warning_count > 0:
            # Filter guidance that relates to warnings (not summary guidance)
            non_summary_guidance = [
                g for g in result['resolution_guidance'] 
                if not g.startswith("Found ")
            ]
            assert len(non_summary_guidance) >= warning_count, \
                f"Should have guidance for {warning_count} warnings but got {len(non_summary_guidance)}"
    
    def test_guidance_describes_how_to_fix(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that guidance describes how to fix the issue.
        """
        test_config = ConfigurationManager()
        test_config.update_endpoint("manufacture", "test_group", "test_endpoint", "/cam/setups/{id}")
        
        result = test_config.validate_config_detailed()
        
        # Guidance should contain actionable words
        guidance_text = ' '.join(result['resolution_guidance']).lower()
        actionable_words = ["use", "change", "fix", "set", "add", "replace"]
        has_actionable = any(word in guidance_text for word in actionable_words)
        
        assert has_actionable, \
            f"Guidance should contain actionable instructions but got: {result['resolution_guidance']}"
    
    def test_valid_config_has_no_pattern_errors(self):
        """
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        
        Test that valid configuration has no pattern-related errors.
        Note: Duplicate paths are expected for endpoints that support multiple HTTP methods
        (e.g., /cam/setups for GET and POST), so we only check for pattern errors.
        """
        # The default config should be valid
        result = self.config.validate_config_detailed()
        
        # Should have no pattern-related errors (placeholder or singular/plural issues)
        pattern_errors = [
            e for e in result['errors'] 
            if 'placeholder' in e.lower() or 'singular' in e.lower() or 'non-standard' in e.lower()
        ]
        assert len(pattern_errors) == 0, \
            f"Valid config should have no pattern errors but got: {pattern_errors}"
        
        # Should have no pattern-related warnings
        pattern_warnings = [
            w for w in result['warnings'] 
            if 'placeholder' in w.lower() or 'singular' in w.lower()
        ]
        assert len(pattern_warnings) == 0, \
            f"Valid config should have no pattern warnings but got: {pattern_warnings}"


# =============================================================================
# Tests for Obsolete Endpoint Removal
# =============================================================================

class TestObsoleteEndpointsRemoved:
    """
    Tests to verify obsolete endpoints are not present in configuration.
    
    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**
    
    These tests ensure that deprecated endpoint patterns have been removed
    from the configuration and replaced with the correct RESTful patterns.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigurationManager()
    
    def _get_all_endpoint_paths(self) -> list:
        """Get all endpoint paths from all categories."""
        all_paths = []
        for category in WorkspaceCategory:
            endpoints = self.config.get_endpoints(category.value)
            for group_name, group_endpoints in endpoints.items():
                if isinstance(group_endpoints, dict):
                    for endpoint_name, path in group_endpoints.items():
                        all_paths.append(path)
        return all_paths
    
    def test_obsolete_setup_create_not_present(self):
        """
        **Validates: Requirements 7.1**
        
        Test that obsolete /cam/setups/create endpoint is not present.
        Should be replaced by POST to /cam/setups.
        """
        all_paths = self._get_all_endpoint_paths()
        
        assert "/cam/setups/create" not in all_paths, \
            "Obsolete endpoint /cam/setups/create should not be present. " \
            "Use POST to /cam/setups instead."
    
    def test_obsolete_setup_modify_not_present(self):
        """
        **Validates: Requirements 7.2**
        
        Test that obsolete /cam/setups/{id}/modify endpoint is not present.
        Should be replaced by PUT to /cam/setups/{setup_id}.
        """
        all_paths = self._get_all_endpoint_paths()
        
        # Check for various forms of the obsolete pattern
        obsolete_patterns = [
            "/cam/setups/{id}/modify",
            "/cam/setups/{setup_id}/modify",
        ]
        
        for pattern in obsolete_patterns:
            assert pattern not in all_paths, \
                f"Obsolete endpoint {pattern} should not be present. " \
                "Use PUT to /cam/setups/{{setup_id}} instead."
    
    def test_obsolete_setup_delete_not_present(self):
        """
        **Validates: Requirements 7.3**
        
        Test that obsolete /cam/setups/{id}/delete endpoint is not present.
        Should be replaced by DELETE to /cam/setups/{setup_id}.
        """
        all_paths = self._get_all_endpoint_paths()
        
        # Check for various forms of the obsolete pattern
        obsolete_patterns = [
            "/cam/setups/{id}/delete",
            "/cam/setups/{setup_id}/delete",
        ]
        
        for pattern in obsolete_patterns:
            assert pattern not in all_paths, \
                f"Obsolete endpoint {pattern} should not be present. " \
                "Use DELETE to /cam/setups/{{setup_id}} instead."
    
    def test_obsolete_toolpath_singular_not_present(self):
        """
        **Validates: Requirements 7.4**
        
        Test that obsolete /cam/toolpath/{id} (singular form) endpoint is not present.
        Should be replaced by /cam/toolpaths/{toolpath_id} (plural form).
        """
        all_paths = self._get_all_endpoint_paths()
        
        # Check for singular form patterns
        for path in all_paths:
            assert "/cam/toolpath/" not in path or "/cam/toolpaths/" in path, \
                f"Obsolete singular endpoint pattern found: {path}. " \
                "Use plural form /cam/toolpaths/{{toolpath_id}} instead."
    
    def test_obsolete_tool_library_create_not_present(self):
        """
        **Validates: Requirements 7.5**
        
        Test that obsolete /tool-libraries/{library_id}/tools/create endpoint is not present.
        Should be replaced by POST to /tool-libraries/tools.
        """
        all_paths = self._get_all_endpoint_paths()
        
        # Check for obsolete create pattern
        obsolete_patterns = [
            "/tool-libraries/{library_id}/tools/create",
            "/tool-libraries/tools/create",
        ]
        
        for pattern in obsolete_patterns:
            assert pattern not in all_paths, \
                f"Obsolete endpoint {pattern} should not be present. " \
                "Use POST to /tool-libraries/tools instead."
    
    def test_obsolete_tool_modify_not_present(self):
        """
        **Validates: Requirements 7.6**
        
        Test that obsolete /tool-libraries/tools/{tool_id}/modify endpoint is not present.
        Should be replaced by PUT to /tool-libraries/tools/{tool_id}.
        """
        all_paths = self._get_all_endpoint_paths()
        
        # Check for obsolete modify pattern
        obsolete_patterns = [
            "/tool-libraries/tools/{tool_id}/modify",
            "/tool-libraries/tools/{id}/modify",
        ]
        
        for pattern in obsolete_patterns:
            assert pattern not in all_paths, \
                f"Obsolete endpoint {pattern} should not be present. " \
                "Use PUT to /tool-libraries/tools/{{tool_id}} instead."
    
    def test_obsolete_tool_search_path_not_present(self):
        """
        **Validates: Requirements 7.6**
        
        Test that obsolete /tool-libraries/tools/search endpoint is not present.
        Should be replaced by /tool-libraries/search.
        """
        all_paths = self._get_all_endpoint_paths()
        
        assert "/tool-libraries/tools/search" not in all_paths, \
            "Obsolete endpoint /tool-libraries/tools/search should not be present. " \
            "Use /tool-libraries/search instead."
    
    def test_no_generic_id_placeholders_in_manufacture(self):
        """
        **Validates: Requirements 7.1-7.6**
        
        Test that no MANUFACTURE endpoints use generic {id} placeholder.
        All should use entity-specific placeholders.
        """
        import re
        
        endpoints = self.config.get_endpoints("manufacture")
        
        for group_name, group_endpoints in endpoints.items():
            if isinstance(group_endpoints, dict):
                for endpoint_name, path in group_endpoints.items():
                    placeholders = re.findall(r'\{([^}]+)\}', path)
                    
                    assert "id" not in placeholders, \
                        f"Generic {{id}} placeholder found in manufacture.{group_name}.{endpoint_name}: {path}. " \
                        "Use entity-specific placeholder like {{setup_id}}, {{toolpath_id}}, etc."
    
    def test_all_manufacture_endpoints_use_correct_patterns(self):
        """
        **Validates: Requirements 7.1-7.6**
        
        Test that all MANUFACTURE endpoints use correct RESTful patterns.
        """
        endpoints = self.config.get_endpoints("manufacture")
        
        # Verify setups use correct patterns
        setups = endpoints.get("setups", {})
        assert "/cam/setups" in setups.values(), "Missing /cam/setups endpoint"
        assert "/cam/setups/{setup_id}" in setups.values(), "Missing /cam/setups/{setup_id} endpoint"
        
        # Verify toolpaths use correct patterns (plural form)
        toolpaths = endpoints.get("toolpaths", {})
        for path in toolpaths.values():
            if "{" in path:
                assert "/cam/toolpaths/" in path, \
                    f"Toolpath endpoint should use plural form: {path}"
        
        # Verify tool_libraries use correct patterns
        tool_libraries = endpoints.get("tool_libraries", {})
        assert "/tool-libraries" in tool_libraries.values(), "Missing /tool-libraries endpoint"
        assert "/tool-libraries/tools" in tool_libraries.values(), "Missing /tool-libraries/tools endpoint"


if HYPOTHESIS_AVAILABLE:
    class TestValidationGuidancePropertyBased:
        """
        Property-based tests using Hypothesis for validation guidance provision.
        
        **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
        **Validates: Requirements 8.3**
        """
        
        def setup_method(self):
            """Set up test fixtures."""
            self.config = ConfigurationManager()
        
        # Define invalid patterns with expected guidance keywords
        INVALID_PATTERNS_WITH_GUIDANCE = [
            ("/cam/setup/{setup_id}", ["setups", "plural"]),
            ("/cam/toolpath/{toolpath_id}", ["toolpaths", "plural"]),
            ("/cam/operation/{operation_id}", ["operations", "plural"]),
            ("/cam/tool/{tool_id}", ["tools", "plural"]),
            ("/tool-library/{library_id}", ["tool-libraries", "plural"]),
            ("/cam/setups/{id}", ["setup_id", "toolpath_id", "operation_id", "tool_id", "library_id"]),
            ("/cam/setups/{setup}", ["setup_id"]),
            ("/cam/toolpaths/{toolpath}", ["toolpath_id"]),
            ("/cam/operations/{operation}", ["operation_id"]),
            ("/cam/tools/{tool}", ["tool_id"]),
            ("/tool-libraries/{library}", ["library_id"]),
        ]
        
        @given(st.sampled_from(INVALID_PATTERNS_WITH_GUIDANCE))
        @settings(max_examples=100)
        def test_all_invalid_patterns_have_relevant_guidance(self, pattern_and_keywords):
            """
            **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
            **Validates: Requirements 8.3**
            
            *For any* invalid endpoint pattern, validation should provide relevant guidance.
            """
            invalid_path, expected_keywords = pattern_and_keywords
            test_config = ConfigurationManager()
            test_config.update_endpoint("manufacture", "test_group", "test_endpoint", invalid_path)
            
            result = test_config.validate_config_detailed()
            
            # Should have guidance
            assert len(result['resolution_guidance']) > 0, \
                f"Should have guidance for invalid path '{invalid_path}'"
            
            # Guidance should contain at least one expected keyword
            guidance_text = ' '.join(result['resolution_guidance']).lower()
            has_relevant_keyword = any(
                keyword.lower() in guidance_text 
                for keyword in expected_keywords
            )
            assert has_relevant_keyword, \
                f"Guidance for '{invalid_path}' should contain one of {expected_keywords} but got: {result['resolution_guidance']}"
        
        @given(st.sampled_from([
            "/cam/setup/{setup_id}",
            "/cam/toolpath/{toolpath_id}",
            "/cam/operation/{operation_id}",
            "/cam/tool/{tool_id}",
            "/tool-library/{library_id}",
            "/cam/setups/{id}",
            "/cam/setups/{setup}",
            "/cam/toolpaths/{toolpath}",
        ]))
        @settings(max_examples=100)
        def test_guidance_is_always_non_empty_string(self, invalid_path):
            """
            **Feature: config-endpoint-sync, Property 4: Validation Guidance Provision**
            **Validates: Requirements 8.3**
            
            *For any* validation issue, guidance should be a non-empty string.
            """
            test_config = ConfigurationManager()
            test_config.update_endpoint("manufacture", "test_group", "test_endpoint", invalid_path)
            
            result = test_config.validate_config_detailed()
            
            # All guidance items should be non-empty strings
            for guidance in result['resolution_guidance']:
                assert isinstance(guidance, str), \
                    f"Guidance should be string but got {type(guidance)}"
                assert len(guidance.strip()) > 0, \
                    f"Guidance should not be empty for path '{invalid_path}'"
