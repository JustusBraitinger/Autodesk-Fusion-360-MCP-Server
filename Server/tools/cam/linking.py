"""
CAM Linking Parameter Tools

This module contains tools for linking parameter management:
- get_toolpath_linking: Get toolpath linking parameters
- modify_toolpath_linking: Modify toolpath linking configuration
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.request_handler import send_request
from core.config import get_endpoints, get_headers, get_timeout
from core import interceptor

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register linking parameter tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(get_toolpath_linking)
    mcp.tool()(modify_toolpath_linking)

def get_toolpath_linking(toolpath_id: str):
    """
    Sie können detaillierte Linking-Parameter für eine spezifische CAM-Werkzeugbahn abrufen.
    
    Verwenden Sie dieses Tool nach list_cam_toolpaths(), um operationsspezifische Linking-Parameter 
    für eine bestimmte Operation zu inspizieren. Sie benötigen die toolpath_id aus der Antwort von list_cam_toolpaths.
    
    Gibt vollständige Linking-Konfiguration zurück, organisiert nach Dialog-Abschnitten:
    - 2D Pocket Operationen: "Leads & Transitions" Abschnitt mit Lead-In/Lead-Out-Typ, Übergangstyp, Bogenradius
    - Trace Operationen: Operationsspezifische Abschnitte mit Kontaktpunkt, Anfahrt-/Rückzugsdistanzen, Übergänge
    - 3D Operationen: "Linking" Abschnitt mit Anfahrtstyp, Rückzugstyp, Freifahrthöhen
    - Editierbare Parameter: Identifikation welche Parameter für den jeweiligen Operationstyp verfügbar sind
    
    Jeder Parameter enthält: Wert, Einheit, Typ, Bearbeitbarkeit und operationsspezifische Beschränkungen.
    
    WICHTIG: Die toolpath_id muss genau mit der von list_cam_toolpaths zurückgegebenen übereinstimmen.
    Wenn die Werkzeugbahn nicht existiert, erhalten Sie einen TOOLPATH_NOT_FOUND-Fehler.
    Die Parameter werden genau so gruppiert, wie sie in Fusion 360's CAM-Interface erscheinen.
    
    Beispielanfrage:
    {
        "toolpath_id": "op_001"
    }
    
    Beispielantwort für 2D Pocket Operation:
    {
        "toolpath_id": "op_001",
        "toolpath_name": "2D Pocket1",
        "operation_type": "2d_pocket",
        "linking_configuration": {
            "sections": {
                "leads_and_transitions": {
                    "lead_in": {
                        "type": "arc",
                        "arc_radius": 2.0,
                        "arc_sweep": 90,
                        "vertical_lead_in": false,
                        "minimum_arc_radius": 0.1
                    },
                    "lead_out": {
                        "type": "arc", 
                        "arc_radius": 2.0,
                        "arc_sweep": 90,
                        "vertical_lead_out": false
                    },
                    "transitions": {
                        "type": "stay_down",
                        "lift_height": 1.0,
                        "order_by_depth": true,
                        "keep_tool_down": true
                    }
                },
                "entry_positioning": {
                    "clearance_height": 25.0,
                    "feed_height": 2.0,
                    "top_height": 0.0
                }
            },
            "editable_parameters": [
                "leads_and_transitions.lead_in.arc_radius",
                "leads_and_transitions.lead_out.arc_radius",
                "leads_and_transitions.transitions.type"
            ]
        }
    }
    
    Beispielantwort für 3D Operation:
    {
        "toolpath_id": "op_002",
        "toolpath_name": "3D Adaptive1",
        "operation_type": "3d_adaptive",
        "linking_configuration": {
            "sections": {
                "linking": {
                    "approach": {
                        "type": "perpendicular",
                        "distance": 5.0,
                        "angle": 0.0
                    },
                    "retract": {
                        "type": "perpendicular", 
                        "distance": 5.0,
                        "angle": 0.0
                    },
                    "clearance": {
                        "height": 25.0,
                        "type": "from_stock_top"
                    }
                },
                "transitions": {
                    "stay_down_distance": 2.0,
                    "lift_height": 1.0,
                    "order_optimization": "by_geometry"
                }
            },
            "editable_parameters": [
                "linking.approach.distance",
                "linking.retract.distance",
                "linking.clearance.height"
            ]
        }
    }
    
    Mögliche Fehler:
    - TOOLPATH_NOT_FOUND: Die toolpath_id existiert nicht
    - CAM_NOT_AVAILABLE: Kein CAM-Arbeitsbereich oder keine CAM-Daten
    - CONNECTION_ERROR: Verbindung zu Fusion 360 fehlgeschlagen
    - OPERATION_NOT_SUPPORTED: Operationstyp unterstützt keine Linking-Parameter
    
    Typische Anwendungsfälle: Analyse von Linking-Strategien, Optimierung von Werkzeugbewegungen,
    Überprüfung von Lead-In/Lead-Out-Konfigurationen, Vorbereitung für Linking-Modifikationen.
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_toolpath_linking']}/{toolpath_id}/linking"
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
        elif hasattr(e, 'response') and e.response is not None and e.response.status_code == 400:
            return {
                "error": True,
                "message": f"Operationstyp unterstützt keine Linking-Parameter.",
                "code": "OPERATION_NOT_SUPPORTED"
            }
        else:
            logging.error("Get toolpath linking failed: %s", e)
            return {
                "error": True,
                "message": f"Fehler beim Abrufen der Werkzeugbahn-Linking-Parameter: {str(e)}",
                "code": "UNKNOWN_ERROR"
            }
    except Exception as e:
        logging.error("Get toolpath linking failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Abrufen der Werkzeugbahn-Linking-Parameter: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def modify_toolpath_linking(toolpath_id: str, linking_config: dict):
    """
    Sie können die Linking-Parameter für eine spezifische CAM-Werkzeugbahn modifizieren.
    
    Verwenden Sie dieses Tool nach get_toolpath_linking(), um operationsspezifische Linking-Parameter 
    für eine bestimmte Operation zu ändern. Sie benötigen die toolpath_id aus der Antwort von list_cam_toolpaths.
    
    KRITISCH:
    - Linking-Parameter müssen gegen operationsspezifische Beschränkungen validiert werden
    - Änderungen müssen mit dem Operationstyp kompatibel sein
    - Linking-Integrität muss aufrechterhalten werden
    - Nur editierbare Parameter können geändert werden
    
    Modifizierbare Linking-Parameter (operationsabhängig):
    - 2D Pocket: Lead-In/Lead-Out-Typ, Bogenradius, Übergangstyp, Hubhöhe
    - Trace: Kontaktpunkt, Anfahrt-/Rückzugsdistanzen, Übergänge
    - 3D Operationen: Anfahrtstyp, Rückzugstyp, Freifahrthöhen, Winkel
    - Drill: Bohrzyklus-Typ, Peck-Tiefe, Verweilzeit, Rückzugsverhalten
    
    Beispielanfrage für 2D Pocket:
    {
        "toolpath_id": "op_001",
        "linking_config": {
            "sections": {
                "leads_and_transitions": {
                    "lead_in": {
                        "type": "arc",
                        "arc_radius": 3.0,
                        "arc_sweep": 90
                    },
                    "lead_out": {
                        "type": "arc",
                        "arc_radius": 3.0,
                        "arc_sweep": 90
                    },
                    "transitions": {
                        "type": "lift",
                        "lift_height": 2.0
                    }
                },
                "entry_positioning": {
                    "clearance_height": 30.0,
                    "feed_height": 3.0
                }
            }
        }
    }
    
    Beispielanfrage für 3D Operation:
    {
        "toolpath_id": "op_002",
        "linking_config": {
            "sections": {
                "linking": {
                    "approach": {
                        "type": "perpendicular",
                        "distance": 8.0,
                        "angle": 0.0
                    },
                    "retract": {
                        "type": "perpendicular",
                        "distance": 8.0,
                        "angle": 0.0
                    },
                    "clearance": {
                        "height": 30.0,
                        "type": "from_stock_top"
                    }
                }
            }
        }
    }
    
    Beispielantwort:
    {
        "success": true,
        "message": "Linking-Konfiguration erfolgreich geändert für Werkzeugbahn 'op_001'",
        "previous_config": {
            "operation_type": "2d_pocket",
            "sections": {...}
        },
        "new_config": {
            "operation_type": "2d_pocket",
            "sections": {...}
        },
        "validation_result": {
            "valid": true,
            "errors": [],
            "warnings": ["Significant change in arc_radius: 2.0 → 3.0"]
        },
        "applied_changes": [
            {
                "parameter": "leads_and_transitions.lead_in.arc_radius",
                "fusion_parameter": "leadInRadius",
                "previous_value": 2.0,
                "new_value": 3.0,
                "type": "linking"
            }
        ]
    }
    
    Mögliche Fehler:
    - TOOLPATH_NOT_FOUND: Die toolpath_id existiert nicht
    - VALIDATION_FAILED: Linking-Konfiguration verletzt operationsspezifische Beschränkungen
    - PARAMETER_READ_ONLY: Versuch, schreibgeschützte Parameter zu ändern
    - OPERATION_NOT_SUPPORTED: Operationstyp unterstützt keine Linking-Parameter
    - PARAMETERS_NOT_ACCESSIBLE: Parameter können nicht zugegriffen werden
    
    Typische Anwendungsfälle: Optimierung von Werkzeugbewegungen, Anpassung von Lead-In/Lead-Out-Strategien,
    Feinabstimmung von Anfahrt-/Rückzugsbewegungen, Verbesserung der Oberflächenqualität.
    
    Requirements: 7.4, 4.4, 4.5
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_toolpath_linking']}/{toolpath_id}/linking"
        payload = linking_config
        headers = get_headers()
        response = requests.post(endpoint, json=payload, headers=headers, timeout=get_timeout())
        return response.json()
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
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                return {
                    "error": True,
                    "message": f"Werkzeugbahn mit ID '{toolpath_id}' nicht gefunden.",
                    "code": "TOOLPATH_NOT_FOUND"
                }
            elif e.response.status_code == 400:
                return {
                    "error": True,
                    "message": "Linking-Konfiguration Validierung fehlgeschlagen. Überprüfen Sie die Parameter.",
                    "code": "VALIDATION_FAILED"
                }
            elif e.response.status_code == 403:
                return {
                    "error": True,
                    "message": "Parameter sind schreibgeschützt oder Zugriff verweigert.",
                    "code": "PARAMETERS_NOT_ACCESSIBLE"
                }
        logging.error("Modify toolpath linking failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Ändern der Werkzeugbahn-Linking-Parameter: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }
    except Exception as e:
        logging.error("Modify toolpath linking failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Ändern der Werkzeugbahn-Linking-Parameter: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }