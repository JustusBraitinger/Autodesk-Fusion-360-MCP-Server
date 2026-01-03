# FusionMCPBridge - Fusion 360 Add-In Entry Point
# Minimal add-in focused on lifecycle management and HTTP server coordination
# All business logic is delegated to modular handler modules

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import threading
import json

# Import existing MANUFACTURE and Tool Library modules
from .handlers import manufacture
from . import tool_library

# Import modular system components
from .core.integration import modular_system
from .core.server import server_manager
from .core.task_queue import task_queue, TaskPriority
from .core.loader import module_loader
from .core.router import request_router
from .core.error_handling import error_handler, ErrorCategory, ErrorSeverity, handle_fusion_api_error

# Import geometry implementations
from .handlers.design import geometry_impl, geometry_impl2

# Set up module-specific logging
module_logger = error_handler.get_module_logger("fusion_bridge")

# Global state
ModelParameterSnapshot = []
app = None
ui = None
design = None
handlers = []
stopFlag = None
myCustomEvent = 'MCPTaskEvent'
customEvent = None


class TaskEventHandler(adsk.core.CustomEventHandler):
    """Custom Event Handler for processing tasks from the queue on the main UI thread"""
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        global ModelParameterSnapshot, design
        try:
            if design:
                ModelParameterSnapshot = geometry_impl2.get_model_parameters(design)
                task_queue.process_tasks()
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "notify")
            module_logger.error(f"Task event handler error: {error_response.message}")


class TaskThread(threading.Thread):
    """Background thread that fires custom events for task processing"""
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(0.2):
            try:
                app.fireCustomEvent(myCustomEvent, json.dumps({}))
            except:
                break


