# Comprehensive Error Handling and Logging System

## Overview

The Fusion MCP Bridge includes a comprehensive error handling and logging system that provides:

- **Detailed error messages with module context**
- **Module-level logging controls**
- **Error isolation between modules**
- **System resilience and graceful degradation**
- **Circuit breaker pattern for fault tolerance**
- **Health monitoring and diagnostics**

## Key Features

### 1. Module-Specific Logging

Each module gets its own logger with configurable levels:

```python
from core.error_handling import error_handler

# Get module-specific logger
module_logger = error_handler.get_module_logger("my_module")

# Use the logger
module_logger.info("Module started")
module_logger.error("Something went wrong")

# Change log level for specific module
error_handler.set_module_log_level("my_module", logging.DEBUG)
```

### 2. Comprehensive Error Context

Errors are captured with rich context information:

```python
from core.error_handling import error_handler, ErrorCategory, ErrorSeverity

try:
    risky_operation()
except Exception as e:
    error_response = error_handler.handle_error(
        error=e,
        module_name="my_module",
        function_name="my_function",
        category=ErrorCategory.FUSION_API,
        severity=ErrorSeverity.HIGH,
        request_path="/api/endpoint",
        user_data={"param": "value"},
        additional_info={"context": "additional details"}
    )
```

### 3. Error Handler Decorator

Automatically handle errors in functions:

```python
from core.error_handling import error_handler_decorator, ErrorCategory, ErrorSeverity

@error_handler_decorator("my_module", ErrorCategory.REQUEST_HANDLING, ErrorSeverity.MEDIUM)
def my_handler_function(path: str, method: str, data: dict):
    # Function implementation
    # Errors are automatically caught and handled
    return {"status": 200, "data": result}
```

### 4. Circuit Breaker Pattern

Prevents cascading failures by temporarily disabling failing components:

- After 5 consecutive failures, the circuit breaker opens
- Requests are rejected with a "service unavailable" message
- Circuit breaker resets after 5 minutes of no failures

### 5. Safe Execution Wrapper

Execute functions with automatic error handling:

```python
from core.error_handling import safe_execute

result = safe_execute(
    risky_function,
    arg1, arg2,
    default_return="fallback_value",
    kwarg1="value"
)
```

## Error Categories

The system classifies errors into categories:

- `MODULE_LOAD` - Module loading and import errors
- `REQUEST_HANDLING` - HTTP request processing errors
- `TASK_EXECUTION` - Task queue execution errors
- `VALIDATION` - Input validation errors
- `FUSION_API` - Fusion 360 API errors
- `CONFIGURATION` - Configuration and setup errors
- `SYSTEM` - General system errors

## Error Severity Levels

- `LOW` - Minor issues that don't affect functionality
- `MEDIUM` - Issues that may affect some functionality
- `HIGH` - Serious issues that affect major functionality
- `CRITICAL` - System-threatening issues

## Health Monitoring

### Health Check Endpoint

Access system health information:

```
GET /health
```

Returns comprehensive health metrics including:
- Server status
- Error statistics
- Module status
- Task queue health
- Circuit breaker states

### Error Statistics Endpoint

Get detailed error statistics:

```
GET /health/errors
```

### Log Level Control

Change logging levels at runtime:

```
POST /health/log-level
{
    "module_name": "design.geometry",
    "log_level": "DEBUG"
}
```

## Error Response Format

Standardized error responses include:

```json
{
    "error": true,
    "message": "User-friendly error message",
    "code": "ERROR_CODE_CONSTANT",
    "category": "error_category",
    "severity": "error_severity",
    "module_context": "module.function",
    "timestamp": 1234567890.123,
    "details": {
        "error_type": "ValueError",
        "module": "my_module",
        "function": "my_function"
    },
    "recovery_suggestions": [
        "Check input parameters",
        "Ensure Fusion 360 is running"
    ]
}
```

## Best Practices

### 1. Use Appropriate Error Categories

Choose the most specific error category for better diagnostics.

### 2. Provide Context

Include relevant context information in error handling calls.

### 3. Use Decorators for Handlers

Use the error handler decorator for HTTP request handlers.

### 4. Validate Input Early

Validate input parameters and return clear error messages.

### 5. Log at Appropriate Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARNING`: Issues that don't prevent operation
- `ERROR`: Errors that affect functionality
- `CRITICAL`: System-threatening issues

### 6. Handle Fusion API Errors

Use the `handle_fusion_api_error` convenience function for Fusion 360 API errors.

## Troubleshooting

### High Error Rates

1. Check error statistics by category and module
2. Review recent error messages for patterns
3. Check circuit breaker states
4. Verify Fusion 360 connectivity and state

### Circuit Breakers Opening

1. Identify the failing component
2. Check underlying system health
3. Review error logs for root cause
4. Wait for automatic reset or restart component

### Module Loading Failures

1. Check dependency requirements
2. Verify file permissions
3. Review import errors in logs
4. Ensure all required modules are present

### Performance Issues

1. Check task queue size
2. Review error processing overhead
3. Adjust log levels if needed
4. Monitor memory usage
