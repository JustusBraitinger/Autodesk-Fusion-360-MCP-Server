import adsk.core
import adsk.fusion
import traceback
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Start HTTP server for remote control
        server = DebuggerHTTPServer()
        server.start()
        
        ui.messageBox('FusionMCPBridge Debugger started on port 5002')
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        # Stop HTTP server
        if hasattr(stop, 'server'):
            stop.server.stop()
    except:
        pass


class DebuggerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/addon/restart':
            self.restart_fusion_mcp_bridge()
        elif self.path == '/addon/stop':
            self.stop_fusion_mcp_bridge()
        elif self.path == '/addon/start':
            self.start_fusion_mcp_bridge()
        elif self.path == '/addon/status':
            self.get_addon_status()
        else:
            self.send_error(404, "Not Found")
    
    def restart_fusion_mcp_bridge(self):
        try:
            app = adsk.core.Application.get()
            scripts = app.scripts
            
            target_addon = None
            for script in scripts:
                if script.name == "FusionMCPBridge" or "FusionMCPBridge" in script.name:
                    target_addon = script
                    break
            
            if not target_addon:
                self.send_json_response({"error": "FusionMCPBridge add-in not found"}, 404)
                return
            
            # Stop if running
            if target_addon.isRunning:
                target_addon.stop()
                app.log("FusionMCPBridge stopped by debugger")
            
            # Start
            target_addon.run()
            app.log("FusionMCPBridge restarted by debugger")
            
            self.send_json_response({
                "success": True,
                "message": "FusionMCPBridge restarted",
                "status": "running" if target_addon.isRunning else "stopped"
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def stop_fusion_mcp_bridge(self):
        try:
            app = adsk.core.Application.get()
            scripts = app.scripts
            
            target_addon = None
            for script in scripts:
                if script.name == "FusionMCPBridge" or "FusionMCPBridge" in script.name:
                    target_addon = script
                    break
            
            if not target_addon:
                self.send_json_response({"error": "FusionMCPBridge add-in not found"}, 404)
                return
            
            if target_addon.isRunning:
                target_addon.stop()
            
            self.send_json_response({
                "success": True,
                "message": "FusionMCPBridge stopped",
                "status": "stopped"
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def start_fusion_mcp_bridge(self):
        try:
            app = adsk.core.Application.get()
            scripts = app.scripts
            
            target_addon = None
            for script in scripts:
                if script.name == "FusionMCPBridge" or "FusionMCPBridge" in script.name:
                    target_addon = script
                    break
            
            if not target_addon:
                self.send_json_response({"error": "FusionMCPBridge add-in not found"}, 404)
                return
            
            if not target_addon.isRunning:
                target_addon.run()
            
            self.send_json_response({
                "success": True,
                "message": "FusionMCPBridge started",
                "status": "running" if target_addon.isRunning else "stopped"
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def get_addon_status(self):
        try:
            app = adsk.core.Application.get()
            scripts = app.scripts
            
            target_addon = None
            for script in scripts:
                if script.name == "FusionMCPBridge" or "FusionMCPBridge" in script.name:
                    target_addon = script
                    break
            
            if not target_addon:
                self.send_json_response({"error": "FusionMCPBridge add-in not found"}, 404)
                return
            
            self.send_json_response({
                "name": target_addon.name,
                "status": "running" if target_addon.isRunning else "stopped",
                "id": target_addon.id,
                "isValid": target_addon.isValid
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass


class DebuggerHTTPServer:
    def __init__(self, port=5002):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        self.server = HTTPServer(('localhost', self.port), DebuggerRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        stop.server = self  # Store reference for cleanup
    
    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
