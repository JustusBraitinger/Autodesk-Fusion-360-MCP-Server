# Fusion MCP Integration


https://github.com/user-attachments/assets/46c8140e-377d-4618-a304-03861cb3d7d9


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

**I highly recommend to do everything inside Visual Studio Code or an other IDE**

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
```
## Add Add-in to Fusion
1. Open Fusion 360
2. Go to **Utilities → Add-ins**
3. Click the **+** button
4. Select the **MCP** folder from this repository, you will probably find it under C:\Users\FusionMCMP
5. **Do NOT start the add-in yet**


## Install Python Dependencies
```bash
cd FusionMCP
cd Server
python -m venv venv
```

### Activate venv

**Windows PowerShell**
```powershell
.\venv\Scripts\Activate
```

### Install packages
```bash
pip install -r requirements.txt
pip install "mcp[cli]"
```

---

## Connect to Claude
The most simple way to add the MCP-Server to Claude Desktop is to run following command:  
```bash
uv run mcp install MCP_Server.py
```
The output should be like this:    

```bash
[11/13/25 08:42:37] INFO     Added server 'Fusion' to Claude config
                    INFO     Successfully installed Fusion in Claude app                                                                                                                                                               
```

# Alternative

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

## 🛠️ Available Tools

---

### ✏️ Sketching & Creation Tools

| Tool | Description |
| :--- | :--- |
| **Draw 2D circle** | Draws a 2D **circle** at a specified position and plane. |
| **Ellipsie** | Generates an **ellipse** (elliptical curve) in the sketching plane. |
| **Draw lines** | Creates a **polyline** (multiple connected lines) as a sketch. |
| **Draw one line** | Draws a single line between two 3D points. |
| **3-Point Arc** | Draws a **circular arc** based on three defined points. |
| **Spline** | Draws a **Spline curve** through a list of 3D points (used for sweep path). |
| **Draw box** | Creates a **box** (solid body) with definable dimensions and position. |
| **Draw cylinder** | Draws a **cylinder** (solid body). |
| **Draw Witzenmann logo** | A **fun demo function** for creating the Witzenmann logo. |

---

### ⚙️ Feature & Modification Tools

| Tool | Description |
| :--- | :--- |
| **Extrude** | **Extrudes** the last active sketch by a given value to create a body. |
| **Revolve** | Creates a revolved body by **revolving** a profile around an axis. |
| **Sweep** | Executes a sweep feature using the previously created profile and spline path. |
| **Loft** | Creates a complex body by **lofting** between a defined number of previously created sketches. |
| **Thin extrusion** | Creates a **thin-walled extrusion** (extrusion with constant wall thickness). |
| **Cut extrude** | Removes material from a body by **cutting** a sketch (as a hole/pocket). |
| **Draw holes** | Creates **Counterbore holes** at specified points on a surface (`faceindex`). |
| **Fillet edges** | Rounds sharp edges with a defined **radius** (fillet). |
| **Shell body** | **Hollows** out the body, leaving a uniform wall thickness. |
| **Circular pattern** | Creates a **circular pattern** (array) of features or bodies around an axis. |


---

### 📏 Analysis & Control

| Tool | Description |
| :--- | :--- |
| **Count** | Counts the total number of all **model parameters**. |
| **List parameters** | Lists all defined **model parameters** in detail. |
| **Change parameter** | Changes the value of an existing named parameter in the model. |
| **Test connection** | Tests the communication link to the Fusion 360 server. |
| **Undo** | **Undoes** the last operation in Fusion 360. |
| **Delete all** | **Deletes all objects** in the current Fusion 360 session (`destroy`). |

---

### 💾 Export

| Tool | Description |
| :--- | :--- |
| **Export STEP** | **Exports** the model as a **STEP** file. |
| **Export STL** | **Exports** the model as an **STL** file. |


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

## Contact
brju1032@h-ka.de
