---
inclusion: fileMatch
fileMatchPattern: "FusionMCPBridge/**/*.py*
---

# Fusion 360 Add-In Modular Architecture Steering Guide

**Version:** 1.0  
**Last Updated:** January 3, 2025  
**Owner:** Bridge Modularization Team  
**Purpose:** Enforce modular architecture principles for the Fusion 360 Add-In (FusionMCPBridge) to prevent regression to monolithic code

## Overview

This steering file enforces modular architecture principles for the Fusion 360 Add-In (`FusionMCPBridge/`) to maintain clean separation of concerns, prevent monolithic code regression, and ensure long-term maintainability. All development must follow these guidelines to preserve the modular structure aligned with Fusion 360 workspace concepts.

## Core Architecture Principles

### 1. Single Responsibility Principle
- **RULE**: Each module must have one clear, well-defined purpose
- **ENFORCEMENT**: Modules exceeding 500 lines require decomposition review
- **VIOLATION**: Mixing unrelated functionality (e.g., geometry and CAM operations in same module)

### 2. Fusion 360 Workspace Alignment
- **RULE**: Module organization must align with Fusion 360 workspace concepts
- **STRUCTURE**: 
  - `handlers/design/` → Design workspace operations
  - `handlers/manufacture/` → MANUFACTURE workspace operations
  - `handlers/research/` → Experimental functionality
  - `handlers/system/` → System-level operations
- **ENFORCEMENT**: All new functionality must be categorized by Fusion 360 workspace

### 3. Dependency Direction
- **RULE**: Dependencies must flow in one direction: Handlers → Core → External Libraries
- **FORBIDDEN**: Handler modules depending on other handler modules
- **ALLOWED**: Handler modules depending on core modules
- **ENFORCEMENT**: Import analysis during code review

## Module Structure Requirements

### Core Module Standards (`core/`)

#### Required Core Modules
- `server.py` - HTTP server setup and lifecycle management
- `config.py` - Centralized configuration with category support
- `router.py` - HTTP request routing system
- `task_queue.py` - Centralized task queue for Fusion 360 API calls
- `loader.py` - Module discovery and loading system
- `error_handling.py` - Centralized error handling and logging
- `validation.py` - Request validation system

#### Core Module Rules
- **MAXIMUM SIZE**: 300 lines per core module
- **DEPENDENCIES**: Only standard Python libraries and Fusion 360 API
- **INTERFACES**: Must provide stable, well-documented interfaces
- **TESTING**: 100% unit test coverage required

### Handler Module Standards (`handlers/`)

#### Design Workspace Handlers (`handlers/design/`)
- `geometry.py` - Basic 3D shapes (box, cylinder, sphere)
- `sketching.py` - 2D drawing operations (lines, circles, arcs, splines)
- `modeling.py` - 3D operations (extrude, revolve, loft, sweep, boolean)
- `features.py` - Features (fillet, holes, patterns, threading)
- `utilities.py` - Design utilities (parameters, selection, export)

#### MANUFACTURE Workspace Handlers (`handlers/manufacture/`)
- `setups.py` - CAM setup management and configuration
- `operations/` - Operation-level functionality subdirectory
  - `toolpaths.py` - Toolpath listing, analysis, and management
  - `tools.py` - Tools assigned to operations
  - `heights.py` - Height parameter management
  - `passes.py` - Multi-pass configuration
  - `linking.py` - Linking parameter management
- `tool_libraries/` - Tool library management subdirectory
  - `libraries.py` - Library listing and management
  - `tools.py` - Tool CRUD operations
  - `search.py` - Tool search and filtering

#### Handler Module Rules
- **MAXIMUM SIZE**: 400 lines per handler module
- **NAMING**: Use Fusion 360 business terminology (see fusion-360-business-language.md)
- **INTERFACES**: Clear function signatures with type hints
- **ERROR HANDLING**: Use centralized error handling from core
- **TASK QUEUE**: Only for WRITE operations that modify the model (see Task Queue Rules below)

## Task Queue Rules (CRITICAL)

### When to Use task_queue
- **REQUIRED**: Operations that CREATE, MODIFY, or DELETE geometry
- **REQUIRED**: Operations that change model parameters
- **REQUIRED**: Any operation that modifies the Fusion 360 document state

### When NOT to Use task_queue
- **FORBIDDEN**: Read-only operations (listing, querying, getting parameters)
- **FORBIDDEN**: Operations that only read from the Fusion 360 API
- **REASON**: task_queue callback pattern doesn't work for HTTP handlers

