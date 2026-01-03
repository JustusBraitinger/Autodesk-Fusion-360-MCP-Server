# Developer Onboarding Guide - Fusion 360 Add-In Modular Architecture

## Welcome to the Fusion 360 Add-In Development Team

This guide will help you understand the modular architecture, set up your development environment, and start contributing effectively to the Fusion 360 Add-In project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment Setup](#development-environment-setup)
4. [Understanding the Codebase](#understanding-the-codebase)
5. [Development Workflow](#development-workflow)
6. [Testing Guidelines](#testing-guidelines)
7. [Common Development Tasks](#common-development-tasks)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Prerequisites

### Required Knowledge
- **Python 3.10+**: Strong understanding of Python programming
- **Fusion 360 API**: Basic familiarity with Autodesk Fusion 360 API concepts
- **HTTP/REST APIs**: Understanding of HTTP request/response patterns
- **Threading**: Knowledge of Python threading and thread safety
- **JSON**: Experience with JSON data structures and serialization

### Required Software
- **Autodesk Fusion 360**: Latest version with API access enabled
- **Python 3.10+**: For development and testing
- **uv**: Python package manager (required for this project)
- **Git**: Version control system
- **Code Editor**: VS Code, PyCharm, or similar with Python support

### Recommended Knowledge
- **Fusion 360 Workspaces**: Understanding of Design and MANUFACTURE workspaces
- **CAD/CAM Concepts**: Basic understanding of 3D modeling and machining
- **Property-Based Testing**: Familiarity with Hypothesis testing framework

## Architecture Overview

### High-Level Architecture

The Fusion 360 Add-In uses a modular architecture that mirrors Fusion 360's workspace organization:

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Requests                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 HTTP Server                                 │
│              (Background Thread)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Request Router                               │
│            (Route to Handler Modules)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Handler Modules                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Design    │ │ MANUFACTURE │ │   System    │           │
│  │  Workspace  │ │  Workspace  │ │ Operations  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Task Queue                                 │
│              (Thread-Safe Bridge)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Fusion 360 API                                │
│                (Main UI Thread)                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Workspace Alignment**: Code organization mirrors Fusion 360's workspace structure
2. **Separation of Concerns**: Each module has a single, well-defined responsibility
3. **Thread Safety**: All Fusion 360 API calls are executed on the main UI thread
4. **Modularity**: New functionality can be added without modifying existing code
5. **Backward Compatibility**: All existing API contracts are preserved

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fusion-360-add-in
```

### 2. Set Up Python Environment

```bash
# Install dependencies with uv
uv sync
```

### 3. Install Fusion 360 Add-In

```bash
# For development (creates symlink for live updates)
uv run install-fusion-plugin --dev

# For production (copies files)
uv run install-fusion-plugin
```

### 4. Verify Installation

1. Open Fusion 360
2. Go to **Scripts and Add-Ins** (Shift+S)
3. Find **FusionMCPBridge** in the Add-Ins tab
4. Click **Run** to start the add-in
5. Verify the add-in shows "Running" status

### 5. Test HTTP Server

```bash
# Test basic connectivity
curl http://localhost:5001/test_connection

# Expected response:
{"status": "success", "message": "Connection successful"}
```

## Understanding the Codebase

### Directory Structure

```
FusionMCPBridge/
├── FusionMCPBridge.py          # Main add-in entry point (minimal)
├── core/                       # Core infrastructure
│   ├── config.py               # Configuration management
│   ├── router.py               # Request routing
│   ├── task_queue.py           # Thread-safe task execution
│   ├── loader.py               # Module loading
│   ├── server.py               # HTTP server management
│   ├── error_handling.py       # Error handling system
│   └── validation.py           # Request validation
├── handlers/                   # Handler modules by workspace
│   ├── design/                 # Design workspace operations
│   ├── manufacture/            # MANUFACTURE workspace operations
│   ├── system/                 # System operations
│   └── research/               # Research and development
└── tests/                      # Test files
```

### Key Files to Understand

1. **Main Entry Point (`FusionMCPBridge.py`)**: Minimal add-in entry point
2. **Configuration Manager (`core/config.py`)**: Centralized configuration
3. **Request Router (`core/router.py`)**: Routes HTTP requests to handlers
4. **Task Queue (`core/task_queue.py`)**: Thread-safe Fusion 360 API execution

## Development Workflow

### 1. Create or Modify Handler

```python
# Example: Adding a new geometry operation
# File: handlers/design/geometry.py

def handle_new_shape(request_data: dict) -> dict:
    """Handle new shape creation request."""
    # Validate input
    shape_type = request_data.get('shape_type')
    dimensions = request_data.get('dimensions', {})
    
    # Queue Fusion 360 API task
    result = queue_task('create_shape', shape_type, dimensions)
    
    return {"status": "success", "data": result}
```

### 2. Test Your Changes

```bash
# Reinstall add-in with changes
uv run install-fusion-plugin --dev

# Restart add-in in Fusion 360
# Test with HTTP request
curl -X POST http://localhost:5001/design/shapes/create \
  -H "Content-Type: application/json" \
  -d '{"shape_type": "box", "dimensions": {"width": 10, "height": 5, "depth": 3}}'
```

### 3. Write Tests

```python
# File: tests/test_geometry.py
import pytest
from handlers.design.geometry import handle_new_shape

def test_handle_new_shape():
    """Test new shape creation."""
    request_data = {
        "shape_type": "box",
        "dimensions": {"width": 10, "height": 5, "depth": 3}
    }
    
    result = handle_new_shape(request_data)
    
    assert result["status"] == "success"
    assert "data" in result
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_geometry.py

# Run with coverage
python -m pytest --cov=handlers tests/
```

## Common Development Tasks

### Adding a New Handler Function

1. **Identify Module**: Determine which handler module should contain the function
2. **Implement Handler**: Create the HTTP request handler function
3. **Implement Task**: Create the Fusion 360 API task function
4. **Update Configuration**: Add endpoint definition
5. **Write Tests**: Create unit and integration tests
6. **Update Documentation**: Document the new functionality

### Debugging Common Issues

#### Add-In Not Loading
1. Check Fusion 360 Scripts and Add-Ins panel
2. Look for Python errors in Text Commands panel
3. Verify add-in files are in correct location
4. Check Python syntax and imports

#### HTTP Requests Failing
1. Verify add-in is running (check status)
2. Test basic connectivity: `curl http://localhost:5001/test_connection`
3. Check request format and endpoint URL
4. Review error logs in Fusion 360

## Best Practices

### Code Organization

1. **Follow Module Structure**: Place code in appropriate workspace-aligned modules
2. **Single Responsibility**: Each function should have one clear purpose
3. **Consistent Naming**: Use descriptive names that reflect Fusion 360 terminology
4. **Error Handling**: Always handle errors gracefully and provide meaningful messages

### Fusion 360 API Usage

1. **Thread Safety**: Always use task queue for Fusion 360 API calls
2. **Object Validation**: Check that API objects exist before using them
3. **Resource Cleanup**: Properly dispose of Fusion 360 objects when done
4. **Error Recovery**: Handle API errors gracefully and maintain add-in stability

### Documentation

1. **Function Documentation**: Document all public functions with docstrings
2. **API Documentation**: Document HTTP endpoints and request/response formats
3. **Architecture Documentation**: Keep architecture documentation up to date
4. **Examples**: Provide usage examples for complex functionality

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Module not found" errors
**Solution**: 
- Check Python path and imports
- Verify module structure matches expected patterns
- Ensure `__init__.py` files exist in all directories

#### Issue: HTTP requests return 404
**Solution**:
- Verify endpoint is defined in configuration
- Check request URL matches endpoint pattern
- Ensure handler function is properly registered

#### Issue: Fusion 360 API calls fail
**Solution**:
- Verify calls are made through task queue system
- Check that required Fusion 360 context exists
- Ensure add-in has necessary permissions

### Getting Help

1. **Documentation**: Review architecture and API documentation
2. **Code Examples**: Look at existing handler implementations
3. **Team Members**: Ask experienced team members for guidance
4. **Fusion 360 API Documentation**: Reference official Autodesk documentation

## Resources and References

### Internal Documentation
- [Modular Architecture Documentation](../architecture/MODULAR_ARCHITECTURE.md)
- [Error Handling Guide](./ERROR_HANDLING.md)
- [Configuration Management](./CONFIGURATION_MANAGEMENT.md)

### External Resources
- [Fusion 360 API Documentation](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-A92A4B10-3781-4925-94C6-47DA85A4F65A)
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)
- [Pytest Documentation](https://docs.pytest.org/)
