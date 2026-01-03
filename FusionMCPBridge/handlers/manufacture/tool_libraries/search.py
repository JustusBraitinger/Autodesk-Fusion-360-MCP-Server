# Tool Library Search Handler
# Handles tool search and filtering across tool libraries

import adsk.core
import adsk.cam
from typing import Dict, Any, Optional, List
import logging
import re

# Import core components
from ....core.task_queue import task_queue, TaskPriority
from ....core.router import request_router

# Set up logging
logger = logging.getLogger(__name__)

def handle_search_tools(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search tools within library catalogs with advanced filtering.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data with search criteria
        
    Returns:
        Response with search results or error information
    """
    try:
        # Extract search parameters
        query = data.get("query", "")
        tool_type = data.get("tool_type")
        diameter_min = data.get("diameter_min")
        diameter_max = data.get("diameter_max")
        library_id = data.get("library_id")
        material = data.get("material")
        coating = data.get("coating")
        flute_count = data.get("flute_count")
        limit = data.get("limit", 50)
        
        result = {}
        
        def execute_search_tools():
            nonlocal result
            try:
                from ....tool_library import list_tools_in_libraries
                
                # Get all tools from libraries
                if library_id:
                    tools_data = list_tools_in_libraries(library_id=library_id)
                else:
                    tools_data = list_tools_in_libraries()
                
                if tools_data.get("error"):
                    result = tools_data
                    return
                
                # Collect all tools for searching
                all_tools = []
                for library in tools_data.get("libraries", []):
                    for tool in library.get("tools", []):
                        tool["library_name"] = library.get("name", "Unknown Library")
                        tool["library_id"] = library.get("id", "unknown")
                        all_tools.append(tool)
                
                # Apply search filters
                filtered_tools = _apply_search_filters(
                    all_tools, query, tool_type, diameter_min, diameter_max,
                    material, coating, flute_count
                )
                
                # Sort results by relevance
                sorted_tools = _sort_search_results(filtered_tools, query)
                
                # Apply limit
                if limit and len(sorted_tools) > limit:
                    sorted_tools = sorted_tools[:limit]
                
                result = {
                    "query": query,
                    "filters": {
                        "tool_type": tool_type,
                        "diameter_min": diameter_min,
                        "diameter_max": diameter_max,
                        "library_id": library_id,
                        "material": material,
                        "coating": coating,
                        "flute_count": flute_count
                    },
                    "total_results": len(sorted_tools),
                    "tools": sorted_tools,
                    "search_time": "< 1s"
                }
                
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error searching tools: {str(e)}",
                    "code": "TOOL_SEARCH_ERROR"
                }
        
        task_queue.queue_task(
            "search_tools",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.tool_libraries.search",
            callback=execute_search_tools
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_search_tools: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_advanced_search(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advanced tool search with complex criteria and sorting options.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data with advanced search criteria
        
    Returns:
        Response with advanced search results or error information
    """
    try:
        search_criteria = data.get("search_criteria", {})
        sort_by = data.get("sort_by", "relevance")  # relevance, diameter, name, type
        sort_order = data.get("sort_order", "asc")  # asc, desc
        group_by = data.get("group_by")  # library, type, material
        limit = data.get("limit", 100)
        
        result = {}
        
        def execute_advanced_search():
            nonlocal result
            try:
                from ....tool_library import list_tools_in_libraries
                
                # Get all tools from libraries
                tools_data = list_tools_in_libraries()
                
                if tools_data.get("error"):
                    result = tools_data
                    return
                
                # Collect all tools for searching
                all_tools = []
                for library in tools_data.get("libraries", []):
                    for tool in library.get("tools", []):
                        tool["library_name"] = library.get("name", "Unknown Library")
                        tool["library_id"] = library.get("id", "unknown")
                        all_tools.append(tool)
                
                # Apply advanced search criteria
                filtered_tools = _apply_advanced_search_criteria(all_tools, search_criteria)
                
                # Sort results
                sorted_tools = _sort_advanced_results(filtered_tools, sort_by, sort_order)
                
                # Apply limit
                if limit and len(sorted_tools) > limit:
                    sorted_tools = sorted_tools[:limit]
                
                # Group results if requested
                if group_by:
                    grouped_results = _group_search_results(sorted_tools, group_by)
                    result = {
                        "search_criteria": search_criteria,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "group_by": group_by,
                        "total_results": len(sorted_tools),
                        "grouped_results": grouped_results
                    }
                else:
                    result = {
                        "search_criteria": search_criteria,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "total_results": len(sorted_tools),
                        "tools": sorted_tools
                    }
                
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error in advanced search: {str(e)}",
                    "code": "ADVANCED_SEARCH_ERROR"
                }
        
        task_queue.queue_task(
            "advanced_search_tools",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.tool_libraries.search",
            callback=execute_advanced_search
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_advanced_search: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def handle_get_search_suggestions(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get search suggestions based on partial query.
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (should contain partial_query)
        
    Returns:
        Response with search suggestions or error
    """
    try:
        partial_query = data.get("partial_query", "")
        suggestion_type = data.get("suggestion_type", "all")  # all, names, types, materials
        limit = data.get("limit", 10)
        
        result = {}
        
        def execute_get_search_suggestions():
            nonlocal result
            try:
                from ....tool_library import list_tools_in_libraries
                
                # Get all tools from libraries
                tools_data = list_tools_in_libraries()
                
                if tools_data.get("error"):
                    result = tools_data
                    return
                
                # Collect suggestion data
                suggestions = {
                    "names": set(),
                    "types": set(),
                    "materials": set(),
                    "coatings": set()
                }
                
                for library in tools_data.get("libraries", []):
                    for tool in library.get("tools", []):
                        # Tool names
                        name = tool.get("name", "")
                        if name and partial_query.lower() in name.lower():
                            suggestions["names"].add(name)
                        
                        # Tool types
                        tool_type = tool.get("type", "")
                        if tool_type and partial_query.lower() in tool_type.lower():
                            suggestions["types"].add(tool_type)
                        
                        # Materials
                        material = tool.get("material", "")
                        if material and partial_query.lower() in material.lower():
                            suggestions["materials"].add(material)
                        
                        # Coatings
                        coating = tool.get("coating", "")
                        if coating and partial_query.lower() in coating.lower():
                            suggestions["coatings"].add(coating)
                
                # Convert sets to sorted lists and apply limits
                formatted_suggestions = {}
                
                if suggestion_type in ["all", "names"]:
                    formatted_suggestions["names"] = sorted(list(suggestions["names"]))[:limit]
                
                if suggestion_type in ["all", "types"]:
                    formatted_suggestions["types"] = sorted(list(suggestions["types"]))[:limit]
                
                if suggestion_type in ["all", "materials"]:
                    formatted_suggestions["materials"] = sorted(list(suggestions["materials"]))[:limit]
                
                if suggestion_type in ["all", "coatings"]:
                    formatted_suggestions["coatings"] = sorted(list(suggestions["coatings"]))[:limit]
                
                result = {
                    "partial_query": partial_query,
                    "suggestion_type": suggestion_type,
                    "suggestions": formatted_suggestions
                }
                
            except Exception as e:
                result = {
                    "error": True,
                    "message": f"Error getting search suggestions: {str(e)}",
                    "code": "SEARCH_SUGGESTIONS_ERROR"
                }
        
        task_queue.queue_task(
            "get_search_suggestions",
            priority=TaskPriority.NORMAL,
            module_context="manufacture.tool_libraries.search",
            callback=execute_get_search_suggestions
        )
        
        task_queue.process_tasks()
        
        return {
            "status": 200 if not result.get("error") else 500,
            "data": result,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        logger.error(f"Error in handle_get_search_suggestions: {str(e)}")
        return {
            "status": 500,
            "error": True,
            "message": f"Handler error: {str(e)}",
            "headers": {"Content-Type": "application/json"}
        }

def _apply_search_filters(tools: List[Dict], query: str, tool_type: str, diameter_min: float,
                         diameter_max: float, material: str, coating: str, flute_count: int) -> List[Dict]:
    """Apply search filters to tool list."""
    filtered_tools = []
    
    for tool in tools:
        # Text query filter
        if query:
            searchable_text = f"{tool.get('name', '')} {tool.get('type', '')} {tool.get('material', '')} {tool.get('coating', '')}"
            if not re.search(re.escape(query), searchable_text, re.IGNORECASE):
                continue
        
        # Tool type filter
        if tool_type and tool.get("type", "").lower() != tool_type.lower():
            continue
        
        # Diameter range filter
        tool_diameter = tool.get("diameter")
        if tool_diameter is not None:
            if diameter_min is not None and tool_diameter < diameter_min:
                continue
            if diameter_max is not None and tool_diameter > diameter_max:
                continue
        
        # Material filter
        if material and tool.get("material", "").lower() != material.lower():
            continue
        
        # Coating filter
        if coating and tool.get("coating", "").lower() != coating.lower():
            continue
        
        # Flute count filter
        if flute_count is not None and tool.get("flute_count") != flute_count:
            continue
        
        filtered_tools.append(tool)
    
    return filtered_tools

def _sort_search_results(tools: List[Dict], query: str) -> List[Dict]:
    """Sort search results by relevance."""
    if not query:
        return sorted(tools, key=lambda t: t.get("name", ""))
    
    def relevance_score(tool):
        score = 0
        name = tool.get("name", "").lower()
        tool_type = tool.get("type", "").lower()
        query_lower = query.lower()
        
        # Exact name match gets highest score
        if name == query_lower:
            score += 100
        # Name starts with query
        elif name.startswith(query_lower):
            score += 50
        # Name contains query
        elif query_lower in name:
            score += 25
        
        # Type matches
        if tool_type == query_lower:
            score += 30
        elif query_lower in tool_type:
            score += 15
        
        return score
    
    return sorted(tools, key=relevance_score, reverse=True)

def _apply_advanced_search_criteria(tools: List[Dict], criteria: Dict[str, Any]) -> List[Dict]:
    """Apply advanced search criteria to tool list."""
    filtered_tools = []
    
    for tool in tools:
        match = True
        
        # Check each criterion
        for field, criterion in criteria.items():
            if not _evaluate_criterion(tool, field, criterion):
                match = False
                break
        
        if match:
            filtered_tools.append(tool)
    
    return filtered_tools

def _evaluate_criterion(tool: Dict, field: str, criterion: Any) -> bool:
    """Evaluate a single search criterion against a tool."""
    tool_value = tool.get(field)
    
    if isinstance(criterion, dict):
        # Range or comparison criterion
        if "min" in criterion and tool_value is not None:
            if tool_value < criterion["min"]:
                return False
        if "max" in criterion and tool_value is not None:
            if tool_value > criterion["max"]:
                return False
        if "equals" in criterion:
            if tool_value != criterion["equals"]:
                return False
        if "contains" in criterion and isinstance(tool_value, str):
            if criterion["contains"].lower() not in tool_value.lower():
                return False
    else:
        # Direct value comparison
        if isinstance(tool_value, str) and isinstance(criterion, str):
            return criterion.lower() in tool_value.lower()
        else:
            return tool_value == criterion
    
    return True

def _sort_advanced_results(tools: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
    """Sort advanced search results."""
    reverse = sort_order.lower() == "desc"
    
    if sort_by == "diameter":
        return sorted(tools, key=lambda t: t.get("diameter", 0), reverse=reverse)
    elif sort_by == "name":
        return sorted(tools, key=lambda t: t.get("name", ""), reverse=reverse)
    elif sort_by == "type":
        return sorted(tools, key=lambda t: t.get("type", ""), reverse=reverse)
    else:  # relevance or default
        return tools

def _group_search_results(tools: List[Dict], group_by: str) -> Dict[str, List[Dict]]:
    """Group search results by specified field."""
    groups = {}
    
    for tool in tools:
        if group_by == "library":
            key = tool.get("library_name", "Unknown Library")
        elif group_by == "type":
            key = tool.get("type", "Unknown Type")
        elif group_by == "material":
            key = tool.get("material", "Unknown Material")
        else:
            key = "All Tools"
        
        if key not in groups:
            groups[key] = []
        groups[key].append(tool)
    
    return groups

# Register handlers with the router
def register_handlers():
    """Register all tool search handlers with the request router"""
    try:
        request_router.register_handler(
            "/tool-libraries/search",
            handle_search_tools,
            methods=["GET", "POST"],
            category="manufacture",
            module_name="manufacture.tool_libraries.search"
        )
        
        request_router.register_handler(
            "/tool-libraries/search/advanced",
            handle_advanced_search,
            methods=["POST"],
            category="manufacture",
            module_name="manufacture.tool_libraries.search"
        )
        
        request_router.register_handler(
            "/tool-libraries/search/suggestions",
            handle_get_search_suggestions,
            methods=["GET"],
            category="manufacture",
            module_name="manufacture.tool_libraries.search"
        )
        
        logger.info("Registered tool library search handlers")
        
    except Exception as e:
        logger.error(f"Error registering tool library search handlers: {str(e)}")

# Auto-register handlers when module is imported
register_handlers()