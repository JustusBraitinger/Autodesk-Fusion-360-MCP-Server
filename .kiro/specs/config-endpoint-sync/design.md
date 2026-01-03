# Design Document: Config Endpoint Synchronization

## Overview

This feature synchronizes the `FusionMCPBridge/core/config.py` endpoint definitions with the actual handler registrations across the modular architecture. The current config.py has approximately 11% accuracy with 16 incorrect endpoints, 25 missing endpoints, and 1 obsolete endpoint. This update will bring the configuration into alignment with the implemented handlers and establish processes to prevent future drift.

## Architecture

The configuration system follows a centralized pattern where `ConfigurationManager` maintains endpoint definitions organized by Fusion 360 workspace categories. The actual routing is handled by `RequestRouter` through `register_handler()` calls in handler modules.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ConfigurationManager                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   DESIGN    │  │ MANUFACTURE │  │   SYSTEM    │              │
│  │  endpoints  │  │  endpoints  │  │  endpoints  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RequestRouter                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  register_handler(path, handler, methods, category)      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  setups.py      │ │  toolpaths.py   │ │  libraries.py   │
│  handlers       │ │  handlers       │ │  handlers       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Components and Interfaces

### ConfigurationManager Updates

The `_endpoints` dictionary in `ConfigurationManager` will be updated to match actual handler registrations:

**MANUFACTURE Workspace Endpoint Groups:**

1. **setups** - CAM setup management
2. **toolpaths** - Toolpath listing and parameters
3. **operations** - Operation-level management (NEW)
4. **tools** - CAM tool management
5. **tool_libraries** - Tool library management
6. **tool_search** - Tool search functionality (NEW)

### Handler Module to Config Mapping

| Handler Module | Config Endpoint Group |
|----------------|----------------------|
| `handlers/manufacture/setups.py` | `setups` |
| `handlers/manufacture/operations/toolpaths.py` | `toolpaths` |
| `handlers/manufacture/operations/heights.py` | `operations` |
| `handlers/manufacture/operations/passes.py` | `operations` |
| `handlers/manufacture/operations/linking.py` | `operations` |
| `handlers/manufacture/operations/tools.py` | `tools` |
| `handlers/manufacture/tool_libraries/libraries.py` | `tool_libraries` |
| `handlers/manufacture/tool_libraries/tools.py` | `tool_libraries` |
| `handlers/manufacture/tool_libraries/search.py` | `tool_search` |

## Data Models

### Updated Endpoint Structure

```python
WorkspaceCategory.MANUFACTURE: {
    "setups": {
        "list": "/cam/setups",                              # GET
        "get": "/cam/setups/{setup_id}",                    # GET
        "create": "/cam/setups",                            # POST (same path, different method)
        "modify": "/cam/setups/{setup_id}",                 # PUT
        "delete": "/cam/setups/{setup_id}",                 # DELETE
        "duplicate": "/cam/setups/{setup_id}/duplicate",    # POST
        "sequence": "/cam/setups/{setup_id}/sequence"       # GET
    },
    "toolpaths": {
        "list": "/cam/toolpaths",                           # GET
        "list_with_heights": "/cam/toolpaths/with-heights", # GET
        "get": "/cam/toolpaths/{toolpath_id}",              # GET
        "parameters": "/cam/toolpaths/{toolpath_id}/parameters",  # GET
        "heights": "/cam/toolpaths/{toolpath_id}/heights",  # GET/PUT
        "passes": "/cam/toolpaths/{toolpath_id}/passes",    # GET/PUT
        "linking": "/cam/toolpaths/{toolpath_id}/linking"   # GET/PUT
    },
    "operations": {
        "tool": "/cam/operations/{operation_id}/tool",                    # GET/PUT
        "heights": "/cam/operations/{operation_id}/heights",              # GET
        "height_param": "/cam/operations/{operation_id}/heights/{parameter_name}",  # PUT
        "heights_validate": "/cam/operations/{operation_id}/heights/validate",      # POST
        "passes": "/cam/operations/{operation_id}/passes",                # GET
        "passes_validate": "/cam/operations/{operation_id}/passes/validate",        # POST
        "passes_optimize": "/cam/operations/{operation_id}/passes/optimize",        # POST
        "linking": "/cam/operations/{operation_id}/linking",              # GET
        "linking_validate": "/cam/operations/{operation_id}/linking/validate"       # POST
    },
    "tools": {
        "list": "/cam/tools",                               # GET
        "usage": "/cam/tools/{tool_id}/usage"               # GET
    },
    "tool_libraries": {
        "list": "/tool-libraries",                          # GET
        "get": "/tool-libraries/{library_id}",              # GET
        "load": "/tool-libraries/load",                     # POST
        "validate_access": "/tool-libraries/validate-access",  # GET
        "tools_list": "/tool-libraries/tools",              # GET
        "tools_create": "/tool-libraries/tools",            # POST
        "tool_get": "/tool-libraries/tools/{tool_id}",      # GET
        "tool_modify": "/tool-libraries/tools/{tool_id}",   # PUT
        "tool_delete": "/tool-libraries/tools/{tool_id}",   # DELETE
        "tool_duplicate": "/tool-libraries/tools/{tool_id}/duplicate",  # POST
        "tool_validate": "/tool-libraries/tools/validate"   # POST
    },
    "tool_search": {
        "search": "/tool-libraries/search",                 # GET/POST
        "advanced": "/tool-libraries/search/advanced",      # POST
        "suggestions": "/tool-libraries/search/suggestions" # GET
    }
}
```

