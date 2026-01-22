"""
Agentic Workspace Tools Package.
Provides tool implementations for agent operations.
"""
from .base_tool import (
    BaseTool,
    ToolResult,
    ToolStatus,
    ToolParameter,
    ToolRegistry,
    tool,
    with_timeout,
    with_retry
)

from .code_analyzer import CodeAnalyzerTool
from .test_runner import TestRunnerTool
from .file_operations import (
    FileReadTool,
    FileWriteTool,
    FileSearchTool,
    GrepTool,
    FileEditTool
)

__all__ = [
    # Base classes
    "BaseTool",
    "ToolResult",
    "ToolStatus",
    "ToolParameter",
    "ToolRegistry",
    
    # Decorators
    "tool",
    "with_timeout",
    "with_retry",
    
    # Tool implementations
    "CodeAnalyzerTool",
    "TestRunnerTool",
    "FileReadTool",
    "FileWriteTool",
    "FileSearchTool",
    "GrepTool",
    "FileEditTool",
]


def get_tool(name: str, config: dict = None):
    """
    Get a tool instance by name.
    
    Args:
        name: Tool name
        config: Optional tool configuration
        
    Returns:
        Tool instance or None if not found
    """
    return ToolRegistry.get_instance(name, config)


def list_tools() -> list[str]:
    """List all available tool names."""
    return ToolRegistry.list_tools()


def get_all_tool_schemas() -> list[dict]:
    """Get JSON schemas for all registered tools."""
    return ToolRegistry.get_all_schemas()
