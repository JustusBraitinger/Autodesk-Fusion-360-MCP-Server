import adsk.core, adsk.fusion, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import threading
import json
import time
import queue
from pathlib import Path

ModelParameterSnapshot = []
httpd = None
task_queue = queue.Queue()  # Queue für thread-safe Aktionen

# Event Handler Variablen
app = None
ui = None
design = None
handlers = []
stopFlag = None
myCustomEvent = 'MCPTaskEvent'
customEvent = None

#Event Handler Class
class TaskEventHandler(adsk.core.CustomEventHandler):
    """
    Custom Event Handler for processing tasks from the queue
    This is used, because Fusion 360 API is not thread-safe
    """
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        global task_queue, ModelParameterSnapshot, design, ui
        try:
            if design:
                # Parameter Snapshot aktualisieren
                ModelParameterSnapshot = get_model_parameters(design)
                
                # Task-Queue abarbeiten
                while not task_queue.empty():
                    try:
                        task = task_queue.get_nowait()
                        self.process_task(task)
                    except queue.Empty:
                        break
                    except Exception as e:
                        if ui:
                            ui.messageBox(f"Task-Fehler: {str(e)}")
                        continue
                        
        except Exception as e:

            pass
    
    def process_task(self, task):
        """Verarbeitet eine einzelne Task"""
        global design, ui
        
        if task[0] == 'set_parameter':
            set_parameter(design, ui, task[1], task[2])
        elif task[0] == 'draw_box':
            
            draw_Box(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
            
        elif task[0] == 'draw_witzenmann':
            draw_Witzenmann(design, ui, task[1],task[2])
        elif task[0] == 'export_stl':
            FilePath = r"C:\Users\justu\Desktop\FusioSTL\testSTL.stl"
            export_as_STL(design, ui, FilePath)
        elif task[0] == 'fillet_edges':
            fillet_edges(design, ui, task[1])
        elif task[0] == 'export_step':
            FilePath = r"C:\Users\justu\Desktop\FusioSTL\testSTEP.step"
            export_as_STEP(design, ui, FilePath)
        elif task[0] == 'draw_cylinder':
            draw_cylinder(design, ui, task[1], task[2], task[3], task[4], task[5],task[6])
        elif task[0] == 'shell_body':
            shell_existing_body(design, ui, task[1], task[2])
        elif task[0] == 'undo':
            undo(design, ui)
        elif task[0] == 'draw_lines':
            draw_lines(design, ui, task[1], task[2])
        elif task[0] == 'extrude_last_sketch':
            extrude_last_sketch(design, ui, task[1])
        elif task[0] == 'revolve_profile':
            # 'rootComp = design.rootComponent
            # sketches = rootComp.sketches
            # sketch = sketches.item(sketches.count - 1)  # Letzter Sketch
            # axisLine = sketch.sketchCurves.sketchLines.item(0)  # Erste Linie als Achse'
            revolve_profile(design, ui,  task[1])        
        elif task[0] == 'arc':
            arc(design, ui, task[1], task[2], task[3], task[4],task[5])
        elif task[0] == 'draw_one_line':
            draw_one_line(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
        elif task[0] == 'holes': #task format: ('holes', points, width, depth, through, faceindex)
            # task[3]=depth, task[4]=through, task[5]=faceindex
            holes(design, ui, task[1], task[2], task[3], task[4])
        elif task[0] == 'circle':
            draw_circle(design, ui, task[1], task[2], task[3], task[4],task[5])
        elif task[0] == 'extrude_thin':
            extrude_thin(design, ui, task[1])
        elif task[0] == 'select_body':
            select_body(design, ui, task[1])
        elif task[0] == 'select_sketch':
            select_sketch(design, ui, task[1])
        elif task[0] == 'spline':
            spline(design, ui, task[1], task[2])
        elif task[0] == 'sweep':
            sweep(design, ui)
        elif task[0] == 'cut_extrude':
            cut_extrude(design,ui,task[1])
        elif task[0] == 'circular_pattern':
            circular_pattern(design,ui,task[1],task[2],task[3])


class TaskThread(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        # Alle 200ms Custom Event feuern für Task-Verarbeitung
        while not self.stopped.wait(0.2):
            try:
                app.fireCustomEvent(myCustomEvent, json.dumps({}))
            except:
                break



###Geometry Functions######
def draw_Box(design, ui, height, width, depth,x,y,z, plane=None):
    """
    Draws Box with given dimensions height, width, depth at position (x,y,z)
    z creates an offset construction plane
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        # Choose base plane based on parameter
        if plane == 'XZ':
            basePlane = rootComp.xZConstructionPlane
        elif plane == 'YZ':
            basePlane = rootComp.yZConstructionPlane
        else:
            basePlane = rootComp.xYConstructionPlane
        
        # Create offset plane at z if z != 0
        if z != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)
        
        lines = sketch.sketchCurves.sketchLines
        # addCenterPointRectangle: (center, corner-relative-to-center)
        lines.addCenterPointRectangle(
            adsk.core.Point3D.create(x, y, 0),
            adsk.core.Point3D.create(x + width/2, y + height/2, 0)
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
def draw_circle(design, ui, radius, x, y, z, plane="XY"):
    """
    Draws a circle with given radius at position (x,y) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
    
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(adsk.core.Point3D.create(x, y, z), radius)
    except:
        if ui:
            ui.messageBox('Failed draw_circle:\n{}'.format(traceback.format_exc()))



def draw_sphere(design, ui, radius, x, y, z):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sketch = sketches.add(rootComp.xYConstructionPlane)
    


def draw_Witzenmann(design, ui,scaling,z):
    """
    Draws Witzenmannlogo 
    can be scaled with scaling factor to make it bigger or smaller
    The z Position can be adjusted with z parameter
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        points1 = [
            (8.283*scaling,10.475*scaling,z),(8.283*scaling,6.471*scaling,z),(-0.126*scaling,6.471*scaling,z),(8.283*scaling,2.691*scaling,z),
            (8.283*scaling,-1.235*scaling,z),(-0.496*scaling,-1.246*scaling,z),(8.283*scaling,-5.715*scaling,z),(8.283*scaling,-9.996*scaling,z),
            (-8.862*scaling,-1.247*scaling,z),(-8.859*scaling,2.69*scaling,z),(-0.639*scaling,2.69*scaling,z),(-8.859*scaling,6.409*scaling,z),
            (-8.859*scaling,10.459*scaling,z)
        ]
        for i in range(len(points1)-1):
            start = adsk.core.Point3D.create(points1[i][0], points1[i][1],points1[i][2])
            end   = adsk.core.Point3D.create(points1[i+1][0], points1[i+1][1],points1[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end) # Verbindungslinie zeichnen
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points1[-1][0],points1[-1][1],points1[-1][2]),
            adsk.core.Point3D.create(points1[0][0],points1[0][1],points1[0][2])
        )

        points2 = [(-3.391*scaling,-5.989*scaling,z),(5.062*scaling,-10.141*scaling,z),(-8.859*scaling,-10.141*scaling,z),(-8.859*scaling,-5.989*scaling,z)]
        for i in range(len(points2)-1):
            start = adsk.core.Point3D.create(points2[i][0], points2[i][1],points2[i][2])
            end   = adsk.core.Point3D.create(points2[i+1][0], points2[i+1][1],points2[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points2[-1][0], points2[-1][1],points2[-1][2]),
            adsk.core.Point3D.create(points2[0][0], points2[0][1],points2[0][2])
        )

        extrudes = rootComp.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(2.0*scaling)
        for i in range(sketch.profiles.count):
            prof = sketch.profiles.item(i)
            extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False,distance)
            extrudes.add(extrudeInput)

    except:
        if ui:
            ui.messageBox('Failed draw_Witzenmann:\n{}'.format(traceback.format_exc()))
##############################################################################################
###2D Geometry Functions######

def spline(design, ui, points, plane="XY"):
    """
    Draws a spline through the given points on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        
        splinePoints = adsk.core.ObjectCollection.create()
        for point in points:
            splinePoints.add(adsk.core.Point3D.create(point[0], point[1], point[2]))
        
        sketch.sketchCurves.sketchFittedSplines.add(splinePoints)
    except:
        if ui:
            ui.messageBox('Failed draw_spline:\n{}'.format(traceback.format_exc()))





def arc(design,ui,point1,point2,points3,plane = "XY",connect = False):
    """
    This creates arc between two points on the specified plane
    """
    try:
        rootComp = design.rootComponent #Holen der Rotkomponente
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane 
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            xyPlane = rootComp.xYConstructionPlane 

            sketch = sketches.add(xyPlane)
        start  = adsk.core.Point3D.create(point1[0],point1[1],point1[2])
        alongpoint    = adsk.core.Point3D.create(point2[0],point2[1],point2[2])
        endpoint =adsk.core.Point3D.create(points3[0],points3[1],points3[2])
        arcs = sketch.sketchCurves.sketchArcs
        arc = arcs.addByThreePoints(start, alongpoint, endpoint)
        if connect:
            startconnect = adsk.core.Point3D.create(start.x, start.y, start.z)
            endconnect = adsk.core.Point3D.create(endpoint.x, endpoint.y, endpoint.z)
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(startconnect, endconnect)
            connect = False
        else:
            lines = sketch.sketchCurves.sketchLines

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def draw_lines(design,ui, points,Plane = "XY"):
    """
    User input: points = [(x1,y1), (x2,y2), ...]
    Plane: "XY", "XZ", "YZ"
    Draws lines between the given points on the specified plane
    Connects the last point to the first point to close the shape
    """
    try:
        rootComp = design.rootComponent #Holen der Rotkomponente
        sketches = rootComp.sketches
        if Plane == "XY":
            xyPlane = rootComp.xYConstructionPlane 
            sketch = sketches.add(xyPlane)
        elif Plane == "XZ":
            xZPlane = rootComp.xZConstructionPlane
            sketch = sketches.add(xZPlane)
        elif Plane == "YZ":
            yZPlane = rootComp.yZConstructionPlane
            sketch = sketches.add(yZPlane)
        for i in range(len(points)-1):
            start = adsk.core.Point3D.create(points[i][0], points[i][1], 0)
            end   = adsk.core.Point3D.create(points[i+1][0], points[i+1][1], 0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points[-1][0],points[-1][1],0),
            adsk.core.Point3D.create(points[0][0],points[0][1],0) #
        ) # Verbindet den ersten und letzten Punkt

    except:
        if ui :
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def draw_one_line(design, ui, x1, y1, z1, x2, y2, z2, plane="XY"):
    """
    Draws a single line between two points (x1, y1, z1) and (x2, y2, z2) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    This function does not add a new sketch it is designed to be used after arc 
    This is how we can make half circles and extrude them

    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)
        
        start = adsk.core.Point3D.create(x1, y1, 0)
        end = adsk.core.Point3D.create(x2, y2, 0)
        sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



#################################################################################



###3D Geometry Functions######



def sweep(design,ui):
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sweeps = rootComp.features.sweepFeatures

        profsketch = sketches.item(sketches.count - 2)  # Letzter Sketch
        prof = profsketch.profiles.item(0) # Letztes Profil im Sketch also der Kreis
        pathsketch = sketches.item(sketches.count - 1) # take the last sketch as path
        # collect all sketch curves in an ObjectCollection
        pathCurves = adsk.core.ObjectCollection.create()
        for i in range(pathsketch.sketchCurves.count):
            pathCurves.add(pathsketch.sketchCurves.item(i))

    
        path = adsk.fusion.Path.create(pathCurves, 0) # connec
        sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        sweeps.add(sweepInput)


def extrude_last_sketch(design, ui, value,taperangle=0):
    """
    Just extrudes the last sketch by the given value
    """
    try:
        deg = adsk.core.ValueInput.createByString(f"{taperangle} deg")
        rootComp = design.rootComponent 
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)  # Letzter Sketch
        prof = sketch.profiles.item(0)  # Erstes Profil im Sketch
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(value)
        extrudeInput.setDistanceExtent(False, distance)
        extrudes.add(extrudeInput)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

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

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
def revolve_profile(design, ui,  angle=360):
    """
    This function revolves already existing sketch with drawn lines from the function draw_lines
    around the given axisLine by the specified angle (default is 360 degrees).
    """
    try:
        rootComp = design.rootComponent
        ui.messageBox('Select a profile to revolve.')
        profile = ui.selectEntity('Select a profile to revolve.', 'Profiles').entity
        ui.messageBox('Select sketch line for axis.')
        axis = ui.selectEntity('Select sketch line for axis.', 'SketchLines').entity
        operation = adsk.fusion.FeatureOperations.NewComponentFeatureOperation
        revolveFeatures = rootComp.features.revolveFeatures
        input = revolveFeatures.createInput(profile, axis, operation)
        input.setAngleExtent(False, adsk.core.ValueInput.createByString(str(angle) + ' deg'))
        revolveFeature = revolveFeatures.add(input)



    except:
        if ui:
            ui.messageBox('Failed revolve_profile:\n{}'.format(traceback.format_exc()))

##############################################################################################

###Selection Functions######


def circular_pattern(design, ui, quantity, axis, plane):
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        circularFeats = rootComp.features.circularPatternFeatures
        body = rootComp.bRepBodies.item(0)
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(body)
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)    
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        
        if axis == "Y":
            yAxis = rootComp.yConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, yAxis)
        elif axis == "X":
            xAxis = rootComp.xConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, xAxis)
        elif axis == "Z":
            zAxis = rootComp.zConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, zAxis)

        circularFeatInput.quantity = adsk.core.ValueInput.createByReal((quantity))
        circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
        circularFeatInput.isSymmetric = False
        circularFeats.add(circularFeatInput)
        
        

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))




def undo(design, ui):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        cmd = ui.commandDefinitions.itemById('UndoCommand')
        cmd.execute()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))





def export_as_STEP(design, ui, FilePath):
    try:
        exportMgr = design.exportManager
        # Absoluter Pfad, r"" für Backslashes
        if not FilePath:
            desktop = Path.home() / "Desktop"
            directories = desktop / "FusionExports"
            directories.mkdir(parents=True, exist_ok=True)
            stepOptions = exportMgr.createSTEPExportOptions(str(directories / "Fusion.step"))
        else:
            stepOptions = exportMgr.createSTEPExportOptions(FilePath)
        res = exportMgr.execute(stepOptions)
        if res:
            ui.messageBox(f"Exported STEP to: {FilePath}")
        else:
            ui.messageBox("STEP export failed")
    except:
        if ui:
            ui.messageBox('Failed export_as_STEP:\n{}'.format(traceback.format_exc()))

def cut_extrude(design,ui,depth):
    try:
        rootComp = design.rootComponent 
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)  # Letzter Sketch
        prof = sketch.profiles.item(0)  # Erstes Profil im Sketch
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof,adsk.fusion.FeatureOperations.CutFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extrudeInput.setDistanceExtent(False, distance)
        extrudes.add(extrudeInput)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def extrude_thin(design, ui, thickness=0.5):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    
    #ui.messageBox('Select a face for the extrusion.')
    #selectedFace = ui.selectEntity('Select a face for the extrusion.', 'Profiles').entity
    selectedFace = sketches.item(sketches.count - 1).profiles.item(0)
    exts = rootComp.features.extrudeFeatures
    extInput = exts.createInput(selectedFace, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Center,
                            adsk.core.ValueInput.createByReal(1))

    distanceExtent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(5))
    extInput.setOneSideExtent(distanceExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

    ext = exts.add(extInput)


def draw_cylinder(design, ui, radius, height, x,y,z,plane = "XY"):
    """
    Draws a cylinder with given radius and height at position (x,y,z)
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(xyPlane)

        center = adsk.core.Point3D.create(x, y, z)
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

def holes(design, ui, points, width=1.0,distance = 1.0,faceindex=0):
    """
    Create one or more holes on a selected face.
    """
   
    try:
        rootComp = design.rootComponent
        holes = rootComp.features.holeFeatures
        sketches = rootComp.sketches
        
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("Keine Bodies gefunden.")
            return
        entities = adsk.core.ObjectCollection.create()
        entities.add(latest_body.faces.item(faceindex))
        sk = sketches.add(latest_body.faces.item(faceindex))# create sketch on faceindex face

        tipangle = 90.0
        for i in range(len(points)):
            holePoint = sk.sketchPoints.add(adsk.core.Point3D.create(points[i][0], points[i][1], 0))
            tipangle = adsk.core.ValueInput.createByString('180 deg')
            holedistance = adsk.core.ValueInput.createByReal(distance)
        
            holeDiam = adsk.core.ValueInput.createByReal(width)
            holeInput = holes.createSimpleInput(holeDiam)
            holeInput.tipAngle = tipangle
            holeInput.setPositionBySketchPoint(holePoint)
            holeInput.setDistanceExtent(holedistance)

        # Add the hole
            holes.add(holeInput)
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



def select_body(design,ui,Bodyname):
    try: 
        rootComp = design.rootComponent 
        target_body = rootComp.bRepBodies.itemByName(Bodyname)
        if target_body is None:
            ui.messageBox(f"Body with the name:  '{Bodyname}' could not be found.")

        return target_body

    except : 
        if ui :
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def select_sketch(design,ui,Sketchname):
    try: 
        rootComp = design.rootComponent 
        target_sketch = rootComp.sketches.itemByName(Sketchname)
        if target_sketch is None:
            ui.messageBox(f"Sketch with the name:  '{Sketchname}' could not be found.")

        return target_sketch

    except : 
        if ui :
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# HTTP Server######
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

            elif path == '/undo':
                task_queue.put(('undo',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Undo wird ausgeführt"}).encode('utf-8'))

            elif path == '/Box':
                height = float(data.get('height',5))
                width = float(data.get('width',5))
                depth = float(data.get('depth',5))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                Plane = data.get('plane',None)  # 'XY', 'XZ', 'YZ' or None

                task_queue.put(('draw_box', height, width, depth,x,y,z, Plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Box wird erstellt"}).encode('utf-8'))

            elif path == '/Witzenmann':
                scale = data.get('scale',1.0)
                z = float(data.get('z',0))
                task_queue.put(('draw_witzenmann', scale,z))

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
                radius = float(data.get('radius'))
                height = float(data.get('height'))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_cylinder', radius, height, x, y,z, plane))
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

            elif path == '/draw_lines':
                points = data.get('points', [])
                Plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_lines', points, Plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Lines werden erstellt"}).encode('utf-8'))
            
            elif path == '/extrude_last_sketch':
                value = float(data.get('value',1.0)) #1.0 as default
                task_queue.put(('extrude_last_sketch', value))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Letzter Sketch wird extrudiert"}).encode('utf-8'))
                
            elif path == '/revolve':
                angle = float(data.get('angle',360)) #360 as default
                #axis = data.get('axis','X')  # 'X', 'Y', 'Z'
                task_queue.put(('revolve_profile', angle))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Profil wird revolviert"}).encode('utf-8'))
            elif path == '/arc':
                point1 = data.get('point1', [0,0])
                point2 = data.get('point2', [1,1])
                point3 = data.get('point3', [2,0])
                connect = bool(data.get('connect', False))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('arc', point1, point2, point3, connect, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Arc wird erstellt"}).encode('utf-8'))
            
            elif path == '/draw_one_line':
                x1 = float(data.get('x1',0))
                y1 = float(data.get('y1',0))
                z1 = float(data.get('z1',0))
                x2 = float(data.get('x2',1))
                y2 = float(data.get('y2',1))
                z2 = float(data.get('z2',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_one_line', x1, y1, z1, x2, y2, z2, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Line wird erstellt"}).encode('utf-8'))
            
            elif path == '/holes':
                points = data.get('points', [[0,0]])
                width = float(data.get('width', 1.0))
                faceindex = int(data.get('faceindex', 0))
                distance = data.get('depth', None)
                if distance is not None:
                    distance = float(distance)
                through = bool(data.get('through', False))
                task_queue.put(('holes', points, width, distance,  faceindex))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                
                self.wfile.write(json.dumps({"message": "Loch wird erstellt"}).encode('utf-8'))

            elif path == '/create_circle':
                radius = float(data.get('radius',1.0))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('circle', radius, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Circle wird erstellt"}).encode('utf-8'))

            elif path == '/extrude_thin':
                thickness = float(data.get('thickness',0.5)) #0.5 as default
                task_queue.put(('extrude_thin', thickness))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Thin Extrude wird erstellt"}).encode('utf-8'))

            elif path == '/select_body':
                name = str(data.get('name', ''))
                task_queue.put(('select_body', name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Body wird ausgewählt"}).encode('utf-8'))

            elif path == '/select_sketch':
                name = str(data.get('name', ''))
                task_queue.put(('select_sketch', name))
       
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sketch wird ausgewählt"}).encode('utf-8'))

            elif path == '/sweep':
                # enqueue a tuple so process_task recognizes the command
                task_queue.put(('sweep',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sweep wird erstellt"}).encode('utf-8'))
            
            elif path == '/spline':
                points = data.get('points', [])
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('spline', points, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Spline wird erstellt"}).encode('utf-8'))

            elif path == '/cut_extrude':
                depth = float(data.get('depth',1.0)) #1.0 as default
                task_queue.put(('cut_extrude', depth))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cut Extrude wird erstellt"}).encode('utf-8'))
            
            elif path == '/circular_pattern':
                quantity = float(data.get('quantity',))
                axis = str(data.get('axis',"X"))
                plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                task_queue.put(('circular_pattern',quantity,axis,plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cirular Pattern wird erstellt"}).encode('utf-8'))


     
            
            else:
                self.send_error(404,'Not Found')

        except Exception as e:
            self.send_error(500,str(e))

def run_server():
    global httpd
    server_address = ('localhost',5000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()


def run(context):
    global app, ui, design, handlers, stopFlag, customEvent
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

        # Custom Event registrieren
        customEvent = app.registerCustomEvent(myCustomEvent) #Every 200ms we create a custom event which doesnt interfere with Fusion main thread
        onTaskEvent = TaskEventHandler() #If we have tasks in the queue, we process them in the main thread
        customEvent.add(onTaskEvent) # Here we add the event handler
        handlers.append(onTaskEvent)

        # Task Thread starten
        stopFlag = threading.Event()
        taskThread = TaskThread(stopFlag)
        taskThread.daemon = True
        taskThread.start()

        ui.messageBox(f"Fusion HTTP Add-In gestartet! Port 5000.\nParameter geladen: {len(ModelParameterSnapshot)} Modellparameter")

        # HTTP-Server starten
        threading.Thread(target=run_server, daemon=True).start()

    except:
        try:
            ui.messageBox('Fehler im Add-In:\n{}'.format(traceback.format_exc()))
        except:
            pass




def stop(context):
    global stopFlag, httpd, task_queue, handlers, app, customEvent
    
    # Stop the task thread
    if stopFlag:
        stopFlag.set()

    # Clean up event handlers
    for handler in handlers:
        try:
            if customEvent:
                customEvent.remove(handler)
        except:
            pass
    
    handlers.clear()

    # Clear the queue without processing (avoid freezing)
    while not task_queue.empty():
        try:
            task_queue.get_nowait() 
            if task_queue.empty(): 
                break
        except:
            break

    # Stop HTTP server
    if httpd:
        try:
            httpd.shutdown()
        except:
            pass

  
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
