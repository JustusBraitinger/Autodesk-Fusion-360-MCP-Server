"""
CAD Features Tools

This module contains tools for creating features:
- fillet_edges: Create edge fillets
- draw_holes: Create holes in bodies
- shell_body: Create shell features
- circular_pattern: Create circular patterns
- rectangular_pattern: Create rectangular patterns
- create_thread: Create threaded features
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.request_handler import send_request
from core.config import get_endpoints, get_headers

def register_tools(mcp_instance: FastMCP):
    """Register feature tools with the MCP server."""
    # Register all tools in this module
    mcp_instance.tool()(fillet_edges)
    mcp_instance.tool()(draw_holes)
    mcp_instance.tool()(shell_body)
    mcp_instance.tool()(circular_pattern)
    mcp_instance.tool()(rectangular_pattern)
    mcp_instance.tool()(create_thread)
    mcp_instance.tool()(ellipsie)
    mcp_instance.tool()(draw_witzenmannlogo)

def fillet_edges(radius: str):
    """Erstellt eine Abrundung an den angegebenen Kanten."""
    try:
        endpoint = get_endpoints("cad")["fillet_edges"]
        payload = {
            "radius": radius
        }
        headers = get_headers()
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Fillet edges failed: %s", e)
        raise

def draw_holes(points: list, depth: float, width: float, faceindex: int = 0):
    """
    Zeichne Löcher in Fusion 360
    Übergebe die Json in richter Form
    Du muss die x und y koordinate angeben z = 0
    Das wird meistens aufgerufen wenn eine Bohrung in der Mitte eines Kreises sein soll
    Also wenn du ein zylinder baust musst du den Mittelpunkt des Zylinders angeben
    Übergebe zusätzlich die Tiefe und den Durchmesser der Bohrung
    Du machst im Moment  nur Counterbore holes
    Du brauchs den faceindex damit Fusion weiß auf welcher Fläche die Bohrung gemacht werden soll
    wenn du einen keris extrudierst ist die oberste Fläche meistens faceindex 1 untere fläche 2
    Die punkte müssen so sein, dass sie nicht außerhalb des Körpers liegen
    BSP:
    2,1mm tief = depth: 0.21
    Breite 10mm = diameter: 1.0
    {
    points : [[0,0,]],
    width : 1.0,
    depth : 0.21,
    faceindex : 0
    }
    """
    try:
        endpoint = get_endpoints("cad")["holes"]
        payload = {
            "points": points,
            "width": width,
            "depth": depth,
            "faceindex": faceindex
        }
        headers = get_headers()
        send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Draw holes failed: %s", e)
        raise

def shell_body(thickness: float, faceindex: int):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst den Faceindex als Integer übergeben
    WEnn du davor eine Box abgerundet hast muss die im klaren sein, dass du 20 neue Flächen hast.
    Die sind alle die kleinen abgerundeten
    Falls du eine Box davor die Ecken verrundet hast, 
    dann ist der Facinedex der großen Flächen mindestens 21
    Es kann immer nur der letzte Body geschält werde

    :param thickness:
    :param faceindex:
    :return:
    """
    try:
        headers = get_headers()
        endpoint = get_endpoints("cad")["shell_body"]
        data = {
            "thickness": thickness,
            "faceindex": faceindex
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Shell body failed: %s", e)

def circular_pattern(plane: str, quantity: float, axis: str):
    """
    Du kannst ein Circular Pattern (Kreismuster) erstellen um Objekte kreisförmig um eine Achse zu verteilen.
    Du übergibst die Anzahl der Kopien als Float, die Achse als String ("X", "Y" oder "Z") und die Ebene als String ("XY", "YZ" oder "XZ").

    Die Achse gibt an, um welche Achse rotiert wird.
    Die Ebene gibt an, in welcher Ebene das Muster verteilt wird.

    Beispiel: 
    - quantity: 6.0 erstellt 6 Kopien gleichmäßig um 360° verteilt
    - axis: "Z" rotiert um die Z-Achse
    - plane: "XY" verteilt die Objekte in der XY-Ebene

    Das Feature wird auf das zuletzt erstellte/ausgewählte Objekt angewendet.
    Typische Anwendungen: Schraubenlöcher in Kreisform, Zahnrad-Zähne, Lüftungsgitter, dekorative Muster.
    """
    try:
        headers = get_headers()
        endpoint = get_endpoints("cad")["circular_pattern"]
        data = {
            "plane": plane,
            "quantity": quantity,
            "axis": axis
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Circular pattern failed: %s", e)
        raise

def rectangular_pattern(plane: str, quantity_one: float, quantity_two: float, distance_one: float, distance_two: float, axis_one: str, axis_two: str):
    """
    Du kannst ein Rectangular Pattern (Rechteckmuster) erstellen um Objekte in einer rechteckigen Anordnung zu verteilen.
    Du musst zwei Mengen (quantity_one, quantity_two) als Float übergeben,
    zwei Abstände (distance_one, distance_two) als Float übergeben,
    Die beiden Richtungen sind die axen ( axis_one, axis_two) als String ("X", "Y" oder "Z") und die Ebene als String ("XY", "YZ" oder "XZ").
    Aus Gründen musst du distance immer mit einer 10 multiplizieren damit es in Fusion 360 stimmt.
    """
    try:
       
        headers = get_headers()
        endpoint = get_endpoints("cad")["rectangular_pattern"]
        data = {
            "plane": plane,
            "quantity_one": quantity_one,
            "quantity_two": quantity_two,
            "distance_one": distance_one,
            "distance_two": distance_two,
            "axis_one": axis_one,
            "axis_two": axis_two
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Rectangular pattern failed: %s", e)
        raise

def create_thread(inside: bool, allsizes: int):
    """Erstellt ein Gewinde in Fusion 360
    Im Moment wählt der User selber in Fusioibn 360 das Profil aus
    Du musst nur angeben ob es innen oder außen sein soll
    und die länge des Gewindes
    allsizes haben folgende werte :
           # allsizes :
        #'1/4', '5/16', '3/8', '7/16', '1/2', '5/8', '3/4', '7/8', '1', '1 1/8', '1 1/4',
        # '1 3/8', '1 1/2', '1 3/4', '2', '2 1/4', '2 1/2', '2 3/4', '3', '3 1/2', '4', '4 1/2', '5')
        # allsizes = int value from 1 to 22
    
    """
    try:
        endpoint = get_endpoints("cad")["threaded"]
        payload = {
            "inside": inside,
            "allsizes": allsizes,
     
        }
        headers = get_headers()
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Create thread failed: %s", e)
        raise

def ellipsie(x_center: float, y_center: float, z_center: float,
              x_major: float, y_major: float, z_major: float, x_through: float, y_through: float, z_through: float, plane: str):
    """Zeichne eine Ellipse in Fusion 360."""
    try:
        endpoint = get_endpoints("cad")["ellipsie"]
        headers = get_headers()
        data = {
            "x_center": x_center,
            "y_center": y_center,
            "z_center": z_center,
            "x_major": x_major,
            "y_major": y_major,
            "z_major": z_major,
            "x_through": x_through,
            "y_through": y_through,
            "z_through": z_through,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw ellipse failed: %s", e)
        raise

def draw_witzenmannlogo(scale: float = 1.0, z: float = 1.0):
    """
    Du baust das witzenmann logo
    Du kannst es skalieren
    es ist immer im Mittelpunkt
    Du kannst die Höhe angeben mit z

    :param scale:
    :param z:
    :return:
    """
    try:
        endpoint = get_endpoints("utility")["witzenmann"]
        payload = {
            "scale": scale,
            "z": z
        }
        headers = get_headers()
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Witzenmannlogo failed: %s", e)
        raise