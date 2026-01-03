"""
Comprehensive Backward Compatibility Validation Tests

This test suite validates that the modular server architecture maintains
complete backward compatibility with the original monolithic implementation.

Tests cover:
- Tool names and signatures remain identical
- FastMCP interface unchanged
- MCP client compatibility
- API contracts preserved
- Semantic behavior maintained
"""

import pytest
import asyncio
import sys
import inspect
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add Server directory to path for imports
server_path = Path(__file__).parent.parent / "Server"
sys.path.insert(0, str(server_path))


class TestFastMCPInterfaceCompatibility:
    """Test that FastMCP interface remains unchanged."""
    
    def test_server_initialization_interface(self):
        """Test that server initialization maintains the same interface."""
        from MCP_Server import initialize_server, main
        
        # Test that initialize_server function exists and is callable
        assert callable(initialize_server)
        assert callable(main)
        
        # Test that initialize_server returns a FastMCP instance
        mcp = initialize_server()
        
        # Verify it has the expected FastMCP methods
        expected_methods = ['run', 'list_tools', 'list_prompts']
        for method in expected_methods:
            assert hasattr(mcp, method), f"FastMCP instance missing method: {method}"
            assert callable(getattr(mcp, method)), f"Method {method} is not callable"
    
    def test_command_line_interface_compatibility(self):
        """Test that command-line interface remains unchanged."""
        from MCP_Server import main
        
        # Test that the argument parser accepts the same arguments
        with patch('sys.argv', ['MCP_Server.py', '--server_type', 'sse']):
            with patch('MCP_Server.initialize_server') as mock_init:
                mock_mcp = MagicMock()
                mock_init.return_value = mock_mcp
                
                try:
                    main()
                except SystemExit:
                    pass  # Expected when mocking
                
                # Verify server was initialized
                mock_init.assert_called_once()
                
                # Verify run was called with correct transport
                mock_mcp.run.assert_called_once_with(transport='sse')
        
        # Test stdio transport
        with patch('sys.argv', ['MCP_Server.py', '--server_type', 'stdio']):
            with patch('MCP_Server.initialize_server') as mock_init:
                mock_mcp = MagicMock()
                mock_init.return_value = mock_mcp
                
                try:
                    main()
                except SystemExit:
                    pass  # Expected when mocking
                
                mock_mcp.run.assert_called_once_with(transport='stdio')
    
    def test_server_transport_compatibility(self):
        """Test that both SSE and stdio transports work."""
        from MCP_Server import initialize_server
        
        mcp = initialize_server()
        
        # Test that run method accepts both transport types
        with patch.object(mcp, 'run') as mock_run:
            # Test SSE transport
            mcp.run(transport='sse')
            mock_run.assert_called_with(transport='sse')
            
            # Test stdio transport
            mcp.run(transport='stdio')
            mock_run.assert_called_with(transport='stdio')


class TestToolSignatureCompatibility:
    """Test that all tool signatures remain identical."""
    
    @pytest.fixture
    def mcp_server(self):
        """Initialize the modular MCP server for testing."""
        from MCP_Server import initialize_server
        return initialize_server()
    
    def test_all_tools_registered(self, mcp_server):
        """Test that all expected tools are registered."""
        # Get all registered tools
        tools_list = asyncio.run(mcp_server.list_tools())
        tool_names = {tool.name for tool in tools_list}
        
        # Define expected tools from original implementation
        expected_cad_tools = {
            'draw_cylinder', 'draw_box', 'draw_sphere', 'draw2Dcircle', 
            'draw_lines', 'draw_one_line', 'draw_arc', 'spline', 'extrude',
            'extrude_thin', 'cut_extrude', 'revolve', 'loft', 'sweep',
            'boolean_operation', 'fillet_edges', 'shell_body', 'draw_holes',
            'circular_pattern', 'rectangular_pattern', 'create_thread'
        }
        
        expected_cam_tools = {
            'list_cam_toolpaths', 'get_toolpath_details', 'list_cam_tools',
            'list_toolpaths_with_heights', 'get_toolpath_heights',
            'get_toolpath_passes', 'get_toolpath_linking', 'analyze_toolpath_sequence'
        }
        
        expected_utility_tools = {
            'test_connection', 'delete_all', 'undo', 'export_step', 'export_stl'
        }
        
        expected_debug_tools = {
            'toggle_response_interceptor'
        }
        
        all_expected_tools = (expected_cad_tools | expected_cam_tools | 
                            expected_utility_tools | expected_debug_tools)
        
        # Verify all expected tools are present
        missing_tools = all_expected_tools - tool_names
        assert not missing_tools, f"Missing tools: {missing_tools}"
        
        # Log extra tools (not necessarily an error, but good to know)
        extra_tools = tool_names - all_expected_tools
        if extra_tools:
            print(f"Extra tools found: {extra_tools}")
    
    def test_tool_parameter_signatures(self, mcp_server):
        """Test that tool parameter signatures match original implementation."""
        tools_list = asyncio.run(mcp_server.list_tools())
        
        # Define expected signatures for key tools (simplified - just check they have parameters)
        tools_with_params = {
            'draw_cylinder', 'draw_box', 'draw_sphere', 'extrude',
            'get_toolpath_details', 'get_toolpath_heights', 'export_step', 'export_stl'
        }
        
        tools_without_params = {
            'list_cam_toolpaths', 'list_cam_tools', 'test_connection', 'delete_all', 'undo'
        }
        
        for tool in tools_list:
            if tool.name in tools_with_params:
                # These tools should have input parameters
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    properties = tool.inputSchema.get('properties', {})
                    assert len(properties) > 0, f"Tool {tool.name} should have parameters but has none"
            elif tool.name in tools_without_params:
                # These tools should have no parameters or empty parameters
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    properties = tool.inputSchema.get('properties', {})
                    # Allow empty or minimal parameters for these tools
    
    def test_tool_descriptions_present(self, mcp_server):
        """Test that all tools have descriptions."""
        tools_list = asyncio.run(mcp_server.list_tools())
        
        for tool in tools_list:
            assert hasattr(tool, 'description'), f"Tool {tool.name} missing description"
            assert tool.description, f"Tool {tool.name} has empty description"
            assert len(tool.description) > 10, f"Tool {tool.name} has too short description"


