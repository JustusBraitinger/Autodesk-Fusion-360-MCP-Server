### Fusion MCP Integration



https://github.com/user-attachments/assets/b2256444-ed79-49fe-8141-86a6376f27c0


## Setup

Install Claude Desktop https://claude.ai/download  
Install Fusion

# Get Repository 
```bash
git clone https://github.com/JustusBraitinger/FusionMCP
```
# Install packages
```bash
cd FusionMCP
cd Server
pip install -r requirements.txt
pip install "mcp[cli]"
```
# Connect to Claude
```bash
uv run mcp install MCP_Server.py
```



## Add Addin to Fusion

To add the Addin to Fusion open Fusion go to Utilities select ADD-INS click the plus and select the MCP folder of this repository.



## Claude Usage
After you run  
```bash
uv run mcp install MCP_Server.py
```
The MCP-Server should be visible in the developer Settings insider Claude Desktop    
If not close Claude completly with Task-Manager and reopen it.   
Like in the video you can give Claude tasks.   
Click on the Plus on the bottom left of the chat.  
Select "Add from Fusion"
Click on your desired prompt




## Available Tools 🧰

- **Count_parameters** : Just counts parameters
- **List_parametsers** : Lists all Modelparams
- **Draw_Box** : Draws a box with given dimensions (Height,Width,Lenth,x,y) => Only in XY currently
- **Draw_Witzenmann** : Draws the Witzenmann logo in 3D
- **Draw_Cylinder** : Draws a cylinder with given dimenstions, also only in XY currently
- **Fillet_Edges** : Fillet edges with a given radius
- **Export** : Export sketch as STEP or STL



# Security Considerations 🔒

## Prompt Injection / Tool Poisoning
Prompt Injection or Tool Poisoning happens when someone deliberately manipulates an MCP tool by embedding malicious prompts into function names, descriptions, or error messages. This can cause the tool to execute unintended commands or reveal sensitive information.

## Rug-Pull
A Rug-Pull occurs when a tool or project initially appears legitimate and harmless. However, a later update from the developer can change its behavior, potentially allowing data to be accessed or files to be created without the user's consent. This issue originates from the developer, not from the protocol or platform itself.

## General Note
While the MCP protocol itself is relatively safe and does not inherently pose major security risks, the actual security of a tool depends heavily on how it is implemented and maintained. Developers must handle inputs carefully, validate all data, and implement proper access controls to prevent vulnerabilities.


 
