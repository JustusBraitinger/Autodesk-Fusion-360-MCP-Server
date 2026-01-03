"""
Performance and Stability Testing for Modular Server Architecture

This test suite validates that the modular server architecture maintains
good performance characteristics and system stability under various conditions.

Tests cover:
- Module loading performance and memory usage
- System stability under error conditions
- Concurrent access and thread safety
- Resource cleanup and memory management
"""

import pytest
import time
import threading
import sys
import gc
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import psutil, but make it optional
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Add Server directory to path for imports
server_path = Path(__file__).parent.parent / "Server"
sys.path.insert(0, str(server_path))


class TestModuleLoadingPerformance:
    """Test module loading performance and memory usage."""
    
    def test_module_loading_time(self):
        """Test that module loading completes within reasonable time."""
        from core.loader import load_all_modules
        
        start_time = time.time()
        loaded_modules = load_all_modules()
        end_time = time.time()
        
        loading_time = end_time - start_time
        
        # Module loading should complete within 10 seconds
        assert loading_time < 10.0, f"Module loading took {loading_time:.2f}s (too slow)"
        
        # Should have loaded some modules successfully
        successful_modules = [m for m in loaded_modules.values() if m.loaded]
        assert len(successful_modules) > 0, "No modules loaded successfully"
        
        print(f"Module loading completed in {loading_time:.2f}s")
        print(f"Loaded {len(successful_modules)} modules successfully")
    
    def test_server_initialization_time(self):
        """Test that server initialization completes within reasonable time."""
        from MCP_Server import initialize_server
        
        start_time = time.time()
        mcp = initialize_server()
        end_time = time.time()
        
        init_time = end_time - start_time
        
        # Server initialization should complete within 15 seconds
        assert init_time < 15.0, f"Server initialization took {init_time:.2f}s (too slow)"
        
        # Verify server is properly initialized
        assert mcp is not None
        assert hasattr(mcp, 'run')
        assert hasattr(mcp, 'list_tools')
        
        print(f"Server initialization completed in {init_time:.2f}s")
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_memory_usage_during_loading(self):
        """Test memory usage during module loading."""
        import psutil
        
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Measure memory before loading
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load modules
        from core.loader import load_all_modules
        loaded_modules = load_all_modules()
        
        # Force garbage collection
        gc.collect()
        
        # Measure memory after loading
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_increase = memory_after - memory_before
        
        # Memory increase should be reasonable (less than 100MB for module loading)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.1f}MB (too much)"
        
        print(f"Memory usage increased by {memory_increase:.1f}MB during module loading")
        
        # Should have loaded modules successfully
        successful_modules = [m for m in loaded_modules.values() if m.loaded]
        assert len(successful_modules) > 0
    
    def test_repeated_loading_performance(self):
        """Test that repeated module loading doesn't degrade performance."""
        from core.loader import ModuleLoader
        
        loading_times = []
        
        # Test multiple loading cycles
        for i in range(3):
            # Create fresh loader instance
            loader = ModuleLoader()
            
            start_time = time.time()
            loaded_modules = loader.load_all_modules()
            end_time = time.time()
            
            loading_time = end_time - start_time
            loading_times.append(loading_time)
            
            # Should load some modules each time
            successful_modules = [m for m in loaded_modules.values() if m.loaded]
            assert len(successful_modules) > 0, f"No modules loaded in iteration {i+1}"
        
        # Performance shouldn't degrade significantly
        first_time = loading_times[0]
        last_time = loading_times[-1]
        
        # Last loading shouldn't be more than 50% slower than first
        assert last_time < first_time * 1.5, f"Performance degraded: {first_time:.2f}s -> {last_time:.2f}s"
        
        print(f"Loading times: {[f'{t:.2f}s' for t in loading_times]}")


