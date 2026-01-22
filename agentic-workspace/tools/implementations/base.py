"""
Base tool infrastructure for the agentic workspace.
Provides abstract base classes and utilities for tool implementations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar, Generic
from enum import Enum
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Execution status for tool operations."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    """
    Standardized result container for tool executions.
    
    All tools return this structure to ensure consistent handling
    across the workflow engine.
    """
    status: ToolStatus
    data: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def is_success(self) -> bool:
        return self.status == ToolStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "error_type": self.error_type,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def success(cls, data: Any, metadata: Optional[Dict] = None, execution_time_ms: float = 0.0) -> "ToolResult":
        return cls(
            status=ToolStatus.SUCCESS,
            data=data,
            metadata=metadata or {},
            execution_time_ms=execution_time_ms
        )
    
    @classmethod
    def failure(cls, error: str, error_type: str = "ToolError", metadata: Optional[Dict] = None) -> "ToolResult":
        return cls(
            status=ToolStatus.FAILURE,
            error=error,
            error_type=error_type,
            metadata=metadata or {}
        )


@dataclass
class ToolParameter:
    """Definition of a single tool parameter."""
    name: str
    param_type: str
    description: str
    required: bool = True
    default: Any = None
    enum_values: Optional[List[str]] = None
    
    def validate(self, value: Any) -> bool:
        """Validate a value against this parameter definition."""
        if value is None:
            return not self.required
        
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
        }
        
        validator = type_validators.get(self.param_type, lambda v: True)
        if not validator(value):
            return False
        
        if self.enum_values and value not in self.enum_values:
            return False
        
        return True


class BaseTool(ABC):
    """
    Abstract base class for all tool implementations.
    
    Tools must implement:
    - name: Unique identifier for the tool
    - description: Human-readable description
    - parameters: List of ToolParameter definitions
    - execute: The actual tool logic
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier in snake_case."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """List of parameters this tool accepts."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    def validate_parameters(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Validate input parameters against definitions.
        
        Returns:
            Error message if validation fails, None if valid
        """
        param_map = {p.name: p for p in self.parameters}
        
        # Check for missing required parameters
        for param in self.parameters:
            if param.required and param.name not in params:
                return f"Missing required parameter: {param.name}"
        
        # Validate provided parameters
        for name, value in params.items():
            if name not in param_map:
                continue  # Allow extra parameters
            
            param = param_map[name]
            if not param.validate(value):
                return f"Invalid value for parameter '{name}': expected {param.param_type}"
        
        return None
    
    def run(self, **kwargs) -> ToolResult:
        """
        Validate parameters and execute the tool.
        
        This is the main entry point for tool execution.
        """
        import time
        start_time = time.time()
        
        validation_error = self.validate_parameters(kwargs)
        if validation_error:
            return ToolResult.failure(validation_error, "ValidationError")
        
        try:
            result = self.execute(**kwargs)
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            logger.exception(f"Tool {self.name} execution failed")
            return ToolResult.failure(str(e), type(e).__name__)
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for this tool."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.param_type,
                "description": param.description
            }
            if param.enum_values:
                prop["enum"] = param.enum_values
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class ToolRegistry:
    """
    Registry for managing available tools.
    
    Tools are registered by name and can be retrieved for execution.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult.failure(f"Unknown tool: {tool_name}", "ToolNotFoundError")
        return tool.run(**kwargs)


# Global registry instance
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


def register_tool(tool: BaseTool) -> BaseTool:
    """Register a tool with the global registry."""
    _global_registry.register(tool)
    return tool
