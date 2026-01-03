# Comprehensive Error Handling and Logging System
# Provides detailed error messages with module context, logging controls, error isolation, and system resilience

import logging
import traceback
import json
import time
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import threading

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    MODULE_LOAD = "module_load"
    REQUEST_HANDLING = "request_handling"
    TASK_EXECUTION = "task_execution"
    VALIDATION = "validation"
    FUSION_API = "fusion_api"
    CONFIGURATION = "configuration"
    SYSTEM = "system"

@dataclass
class ErrorContext:
    """Context information for errors"""
    module_name: str
    function_name: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: float
    request_path: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

@dataclass
class ErrorResponse:
    """Standardized error response structure"""
    error: bool = True
    message: str = ""
    code: str = ""
    category: str = ""
    severity: str = ""
    module_context: str = ""
    timestamp: float = 0.0
    details: Optional[Dict[str, Any]] = None
    recovery_suggestions: Optional[List[str]] = None

class ModuleLogger:
    """Module-specific logger with configurable levels and context"""
    
    def __init__(self, module_name: str, base_level: int = logging.INFO):
        """
        Initialize module logger
        
        Args:
            module_name: Name of the module
            base_level: Base logging level
        """
        self.module_name = module_name
        self.logger = logging.getLogger(f"fusion_mcp.{module_name}")
        self.logger.setLevel(base_level)
        
        # Create formatter with module context
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(module_name)s] - %(message)s'
        )
        
        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Add module name to all log records
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.module_name = self.module_name
            return record
        logging.setLogRecordFactory(record_factory)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self.logger.critical(message, extra=kwargs)
    
    def set_level(self, level: int):
        """Set logging level for this module"""
        self.logger.setLevel(level)

