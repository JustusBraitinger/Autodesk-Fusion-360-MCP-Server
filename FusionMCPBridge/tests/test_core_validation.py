#!/usr/bin/env python3
"""
Unit tests for FusionMCPBridge/core/validation.py

Tests the request validation system for the Fusion 360 Add-In.
"""

import pytest
import sys
import os

# Ensure FusionMCPBridge is at the front of sys.path
bridge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if bridge_path not in sys.path:
    sys.path.insert(0, bridge_path)

from core.validation import (
    RequestValidator,
    ValidationError,
    ParameterType,
    ParameterRule,
    request_validator
)


class TestParameterType:
    """Test ParameterType enum."""
    
    def test_parameter_types_exist(self):
        """Test that all expected parameter types exist."""
        assert ParameterType.STRING.value == "string"
        assert ParameterType.INTEGER.value == "integer"
        assert ParameterType.FLOAT.value == "float"
        assert ParameterType.BOOLEAN.value == "boolean"
        assert ParameterType.ARRAY.value == "array"
        assert ParameterType.OBJECT.value == "object"


class TestParameterRule:
    """Test ParameterRule dataclass."""
    
    def test_parameter_rule_creation(self):
        """Test creating a ParameterRule."""
        rule = ParameterRule(
            name="test_param",
            type=ParameterType.STRING,
            required=True,
            default="default_value"
        )
        
        assert rule.name == "test_param"
        assert rule.type == ParameterType.STRING
        assert rule.required is True
        assert rule.default == "default_value"
    
    def test_parameter_rule_defaults(self):
        """Test ParameterRule default values."""
        rule = ParameterRule(
            name="test_param",
            type=ParameterType.STRING
        )
        
        assert rule.required is False
        assert rule.default is None
        assert rule.min_value is None
        assert rule.max_value is None
        assert rule.allowed_values is None
        assert rule.pattern is None


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating a ValidationError."""
        error = ValidationError("Test error message", "TEST_CODE")
        
        assert error.message == "Test error message"
        assert error.code == "TEST_CODE"
        assert str(error) == "Test error message"
    
    def test_validation_error_default_code(self):
        """Test ValidationError with default code."""
        error = ValidationError("Test error message")
        
        assert error.code == "VALIDATION_ERROR"


class TestRequestValidator:
    """Test cases for the RequestValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = RequestValidator()
    
    def test_initialization(self):
        """Test RequestValidator initialization."""
        assert self.validator is not None
        assert self.validator.validation_rules == {}
        assert self.validator.path_patterns == {}
    
    def test_register_validation_rules(self):
        """Test registering validation rules."""
        rules = [
            ParameterRule("param1", ParameterType.STRING, required=True),
            ParameterRule("param2", ParameterType.INTEGER, default=10)
        ]
        
        self.validator.register_validation_rules("/test", rules)
        
        assert "/test" in self.validator.validation_rules
        assert len(self.validator.validation_rules["/test"]) == 2
    
    def test_validate_request_no_rules(self):
        """Test validating request with no registered rules."""
        data = {"key": "value"}
        result = self.validator.validate_request("/unknown", "POST", data)
        
        # Should return data as-is when no rules registered
        assert result == data
    
    def test_validate_request_required_parameter_present(self):
        """Test validating request with required parameter present."""
        rules = [
            ParameterRule("name", ParameterType.STRING, required=True)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        data = {"name": "test_value"}
        result = self.validator.validate_request("/test", "POST", data)
        
        assert result["name"] == "test_value"
    
    def test_validate_request_required_parameter_missing(self):
        """Test validating request with required parameter missing."""
        rules = [
            ParameterRule("name", ParameterType.STRING, required=True)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_request("/test", "POST", {})
        
        assert "Required parameter" in exc_info.value.message
        assert exc_info.value.code == "MISSING_REQUIRED_PARAMETER"
    
    def test_validate_request_default_value(self):
        """Test validating request uses default value."""
        rules = [
            ParameterRule("count", ParameterType.INTEGER, default=5)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {})
        
        assert result["count"] == 5
    
    def test_validate_request_type_conversion_string(self):
        """Test type conversion for string parameter."""
        rules = [
            ParameterRule("name", ParameterType.STRING)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {"name": 123})
        
        assert result["name"] == "123"
        assert isinstance(result["name"], str)
    
    def test_validate_request_type_conversion_integer(self):
        """Test type conversion for integer parameter."""
        rules = [
            ParameterRule("count", ParameterType.INTEGER)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {"count": "42"})
        
        assert result["count"] == 42
        assert isinstance(result["count"], int)
    
    def test_validate_request_type_conversion_float(self):
        """Test type conversion for float parameter."""
        rules = [
            ParameterRule("value", ParameterType.FLOAT)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {"value": "3.14"})
        
        assert result["value"] == 3.14
        assert isinstance(result["value"], float)
    
    def test_validate_request_type_conversion_boolean(self):
        """Test type conversion for boolean parameter."""
        rules = [
            ParameterRule("enabled", ParameterType.BOOLEAN)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        # Test various truthy values
        result = self.validator.validate_request("/test", "POST", {"enabled": "true"})
        assert result["enabled"] is True
        
        result = self.validator.validate_request("/test", "POST", {"enabled": "yes"})
        assert result["enabled"] is True
        
        result = self.validator.validate_request("/test", "POST", {"enabled": "false"})
        assert result["enabled"] is False
    
    def test_validate_request_type_array(self):
        """Test validation for array parameter."""
        rules = [
            ParameterRule("items", ParameterType.ARRAY)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {"items": [1, 2, 3]})
        assert result["items"] == [1, 2, 3]
    
    def test_validate_request_type_array_invalid(self):
        """Test validation fails for non-array when array expected."""
        rules = [
            ParameterRule("items", ParameterType.ARRAY)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_request("/test", "POST", {"items": "not_an_array"})
        
        assert "must be an array" in exc_info.value.message
    
    def test_validate_request_type_object(self):
        """Test validation for object parameter."""
        rules = [
            ParameterRule("config", ParameterType.OBJECT)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        result = self.validator.validate_request("/test", "POST", {"config": {"key": "value"}})
        assert result["config"] == {"key": "value"}
    
    def test_validate_request_type_object_invalid(self):
        """Test validation fails for non-object when object expected."""
        rules = [
            ParameterRule("config", ParameterType.OBJECT)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_request("/test", "POST", {"config": "not_an_object"})
        
        assert "must be an object" in exc_info.value.message
    
    def test_validate_request_min_value(self):
        """Test validation with min_value constraint."""
        rules = [
            ParameterRule("count", ParameterType.INTEGER, min_value=1)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        # Valid value
        result = self.validator.validate_request("/test", "POST", {"count": 5})
        assert result["count"] == 5
        
        # Invalid value
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_request("/test", "POST", {"count": 0})
        
        assert "must be >=" in exc_info.value.message
    
    def test_validate_request_max_value(self):
        """Test validation with max_value constraint."""
        rules = [
            ParameterRule("count", ParameterType.INTEGER, max_value=100)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        # Valid value
        result = self.validator.validate_request("/test", "POST", {"count": 50})
        assert result["count"] == 50
        
        # Invalid value
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_request("/test", "POST", {"count": 150})
        
        assert "must be <=" in exc_info.value.message
    
    def test_validate_request_allowed_values(self):
        """Test validation with allowed_values constraint."""
        rules = [
            ParameterRule("plane", ParameterType.STRING, allowed_values=["XY", "XZ", "YZ"])
        ]
        self.validator.register_validation_rules("/test", rules)
        
        # Valid value
        result = self.validator.validate_request("/test", "POST", {"plane": "XY"})
        assert result["plane"] == "XY"
        
        # Invalid value
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_request("/test", "POST", {"plane": "AB"})
        
        assert "must be one of" in exc_info.value.message
    
    def test_validate_request_pattern(self):
        """Test validation with pattern constraint."""
        rules = [
            ParameterRule("email", ParameterType.STRING, pattern=r"^[\w.-]+@[\w.-]+\.\w+$")
        ]
        self.validator.register_validation_rules("/test", rules)
        
        # Valid value
        result = self.validator.validate_request("/test", "POST", {"email": "test@example.com"})
        assert result["email"] == "test@example.com"
        
        # Invalid value
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_request("/test", "POST", {"email": "invalid"})
        
        assert "does not match required pattern" in exc_info.value.message
    
    def test_validate_request_preserves_extra_data(self):
        """Test that validation preserves data not in rules."""
        rules = [
            ParameterRule("name", ParameterType.STRING)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        data = {"name": "test", "extra_field": "extra_value"}
        result = self.validator.validate_request("/test", "POST", data)
        
        assert result["name"] == "test"
        assert result["extra_field"] == "extra_value"
    
    def test_get_validation_rules(self):
        """Test getting all validation rules."""
        rules = [
            ParameterRule("param", ParameterType.STRING)
        ]
        self.validator.register_validation_rules("/test", rules)
        
        all_rules = self.validator.get_validation_rules()
        
        assert "/test" in all_rules
        assert len(all_rules["/test"]) == 1


class TestGlobalRequestValidator:
    """Test the global request_validator instance."""
    
    def test_global_instance_exists(self):
        """Test that global request_validator instance exists."""
        assert request_validator is not None
        assert isinstance(request_validator, RequestValidator)
    
    def test_common_validation_rules_registered(self):
        """Test that common validation rules are registered."""
        rules = request_validator.get_validation_rules()
        
        # Check for some expected endpoints
        assert "/Box" in rules
        assert "/draw_cylinder" in rules
        assert "/sphere" in rules


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
