import adsk.core, adsk.fusion, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import time

"""
Ideen für die Zukunft:
- Löschen von Parametern
- Hinzufügen von Parametern
- Exportieren von Modellen (STL, STEP, etc.)
- HTTPs Unterstützung"""





ModelParameterSnapshot = []
httpd = None
_polling_interval = 0.1  # Sekunden, alle 0,1 Sekunden aktualisieren
_stop_polling = False
changeParam = None
Box = None # Am Anfang keine Box deswegen halt NOne
newParam = None # Variable für neuen Parameter, falls ein neuer Parameter hinzugefügt werden soll
BoxHeight = 5
BoxWidth = 5
BoxDepth = 5
Witzenmann = None
# #################
# Box bauen


def draw_Witzenmann(design, ui):


    try:
        global Witzenmann
    

        # Neues Design erstellen
        
        rootComp = design.rootComponent

        # Neues Sketch auf XY-Ebene
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        points1 = [
            (8.283,10.475),
            (8.283,6.471),
            (-0.126,6.471),
            (8.283,2.691),
            (8.283,-1.235),
            (-0.496,-1.246),
            (8.283,-5.715),
            (8.283,-9.996),
            (-8.862,-1.247),
            (-8.859,2.69),
            (-0.639,2.69),
            (-8.859,6.409),
            (-8.859,10.459)
        ]

        for i in range(len(points1)-1):
            start = adsk.core.Point3D.create(points1[i][0], points1[i][1], 0)
            end   = adsk.core.Point3D.create(points1[i+1][0], points1[i+1][1], 0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        # Letzten Punkt mit dem ersten verbinden
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points1[-1][0], points1[-1][1], 0),
            adsk.core.Point3D.create(points1[0][0], points1[0][1], 0)
        )

        points2 = [
            (-3.391,-5.989),
            (5.062,-10.141),
            (-8.859,-10.141),
            (-8.859,-5.989)
        ]

        for i in range(len(points2)-1):
            start = adsk.core.Point3D.create(points2[i][0], points2[i][1], 0)
            end   = adsk.core.Point3D.create(points2[i+1][0], points2[i+1][1], 0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        # Letzten Punkt mit dem ersten verbinden
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points2[-1][0], points2[-1][1], 0),
            adsk.core.Point3D.create(points2[0][0], points2[0][1], 0)
        )

     
        extrudes = rootComp.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(2.0)

        # Extrudiere alle Profile
        for i in range(sketch.profiles.count):
            prof = sketch.profiles.item(i)
            extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False, distance)
            extrudes.add(extrudeInput)

        Witzenmann = None


    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



def draw_Box(design,ui, BoxHeight, BoxWidth,BoxDepth):
    """
    Erstellung einer Box in drei Schritte, ( Fast unbegrenzt erweiterbar)
    Standartmäßig 5x5x5 Box
    1. Neuer Sketch auf der xy Ebene
    2. Rechteck zeichnen
    3. Extrudieren des Rechtecks zu einer Box (3D)
    """
    try:

        global Box
        rootComp = design.rootComponent #Holen der Rotkomponente
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane #einfac xy Ebene holen


        sketch = sketches.add(xyPlane) # Einen neuen Sketch auf der xy Ebene erstellen
        lines = sketch.sketchCurves.sketchLines
        rect = lines.addCenterPointRectangle(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(BoxWidth/2, BoxHeight/2, 0)) #Koordinaten des Rechtecks
        prof = sketch.profiles.item(0)
        



        extrudes = rootComp.features.extrudeFeatures # Muss man so machen um die Metoden von ExtrudeFeatures zu benutzen, die braucuhen wir um die Box zu extrudieren (3D)
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(BoxDepth)
        extInput.setDistanceExtent(False, distance)
        extrude = extrudes.add(extInput)
        


        Box = None #Box wieder auf None setzen, damit die Box nur einmal gebaut wird, sonst stürzt Fusion ab. und damit man nochmal eine Box bauen kann

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))




