# Design Geometry Implementation
# Contains all Fusion 360 geometry creation functions
# These functions execute on the main UI thread via the task queue

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math
import os

def draw_text(design, ui, text, thickness,
              x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane="XY"):
    """Draw extruded text on the specified plane"""
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
        input = texts.createInput2(f"{text}", thickness)
        input.setAsMultiLine(point_1, point_2,
                             adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                             adsk.core.VerticalAlignments.TopVerticalAlignment, 0)
        sketchtext = texts.add(input)
        extrudes = rootComp.features.extrudeFeatures
        
        extInput = extrudes.createInput(sketchtext, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(extrusion_value)
        extInput.setDistanceExtent(False, distance)
        extInput.isSolid = True
        ext = extrudes.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed draw_text:\n{}'.format(traceback.format_exc()))


def create_sphere(design, ui, radius, x, y, z):
    """Create a sphere at the specified position"""
    try:
        rootComp = design.rootComponent
        component = design.rootComponent
        sketches = rootComp.sketches
        
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(adsk.core.Point3D.create(x, y, z), radius)
        lines = sketch.sketchCurves.sketchLines
        axisLine = lines.addByTwoPoints(
            adsk.core.Point3D.create(x - radius, y, z),
            adsk.core.Point3D.create(x + radius, y, z)
        )

        profile = sketch.profiles.item(0)
        revolves = component.features.revolveFeatures
        revInput = revolves.createInput(profile, axisLine, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)
        angle = adsk.core.ValueInput.createByReal(2 * math.pi)
        revInput.setAngleExtent(False, angle)
        ext = revolves.add(revInput)
    except:
        if ui:
            ui.messageBox('Failed create_sphere:\n{}'.format(traceback.format_exc()))


def draw_Box(design, ui, height, width, depth, x, y, z, plane=None):
    """Draw a box with given dimensions at position (x,y,z)"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        if plane == 'XZ':
            basePlane = rootComp.xZConstructionPlane
        elif plane == 'YZ':
            basePlane = rootComp.yZConstructionPlane
        else:
            basePlane = rootComp.xYConstructionPlane
        
        if z != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)
        
        lines = sketch.sketchCurves.sketchLines
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


def draw_ellipis(design, ui, x_center, y_center, z_center,
                 x_major, y_major, z_major, x_through, y_through, z_through, plane="XY"):
    """Draw an ellipse on the specified plane using three points"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        
        centerPoint = adsk.core.Point3D.create(float(x_center), float(y_center), float(z_center))
        majorAxisPoint = adsk.core.Point3D.create(float(x_major), float(y_major), float(z_major))
        throughPoint = adsk.core.Point3D.create(float(x_through), float(y_through), float(z_through))
        sketchEllipse = sketch.sketchCurves.sketchEllipses
        ellipse = sketchEllipse.add(centerPoint, majorAxisPoint, throughPoint)
    except:
        if ui:
            ui.messageBox('Failed to draw ellipsis:\n{}'.format(traceback.format_exc()))


def draw_2d_rect(design, ui, x_1, y_1, z_1, x_2, y_2, z_2, plane="XY"):
    """Draw a 2D rectangle on the specified plane"""
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
    """Draw a circle with given radius at position (x,y,z) on the specified plane"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
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
            if x != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(x)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(y, z, 0)
        else:
            basePlane = rootComp.xYConstructionPlane
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


def draw_Witzenmann(design, ui, scaling, z):
    """Draw Witzenmann logo with scaling factor"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        points1 = [
            (8.283*scaling, 10.475*scaling, z), (8.283*scaling, 6.471*scaling, z),
            (-0.126*scaling, 6.471*scaling, z), (8.283*scaling, 2.691*scaling, z),
            (8.283*scaling, -1.235*scaling, z), (-0.496*scaling, -1.246*scaling, z),
            (8.283*scaling, -5.715*scaling, z), (8.283*scaling, -9.996*scaling, z),
            (-8.862*scaling, -1.247*scaling, z), (-8.859*scaling, 2.69*scaling, z),
            (-0.639*scaling, 2.69*scaling, z), (-8.859*scaling, 6.409*scaling, z),
            (-8.859*scaling, 10.459*scaling, z)
        ]
        for i in range(len(points1)-1):
            start = adsk.core.Point3D.create(points1[i][0], points1[i][1], points1[i][2])
            end = adsk.core.Point3D.create(points1[i+1][0], points1[i+1][1], points1[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points1[-1][0], points1[-1][1], points1[-1][2]),
            adsk.core.Point3D.create(points1[0][0], points1[0][1], points1[0][2])
        )

        points2 = [(-3.391*scaling, -5.989*scaling, z), (5.062*scaling, -10.141*scaling, z),
                   (-8.859*scaling, -10.141*scaling, z), (-8.859*scaling, -5.989*scaling, z)]
        for i in range(len(points2)-1):
            start = adsk.core.Point3D.create(points2[i][0], points2[i][1], points2[i][2])
            end = adsk.core.Point3D.create(points2[i+1][0], points2[i+1][1], points2[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points2[-1][0], points2[-1][1], points2[-1][2]),
            adsk.core.Point3D.create(points2[0][0], points2[0][1], points2[0][2])
        )

        extrudes = rootComp.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(2.0*scaling)
        for i in range(sketch.profiles.count):
            prof = sketch.profiles.item(i)
            extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False, distance)
            extrudes.add(extrudeInput)
    except:
        if ui:
            ui.messageBox('Failed draw_Witzenmann:\n{}'.format(traceback.format_exc()))


def move_last_body(design, ui, x, y, z):
    """Move the last created body by the specified vector"""
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        moveFeats = features.moveFeatures
        body = rootComp.bRepBodies
        bodies = adsk.core.ObjectCollection.create()
        
        if body.count > 0:
            latest_body = body.item(body.count - 1)
            bodies.add(latest_body)
        else:
            ui.messageBox("Keine Bodies gefunden.")
            return

        vector = adsk.core.Vector3D.create(x, y, z)
        transform = adsk.core.Matrix3D.create()
        transform.translation = vector
        moveFeatureInput = moveFeats.createInput2(bodies)
        moveFeatureInput.defineAsFreeMove(transform)
        moveFeats.add(moveFeatureInput)
    except:
        if ui:
            ui.messageBox('Failed to move the body:\n{}'.format(traceback.format_exc()))


def offsetplane(design, ui, offset, plane="XY"):
    """Create a new offset construction plane"""
    try:
        rootComp = design.rootComponent
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
