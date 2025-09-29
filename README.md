# Fusion MCP Integration


## Motivation

The motivation behind this project is to visualize the potential of the MCP protocol when it is used with Autodesk Fusion.  
It demonstrates how MCP can serve as a bridge between AI-driven tools and Fusion's modeling environment, enabling 
automated geometry generation, parameter control, and interactive workflows.










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
The InsatllAddin.py file currently does **not** work



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
- **Shell body** : Shells a body with given thickness and face index


## Possible extensions

- Make it possible to extrude, shell, revolve (Pretty hard to select the right body and side if many bodies are involved)
- For show I could implement cameramovement after a prompt
  




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
Because the Fusion API is not threadsafe we need to start two external threads:  

In the first one we start a thread for out HTTP-Server, with which one we are able to communicate with the MCP-Server (A websocket approach would maybe be better and more stable)

```python
# start HTTP-Server
threading.Thread(target=run_server, daemon=True).start()
```

In the second one we start the polling loop thread:
```python
threading.Thread(target=lambda: polling_loop(design, ui), daemon=True).start()
```

### Polling loop :

The polling loop checks the task queue and executes tasks in the main thread.  
```python
task = task_queue.get()
if task[0] == 'set_parameter':
  set_parameter(design, ui, task[1], task[2])
```







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

 