def register_task_handlers():
    """Register all task handlers with the centralized task queue system"""
    global design, ui
    
    # Design workspace - Geometry handlers
    task_queue.register_task_handler('set_parameter', lambda name, value: geometry_impl2.set_parameter(design, ui, name, value))
    task_queue.register_task_handler('draw_box', lambda height, width, depth, x, y, z, plane=None: geometry_impl.draw_Box(design, ui, height, width, depth, x, y, z, plane))
    task_queue.register_task_handler('draw_witzenmann', lambda scaling, z: geometry_impl.draw_Witzenmann(design, ui, scaling, z))
    task_queue.register_task_handler('export_stl', lambda name: geometry_impl2.export_as_STL(design, ui, name))
    task_queue.register_task_handler('fillet_edges', lambda radius: geometry_impl2.fillet_edges(design, ui, radius))
    task_queue.register_task_handler('export_step', lambda name: geometry_impl2.export_as_STEP(design, ui, name))
    task_queue.register_task_handler('draw_cylinder', lambda radius, height, x, y, z, plane='XY': geometry_impl2.draw_cylinder(design, ui, radius, height, x, y, z, plane))
    task_queue.register_task_handler('shell_body', lambda thickness, faceindex: geometry_impl2.shell_existing_body(design, ui, thickness, faceindex))
    task_queue.register_task_handler('undo', lambda: geometry_impl2.undo(design, ui))
    task_queue.register_task_handler('draw_lines', lambda points, plane='XY': geometry_impl2.draw_lines(design, ui, points, plane))
    task_queue.register_task_handler('extrude_last_sketch', lambda value, taperangle: geometry_impl2.extrude_last_sketch(design, ui, value, taperangle))
    task_queue.register_task_handler('revolve_profile', lambda angle: geometry_impl2.revolve_profile(design, ui, angle))
    task_queue.register_task_handler('arc', lambda point1, point2, point3, plane='XY', connect=False: geometry_impl2.arc(design, ui, point1, point2, point3, plane, connect))
    task_queue.register_task_handler('draw_one_line', lambda x1, y1, z1, x2, y2, z2, plane='XY': geometry_impl2.draw_one_line(design, ui, x1, y1, z1, x2, y2, z2, plane))
    task_queue.register_task_handler('holes', lambda points, width, depth, faceindex: geometry_impl2.holes(design, ui, points, width, depth, faceindex))
    task_queue.register_task_handler('circle', lambda radius, x, y, z, plane='XY': geometry_impl.draw_circle(design, ui, radius, x, y, z, plane))
    task_queue.register_task_handler('extrude_thin', lambda thickness, distance: geometry_impl2.extrude_thin(design, ui, thickness, distance))
    task_queue.register_task_handler('select_body', lambda bodyname: geometry_impl2.select_body(design, ui, bodyname))
    task_queue.register_task_handler('select_sketch', lambda sketchname: geometry_impl2.select_sketch(design, ui, sketchname))
    task_queue.register_task_handler('spline', lambda points, plane='XY': geometry_impl2.spline(design, ui, points, plane))
    task_queue.register_task_handler('sweep', lambda: geometry_impl2.sweep(design, ui))
    task_queue.register_task_handler('cut_extrude', lambda depth: geometry_impl2.cut_extrude(design, ui, depth))
    task_queue.register_task_handler('circular_pattern', lambda quantity, axis, plane: geometry_impl2.circular_pattern(design, ui, quantity, axis, plane))
    task_queue.register_task_handler('offsetplane', lambda offset, plane='XY': geometry_impl.offsetplane(design, ui, offset, plane))
    task_queue.register_task_handler('loft', lambda sketchcount: geometry_impl2.loft(design, ui, sketchcount))
    task_queue.register_task_handler('ellipsis', lambda x_center, y_center, z_center, x_major, y_major, z_major, x_through, y_through, z_through, plane='XY': geometry_impl.draw_ellipis(design, ui, x_center, y_center, z_center, x_major, y_major, z_major, x_through, y_through, z_through, plane))
    task_queue.register_task_handler('draw_sphere', lambda radius, x, y, z: geometry_impl.create_sphere(design, ui, radius, x, y, z))
    task_queue.register_task_handler('threaded', lambda inside, sizes: geometry_impl2.create_thread(design, ui, inside, sizes))
    task_queue.register_task_handler('delete_everything', lambda: geometry_impl2.delete(design, ui))
    task_queue.register_task_handler('boolean_operation', lambda op: geometry_impl2.boolean_operation(design, ui, op))
    task_queue.register_task_handler('draw_2d_rectangle', lambda x1, y1, z1, x2, y2, z2, plane='XY': geometry_impl.draw_2d_rect(design, ui, x1, y1, z1, x2, y2, z2, plane))
    task_queue.register_task_handler('rectangular_pattern', lambda axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane='XY': geometry_impl2.rect_pattern(design, ui, axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane))
    task_queue.register_task_handler('draw_text', lambda text, thickness, x1, y1, z1, x2, y2, z2, extrusion_value, plane='XY': geometry_impl.draw_text(design, ui, text, thickness, x1, y1, z1, x2, y2, z2, extrusion_value, plane))
    task_queue.register_task_handler('move_body', lambda x, y, z: geometry_impl.move_last_body(design, ui, x, y, z))
    
    # Research handlers
    task_queue.register_task_handler('work_coordinate_system_api_research', _run_wcs_api_research)
    task_queue.register_task_handler('model_id_research', _run_model_id_research)
    
    # Parameter handlers
    task_queue.register_task_handler('count_parameters', lambda: geometry_impl2.count_parameters(design, ui))
    task_queue.register_task_handler('list_parameters', lambda: geometry_impl2.list_parameters(design, ui))


def _run_wcs_api_research():
    """Helper function for Work Coordinate System API research"""
    try:
        from .wcs_api_research import run_wcs_api_research
        run_wcs_api_research()
    except Exception as e:
        if ui:
            ui.messageBox(f'Work Coordinate System API research error: {str(e)}')


def _run_model_id_research():
    """Helper function for model ID research"""
    try:
        from .model_id_research import run_model_id_research
        run_model_id_research()
    except Exception as e:
        if ui:
            ui.messageBox(f'Model ID research error: {str(e)}')


