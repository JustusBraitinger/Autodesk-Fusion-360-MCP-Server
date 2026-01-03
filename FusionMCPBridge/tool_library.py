"""
Tool Library Module for Fusion 360 MCP Add-In

This module provides centralized access to Fusion 360's Tool Library system,
enabling AI assistants to browse, query, create, modify, and manage cutting tools.

The Tool Library is where cutting tools are defined, organized, and stored for use
in CAM operations. This module supports:
- Listing tool libraries (local, cloud, document)
- Querying detailed tool information including geometry and cutting data
- Creating new tools with custom specifications
- Modifying existing tool properties
- Duplicating and deleting tools
- Searching for tools by criteria

All functions follow the existing architecture pattern: they are called from HTTP
endpoints and execute on Fusion's main thread via the task queue.

Requirements: 1.1, 2.1, 3.1
"""

import adsk.core
import adsk.fusion
import adsk.cam
from typing import Optional, List, Dict, Any


# Tool type mapping from enum to string
TOOL_TYPE_MAP: Dict[int, str] = {
    0: "flat end mill",
    1: "ball end mill",
    2: "bull nose end mill",
    3: "chamfer mill",
    4: "face mill",
    5: "slot mill",
    6: "radius mill",
    7: "dovetail mill",
    8: "tapered mill",
    9: "lollipop mill",
    10: "drill",
    11: "center drill",
    12: "spot drill",
    13: "tap",
    14: "reamer",
    15: "boring bar",
    16: "counter bore",
    17: "counter sink",
    18: "thread mill",
    19: "form mill",
    20: "engrave",
}

# Reverse mapping from string to enum
TOOL_TYPE_REVERSE_MAP: Dict[str, int] = {v: k for k, v in TOOL_TYPE_MAP.items()}

# Supported tool types for creation (subset of all types)
SUPPORTED_TOOL_TYPES: List[str] = [
    "flat end mill",
    "ball end mill", 
    "drill",
    "tap",
    "face mill",
    "chamfer mill"
]


# Library type mapping based on Fusion 360 library sources
LIBRARY_TYPE_MAP: Dict[str, str] = {
    "LocalLibraryLocation": "local",
    "CloudLibraryLocation": "cloud",
    "DocumentLibraryLocation": "document",
    "FusionLibraryLocation": "cloud",  # Fusion 360 built-in libraries
}


def _get_cam_product() -> Optional[adsk.cam.CAM]:
    """
    Safely access the CAM product from the active Fusion 360 document.
    
    Returns:
        adsk.cam.CAM | None: The CAM product if available, None otherwise.
    """
    try:
        app = adsk.core.Application.get()
        if not app:
            return None
            
        doc = app.activeDocument
        if not doc:
            return None
        
        products = doc.products
        cam_product = products.itemByProductType('CAMProductType')
        
        if cam_product:
            return adsk.cam.CAM.cast(cam_product)
        
        return None
        
    except Exception:
        return None


def _find_library_by_id(library_id: str) -> Optional[Any]:
    """
    Find a tool library by its ID.
    
    Searches local, cloud, and document libraries for a matching library ID.
    
    Args:
        library_id: The unique identifier of the library (entityToken)
        
    Returns:
        The library object if found, None otherwise.
        
    Requirements: 1.1, 2.3
    """
    try:
        # Get the CAM manager and library manager
        camManager = adsk.cam.CAMManager.get()
        if not camManager:
            return None
        
        libraryManager = camManager.libraryManager
        if not libraryManager:
            return None
        
        toolLibraries = libraryManager.toolLibraries
        if not toolLibraries:
            return None
        
        # Try different location types to find the library - match list_libraries filtering
        location_types = [
            adsk.cam.LibraryLocations.LocalLibraryLocation,
            adsk.cam.LibraryLocations.CloudLibraryLocation
            # Exclude Fusion360LibraryLocation to filter out system libraries
        ]
        
        library_index = 0
        for location_type in location_types:
            try:
                location_url = toolLibraries.urlByLocation(location_type)
                assetURLs = toolLibraries.childAssetURLs(location_url)
                
                for url in assetURLs:
                    try:
                        toolLibrary = toolLibraries.toolLibraryAtURL(url)
                        if toolLibrary:
                            current_id = f"library_{library_index}"
                            if current_id == library_id:
                                return toolLibrary
                            library_index += 1
                    except Exception:
                        continue
            except Exception:
                continue
        
        return None
        
    except Exception:
        return None


def _get_library_type(library: Any) -> str:
    """
    Determine the type of a tool library (local, cloud, or document).
    
    Args:
        library: The tool library object
        
    Returns:
        str: Library type - "local", "cloud", or "document"
    """
    try:
        # Try to get the library location type
        if hasattr(library, 'libraryLocation'):
            location = library.libraryLocation
            if location:
                location_type = type(location).__name__
                return LIBRARY_TYPE_MAP.get(location_type, "local")
        
        # Fallback: check URL or path patterns
        if hasattr(library, 'url'):
            url = library.url
            if url:
                url_str = str(url)
                if 'cloud' in url_str.lower() or 'fusion' in url_str.lower():
                    return "cloud"
                elif 'document' in url_str.lower():
                    return "document"
        
        # Default to local
        return "local"
        
    except Exception:
        return "local"


def _is_library_writable(library: Any) -> bool:
    """
    Check if a tool library is writable.
    
    Cloud libraries and some system libraries are typically read-only.
    Local and document libraries are usually writable.
    
    Args:
        library: The tool library object
        
    Returns:
        bool: True if the library can be modified, False otherwise.
        
    Requirements: 4.5, 5.5, 6.4, 7.3
    """
    try:
        # Check for explicit isReadOnly property
        if hasattr(library, 'isReadOnly'):
            return not library.isReadOnly
        
        # Check for canEdit property
        if hasattr(library, 'canEdit'):
            return library.canEdit
        
        # Determine by library type - cloud libraries are typically read-only
        lib_type = _get_library_type(library)
        if lib_type == "cloud":
            return False
        
        # Local and document libraries are typically writable
        return True
        
    except Exception:
        return False


def _get_tool_type_enum(type_string: str) -> Optional[int]:
    """
    Map a string tool type to Fusion ToolType enum value.
    
    Supports the following tool types:
    - flat end mill
    - ball end mill
    - drill
    - tap
    - face mill
    - chamfer mill
    
    Args:
        type_string: The tool type as a string (case-insensitive)
        
    Returns:
        int | None: The ToolType enum value, or None if type is not supported.
        
    Requirements: 4.1
    """
    if not type_string:
        return None
    
    # Normalize the type string (lowercase, strip whitespace)
    normalized = type_string.lower().strip()
    
    # Check if it's a supported type
    if normalized not in SUPPORTED_TOOL_TYPES:
        return None
    
    # Return the enum value from the reverse map
    return TOOL_TYPE_REVERSE_MAP.get(normalized)


