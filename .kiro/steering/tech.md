# Technology Stack

## Languages
- Python 3.10+

## Core Dependencies
- **fastmcp**: MCP server framework (v2.12.0)
- **uvicorn**: ASGI server for HTTP transport
- **requests**: HTTP client for Fusion communication
- **uv**: Python package manager (used for running MCP server)

## Fusion 360 APIs
- `adsk.core`: Core Fusion 360 API
- `adsk.fusion`: Modeling and design API
- `adsk.cam`: CAM/manufacturing API

## Communication
- MCP Server listens on SSE endpoint: `http://127.0.0.1:8000/sse`
- Fusion Add-In HTTP server: `http://localhost:5001`

## AI Integration
- Claude Desktop (native MCP support)
- VS Code Copilot (HTTP/SSE transport)

## Common Commands

### Setup (Modern - Recommended)
```bash
# Install all dependencies with uv
uv sync
```

### Install Fusion Add-In
```bash
# For development (symlink - changes reflect immediately)
uv run install-fusion-plugin --dev

# For distribution (copy files)
uv run install-fusion-plugin
```

### Run MCP Server
```bash
uv run start-mcp-server
```

### Register with Claude
```bash
uv run fastmcp install src/fusion_mcp/server.py --name Fusion
```

### Legacy Commands (still supported)
```bash
# Manual setup
cd Server
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Legacy installers
python Install_Addin.py
python Install_Addin_Symlink.py

# Run server directly
cd Server
python MCP_Server.py
```

## Unit Conversion (Critical)
Fusion 360 uses centimeters internally:
- 1 unit = 1 cm = 10 mm
- All mm values must be divided by 10
- Example: 28.3 mm → 2.83 units
