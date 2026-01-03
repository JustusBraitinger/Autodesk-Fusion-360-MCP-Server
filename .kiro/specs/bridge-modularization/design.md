# Design Document

## Overview

This design transforms the monolithic Fusion 360 Add-In (`FusionMCPBridge.py`) into a modular, maintainable architecture aligned with Fusion 360's workspace concepts. The current 2800+ line single file will be restructured into logical modules organized by Fusion 360 functionality (Design workspace operations, MANUFACTURE workspace operations), with centralized HTTP request handling, task queue management, and configuration. The modular design maintains full backward compatibility while enabling easier development, testing, and maintenance, and respects Fusion 360's threading constraints.

## Architecture

The modular architecture follows Fusion 360's workspace organization with clear separation of concerns:

```
FusionMCPBridge/
├── FusionMCPBridge.py         # Minimal add-in entry point and HTTP server
├── core/                      # Core system components
│   ├── __init__.py
│   ├── server.py             # HTTP server setup and lifecycle management
│   ├── config.py             # Centralized configuration and endpoint management
│   ├── router.py             # HTTP request routing system
│   ├── task_queue.py         # Centralized task queue and processor
│   └── loader.py             # Module discovery and loading system
├── handlers/                  # Request handler modules organized by Fusion 360 concepts
│   ├── __init__.py
│   ├── design/               # Design workspace operations (CAD)
│   │   ├── __init__.py
│   │   ├── geometry.py       # Basic shapes (box, cylinder, sphere)
│   │   ├── sketching.py      # 2D drawing (lines, circles, arcs, splines)
│   │   ├── modeling.py       # 3D operations (extrude, revolve, loft, sweep)
│   │   ├── features.py       # Features (fillet, holes, patterns, threading)
│   │   └── utilities.py      # Design utilities (parameters, selection, export)
│   ├── manufacture/          # MANUFACTURE workspace operations (CAM)
│   │   ├── __init__.py
│   │   ├── setups.py         # CAM setup management and configuration
│   │   ├── operations/       # Operation-level functionality (toolpaths and parameters)
│   │   │   ├── __init__.py
│   │   │   ├── toolpaths.py  # Toolpath listing, analysis, and management
│   │   │   ├── tools.py      # Tools assigned to operations
│   │   │   ├── heights.py    # Height parameter management
│   │   │   ├── passes.py     # Multi-pass configuration
│   │   │   └── linking.py    # Linking parameter management
│   │   ├── tools.py          # Cutting tool management and operations
│   │   ├── tool_libraries/   # Tool library management (part of MANUFACTURE)
│   │   │   ├── __init__.py
│   │   │   ├── libraries.py  # Library listing and management
│   │   │   ├── tools.py      # Tool CRUD operations
│   │   │   └── search.py     # Tool search and filtering
│   │   └── parameters.py     # General CAM parameter modification and validation
│   ├── research/             # Research and development operations
│   │   ├── __init__.py
│   │   ├── wcs_api.py        # WCS API research
│   │   └── model_id.py       # Model ID research
│   └── system/               # System operations
│       ├── __init__.py
│       ├── lifecycle.py      # Add-in lifecycle management
│       ├── parameters.py     # System parameter management
│       └── utilities.py      # System utilities (test, undo, delete)
```

## Components and Interfaces

### Core Components

#### Add-In Entry Point (`FusionMCPBridge.py`)
- **Purpose**: Minimal add-in entry point focused on lifecycle and HTTP server coordination
- **Interface**: 
  - `run(context)`: Add-in startup and module initialization
  - `stop(context)`: Add-in shutdown and cleanup coordination
- **Responsibilities**: Add-in lifecycle, HTTP server startup, module loading coordination
- **Dependencies**: Core modules (server, loader, task_queue)

#### HTTP Server (`core/server.py`)
- **Purpose**: HTTP server setup, request handling, and lifecycle management
- **Interface**:
  - `create_server() -> HTTPServer`: Creates configured HTTP server
  - `start_server()`: Starts HTTP server in background thread
  - `stop_server()`: Stops HTTP server and cleans up resources
- **Dependencies**: Router, Configuration Manager

