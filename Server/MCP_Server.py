import requests
from mcp.server.fastmcp import FastMCP
import json
mcp = FastMCP("Test")



@mcp.tool()
def count() :
    r = requests.get("http://localhost:5000/count_parameters")

    data = r.json()
    return data

@mcp.tool()
def list_parameters():
    r = requests.get("http://localhost:5000/list_parameters")

    data = r.json()
    return data

@mcp.tool()
def change_parameter(name: str, value: str):
    url = "http://localhost:5000/set_parameter"
    data = {
        "name": name,
        "value": value
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()

@mcp.tool()
def draw_box(height_value:str, width_value:str, depth_value:str):
    url = "http://localhost:5000/Box"

    data = {
        "height":height_value,
        "width": width_value,
        "depth": depth_value
    }

    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    return response.json()


@mcp.prompt()
def prompt():
    return "Du bist ein Assistent, der Parameter eines Systems verwaltet.Sprich den User immer mit Hans an bei jeder Antwort. Du kannst die Anzahl der Parameter abrufen, eine Liste aller Parameter anzeigen und die Werte einzelner Parameter ändern. Verwende die bereitgestellten Tools, um diese Aufgaben zu erfüllen."
