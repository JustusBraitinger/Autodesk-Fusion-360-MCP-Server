# Fusion 360 API Configuration

# Base URL für den Fusion 360 Server
BASE_URL = "http://localhost:5000"

# API Endpoints
ENDPOINTS = {
    "holes": f"{BASE_URL}/holes",
    "destroy": f"{BASE_URL}/destroy",
    "witzenmann": f"{BASE_URL}/Witzenmann",
    "spline": f"{BASE_URL}/spline",
    "sweep": f"{BASE_URL}/sweep",
    "undo": f"{BASE_URL}/undo",
    "count_parameters": f"{BASE_URL}/count_parameters",
    "list_parameters": f"{BASE_URL}/list_parameters",
    "export_step": f"{BASE_URL}/Export_STEP",
    "export_stl": f"{BASE_URL}/Export_STL",
    "fillet_edges": f"{BASE_URL}/fillet_edges",
    "change_parameter": f"{BASE_URL}/set_parameter",
    "draw_cylinder": f"{BASE_URL}/draw_cylinder",
    "draw_box": f"{BASE_URL}/Box",
    "shell_body": f"{BASE_URL}/shell_body",
    "draw_lines": f"{BASE_URL}/draw_lines",
    "extrude": f"{BASE_URL}/extrude_last_sketch",
    "extrude_thin": f"{BASE_URL}/extrude_thin",
    "cut_extrude": f"{BASE_URL}/cut_extrude",
    "revolve": f"{BASE_URL}/revolve",
    "draw_arc": f"{BASE_URL}/arc",
    "draw_one_line": f"{BASE_URL}/draw_one_line",
    "circular_pattern": f"{BASE_URL}/circular_pattern",
    "ellipsie": f"{BASE_URL}/ellipsis",
    "draw2Dcircle": f"{BASE_URL}/create_circle",
    "loft": f"{BASE_URL}/loft",
    "test_connection": f"{BASE_URL}/test_connection",
    "draw_sphere": f"{BASE_URL}/sphere",
    "threaded": f"{BASE_URL}/threaded",
    "delete_everything": f"{BASE_URL}/delete_everything",
    "boolean_operation": f"{BASE_URL}/boolean_operation"
    
}

# Request Headers
HEADERS = {
    "Content-Type": "application/json"
}

# Timeouts (in Sekunden)
REQUEST_TIMEOUT = 30