### Correct Read-Only Handler Pattern
```python
def handle_get_data(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Read-only handler - call impl directly."""
    try:
        cam = get_cam_product()
        if cam:
            result = get_data_impl(cam, data.get("id"))
        else:
            result = {"error": True, "message": "No CAM data", "code": "NO_CAM_DATA"}
        return {"status": 200 if not result.get("error") else 500, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": str(e)}
```

### BROKEN Pattern (DO NOT USE for read-only handlers)
```python
# THIS PATTERN RETURNS EMPTY {} - DO NOT USE FOR READ-ONLY OPERATIONS
def handle_get_data(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    def execute():
        nonlocal result
        result = get_data_impl()  # Never executes properly!
    task_queue.queue_task("get_data", callback=execute)
    task_queue.process_tasks()
    return {"data": result}  # Returns empty {}
```

### Why the Broken Pattern Fails
1. HTTP handlers run in background threads
2. task_queue is designed for CustomEvent main-thread execution
3. The callback with `nonlocal result` doesn't execute synchronously
4. Read-only Fusion 360 API calls are thread-safe and don't need task_queue

## Module Decomposition Guidelines

### When to Decompose a Module

#### Size Thresholds
- **WARNING**: Module exceeds 300 lines (core) or 400 lines (handler)
- **MANDATORY**: Module exceeds 500 lines
- **IMMEDIATE**: Module exceeds 750 lines

#### Complexity Indicators
- More than 10 public functions
- More than 5 distinct responsibilities
- Cyclomatic complexity > 15 per function
- Multiple unrelated import groups

#### Functional Indicators
- Mixed workspace operations (Design + MANUFACTURE)
- Multiple API categories (geometry + CAM + system)
- Unrelated error handling patterns

### Decomposition Process

#### 1. Identify Boundaries
- Group related functions by Fusion 360 workspace
- Separate by API category (geometry, CAM, system)
- Identify shared utilities for extraction

#### 2. Create New Modules
- Follow existing naming conventions
- Maintain directory structure alignment
- Update module loader registration

#### 3. Extract Shared Code
- Move common utilities to appropriate core modules
- Create shared interfaces for cross-module communication
- Maintain backward compatibility

#### 4. Update Dependencies
- Update import statements
- Verify dependency direction compliance
- Test module isolation

## Code Review Checklist

### Architecture Compliance

#### Module Organization
- [ ] New code placed in appropriate workspace-aligned directory
- [ ] Module size within acceptable limits (≤400 lines for handlers, ≤300 for core)
- [ ] Single responsibility principle maintained
- [ ] No mixing of unrelated functionality

#### Dependencies
- [ ] Dependencies flow in correct direction (Handlers → Core → External)
- [ ] No handler-to-handler dependencies
- [ ] Core modules have minimal external dependencies
- [ ] All Fusion 360 API calls use centralized task queue

#### Naming and Terminology
- [ ] Uses official Fusion 360 business terminology
- [ ] Consistent with fusion-360-business-language.md steering file
- [ ] Clear, descriptive function and variable names
- [ ] Follows established naming patterns

#### Error Handling
- [ ] Uses centralized error handling from core.error_handling
- [ ] Consistent error response formats
- [ ] Proper error isolation between modules
- [ ] Module context included in error messages

#### Testing
- [ ] Unit tests for new functionality
- [ ] Property-based tests for universal properties
- [ ] Module isolation verified
- [ ] Backward compatibility maintained

### Interface Design
- [ ] Clear function signatures with type hints
- [ ] Well-documented public interfaces
- [ ] Stable API contracts maintained
- [ ] Proper separation of public and private functions

## Architectural Violation Detection

### Automated Checks

#### Import Analysis
```python
# VIOLATION: Handler importing another handler
from handlers.design.geometry import create_box  # ❌ FORBIDDEN

# CORRECT: Handler importing from core
from core.task_queue import queue_task  # ✅ ALLOWED
```

#### Size Monitoring
- Monitor module line counts during CI/CD
- Flag modules approaching size thresholds
- Require decomposition plan for oversized modules

#### Dependency Validation
- Analyze import statements for circular dependencies
- Verify dependency direction compliance
- Check for unauthorized cross-handler dependencies

### Manual Review Points

#### Architecture Review
- New modules require architecture team approval
- Decomposition plans must be documented
- Cross-module interfaces require design review

#### Code Quality Gates
- No merge without architecture compliance
- Size threshold violations block deployment
- Dependency violations require immediate remediation

