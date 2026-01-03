"""
Dynamic module discovery and loading system.

This module provides automatic discovery and loading of tool modules,
with dependency validation and error handling for module loading.
"""

import sys
import importlib
import importlib.util
import logging
import traceback
import time
from typing import List, Dict, Optional, Set, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from .registry import register_tool, register_prompt, validate_dependencies

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for module loading."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ModuleError:
    """Detailed information about a module loading error."""
    module_path: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    traceback: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    dependencies_missing: List[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Information about a loaded module."""
    name: str
    category: str
    tools: List[str]
    prompts: List[str]
    loaded: bool
    dependencies: List[str]
    module_path: str
    error: Optional[str] = None
    detailed_errors: List[ModuleError] = field(default_factory=list)
    load_time: Optional[float] = None


class ModuleLoadError(Exception):
    """Exception raised when module loading fails."""
    
    def __init__(self, message: str, module_path: str = "", error_type: str = "UNKNOWN", 
                 severity: ErrorSeverity = ErrorSeverity.ERROR, suggestions: List[str] = None):
        super().__init__(message)
        self.module_path = module_path
        self.error_type = error_type
        self.severity = severity
        self.suggestions = suggestions or []


class DependencyError(ModuleLoadError):
    """Exception raised when module dependencies are not satisfied."""
    
    def __init__(self, message: str, module_path: str = "", missing_deps: List[str] = None):
        super().__init__(message, module_path, "DEPENDENCY_ERROR", ErrorSeverity.ERROR)
        self.missing_dependencies = missing_deps or []


class ModuleStructureError(ModuleLoadError):
    """Exception raised when module structure is invalid."""
    
    def __init__(self, message: str, module_path: str = ""):
        super().__init__(message, module_path, "STRUCTURE_ERROR", ErrorSeverity.WARNING)


class ModuleLoader:
    """Dynamic module discovery and loading system."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the module loader.
        
        Args:
            base_path: Base path for module discovery (defaults to Server directory)
        """
        if base_path is None:
            # Default to Server directory relative to this file
            current_dir = Path(__file__).parent.parent
            self.base_path = current_dir
        else:
            self.base_path = Path(base_path)
            
        self.tools_path = self.base_path / "tools"
        self.prompts_path = self.base_path / "prompts"
        
        self._loaded_modules: Dict[str, ModuleInfo] = {}
        self._failed_modules: Dict[str, str] = {}
        self._module_errors: List[ModuleError] = []
        self._mcp_instance = None
        self._error_recovery_enabled = True
        
        logger.info(f"ModuleLoader initialized with base path: {self.base_path}")
        
    def set_error_recovery(self, enabled: bool) -> None:
        """
        Enable or disable error recovery mode.
        
        Args:
            enabled: Whether to enable graceful degradation on errors
        """
        self._error_recovery_enabled = enabled
        logger.info(f"Error recovery {'enabled' if enabled else 'disabled'}")
        
    def _create_error(self, module_path: str, error_type: str, message: str, 
                     severity: ErrorSeverity = ErrorSeverity.ERROR, 
                     exception: Optional[Exception] = None,
                     suggestions: List[str] = None) -> ModuleError:
        """
        Create a detailed error record.
        
        Args:
            module_path: Path of the module that failed
            error_type: Type of error (IMPORT_ERROR, DEPENDENCY_ERROR, etc.)
            message: Error message
            severity: Error severity level
            exception: Original exception if available
            suggestions: List of suggested fixes
            
        Returns:
            ModuleError: Detailed error information
        """
        error = ModuleError(
            module_path=module_path,
            error_type=error_type,
            error_message=message,
            severity=severity,
            suggestions=suggestions or []
        )
        
        if exception:
            error.traceback = traceback.format_exc()
            
        self._module_errors.append(error)
        return error
        
    def _handle_import_error(self, module_path: str, import_error: ImportError) -> ModuleError:
        """
        Handle import errors with detailed analysis and suggestions.
        
        Args:
            module_path: Module path that failed to import
            import_error: The import error
            
        Returns:
            ModuleError: Detailed error information
        """
        error_msg = str(import_error)
        suggestions = []
        
        # Analyze common import error patterns
        if "No module named" in error_msg:
            missing_module = error_msg.split("'")[1] if "'" in error_msg else "unknown"
            suggestions.extend([
                f"Install missing dependency: pip install {missing_module}",
                f"Check if module path is correct: {module_path}",
                "Verify module file exists and has correct permissions"
            ])
        elif "cannot import name" in error_msg:
            suggestions.extend([
                "Check if the imported function/class exists in the target module",
                "Verify there are no circular import dependencies",
                "Check for typos in import statements"
            ])
        elif "relative import" in error_msg:
            suggestions.extend([
                "Use absolute imports instead of relative imports",
                "Ensure __init__.py files exist in all package directories",
                "Check Python path configuration"
            ])
        else:
            suggestions.extend([
                "Check module syntax for errors",
                "Verify all dependencies are installed",
                "Check file permissions and accessibility"
            ])
            
        return self._create_error(
            module_path=module_path,
            error_type="IMPORT_ERROR",
            message=f"Failed to import module: {error_msg}",
            severity=ErrorSeverity.ERROR,
            exception=import_error,
            suggestions=suggestions
        )
        
    def _handle_dependency_error(self, module_path: str, missing_deps: List[str]) -> ModuleError:
        """
        Handle dependency validation errors.
        
        Args:
            module_path: Module path with missing dependencies
            missing_deps: List of missing dependency names
            
        Returns:
            ModuleError: Detailed error information
        """
        suggestions = [
            "Load missing dependencies first",
            "Check if dependency names are correct",
            "Verify dependency modules exist in the expected locations"
        ]
        
        for dep in missing_deps:
            suggestions.append(f"Ensure module '{dep}' is loaded and available")
            
        error = self._create_error(
            module_path=module_path,
            error_type="DEPENDENCY_ERROR",
            message=f"Missing dependencies: {', '.join(missing_deps)}",
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions
        )
        error.dependencies_missing = missing_deps
        return error
        
    def _handle_structure_error(self, module_path: str, structure_issue: str) -> ModuleError:
        """
        Handle module structure validation errors.
        
        Args:
            module_path: Module path with structure issues
            structure_issue: Description of the structure problem
            
        Returns:
            ModuleError: Detailed error information
        """
        suggestions = [
            "Add missing register_tools or register_prompts function",
            "Follow the expected module structure pattern",
            "Check existing working modules for reference",
            "Ensure tool functions have proper decorators"
        ]
        
        return self._create_error(
            module_path=module_path,
            error_type="STRUCTURE_ERROR",
            message=f"Module structure issue: {structure_issue}",
            severity=ErrorSeverity.WARNING,
            suggestions=suggestions
        )
        
    def _log_error_summary(self) -> None:
        """Log a summary of all errors encountered during loading."""
        if not self._module_errors:
            return
            
        error_counts = {}
        for error in self._module_errors:
            error_counts[error.severity] = error_counts.get(error.severity, 0) + 1
            
        logger.error("=== MODULE LOADING ERROR SUMMARY ===")
        for severity, count in error_counts.items():
            logger.error(f"{severity.value.upper()}: {count} errors")
            
        logger.error("=== DETAILED ERRORS ===")
        for error in self._module_errors:
            logger.error(f"[{error.severity.value.upper()}] {error.module_path}: {error.error_message}")
            if error.suggestions:
                logger.error(f"  Suggestions: {'; '.join(error.suggestions)}")
                
    def get_error_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive error report.
        
        Returns:
            dict: Detailed error report with statistics and suggestions
        """
        error_counts = {}
        errors_by_type = {}
        
        for error in self._module_errors:
            # Count by severity
            error_counts[error.severity.value] = error_counts.get(error.severity.value, 0) + 1
            
            # Group by error type
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error)
            
        return {
            "total_errors": len(self._module_errors),
            "error_counts": error_counts,
            "errors_by_type": errors_by_type,
            "failed_modules": len(self._failed_modules),
            "loaded_modules": len([m for m in self._loaded_modules.values() if m.loaded]),
            "recovery_enabled": self._error_recovery_enabled,
            "suggestions": self._get_general_suggestions()
        }
        
    def _get_general_suggestions(self) -> List[str]:
        """Get general suggestions based on error patterns."""
        suggestions = []
        
        if self._module_errors:
            import_errors = [e for e in self._module_errors if e.error_type == "IMPORT_ERROR"]
            dependency_errors = [e for e in self._module_errors if e.error_type == "DEPENDENCY_ERROR"]
            
            if import_errors:
                suggestions.append("Check Python environment and installed packages")
                suggestions.append("Verify module file paths and permissions")
                
            if dependency_errors:
                suggestions.append("Review module loading order")
                suggestions.append("Consider loading dependencies first")
                
        return suggestions
        
    def set_mcp_instance(self, mcp_instance) -> None:
        """
        Set the MCP instance for tool registration.
        
        Args:
            mcp_instance: FastMCP server instance
        """
        self._mcp_instance = mcp_instance
        logger.info("MCP instance set for module loader")
        
    def discover_modules(self, category: Optional[str] = None) -> List[str]:
        """
        Discover available modules in the tools and prompts directories.
        
        Args:
            category: Optional category filter (cad, cam, utility, debug)
            
        Returns:
            list: List of discovered module paths
        """
        logger.info(f"Discovering modules for category: {category}")
        
        discovered_modules = []
        
        # Discover tool modules
        if self.tools_path.exists():
            discovered_modules.extend(self._discover_in_directory(self.tools_path, "tools", category))
        else:
            logger.warning(f"Tools directory not found: {self.tools_path}")
            
        # Discover prompt modules
        if self.prompts_path.exists():
            discovered_modules.extend(self._discover_in_directory(self.prompts_path, "prompts", category))
        else:
            logger.info(f"Prompts directory not found: {self.prompts_path}")
            
        logger.info(f"Discovered {len(discovered_modules)} modules")
        return discovered_modules
        
    def _discover_in_directory(self, directory: Path, module_type: str, category: Optional[str] = None) -> List[str]:
        """
        Discover modules in a specific directory.
        
        Args:
            directory: Directory to search
            module_type: Type of modules (tools or prompts)
            category: Optional category filter
            
        Returns:
            list: List of discovered module paths
        """
        modules = []
        
        try:
            for category_dir in directory.iterdir():
                if not category_dir.is_dir() or category_dir.name.startswith('_'):
                    continue
                    
                # Skip if category filter is specified and doesn't match
                if category and category_dir.name != category:
                    continue
                    
                # Look for Python files in the category directory
                for py_file in category_dir.glob("*.py"):
                    if py_file.name.startswith('_'):
                        continue
                        
                    module_path = f"{module_type}.{category_dir.name}.{py_file.stem}"
                    modules.append(module_path)
                    logger.debug(f"Discovered module: {module_path}")
                    
        except Exception as e:
            logger.error(f"Error discovering modules in {directory}: {e}")
            
        return modules
        
    def load_module(self, module_path: str) -> Optional[ModuleInfo]:
        """
        Load a specific module with comprehensive error handling.
        
        Args:
            module_path: Module path (e.g., "tools.cad.geometry")
            
        Returns:
            ModuleInfo or None: Module information if loaded successfully
        """
        logger.info(f"Loading module: {module_path}")
        
        start_time = time.time()
        
        try:
            # Parse module path
            parts = module_path.split('.')
            if len(parts) < 3:
                raise ModuleStructureError(f"Invalid module path format: {module_path}", module_path)
                
            module_type = parts[0]  # tools or prompts
            category = parts[1]     # cad, cam, utility, debug
            module_name = parts[2]  # geometry, sketching, etc.
            
            # Validate module type
            if module_type not in ["tools", "prompts"]:
                raise ModuleStructureError(f"Invalid module type: {module_type}", module_path)
                
            # Import the module with detailed error handling
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                error = self._handle_import_error(module_path, e)
                if not self._error_recovery_enabled:
                    raise ModuleLoadError(error.error_message, module_path, error.error_type)
                    
                # Create failed module info for graceful degradation
                return self._create_failed_module_info(module_path, error)
                
            # Validate module structure
            structure_error = None
            try:
                self._validate_module_structure(module, module_type)
            except ModuleStructureError as e:
                structure_error = self._handle_structure_error(module_path, str(e))
                if not self._error_recovery_enabled:
                    raise
                # Continue loading despite structure issues
                
            # Create module info
            module_info = ModuleInfo(
                name=module_name,
                category=category,
                tools=[],
                prompts=[],
                loaded=False,
                dependencies=getattr(module, 'DEPENDENCIES', []),
                module_path=module_path,
                load_time=time.time() - start_time
            )
            
            # Check dependencies before registration
            missing_deps = self._check_dependencies(module_info.dependencies)
            if missing_deps:
                error = self._handle_dependency_error(module_path, missing_deps)
                if not self._error_recovery_enabled:
                    raise DependencyError(error.error_message, module_path, missing_deps)
                    
                # Add error to module info but continue
                module_info.detailed_errors.append(error)
                logger.warning(f"Module {module_path} has missing dependencies but continuing due to error recovery")
            
            # Add structure error if it occurred
            if structure_error:
                module_info.detailed_errors.append(structure_error)
                
            # Register tools/prompts based on module type
            try:
                if module_type == "tools":
                    self._register_tools_from_module(module, category, module_info)
                elif module_type == "prompts":
                    self._register_prompts_from_module(module, category, module_info)
            except Exception as e:
                error = self._create_error(
                    module_path=module_path,
                    error_type="REGISTRATION_ERROR",
                    message=f"Failed to register {module_type}: {str(e)}",
                    severity=ErrorSeverity.ERROR,
                    exception=e,
                    suggestions=[
                        f"Check {module_type} registration function implementation",
                        "Verify MCP instance is properly set",
                        "Check for syntax errors in tool/prompt definitions"
                    ]
                )
                
                if not self._error_recovery_enabled:
                    raise ModuleLoadError(error.error_message, module_path, error.error_type)
                    
                module_info.detailed_errors.append(error)
                
            module_info.loaded = True
            module_info.load_time = time.time() - start_time
            self._loaded_modules[module_path] = module_info
            
            logger.info(f"Successfully loaded module: {module_path} in {module_info.load_time:.3f}s")
            return module_info
            
        except Exception as e:
            load_time = time.time() - start_time
            
            # Create comprehensive error information
            if not isinstance(e, ModuleLoadError):
                error = self._create_error(
                    module_path=module_path,
                    error_type="UNKNOWN_ERROR",
                    message=f"Unexpected error loading module: {str(e)}",
                    severity=ErrorSeverity.CRITICAL,
                    exception=e,
                    suggestions=[
                        "Check module file for syntax errors",
                        "Verify all imports are available",
                        "Check system resources and permissions"
                    ]
                )
            
            error_msg = f"Failed to load module {module_path}: {e}"
            logger.error(error_msg)
            self._failed_modules[module_path] = str(e)
            
            # Create failed module info
            module_info = ModuleInfo(
                name=module_path.split('.')[-1],
                category=module_path.split('.')[1] if len(module_path.split('.')) > 1 else "unknown",
                tools=[],
                prompts=[],
                loaded=False,
                dependencies=[],
                module_path=module_path,
                error=str(e),
                load_time=load_time
            )
            
            if hasattr(self, '_module_errors') and self._module_errors:
                module_info.detailed_errors = [err for err in self._module_errors if err.module_path == module_path]
            
            return module_info
            
    def _create_failed_module_info(self, module_path: str, error: ModuleError) -> ModuleInfo:
        """Create a ModuleInfo for a failed module."""
        parts = module_path.split('.')
        return ModuleInfo(
            name=parts[-1] if parts else "unknown",
            category=parts[1] if len(parts) > 1 else "unknown",
            tools=[],
            prompts=[],
            loaded=False,
            dependencies=[],
            module_path=module_path,
            error=error.error_message,
            detailed_errors=[error]
        )
        
    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        Check if module dependencies are satisfied.
        
        Args:
            dependencies: List of dependency names
            
        Returns:
            list: List of missing dependencies
        """
        missing = []
        loaded_module_names = {m.name for m in self._loaded_modules.values() if m.loaded}
        
        for dep in dependencies:
            if dep not in loaded_module_names:
                missing.append(dep)
                
        return missing
            
    def _validate_module_structure(self, module: Any, module_type: str) -> None:
        """
        Validate that a module has the expected structure.
        
        Args:
            module: Imported module
            module_type: Type of module (tools or prompts)
            
        Raises:
            ModuleStructureError: If module structure is invalid
        """
        if module_type == "tools":
            # Tools modules should have a register_tools function
            if not hasattr(module, 'register_tools'):
                raise ModuleStructureError(
                    f"Tools module {module.__name__} missing register_tools function",
                    module.__name__
                )
        elif module_type == "prompts":
            # Prompts modules should have a register_prompts function
            if not hasattr(module, 'register_prompts'):
                raise ModuleStructureError(
                    f"Prompts module {module.__name__} missing register_prompts function", 
                    module.__name__
                )
                
    def _register_tools_from_module(self, module: Any, category: str, module_info: ModuleInfo) -> None:
        """
        Register tools from a module.
        
        Args:
            module: Imported module
            category: Tool category
            module_info: Module information to update
        """
        try:
            # Check if module has register_tools function
            if hasattr(module, 'register_tools') and self._mcp_instance:
                # Call the module's register_tools function with MCP instance
                module.register_tools(self._mcp_instance)
                
                # Extract tool names from the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and not attr_name.startswith('_') and attr_name != 'register_tools':
                        # Check if it looks like a tool function (has parameters)
                        if hasattr(attr, '__annotations__') or hasattr(attr, '__doc__'):
                            module_info.tools.append(attr_name)
                            
                logger.info(f"Registered {len(module_info.tools)} tools from module {module.__name__}")
            else:
                # Fallback: look for functions that could be tools
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and hasattr(attr, '__annotations__'):
                        # Check if it looks like a tool function
                        if not attr_name.startswith('_') and attr_name not in ['register_tools']:
                            try:
                                # Register with the registry
                                register_tool(attr, category)
                                module_info.tools.append(attr_name)
                                logger.debug(f"Registered tool: {attr_name}")
                            except Exception as e:
                                logger.warning(f"Failed to register tool {attr_name}: {e}")
                                
        except Exception as e:
            logger.error(f"Error registering tools from module {module.__name__}: {e}")
            raise ModuleLoadError(f"Tool registration failed: {e}")
            
    def _register_prompts_from_module(self, module: Any, category: str, module_info: ModuleInfo) -> None:
        """
        Register prompts from a module.
        
        Args:
            module: Imported module
            category: Prompt category
            module_info: Module information to update
        """
        try:
            # Check if module has register_prompts function
            if hasattr(module, 'register_prompts'):
                # Call the module's register_prompts function
                module.register_prompts()
                logger.info(f"Registered prompts from module {module.__name__}")
            else:
                # Fallback: look for prompt functions
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and not attr_name.startswith('_'):
                        if attr_name.endswith('_prompt') or 'prompt' in attr_name.lower():
                            try:
                                register_prompt(attr, category)
                                module_info.prompts.append(attr_name)
                                logger.debug(f"Registered prompt: {attr_name}")
                            except Exception as e:
                                logger.warning(f"Failed to register prompt {attr_name}: {e}")
                                
        except Exception as e:
            logger.error(f"Error registering prompts from module {module.__name__}: {e}")
            raise ModuleLoadError(f"Prompt registration failed: {e}")
            
    def load_all_modules(self) -> Dict[str, ModuleInfo]:
        """
        Discover and load all available modules with comprehensive error handling.
        
        Returns:
            dict: Dictionary of module path to ModuleInfo
        """
        logger.info("Loading all modules")
        
        # Clear previous errors
        self._module_errors.clear()
        
        # Discover all modules
        discovered_modules = self.discover_modules()
        
        if not discovered_modules:
            logger.warning("No modules discovered for loading")
            return {}
        
        logger.info(f"Discovered {len(discovered_modules)} modules to load")
        
        # Load each module
        loaded_modules = {}
        successful_loads = 0
        failed_loads = 0
        
        for module_path in discovered_modules:
            try:
                module_info = self.load_module(module_path)
                if module_info:
                    loaded_modules[module_path] = module_info
                    if module_info.loaded:
                        successful_loads += 1
                    else:
                        failed_loads += 1
            except Exception as e:
                logger.error(f"Critical error loading module {module_path}: {e}")
                failed_loads += 1
                
        # Validate dependencies after all modules are loaded
        dependency_validation_passed = True
        try:
            dependency_validation_passed = validate_dependencies()
        except Exception as e:
            logger.error(f"Dependency validation failed: {e}")
            self._create_error(
                module_path="system",
                error_type="DEPENDENCY_VALIDATION_ERROR",
                message=f"Global dependency validation failed: {str(e)}",
                severity=ErrorSeverity.ERROR,
                exception=e,
                suggestions=[
                    "Check module loading order",
                    "Verify all required modules are present",
                    "Review module dependency declarations"
                ]
            )
            
        if not dependency_validation_passed:
            logger.warning("Some module dependencies are not satisfied")
            
        # Log comprehensive summary
        logger.info(f"Module loading complete: {successful_loads} successful, {failed_loads} failed")
        
        if self._module_errors:
            self._log_error_summary()
            
        # Log performance statistics
        total_load_time = sum(m.load_time or 0 for m in loaded_modules.values())
        avg_load_time = total_load_time / len(loaded_modules) if loaded_modules else 0
        logger.info(f"Total load time: {total_load_time:.3f}s, Average: {avg_load_time:.3f}s per module")
        
        return loaded_modules
        
    def load_category(self, category: str) -> Dict[str, ModuleInfo]:
        """
        Load modules for a specific category.
        
        Args:
            category: Category to load (cad, cam, utility, debug)
            
        Returns:
            dict: Dictionary of module path to ModuleInfo
        """
        logger.info(f"Loading modules for category: {category}")
        
        # Discover modules for the category
        discovered_modules = self.discover_modules(category)
        
        # Load each module
        loaded_modules = {}
        for module_path in discovered_modules:
            module_info = self.load_module(module_path)
            if module_info:
                loaded_modules[module_path] = module_info
                
        logger.info(f"Loaded {len([m for m in loaded_modules.values() if m.loaded])} modules for category {category}")
        
        return loaded_modules
        
    def get_loaded_modules(self) -> List[ModuleInfo]:
        """
        Get list of successfully loaded modules.
        
        Returns:
            list: List of loaded modules
        """
        return [module for module in self._loaded_modules.values() if module.loaded]
        
    def get_failed_modules(self) -> Dict[str, str]:
        """
        Get dictionary of failed modules and their error messages.
        
        Returns:
            dict: Dictionary of module path to error message
        """
        return self._failed_modules.copy()
        
    def validate_module(self, module_path: str) -> bool:
        """
        Validate a specific module structure and dependencies.
        
        Args:
            module_path: Module path to validate
            
        Returns:
            bool: True if module is valid
        """
        logger.info(f"Validating module: {module_path}")
        
        if module_path not in self._loaded_modules:
            logger.error(f"Module not loaded: {module_path}")
            return False
            
        module_info = self._loaded_modules[module_path]
        
        # Check if module loaded successfully
        if not module_info.loaded:
            logger.error(f"Module failed to load: {module_path}")
            return False
            
        # Check dependencies
        for dependency in module_info.dependencies:
            if dependency not in [m.name for m in self._loaded_modules.values() if m.loaded]:
                logger.error(f"Module {module_path} has unmet dependency: {dependency}")
                return False
                
        logger.info(f"Module {module_path} validation passed")
        return True
        
    def reload_module(self, module_path: str) -> Optional[ModuleInfo]:
        """
        Reload a specific module.
        
        Args:
            module_path: Module path to reload
            
        Returns:
            ModuleInfo or None: Module information if reloaded successfully
        """
        logger.info(f"Reloading module: {module_path}")
        
        # Remove from loaded modules if present
        if module_path in self._loaded_modules:
            del self._loaded_modules[module_path]
            
        # Remove from failed modules if present
        if module_path in self._failed_modules:
            del self._failed_modules[module_path]
            
        # Reload the module in Python
        try:
            if module_path in sys.modules:
                importlib.reload(sys.modules[module_path])
        except Exception as e:
            logger.warning(f"Failed to reload Python module {module_path}: {e}")
            
        # Load the module again
        return self.load_module(module_path)
        
    def get_module_info(self, module_path: str) -> Optional[ModuleInfo]:
        """
        Get information about a specific module.
        
        Args:
            module_path: Module path
            
        Returns:
            ModuleInfo or None: Module information if found
        """
        return self._loaded_modules.get(module_path)
        
    def get_categories(self) -> Set[str]:
        """
        Get set of categories from loaded modules.
        
        Returns:
            set: Set of category names
        """
        return {module.category for module in self._loaded_modules.values()}
        
    def get_module_count(self, category: Optional[str] = None) -> int:
        """
        Get count of loaded modules.
        
        Args:
            category: Optional category filter
            
        Returns:
            int: Number of loaded modules
        """
        if category is None:
            return len([m for m in self._loaded_modules.values() if m.loaded])
        else:
            return len([m for m in self._loaded_modules.values() if m.loaded and m.category == category])
            
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status of the module loading system.
        
        Returns:
            dict: Health status information
        """
        total_modules = len(self._loaded_modules)
        loaded_modules = len([m for m in self._loaded_modules.values() if m.loaded])
        failed_modules = total_modules - loaded_modules
        
        critical_errors = len([e for e in self._module_errors if e.severity == ErrorSeverity.CRITICAL])
        error_count = len([e for e in self._module_errors if e.severity == ErrorSeverity.ERROR])
        warning_count = len([e for e in self._module_errors if e.severity == ErrorSeverity.WARNING])
        
        # Determine overall health
        if critical_errors > 0:
            health = "CRITICAL"
        elif error_count > loaded_modules / 2:  # More than half failed
            health = "POOR"
        elif error_count > 0 or warning_count > 0:
            health = "DEGRADED"
        else:
            health = "HEALTHY"
            
        return {
            "health": health,
            "total_modules": total_modules,
            "loaded_modules": loaded_modules,
            "failed_modules": failed_modules,
            "critical_errors": critical_errors,
            "errors": error_count,
            "warnings": warning_count,
            "error_recovery_enabled": self._error_recovery_enabled,
            "categories": list(self.get_categories())
        }
        
    def clear_errors(self) -> None:
        """Clear all recorded errors."""
        self._module_errors.clear()
        logger.info("Cleared all module loading errors")
        
    def retry_failed_modules(self) -> Dict[str, ModuleInfo]:
        """
        Retry loading all previously failed modules.
        
        Returns:
            dict: Results of retry attempts
        """
        logger.info("Retrying failed module loads")
        
        failed_paths = list(self._failed_modules.keys())
        retry_results = {}
        
        # Clear previous failures
        self._failed_modules.clear()
        
        for module_path in failed_paths:
            logger.info(f"Retrying module: {module_path}")
            module_info = self.load_module(module_path)
            if module_info:
                retry_results[module_path] = module_info
                
        successful_retries = len([m for m in retry_results.values() if m.loaded])
        logger.info(f"Retry complete: {successful_retries}/{len(failed_paths)} modules now loaded")
        
        return retry_results