#### Configuration Manager (`core/config.py`)
- **Purpose**: Centralized configuration management with category support aligned to Fusion 360 workspaces
- **Interface**:
  - `get_server_config() -> dict`: Returns HTTP server configuration
  - `get_endpoints(category: str = None) -> dict`: Returns endpoints by category
  - `get_headers() -> dict`: Returns HTTP headers
  - `validate_config() -> bool`: Validates configuration integrity
- **Categories**: Design, Manufacture, Research, System

#### Request Router (`core/router.py`)
- **Purpose**: HTTP request routing to appropriate handler modules based on path patterns
- **Interface**:
  - `route_request(path: str, method: str, data: dict) -> dict`: Route request to handler
  - `register_handler(pattern: str, handler: callable)`: Register path pattern handler
  - `get_routes() -> dict`: Get all registered routes
- **Features**: Pattern matching, method-specific routing, error handling

#### Task Queue System (`core/task_queue.py`)
- **Purpose**: Centralized task queue and processor for thread-safe Fusion 360 API calls
- **Interface**:
  - `queue_task(task_type: str, *args) -> None`: Queue task for execution
  - `process_tasks()`: Process queued tasks on main thread
  - `register_task_handler(task_type: str, handler: callable)`: Register task handler
- **Features**: Thread safety, error isolation, task prioritization
- **Integration**: Used by all handler modules for Fusion 360 API calls

#### Module Loader (`core/loader.py`)
- **Purpose**: Dynamic discovery and loading of handler modules
- **Interface**:
  - `load_all_modules()`: Discover and load all handler modules
  - `load_category(category: str)`: Load specific handler category
  - `get_loaded_modules() -> list`: Get list of loaded modules
  - `validate_module(module) -> bool`: Validate module structure and dependencies

### Handler Modules

#### Design Workspace Handlers (`handlers/design/`)

**Geometry Handler (`handlers/design/geometry.py`)**
- Basic 3D shapes: `handle_box`, `handle_cylinder`, `handle_sphere`
- Positioning and coordinate management
- Unit conversion handling (mm to cm)

**Sketching Handler (`handlers/design/sketching.py`)**
- 2D drawing: `handle_circle`, `handle_lines`, `handle_arc`, `handle_spline`
- Plane management and coordinate systems
- Sketch creation and management

**Modeling Handler (`handlers/design/modeling.py`)**
- 3D operations: `handle_extrude`, `handle_revolve`, `handle_loft`, `handle_sweep`
- Boolean operations: `handle_boolean_operation`
- Advanced modeling features

**Features Handler (`handlers/design/features.py`)**
- Features: `handle_fillet`, `handle_shell`, `handle_holes`, `handle_thread`
- Patterns: `handle_circular_pattern`, `handle_rectangular_pattern`
- Feature modification and management

**Utilities Handler (`handlers/design/utilities.py`)**
- Export: `handle_export_step`, `handle_export_stl`
- Parameters: `handle_set_parameter`, `handle_list_parameters`
- Selection and manipulation utilities

#### MANUFACTURE Workspace Handlers (`handlers/manufacture/`)

**Setups Handler (`handlers/manufacture/setups.py`)**
- Setup management: `handle_list_setups`, `handle_get_setup`, `handle_create_setup`
- Setup modification: `handle_modify_setup`, `handle_duplicate_setup`
- Setup deletion: `handle_delete_setup`

**Operation Handlers (`handlers/manufacture/operations/`)**

**Toolpaths Handler (`handlers/manufacture/operations/toolpaths.py`)**
- Toolpath listing: `handle_list_toolpaths`, `handle_list_toolpaths_with_heights`
- Toolpath details: `handle_get_toolpath_details`, `handle_get_toolpath_parameters`
- Sequence analysis: `handle_analyze_setup_sequence`

**Tools Handler (`handlers/manufacture/operations/tools.py`)**
- Operation tool listing: `handle_list_cam_tools` (tools assigned to operations)
- Tool assignment and operation-specific tool management

**Heights Handler (`handlers/manufacture/operations/heights.py`)**
- Height parameters: `handle_get_detailed_heights`
- Safety height validation

**Passes Handler (`handlers/manufacture/operations/passes.py`)**
- Pass configuration: `handle_get_toolpath_passes`, `handle_modify_toolpath_passes`
- Pass validation and optimization

**Linking Handler (`handlers/manufacture/operations/linking.py`)**
- Linking parameters: `handle_get_toolpath_linking`, `handle_modify_toolpath_linking`
- Lead-in/lead-out configuration

