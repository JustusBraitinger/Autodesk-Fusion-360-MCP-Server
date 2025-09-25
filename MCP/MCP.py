import adsk.core, adsk.fusion, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import threading
import json
import time
import queue

# ##################################
# Globale Variablen
# ##################################
ModelParameterSnapshot = []
httpd = None
_polling_interval = 0.1  # Sekunden
_stop_polling = False
task_queue = queue.Queue()  # Queue für thread-safe Aktionen

 

def shell_existing_body(design, ui, thickness=0.5, faceindex=0):
    """
    Shells the body on a specified face index with given thickness
    """
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        
        body = rootComp.bRepBodies.item(0)

        entities = adsk.core.ObjectCollection.create()
        entities.add(body.faces.item(faceindex))

        shellFeats = features.shellFeatures
        isTangentChain = False
        shellInput = shellFeats.createInput(entities, isTangentChain)

        thicknessVal = adsk.core.ValueInput.createByReal(thickness)
        shellInput.insideThickness = thicknessVal

        shellInput.shellType = adsk.fusion.ShellTypes.SharpOffsetShellType

        # Ausführen
        shellFeats.add(shellInput)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def export_as_STEP(design, ui, FilePath):
    try:
        exportMgr = design.exportManager
        # Absoluter Pfad, r"" für Backslashes
        stepOptions = exportMgr.createSTEPExportOptions(r"C:\Users\justu\Desktop\FusioSTL\Fusion.step")
        res = exportMgr.execute(stepOptions)
        if res:
            ui.messageBox(f"Exported STEP to: {FilePath}")
        else:
            ui.messageBox("STEP export failed")
    except:
        if ui:
            ui.messageBox('Failed export_as_STEP:\n{}'.format(traceback.format_exc()))



def fillet_edges(design, ui, radius=0.3):
    try:
        rootComp = design.rootComponent

        bodies = rootComp.bRepBodies

        edgeCollection = adsk.core.ObjectCollection.create()
        for body_idx in range(bodies.count):
            body = bodies.item(body_idx)
            for edge_idx in range(body.edges.count):
                edge = body.edges.item(edge_idx)
                edgeCollection.add(edge)

        fillets = rootComp.features.filletFeatures
        radiusInput = adsk.core.ValueInput.createByReal(radius)
        filletInput = fillets.createInput()
        filletInput.isRollingBallCorner = True
        edgeSetInput = filletInput.edgeSetInputs.addConstantRadiusEdgeSet(edgeCollection, radiusInput, True)
        edgeSetInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
        fillets.add(filletInput)
        ui.messageBox('Failasdasdasdasdasded:\n{}'.format(traceback.format_exc()))

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def draw_cylinder(design, ui, radius, height, x,y):
    """
    Draws a cylinder with given radius and height at position (x,y)
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        center = adsk.core.Point3D.create(x, y, 0)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)

        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(height)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)

    except:
        if ui:
            ui.messageBox('Failed draw_cylinder:\n{}'.format(traceback.format_exc()))

def draw_Box(design, ui, height, width, depth,x,y, plane=None):
    """
    Draws Box with given dimensions height, width, depth
    
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        xZPlane = rootComp.xZConstructionPlane
        yZPlane = rootComp.yZConstructionPlane
        if plane == 'XZ':
            sketch = sketches.add(xZPlane)
        elif plane == 'YZ':
            sketch = sketches.add(yZPlane)
        else:
            sketch = sketches.add(xyPlane)
        lines = sketch.sketchCurves.sketchLines
        lines.addCenterPointRectangle(
            adsk.core.Point3D.create(x, y, 0),
            adsk.core.Point3D.create(width/2, height/2, 0)
        )
        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed draw_Box:\n{}'.format(traceback.format_exc()))

