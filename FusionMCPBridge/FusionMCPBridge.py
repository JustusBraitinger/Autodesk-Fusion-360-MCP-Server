import adsk.core
import adsk.fusion
import adsk.cam
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import queue
import math
import os
import re

# Import CAM module
from . import cam
# Import Tool Library module
from . import tool_library

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
                        
        except Exception:

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

            export_as_STL(design, ui, task[1])
        elif task[0] == 'fillet_edges':
            fillet_edges(design, ui, task[1])
        elif task[0] == 'export_step':

            export_as_STEP(design, ui, task[1])
        elif task[0] == 'draw_cylinder':
            draw_cylinder(design, ui, task[1], task[2], task[3], task[4], task[5],task[6])
        elif task[0] == 'shell_body':
            shell_existing_body(design, ui, task[1], task[2])
        elif task[0] == 'undo':
            undo(design, ui)
        elif task[0] == 'draw_lines':
            draw_lines(design, ui, task[1], task[2])
        elif task[0] == 'extrude_last_sketch':
            extrude_last_sketch(design, ui, task[1],task[2])
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
            extrude_thin(design, ui, task[1],task[2])
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
        elif task[0] == 'offsetplane':
            offsetplane(design,ui,task[1],task[2])
        elif task[0] == 'loft':
            loft(design, ui, task[1])
        elif task[0] == 'ellipsis':
            draw_ellipis(design,ui,task[1],task[2],task[3],task[4],task[5],task[6],task[7],task[8],task[9],task[10])
        elif task[0] == 'draw_sphere':
            create_sphere(design, ui, task[1], task[2], task[3], task[4])
        elif task[0] == 'threaded':
            create_thread(design, ui, task[1], task[2])
        elif task[0] == 'delete_everything':
            delete(design, ui)
        elif task[0] == 'boolean_operation':
            boolean_operation(design,ui,task[1])
        elif task[0] == 'draw_2d_rectangle':
            draw_2d_rect(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
        elif task[0] == 'rectangular_pattern':
            rect_pattern(design,ui,task[1],task[2],task[3],task[4],task[5],task[6],task[7])
        elif task[0] == 'draw_text':
            draw_text(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9],task[10])
        elif task[0] == 'move_body':
            move_last_body(design,ui,task[1],task[2],task[3])
        


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

