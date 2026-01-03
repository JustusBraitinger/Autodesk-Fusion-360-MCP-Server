# Integration Module
# Integrates the modular system with the main Fusion 360 Add-In

import logging
from typing import Dict, Any, Optional
from .config import config_manager
from .router import request_router
from .server import server_manager
from .loader import module_loader
from .task_queue import task_queue
from .validation import request_validator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModularSystemIntegration:
    """
    Integration manager for the modular Fusion 360 Add-In system.
    Coordinates initialization and management of all modular components.
    """
    
    def __init__(self):
        """Initialize the modular system integration"""
        self.initialized = False
        self.components_status = {
            'config': False,
            'router': False,
            'loader': False,
            'server': False,
            'task_queue': False,
            'validation': False
        }
    
    def initialize_system(self) -> bool:
        """
        Initialize the complete modular system
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing modular Fusion 360 Add-In system...")
            
            # 1. Initialize configuration
            if not self._initialize_configuration():
                return False
            
            # 2. Initialize validation system
            if not self._initialize_validation():
                return False
            
            # 3. Initialize router
            if not self._initialize_router():
                return False
            
            # 4. Initialize task queue
            if not self._initialize_task_queue():
                return False
            
            # 5. Load handler modules
            if not self._initialize_module_loader():
                return False
            
            # 6. Initialize HTTP server
            if not self._initialize_server():
                return False
            
            self.initialized = True
            logger.info("Modular system initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize modular system: {str(e)}")
            return False
    
    def _initialize_configuration(self) -> bool:
        """Initialize configuration manager with detailed validation"""
        try:
            # Perform detailed validation
            validation_result = config_manager.validate_config_detailed()
            
            if not validation_result['valid']:
                logger.error("Configuration validation failed:")
                for error in validation_result['errors']:
                    logger.error(f"  - {error}")
                
                if validation_result['resolution_guidance']:
                    logger.error("Resolution guidance:")
                    for guidance in validation_result['resolution_guidance']:
                        logger.error(f"  - {guidance}")
                
                return False
            
            # Log warnings if any
            if validation_result['warnings']:
                logger.warning("Configuration warnings:")
                for warning in validation_result['warnings']:
                    logger.warning(f"  - {warning}")
            
            # Log conflicts if any
            if validation_result['conflicts']:
                logger.warning("Configuration conflicts:")
                for conflict in validation_result['conflicts']:
                    logger.warning(f"  - {conflict}")
            
            self.components_status['config'] = True
            logger.debug("Configuration manager initialized with detailed validation")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {str(e)}")
            return False
    
    def _initialize_validation(self) -> bool:
        """Initialize request validation system"""
        try:
            # Validation rules are already registered in the validation module
            # Just verify the validator is working
            test_data = {"test": "value"}
            request_validator.validate_request("/test", "GET", test_data)
            
            self.components_status['validation'] = True
            logger.debug("Request validation system initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize validation: {str(e)}")
            return False
    
    def _initialize_router(self) -> bool:
        """Initialize request router"""
        try:
            # Router is already initialized, just verify it's working
            routes = request_router.get_routes()
            
            # Validate routes
            issues = request_router.validate_routes()
            if issues:
                logger.warning(f"Router validation issues: {issues}")
            
            self.components_status['router'] = True
            logger.debug(f"Request router initialized with {len(routes)} routes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize router: {str(e)}")
            return False
    
    def _initialize_task_queue(self) -> bool:
        """Initialize task queue system"""
        try:
            # Task queue is already initialized, just verify it's working
            queue_size = task_queue.get_queue_size()
            
            self.components_status['task_queue'] = True
            logger.debug(f"Task queue initialized (current size: {queue_size})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize task queue: {str(e)}")
            return False
    
    def _initialize_module_loader(self) -> bool:
        """Initialize module loader and load handler modules"""
        try:
            # Load all handler modules
            loaded_count = module_loader.load_all_modules()
            
            if loaded_count == 0:
                logger.warning("No handler modules were loaded")
            
            # Validate loaded modules
            issues = module_loader.validate_all_modules()
            if issues:
                logger.warning(f"Module validation issues: {issues}")
            
            self.components_status['loader'] = True
            logger.debug(f"Module loader initialized, loaded {loaded_count} modules")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize module loader: {str(e)}")
            return False
    
    def _initialize_server(self) -> bool:
        """Initialize HTTP server manager"""
        try:
            # Server manager is already initialized, just verify configuration
            server_info = server_manager.get_server_info()
            
            self.components_status['server'] = True
            logger.debug(f"HTTP server manager initialized: {server_info}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {str(e)}")
            return False
    
    def start_system(self) -> bool:
        """
        Start the modular system (HTTP server)
        
        Returns:
            True if system started successfully, False otherwise
        """
        if not self.initialized:
            logger.error("System not initialized. Call initialize_system() first.")
            return False
        
        try:
            # Start HTTP server
            if server_manager.start_server():
                logger.info("Modular system started successfully")
                return True
            else:
                logger.error("Failed to start HTTP server")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start modular system: {str(e)}")
            return False
    
    def stop_system(self) -> bool:
        """
        Stop the modular system
        
        Returns:
            True if system stopped successfully, False otherwise
        """
        try:
            # Stop HTTP server
            if server_manager.stop_server():
                logger.info("Modular system stopped successfully")
                return True
            else:
                logger.error("Failed to stop HTTP server")
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop modular system: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            Dictionary with system status information
        """
        status = {
            'initialized': self.initialized,
            'components': self.components_status.copy(),
            'server': server_manager.get_server_info(),
            'router_stats': request_router.get_stats(),
            'loaded_modules': len(module_loader.get_loaded_modules()),
            'task_queue_size': task_queue.get_queue_size()
        }
        
        return status
    
    def reload_modules(self) -> bool:
        """
        Reload all handler modules
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            # Clear existing routes
            request_router.routes.clear()
            
            # Reload modules
            loaded_count = module_loader.load_all_modules()
            
            logger.info(f"Reloaded {loaded_count} modules")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload modules: {str(e)}")
            return False
    
    def update_configuration(self, category: str, endpoint_group: str, endpoint_name: str, path: str) -> bool:
        """
        Update configuration and propagate changes to all modules
        
        Args:
            category: Workspace category
            endpoint_group: Group within the category
            endpoint_name: Name of the endpoint
            path: New URL path
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate the change before applying
            validation_result = config_manager.validate_config_detailed()
            if not validation_result['valid']:
                logger.error("Cannot update configuration - current configuration is invalid")
                return False
            
            # Update the configuration
            config_manager.update_endpoint(category, endpoint_group, endpoint_name, path)
            
            # Validate after update
            validation_result = config_manager.validate_config_detailed()
            if not validation_result['valid']:
                logger.error("Configuration update resulted in invalid configuration")
                for error in validation_result['errors']:
                    logger.error(f"  - {error}")
                return False
            
            # Notify all loaded modules of the configuration change
            for module_info in module_loader.get_loaded_modules():
                changes = config_manager.get_configuration_changes(module_info.name)
                if changes:
                    logger.debug(f"Notified module {module_info.name} of {len(changes)} configuration changes")
            
            logger.info(f"Successfully updated configuration: {category}.{endpoint_group}.{endpoint_name} = {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {str(e)}")
            return False
    
    def add_category_configuration(self, category: str, config: Dict[str, Any]) -> bool:
        """
        Add category-specific configuration
        
        Args:
            category: Category name
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_manager.add_category_configuration(category, config)
            logger.info(f"Added category configuration for: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add category configuration: {str(e)}")
            return False
    
    def validate_current_configuration(self) -> Dict[str, Any]:
        """
        Validate current configuration and return detailed results
        
        Returns:
            Detailed validation results
        """
        return config_manager.validate_config_detailed()

# Global modular system integration instance
modular_system = ModularSystemIntegration()