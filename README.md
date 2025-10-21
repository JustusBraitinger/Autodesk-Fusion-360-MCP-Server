# Fusion MCP Integration


## Motivation

The motivation behind this project is to visualize the potential of the MCP protocol when it is used with Autodesk Fusion.  
It demonstrates how MCP can serve as a bridge between AI-driven tools and Fusion's modeling environment, enabling 
automated geometry generation, parameter control, and interactive workflows.






https://github.com/user-attachments/assets/da168905-8d8a-4537-a804-5b5e17c2ce26






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

## Add Addin to Fusion

To add the Addin to Fusion open Fusion go to Utilities select ADD-INS click the plus and select the MCP folder of this repository.  
The InsatllAddin.py file currently does **not** work






# Connect to Claude

Go into the Claude Settings and click on developer   
Click edit Config   
Edit your JSON like below. Just change the Path to your path of the python script which runs your Server.
```bash

{
  "mcpServers": {
    "FusionMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users...Pathtopython
        "run",
        "MCP_Server.py"
      ]
    }
  }
}

```

Or run the command 
```bash
uv run mcp install MCP_Server.py
```
The output should be :
```bash
[10/21/25 07:40:09] INFO     Added server 'Fusion' to Claude config                                                                                                                                           
                    INFO     Successfully installed Fusion in Claude app     
```


The MCP-Server should be visible in the developer Settings insider Claude Desktop    
If not close Claude completly with Task-Manager and reopen it.   
Like in the video you can give Claude tasks.   
Click on the Plus on the bottom left of the chat.  
Select "Add from Fusion"
Click on your desired prompt

## Connect MCP inside VS-Code to Copilot

If you have a copilot license inside VS-Code you just have to copy this json into the **`mcp.json`**    
After that you just start the **`MCP_Server.py`** and you can use the mcp Server inside of Visual Studio Code
```bash
{
	"servers": {
		"FusionMCP": {
			"url": "http://127.0.0.1:8000/sse",
			"type": "http"
		},
		
	},
	"inputs": []
}
```





## Available Tools 🧰

- **Count_parameters** : Just counts parameters
- **List_parametsers** : Lists all Modelparams
- **Draw_Box** : Draws a box with given dimensions (Height,Width,Lenth,x,y)
- **Draw_Witzenmann** : Draws the Witzenmann logo in 3D
- **Draw_Cylinder** : Draws a cylinder with given dimenstions
- **Fillet_Edges** : Fillet edges with a given radius
- **Export** : Export sketch as STEP or STL
- **Shell body** : Shells a body with given thickness and face index
- **Undo Command** : Undos last change
- **Draw multiple lines** : Draws lines with given coordinates
- **3-Point-Arc** : Creates a 3-Point-Arc
- **Revolve** : Asks in Fusion for the body and the axis and revolves with given angle
- **Sweep** : Draws circle first, then spline, then sweeps
- **Thin-extrude** : Extrudes thin with given wall thickness



# Architecture

## Server.py

In this file we initialize the FastMCP Server and define tools and prompts.  
For example in the following tool we call the HTTP-Endpoint for counting every existing parameter in the current project.

```python
@mcp.tool()
def count() :
    r = requests.get("http://localhost:5000/count_parameters")
    data = r.json()
```

There are also predetermined prompts which you can define by @mcp.prompt(). In the following example it gives instructions how to interact with the user, if asked for a box.
```python
@mcp.prompt()
def box():
    return "Rede deutsch!Frage den Benutzer nach Höhe, Breite und Tiefe und baue eine Box in Fusion 360 ein. Verwende dazu das Tool draw_box. Frage danach den User ob er das als STL Datei exportiert haben will."
```

## MCP.py

This is the main addin.  
Because the Fusion API is not threadsafe we handle external requests with the CustomEventHandler
```python
class TaskEventHandler(adsk.core.CustomEventHandler):
```

We use a queue for processing the tasks
```python
    def process_task(self, task):
        global design, ui
        
        if task[0] == 'set_parameter':
            set_parameter(design, ui, task[1], task[2])```
```



I chose this architecture as PoC but a websocket approach would probably be better.   
It is extremly important that you never call Fusion API outside of the main thread!  







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




  
# Disclaimer

The current Fusion 360 API has several limitations when used with modern MCP operations:  
- It is relatively old and **not built for MCP-style workflows**.  
- The API is **not thread-safe**, which can lead to stability issues in asynchronous or parallel tasks.  
- The official documentation is limited and sometimes outdated, which makes development more challenging.  

This project is therefore an experimental prototype to explore what is possible, rather than a production-ready solution.

 # TODO 
IMPORTANT : Add functionality for selecting body, sketches, pfofiles 


### Future Tools :    
- Offsetplane   
- Thinextrude
- Anglextrude
- Sphere
- Sektchcircle Sketchrectangle

 
