"""
CAM Toolpath Tools

This module contains tools for toolpath management:
- list_cam_toolpaths: List all CAM toolpaths
- get_toolpath_details: Get detailed toolpath parameters
- list_toolpaths_with_heights: List toolpaths with height information
- analyze_toolpath_sequence: Analyze toolpath execution sequence
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.config import get_endpoints, get_timeout
from core import interceptor

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register toolpath tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(list_cam_toolpaths)
    mcp.tool()(get_toolpath_details)
    mcp.tool()(list_toolpaths_with_heights)
    mcp.tool()(analyze_toolpath_sequence)

def list_cam_toolpaths():
    """
    You can list all CAM toolpath operations in the current Fusion 360 document.
    
    This is typically the first tool you call when working with CAM data.
    Use this to discover what operations exist before inspecting specific toolpath parameters.
    
    Each toolpath includes: id, name, operation type, tool name, and validity status.
    Toolpaths are organized by their parent setup.
    
    IMPORTANT: If no CAM data exists in the document, you'll get an empty list with a message.
    
    Example response:
    {
        "setups": [
            {
                "id": "setup_001",
                "name": "Setup1",
                "toolpaths": [
                    {
                        "id": "op_001",
                        "name": "Adaptive1",
                        "type": "adaptive",
                        "tool_name": "6mm Flat Endmill",
                        "tool_id": "tool_001",
                        "is_valid": true
                    }
                ]
            }
        ],
        "total_count": 1,
        "message": null
    }
    
    Typical use cases: Getting an overview of machining operations, finding toolpath IDs for further inspection.
    """
    try:
        endpoint = get_endpoints("cam")["cam_toolpaths"]
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
    except requests.ConnectionError:
        return {
            "error": True,
            "message": "Cannot connect to Fusion 360. Ensure the add-in is running.",
            "code": "CONNECTION_ERROR"
        }
    except requests.Timeout:
        return {
            "error": True,
            "message": "Request to Fusion 360 timed out. The add-in may be busy.",
            "code": "TIMEOUT_ERROR"
        }
    except Exception as e:
        logging.error("List CAM toolpaths failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to list toolpaths: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def get_toolpath_details(toolpath_id: str):
    """
    You can get detailed parameters for a specific CAM toolpath operation.
    
    Use this after list_cam_toolpaths() to inspect the full parameters of a specific operation.
    You need the toolpath_id from the list_cam_toolpaths response.
    
    Returns feeds/speeds, geometry settings, heights, tool information, and tool settings.
    Each parameter includes: value, unit, type, constraints, and whether it's editable.
    
    IMPORTANT: The toolpath_id must match exactly what was returned by list_cam_toolpaths.
    If the toolpath doesn't exist, you'll get a TOOLPATH_NOT_FOUND error.
    
    Parameters returned include:
    - feeds_and_speeds: spindle_speed, cutting_feedrate, plunge_feedrate, ramp_feedrate
    - geometry: stepover, stepdown, tolerance, stock_to_leave
    - heights: clearance_height, retract_height, feed_height
    - tool_settings: Preset cutting parameters from the tool library (see below)
    
    Tool Settings Section:
    The response includes a tool_settings section with preset cutting parameters stored
    in the tool library. These are the manufacturer or user-defined defaults for the tool:
    - preset_spindle_speed: Default spindle speed in RPM (e.g., 10000)
    - surface_speed: Recommended surface speed in m/min (e.g., 200)
    - feed_per_tooth: Feed per tooth in mm (e.g., 0.05)
    - ramp_spindle_speed: Spindle speed for ramping moves in RPM (e.g., 8000)
    - plunge_spindle_speed: Spindle speed for plunge moves in RPM (e.g., 5000)
    - feed_per_revolution: Feed per revolution in mm/rev (e.g., 0.2)
    
    Example tool_settings in response:
    {
        "tool_settings": {
            "preset_spindle_speed": {"value": 10000, "unit": "rpm", "type": "numeric"},
            "surface_speed": {"value": 200, "unit": "m/min", "type": "numeric"},
            "feed_per_tooth": {"value": 0.05, "unit": "mm", "type": "numeric"},
            "ramp_spindle_speed": {"value": 8000, "unit": "rpm", "type": "numeric"},
            "plunge_spindle_speed": {"value": 5000, "unit": "rpm", "type": "numeric"},
            "feed_per_revolution": {"value": 0.2, "unit": "mm/rev", "type": "numeric"}
        }
    }
    
    Example request:
    {
        "toolpath_id": "op_001"
    }
    
    Typical use cases: Analyzing current machining parameters, comparing operation parameters
    against tool presets, preparing to suggest optimizations, checking if parameters are 
    editable before attempting modification.
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_toolpath']}/{toolpath_id}"
        response = requests.get(endpoint, timeout=get_timeout())
        return interceptor.intercept_response(endpoint, response, "GET")
    except requests.ConnectionError:
        return {
            "error": True,
            "message": "Cannot connect to Fusion 360. Ensure the add-in is running.",
            "code": "CONNECTION_ERROR"
        }
    except requests.Timeout:
        return {
            "error": True,
            "message": "Request to Fusion 360 timed out. The add-in may be busy.",
            "code": "TIMEOUT_ERROR"
        }
    except Exception as e:
        logging.error("Get toolpath details failed: %s", e)
        return {
            "error": True,
            "message": f"Failed to get toolpath details: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def list_toolpaths_with_heights():
    """
    Sie können alle CAM-Werkzeugbahnen mit ihren Höhenparametern in einem einzigen Aufruf auflisten.
    
    Dieses Tool kombiniert die Werkzeugbahn-Auflistung mit der Höhenparameter-Extraktion und bietet
    eine umfassende Übersicht über alle Bearbeitungsoperationen einschließlich kritischer Höheninformationen.
    
    Jede Werkzeugbahn enthält:
    - Grundlegende Informationen: ID, Name, Operationstyp, Werkzeugname, Gültigkeitsstatus
    - Höhenparameter: Freifahrhöhe, Rückzugshöhe, Anfahrhöhe, obere und untere Höhe
    - Parametermetadaten: Werte, Einheiten, Ausdrücke und Bearbeitbarkeit
    
    WICHTIG: Wenn keine CAM-Daten im Dokument vorhanden sind, erhalten Sie eine leere Liste mit einer Nachricht.
    Höhenparameter werden nur für Werkzeugbahnen zurückgegeben, die diese Parameter definiert haben.
    
    Beispielantwort:
    {
        "setups": [
            {
                "id": "setup_001",
                "name": "Setup1",
                "toolpaths": [
                    {
                        "id": "op_001",
                        "name": "Adaptive1",
                        "type": "adaptive",
                        "tool_name": "6mm Flat Endmill",
                        "tool_id": "tool_001",
                        "is_valid": true,
                        "heights": {
                            "clearance_height": {
                                "value": 25.0,
                                "unit": "mm",
                                "expression": "stockTop + 5mm",
                                "type": "numeric",
                                "editable": true
                            },
                            "retract_height": {
                                "value": 15.0,
                                "unit": "mm",
                                "expression": "stockTop",
                                "type": "numeric",
                                "editable": true
                            }
                        }
                    }
                ]
            }
        ],
        "total_count": 1,
        "message": null
    }
    
    Typische Anwendungsfälle: Vollständige Übersicht über Bearbeitungsoperationen mit Höheninformationen,
    Analyse von Sicherheitshöhen für Kollisionsvermeidung, Vorbereitung für Höhenoptimierungen.
    
    Requirements: 1.1, 1.4, 2.1
    """
    try:
        endpoint = get_endpoints("cam")["cam_toolpaths_heights"]
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
    except Exception as e:
        logging.error("List toolpaths with heights failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Auflisten der Werkzeugbahnen mit Höhen: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def analyze_toolpath_sequence(setup_id: str):
    """
    Sie können eine detaillierte Sequenzanalyse für alle Werkzeugbahnen in einem spezifischen CAM-Setup durchführen.
    
    Verwenden Sie dieses Tool nach list_cam_toolpaths(), um die Ausführungsreihenfolge und Abhängigkeiten 
    aller Werkzeugbahnen in einem Setup zu analysieren. Sie benötigen die setup_id aus der Antwort von list_cam_toolpaths.
    
    Gibt vollständige Sequenzanalyse zurück einschließlich:
    - Ausführungsreihenfolge: Vollständige Kette mit Ausführungsreihenfolge aller Operationen
    - Werkzeugwechsel: Identifikation von Werkzeugwechseln und deren Auswirkung auf die Bearbeitungszeit
    - Abhängigkeiten: Operationen die vor anderen abgeschlossen werden müssen
    - Optimierungsempfehlungen: Vorschläge zur Neuordnung oder Neugruppierung von Strategien
    - Zeitschätzungen: Geschätzte Bearbeitungszeiten und Effizienzmetriken
    
    Jede Operation enthält: Reihenfolge, Werkzeug-ID, geschätzte Zeit, Abhängigkeiten und Pass-Anzahl.
    
    WICHTIG: Die setup_id muss genau mit der von list_cam_toolpaths zurückgegebenen übereinstimmen.
    Wenn das Setup nicht existiert, erhalten Sie einen SETUP_NOT_FOUND-Fehler.
    Wenn das Setup keine Werkzeugbahnen enthält, wird eine leere Sequenz zurückgegeben.
    
    Beispielanfrage:
    {
        "setup_id": "setup_001"
    }
    
    Beispielantwort:
    {
        "setup_id": "setup_001",
        "setup_name": "Setup1",
        "total_toolpaths": 5,
        "execution_sequence": [
            {
                "order": 1,
                "toolpath_id": "op_001",
                "toolpath_name": "Adaptive Clearing",
                "tool_id": "tool_001",
                "tool_name": "6mm Flat Endmill",
                "estimated_time": "15:30",
                "dependencies": [],
                "pass_count": 1
            },
            {
                "order": 2,
                "toolpath_id": "op_002", 
                "toolpath_name": "Contour Finishing",
                "tool_id": "tool_002",
                "tool_name": "3mm Ball Endmill",
                "estimated_time": "8:45",
                "dependencies": ["op_001"],
                "pass_count": 2
            },
            {
                "order": 3,
                "toolpath_id": "op_003",
                "toolpath_name": "Drilling",
                "tool_id": "tool_003",
                "tool_name": "5mm Drill",
                "estimated_time": "2:15",
                "dependencies": [],
                "pass_count": 1
            }
        ],
        "tool_changes": [
            {
                "after_toolpath": "op_001",
                "from_tool": "tool_001",
                "to_tool": "tool_002",
                "change_time": "2:00"
            },
            {
                "after_toolpath": "op_002",
                "from_tool": "tool_002",
                "to_tool": "tool_003",
                "change_time": "1:30"
            }
        ],
        "optimization_recommendations": [
            {
                "type": "tool_change_reduction",
                "description": "Erwägen Sie die Neuordnung von Operationen zur Minimierung von Werkzeugwechseln",
                "potential_savings": "4:00",
                "suggested_order": ["op_001", "op_003", "op_002"]
            },
            {
                "type": "dependency_optimization",
                "description": "Operation op_003 kann parallel zu op_001 ausgeführt werden",
                "potential_savings": "2:15"
            }
        ],
        "total_estimated_time": "29:00",
        "total_tool_changes": 2,
        "efficiency_score": 0.85
    }
    
    Mögliche Fehler:
    - SETUP_NOT_FOUND: Die setup_id existiert nicht
    - CAM_NOT_AVAILABLE: Kein CAM-Arbeitsbereich oder keine CAM-Daten
    - CONNECTION_ERROR: Verbindung zu Fusion 360 fehlgeschlagen
    - EMPTY_SETUP: Setup enthält keine Werkzeugbahnen
    
    Typische Anwendungsfälle: Optimierung von Bearbeitungssequenzen, Analyse von Werkzeugwechseln,
    Identifikation von Abhängigkeiten, Zeitschätzung für Bearbeitungsprojekte.
    
    Requirements: 2.1, 2.2, 2.4, 3.4, 5.5
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_setup_sequence']}/{setup_id}/sequence"
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
                "message": f"Setup mit ID '{setup_id}' nicht gefunden.",
                "code": "SETUP_NOT_FOUND"
            }
        elif hasattr(e, 'response') and e.response is not None and e.response.status_code == 204:
            return {
                "error": True,
                "message": f"Setup '{setup_id}' enthält keine Werkzeugbahnen.",
                "code": "EMPTY_SETUP"
            }
        else:
            logging.error("Analyze toolpath sequence failed: %s", e)
            return {
                "error": True,
                "message": f"Fehler beim Analysieren der Werkzeugbahn-Sequenz: {str(e)}",
                "code": "UNKNOWN_ERROR"
            }
    except Exception as e:
        logging.error("Analyze toolpath sequence failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Analysieren der Werkzeugbahn-Sequenz: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }