# System Health Monitoring Handler
# Provides system health metrics, error statistics, and diagnostic information

import json
import time
from typing import Dict, Any

from ...core.error_handling import error_handler, error_handler_decorator, ErrorCategory, ErrorSeverity
from ...core.server import server_manager
from ...core.router import request_router
from ...core.task_queue import task_queue
from ...core.loader import module_loader

@error_handler_decorator("system.health", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.LOW)
def handle_health_check(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle health check requests with comprehensive system status
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary with system health information
    """
    try:
        # Get error statistics
        error_stats = error_handler.get_error_statistics()
        
        # Get server information
        server_info = server_manager.get_server_info()
        
        # Get router statistics
        router_stats = request_router.get_stats()
        
        # Get task queue statistics
        task_stats = task_queue.get_stats()
        
        # Get module information
        loaded_modules = module_loader.get_loaded_modules()
        
        # Calculate overall health score
        health_score = _calculate_health_score(error_stats, server_info, router_stats, task_stats)
        
        health_data = {
            "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "unhealthy",
            "health_score": health_score,
            "timestamp": time.time(),
            "server": {
                "running": server_info.get("running", False),
                "host": server_info.get("host"),
                "port": server_info.get("port"),
                "health_status": server_info.get("health_status", "unknown")
            },
            "routing": {
                "routes_registered": router_stats.get("routes_registered", 0),
                "requests_routed": router_stats.get("requests_routed", 0),
                "requests_failed": router_stats.get("requests_failed", 0),
                "success_rate": _calculate_success_rate(router_stats)
            },
            "task_queue": {
                "queue_size": task_stats.get("tasks_queued", 0) - task_stats.get("tasks_processed", 0),
                "tasks_processed": task_stats.get("tasks_processed", 0),
                "tasks_failed": task_stats.get("tasks_failed", 0),
                "last_process_time": task_stats.get("last_process_time")
            },
            "modules": {
                "total_loaded": len(loaded_modules),
                "by_category": _group_modules_by_category(loaded_modules)
            },
            "errors": {
                "total_errors": error_stats.get("total_errors", 0),
                "recent_errors": error_stats.get("recent_errors", 0),
                "by_category": error_stats.get("error_by_category", {}),
                "by_severity": error_stats.get("error_by_severity", {}),
                "circuit_breakers": error_stats.get("circuit_breakers", {})
            }
        }
        
        return {
            "status": 200,
            "data": health_data,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        # Fallback health check if main system fails
        return {
            "status": 500,
            "data": {
                "status": "unhealthy",
                "health_score": 0,
                "timestamp": time.time(),
                "error": str(e),
                "message": "Health check system failure"
            },
            "headers": {"Content-Type": "application/json"}
        }

@error_handler_decorator("system.health", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.LOW)
def handle_error_statistics(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle requests for detailed error statistics
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary with detailed error statistics
    """
    try:
        error_stats = error_handler.get_error_statistics()
        
        return {
            "status": 200,
            "data": error_stats,
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Failed to retrieve error statistics: {str(e)}",
            "code": "ERROR_STATS_FAILURE",
            "headers": {"Content-Type": "application/json"}
        }

@error_handler_decorator("system.health", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.LOW)
def handle_set_log_level(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle requests to set logging level for specific modules
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data (should contain module_name and log_level)
        
    Returns:
        Response dictionary confirming log level change
    """
    try:
        module_name = data.get("module_name")
        log_level = data.get("log_level")
        
        if not module_name or log_level is None:
            return {
                "status": 400,
                "error": True,
                "message": "module_name and log_level parameters are required",
                "code": "MISSING_PARAMETERS",
                "headers": {"Content-Type": "application/json"}
            }
        
        # Convert string log level to integer
        import logging
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        if isinstance(log_level, str):
            log_level = level_map.get(log_level.upper())
            if log_level is None:
                return {
                    "status": 400,
                    "error": True,
                    "message": "Invalid log level. Use DEBUG, INFO, WARNING, ERROR, or CRITICAL",
                    "code": "INVALID_LOG_LEVEL",
                    "headers": {"Content-Type": "application/json"}
                }
        
        # Set the log level
        error_handler.set_module_log_level(module_name, log_level)
        
        return {
            "status": 200,
            "data": {
                "message": f"Log level set to {logging.getLevelName(log_level)} for module {module_name}",
                "module_name": module_name,
                "log_level": logging.getLevelName(log_level)
            },
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Failed to set log level: {str(e)}",
            "code": "LOG_LEVEL_SET_FAILURE",
            "headers": {"Content-Type": "application/json"}
        }

@error_handler_decorator("system.health", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.LOW)
def handle_clear_error_history(path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle requests to clear error history (maintenance operation)
    
    Args:
        path: Request path
        method: HTTP method
        data: Request data
        
    Returns:
        Response dictionary confirming error history cleared
    """
    try:
        error_handler.clear_error_history()
        
        return {
            "status": 200,
            "data": {
                "message": "Error history cleared successfully",
                "timestamp": time.time()
            },
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        return {
            "status": 500,
            "error": True,
            "message": f"Failed to clear error history: {str(e)}",
            "code": "CLEAR_HISTORY_FAILURE",
            "headers": {"Content-Type": "application/json"}
        }

def _calculate_health_score(error_stats: Dict, server_info: Dict, router_stats: Dict, task_stats: Dict) -> int:
    """
    Calculate overall system health score (0-100)
    
    Args:
        error_stats: Error statistics
        server_info: Server information
        router_stats: Router statistics
        task_stats: Task queue statistics
        
    Returns:
        Health score from 0 (unhealthy) to 100 (perfect health)
    """
    score = 100
    
    # Server health
    if not server_info.get("running", False):
        score -= 50
    
    # Error rate impact
    recent_errors = error_stats.get("recent_errors", 0)
    if recent_errors > 20:
        score -= 30
    elif recent_errors > 10:
        score -= 15
    elif recent_errors > 5:
        score -= 5
    
    # Circuit breaker impact
    circuit_breakers = error_stats.get("circuit_breakers", {})
    open_breakers = sum(1 for state in circuit_breakers.values() if state == "open")
    score -= open_breakers * 10
    
    # Request success rate impact
    success_rate = _calculate_success_rate(router_stats)
    if success_rate < 0.9:
        score -= (0.9 - success_rate) * 100
    
    # Task queue health
    queue_size = task_stats.get("tasks_queued", 0) - task_stats.get("tasks_processed", 0)
    if queue_size > 100:
        score -= 20
    elif queue_size > 50:
        score -= 10
    
    return max(0, min(100, int(score)))

def _calculate_success_rate(router_stats: Dict) -> float:
    """Calculate request success rate"""
    routed = router_stats.get("requests_routed", 0)
    failed = router_stats.get("requests_failed", 0)
    total = routed + failed
    
    if total == 0:
        return 1.0
    
    return routed / total

def _group_modules_by_category(modules: list) -> Dict[str, int]:
    """Group modules by category and count them"""
    categories = {}
    for module in modules:
        category = module.category
        categories[category] = categories.get(category, 0) + 1
    return categories

# Handler registration - these will be automatically registered by the module loader
HANDLERS = [
    {
        "pattern": "/health",
        "handler": handle_health_check,
        "methods": ["GET"],
        "category": "system"
    },
    {
        "pattern": "/health/errors",
        "handler": handle_error_statistics,
        "methods": ["GET"],
        "category": "system"
    },
    {
        "pattern": "/health/log-level",
        "handler": handle_set_log_level,
        "methods": ["POST"],
        "category": "system"
    },
    {
        "pattern": "/health/clear-errors",
        "handler": handle_clear_error_history,
        "methods": ["POST"],
        "category": "system"
    }
]