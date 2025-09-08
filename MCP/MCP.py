import adsk.core, adsk.fusion, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import time







ModelParameterSnapshot = []
httpd = None
_polling_interval = 0.1  # Sekunden, alle 0,1 Sekunden aktualisieren
_stop_polling = False
changeParam = None
Box = None # Am Anfang keine Box deswegen halt NOne
newParam = None # Variable für neuen Parameter, falls ein neuer Parameter hinzugefügt werden soll
# #################
# Box bauen


def draw_Box(design,ui):
    try:
        global Box
        rootComp = design.rootComponent #Holen der Rotkomponente
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane #einfac xy Ebene holen


        sketch = sketches.add(xyPlane) # Einen neuen Sketch auf der xy Ebene erstellen
        lines = sketch.sketchCurves.sketchLines
        rect = lines.addCenterPointRectangle(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(5,5,0)) #Koordinaten des Rechtecks
        prof = sketch.profiles.item(0)



        extrudes = rootComp.features.extrudeFeatures # Muss man so machen um die Metoden von ExtrudeFeatures zu benutzen, die braucuhen wir um die Box zu extrudieren (3D)
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(5)
        extInput.setDistanceExtent(False, distance)
        extrude = extrudes.add(extInput)
        


        Box = None #Box wieder auf None setzen, damit die Box nur einmal gebaut wird, sonst stürzt Fusion ab. und damit man nochmal eine Box bauen kann

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

##################################
# Parameter aus Fusion holen
##################################
def get_model_parameters(design):
    model_params = []
    user_params = design.userParameters

    for param in design.allParameters:
        is_user_param = False
        for i in range(user_params.count):
            if user_params.item(i) == param:
                is_user_param = True
                break
        if not is_user_param:
           
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
    changeParam = design.allParameters.itemByName(name)
    changeParam.expression = value



##################################
# HTTP Request Handler
##################################
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Hier schreibe wir die verschiedenen Endpoits rein
        Es handelt sich hier um GET Requests, also nur Daten abfragen
        
        """
        try:
            
            global ModelParameterSnapshot
            global Box
            if self.path == '/count_parameters':
                count = len(ModelParameterSnapshot)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"user_parameter_count": count}).encode('utf-8'))

            elif self.path == '/list_parameters':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ModelParameter": ModelParameterSnapshot}).encode('utf-8'))


            #TODO GEHT NOCH NICHT!!!
            elif self.path == '/Box': 
                Box = True #Setzen des globalen Parameters um die polling zu "aktivieren"
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"Boxstaturs": "Box wurde erfolgreich erstellt ;)"} ).encode('utf-8'))

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
        Hier machen wir den Push Request rein
        Das Ziel ist eine Route die einen Parameter ändert nach Namen
        Der User soll in der Lage sein einen Parameter zu ändern indem er einen HTTP Request mit dem Parameternamen und dem neuen Wert sendet
        Den Namen und den Wert holen wir aus der URL

        """


        try:
            global changeParam, newParam
            if self.path.startswith('/set_parameter'):

                content_length = int(self.headers['Content-Length']) 
                post_data = self.rfile.read(content_length) # Daten lesen die vom MCP Client gesendet wurden
                data = json.loads(post_data)

                #Auslesen des Namens und des neuen Wertesn
                name = data.get('name')
                value = data.get('value')
                changeParam = name # Setzen des globalen Parameters der geändert werden soll
                newParam = value   # Setzen des neuen Wertes der gesetzt werden soll
                if name and value:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": f"Parameter {name} wird auf {value} gesetzt."}).encode('utf-8'))




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
    Hier kommen alle Funktionen rein, die regelmäßig im Main-Thread ausgeführt werden müssen also 
    Funktionen die auf Parameter zugreifen oder die Fusion API verwenden
    Das ist notwendig, da die Fusion API nicht threadsicher ist, was bedeutet, dass sie nur im Hauptthread aufgerufen werden darf
    Wenn wir unsere Daten nur im Hauptthread aktualisieren, werden sie sich nicht live aktualisieren, wenn wir in Fusion Parameter ändern
    Polling ist eine Methode, bei der in regelmäßigen Abständen überprüft wird, ob sich etwas geändert hat
    """
    global ModelParameterSnapshot, _stop_polling, changeParam, newParam, Box
    while not _stop_polling:
        try:
            ModelParameterSnapshot = get_model_parameters(design)
            if changeParam and newParam:
                set_parameter(design, ui, changeParam, newParam)
                changeParam = None
                newParam = None
            if Box :
                draw_Box(design,ui)
                Box = None
        except:
            pass
        time.sleep(_polling_interval)





##Add-In Event Handler
def run(context):
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

