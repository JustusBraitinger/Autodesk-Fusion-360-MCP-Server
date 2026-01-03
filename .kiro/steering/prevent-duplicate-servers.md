# CRITICAL: Prevent Duplicate Server Architecture

## Problem Statement
This project suffered from a critical architectural issue where two separate MCP servers were developed in parallel:
- `/Server/MCP_Server.py` - Original working server
- `/src/fusion_mcp/server.py` - New server with advanced features

This caused confusion, wasted development time, and created maintenance nightmares.

## MANDATORY Rules to Prevent Recurrence

### 0. System Requirements
**RULE**: This project REQUIRES `uv` (Python package manager) for all operations.
**ENFORCEMENT**: 
- `uv` MUST be installed and available in system PATH
- All server execution MUST use `uv run` commands
- All dependency management MUST use `uv sync`
- All add-in installation MUST use `uv run install-fusion-plugin`
- Install: https://docs.astral.sh/uv/getting-started/installation/

### 1. Single Source of Truth
**RULE**: There SHALL be only ONE MCP server implementation in this project.
**LOCATION**: `/Server/MCP_Server.py`
**ENFORCEMENT**: Any new MCP server files outside `/Server/` directory MUST be rejected in code review.

### 2. Extension, Not Replacement
**RULE**: New functionality MUST be added to existing `/Server/MCP_Server.py`, not created in new files.
**PROCESS**: 
1. Identify new functionality needed
2. Add functions to existing `/Server/MCP_Server.py`
3. Update `/Server/config.py` with new endpoints
4. Test with existing server

### 3. Fusion 360 Add-in Consistency
**RULE**: The Fusion 360 add-in (`/FusionMCPBridge/`) MUST match the server endpoints.
**ENFORCEMENT**: 
- Every endpoint in `/Server/config.py` MUST have corresponding handler in `/FusionMCPBridge/FusionMCPBridge.py`
- Every endpoint in server MUST be tested with `curl http://localhost:5001/endpoint`

### 4. Configuration Synchronization
**RULE**: These files MUST stay synchronized:
- `/Server/config.py` - Server-side endpoint definitions
- `/FusionMCPBridge/config.py` - Add-in endpoint definitions (if used)
- `/pyproject.toml` - Must point to correct module paths

### 5. Development Workflow
**MANDATORY PROCESS**:
1. **Before adding new functionality**:
   - Check if `/Server/MCP_Server.py` can be extended
   - Never create new server files
2. **When adding endpoints**:
   - Add to `/Server/config.py`
   - Add handler to `/FusionMCPBridge/FusionMCPBridge.py`
   - Test both server and add-in
3. **When modifying imports**:
   - Use relative imports in add-in: `from .module import function`
   - Test import syntax outside Fusion 360 where possible

### 6. Testing Requirements
**MANDATORY TESTS** before considering work complete:
1. **Server Test**: `cd Server && python3 MCP_Server.py --server_type sse`
2. **Add-in Test**: `curl http://localhost:5001/new-endpoint`
3. **Agent Test**: Use Kiro CLI agent to call new functions
4. **Integration Test**: Full MCP Server → Fusion 360 Add-in → Fusion 360 API chain

### 7. File Structure Enforcement
**ALLOWED**:
```
/Server/
  ├── MCP_Server.py          # ONLY MCP server file
  ├── config.py              # Server configuration
  ├── cli.py                 # CLI utilities
  └── __init__.py            # Module init

/FusionMCPBridge/
  ├── FusionMCPBridge.py     # HTTP server and routing
  ├── tool_library.py        # Tool library functionality
  ├── config.py              # Add-in configuration
  └── handlers/
      ├── design/            # Design workspace handlers
      └── manufacture/       # MANUFACTURE workspace handlers (CAM)
```

**FORBIDDEN**:
- Any MCP server files outside `/Server/`
- Multiple server implementations
- Duplicate functionality across files

### 8. Code Review Checklist
Before merging ANY changes:
- [ ] Only one MCP server exists (`/Server/MCP_Server.py`)
- [ ] New endpoints added to both server and add-in
- [ ] All endpoints tested with curl
- [ ] Agent configuration updated if needed
- [ ] No duplicate functionality
- [ ] Imports use correct relative syntax
- [ ] pyproject.toml points to correct modules

### 9. Emergency Recovery Process
If duplicate servers are discovered:
1. **STOP** all development
2. **IDENTIFY** which server has the most complete functionality
3. **BACKPORT** missing functionality to the chosen server
4. **DELETE** the duplicate server files
5. **UPDATE** all configurations to point to single server
6. **TEST** entire system end-to-end

### 10. Documentation Requirements
**MANDATORY**: Every new endpoint MUST be documented with:
- Purpose and functionality
- Required Fusion 360 state (design open, workspace, etc.)
- Example request/response
- Error conditions
- Dependencies on other endpoints

## Violation Consequences
- **Code Review**: Automatic rejection of PRs violating these rules
- **Development**: Immediate halt of work to fix architectural issues
- **Documentation**: Update this file with any new lessons learned

## Success Metrics
- Only one MCP server file exists
- All endpoints work in both server and add-in
- Agent can successfully call all functions
- No 404 errors on implemented endpoints
- Clear separation of concerns between files

This document MUST be updated whenever architectural decisions are made.