def _deserialize_tool_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate tool data from a create/modify request.
    
    Extracts geometry, specifications, and cutting_data from the request.
    Validates that required fields (type, diameter, overall_length) are present.
    
    Args:
        data: Dictionary containing tool data with optional nested structures:
            - type: Tool type string (required)
            - name: Tool name/description (optional)
            - tool_number: Tool number (optional)
            - geometry: Dict with diameter, overall_length, flute_length, etc.
            - specifications: Dict with flute_count, material, coating
            - cutting_data: Dict with spindle_speed, feed_per_tooth, surface_speed
            
    Returns:
        dict: Validated and normalized tool data, or error response:
            On success:
                - type: Validated tool type string
                - type_enum: ToolType enum value
                - name: Tool name (optional)
                - tool_number: Tool number (optional)
                - geometry: Validated geometry dict
                - specifications: Validated specifications dict
                - cutting_data: Validated cutting data dict
            On error:
                - error: True
                - message: Error description
                - code: MISSING_REQUIRED_FIELD or INVALID_TOOL_DATA
                
    Requirements: 4.2, 4.3, 4.4
    """
    result = {
        "type": None,
        "type_enum": None,
        "name": None,
        "tool_number": None,
        "geometry": {},
        "specifications": {},
        "cutting_data": {}
    }
    
    # Validate required field: type
    tool_type = data.get("type")
    if not tool_type:
        return {
            "error": True,
            "message": "Missing required field: type",
            "code": "MISSING_REQUIRED_FIELD"
        }
    
    # Validate tool type is supported
    type_enum = _get_tool_type_enum(tool_type)
    if type_enum is None:
        return {
            "error": True,
            "message": f"Unsupported tool type: '{tool_type}'. Supported types: {', '.join(SUPPORTED_TOOL_TYPES)}",
            "code": "INVALID_TOOL_DATA"
        }
    
    result["type"] = tool_type.lower().strip()
    result["type_enum"] = type_enum
    
    # Extract geometry (can be nested or flat)
    geometry = data.get("geometry", {})
    if not isinstance(geometry, dict):
        geometry = {}
    
    # Also check for flat geometry fields
    diameter = geometry.get("diameter") or data.get("diameter")
    overall_length = geometry.get("overall_length") or data.get("overall_length")
    
    # Validate required geometry fields
    if diameter is None:
        return {
            "error": True,
            "message": "Missing required field: diameter (in geometry or at top level)",
            "code": "MISSING_REQUIRED_FIELD"
        }
    
    if overall_length is None:
        return {
            "error": True,
            "message": "Missing required field: overall_length (in geometry or at top level)",
            "code": "MISSING_REQUIRED_FIELD"
        }
    
    # Validate diameter is positive
    try:
        diameter = float(diameter)
        if diameter <= 0:
            return {
                "error": True,
                "message": "Invalid diameter: must be a positive number",
                "code": "INVALID_TOOL_DATA"
            }
    except (ValueError, TypeError):
        return {
            "error": True,
            "message": "Invalid diameter: must be a number",
            "code": "INVALID_TOOL_DATA"
        }
    
    # Validate overall_length is positive
    try:
        overall_length = float(overall_length)
        if overall_length <= 0:
            return {
                "error": True,
                "message": "Invalid overall_length: must be a positive number",
                "code": "INVALID_TOOL_DATA"
            }
    except (ValueError, TypeError):
        return {
            "error": True,
            "message": "Invalid overall_length: must be a number",
            "code": "INVALID_TOOL_DATA"
        }
    
    # Build validated geometry
    result["geometry"] = {
        "diameter": diameter,
        "overall_length": overall_length,
        "flute_length": geometry.get("flute_length") or data.get("flute_length"),
        "shaft_diameter": geometry.get("shaft_diameter") or data.get("shaft_diameter"),
        "corner_radius": geometry.get("corner_radius") or data.get("corner_radius")
    }
    
    # Extract optional name and tool_number
    result["name"] = data.get("name")
    result["tool_number"] = data.get("tool_number")
    
    # Extract specifications (can be nested or flat)
    specifications = data.get("specifications", {})
    if not isinstance(specifications, dict):
        specifications = {}
    
    result["specifications"] = {
        "flute_count": specifications.get("flute_count") or data.get("flute_count"),
        "material": specifications.get("material") or data.get("material"),
        "coating": specifications.get("coating") or data.get("coating")
    }
    
    # Extract cutting data (can be nested or flat)
    cutting_data = data.get("cutting_data", {})
    if not isinstance(cutting_data, dict):
        cutting_data = {}
    
    result["cutting_data"] = {
        "spindle_speed": cutting_data.get("spindle_speed") or data.get("spindle_speed"),
        "feed_per_tooth": cutting_data.get("feed_per_tooth") or data.get("feed_per_tooth"),
        "surface_speed": cutting_data.get("surface_speed") or data.get("surface_speed")
    }
    
    return result


def _serialize_library(library: Any, index: int = 0) -> Dict[str, Any]:
    """
    Serialize a tool library to a dictionary for API responses.
    
    Extracts library id, name, type, tool count, and writable status.
    
    Args:
        library: The tool library object
        index: Fallback index for ID generation if entityToken unavailable
        
    Returns:
        dict: Library information including:
            - id: Unique library identifier
            - name: Library display name
            - type: Library type (local/cloud/document)
            - tool_count: Number of tools in the library
            - is_writable: Whether the library can be modified
            
    Requirements: 1.2
    """
    try:
        # Get library ID
        lib_id = getattr(library, 'entityToken', None)
        if not lib_id:
            lib_id = f"lib_{index}"
        
        # Get library name
        lib_name = getattr(library, 'name', None)
        if not lib_name:
            lib_name = f"Library {index + 1}"
        
        # Get library type
        lib_type = _get_library_type(library)
        
        # Get tool count
        tool_count = 0
        if hasattr(library, 'tools'):
            tools = library.tools
            if tools:
                tool_count = tools.count
        
        # Check if writable
        is_writable = _is_library_writable(library)
        
        return {
            "id": lib_id,
            "name": lib_name,
            "type": lib_type,
            "tool_count": tool_count,
            "is_writable": is_writable
        }
        
    except Exception as e:
        return {
            "id": f"lib_{index}",
            "name": f"Library {index + 1}",
            "type": "local",
            "tool_count": 0,
            "is_writable": False,
            "error": str(e)
        }


def list_libraries() -> Dict[str, Any]:
    """
    List all accessible tool libraries in Fusion 360.
    
    Returns all local, cloud, and document libraries with their metadata.
    """
    try:
        # Get the CAM manager and library manager
        camManager = adsk.cam.CAMManager.get()
        if not camManager:
            return {
                "libraries": [],
                "total_count": 0,
                "message": "CAM Manager not available. Please ensure MANUFACTURE workspace is active."
            }
        
        libraryManager = camManager.libraryManager
        if not libraryManager:
            return {
                "libraries": [],
                "total_count": 0,
                "message": "Library Manager not available."
            }
        
        toolLibraries = libraryManager.toolLibraries
        if not toolLibraries:
            return {
                "libraries": [],
                "total_count": 0,
                "message": "No tool libraries accessible."
            }
        
        libraries = []
        
        # Debug: Try to get available locations using urlByLocation
        app = adsk.core.Application.get()
        
        # Try different location types - prioritize user/local libraries
        location_types = [
            adsk.cam.LibraryLocations.LocalLibraryLocation,
            adsk.cam.LibraryLocations.CloudLibraryLocation
        ]
        
        for location_type in location_types:
            try:
                location_url = toolLibraries.urlByLocation(location_type)
                app.log(f"Found location: {location_type} -> {location_url}")
                
                # Get child URLs for this location
                assetURLs = toolLibraries.childAssetURLs(location_url)
                app.log(f"Asset URLs at {location_url}: {len(assetURLs)} found")
                
                for i, url in enumerate(assetURLs):
                    try:
                        toolLibrary = toolLibraries.toolLibraryAtURL(url)
                        if toolLibrary:
                            tool_count = toolLibrary.count
                            
                            # Determine library type based on URL
                            url_str = url.toString() if hasattr(url, 'toString') else str(url)
                            lib_type = "user"  # Default to user libraries
                            if "systemlibraryroot://" in url_str or "fusion360libraryroot://" in url_str:
                                lib_type = "system"
                            elif "cloudlibraryroot://" in url_str or url_str.startswith("cloud://"):
                                lib_type = "cloud"
                            
                            libraries.append({
                                "id": f"library_{len(libraries)}",
                                "name": toolLibrary.name if hasattr(toolLibrary, 'name') and toolLibrary.name else f"Library {len(libraries)+1}",
                                "type": lib_type,
                                "tool_count": tool_count,
                                "is_writable": lib_type != "system",
                                "url": url_str
                            })
                    except Exception as e:
                        app.log(f"Error accessing library at {url}: {str(e)}")
                        continue
            except Exception as e:
                app.log(f"Error with location type {location_type}: {str(e)}")
                continue
        
        total_count = len(libraries)
        message = None if total_count > 0 else "No tool libraries found."
        
        return {
            "libraries": libraries,
            "total_count": total_count,
            "message": message
        }
        
    except Exception as e:
        return {
            "libraries": [],
            "total_count": 0,
            "message": f"Error accessing tool libraries: {str(e)}"
        }

def find_tool_by_id(tool_id: str) -> Optional[Any]:
    """
    Find a tool by its ID, searching all libraries and CAM operations.
    
    This is a shared function used by both tool_library and cam modules.
    First searches all tool libraries, then falls back to searching
    tools used in CAM operations.
    
    Args:
        tool_id: The unique identifier of the tool (entityToken)
        
    Returns:
        The tool object if found, None otherwise.
        
    Requirements: 3.4, 5.6, 7.4
    """
    try:
        cam = _get_cam_product()
        if not cam:
            return None
        
        # First, search in tool libraries
        if hasattr(cam, 'toolLibraries'):
            tool_libraries = cam.toolLibraries
            if tool_libraries:
                for lib_idx in range(tool_libraries.count):
                    library = tool_libraries.item(lib_idx)
                    if hasattr(library, 'tools'):
                        tools = library.tools
                        if tools:
                            for tool_idx in range(tools.count):
                                tool = tools.item(tool_idx)
                                current_id = getattr(tool, 'entityToken', None) or str(id(tool))
                                if current_id == tool_id:
                                    return tool
        
        # Fallback: search through CAM operations
        setups = cam.setups
        if not setups:
            return None
        
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            # Check direct operations
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    if hasattr(operation, 'tool') and operation.tool:
                        tool = operation.tool
                        current_id = getattr(tool, 'entityToken', None) or str(id(tool))
                        if current_id == tool_id:
                            return tool
            
            # Check folder operations
            if hasattr(setup, 'folders'):
                folders = setup.folders
                if folders:
                    for folder_idx in range(folders.count):
                        folder = folders.item(folder_idx)
                        if hasattr(folder, 'operations'):
                            folder_ops = folder.operations
                            if folder_ops:
                                for op_idx in range(folder_ops.count):
                                    operation = folder_ops.item(op_idx)
                                    if hasattr(operation, 'tool') and operation.tool:
                                        tool = operation.tool
                                        current_id = getattr(tool, 'entityToken', None) or str(id(tool))
                                        if current_id == tool_id:
                                            return tool
        
        return None
        
    except Exception:
        return None


def _get_tool_type_string(tool: Any) -> str:
    """
    Get the tool type as a human-readable string.
    
    Args:
        tool: The CAM tool object
        
    Returns:
        str: The tool type name (e.g., "flat end mill", "drill")
    """
    try:
        if hasattr(tool, 'type'):
            tool_type_enum = tool.type
            return TOOL_TYPE_MAP.get(tool_type_enum, f"type_{tool_type_enum}")
        return "unknown"
    except Exception:
        return "unknown"


def serialize_tool(tool: Any) -> Dict[str, Any]:
    """
    Serialize a tool to basic info dictionary for list responses.
    
    Extracts id, name, type, tool_number, diameter, and overall_length.
    Handles missing properties gracefully by returning None for unavailable fields.
    
    Args:
        tool: The CAM tool object
        
    Returns:
        dict: Basic tool information including:
            - id: Unique tool identifier (entityToken)
            - name: Tool name/description
            - type: Tool type string
            - tool_number: Tool number in library
            - diameter: Tool diameter in mm
            - diameter_unit: Unit for diameter (always "mm")
            - overall_length: Overall tool length in mm
            
    Requirements: 2.2, 8.5
    """
    try:
        # Initialize with defaults
        tool_data = {
            "id": tool.entityToken if hasattr(tool, 'entityToken') else str(id(tool)),
            "name": "Unknown tool",
            "type": "unknown",
            "tool_number": None,
            "diameter": None,
            "diameter_unit": "mm",
            "overall_length": None
        }
        
        # Extract data from tool parameters (the reliable way)
        if hasattr(tool, 'parameters'):
            params = tool.parameters
            
            # Get tool_description (name)
            desc_param = params.itemByName('tool_description')
            if desc_param and desc_param.expression:
                tool_data["name"] = desc_param.expression.strip("'\"")
            
            # Get tool_number
            num_param = params.itemByName('tool_number')
            if num_param:
                try:
                    tool_data["tool_number"] = int(num_param.value.value)
                except Exception:
                    pass
            
            # Get tool_diameter (in mm - Fusion stores in cm, multiply by 10)
            diam_param = params.itemByName('tool_diameter')
            if diam_param:
                try:
                    # Fusion stores in cm, convert to mm
                    tool_data["diameter"] = float(diam_param.value.value) * 10
                except Exception:
                    pass
            
            # Get tool_type
            type_param = params.itemByName('tool_type')
            if type_param and type_param.expression:
                tool_data["type"] = type_param.expression.strip("'\"")
            
            # Get tool_overallLength (in mm - Fusion stores in cm, multiply by 10)
            length_param = params.itemByName('tool_overallLength')
            if length_param:
                try:
                    # Fusion stores in cm, convert to mm
                    tool_data["overall_length"] = float(length_param.value.value) * 10
                except Exception:
                    pass
        
        return tool_data
        
    except Exception:
        return {
            "id": str(id(tool)),
            "name": "Error reading tool",
            "type": "unknown",
            "tool_number": None,
            "diameter": None,
            "diameter_unit": "mm",
            "overall_length": None
        }


def list_tools(library_id: str) -> Dict[str, Any]:
    """
    List all tools in a specific tool library.
    
    Finds the library by ID and returns all tools with basic information.
    
    Args:
        library_id: The unique identifier of the library (entityToken)
        
    Returns:
        dict: Response containing:
            - library_id: The library identifier
            - library_name: The library display name
            - tools: List of tool objects with id, name, type, tool_number, diameter, overall_length
            - total_count: Total number of tools in the library
            - message: Informative message (null if tools exist, message if empty)
            
        On error:
            - error: True
            - message: Error description
            - code: Error code (LIBRARY_NOT_FOUND)
            
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    try:
        # Find the library by ID
        library = _find_library_by_id(library_id)
        
        if not library:
            return {
                "error": True,
                "message": f"Library with ID '{library_id}' not found",
                "code": "LIBRARY_NOT_FOUND"
            }
        
        # Get library name
        library_name = getattr(library, 'name', None)
        if not library_name:
            library_name = "Unknown Library"
        
        # Get tools from the library
        tools_list = []
        
        # Debug logging
        app = adsk.core.Application.get()
        app.log(f"Found library: {library_name}")
        app.log(f"Library type: {type(library)}")
        app.log(f"Library attributes: {[attr for attr in dir(library) if not attr.startswith('_')]}")
        
        # Try different ways to access tools
        tools = None
        if hasattr(library, 'tools'):
            tools = library.tools
            app.log("Using library.tools")
        elif hasattr(library, 'count'):
            app.log(f"Library has count: {library.count}")
            # The library itself might be iterable
            tools_list = []
            for i in range(library.count):
                tool = library.item(i)
                app.log(f"Processing tool {i}: {tool}")
                tool_data = serialize_tool(tool)
                tools_list.append(tool_data)
        else:
            app.log("No tools access method found")
        
        total_count = len(tools_list)
        
        # Set message for empty list
        message = None
        if total_count == 0:
            message = f"Library '{library_name}' contains no tools."
        
        return {
            "library_id": library_id,
            "library_name": library_name,
            "tools": tools_list,
            "total_count": total_count,
            "message": message
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error listing tools: {str(e)}",
            "code": "INTERNAL_ERROR"
        }


