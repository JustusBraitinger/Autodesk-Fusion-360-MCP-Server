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

### Setup
```bash
# Create virtual environment
cd Server
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: .\venv\Scripts\Activate  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
pip install "mcp[cli]"
```

### Install Fusion Add-In
```bash
python Install_Addin.py
# or for fixed version:
python Install_Addin_Fixed.py
```

### Run MCP Server
```bash
cd Server
python MCP_Server.py
# or via uv:
uv run MCP_Server.py
```

### Register with Claude
```bash
cd Server
uv run mcp install MCP_Server.py
```

## Unit Conversion (Critical)
Fusion 360 uses centimeters internally:
- 1 unit = 1 cm = 10 mm
- All mm values must be divided by 10
- Example: 28.3 mm → 2.83 units
