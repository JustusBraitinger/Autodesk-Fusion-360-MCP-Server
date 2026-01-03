# Fusion 360 Add-In Modular Architecture Documentation

## Overview

This document provides comprehensive documentation for the modular Fusion 360 Add-In architecture, mapping the modular structure to Fusion 360 workspace concepts, documenting module responsibilities and interfaces, and explaining data flow between modules.

## Architecture Mapping to Fusion 360 Workspaces

The modular architecture directly aligns with Fusion 360's workspace organization, providing a natural mapping between code structure and user workflow:

### Fusion 360 Workspace Alignment

```
Fusion 360 Workspaces          →    Modular Architecture
─────────────────────────────────────────────────────────────
Design Workspace               →    handlers/design/
├── Sketch                     →    ├── sketching.py
├── Create (3D Operations)     →    ├── modeling.py
├── Modify (Features)          →    ├── features.py
├── Construct (Geometry)       →    ├── geometry.py
└── Inspect/Utilities          →    └── utilities.py

MANUFACTURE Workspace          →    handlers/manufacture/
├── Setup                      →    ├── setups.py
├── Milling Operations         →    ├── operations/
│   ├── Toolpaths             →    │   ├── toolpaths.py
│   ├── Tools                 →    │   ├── tools.py
│   ├── Heights               →    │   ├── heights.py
│   ├── Passes                →    │   ├── passes.py
│   └── Linking               →    │   └── linking.py
└── Tool Libraries            →    └── tool_libraries/
    ├── Library Management    →        ├── libraries.py
    ├── Tool CRUD             →        ├── tools.py
    └── Search & Filter       →        └── search.py

System Operations              →    handlers/system/
├── Add-in Lifecycle          →    ├── lifecycle.py
├── Parameters                →    ├── parameters.py
└── Utilities                 →    └── utilities.py

Research & Development         →    handlers/research/
├── WCS API Research          →    ├── wcs_api.py
└── Model ID Research         →    └── model_id.py
```

### Workspace Context Preservation

The modular architecture preserves Fusion 360's workspace context:

- **Design Workspace Operations**: All CAD operations (geometry, sketching, modeling, features) are grouped together, maintaining the logical flow from 2D sketches to 3D models to finished features
- **MANUFACTURE Workspace Operations**: CAM operations follow the natural workflow from setup creation through toolpath generation to tool library management
- **Cross-Workspace Operations**: System and research modules provide functionality that spans multiple workspaces

## Module Structure and Organization

### Core Infrastructure (`core/`)

The core infrastructure provides foundational services that all handler modules depend on:

```
core/
├── __init__.py              # Core module initialization
├── config.py                # Centralized configuration management
├── error_handling.py        # Comprehensive error handling system
├── integration.py           # Cross-module integration utilities
├── loader.py                # Dynamic module discovery and loading
├── router.py                # HTTP request routing system
├── server.py                # HTTP server lifecycle management
├── task_queue.py            # Thread-safe Fusion 360 API execution
└── validation.py            # Request and data validation
```

**Purpose**: Provides stable, reusable infrastructure that enables modular handler development without code duplication.

### Handler Modules (`handlers/`)

Handler modules are organized by Fusion 360 workspace concepts and contain the business logic for specific operations:

#### Design Workspace Handlers (`handlers/design/`)

Maps directly to Fusion 360's Design workspace functionality:

```
design/
├── __init__.py              # Design module initialization
├── geometry.py              # Basic 3D shapes (box, cylinder, sphere)
├── sketching.py             # 2D drawing operations (lines, circles, arcs)
├── modeling.py              # 3D operations (extrude, revolve, loft, sweep)
├── features.py              # Features (fillet, holes, patterns, threading)
└── utilities.py             # Design utilities (parameters, export)
```

**Fusion 360 Workflow Alignment**:
1. **Sketching** → Create 2D profiles and constraints
2. **Geometry** → Add basic 3D shapes and construction geometry
3. **Modeling** → Transform sketches into 3D bodies using operations
4. **Features** → Add finishing touches and modifications
5. **Utilities** → Export, parameterize, and manage the design

#### MANUFACTURE Workspace Handlers (`handlers/manufacture/`)

Reflects the complete CAM workflow in Fusion 360's MANUFACTURE workspace:

```
manufacture/
├── __init__.py              # MANUFACTURE module initialization
├── setups.py                # CAM setup creation and management
├── operations/              # Operation-level functionality
│   ├── __init__.py          # Operations module initialization
│   ├── toolpaths.py         # Toolpath listing and analysis
│   ├── tools.py             # Tools assigned to operations
│   ├── heights.py           # Height parameter management
│   ├── passes.py            # Multi-pass configuration
│   └── linking.py           # Linking parameter management
└── tool_libraries/          # Tool library management
    ├── __init__.py          # Tool libraries module initialization
    ├── libraries.py         # Library listing and management
    ├── tools.py             # Tool CRUD operations
    └── search.py            # Tool search and filtering
```

**CAM Workflow Alignment**:
1. **Setup Creation** (`setups.py`) → Define WCS, stock, and machining context
2. **Operation Definition** (`operations/`) → Create and configure machining operations
3. **Tool Management** (`tool_libraries/`) → Select and manage cutting tools
4. **Toolpath Generation** → Generate and optimize machining paths

