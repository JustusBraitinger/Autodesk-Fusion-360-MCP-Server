# Design Geometry Implementation - Part 2
# Additional geometry creation functions

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math
import os


def create_thread(design, ui, inside, sizes):
    """Create a thread on a selected face"""
    try:
        rootComp = design.rootComponent
        threadFeatures = rootComp.features.threadFeatures
        
        ui.messageBox('Select a face for threading.')
        face = ui.selectEntity("Select a face for threading", "Faces").entity
        faces = adsk.core.ObjectCollection.create()
        faces.add(face)
        
        threadDataQuery = threadFeatures.threadDataQuery
        threadTypes = threadDataQuery.allThreadTypes
        threadType = threadTypes[0]
        allsizes = threadDataQuery.allSizes(threadType)
        threadSize = allsizes[sizes]
        
        allDesignations = threadDataQuery.allDesignations(threadType, threadSize)
        threadDesignation = allDesignations[0]
        
        allClasses = threadDataQuery.allClasses(False, threadType, threadDesignation)
        threadClass = allClasses[0]
        
        threadInfo = threadFeatures.createThreadInfo(inside, threadType, threadDesignation, threadClass)
        threadInput = threadFeatures.createInput(faces, threadInfo)
        threadInput.isFullLength = True
        thread = threadFeatures.add(threadInput)
    except:
        if ui:
            ui.messageBox('Failed thread:\n{}'.format(traceback.format_exc()))


def spline(design, ui, points, plane="XY"):
    """Draw a spline through the given points on the specified plane"""
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


def arc(design, ui, point1, point2, points3, plane="XY", connect=False):
    """Create an arc between points on the specified plane"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        
        start = adsk.core.Point3D.create(point1[0], point1[1], point1[2])
        alongpoint = adsk.core.Point3D.create(point2[0], point2[1], point2[2])
        endpoint = adsk.core.Point3D.create(points3[0], points3[1], points3[2])
        arcs = sketch.sketchCurves.sketchArcs
        arc = arcs.addByThreePoints(start, alongpoint, endpoint)
        if connect:
            startconnect = adsk.core.Point3D.create(start.x, start.y, start.z)
            endconnect = adsk.core.Point3D.create(endpoint.x, endpoint.y, endpoint.z)
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(startconnect, endconnect)
    except:
        if ui:
            ui.messageBox('Failed arc:\n{}'.format(traceback.format_exc()))


def draw_lines(design, ui, points, Plane="XY"):
    """Draw lines between the given points, closing the shape"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if Plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif Plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif Plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        
        for i in range(len(points)-1):
            start = adsk.core.Point3D.create(points[i][0], points[i][1], 0)
            end = adsk.core.Point3D.create(points[i+1][0], points[i+1][1], 0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points[-1][0], points[-1][1], 0),
            adsk.core.Point3D.create(points[0][0], points[0][1], 0)
        )
    except:
        if ui:
            ui.messageBox('Failed draw_lines:\n{}'.format(traceback.format_exc()))


def draw_one_line(design, ui, x1, y1, z1, x2, y2, z2, plane="XY"):
    """Draw a single line between two points in the last sketch"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)
        
        start = adsk.core.Point3D.create(x1, y1, 0)
        end = adsk.core.Point3D.create(x2, y2, 0)
        sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    except:
        if ui:
            ui.messageBox('Failed draw_one_line:\n{}'.format(traceback.format_exc()))


def extrude_last_sketch(design, ui, value, taperangle):
    """Extrude the last sketch profile"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)
        prof = sketch.profiles.item(0)
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
            ui.messageBox('Failed extrude_last_sketch:\n{}'.format(traceback.format_exc()))


def shell_existing_body(design, ui, thickness=0.5, faceindex=0):
    """Shell the body on a specified face index"""
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
        shellFeats.add(shellInput)
    except:
        if ui:
            ui.messageBox('Failed shell_existing_body:\n{}'.format(traceback.format_exc()))


def fillet_edges(design, ui, radius=0.3):
    """Fillet all edges of all bodies"""
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
            ui.messageBox('Failed fillet_edges:\n{}'.format(traceback.format_exc()))


def revolve_profile(design, ui, angle=360):
    """Revolve a selected profile around a selected axis"""
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


