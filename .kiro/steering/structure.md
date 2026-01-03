# Project Structure

```
FusionMCP/
├── src/fusion_mcp/            # MCP Server package (new uv-based structure)
│   ├── __init__.py            # Package init with version
│   ├── server.py              # Main server - defines MCP tools and prompts
│   ├── cli.py                 # CLI entry points (install-fusion-plugin, start-mcp-server)
│   ├── config.py              # API endpoints and configuration
│   └── interceptor.py         # Response interceptor for debugging
│
├── Server/                    # Legacy MCP Server (kept for backward compatibility)
│   ├── MCP_Server.py          # Original server file
│   ├── config.py              # API endpoints and configuration
│   ├── interceptor.py         # Response interceptor
│   └── requirements.txt       # Python dependencies
│
├── FusionMCPBridge/           # Fusion 360 Add-In (runs inside Fusion)
│   ├── FusionMCPBridge.py     # Main add-in - HTTP server + geometry functions
│   ├── FusionMCPBridge.manifest # Fusion add-in manifest
│   ├── config.py              # Add-in configuration and endpoints
│   ├── cert.pem               # SSL certificate
│   ├── key.pem                # SSL key
│   └── AddInIcon.svg          # Add-in icon
│
├── pyproject.toml             # Project config, deps, entry points
├── uv.lock                    # Locked dependency versions
├── Install_Addin.py           # Legacy add-in installer script
├── Install_Addin_Fixed.py     # Fixed version of installer
├── Install_Addin_Symlink.py   # Symlink installer for development
└── README.md                  # Setup and usage documentation
```

## Key Files

### src/fusion_mcp/server.py
- Defines all MCP tools using `@mcp.tool()` decorator
- Each tool sends HTTP request to Fusion Add-In
- Contains detailed German instructions for AI behavior
- Can be run via `uv run start-mcp-server`

### src/fusion_mcp/cli.py
- `install_plugin()`: Installs FusionMCPBridge to Fusion add-ins directory
- `start_server()`: Starts the MCP server with SSE transport
- `get_fusion_addins_path()`: Platform-specific path resolution

### FusionMCPBridge/FusionMCPBridge.py
- `TaskEventHandler`: Processes queued tasks on Fusion's main thread
- Geometry functions: `draw_Box`, `draw_cylinder`, `extrude_last_sketch`, etc.
- HTTP request handler routes to appropriate geometry functions
- Uses task queue pattern (Fusion API is not thread-safe)

### Config Files
- `src/fusion_mcp/config.py`: Server-side endpoints
- `FusionMCPBridge/config.py`: Add-in configuration
Both define:
- `BASE_URL`: Fusion Add-In server address (http://localhost:5001)
- `ENDPOINTS`: Dictionary mapping operation names to URLs
- `HEADERS`: Standard HTTP headers

## Threading Model
Fusion 360 API requires main thread execution:
1. HTTP server receives request in background thread
2. Task added to `task_queue`
3. `TaskEventHandler` fires every 200ms via CustomEvent
4. Handler processes queue on main UI thread

## CLI Commands
```bash
uv sync                           # Install dependencies
uv run install-fusion-plugin      # Copy add-in to Fusion
uv run install-fusion-plugin --dev # Symlink for development
uv run start-mcp-server           # Start MCP server
uv run fastmcp install src/fusion_mcp/server.py --name Fusion  # Register with Claude
```
