#!/usr/bin/env python3
"""
Unit tests for Server/core/request_handler.py

Tests the centralized HTTP request handling system including retry logic,
timeout handling, and standardized error responses.

Requirements: 7.1, 7.2, 7.4
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock, Mock
import requests

# Add Server directory to path for imports
server_path = os.path.join(os.path.dirname(__file__), "..", "Server")
if server_path not in sys.path:
    sys.path.insert(0, server_path)

from core import request_handler


class TestRequestHandlerInitialization:
    """Test request handler initialization."""
    
    @patch('core.request_handler.get_base_url')
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    def test_initialize_request_handler_success(self, mock_timeout, mock_headers, mock_base_url):
        """Test successful request handler initialization."""
        mock_base_url.return_value = "http://localhost:5001"
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        
        # Should not raise any exception
        request_handler.initialize_request_handler()
    
    @patch('core.request_handler.get_base_url')
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    def test_initialize_request_handler_empty_base_url(self, mock_timeout, mock_headers, mock_base_url):
        """Test initialization failure with empty base URL."""
        mock_base_url.return_value = ""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        
        with pytest.raises(ValueError, match="Base URL not configured"):
            request_handler.initialize_request_handler()
    
    @patch('core.request_handler.get_base_url')
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    def test_initialize_request_handler_empty_headers(self, mock_timeout, mock_headers, mock_base_url):
        """Test initialization failure with empty headers."""
        mock_base_url.return_value = "http://localhost:5001"
        mock_headers.return_value = {}
        mock_timeout.return_value = 30
        
        with pytest.raises(ValueError, match="Headers not configured"):
            request_handler.initialize_request_handler()
    
    @patch('core.request_handler.get_base_url')
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    def test_initialize_request_handler_invalid_timeout(self, mock_timeout, mock_headers, mock_base_url):
        """Test initialization failure with invalid timeout."""
        mock_base_url.return_value = "http://localhost:5001"
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 0
        
        with pytest.raises(ValueError, match="Timeout must be positive"):
            request_handler.initialize_request_handler()


class TestSendRequest:
    """Test the main send_request function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_endpoint = "http://localhost:5001/test"
        self.test_data = {"key": "value"}
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"success": True}
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.post')
    def test_send_request_post_success(self, mock_post, mock_intercept, mock_timeout, mock_headers):
        """Test successful POST request."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.return_value = self.mock_response
        mock_intercept.return_value = {"success": True}
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "POST")
        
        assert result == {"success": True}
        mock_post.assert_called_once()
        mock_intercept.assert_called_once_with(self.test_endpoint, self.mock_response, "POST")
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.get')
    def test_send_request_get_success(self, mock_get, mock_intercept, mock_timeout, mock_headers):
        """Test successful GET request."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_get.return_value = self.mock_response
        mock_intercept.return_value = {"success": True}
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "GET")
        
        assert result == {"success": True}
        mock_get.assert_called_once()
        mock_intercept.assert_called_once_with(self.test_endpoint, self.mock_response, "GET")
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.put')
    def test_send_request_put_success(self, mock_put, mock_intercept, mock_timeout, mock_headers):
        """Test successful PUT request."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_put.return_value = self.mock_response
        mock_intercept.return_value = {"success": True}
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "PUT")
        
        assert result == {"success": True}
        mock_put.assert_called_once()
        mock_intercept.assert_called_once_with(self.test_endpoint, self.mock_response, "PUT")
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.delete')
    def test_send_request_delete_success(self, mock_delete, mock_intercept, mock_timeout, mock_headers):
        """Test successful DELETE request."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_delete.return_value = self.mock_response
        mock_intercept.return_value = {"success": True}
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "DELETE")
        
        assert result == {"success": True}
        mock_delete.assert_called_once()
        mock_intercept.assert_called_once_with(self.test_endpoint, self.mock_response, "DELETE")
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    def test_send_request_unsupported_method(self, mock_timeout, mock_headers):
        """Test unsupported HTTP method."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "PATCH")
        
        assert result["error"] is True
        assert "UNKNOWN_ERROR" in result["code"]
        assert "Unsupported HTTP method" in result["message"]
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('requests.post')
    def test_send_request_connection_error_retry(self, mock_post, mock_timeout, mock_headers):
        """Test connection error with retry logic."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.side_effect = requests.ConnectionError("Connection failed")
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "POST")
        
        # Should retry 3 times
        assert mock_post.call_count == 3
        assert result["error"] is True
        assert result["code"] == "CONNECTION_ERROR"
        assert "Cannot connect to Fusion 360" in result["message"]
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('requests.post')
    def test_send_request_timeout_error_retry(self, mock_post, mock_timeout, mock_headers):
        """Test timeout error with retry logic."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "POST")
        
        # Should retry 3 times
        assert mock_post.call_count == 3
        assert result["error"] is True
        assert result["code"] == "TIMEOUT_ERROR"
        assert "Request to Fusion 360 timed out" in result["message"]
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('requests.post')
    def test_send_request_general_request_error(self, mock_post, mock_timeout, mock_headers):
        """Test general request error."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.side_effect = requests.RequestException("General request error")
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "POST")
        
        assert mock_post.call_count == 3
        assert result["error"] is True
        assert result["code"] == "REQUEST_ERROR"
        assert "Request failed" in result["message"]
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('requests.post')
    def test_send_request_unexpected_error(self, mock_post, mock_timeout, mock_headers):
        """Test unexpected error handling."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.side_effect = ValueError("Unexpected error")
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "POST")
        
        assert mock_post.call_count == 3
        assert result["error"] is True
        assert result["code"] == "UNKNOWN_ERROR"
        assert "Unexpected error" in result["message"]
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.post')
    def test_send_request_retry_success_on_second_attempt(self, mock_post, mock_intercept, mock_timeout, mock_headers):
        """Test successful request on retry."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_intercept.return_value = {"success": True}
        
        # First call fails, second succeeds
        mock_post.side_effect = [
            requests.ConnectionError("Connection failed"),
            self.mock_response
        ]
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "POST")
        
        assert mock_post.call_count == 2
        assert result == {"success": True}
        mock_intercept.assert_called_once()
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.post')
    def test_send_request_empty_data(self, mock_post, mock_intercept, mock_timeout, mock_headers):
        """Test request with empty data."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.return_value = self.mock_response
        mock_intercept.return_value = {"success": True}
        
        result = request_handler.send_request(self.test_endpoint, {}, "POST")
        
        assert result == {"success": True}
        # Verify that empty dict was converted to "{}"
        args, kwargs = mock_post.call_args
        assert args[1] == "{}"  # JSON data should be "{}"
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.post')
    def test_send_request_none_data(self, mock_post, mock_intercept, mock_timeout, mock_headers):
        """Test request with None data."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.return_value = self.mock_response
        mock_intercept.return_value = {"success": True}
        
        result = request_handler.send_request(self.test_endpoint, None, "POST")
        
        assert result == {"success": True}
        # Verify that None was converted to "{}"
        args, kwargs = mock_post.call_args
        assert args[1] == "{}"  # JSON data should be "{}"