def rect_pattern(design, ui, axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane="XY"):
    """Create a rectangular pattern of the last body"""
    try:
        rootComp = design.rootComponent
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
            return
        
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

        rectangularPatternInput = rectFeats.createInput(inputEntites, baseaxis_one, quantity_one, distance_one, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        rectangularPatternInput.setDirectionTwo(baseaxis_two, quantity_two, distance_two)
        rectangularFeature = rectFeats.add(rectangularPatternInput)
    except:
        if ui:
            ui.messageBox('Failed rectangular pattern:\n{}'.format(traceback.format_exc()))


def circular_pattern(design, ui, quantity, axis, plane):
    """Create a circular pattern of the last body"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        circularFeats = rootComp.features.circularPatternFeatures
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("Keine Bodies gefunden.")
            return
        
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
        
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        
        if axis == "Y":
            circularFeatInput = circularFeats.createInput(inputEntites, rootComp.yConstructionAxis)
        elif axis == "X":
            circularFeatInput = circularFeats.createInput(inputEntites, rootComp.xConstructionAxis)
        elif axis == "Z":
            circularFeatInput = circularFeats.createInput(inputEntites, rootComp.zConstructionAxis)

        circularFeatInput.quantity = adsk.core.ValueInput.createByReal(quantity)
        circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
        circularFeatInput.isSymmetric = False
        circularFeats.add(circularFeatInput)
    except:
        if ui:
            ui.messageBox('Failed circular_pattern:\n{}'.format(traceback.format_exc()))


def undo(design, ui):
    """Execute undo command"""
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        cmd = ui.commandDefinitions.itemById('UndoCommand')
        cmd.execute()
    except:
        if ui:
            ui.messageBox('Failed undo:\n{}'.format(traceback.format_exc()))


def delete(design, ui):
    """Remove all bodies from the design"""
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        removeFeat = rootComp.features.removeFeatures

        for i in range(bodies.count - 1, -1, -1):
            body = bodies.item(i)
            removeFeat.add(body)
    except:
        if ui:
            ui.messageBox('Failed delete:\n{}'.format(traceback.format_exc()))


def export_as_STEP(design, ui, Name):
    """Export design as STEP file"""
    try:
        exportMgr = design.exportManager
        directory_name = "Fusion_Exports"
        FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        Export_dir_path = os.path.join(FilePath, directory_name, Name)
        os.makedirs(Export_dir_path, exist_ok=True)
        
        stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path + f'/{Name}.step')
        res = exportMgr.execute(stepOptions)
        if res:
            ui.messageBox(f"Exported STEP to: {Export_dir_path}")
        else:
            ui.messageBox("STEP export failed")
    except:
        if ui:
            ui.messageBox('Failed export_as_STEP:\n{}'.format(traceback.format_exc()))


def cut_extrude(design, ui, depth):
    """Cut extrude the last sketch profile"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)
        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extrudeInput.setDistanceExtent(False, distance)
        extrudes.add(extrudeInput)
    except:
        if ui:
            ui.messageBox('Failed cut_extrude:\n{}'.format(traceback.format_exc()))


def extrude_thin(design, ui, thickness, distance):
    """Create a thin extrusion from the last sketch"""
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    selectedFace = sketches.item(sketches.count - 1).profiles.item(0)
    exts = rootComp.features.extrudeFeatures
    extInput = exts.createInput(selectedFace, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Center,
                            adsk.core.ValueInput.createByReal(thickness))
    distanceExtent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance))
    extInput.setOneSideExtent(distanceExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    ext = exts.add(extInput)


def draw_cylinder(design, ui, radius, height, x, y, z, plane="XY"):
    """Draw a cylinder with given radius and height"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)

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


def export_as_STL(design, ui, Name):
    """Export design as STL file"""
    try:
        rootComp = design.rootComponent
        exportMgr = design.exportManager
        stlRootOptions = exportMgr.createSTLExportOptions(rootComp)
        
        directory_name = "Fusion_Exports"
        FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        Export_dir_path = os.path.join(FilePath, directory_name, Name)
        os.makedirs(Export_dir_path, exist_ok=True)

        printUtils = stlRootOptions.availablePrintUtilities
        for printUtil in printUtils:
            stlRootOptions.sendToPrintUtility = True
            stlRootOptions.printUtility = printUtil
            exportMgr.execute(stlRootOptions)

        allOccu = rootComp.allOccurrences
        for occ in allOccu:
            Name = Export_dir_path + "/" + occ.component.name
            stlExportOptions = exportMgr.createSTLExportOptions(occ, Name)
            stlExportOptions.sendToPrintUtility = False
            exportMgr.execute(stlExportOptions)

        allBodies = rootComp.bRepBodies
        for body in allBodies:
            Name = Export_dir_path + "/" + body.parentComponent.name + '-' + body.name
            stlExportOptions = exportMgr.createSTLExportOptions(body, Name)
            stlExportOptions.sendToPrintUtility = False
            exportMgr.execute(stlExportOptions)
            
        ui.messageBox(f"Exported STL to: {Export_dir_path}")
    except:
        if ui:
            ui.messageBox('Failed export_as_STL:\n{}'.format(traceback.format_exc()))


def holes(design, ui, points, width=1.0, distance=1.0, faceindex=0):
    """Create holes on a face"""
    try:
        rootComp = design.rootComponent
        holes = rootComp.features.holeFeatures
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("Keine Bodies gefunden.")
            return
        
        sk = sketches.add(latest_body.faces.item(faceindex))

        for i in range(len(points)):
            holePoint = sk.sketchPoints.add(adsk.core.Point3D.create(points[i][0], points[i][1], 0))
            tipangle = adsk.core.ValueInput.createByString('180 deg')
            holedistance = adsk.core.ValueInput.createByReal(distance)
            holeDiam = adsk.core.ValueInput.createByReal(width)
            holeInput = holes.createSimpleInput(holeDiam)
            holeInput.tipAngle = tipangle
            holeInput.setPositionBySketchPoint(holePoint)
            holeInput.setDistanceExtent(holedistance)
            holes.add(holeInput)
    except:
        if ui:
            ui.messageBox('Failed holes:\n{}'.format(traceback.format_exc()))


def select_body(design, ui, Bodyname):
    """Select a body by name"""
    try:
        rootComp = design.rootComponent
        target_body = rootComp.bRepBodies.itemByName(Bodyname)
        if target_body is None:
            ui.messageBox(f"Body with the name: '{Bodyname}' could not be found.")
        return target_body
    except:
        if ui:
            ui.messageBox('Failed select_body:\n{}'.format(traceback.format_exc()))


def select_sketch(design, ui, Sketchname):
    """Select a sketch by name"""
    try:
        rootComp = design.rootComponent
        target_sketch = rootComp.sketches.itemByName(Sketchname)
        if target_sketch is None:
            ui.messageBox(f"Sketch with the name: '{Sketchname}' could not be found.")
        return target_sketch
    except:
        if ui:
            ui.messageBox('Failed select_sketch:\n{}'.format(traceback.format_exc()))


def sweep(design, ui):
    """Create a sweep feature (requires user selection)"""
    try:
        rootComp = design.rootComponent
        ui.messageBox('Select a profile for sweep.')
        profile = ui.selectEntity('Select a profile for sweep.', 'Profiles').entity
        ui.messageBox('Select a path for sweep.')
        path = ui.selectEntity('Select a path for sweep.', 'SketchCurves').entity
        
        sweepFeatures = rootComp.features.sweepFeatures
        sweepInput = sweepFeatures.createInput(profile, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        sweepFeature = sweepFeatures.add(sweepInput)
    except:
        if ui:
            ui.messageBox('Failed sweep:\n{}'.format(traceback.format_exc()))


def loft(design, ui, sketchcount):
    """Create a loft between the last N sketches"""
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        loftFeatures = rootComp.features.loftFeatures
        
        loftInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        for i in range(sketchcount):
            sketch = sketches.item(sketches.count - 1 - i)
            profile = sketch.profiles.item(0)
            loftInput.loftSections.add(profile)
        
        loftFeature = loftFeatures.add(loftInput)
    except:
        if ui:
            ui.messageBox('Failed loft:\n{}'.format(traceback.format_exc()))


def boolean_operation(design, ui, op):
    """Perform boolean operation between bodies"""
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        
        if bodies.count < 2:
            ui.messageBox("Need at least 2 bodies for boolean operation.")
            return
        
        targetBody = bodies.item(0)
        toolBodies = adsk.core.ObjectCollection.create()
        for i in range(1, bodies.count):
            toolBodies.add(bodies.item(i))
        
        combineFeatures = rootComp.features.combineFeatures
        
        if op == 'join':
            operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        elif op == 'cut':
            operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        elif op == 'intersect':
            operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        else:
            operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        
        combineInput = combineFeatures.createInput(targetBody, toolBodies)
        combineInput.operation = operation
        combineFeatures.add(combineInput)
    except:
        if ui:
            ui.messageBox('Failed boolean_operation:\n{}'.format(traceback.format_exc()))


def get_model_parameters(design):
    """Get all model parameters"""
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
    """Set a parameter value"""
    try:
        param = design.allParameters.itemByName(name)
        param.expression = value
    except:
        if ui:
            ui.messageBox('Failed set_parameter:\n{}'.format(traceback.format_exc()))


def count_parameters(design, ui):
    """Count all parameters in the design"""
    try:
        param_count = design.allParameters.count
        if ui:
            ui.messageBox(f'Total parameters: {param_count}')
        return param_count
    except:
        if ui:
            ui.messageBox('Failed count_parameters:\n{}'.format(traceback.format_exc()))
        return 0


def list_parameters(design, ui):
    """List all parameters in the design"""
    try:
        params = []
        for i in range(design.allParameters.count):
            param = design.allParameters.item(i)
            param_info = {
                "name": param.name,
                "value": param.value,
                "unit": str(param.unit),
                "expression": str(param.expression) if param.expression else ""
            }
            params.append(param_info)
        
        if ui:
            param_list = "\n".join([f"{p['name']}: {p['value']} {p['unit']}" for p in params])
            ui.messageBox(f'Parameters:\n{param_list}')
        
        return params
    except:
        if ui:
            ui.messageBox('Failed list_parameters:\n{}'.format(traceback.format_exc()))
        return []