def draw_text(design, ui, text, thickness,
              x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value,plane="XY"):
    
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
        point_2 = adsk.core.Point3D.create(x_2, y_2, z_2)

        texts = sketch.sketchTexts
        input = texts.createInput2(f"{text}",thickness)
        input.setAsMultiLine(point_1,
                             point_2,
                             adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                             adsk.core.VerticalAlignments.TopVerticalAlignment, 0)
        sketchtext = texts.add(input)
        extrudes = rootComp.features.extrudeFeatures
        
        extInput = extrudes.createInput(sketchtext, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(extrusion_value)
        extInput.setDistanceExtent(False, distance)
        extInput.isSolid = True
        
        # Create the extrusion
        ext = extrudes.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed draw_text:\n{}'.format(traceback.format_exc()))
def create_sphere(design, ui, radius, x, y, z):
    try:
        rootComp = design.rootComponent
        component: adsk.fusion.Component = design.rootComponent
        # Create a new sketch on the xy plane.
        sketches = rootComp.sketches
        
        xyPlane =  rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        # Draw a circle.
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(adsk.core.Point3D.create(x,y,z), radius)
        # Draw a line to use as the axis of revolution.
        lines = sketch.sketchCurves.sketchLines
        axisLine = lines.addByTwoPoints(
            adsk.core.Point3D.create(x - radius, y, z),
            adsk.core.Point3D.create(x + radius, y, z)
        )

        # Get the profile defined by half of the circle.
        profile = sketch.profiles.item(0)
        # Create an revolution input for a revolution while specifying the profile and that a new component is to be created
        revolves = component.features.revolveFeatures
        revInput = revolves.createInput(profile, axisLine, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)
        # Define that the extent is an angle of 2*pi to get a sphere
        angle = adsk.core.ValueInput.createByReal(2*math.pi)
        revInput.setAngleExtent(False, angle)
        # Create the extrusion.
        ext = revolves.add(revInput)
        
        
    except:
        if ui :
            ui.messageBox('Failed create_sphere:\n{}'.format(traceback.format_exc()))





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

def draw_ellipis(design,ui,x_center,y_center,z_center,
                 x_major, y_major,z_major,x_through,y_through,z_through,plane ="XY"):
    """
    Draws an ellipse on the specified plane using three points.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        # Always define the points and create the ellipse
        # Ensure all arguments are floats (Fusion API is strict)
        centerPoint = adsk.core.Point3D.create(float(x_center), float(y_center), float(z_center))
        majorAxisPoint = adsk.core.Point3D.create(float(x_major), float(y_major), float(z_major))
        throughPoint = adsk.core.Point3D.create(float(x_through), float(y_through), float(z_through))
        sketchEllipse = sketch.sketchCurves.sketchEllipses
        ellipse = sketchEllipse.add(centerPoint, majorAxisPoint, throughPoint)
    except:
        if ui:
            ui.messageBox('Failed to draw ellipsis:\n{}'.format(traceback.format_exc()))

def draw_2d_rect(design, ui, x_1, y_1, z_1, x_2, y_2, z_2, plane="XY"):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes

    if plane == "XZ":
        baseplane = rootComp.xZConstructionPlane
        if y_1 and y_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(y_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    elif plane == "YZ":
        baseplane = rootComp.yZConstructionPlane
        if x_1 and x_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(x_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    else:
        baseplane = rootComp.xYConstructionPlane
        if z_1 and z_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)

    rectangles = sketch.sketchCurves.sketchLines
    point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
    points_2 = adsk.core.Point3D.create(x_2, y_2, z_2)
    rectangles.addTwoPointRectangle(point_1, points_2)



def draw_circle(design, ui, radius, x, y, z, plane="XY"):
    
    """
    Draws a circle with given radius at position (x,y,z) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    For XY plane: circle at (x,y) with z offset
    For XZ plane: circle at (x,z) with y offset  
    For YZ plane: circle at (y,z) with x offset
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        # Determine which plane and coordinates to use
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
            # For XZ plane: x and z are in-plane, y is the offset
            if y != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(y)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(x, z, 0)
            
        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
            # For YZ plane: y and z are in-plane, x is the offset
            if x != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(x)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(y, z, 0)
            
        else:  # XY plane (default)
            basePlane = rootComp.xYConstructionPlane
            # For XY plane: x and y are in-plane, z is the offset
            if z != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(z)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(x, y, 0)
    
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(centerPoint, radius)
    except:
        if ui:
            ui.messageBox('Failed draw_circle:\n{}'.format(traceback.format_exc()))




def draw_sphere(design, ui, radius, x, y, z):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sketch = sketches.add(rootComp.xYConstructionPlane)
#USELESS  


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


def move_last_body(design,ui,x,y,z):
    
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        sketches = rootComp.sketches
        moveFeats = features.moveFeatures
        body = rootComp.bRepBodies
        bodies = adsk.core.ObjectCollection.create()
        
        if body.count > 0:
                latest_body = body.item(body.count - 1)
                bodies.add(latest_body)
        else:
            ui.messageBox("Keine Bodies gefunden.")
            return

        vector = adsk.core.Vector3D.create(x,y,z)
        transform = adsk.core.Matrix3D.create()
        transform.translation = vector
        moveFeatureInput = moveFeats.createInput2(bodies)
        moveFeatureInput.defineAsFreeMove(transform)
        moveFeats.add(moveFeatureInput)
    except:
        if ui:
            ui.messageBox('Failed to move the body:\n{}'.format(traceback.format_exc()))


def offsetplane(design,ui,offset,plane ="XY"):

    """,
    Creates a new offset sketch which can be selected
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        offset = adsk.core.ValueInput.createByReal(offset)
        ctorPlanes = rootComp.constructionPlanes
        ctorPlaneInput1 = ctorPlanes.createInput()
        
        if plane == "XY":         
            ctorPlaneInput1.setByOffset(rootComp.xYConstructionPlane, offset)
        elif plane == "XZ":
            ctorPlaneInput1.setByOffset(rootComp.xZConstructionPlane, offset)
        elif plane == "YZ":
            ctorPlaneInput1.setByOffset(rootComp.yZConstructionPlane, offset)
        ctorPlanes.add(ctorPlaneInput1)
    except:
        if ui:
            ui.messageBox('Failed offsetplane:\n{}'.format(traceback.format_exc()))



def create_thread(design, ui,inside,sizes):
    """
    
    params:
    inside: boolean information if the face is inside or outside
    lengt: length of the thread
    sizes : index of the size in the allsizes list
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        threadFeatures = rootComp.features.threadFeatures
        
        ui.messageBox('Select a face for threading.')               
        face = ui.selectEntity("Select a face for threading", "Faces").entity
        faces = adsk.core.ObjectCollection.create()
        faces.add(face)
        #Get the thread infos
        
        
        threadDataQuery = threadFeatures.threadDataQuery
        threadTypes = threadDataQuery.allThreadTypes
        threadType = threadTypes[0]

        allsizes = threadDataQuery.allSizes(threadType)
        
        # allsizes :
        #'1/4', '5/16', '3/8', '7/16', '1/2', '5/8', '3/4', '7/8', '1', '1 1/8', '1 1/4',
        # '1 3/8', '1 1/2', '1 3/4', '2', '2 1/4', '2 1/2', '2 3/4', '3', '3 1/2', '4', '4 1/2', '5')
        #
        threadSize = allsizes[sizes]


        
        allDesignations = threadDataQuery.allDesignations(threadType, threadSize)
        threadDesignation = allDesignations[0]
        
        allClasses = threadDataQuery.allClasses(False, threadType, threadDesignation)
        threadClass = allClasses[0]
        
        # create the threadInfo according to the query result
        threadInfo = threadFeatures.createThreadInfo(inside, threadType, threadDesignation, threadClass)
        
        # get the face the thread will be applied to
    
        

        threadInput = threadFeatures.createInput(faces, threadInfo)
        threadInput.isFullLength = True
        
        # create the final thread
        thread = threadFeatures.add(threadInput)




        
    except: 
        if ui:
            ui.messageBox('Failed offsetplane thread:\n{}'.format(traceback.format_exc()))







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
def loft(design, ui, sketchcount):
    """
    Creates a loft between the last 'sketchcount' sketches
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        loftFeatures = rootComp.features.loftFeatures
        
        loftInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        loftSectionsObj = loftInput.loftSections
        
        # Add profiles from the last 'sketchcount' sketches
        for i in range(sketchcount):
            sketch = sketches.item(sketches.count - 1 - i)
            profile = sketch.profiles.item(0)
            loftSectionsObj.add(profile)
        
        loftInput.isSolid = True
        loftInput.isClosed = False
        loftInput.isTangentEdgesMerged = True
        
        # Create loft feature
        loftFeatures.add(loftInput)
        
    except:
        if ui:
            ui.messageBox('Failed loft:\n{}'.format(traceback.format_exc()))



def boolean_operation(design,ui,op):
    """
    This function performs boolean operations (cut, intersect, join)
    It is important to draw the target body first, then the tool body
    
    """
    try:
        app = adsk.core.Application.get()
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        ui  = app.userInterface

        # Get the root component of the active design.
        rootComp = design.rootComponent
        features = rootComp.features
        bodies = rootComp.bRepBodies
       
        targetBody = bodies.item(0) # target body has to be the first drawn body
        toolBody = bodies.item(1)   # tool body has to be the second drawn body

        
        combineFeatures = rootComp.features.combineFeatures
        tools = adsk.core.ObjectCollection.create()
        tools.add(toolBody)
        input: adsk.fusion.CombineFeatureInput = combineFeatures.createInput(targetBody, tools)
        input.isNewComponent = False
        input.isKeepToolBodies = False
        if op == "cut":
            input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        elif op == "intersect":
            input.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        elif op == "join":
            input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            
        combineFeature = combineFeatures.add(input)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))






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


def extrude_last_sketch(design, ui, value,taperangle):
    """
    Just extrudes the last sketch by the given value
    """
    try:
        rootComp = design.rootComponent 
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)  # Letzter Sketch
        prof = sketch.profiles.item(0)  # Erstes Profil im Sketch
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(value)
        
        if taperangle != 0:
            taperValue = adsk.core.ValueInput.createByString(f'{taperangle} deg')
     
            extent_distance = adsk.fusion.DistanceExtentDefinition.create(distance)
            extrudeInput.setOneSideExtent(extent_distance, adsk.fusion.ExtentDirections.PositiveExtentDirection, taperValue)
        else:
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
def rect_pattern(design,ui,axis_one ,axis_two ,quantity_one,quantity_two,distance_one,distance_two,plane="XY"):
    """
    Creates a rectangular pattern of the last body along the specified axis and plane
    There are two quantity parameters for two directions
    There are also two distance parameters for the spacing in two directions
    params:
    axis: "X", "Y", or "Z" axis for the pattern direction
    quantity_one: Number of instances in the first direction
    quantity_two: Number of instances in the second direction
    distance_one: Spacing between instances in the first direction
    distance_two: Spacing between instances in the second direction
    plane: Construction plane for the pattern ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        rectFeats = rootComp.features.rectangularPatternFeatures



        quantity_one = adsk.core.ValueInput.createByString(f"{quantity_one}")
        quantity_two = adsk.core.ValueInput.createByString(f"{quantity_two}")
        distance_one = adsk.core.ValueInput.createByString(f"{distance_one}")
        distance_two = adsk.core.ValueInput.createByString(f"{distance_two}")

        bodies = rootComp.bRepBodies
        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("Keine Bodies gefunden.")
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
        baseaxis_one = None    
        if axis_one == "Y":
            baseaxis_one = rootComp.yConstructionAxis 
        elif axis_one == "X":
            baseaxis_one = rootComp.xConstructionAxis
        elif axis_one == "Z":
            baseaxis_one = rootComp.zConstructionAxis


        baseaxis_two = None    
        if axis_two == "Y":
            baseaxis_two = rootComp.yConstructionAxis  
        elif axis_two == "X":
            baseaxis_two = rootComp.xConstructionAxis
        elif axis_two == "Z":
            baseaxis_two = rootComp.zConstructionAxis

 

        rectangularPatternInput = rectFeats.createInput(inputEntites,baseaxis_one, quantity_one, distance_one, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        #second direction
        rectangularPatternInput.setDirectionTwo(baseaxis_two,quantity_two, distance_two)
        rectangularFeature = rectFeats.add(rectangularPatternInput)
    except:
        if ui:
            ui.messageBox('Failed to execute rectangular pattern:\n{}'.format(traceback.format_exc()))
        
        

def circular_pattern(design, ui, quantity, axis, plane):
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        circularFeats = rootComp.features.circularPatternFeatures
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("Keine Bodies gefunden.")
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
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


def delete(design,ui):
    """
    Remove every body and sketch from the design so nothing is left
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies
        removeFeat = rootComp.features.removeFeatures

        # Von hinten nach vorne löschen
        for i in range(bodies.count - 1, -1, -1): # startet bei bodies.count - 1 und geht in Schritten von -1 bis 0 
            body = bodies.item(i)
            removeFeat.add(body)

        
    except:
        if ui:
            ui.messageBox('Failed to delete:\n{}'.format(traceback.format_exc()))



def export_as_STEP(design, ui,Name):
    try:
        
        exportMgr = design.exportManager
              
        directory_name = "Fusion_Exports"
        FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
        Export_dir_path = os.path.join(FilePath, directory_name, Name)
        os.makedirs(Export_dir_path, exist_ok=True) 
        
        stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path+ f'/{Name}.step')  # Save as Fusion.step in the export directory
       # stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path)       
        
        
        res = exportMgr.execute(stepOptions)
        if res:
            ui.messageBox(f"Exported STEP to: {Export_dir_path}")
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


def extrude_thin(design, ui, thickness,distance):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    
    #ui.messageBox('Select a face for the extrusion.')
    #selectedFace = ui.selectEntity('Select a face for the extrusion.', 'Profiles').entity
    selectedFace = sketches.item(sketches.count - 1).profiles.item(0)
    exts = rootComp.features.extrudeFeatures
    extInput = exts.createInput(selectedFace, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Center,
                            adsk.core.ValueInput.createByReal(thickness))

    distanceExtent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance))
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



def export_as_STL(design, ui,Name):
    """
    No idea whats happening here
    Copied straight up from API examples
    """
    try:

        rootComp = design.rootComponent
        

        exportMgr = design.exportManager

        stlRootOptions = exportMgr.createSTLExportOptions(rootComp)
        
        directory_name = "Fusion_Exports"
        FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
        Export_dir_path = os.path.join(FilePath, directory_name, Name)
        os.makedirs(Export_dir_path, exist_ok=True) 

        printUtils = stlRootOptions.availablePrintUtilities

        # export the root component to the print utility, instead of a specified file            
        for printUtil in printUtils:
            stlRootOptions.sendToPrintUtility = True
            stlRootOptions.printUtility = printUtil

            exportMgr.execute(stlRootOptions)
            

        
        # export the occurrence one by one in the root component to a specified file
        allOccu = rootComp.allOccurrences
        for occ in allOccu:
            Name = Export_dir_path + "/" + occ.component.name
            
            # create stl exportOptions
            stlExportOptions = exportMgr.createSTLExportOptions(occ, Name)
            stlExportOptions.sendToPrintUtility = False
            
            exportMgr.execute(stlExportOptions)

        # export the body one by one in the design to a specified file
        allBodies = rootComp.bRepBodies
        for body in allBodies:
            Name = Export_dir_path + "/" + body.parentComponent.name + '-' + body.name 
            
            # create stl exportOptions
            stlExportOptions = exportMgr.createSTLExportOptions(body, Name)
            stlExportOptions.sendToPrintUtility = False
            
            exportMgr.execute(stlExportOptions)
            
        ui.messageBox(f"Exported STL to: {Export_dir_path}")
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def get_model_parameters(design):
    model_params = []
    user_params = design.userParameters
    for param in design.allParameters:
        if all(user_params.item(i) != param for i in range(user_params.count)):
            try:
                wert = str(param.value)
            except Exception:
                wert = ""
            model_params.append({
                "Name": str(param.name),
                "Wert": wert,
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
            
            # CAM Endpoints
            elif self.path == '/cam/toolpaths/heights':
                # GET /cam/toolpaths/heights - List all toolpaths with height parameters
                # Requirements: 1.1, 1.4, 2.1, 2.5
                try:
                    # Use enhanced validation that provides detailed error information
                    result = cam.list_toolpaths_with_heights()
                    
                    if result.get('error'):
                        # Map error codes to appropriate HTTP status codes
                        error_code = result.get('code', 'UNKNOWN_ERROR')
                        if error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                            status_code = 400  # Bad Request - client needs to fix their setup
                        elif error_code == 'CAM_ACCESS_ERROR':
                            status_code = 403  # Forbidden - access issue
                        else:
                            status_code = 500  # Internal Server Error
                        
                        self.send_response(status_code)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                        return
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": True,
                        "message": f"Unexpected error retrieving toolpaths with heights: {str(e)}",
                        "code": "INTERNAL_ERROR"
                    }).encode('utf-8'))
            
            elif self.path == '/cam/toolpaths':
                # GET /cam/toolpaths - List all toolpaths in document
                # Requirements: 1.1, 1.2, 1.3, 1.4
                cam_product = cam.get_cam_product()
                result = cam.list_all_toolpaths(cam_product)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            
            elif self.path.startswith('/cam/toolpath/') and self.path.endswith('/heights'):
                # GET /cam/toolpath/{id}/heights - Get detailed height information for specific toolpath
                # Requirements: 2.2, 3.1, 3.2, 3.3, 3.4, 2.5
                try:
                    # Extract toolpath ID from URL path: /cam/toolpath/{id}/heights
                    path_parts = self.path.split('/')
                    if len(path_parts) >= 4:
                        toolpath_id = path_parts[3]  # /cam/toolpath/{id}/heights
                        
                        # Use enhanced validation and error handling
                        result = cam.get_detailed_heights(toolpath_id=toolpath_id)
                        
                        if result.get('error'):
                            # Map error codes to appropriate HTTP status codes
                            error_code = result.get('code', 'UNKNOWN_ERROR')
                            if error_code == 'TOOLPATH_NOT_FOUND':
                                status_code = 404  # Not Found
                            elif error_code == 'MISSING_TOOLPATH_ID':
                                status_code = 400  # Bad Request
                            elif error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                                status_code = 400  # Bad Request - client needs to fix their setup
                            elif error_code == 'CAM_ACCESS_ERROR':
                                status_code = 403  # Forbidden - access issue
                            else:
                                status_code = 500  # Internal Server Error
                            
                            self.send_response(status_code)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(result).encode('utf-8'))
                            return
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": True,
                            "message": "Invalid path format. Expected: /cam/toolpath/{id}/heights",
                            "code": "INVALID_PATH"
                        }).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": True,
                        "message": f"Unexpected error retrieving detailed heights: {str(e)}",
                        "code": "INTERNAL_ERROR"
                    }).encode('utf-8'))
            
            elif self.path.startswith('/cam/toolpath/') and self.path.endswith('/passes'):
                # GET /cam/toolpath/{id}/passes - Get pass configuration for specific toolpath
                # Requirements: 1.1, 1.2, 1.4, 1.5
                try:
                    # Extract toolpath ID from URL path: /cam/toolpath/{id}/passes
                    path_parts = self.path.split('/')
                    if len(path_parts) >= 4:
                        toolpath_id = path_parts[3]  # /cam/toolpath/{id}/passes
                        
                        # Get CAM product and call the function
                        cam_product = cam.get_cam_product()
                        result = cam.get_toolpath_passes(cam_product, toolpath_id)
                        
                        if result.get('error'):
                            # Map error codes to appropriate HTTP status codes
                            error_code = result.get('code', 'UNKNOWN_ERROR')
                            if error_code == 'TOOLPATH_NOT_FOUND':
                                status_code = 404  # Not Found
                            elif error_code == 'MISSING_TOOLPATH_ID':
                                status_code = 400  # Bad Request
                            elif error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                                status_code = 400  # Bad Request - client needs to fix their setup
                            elif error_code == 'CAM_ACCESS_ERROR':
                                status_code = 403  # Forbidden - access issue
                            else:
                                status_code = 500  # Internal Server Error
                            
                            self.send_response(status_code)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(result).encode('utf-8'))
                            return
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": True,
                            "message": "Invalid path format. Expected: /cam/toolpath/{id}/passes",
                            "code": "INVALID_PATH"
                        }).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": True,
                        "message": f"Unexpected error retrieving toolpath passes: {str(e)}",
                        "code": "INTERNAL_ERROR"
                    }).encode('utf-8'))
            
            elif self.path.startswith('/cam/toolpath/') and self.path.endswith('/linking'):
                # GET /cam/toolpath/{id}/linking - Get linking parameters for specific toolpath
                # Requirements: 7.1, 7.2, 7.3, 7.5
                try:
                    # Extract toolpath ID from URL path: /cam/toolpath/{id}/linking
                    path_parts = self.path.split('/')
                    if len(path_parts) >= 4:
                        toolpath_id = path_parts[3]  # /cam/toolpath/{id}/linking
                        
                        # Get CAM product and call the function
                        cam_product = cam.get_cam_product()
                        result = cam.get_toolpath_linking(cam_product, toolpath_id)
                        
                        if result.get('error'):
                            # Map error codes to appropriate HTTP status codes
                            error_code = result.get('code', 'UNKNOWN_ERROR')
                            if error_code == 'TOOLPATH_NOT_FOUND':
                                status_code = 404  # Not Found
                            elif error_code == 'MISSING_TOOLPATH_ID':
                                status_code = 400  # Bad Request
                            elif error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                                status_code = 400  # Bad Request - client needs to fix their setup
                            elif error_code == 'CAM_ACCESS_ERROR':
                                status_code = 403  # Forbidden - access issue
                            else:
                                status_code = 500  # Internal Server Error
                            
                            self.send_response(status_code)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(result).encode('utf-8'))
                            return
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": True,
                            "message": "Invalid path format. Expected: /cam/toolpath/{id}/linking",
                            "code": "INVALID_PATH"
                        }).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": True,
                        "message": f"Unexpected error retrieving toolpath linking: {str(e)}",
                        "code": "INTERNAL_ERROR"
                    }).encode('utf-8'))
            
            elif self.path.startswith('/cam/toolpath/') and '/parameter' not in self.path and not self.path.endswith('/heights'):
                # GET /cam/toolpath/<id> - Get parameters for specific toolpath
                # Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
                toolpath_id = self.path[len('/cam/toolpath/'):]
                cam_product = cam.get_cam_product()
                result = cam.get_toolpath_parameters(cam_product, toolpath_id)
                
                if result.get('error') and result.get('code') == 'TOOLPATH_NOT_FOUND':
                    self.send_response(404)
                else:
                    self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            
            elif self.path == '/cam/tools':
                # GET /cam/tools - List all tools used in document
                # Requirements: 6.1
                cam_product = cam.get_cam_product()
                result = cam.list_all_tools(cam_product)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            
            elif self.path.startswith('/cam/setup/') and self.path.endswith('/sequence'):
                # GET /cam/setup/{id}/sequence - Analyze toolpath sequence in a setup
                # Requirements: 2.1, 2.2, 2.4, 3.4
                try:
                    # Extract setup ID from URL path: /cam/setup/{id}/sequence
                    path_parts = self.path.split('/')
                    if len(path_parts) >= 4:
                        setup_id = path_parts[3]  # /cam/setup/{id}/sequence
                        
                        # Get CAM product and call the function
                        cam_product = cam.get_cam_product()
                        result = cam.analyze_setup_sequence(cam_product, setup_id)
                        
                        if result.get('error'):
                            # Map error codes to appropriate HTTP status codes
                            error_code = result.get('code', 'UNKNOWN_ERROR')
                            if error_code == 'SETUP_NOT_FOUND':
                                status_code = 404  # Not Found
                            elif error_code == 'MISSING_SETUP_ID':
                                status_code = 400  # Bad Request
                            elif error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                                status_code = 400  # Bad Request - client needs to fix their setup
                            elif error_code == 'CAM_ACCESS_ERROR':
                                status_code = 403  # Forbidden - access issue
                            else:
                                status_code = 500  # Internal Server Error
                            
                            self.send_response(status_code)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(result).encode('utf-8'))
                            return
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": True,
                            "message": "Invalid path format. Expected: /cam/setup/{id}/sequence",
                            "code": "INVALID_PATH"
                        }).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": True,
                        "message": f"Unexpected error retrieving setup sequence: {str(e)}",
                        "code": "INTERNAL_ERROR"
                    }).encode('utf-8'))
            
            # Tool Library Endpoints - GET
            elif self.path == '/tool-libraries':
                # GET /tool-libraries - List all accessible tool libraries
                # Requirements: 1.1, 1.2, 1.3
                print(f"DEBUG: tool-libraries endpoint hit, path={self.path}")
                result = tool_library.list_libraries()
                print(f"DEBUG: result={result}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            
            elif self.path.startswith('/tool-libraries/') and self.path.endswith('/tools'):
                # GET /tool-libraries/{library_id}/tools - List tools in a specific library
                # Requirements: 2.1, 2.2, 2.3, 2.4
                # Extract library_id from path: /tool-libraries/{library_id}/tools
                path_parts = self.path.split('/')
                if len(path_parts) >= 4:
                    library_id = path_parts[2]
                    result = tool_library.list_tools(library_id)
                    
                    if result.get('error') and result.get('code') == 'LIBRARY_NOT_FOUND':
                        self.send_response(404)
                    else:
                        self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                else:
                    self.send_error(400, 'Invalid path format')
            
            elif self.path.startswith('/tools/') and '/duplicate' not in self.path:
                # GET /tools/{tool_id} - Get detailed tool information
                # Requirements: 3.1, 3.2, 3.3, 3.4
                tool_id = self.path[len('/tools/'):]
                result = tool_library.get_tool(tool_id)
                
                if result.get('error') and result.get('code') == 'TOOL_NOT_FOUND':
                    self.send_response(404)
                else:
                    self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            
            # NOTE: /cam/tool/{tool_id} endpoint has been deprecated and removed.
            # Use /tools/{tool_id} instead for tool details.
           
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
                name = str(data.get('Name','Test.stl'))
                task_queue.put(('export_stl', name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "STL Export gestartet"}).encode('utf-8'))


            elif path == '/Export_STEP':
                name = str(data.get('name','Test.step'))
                task_queue.put(('export_step',name))
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
                taperangle = float(data.get('taperangle')) #0.0 as default
                task_queue.put(('extrude_last_sketch', value,taperangle))
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
                distance = float(data.get('distance',1.0)) #1.0 as default
                task_queue.put(('extrude_thin', thickness,distance))
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
            
            elif path == '/offsetplane':
                offset = float(data.get('offset',0.0))
                plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
               
                task_queue.put(('offsetplane', offset, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Offset Plane wird erstellt"}).encode('utf-8'))

            elif path == '/loft':
                sketchcount = int(data.get('sketchcount',2))
                task_queue.put(('loft', sketchcount))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Loft wird erstellt"}).encode('utf-8'))
            
            elif path == '/ellipsis':
                 x_center = float(data.get('x_center',0))
                 y_center = float(data.get('y_center',0))
                 z_center = float(data.get('z_center',0))
                 x_major = float(data.get('x_major',10))
                 y_major = float(data.get('y_major',0))
                 z_major = float(data.get('z_major',0))
                 x_through = float(data.get('x_through',5))
                 y_through = float(data.get('y_through',4))
                 z_through = float(data.get('z_through',0))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 task_queue.put(('ellipsis', x_center, y_center, z_center,
                                  x_major, y_major, z_major, x_through, y_through, z_through, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Ellipsis wird erstellt"}).encode('utf-8'))
                 
            elif path == '/sphere':
                radius = float(data.get('radius',5.0))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_sphere', radius, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sphere wird erstellt"}).encode('utf-8'))

            elif path == '/threaded':
                inside = bool(data.get('inside', True))
                allsizes = int(data.get('allsizes', 30))
                task_queue.put(('threaded', inside, allsizes))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Threaded Feature wird erstellt"}).encode('utf-8'))
                
            elif path == '/delete_everything':
                task_queue.put(('delete_everything',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Alle Bodies werden gelöscht"}).encode('utf-8'))
                
            elif path == '/boolean_operation':
                operation = data.get('operation', 'join')  # 'join', 'cut', 'intersect'
                task_queue.put(('boolean_operation', operation))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Boolean Operation wird ausgeführt"}).encode('utf-8'))
            
            elif path == '/test_connection':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Verbindung erfolgreich"}).encode('utf-8'))
            
            # CAM Parameter Modification Endpoint
            # POST /cam/toolpath/<id>/parameter - Modify a toolpath parameter
            # Requirements: 4.1, 4.2, 4.3, 4.4
            elif path.startswith('/cam/toolpath/') and path.endswith('/parameter'):
                # Extract toolpath ID from path: /cam/toolpath/<id>/parameter
                match = re.match(r'/cam/toolpath/(.+)/parameter', path)
                if match:
                    toolpath_id = match.group(1)
                    param_name = data.get('name')
                    param_value = data.get('value')
                    
                    if not param_name:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": True,
                            "message": "Parameter 'name' is required",
                            "code": "MISSING_PARAMETER"
                        }).encode('utf-8'))
                    elif param_value is None:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": True,
                            "message": "Parameter 'value' is required",
                            "code": "MISSING_PARAMETER"
                        }).encode('utf-8'))
                    else:
                        cam_product = cam.get_cam_product()
                        result = cam.set_toolpath_parameter(cam_product, toolpath_id, param_name, param_value)
                        
                        if result.get('error'):
                            if result.get('code') == 'TOOLPATH_NOT_FOUND':
                                self.send_response(404)
                            elif result.get('code') in ['INVALID_VALUE', 'READ_ONLY', 'PARAMETER_NOT_FOUND']:
                                self.send_response(400)
                            else:
                                self.send_response(500)
                        else:
                            self.send_response(200)
                        
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                else:
                    self.send_error(400, 'Invalid path format')
            
            elif path == '/draw_2d_rectangle':
                x_1 = float(data.get('x_1',0))
                y_1 = float(data.get('y_1',0))
                z_1 = float(data.get('z_1',0))
                x_2 = float(data.get('x_2',1))
                y_2 = float(data.get('y_2',1))
                z_2 = float(data.get('z_2',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_2d_rectangle', x_1, y_1, z_1, x_2, y_2, z_2, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "2D Rechteck wird erstellt"}).encode('utf-8'))
            
            
            elif path == '/rectangular_pattern':
                 quantity_one = float(data.get('quantity_one',2))
                 distance_one = float(data.get('distance_one',5))
                 axis_one = str(data.get('axis_one',"X"))
                 quantity_two = float(data.get('quantity_two',2))
                 distance_two = float(data.get('distance_two',5))
                 axis_two = str(data.get('axis_two',"Y"))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 # Parameter-Reihenfolge: axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane
                 task_queue.put(('rectangular_pattern', axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Rectangular Pattern wird erstellt"}).encode('utf-8'))
                 
            elif path == '/draw_text':
                 text = str(data.get('text',"Hello"))
                 x_1 = float(data.get('x_1',0))
                 y_1 = float(data.get('y_1',0))
                 z_1 = float(data.get('z_1',0))
                 x_2 = float(data.get('x_2',10))
                 y_2 = float(data.get('y_2',4))
                 z_2 = float(data.get('z_2',0))
                 extrusion_value = float(data.get('extrusion_value',1.0))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 thickness = float(data.get('thickness',0.5))
                 task_queue.put(('draw_text', text,thickness, x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Text wird erstellt"}).encode('utf-8'))
                 
            elif path == '/move_body':
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                task_queue.put(('move_body', x, y, z))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Body wird verschoben"}).encode('utf-8'))
            
            # Tool Library Endpoints - POST, PUT, DELETE
            # POST /tool-libraries/{library_id}/tools - Create a new tool
            # Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
            elif path.startswith('/tool-libraries/') and path.endswith('/tools'):
                # Extract library_id from path: /tool-libraries/{library_id}/tools
                path_parts = path.split('/')
                if len(path_parts) >= 4:
                    library_id = path_parts[2]
                    result = tool_library.create_tool(library_id, data)
                    
                    if result.get('error'):
                        if result.get('code') == 'LIBRARY_NOT_FOUND':
                            self.send_response(404)
                        elif result.get('code') == 'LIBRARY_READ_ONLY':
                            self.send_response(403)
                        elif result.get('code') in ['MISSING_REQUIRED_FIELD', 'INVALID_TOOL_DATA']:
                            self.send_response(400)
                        else:
                            self.send_response(500)
                    else:
                        self.send_response(201)  # Created
                    
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                else:
                    self.send_error(400, 'Invalid path format')
            
            # POST /tools/{tool_id}/duplicate - Duplicate a tool
            # Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
            elif path.startswith('/tools/') and path.endswith('/duplicate'):
                # Extract tool_id from path: /tools/{tool_id}/duplicate
                match = re.match(r'/tools/(.+)/duplicate', path)
                if match:
                    tool_id = match.group(1)
                    target_library_id = data.get('target_library_id')
                    new_name = data.get('new_name')
                    
                    if not target_library_id:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": True,
                            "message": "Parameter 'target_library_id' is required",
                            "code": "MISSING_PARAMETER"
                        }).encode('utf-8'))
                    else:
                        result = tool_library.duplicate_tool(tool_id, target_library_id, new_name)
                        
                        if result.get('error'):
                            if result.get('code') == 'TOOL_NOT_FOUND':
                                self.send_response(404)
                            elif result.get('code') == 'LIBRARY_NOT_FOUND':
                                self.send_response(404)
                            elif result.get('code') == 'LIBRARY_READ_ONLY':
                                self.send_response(403)
                            else:
                                self.send_response(500)
                        else:
                            self.send_response(201)  # Created
                        
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                else:
                    self.send_error(400, 'Invalid path format')
            
            # POST /tools/search - Search for tools
            # Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
            elif path == '/tools/search':
                result = tool_library.search_tools(data)
                
                if result.get('error'):
                    if result.get('code') == 'INVALID_TOOL_DATA':
                        self.send_response(400)
                    else:
                        self.send_response(500)
                else:
                    self.send_response(200)
                
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            
            # POST /cam/toolpath/{id}/passes - Modify pass configuration
            # Requirements: 4.1, 4.2, 4.3, 4.5
            elif path.startswith('/cam/toolpath/') and path.endswith('/passes'):
                try:
                    # Extract toolpath ID from URL path: /cam/toolpath/{id}/passes
                    path_parts = path.split('/')
                    if len(path_parts) >= 4:
                        toolpath_id = path_parts[3]  # /cam/toolpath/{id}/passes
                        
                        # Validate required data
                        if not data:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({
                                "success": False,
                                "error": True,
                                "message": "Pass configuration data is required",
                                "code": "MISSING_DATA"
                            }).encode('utf-8'))
                            return
                        
                        # Get CAM product and call the modification function
                        cam_product = cam.get_cam_product()
                        result = cam.modify_toolpath_passes(cam_product, toolpath_id, data)
                        
                        # Map error codes to appropriate HTTP status codes
                        if result.get('error'):
                            error_code = result.get('code', 'UNKNOWN_ERROR')
                            if error_code == 'TOOLPATH_NOT_FOUND':
                                status_code = 404  # Not Found
                            elif error_code in ['MISSING_TOOLPATH_ID', 'MISSING_PASS_CONFIG', 'VALIDATION_FAILED']:
                                status_code = 400  # Bad Request
                            elif error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                                status_code = 400  # Bad Request - client needs to fix their setup
                            elif error_code == 'CAM_ACCESS_ERROR':
                                status_code = 403  # Forbidden - access issue
                            else:
                                status_code = 500  # Internal Server Error
                            
                            self.send_response(status_code)
                        else:
                            self.send_response(200)
                        
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": True,
                            "message": "Invalid path format. Expected: /cam/toolpath/{id}/passes",
                            "code": "INVALID_PATH"
                        }).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"Unexpected error modifying toolpath passes: {str(e)}",
                        "code": "INTERNAL_ERROR"
                    }).encode('utf-8'))
            
            # POST /cam/toolpath/{id}/linking - Modify linking configuration
            # Requirements: 7.4, 4.4, 4.5
            elif path.startswith('/cam/toolpath/') and path.endswith('/linking'):
                try:
                    # Extract toolpath ID from URL path: /cam/toolpath/{id}/linking
                    path_parts = path.split('/')
                    if len(path_parts) >= 4:
                        toolpath_id = path_parts[3]  # /cam/toolpath/{id}/linking
                        
                        # Validate required data
                        if not data:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({
                                "success": False,
                                "error": True,
                                "message": "Linking configuration data is required",
                                "code": "MISSING_DATA"
                            }).encode('utf-8'))
                            return
                        
                        # Get CAM product and call the modification function
                        cam_product = cam.get_cam_product()
                        result = cam.modify_toolpath_linking(cam_product, toolpath_id, data)
                        
                        # Map error codes to appropriate HTTP status codes
                        if result.get('error'):
                            error_code = result.get('code', 'UNKNOWN_ERROR')
                            if error_code == 'TOOLPATH_NOT_FOUND':
                                status_code = 404  # Not Found
                            elif error_code in ['MISSING_TOOLPATH_ID', 'MISSING_LINKING_CONFIG', 'VALIDATION_FAILED']:
                                status_code = 400  # Bad Request
                            elif error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                                status_code = 400  # Bad Request - client needs to fix their setup
                            elif error_code == 'CAM_ACCESS_ERROR':
                                status_code = 403  # Forbidden - access issue
                            elif error_code == 'PARAMETERS_NOT_ACCESSIBLE':
                                status_code = 403  # Forbidden - parameter access issue
                            else:
                                status_code = 500  # Internal Server Error
                            
                            self.send_response(status_code)
                        else:
                            self.send_response(200)
                        
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": True,
                            "message": "Invalid path format. Expected: /cam/toolpath/{id}/linking",
                            "code": "INVALID_PATH"
                        }).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"Unexpected error modifying toolpath linking: {str(e)}",
                        "code": "INTERNAL_ERROR"
                    }).encode('utf-8'))
            
            else:
                self.send_error(404,'Not Found')

        except Exception as e:
            self.send_error(500,str(e))

    def do_PUT(self):
        """Handle PUT requests for tool modification."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            put_data = self.rfile.read(content_length)
            data = json.loads(put_data) if put_data else {}
            path = self.path

            # PUT /tools/{tool_id} - Modify a tool
            # Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
            if path.startswith('/tools/') and '/duplicate' not in path:
                tool_id = path[len('/tools/'):]
                result = tool_library.modify_tool(tool_id, data)
                
                if result.get('error'):
                    if result.get('code') == 'TOOL_NOT_FOUND':
                        self.send_response(404)
                    elif result.get('code') == 'TOOL_READ_ONLY':
                        self.send_response(403)
                    else:
                        self.send_response(500)
                else:
                    self.send_response(200)
                
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            else:
                self.send_error(404, 'Not Found')

        except Exception as e:
            self.send_error(500, str(e))

    def do_DELETE(self):
        """Handle DELETE requests for tool deletion."""
        try:
            path = self.path

            # DELETE /tools/{tool_id} - Delete a tool
            # Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
            if path.startswith('/tools/'):
                tool_id = path[len('/tools/'):]
                result = tool_library.delete_tool(tool_id)
                
                if result.get('error'):
                    if result.get('code') == 'TOOL_NOT_FOUND':
                        self.send_response(404)
                    elif result.get('code') in ['TOOL_READ_ONLY', 'TOOL_IN_USE']:
                        self.send_response(403)
                    else:
                        self.send_response(500)
                else:
                    self.send_response(200)
                
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            else:
                self.send_error(404, 'Not Found')

        except Exception as e:
            self.send_error(500, str(e))

def run_server():
    global httpd
    server_address = ('localhost',5001)
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

        ui.messageBox(f"Fusion HTTP Add-In gestartet! Port 5001.\nParameter geladen: {len(ModelParameterSnapshot)} Modellparameter")

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