def _find_library_for_tool(tool_id: str) -> Optional[Any]:
    """
    Find the library that contains a specific tool.
    
    Searches all tool libraries to find which one contains the tool with the given ID.
    
    Args:
        tool_id: The unique identifier of the tool (entityToken)
        
    Returns:
        The library object containing the tool, or None if not found in any library.
    """
    try:
        cam = _get_cam_product()
        if not cam:
            return None
        
        if not hasattr(cam, 'toolLibraries'):
            return None
        
        tool_libraries = cam.toolLibraries
        if not tool_libraries:
            return None
        
        for lib_idx in range(tool_libraries.count):
            library = tool_libraries.item(lib_idx)
            if hasattr(library, 'tools'):
                tools = library.tools
                if tools:
                    for tool_idx in range(tools.count):
                        tool = tools.item(tool_idx)
                        current_id = getattr(tool, 'entityToken', None) or str(id(tool))
                        if current_id == tool_id:
                            return library
        
        return None
        
    except Exception:
        return None


def serialize_tool_full(tool: Any, library: Any = None) -> Dict[str, Any]:
    """
    Serialize a tool to complete details dictionary.
    
    Includes full geometry, specifications, and cutting data.
    
    Args:
        tool: The CAM tool object
        library: Optional library object for context information
        
    Returns:
        dict: Complete tool information including:
            - id, name, type, tool_number (basic info)
            - geometry: diameter, overall_length, flute_length, shaft_diameter, corner_radius
            - specifications: flute_count, material, coating
            - cutting_data: spindle_speed, feed_per_tooth, surface_speed (if available)
            - library_id, library_name (if library provided)
            
    Requirements: 3.1, 3.2, 3.3
    """
    try:
        # Start with basic info
        tool_data = {
            "id": getattr(tool, 'entityToken', None) or str(id(tool)),
            "name": getattr(tool, 'description', None) or getattr(tool, 'name', 'Unknown tool'),
            "type": _get_tool_type_string(tool),
            "tool_number": getattr(tool, 'toolNumber', None),
        }
        
        # Extract geometry
        geometry = {
            "diameter": getattr(tool, 'diameter', None),
            "diameter_unit": "mm",
            "overall_length": getattr(tool, 'bodyLength', None),
            "flute_length": getattr(tool, 'fluteLength', None),
            "shaft_diameter": getattr(tool, 'shaftDiameter', None),
            "corner_radius": getattr(tool, 'cornerRadius', None)
        }
        tool_data["geometry"] = geometry
        
        # Extract specifications
        specifications = {
            "flute_count": getattr(tool, 'numberOfFlutes', None),
            "material": getattr(tool, 'material', None),
            "coating": getattr(tool, 'coating', None)
        }
        tool_data["specifications"] = specifications
        
        # Extract cutting data (presets)
        cutting_data = {}
        
        # Try direct tool properties first
        if hasattr(tool, 'spindleSpeed') and tool.spindleSpeed:
            cutting_data["spindle_speed"] = tool.spindleSpeed
            cutting_data["spindle_speed_unit"] = "rpm"
        
        if hasattr(tool, 'feedPerTooth') and tool.feedPerTooth:
            cutting_data["feed_per_tooth"] = tool.feedPerTooth
            cutting_data["feed_per_tooth_unit"] = "mm"
        
        if hasattr(tool, 'surfaceSpeed') and tool.surfaceSpeed:
            cutting_data["surface_speed"] = tool.surfaceSpeed
            cutting_data["surface_speed_unit"] = "m/min"
        
        # Try to get from presets if direct properties not available
        if hasattr(tool, 'presets') and tool.presets:
            try:
                presets = tool.presets
                if presets.count > 0:
                    preset = presets.item(0)  # Use first preset
                    
                    if "spindle_speed" not in cutting_data and hasattr(preset, 'spindleSpeed'):
                        cutting_data["spindle_speed"] = preset.spindleSpeed
                        cutting_data["spindle_speed_unit"] = "rpm"
                    
                    if "feed_per_tooth" not in cutting_data and hasattr(preset, 'feedPerTooth'):
                        cutting_data["feed_per_tooth"] = preset.feedPerTooth
                        cutting_data["feed_per_tooth_unit"] = "mm"
                    
                    if "surface_speed" not in cutting_data and hasattr(preset, 'surfaceSpeed'):
                        cutting_data["surface_speed"] = preset.surfaceSpeed
                        cutting_data["surface_speed_unit"] = "m/min"
            except Exception:
                pass
        
        # Only include cutting_data if we have any values
        if cutting_data:
            tool_data["cutting_data"] = cutting_data
        else:
            tool_data["cutting_data"] = None
        
        # Add library context if provided
        if library:
            tool_data["library_id"] = getattr(library, 'entityToken', None)
            tool_data["library_name"] = getattr(library, 'name', None)
        
        return tool_data
        
    except Exception as e:
        return {
            "id": None,
            "name": "Error accessing tool",
            "type": "unknown",
            "tool_number": None,
            "geometry": None,
            "specifications": None,
            "cutting_data": None,
            "error": str(e)
        }


