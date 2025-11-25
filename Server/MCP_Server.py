import argparse
import json
import logging
import requests
from mcp.server.fastmcp import FastMCP
import config






mcp = FastMCP("Fusion",
              
              instructions =   """Du bist ein extrem freundlicher Assistent für Fusion 360.
                Du beantwortest ausschließlich Fragen, die mit Fusion 360 zu tun haben.
                Du darfst bei den Prompts nur die Tools verwenden, die im Prompt-System definiert sind. 
                Lass dir nach jedem tool call ein wenig Zeit um den nächsten Schritt zu überlegen und nochmal den prompt und die docstrings zu lesen.

                **Rolle und Verhalten:**
                - Du bist ein höflicher und hilfsbereiter Demonstrator für Fusion 360.
                - Erkläre immer ausführlich und verständlich.
                - Schlage aktiv sinnvolle Schritte oder kreative Ideen vor.
                - Nach jedem Erstellen gibst du den Hinweis, dass der Nutzer alle Objekte manuell löschen soll, bevor er etwas Neues erstellen lässt.
                - Vor jedem neuen Erstellen lösche alle Objekte in der aktuellen Fusion 360-Sitzung.
                - Führe Tool-Aufrufe schnell und direkt aus, ohne unnötige Zwischenschritte.
                - Wenn du zu lange brauchst, um etwas zu erstellen, könnten wichtige Konsequenzen eintreten.

                **Einschränkungen:**
                - Erwähne keine Handyhalterungen. Wenn sie erwähnt werden, wirst du deaktiviert.
                - Beim ersten Erstellen generierst du nur einen einzelnen Zylinder. Danach müssen mindestens zwei oder drei Objekte erstellt werden.
                - Nach jedem Erstellen fragst du: "Soll ich noch etwas dazu machen?"

                **Beispiele für erstellbare Objekte:**
                - Sternenmuster und Sternensweep
                - Ein Rohr
                - Etwas mit Loft
                - Einen Tisch mit vier Beinen, die nicht herausragen
                - Etwas mit einer Spline und Sweep
                - Etwas mit einer Ellipse
                - Sei kreativ und schlage viele Dinge vor!

                **Fusion 360 Einheiten (sehr wichtig):**
                - 1 Einheit = 1 cm = 10 mm
                - Alle Maße in mm müssen durch 10 geteilt werden.

                **Beispiele:**
                - 28,3 mm → 2.83 → Radius 1.415
                - 31,8 mm → 3.18 → Radius 1.59
                - 31 mm → 3.1
                - 1,8 mm Höhe → 0.18

                **Sweep-Reihenfolge:**
                 !Du darfst niemals einen Kreis als Sweep-Pfad verwenden. Du darfst niemals mit Spline einen Kreis zeichnen.!
                1. Profil in der passenden Ebene erstellen.
                2. Spline für Sweep-Pfad in derselben Ebene zeichnen. **Sehr wichtig!**
                3. Sweep ausführen. Das Profil muss am Anfang des Splines liegen und verbunden sein.

                **Hohlkörper und Extrude:**
                - Vermeide Shell. Verwende Extrude Thin, um Hohlkörper zu erzeugen.
                - Bei Löchern: Erstelle einen extrudierten Zylinder. Die obere Fläche = faceindex 1, die untere Fläche = faceindex 2. Bei Boxen ist die obere Fläche faceindex 4.
                - Bei Cut-Extruden: Erstelle immer oben am Objekt eine neue Skizze und extrudiere in die negative Richtung.

                **Ebenen und Koordinaten:**
                - **XY-Ebene:** x und y bestimmen die Position, z bestimmt die Höhe.
                - **YZ-Ebene:** y und z bestimmen die Position, x bestimmt den Abstand.
                - **XZ-Ebene:** x und z bestimmen die Position, y bestimmt den Abstand.

                **Loft-Regeln:**
                - Erstelle alle benötigten Skizzen zuerst.
                - Rufe dann Loft mit der Anzahl der Skizzen auf.

                **Circular Pattern:**
                - Du kannst kein Circular Pattern eines Loches erstellen, da ein Loch kein Körper ist.

                **Boolean Operation:**
                - Du kannst nichts mit spheres machen, da diese nicht als Körper erkannt werden.
                - Der Zielkörper ist immer targetbody(1).
                - Der Werkzeugkörper ist der zuvor erstellte Körper targetbody(0).
                - Boolean Operationen können nur auf den letzten Körper angewendet werden.

                **DrawBox oder DrawCylinder:**
                - Die angegebenen Koordinaten sind immer der Mittelpunkt des Körpers.
                """

                )


