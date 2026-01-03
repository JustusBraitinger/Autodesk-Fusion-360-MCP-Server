---
inclusion: fileMatch
fileMatchPattern: "FusionMCPBridge/**/*.py"
---

# Configuration Endpoint Synchronization Steering Guide

**Version:** 1.0  
**Last Updated:** January 3, 2026  
**Owner:** Config Endpoint Sync Team  
**Purpose:** Prevent configuration drift between `config.py` endpoint definitions and handler registrations

## Overview

This steering file enforces synchronization between the `FusionMCPBridge/core/config.py` endpoint definitions and the actual handler registrations across the modular architecture. Configuration drift leads to validation failures, documentation inconsistencies, and runtime errors. All development must follow these guidelines to maintain configuration accuracy.

## Scope

This steering file applies to:
- `FusionMCPBridge/core/config.py` - Centralized endpoint configuration
- `FusionMCPBridge/handlers/**/*.py` - All handler modules with `register_handler()` calls
- `FusionMCPBridge/core/router.py` - Request routing system

## Trigger Conditions for Config Updates

### MANDATORY: Update config.py When

1. **New Handler Registration**
   - WHEN a new `register_handler()` call is added to any handler module
   - THEN add corresponding endpoint to `config.py` in the appropriate category and group

2. **Handler Path Modification**
   - WHEN an existing handler's path is modified in `register_handler()`
   - THEN update the matching endpoint path in `config.py`

3. **Handler Removal**
   - WHEN a handler is removed or deprecated
   - THEN remove the corresponding endpoint from `config.py`

4. **New Handler Module Creation**
   - WHEN a new handler module is created in `handlers/`
   - THEN add a new endpoint group to `config.py` if needed

5. **Placeholder Changes**
   - WHEN a URL placeholder is renamed (e.g., `{id}` to `{setup_id}`)
   - THEN update all affected endpoints in `config.py`

## Handler-to-Config Mapping Table

| Handler Module | Config Category | Config Endpoint Group |
|----------------|-----------------|----------------------|
| `handlers/manufacture/setups.py` | `MANUFACTURE` | `setups` |
| `handlers/manufacture/operations/toolpaths.py` | `MANUFACTURE` | `toolpaths` |
| `handlers/manufacture/operations/heights.py` | `MANUFACTURE` | `operations` |
| `handlers/manufacture/operations/passes.py` | `MANUFACTURE` | `operations` |
| `handlers/manufacture/operations/linking.py` | `MANUFACTURE` | `operations` |
| `handlers/manufacture/operations/tools.py` | `MANUFACTURE` | `tools` |
| `handlers/manufacture/tool_libraries/libraries.py` | `MANUFACTURE` | `tool_libraries` |
| `handlers/manufacture/tool_libraries/tools.py` | `MANUFACTURE` | `tool_libraries` |
| `handlers/manufacture/tool_libraries/search.py` | `MANUFACTURE` | `tool_search` |
| `handlers/design/geometry.py` | `DESIGN` | `geometry` |
| `handlers/design/sketching.py` | `DESIGN` | `sketching` |
| `handlers/design/modeling.py` | `DESIGN` | `modeling` |
| `handlers/design/features.py` | `DESIGN` | `features` |
| `handlers/design/utilities.py` | `DESIGN` | `utilities` |
| `handlers/system/lifecycle.py` | `SYSTEM` | `lifecycle` |
| `handlers/system/utilities.py` | `SYSTEM` | `utilities` |
| `handlers/research/*.py` | `RESEARCH` | (varies) |

## Placeholder Naming Conventions

### Standard Placeholder Names

| Entity Type | Placeholder Name | Example Path |
|-------------|------------------|--------------|
| Setup | `{setup_id}` | `/cam/setups/{setup_id}` |
| Toolpath | `{toolpath_id}` | `/cam/toolpaths/{toolpath_id}` |
| Operation | `{operation_id}` | `/cam/operations/{operation_id}/tool` |
| Tool | `{tool_id}` | `/cam/tools/{tool_id}/usage` |
| Library | `{library_id}` | `/tool-libraries/{library_id}` |
| Parameter | `{parameter_name}` | `/cam/operations/{operation_id}/heights/{parameter_name}` |

### FORBIDDEN Placeholder Patterns

| Invalid Pattern | Correct Pattern | Reason |
|-----------------|-----------------|--------|
| `{id}` | `{setup_id}`, `{toolpath_id}`, etc. | Too generic, unclear entity type |
| `{setup}` | `{setup_id}` | Missing `_id` suffix |
| `{toolpath}` | `{toolpath_id}` | Missing `_id` suffix |
| `{operation}` | `{operation_id}` | Missing `_id` suffix |
| `{tool}` | `{tool_id}` | Missing `_id` suffix |
| `{library}` | `{library_id}` | Missing `_id` suffix |
| `{param}` | `{parameter_name}` | Non-standard abbreviation |
| `{name}` | `{parameter_name}` | Too generic |

## Endpoint Path Conventions

### Use Plural Forms for Collection Paths

| Incorrect (Singular) | Correct (Plural) |
|---------------------|------------------|
| `/cam/setup/` | `/cam/setups/` |
| `/cam/toolpath/` | `/cam/toolpaths/` |
| `/cam/operation/` | `/cam/operations/` |
| `/cam/tool/` | `/cam/tools/` |
| `/tool-library/` | `/tool-libraries/` |

