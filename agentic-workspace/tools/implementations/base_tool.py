"""
Base tool system for the agentic workspace.
Provides abstract classes and utilities for implementing custom tools.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import functools
from pathlib import Path


class ToolStatus(Enum):
    """Execution status for tool operations."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID_INPUT = "invalid_input"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class ToolResult:
    """Result container for tool execution."""
    status: ToolStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata
        }

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ToolStatus.SUCCESS


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    param_type: str
    description: str
    required: bool = True
    default: Any = None
    enum_values: Optional[list] = None

    def validate(self, value: Any) -> bool:
        """Validate a value against this parameter definition."""
        if value is None:
            return not self.required

        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected_type = type_map.get(self.param_type)
        if expected_type and not isinstance(value, expected_type):
            return False

        if self.enum_values and value not in self.enum_values:
            return False

        return True


class BaseTool(ABC):
    """
    Abstract base class for all tools in the agentic workspace.
    
    Tools must implement the `execute` method and define their
    parameters via the `get_parameters` class method.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tool with optional configuration.
        
        Args:
            config: Tool-specific configuration dictionary
        """
        self.config = config or {}
        self._validate_config()

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does."""
        pass

    @classmethod
    @abstractmethod
    def get_parameters(cls) -> list[ToolParameter]:
        """Return the list of parameters this tool accepts."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Tool parameters as keyword arguments
            
        Returns:
            ToolResult containing execution status and data
        """
        pass

    def _validate_config(self) -> None:
        """Validate tool configuration. Override for custom validation."""
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters against the tool's parameter definitions.
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        for param_def in self.get_parameters():
            value = params.get(param_def.name, param_def.default)

            if param_def.required and value is None:
                return False, f"Missing required parameter: {param_def.name}"

            if not param_def.validate(value):
                return False, f"Invalid value for parameter {param_def.name}: {value}"

        return True, None

    def __call__(self, **kwargs) -> ToolResult:
        """Allow calling the tool directly as a function."""
        is_valid, error = self.validate_params(kwargs)
        if not is_valid:
            return ToolResult(
                status=ToolStatus.INVALID_INPUT,
                error=error
            )

        start_time = time.time()
        try:
            result = self.execute(**kwargs)
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

    def to_schema(self) -> Dict[str, Any]:
        """Generate JSON schema representation of this tool."""
        properties = {}
        required = []

        for param in self.get_parameters():
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
    """Registry for managing and accessing tools."""

    _instance = None
    _tools: Dict[str, Type[BaseTool]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, tool_class: Type[BaseTool]) -> Type[BaseTool]:
        """
        Register a tool class. Can be used as a decorator.
        
        Args:
            tool_class: The tool class to register
            
        Returns:
            The same tool class (for decorator usage)
        """
        instance = tool_class()
        cls._tools[instance.name] = tool_class
        return tool_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseTool]]:
        """Get a registered tool by name."""
        return cls._tools.get(name)

    @classmethod
    def get_instance(cls, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """Get an instance of a registered tool."""
        tool_class = cls.get(name)
        if tool_class:
            return tool_class(config)
        return None

    @classmethod
    def list_tools(cls) -> list[str]:
        """List all registered tool names."""
        return list(cls._tools.keys())

    @classmethod
    def get_all_schemas(cls) -> list[Dict[str, Any]]:
        """Get JSON schemas for all registered tools."""
        schemas = []
        for tool_class in cls._tools.values():
            instance = tool_class()
            schemas.append(instance.to_schema())
        return schemas


def tool(name: str = None, description: str = None):
    """
    Decorator to create a tool from a function.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
    """
    def decorator(func: Callable) -> Type[BaseTool]:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or "No description"

        # Extract parameters from function signature
        import inspect
        sig = inspect.signature(func)
        params = []

        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue

            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                type_map = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object"
                }
                param_type = type_map.get(param.annotation, "string")

            required = param.default == inspect.Parameter.empty
            default = None if required else param.default

            params.append(ToolParameter(
                name=param_name,
                param_type=param_type,
                description=f"Parameter: {param_name}",
                required=required,
                default=default
            ))

        class FunctionTool(BaseTool):
            @property
            def name(self) -> str:
                return tool_name

            @property
            def description(self) -> str:
                return tool_description

            @classmethod
            def get_parameters(cls) -> list[ToolParameter]:
                return params

            def execute(self, **kwargs) -> ToolResult:
                try:
                    result = func(**kwargs)
                    return ToolResult(status=ToolStatus.SUCCESS, data=result)
                except Exception as e:
                    return ToolResult(status=ToolStatus.ERROR, error=str(e))

        FunctionTool.__name__ = f"{tool_name}Tool"
        ToolRegistry.register(FunctionTool)
        return FunctionTool

    return decorator


def with_timeout(seconds: float):
    """Decorator to add timeout to tool execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            result = [ToolResult(status=ToolStatus.TIMEOUT, error=f"Execution timed out after {seconds}s")]

            def target():
                result[0] = func(*args, **kwargs)

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                return ToolResult(
                    status=ToolStatus.TIMEOUT,
                    error=f"Execution timed out after {seconds}s"
                )
            return result[0]

        return wrapper
    return decorator


def with_retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """Decorator to add retry logic to tool execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                result = func(*args, **kwargs)
                if result.is_success:
                    return result
                last_error = result.error
                if attempt < max_attempts - 1:
                    time.sleep(backoff_factor ** attempt)

            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Failed after {max_attempts} attempts. Last error: {last_error}"
            )

        return wrapper
    return decorator