def draw_Witzenmann(design, ui):
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        points1 = [
            (8.283,10.475),(8.283,6.471),(-0.126,6.471),(8.283,2.691),
            (8.283,-1.235),(-0.496,-1.246),(8.283,-5.715),(8.283,-9.996),
            (-8.862,-1.247),(-8.859,2.69),(-0.639,2.69),(-8.859,6.409),
            (-8.859,10.459)
        ]
        for i in range(len(points1)-1):
            start = adsk.core.Point3D.create(points1[i][0], points1[i][1],0)
            end   = adsk.core.Point3D.create(points1[i+1][0], points1[i+1][1],0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points1[-1][0],points1[-1][1],0),
            adsk.core.Point3D.create(points1[0][0],points1[0][1],0)
        )

        points2 = [(-3.391,-5.989),(5.062,-10.141),(-8.859,-10.141),(-8.859,-5.989)]
        for i in range(len(points2)-1):
            start = adsk.core.Point3D.create(points2[i][0], points2[i][1],0)
            end   = adsk.core.Point3D.create(points2[i+1][0], points2[i+1][1],0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points2[-1][0], points2[-1][1],0),
            adsk.core.Point3D.create(points2[0][0], points2[0][1],0)
        )

        extrudes = rootComp.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(2.0)
        for i in range(sketch.profiles.count):
            prof = sketch.profiles.item(i)
            extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False,distance)
            extrudes.add(extrudeInput)

    except:
        if ui:
            ui.messageBox('Failed draw_Witzenmann:\n{}'.format(traceback.format_exc()))

def export_as_STL(design, ui, FilePath):
    try:
        rootComp = design.rootComponent
        exportMgr = design.exportManager
        stlRootOptions = exportMgr.createSTLExportOptions(rootComp)
        stlRootOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        stlRootOptions.filename = FilePath
        exportMgr.execute(stlRootOptions)
        ui.messageBox(f"Exported STL to: {FilePath}")
    except:
        if ui:
            ui.messageBox('Failed export_as_STL:\n{}'.format(traceback.format_exc()))

def get_model_parameters(design):
    model_params = []
    user_params = design.userParameters
    for param in design.allParameters:
        if all(user_params.item(i) != param for i in range(user_params.count)):
            model_params.append({
                "Name": str(param.name),
                "Wert": str(param.value),
                "Einheit": str(param.unit),
                "Expression": str(param.expression) if param.expression else ""
            })
    return model_params

def set_parameter(design, ui, name, value):
    try:
        param = design.allParameters.itemByName(name)
        param.expression = value
    except:
        if ui:
            ui.messageBox('Failed set_parameter:\n{}'.format(traceback.format_exc()))


# ##################################
# HTTP Server
# ##################################
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global ModelParameterSnapshot
        try:
            if self.path == '/count_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"user_parameter_count": len(ModelParameterSnapshot)}).encode('utf-8'))
            elif self.path == '/list_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ModelParameter": ModelParameterSnapshot}).encode('utf-8'))
            else:
                self.send_error(404,'Not Found')
        except Exception as e:
            self.send_error(500,str(e))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length',0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data) if post_data else {}
            path = self.path

            # Alle Aktionen in die Queue legen
            if path.startswith('/set_parameter'):
                name = data.get('name')
                value = data.get('value')
                if name and value:
                    task_queue.put(('set_parameter', name, value))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": f"Parameter {name} wird gesetzt"}).encode('utf-8'))

            elif path == '/Box':
                height = float(data.get('height',5))
                width = float(data.get('width',5))
                depth = float(data.get('depth',5))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                Plane = data.get('plane',None)  # 'XY', 'XZ', 'YZ' or None

                task_queue.put(('draw_box', height, width, depth,x,y, Plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Box wird erstellt"}).encode('utf-8'))

            elif path == '/Witzenmann':
                task_queue.put(('draw_witzenmann',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Witzenmann-Logo wird erstellt"}).encode('utf-8'))

            elif path == '/Export_STL':
                task_queue.put(('export_stl', r"C:\Users\justu\Desktop\FusioSTL\Test.stl"))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "STL Export gestartet"}).encode('utf-8'))


            elif path == '/Export_STEP':
                task_queue.put(('export_step', r"C:\Users\justu\Desktop\FusioSTL\Test.step"))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "STEP Export gestartet"}).encode('utf-8'))


            elif path == '/fillet_edges':
                radius = float(data.get('radius',0.3)) #0.3 as default
                task_queue.put(('fillet_edges',radius))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Fillet edges started"}).encode('utf-8'))

            elif path == '/draw_cylinder':
                radius = float(data.get('radius',5))
                height = float(data.get('height',10))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                task_queue.put(('draw_cylinder', radius, height, x, y))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cylinder wird erstellt"}).encode('utf-8'))
            

            elif path == '/shell_body':
                thickness = float(data.get('thickness',0.5)) #0.5 as default
                faceindex = int(data.get('faceindex',0))
                task_queue.put(('shell_body', thickness, faceindex))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Shell body wird erstellt"}).encode('utf-8'))

            else:
                self.send_error(404,'Not Found')

        except Exception as e:
            self.send_error(500,str(e))