## Remediation Guidance

### Common Violations and Fixes

#### Violation: Oversized Module
**Detection**: Module exceeds size thresholds
**Remediation**:
1. Identify functional boundaries within module
2. Create new modules following workspace alignment
3. Extract shared utilities to core modules
4. Update imports and test thoroughly

#### Violation: Cross-Handler Dependencies
**Detection**: Handler module importing from another handler
**Remediation**:
1. Extract shared functionality to core module
2. Create common interface in core
3. Update both handlers to use core interface
4. Verify module isolation maintained

#### Violation: Mixed Workspace Operations
**Detection**: Single module handling both Design and MANUFACTURE operations
**Remediation**:
1. Separate operations by workspace
2. Move Design operations to handlers/design/
3. Move MANUFACTURE operations to handlers/manufacture/
4. Create core interfaces for shared functionality

#### Violation: Monolithic Request Handling
**Detection**: HTTP request handling mixed with business logic
**Remediation**:
1. Extract business logic to appropriate handler modules
2. Keep only routing logic in request handlers
3. Use centralized router from core.router
4. Maintain consistent error response formats

### Emergency Procedures

#### Critical Architecture Violation
1. **STOP**: Halt all development on affected modules
2. **ASSESS**: Determine scope and impact of violation
3. **PLAN**: Create detailed remediation plan
4. **EXECUTE**: Implement fixes following proper review process
5. **VERIFY**: Ensure compliance before resuming development

#### Regression to Monolithic Code
1. **IDENTIFY**: Locate monolithic code patterns
2. **ISOLATE**: Prevent further monolithic additions
3. **DECOMPOSE**: Break down monolithic sections
4. **REFACTOR**: Apply modular architecture principles
5. **DOCUMENT**: Update steering file with lessons learned

## Maintenance and Evolution

### Regular Architecture Reviews

#### Monthly Reviews
- Module size monitoring
- Dependency analysis
- Architecture compliance assessment
- Performance impact evaluation

#### Quarterly Reviews
- Architecture principle updates
- Steering file revisions
- Tool and process improvements
- Training needs assessment

### Continuous Improvement

#### Metrics Tracking
- Module count and size distribution
- Dependency complexity metrics
- Code review compliance rates
- Architecture violation frequency

#### Process Refinement
- Update guidelines based on lessons learned
- Improve automated detection tools
- Enhance developer training materials
- Streamline remediation procedures

## Developer Guidelines

### Before Adding New Functionality

1. **IDENTIFY**: Determine appropriate module category
2. **CHECK**: Verify module size and complexity limits
3. **DESIGN**: Plan interfaces and dependencies
4. **REVIEW**: Get architecture approval for new modules

### During Development

1. **FOLLOW**: Use established patterns and conventions
2. **TEST**: Verify module isolation and boundaries
3. **DOCUMENT**: Update interfaces and dependencies
4. **VALIDATE**: Check compliance with steering file

### Before Code Review

1. **VERIFY**: Run automated architecture checks
2. **CONFIRM**: All guidelines followed
3. **PREPARE**: Document any architectural decisions
4. **TEST**: Ensure backward compatibility maintained

## Success Metrics

### Architecture Health
- **Module Count**: Stable or growing appropriately
- **Average Module Size**: Within acceptable limits
- **Dependency Complexity**: Low and well-structured
- **Architecture Violations**: Trending toward zero

### Development Velocity
- **Feature Addition Time**: Consistent or improving
- **Bug Fix Time**: Reduced due to better isolation
- **Code Review Time**: Efficient due to clear guidelines
- **Onboarding Time**: Reduced for new developers

### System Quality
- **Maintainability**: High due to modular structure
- **Testability**: Improved through module isolation
- **Reliability**: Enhanced through proper error handling
- **Performance**: Maintained or improved

## References

- [Fusion 360 Business Language](./fusion-360-business-language.md)
- [Bridge Modularization Requirements](./../specs/bridge-modularization/requirements.md)
- [Bridge Modularization Design](./../specs/bridge-modularization/design.md)
- [Python Testing Guidelines](./python-testing.md)

## Change Log

- **v1.0** (January 3, 2025): Initial creation with comprehensive modular architecture guidelines for Fusion 360 Add-In - Bridge Modularization Team

---

**CRITICAL**: This steering file must be consulted for ALL changes to the Fusion 360 Add-In codebase. Violations will result in immediate code review rejection and required remediation before merge approval.