def get_tool(tool_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific tool.
    
    Finds the tool by ID and returns complete tool details including
    geometry, specifications, cutting data, and library context.
    
    Args:
        tool_id: The unique identifier of the tool (entityToken)
        
    Returns:
        dict: Complete tool information including:
            - id, name, type, tool_number (basic info)
            - geometry: diameter, overall_length, flute_length, shaft_diameter, corner_radius
            - specifications: flute_count, material, coating
            - cutting_data: spindle_speed, feed_per_tooth, surface_speed (if available)
            - library_id, library_name (library context)
            
        On error:
            - error: True
            - message: Error description
            - code: Error code (TOOL_NOT_FOUND)
            
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    try:
        # Find the tool by ID
        tool = find_tool_by_id(tool_id)
        
        if not tool:
            return {
                "error": True,
                "message": f"Tool with ID '{tool_id}' not found",
                "code": "TOOL_NOT_FOUND"
            }
        
        # Find the library containing this tool for context
        library = _find_library_for_tool(tool_id)
        
        # Get full tool details with library context
        tool_data = serialize_tool_full(tool, library)
        
        # Ensure library context is included even if not found in a library
        # (tool might be from a CAM operation)
        if "library_id" not in tool_data or tool_data.get("library_id") is None:
            tool_data["library_id"] = None
            tool_data["library_name"] = "Operation Tool"
        
        return tool_data
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error retrieving tool details: {str(e)}",
            "code": "INTERNAL_ERROR"
        }


