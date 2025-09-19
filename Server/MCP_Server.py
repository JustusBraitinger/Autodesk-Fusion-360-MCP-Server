import requests
from mcp.server.fastmcp import FastMCP
import json
mcp = FastMCP("Test")


@mcp.tool()
def draw_witzenmannlogo():
    r = requests.post("http://localhost:5000/Witzenmann")
    data = r.json()
    return data


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


    return response.json()
@mcp.prompt()
def witzenmann():
    return "Rede deutsch! Baue das WITZENMANN Logo in Fusion 360 ein. Verwende dazu das Tool draw_witzenmannlogo."
@mcp.prompt()
def box():
    return "Rede deutsch!Frage den Benutzer nach Höhe, Breite und Tiefe und baue eine Box in Fusion 360 ein. Verwende dazu das Tool draw_box."


if __name__ == "__main__":
    mcp.run()
