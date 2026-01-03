# Module Loader
# Dynamic discovery and loading of handler modules with automatic validation

import os
import sys
import importlib
import inspect
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from .error_handling import error_handler, ErrorCategory, ErrorSeverity, handle_module_load_error

# Set up module-specific logging
module_logger = error_handler.get_module_logger("core.loader")

@dataclass
class HandlerInfo:
    """Information about a registered handler function"""
    name: str
    pattern: str
    handler_func: Callable
    category: str
    methods: List[str]
    dependencies: List[str]

@dataclass
class ModuleInfo:
    """Information about a loaded module"""
    name: str
    category: str
    handlers: List[HandlerInfo]
    loaded: bool
    dependencies: List[str]
    fusion_api_requirements: List[str]

class ModuleLoader:
    """
    Dynamic module discovery and loading system for handler modules.
    Automatically discovers modules in the handlers directory and validates dependencies.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the module loader with error handling
        
        Args:
            base_path: Base path for the add-in (defaults to current directory)
        """
        try:
            self.base_path = base_path or os.path.dirname(os.path.dirname(__file__))
            self.handlers_path = os.path.join(self.base_path, "handlers")
            self.loaded_modules: Dict[str, ModuleInfo] = {}
            self.registered_handlers: Dict[str, HandlerInfo] = {}
            
            # Ensure handlers directory exists
            if not os.path.exists(self.handlers_path):
                os.makedirs(self.handlers_path)
                module_logger.info(f"Created handlers directory: {self.handlers_path}")
                
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.loader",
                function_name="__init__",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL
            )
            module_logger.critical(f"Module loader initialization failed: {error_response.message}")
            raise
    
    def discover_modules(self) -> List[str]:
        """
        Discover all available handler modules with error handling
        
        Returns:
            List of module names that can be loaded
        """
        modules = []
        
        try:
            if not os.path.exists(self.handlers_path):
                module_logger.warning(f"Handlers directory not found: {self.handlers_path}")
                return modules
            
            # Walk through handlers directory
            for root, dirs, files in os.walk(self.handlers_path):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != '__pycache__']
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        try:
                            # Calculate relative module path
                            rel_path = os.path.relpath(root, self.handlers_path)
                            if rel_path == '.':
                                module_name = file[:-3]  # Remove .py extension
                            else:
                                module_name = f"{rel_path.replace(os.sep, '.')}.{file[:-3]}"
                            
                            modules.append(module_name)
                            module_logger.debug(f"Discovered module: {module_name}")
                            
                        except Exception as e:
                            error_response = error_handler.handle_error(
                                error=e,
                                module_name="core.loader",
                                function_name="discover_modules",
                                category=ErrorCategory.MODULE_LOAD,
                                severity=ErrorSeverity.LOW,
                                additional_info={"file": file, "root": root}
                            )
                            module_logger.warning(f"Failed to process module file {file}: {error_response.message}")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.loader",
                function_name="discover_modules",
                category=ErrorCategory.MODULE_LOAD,
                severity=ErrorSeverity.HIGH
            )
            module_logger.error(f"Module discovery failed: {error_response.message}")
        
        return modules
    
    def validate_module_dependencies(self, module) -> List[str]:
        """
        Validate that a module's dependencies are available
        
        Args:
            module: The imported module to validate
            
        Returns:
            List of missing dependencies
        """
        missing_deps = []
        
        # Check for Fusion 360 API requirements
        fusion_apis = ['adsk.core', 'adsk.fusion', 'adsk.cam']
        for api in fusion_apis:
            if hasattr(module, f'REQUIRES_{api.replace(".", "_").upper()}'):
                try:
                    importlib.import_module(api)
                except ImportError:
                    missing_deps.append(api)
        
        # Check for other module dependencies
        if hasattr(module, 'DEPENDENCIES'):
            for dep in module.DEPENDENCIES:
                try:
                    importlib.import_module(dep)
                except ImportError:
                    missing_deps.append(dep)
        
        return missing_deps
    
    def extract_handlers_from_module(self, module, module_name: str) -> List[HandlerInfo]:
        """
        Extract handler functions from a module
        
        Args:
            module: The imported module
            module_name: Name of the module
            
        Returns:
            List of HandlerInfo objects for functions in the module
        """
        handlers = []
        
        # Look for functions that could be handlers
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            # Skip private functions
            if name.startswith('_'):
                continue
            
            # Check if function has handler metadata
            if hasattr(obj, 'handler_info'):
                handler_info = obj.handler_info
                handlers.append(HandlerInfo(
                    name=handler_info.get('name', name),
                    pattern=handler_info.get('pattern', f'/{name}'),
                    handler_func=obj,
                    category=handler_info.get('category', 'system'),
                    methods=handler_info.get('methods', ['GET', 'POST']),  # Keep as strings
                    dependencies=handler_info.get('dependencies', [])
                ))
            else:
                # Auto-detect handlers based on naming convention
                if name.startswith('handle_'):
                    # Determine category from module path
                    category = 'system'
                    if 'design' in module_name:
                        category = 'design'
                    elif 'manufacture' in module_name or 'cam' in module_name:
                        category = 'manufacture'
                    elif 'research' in module_name:
                        category = 'research'
                    
                    handlers.append(HandlerInfo(
                        name=name,
                        pattern=f'/{name.replace("handle_", "")}',
                        handler_func=obj,
                        category=category,
                        methods=['GET', 'POST'],  # Keep as strings
                        dependencies=[]
                    ))
        
        return handlers
    
    def load_module(self, module_name: str) -> bool:
        """
        Load a specific module with comprehensive error handling and isolation
        
        Args:
            module_name: Name of the module to load
            
        Returns:
            True if module loaded successfully, False otherwise
        """
        try:
            # Construct full module path
            full_module_name = f"handlers.{module_name}"
            
            # Add handlers path to sys.path if not already there
            if self.handlers_path not in sys.path:
                sys.path.insert(0, os.path.dirname(self.handlers_path))
            
            # Import the module with error isolation
            try:
                module = importlib.import_module(full_module_name)
            except ImportError as e:
                error_response = handle_module_load_error(e, module_name)
                module_logger.error(f"Failed to import module {module_name}: {error_response.message}")
                return False
            except Exception as e:
                error_response = handle_module_load_error(e, module_name)
                module_logger.error(f"Module import error for {module_name}: {error_response.message}")
                return False
            
            # Validate dependencies
            try:
                missing_deps = self.validate_module_dependencies(module)
                if missing_deps:
                    error_response = error_handler.handle_error(
                        error=ImportError(f"Missing dependencies: {missing_deps}"),
                        module_name="core.loader",
                        function_name="load_module",
                        category=ErrorCategory.MODULE_LOAD,
                        severity=ErrorSeverity.HIGH,
                        additional_info={"module": module_name, "missing_deps": missing_deps}
                    )
                    module_logger.error(f"Module {module_name} has missing dependencies: {missing_deps}")
                    return False
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    module_name="core.loader",
                    function_name="load_module",
                    category=ErrorCategory.MODULE_LOAD,
                    severity=ErrorSeverity.MEDIUM,
                    additional_info={"module": module_name}
                )
                module_logger.warning(f"Dependency validation failed for {module_name}: {error_response.message}")
            
            # Extract handlers with error handling
            handlers = []
            try:
                # Check if module has HANDLERS attribute (new style)
                if hasattr(module, 'HANDLERS'):
                    for handler_def in module.HANDLERS:
                        try:
                            handler_info = HandlerInfo(
                                name=handler_def.get('name', handler_def['handler'].__name__),
                                pattern=handler_def['pattern'],
                                handler_func=handler_def['handler'],
                                category=handler_def['category'],
                                methods=handler_def.get('methods', ['GET', 'POST']),
                                dependencies=handler_def.get('dependencies', [])
                            )
                            handlers.append(handler_info)
                            
                            # Register with router
                            from .router import request_router
                            request_router.register_handler(
                                pattern=handler_def['pattern'],
                                handler=handler_def['handler'],
                                methods=handler_def.get('methods', ['GET', 'POST']),
                                category=handler_def['category'],
                                module_name=module_name
                            )
                        except Exception as e:
                            error_response = error_handler.handle_error(
                                error=e,
                                module_name=module_name,
                                function_name="load_module",
                                category=ErrorCategory.MODULE_LOAD,
                                severity=ErrorSeverity.MEDIUM,
                                additional_info={"handler_def": str(handler_def)}
                            )
                            module_logger.warning(f"Failed to register handler in {module_name}: {error_response.message}")
                else:
                    # Extract handlers using old method
                    handlers = self.extract_handlers_from_module(module, module_name)
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    module_name=module_name,
                    function_name="load_module",
                    category=ErrorCategory.MODULE_LOAD,
                    severity=ErrorSeverity.HIGH
                )
                module_logger.error(f"Handler extraction failed for {module_name}: {error_response.message}")
                return False
            
            # Determine category from module path
            category = 'system'
            if 'design' in module_name:
                category = 'design'
            elif 'manufacture' in module_name or 'cam' in module_name:
                category = 'manufacture'
            elif 'research' in module_name:
                category = 'research'
            
            # Create module info
            module_info = ModuleInfo(
                name=module_name,
                category=category,
                handlers=handlers,
                loaded=True,
                dependencies=getattr(module, 'DEPENDENCIES', []),
                fusion_api_requirements=getattr(module, 'FUSION_API_REQUIREMENTS', [])
            )
            
            # Store module info
            self.loaded_modules[module_name] = module_info
            
            # Register handlers (for old style modules)
            if not hasattr(module, 'HANDLERS'):
                for handler in handlers:
                    self.registered_handlers[handler.pattern] = handler
            
            module_logger.info(f"Successfully loaded module: {module_name} with {len(handlers)} handlers")
            return True
            
        except Exception as e:
            error_response = handle_module_load_error(e, module_name)
            module_logger.error(f"Failed to load module {module_name}: {error_response.message}")
            return False
    
    def load_category(self, category: str) -> int:
        """
        Load all modules in a specific category
        
        Args:
            category: Category name (design, manufacture, research, system)
            
        Returns:
            Number of modules successfully loaded
        """
        modules = self.discover_modules()
        loaded_count = 0
        
        for module_name in modules:
            if category.lower() in module_name.lower():
                if self.load_module(module_name):
                    loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} modules in category: {category}")
        return loaded_count
    
    def load_all_modules(self) -> int:
        """
        Discover and load all available handler modules with error resilience
        
        Returns:
            Number of modules successfully loaded
        """
        try:
            modules = self.discover_modules()
            loaded_count = 0
            failed_modules = []
            
            for module_name in modules:
                try:
                    if self.load_module(module_name):
                        loaded_count += 1
                    else:
                        failed_modules.append(module_name)
                except Exception as e:
                    error_response = error_handler.handle_error(
                        error=e,
                        module_name="core.loader",
                        function_name="load_all_modules",
                        category=ErrorCategory.MODULE_LOAD,
                        severity=ErrorSeverity.MEDIUM,
                        additional_info={"failed_module": module_name}
                    )
                    module_logger.error(f"Module loading failed for {module_name}: {error_response.message}")
                    failed_modules.append(module_name)
            
            module_logger.info(f"Loaded {loaded_count} out of {len(modules)} discovered modules")
            
            if failed_modules:
                module_logger.warning(f"Failed to load modules: {failed_modules}")
            
            return loaded_count
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.loader",
                function_name="load_all_modules",
                category=ErrorCategory.MODULE_LOAD,
                severity=ErrorSeverity.HIGH
            )
            module_logger.error(f"Module loading process failed: {error_response.message}")
            return 0
    
    def get_loaded_modules(self) -> List[ModuleInfo]:
        """
        Get list of all loaded modules
        
        Returns:
            List of ModuleInfo objects for loaded modules
        """
        return list(self.loaded_modules.values())
    
    def get_handlers_by_category(self, category: str) -> List[HandlerInfo]:
        """
        Get all handlers in a specific category
        
        Args:
            category: Category name
            
        Returns:
            List of HandlerInfo objects for the category
        """
        handlers = []
        for module_info in self.loaded_modules.values():
            if module_info.category == category:
                handlers.extend(module_info.handlers)
        return handlers
    
    def get_handler_by_pattern(self, pattern: str) -> Optional[HandlerInfo]:
        """
        Get handler by URL pattern
        
        Args:
            pattern: URL pattern to match
            
        Returns:
            HandlerInfo object if found, None otherwise
        """
        return self.registered_handlers.get(pattern)
    
    def validate_all_modules(self) -> Dict[str, List[str]]:
        """
        Validate all loaded modules and return any issues
        
        Returns:
            Dictionary mapping module names to lists of validation issues
        """
        issues = {}
        
        for module_name, module_info in self.loaded_modules.items():
            module_issues = []
            
            # Check if module is actually loaded
            if not module_info.loaded:
                module_issues.append("Module failed to load")
            
            # Check handlers
            if not module_info.handlers:
                module_issues.append("No handlers found in module")
            
            # Check for duplicate patterns
            patterns = [h.pattern for h in module_info.handlers]
            if len(patterns) != len(set(patterns)):
                module_issues.append("Duplicate handler patterns found")
            
            if module_issues:
                issues[module_name] = module_issues
        
        return issues

# Global module loader instance
module_loader = ModuleLoader()