def register_http_routes():
    """Register all HTTP routes with the modular router"""
    global ModelParameterSnapshot
    
    # System endpoints
    request_router.register_handler('/test_connection', handle_test_connection, ['GET', 'POST'], 'system', 'main')
    request_router.register_handler('/count_parameters', handle_count_parameters, ['GET'], 'system', 'main')
    request_router.register_handler('/list_parameters', handle_list_parameters, ['GET'], 'system', 'main')
    
    # Design workspace - Geometry endpoints
    request_router.register_handler('/Box', handle_box, ['POST'], 'design', 'main')
    request_router.register_handler('/Witzenmann', handle_witzenmann, ['POST'], 'design', 'main')
    request_router.register_handler('/draw_cylinder', handle_cylinder, ['POST'], 'design', 'main')
    request_router.register_handler('/sphere', handle_sphere, ['POST'], 'design', 'main')
    request_router.register_handler('/create_circle', handle_circle, ['POST'], 'design', 'main')
    request_router.register_handler('/draw_lines', handle_draw_lines, ['POST'], 'design', 'main')
    request_router.register_handler('/draw_one_line', handle_draw_one_line, ['POST'], 'design', 'main')
    request_router.register_handler('/arc', handle_arc, ['POST'], 'design', 'main')
    request_router.register_handler('/spline', handle_spline, ['POST'], 'design', 'main')
    request_router.register_handler('/ellipsis', handle_ellipsis, ['POST'], 'design', 'main')
    request_router.register_handler('/extrude_last_sketch', handle_extrude, ['POST'], 'design', 'main')
    request_router.register_handler('/extrude_thin', handle_extrude_thin, ['POST'], 'design', 'main')
    request_router.register_handler('/cut_extrude', handle_cut_extrude, ['POST'], 'design', 'main')
    request_router.register_handler('/revolve', handle_revolve, ['POST'], 'design', 'main')
    request_router.register_handler('/sweep', handle_sweep, ['POST'], 'design', 'main')
    request_router.register_handler('/loft', handle_loft, ['POST'], 'design', 'main')
    request_router.register_handler('/fillet_edges', handle_fillet, ['POST'], 'design', 'main')
    request_router.register_handler('/shell_body', handle_shell, ['POST'], 'design', 'main')
    request_router.register_handler('/holes', handle_holes, ['POST'], 'design', 'main')
    request_router.register_handler('/threaded', handle_threaded, ['POST'], 'design', 'main')
    request_router.register_handler('/circular_pattern', handle_circular_pattern, ['POST'], 'design', 'main')
    request_router.register_handler('/rectangular_pattern', handle_rectangular_pattern, ['POST'], 'design', 'main')
    request_router.register_handler('/offsetplane', handle_offsetplane, ['POST'], 'design', 'main')
    request_router.register_handler('/boolean_operation', handle_boolean, ['POST'], 'design', 'main')
    request_router.register_handler('/select_body', handle_select_body, ['POST'], 'design', 'main')
    request_router.register_handler('/select_sketch', handle_select_sketch, ['POST'], 'design', 'main')
    request_router.register_handler('/set_parameter', handle_set_parameter, ['POST'], 'design', 'main')
    request_router.register_handler('/undo', handle_undo, ['POST'], 'design', 'main')
    request_router.register_handler('/delete_everything', handle_delete, ['POST'], 'design', 'main')
    request_router.register_handler('/Export_STL', handle_export_stl, ['POST'], 'design', 'main')
    request_router.register_handler('/Export_STEP', handle_export_step, ['POST'], 'design', 'main')
    
    # MANUFACTURE workspace - CAM endpoints
    request_router.register_handler('/cam/setups', handle_cam_setups, ['GET'], 'manufacture', 'main')
    request_router.register_handler('/cam/toolpaths', handle_cam_toolpaths, ['GET'], 'manufacture', 'main')
    request_router.register_handler('/cam/toolpaths/heights', handle_cam_toolpaths_heights, ['GET'], 'manufacture', 'main')
    request_router.register_handler('/cam/tools', handle_cam_tools, ['GET'], 'manufacture', 'main')
    
    # Tool Library endpoints
    request_router.register_handler('/tool-libraries', handle_tool_libraries, ['GET'], 'manufacture', 'main')
    
    # Research endpoints
    request_router.register_handler('/research/work_coordinate_system_api', handle_wcs_research, ['GET'], 'research', 'main')
    request_router.register_handler('/research/model-id', handle_model_id_research, ['GET'], 'research', 'main')


# HTTP Route Handlers - System
def handle_test_connection(path, method, data):
    return {"status": 200, "data": {"message": "Verbindung erfolgreich"}}

def handle_count_parameters(path, method, data):
    return {"status": 200, "data": {"user_parameter_count": len(ModelParameterSnapshot)}}

def handle_list_parameters(path, method, data):
    return {"status": 200, "data": {"ModelParameter": ModelParameterSnapshot}}


