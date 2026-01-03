# Configuration Manager
# Centralized configuration management with category support aligned to Fusion 360 workspaces

import json
from typing import Dict, Any, Optional, List
from enum import Enum

class WorkspaceCategory(Enum):
    """Fusion 360 workspace categories for organizing endpoints and configuration"""
    DESIGN = "design"
    MANUFACTURE = "manufacture"
    RESEARCH = "research"
    SYSTEM = "system"

class ConfigurationManager:
    """
    Centralized configuration manager with category support aligned to Fusion 360 workspaces.
    Manages HTTP endpoints, server settings, and module-specific configurations.
    """
    
    def __init__(self):
        self._server_config = {
            "host": "localhost",
            "port": 5001,
            "timeout": 30,
            "max_retries": 3
        }
        
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Endpoints organized by Fusion 360 workspace categories
        self._endpoints = {
            WorkspaceCategory.DESIGN: {
                "geometry": {
                    "box": "/Box",
                    "cylinder": "/draw_cylinder", 
                    "sphere": "/sphere",
                    "circle": "/create_circle",
                    "lines": "/draw_lines",
                    "rectangle": "/draw_2d_rectangle"
                },
                "sketching": {
                    "arc": "/arc",
                    "spline": "/spline",
                    "ellipse": "/ellipsis",
                    "text": "/draw_text"
                },
                "modeling": {
                    "extrude": "/extrude_last_sketch",
                    "revolve": "/revolve",
                    "loft": "/loft",
                    "sweep": "/sweep",
                    "boolean": "/boolean_operation"
                },
                "features": {
                    "fillet": "/fillet_edges",
                    "shell": "/shell_body",
                    "holes": "/holes",
                    "thread": "/threaded",
                    "circular_pattern": "/circular_pattern",
                    "rectangular_pattern": "/rectangular_pattern"
                },
                "utilities": {
                    "export_step": "/Export_STEP",
                    "export_stl": "/Export_STL",
                    "parameters": "/set_parameter",
                    "list_parameters": "/list_parameters",
                    "count_parameters": "/count_parameters"
                }
            },
            
            WorkspaceCategory.MANUFACTURE: {
                "setups": {
                    "list": "/cam/setups",
                    "get": "/cam/setups/{setup_id}",
                    "create": "/cam/setups",
                    "modify": "/cam/setups/{setup_id}",
                    "delete": "/cam/setups/{setup_id}",
                    "duplicate": "/cam/setups/{setup_id}/duplicate",
                    "sequence": "/cam/setups/{setup_id}/sequence"
                },
                "toolpaths": {
                    "list": "/cam/toolpaths",
                    "list_with_heights": "/cam/toolpaths/with-heights",
                    "get": "/cam/toolpaths/{toolpath_id}",
                    "parameters": "/cam/toolpaths/{toolpath_id}/parameters",
                    "heights": "/cam/toolpaths/{toolpath_id}/heights",
                    "passes": "/cam/toolpaths/{toolpath_id}/passes",
                    "linking": "/cam/toolpaths/{toolpath_id}/linking"
                },
                "operations": {
                    "tool": "/cam/operations/{operation_id}/tool",
                    "heights": "/cam/operations/{operation_id}/heights",
                    "height_param": "/cam/operations/{operation_id}/heights/{parameter_name}",
                    "heights_validate": "/cam/operations/{operation_id}/heights/validate",
                    "passes": "/cam/operations/{operation_id}/passes",
                    "passes_validate": "/cam/operations/{operation_id}/passes/validate",
                    "passes_optimize": "/cam/operations/{operation_id}/passes/optimize",
                    "linking": "/cam/operations/{operation_id}/linking",
                    "linking_validate": "/cam/operations/{operation_id}/linking/validate"
                },
                "tools": {
                    "list": "/cam/tools",
                    "usage": "/cam/tools/{tool_id}/usage"
                },
                "tool_libraries": {
                    "list": "/tool-libraries",
                    "get": "/tool-libraries/{library_id}",
                    "load": "/tool-libraries/load",
                    "validate_access": "/tool-libraries/validate-access",
                    "tools_list": "/tool-libraries/tools",
                    "tools_create": "/tool-libraries/tools",
                    "tool_get": "/tool-libraries/tools/{tool_id}",
                    "tool_modify": "/tool-libraries/tools/{tool_id}",
                    "tool_delete": "/tool-libraries/tools/{tool_id}",
                    "tool_duplicate": "/tool-libraries/tools/{tool_id}/duplicate",
                    "tool_validate": "/tool-libraries/tools/validate"
                },
                "tool_search": {
                    "search": "/tool-libraries/search",
                    "advanced": "/tool-libraries/search/advanced",
                    "suggestions": "/tool-libraries/search/suggestions"
                }
            },
            
            WorkspaceCategory.RESEARCH: {
                "work_coordinate_system_api": {
                    "research": "/research/work_coordinate_system_api"
                },
                "model_id": {
                    "research": "/research/model-id"
                }
            },
            
            WorkspaceCategory.SYSTEM: {
                "lifecycle": {
                    "test_connection": "/test_connection"
                },
                "utilities": {
                    "undo": "/undo",
                    "delete_everything": "/delete_everything",
                    "move_body": "/move_body",
                    "offset_plane": "/offsetplane"
                }
            }
        }
        
        # Module-specific configuration
        self._module_config = {}
        
    def get_server_config(self) -> Dict[str, Any]:
        """Returns HTTP server configuration"""
        return self._server_config.copy()
    
    def get_endpoints(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns endpoints by category or all endpoints if category is None
        
        Args:
            category: Workspace category name (design, manufacture, research, system)
        
        Returns:
            Dictionary of endpoints for the specified category or all endpoints
        """
        if category is None:
            return {cat.value: endpoints for cat, endpoints in self._endpoints.items()}
        
        # Convert string to enum if needed
        if isinstance(category, str):
            try:
                category_enum = WorkspaceCategory(category.lower())
            except ValueError:
                raise ValueError(f"Invalid category: {category}. Valid categories: {[c.value for c in WorkspaceCategory]}")
        else:
            category_enum = category
            
        return self._endpoints.get(category_enum, {})
    
    def get_headers(self) -> Dict[str, str]:
        """Returns HTTP headers"""
        return self._headers.copy()
    
    def get_timeout(self) -> int:
        """Returns request timeout in seconds"""
        return self._server_config["timeout"]
    
    def get_max_retries(self) -> int:
        """Returns maximum number of retries for requests"""
        return self._server_config["max_retries"]
    
    def validate_config(self) -> bool:
        """
        Validates configuration integrity
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate server config
            required_server_keys = ["host", "port", "timeout", "max_retries"]
            for key in required_server_keys:
                if key not in self._server_config:
                    return False
            
            # Validate port is valid
            port = self._server_config["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False
            
            # Validate timeout and retries are positive
            if self._server_config["timeout"] <= 0 or self._server_config["max_retries"] <= 0:
                return False
            
            # Validate endpoints structure
            for category, endpoints in self._endpoints.items():
                if not isinstance(category, WorkspaceCategory):
                    return False
                if not isinstance(endpoints, dict):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def validate_config_detailed(self) -> Dict[str, Any]:
        """
        Validates configuration integrity with detailed error reporting
        
        Returns:
            Dictionary with validation results, errors, and resolution guidance
        """
        import re
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'conflicts': [],
            'resolution_guidance': []
        }
        
        # Define valid placeholder names per entity type
        valid_placeholders = {
            "setup_id", "toolpath_id", "operation_id", 
            "tool_id", "library_id", "parameter_name"
        }
        
        # Define invalid/non-standard placeholder patterns
        invalid_placeholder_patterns = {
            "id": "Use entity-specific placeholder like {setup_id}, {toolpath_id}, {operation_id}, {tool_id}, or {library_id}",
            "setup": "Use {setup_id} instead of {setup}",
            "toolpath": "Use {toolpath_id} instead of {toolpath}",
            "operation": "Use {operation_id} instead of {operation}",
            "tool": "Use {tool_id} instead of {tool}",
            "library": "Use {library_id} instead of {library}",
            "param": "Use {parameter_name} instead of {param}",
            "name": "Use {parameter_name} for parameter names, or entity-specific placeholder for IDs",
        }
        
        # Define expected plural forms for path segments
        singular_to_plural = {
            "/cam/setup/": "/cam/setups/",
            "/cam/toolpath/": "/cam/toolpaths/",
            "/cam/operation/": "/cam/operations/",
            "/cam/tool/": "/cam/tools/",
            "/tool-library/": "/tool-libraries/",
        }
        
        try:
            # Validate server config
            required_server_keys = ["host", "port", "timeout", "max_retries"]
            for key in required_server_keys:
                if key not in self._server_config:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Missing required server configuration key: {key}")
                    validation_result['resolution_guidance'].append(f"Add '{key}' to server configuration")
            
            # Validate port is valid
            if 'port' in self._server_config:
                port = self._server_config["port"]
                if not isinstance(port, int):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Port must be an integer, got {type(port).__name__}")
                    validation_result['resolution_guidance'].append("Set port to a valid integer between 1 and 65535")
                elif port < 1 or port > 65535:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Port {port} is out of valid range (1-65535)")
                    validation_result['resolution_guidance'].append("Set port to a value between 1 and 65535")
            
            # Validate timeout and retries are positive
            if 'timeout' in self._server_config:
                timeout = self._server_config["timeout"]
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Timeout must be a positive number, got {timeout}")
                    validation_result['resolution_guidance'].append("Set timeout to a positive number (recommended: 30)")
            
            if 'max_retries' in self._server_config:
                retries = self._server_config["max_retries"]
                if not isinstance(retries, int) or retries <= 0:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Max retries must be a positive integer, got {retries}")
                    validation_result['resolution_guidance'].append("Set max_retries to a positive integer (recommended: 3)")
            
            # Validate endpoints structure
            endpoint_paths = set()
            for category, endpoints in self._endpoints.items():
                if not isinstance(category, WorkspaceCategory):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Invalid category type: {type(category).__name__}")
                    validation_result['resolution_guidance'].append("Ensure all categories are WorkspaceCategory enums")
                    continue
                
                if not isinstance(endpoints, dict):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Endpoints for category {category.value} must be a dictionary")
                    validation_result['resolution_guidance'].append(f"Fix endpoints structure for category {category.value}")
                    continue
                
                # Check for duplicate endpoint paths and validate patterns
                for group_name, group_endpoints in endpoints.items():
                    if not isinstance(group_endpoints, dict):
                        validation_result['warnings'].append(f"Endpoint group {group_name} in {category.value} is not a dictionary")
                        continue
                    
                    for endpoint_name, path in group_endpoints.items():
                        if not isinstance(path, str):
                            validation_result['errors'].append(f"Endpoint path for {category.value}.{group_name}.{endpoint_name} must be a string")
                            validation_result['resolution_guidance'].append(f"Set valid string path for {category.value}.{group_name}.{endpoint_name}")
                            validation_result['valid'] = False
                            continue
                        
                        # Check for duplicate paths
                        if path in endpoint_paths:
                            validation_result['conflicts'].append(f"Duplicate endpoint path: {path} (found in {category.value}.{group_name}.{endpoint_name})")
                            validation_result['resolution_guidance'].append(f"Use unique paths for all endpoints - {path} is duplicated")
                        else:
                            endpoint_paths.add(path)
                        
                        # Validate endpoint path patterns
                        path_issues = self._validate_endpoint_path_pattern(
                            path, category.value, group_name, endpoint_name,
                            valid_placeholders, invalid_placeholder_patterns, singular_to_plural
                        )
                        
                        for issue in path_issues:
                            if issue['type'] == 'error':
                                validation_result['errors'].append(issue['message'])
                                validation_result['valid'] = False
                            else:
                                validation_result['warnings'].append(issue['message'])
                            
                            if issue.get('guidance'):
                                validation_result['resolution_guidance'].append(issue['guidance'])
            
            # Check for configuration conflicts in module configs
            for module_name, module_config in self._module_config.items():
                if not isinstance(module_config, dict):
                    validation_result['warnings'].append(f"Module configuration for {module_name} is not a dictionary")
            
            # Add summary guidance
            if validation_result['errors']:
                validation_result['resolution_guidance'].insert(0, f"Found {len(validation_result['errors'])} critical errors that must be fixed")
            if validation_result['conflicts']:
                validation_result['resolution_guidance'].insert(0, f"Found {len(validation_result['conflicts'])} configuration conflicts that should be resolved")
            if validation_result['warnings']:
                validation_result['resolution_guidance'].append(f"Found {len(validation_result['warnings'])} warnings that should be addressed")
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            validation_result['resolution_guidance'].append("Check configuration structure and fix any syntax errors")
            return validation_result
    
    def _validate_endpoint_path_pattern(
        self, 
        path: str, 
        category: str, 
        group_name: str, 
        endpoint_name: str,
        valid_placeholders: set,
        invalid_placeholder_patterns: Dict[str, str],
        singular_to_plural: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Validates an endpoint path for pattern consistency.
        
        Detects:
        - Singular vs plural path inconsistencies
        - Non-standard placeholder names
        - Invalid placeholder patterns
        
        Args:
            path: The endpoint path to validate
            category: The workspace category
            group_name: The endpoint group name
            endpoint_name: The endpoint name
            valid_placeholders: Set of valid placeholder names
            invalid_placeholder_patterns: Dict of invalid patterns to guidance
            singular_to_plural: Dict mapping singular to plural forms
            
        Returns:
            List of issue dictionaries with 'type', 'message', and optional 'guidance'
        """
        import re
        issues = []
        endpoint_ref = f"{category}.{group_name}.{endpoint_name}"
        
        # Check for singular vs plural path inconsistencies
        for singular, plural in singular_to_plural.items():
            if singular in path:
                issues.append({
                    'type': 'warning',
                    'message': f"Singular path segment '{singular.strip('/')}' found in {endpoint_ref}: {path}. Consider using plural form '{plural.strip('/')}'",
                    'guidance': f"Change '{singular}' to '{plural}' in endpoint {endpoint_ref} for consistency. Example: {path.replace(singular, plural)}"
                })
        
        # Extract and validate placeholders
        placeholders = re.findall(r'\{([^}]+)\}', path)
        
        for placeholder in placeholders:
            # Check for invalid/non-standard placeholder patterns
            if placeholder in invalid_placeholder_patterns:
                guidance = invalid_placeholder_patterns[placeholder]
                issues.append({
                    'type': 'error',
                    'message': f"Non-standard placeholder '{{{placeholder}}}' found in {endpoint_ref}: {path}",
                    'guidance': f"{guidance}. Fix endpoint {endpoint_ref}"
                })
            # Check if placeholder is not in valid set
            elif placeholder not in valid_placeholders:
                issues.append({
                    'type': 'warning',
                    'message': f"Unknown placeholder '{{{placeholder}}}' found in {endpoint_ref}: {path}",
                    'guidance': f"Use standard placeholder names: {', '.join(sorted(valid_placeholders))}. If '{{{placeholder}}}' is intentional, consider adding it to the valid placeholders list."
                })
        
        return issues
    
    def set_module_config(self, module_name: str, config: Dict[str, Any]) -> None:
        """
        Sets configuration for a specific module
        
        Args:
            module_name: Name of the module
            config: Configuration dictionary for the module
        """
        self._module_config[module_name] = config
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """
        Gets configuration for a specific module
        
        Args:
            module_name: Name of the module
            
        Returns:
            Configuration dictionary for the module
        """
        return self._module_config.get(module_name, {})
    
    def update_endpoint(self, category: str, endpoint_group: str, endpoint_name: str, path: str) -> None:
        """
        Updates or adds an endpoint and propagates changes to all dependent modules
        
        Args:
            category: Workspace category (design, manufacture, research, system)
            endpoint_group: Group within the category (e.g., 'geometry', 'toolpaths')
            endpoint_name: Name of the endpoint
            path: URL path for the endpoint
        """
        try:
            category_enum = WorkspaceCategory(category.lower())
        except ValueError:
            raise ValueError(f"Invalid category: {category}")
        
        if category_enum not in self._endpoints:
            self._endpoints[category_enum] = {}
        
        if endpoint_group not in self._endpoints[category_enum]:
            self._endpoints[category_enum][endpoint_group] = {}
        
        # Store old value for change detection
        old_path = self._endpoints[category_enum][endpoint_group].get(endpoint_name)
        
        # Update endpoint
        self._endpoints[category_enum][endpoint_group][endpoint_name] = path
        
        # Propagate changes to dependent modules if endpoint changed
        if old_path != path:
            self._propagate_configuration_change(category, endpoint_group, endpoint_name, path)
    
    def _propagate_configuration_change(self, category: str, endpoint_group: str, endpoint_name: str, path: str) -> None:
        """
        Propagate configuration changes to all dependent modules
        
        Args:
            category: Category that changed
            endpoint_group: Group that changed
            endpoint_name: Endpoint that changed
            path: New path value
        """
        # Notify all modules that configuration has changed
        change_info = {
            'type': 'endpoint_update',
            'category': category,
            'endpoint_group': endpoint_group,
            'endpoint_name': endpoint_name,
            'new_path': path,
            'timestamp': __import__('time').time()
        }
        
        # Store change in module configs for modules to check
        for module_name in self._module_config:
            if 'config_changes' not in self._module_config[module_name]:
                self._module_config[module_name]['config_changes'] = []
            self._module_config[module_name]['config_changes'].append(change_info)
    
    def get_configuration_changes(self, module_name: str) -> List[Dict[str, Any]]:
        """
        Get configuration changes for a specific module
        
        Args:
            module_name: Name of the module
            
        Returns:
            List of configuration changes since last check
        """
        if module_name not in self._module_config:
            return []
        
        changes = self._module_config[module_name].get('config_changes', [])
        # Clear changes after returning them
        self._module_config[module_name]['config_changes'] = []
        return changes
    
    def add_category_configuration(self, category: str, config: Dict[str, Any]) -> None:
        """
        Add category-specific configuration
        
        Args:
            category: Category name
            config: Configuration dictionary for the category
        """
        try:
            category_enum = WorkspaceCategory(category.lower())
        except ValueError:
            raise ValueError(f"Invalid category: {category}. Valid categories: {[c.value for c in WorkspaceCategory]}")
        
        # Store category-specific configuration
        category_key = f"category_{category_enum.value}"
        self._module_config[category_key] = config
    
    def get_category_configuration(self, category: str) -> Dict[str, Any]:
        """
        Get category-specific configuration
        
        Args:
            category: Category name
            
        Returns:
            Configuration dictionary for the category
        """
        try:
            category_enum = WorkspaceCategory(category.lower())
        except ValueError:
            return {}
        
        category_key = f"category_{category_enum.value}"
        return self._module_config.get(category_key, {})

# Global configuration manager instance
config_manager = ConfigurationManager()