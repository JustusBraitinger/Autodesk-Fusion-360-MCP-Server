"""
Prompt management system for Fusion 360 MCP Server.

This module provides centralized prompt registration and management,
separating prompts from tools for better maintainability and organization.
"""

from .registry import PromptRegistry

__all__ = ['PromptRegistry']