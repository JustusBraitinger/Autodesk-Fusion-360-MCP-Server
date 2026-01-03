---
inclusion: fileMatch
fileMatchPattern: ['FusionMCPBridge/**/*.py', '**/fusion*.py', '**/tool_library.py']
---

# Fusion 360 Python Add-In Development

## API Documentation
- [API Reference](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-A92A4B10-3781-4925-94C6-47DA85A4F65A)
- [Python/C++ Examples](https://help.autodesk.com/view/fusion360/ENU/?guid=SampleList)

## Core Imports
```python
import adsk.core    # Application, UI, geometry primitives
import adsk.fusion  # Design, sketches, features, bodies
import adsk.cam     # CAM operations, toolpaths, tool libraries
```

## Threading Model (CRITICAL)
Fusion 360 API is NOT thread-safe. All API calls MUST execute on the main UI thread.

**Required Pattern: Task Queue + Custom Event**
```python
task_queue = queue.Queue()
myCustomEvent = 'MCPTaskEvent'

class TaskEventHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        while not task_queue.empty():
            task = task_queue.get_nowait()
            self.process_task(task)

# Fire event every 200ms from background thread
app.fireCustomEvent(myCustomEvent, json.dumps({}))
```

## Unit Conversion (CRITICAL)
Fusion 360 uses centimeters internally:
- `1 unit = 1 cm = 10 mm`
- Convert mm to units: `value_mm / 10`
- Example: `28.3 mm → 2.83 units`

## Add-In Lifecycle
```python
def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    customEvent = app.registerCustomEvent(myCustomEvent)
    customEvent.add(TaskEventHandler())

def stop(context):
    # MUST clean up handlers, stop threads, shutdown servers
    customEvent.remove(handler)
```

## Design Access Patterns

### Root Component
```python
rootComp = design.rootComponent
sketches = rootComp.sketches
features = rootComp.features
bodies = rootComp.bRepBodies
```

### Sketch Creation
```python
# Standard planes
sketch = sketches.add(rootComp.xYConstructionPlane)
sketch = sketches.add(rootComp.xZConstructionPlane)
sketch = sketches.add(rootComp.yZConstructionPlane)

# Offset plane
planes = rootComp.constructionPlanes
planeInput = planes.createInput()
planeInput.setByOffset(basePlane, adsk.core.ValueInput.createByReal(offset))
offsetPlane = planes.add(planeInput)
sketch = sketches.add(offsetPlane)
```

### Sketch Geometry
```python
# Points
point = adsk.core.Point3D.create(x, y, z)

# Lines
lines = sketch.sketchCurves.sketchLines
lines.addByTwoPoints(startPoint, endPoint)
lines.addCenterPointRectangle(center, corner)
lines.addTwoPointRectangle(point1, point2)

# Circles
circles = sketch.sketchCurves.sketchCircles
circles.addByCenterRadius(centerPoint, radius)

# Arcs
arcs = sketch.sketchCurves.sketchArcs
arcs.addByThreePoints(start, along, end)

# Splines
splines = sketch.sketchCurves.sketchFittedSplines
splines.add(pointCollection)  # ObjectCollection of Point3D
```

### Feature Operations
```python
# Extrusion
extrudes = rootComp.features.extrudeFeatures
profile = sketch.profiles.item(0)
extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(distance))
extrudes.add(extInput)

# Revolution
revolves = rootComp.features.revolveFeatures
revInput = revolves.createInput(profile, axisLine, operation)
revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(angle))
revolves.add(revInput)
```

### Feature Operations Enum
```python
adsk.fusion.FeatureOperations.NewBodyFeatureOperation
adsk.fusion.FeatureOperations.JoinFeatureOperation
adsk.fusion.FeatureOperations.CutFeatureOperation
adsk.fusion.FeatureOperations.IntersectFeatureOperation
adsk.fusion.FeatureOperations.NewComponentFeatureOperation
```

## CAM API Patterns

### Accessing CAM Product
```python
def get_cam_product():
    app = adsk.core.Application.get()
    doc = app.activeDocument
    products = doc.products
    cam_product = products.itemByProductType('CAMProductType')
    return adsk.cam.CAM.cast(cam_product)
```

### Tool Library Access
```python
camManager = adsk.cam.CAMManager.get()
libraryManager = camManager.libraryManager
toolLibraries = libraryManager.toolLibraries

# Access by URL
url = adsk.core.URL.create('systemlibraryroot://Samples/Milling Tools (Metric).json')
toolLibrary = toolLibraries.toolLibraryAtURL(url)

# Library locations
toolLibraries.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)
toolLibraries.urlByLocation(adsk.cam.LibraryLocations.CloudLibraryLocation)
```

### Tool Properties (via parameters)
```python
params = tool.parameters
desc_param = params.itemByName('tool_description')
diam_param = params.itemByName('tool_diameter')
type_param = params.itemByName('tool_type')
length_param = params.itemByName('tool_overallLength')
num_param = params.itemByName('tool_number')

# Access values
if desc_param:
    name = desc_param.expression.strip("'\"")
if diam_param:
    diameter = float(diam_param.value.value)
```

## Error Handling
```python
try:
    # API operations
except:
    if ui:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

## Debugging
```python
app = adsk.core.Application.get()
app.log(f"Debug: {variable}")  # Visible in Text Commands panel
```

## Project-Specific Rules

### HTTP Server Integration
- Server runs on port 5001
- Background thread handles HTTP requests
- Tasks queued for main thread execution via CustomEvent
- JSON request/response format

### Module Imports
Use relative imports within add-in:
```python
from . import cam
from .tool_library import find_tool_by_id, serialize_tool
```

### Collection Iteration
```python
for i in range(collection.count):
    item = collection.item(i)
```

### Defensive Coding
- Always check for `None` before accessing properties
- Use `hasattr()` for optional properties
- Use `getattr(obj, 'prop', default)` for safe access
- Clean up handlers and threads in `stop()` function

### Tool Object Access
Tool objects use `.description` not `.name`:
```python
tool_name = tool.description if hasattr(tool, 'description') and tool.description else "Unnamed Tool"
```
