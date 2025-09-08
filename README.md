# Fusion MCP Projekt

## Voraussetzungen

- Autodesk Fusion 360
- MCP-CLI (`uv`)
- Claude Desktop (oder ein anderer MCP-kompatibler Client)



## Installation

### 1. Repository klonen

```bash
git clone https://github.com/JustusBraitinger/FusionMCP.git
cd FusionMCP
```
### 2. Pakete installieren

   ```pip install uv mcp fastmcp
      cd mcp_server
      python -m pip install -r requirements.txt

```
### 3. Addin installieren
```bash
python Install.Addin.py
```
### 4. MCP Server starten
```bash
uv run mcp install MCP_Server.py

```
MCP Server läuft lokal und kann in Claude genutzt werden.
