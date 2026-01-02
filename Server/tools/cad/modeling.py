"""
CAD Modeling Tools

This module contains tools for 3D modeling operations:
- extrude: Extrude sketches into 3D
- extrude_thin: Create thin-walled extrusions
- cut_extrude: Cut extrude operations
- revolve: Revolve sketches around axis
- loft: Loft between multiple sketches
- sweep: Sweep profile along path
- boolean_operation: Boolean operations between bodies
"""

import json
import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.request_handler import send_request
from core.config import get_endpoints, get_headers

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register modeling tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(extrude)
    mcp.tool()(extrude_thin)
    mcp.tool()(cut_extrude)
    mcp.tool()(revolve)
    mcp.tool()(loft)
    mcp.tool()(sweep)
    mcp.tool()(boolean_operation)
    mcp.tool()(draw_2d_rectangle)
    mcp.tool()(draw_text)

def extrude(value: float,angle:float):
    """Extrudiert die letzte Skizze um einen angegebenen Wert.
    Du kannst auch einen Winkel angeben
    
    """
    try:
        url = get_endpoints("cad")["extrude"]
        data = {
            "value": value,
            "taperangle": angle
        }
        data = json.dumps(data)
        headers = get_headers()
        response = requests.post(url, data, headers=headers)
        return response.json()
    except requests.RequestException as e:
        logging.error("Extrude failed: %s", e)
        raise

def extrude_thin(thickness :float, distance : float):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst schöne Hohlkörper damit erstellen
    :param thickness: Die Dicke der Wand in mm
    """
    try:
        headers = get_headers()
        endpoint = get_endpoints("cad")["extrude_thin"]
        data = {
            "thickness": thickness,
            "distance": distance
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Extrude thin failed: %s", e)
        raise

def cut_extrude(depth :float):
    """
    Du kannst die Tiefe des Schnitts als Float übergeben
    :param depth: Die Tiefe des Schnitts in mm
    depth muss negativ sein ganz wichtig!
    """
    try:
        headers = get_headers()
        endpoint = get_endpoints("cad")["cut_extrude"]
        data = {
            "depth": depth
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Cut extrude failed: %s", e)
        raise
    
def revolve(angle : float):
    """
    Sobald du dieses tool aufrufst wird der nutzer gebeten in Fusion ein profil
    auszuwählen und dann eine Achse.
    Wir übergeben den Winkel als Float
    """
    try:
        headers = get_headers()    
        endpoint = get_endpoints("cad")["revolve"]
        data = {
            "angle": angle

        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Revolve failed: %s", e)  
        raise

def loft(sketchcount: int):
    """
    Du kannst eine Loft Funktion in Fusion 360 erstellen
    Du übergibst die Anzahl der Sketches die du für die Loft benutzt hast als Integer
    Die Sketches müssen in der richtigen Reihenfolge erstellt worden sein
    Also zuerst Sketch 1 dann Sketch 2 dann Sketch 3 usw.
    """
    try:
        endpoint = get_endpoints("cad")["loft"]
        headers = get_headers()
        data = {
            "sketchcount": sketchcount
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Loft failed: %s", e)
        raise

def sweep():
    """
    Benutzt den vorhrig erstellten spline und den davor erstellten krei,
    um eine sweep funktion auszuführen
    """
    try:
        endpoint = get_endpoints("cad")["sweep"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Sweep failed: %s", e)
        raise

def boolean_operation(operation: str):
    """
    Führe eine boolesche Operation auf dem letzten Körper aus.
    Du kannst die Operation als String übergeben.
    Mögliche Werte sind: "cut", "join", "intersect"
    Wichtig ist, dass du vorher zwei Körper erstellt hast,
    """
    try:
        headers = get_headers()
        endpoint = get_endpoints("cad")["boolean_operation"]
        data = {
            "operation": operation
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Boolean operation failed: %s", e)
        raise

def draw_2d_rectangle(x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, plane: str):
    """
    Zeichne ein 2D-Rechteck in Fusion 360 für loft /Sweep etc.
    """
    try:
        headers = get_headers()
        endpoint = get_endpoints("cad")["draw_2d_rectangle"]
        data = {
            "x_1": x_1,
            "y_1": y_1,
            "z_1": z_1,
            "x_2": x_2,
            "y_2": y_2,
            "z_2": z_2,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw 2D rectangle failed: %s", e)
        raise

def draw_text(text: str, plane: str, x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, thickness: float,value: float):
    """
    Zeichne einen Text in Fusion 360 der ist ein Sketch also kannst dz  ann extruden
    Mit value kannst du angeben wie weit du den text extrudieren willst
    """
    try:
        headers = get_headers()
        endpoint = get_endpoints("cad")["draw_text"]
        data = {
            "text": text,
            "plane": plane,
            "x_1": x_1,
            "y_1": y_1,
            "z_1": z_1,
            "x_2": x_2,
            "y_2": y_2,
            "z_2": z_2,
            "thickness": thickness,
            "extrusion_value": value
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw text failed: %s", e)
        raise