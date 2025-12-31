# Project Structure

```
FusionMCP/
├── Server/                    # MCP Server (runs standalone)
│   ├── MCP_Server.py          # Main server - defines MCP tools and prompts
│   ├── config.py              # API endpoints and configuration
│   └── requirements.txt       # Python dependencies
│
├── MCP/                       # Fusion 360 Add-In (runs inside Fusion)
│   ├── MCP.py                 # Main add-in - HTTP server + geometry functions
│   ├── config.py              # Add-in configuration and endpoints
│   ├── cam.py                 # CAM-specific functionality
│   ├── MCP.manifest           # Fusion add-in manifest
│   ├── commands/              # UI command implementations
│   │   ├── commandDialog/     # Dialog-based command example
│   │   ├── paletteSend/       # Palette communication
│   │   └── paletteShow/       # HTML palette display
│   └── lib/
│       └── fusionAddInUtils/  # Shared utilities (event handling, logging)
│
├── Install_Addin.py           # Add-in installer script
├── Install_Addin_Fixed.py     # Fixed version of installer
└── README.md                  # Setup and usage documentation
```

## Key Files

### Server/MCP_Server.py
- Defines all MCP tools using `@mcp.tool()` decorator
- Each tool sends HTTP request to Fusion Add-In
- Contains detailed German instructions for AI behavior

### MCP/MCP.py
- `TaskEventHandler`: Processes queued tasks on Fusion's main thread
- Geometry functions: `draw_Box`, `draw_cylinder`, `extrude_last_sketch`, etc.
- HTTP request handler routes to appropriate geometry functions
- Uses task queue pattern (Fusion API is not thread-safe)

### Config Files
Both `Server/config.py` and `MCP/config.py` define:
- `BASE_URL`: Fusion Add-In server address
- `ENDPOINTS`: Dictionary mapping operation names to URLs
- `HEADERS`: Standard HTTP headers

## Threading Model
Fusion 360 API requires main thread execution:
1. HTTP server receives request in background thread
2. Task added to `task_queue`
3. `TaskEventHandler` fires every 200ms via CustomEvent
4. Handler processes queue on main UI thread
