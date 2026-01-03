# Quick Reference: Fusion 360 MCP Development

## Requirements
- Python 3.10+
- **uv (Python package manager)** - Required for dependency management and running the MCP server
- Autodesk Fusion 360
- Kiro CLI (for agent functionality)

**Critical**: `uv` must be installed and available in system PATH. The project uses `uv` for:
- Dependency management (`uv sync`)
- Running the MCP server (`uv run python3 Server/MCP_Server.py`)
- Installing the Fusion 360 add-in (`uv run install-fusion-plugin --dev`)

Install uv: https://docs.astral.sh/uv/getting-started/installation/

## Current Working Architecture
```
MCP Server (port 8000) → HTTP → Fusion 360 Add-in (port 5001) → Fusion 360 API
```

## Key Commands

### Start Manual Server (for debugging)
```bash
cd /Users/bsport/projects/fustion360-mcp/Autodesk-Fusion-360-MCP-Server/Server
python3 MCP_Server.py --server_type sse
```

### Install/Update Fusion 360 Add-in
```bash
cd /Users/bsport/projects/fustion360-mcp/Autodesk-Fusion-360-MCP-Server
uv run install-fusion-plugin --dev
```

### Test Endpoints
```bash
# Test add-in HTTP server
curl http://localhost:5001/test_connection
curl http://localhost:5001/cam/toolpaths
curl http://localhost:5001/tool-libraries

# Test MCP server (if running manually)
curl http://127.0.0.1:8000/sse
```

## Critical Files

### Server (MCP)
- `/Server/MCP_Server.py` - **ONLY** MCP server file
- `/Server/config.py` - Server endpoint configuration

### Fusion 360 Add-in
- `/FusionMCPBridge/FusionMCPBridge.py` - HTTP routing and handlers
- `/FusionMCPBridge/tool_library.py` - Tool library business logic
- `/FusionMCPBridge/handlers/manufacture/` - MANUFACTURE workspace handlers

### Agent Configuration
- `/.kiro/agents/fusion-360.json` - Kiro CLI agent config

## Common Issues & Solutions

### 404 Errors on Endpoints
1. Restart Fusion 360 add-in (Stop → Start in Scripts and Add-Ins)
2. Reinstall symlink: `uv run install-fusion-plugin --dev`
3. Check Text Commands panel in Fusion 360 for Python errors

### Handlers Return Empty `{}` Response
**Root Cause**: Handler using task_queue incorrectly for read-only operations.
**Solution**: Read-only CAM handlers should call `_impl` functions directly, NOT use task_queue.
See "Handler Implementation Rules" section below.

### Tool Object Attribute Errors
- Use `tool.description` instead of `tool.name`
- Always check `hasattr(tool, 'description')` before accessing

### Import Errors in Add-in
- Use relative imports: `from .module import function`
- Not absolute imports: `from module import function`

### Agent Connection Issues
- Ensure correct transport type in agent config
- For manual server: use HTTP transport with `http://127.0.0.1:8000/sse`
- For agent-managed: use stdio transport with uv command

### Restart Bridge Remotely
```bash
curl http://localhost:5002/addon/restart
```
Note: Bridge runs on port 5001, but restart endpoint is on port 5002.

## Fusion 360 Requirements
- Active design document must be open
- Must be in CAM (MANUFACTURE) workspace for tool library functions
- Add-in must show "Running" status in Scripts and Add-Ins panel

## Debug Process
1. **Test add-in**: `curl http://localhost:5001/endpoint`
2. **Check Fusion 360 Text Commands panel** for Python errors
3. **Verify symlink**: `ls -la "/Users/bsport/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/FusionMCPBridge"`
4. **Test MCP server**: Use Kiro CLI agent or manual server
5. **Check agent logs**: Look for MCP connection errors

## Working Endpoints
- ✅ `/cam/toolpaths` - List CAM toolpaths
- ✅ `/cam/tools` - List CAM tools  
- ✅ `/tool-libraries` - List tool libraries (requires CAM workspace)
- ✅ Basic CAD operations (draw, extrude, etc.)

## Emergency Reset
If system is broken:
1. Stop Fusion 360 add-in
2. `uv run install-fusion-plugin --dev`
3. Restart Fusion 360 add-in
4. Test basic endpoint: `curl http://localhost:5001/cam/toolpaths`
5. If still broken, restart Fusion 360 completely


## Handler Implementation Rules

### When to Use task_queue
- **USE task_queue**: For operations that MODIFY the Fusion 360 model (geometry creation, parameter changes)
- **DO NOT use task_queue**: For READ-ONLY operations (listing toolpaths, getting parameters, querying tools)

### Correct Pattern for Read-Only Handlers
```python
def handle_get_something(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Read-only handler - call impl directly, no task_queue."""
    try:
        param_id = data.get("param_id")
        if not param_id:
            return {"status": 400, "error": True, "message": "param_id required"}
        
        # CORRECT: Call impl function directly
        cam = get_cam_product()
        if cam:
            result = get_something_impl(cam, param_id)
        else:
            result = {"error": True, "message": "No CAM data", "code": "NO_CAM_DATA"}
        
        return {"status": 200 if not result.get("error") else 500, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": str(e)}
```

### WRONG Pattern (causes empty `{}` responses)
```python
def handle_get_something(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """BROKEN: task_queue callback pattern doesn't work for handlers."""
    result = {}
    
    def execute():
        nonlocal result
        result = get_something_impl()  # This never executes properly!
    
    # WRONG: task_queue.queue_task() doesn't execute the callback inline
    task_queue.queue_task("get_something", callback=execute)
    task_queue.process_tasks()  # This doesn't help either
    
    return {"data": result}  # Returns empty {}
```

### Why task_queue Doesn't Work for Handlers
1. task_queue is designed for the CustomEvent pattern (main thread execution)
2. HTTP handlers run in a background thread
3. The callback pattern with `nonlocal result` doesn't execute synchronously
4. Read-only Fusion 360 API calls are safe from any thread

### Modular Handler Checklist
- [ ] Handler imports only `request_router` from core (not task_queue for read-only)
- [ ] Handler calls `_impl` function directly
- [ ] Handler registered via `register_handlers()` at module load
- [ ] Parent `__init__.py` imports the handler module