# HTTP Route Handlers - Design Workspace Geometry
def handle_box(path, method, data):
    height = float(data.get('height', 5))
    width = float(data.get('width', 5))
    depth = float(data.get('depth', 5))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    plane = data.get('plane', None)
    task_queue.queue_task('draw_box', height, width, depth, x, y, z, plane)
    return {"status": 200, "data": {"message": "Box wird erstellt"}}

def handle_witzenmann(path, method, data):
    scale = data.get('scale', 1.0)
    z = float(data.get('z', 0))
    task_queue.queue_task('draw_witzenmann', scale, z)
    return {"status": 200, "data": {"message": "Witzenmann-Logo wird erstellt"}}

def handle_cylinder(path, method, data):
    radius = float(data.get('radius', 2.5))
    height = float(data.get('height', 5))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    plane = data.get('plane', 'XY')
    task_queue.queue_task('draw_cylinder', radius, height, x, y, z, plane)
    return {"status": 200, "data": {"message": "Cylinder wird erstellt"}}

def handle_sphere(path, method, data):
    radius = float(data.get('radius', 5.0))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    task_queue.queue_task('draw_sphere', radius, x, y, z)
    return {"status": 200, "data": {"message": "Sphere wird erstellt"}}

def handle_circle(path, method, data):
    radius = float(data.get('radius', 1.0))
    x = float(data.get('x', 0))
    y = float(data.get('y', 0))
    z = float(data.get('z', 0))
    plane = data.get('plane', 'XY')
    task_queue.queue_task('circle', radius, x, y, z, plane)
    return {"status": 200, "data": {"message": "Circle wird erstellt"}}

def handle_draw_lines(path, method, data):
    points = data.get('points', [])
    plane = data.get('plane', 'XY')
    task_queue.queue_task('draw_lines', points, plane)
    return {"status": 200, "data": {"message": "Lines werden erstellt"}}

def handle_draw_one_line(path, method, data):
    x1 = float(data.get('x1', 0))
    y1 = float(data.get('y1', 0))
    z1 = float(data.get('z1', 0))
    x2 = float(data.get('x2', 1))
    y2 = float(data.get('y2', 1))
    z2 = float(data.get('z2', 0))
    plane = data.get('plane', 'XY')
    task_queue.queue_task('draw_one_line', x1, y1, z1, x2, y2, z2, plane)
    return {"status": 200, "data": {"message": "Line wird erstellt"}}

def handle_arc(path, method, data):
    point1 = data.get('point1', [0, 0])
    point2 = data.get('point2', [1, 1])
    point3 = data.get('point3', [2, 0])
    connect = bool(data.get('connect', False))
    plane = data.get('plane', 'XY')
    task_queue.queue_task('arc', point1, point2, point3, plane, connect)
    return {"status": 200, "data": {"message": "Arc wird erstellt"}}

def handle_spline(path, method, data):
    points = data.get('points', [])
    plane = data.get('plane', 'XY')
    task_queue.queue_task('spline', points, plane)
    return {"status": 200, "data": {"message": "Spline wird erstellt"}}

def handle_ellipsis(path, method, data):
    x_center = float(data.get('x_center', 0))
    y_center = float(data.get('y_center', 0))
    z_center = float(data.get('z_center', 0))
    x_major = float(data.get('x_major', 10))
    y_major = float(data.get('y_major', 0))
    z_major = float(data.get('z_major', 0))
    x_through = float(data.get('x_through', 5))
    y_through = float(data.get('y_through', 4))
    z_through = float(data.get('z_through', 0))
    plane = data.get('plane', 'XY')
    task_queue.queue_task('ellipsis', x_center, y_center, z_center, x_major, y_major, z_major, x_through, y_through, z_through, plane)
    return {"status": 200, "data": {"message": "Ellipsis wird erstellt"}}


def handle_extrude(path, method, data):
    value = float(data.get('value', 1.0))
    taperangle = float(data.get('taperangle', 0))
    task_queue.queue_task('extrude_last_sketch', value, taperangle)
    return {"status": 200, "data": {"message": "Letzter Sketch wird extrudiert"}}