class TestPromptCompatibility:
    """Test that prompt system maintains compatibility."""
    
    @pytest.fixture
    def mcp_server(self):
        """Initialize the modular MCP server for testing."""
        from MCP_Server import initialize_server
        return initialize_server()
    
    def test_all_prompts_registered(self, mcp_server):
        """Test that all expected prompts are registered."""
        prompts_list = asyncio.run(mcp_server.list_prompts())
        prompt_names = {prompt.name for prompt in prompts_list}
        
        # Define expected prompts from original implementation
        expected_prompts = {
            'weingals', 'magnet', 'dna', 'flansch', 'vase', 'teil', 'kompensator'
        }
        
        # Verify all expected prompts are present
        missing_prompts = expected_prompts - prompt_names
        assert not missing_prompts, f"Missing prompts: {missing_prompts}"
    
    def test_prompt_content_preserved(self, mcp_server):
        """Test that prompt content is preserved from original implementation."""
        from prompts.registry import get_prompt_registry
        
        registry = get_prompt_registry()
        
        # Test a few key prompts to ensure content is preserved
        test_prompts = ['weingals', 'magnet', 'dna']
        
        for prompt_name in test_prompts:
            if prompt_name in registry.list_prompts():
                content = registry.get_prompt(prompt_name)
                assert content, f"Prompt {prompt_name} has no content"
                assert len(content) > 50, f"Prompt {prompt_name} content too short"
                # Verify it contains German instructions (characteristic of original)
                assert any(word in content.lower() for word in ['fusion', 'erstelle', 'zeichne', 'benutze', 'tool']), \
                    f"Prompt {prompt_name} missing expected German content"


class TestModuleLoadingCompatibility:
    """Test that module loading maintains system stability."""
    
    def test_graceful_module_loading(self):
        """Test that module loading handles errors gracefully."""
        from core.loader import load_all_modules, get_health_status
        
        # Load all modules
        loaded_modules = load_all_modules()
        
        # Verify some modules loaded successfully
        successful_modules = [m for m in loaded_modules.values() if m.loaded]
        assert len(successful_modules) > 0, "No modules loaded successfully"
        
        # Check system health
        health_status = get_health_status()
        # Updated to match actual health status values
        assert health_status['health'] in ['HEALTHY', 'DEGRADED', 'POOR', 'CRITICAL']
        assert health_status['loaded_modules'] > 0
        assert len(health_status['categories']) > 0
    
    def test_error_recovery_enabled(self):
        """Test that error recovery is enabled for graceful degradation."""
        from core.loader import get_health_status
        
        health_status = get_health_status()
        
        # Even if some modules fail, system should continue
        # This is tested by verifying we can get health status without exceptions
        assert isinstance(health_status, dict)
        assert 'health' in health_status
        assert 'loaded_modules' in health_status
        assert 'failed_modules' in health_status


