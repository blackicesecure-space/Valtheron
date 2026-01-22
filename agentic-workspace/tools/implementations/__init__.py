"""
Tool implementations for the agentic workspace.

This package provides all tool implementations that agents can use.
Tools are automatically registered with the global registry on import.
"""
from .base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolStatus,
    ToolRegistry,
    get_registry,
    register_tool,
)

# Import tool modules to trigger registration
from . import file_tools
from . import code_analyzer
from . import bash_tools

__all__ = [
    "BaseTool",
    "ToolParameter", 
    "ToolResult",
    "ToolStatus",
    "ToolRegistry",
    "get_registry",
    "register_tool",
]


def list_available_tools():
    """List all registered tools."""
    return get_registry().list_tools()


def get_tool(name: str):
    """Get a tool by name."""
    return get_registry().get(name)


def execute_tool(name: str, **kwargs) -> ToolResult:
    """Execute a tool by name with given parameters."""
    return get_registry().execute(name, **kwargs)
