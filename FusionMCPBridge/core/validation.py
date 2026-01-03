# Request Validation System
# Provides centralized request validation before routing to handlers

import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ValidationError(Exception):
    """Exception raised when request validation fails"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ParameterType(Enum):
    """Supported parameter types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

@dataclass
class ParameterRule:
    """Validation rule for a parameter"""
    name: str
    type: ParameterType
    required: bool = False
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None

class RequestValidator:
    """
    Request validation system that validates requests before routing to handlers.
    Provides parameter validation, type checking, and constraint enforcement.
    """
    
    def __init__(self):
        """Initialize the request validator"""
        self.validation_rules: Dict[str, List[ParameterRule]] = {}
        self.path_patterns: Dict[str, str] = {}  # Maps patterns to endpoint names
    
    def register_validation_rules(self, pattern: str, rules: List[ParameterRule]) -> None:
        """
        Register validation rules for a specific endpoint pattern
        
        Args:
            pattern: URL pattern (e.g., "/Box", "/cam/toolpath/{id}")
            rules: List of parameter validation rules
        """
        self.validation_rules[pattern] = rules
        # Store pattern for lookup
        endpoint_name = pattern.replace("{", "").replace("}", "").replace("/", "_").strip("_")
        self.path_patterns[pattern] = endpoint_name
    
    def validate_request(self, path: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an HTTP request against registered rules
        
        Args:
            path: Request path
            method: HTTP method
            data: Request data
            
        Returns:
            Validated and processed data dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        # Find matching validation rules
        rules = self._find_validation_rules(path)
        
        if not rules:
            # No validation rules registered, return data as-is
            return data
        
        validated_data = {}
        
        # Validate each parameter
        for rule in rules:
            value = data.get(rule.name)
            
            # Check required parameters
            if rule.required and value is None:
                raise ValidationError(
                    f"Required parameter '{rule.name}' is missing",
                    "MISSING_REQUIRED_PARAMETER"
                )
            
            # Use default value if parameter is missing
            if value is None and rule.default is not None:
                value = rule.default
            
            # Skip validation if value is still None (optional parameter)
            if value is None:
                continue
            
            # Validate parameter type and constraints
            validated_value = self._validate_parameter(rule, value)
            validated_data[rule.name] = validated_value
        
        # Add any additional data that wasn't validated
        for key, value in data.items():
            if key not in validated_data:
                validated_data[key] = value
        
        return validated_data
    
    def _find_validation_rules(self, path: str) -> Optional[List[ParameterRule]]:
        """
        Find validation rules for a given path
        
        Args:
            path: Request path
            
        Returns:
            List of validation rules or None if no rules found
        """
        # First try exact match
        if path in self.validation_rules:
            return self.validation_rules[path]
        
        # Try pattern matching for parameterized paths
        for pattern in self.validation_rules:
            if self._path_matches_pattern(path, pattern):
                return self.validation_rules[pattern]
        
        return None
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches a pattern with parameters
        
        Args:
            path: Actual request path
            pattern: Pattern with {param} placeholders
            
        Returns:
            True if path matches pattern
        """
        import re
        
        # Convert pattern to regex
        regex_pattern = re.sub(r'\{(\w+)\}', r'[^/]+', pattern)
        regex_pattern = f"^{regex_pattern}$"
        
        return bool(re.match(regex_pattern, path))
    
    def _validate_parameter(self, rule: ParameterRule, value: Any) -> Any:
        """
        Validate a single parameter against its rule
        
        Args:
            rule: Parameter validation rule
            value: Parameter value to validate
            
        Returns:
            Validated and converted value
            
        Raises:
            ValidationError: If validation fails
        """
        # Type conversion and validation
        try:
            if rule.type == ParameterType.STRING:
                validated_value = str(value)
            elif rule.type == ParameterType.INTEGER:
                validated_value = int(value)
            elif rule.type == ParameterType.FLOAT:
                validated_value = float(value)
            elif rule.type == ParameterType.BOOLEAN:
                if isinstance(value, bool):
                    validated_value = value
                elif isinstance(value, str):
                    validated_value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    validated_value = bool(value)
            elif rule.type == ParameterType.ARRAY:
                if not isinstance(value, list):
                    raise ValidationError(
                        f"Parameter '{rule.name}' must be an array",
                        "INVALID_PARAMETER_TYPE"
                    )
                validated_value = value
            elif rule.type == ParameterType.OBJECT:
                if not isinstance(value, dict):
                    raise ValidationError(
                        f"Parameter '{rule.name}' must be an object",
                        "INVALID_PARAMETER_TYPE"
                    )
                validated_value = value
            else:
                validated_value = value
                
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Parameter '{rule.name}' has invalid type. Expected {rule.type.value}",
                "INVALID_PARAMETER_TYPE"
            )
        
        # Validate constraints
        if rule.min_value is not None and isinstance(validated_value, (int, float)):
            if validated_value < rule.min_value:
                raise ValidationError(
                    f"Parameter '{rule.name}' must be >= {rule.min_value}",
                    "PARAMETER_OUT_OF_RANGE"
                )
        
        if rule.max_value is not None and isinstance(validated_value, (int, float)):
            if validated_value > rule.max_value:
                raise ValidationError(
                    f"Parameter '{rule.name}' must be <= {rule.max_value}",
                    "PARAMETER_OUT_OF_RANGE"
                )
        
        if rule.allowed_values is not None:
            if validated_value not in rule.allowed_values:
                raise ValidationError(
                    f"Parameter '{rule.name}' must be one of: {rule.allowed_values}",
                    "INVALID_PARAMETER_VALUE"
                )
        
        if rule.pattern is not None and isinstance(validated_value, str):
            import re
            if not re.match(rule.pattern, validated_value):
                raise ValidationError(
                    f"Parameter '{rule.name}' does not match required pattern",
                    "INVALID_PARAMETER_FORMAT"
                )
        
        return validated_value
    
    def get_validation_rules(self) -> Dict[str, List[ParameterRule]]:
        """
        Get all registered validation rules
        
        Returns:
            Dictionary of validation rules by pattern
        """
        return self.validation_rules.copy()

# Global request validator instance
request_validator = RequestValidator()

# Register common validation rules
def register_common_validation_rules():
    """Register validation rules for common endpoints"""
    
    # Box creation validation
    request_validator.register_validation_rules("/Box", [
        ParameterRule("height", ParameterType.FLOAT, default=5.0, min_value=0.1),
        ParameterRule("width", ParameterType.FLOAT, default=5.0, min_value=0.1),
        ParameterRule("depth", ParameterType.FLOAT, default=5.0, min_value=0.1),
        ParameterRule("x", ParameterType.FLOAT, default=0.0),
        ParameterRule("y", ParameterType.FLOAT, default=0.0),
        ParameterRule("z", ParameterType.FLOAT, default=0.0),
        ParameterRule("plane", ParameterType.STRING, default="XY", allowed_values=["XY", "XZ", "YZ"])
    ])
    
    # Cylinder creation validation
    request_validator.register_validation_rules("/draw_cylinder", [
        ParameterRule("radius", ParameterType.FLOAT, default=2.5, min_value=0.1),
        ParameterRule("height", ParameterType.FLOAT, default=5.0, min_value=0.1),
        ParameterRule("x", ParameterType.FLOAT, default=0.0),
        ParameterRule("y", ParameterType.FLOAT, default=0.0),
        ParameterRule("z", ParameterType.FLOAT, default=0.0),
        ParameterRule("plane", ParameterType.STRING, default="XY", allowed_values=["XY", "XZ", "YZ"])
    ])
    
    # Sphere creation validation
    request_validator.register_validation_rules("/sphere", [
        ParameterRule("radius", ParameterType.FLOAT, default=5.0, min_value=0.1),
        ParameterRule("x", ParameterType.FLOAT, default=0.0),
        ParameterRule("y", ParameterType.FLOAT, default=0.0),
        ParameterRule("z", ParameterType.FLOAT, default=0.0)
    ])
    
    # Move body validation
    request_validator.register_validation_rules("/move_body", [
        ParameterRule("x", ParameterType.FLOAT, default=0.0),
        ParameterRule("y", ParameterType.FLOAT, default=0.0),
        ParameterRule("z", ParameterType.FLOAT, default=0.0)
    ])
    
    # Offset plane validation
    request_validator.register_validation_rules("/offsetplane", [
        ParameterRule("offset", ParameterType.FLOAT, default=0.0),
        ParameterRule("plane", ParameterType.STRING, default="XY", allowed_values=["XY", "XZ", "YZ"])
    ])

# Initialize common validation rules
register_common_validation_rules()