**Tool Library Handlers (`handlers/manufacture/tool_libraries/`)**

**Libraries Handler (`handlers/manufacture/tool_libraries/libraries.py`)**
- Library listing: `handle_list_libraries` (available tool library files)
- Library management and access

**Tools Handler (`handlers/manufacture/tool_libraries/tools.py`)**
- Tool catalog CRUD: `handle_list_tools`, `handle_get_tool`, `handle_create_tool` (tools in library catalogs)
- Tool library modification: `handle_modify_tool`, `handle_delete_tool`
- Tool duplication: `handle_duplicate_tool` (within library catalogs)

**Search Handler (`handlers/manufacture/tool_libraries/search.py`)**
- Tool catalog search: `handle_search_tools` (search within library catalogs)
- Advanced filtering and search capabilities across tool libraries

**Parameters Handler (`handlers/manufacture/parameters.py`)**
- General CAM parameter modification: `handle_modify_toolpath_parameter`
- Parameter validation and constraints

#### Research Handlers (`handlers/research/`)

**WCS API Handler (`handlers/research/wcs_api.py`)**
- WCS research: `handle_wcs_api_research`
- API exploration and documentation

**Model ID Handler (`handlers/research/model_id.py`)**
- Model ID research: `handle_model_id_research`
- ID pattern analysis and validation

#### System Handlers (`handlers/system/`)

**Lifecycle Handler (`handlers/system/lifecycle.py`)**
- System operations: `handle_test_connection`
- Add-in status and health checks

**Parameters Handler (`handlers/system/parameters.py`)**
- Parameter management: `handle_count_parameters`, `handle_list_parameters`
- System-level parameter operations

**Utilities Handler (`handlers/system/utilities.py`)**
- System utilities: `handle_undo`, `handle_delete_everything`
- System maintenance operations

## Data Models

### Handler Registration Model
```python
@dataclass
class HandlerInfo:
    name: str
    pattern: str
    handler_func: callable
    category: str
    methods: list[str]
    dependencies: list[str]
```

### Task Model
```python
@dataclass
class Task:
    task_type: str
    args: tuple
    kwargs: dict
    priority: int
    timestamp: float
    module_context: str
```

### Configuration Model
```python
@dataclass
class EndpointConfig:
    category: str
    base_path: str
    endpoints: dict[str, str]
    methods: dict[str, list[str]]
    validation_rules: dict[str, dict]
```

