"""
Tool and prompt registration system.

This module provides centralized registration and management of tools and prompts,
including dependency validation and category-based organization.
"""

from typing import List, Dict, Optional, Callable, Any
import logging
import inspect
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about a registered tool."""
    name: str
    function: Callable
    category: str
    dependencies: List[str]
    description: str
    parameters: Dict[str, Any]


@dataclass
class PromptInfo:
    """Information about a registered prompt."""
    name: str
    function: Callable
    category: str
    description: str
    parameters: Dict[str, Any]


class ToolRegistry:
    """Central registry for tools and prompts."""
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._prompts: Dict[str, PromptInfo] = {}
        self._categories: Dict[str, List[str]] = {
            "cad": [],
            "cam": [],
            "utility": [],
            "debug": []
        }
        
    def register_tool(self, tool_func: Callable, category: str, dependencies: Optional[List[str]] = None) -> None:
        """
        Register a tool function.
        
        Args:
            tool_func: The tool function to register
            category: Tool category (cad, cam, utility, debug)
            dependencies: Optional list of dependency names
        """
        if dependencies is None:
            dependencies = []
            
        # Extract function information
        name = tool_func.__name__
        description = tool_func.__doc__ or f"Tool: {name}"
        
        # Get function signature for parameters
        sig = inspect.signature(tool_func)
        parameters = {}
        for param_name, param in sig.parameters.items():
            parameters[param_name] = {
                "type": param.annotation if param.annotation != inspect.Parameter.empty else "Any",
                "default": param.default if param.default != inspect.Parameter.empty else None
            }
        
        tool_info = ToolInfo(
            name=name,
            function=tool_func,
            category=category.lower(),
            dependencies=dependencies,
            description=description,
            parameters=parameters
        )
        
        self._tools[name] = tool_info
        
        # Add to category tracking
        if category.lower() not in self._categories:
            self._categories[category.lower()] = []
        if name not in self._categories[category.lower()]:
            self._categories[category.lower()].append(name)
            
        logger.info(f"Registered tool '{name}' in category '{category}'")
        
    def register_prompt(self, prompt_func: Callable, category: str) -> None:
        """
        Register a prompt function.
        
        Args:
            prompt_func: The prompt function to register
            category: Prompt category
        """
        # Extract function information
        name = prompt_func.__name__
        description = prompt_func.__doc__ or f"Prompt: {name}"
        
        # Get function signature for parameters
        sig = inspect.signature(prompt_func)
        parameters = {}
        for param_name, param in sig.parameters.items():
            parameters[param_name] = {
                "type": param.annotation if param.annotation != inspect.Parameter.empty else "Any",
                "default": param.default if param.default != inspect.Parameter.empty else None
            }
        
        prompt_info = PromptInfo(
            name=name,
            function=prompt_func,
            category=category.lower(),
            description=description,
            parameters=parameters
        )
        
        self._prompts[name] = prompt_info
        logger.info(f"Registered prompt '{name}' in category '{category}'")
        
    def get_tools(self, category: Optional[str] = None) -> List[ToolInfo]:
        """
        Get registered tools, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            list: List of registered tools
        """
        if category is None:
            return list(self._tools.values())
        
        category_lower = category.lower()
        if category_lower in self._categories:
            return [self._tools[name] for name in self._categories[category_lower] if name in self._tools]
        else:
            logger.warning(f"Unknown category: {category}")
            return []
        
    def get_prompts(self, category: Optional[str] = None) -> List[PromptInfo]:
        """
        Get registered prompts, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            list: List of registered prompts
        """
        if category is None:
            return list(self._prompts.values())
        
        return [prompt for prompt in self._prompts.values() if prompt.category == category.lower()]
        
    def get_tool_by_name(self, name: str) -> Optional[ToolInfo]:
        """
        Get a specific tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolInfo or None: Tool information if found
        """
        return self._tools.get(name)
        
    def get_prompt_by_name(self, name: str) -> Optional[PromptInfo]:
        """
        Get a specific prompt by name.
        
        Args:
            name: Prompt name
            
        Returns:
            PromptInfo or None: Prompt information if found
        """
        return self._prompts.get(name)
        
    def validate_dependencies(self) -> bool:
        """
        Validate all tool dependencies.
        
        Returns:
            bool: True if all dependencies are satisfied
        """
        logger.info("Validating tool dependencies")
        
        all_valid = True
        for tool_name, tool_info in self._tools.items():
            for dependency in tool_info.dependencies:
                if dependency not in self._tools:
                    logger.error(f"Tool '{tool_name}' has unmet dependency: '{dependency}'")
                    all_valid = False
                    
        if all_valid:
            logger.info("All tool dependencies are satisfied")
        else:
            logger.error("Some tool dependencies are not satisfied")
            
        return all_valid
        
    def get_categories(self) -> List[str]:
        """
        Get list of available categories.
        
        Returns:
            list: List of category names
        """
        return list(self._categories.keys())
        
    def get_tool_count(self, category: Optional[str] = None) -> int:
        """
        Get count of registered tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            int: Number of tools
        """
        if category is None:
            return len(self._tools)
        
        category_lower = category.lower()
        if category_lower in self._categories:
            return len(self._categories[category_lower])
        else:
            return 0
            
    def get_prompt_count(self, category: Optional[str] = None) -> int:
        """
        Get count of registered prompts.
        
        Args:
            category: Optional category filter
            
        Returns:
            int: Number of prompts
        """
        if category is None:
            return len(self._prompts)
        
        return len([p for p in self._prompts.values() if p.category == category.lower()])


# Global registry instance
_registry = ToolRegistry()


def register_tool(tool_func: Callable, category: str, dependencies: Optional[List[str]] = None) -> None:
    """Register a tool function."""
    _registry.register_tool(tool_func, category, dependencies)


def register_prompt(prompt_func: Callable, category: str) -> None:
    """Register a prompt function."""
    _registry.register_prompt(prompt_func, category)


def get_tools(category: Optional[str] = None) -> List[ToolInfo]:
    """Get registered tools."""
    return _registry.get_tools(category)


def get_prompts(category: Optional[str] = None) -> List[PromptInfo]:
    """Get registered prompts."""
    return _registry.get_prompts(category)


def get_tool_by_name(name: str) -> Optional[ToolInfo]:
    """Get a specific tool by name."""
    return _registry.get_tool_by_name(name)


def get_prompt_by_name(name: str) -> Optional[PromptInfo]:
    """Get a specific prompt by name."""
    return _registry.get_prompt_by_name(name)


def validate_dependencies() -> bool:
    """Validate all tool dependencies."""
    return _registry.validate_dependencies()


def get_categories() -> List[str]:
    """Get list of available categories."""
    return _registry.get_categories()


def get_tool_count(category: Optional[str] = None) -> int:
    """Get count of registered tools."""
    return _registry.get_tool_count(category)


def get_prompt_count(category: Optional[str] = None) -> int:
    """Get count of registered prompts."""
    return _registry.get_prompt_count(category)