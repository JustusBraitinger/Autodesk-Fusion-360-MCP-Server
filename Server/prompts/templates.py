"""
Prompt template definitions for Fusion 360 MCP Server.

This module contains all prompt templates extracted from the monolithic server,
organized and documented for better maintainability.
"""

from .registry import register_prompt


def weingals_prompt():
    """
    Weingals prompt - Creates a revolved profile using lines and revolve operation.
    
    Dependencies: draw_lines, revolve
    Category: modeling
    """
    return """
    SCHRITT 1: Zeichne Linien
    - Benutze Tool: draw_lines
    - Ebene: XY
    - Punkte: [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]]
    
    SCHRITT 2: Drehe das Profil
    - Benutze Tool: revolve
    - Winkel: 360
    - Der Nutzer wählt in Fusion das Profil und die Achse aus
    """


def magnet_prompt():
    """
    Magnet prompt - Creates a magnet with two cylinders, hole, and logo.
    
    Dependencies: draw_cylinder, draw_holes, draw_witzenmannlogo
    Category: modeling
    """
    return """
    SCHRITT 1: Großer Zylinder oben
    - Benutze Tool: draw_cylinder
    - Radius: 1.59
    - Höhe: 0.3
    - Position: x=0, y=0, z=0.18
    - Ebene: XY
    
    SCHRITT 2: Kleiner Zylinder unten
    - Benutze Tool: draw_cylinder
    - Radius: 1.415
    - Höhe: 0.18
    - Position: x=0, y=0, z=0
    - Ebene: XY
    
    SCHRITT 3: Loch in die Mitte bohren
    - Benutze Tool: draw_holes
    - Punkte: [[0, 0]]
    - Durchmesser (width): 1.0
    - Tiefe (depth): 0.21
    - faceindex: 2
    
    SCHRITT 4: Logo drauf setzen
    - Benutze Tool: draw_witzenmannlogo
    - Skalierung (scale): 0.1
    - Höhe (z): 0.28
    """


def dna_prompt():
    """
    DNA prompt - Creates a DNA double helix using circles, splines, and sweep operations.
    
    Dependencies: draw2Dcircle, spline, sweep
    Category: modeling
    """
    return """
    Benutze nur die tools : draw2Dcircle , spline , sweep
    Erstelle eine DNA Doppelhelix in Fusion 360
    
    DNA STRANG 1:
    
    SCHRITT 1: 
    - Benutze Tool: draw2Dcircle
    - Radius: 0.5
    - Position: x=3, y=0, z=0
    - Ebene: XY
    
    SCHRITT 2: 
    - Benutze Tool: spline
    - Ebene: XY
    - Punkte: [[3,0,0], [2.121,2.121,6.25], [0,3,12.5], [-2.121,2.121,18.75], [-3,0,25], [-2.121,-2.121,31.25], [0,-3,37.5], [2.121,-2.121,43.75], [3,0,50]]
    
    SCHRITT 3: Kreis an der Linie entlang ziehen
    - Benutze Tool: sweep
    
    
    DNA STRANG 2:
    
    SCHRITT 4: 
    - Benutze Tool: draw2Dcircle
    - Radius: 0.5
    - Position: x=-3, y=0, z=0
    - Ebene: XY
    
    SCHRITT 5: 
    - Benutze Tool: spline
    - Ebene: XY
    - Punkte: [[-3,0,0], [-2.121,-2.121,6.25], [0,-3,12.5], [2.121,-2.121,18.75], [3,0,25], [2.121,2.121,31.25], [0,3,37.5], [-2.121,2.121,43.75], [-3,0,50]]
    
    SCHRITT 6: Zweiten Kreis an der zweiten Linie entlang ziehen
    - Benutze Tool: sweep
    
    FERTIG: Jetzt hast du eine DNA Doppelhelix!
    """


def flansch_prompt():
    """
    Flansch prompt - Creates a flange with holes and optional center hole.
    
    Dependencies: draw_cylinder, draw_holes, draw2Dcircle, cut_extrude
    Category: modeling
    """
    return """
    SCHRITT 1: 
    - Benutze Tool: draw_cylinder
    - Denk dir sinnvolle Maße aus (z.B. Radius: 5, Höhe: 1)
    - Position: x=0, y=0, z=0
    - Ebene: XY
    
    SCHRITT 2: Löcher
    - Benutze Tool: draw_holes
    - Mache 6-8 Löcher im Kreis verteilt
    - Tiefe: Mehr als die Zylinderhöhe (damit sie durchgehen)
    - faceindex: 1
    - Beispiel Punkte für 6 Löcher: [[4,0], [2,3.46], [-2,3.46], [-4,0], [-2,-3.46], [2,-3.46]]
    
    SCHRITT 3: Frage den Nutzer
    - "Soll in der Mitte auch ein Loch sein?"
    
    WENN JA:
    SCHRITT 4: 
    - Benutze Tool: draw2Dcircle
    - Radius: 2 (oder was der Nutzer will)
    - Position: x=0, y=0, z=0
    - Ebene: XY
    
    SCHRITT 5: 
    - Benutze Tool: cut_extrude
    - Tiefe: +2 (pos Wert! Größer als Zylinderhöhe)
    """


