"""
Prompt registry system for centralized prompt management.

This module provides functionality for registering, validating, and managing
prompt templates independently from tool implementations.
"""

import logging
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass


@dataclass
class PromptInfo:
    """Information about a registered prompt."""
    name: str
    function: Callable
    description: str
    category: str = "general"
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PromptRegistry:
    """
    Centralized registry for prompt templates and management.
    
    Provides functionality for:
    - Dynamic prompt registration
    - Prompt validation and dependency checking
    - Category-based prompt organization
    - Template-based prompt generation
    """
    
    def __init__(self):
        self._prompts: Dict[str, PromptInfo] = {}
        self._categories: Dict[str, List[str]] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_prompt(self, name: str, prompt_func: Callable, 
                       description: str = "", category: str = "general",
                       dependencies: List[str] = None) -> bool:
        """
        Register a prompt function with the registry.
        
        Args:
            name: Unique prompt name
            prompt_func: Function that returns the prompt string
            description: Human-readable description of the prompt
            category: Category for organization (default: "general")
            dependencies: List of required tools or other prompts
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        if dependencies is None:
            dependencies = []
            
        if name in self._prompts:
            self._logger.warning(f"Prompt '{name}' already registered, overwriting")
        
        try:
            # Validate prompt function
            if not callable(prompt_func):
                raise ValueError(f"Prompt function for '{name}' is not callable")
            
            # Test prompt function execution
            test_result = prompt_func()
            if not isinstance(test_result, str):
                raise ValueError(f"Prompt function for '{name}' must return a string")
            
            # Register the prompt
            prompt_info = PromptInfo(
                name=name,
                function=prompt_func,
                description=description,
                category=category,
                dependencies=dependencies
            )
            
            self._prompts[name] = prompt_info
            
            # Update category index
            if category not in self._categories:
                self._categories[category] = []
            if name not in self._categories[category]:
                self._categories[category].append(name)
            
            self._logger.info(f"Registered prompt '{name}' in category '{category}'")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to register prompt '{name}': {e}")
            return False
    
    def get_prompt(self, name: str) -> Optional[str]:
        """
        Get a prompt by name.
        
        Args:
            name: Name of the prompt to retrieve
            
        Returns:
            str: The prompt content, or None if not found
        """
        if name not in self._prompts:
            self._logger.error(f"Prompt '{name}' not found")
            return None
        
        try:
            return self._prompts[name].function()
        except Exception as e:
            self._logger.error(f"Failed to execute prompt '{name}': {e}")
            return None
    
    def list_prompts(self, category: str = None) -> List[str]:
        """
        List all available prompts, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List[str]: List of prompt names
        """
        if category is None:
            return list(self._prompts.keys())
        
        return self._categories.get(category, [])
    
    def get_prompt_info(self, name: str) -> Optional[PromptInfo]:
        """
        Get detailed information about a prompt.
        
        Args:
            name: Name of the prompt
            
        Returns:
            PromptInfo: Prompt information, or None if not found
        """
        return self._prompts.get(name)
    
    def get_categories(self) -> List[str]:
        """
        Get all available prompt categories.
        
        Returns:
            List[str]: List of category names
        """
        return list(self._categories.keys())
    
    def validate_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate all prompt dependencies.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping prompt names to missing dependencies
        """
        missing_deps = {}
        
        for prompt_name, prompt_info in self._prompts.items():
            missing = []
            for dep in prompt_info.dependencies:
                # Check if dependency is another prompt
                if dep not in self._prompts:
                    # Could also check for tool dependencies here
                    missing.append(dep)
            
            if missing:
                missing_deps[prompt_name] = missing
        
        return missing_deps
    
    def unregister_prompt(self, name: str) -> bool:
        """
        Remove a prompt from the registry.
        
        Args:
            name: Name of the prompt to remove
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        if name not in self._prompts:
            self._logger.warning(f"Prompt '{name}' not found for removal")
            return False
        
        prompt_info = self._prompts[name]
        category = prompt_info.category
        
        # Remove from main registry
        del self._prompts[name]
        
        # Remove from category index
        if category in self._categories and name in self._categories[category]:
            self._categories[category].remove(name)
            
            # Clean up empty categories
            if not self._categories[category]:
                del self._categories[category]
        
        self._logger.info(f"Unregistered prompt '{name}'")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dict[str, Any]: Statistics about registered prompts
        """
        return {
            "total_prompts": len(self._prompts),
            "categories": len(self._categories),
            "prompts_by_category": {cat: len(prompts) for cat, prompts in self._categories.items()},
            "prompts_with_dependencies": len([p for p in self._prompts.values() if p.dependencies])
        }


# Global registry instance
_global_registry = PromptRegistry()


def get_prompt_registry() -> PromptRegistry:
    """Get the global prompt registry instance."""
    return _global_registry


def register_prompt(name: str, prompt_func: Callable, 
                   description: str = "", category: str = "general",
                   dependencies: List[str] = None) -> bool:
    """Convenience function to register a prompt with the global registry."""
    return _global_registry.register_prompt(name, prompt_func, description, category, dependencies)


def get_prompt(name: str) -> Optional[str]:
    """Convenience function to get a prompt from the global registry."""
    return _global_registry.get_prompt(name)