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


## Possible extensions

- Make it possible to extrude, shell, revolve (Pretty hard to select the right body and side if many bodies are involved)
- For show I could implement cameramovement after a prompt
  

# Security Considerations🔒

- **Prompt Injection / Tool Poisoning**  
  - Someone can manipulate the MCP tool on purpose.  
  - Malicious prompts can be put into function names, descriptions, or error messages.  
  - This can make the tool do things it shouldn't, like reveal data.

- **Rug-Pull**  
  - The tool looks safe at first.  
  - Later updates from the developer can change it.  
  - It might access your data or create files without permission.  
  - The risk comes from the developer, not the protocol.

- **General Note**  
  - The MCP protocol itself is mostly safe.  
  - The real security depends on how the tool is built and used.  
  - Developers should check inputs, validate data, and add access controls.
 

# Security Considerations in this Project
  - This project runs locally on your machine.
  - Currently, it uses plain HTTP for communication. This is fine for local use, but HTTP is unencrypted and could be insecure if exposed to a network.
  - Switching to HTTPS would make communication more secure and follow best practices.
  - Only trusted scripts and inputs should be used to avoid potential issues.



 