### Module Info Model
```python
@dataclass
class ModuleInfo:
    name: str
    category: str
    handlers: list[HandlerInfo]
    loaded: bool
    dependencies: list[str]
    fusion_api_requirements: list[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Module loading and discovery properties (1.1, 1.4, 1.5) can be combined into a comprehensive module system property
- Request routing properties (2.1, 2.3, 2.4, 2.5) can be consolidated into a centralized routing property
- Module isolation properties (3.2, 5.2, 6.2, 10.2) can be merged into a general isolation property
- Task queue properties (4.1, 4.2, 4.3, 4.4, 4.5) can be combined into a centralized task processing property
- Error handling properties (8.1, 8.2, 8.5) can be consolidated into a comprehensive error handling property
- Backward compatibility properties (9.1, 9.2, 9.4, 9.5) can be merged into a single compatibility property

### Core Properties

**Property 1: Module Discovery and Loading**
*For any* valid handler module directory structure, the system should automatically discover, validate dependencies, and load all modules with their handlers registered correctly
**Validates: Requirements 1.1, 1.4, 1.5**

**Property 2: Request Routing and Handling**
*For any* HTTP request with a valid path, the system should route it to the appropriate handler module and maintain consistent error response formats across all modules
**Validates: Requirements 2.1, 2.3, 2.4, 2.5**

**Property 3: Module Organization and Categorization**
*For any* operation type (Design, MANUFACTURE, Tool Library, Research), all related operations should be properly categorized in their respective modules according to Fusion 360 workspace concepts
**Validates: Requirements 1.3, 3.1, 3.3, 5.1, 6.1, 10.1**

**Property 4: Module Isolation and Independence**
*For any* modification to one module category, other module categories should remain completely unaffected and continue to function normally
**Validates: Requirements 3.2, 3.4, 5.2, 6.2, 6.4, 10.2, 10.4**

**Property 5: Centralized Task Queue Processing**
*For any* Fusion 360 API call from any module, the call should go through the centralized task queue system with proper thread safety, error isolation, and consistent logging
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

**Property 6: System Extensibility**
*For any* new module or handler added to the system, it should be automatically discovered and integrated without requiring modifications to existing core code or other modules
**Validates: Requirements 1.2, 2.3, 5.3, 6.3, 10.3**

**Property 7: Main File Minimalism**
*For any* system functionality, the main add-in file should delegate to specialized modules rather than implementing functionality directly, containing only lifecycle management and coordination
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

**Property 8: Comprehensive Error Handling**
*For any* error condition (module load failure, operation error, dependency missing), the system should provide detailed error messages with context, maintain stability, and continue operating with available modules
**Validates: Requirements 8.1, 8.2, 8.3, 8.5**

**Property 9: Configuration Management Consistency**
*For any* configuration change (endpoints, settings), all dependent modules should automatically use the updated configuration without requiring individual module modifications
**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

**Property 10: Backward Compatibility Preservation**
*For any* existing HTTP endpoint and response format, the modular system should maintain identical API contracts and behavior as the original monolithic implementation
**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

**Property 11: Fusion 360 Terminology Consistency**
*For any* module name, endpoint, or error message, the system should use official Fusion 360 business terminology as defined in the fusion-360-business-language steering file
**Validates: Requirements 14.1, 14.3, 14.4**

**Property 12: System Resilience and Stability**
*For any* module failure or error, the system should isolate the failure, continue operating with remaining functional modules, and not cascade failures across the entire system
**Validates: Requirements 8.5, 9.3**

## Error Handling

### Module Loading Errors
- **Missing Dependencies**: Log detailed error with missing Fusion 360 API requirements and continue loading other modules
- **Invalid Module Structure**: Report structural issues and skip malformed modules
- **Import Failures**: Capture import errors with full traceback and module context

### Runtime Errors
- **Handler Execution Failures**: Wrap handler errors with module context and operation identification
- **Task Queue Errors**: Isolate task failures and provide detailed error information without affecting other queued tasks
- **Configuration Errors**: Validate configuration on load and provide specific error messages for invalid values
- **HTTP Request Errors**: Standardize HTTP error responses across all handler modules with consistent error codes

### Recovery Strategies
- **Graceful Degradation**: Continue operation with available modules when some fail to load
- **Error Isolation**: Prevent errors in one module from affecting others
- **Task Queue Resilience**: Ensure task failures don't block other tasks or crash the task processor
- **Diagnostic Information**: Provide detailed logging for troubleshooting module and handler issues

## Testing Strategy

### Unit Testing Approach
- **Module Loading Tests**: Verify correct loading of individual handler modules and error handling for malformed modules
- **Handler Registration Tests**: Test handler registration process and validation of handler metadata
- **Request Routing Tests**: Verify HTTP request routing to appropriate handlers and error handling for invalid routes
- **Task Queue Tests**: Test task queuing, processing, and error isolation between tasks
- **Configuration Tests**: Verify configuration loading, validation, and propagation to handlers
- **Integration Points**: Test interactions between core components (router, loader, config manager, task queue)

### Property-Based Testing Requirements
- **Testing Framework**: Use Hypothesis for Python property-based testing with minimum 100 iterations per property
- **Property Test Tagging**: Each property-based test must include a comment with the format: `**Feature: bridge-modularization, Property {number}: {property_text}**`
- **Test Coverage**: Each correctness property must be implemented by a single property-based test
- **Generator Strategy**: Create smart generators that produce valid module structures, handler definitions, HTTP requests, and task scenarios while respecting Fusion 360's threading constraints

### Dual Testing Approach
- **Unit Tests**: Cover specific examples, edge cases, and error conditions for individual components
- **Property Tests**: Verify universal properties that should hold across all inputs and module combinations
- **Complementary Coverage**: Unit tests catch concrete bugs while property tests verify general correctness of the modular architecture
- **Fusion 360 Constraints**: Tests must respect Fusion 360's threading model and API limitations

### Test Organization
- Unit tests will be co-located with source files using `.test.py` suffix
- Property-based tests will focus on core system properties like module loading, request routing, and task queue processing
- Integration tests will verify end-to-end functionality from HTTP request through task execution
- Mock Fusion 360 API components will be used where possible to enable testing outside of Fusion 360 environment