### Path Structure Patterns

```
# Collection listing (GET)
/cam/setups

# Single resource (GET/PUT/DELETE)
/cam/setups/{setup_id}

# Resource action (POST)
/cam/setups/{setup_id}/duplicate

# Nested resource
/cam/operations/{operation_id}/heights/{parameter_name}
```

## Code Review Checklist

### Before Merging Handler Changes

- [ ] **New handlers have corresponding config.py entries**
  - Every `register_handler()` call has a matching endpoint in `config.py`
  - Endpoint is in the correct category and group

- [ ] **Modified handler paths are reflected in config.py**
  - Path changes in handlers are mirrored in config.py
  - No stale paths remain in config.py

- [ ] **Removed handlers have config.py entries removed**
  - Deprecated handlers have endpoints removed from config.py
  - No orphaned endpoints exist

- [ ] **Placeholder names follow conventions**
  - All placeholders use entity-specific names (`{setup_id}`, not `{id}`)
  - Placeholder names match the entity type being referenced

- [ ] **Endpoint paths use correct patterns**
  - Collection paths use plural forms (`/cam/setups`, not `/cam/setup`)
  - Resource paths follow RESTful conventions

- [ ] **Validation passes**
  - `ConfigurationManager.validate_config_detailed()` returns no errors
  - All warnings are addressed or documented

### Validation Command

Run this validation before committing changes:

```python
from FusionMCPBridge.core.config import config_manager

result = config_manager.validate_config_detailed()
if not result['valid']:
    print("ERRORS:", result['errors'])
    print("GUIDANCE:", result['resolution_guidance'])
if result['warnings']:
    print("WARNINGS:", result['warnings'])
```

## Common Violations and Fixes

### Violation: Missing Config Entry

**Detection**: Handler has `register_handler()` but no config.py entry
**Fix**:
1. Identify the handler's category (DESIGN, MANUFACTURE, SYSTEM, RESEARCH)
2. Identify or create the appropriate endpoint group
3. Add the endpoint with correct path and placeholder names

```python
# In config.py, add to appropriate category
"new_endpoint_group": {
    "action_name": "/path/to/{entity_id}/action"
}
```

### Violation: Stale Config Entry

**Detection**: Config.py has endpoint but handler was removed
**Fix**:
1. Remove the endpoint from config.py
2. Verify no other code references the removed endpoint
3. Update any documentation referencing the endpoint

### Violation: Path Mismatch

**Detection**: Handler path differs from config.py path
**Fix**:
1. Determine which path is correct (usually the handler)
2. Update config.py to match the handler path
3. Run validation to confirm fix

### Violation: Invalid Placeholder

**Detection**: Placeholder uses non-standard name
**Fix**:
1. Update handler to use standard placeholder name
2. Update config.py to match
3. Update any code that parses the placeholder

## Endpoint Structure Reference

### MANUFACTURE Workspace Endpoints

```python
WorkspaceCategory.MANUFACTURE: {
    "setups": {
        "list": "/cam/setups",                              # GET
        "get": "/cam/setups/{setup_id}",                    # GET
        "create": "/cam/setups",                            # POST
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

## Automated Validation

### Property-Based Tests

The following properties are tested automatically:

1. **Config-Handler Endpoint Consistency** (Property 1)
   - Every config.py endpoint has a matching handler registration

2. **Placeholder Naming Consistency** (Property 2)
   - All placeholders follow naming conventions

3. **Validation Detection Completeness** (Property 3)
   - `validate_config_detailed()` catches all pattern violations

4. **Validation Guidance Provision** (Property 4)
   - All validation issues include resolution guidance

### Running Validation Tests

```bash
# Run config validation tests
uv run pytest FusionMCPBridge/tests/test_core_config.py -v -k "property"
```

## Emergency Procedures

### Configuration Drift Detected

1. **STOP**: Halt development on affected handlers
2. **AUDIT**: Compare all handler registrations with config.py
3. **FIX**: Update config.py to match handlers
4. **VALIDATE**: Run `validate_config_detailed()` to confirm
5. **TEST**: Run property-based tests to verify consistency
6. **DOCUMENT**: Update this steering file if new patterns emerge

### Breaking Change Required

If a breaking change to endpoint paths is necessary:

1. **DOCUMENT**: Create migration guide for affected endpoints
2. **DEPRECATE**: Mark old endpoints as deprecated (don't remove immediately)
3. **ADD**: Add new endpoints with correct patterns
4. **MIGRATE**: Update all handler registrations
5. **REMOVE**: Remove deprecated endpoints after migration period
6. **VALIDATE**: Run full validation suite

## References

- [Config Endpoint Sync Requirements](../.kiro/specs/config-endpoint-sync/requirements.md)
- [Config Endpoint Sync Design](../.kiro/specs/config-endpoint-sync/design.md)
- [Fusion Bridge Modular Architecture](./fusion-bridge-modular-architecture.md)
- [Fusion 360 Business Language](./fusion-360-business-language.md)

## Change Log

- **v1.0** (January 3, 2026): Initial creation with comprehensive config synchronization guidelines - Config Endpoint Sync Team

---

**CRITICAL**: This steering file must be consulted for ALL changes to handler registrations or config.py endpoints. Violations will result in code review rejection and required remediation before merge approval.