class TestConvenienceFunctions:
    """Test convenience functions for specific HTTP methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_endpoint = "http://localhost:5001/test"
        self.test_data = {"key": "value"}
    
    @patch('core.request_handler.send_request')
    def test_send_get_request(self, mock_send_request):
        """Test send_get_request convenience function."""
        mock_send_request.return_value = {"success": True}
        
        result = request_handler.send_get_request(self.test_endpoint, self.test_data)
        
        assert result == {"success": True}
        mock_send_request.assert_called_once_with(self.test_endpoint, self.test_data, "GET")
    
    @patch('core.request_handler.send_request')
    def test_send_get_request_no_params(self, mock_send_request):
        """Test send_get_request with no parameters."""
        mock_send_request.return_value = {"success": True}
        
        result = request_handler.send_get_request(self.test_endpoint)
        
        assert result == {"success": True}
        mock_send_request.assert_called_once_with(self.test_endpoint, {}, "GET")
    
    @patch('core.request_handler.send_request')
    def test_send_post_request(self, mock_send_request):
        """Test send_post_request convenience function."""
        mock_send_request.return_value = {"success": True}
        
        result = request_handler.send_post_request(self.test_endpoint, self.test_data)
        
        assert result == {"success": True}
        mock_send_request.assert_called_once_with(self.test_endpoint, self.test_data, "POST")
    
    @patch('core.request_handler.send_request')
    def test_send_put_request(self, mock_send_request):
        """Test send_put_request convenience function."""
        mock_send_request.return_value = {"success": True}
        
        result = request_handler.send_put_request(self.test_endpoint, self.test_data)
        
        assert result == {"success": True}
        mock_send_request.assert_called_once_with(self.test_endpoint, self.test_data, "PUT")
    
    @patch('core.request_handler.send_request')
    def test_send_delete_request(self, mock_send_request):
        """Test send_delete_request convenience function."""
        mock_send_request.return_value = {"success": True}
        
        result = request_handler.send_delete_request(self.test_endpoint)
        
        assert result == {"success": True}
        mock_send_request.assert_called_once_with(self.test_endpoint, {}, "DELETE")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_endpoint = "http://localhost:5001/test"
        self.test_data = {"key": "value"}
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('requests.post')
    def test_json_serialization_error(self, mock_post, mock_timeout, mock_headers):
        """Test handling of JSON serialization errors."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        
        # Create data that can't be JSON serialized
        class UnserializableClass:
            pass
        
        unserializable_data = {"obj": UnserializableClass()}
        
        result = request_handler.send_request(self.test_endpoint, unserializable_data, "POST")
        
        assert result["error"] is True
        assert result["code"] == "UNKNOWN_ERROR"
    
    @patch('core.request_handler.get_headers')
    @patch('core.request_handler.get_timeout')
    @patch('core.request_handler.interceptor.intercept_response')
    @patch('requests.post')
    def test_interceptor_error_handling(self, mock_post, mock_intercept, mock_timeout, mock_headers):
        """Test handling of interceptor errors."""
        mock_headers.return_value = {"Content-Type": "application/json"}
        mock_timeout.return_value = 30
        mock_post.return_value = Mock()
        mock_intercept.side_effect = Exception("Interceptor error")
        
        result = request_handler.send_request(self.test_endpoint, self.test_data, "POST")
        
        assert result["error"] is True
        assert result["code"] == "UNKNOWN_ERROR"
        assert "Interceptor error" in result["message"]
    
    def test_case_insensitive_method(self):
        """Test that HTTP methods are case insensitive."""
        with patch('core.request_handler.get_headers') as mock_headers, \
             patch('core.request_handler.get_timeout') as mock_timeout, \
             patch('core.request_handler.interceptor.intercept_response') as mock_intercept, \
             patch('requests.post') as mock_post:
            
            mock_headers.return_value = {"Content-Type": "application/json"}
            mock_timeout.return_value = 30
            mock_post.return_value = Mock()
            mock_intercept.return_value = {"success": True}
            
            # Test lowercase
            result = request_handler.send_request(self.test_endpoint, self.test_data, "post")
            assert result == {"success": True}
            
            # Test mixed case
            result = request_handler.send_request(self.test_endpoint, self.test_data, "Post")
            assert result == {"success": True}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])