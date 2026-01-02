# Design Document

## Overview

This design transforms the monolithic Fusion 360 MCP Server into a modular, maintainable architecture. The current 2500+ line single file will be restructured into logical modules organized by functionality, with centralized configuration management, request handling, and tool registration. The modular design maintains full backward compatibility while enabling easier development, testing, and maintenance.

## Architecture

The modular architecture follows a layered approach with clear separation of concerns:

```
Server/
├── MCP_Server.py              # Minimal server entry point
├── core/                      # Core system components
│   ├── __init__.py
│   ├── server.py             # FastMCP server setup and initialization
│   ├── config.py             # Centralized configuration management
│   ├── registry.py           # Tool and prompt registration system
│   ├── loader.py             # Dynamic module loading system
│   ├── request_handler.py    # Centralized HTTP request handling
│   └── interceptor.py        # Response interceptor functionality (moved from root)
├── tools/                     # Tool modules organized by category
│   ├── __init__.py
│   ├── cad/                  # CAD-related tools
│   │   ├── __init__.py
│   │   ├── geometry.py       # Basic shapes (cylinder, box, sphere)
│   │   ├── sketching.py      # 2D drawing tools (lines, circles, arcs)
│   │   ├── modeling.py       # 3D modeling (extrude, revolve, loft)
│   │   └── features.py       # Features (fillet, holes, patterns)
│   ├── cam/                  # CAM-related tools
│   │   ├── __init__.py
│   │   ├── toolpaths.py      # Toolpath management and inspection
│   │   ├── tools.py          # Cutting tool management
│   │   ├── parameters.py     # Parameter modification tools
│   │   ├── heights.py        # Height parameter tools
│   │   ├── passes.py         # Multi-pass configuration tools
│   │   └── linking.py        # Linking parameter tools
│   ├── utility/              # Utility tools
│   │   ├── __init__.py
│   │   ├── system.py         # System tools (test, delete, undo)
│   │   ├── export.py         # Export functionality (STEP, STL)
│   │   └── parameters.py     # Parameter management
│   └── debug/                # Debug and development tools
│       ├── __init__.py
│       └── controls.py       # Debug control tools (toggle_response_interceptor)
├── prompts/                   # Prompt templates
│   ├── __init__.py
│   ├── registry.py           # Prompt registration system
│   └── templates.py          # Prompt template definitions
```

## Components and Interfaces

### Core Components

#### Server (`core/server.py`)
- **Purpose**: FastMCP server initialization and configuration
- **Interface**: 
  - `create_server() -> FastMCP`: Creates configured FastMCP instance
  - `setup_instructions() -> str`: Returns server instructions
- **Dependencies**: Configuration Manager, Tool Registry

#### Configuration Manager (`core/config.py`)
- **Purpose**: Centralized configuration management with category support
- **Interface**:
  - `get_base_url() -> str`: Returns Fusion 360 base URL
  - `get_endpoints(category: str = None) -> dict`: Returns endpoints by category
  - `get_headers() -> dict`: Returns HTTP headers
  - `get_timeout() -> int`: Returns request timeout
- **Categories**: CAD, CAM, Utility, Debug

#### Tool Registry (`core/registry.py`)
- **Purpose**: Central registration and management of tools and prompts
- **Interface**:
  - `register_tool(tool_func, category: str)`: Register a tool function
  - `register_prompt(prompt_func, category: str)`: Register a prompt function
  - `get_tools(category: str = None) -> list`: Get registered tools
  - `get_prompts(category: str = None) -> list`: Get registered prompts
  - `validate_dependencies() -> bool`: Validate all tool dependencies

#### Module Loader (`core/loader.py`)
- **Purpose**: Dynamic discovery and loading of tool modules
- **Interface**:
  - `load_all_modules()`: Discover and load all tool modules
  - `load_category(category: str)`: Load specific tool category
  - `get_loaded_modules() -> list`: Get list of loaded modules
  - `validate_module(module) -> bool`: Validate module structure

#### Request Handler (`core/request_handler.py`)
- **Purpose**: Centralized HTTP request handling with consistent error handling
- **Interface**:
  - `send_request(endpoint: str, data: dict, method: str = "POST") -> dict`: Send HTTP request
  - `send_get_request(endpoint: str) -> dict`: Send GET request
  - `send_post_request(endpoint: str, data: dict) -> dict`: Send POST request