class ErrorHandler:
    """
    Comprehensive error handling system with module context, isolation, and resilience.
    Provides detailed error messages, recovery suggestions, and system stability.
    """
    
    def __init__(self):
        """Initialize the error handler"""
        self.module_loggers: Dict[str, ModuleLogger] = {}
        self.error_history: List[ErrorContext] = []
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize system logger
        self.system_logger = self.get_module_logger("system")
        self.system_logger.info("Error handling system initialized")
    
    def get_module_logger(self, module_name: str) -> ModuleLogger:
        """
        Get or create a module-specific logger
        
        Args:
            module_name: Name of the module
            
        Returns:
            ModuleLogger instance for the module
        """
        if module_name not in self.module_loggers:
            self.module_loggers[module_name] = ModuleLogger(module_name)
        return self.module_loggers[module_name]
    
    def set_module_log_level(self, module_name: str, level: int):
        """
        Set logging level for a specific module
        
        Args:
            module_name: Name of the module
            level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        logger = self.get_module_logger(module_name)
        logger.set_level(level)
        self.system_logger.info(f"Set log level for module {module_name} to {logging.getLevelName(level)}")
    
    def handle_error(self, 
                    error: Exception,
                    module_name: str,
                    function_name: str,
                    category: ErrorCategory,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    request_path: Optional[str] = None,
                    user_data: Optional[Dict[str, Any]] = None,
                    additional_info: Optional[Dict[str, Any]] = None) -> ErrorResponse:
        """
        Handle an error with comprehensive context and logging
        
        Args:
            error: The exception that occurred
            module_name: Name of the module where error occurred
            function_name: Name of the function where error occurred
            category: Error category
            severity: Error severity level
            request_path: HTTP request path (if applicable)
            user_data: User request data (if applicable)
            additional_info: Additional context information
            
        Returns:
            ErrorResponse with detailed error information
        """
        # Create error context
        error_context = ErrorContext(
            module_name=module_name,
            function_name=function_name,
            category=category,
            severity=severity,
            timestamp=time.time(),
            request_path=request_path,
            user_data=user_data,
            stack_trace=traceback.format_exc(),
            additional_info=additional_info
        )
        
        # Log the error with appropriate level
        logger = self.get_module_logger(module_name)
        error_message = f"Error in {function_name}: {str(error)}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(error_message, extra={"error_context": asdict(error_context)})
        elif severity == ErrorSeverity.HIGH:
            logger.error(error_message, extra={"error_context": asdict(error_context)})
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(error_message, extra={"error_context": asdict(error_context)})
        else:
            logger.info(error_message, extra={"error_context": asdict(error_context)})
        
        # Store error in history
        with self._lock:
            self.error_history.append(error_context)
            # Keep only last 1000 errors to prevent memory issues
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]
            
            # Update error counts
            error_key = f"{module_name}.{function_name}.{category.value}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Check circuit breaker
        if self._should_circuit_break(module_name, function_name, category):
            return self._create_circuit_breaker_response(module_name, function_name)
        
        # Generate error response
        error_response = ErrorResponse(
            error=True,
            message=self._generate_user_friendly_message(error, category),
            code=self._generate_error_code(error, category),
            category=category.value,
            severity=severity.value,
            module_context=f"{module_name}.{function_name}",
            timestamp=error_context.timestamp,
            details=self._extract_error_details(error, error_context),
            recovery_suggestions=self._generate_recovery_suggestions(error, category, module_name)
        )
        
        # Attempt recovery if strategy is available
        self._attempt_recovery(error, module_name, function_name, category)
        
        return error_response
    
    def _generate_user_friendly_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        base_message = str(error)
        
        if category == ErrorCategory.MODULE_LOAD:
            return f"Failed to load module: {base_message}"
        elif category == ErrorCategory.REQUEST_HANDLING:
            return f"Request processing error: {base_message}"
        elif category == ErrorCategory.TASK_EXECUTION:
            return f"Task execution failed: {base_message}"
        elif category == ErrorCategory.VALIDATION:
            return f"Input validation error: {base_message}"
        elif category == ErrorCategory.FUSION_API:
            return f"Fusion 360 API error: {base_message}"
        elif category == ErrorCategory.CONFIGURATION:
            return f"Configuration error: {base_message}"
        else:
            return f"System error: {base_message}"
    
    def _generate_error_code(self, error: Exception, category: ErrorCategory) -> str:
        """Generate standardized error code"""
        error_type = type(error).__name__
        return f"{category.value.upper()}_{error_type.upper()}"
    
    def _extract_error_details(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Extract detailed error information"""
        details = {
            "error_type": type(error).__name__,
            "error_args": error.args,
            "module": context.module_name,
            "function": context.function_name,
            "timestamp": context.timestamp
        }
        
        if context.request_path:
            details["request_path"] = context.request_path
        
        if context.additional_info:
            details.update(context.additional_info)
        
        return details
    
    def _generate_recovery_suggestions(self, error: Exception, category: ErrorCategory, module_name: str) -> List[str]:
        """Generate recovery suggestions based on error type and category"""
        suggestions = []
        
        if category == ErrorCategory.MODULE_LOAD:
            suggestions.extend([
                "Check if all required dependencies are installed",
                "Verify module file exists and has correct permissions",
                "Restart the add-in to reload modules"
            ])
        elif category == ErrorCategory.FUSION_API:
            suggestions.extend([
                "Ensure Fusion 360 is running and a design is open",
                "Check if you're in the correct workspace (Design/MANUFACTURE)",
                "Try restarting Fusion 360 if the issue persists"
            ])
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Check input parameters for correct types and values",
                "Refer to API documentation for required parameters",
                "Ensure all required fields are provided"
            ])
        elif category == ErrorCategory.TASK_EXECUTION:
            suggestions.extend([
                "Check if Fusion 360 is responsive",
                "Verify the operation is valid for current design state",
                "Try the operation manually in Fusion 360 first"
            ])
        
        # Add module-specific suggestions
        if "design" in module_name:
            suggestions.append("Ensure you're in the Design workspace")
        elif "manufacture" in module_name:
            suggestions.append("Ensure you're in the MANUFACTURE workspace")
        
        return suggestions
    
    def _should_circuit_break(self, module_name: str, function_name: str, category: ErrorCategory) -> bool:
        """Check if circuit breaker should activate"""
        key = f"{module_name}.{function_name}.{category.value}"
        
        with self._lock:
            if key not in self.circuit_breakers:
                self.circuit_breakers[key] = {
                    "failure_count": 0,
                    "last_failure": 0,
                    "state": "closed"  # closed, open, half_open
                }
            
            breaker = self.circuit_breakers[key]
            current_time = time.time()
            
            # Reset if enough time has passed
            if current_time - breaker["last_failure"] > 300:  # 5 minutes
                breaker["failure_count"] = 0
                breaker["state"] = "closed"
            
            # Increment failure count
            breaker["failure_count"] += 1
            breaker["last_failure"] = current_time
            
            # Open circuit if too many failures
            if breaker["failure_count"] >= 5 and breaker["state"] == "closed":
                breaker["state"] = "open"
                self.system_logger.warning(f"Circuit breaker opened for {key}")
                return True
            
            return breaker["state"] == "open"
    
    def _create_circuit_breaker_response(self, module_name: str, function_name: str) -> ErrorResponse:
        """Create response when circuit breaker is open"""
        return ErrorResponse(
            error=True,
            message="Service temporarily unavailable due to repeated failures",
            code="CIRCUIT_BREAKER_OPEN",
            category="system",
            severity="high",
            module_context=f"{module_name}.{function_name}",
            timestamp=time.time(),
            recovery_suggestions=[
                "Wait a few minutes before trying again",
                "Check system logs for underlying issues",
                "Restart the add-in if problems persist"
            ]
        )
    
    def _attempt_recovery(self, error: Exception, module_name: str, function_name: str, category: ErrorCategory):
        """Attempt automatic recovery if strategy is available"""
        recovery_key = f"{module_name}.{function_name}.{category.value}"
        
        if recovery_key in self.recovery_strategies:
            try:
                self.recovery_strategies[recovery_key](error)
                self.system_logger.info(f"Recovery attempted for {recovery_key}")
            except Exception as recovery_error:
                self.system_logger.error(f"Recovery failed for {recovery_key}: {str(recovery_error)}")
    
    def register_recovery_strategy(self, module_name: str, function_name: str, category: ErrorCategory, strategy: Callable):
        """Register a recovery strategy for specific error conditions"""
        key = f"{module_name}.{function_name}.{category.value}"
        self.recovery_strategies[key] = strategy
        self.system_logger.info(f"Registered recovery strategy for {key}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and health metrics"""
        with self._lock:
            total_errors = len(self.error_history)
            recent_errors = [e for e in self.error_history if time.time() - e.timestamp < 3600]  # Last hour
            
            error_by_category = {}
            error_by_module = {}
            error_by_severity = {}
            
            for error in self.error_history:
                # By category
                cat = error.category.value
                error_by_category[cat] = error_by_category.get(cat, 0) + 1
                
                # By module
                mod = error.module_name
                error_by_module[mod] = error_by_module.get(mod, 0) + 1
                
                # By severity
                sev = error.severity.value
                error_by_severity[sev] = error_by_severity.get(sev, 0) + 1
            
            return {
                "total_errors": total_errors,
                "recent_errors": len(recent_errors),
                "error_by_category": error_by_category,
                "error_by_module": error_by_module,
                "error_by_severity": error_by_severity,
                "circuit_breakers": {k: v["state"] for k, v in self.circuit_breakers.items()},
                "active_modules": list(self.module_loggers.keys())
            }
    
    def clear_error_history(self):
        """Clear error history (for maintenance)"""
        with self._lock:
            self.error_history.clear()
            self.error_counts.clear()
            self.circuit_breakers.clear()
        self.system_logger.info("Error history cleared")

def error_handler_decorator(module_name: str, category: ErrorCategory, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """
    Decorator for automatic error handling in functions
    
    Args:
        module_name: Name of the module
        category: Error category
        severity: Error severity level
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    module_name=module_name,
                    function_name=func.__name__,
                    category=category,
                    severity=severity,
                    additional_info={"args": str(args), "kwargs": str(kwargs)}
                )
                
                # Return error response in expected format
                return {
                    "status": 500,
                    "error": True,
                    "message": error_response.message,
                    "code": error_response.code,
                    "details": error_response.details,
                    "recovery_suggestions": error_response.recovery_suggestions,
                    "headers": {"Content-Type": "application/json"}
                }
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default_return=None, **kwargs) -> Any:
    """
    Safely execute a function with automatic error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        default_return: Default return value on error
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        module_name = getattr(func, '__module__', 'unknown')
        error_handler.handle_error(
            error=e,
            module_name=module_name,
            function_name=func.__name__,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.LOW
        )
        return default_return

# Global error handler instance
error_handler = ErrorHandler()

# Convenience functions for common error handling patterns
def handle_module_load_error(error: Exception, module_name: str) -> ErrorResponse:
    """Handle module loading errors"""
    return error_handler.handle_error(
        error=error,
        module_name="loader",
        function_name="load_module",
        category=ErrorCategory.MODULE_LOAD,
        severity=ErrorSeverity.HIGH,
        additional_info={"failed_module": module_name}
    )

def handle_request_error(error: Exception, path: str, method: str, data: Dict[str, Any]) -> ErrorResponse:
    """Handle HTTP request errors"""
    return error_handler.handle_error(
        error=error,
        module_name="router",
        function_name="route_request",
        category=ErrorCategory.REQUEST_HANDLING,
        severity=ErrorSeverity.MEDIUM,
        request_path=path,
        user_data=data,
        additional_info={"method": method}
    )

def handle_task_error(error: Exception, task_type: str, module_context: str) -> ErrorResponse:
    """Handle task execution errors"""
    return error_handler.handle_error(
        error=error,
        module_name=module_context,
        function_name="execute_task",
        category=ErrorCategory.TASK_EXECUTION,
        severity=ErrorSeverity.MEDIUM,
        additional_info={"task_type": task_type}
    )

def handle_fusion_api_error(error: Exception, module_name: str, function_name: str) -> ErrorResponse:
    """Handle Fusion 360 API errors"""
    return error_handler.handle_error(
        error=error,
        module_name=module_name,
        function_name=function_name,
        category=ErrorCategory.FUSION_API,
        severity=ErrorSeverity.HIGH
    )