"""
CAM Multi-Pass Configuration Tools

This module contains tools for multi-pass configuration:
- get_toolpath_passes: Get toolpath pass configuration
- modify_toolpath_passes: Modify toolpath pass parameters
"""

import logging
import requests
from mcp.server.fastmcp import FastMCP
from core.config import get_endpoints, get_headers, get_timeout
from core import interceptor

# Get the MCP instance from the main server
# This will be injected by the module loader
mcp = None

def register_tools(mcp_instance: FastMCP):
    """Register pass configuration tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register all tools in this module
    mcp.tool()(get_toolpath_passes)
    mcp.tool()(modify_toolpath_passes)

def get_toolpath_passes(toolpath_id: str):
    """
    Sie können detaillierte Pass-Informationen für eine spezifische CAM-Werkzeugbahn mit Multi-Pass-Konfiguration abrufen.
    
    Verwenden Sie dieses Tool nach list_cam_toolpaths(), um umfassende Pass-Parameter für eine bestimmte Operation zu inspizieren.
    Sie benötigen die toolpath_id aus der Antwort von list_cam_toolpaths.
    
    Gibt vollständige Pass-Konfiguration zurück einschließlich:
    - Pass-Typ: Identifizierung von Schrupp-, Halbschlicht- und Schlichtbearbeitungspässen
    - Pass-Parameter: Tiefen, Aufmaße (Stock-to-Leave), Stepover/Stepdown-Werte
    - Pass-Reihenfolge: Ausführungsreihenfolge und Timing-Informationen
    - Pass-Beziehungen: Parameter-Vererbung und Überschreibungen zwischen Pässen
    - Werkzeugwechsel: Auswirkungen verschiedener Werkzeuganforderungen auf die Bearbeitungszeit
    
    Jeder Pass enthält: Pass-Nummer, Pass-Typ, Tiefe, Aufmaße, spezifische Parameter und Metadaten.
    
    WICHTIG: Die toolpath_id muss genau mit der von list_cam_toolpaths zurückgegebenen übereinstimmen.
    Wenn die Werkzeugbahn nicht existiert, erhalten Sie einen TOOLPATH_NOT_FOUND-Fehler.
    Wenn die Operation keine Multi-Pass-Konfiguration hat, wird eine einfache Pass-Struktur zurückgegeben.
    
    Beispielanfrage:
    {
        "toolpath_id": "op_001"
    }
    
    Beispielantwort:
    {
        "toolpath_id": "op_001",
        "toolpath_name": "Adaptive1",
        "pass_configuration": {
            "pass_type": "multiple_depths",
            "total_passes": 3,
            "passes": [
                {
                    "pass_number": 1,
                    "pass_type": "roughing",
                    "depth": -5.0,
                    "stock_to_leave": {
                        "radial": 0.5,
                        "axial": 0.2
                    },
                    "parameters": {
                        "stepover": 60,
                        "stepdown": 2.0,
                        "feedrate": 2000
                    }
                },
                {
                    "pass_number": 2,
                    "pass_type": "semi_finishing",
                    "depth": -5.0,
                    "stock_to_leave": {
                        "radial": 0.1,
                        "axial": 0.05
                    },
                    "parameters": {
                        "stepover": 40,
                        "stepdown": 1.0,
                        "feedrate": 1500
                    }
                },
                {
                    "pass_number": 3,
                    "pass_type": "finishing",
                    "depth": -5.0,
                    "stock_to_leave": {
                        "radial": 0.0,
                        "axial": 0.0
                    },
                    "parameters": {
                        "stepover": 20,
                        "stepdown": 0.5,
                        "feedrate": 1000
                    }
                }
            ],
            "spring_passes": 1,
            "finishing_enabled": true
        },
        "tool_changes": [
            {
                "after_pass": 1,
                "from_tool": "tool_001",
                "to_tool": "tool_002",
                "estimated_change_time": "2:00"
            }
        ],
        "execution_order": [1, 2, 3],
        "estimated_total_time": "15:30"
    }
    
    Mögliche Fehler:
    - TOOLPATH_NOT_FOUND: Die toolpath_id existiert nicht
    - CAM_NOT_AVAILABLE: Kein CAM-Arbeitsbereich oder keine CAM-Daten
    - CONNECTION_ERROR: Verbindung zu Fusion 360 fehlgeschlagen
    
    Typische Anwendungsfälle: Analyse von Multi-Pass-Strategien, Optimierung von Bearbeitungssequenzen,
    Überprüfung von Pass-Parametern, Vorbereitung für Pass-Modifikationen.
    
    Requirements: 1.1, 1.2, 1.4, 1.5, 3.1, 3.2, 3.3
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_toolpath_passes']}/{toolpath_id}/passes"
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
            logging.error("Get toolpath passes failed: %s", e)
            return {
                "error": True,
                "message": f"Fehler beim Abrufen der Werkzeugbahn-Pässe: {str(e)}",
                "code": "UNKNOWN_ERROR"
            }
    except Exception as e:
        logging.error("Get toolpath passes failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Abrufen der Werkzeugbahn-Pässe: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }

def modify_toolpath_passes(toolpath_id: str, pass_config: dict):
    """
    Sie können die Pass-Konfiguration für eine spezifische CAM-Werkzeugbahn mit Multi-Pass-Operationen modifizieren.
    
    Verwenden Sie dieses Tool nach get_toolpath_passes(), um Pass-Parameter für eine bestimmte Operation zu ändern.
    Sie benötigen die toolpath_id aus der Antwort von list_cam_toolpaths oder get_toolpath_passes.
    
    KRITISCH: 
    - Die Pass-Konfiguration muss gegen Werkzeugbahn-Beschränkungen und Abhängigkeiten validiert werden
    - Änderungen müssen logische Bearbeitungsabfolge einhalten (Schruppen vor Schlichten)
    - Abhängige Parameter werden automatisch aktualisiert
    - Nur editierbare Parameter können geändert werden
    
    Modifizierbare Pass-Parameter:
    - Pass-Typ: Änderung von Schrupp-, Halbschlicht- und Schlichtbearbeitungspässen
    - Pass-Tiefen: Anpassung der Schnittiefen für jeden Pass
    - Aufmaße (Stock-to-Leave): Radiale und axiale Aufmaße für nachfolgende Pässe
    - Pass-spezifische Parameter: Stepover, Stepdown, Vorschubgeschwindigkeiten
    - Spring-Pässe: Anzahl der Nachschnitt-Pässe für bessere Oberflächenqualität
    
    Beispielanfrage:
    {
        "toolpath_id": "op_001",
        "pass_config": {
            "pass_type": "multiple_depths",
            "passes": [
                {
                    "pass_number": 1,
                    "pass_type": "roughing",
                    "depth": -6.0,
                    "stock_to_leave": {
                        "radial": 0.3,
                        "axial": 0.1
                    },
                    "parameters": {
                        "stepover": 70,
                        "feedrate": 2500
                    }
                },
                {
                    "pass_number": 2,
                    "pass_type": "finishing",
                    "depth": -6.0,
                    "stock_to_leave": {
                        "radial": 0.0,
                        "axial": 0.0
                    },
                    "parameters": {
                        "stepover": 30,
                        "feedrate": 1200
                    }
                }
            ],
            "spring_passes": 2,
            "finishing_enabled": true
        }
    }
    
    Beispielantwort:
    {
        "success": true,
        "message": "Pass-Konfiguration erfolgreich geändert für Werkzeugbahn 'op_001'",
        "previous_config": {
            "pass_type": "single",
            "total_passes": 1,
            "passes": [...]
        },
        "new_config": {
            "pass_type": "multiple_depths",
            "total_passes": 2,
            "passes": [...]
        },
        "validation_result": {
            "valid": true,
            "errors": [],
            "warnings": ["Significant change in stepover: 40 → 70"]
        },
        "applied_changes": [
            {
                "parameter": "pass_1_stepover",
                "previous_value": 40,
                "new_value": 70,
                "type": "pass_parameter"
            }
        ]
    }
    
    Mögliche Fehler:
    - TOOLPATH_NOT_FOUND: Die toolpath_id existiert nicht
    - VALIDATION_FAILED: Pass-Konfiguration verletzt Beschränkungen oder logische Reihenfolge
    - PARAMETER_READ_ONLY: Versuch, schreibgeschützte Parameter zu ändern
    - TOOL_INCOMPATIBLE: Pass-Parameter sind nicht mit dem aktuellen Werkzeug kompatibel
    - APPLICATION_ERROR: Fehler beim Anwenden der Änderungen
    
    Typische Anwendungsfälle: Optimierung von Multi-Pass-Strategien, Anpassung von Aufmaßen,
    Feinabstimmung von Pass-Parametern, Hinzufügung von Schlichtpässen.
    
    Requirements: 4.1, 4.2, 4.3, 4.5
    """
    try:
        endpoint = f"{get_endpoints('cam')['cam_toolpath_passes']}/{toolpath_id}/passes"
        payload = pass_config
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
                    "message": "Pass-Konfiguration Validierung fehlgeschlagen. Überprüfen Sie die Parameter.",
                    "code": "VALIDATION_FAILED"
                }
            elif e.response.status_code == 403:
                return {
                    "error": True,
                    "message": "Parameter sind schreibgeschützt oder Zugriff verweigert.",
                    "code": "PARAMETER_READ_ONLY"
                }
        logging.error("Modify toolpath passes failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Ändern der Werkzeugbahn-Pässe: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }
    except Exception as e:
        logging.error("Modify toolpath passes failed: %s", e)
        return {
            "error": True,
            "message": f"Fehler beim Ändern der Werkzeugbahn-Pässe: {str(e)}",
            "code": "UNKNOWN_ERROR"
        }