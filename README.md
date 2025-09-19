### Fusion MCP Integration


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


```bash
cd ..
```
## Add Addin to Fusion

To add the Addin to Fusion open Fusion go to Utilities select ADD-INS click the plus and select the MCP folder of this repository.


## How to use
Open Claude and go to the developer settings. Here should be your Test MCP Server  
If not close Claude completly with Task-Manager and reopen it.


Click on the Plus on the bottom left of the chat.  
Select "Add from Test"
Click on your desired prompt

 