- **Features**: Retry logic, timeout handling, error standardization
- **Dependencies**: Uses `core.interceptor` for optional response logging and debugging

#### Interceptor (`core/interceptor.py`)
- **Purpose**: Response interception and logging for debugging HTTP communication
- **Interface**: 
  - `intercept_response(endpoint: str, response: Response, method: str) -> dict`: Process and optionally log responses
  - `toggle_interceptor() -> bool`: Toggle interceptor state
  - `is_interceptor_enabled() -> bool`: Check interceptor state
- **Integration**: Used by request handler for consistent logging across all HTTP requests

### Tool Modules

#### CAD Tools

**Geometry Tools (`tools/cad/geometry.py`)**
- Basic 3D shapes: `draw_cylinder`, `draw_box`, `draw_sphere`
- Positioning and coordinate management
- Unit conversion handling

**Sketching Tools (`tools/cad/sketching.py`)**
- 2D drawing: `draw2Dcircle`, `draw_lines`, `draw_one_line`, `draw_arc`
- Spline creation: `spline`
- Plane management and coordinate systems

**Modeling Tools (`tools/cad/modeling.py`)**
- 3D operations: `extrude`, `extrude_thin`, `cut_extrude`, `revolve`
- Advanced modeling: `loft`, `sweep`
- Boolean operations: `boolean_operation`

**Feature Tools (`tools/cad/features.py`)**
- Features: `fillet_edges`, `shell_body`, `draw_holes`
- Patterns: `circular_pattern`, `rectangular_pattern`
- Threading: `create_thread`

#### CAM Tools

**Toolpath Tools (`tools/cam/toolpaths.py`)**
- Toolpath listing: `list_cam_toolpaths`, `list_toolpaths_with_heights`
- Toolpath details: `get_toolpath_details`
- Sequence analysis: `analyze_toolpath_sequence`

**Tool Management (`tools/cam/tools.py`)**
- Tool listing: `list_cam_tools`, `list_tool_libraries`
- Tool information: `get_tool_info`
- Tool library management functions

**Parameter Tools (`tools/cam/parameters.py`)**
- Parameter modification: `modify_toolpath_parameter`
- Parameter validation and constraints

**Height Tools (`tools/cam/heights.py`)**
- Height parameter management: `get_toolpath_heights`
- Safety height validation

**Pass Tools (`tools/cam/passes.py`)**
- Multi-pass configuration: `get_toolpath_passes`, `modify_toolpath_passes`
- Pass validation and optimization

**Linking Tools (`tools/cam/linking.py`)**
- Linking parameters: `get_toolpath_linking`, `modify_toolpath_linking`
- Lead-in/lead-out configuration

### Prompt System

#### Prompt Registry (`prompts/registry.py`)
- **Purpose**: Registration and management of prompt templates
- **Interface**:
  - `register_prompt(name: str, template_func)`: Register prompt template
  - `get_prompt(name: str) -> str`: Get prompt by name
  - `list_prompts() -> list`: List all available prompts

#### Prompt Templates (`prompts/templates.py`)
- All existing prompts: `weingals`, `magnet`, `dna`, `flansch`, `vase`, `teil`, `kompensator`
- Template-based prompt generation
- Parameter substitution support

## Data Models

### Tool Registration Model
```python
@dataclass
class ToolInfo:
    name: str
    function: callable
    category: str
    dependencies: list[str]
    description: str
    parameters: dict
```

### Configuration Model
```python
@dataclass
class EndpointConfig:
    category: str
    endpoints: dict[str, str]
    headers: dict[str, str]
    timeout: int
```