def export_as_STL(design,ui, FilePath):
    rootComp = design.rootComponent # Hier holen wir die Root-Komponente, also die Hauptkomponente des Modells

    exportMgr = design.exportManager
    stlRootOptions = exportMgr.createSTLExportOptions(rootComp)
    stlRootOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    stlRootOptions.filename = FilePath
    exportMgr.execute(stlRootOptions)
    ui.messageBox(f"Exported STL to: {FilePath}")
##################################
# Parameter aus Fusion holen
##################################
def get_model_parameters(design):
    """
    Es gibt keine direkte Methode um nur die Modellparameter zu holen
    Deswegen nehmen wir alle Parameter und filtern die UserParameter raus
    ModelParameter sind alle Parameter die nicht vom User erstellt wurden

    Rückgabe:
    Liste von Dictionaries mit den Keys: Name, Wert, Einheit, Expression
    """
    model_params = [] # Liste für die Modellparameter
    user_params = design.userParameters # Alle UserParameter holen um sie mit den anderen zu vergleichen um ModelParameter zu filtern

    for param in design.allParameters: #Iteration über alle Parameter
        is_user_param = False
        for i in range(user_params.count): 
            if user_params.item(i) == param:
                is_user_param = True
                break
        if not is_user_param: # Wenn es kein UserParameter ist dann ist es ein ModelParameter
           
            param_info = {
                "Name": str(param.name),
                "Wert": str(param.value),
                "Einheit": str(param.unit),
                "Expression": str(param.expression) if param.expression else ""
            }
            model_params.append(param_info)
            
    return model_params
##################################
# Parameter ändern bei Name
##################################

def set_parameter(design, ui, name, value):
    """
    Funktion um einen Parameter zu ändern
    Hier dürfen wir auf den Main-Thread zugreifen, da die Funktion im Polling aufgerufen wird
    Input (Parameter):
    name: Name des Parameters der geändert werden soll
    value: Neuer Wert der gesetzt werden soll


    Rückgabe: 
    None, da die Änderung direkt im Design erfolgt
    """
    changeParam = design.allParameters.itemByName(name) 
    changeParam.expression = value