def handle_extrude_thin(path, method, data):
    thickness = float(data.get('thickness', 0.5))
    distance = float(data.get('distance', 1.0))
    task_queue.queue_task('extrude_thin', thickness, distance)
    return {"status": 200, "data": {"message": "Thin Extrude wird erstellt"}}

def handle_cut_extrude(path, method, data):
    depth = float(data.get('depth', 1.0))
    task_queue.queue_task('cut_extrude', depth)
    return {"status": 200, "data": {"message": "Cut Extrude wird erstellt"}}

def handle_revolve(path, method, data):
    angle = float(data.get('angle', 360))
    task_queue.queue_task('revolve_profile', angle)
    return {"status": 200, "data": {"message": "Profil wird revolviert"}}

def handle_sweep(path, method, data):
    task_queue.queue_task('sweep')
    return {"status": 200, "data": {"message": "Sweep wird erstellt"}}

def handle_loft(path, method, data):
    sketchcount = int(data.get('sketchcount', 2))
    task_queue.queue_task('loft', sketchcount)
    return {"status": 200, "data": {"message": "Loft wird erstellt"}}

def handle_fillet(path, method, data):
    radius = float(data.get('radius', 0.3))
    task_queue.queue_task('fillet_edges', radius)
    return {"status": 200, "data": {"message": "Fillet edges started"}}

def handle_shell(path, method, data):
    thickness = float(data.get('thickness', 0.5))
    faceindex = int(data.get('faceindex', 0))
    task_queue.queue_task('shell_body', thickness, faceindex)
    return {"status": 200, "data": {"message": "Shell body wird erstellt"}}

def handle_holes(path, method, data):
    points = data.get('points', [[0, 0]])
    width = float(data.get('width', 1.0))
    faceindex = int(data.get('faceindex', 0))
    distance = data.get('depth', None)
    if distance is not None:
        distance = float(distance)
    task_queue.queue_task('holes', points, width, distance, faceindex)
    return {"status": 200, "data": {"message": "Loch wird erstellt"}}

def handle_threaded(path, method, data):
    inside = bool(data.get('inside', True))
    allsizes = int(data.get('allsizes', 30))
    task_queue.queue_task('threaded', inside, allsizes)
    return {"status": 200, "data": {"message": "Threaded Feature wird erstellt"}}

def handle_circular_pattern(path, method, data):
    quantity = float(data.get('quantity', 4))
    axis = str(data.get('axis', "X"))
    plane = str(data.get('plane', 'XY'))
    task_queue.queue_task('circular_pattern', quantity, axis, plane)
    return {"status": 200, "data": {"message": "Circular Pattern wird erstellt"}}

def handle_rectangular_pattern(path, method, data):
    axis_one = str(data.get('axis_one', 'X'))
    axis_two = str(data.get('axis_two', 'Y'))
    quantity_one = int(data.get('quantity_one', 2))
    quantity_two = int(data.get('quantity_two', 2))
    distance_one = float(data.get('distance_one', 10))
    distance_two = float(data.get('distance_two', 10))
    plane = str(data.get('plane', 'XY'))
    task_queue.queue_task('rectangular_pattern', axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane)
    return {"status": 200, "data": {"message": "Rectangular Pattern wird erstellt"}}

def handle_offsetplane(path, method, data):
    offset = float(data.get('offset', 0.0))
    plane = str(data.get('plane', 'XY'))
    task_queue.queue_task('offsetplane', offset, plane)
    return {"status": 200, "data": {"message": "Offset Plane wird erstellt"}}

def handle_boolean(path, method, data):
    operation = data.get('operation', 'join')
    task_queue.queue_task('boolean_operation', operation)
    return {"status": 200, "data": {"message": "Boolean Operation wird ausgeführt"}}

def handle_select_body(path, method, data):
    name = str(data.get('name', ''))
    task_queue.queue_task('select_body', name)
    return {"status": 200, "data": {"message": "Body wird ausgewählt"}}

def handle_select_sketch(path, method, data):
    name = str(data.get('name', ''))
    task_queue.queue_task('select_sketch', name)
    return {"status": 200, "data": {"message": "Sketch wird ausgewählt"}}

def handle_set_parameter(path, method, data):
    name = data.get('name')
    value = data.get('value')
    if name and value:
        task_queue.queue_task('set_parameter', name, value)
        return {"status": 200, "data": {"message": f"Parameter {name} wird gesetzt"}}
    return {"status": 400, "error": True, "message": "Missing name or value"}

