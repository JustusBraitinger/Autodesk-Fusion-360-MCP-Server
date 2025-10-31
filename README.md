# Fusion MCP Integration

## Motivation
This project demonstrates the potential of the MCP protocol when integrated with Autodesk Fusion 360.  
It shows how MCP can act as a bridge between AI-driven tools and Fusion's modeling environment, enabling:
- Automated geometry generation  
- Parameter control  
- Interactive workflows  

> **Goal:** Enable conversational CAD and AI-driven automation in Fusion.

---
# Quickstart with Claude 

```bash
git clone https://github.com/JustusBraitinger/FusionMCP
cd FusionMCP/Server
python -m venv venv
.\venv\Scripts\Activate   # or source venv/bin/activate
pip install -r requirements.txt
pip install "mcp[cli]"
cd FusionMCP
uv run mcp install MCP_Server.py
```

# More detailed Setup


## Demo
https://github.com/user-attachments/assets/da168905-8d8a-4537-a804-5b5e17c2ce26

---

## Requirements
| Requirement | Link |
|------------|------|
| Python 3.10+ | https://python.org |
| Autodesk Fusion 360 | https://autodesk.com/fusion360 |
| Claude Desktop | https://claude.ai/download |
| VS Code | https://code.visualstudio.com |

---

## Clone Repository
```bash
git clone https://github.com/JustusBraitinger/FusionMCP
cd FusionMCP
```

## Add Add-in to Fusion
1. Open Fusion 360
2. Go to **Utilities → Add-ins**
3. Click the **+** button
4. Select the **MCP** folder from this repository
5. **Do NOT start the add-in yet**

## Install Python Dependencies
```bash
cd Server
python -m venv venv
```

### Activate venv

**Windows PowerShell**
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source venv/bin/activate
```

### Install packages
```bash
pip install -r requirements.txt
pip install "mcp[cli]"
```

---

## Connect to Claude

### Modify Claude Config
In Claude Desktop go to:  
**Settings → Developer → Edit Config**

Add this block (change the path for your system):
```json
{
  "mcpServers": {
    "FusionMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Path\\to\\FusionMCP\\Server",
        "run",
        "MCP_Server.py"
      ]
    }
  }
}
```
> **Note:** Windows paths require double backslashes `\\`

**Alternative install command**
```bash
uv run mcp install MCP_Server.py
```

### Using the MCP in Claude
1. Restart Claude if needed (force close if not visible)
2. Click **➕ Add** (bottom left of chat)
3. Select **Add from Fusion**
4. Choose a Fusion MCP prompt

---

## Use MCP in VS Code (Copilot)

Create or edit the file:
```
%APPDATA%\Code\User\globalStorage\github.copilot-chat\mcp.json
```

Paste:
```json
{
  "servers": {
    "FusionMCP": {
      "url": "http://127.0.0.1:8000/sse",
      "type": "http"
    }
  },
  "inputs": []
}
```

### Alternative Setup in VS Code
1. Press **CTRL + SHIFT + P** → search **MCP** → choose:
2. **Add MCP**
3. **HTTP**
4. Enter:
5. Name your MCP **`FusionMCP`**!!
```
http://127.0.0.1:8000/sse
```

---

## Try It Out 😄

Start the server:
```bash
python MCP_Server.py
```

Then in VS Code, type:
```
/mcp.FusionMCP
```
Now you will see a list of predetermined Prompts.   

---

## Available Tools 🧰

| Tool | Description |
|------|-------------|
| Count parameters | Counts all model parameters |
| List parameters | Lists model parameters |
| Draw box | Create a box with H/W/L and position |
| Draw cylinder | Draws cylinder |
| Draw Witzenmann logo | Fun demo |
| Fillet edges | Fillet edges by radius |
| Shell body | Hollow body |
| Export | Export STL/STEP |
| Undo | Undo last operation |
| Draw lines | Polyline sketch |
| 3-Point Arc | Arc tool |
| Revolve | Revolves profile |
| Sweep | Circle + spline sweep |
| Thin extrusion | Thin wall extrusion |

---

## Architecture

### Server.py
- Defines MCP server, tools, and prompts
- Handles HTTP calls to Fusion add-in

### MCP.py
- Fusion Add-in
- Because the Fusion API is not thread-safe, this uses:
  - Custom event handler
  - Task queue

---

## Security Considerations 🔒
- Local execution → safe by default
- Currently HTTP (OK locally, insecure on networks)
- Validate tool inputs to avoid prompt injection
- Real security depends on tool implementation

---

## Disclaimer
Fusion API limitations:
- Not thread-safe
- Not designed for async MCP workflows
- Documentation outdated in places

**This is a proof-of-concept, not production software.**
