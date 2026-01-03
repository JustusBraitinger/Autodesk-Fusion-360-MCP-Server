# HTTP Server Management
# HTTP server setup, request handling, and lifecycle management

import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
import logging

from .config import config_manager
from .router import request_router
from .task_queue import task_queue
from .error_handling import error_handler, ErrorCategory, ErrorSeverity, handle_request_error

# Set up module-specific logging
module_logger = error_handler.get_module_logger("core.server")

class ModularRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler that uses the modular routing system.
    Routes requests through the centralized router to appropriate handler modules.
    """
    
    def log_message(self, format, *args):
        """Override to use our logging system"""
        module_logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        self._handle_request("GET")
    
    def do_POST(self):
        """Handle POST requests"""
        self._handle_request("POST")
    
    def do_PUT(self):
        """Handle PUT requests"""
        self._handle_request("PUT")
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._handle_request("DELETE")
    
    def _handle_request(self, method: str):
        """
        Handle HTTP request using the modular routing system with comprehensive error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
        """
        try:
            # Get request data for POST/PUT requests
            data = {}
            if method in ["POST", "PUT"]:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    try:
                        data = json.loads(post_data.decode('utf-8'))
                    except json.JSONDecodeError as e:
                        error_response = handle_request_error(e, self.path, method, {})
                        self._send_error_response(400, error_response.message)
                        return
            
            # Route the request with error handling
            try:
                response = request_router.route_request(self.path, method, data)
            except Exception as e:
                error_response = handle_request_error(e, self.path, method, data)
                module_logger.error(f"Request routing failed: {error_response.message}")
                self._send_error_response(500, error_response.message)
                return
            
            # Send response
            self._send_response(response)
            
        except Exception as e:
            # Last resort error handling
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.server",
                function_name="_handle_request",
                category=ErrorCategory.REQUEST_HANDLING,
                severity=ErrorSeverity.HIGH,
                request_path=self.path,
                additional_info={"method": method}
            )
            module_logger.critical(f"Critical request handling error: {error_response.message}")
            self._send_error_response(500, "Internal server error")
    
    def _send_response(self, response: Dict[str, Any]):
        """
        Send HTTP response with enhanced error handling
        
        Args:
            response: Response dictionary with status, data, headers
        """
        try:
            status = response.get("status", 200)
            headers = response.get("headers", {"Content-Type": "application/json"})
            
            # Send status
            self.send_response(status)
            
            # Send headers
            for header_name, header_value in headers.items():
                self.send_header(header_name, header_value)
            self.end_headers()
            
            # Send body
            if "data" in response:
                body = json.dumps(response["data"]).encode('utf-8')
            elif "message" in response:
                body = json.dumps({"message": response["message"]}).encode('utf-8')
            elif "error" in response:
                body = json.dumps({
                    "error": response["error"],
                    "message": response.get("message", "Unknown error"),
                    "code": response.get("code", "UNKNOWN_ERROR"),
                    "details": response.get("details"),
                    "recovery_suggestions": response.get("recovery_suggestions")
                }).encode('utf-8')
            else:
                # Send the entire response as JSON
                response_copy = response.copy()
                response_copy.pop("status", None)
                response_copy.pop("headers", None)
                body = json.dumps(response_copy).encode('utf-8')
            
            self.wfile.write(body)
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.server",
                function_name="_send_response",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH
            )
            module_logger.error(f"Response sending error: {error_response.message}")
            # Try to send a basic error response
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": True, 
                    "message": "Response error",
                    "code": "RESPONSE_SEND_ERROR"
                }).encode('utf-8'))
            except:
                pass
    
    def _send_error_response(self, status_code: int, message: str):
        """
        Send error response with enhanced error context
        
        Args:
            status_code: HTTP status code
            message: Error message
        """
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": True,
                "message": message,
                "status": status_code,
                "code": f"HTTP_{status_code}",
                "timestamp": error_handler.error_history[-1].timestamp if error_handler.error_history else None
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
        except Exception as e:
            module_logger.critical(f"Error response sending failed: {str(e)}")

class HTTPServerManager:
    """
    HTTP server lifecycle management with enhanced error handling and resilience.
    Handles server startup, shutdown, configuration, and graceful degradation.
    """
    
    def __init__(self):
        """Initialize the HTTP server manager"""
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
        self.module_logger = error_handler.get_module_logger("core.server_manager")
    
    def create_server(self) -> HTTPServer:
        """
        Create configured HTTP server with error handling
        
        Returns:
            Configured HTTPServer instance
            
        Raises:
            Exception: If server creation fails
        """
        try:
            server_config = config_manager.get_server_config()
            host = server_config["host"]
            port = server_config["port"]
            
            server_address = (host, port)
            server = HTTPServer(server_address, ModularRequestHandler)
            
            self.module_logger.info(f"Created HTTP server on {host}:{port}")
            return server
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.server_manager",
                function_name="create_server",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL
            )
            self.module_logger.critical(f"Server creation failed: {error_response.message}")
            raise
    
    def start_server(self) -> bool:
        """
        Start HTTP server in background thread with error handling
        
        Returns:
            True if server started successfully, False otherwise
        """
        if self.running:
            self.module_logger.warning("Server is already running")
            return False
        
        try:
            self.server = self.create_server()
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.running = True
            self.module_logger.info("HTTP server started successfully")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.server_manager",
                function_name="start_server",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL
            )
            self.module_logger.error(f"Failed to start server: {error_response.message}")
            return False
    
    def stop_server(self) -> bool:
        """
        Stop HTTP server and clean up resources with error handling
        
        Returns:
            True if server stopped successfully, False otherwise
        """
        if not self.running:
            self.module_logger.warning("Server is not running")
            return False
        
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
                self.server = None
            
            if self.server_thread:
                self.server_thread.join(timeout=5.0)
                self.server_thread = None
            
            self.running = False
            self.module_logger.info("HTTP server stopped successfully")
            return True
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.server_manager",
                function_name="stop_server",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH
            )
            self.module_logger.error(f"Failed to stop server: {error_response.message}")
            return False
    
    def _run_server(self):
        """Run the HTTP server with error handling (internal method for thread)"""
        try:
            if self.server:
                self.module_logger.info("HTTP server thread started")
                self.server.serve_forever()
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.server_manager",
                function_name="_run_server",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL
            )
            self.module_logger.critical(f"Server runtime error: {error_response.message}")
        finally:
            self.running = False
            self.module_logger.info("HTTP server thread stopped")
    
    def is_running(self) -> bool:
        """
        Check if server is running
        
        Returns:
            True if server is running, False otherwise
        """
        return self.running
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information with enhanced diagnostics
        
        Returns:
            Dictionary with server status, configuration, and health metrics
        """
        try:
            server_config = config_manager.get_server_config()
            error_stats = error_handler.get_error_statistics()
            
            return {
                "running": self.running,
                "host": server_config["host"],
                "port": server_config["port"],
                "timeout": server_config["timeout"],
                "routes_registered": len(request_router.get_routes()),
                "task_queue_size": task_queue.get_queue_size(),
                "error_statistics": error_stats,
                "health_status": self._get_health_status()
            }
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                module_name="core.server_manager",
                function_name="get_server_info",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.LOW
            )
            return {
                "error": True,
                "message": error_response.message,
                "running": self.running
            }
    
    def _get_health_status(self) -> str:
        """
        Determine server health status based on error rates and system state
        
        Returns:
            Health status string: "healthy", "degraded", "unhealthy"
        """
        try:
            error_stats = error_handler.get_error_statistics()
            recent_errors = error_stats.get("recent_errors", 0)
            
            # Check circuit breakers
            circuit_breakers = error_stats.get("circuit_breakers", {})
            open_breakers = sum(1 for state in circuit_breakers.values() if state == "open")
            
            if not self.running:
                return "unhealthy"
            elif open_breakers > 0 or recent_errors > 10:
                return "degraded"
            else:
                return "healthy"
                
        except Exception:
            return "unknown"

# Global HTTP server manager instance
server_manager = HTTPServerManager()