def handle_undo(path, method, data):
    task_queue.queue_task('undo')
    return {"status": 200, "data": {"message": "Undo wird ausgeführt"}}

def handle_delete(path, method, data):
    task_queue.queue_task('delete_everything')
    return {"status": 200, "data": {"message": "Alle Bodies werden gelöscht"}}

def handle_export_stl(path, method, data):
    name = str(data.get('Name', 'Test.stl'))
    task_queue.queue_task('export_stl', name)
    return {"status": 200, "data": {"message": "STL Export gestartet"}}

def handle_export_step(path, method, data):
    name = str(data.get('name', 'Test.step'))
    task_queue.queue_task('export_step', name)
    return {"status": 200, "data": {"message": "STEP Export gestartet"}}


# HTTP Route Handlers - MANUFACTURE Workspace (CAM)
def handle_cam_setups(path, method, data):
    try:
        result = manufacture.list_setups_detailed()
        if result.get('error'):
            error_code = result.get('code', 'UNKNOWN_ERROR')
            if error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                return {"status": 400, **result}
            elif error_code == 'CAM_ACCESS_ERROR':
                return {"status": 403, **result}
            return {"status": 500, **result}
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": f"Unexpected error: {str(e)}", "code": "INTERNAL_ERROR"}

def handle_cam_toolpaths(path, method, data):
    try:
        cam_product = manufacture.get_cam_product()
        result = manufacture.list_all_toolpaths(cam_product)
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": f"Error: {str(e)}", "code": "INTERNAL_ERROR"}

def handle_cam_toolpaths_heights(path, method, data):
    try:
        result = manufacture.list_toolpaths_with_heights()
        if result.get('error'):
            error_code = result.get('code', 'UNKNOWN_ERROR')
            if error_code in ['NO_APPLICATION', 'NO_DOCUMENT', 'NO_PRODUCTS', 'NO_CAM_DATA', 'NO_CAM_SETUPS', 'CAM_NOT_INITIALIZED']:
                return {"status": 400, **result}
            elif error_code == 'CAM_ACCESS_ERROR':
                return {"status": 403, **result}
            return {"status": 500, **result}
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": f"Error: {str(e)}", "code": "INTERNAL_ERROR"}

def handle_cam_tools(path, method, data):
    try:
        cam_product = manufacture.get_cam_product()
        result = manufacture.list_all_tools(cam_product)
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": f"Error: {str(e)}", "code": "INTERNAL_ERROR"}


# HTTP Route Handlers - Tool Library
def handle_tool_libraries(path, method, data):
    try:
        result = tool_library.list_libraries()
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": f"Error: {str(e)}", "code": "INTERNAL_ERROR"}


# HTTP Route Handlers - Research
def handle_wcs_research(path, method, data):
    try:
        from .wcs_api_research import run_wcs_api_research
        result = run_wcs_api_research()
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": f"Error: {str(e)}", "code": "RESEARCH_ERROR"}

def handle_model_id_research(path, method, data):
    try:
        from .model_id_research import run_model_id_research
        result = run_model_id_research()
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 500, "error": True, "message": f"Error: {str(e)}", "code": "RESEARCH_ERROR"}


