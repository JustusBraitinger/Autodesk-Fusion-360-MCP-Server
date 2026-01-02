#!/usr/bin/env python3
"""
Unit tests for Server/core/loader.py

Tests the dynamic module discovery and loading system including
dependency validation and error handling for module loading.

Requirements: 7.1, 7.2, 7.4
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any

# Add Server directory to path for imports
server_path = os.path.join(os.path.dirname(__file__), "..", "Server")
if server_path not in sys.path:
    sys.path.insert(0, server_path)

from core.loader import (
    ModuleLoader, ModuleInfo, ModuleError, ErrorSeverity,
    ModuleLoadError, DependencyError, ModuleStructureError,
    set_mcp_instance, load_all_modules, load_category,
    get_loaded_modules, get_failed_modules, validate_module,
    get_error_report, get_health_status
)


class TestModuleLoader:
    """Test cases for the ModuleLoader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory structure for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.tools_dir = self.temp_dir / "tools"
        self.prompts_dir = self.temp_dir / "prompts"
        
        # Create directory structure
        self.tools_dir.mkdir(parents=True)
        self.prompts_dir.mkdir(parents=True)
        
        # Create category directories
        (self.tools_dir / "cad").mkdir()
        (self.tools_dir / "cam").mkdir()
        (self.tools_dir / "utility").mkdir()
        (self.prompts_dir / "general").mkdir()
        
        # Create __init__.py files
        (self.tools_dir / "__init__.py").touch()
        (self.tools_dir / "cad" / "__init__.py").touch()
        (self.tools_dir / "cam" / "__init__.py").touch()
        (self.tools_dir / "utility" / "__init__.py").touch()
        (self.prompts_dir / "__init__.py").touch()
        (self.prompts_dir / "general" / "__init__.py").touch()
        
        self.loader = ModuleLoader(str(self.temp_dir))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_tool_module(self, category: str, name: str, content: str = None):
        """Create a test tool module file."""
        if content is None:
            content = f'''
"""Test {name} module."""

def register_tools(mcp_instance):
    """Register tools with MCP instance."""
    pass

def test_tool_{name}(param: str) -> str:
    """Test tool function."""
    return f"result_{name}_" + param
'''
        
        module_file = self.tools_dir / category / f"{name}.py"
        module_file.write_text(content)
        return module_file
    
    def create_test_prompt_module(self, category: str, name: str, content: str = None):
        """Create a test prompt module file."""
        if content is None:
            content = f'''
"""Test {name} prompt module."""

def register_prompts():
    """Register prompts."""
    pass

def test_prompt_{name}(template: str) -> str:
    """Test prompt function."""
    return f"prompt_{name}_" + template
'''
        
        module_file = self.prompts_dir / category / f"{name}.py"
        module_file.write_text(content)
        return module_file
    
    def test_module_loader_initialization(self):
        """Test ModuleLoader initialization."""
        assert self.loader.base_path == self.temp_dir
        assert self.loader.tools_path == self.tools_dir
        assert self.loader.prompts_path == self.prompts_dir
        assert len(self.loader._loaded_modules) == 0
        assert len(self.loader._failed_modules) == 0
        assert len(self.loader._module_errors) == 0
    
    def test_module_loader_default_path(self):
        """Test ModuleLoader with default path."""
        loader = ModuleLoader()
        # Should default to Server directory
        assert "Server" in str(loader.base_path)
    
    def test_set_error_recovery(self):
        """Test error recovery mode setting."""
        assert self.loader._error_recovery_enabled is True
        
        self.loader.set_error_recovery(False)
        assert self.loader._error_recovery_enabled is False
        
        self.loader.set_error_recovery(True)
        assert self.loader._error_recovery_enabled is True
    
    def test_set_mcp_instance(self):
        """Test setting MCP instance."""
        mock_mcp = MagicMock()
        self.loader.set_mcp_instance(mock_mcp)
        assert self.loader._mcp_instance == mock_mcp
    
    def test_discover_modules_tools(self):
        """Test discovering tool modules."""
        # Create test modules
        self.create_test_tool_module("cad", "geometry")
        self.create_test_tool_module("cam", "toolpaths")
        
        modules = self.loader.discover_modules()
        
        assert len(modules) >= 2
        assert "tools.cad.geometry" in modules
        assert "tools.cam.toolpaths" in modules
    
    def test_discover_modules_prompts(self):
        """Test discovering prompt modules."""
        # Create test modules
        self.create_test_prompt_module("general", "templates")
        
        modules = self.loader.discover_modules()
        
        assert "prompts.general.templates" in modules
    
    def test_discover_modules_category_filter(self):
        """Test discovering modules with category filter."""
        # Create test modules
        self.create_test_tool_module("cad", "geometry")
        self.create_test_tool_module("cam", "toolpaths")
        
        cad_modules = self.loader.discover_modules("cad")
        cam_modules = self.loader.discover_modules("cam")
        
        assert len(cad_modules) == 1
        assert len(cam_modules) == 1
        assert "tools.cad.geometry" in cad_modules
        assert "tools.cam.toolpaths" in cam_modules
    
    def test_discover_modules_ignores_private_files(self):
        """Test that discovery ignores private files."""
        # Create private files (starting with _)
        (self.tools_dir / "cad" / "_private.py").write_text("# Private module")
        (self.tools_dir / "_private_category").mkdir()
        
        modules = self.loader.discover_modules()
        
        # Should not include private files
        private_modules = [m for m in modules if "_private" in m]
        assert len(private_modules) == 0
    
    def test_discover_modules_nonexistent_directory(self):
        """Test discovery with non-existent directory."""
        # Remove tools directory
        shutil.rmtree(self.tools_dir)
        
        modules = self.loader.discover_modules()
        
        # Should handle gracefully and return empty list for tools
        assert isinstance(modules, list)
    
    @patch('core.loader.importlib.import_module')
    def test_load_module_success(self, mock_import):
        """Test successful module loading."""
        # Create test module
        self.create_test_tool_module("cad", "geometry")
        
        # Mock the imported module
        mock_module = MagicMock()
        mock_module.__name__ = "tools.cad.geometry"
        mock_module.register_tools = MagicMock()
        mock_import.return_value = mock_module
        
        # Set MCP instance
        mock_mcp = MagicMock()
        self.loader.set_mcp_instance(mock_mcp)
        
        module_info = self.loader.load_module("tools.cad.geometry")
        
        assert module_info is not None
        assert module_info.name == "geometry"
        assert module_info.category == "cad"
        assert module_info.loaded is True
        assert module_info.module_path == "tools.cad.geometry"
        assert module_info.load_time is not None
        assert module_info.load_time > 0
    
    @patch('core.loader.importlib.import_module')
    def test_load_module_import_error(self, mock_import):
        """Test module loading with import error."""
        mock_import.side_effect = ImportError("No module named 'nonexistent'")
        
        module_info = self.loader.load_module("tools.cad.nonexistent")
        
        assert module_info is not None
        assert module_info.loaded is False
        assert module_info.error is not None
        assert "Failed to import module" in module_info.error
        assert len(module_info.detailed_errors) > 0
        assert module_info.detailed_errors[0].error_type == "IMPORT_ERROR"
    
    def test_load_module_invalid_path_format(self):
        """Test loading module with invalid path format."""
        module_info = self.loader.load_module("invalid_path")
        
        assert module_info is not None
        assert module_info.loaded is False
        assert "Invalid module path format" in module_info.error
    
    def test_load_module_invalid_module_type(self):
        """Test loading module with invalid module type."""
        module_info = self.loader.load_module("invalid.cad.geometry")
        
        assert module_info is not None
        assert module_info.loaded is False
        assert "Invalid module type" in module_info.error
    
    @patch('core.loader.importlib.import_module')
    def test_load_module_missing_dependencies(self, mock_import):
        """Test loading module with missing dependencies."""
        # Create module with dependencies
        content = '''
"""Test module with dependencies."""

DEPENDENCIES = ["nonexistent_dependency"]

def register_tools(mcp_instance):
    pass
'''
        self.create_test_tool_module("cad", "geometry", content)
        
        mock_module = MagicMock()
        mock_module.__name__ = "tools.cad.geometry"
        mock_module.DEPENDENCIES = ["nonexistent_dependency"]
        mock_module.register_tools = MagicMock()
        mock_import.return_value = mock_module
        
        module_info = self.loader.load_module("tools.cad.geometry")
        
        # With error recovery enabled, should still load but with errors
        assert module_info is not None
        assert len(module_info.detailed_errors) > 0
        dependency_errors = [e for e in module_info.detailed_errors if e.error_type == "DEPENDENCY_ERROR"]
        assert len(dependency_errors) > 0
    
    @patch('core.loader.importlib.import_module')
    def test_load_module_structure_validation_error(self, mock_import):
        """Test loading module with structure validation error."""
        mock_module = MagicMock()
        mock_module.__name__ = "tools.cad.geometry"
        
        # Create a real object without register_tools to trigger hasattr properly
        class MockModuleWithoutRegisterTools:
            def __init__(self):
                self.__name__ = "tools.cad.geometry"
        
        mock_module_obj = MockModuleWithoutRegisterTools()
        mock_import.return_value = mock_module_obj
        
        module_info = self.loader.load_module("tools.cad.geometry")
        
        # Should still load with error recovery but note the structure issue
        assert module_info is not None
        structure_errors = [e for e in module_info.detailed_errors if e.error_type == "STRUCTURE_ERROR"]
        assert len(structure_errors) > 0
    
    def test_load_all_modules(self):
        """Test loading all discovered modules."""
        # Create test modules
        self.create_test_tool_module("cad", "geometry")
        self.create_test_tool_module("cam", "toolpaths")
        self.create_test_prompt_module("general", "templates")
        
        with patch('core.loader.importlib.import_module') as mock_import:
            # Mock successful imports
            mock_import.return_value = MagicMock()
            
            loaded_modules = self.loader.load_all_modules()
            
            assert isinstance(loaded_modules, dict)
            assert len(loaded_modules) >= 3
    
    def test_load_category(self):
        """Test loading modules for specific category."""
        # Create test modules
        self.create_test_tool_module("cad", "geometry")
        self.create_test_tool_module("cam", "toolpaths")
        
        with patch('core.loader.importlib.import_module') as mock_import:
            mock_import.return_value = MagicMock()
            
            cad_modules = self.loader.load_category("cad")
            
            assert isinstance(cad_modules, dict)
            assert len(cad_modules) == 1
            assert any("cad" in path for path in cad_modules.keys())
    
    def test_get_loaded_modules(self):
        """Test getting list of loaded modules."""
        # Manually add some test modules
        module_info = ModuleInfo(
            name="test_module",
            category="cad",
            tools=[],
            prompts=[],
            loaded=True,
            dependencies=[],
            module_path="tools.cad.test_module"
        )
        self.loader._loaded_modules["tools.cad.test_module"] = module_info
        
        loaded = self.loader.get_loaded_modules()
        
        assert len(loaded) == 1
        assert loaded[0].name == "test_module"
        assert loaded[0].loaded is True
    
    def test_get_failed_modules(self):
        """Test getting failed modules."""
        self.loader._failed_modules["failed.module"] = "Test error"
        
        failed = self.loader.get_failed_modules()
        
        assert len(failed) == 1
        assert "failed.module" in failed
        assert failed["failed.module"] == "Test error"
    
    def test_validate_module_success(self):
        """Test successful module validation."""
        # Add a loaded module
        module_info = ModuleInfo(
            name="test_module",
            category="cad",
            tools=[],
            prompts=[],
            loaded=True,
            dependencies=[],
            module_path="tools.cad.test_module"
        )
        self.loader._loaded_modules["tools.cad.test_module"] = module_info
        
        result = self.loader.validate_module("tools.cad.test_module")
        assert result is True
    
    def test_validate_module_not_loaded(self):
        """Test validation of non-loaded module."""
        result = self.loader.validate_module("nonexistent.module")
        assert result is False
    
    def test_validate_module_failed_to_load(self):
        """Test validation of module that failed to load."""
        # Add a failed module
        module_info = ModuleInfo(
            name="failed_module",
            category="cad",
            tools=[],
            prompts=[],
            loaded=False,
            dependencies=[],
            module_path="tools.cad.failed_module"
        )
        self.loader._loaded_modules["tools.cad.failed_module"] = module_info
        
        result = self.loader.validate_module("tools.cad.failed_module")
        assert result is False
    
    def test_get_categories(self):
        """Test getting categories from loaded modules."""
        # Add modules from different categories
        for category in ["cad", "cam", "utility"]:
            module_info = ModuleInfo(
                name=f"test_{category}",
                category=category,
                tools=[],
                prompts=[],
                loaded=True,
                dependencies=[],
                module_path=f"tools.{category}.test"
            )
            self.loader._loaded_modules[f"tools.{category}.test"] = module_info
        
        categories = self.loader.get_categories()
        
        assert isinstance(categories, set)
        assert "cad" in categories
        assert "cam" in categories
        assert "utility" in categories
    
    def test_get_module_count(self):
        """Test getting module count."""
        # Add test modules
        for i, category in enumerate(["cad", "cam"]):
            module_info = ModuleInfo(
                name=f"test_{i}",
                category=category,
                tools=[],
                prompts=[],
                loaded=True,
                dependencies=[],
                module_path=f"tools.{category}.test_{i}"
            )
            self.loader._loaded_modules[f"tools.{category}.test_{i}"] = module_info
        
        total_count = self.loader.get_module_count()
        cad_count = self.loader.get_module_count("cad")
        cam_count = self.loader.get_module_count("cam")
        
        assert total_count == 2
        assert cad_count == 1
        assert cam_count == 1
    
    def test_get_health_status(self):
        """Test getting health status."""
        # Add a successful module
        success_module = ModuleInfo(
            name="success",
            category="cad",
            tools=[],
            prompts=[],
            loaded=True,
            dependencies=[],
            module_path="tools.cad.success"
        )
        self.loader._loaded_modules["tools.cad.success"] = success_module
        
        # Add a failed module
        failed_module = ModuleInfo(
            name="failed",
            category="cam",
            tools=[],
            prompts=[],
            loaded=False,
            dependencies=[],
            module_path="tools.cam.failed"
        )
        self.loader._loaded_modules["tools.cam.failed"] = failed_module
        
        health = self.loader.get_health_status()
        
        assert isinstance(health, dict)
        assert "health" in health
        assert "total_modules" in health
        assert "loaded_modules" in health
        assert "failed_modules" in health
        assert health["total_modules"] == 2
        assert health["loaded_modules"] == 1
        assert health["failed_modules"] == 1
    
    def test_clear_errors(self):
        """Test clearing errors."""
        # Add some errors
        error = ModuleError(
            module_path="test.module",
            error_type="TEST_ERROR",
            error_message="Test error",
            severity=ErrorSeverity.ERROR
        )
        self.loader._module_errors.append(error)
        
        assert len(self.loader._module_errors) == 1
        
        self.loader.clear_errors()
        
        assert len(self.loader._module_errors) == 0
    
    def test_get_error_report(self):
        """Test getting error report."""
        # Add some errors
        error1 = ModuleError(
            module_path="test.module1",
            error_type="IMPORT_ERROR",
            error_message="Import failed",
            severity=ErrorSeverity.ERROR
        )
        error2 = ModuleError(
            module_path="test.module2",
            error_type="DEPENDENCY_ERROR",
            error_message="Dependency missing",
            severity=ErrorSeverity.WARNING
        )
        self.loader._module_errors.extend([error1, error2])
        
        report = self.loader.get_error_report()
        
        assert isinstance(report, dict)
        assert "total_errors" in report
        assert "error_counts" in report
        assert "errors_by_type" in report
        assert report["total_errors"] == 2
        assert "error" in report["error_counts"]
        assert "warning" in report["error_counts"]


