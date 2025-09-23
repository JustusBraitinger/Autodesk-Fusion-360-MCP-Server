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


## How to use
Open Claude and go to the developer settings. Here should be your Test MCP Server  
If not close Claude completly with Task-Manager and reopen it.


Click on the Plus on the bottom left of the chat.  


Select "Add from Test"
Click on your desired prompt



## Available Tools

- **Count_parameters** : Just counts parameters
- **List_parametsers** : Lists all Modelparams
- **Draw_Box** : Draws a box with given dimensions (Height,Width,Lenth,x,y) => Only in XY currently
- **Draw_Witzenmann** : Draws the Witzenmann logo in 3D
- **Draw_Cylinder** : Draws a cylinder with given dimenstions, also only in XY currently
- **Fillet_Edges** : Fillet edges with a given radius
- **Export** : Export sketch as STEP or STL


## Claude Usage
After you run  
```bash
uv run mcp install MCP_Server.py
```
The MCP-Server should be visible in the developer Settings insider Claude Desktop  
Like in the video you can give Claude tasks.  
Predetermined prompts are also available via the plus icon on the bottom left.



 
