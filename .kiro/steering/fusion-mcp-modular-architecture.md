---
inclusion: fileMatch
fileMatchPattern: "Server/**/*.py*
---


# Fusion MCP Modular Architecture Guide

## Overview
This steering file documents the modular architecture patterns and conventions for the Fusion 360 MCP Server. Follow these guidelines when adding new functionality, modifying existing tools, or maintaining the codebase.

## Directory Structure and Organization

### Core Infrastructure (`Server/core/`)
**Purpose**: Fundamental system components that provide infrastructure for the entire server.

- `server.py` - FastMCP server initialization and configuration
- `config.py` - Centralized configuration management with category support  
- `registry.py` - Tool and prompt registration system
- `loader.py` - Dynamic module discovery and loading
- `request_handler.py` - Centralized HTTP request handling with retry logic
- `interceptor.py` - Response interception and logging for debugging

**Rule**: Core modules should have minimal dependencies and provide stable interfaces for other components.

### Tool Categories (`Server/tools/`)
**Purpose**: Organized tool modules grouped by functionality.

#### CAD Tools (`Server/tools/cad/`)
- `geometry.py` - Basic 3D shapes (cylinder, box, sphere)
- `sketching.py` - 2D drawing tools (lines, circles, arcs, splines)
- `modeling.py` - 3D operations (extrude, revolve, loft, sweep)
- `features.py` - Features (fillet, holes, patterns, threading)

#### CAM Tools (`Server/tools/cam/`)
- `toolpaths.py` - Toolpath listing and inspection
- `tools.py` - Cutting tool management and library access
- `parameters.py` - Parameter modification and validation
- `heights.py` - Height parameter management
- `passes.py` - Multi-pass configuration
- `linking.py` - Linking parameter management

#### Utility Tools (`Server/tools/utility/`)
- `system.py` - System operations (test, delete, undo)
- `export.py` - Export functionality (STEP, STL)
- `parameters.py` - Parameter management utilities

#### Debug Tools (`Server/tools/debug/`)
- `controls.py` - Debug control tools (interceptor toggle)

### Prompts (`Server/prompts/`)
- `registry.py` - Prompt registration and management
- `templates.py` - All prompt template definitions

## Development Patterns

### Adding New Tools

1. **Determine Category**: Place tools in the appropriate category directory
2. **Use Request Handler**: All HTTP requests must go through `core.request_handler`
3. **Register Tools**: Tools are automatically discovered and registered by the module loader
4. **Follow Naming**: Use descriptive names that match the tool's functionality

```python
# Example tool in tools/cad/geometry.py
from core.request_handler import send_request
from core.config import get_endpoints

@mcp.tool()
def draw_new_shape(param1: float, param2: str):
    """Tool description following existing patterns."""
    endpoint = get_endpoints("cad")["new_shape"]
    payload = {"param1": param1, "param2": param2}
    return send_request(endpoint, payload)
```

### Configuration Management

- **Centralized**: All configuration goes through `core.config`
- **Categorized**: Endpoints organized by tool category (CAD, CAM, Utility, Debug)
- **Consistent**: Use the same configuration interface across all tools

```python
# Access configuration
from core.config import get_endpoints, get_headers, get_timeout

endpoints = get_endpoints("cad")  # Get CAD-specific endpoints
headers = get_headers()           # Get standard headers
timeout = get_timeout()           # Get request timeout
```

### Error Handling Patterns

- **Consistent Errors**: Use standardized error responses from request handler
- **Module Context**: Include module and tool identification in error logs
- **Graceful Degradation**: Continue operation when individual tools fail

```python
# Standard error handling pattern
try:
    return send_request(endpoint, payload)
except requests.RequestException as e:
    logging.error(f"Tool {tool_name} in module {module_name} failed: {e}")
    return {"error": True, "message": str(e), "code": "REQUEST_FAILED"}
```

### Testing Conventions

- **Co-located Tests**: Place `.test.py` files alongside source files
- **Property-Based Tests**: Use Hypothesis for testing universal properties
- **Test Tagging**: Tag property tests with feature and property information
- **Module Isolation**: Test modules independently to verify boundaries

## Architecture Principles

### Single Responsibility
- Each module has one clear purpose
- Tools are grouped by functionality, not implementation details
- Core components provide single, focused services

### Dependency Management
- Core modules have minimal dependencies
- Tool modules depend on core, not on each other
- Clear dependency direction: Tools → Core → External Libraries

### Extensibility
- New tool categories can be added without modifying existing code
- Module loader automatically discovers new modules
- Configuration system supports category-specific settings

### Backward Compatibility
- All existing tool names and signatures are preserved
- API contracts remain identical to monolithic version
- Semantic behavior is maintained across refactoring

## Common Patterns

### Tool Registration
Tools are automatically registered by the module loader. No manual registration required.

### HTTP Requests
Always use the centralized request handler:
```python
from core.request_handler import send_request, send_get_request

# POST request
result = send_request(endpoint, data)

# GET request  
result = send_get_request(endpoint)
```

### Configuration Access
Access configuration through the centralized manager:
```python
from core.config import get_endpoints

endpoints = get_endpoints("cam")  # Category-specific endpoints
toolpath_url = endpoints["cam_toolpaths"]
```

### Error Responses
Use consistent error response format:
```python
{
    "error": True,
    "message": "Human-readable error description",
    "code": "ERROR_CODE_CONSTANT"
}
```

## Migration Guidelines

When moving tools from the monolithic server:

1. **Identify Category**: Determine which category the tool belongs to
2. **Extract Dependencies**: Move shared code to appropriate core modules
3. **Update Imports**: Change imports to use modular structure
4. **Test Compatibility**: Verify tool behavior remains identical
5. **Update Documentation**: Document any new patterns or conventions

## Debugging and Maintenance

### Interceptor Usage
The response interceptor is core infrastructure for debugging:
- Enable via `toggle_response_interceptor` tool
- Logs all HTTP responses with formatted JSON
- Integrated into centralized request handler

### Module Loading Issues
- Check module structure matches expected patterns
- Verify all dependencies are available
- Review loader logs for detailed error information

### Configuration Problems
- Validate configuration format and values
- Check category-specific endpoint definitions
- Verify configuration propagation to all tools

## Future Considerations

### Adding New Categories
1. Create new directory under `tools/`
2. Add category-specific configuration section
3. Implement tools following established patterns
4. Update documentation and steering files

### Performance Optimization
- Module loading is done once at startup
- Request handler includes retry logic and timeout handling
- Configuration is cached and reused across requests

### Testing Strategy
- Unit tests for individual components
- Property-based tests for universal behaviors
- Integration tests for end-to-end functionality
- Backward compatibility tests for API preservation

This architecture provides a solid foundation for maintaining and extending the Fusion 360 MCP Server while preserving all existing functionality and ensuring long-term maintainability.