### Module Info Model
```python
@dataclass
class ModuleInfo:
    name: str
    category: str
    tools: list[ToolInfo]
    prompts: list[str]
    loaded: bool
    dependencies: list[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Module loading properties (1.1, 1.4) can be combined into a comprehensive module discovery property
- Tool categorization properties (2.1, 2.4) can be merged into a single boundary enforcement property  
- Request handling properties (3.1, 3.4, 3.5) can be consolidated into a centralized request handling property
- Configuration properties (4.1, 4.2) can be combined into a configuration management property
- Error handling properties (7.1, 7.2, 7.3) can be merged into a comprehensive error reporting property

### Core Properties

**Property 1: Module Discovery and Loading**
*For any* valid tool module directory structure, the system should automatically discover, validate, and load all modules with their tools and prompts registered correctly
**Validates: Requirements 1.1, 1.4, 1.5**

**Property 2: Tool Categorization and Isolation**
*For any* tool category (CAD, CAM, Utility, Debug), all tools within that category should be isolated from other categories and modifications to one category should not affect others
**Validates: Requirements 2.1, 2.2, 2.4**

**Property 3: Extensible Module System**
*For any* new tool category or module, the system should support adding it without requiring modifications to existing core code or other modules
**Validates: Requirements 1.2, 2.3, 4.3**

**Property 4: Centralized Request Handling**
*For any* HTTP request made by any tool, the request should go through the centralized request handler with consistent error handling, retry logic, and timeout behavior
**Validates: Requirements 3.1, 3.2, 3.4, 3.5**

**Property 5: Configuration Management Consistency**
*For any* configuration change (endpoints, headers, timeouts), all dependent tools should automatically use the updated configuration without requiring individual tool modifications
**Validates: Requirements 4.1, 4.2, 4.4**

**Property 6: Server Minimalism and Delegation**
*For any* server functionality (tool registration, configuration access, tool discovery), the main server file should delegate to appropriate specialized components rather than implementing the functionality directly
**Validates: Requirements 5.2, 5.3, 5.4**

**Property 7: Prompt-Tool Independence**
*For any* prompt modification or addition, the change should not require modifications to tool implementations and should support dynamic registration
**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

**Property 8: Comprehensive Error Handling**
*For any* error condition (module load failure, tool error, dependency missing), the system should provide detailed error messages with context and maintain stability by continuing operation with available modules
**Validates: Requirements 7.1, 7.2, 7.3, 7.5**

**Property 9: Backward Compatibility Preservation**
*For any* existing tool or API contract, the modular system should maintain identical tool names, signatures, and behavior as the original monolithic implementation
**Validates: Requirements 8.1, 8.2, 8.4, 8.5**

**Property 10: System Resilience**
*For any* module failure or error, the system should continue operating with remaining functional modules and not cascade failures across the entire system
**Validates: Requirements 7.5, 8.3**

## Error Handling

### Module Loading Errors
- **Missing Dependencies**: Log detailed error with missing dependency names and continue loading other modules
- **Invalid Module Structure**: Report structural issues and skip malformed modules
- **Import Failures**: Capture import errors with full traceback and module context

### Runtime Errors
- **Tool Execution Failures**: Wrap tool errors with module context and tool identification
- **Configuration Errors**: Validate configuration on load and provide specific error messages for invalid values
- **Request Failures**: Standardize HTTP error responses across all tools with consistent error codes

### Recovery Strategies
- **Graceful Degradation**: Continue operation with available modules when some fail to load
- **Error Isolation**: Prevent errors in one module from affecting others
- **Diagnostic Information**: Provide detailed logging for troubleshooting module and tool issues

## Testing Strategy

### Unit Testing Approach
- **Module Loading Tests**: Verify correct loading of individual modules and error handling for malformed modules
- **Tool Registration Tests**: Test tool registration process and validation of tool metadata
- **Configuration Tests**: Verify configuration loading, validation, and propagation to tools
- **Request Handler Tests**: Test HTTP request handling, retry logic, and error responses
- **Integration Points**: Test interactions between core components (registry, loader, config manager)

### Property-Based Testing Requirements
- **Testing Framework**: Use Hypothesis for Python property-based testing with minimum 100 iterations per property
- **Property Test Tagging**: Each property-based test must include a comment with the format: `**Feature: server-modularization, Property {number}: {property_text}**`
- **Test Coverage**: Each correctness property must be implemented by a single property-based test
- **Generator Strategy**: Create smart generators that produce valid module structures, tool definitions, and configuration scenarios

### Dual Testing Approach
- **Unit Tests**: Cover specific examples, edge cases, and error conditions for individual components
- **Property Tests**: Verify universal properties that should hold across all inputs and module combinations
- **Complementary Coverage**: Unit tests catch concrete bugs while property tests verify general correctness of the modular architecture

### Test Organization
- Unit tests will be co-located with source files using `.test.py` suffix
- Property-based tests will focus on core system properties like module loading, tool registration, and configuration management
- Integration tests will verify end-to-end functionality from module loading through tool execution