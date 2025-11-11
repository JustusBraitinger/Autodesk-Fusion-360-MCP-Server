import requests
from mcp.server.fastmcp import FastMCP
import json
import argparse



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

@mcp.tool()
def draw_holes(points : list,depth : float, width : float,faceindex : int = 0):
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
    url = "http://localhost:5000/holes"
    data = {
        "points": points,
        "width": width,
        "depth": depth,
        "faceindex": faceindex
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    data = response.json()
    return data
@mcp.tool()
def draw_witzenmannlogo(scale : float=1.0, z : float = 1.0):
    """
    Du baust das witzenmann logo
    Du kannst es skalieren
    es ist immer im Mittelpunkt
    Du kannst die Höhe angeben mit z

    :param scale:
    :param z:
    :return:
    """
    data = {
        "scale": scale,
        "z" : z
    }

    url = "http://localhost:5000/Witzenmann"
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    data = response.json()
    return data
@mcp.tool()
def spline(points : list, plane : str):
    """
    Zeichne eine Spline Kurve in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: [[0,0,0],[5,0,0],[5,5,5],[0,5,5],[0,0,0]]
    Es ist essenziell, dass du die Z-Koordinate angibst, auch wenn sie 0 ist
    Wenn nicht explizit danach gefragt ist mache es so, dass die Linien nach oben zeigen
    Du kannst die Ebene als String übergeben
    Es ist essenziell, dass die linien die gleiche ebene haben wie das profil was du sweepen willst
   
    """
    url = "http://localhost:5000/spline"
    data = {
        "points": points,
        "plane": plane
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()

@mcp.tool()
def sweep():
    """
    Benutzt den vorhrig erstellten spline und den davor erstellten kreis um eine sweep funktion auszuführen
    
    
    """
    r = requests.post("http://localhost:5000/sweep")

    data = r.json()

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
    url = "http://localhost:5000/Box"

    data = {
        "height":height_value,
        "width": width_value,
        "depth": depth_value,
        "x" : x_value,
        "y" : y_value,
        "z" : z_value,
        "Plane": plane

    }

    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    return response.json()

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
    url = "http://localhost:5000/shell_body"
    data = {
        "thickness": thickness,
        "faceindex": faceindex,
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
def extrude_thin(thickness :float, distance : float):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst schöne Hohlkörper damit erstellen
    :param thickness: Die Dicke der Wand in mm
    """
    url = "http://localhost:5000/extrude_thin"
    data = {
        "thickness": thickness,
        "distance": distance
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()

@mcp.tool()
def cut_extrude(depth :float):
    """
    Du kannst die Tiefe des Schnitts als Float übergeben
    :param depth: Die Tiefe des Schnitts in mm
    depth muss negativ sein ganz wichtig!
    
    """
    url = "http://localhost:5000/cut_extrude"
    data = {
        "depth": depth
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
    Es wird eine Linie von point1 zu point3 gezeichnet die durch point2 geht also musst du nicht extra eine Linie zeichnen
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
    url = "http://localhost:5000/circular_pattern"
    data = {
        "plane": plane,
        "quantity": quantity,
        "axis": axis
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()



@mcp.tool()
def ellipsie(x_center: float, y_center: float, z_center: float,
              x_major: float, y_major: float, z_major: float, x_through: float, y_through: float, z_through: float, plane: str):
    
    url = "http://localhost:5000/ellipsis"                                       

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
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()





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
    url = "http://localhost:5000/create_circle"
    data = {
        "radius": radius,
        "x": x,
        "y": y,
        "z": z,
        "plane": plane
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()

@mcp.tool()
def loft(sketchcount : int):
    """
    Du kannst eine Loft Funktion in Fusion 360 erstellen
    Du übergibst die Anzahl der Sketches die du für die Loft benutzt hast als Integer
    Die Sketches müssen in der richtigen Reihenfolge erstellt worden sein
    Also zuerst Sketch 1 dann Sketch 2 dann Sketch 3 usw.
    """
    url = "http://localhost:5000/loft"
    data = {
        "sketchcount": sketchcount
    }
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.json()





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

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )
    args = parser.parse_args()

    mcp.run(transport=args.server_type)

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