def run(context):
    """Add-in entry point - Initialize and start the modular system"""
    global app, ui, design, handlers, stopFlag, customEvent, ModelParameterSnapshot
    
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        if design is None:
            ui.messageBox("No active design open! Please open a design document.")
            return

        module_logger.info("Starting Fusion MCP Bridge")

        # Initialize modular system
        try:
            if modular_system.initialize_system():
                module_logger.info("Modular system initialized")
            else:
                module_logger.warning("Modular system initialization returned false")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.error(f"Modular system error: {error_response.message}")

        # Load handler modules
        try:
            loaded_count = module_loader.load_all_modules()
            module_logger.info(f"Loaded {loaded_count} handler modules")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.error(f"Module loading error: {error_response.message}")

        # Register task handlers
        try:
            register_task_handlers()
            module_logger.info("Task handlers registered")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.error(f"Task handler registration error: {error_response.message}")

        # Register HTTP routes
        try:
            register_http_routes()
            module_logger.info("HTTP routes registered")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.error(f"HTTP route registration error: {error_response.message}")

        # Initial parameter snapshot
        try:
            ModelParameterSnapshot = geometry_impl2.get_model_parameters(design)
            module_logger.info(f"Loaded {len(ModelParameterSnapshot)} model parameters")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.error(f"Parameter snapshot error: {error_response.message}")
            ModelParameterSnapshot = []

        # Register custom event for task processing
        try:
            customEvent = app.registerCustomEvent(myCustomEvent)
            onTaskEvent = TaskEventHandler()
            customEvent.add(onTaskEvent)
            handlers.append(onTaskEvent)
            module_logger.info("Custom event handler registered")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.error(f"Custom event registration error: {error_response.message}")

        # Start task thread
        try:
            stopFlag = threading.Event()
            taskThread = TaskThread(stopFlag)
            taskThread.daemon = True
            taskThread.start()
            module_logger.info("Task thread started")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.error(f"Task thread start error: {error_response.message}")

        # Start HTTP server
        try:
            if server_manager.start_server():
                server_info = server_manager.get_server_info()
                module_logger.info(f"HTTP server started on port {server_info['port']}")
                ui.messageBox(f"Fusion MCP Bridge started!\n"
                             f"Port: {server_info['port']}\n"
                             f"Parameters: {len(ModelParameterSnapshot)}\n"
                             f"Routes: {server_info['routes_registered']}")
            else:
                module_logger.critical("Failed to start HTTP server")
                ui.messageBox("Failed to start HTTP server!")
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.critical(f"Server startup error: {error_response.message}")
            ui.messageBox(f"Server startup error: {error_response.message}")

    except Exception as e:
        try:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "run")
            module_logger.critical(f"Critical startup error: {error_response.message}")
            ui.messageBox(f'Add-in error:\n{error_response.message}\n\n{traceback.format_exc()}')
        except:
            pass


def stop(context):
    """Add-in shutdown - Clean up all resources"""
    global stopFlag, handlers, app, customEvent
    
    module_logger.info("Stopping Fusion MCP Bridge")
    
    # Stop modular system
    try:
        modular_system.stop_system()
        module_logger.info("Modular system stopped")
    except Exception as e:
        error_response = handle_fusion_api_error(e, "fusion_bridge", "stop")
        module_logger.error(f"Modular system stop error: {error_response.message}")
    
    # Stop HTTP server
    try:
        if server_manager.stop_server():
            module_logger.info("HTTP server stopped")
        else:
            module_logger.warning("HTTP server stop returned false")
    except Exception as e:
        error_response = handle_fusion_api_error(e, "fusion_bridge", "stop")
        module_logger.error(f"HTTP server stop error: {error_response.message}")
    
    # Stop task thread
    try:
        if stopFlag:
            stopFlag.set()
            module_logger.info("Task thread stop signal sent")
    except Exception as e:
        error_response = handle_fusion_api_error(e, "fusion_bridge", "stop")
        module_logger.error(f"Task thread stop error: {error_response.message}")

    # Clean up event handlers
    cleaned_handlers = 0
    for handler in handlers:
        try:
            if customEvent:
                customEvent.remove(handler)
                cleaned_handlers += 1
        except Exception as e:
            error_response = handle_fusion_api_error(e, "fusion_bridge", "stop")
            module_logger.warning(f"Handler cleanup error: {error_response.message}")
    
    handlers.clear()
    module_logger.info(f"Cleaned up {cleaned_handlers} event handlers")

    # Clear task queue
    try:
        cleared_tasks = task_queue.clear_queue()
        module_logger.info(f"Cleared {cleared_tasks} tasks from queue")
    except Exception as e:
        error_response = handle_fusion_api_error(e, "fusion_bridge", "stop")
        module_logger.error(f"Task queue clear error: {error_response.message}")
    
    # Log final statistics
    try:
        error_stats = error_handler.get_error_statistics()
        module_logger.info(f"Final stats: {error_stats.get('total_errors', 0)} total errors")
    except Exception as e:
        module_logger.error(f"Failed to get final error statistics: {str(e)}")
    
    module_logger.info("Fusion MCP Bridge stopped")

    try:
        app = adsk.core.Application.get()
        if app:
            ui = app.userInterface
            if ui:
                ui.messageBox("Fusion MCP Bridge stopped")
    except:
        pass