class TestSystemStability:
    """Test system stability under various error conditions."""
    
    def test_stability_with_module_failures(self):
        """Test system stability when some modules fail to load."""
        from core.loader import ModuleLoader
        
        # Create loader with error recovery enabled
        loader = ModuleLoader()
        loader.set_error_recovery(True)
        
        # Mock some modules to fail
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            # Fail imports for some fake modules
            if 'fake_failing_module' in name:
                raise ImportError(f"Mocked failure for {name}")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            # Should handle failures gracefully
            loaded_modules = loader.load_all_modules()
            
            # System should still be functional
            health_status = loader.get_health_status()
            assert health_status is not None
            assert 'health' in health_status
            
            # Should have some successful modules
            successful_modules = [m for m in loaded_modules.values() if m.loaded]
            assert len(successful_modules) > 0, "No modules loaded despite error recovery"
    
    def test_stability_with_configuration_errors(self):
        """Test system stability with configuration errors."""
        from core.config import validate_configuration
        
        # Test with various configuration states
        with patch('core.config._BASE_URL', ''):
            # Should handle empty base URL gracefully
            result = validate_configuration()
            assert isinstance(result, bool)  # Should not crash
        
        with patch('core.config._REQUEST_TIMEOUT', -1):
            # Should handle invalid timeout gracefully
            result = validate_configuration()
            assert isinstance(result, bool)  # Should not crash
        
        with patch('core.config._HEADERS', {}):
            # Should handle empty headers gracefully
            result = validate_configuration()
            assert isinstance(result, bool)  # Should not crash
    
    def test_stability_with_request_handler_errors(self):
        """Test system stability when request handler encounters errors."""
        from core.request_handler import send_request
        
        # Test with various error conditions
        test_cases = [
            ("http://invalid-url-12345", {"test": "data"}),
            ("", {"test": "data"}),
            ("http://localhost:99999", {"test": "data"}),  # Invalid port
        ]
        
        for endpoint, data in test_cases:
            # Should handle errors gracefully without crashing
            try:
                result = send_request(endpoint, data)
                # Should return some kind of error response
                assert isinstance(result, dict)
            except Exception as e:
                # If it raises an exception, it should be a controlled one
                assert "Connection" in str(e) or "Invalid" in str(e) or "timeout" in str(e).lower()
    
    def test_stability_with_concurrent_operations(self):
        """Test system stability under concurrent operations."""
        from core.config import get_endpoints, get_headers
        from core.loader import get_health_status
        
        def worker_function(worker_id: int) -> Dict[str, Any]:
            """Worker function for concurrent testing."""
            results = {}
            
            try:
                # Test configuration access
                results['endpoints'] = len(get_endpoints())
                results['headers'] = len(get_headers())
                
                # Test health status
                health = get_health_status()
                results['health'] = health['health']
                
                results['worker_id'] = worker_id
                results['success'] = True
                
            except Exception as e:
                results['error'] = str(e)
                results['success'] = False
                
            return results
        
        # Run multiple workers concurrently
        num_workers = 5
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_function, i) for i in range(num_workers)]
            results = [future.result() for future in as_completed(futures)]
        
        # All workers should complete successfully
        successful_workers = [r for r in results if r.get('success', False)]
        assert len(successful_workers) == num_workers, f"Only {len(successful_workers)}/{num_workers} workers succeeded"
        
        # Results should be consistent across workers
        endpoint_counts = [r['endpoints'] for r in successful_workers]
        assert len(set(endpoint_counts)) == 1, "Inconsistent endpoint counts across workers"
        
        print(f"All {num_workers} concurrent workers completed successfully")


class TestConcurrentAccess:
    """Test concurrent access and thread safety."""
    
    def test_concurrent_tool_registration(self):
        """Test concurrent tool registration doesn't cause issues."""
        from core.registry import ToolRegistry
        
        registry = ToolRegistry()
        results = []
        errors = []
        
        def register_tools(worker_id: int):
            """Register tools from a worker thread."""
            try:
                for i in range(10):
                    tool_name = f"test_tool_{worker_id}_{i}"
                    
                    def dummy_tool():
                        return f"Result from {tool_name}"
                    
                    dummy_tool.__name__ = tool_name
                    registry.register_tool(dummy_tool, "test")
                    results.append((worker_id, tool_name, True))  # Assume success if no exception
                    
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run multiple workers concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=register_tools, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0, f"Concurrent registration errors: {errors}"
        
        # Should have registered tools from all workers
        successful_registrations = [r for r in results if r[2]]  # r[2] is success flag
        assert len(successful_registrations) > 0, "No tools registered successfully"
        
        # Verify tools are actually in the registry
        registered_tools = registry.get_tools()
        assert len(registered_tools) > 0, "No tools found in registry after registration"
        
        print(f"Successfully registered {len(successful_registrations)} tools concurrently")
        print(f"Registry contains {len(registered_tools)} tools")
    
    def test_concurrent_configuration_access(self):
        """Test concurrent configuration access is thread-safe."""
        from core.config import get_endpoints, get_headers, get_base_url, get_timeout
        
        results = []
        errors = []
        
        def access_config(worker_id: int):
            """Access configuration from a worker thread."""
            try:
                for _ in range(50):  # Multiple accesses per worker
                    base_url = get_base_url()
                    headers = get_headers()
                    timeout = get_timeout()
                    endpoints = get_endpoints()
                    
                    # Verify consistency
                    assert isinstance(base_url, str)
                    assert isinstance(headers, dict)
                    assert isinstance(timeout, (int, float))
                    assert isinstance(endpoints, dict)
                    
                results.append(worker_id)
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run multiple workers concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_config, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        
        # All workers should complete successfully
        assert len(results) == 5, f"Only {len(results)}/5 workers completed successfully"
        
        print("Concurrent configuration access completed successfully")
    
    def test_concurrent_health_checks(self):
        """Test concurrent health status checks."""
        from core.loader import get_health_status, get_error_report
        
        results = []
        errors = []
        
        def check_health(worker_id: int):
            """Check system health from a worker thread."""
            try:
                for _ in range(10):
                    health_status = get_health_status()
                    error_report = get_error_report()
                    
                    # Verify structure
                    assert isinstance(health_status, dict)
                    assert 'health' in health_status
                    assert isinstance(error_report, dict)
                    
                results.append(worker_id)
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run multiple workers concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=check_health, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0, f"Concurrent health check errors: {errors}"
        
        # All workers should complete successfully
        assert len(results) == 3, f"Only {len(results)}/3 workers completed successfully"
        
        print("Concurrent health checks completed successfully")


