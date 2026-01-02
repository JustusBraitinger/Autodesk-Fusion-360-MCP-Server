"""
Centralized HTTP request handling with consistent error handling.

This module provides centralized request handling for all HTTP communication
with Fusion 360, including retry logic, timeout handling, and standardized
error responses.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from .config import get_base_url, get_headers, get_timeout
from . import interceptor

logger = logging.getLogger(__name__)

# Request timeout configuration
REQUEST_TIMEOUT = 30


def initialize_request_handler():
    """
    Initialize the request handler with configuration.
    
    This function sets up the request handler with the current configuration
    and validates that all required settings are available.
    """
    logger.info("Initializing centralized request handler")
    
    # Validate configuration
    base_url = get_base_url()
    headers = get_headers()
    timeout = get_timeout()
    
    if not base_url:
        raise ValueError("Base URL not configured")
    if not headers:
        raise ValueError("Headers not configured")
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
        
    logger.info(f"Request handler initialized - Base URL: {base_url}, Timeout: {timeout}s")


def send_request(endpoint: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
    """
    Send HTTP request with comprehensive error handling and retry logic.
    
    Args:
        endpoint: The API endpoint URL
        data: The payload data to send in the request
        method: HTTP method (POST, GET, PUT, DELETE)
        
    Returns:
        dict: Response data from the server
        
    Raises:
        requests.RequestException: If request fails after all retries
    """
    max_retries = 3
    headers = get_headers()
    timeout = get_timeout()
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Sending {method} request to {endpoint} (attempt {attempt + 1}/{max_retries})")
            
            if method.upper() == "POST":
                json_data = json.dumps(data) if data else "{}"
                response = requests.post(endpoint, json_data, headers=headers, timeout=timeout)
            elif method.upper() == "GET":
                response = requests.get(endpoint, params=data, headers=headers, timeout=timeout)
            elif method.upper() == "PUT":
                json_data = json.dumps(data) if data else "{}"
                response = requests.put(endpoint, json_data, headers=headers, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(endpoint, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Use interceptor to optionally log and return JSON response
            return interceptor.intercept_response(endpoint, response, method.upper())

        except requests.ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {
                    "error": True,
                    "message": "Cannot connect to Fusion 360. Ensure the add-in is running.",
                    "code": "CONNECTION_ERROR"
                }
                
        except requests.Timeout as e:
            logger.warning(f"Timeout error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {
                    "error": True,
                    "message": "Request to Fusion 360 timed out. The add-in may be busy.",
                    "code": "TIMEOUT_ERROR"
                }
                
        except requests.RequestException as e:
            logger.error(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {
                    "error": True,
                    "message": f"Request failed: {str(e)}",
                    "code": "REQUEST_ERROR"
                }

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {
                    "error": True,
                    "message": f"Unexpected error: {str(e)}",
                    "code": "UNKNOWN_ERROR"
                }


def send_get_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Send GET request with error handling.
    
    Args:
        endpoint: The API endpoint URL
        params: Optional query parameters
        
    Returns:
        dict: Response data from the server
    """
    return send_request(endpoint, params or {}, "GET")


def send_post_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send POST request with error handling.
    
    Args:
        endpoint: The API endpoint URL
        data: The payload data to send
        
    Returns:
        dict: Response data from the server
    """
    return send_request(endpoint, data, "POST")


def send_put_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send PUT request with error handling.
    
    Args:
        endpoint: The API endpoint URL
        data: The payload data to send
        
    Returns:
        dict: Response data from the server
    """
    return send_request(endpoint, data, "PUT")


def send_delete_request(endpoint: str) -> Dict[str, Any]:
    """
    Send DELETE request with error handling.
    
    Args:
        endpoint: The API endpoint URL
        
    Returns:
        dict: Response data from the server
    """
    return send_request(endpoint, {}, "DELETE")