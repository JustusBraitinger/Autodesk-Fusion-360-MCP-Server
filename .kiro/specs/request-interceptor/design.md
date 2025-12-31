# Design Document: Request Interceptor

## Overview

The request interceptor is a debugging feature for the MCP Server that captures and logs HTTP responses from the Fusion 360 Add-In. When enabled, it prints formatted JSON responses to the console along with endpoint context, helping developers troubleshoot communication issues without modifying the actual data flow.

## Architecture

The interceptor follows a decorator/wrapper pattern that wraps HTTP response handling:

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server                              │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────┐  │
│  │  MCP Tools  │───▶│  Interceptor     │───▶│  Console   │  │
│  │             │    │  (when enabled)  │    │  Output    │  │
│  └─────────────┘    └──────────────────┘    └────────────┘  │
│         │                    │                               │
│         │                    │ (pass-through)                │
│         ▼                    ▼                               │
│  ┌─────────────────────────────────────┐                    │
│  │         requests library            │                    │
│  │    (POST/GET to Fusion Add-In)      │                    │
│  └─────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Interceptor State Module

A simple module-level state management for the interceptor flag.

```python
# Global interceptor state
_interceptor_enabled: bool = False

def is_interceptor_enabled() -> bool:
    """Check if the interceptor is currently enabled."""
    return _interceptor_enabled

def set_interceptor_enabled(enabled: bool) -> None:
    """Enable or disable the interceptor at runtime."""
    global _interceptor_enabled
    _interceptor_enabled = enabled

def toggle_interceptor() -> bool:
    """Toggle the interceptor state and return the new state."""
    global _interceptor_enabled
    _interceptor_enabled = not _interceptor_enabled
    return _interceptor_enabled
```

### 2. Response Logger

Handles the actual logging of responses to console.

```python
def log_response(endpoint: str, response_data: any, method: str = "POST") -> None:
    """
    Log an HTTP response to the console.
    
    Args:
        endpoint: The URL that was called
        response_data: The response data (dict, list, or raw)
        method: HTTP method used (POST/GET)
    """
    pass  # Implementation details in tasks
```

### 3. Interceptor Wrapper

Wraps the response handling to optionally log before returning.

```python
def intercept_response(endpoint: str, response: requests.Response, method: str = "POST") -> dict:
    """
    Process a response, optionally logging it, and return the JSON data.
    
    Args:
        endpoint: The URL that was called
        response: The requests.Response object
        method: HTTP method used
        
    Returns:
        The parsed JSON response data
    """
    pass  # Implementation details in tasks
```

## Data Models

### Interceptor Configuration

```python
@dataclass
class InterceptorConfig:
    enabled: bool = False  # Default to disabled
```

### Log Output Format

When logging is enabled, output follows this format:

```
═══════════════════════════════════════════════════════════════
[INTERCEPTOR] POST http://localhost:5001/api/draw_cylinder
───────────────────────────────────────────────────────────────
{
    "success": true,
    "message": "Cylinder created",
    "data": {
        "body_id": "body_001"
    }
}
═══════════════════════════════════════════════════════════════
```

For errors:

```
═══════════════════════════════════════════════════════════════
[INTERCEPTOR] GET http://localhost:5001/api/cam/toolpaths
───────────────────────────────────────────────────────────────
[ERROR] Failed to parse JSON response: Expecting value: line 1 column 1
Raw response: <html>Error 500</html>
═══════════════════════════════════════════════════════════════
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Interceptor transparency
*For any* HTTP response processed by the interceptor, the data returned to the caller SHALL be identical to the original response data, regardless of whether logging is enabled or disabled.
**Validates: Requirements 3.3**

### Property 2: Logging occurs when enabled
*For any* HTTP response when the interceptor is enabled, the response data SHALL be printed to the console output.
**Validates: Requirements 1.2, 2.1**

### Property 3: No logging when disabled
*For any* HTTP response when the interceptor is disabled, no response data SHALL be printed to the console output.
**Validates: Requirements 1.3**

### Property 4: Output format correctness
*For any* logged response, the output SHALL contain the endpoint URL, the HTTP method, and properly indented JSON (or error message for non-JSON).
**Validates: Requirements 2.2, 2.3, 2.4**

### Property 5: Runtime toggle immediacy
*For any* toggle of the interceptor state, the very next HTTP request SHALL respect the new state.
**Validates: Requirements 4.2**

## Error Handling

| Scenario | Handling |
|----------|----------|
| Non-JSON response | Log error message with raw response snippet, return original response |
| JSON decode error | Log the decode error, attempt to return raw text |
| Network error | Let the existing error handling in `send_request` handle it |
| Toggle during request | Apply new state to next request (current request completes with original state) |

## Testing Strategy

### Property-Based Testing

The design uses **pytest** with **hypothesis** for property-based testing.

Each property-based test MUST:
- Run a minimum of 100 iterations
- Be tagged with a comment referencing the correctness property: `# **Feature: request-interceptor, Property {number}: {property_text}**`
- Use hypothesis strategies to generate varied inputs

### Unit Tests

Unit tests cover:
- Default state verification (interceptor disabled by default)
- Toggle mechanism functionality
- Output format validation with specific examples
- Error handling for malformed responses

### Test Structure

```
Server/
├── MCP_Server.py
├── interceptor.py          # New module for interceptor logic
├── tests/
│   ├── __init__.py
│   ├── test_interceptor.py # Unit tests
│   └── test_interceptor_properties.py  # Property-based tests
```