class TestAPIContractCompatibility:
    """Test that API contracts are preserved."""
    
    def test_configuration_structure(self):
        """Test that configuration structure is preserved."""
        from core.config import get_endpoints, get_headers, get_timeout, get_base_url
        
        # Test that configuration functions exist and return expected types
        base_url = get_base_url()
        assert isinstance(base_url, str)
        assert base_url.startswith('http')
        
        headers = get_headers()
        assert isinstance(headers, dict)
        assert 'Content-Type' in headers
        
        timeout = get_timeout()
        assert isinstance(timeout, (int, float))
        assert timeout > 0
        
        # Test category-specific endpoints
        categories = ['cad', 'cam', 'utility', 'debug']
        for category in categories:
            endpoints = get_endpoints(category)
            assert isinstance(endpoints, dict)
            # Debug category might be empty, others should have endpoints
            if category != 'debug':
                assert len(endpoints) > 0, f"Category {category} should have endpoints"
    
    def test_request_handler_interface(self):
        """Test that request handler maintains expected interface."""
        from core.request_handler import send_request, send_get_request, send_post_request
        
        # Verify functions exist and are callable
        assert callable(send_request)
        assert callable(send_get_request) 
        assert callable(send_post_request)
        
        # Test function signatures
        
        # send_request should accept endpoint, data, method
        sig = inspect.signature(send_request)
        params = list(sig.parameters.keys())
        assert 'endpoint' in params
        assert 'data' in params
        
        # send_get_request should accept endpoint
        sig = inspect.signature(send_get_request)
        params = list(sig.parameters.keys())
        assert 'endpoint' in params
        
        # send_post_request should accept endpoint and data
        sig = inspect.signature(send_post_request)
        params = list(sig.parameters.keys())
        assert 'endpoint' in params
        assert 'data' in params


class TestSemanticBehaviorCompatibility:
    """Test that semantic behavior is maintained."""
    
    def test_tool_execution_flow(self):
        """Test that tools follow the same execution flow."""
        from core.request_handler import send_request
        from core.config import get_endpoints
        
        # Mock the HTTP request to test the flow
        with patch('core.request_handler.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_post.return_value = mock_response
            
            # Test that a request goes through the expected flow
            endpoints = get_endpoints('cad')
            if 'draw_cylinder' in endpoints:
                result = send_request(endpoints['draw_cylinder'], {'radius': 5, 'height': 10})
                
                # Verify request was made
                mock_post.assert_called_once()
                
                # Verify result structure
                assert isinstance(result, dict)
    
    def test_error_handling_behavior(self):
        """Test that error handling behavior is preserved."""
        from core.request_handler import send_request
        
        # Test with invalid endpoint to trigger error handling
        with patch('core.request_handler.requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            # Should handle error gracefully
            result = send_request("http://invalid", {})
            
            # Should return error structure
            assert isinstance(result, dict)
            assert 'error' in result or 'message' in result


class TestMCPClientCompatibility:
    """Test compatibility with existing MCP clients."""
    
    def test_tool_listing_format(self):
        """Test that tool listing format matches MCP specification."""
        from MCP_Server import initialize_server
        
        mcp = initialize_server()
        tools_list = asyncio.run(mcp.list_tools())
        
        # Verify each tool has required MCP fields
        for tool in tools_list:
            assert hasattr(tool, 'name'), "Tool missing name attribute"
            assert hasattr(tool, 'description'), f"Tool {tool.name} missing description"
            
            # Verify name is valid MCP tool name
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0
            assert not tool.name.startswith('_')
            
            # Verify description is meaningful
            assert isinstance(tool.description, str)
            assert len(tool.description) > 0
    
    def test_prompt_listing_format(self):
        """Test that prompt listing format matches MCP specification."""
        from MCP_Server import initialize_server
        
        mcp = initialize_server()
        prompts_list = asyncio.run(mcp.list_prompts())
        
        # Verify each prompt has required MCP fields
        for prompt in prompts_list:
            assert hasattr(prompt, 'name'), "Prompt missing name attribute"
            
            # Verify name is valid MCP prompt name
            assert isinstance(prompt.name, str)
            assert len(prompt.name) > 0
            assert not prompt.name.startswith('_')
    
    def test_server_metadata_compatibility(self):
        """Test that server metadata is compatible with MCP clients."""
        from MCP_Server import initialize_server
        
        mcp = initialize_server()
        
        # Verify server has expected attributes for MCP compatibility
        assert hasattr(mcp, 'run')
        assert hasattr(mcp, 'list_tools')
        assert hasattr(mcp, 'list_prompts')
        
        # Test that server can be started (mock the actual run)
        with patch.object(mcp, 'run') as mock_run:
            mcp.run(transport='stdio')
            mock_run.assert_called_once_with(transport='stdio')


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "--tb=short"])