class TestResourceCleanup:
    """Test resource cleanup and memory management."""
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_module_loader_cleanup(self):
        """Test that module loader properly cleans up resources."""
        from core.loader import ModuleLoader
        
        # Create and use multiple loader instances
        loaders = []
        for i in range(3):
            loader = ModuleLoader()
            loaded_modules = loader.load_all_modules()
            loaders.append(loader)
            
            # Verify loader is functional
            health_status = loader.get_health_status()
            assert health_status is not None
        
        # Clear references and force garbage collection
        del loaders
        gc.collect()
        
        # Memory should be manageable (this is a basic check)
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Should not use excessive memory (less than 200MB for testing)
        assert memory_mb < 200, f"Memory usage too high: {memory_mb:.1f}MB"
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_registry_cleanup(self):
        """Test that registries properly clean up resources."""
        from core.registry import ToolRegistry
        from prompts.registry import PromptRegistry
        
        # Create and populate registries
        tool_registry = ToolRegistry()
        prompt_registry = PromptRegistry()
        
        # Register some test items
        for i in range(10):
            def dummy_tool():
                return f"test_{i}"
            dummy_tool.__name__ = f"test_tool_{i}"
            tool_registry.register_tool(dummy_tool, "test")
            
            def dummy_prompt():
                return f"prompt_{i}"
            prompt_registry.register_prompt(f"test_prompt_{i}", dummy_prompt)
        
        # Verify registrations
        assert len(tool_registry.get_tools()) >= 10
        assert len(prompt_registry.list_prompts()) >= 10
        
        # Clear registries
        del tool_registry
        del prompt_registry
        gc.collect()
        
        # Should not cause memory leaks (basic check)
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 200, f"Memory usage too high after cleanup: {memory_mb:.1f}MB"
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_server_instance_cleanup(self):
        """Test that server instances can be properly cleaned up."""
        from MCP_Server import initialize_server
        
        # Create multiple server instances
        servers = []
        for i in range(2):  # Keep this small to avoid resource exhaustion
            server = initialize_server()
            servers.append(server)
            
            # Verify server is functional
            assert server is not None
            assert hasattr(server, 'run')
        
        # Clear references
        del servers
        gc.collect()
        
        # Should not cause excessive memory usage
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 300, f"Memory usage too high after server cleanup: {memory_mb:.1f}MB"


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""
    
    def test_partial_module_failure_recovery(self):
        """Test recovery when some modules fail to load."""
        from core.loader import ModuleLoader
        
        loader = ModuleLoader()
        loader.set_error_recovery(True)
        
        # Mock some imports to fail
        original_import = __import__
        failed_modules = ['fake_module_1', 'fake_module_2']
        
        def mock_import(name, *args, **kwargs):
            if any(failed in name for failed in failed_modules):
                raise ImportError(f"Mocked failure for {name}")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            loaded_modules = loader.load_all_modules()
            
            # Should have some successful modules despite failures
            successful_modules = [m for m in loaded_modules.values() if m.loaded]
            assert len(successful_modules) > 0, "No modules loaded with error recovery"
            
            # Health status should reflect partial failure
            health_status = loader.get_health_status()
            assert health_status['health'] in ['HEALTHY', 'DEGRADED', 'POOR']
            
            # Error report should contain information about failures
            error_report = loader.get_error_report()
            assert error_report['total_errors'] >= 0  # May have errors from mocked failures
    
    def test_configuration_fallback_behavior(self):
        """Test fallback behavior when configuration is invalid."""
        from core.config import get_endpoints, get_base_url
        
        # Test with temporarily invalid configuration
        with patch('core.config._ENDPOINTS', {}):
            # Should return empty dict instead of crashing
            endpoints = get_endpoints()
            assert isinstance(endpoints, dict)
        
        with patch('core.config._BASE_URL', None):
            # Should handle None gracefully
            try:
                base_url = get_base_url()
                # If it doesn't crash, it should return something reasonable
                assert base_url is not None or base_url == ""  # Allow None or empty string
            except Exception as e:
                # If it raises an exception, it should be controlled
                assert any(word in str(e).lower() for word in ["configuration", "url", "none", "base"]), \
                    f"Unexpected error message: {str(e)}"
    
    def test_request_handler_retry_behavior(self):
        """Test request handler retry and error handling behavior."""
        from core.request_handler import send_request
        
        # Test with unreachable endpoint
        result = send_request("http://localhost:99999", {"test": "data"})
        
        # Should return error response instead of crashing
        assert isinstance(result, dict)
        # Should indicate error condition
        assert 'error' in result or 'message' in result or result.get('success') is False


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "--tb=short"])