#### System Operations (`handlers/system/`)

Provides system-level functionality that spans multiple workspaces:

```
system/
├── __init__.py              # System module initialization
├── health.py                # System health monitoring
├── lifecycle.py             # Add-in lifecycle management
├── parameters.py            # System parameter management
└── utilities.py             # System utilities (undo, delete, test)
```

#### Research Operations (`handlers/research/`)

Contains experimental and development functionality:

```
research/
├── __init__.py              # Research module initialization
├── model_id.py              # Model ID research and analysis
└── wcs_api.py               # WCS API research and exploration
```

## Module Responsibilities and Interfaces

### Core Module Responsibilities

#### Configuration Manager (`core/config.py`)
**Responsibility**: Centralized configuration management with category support
**Interface**:
```python
def get_server_config() -> dict
def get_endpoints(category: str = None) -> dict
def get_headers() -> dict
def validate_config() -> bool
def get_category_config(category: str) -> dict
```
**Dependencies**: None (foundational)
**Used By**: All handler modules, router, server

#### Request Router (`core/router.py`)
**Responsibility**: HTTP request routing to appropriate handler modules
**Interface**:
```python
def route_request(path: str, method: str, data: dict) -> dict
def register_handler(pattern: str, handler: callable) -> None
def get_routes() -> dict
def validate_route(path: str) -> bool
```
**Dependencies**: Configuration Manager, Error Handling
**Used By**: HTTP Server, Handler Modules

#### Task Queue System (`core/task_queue.py`)
**Responsibility**: Thread-safe Fusion 360 API execution
**Interface**:
```python
def queue_task(task_type: str, *args, **kwargs) -> None
def process_tasks() -> None
def register_task_handler(task_type: str, handler: callable) -> None
def get_queue_status() -> dict
```
**Dependencies**: Error Handling
**Used By**: All handler modules requiring Fusion 360 API access

#### Module Loader (`core/loader.py`)
**Responsibility**: Dynamic discovery and loading of handler modules
**Interface**:
```python
def load_all_modules() -> list
def load_category(category: str) -> list
def get_loaded_modules() -> list
def validate_module(module) -> bool
def reload_module(module_name: str) -> bool
```
**Dependencies**: Configuration Manager, Error Handling
**Used By**: Main add-in file, HTTP Server

#### Error Handling (`core/error_handling.py`)
**Responsibility**: Comprehensive error handling and logging
**Interface**:
```python
def handle_module_error(module_name: str, error: Exception) -> dict
def log_operation_error(operation: str, context: dict, error: Exception) -> None
def create_error_response(error_type: str, message: str, context: dict) -> dict
def validate_dependencies(module_name: str, dependencies: list) -> bool
```
**Dependencies**: None (foundational)
**Used By**: All modules

## Data Flow Between Modules

### Request Processing Flow

```
HTTP Request → Router → Handler Module → Task Queue → Fusion 360 API → Response
     ↓              ↓           ↓             ↓              ↓           ↓
Configuration  Route      Module        Task         API Call    Response
   Manager    Matching   Selection    Queuing       Execution   Formatting
```

### Threading and Concurrency

#### Thread Safety Model
```
HTTP Server Thread → Request Queue → Main UI Thread
                  ↓                ↓
            Background          Fusion 360 API
            Processing          Execution
```

**Key Principles**:
- HTTP server runs in background thread
- All Fusion 360 API calls execute on main UI thread
- Task queue provides thread-safe communication
- Error isolation prevents thread contamination

## Integration Points

### Fusion 360 API Integration

Each handler module integrates with specific Fusion 360 API components:

- **Design Handlers**: `adsk.fusion` (Design workspace APIs)
- **MANUFACTURE Handlers**: `adsk.cam` (CAM workspace APIs)
- **System Handlers**: `adsk.core` (Core application APIs)
- **All Handlers**: `adsk.core.Application` (Application context)

### Backward Compatibility

The modular architecture maintains complete backward compatibility:

- **API Contracts**: All existing endpoints maintain identical request/response formats
- **Behavior Preservation**: Semantic behavior remains unchanged
- **Error Responses**: Error codes and messages match original implementation
- **Performance**: Response times and resource usage remain consistent

## Development Guidelines

### Adding New Modules

1. **Determine Category**: Identify appropriate workspace category
2. **Create Module Structure**: Follow established directory patterns
3. **Implement Handlers**: Use standard handler patterns and interfaces
4. **Register Handlers**: Handlers are automatically discovered by module loader
5. **Update Configuration**: Add endpoint definitions to configuration
6. **Test Integration**: Verify module loading and request routing
7. **Update Documentation**: Document new module responsibilities and interfaces

### Cross-Module Dependencies

- **Minimize Dependencies**: Keep modules as independent as possible
- **Use Core Services**: Leverage core infrastructure for common functionality
- **Document Dependencies**: Clearly document any cross-module dependencies
- **Validate at Load Time**: Check dependencies during module loading

This modular architecture provides a maintainable, extensible foundation for the Fusion 360 Add-In while preserving the natural workflow and organization that Fusion 360 users expect.