def vase_prompt():
    """
    Vase prompt - Creates a designer vase using loft and shell operations.
    
    Dependencies: draw2Dcircle, loft, shell_body
    Category: modeling
    """
    return """
    SCHRITT 1: 
    - Benutze Tool: draw2Dcircle
    - Radius: 2.5
    - Position: x=0, y=0, z=0
    - Ebene: XY
    
    SCHRITT 2: 
    - Benutze Tool: draw2Dcircle
    - Radius: 1.5
    - Position: x=0, y=0, z=4
    - Ebene: XY
    
    SCHRITT 3:
    - Benutze Tool: draw2Dcircle
    - Radius: 3
    - Position: x=0, y=0, z=8
    - Ebene: XY
    
    SCHRITT 4: 
    - Benutze Tool: draw2Dcircle
    - Radius: 2
    - Position: x=0, y=0, z=12
    - Ebene: XY
    
    SCHRITT 5: 
    - Benutze Tool: loft
    - sketchcount: 4
    
    SCHRITT 6: Vase aushöhlen (nur Wände übrig lassen)
    - Benutze Tool: shell_body
    - Wandstärke (thickness): 0.3
    - faceindex: 1
    
    FERTIG: Jetzt hast du eine schöne Designer-Vase!
    """


def teil_prompt():
    """
    Teil prompt - Creates a part with holes and threading.
    
    Dependencies: draw_box, draw_holes, draw2Dcircle, cut_extrude, create_thread
    Category: modeling
    """
    return """
    SCHRITT 1: 
    - Benutze Tool: draw_box
    - Breite (width_value): "10"
    - Höhe (height_value): "10"
    - Tiefe (depth_value): "0.5"
    - Position: x=0, y=0, z=0
    - Ebene: XY
    
    SCHRITT 2: Kleine Löcher bohren
    - Benutze Tool: draw_holes
    - 8 Löcher total: 4 in den Ecken + 4 näher zur Mitte
    - Beispiel Punkte: [[4,4], [4,-4], [-4,4], [-4,-4], [2,2], [2,-2], [-2,2], [-2,-2]]
    - Durchmesser (width): 0.5
    - Tiefe (depth): 0.2
    - faceindex: 4
    
    SCHRITT 3: Kreis in der Mitte zeichnen
    - Benutze Tool: draw2Dcircle
    - Radius: 1
    - Position: x=0, y=0, z=0
    - Ebene: XY
    
    SCHRITT 4: 
    - Benutze Tool: cut_extrude
    - Tiefe: +10 (MUSS Positiv SEIN!)
    
    SCHRITT 5: Sage dem Nutzer
    - "Bitte wähle jetzt in Fusion 360 die innere Fläche des mittleren Lochs aus"
    
    SCHRITT 6: Gewinde erstellen
    - Benutze Tool: create_thread
    - inside: True (Innengewinde)
    - allsizes: 10 (für 1/4 Zoll Gewinde)
    
    FERTIG: Teil mit Löchern und Gewinde ist fertig!
    """


def kompensator_prompt():
    """
    Kompensator prompt - Creates a compensator with thin-walled tube and rings.
    
    Dependencies: delete_all, draw2Dcircle, extrude_thin, fillet_edges
    Category: modeling
    """
    return """
                Bau einen Kompensator in Fusion 360 mit dem MCP: Lösche zuerst alles.
                Erstelle dann ein dünnwandiges Rohr: Zeichne einen 2D-Kreis mit Radius 5 in der XY-Ebene bei z=0, 
                extrudiere ihn thin mit distance 10 und thickness 0.1. Füge dann 8 Ringe nacheinander übereinander hinzu (Erst Kreis dann Extrusion 8 mal): Für jeden Ring in
                den Höhen z=1 bis z=8 zeichne einen 2D-Kreis mit Radius 5.1 in der XY-Ebene und extrudiere ihn thin mit distance 0.5 und thickness 0.5.
                Verwende keine boolean operations, lass die Ringe als separate Körper. Runde anschließend die Kanten mit Radius 0.2 ab.
                Mache schnell!!!!!!
    
                """


# Register all prompts with the registry
def register_all_prompts():
    """Register all prompt templates with the global registry."""
    
    # Register modeling prompts
    register_prompt(
        "weingals", 
        weingals_prompt,
        "Creates a revolved profile using lines and revolve operation",
        "modeling",
        ["draw_lines", "revolve"]
    )
    
    register_prompt(
        "magnet", 
        magnet_prompt,
        "Creates a magnet with two cylinders, hole, and logo",
        "modeling",
        ["draw_cylinder", "draw_holes", "draw_witzenmannlogo"]
    )
    
    register_prompt(
        "dna", 
        dna_prompt,
        "Creates a DNA double helix using circles, splines, and sweep operations",
        "modeling",
        ["draw2Dcircle", "spline", "sweep"]
    )
    
    register_prompt(
        "flansch", 
        flansch_prompt,
        "Creates a flange with holes and optional center hole",
        "modeling",
        ["draw_cylinder", "draw_holes", "draw2Dcircle", "cut_extrude"]
    )
    
    register_prompt(
        "vase", 
        vase_prompt,
        "Creates a designer vase using loft and shell operations",
        "modeling",
        ["draw2Dcircle", "loft", "shell_body"]
    )
    
    register_prompt(
        "teil", 
        teil_prompt,
        "Creates a part with holes and threading",
        "modeling",
        ["draw_box", "draw_holes", "draw2Dcircle", "cut_extrude", "create_thread"]
    )
    
    register_prompt(
        "kompensator", 
        kompensator_prompt,
        "Creates a compensator with thin-walled tube and rings",
        "modeling",
        ["delete_all", "draw2Dcircle", "extrude_thin", "fillet_edges"]
    )


# Auto-register prompts when module is imported
register_all_prompts()