import requests
from mcp.server.fastmcp import FastMCP
import json
mcp = FastMCP("Fusion")


@mcp.tool()
def draw_witzenmannlogo():
    r = requests.post("http://localhost:5000/Witzenmann")
    data = r.json()
    return data

@mcp.tool()
def undo():
    r = requests.post("http://localhost:5000/undo")

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
def export_STEP():
    r = requests.post("http://localhost:5000/Export_STEP")

    data = r.json()
    return data

@mcp.tool()
def export_STL():
    r = requests.post("http://localhost:5000/Export_STL")

    data = r.json()
    return data

@mcp.tool()
def fillet_edges(radius: str):
    url = "http://localhost:5000/fillet_edges"
    data = {
        "radius": radius
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()
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
def draw_cylinder(radius: float = 5.0, height: float = 10.0, x: float = 0.0, y: float = 0.0):
    """
    Zeichne ienen Zylinder, du kannst du in der XY Ebende arbeiten
    Es gibt Standartwerte
    """
    r = requests.post("http://localhost:5000/draw_cylinder")
    data = {
        "radius": radius,
        "height": height,
        "x": x,
        "y": y


    }
    return data
@mcp.tool()
def draw_box(height_value:str, width_value:str, depth_value:str, x_value:float, y_value:float):
    """
    Du kannst die Höhe, Breite und Tiefe der Box als Strings übergeben.
    Du kannst die Koordinaten x, y der Box als Strings übergeben.Gib immer Koordinaten an
    Depth ist die Tiefe in z Richtung
    """
    url = "http://localhost:5000/Box"

    data = {
        "height":height_value,
        "width": width_value,
        "depth": depth_value,
        "x" : x_value,
        "y" : y_value,

    }

    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    return response.json()

@mcp.tool()
def shell_body(thickness: float, faceindex: int):
    """


    Du kannst die Dicke der Wand als Float übergeben
    Du kannst den Faceindex als Integer übergeben

    :param thickness:
    :param faceindex:
    :return:
    """
    url = "http://localhost:5000/shell_body"
    data = {
        "thickness": thickness,
        "faceindex": faceindex
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()

    return response.json()
@mcp.prompt()
def witzenmann():
    return "Rede deutsch! Baue das WITZENMANN Logo in Fusion 360 ein. Verwende dazu das Tool draw_witzenmannlogo."
@mcp.prompt()
def box():
    return "Rede deutsch!Frage den Benutzer nach Höhe, Breite und Tiefe und baue eine Box in Fusion 360 ein. Verwende dazu das Tool draw_box. Frage danach den User ob er das als STL Datei exportiert haben will."
@mcp.prompt()
def fillet():
    return "Rede deutsch! Frage den Benutzer nach dem Radius und verrunde alle Kanten der Box in Fusion 360. Verwende dazu das Tool fillet_edges."

@mcp.prompt()
def summary():
    return "Du bist ein hilfreicher Assistent für Fusion 360. Liste jeden Parameter auf den du hast und sag was du kannst!"



if __name__ == "__main__":
    mcp.run()
