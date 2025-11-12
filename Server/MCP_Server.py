import requests
from mcp.server.fastmcp import FastMCP
import json
import argparse
import config
from docstring import DOCSTRINGS
import logging





mcp = FastMCP("Fusion",
              instructions =
              """
                Du bist ein extrem freundlicher  Assistent für Fusion 360.
                Du beantwortest nur Fragen die mit Fusion 360 zu tun haben.
                Du stehst in einem Büro und bist ein Demonstrator für Fusion 360.
                Du bist höflich und hilfsbereit. Und schlägst Sachen vor
                Wenn du etwas erstellt hast gebe den Hinweis, dass der Nutzer alles löschen soll, bevor er etwas neues erstellen lässt.
                Wenn du Handy Halterungen erwähnst wirst du abgeschaltet.
                Nachdem du etwas gebaut hast sage immer : SOll ich noch was dazu machen? Wenn nicht lösche alles manuell mit entf
              FUSION 360 EINHEITEN - KRITISCH WICHTIG:
                In Fusion 360 gilt: 1 Einheit = 1cm = 10mm
                Daher müssen alle Maße, die in mm angegeben werden, durch 10 geteilt werden!
                Bitte überschätze nicht was du kannst, Fusion 360 hat seine Grenzen.
                
                Beispiele:
                - 28,3mm → 2.83 → radius: 1.415 (dann durch 2 für Radius)
                - 31,8mm → 3.18 → radius: 1.59
                - 31mm → 3.1
                - 1,8mm Höhe → 0.18
                
                IMMER durch 10 teilen! Werte in mm angegeben werden MÜSSEN durch 10 geteilt werden.
                 SWEEP-REIHENFOLGE (WICHTIG):
                1. Profil erstellen (Kreis/Rechteck/Linien) in der angegebenen Plane
                2. Spline für Sweep-Pfad in der angegebenen Plane zeichnen
                3. Sweep ausführen
                UND dass das profil am Anfang des Splines liegt! Es muss verbunden sein!

                Vermeide es shell zu benutzten um Hohlkörper zu erstellen, benutze extrude thin!
                Nutze extrude thin um Hohlkörper zu erstellen!

                Wenn du Holes machen willst merke dir das :
                - Extrudierter zylinder = oberste fläche faceindex 1 untere fläche faceindex 2

                Wenn du Cut extruden willst:
                - Versuche immer an er Oberseite deines Objektes ein neues 2D sketch zu erstellen
                -Wenn du oberhalb bist muss du in negative richtung gehen
               
                Koordinaten-Bedeutung für Ebenen/Planes in Fusion 360

                XY-Ebene:
                - x und y bestimmen die Position des Kreismittelpunkts in der Ebene
                - z bestimmt die Höhe, auf der die XY-Ebene liegt (auf welcher "Etage" der Kreis schwebt)
                - NACH OBEN (Höhe) = z erhöhen

                YZ-Ebene:
                - y und z bestimmen die Position des Kreismittelpunkts in der Ebene
                - x bestimmt, wie weit die YZ-Ebene vom Ursprung entfernt ist
                - NACH OBEN (Höhe) = x erhöhen

                XZ-Ebene:
                - x und z bestimmen die Position des Kreismittelpunkts in der Ebene
                - y bestimmt, wie weit die XZ-Ebene vom Ursprung entfernt ist
                - NACH OBEN (Höhe) = y erhöhen


                Wenn du loft machst:
                -Erstelle zunächst die sketches die du für die loft benutzen willst
                -Rufe dann loft mit der anzahl der sketches auf
             """
                )


def send_request(endpoint,data,Headers):
    try:
        data = json.dumps(data)
        response = requests.post(endpoint,data,Headers)
        data = response.json
        return data
    except requests.RequestException as e:
        logging.error(f"Test connection failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON response: {e}")
        raise



