import requests
from mcp.server.fastmcp import FastMCP
import json
mcp = FastMCP("Fusion")


@mcp.tool()
def draw_witzenmannlogo(scale : float=1.0):

    data = {
        "scale": scale
    }

    url = "http://localhost:5000/Witzenmann"
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    data = response.json()
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
def draw_cylinder(radius: float , height: float , x: float, y: float , z: float , plane: str="XY"):
    """
    Zeichne einen Zylinder, du kannst du in der XY Ebende arbeiten
    Es gibt Standartwerte
    """
    url ="http://localhost:5000/draw_cylinder"
    data = {
        "radius": radius,
        "height": height,
        "x": x,
        "y": y,
        "z": z,
        "plane": plane
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    data = response.json()
    return data
@mcp.tool()
def draw_box(height_value:str, width_value:str, depth_value:str, x_value:float, y_value:float, plane:str="XY"):
    """
    Du kannst die Höhe, Breite und Tiefe der Box als Strings übergeben.
    Depth ist die Tiefe in z Richtung also wenn gesagt wird die Box soll flach sein dann gibst du einen geringen Wert an!
    Du kannst die Koordinaten x, y der Box als Strings übergeben.Gib immer Koordinaten an, jene geben den Mittelpunkt der Box an.
    Depth ist die Tiefe in z Richtung
    Ganz wichtg 10 ist 100mm in Fusion 360
    Du kannst die Ebene als String übergeben

    Beispiel: "XY", "YZ", "XZ"
    """
    url = "http://localhost:5000/Box"

    data = {
        "height":height_value,
        "width": width_value,
        "depth": depth_value,
        "x" : x_value,
        "y" : y_value,
        "Plane": plane

    }

    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    return response.json()

@mcp.tool()
def shell_body(thickness: float, faceindex: int):
    """


    Du kannst die Dicke der Wand als Float übergeben
    Du kannst den Faceindex als Integer übergeben
    WEnn du davor eine Box abgerundet hast muss die im klaren sein, dass du 20 neue Flächen hast. Die sind alle die kleinen abgerundeten
    Falls du eine Box davor die Ecken verrundet hast, dann ist der Facinedex der großen Flächen mindestens 21
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


@mcp.tool()
def draw_lines(points : list, plane : str):
    """
    Zeichne Linien in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: [[0,0,0],[5,0,0],[5,5,5],[0,5,5],[0,0,0]]
    Es ist essenziell, dass du die Z-Koordinate angibst, auch wenn sie 0 ist
    Wenn nicht explizit danach gefragt ist mache es so, dass die Linien nach oben zeigen
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"
    """
    url = "http://localhost:5000/draw_lines"
    data = {
        "points": points,
        "plane": plane
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()

@mcp.tool()
def extrude(value : float):
    url = "http://localhost:5000/extrude_last_sketch"
    data = {
        "value": value
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()


@mcp.tool()
def revolve(angle : float):
    """
    Sobald du dieses tool aufrufst wird der nutzer gebeten in Fusion ein profile auszuwählen und dann eine Achse.
    Wir übergeben den Winkel als Float
    """
    url = "http://localhost:5000/revolve"
    data = {
        "angle": angle,

    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()

@mcp.tool()
def draw_arc(point1 : list, point2 : list, point3 : list, plane : str):
    """
    Zeichne einen Bogen in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: point1 = [0,0,0], point2 = [5,5,5], point3 = [10,0,0]
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"

    """
    url = "http://localhost:5000/arc"
    data = {
        "point1": point1,
        "point2": point2,
        "point3": point3,
        "plane": plane
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()
@mcp.tool()
def draw_one_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, plane: str="XY"):
    """
    Zeichne eine Linie in Fusion 360
    Du kannst die Koordinaten als Float übergeben
    Beispiel: x1 = 0.0, y1 = 0.0, z1 = 0.0, x2 = 10.0, y2 = 10.0, z2 = 10.0
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"
    """
    url = "http://localhost:5000/draw_one_line"
    data = {
        "x1": x1,
        "y1": y1,
        "z1": z1,
        "x2": x2,
        "y2": y2,
        "z2": z2,
        "plane": plane
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
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

@mcp.prompt()
def weingals():
    return "Nutze folgende Koordinaten für Linien : [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]], Rufe danach die revolve Funktion auf"


mcp.run()

