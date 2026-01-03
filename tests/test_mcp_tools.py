#!/usr/bin/env python3
"""
MCP Tools Backward Compatibility Test

This script tests that existing MCP tools are properly defined and maintain their signatures.
It verifies that the MCP server has all expected tools and they have correct parameters.

Requirements: 1.5
"""

import sys
import asyncio
from typing import Dict, Any, Callable

def load_mcp_server():
    """Load and initialize the modular MCP server."""
    try:
        # Add Server directory to path
        import os
        server_path = os.path.join(os.getcwd(), "Server")
        if server_path not in sys.path:
            sys.path.insert(0, server_path)
        
        # Import the server initialization function
        from Server.MCP_Server import initialize_server
        
        # Initialize the modular server (this will load all modules)
        mcp = initialize_server()
        return mcp
    except Exception as e:
        print(f"Failed to load MCP server: {e}")
        return None

def get_mcp_tools(mcp_instance) -> Dict[str, Callable]:
    """Extract all MCP tools from the initialized server."""
    try:
        # Get all registered tools using FastMCP's list_tools method
        tools_list = asyncio.run(mcp_instance.list_tools())
        tools = {tool.name: tool for tool in tools_list}
        return tools
    except Exception as e:
        print(f"Failed to get MCP tools: {e}")
        return {}

def analyze_tool_signature(tool) -> Dict[str, Any]:
    """Analyze a tool's signature from FastMCP tool object."""
    try:
        # Get tool information from FastMCP tool object
        tool_info = {
            "name": tool.name,
            "description": tool.description if hasattr(tool, 'description') else "",
            "parameters": []
        }
        
        # Debug: print tool attributes
        # print(f"    Debug - Tool attributes: {[attr for attr in dir(tool) if not attr.startswith('_')]}")
        
        # Extract parameters from the tool's input schema if available
        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            schema = tool.inputSchema
            # print(f"    Debug - Input schema: {schema}")
            if 'properties' in schema:
                for param_name, param_info in schema['properties'].items():
                    param_type = param_info.get('type', 'Any')
                    required = param_name in schema.get('required', [])
                    
                    tool_info["parameters"].append({
                        "name": param_name,
                        "type": param_type,
                        "required": required
                    })
        elif hasattr(tool, 'input_schema') and tool.input_schema:
            schema = tool.input_schema
            # print(f"    Debug - Input schema: {schema}")
            if 'properties' in schema:
                for param_name, param_info in schema['properties'].items():
                    param_type = param_info.get('type', 'Any')
                    required = param_name in schema.get('required', [])
                    
                    tool_info["parameters"].append({
                        "name": param_name,
                        "type": param_type,
                        "required": required
                    })
        # else:
        #     print(f"    Debug - No input schema found")
        
        return tool_info
    except Exception as e:
        print(f"Error analyzing tool signature: {e}")
        return {
            "name": getattr(tool, 'name', 'unknown'),
            "description": "",
            "parameters": []
        }

def test_existing_toolpath_tools():
    """Test that existing toolpath tools are properly defined."""
    print("Testing Existing Toolpath MCP Tools")
    print("=" * 40)
    
    # Load MCP server
    mcp = load_mcp_server()
    assert mcp is not None, "Failed to load MCP server"
    
    # Get all tools
    tools = get_mcp_tools(mcp)
    print(f"Found {len(tools)} MCP tools total")
    
    # Define expected existing tools and their signatures
    expected_tools = {
        "list_cam_toolpaths": {
            "parameters": [],  # No parameters expected
            "description_contains": ["list", "toolpath", "CAM"]
        },
        "get_toolpath_details": {
            "parameters": [{"name": "toolpath_id", "type": "string", "required": True}],
            "description_contains": ["detailed", "parameters", "toolpath"]
        },
        "modify_toolpath_parameter": {
            "parameters": [
                {"name": "toolpath_id", "type": "string", "required": True},
                {"name": "parameter_name", "type": "string", "required": True},
                {"name": "value", "type": "string", "required": True}
            ],
            "description_contains": ["modify", "parameter", "toolpath"]
        },
        "list_cam_tools": {
            "parameters": [],
            "description_contains": ["list", "tools", "CAM"]
        },
        "get_tool_info": {
            "parameters": [{"name": "tool_id", "type": "string", "required": True}],
            "description_contains": ["tool", "information", "detailed"]
        }
    }
    
    # Test each expected tool
    for tool_name, expected in expected_tools.items():
        print(f"\n  Testing {tool_name}...")
        
        assert tool_name in tools, f"Tool {tool_name} not found"
        
        # Analyze the tool
        tool_info = analyze_tool_signature(tools[tool_name])
        
        # Check parameters
        expected_params = expected.get("parameters", [])
        actual_params = tool_info["parameters"]
        
        assert len(expected_params) == len(actual_params), f"Expected {len(expected_params)} parameters, got {len(actual_params)}"
        
        # Check each parameter
        for i, expected_param in enumerate(expected_params):
            assert i < len(actual_params), f"Missing parameter {expected_param['name']}"
            actual_param = actual_params[i]
            
            assert actual_param["name"] == expected_param["name"], f"Parameter name mismatch: expected {expected_param['name']}, got {actual_param['name']}"
            assert actual_param["required"] == expected_param["required"], f"Parameter required mismatch for {expected_param['name']}"
        
        # Check description contains expected keywords
        description = tool_info["description"].lower()
        for keyword in expected.get("description_contains", []):
            assert keyword.lower() in description, f"Description missing keyword '{keyword}'"
        
        print(f"    ✓ {tool_name} passed all checks")

def test_new_height_tools():
    """Test that new height tools are properly defined."""
    print("\n\nTesting New Height-Enabled MCP Tools")
    print("=" * 40)
    
    # Load MCP server
    mcp = load_mcp_server()
    assert mcp is not None, "Failed to load MCP server"
    
    # Get all tools
    tools = get_mcp_tools(mcp)
    
    # Define expected new tools
    new_tools = {
        "list_toolpaths_with_heights": {
            "parameters": [],
            "description_contains": ["height", "toolpath", "list"]
        },
        "get_toolpath_heights": {
            "parameters": [{"name": "toolpath_id", "type": "string", "required": True}],
            "description_contains": ["height", "toolpath", "detailed"]
        }
    }
    
    for tool_name, expected in new_tools.items():
        print(f"\n  Testing {tool_name}...")
        
        assert tool_name in tools, f"New tool {tool_name} not found"
        
        # Analyze the tool
        tool_info = analyze_tool_signature(tools[tool_name])
        
        # Check parameters
        expected_params = expected.get("parameters", [])
        actual_params = tool_info["parameters"]
        
        assert len(expected_params) == len(actual_params), f"Expected {len(expected_params)} parameters, got {len(actual_params)}"
        
        # Check description contains expected keywords
        description = tool_info["description"].lower()
        expected_keywords = expected.get("description_contains", [])
        missing_keywords = [kw for kw in expected_keywords if kw.lower() not in description]
        
        if missing_keywords:
            print(f"    ⚠️  WARNING: Description missing keywords: {missing_keywords}")
        
        print(f"    ✅ PASSED: {tool_name} signature correct")

if __name__ == "__main__":
    test_existing_toolpath_tools()
    test_new_height_tools()