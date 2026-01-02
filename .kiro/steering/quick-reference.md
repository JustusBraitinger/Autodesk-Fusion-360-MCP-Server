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
- `/FusionMCPBridge/cam.py` - CAM functionality

### Agent Configuration
- `/.kiro/agents/fusion-360.json` - Kiro CLI agent config

## Common Issues & Solutions

### 404 Errors on Endpoints
1. Restart Fusion 360 add-in (Stop → Start in Scripts and Add-Ins)
2. Reinstall symlink: `uv run install-fusion-plugin --dev`
3. Check Text Commands panel in Fusion 360 for Python errors

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
