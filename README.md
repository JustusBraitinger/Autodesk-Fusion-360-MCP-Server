# Fusion MCP Projekt https://github.com/user-attachments/assets/3c373629-e4f4-4531-adb0-3b57a1ad8f05 ## Voraussetzungen - Autodesk Fusion 360 - Claude Desktop (oder ein anderer MCP-kompatibler Client) Claude erst öffnen, wenn InstallAddin.py ausgeführt wurde bzw. das Addin manuell in Fusion hinzugefügt wurde! Falls schon offen Claude über den Task-Manager schließen ## Installation ### 1. Repository klonen
bash
git clone https://github.com/JustusBraitinger/FusionMCP.git
cd FusionMCP
### 2. Pakete installieren
pip install uv mcp fastmcp
      cd Server
      python -m pip install -r requirements.txt
### 3. Addin installieren Zur Zeit muss es in Fusion manuell hinzugefügt werden. Hierfür öffnet man Fusion und geht unter Utilities auf ADD-INS Jetzt auf das Plus drücken und "Script or add-in from device" auswählen. Den Ordner MCP aus dem Repo bzw. den Ordner auswählen und bestätigen ### 4. MCP Server starten
bash
uv run mcp install MCP_Server.py
MCP Server läuft lokal und kann in Claude genutzt werden. Um zu überprüfen ob der Server in Claude läuft gehe auf die Einstellung -> Entwickler. Da sollte der MCP Server TEST laufen! ### Architektur ## 1. Das Fusion Addin wird manuell unter Utilities -> Addin gestartet Das Addin startet einen HTTP Server und hostet ihn in einem Nebenthread, da der Fusion Hauptthread nicht benutzt werden darf
python
   threading.Thread(target=run_server, daemon=True).start() # Der erste Thread startet den HTTP Server im Hintergrund
### Zukünfitges ## 1. Witzenmann-Logo mit Prompt erstellen Vorgegebene Prompts definieren für Ausstellung im Digital Lab mach das auf englisch