class TestGlobalLoaderFunctions:
    """Test global loader functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset global loader state
        from core.loader import _loader
        _loader._loaded_modules.clear()
        _loader._failed_modules.clear()
        _loader._module_errors.clear()
    
    def test_set_mcp_instance_global(self):
        """Test setting MCP instance globally."""
        mock_mcp = MagicMock()
        set_mcp_instance(mock_mcp)
        
        from core.loader import _loader
        assert _loader._mcp_instance == mock_mcp
    
    @patch('core.loader._loader.load_all_modules')
    def test_load_all_modules_global(self, mock_load_all):
        """Test global load_all_modules function."""
        mock_load_all.return_value = {"test": "result"}
        
        result = load_all_modules()
        
        assert result == {"test": "result"}
        mock_load_all.assert_called_once()
    
    @patch('core.loader._loader.load_category')
    def test_load_category_global(self, mock_load_category):
        """Test global load_category function."""
        mock_load_category.return_value = {"test": "result"}
        
        result = load_category("cad")
        
        assert result == {"test": "result"}
        mock_load_category.assert_called_once_with("cad")
    
    @patch('core.loader._loader.get_loaded_modules')
    def test_get_loaded_modules_global(self, mock_get_loaded):
        """Test global get_loaded_modules function."""
        mock_get_loaded.return_value = ["module1", "module2"]
        
        result = get_loaded_modules()
        
        assert result == ["module1", "module2"]
        mock_get_loaded.assert_called_once()
    
    @patch('core.loader._loader.get_failed_modules')
    def test_get_failed_modules_global(self, mock_get_failed):
        """Test global get_failed_modules function."""
        mock_get_failed.return_value = {"failed": "error"}
        
        result = get_failed_modules()
        
        assert result == {"failed": "error"}
        mock_get_failed.assert_called_once()
    
    @patch('core.loader._loader.validate_module')
    def test_validate_module_global(self, mock_validate):
        """Test global validate_module function."""
        mock_validate.return_value = True
        
        result = validate_module("test.module")
        
        assert result is True
        mock_validate.assert_called_once_with("test.module")
    
    @patch('core.loader._loader.get_error_report')
    def test_get_error_report_global(self, mock_get_report):
        """Test global get_error_report function."""
        mock_get_report.return_value = {"errors": 0}
        
        result = get_error_report()
        
        assert result == {"errors": 0}
        mock_get_report.assert_called_once()
    
    @patch('core.loader._loader.get_health_status')
    def test_get_health_status_global(self, mock_get_health):
        """Test global get_health_status function."""
        mock_get_health.return_value = {"health": "HEALTHY"}
        
        result = get_health_status()
        
        assert result == {"health": "HEALTHY"}
        mock_get_health.assert_called_once()


class TestErrorClasses:
    """Test custom error classes."""
    
    def test_module_load_error(self):
        """Test ModuleLoadError exception."""
        error = ModuleLoadError(
            "Test error",
            module_path="test.module",
            error_type="TEST_ERROR",
            severity=ErrorSeverity.ERROR,
            suggestions=["Fix this", "Try that"]
        )
        
        assert str(error) == "Test error"
        assert error.module_path == "test.module"
        assert error.error_type == "TEST_ERROR"
        assert error.severity == ErrorSeverity.ERROR
        assert error.suggestions == ["Fix this", "Try that"]
    
    def test_dependency_error(self):
        """Test DependencyError exception."""
        error = DependencyError(
            "Missing dependencies",
            module_path="test.module",
            missing_deps=["dep1", "dep2"]
        )
        
        assert str(error) == "Missing dependencies"
        assert error.module_path == "test.module"
        assert error.error_type == "DEPENDENCY_ERROR"
        assert error.severity == ErrorSeverity.ERROR
        assert error.missing_dependencies == ["dep1", "dep2"]
    
    def test_module_structure_error(self):
        """Test ModuleStructureError exception."""
        error = ModuleStructureError(
            "Invalid structure",
            module_path="test.module"
        )
        
        assert str(error) == "Invalid structure"
        assert error.module_path == "test.module"
        assert error.error_type == "STRUCTURE_ERROR"
        assert error.severity == ErrorSeverity.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])