def run_server():
    global httpd
    server_address = ('localhost',5000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()

# ##################################
# Polling-Loop im Main-Thread
# ##################################
def polling_loop(design, ui):
    global _stop_polling, ModelParameterSnapshot
    while not _stop_polling:
        try:
            # Parameter Snapshot
            ModelParameterSnapshot = get_model_parameters(design)
            
            # Task-Queue abarbeiten
            while not task_queue.empty():
                task = task_queue.get()
                if task[0] == 'set_parameter':
                    set_parameter(design, ui, task[1], task[2])
                elif task[0] == 'draw_box':
                    draw_Box(design, ui, task[1], task[2], task[3], task[4], task[5])
                elif task[0] == 'draw_witzenmann':
                    draw_Witzenmann(design, ui)
                elif task[0] == 'export_stl':
                    FilePath = r"C:\Users\justu\Desktop\FusioSTL\testSTL.stl"
                    export_as_STL(design, ui, FilePath)
                elif task[0] == 'fillet_edges':
                    fillet_edges(design, ui,task[1])
                elif task[0] == 'export_step':
                    FilePath = r"C:\Users\justu\Desktop\FusioSTL\testSTEP.step"
                    export_as_STEP(design, ui, FilePath)
                elif task[0] == 'draw_cylinder':
                    draw_cylinder(design, ui, task[1], task[2], task[3], task[4])
                elif task[0] == 'shell_body':
                    shell_existing_body(design, ui, task[1], task[2])
        except:
            pass
        time.sleep(_polling_interval)

# ##################################
# Add-In Event Handler
# ##################################
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
        global ModelParameterSnapshot
        ModelParameterSnapshot = get_model_parameters(design)

        ui.messageBox(f"Fusion HTTP Add-In gestartet! Port 5000.\nParameter geladen: {len(ModelParameterSnapshot)} Modellparameter")

        # HTTP-Server starten
        threading.Thread(target=run_server, daemon=True).start()

        # Polling-Loop starten
        threading.Thread(target=lambda: polling_loop(design, ui), daemon=True).start()

    except:
        try:
            ui.messageBox('Fehler im Add-In:\n{}'.format(traceback.format_exc()))
        except:
            pass

def stop(context):
    global _stop_polling, httpd, task_queue
    _stop_polling = True

  
    while not task_queue.empty():
        try:
            task_queue.get_nowait() 
            if task_queue.empty():
                break
            
        except:
            break

  
    if httpd:
        try:
            httpd.shutdown()
            httpd.server_close()
        except:
            pass
        httpd = None

    

   
    try:
        app = adsk.core.Application.get()
        if app:
            ui = app.userInterface
            if ui:
                ui.messageBox("Fusion HTTP Add-In gestoppt")
    except:
        pass
