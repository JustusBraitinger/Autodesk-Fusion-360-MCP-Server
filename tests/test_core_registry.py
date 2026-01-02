#!/usr/bin/env python3
"""
Unit tests for Server/core/registry.py

Tests the tool and prompt registration system including dependency validation
and category-based organization.

Requirements: 7.1, 7.2, 7.4
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from typing import List, Optional

# Add Server directory to path for imports
server_path = os.path.join(os.path.dirname(__file__), "..", "Server")
if server_path not in sys.path:
    sys.path.insert(0, server_path)

from core.registry import (
    ToolRegistry, ToolInfo, PromptInfo,
    register_tool, register_prompt, get_tools, get_prompts,
    get_tool_by_name, get_prompt_by_name, validate_dependencies,
    get_categories, get_tool_count, get_prompt_count
)


class TestToolRegistry:
    """Test cases for the ToolRegistry class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        
        # Create mock tool functions
        def mock_tool_1(param1: str, param2: int = 10) -> dict:
            """Mock tool function 1."""
            return {"result": f"{param1}_{param2}"}
            
        def mock_tool_2(data: dict) -> bool:
            """Mock tool function 2."""
            return True
            
        def mock_prompt_1(template: str) -> str:
            """Mock prompt function 1."""
            return f"Prompt: {template}"
            
        self.mock_tool_1 = mock_tool_1
        self.mock_tool_2 = mock_tool_2
        self.mock_prompt_1 = mock_prompt_1
    
    def test_register_tool_basic(self):
        """Test basic tool registration."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        
        tools = self.registry.get_tools()
        assert len(tools) == 1
        
        tool = tools[0]
        assert tool.name == "mock_tool_1"
        assert tool.category == "cad"
        assert tool.function == self.mock_tool_1
        assert "Mock tool function 1." in tool.description
        assert len(tool.dependencies) == 0
    
    def test_register_tool_with_dependencies(self):
        """Test tool registration with dependencies."""
        dependencies = ["dependency1", "dependency2"]
        self.registry.register_tool(self.mock_tool_1, "cam", dependencies)
        
        tool = self.registry.get_tool_by_name("mock_tool_1")
        assert tool is not None
        assert tool.dependencies == dependencies
    
    def test_register_tool_parameters_extraction(self):
        """Test that tool parameters are correctly extracted."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        
        tool = self.registry.get_tool_by_name("mock_tool_1")
        assert tool is not None
        assert "param1" in tool.parameters
        assert "param2" in tool.parameters
        
        param1 = tool.parameters["param1"]
        assert param1["type"] == str
        assert param1["default"] is None
        
        param2 = tool.parameters["param2"]
        assert param2["type"] == int
        assert param2["default"] == 10
    
    def test_register_tool_category_tracking(self):
        """Test that tools are properly tracked by category."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        self.registry.register_tool(self.mock_tool_2, "cam")
        
        cad_tools = self.registry.get_tools("cad")
        cam_tools = self.registry.get_tools("cam")
        
        assert len(cad_tools) == 1
        assert len(cam_tools) == 1
        assert cad_tools[0].name == "mock_tool_1"
        assert cam_tools[0].name == "mock_tool_2"
    
    def test_register_tool_case_insensitive_category(self):
        """Test that category names are normalized to lowercase."""
        self.registry.register_tool(self.mock_tool_1, "CAD")
        
        tool = self.registry.get_tool_by_name("mock_tool_1")
        assert tool.category == "cad"
        
        cad_tools = self.registry.get_tools("cad")
        assert len(cad_tools) == 1
    
    def test_register_prompt_basic(self):
        """Test basic prompt registration."""
        self.registry.register_prompt(self.mock_prompt_1, "general")
        
        prompts = self.registry.get_prompts()
        assert len(prompts) == 1
        
        prompt = prompts[0]
        assert prompt.name == "mock_prompt_1"
        assert prompt.category == "general"
        assert prompt.function == self.mock_prompt_1
        assert "Mock prompt function 1." in prompt.description
    
    def test_register_prompt_parameters_extraction(self):
        """Test that prompt parameters are correctly extracted."""
        self.registry.register_prompt(self.mock_prompt_1, "general")
        
        prompt = self.registry.get_prompt_by_name("mock_prompt_1")
        assert prompt is not None
        assert "template" in prompt.parameters
        
        template_param = prompt.parameters["template"]
        assert template_param["type"] == str
        assert template_param["default"] is None
    
    def test_get_tools_all_categories(self):
        """Test getting all tools regardless of category."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        self.registry.register_tool(self.mock_tool_2, "cam")
        
        all_tools = self.registry.get_tools()
        assert len(all_tools) == 2
        
        tool_names = {tool.name for tool in all_tools}
        assert "mock_tool_1" in tool_names
        assert "mock_tool_2" in tool_names
    
    def test_get_tools_by_category(self):
        """Test getting tools filtered by category."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        self.registry.register_tool(self.mock_tool_2, "cam")
        
        cad_tools = self.registry.get_tools("cad")
        cam_tools = self.registry.get_tools("cam")
        utility_tools = self.registry.get_tools("utility")
        
        assert len(cad_tools) == 1
        assert len(cam_tools) == 1
        assert len(utility_tools) == 0
        
        assert cad_tools[0].name == "mock_tool_1"
        assert cam_tools[0].name == "mock_tool_2"
    
    def test_get_tools_unknown_category(self):
        """Test getting tools for unknown category."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        
        unknown_tools = self.registry.get_tools("unknown")
        assert len(unknown_tools) == 0
    
    def test_get_prompts_by_category(self):
        """Test getting prompts filtered by category."""
        self.registry.register_prompt(self.mock_prompt_1, "general")
        
        general_prompts = self.registry.get_prompts("general")
        specific_prompts = self.registry.get_prompts("specific")
        
        assert len(general_prompts) == 1
        assert len(specific_prompts) == 0
        assert general_prompts[0].name == "mock_prompt_1"
    
    def test_get_tool_by_name_exists(self):
        """Test getting existing tool by name."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        
        tool = self.registry.get_tool_by_name("mock_tool_1")
        assert tool is not None
        assert tool.name == "mock_tool_1"
        assert tool.function == self.mock_tool_1
    
    def test_get_tool_by_name_not_exists(self):
        """Test getting non-existing tool by name."""
        tool = self.registry.get_tool_by_name("nonexistent_tool")
        assert tool is None
    
    def test_get_prompt_by_name_exists(self):
        """Test getting existing prompt by name."""
        self.registry.register_prompt(self.mock_prompt_1, "general")
        
        prompt = self.registry.get_prompt_by_name("mock_prompt_1")
        assert prompt is not None
        assert prompt.name == "mock_prompt_1"
        assert prompt.function == self.mock_prompt_1
    
    def test_get_prompt_by_name_not_exists(self):
        """Test getting non-existing prompt by name."""
        prompt = self.registry.get_prompt_by_name("nonexistent_prompt")
        assert prompt is None
    
    def test_validate_dependencies_satisfied(self):
        """Test dependency validation when all dependencies are satisfied."""
        # Register dependency first
        self.registry.register_tool(self.mock_tool_1, "cad")
        
        # Register tool with dependency
        self.registry.register_tool(self.mock_tool_2, "cam", ["mock_tool_1"])
        
        result = self.registry.validate_dependencies()
        assert result is True
    
    def test_validate_dependencies_unsatisfied(self):
        """Test dependency validation when dependencies are not satisfied."""
        # Register tool with unmet dependency
        self.registry.register_tool(self.mock_tool_1, "cad", ["nonexistent_dependency"])
        
        result = self.registry.validate_dependencies()
        assert result is False
    
    def test_validate_dependencies_no_dependencies(self):
        """Test dependency validation when no tools have dependencies."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        self.registry.register_tool(self.mock_tool_2, "cam")
        
        result = self.registry.validate_dependencies()
        assert result is True
    
    def test_get_categories(self):
        """Test getting list of available categories."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        self.registry.register_tool(self.mock_tool_2, "cam")
        
        categories = self.registry.get_categories()
        assert isinstance(categories, list)
        assert "cad" in categories
        assert "cam" in categories
        assert "utility" in categories  # Default categories
        assert "debug" in categories
    
    def test_get_tool_count_all(self):
        """Test getting total tool count."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        self.registry.register_tool(self.mock_tool_2, "cam")
        
        count = self.registry.get_tool_count()
        assert count == 2
    
    def test_get_tool_count_by_category(self):
        """Test getting tool count by category."""
        self.registry.register_tool(self.mock_tool_1, "cad")
        self.registry.register_tool(self.mock_tool_2, "cam")
        
        cad_count = self.registry.get_tool_count("cad")
        cam_count = self.registry.get_tool_count("cam")
        utility_count = self.registry.get_tool_count("utility")
        
        assert cad_count == 1
        assert cam_count == 1
        assert utility_count == 0
    
    def test_get_prompt_count_all(self):
        """Test getting total prompt count."""
        self.registry.register_prompt(self.mock_prompt_1, "general")
        
        count = self.registry.get_prompt_count()
        assert count == 1
    
    def test_get_prompt_count_by_category(self):
        """Test getting prompt count by category."""
        self.registry.register_prompt(self.mock_prompt_1, "general")
        
        general_count = self.registry.get_prompt_count("general")
        specific_count = self.registry.get_prompt_count("specific")
        
        assert general_count == 1
        assert specific_count == 0


