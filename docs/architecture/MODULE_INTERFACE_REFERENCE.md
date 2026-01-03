# Module Interface Reference - Fusion 360 Add-In Modular Architecture

## Overview

This document provides a comprehensive reference for all module interfaces in the Fusion 360 Add-In modular architecture. It serves as the definitive guide for understanding how modules interact, what interfaces they expose, and how to use them effectively.

## Table of Contents

1. [Core Module Interfaces](#core-module-interfaces)
2. [Design Workspace Handler Interfaces](#design-workspace-handler-interfaces)
3. [MANUFACTURE Workspace Handler Interfaces](#manufacture-workspace-handler-interfaces)
4. [System Handler Interfaces](#system-handler-interfaces)
5. [Interface Patterns and Conventions](#interface-patterns-and-conventions)
6. [Data Models and Types](#data-models-and-types)

## Core Module Interfaces

### Configuration Manager (`core/config.py`)

```python
class ConfigurationManager:
    """Centralized configuration management with category support."""
    
    def get_server_config() -> dict:
        """Get HTTP server configuration."""
    
    def get_endpoints(category: str = None) -> dict:
        """Get endpoint definitions by category."""
    
    def get_headers() -> dict:
        """Get standard HTTP headers."""
    
    def validate_config() -> bool:
        """Validate configuration integrity."""
    
    def get_category_config(category: str) -> dict:
        """Get category-specific configuration."""
```

### Request Router (`core/router.py`)

```python
class RequestRouter:
    """HTTP request routing to appropriate handler modules."""
    
    def route_request(path: str, method: str, data: dict) -> dict:
        """Route HTTP request to appropriate handler."""
    
    def register_handler(pattern: str, handler: callable, 
                        methods: list[str] = None, 
                        category: str = None) -> None:
        """Register a handler for a URL pattern."""
    
    def get_routes() -> dict:
        """Get all registered routes."""
    
    def validate_route(path: str) -> bool:
        """Check if a route exists for the given path."""
```

### Task Queue System (`core/task_queue.py`)

```python
class TaskQueue:
    """Thread-safe task queue for Fusion 360 API execution."""
    
    def queue_task(task_type: str, *args, **kwargs) -> str:
        """Queue a task for execution on the main thread."""
    
    def process_tasks() -> None:
        """Process queued tasks (called on main UI thread)."""
    
    def register_task_handler(task_type: str, handler: callable) -> None:
        """Register a handler for a specific task type."""
    
    def get_task_result(task_id: str) -> dict:
        """Get the result of a completed task."""
    
    def get_queue_status() -> dict:
        """Get current queue status and metrics."""
```

### Module Loader (`core/loader.py`)

```python
class ModuleLoader:
    """Dynamic discovery and loading of handler modules."""
    
    def load_all_modules() -> list[ModuleInfo]:
        """Discover and load all handler modules."""
    
    def load_category(category: str) -> list[ModuleInfo]:
        """Load modules for a specific category."""
    
    def get_loaded_modules() -> list[ModuleInfo]:
        """Get list of currently loaded modules."""
    
    def validate_module(module) -> bool:
        """Validate module structure and dependencies."""
    
    def reload_module(module_name: str) -> bool:
        """Reload a specific module (for development)."""
```

### Error Handling (`core/error_handling.py`)

```python
class ErrorHandler:
    """Comprehensive error handling and logging system."""
    
    def handle_module_error(module_name: str, error: Exception, 
                          context: dict = None) -> dict:
        """Handle errors from handler modules."""
    
    def log_operation_error(operation: str, context: dict, 
                          error: Exception) -> None:
        """Log operation errors with context."""
    
    def create_error_response(error_type: str, message: str, 
                            context: dict = None) -> dict:
        """Create standardized error response."""
    
    def validate_dependencies(module_name: str, 
                            dependencies: list[str]) -> bool:
        """Validate module dependencies are available."""
```

## Design Workspace Handler Interfaces

### Geometry Handler (`handlers/design/geometry.py`)

```python
def handle_box(request_data: dict) -> dict:
    """
    Create a box geometry.
    
    Args:
        request_data: {
            "width": float,      # Width in mm
            "height": float,     # Height in mm  
            "depth": float,      # Depth in mm
            "position": [x, y, z] (optional)
        }
    """

def handle_cylinder(request_data: dict) -> dict:
    """Create a cylinder geometry."""

def handle_sphere(request_data: dict) -> dict:
    """Create a sphere geometry."""
```

### Sketching Handler (`handlers/design/sketching.py`)

```python
def handle_circle(request_data: dict) -> dict:
    """Create a circle in a sketch."""

def handle_lines(request_data: dict) -> dict:
    """Create lines in a sketch."""

def handle_arc(request_data: dict) -> dict:
    """Create an arc in a sketch."""
```

### Modeling Handler (`handlers/design/modeling.py`)

```python
def handle_extrude(request_data: dict) -> dict:
    """Extrude a sketch profile."""

def handle_revolve(request_data: dict) -> dict:
    """Revolve a sketch profile around an axis."""

def handle_loft(request_data: dict) -> dict:
    """Create a loft between multiple profiles."""
```

## MANUFACTURE Workspace Handler Interfaces

### Setups Handler (`handlers/manufacture/setups.py`)

```python
def handle_list_setups(request_data: dict) -> dict:
    """List all CAM setups in the active document."""

def handle_create_setup(request_data: dict) -> dict:
    """
    Create a new CAM setup.
    
    Args:
        request_data: {
            "name": str,
            "model_geometry": [str],  # Body/component IDs
            "wcs": {
                "origin": [x, y, z],
                "x_axis": [x, y, z],
                "z_axis": [x, y, z]
            },
            "stock": {
                "type": str,          # "relative", "fixed"
                "offset": float       # Stock offset in mm
            }
        }
    """

def handle_modify_setup(request_data: dict) -> dict:
    """Modify an existing CAM setup."""
```

### Toolpaths Handler (`handlers/manufacture/operations/toolpaths.py`)

```python
def handle_list_toolpaths(request_data: dict) -> dict:
    """List toolpaths for a setup or operation."""

def handle_get_toolpath_details(request_data: dict) -> dict:
    """Get detailed information about a specific toolpath."""

def handle_analyze_setup_sequence(request_data: dict) -> dict:
    """Analyze the operation sequence for a setup."""
```

### Tool Libraries Handler (`handlers/manufacture/tool_libraries/libraries.py`)

```python
def handle_list_libraries(request_data: dict) -> dict:
    """List available tool libraries."""

def handle_load_library(request_data: dict) -> dict:
    """Load a specific tool library."""
```

## Interface Patterns and Conventions

### Standard Handler Function Signature

All handler functions follow this pattern:

```python
def handle_operation_name(request_data: dict) -> dict:
    """
    Brief description of what the handler does.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Returns:
        dict: Standardized response dictionary
        
    Raises:
        ValidationError: If request data is invalid
        APIError: If Fusion 360 API call fails
    """
```

### Standard Response Format

All handlers return responses in this format:

```python
{
    "status": "success" | "error",
    "data": dict,           # Operation results (success only)
    "message": str,         # Human-readable message
    "error_code": str,      # Error code (error only)
    "metadata": {           # Optional execution metadata
        "execution_time": float,
        "api_calls": int,
        "request_id": str
    }
}
```

### Error Response Format

Error responses follow this standardized format:

```python
{
    "status": "error",
    "error_code": "VALIDATION_ERROR" | "API_ERROR" | "SYSTEM_ERROR",
    "message": "Human-readable error message",
    "details": {
        "field": "specific field that caused error",
        "value": "invalid value",
        "expected": "expected format or range"
    },
    "suggestions": [
        "Try using positive values for dimensions",
        "Ensure a design document is active"
    ]
}
```

## Data Models and Types

### Common Data Types

```python
# Geometric types
Point3D = tuple[float, float, float]
Vector3D = tuple[float, float, float]
Dimensions = dict[str, float]  # {"width": 10.0, "height": 5.0}

# Fusion 360 object references
EntityToken = str  # Unique identifier for Fusion 360 objects
FeatureId = str    # Feature identifier
BodyId = str       # Body identifier

# Request/Response types
RequestData = dict[str, Any]
ResponseData = dict[str, Any]

# Configuration types
EndpointConfig = dict[str, str]
CategoryConfig = dict[str, Any]
```

### Handler Registration Model

```python
@dataclass
class HandlerInfo:
    name: str                    # Handler identifier
    pattern: str                 # URL pattern for routing
    handler_func: callable       # Handler function reference
    category: str                # Workspace category
    methods: list[str]           # Supported HTTP methods
    dependencies: list[str]      # Required Fusion 360 API modules
    validation_schema: dict      # Request validation schema
    documentation: str           # Handler documentation
    examples: list[dict]         # Usage examples
```

### Module Information Model

```python
@dataclass
class ModuleInfo:
    name: str                    # Module name
    category: str                # Module category
    handlers: list[HandlerInfo]  # Handler functions in module
    loaded: bool                 # Load status
    dependencies: list[str]      # Module dependencies
    fusion_api_requirements: list[str]  # Required Fusion 360 APIs
    version: str                 # Module version
    documentation: str           # Module documentation
```

## Integration Guidelines

### Adding New Handler Modules

1. **Follow Naming Conventions**: Use descriptive names that reflect Fusion 360 terminology
2. **Implement Standard Interface**: All handlers must follow the standard signature
3. **Use Task Queue**: All Fusion 360 API calls must go through the task queue
4. **Handle Errors Gracefully**: Use the error handling system for consistent error responses
5. **Document Thoroughly**: Provide comprehensive documentation and examples

### Cross-Module Communication

When modules need to communicate:

1. **Use Core Services**: Leverage core infrastructure for shared functionality
2. **Minimize Dependencies**: Keep modules as independent as possible
3. **Document Interfaces**: Clearly document any cross-module interfaces
4. **Validate at Runtime**: Check dependencies during module loading