# Global loader instance
_loader = ModuleLoader()


def set_mcp_instance(mcp_instance) -> None:
    """Set the MCP instance for the global loader."""
    _loader.set_mcp_instance(mcp_instance)


def load_all_modules() -> Dict[str, ModuleInfo]:
    """Load all available modules."""
    return _loader.load_all_modules()


def load_category(category: str) -> Dict[str, ModuleInfo]:
    """Load modules for a specific category."""
    return _loader.load_category(category)


def get_loaded_modules() -> List[ModuleInfo]:
    """Get list of successfully loaded modules."""
    return _loader.get_loaded_modules()


def get_failed_modules() -> Dict[str, str]:
    """Get dictionary of failed modules and their error messages."""
    return _loader.get_failed_modules()


def validate_module(module_path: str) -> bool:
    """Validate a specific module."""
    return _loader.validate_module(module_path)


def reload_module(module_path: str) -> Optional[ModuleInfo]:
    """Reload a specific module."""
    return _loader.reload_module(module_path)


def get_module_info(module_path: str) -> Optional[ModuleInfo]:
    """Get information about a specific module."""
    return _loader.get_module_info(module_path)


def get_categories() -> Set[str]:
    """Get set of categories from loaded modules."""
    return _loader.get_categories()


def get_module_count(category: Optional[str] = None) -> int:
    """Get count of loaded modules."""
    return _loader.get_module_count(category)


def get_error_report() -> Dict[str, Any]:
    """Get comprehensive error report."""
    return _loader.get_error_report()


def get_health_status() -> Dict[str, Any]:
    """Get overall health status of the module loading system."""
    return _loader.get_health_status()


def set_error_recovery(enabled: bool) -> None:
    """Enable or disable error recovery mode."""
    _loader.set_error_recovery(enabled)


def clear_errors() -> None:
    """Clear all recorded errors."""
    _loader.clear_errors()


def retry_failed_modules() -> Dict[str, ModuleInfo]:
    """Retry loading all previously failed modules."""
    return _loader.retry_failed_modules()