##################################
# HTTP Request Handler
##################################
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Verarbeitet HTTP GET-Anfragen

        Es gibt 2 Routen:
        /count_parameters: Gibt die Anzahl der Modellparameter zurück
        /list_parameters: Gibt eine Liste aller Modellparameter zurück

        Wichtig:
        Hier darf auf keinen Fall Zugriff auf die Fusion API erfolgen, da der HTTP Server in einem eigenen Thread läuft 
        und die Fusion API nicht threadsicher ist.
        Wenn hier zugegriffen wird, stürzt Fusion ab.
        """
        try:
            global ModelParameterSnapshot, Witzenmann
            if self.path == '/count_parameters':
                count = (ModelParameterSnapshot)
    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"user_parameter_count": count}).encode('utf-8'))
            elif self.path == '/list_parameters':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ModelParameter": ModelParameterSnapshot}).encode('utf-8'))
            else:
                self.send_error(404, 'Not Found')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
            self.wfile.write(json.dumps({"error": error_msg}).encode('utf-8'))


    def do_POST(self):
        """
        Verarbeitet HTTP POST-Anfragen

        /set_parameter: Setzt einen Modellparameter
        /Box: Erstellt eine Box mit übergebenen Werten
        """
        try:
            global changeParam, newParam, Box, BoxHeight, BoxWidth, BoxDepth
            if self.path.startswith('/set_parameter'):
                content_length = int(self.headers['Content-Length']) 
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                name = data.get('name')
                value = data.get('value')
                changeParam = name
                newParam = value
                if name and value:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": f"Parameter {name} wird auf {value} gesetzt."}).encode('utf-8'))
            elif self.path == '/Box':
                
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data) if post_data else {}
                Box = True
                try:
                    BoxHeight = float(params.get('height', 5))
                except (ValueError, TypeError):
                    BoxHeight = 5
                try:
                    BoxWidth = float(params.get('width', 5))
                except (ValueError, TypeError):
                    BoxWidth = 5
                try:
                    BoxDepth = float(params.get('depth', 5))
                except (ValueError, TypeError):
                    BoxDepth = 5
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"Boxstatus": "Box wurde erfolgreich erstellt mit den Werten: Höhe = {}, Breite = {}, Tiefe = {}".format(BoxHeight, BoxWidth, BoxDepth)}).encode('utf-8'))
            
            
            elif self.path == '/Witzenmann':
                global Witzenmann
                Witzenmann = True
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"Witzenmannstatus": "Witzenmannlogo wurde erfolgreich erstellt"}).encode('utf-8'))
                

            else:
                self.send_error(404, 'Not Found')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
            self.wfile.write(json.dumps({"error": error_msg}).encode('utf-8'))



##################################
# HTTP Server starten
##################################
def run_server():
    global httpd
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()

##################################
# Polling-Funktion (im Main-Thread)
##################################
def polling_loop(design,ui):
    """
    Hier aktualisieren wir in regelmäßigen Abständen die Liste der Modellparameter

    Aufgaben :
    - Prüfung ob ein Parameter geändert werden soll (changeParam und newParam sind nicht None)
    - Prüfung ob eine Box erstellt werden soll (Box ist nicht None)
    - Aktualisierung der ModelParameterSnapshot Liste
    """
    global ModelParameterSnapshot, _stop_polling, changeParam, newParam, Box, BoxHeight, BoxWidth, BoxDepth, Witzenmann
    while not _stop_polling:
        try:
            ModelParameterSnapshot = get_model_parameters(design)
            if changeParam and newParam:
                set_parameter(design, ui, changeParam, newParam)
                changeParam = None
                newParam = None
            if Box :
                draw_Box(design,ui, BoxHeight, BoxWidth,BoxDepth)
                #Box = None
                #BoxHeight = None
                #BoxWidth = None
                #BoxDepth = None
            if Witzenmann:
                ui.messageBox("Witzenmann-Logo wird gezeichnet!")
                draw_Witzenmann(design,ui)
                Witzenmann = None
        except:
            pass
        time.sleep(_polling_interval)





##Add-In Event Handler
def run(context):
    """
    Hier startet das Add-In

    - Initialer Snapshot der Modellparameter
    - Starten des HTTP Servers im Hintergrund (Thread 1)
    - Starten der Polling-Funktion im Hintergrund (Thread 2)

    
    """


    global _stop_polling
    
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        
        if design is None:
            ui.messageBox("Kein aktives Design geöffnet!")
            return

        # Initialer Snapshot
        ModelParameterSnapshot = get_model_parameters(design)

        ui.messageBox("Fusion HTTP Add-In gestartet! Port 5000.\nParameter geladen: {} Modellparameter".format(len(ModelParameterSnapshot)))
        

        # HTTP-Server im Hintergrund starten
        threading.Thread(target=run_server, daemon=True).start() # Der erste Thread startet den HTTP Server im Hintergrund

        # Polling im Main-Thread starten
        
        def start_polling():
            polling_loop(design,ui) #Dake Copilot ohne das gehts garnet
        # Abfrageroutine im Hintergrund starten (zweiter Thread)
        threading.Thread(target=start_polling, daemon=True).start() # Der zweite Thread startet das Polling im Main-Thread
        
    except:
        try:
            ui.messageBox('Fehler im Add-In:\n{}'.format(traceback.format_exc()))
        except:
            pass

def stop(context):
    global _stop_polling, httpd
    _stop_polling = True

    if httpd:
        try:
            httpd.shutdown()      # stoppt serve_forever()
            httpd.server_close()  # schließt Socket
        except:
            pass
        httpd = None

    try:
        ui = adsk.core.Application.get().userInterface
        ui.messageBox("Fusion HTTP Add-In gestoppt")
    except:
        pass

