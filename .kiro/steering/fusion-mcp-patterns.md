---
inclusion: always
---

# Fusion 360 MCP: Known Issues & Patterns

## Critical Architecture Rules

### Single Server Principle
- **ONLY** use `/Server/MCP_Server.py` as the MCP server
- **NEVER** create new server files in `/src/` or elsewhere
- Extend existing server, don't replace it

### Endpoint Synchronization
When adding endpoints, update BOTH:
1. `/Server/config.py` - Server-side definitions
2. `/FusionMCPBridge/FusionMCPBridge.py` - Add-in HTTP handlers

## Fusion 360 API Patterns

### Tool Object Access
```python
# CORRECT - Tool objects use .description, not .name
"name": tool.description if hasattr(tool, 'description') and tool.description else "Unnamed Tool"

# WRONG - Will cause AttributeError
"name": tool.name
```

### Import Syntax in Add-in
```python
# CORRECT - Relative imports required
from .tool_library import find_tool_by_id

# WRONG - Causes ModuleNotFoundError
from tool_library import find_tool_by_id
```

### Tool Library API Pattern
```python
# CORRECT - Use CAM Manager chain
camManager = adsk.cam.CAMManager.get()
libraryManager = camManager.libraryManager
toolLibraries = libraryManager.toolLibraries
url = adsk.core.URL.create('systemlibraryroot://Samples/Milling Tools (Metric).json')
toolLibrary = toolLibraries.toolLibraryAtURL(url)
```

## Agent Configuration

### Working MCP Server Config
```json
{
  "mcpServers": {
    "FusionMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/bsport/projects/fustion360-mcp/Autodesk-Fusion-360-MCP-Server",
        "run",
        "python3",
        "Server/MCP_Server.py",
        "--server_type",
        "stdio"
      ]
    }
  }
}
```

### Manual Server (Debugging)
```bash
cd Server && python3 MCP_Server.py --server_type sse
```
Config: `"url": "http://127.0.0.1:8000/sse", "type": "http"`

## Troubleshooting Checklist

### 404 Errors on Endpoints
1. Restart Fusion 360 add-in (Stop → Start)
2. Reinstall symlink: `uv run install-fusion-plugin --dev`
3. Check Text Commands panel for Python errors

### After Code Changes
1. Reinstall symlink: `uv run install-fusion-plugin --dev`
2. Restart add-in in Fusion 360
3. Test endpoint: `curl http://localhost:5001/endpoint`

### Tool Library Functions Require
- Active design document open
- CAM (MANUFACTURE) workspace active
- Valid file permissions on library JSON files

## Debug Commands
```bash
# Test add-in HTTP server
curl http://localhost:5001/test_connection
curl http://localhost:5001/cam/toolpaths
curl http://localhost:5001/tool-libraries

# Verify symlink
ls -la "/Users/bsport/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/FusionMCPBridge"
```

## Key Files Reference

| Purpose | File |
|---------|------|
| MCP Server | `/Server/MCP_Server.py` |
| Server Config | `/Server/config.py` |
| Add-in Main | `/FusionMCPBridge/FusionMCPBridge.py` |
| CAM Functions | `/FusionMCPBridge/cam.py` |
| Tool Libraries | `/FusionMCPBridge/tool_library.py` |
| Agent Config | `/.kiro/agents/fusion-360.json` |