class TestGlobalRegistryFunctions:
    """Test the global registry functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear global registry state
        from core.registry import _registry
        _registry._tools.clear()
        _registry._prompts.clear()
        _registry._categories = {
            "cad": [],
            "cam": [],
            "utility": [],
            "debug": []
        }
        
        def mock_global_tool(param: str) -> str:
            """Mock global tool."""
            return param
            
        def mock_global_prompt(template: str) -> str:
            """Mock global prompt."""
            return template
            
        self.mock_global_tool = mock_global_tool
        self.mock_global_prompt = mock_global_prompt
    
    def test_global_register_tool(self):
        """Test global tool registration function."""
        register_tool(self.mock_global_tool, "cad")
        
        tools = get_tools()
        assert len(tools) == 1
        assert tools[0].name == "mock_global_tool"
    
    def test_global_register_prompt(self):
        """Test global prompt registration function."""
        register_prompt(self.mock_global_prompt, "general")
        
        prompts = get_prompts()
        assert len(prompts) == 1
        assert prompts[0].name == "mock_global_prompt"
    
    def test_global_get_tools(self):
        """Test global get tools function."""
        register_tool(self.mock_global_tool, "cad")
        
        all_tools = get_tools()
        cad_tools = get_tools("cad")
        cam_tools = get_tools("cam")
        
        assert len(all_tools) == 1
        assert len(cad_tools) == 1
        assert len(cam_tools) == 0
    
    def test_global_get_prompts(self):
        """Test global get prompts function."""
        register_prompt(self.mock_global_prompt, "general")
        
        all_prompts = get_prompts()
        general_prompts = get_prompts("general")
        specific_prompts = get_prompts("specific")
        
        assert len(all_prompts) == 1
        assert len(general_prompts) == 1
        assert len(specific_prompts) == 0
    
    def test_global_get_tool_by_name(self):
        """Test global get tool by name function."""
        register_tool(self.mock_global_tool, "cad")
        
        tool = get_tool_by_name("mock_global_tool")
        assert tool is not None
        assert tool.name == "mock_global_tool"
        
        nonexistent = get_tool_by_name("nonexistent")
        assert nonexistent is None
    
    def test_global_get_prompt_by_name(self):
        """Test global get prompt by name function."""
        register_prompt(self.mock_global_prompt, "general")
        
        prompt = get_prompt_by_name("mock_global_prompt")
        assert prompt is not None
        assert prompt.name == "mock_global_prompt"
        
        nonexistent = get_prompt_by_name("nonexistent")
        assert nonexistent is None
    
    def test_global_validate_dependencies(self):
        """Test global validate dependencies function."""
        register_tool(self.mock_global_tool, "cad")
        
        result = validate_dependencies()
        assert result is True
    
    def test_global_get_categories(self):
        """Test global get categories function."""
        categories = get_categories()
        assert isinstance(categories, list)
        assert len(categories) >= 4  # At least the default categories
    
    def test_global_get_tool_count(self):
        """Test global get tool count function."""
        register_tool(self.mock_global_tool, "cad")
        
        total_count = get_tool_count()
        cad_count = get_tool_count("cad")
        
        assert total_count == 1
        assert cad_count == 1
    
    def test_global_get_prompt_count(self):
        """Test global get prompt count function."""
        register_prompt(self.mock_global_prompt, "general")
        
        total_count = get_prompt_count()
        general_count = get_prompt_count("general")
        
        assert total_count == 1
        assert general_count == 1


class TestRegistryEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
    
    def test_register_tool_no_docstring(self):
        """Test registering tool without docstring."""
        def tool_no_doc():
            pass
            
        self.registry.register_tool(tool_no_doc, "cad")
        
        tool = self.registry.get_tool_by_name("tool_no_doc")
        assert tool is not None
        assert "Tool: tool_no_doc" in tool.description
    
    def test_register_tool_no_annotations(self):
        """Test registering tool without type annotations."""
        def tool_no_annotations(param1, param2=None):
            """Tool without annotations."""
            return param1
            
        self.registry.register_tool(tool_no_annotations, "cad")
        
        tool = self.registry.get_tool_by_name("tool_no_annotations")
        assert tool is not None
        assert "param1" in tool.parameters
        assert "param2" in tool.parameters
        
        # Parameters should have "Any" type when no annotation
        assert tool.parameters["param1"]["type"] == "Any"
        assert tool.parameters["param2"]["type"] == "Any"
    
    def test_register_duplicate_tool_name(self):
        """Test registering tools with duplicate names."""
        def tool_1():
            """First tool."""
            pass
            
        def tool_1():  # Same name
            """Second tool."""
            pass
            
        self.registry.register_tool(tool_1, "cad")
        # Second registration should overwrite the first
        self.registry.register_tool(tool_1, "cam")
        
        tool = self.registry.get_tool_by_name("tool_1")
        assert tool is not None
        assert tool.category == "cam"  # Should be the last registered
    
    def test_empty_category_name(self):
        """Test registering with empty category name."""
        def test_tool():
            pass
            
        self.registry.register_tool(test_tool, "")
        
        tool = self.registry.get_tool_by_name("test_tool")
        assert tool is not None
        assert tool.category == ""
        
        # Should be able to retrieve by empty category
        empty_tools = self.registry.get_tools("")
        assert len(empty_tools) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])