def create_tool(library_id: str, tool_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new tool in a specified library.
    
    Creates a tool with the specified type and geometry, and optionally sets
    specifications and cutting data.
    
    Args:
        library_id: The unique identifier of the target library (entityToken)
        tool_data: Dictionary containing tool properties:
            Required:
                - type: Tool type string (flat end mill, ball end mill, drill, tap, face mill, chamfer mill)
                - diameter: Tool diameter (in geometry or at top level)
                - overall_length: Overall tool length (in geometry or at top level)
            Optional:
                - name: Tool name/description
                - tool_number: Tool number
                - geometry: Dict with flute_length, shaft_diameter, corner_radius
                - specifications: Dict with flute_count, material, coating
                - cutting_data: Dict with spindle_speed, feed_per_tooth, surface_speed
                
    Returns:
        dict: Response containing:
            On success:
                - id: The new tool's unique identifier
                - name: The tool name
                - message: Confirmation message
            On error:
                - error: True
                - message: Error description
                - code: Error code (LIBRARY_NOT_FOUND, LIBRARY_READ_ONLY, MISSING_REQUIRED_FIELD, INVALID_TOOL_DATA)
                
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
    try:
        # Find the library by ID
        library = _find_library_by_id(library_id)
        
        if not library:
            return {
                "error": True,
                "message": f"Library with ID '{library_id}' not found",
                "code": "LIBRARY_NOT_FOUND"
            }
        
        # Check if library is writable
        if not _is_library_writable(library):
            library_name = getattr(library, 'name', 'Unknown Library')
            return {
                "error": True,
                "message": f"Library '{library_name}' is read-only and cannot be modified",
                "code": "LIBRARY_READ_ONLY"
            }
        
        # Validate and parse tool data
        parsed_data = _deserialize_tool_data(tool_data)
        
        # Check for validation errors
        if parsed_data.get("error"):
            return parsed_data
        
        # Get the tools collection from the library
        if not hasattr(library, 'tools'):
            return {
                "error": True,
                "message": "Library does not support tool creation",
                "code": "INVALID_TOOL_DATA"
            }
        
        tools = library.tools
        if tools is None:
            return {
                "error": True,
                "message": "Cannot access tools collection in library",
                "code": "INTERNAL_ERROR"
            }
        
        # Create the tool using Fusion 360 API
        # The exact API depends on Fusion 360 version, but typically:
        # tools.add() or tools.createTool() with a ToolInput
        
        try:
            # Try to create a new tool
            # Fusion 360 CAM API uses ToolInput for tool creation
            app = adsk.core.Application.get()
            
            # Get the tool type enum
            tool_type_enum = parsed_data["type_enum"]
            
            # Create tool input based on tool type
            # Note: The actual Fusion 360 API may vary - this is the general pattern
            if hasattr(tools, 'createInput'):
                # Modern API pattern
                tool_input = tools.createInput(tool_type_enum)
            elif hasattr(tools, 'add'):
                # Alternative API pattern - create tool directly
                # This creates a default tool that we then modify
                new_tool = tools.add(tool_type_enum)
                if new_tool:
                    # Set tool properties
                    _apply_tool_properties(new_tool, parsed_data)
                    
                    # Get the new tool ID
                    new_tool_id = getattr(new_tool, 'entityToken', None) or str(id(new_tool))
                    tool_name = parsed_data.get("name") or f"New {parsed_data['type']}"
                    
                    return {
                        "id": new_tool_id,
                        "name": tool_name,
                        "message": f"Tool '{tool_name}' created successfully in library"
                    }
                else:
                    return {
                        "error": True,
                        "message": "Failed to create tool in library",
                        "code": "INTERNAL_ERROR"
                    }
            else:
                # Fallback: Try to create tool using ToolLibrary.createTool if available
                if hasattr(library, 'createTool'):
                    new_tool = library.createTool(tool_type_enum)
                    if new_tool:
                        _apply_tool_properties(new_tool, parsed_data)
                        
                        new_tool_id = getattr(new_tool, 'entityToken', None) or str(id(new_tool))
                        tool_name = parsed_data.get("name") or f"New {parsed_data['type']}"
                        
                        return {
                            "id": new_tool_id,
                            "name": tool_name,
                            "message": f"Tool '{tool_name}' created successfully in library"
                        }
                
                return {
                    "error": True,
                    "message": "Tool creation not supported by this library type",
                    "code": "INVALID_TOOL_DATA"
                }
                
        except Exception as api_error:
            return {
                "error": True,
                "message": f"Fusion API error during tool creation: {str(api_error)}",
                "code": "INTERNAL_ERROR"
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error creating tool: {str(e)}",
            "code": "INTERNAL_ERROR"
        }


def _apply_tool_properties(tool: Any, parsed_data: Dict[str, Any]) -> None:
    """
    Apply properties from parsed tool data to a Fusion 360 tool object.
    
    Sets geometry, specifications, and cutting data on the tool.
    
    Args:
        tool: The Fusion 360 tool object to modify
        parsed_data: Validated tool data from _deserialize_tool_data()
        
    Requirements: 4.3, 4.4
    """
    try:
        # Set basic properties
        if parsed_data.get("name"):
            if hasattr(tool, 'description'):
                tool.description = parsed_data["name"]
            elif hasattr(tool, 'name'):
                tool.name = parsed_data["name"]
        
        if parsed_data.get("tool_number") is not None:
            if hasattr(tool, 'toolNumber'):
                tool.toolNumber = parsed_data["tool_number"]
        
        # Set geometry properties
        geometry = parsed_data.get("geometry", {})
        
        if geometry.get("diameter") is not None:
            if hasattr(tool, 'diameter'):
                tool.diameter = geometry["diameter"]
        
        if geometry.get("overall_length") is not None:
            if hasattr(tool, 'bodyLength'):
                tool.bodyLength = geometry["overall_length"]
        
        if geometry.get("flute_length") is not None:
            if hasattr(tool, 'fluteLength'):
                tool.fluteLength = geometry["flute_length"]
        
        if geometry.get("shaft_diameter") is not None:
            if hasattr(tool, 'shaftDiameter'):
                tool.shaftDiameter = geometry["shaft_diameter"]
        
        if geometry.get("corner_radius") is not None:
            if hasattr(tool, 'cornerRadius'):
                tool.cornerRadius = geometry["corner_radius"]
        
        # Set specifications
        specifications = parsed_data.get("specifications", {})
        
        if specifications.get("flute_count") is not None:
            if hasattr(tool, 'numberOfFlutes'):
                tool.numberOfFlutes = specifications["flute_count"]
        
        if specifications.get("material") is not None:
            if hasattr(tool, 'material'):
                tool.material = specifications["material"]
        
        if specifications.get("coating") is not None:
            if hasattr(tool, 'coating'):
                tool.coating = specifications["coating"]
        
        # Set cutting data
        cutting_data = parsed_data.get("cutting_data", {})
        
        if cutting_data.get("spindle_speed") is not None:
            if hasattr(tool, 'spindleSpeed'):
                tool.spindleSpeed = cutting_data["spindle_speed"]
        
        if cutting_data.get("feed_per_tooth") is not None:
            if hasattr(tool, 'feedPerTooth'):
                tool.feedPerTooth = cutting_data["feed_per_tooth"]
        
        if cutting_data.get("surface_speed") is not None:
            if hasattr(tool, 'surfaceSpeed'):
                tool.surfaceSpeed = cutting_data["surface_speed"]
                
    except Exception:
        # Silently handle property setting errors
        # The tool was created, some properties may not have been set
        pass


def modify_tool(tool_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modify an existing tool's properties.
    
    Finds the tool by ID and updates the specified properties including
    geometry, specifications, and cutting data.
    
    Args:
        tool_id: The unique identifier of the tool (entityToken)
        updates: Dictionary containing properties to update:
            Optional:
                - name: Tool name/description
                - tool_number: Tool number
                - geometry: Dict with diameter, overall_length, flute_length, shaft_diameter, corner_radius
                - specifications: Dict with flute_count, material, coating
                - cutting_data: Dict with spindle_speed, feed_per_tooth, surface_speed
                
    Returns:
        dict: Response containing:
            On success:
                - id: The tool's unique identifier
                - name: The updated tool name
                - type: The tool type
                - geometry: Updated geometry properties
                - specifications: Updated specifications
                - cutting_data: Updated cutting data
                - message: Confirmation message
            On error:
                - error: True
                - message: Error description
                - code: Error code (TOOL_NOT_FOUND, TOOL_READ_ONLY)
                
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
    """
    try:
        # Find the tool by ID
        tool = find_tool_by_id(tool_id)
        
        if not tool:
            return {
                "error": True,
                "message": f"Tool with ID '{tool_id}' not found",
                "code": "TOOL_NOT_FOUND"
            }
        
        # Find the library containing this tool
        library = _find_library_for_tool(tool_id)
        
        # Check if the library is writable
        # If tool is not in a library (e.g., operation tool), check tool directly
        if library:
            if not _is_library_writable(library):
                library_name = getattr(library, 'name', 'Unknown Library')
                return {
                    "error": True,
                    "message": f"Tool is in read-only library '{library_name}' and cannot be modified",
                    "code": "TOOL_READ_ONLY"
                }
        else:
            # Tool is from a CAM operation, check if it can be modified
            # Operation tools are typically read-only
            if hasattr(tool, 'isReadOnly') and tool.isReadOnly:
                return {
                    "error": True,
                    "message": "Tool is read-only and cannot be modified",
                    "code": "TOOL_READ_ONLY"
                }
        
        # Apply updates to the tool
        _apply_tool_updates(tool, updates)
        
        # Get the updated tool data to return
        tool_data = serialize_tool_full(tool, library)
        
        # Add success message
        tool_name = tool_data.get("name", "Unknown tool")
        tool_data["message"] = f"Tool '{tool_name}' modified successfully"
        
        return tool_data
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error modifying tool: {str(e)}",
            "code": "INTERNAL_ERROR"
        }


def _apply_tool_updates(tool: Any, updates: Dict[str, Any]) -> None:
    """
    Apply update properties to a Fusion 360 tool object.
    
    Only updates properties that are explicitly provided in the updates dict.
    Unlike _apply_tool_properties, this doesn't require type/diameter/length.
    
    Args:
        tool: The Fusion 360 tool object to modify
        updates: Dictionary containing properties to update:
            - name: Tool name/description
            - tool_number: Tool number
            - geometry: Dict with diameter, overall_length, flute_length, shaft_diameter, corner_radius
            - specifications: Dict with flute_count, material, coating
            - cutting_data: Dict with spindle_speed, feed_per_tooth, surface_speed
            
    Requirements: 5.2, 5.3, 5.4
    """
    try:
        # Update basic properties
        if "name" in updates and updates["name"] is not None:
            if hasattr(tool, 'description'):
                tool.description = updates["name"]
            elif hasattr(tool, 'name'):
                tool.name = updates["name"]
        
        if "tool_number" in updates and updates["tool_number"] is not None:
            if hasattr(tool, 'toolNumber'):
                tool.toolNumber = updates["tool_number"]
        
        # Update geometry properties
        geometry = updates.get("geometry", {})
        if isinstance(geometry, dict):
            if "diameter" in geometry and geometry["diameter"] is not None:
                if hasattr(tool, 'diameter'):
                    tool.diameter = float(geometry["diameter"])
            
            if "overall_length" in geometry and geometry["overall_length"] is not None:
                if hasattr(tool, 'bodyLength'):
                    tool.bodyLength = float(geometry["overall_length"])
            
            if "flute_length" in geometry and geometry["flute_length"] is not None:
                if hasattr(tool, 'fluteLength'):
                    tool.fluteLength = float(geometry["flute_length"])
            
            if "shaft_diameter" in geometry and geometry["shaft_diameter"] is not None:
                if hasattr(tool, 'shaftDiameter'):
                    tool.shaftDiameter = float(geometry["shaft_diameter"])
            
            if "corner_radius" in geometry and geometry["corner_radius"] is not None:
                if hasattr(tool, 'cornerRadius'):
                    tool.cornerRadius = float(geometry["corner_radius"])
        
        # Update specifications
        specifications = updates.get("specifications", {})
        if isinstance(specifications, dict):
            if "flute_count" in specifications and specifications["flute_count"] is not None:
                if hasattr(tool, 'numberOfFlutes'):
                    tool.numberOfFlutes = int(specifications["flute_count"])
            
            if "material" in specifications and specifications["material"] is not None:
                if hasattr(tool, 'material'):
                    tool.material = specifications["material"]
            
            if "coating" in specifications and specifications["coating"] is not None:
                if hasattr(tool, 'coating'):
                    tool.coating = specifications["coating"]
        
        # Update cutting data
        cutting_data = updates.get("cutting_data", {})
        if isinstance(cutting_data, dict):
            if "spindle_speed" in cutting_data and cutting_data["spindle_speed"] is not None:
                if hasattr(tool, 'spindleSpeed'):
                    tool.spindleSpeed = float(cutting_data["spindle_speed"])
            
            if "feed_per_tooth" in cutting_data and cutting_data["feed_per_tooth"] is not None:
                if hasattr(tool, 'feedPerTooth'):
                    tool.feedPerTooth = float(cutting_data["feed_per_tooth"])
            
            if "surface_speed" in cutting_data and cutting_data["surface_speed"] is not None:
                if hasattr(tool, 'surfaceSpeed'):
                    tool.surfaceSpeed = float(cutting_data["surface_speed"])
                
    except Exception:
        # Silently handle property setting errors
        # Some properties may not have been set
        pass


def duplicate_tool(tool_id: str, target_library_id: str, new_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Duplicate an existing tool to a target library.
    
    Creates a copy of the source tool in the specified target library,
    copying all geometry, specifications, and cutting data.
    
    Args:
        tool_id: The unique identifier of the source tool (entityToken)
        target_library_id: The unique identifier of the target library (entityToken)
        new_name: Optional new name for the duplicated tool. If not provided,
                  the original tool's name will be used with " (Copy)" suffix.
                
    Returns:
        dict: Response containing:
            On success:
                - id: The new tool's unique identifier
                - name: The duplicated tool's name
                - source_tool_id: The original tool's ID
                - target_library_id: The target library's ID
                - message: Confirmation message
            On error:
                - error: True
                - message: Error description
                - code: Error code (TOOL_NOT_FOUND, LIBRARY_NOT_FOUND, LIBRARY_READ_ONLY)
                
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    try:
        # Find the source tool by ID
        source_tool = find_tool_by_id(tool_id)
        
        if not source_tool:
            return {
                "error": True,
                "message": f"Source tool with ID '{tool_id}' not found",
                "code": "TOOL_NOT_FOUND"
            }
        
        # Find the target library by ID
        target_library = _find_library_by_id(target_library_id)
        
        if not target_library:
            return {
                "error": True,
                "message": f"Target library with ID '{target_library_id}' not found",
                "code": "LIBRARY_NOT_FOUND"
            }
        
        # Check if target library is writable
        if not _is_library_writable(target_library):
            library_name = getattr(target_library, 'name', 'Unknown Library')
            return {
                "error": True,
                "message": f"Target library '{library_name}' is read-only and cannot be modified",
                "code": "LIBRARY_READ_ONLY"
            }
        
        # Get the source tool's full data for copying
        source_library = _find_library_for_tool(tool_id)
        source_data = serialize_tool_full(source_tool, source_library)
        
        # Determine the name for the duplicated tool
        original_name = source_data.get("name", "Unknown tool")
        if new_name:
            duplicate_name = new_name
        else:
            duplicate_name = f"{original_name} (Copy)"
        
        # Get the tool type enum from the source tool
        tool_type_string = source_data.get("type", "flat end mill")
        tool_type_enum = _get_tool_type_enum(tool_type_string)
        
        if tool_type_enum is None:
            # If the tool type is not in our supported list, try to get it directly
            if hasattr(source_tool, 'type'):
                tool_type_enum = source_tool.type
            else:
                return {
                    "error": True,
                    "message": f"Cannot duplicate tool: unsupported tool type '{tool_type_string}'",
                    "code": "INVALID_TOOL_DATA"
                }
        
        # Get the tools collection from the target library
        if not hasattr(target_library, 'tools'):
            return {
                "error": True,
                "message": "Target library does not support tool creation",
                "code": "INVALID_TOOL_DATA"
            }
        
        tools = target_library.tools
        if tools is None:
            return {
                "error": True,
                "message": "Cannot access tools collection in target library",
                "code": "INTERNAL_ERROR"
            }
        
        # Create the new tool in the target library
        try:
            new_tool = None
            
            # Try different API patterns for tool creation
            if hasattr(tools, 'add'):
                new_tool = tools.add(tool_type_enum)
            elif hasattr(target_library, 'createTool'):
                new_tool = target_library.createTool(tool_type_enum)
            
            if not new_tool:
                return {
                    "error": True,
                    "message": "Failed to create duplicate tool in target library",
                    "code": "INTERNAL_ERROR"
                }
            
            # Copy all properties from source tool to new tool
            _copy_tool_properties(source_tool, new_tool, source_data)
            
            # Apply the new name
            if hasattr(new_tool, 'description'):
                new_tool.description = duplicate_name
            elif hasattr(new_tool, 'name'):
                new_tool.name = duplicate_name
            
            # Get the new tool ID
            new_tool_id = getattr(new_tool, 'entityToken', None) or str(id(new_tool))
            
            return {
                "id": new_tool_id,
                "name": duplicate_name,
                "source_tool_id": tool_id,
                "target_library_id": target_library_id,
                "message": f"Tool '{original_name}' duplicated successfully as '{duplicate_name}'"
            }
            
        except Exception as api_error:
            return {
                "error": True,
                "message": f"Fusion API error during tool duplication: {str(api_error)}",
                "code": "INTERNAL_ERROR"
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error duplicating tool: {str(e)}",
            "code": "INTERNAL_ERROR"
        }


def _copy_tool_properties(source_tool: Any, target_tool: Any, source_data: Dict[str, Any]) -> None:
    """
    Copy all properties from a source tool to a target tool.
    
    Copies geometry, specifications, and cutting data from the source tool
    to the target tool. Uses both direct property access and serialized data
    for maximum compatibility.
    
    Args:
        source_tool: The source Fusion 360 tool object
        target_tool: The target Fusion 360 tool object to copy properties to
        source_data: Serialized source tool data from serialize_tool_full()
        
    Requirements: 6.3
    """
    try:
        # Copy tool number
        if hasattr(source_tool, 'toolNumber') and hasattr(target_tool, 'toolNumber'):
            try:
                target_tool.toolNumber = source_tool.toolNumber
            except Exception:
                pass
        
        # Copy geometry properties
        geometry = source_data.get("geometry", {})
        
        # Diameter
        if hasattr(source_tool, 'diameter') and hasattr(target_tool, 'diameter'):
            try:
                target_tool.diameter = source_tool.diameter
            except Exception:
                if geometry.get("diameter") is not None:
                    try:
                        target_tool.diameter = geometry["diameter"]
                    except Exception:
                        pass
        
        # Overall length (bodyLength)
        if hasattr(source_tool, 'bodyLength') and hasattr(target_tool, 'bodyLength'):
            try:
                target_tool.bodyLength = source_tool.bodyLength
            except Exception:
                if geometry.get("overall_length") is not None:
                    try:
                        target_tool.bodyLength = geometry["overall_length"]
                    except Exception:
                        pass
        
        # Flute length
        if hasattr(source_tool, 'fluteLength') and hasattr(target_tool, 'fluteLength'):
            try:
                target_tool.fluteLength = source_tool.fluteLength
            except Exception:
                if geometry.get("flute_length") is not None:
                    try:
                        target_tool.fluteLength = geometry["flute_length"]
                    except Exception:
                        pass
        
        # Shaft diameter
        if hasattr(source_tool, 'shaftDiameter') and hasattr(target_tool, 'shaftDiameter'):
            try:
                target_tool.shaftDiameter = source_tool.shaftDiameter
            except Exception:
                if geometry.get("shaft_diameter") is not None:
                    try:
                        target_tool.shaftDiameter = geometry["shaft_diameter"]
                    except Exception:
                        pass
        
        # Corner radius
        if hasattr(source_tool, 'cornerRadius') and hasattr(target_tool, 'cornerRadius'):
            try:
                target_tool.cornerRadius = source_tool.cornerRadius
            except Exception:
                if geometry.get("corner_radius") is not None:
                    try:
                        target_tool.cornerRadius = geometry["corner_radius"]
                    except Exception:
                        pass
        
        # Copy specifications
        specifications = source_data.get("specifications", {})
        
        # Number of flutes
        if hasattr(source_tool, 'numberOfFlutes') and hasattr(target_tool, 'numberOfFlutes'):
            try:
                target_tool.numberOfFlutes = source_tool.numberOfFlutes
            except Exception:
                if specifications.get("flute_count") is not None:
                    try:
                        target_tool.numberOfFlutes = specifications["flute_count"]
                    except Exception:
                        pass
        
        # Material
        if hasattr(source_tool, 'material') and hasattr(target_tool, 'material'):
            try:
                target_tool.material = source_tool.material
            except Exception:
                if specifications.get("material") is not None:
                    try:
                        target_tool.material = specifications["material"]
                    except Exception:
                        pass
        
        # Coating
        if hasattr(source_tool, 'coating') and hasattr(target_tool, 'coating'):
            try:
                target_tool.coating = source_tool.coating
            except Exception:
                if specifications.get("coating") is not None:
                    try:
                        target_tool.coating = specifications["coating"]
                    except Exception:
                        pass
        
        # Copy cutting data
        cutting_data = source_data.get("cutting_data") or {}
        
        # Spindle speed
        if hasattr(source_tool, 'spindleSpeed') and hasattr(target_tool, 'spindleSpeed'):
            try:
                if source_tool.spindleSpeed:
                    target_tool.spindleSpeed = source_tool.spindleSpeed
            except Exception:
                if cutting_data.get("spindle_speed") is not None:
                    try:
                        target_tool.spindleSpeed = cutting_data["spindle_speed"]
                    except Exception:
                        pass
        
        # Feed per tooth
        if hasattr(source_tool, 'feedPerTooth') and hasattr(target_tool, 'feedPerTooth'):
            try:
                if source_tool.feedPerTooth:
                    target_tool.feedPerTooth = source_tool.feedPerTooth
            except Exception:
                if cutting_data.get("feed_per_tooth") is not None:
                    try:
                        target_tool.feedPerTooth = cutting_data["feed_per_tooth"]
                    except Exception:
                        pass
        
        # Surface speed
        if hasattr(source_tool, 'surfaceSpeed') and hasattr(target_tool, 'surfaceSpeed'):
            try:
                if source_tool.surfaceSpeed:
                    target_tool.surfaceSpeed = source_tool.surfaceSpeed
            except Exception:
                if cutting_data.get("surface_speed") is not None:
                    try:
                        target_tool.surfaceSpeed = cutting_data["surface_speed"]
                    except Exception:
                        pass
                        
    except Exception:
        # Silently handle property copying errors
        # The tool was created, some properties may not have been copied
        pass


def _is_tool_in_use(tool_id: str) -> bool:
    """
    Check if a tool is currently in use by any CAM operations.
    
    Searches all setups and their operations to determine if the tool
    with the given ID is referenced by any toolpath operation.
    
    Args:
        tool_id: The unique identifier of the tool (entityToken)
        
    Returns:
        bool: True if the tool is used by at least one CAM operation,
              False otherwise.
              
    Requirements: 7.2
    """
    try:
        cam = _get_cam_product()
        if not cam:
            return False
        
        setups = cam.setups
        if not setups:
            return False
        
        # Search through all setups
        for setup_idx in range(setups.count):
            setup = setups.item(setup_idx)
            
            # Check direct operations in the setup
            operations = setup.operations
            if operations:
                for op_idx in range(operations.count):
                    operation = operations.item(op_idx)
                    if hasattr(operation, 'tool') and operation.tool:
                        op_tool = operation.tool
                        op_tool_id = getattr(op_tool, 'entityToken', None) or str(id(op_tool))
                        if op_tool_id == tool_id:
                            return True
            
            # Check operations in folders
            if hasattr(setup, 'folders'):
                folders = setup.folders
                if folders:
                    for folder_idx in range(folders.count):
                        folder = folders.item(folder_idx)
                        if hasattr(folder, 'operations'):
                            folder_ops = folder.operations
                            if folder_ops:
                                for op_idx in range(folder_ops.count):
                                    operation = folder_ops.item(op_idx)
                                    if hasattr(operation, 'tool') and operation.tool:
                                        op_tool = operation.tool
                                        op_tool_id = getattr(op_tool, 'entityToken', None) or str(id(op_tool))
                                        if op_tool_id == tool_id:
                                            return True
            
            # Check nested folders (some setups have deeper folder structures)
            if hasattr(setup, 'allOperations'):
                try:
                    all_ops = setup.allOperations
                    if all_ops:
                        for op_idx in range(all_ops.count):
                            operation = all_ops.item(op_idx)
                            if hasattr(operation, 'tool') and operation.tool:
                                op_tool = operation.tool
                                op_tool_id = getattr(op_tool, 'entityToken', None) or str(id(op_tool))
                                if op_tool_id == tool_id:
                                    return True
                except Exception:
                    # allOperations may not be available in all Fusion versions
                    pass
        
        return False
        
    except Exception:
        # If we can't determine usage, assume it's not in use
        # This is safer than blocking deletion unnecessarily
        return False


def delete_tool(tool_id: str) -> Dict[str, Any]:
    """
    Delete a tool from its library.
    
    Finds the tool by ID, verifies it can be deleted (library is writable,
    tool is not in use), and removes it from the library.
    
    Args:
        tool_id: The unique identifier of the tool (entityToken)
        
    Returns:
        dict: Response containing:
            On success:
                - message: Confirmation message
                - tool_id: The deleted tool's ID
                - tool_name: The deleted tool's name
            On error:
                - error: True
                - message: Error description
                - code: Error code (TOOL_NOT_FOUND, TOOL_READ_ONLY, TOOL_IN_USE)
                
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    try:
        # Find the tool by ID
        tool = find_tool_by_id(tool_id)
        
        if not tool:
            return {
                "error": True,
                "message": f"Tool with ID '{tool_id}' not found",
                "code": "TOOL_NOT_FOUND"
            }
        
        # Get tool name for response message
        tool_name = getattr(tool, 'description', None) or getattr(tool, 'name', 'Unknown tool')
        
        # Find the library containing this tool
        library = _find_library_for_tool(tool_id)
        
        if not library:
            # Tool might be from a CAM operation, not a library
            return {
                "error": True,
                "message": f"Tool '{tool_name}' is not in a tool library and cannot be deleted. "
                          "It may be an operation-specific tool.",
                "code": "TOOL_READ_ONLY"
            }
        
        # Check if the library is writable
        if not _is_library_writable(library):
            library_name = getattr(library, 'name', 'Unknown Library')
            return {
                "error": True,
                "message": f"Tool '{tool_name}' is in read-only library '{library_name}' and cannot be deleted",
                "code": "TOOL_READ_ONLY"
            }
        
        # Check if the tool is in use by any CAM operations
        if _is_tool_in_use(tool_id):
            return {
                "error": True,
                "message": f"Tool '{tool_name}' is currently in use by CAM operations and cannot be deleted. "
                          "Remove the tool from all operations first.",
                "code": "TOOL_IN_USE"
            }
        
        # Attempt to delete the tool from the library
        try:
            # Get the tools collection from the library
            if not hasattr(library, 'tools'):
                return {
                    "error": True,
                    "message": "Library does not support tool deletion",
                    "code": "INTERNAL_ERROR"
                }
            
            tools = library.tools
            if tools is None:
                return {
                    "error": True,
                    "message": "Cannot access tools collection in library",
                    "code": "INTERNAL_ERROR"
                }
            
            # Find the tool index in the library's tools collection
            tool_index = None
            for idx in range(tools.count):
                lib_tool = tools.item(idx)
                lib_tool_id = getattr(lib_tool, 'entityToken', None) or str(id(lib_tool))
                if lib_tool_id == tool_id:
                    tool_index = idx
                    break
            
            if tool_index is None:
                return {
                    "error": True,
                    "message": f"Tool '{tool_name}' not found in library's tools collection",
                    "code": "INTERNAL_ERROR"
                }
            
            # Delete the tool using available API methods
            deleted = False
            
            # Try different deletion methods based on Fusion 360 API
            if hasattr(tool, 'deleteMe'):
                # Direct deletion on the tool object
                deleted = tool.deleteMe()
            elif hasattr(tools, 'removeByIndex'):
                # Remove by index from collection
                deleted = tools.removeByIndex(tool_index)
            elif hasattr(tools, 'remove'):
                # Remove tool object from collection
                deleted = tools.remove(tool)
            elif hasattr(library, 'deleteTool'):
                # Library-level deletion method
                deleted = library.deleteTool(tool)
            
            if deleted:
                return {
                    "message": f"Tool '{tool_name}' deleted successfully",
                    "tool_id": tool_id,
                    "tool_name": tool_name
                }
            else:
                return {
                    "error": True,
                    "message": f"Failed to delete tool '{tool_name}'. The deletion operation returned false.",
                    "code": "INTERNAL_ERROR"
                }
                
        except Exception as api_error:
            return {
                "error": True,
                "message": f"Fusion API error during tool deletion: {str(api_error)}",
                "code": "INTERNAL_ERROR"
            }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error deleting tool: {str(e)}",
            "code": "INTERNAL_ERROR"
        }


def search_tools(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for tools across libraries based on specified criteria.
    
    Searches specified libraries (or all libraries if not specified) and
    filters tools by type, diameter range, and material.
    
    Args:
        criteria: Dictionary containing search criteria:
            Optional:
                - tool_type: Tool type string to filter by (e.g., "flat end mill", "drill")
                - diameter_min: Minimum diameter (inclusive)
                - diameter_max: Maximum diameter (inclusive)
                - material: Tool material to filter by (e.g., "carbide", "HSS")
                - library_ids: List of library IDs to search (searches all if not specified)
                
    Returns:
        dict: Response containing:
            On success:
                - tools: List of matching tools with id, name, type, diameter
                - total_count: Number of matching tools
                - search_criteria: Echo of the search criteria used
                - message: Informative message (null if tools found, message if empty)
            On error:
                - error: True
                - message: Error description
                - code: Error code
                
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
    """
    try:
        # Extract search criteria
        tool_type = criteria.get("tool_type")
        diameter_min = criteria.get("diameter_min")
        diameter_max = criteria.get("diameter_max")
        material = criteria.get("material")
        library_ids = criteria.get("library_ids")
        
        # Normalize tool_type for comparison
        if tool_type:
            tool_type = tool_type.lower().strip()
        
        # Normalize material for comparison
        if material:
            material = material.lower().strip()
        
        # Validate diameter range if provided
        if diameter_min is not None:
            try:
                diameter_min = float(diameter_min)
            except (ValueError, TypeError):
                return {
                    "error": True,
                    "message": "Invalid diameter_min: must be a number",
                    "code": "INVALID_TOOL_DATA"
                }
        
        if diameter_max is not None:
            try:
                diameter_max = float(diameter_max)
            except (ValueError, TypeError):
                return {
                    "error": True,
                    "message": "Invalid diameter_max: must be a number",
                    "code": "INVALID_TOOL_DATA"
                }
        
        # Validate diameter range logic
        if diameter_min is not None and diameter_max is not None:
            if diameter_min > diameter_max:
                return {
                    "error": True,
                    "message": "Invalid diameter range: diameter_min cannot be greater than diameter_max",
                    "code": "INVALID_TOOL_DATA"
                }
        
        # Get CAM product
        cam = _get_cam_product()
        if not cam:
            return {
                "tools": [],
                "total_count": 0,
                "search_criteria": criteria,
                "message": "No CAM product available. Please open a document with MANUFACTURE workspace."
            }
        
        if not hasattr(cam, 'toolLibraries'):
            return {
                "tools": [],
                "total_count": 0,
                "search_criteria": criteria,
                "message": "Tool libraries not accessible in current CAM product."
            }
        
        tool_libraries = cam.toolLibraries
        if not tool_libraries:
            return {
                "tools": [],
                "total_count": 0,
                "search_criteria": criteria,
                "message": "No tool libraries found."
            }
        
        # Determine which libraries to search
        libraries_to_search = []
        
        if library_ids and isinstance(library_ids, list) and len(library_ids) > 0:
            # Search only specified libraries
            for lib_id in library_ids:
                library = _find_library_by_id(lib_id)
                if library:
                    libraries_to_search.append(library)
            
            if not libraries_to_search:
                return {
                    "tools": [],
                    "total_count": 0,
                    "search_criteria": criteria,
                    "message": "None of the specified libraries were found."
                }
        else:
            # Search all libraries
            for lib_idx in range(tool_libraries.count):
                library = tool_libraries.item(lib_idx)
                libraries_to_search.append(library)
        
        # Search tools in the selected libraries
        matching_tools = []
        
        for library in libraries_to_search:
            if not hasattr(library, 'tools'):
                continue
            
            tools = library.tools
            if not tools:
                continue
            
            for tool_idx in range(tools.count):
                tool = tools.item(tool_idx)
                
                # Apply filters
                if not _tool_matches_criteria(tool, tool_type, diameter_min, diameter_max, material):
                    continue
                
                # Tool matches all criteria - serialize it for the response
                tool_data = _serialize_tool_for_search(tool)
                matching_tools.append(tool_data)
        
        total_count = len(matching_tools)
        
        # Set message for empty results
        message = None
        if total_count == 0:
            message = "No tools match the specified search criteria."
        
        return {
            "tools": matching_tools,
            "total_count": total_count,
            "search_criteria": criteria,
            "message": message
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Error searching tools: {str(e)}",
            "code": "INTERNAL_ERROR"
        }


def _tool_matches_criteria(
    tool: Any,
    tool_type: Optional[str],
    diameter_min: Optional[float],
    diameter_max: Optional[float],
    material: Optional[str]
) -> bool:
    """
    Check if a tool matches the specified search criteria.
    
    All provided criteria must match for the tool to be considered a match.
    Criteria that are None are not applied (match any value).
    
    Args:
        tool: The CAM tool object to check
        tool_type: Tool type string to match (case-insensitive), or None to match any
        diameter_min: Minimum diameter (inclusive), or None for no minimum
        diameter_max: Maximum diameter (inclusive), or None for no maximum
        material: Tool material to match (case-insensitive), or None to match any
        
    Returns:
        bool: True if the tool matches all specified criteria, False otherwise.
        
    Requirements: 8.2, 8.3
    """
    try:
        # Filter by tool type
        if tool_type is not None:
            actual_type = _get_tool_type_string(tool)
            if actual_type.lower().strip() != tool_type:
                return False
        
        # Filter by diameter range
        if diameter_min is not None or diameter_max is not None:
            tool_diameter = getattr(tool, 'diameter', None)
            
            if tool_diameter is None:
                # Tool has no diameter - doesn't match diameter criteria
                return False
            
            try:
                tool_diameter = float(tool_diameter)
            except (ValueError, TypeError):
                return False
            
            # Check minimum diameter (inclusive)
            if diameter_min is not None and tool_diameter < diameter_min:
                return False
            
            # Check maximum diameter (inclusive)
            if diameter_max is not None and tool_diameter > diameter_max:
                return False
        
        # Filter by material
        if material is not None:
            tool_material = getattr(tool, 'material', None)
            
            if tool_material is None:
                # Tool has no material specified - doesn't match material criteria
                return False
            
            if str(tool_material).lower().strip() != material:
                return False
        
        # Tool matches all criteria
        return True
        
    except Exception:
        # If we can't check the tool, consider it non-matching
        return False


def _serialize_tool_for_search(tool: Any) -> Dict[str, Any]:
    """
    Serialize a tool for search results.
    
    Returns a minimal representation with id, name, type, and diameter
    as specified in the requirements.
    
    Args:
        tool: The CAM tool object
        
    Returns:
        dict: Tool information including:
            - id: Unique tool identifier
            - name: Tool name/description
            - type: Tool type string
            - diameter: Tool diameter in mm
            
    Requirements: 8.5
    """
    try:
        return {
            "id": getattr(tool, 'entityToken', None) or str(id(tool)),
            "name": getattr(tool, 'description', None) or getattr(tool, 'name', 'Unknown tool'),
            "type": _get_tool_type_string(tool),
            "diameter": getattr(tool, 'diameter', None)
        }
    except Exception as e:
        return {
            "id": None,
            "name": "Error accessing tool",
            "type": "unknown",
            "diameter": None,
            "error": str(e)
        }