### Placeholder Naming Convention

| Entity Type | Placeholder Name |
|-------------|------------------|
| Setup | `{setup_id}` |
| Toolpath | `{toolpath_id}` |
| Operation | `{operation_id}` |
| Tool | `{tool_id}` |
| Library | `{library_id}` |
| Parameter | `{parameter_name}` |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Config-Handler Endpoint Consistency

*For any* endpoint path defined in the ConfigurationManager's `_endpoints` dictionary for the MANUFACTURE workspace, there SHALL exist a corresponding `register_handler()` call in the handler modules with a matching path pattern.

**Validates: Requirements 1.1, 1.2**

### Property 2: Placeholder Naming Consistency

*For any* endpoint path containing a placeholder (pattern `{...}`), the placeholder name SHALL match the entity type convention: `{setup_id}` for setups, `{toolpath_id}` for toolpaths, `{operation_id}` for operations, `{tool_id}` for tools, `{library_id}` for libraries.

**Validates: Requirements 1.3**

### Property 3: Validation Detection Completeness

*For any* configuration with an endpoint path that does not match the expected pattern (e.g., singular vs plural, wrong placeholder name), the `validate_config_detailed()` method SHALL include that path in the validation errors or warnings.

**Validates: Requirements 8.1, 8.2**

### Property 4: Validation Guidance Provision

*For any* validation error or warning detected by `validate_config_detailed()`, the result SHALL include a non-empty resolution guidance string that describes how to fix the issue.

**Validates: Requirements 8.3**

## Error Handling

### Configuration Validation Errors

The `validate_config_detailed()` method will be enhanced to detect:

1. **Path Pattern Errors**: Endpoints using incorrect patterns (e.g., `/cam/toolpath/` instead of `/cam/toolpaths/`)
2. **Placeholder Inconsistencies**: Endpoints using non-standard placeholder names (e.g., `{id}` instead of `{setup_id}`)
3. **Missing Endpoints**: Endpoints defined in handlers but not in config (warning level)
4. **Obsolete Endpoints**: Endpoints in config that don't have corresponding handlers (warning level)

### Error Response Format

```python
{
    'valid': bool,
    'errors': [str],           # Critical issues
    'warnings': [str],         # Non-critical issues
    'conflicts': [str],        # Duplicate paths
    'resolution_guidance': [str]  # How to fix issues
}
```

## Testing Strategy

### Unit Testing

Unit tests will verify:
- Each endpoint group contains expected paths
- Placeholder naming follows conventions
- Obsolete endpoints are removed
- New endpoints are present

### Property-Based Testing

Property-based tests using `hypothesis` will verify:
- Config-handler consistency across all endpoints
- Placeholder naming consistency
- Validation detection completeness
- Guidance provision for all detected issues

**Property Testing Configuration:**
- Minimum 100 iterations per property test
- Tests tagged with `**Feature: config-endpoint-sync, Property {number}: {property_text}**`

### Test File Location

Tests will be added to `FusionMCPBridge/tests/test_core_config.py`

## Steering File Design

A new steering file `.kiro/steering/config-endpoint-sync.md` will be created with:

### Content Structure

1. **Purpose**: Prevent configuration drift between config.py and handler registrations
2. **When to Update Config**: Triggers for config.py updates
3. **Handler-to-Config Mapping**: Reference table
4. **Code Review Checklist**: Verification steps
5. **Placeholder Conventions**: Naming standards

### Trigger Conditions

The steering file will specify that config.py must be updated when:
- A new `register_handler()` call is added
- An existing handler's path is modified
- A handler is removed or deprecated
- A new handler module is created

### Code Review Checklist

```markdown
- [ ] New handlers have corresponding config.py entries
- [ ] Modified handler paths are reflected in config.py
- [ ] Removed handlers have config.py entries removed
- [ ] Placeholder names follow conventions
- [ ] Endpoint paths use correct patterns (plural forms)
```