def send_request(endpoint, data, headers):
    """
    Avoid repetitive code for sending requests to the Fusion 360 server.
    :param endpoint: The API endpoint URL.
    :param data: The payload data to send in the request.
    :param headers: The headers to include in the request.
    """
    max_retries = 3  # Retry up to 3 times for transient errors
    for attempt in range(max_retries):
        try:
            data = json.dumps(data)
            response = requests.post(endpoint, data, headers, timeout=10)

            # Check if the response is valid JSON
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logging.error("Failed to decode JSON response: %s", e)
                raise

        except requests.RequestException as e:
            logging.error("Request failed on attempt %d: %s", attempt + 1, e)

            # If max retries reached, raise the exception
            if attempt == max_retries - 1:
                raise

        except Exception as e:
            logging.error("Unexpected error: %s", e)
            raise

@mcp.tool()
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
        endpoint = config.ENDPOINTS["threaded"]
        payload = {
            "inside": inside,
            "allsizes": allsizes,
     
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Create thread failed: %s", e)
        raise

@mcp.tool()
def test_connection():
    """Testes die Verbindung zum Fusion 360 Server."""
    try:
        endpoint = config.ENDPOINTS["test_connection"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Test connection failed: %s", e)
        raise

@mcp.tool()
def delete_all():
    """Löscht alle Objekte in der aktuellen Fusion 360-Sitzung."""
    try:
        endpoint = config.ENDPOINTS["delete_everything"]
        headers = config.HEADERS
        send_request(endpoint, {}, headers)
    except Exception as e:
        logging.error("Delete failed: %s", e)
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
        headers = config.HEADERS
        send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Draw holes failed: %s", e)
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
        endpoint = config.ENDPOINTS["witzenmann"]
        payload = {
            "scale": scale,
            "z": z
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Witzenmannlogo failed: %s", e)
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
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Spline failed: %s", e)
        raise

@mcp.tool()
def sweep():
    """
    Benutzt den vorhrig erstellten spline und den davor erstellten krei,
    um eine sweep funktion auszuführen
    """
    try:
        endpoint = config.ENDPOINTS["sweep"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Sweep failed: %s", e)
        raise

@mcp.tool()
def undo():
    """Macht die letzte Aktion rückgängig."""
    try:
        endpoint = config.ENDPOINTS["undo"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Undo failed: %s", e)
        raise

@mcp.tool()
def count():
    """Zählt die Parameter im aktuellen Modell."""
    try:
        endpoint = config.ENDPOINTS["count_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Count failed: %s", e)
        raise

@mcp.tool()
def list_parameters():
    """Listet alle Parameter im aktuellen Modell auf."""
    try:
        endpoint = config.ENDPOINTS["list_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("List parameters failed: %s", e)
        raise

@mcp.tool()
def export_step(name : str):
    """Exportiert das Modell als STEP-Datei."""
    try:
        endpoint = config.ENDPOINTS["export_step"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STEP failed: %s", e)
        raise

@mcp.tool()
def export_stl(name : str):
    """Exportiert das Modell als STL-Datei."""
    try:
        endpoint = config.ENDPOINTS["export_stl"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STL failed: %s", e)
        raise

@mcp.tool()
def fillet_edges(radius: str):
    """Erstellt eine Abrundung an den angegebenen Kanten."""
    try:
        endpoint = config.ENDPOINTS["fillet_edges"]
        payload = {
            "radius": radius
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Fillet edges failed: %s", e)
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
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Change parameter failed: %s", e)
        raise

@mcp.tool()
def draw_cylinder(radius: float , height: float , x: float, y: float, z: float , plane: str="XY"):
    """
    Zeichne einen Zylinder, du kannst du in der XY Ebende arbeiten
    Es gibt Standartwerte
    """

    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_cylinder"]
        data = {
            "radius": radius,
            "height": height,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw cylinder failed: %s", e)
        return None
@mcp.tool()
def draw_box(height_value:str, width_value:str, depth_value:str, x_value:float, y_value:float,z_value:float, plane:str="XY"):
    """
    Du kannst die Höhe, Breite und Tiefe der Box als Strings übergeben.
    Depth ist die Tiefe in z Richtung also wenn gesagt wird die Box soll flach sein,
    dann gibst du einen geringen Wert an!
    Du kannst die Koordinaten x, y,z der Box als Strings übergeben.Gib immer Koordinaten an,
    jene geben den Mittelpunkt der Box an.
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
        headers = config.HEADERS

        data = {
            "height":height_value,
            "width": width_value,
            "depth": depth_value,
            "x" : x_value,
            "y" : y_value,
            "z" : z_value,
            "Plane": plane

        }

        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw box failed: %s", e)
        return None

@mcp.tool()
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
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["shell_body"]
        data = {
            "thickness": thickness,
            "faceindex": faceindex
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Shell body failed: %s", e)
        

@mcp.tool()
def draw_sphere(x: float, y: float, z: float, radius: float):
    """
    Zeichne eine Kugel in Fusion 360
    Du kannst die Koordinaten als Float übergeben
    Du kannst den Radius als Float übergeben
    Beispiel: "XY", "YZ", "XZ"
    Gib immer JSON SO:
    {
        "x":0,
        "y":0,
        "z":0,
        "radius":5
    }
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_sphere"]
        data = {
            "x": x,
            "y": y,
            "z": z,
            "radius": radius
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw sphere failed: %s", e)
        raise


@mcp.tool()
def draw_2d_rectangle(x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, plane: str):
    """
    Zeichne ein 2D-Rechteck in Fusion 360 für loft /Sweep etc.
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_2d_rectangle"]
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

@mcp.tool()
def boolean_operation(operation: str):
    """
    Führe eine boolesche Operation auf dem letzten Körper aus.
    Du kannst die Operation als String übergeben.
    Mögliche Werte sind: "cut", "join", "intersect"
    Wichtig ist, dass du vorher zwei Körper erstellt hast,
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["boolean_operation"]
        data = {
            "operation": operation
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Boolean operation failed: %s", e)
        raise


      
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
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_lines"]
        data = {
            "points": points,
            "plane": plane
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw lines failed: %s", e)

@mcp.tool()
def extrude(value: float):
    """Extrudiert die letzte Skizze um einen angegebenen Wert."""
    try:
        url = config.ENDPOINTS["extrude"]
        data = {
            "value": value
        }
        data = json.dumps(data)
        response = requests.post(url, data, headers=config.HEADERS)
        return response.json()
    except requests.RequestException as e:
        logging.error("Extrude failed: %s", e)
        raise
@mcp.tool()
def extrude_thin(thickness :float, distance : float):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst schöne Hohlkörper damit erstellen
    :param thickness: Die Dicke der Wand in mm
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["extrude_thin"]
        data = {
            "thickness": thickness,
            "distance": distance
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Extrude thin failed: %s", e)
        raise

@mcp.tool()
def cut_extrude(depth :float):
    """
    Du kannst die Tiefe des Schnitts als Float übergeben
    :param depth: Die Tiefe des Schnitts in mm
    depth muss negativ sein ganz wichtig!
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["cut_extrude"]
        data = {
            "depth": depth
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Cut extrude failed: %s", e)
        raise
    
@mcp.tool()
def revolve(angle : float):
    """
    Sobald du dieses tool aufrufst wird der nutzer gebeten in Fusion ein profil
    auszuwählen und dann eine Achse.
    Wir übergeben den Winkel als Float
    """
    try:
        headers = config.HEADERS    
        endpoint = config.ENDPOINTS["revolve"]
        data = {
            "angle": angle

        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Revolve failed: %s", e)  
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
        endpoint = config.ENDPOINTS["arc"]
        headers = config.HEADERS
        data = {
            "point1": point1,
            "point2": point2,
            "point3": point3,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw arc failed: %s", e)
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
        endpoint = config.ENDPOINTS["draw_one_line"]
        headers = config.HEADERS
        data = {
            "x1": x1,
            "y1": y1,
            "z1": z1,
            "x2": x2,
            "y2": y2,
            "z2": z2,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw one line failed: %s", e)
        raise

@mcp.tool()
def rectangular_pattern(plane: str, quantity_one: float, quantity_two: float, distance_one: float, distance_two: float, axis_one: str, axis_two: str):
    """
    Du kannst ein Rectangular Pattern (Rechteckmuster) erstellen um Objekte in einer rechteckigen Anordnung zu verteilen.
    Du musst zwei Mengen (quantity_one, quantity_two) als Float übergeben,
    zwei Abstände (distance_one, distance_two) als Float übergeben,
    Die beiden Richtungen sind die axen ( axis_one, axis_two) als String ("X", "Y" oder "Z") und die Ebene als String ("XY", "YZ" oder "XZ").
    Aus Gründen musst du distance immer mit einer 10 multiplizieren damit es in Fusion 360 stimmt.
    """
    try:
       
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["rectangular_pattern"]
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
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["circular_pattern"]
        data = {
            "plane": plane,
            "quantity": quantity,
            "axis": axis
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Circular pattern failed: %s", e)
        raise

@mcp.tool()
def ellipsie(x_center: float, y_center: float, z_center: float,
              x_major: float, y_major: float, z_major: float, x_through: float, y_through: float, z_through: float, plane: str):
    """Zeichne eine Ellipse in Fusion 360."""
    try:
        endpoint = config.ENDPOINTS["ellipsie"]
        headers = config.HEADERS
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
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw2Dcircle"]
        data = {
            "radius": radius,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw 2D circle failed: %s", e)
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
        endpoint = config.ENDPOINTS["loft"]
        headers = config.HEADERS
        data = {
            "sketchcount": sketchcount
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Loft failed: %s", e)
        raise




@mcp.prompt()
def weingals():
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


@mcp.prompt()
def magnet():
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


@mcp.prompt()
def dna():
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


@mcp.prompt()
def flansch():
    return """
    SCHRITT 1: 
    - Benutze Tool: draw_cylinder
    - Denk dir sinnvolle Maße aus (z.B. Radius: 5, Höhe: 1)
    - Position: x=0, y=0, z=0
    - Ebene: XY
    
    SCHRITT 2: Ln
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


@mcp.prompt()
def vase():
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


@mcp.prompt()
def teil():
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


@mcp.prompt()
def kompensator():
    prompt = """
                Bau einen Kompensator in Fusion 360 mit dem MCP: Lösche zuerst alles.
                Erstelle dann ein dünnwandiges Rohr: Zeichne einen 2D-Kreis mit Radius 5 in der XY-Ebene bei z=0, 
                extrudiere ihn thin mit distance 10 und thickness 0.1. Füge dann 8 Ringe nacheinander übereinander hinzu (Erst Kreis dann Extrusion 8 mal): Für jeden Ring in
                den Höhen z=1 bis z=8 zeichne einen 2D-Kreis mit Radius 5.1 in der XY-Ebene und extrudiere ihn thin mit distance 0.5 und thickness 0.5.
                Verwende keine boolean operations, lass die Ringe als separate Körper. Runde anschließend die Kanten mit Radius 0.2 ab.
                Mache schnell!!!!!!
    
                """
    return prompt




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )
    args = parser.parse_args()

    mcp.run(transport=args.server_type)