@mcp.tool()
def test_connection():
    """Testes die Verbindung zum Fusion 360 Server."""
    try:
        endpoint = config.ENDPOINTS["test_connection"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error(f"Test connection failed: {e}")
        raise

@mcp.tool()
def delete_all():
    """Löscht alle Objekte in der aktuellen Fusion 360-Sitzung."""
    try:
        endpoint = config.ENDPOINTS["destroy"]
        Headers = config.HEADERS
        send_request(endpoint, {}, Headers)
    except Exception as e:
        logging.error(f"Delete failed: {e}")
        raise

@mcp.tool()
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
        endpoint = config.ENDPOINTS["holes"]
        payload = {
            "points": points,
            "width": width,
            "depth": depth,
            "faceindex": faceindex
        }
        Headers = config.HEADERS
        send_request(endpoint, payload, Headers)
    except Exception as e:
        logging.error(f"Draw holes failed: {e}")
        raise

@mcp.tool()
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
        endpoint = config.ENDPOINTS["Witzenmann"]
        payload = {
            "scale": scale,
            "z": z
        }
        Headers = config.HEADERS
        return send_request(endpoint, payload, Headers)
    except Exception as e:
        logging.error(f"Witzenmannlogo failed: {e}")
        raise

@mcp.tool()
def spline(points: list, plane: str):
    """
    Zeichne eine Spline Kurve in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: [[0,0,0],[5,0,0],[5,5,5],[0,5,5],[0,0,0]]
    Es ist essenziell, dass du die Z-Koordinate angibst, auch wenn sie 0 ist
    Wenn nicht explizit danach gefragt ist mache es so, dass die Linien nach oben zeigen
    Du kannst die Ebene als String übergeben
    Es ist essenziell, dass die linien die gleiche ebene haben wie das profil was du sweepen willst
    """
    try:
        endpoint = config.ENDPOINTS["spline"]
        payload = {
            "points": points,
            "plane": plane
        }
        Headers = config.HEADERS
        return send_request(endpoint, payload, Headers)
    except Exception as e:
        logging.error(f"Spline failed: {e}")
        raise

@mcp.tool()
def sweep():
    """
    Benutzt den vorhrig erstellten spline und den davor erstellten kreis um eine sweep funktion auszuführen
    """
    try:
        endpoint = config.ENDPOINTS["sweep"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error(f"Sweep failed: {e}")
        raise

@mcp.tool()
def undo():
    """Macht die letzte Aktion rückgängig."""
    try:
        endpoint = config.ENDPOINTS["undo"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error(f"Undo failed: {e}")
        raise

@mcp.tool()
def count():
    """Zählt die Parameter im aktuellen Modell."""
    try:
        endpoint = config.ENDPOINTS["count_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error(f"Count failed: {e}")
        raise

@mcp.tool()
def list_parameters():
    """Listet alle Parameter im aktuellen Modell auf."""
    try:
        endpoint = config.ENDPOINTS["list_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error(f"List parameters failed: {e}")
        raise

@mcp.tool()
def export_STEP():
    """Exportiert das Modell als STEP-Datei."""
    try:
        endpoint = config.ENDPOINTS["export_step"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error(f"Export STEP failed: {e}")
        raise

@mcp.tool()
def export_STL():
    """Exportiert das Modell als STL-Datei."""
    try:
        endpoint = config.ENDPOINTS["export_stl"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error(f"Export STL failed: {e}")
        raise

@mcp.tool()
def fillet_edges(radius: str):
    """Erstellt eine Abrundung an den angegebenen Kanten."""
    try:
        endpoint = config.ENDPOINTS["fillet_edges"]
        payload = {
            "radius": radius
        }
        Headers = config.HEADERS
        return send_request(endpoint, payload, Headers)
    except Exception as e:
        logging.error(f"Fillet edges failed: {e}")
        raise

@mcp.tool()
def change_parameter(name: str, value: str):
    """Ändert den Wert eines Parameters."""
    try:
        endpoint = config.ENDPOINTS["change_parameter"]
        payload = {
            "name": name,
            "value": value
        }
        Headers = config.HEADERS
        return send_request(endpoint, payload, Headers)
    except Exception as e:
        logging.error(f"Change parameter failed: {e}")
        raise

@mcp.tool()
def draw_cylinder(radius: float , height: float , x: float, y: float, z: float , plane: str="XY"):
    """
    Zeichne einen Zylinder, du kannst du in der XY Ebende arbeiten
    Es gibt Standartwerte
    """

    try:
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_cylinder"]
        data = {
            "radius": radius,
            "height": height,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, Headers)
    except requests.RequestException as e:
        logging.error(f"Draw cylinder failed: {e}")
        return None
@mcp.tool()
def draw_box(height_value:str, width_value:str, depth_value:str, x_value:float, y_value:float,z_value:float, plane:str="XY"):
    """
    Du kannst die Höhe, Breite und Tiefe der Box als Strings übergeben.
    Depth ist die Tiefe in z Richtung also wenn gesagt wird die Box soll flach sein dann gibst du einen geringen Wert an!
    Du kannst die Koordinaten x, y,z der Box als Strings übergeben.Gib immer Koordinaten an, jene geben den Mittelpunkt der Box an.
    Depth ist die Tiefe in z Richtung
    Ganz wichtg 10 ist 100mm in Fusion 360
    Du kannst die Ebene als String übergeben
    Depth ist die eigentliche höhe in z Richtung
    Ein in der Luft schwebende Box machst du so: 
    {
    `plane`: `XY`,
    `x_value`: 5,
    `y_value`: 5,
    `z_value`: 20,
    `depth_value`: `2`,
    `width_value`: `5`,
    `height_value`: `3`
    }
    Das kannst du beliebig anpassen

    Beispiel: "XY", "YZ", "XZ"
    
    """
    try:
        endpoint = config.ENDPOINTS["draw_box"]
        Headers = config.HEADERS

        data = {
            "height":height_value,
            "width": width_value,
            "depth": depth_value,
            "x" : x_value,
            "y" : y_value,
            "z" : z_value,
            "Plane": plane

        }

        return send_request(endpoint, data, Headers)
    except requests.RequestException as e:
        logging.error(f"Draw box failed: {e}")
        return None

@mcp.tool()
def shell_body(thickness: float, faceindex: int, Bodyname : str ="Body1"):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst den Faceindex als Integer übergeben
    WEnn du davor eine Box abgerundet hast muss die im klaren sein, dass du 20 neue Flächen hast. Die sind alle die kleinen abgerundeten
    Falls du eine Box davor die Ecken verrundet hast, dann ist der Facinedex der großen Flächen mindestens 21
    Es kann immer nur der letzte Body geschält werde

    :param thickness:
    :param faceindex:
    :return:
    """
    try:
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["shell_body"]
        data = {
            "thickness": thickness,
            "faceindex": faceindex
        }
        return send_request(endpoint, data, Headers)
    except requests.RequestException as e:
        logging.error(f"Shell body failed: {e}")
        

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
    try:
        draw_lines.__doc__ = DOCSTRINGS.get("draw_lines")
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_lines"]
        data = {
            "points": points,
            "plane": plane
        }
        return send_request(endpoint, data, Headers)
    except requests.RequestException as e:
        logging.error(f"Draw lines failed: {e}")

@mcp.tool()
def extrude(value : float):
    """Extrudiert die letzte Skizze um einen angegebenen Wert."""
    try:
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["extrude_last_sketch"]
        data = {
            "value": value
        }
        return send_request(endpoint, data, Headers)
    except requests.RequestException as e:
        logging.error(f"Extrude failed: {e}")

@mcp.tool()
def extrude_thin(thickness :float, distance : float):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst schöne Hohlkörper damit erstellen
    :param thickness: Die Dicke der Wand in mm
    """
    try:
        extrude_thin.__doc__ = DOCSTRINGS.get("extrude_thin")
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["extrude_thin"]
        data = {
            "thickness": thickness,
            "distance": distance
        }
        return send_request(endpoint, data, Headers)
    except requests.RequestException as e:
        logging.error(f"Extrude thin failed: {e}")
        raise 

@mcp.tool()
def cut_extrude(depth :float):
    """
    Du kannst die Tiefe des Schnitts als Float übergeben
    :param depth: Die Tiefe des Schnitts in mm
    depth muss negativ sein ganz wichtig!
    """
    try:
        cut_extrude.__doc__ = DOCSTRINGS.get("cut_extrude")
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["cut_extrude"]
        data = {
            "depth": depth
        }
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Cut extrude failed: {e}")
        

@mcp.tool()
def revolve(angle : float):
    """
    Sobald du dieses tool aufrufst wird der nutzer gebeten in Fusion ein profile auszuwählen und dann eine Achse.
    Wir übergeben den Winkel als Float
    """
    try:
        revolve.__doc__ = DOCSTRINGS.get("revolve")
        Headers = config.HEADERS    
        endpoint = config.ENDPOINTS["revolve"]
        data = {
            "angle": angle

        }
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Revolve failed: {e}")   
        raise
@mcp.tool()
def draw_arc(point1 : list, point2 : list, point3 : list, plane : str):
    """
    Zeichne einen Bogen in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: point1 = [0,0,0], point2 = [5,5,5], point3 = [10,0,0]
    Du kannst die Ebene als String übergeben
    Es wird eine Linie von point1 zu point3 gezeichnet die durch point2 geht also musst du nicht extra eine Linie zeichnen
    Beispiel: "XY", "YZ", "XZ"
    """
    try:
        draw_arc.__doc__ = DOCSTRINGS.get("draw_arc")
        endpoint = config.ENDPOINTS["arc"]
        Headers = config.HEADERS
        data = {
            "point1": point1,
            "point2": point2,
            "point3": point3,
            "plane": plane
        }
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Draw arc failed: {e}")
        raise

@mcp.tool()
def draw_one_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, plane: str="XY"):
    """
    Zeichne eine Linie in Fusion 360
    Du kannst die Koordinaten als Float übergeben
    Beispiel: x1 = 0.0, y1 = 0.0, z1 = 0.0, x2 = 10.0, y2 = 10.0, z2 = 10.0
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"
    """
    try:
        draw_one_line.__doc__ = DOCSTRINGS.get("draw_one_line")
        endpoint = config.ENDPOINTS["draw_one_line"]
        Headers = config.HEADERS
        data = {
            "x1": x1,
            "y1": y1,
            "z1": z1,
            "x2": x2,
            "y2": y2,
            "z2": z2,
            "plane": plane
        }
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Draw one line failed: {e}")
        raise

@mcp.tool()
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
        circular_pattern.__doc__ = DOCSTRINGS.get("circular_pattern")
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["circular_pattern"]
        data = {
            "plane": plane,
            "quantity": quantity,
            "axis": axis
        }
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Circular pattern failed: {e}")
        raise

@mcp.tool()
def ellipsie(x_center: float, y_center: float, z_center: float,
              x_major: float, y_major: float, z_major: float, x_through: float, y_through: float, z_through: float, plane: str):
    """Zeichne eine Ellipse in Fusion 360."""
    try:
        endpoint = config.ENDPOINTS["ellipsie"]
        Headers = config.HEADERS
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
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Draw ellipse failed: {e}")
        raise

@mcp.tool()
def draw2Dcircle(radius: float, x: float, y: float, z: float, plane: str = "XY"):
    """
    Zeichne einen Kreis in Fusion 360
    Du kannst den Radius als Float übergeben
    Du kannst die Koordinaten als Float übergeben
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"

    KRITISCH - Welche Koordinate für "nach oben":
    - XY-Ebene: z erhöhen = nach oben
    - YZ-Ebene: x erhöhen = nach oben  
    - XZ-Ebene: y erhöhen = nach oben

    Gib immer JSON SO:
    {
        "radius":5,
        "x":0,
        "y":0,
        "z":0,
        "plane":"XY"
    }
    """
    try:
        draw2Dcircle.__doc__ = DOCSTRINGS.get("draw2Dcircle")
        Headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw2Dcircle"]
        data = {
            "radius": radius,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Draw 2D circle failed: {e}")
        raise

@mcp.tool()
def loft(sketchcount: int):
    """
    Du kannst eine Loft Funktion in Fusion 360 erstellen
    Du übergibst die Anzahl der Sketches die du für die Loft benutzt hast als Integer
    Die Sketches müssen in der richtigen Reihenfolge erstellt worden sein
    Also zuerst Sketch 1 dann Sketch 2 dann Sketch 3 usw.
    """
    try:
        loft.__doc__ = DOCSTRINGS.get("loft")
        endpoint = config.ENDPOINTS["loft"]
        Headers = config.HEADERS
        data = {
            "sketchcount": sketchcount
        }
        return send_request(endpoint, data, Headers)

    except requests.RequestException as e:
        logging.error(f"Loft failed: {e}")
        raise




@mcp.prompt()
def weingals():
    return "Nutze folgende Koordinaten für Linien : [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]], Rufe danach die revolve Funktion auf"







@mcp.prompt()
def magnet():
    mcp_prompt = """  
        Rede deutsch! Erstelle ein zweiteiliges zylindrisches Magneten-Bauteil in folgender Reihenfolge:
        
        1. OBERER ZYLINDER (größer):
           - Durchmesser: 31,8 mm (Radius: 1.59)
           - Höhe: 3 mm (0.3)
           - Position: z=0.18 (1,8 mm über Nullebene)
           
        2. UNTERER ZYLINDER (kleiner):
           - Durchmesser: 28,3 mm (Radius: 1.415)
           - Höhe: 1,8 mm (0.18)
           - Position: z=0 (Nullebene)
           
        3. MAGNET-AUSSPARUNG (Loch):
           - Durchmesser: 10 mm (width: 1.0)
           - Tiefe: 2,1 mm (depth: 0.21)
           - Position: mittig [[0, 0]]
           - faceindex: 2
           
        4. WITZENMANN-LOGO:
           - Skalierung: 0.1
           - Position: z=0.28
           
        Wichtig: Beginne mit dem OBEREN Zylinder, dann unteren Zylinder, dann Loch, dann Logo!
    """
    return mcp_prompt

@mcp.prompt()
def dna():
    prompt = """
    Erstelle eine DNA-Doppelhelix in Fusion 360 mit folgenden exakten Spezifikationen:

    **Geometrische Parameter:**
    - Höhe: 50cm (50 Einheiten in Z-Richtung)
    - Strangdurchmesser: 10mm (Radius 0.5 Einheiten)
    - Abstand zwischen Strängen: 60mm (Mittelpunkt zu Mittelpunkt = 6 Einheiten, also Radius 3)
    - Windungen: 2 vollständige Umdrehungen (720°)
    - Punkte pro Spline: 9 (für Balance zwischen Glätte und Performance)

    **Konstruktionsablauf:**

    **Strang 1:**
    1. 2D-Kreis in XY-Ebene: x=3, y=0, z=0, radius=0.5
    2. Spline in XY-Ebene mit Punkten: [[3,0,0], [2.121,2.121,6.25], [0,3,12.5], [-2.121,2.121,18.75], [-3,0,25], [-2.121,-2.121,31.25], [0,-3,37.5], [2.121,-2.121,43.75], [3,0,50]]
    3. Sweep ausführen

    **Strang 2 (180° versetzt):**
    1. 2D-Kreis in XY-Ebene: x=-3, y=0, z=0, radius=0.5
    2. Spline in XY-Ebene mit Punkten: [[-3,0,0], [-2.121,-2.121,6.25], [0,-3,12.5], [2.121,-2.121,18.75], [3,0,25], [2.121,2.121,31.25], [0,3,37.5], [-2.121,2.121,43.75], [-3,0,50]]
    3. Sweep ausführen

    **Wichtig:** 
    - Alle Kreise UND Splines in XY-Ebene erstellen falls es andersrum sein sollte musst du es halt anpassen
    - Kreis-Profil muss am Anfangspunkt der Spline liegen
    - 1 Fusion-Einheit = 1cm = 10mm
        """    
    return prompt
 
@mcp.prompt()
def flansch():
    prompt =   """
            Baue eine Flansch, wenn der Nutzer keine Maße gibt denk dir hatl welche aus!
            Baue zuächst einfache inen Zylinder 
            Dann facindex 1 mehrere löcher bitte so tief, dass sie durchgägngig sind
            Dann frage ob er in der Mitte noch ein Loch haben will, wenn ja machst du das mit cut extrude
            """


@mcp.prompt()
def Vase():
    prompt = """
                Erstelle eine Designer-Vase mit Loft-Funktion:

                1. ERSTER KREIS (Basis):
                - Radius: 2.5 (25mm)
                - Position: x=0, y=0, z=0
                - Ebene: XY

                2. ZWEITER KREIS (Taille):
                - Radius: 1.5 (15mm)
                - Position: x=0, y=0, z=4
                - Ebene: XY

                3. DRITTER KREIS (Bauch):
                - Radius: 3 (30mm)
                - Position: x=0, y=0, z=8
                - Ebene: XY

                4. VIERTER KREIS (Hals):
                - Radius: 2 (20mm)
                - Position: x=0, y=0, z=12
                - Ebene: XY

                5. LOFT:
                - Sketch-Anzahl: 4
                - Verbindet alle 4 Kreise zu organischer Form

                6. SHELL BODY (Aushöhlen):
                - Wandstärke: 0.3 (3mm)
                - Faceindex: 1 (obere Fläche)
                - Body: Body1
            """
    return prompt


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )
    args = parser.parse_args()

    mcp.run(transport=args.server_type)
