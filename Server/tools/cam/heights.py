"""
CAM Height Parameter Tools

This module contains tools for height parameter management:
- get_toolpath_heights: Get toolpath height parameters
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.request_handler import send_request, send_get_request
from core.config import get_endpoints, get_headers, get_timeout
from core import interceptor

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register height parameter tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(get_toolpath_heights)

def get_toolpath_heights(toolpath_id: str):
    """
    Sie können detaillierte Höheninformationen für eine spezifische CAM-Werkzeugbahn abrufen.
    
    Verwenden Sie dieses Tool nach list_toolpaths_with_heights() oder list_cam_toolpaths(), um
    umfassende Höhenparameter für eine bestimmte Operation zu inspizieren.
    Sie benötigen die toolpath_id aus der Antwort von list_toolpaths_with_heights.
    
    Gibt vollständige Höhenparameter zurück einschließlich:
    - Freifahrhöhe (clearance_height): Sichere Fahrhöhe über allen Hindernissen
    - Rückzugshöhe (retract_height): Höhe für schnelle Positionierbewegungen
    - Anfahrhöhe (feed_height): Höhe, bei der die Vorschubgeschwindigkeit beginnt
    - Obere Höhe (top_height): Obere Materialgrenze für die Operation
    - Untere Höhe (bottom_height): Untere Materialgrenze für die Operation
    
    Jeder Parameter enthält: Wert, Einheit, Ausdruck, Typ, Bearbeitbarkeit und Beschränkungen.
    
    WICHTIG: Die toolpath_id muss genau mit der von list_toolpaths_with_heights zurückgegebenen übereinstimmen.
    Wenn die Werkzeugbahn nicht existiert, erhalten Sie einen TOOLPATH_NOT_FOUND-Fehler.
    
    Beispielanfrage:
    {
        "toolpath_id": "op_001"
    }
    
    Beispielantwort:
    {
        "toolpath_id": "op_001",
        "toolpath_name": "Adaptive1",
        "heights": {
            "clearance_height": {
                "value": 25.0,
                "unit": "mm",
                "expression": "stockTop + 5mm",
                "type": "numeric",
                "editable": true,
                "min_value": null,
                "max_value": null
            },
            "retract_height": {
                "value": 15.0,
                "unit": "mm",
                "expression": "stockTop",
                "type": "numeric",
                "editable": true,
                "min_value": null,
                "max_value": null
            },
            "feed_height": {
                "value": 2.0,
                "unit": "mm",
                "expression": "stockTop - 3mm",
                "type": "numeric",
                "editable": true,
                "min_value": null,
                "max_value": null
            },
            "top_height": {
                "value": 0.0,
                "unit": "mm",
                "expression": "stockTop",
                "type": "numeric",
                "editable": true,
                "min_value": null,
                "max_value": null
            },
            "bottom_height": {
                "value": -10.0,
                "unit": "mm",
                "expression": "stockTop - 10mm",
                "type": "numeric",
                "editable": true,
                "min_value": null,
                "max_value": null
            }
        }
    }
    
    Mögliche Fehler:
    - TOOLPATH_NOT_FOUND: Die toolpath_id existiert nicht
    - CAM_NOT_AVAILABLE: Kein CAM-Arbeitsbereich oder keine CAM-Daten
    - CONNECTION_ERROR: Verbindung zu Fusion 360 fehlgeschlagen
    
    Typische Anwendungsfälle: Detaillierte Analyse von Höhenparametern, Überprüfung von Sicherheitshöhen,
    Vorbereitung für Höhenmodifikationen, Kollisionsvermeidung.
    
    Requirements: 2.2, 3.1, 3.2, 3.3, 3.4
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_toolpath_heights']}/{toolpath_id}/heights"
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
    except requests.ConnectionError:
        return {
            "error": True,
            "message": "Kann nicht mit Fusion 360 verbinden. Stellen Sie sicher, dass das Add-In läuft.",
            "code": "CONNECTION_ERROR"
        }
    except requests.Timeout:
        return {
            "error": True,
            "message": "Anfrage an Fusion 360 ist abgelaufen. Das Add-In könnte beschäftigt sein.",
            "code": "TIMEOUT_ERROR"
        }
    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
            return {
                "error": True,
                "message": f"Werkzeugbahn mit ID '{toolpath_id}' nicht gefunden.",
                "code": "TOOLPATH_NOT_FOUND"
            }
        else:
            logging.error("Get toolpath heights failed: %s", e)
            return {
                "error": True,
                "message": f"Fehler beim Abrufen der Werkzeugbahn-Höhen: {str(e)}",
                "code": "UNKNOWN_ERROR"
            }
    except Exception as e:
        logging.error("Get toolpath heights failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Abrufen der Werkzeugbahn-Höhen: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }