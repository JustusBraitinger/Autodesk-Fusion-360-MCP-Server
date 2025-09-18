Fusion MCP Project

https://github.com/user-attachments/assets/3c373629-e4f4-4531-adb0-3b57a1ad8f05

Prerequisites

Autodesk Fusion 360

Claude Desktop (or any other MCP-compatible client)

Note: Open Claude only after InstallAddin.py has been executed or the add-in has been manually added in Fusion!
If Claude is already open, close it via Task Manager.

Installation
1. Clone the repository
git clone https://github.com/JustusBraitinger/FusionMCP.git
cd FusionMCP

2. Install packages
pip install uv mcp fastmcp
cd Server
python -m pip install -r requirements.txt

3. Install the add-in

Currently, it must be added manually in Fusion:

Open Fusion and go to Utilities → ADD-INS

Click the Plus (+) button and select "Script or add-in from device"

Choose the MCP folder from the repository (or its containing folder) and confirm

4. Start the MCP server
uv run mcp install MCP_Server.py


The MCP server runs locally and can be used in Claude.
To verify the server is running in Claude, go to Settings → Developer. You should see the MCP server TEST running.

Architecture
1. Fusion Add-in

The Fusion add-in is started manually under Utilities → Add-in.
The add-in launches an HTTP server in a separate thread because the Fusion main thread must not be blocked:

threading.Thread(target=run_server, daemon=True).start()  # Starts the HTTP server in the background
