"""
Base LLM Provider classes and interfaces.
Defines the contract that all LLM providers must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum
import json


class MessageRole(Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """Represents a message in a conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "role": self.role.value,
            "content": self.content
        }
        if self.name:
            result["name"] = self.name
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result
    
    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)
    
    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)
    
    @classmethod
    def assistant(cls, content: str) -> "LLMMessage":
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content)
    
    @classmethod
    def tool_result(cls, tool_call_id: str, content: str, name: str = None) -> "LLMMessage":
        """Create a tool result message."""
        return cls(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name
        )


@dataclass
class ToolCall:
    """Represents a tool call requested by the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments
        }


@dataclass
class ToolResult:
    """Result from executing a tool."""
    tool_call_id: str
    output: Any
    error: Optional[str] = None
    
    @property
    def is_error(self) -> bool:
        return self.error is not None
    
    def to_content(self) -> str:
        """Convert to content string for LLM."""
        if self.is_error:
            return json.dumps({"error": self.error})
        return json.dumps(self.output) if not isinstance(self.output, str) else self.output


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    stop_reason: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Any] = None
    
    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0
    
    @property
    def input_tokens(self) -> int:
        return self.usage.get("input_tokens", 0)
    
    @property
    def output_tokens(self) -> int:
        return self.usage.get("output_tokens", 0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "stop_reason": self.stop_reason,
            "usage": self.usage
        }


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120
    max_retries: int = 3
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Create config from dictionary."""
        return cls(
            api_key=data.get("api_key"),
            api_base=data.get("api_base"),
            model=data.get("model", ""),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
            timeout=data.get("timeout", 120),
            max_retries=data.get("max_retries", 3),
            extra=data.get("extra", {})
        )


@dataclass 
class ToolDefinition:
    """Definition of a tool that can be used by the LLM."""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All provider implementations must inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self._validate_config()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported model identifiers."""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the provider configuration."""
        pass
    
    @abstractmethod
    def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion for the given messages.
        
        Args:
            messages: List of conversation messages
            tools: Optional list of available tools
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse containing the completion
        """
        pass
    
    @abstractmethod
    def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream a completion for the given messages.
        
        Args:
            messages: List of conversation messages
            tools: Optional list of available tools
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Content chunks as they are generated
        """
        pass
    
    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        tool_executor: Optional[Callable[[ToolCall], ToolResult]] = None,
        max_tool_rounds: int = 10,
        **kwargs
    ) -> LLMResponse:
        """
        High-level chat interface with automatic tool execution.
        
        Args:
            user_message: The user's message
            system_prompt: Optional system prompt
            tools: Optional list of available tools
            tool_executor: Function to execute tool calls
            max_tool_rounds: Maximum rounds of tool use
            **kwargs: Additional parameters
            
        Returns:
            Final LLMResponse after tool execution
        """
        messages = []
        
        if system_prompt:
            messages.append(LLMMessage.system(system_prompt))
        
        messages.append(LLMMessage.user(user_message))
        
        for _ in range(max_tool_rounds):
            response = self.complete(messages, tools=tools, **kwargs)
            
            if not response.has_tool_calls or not tool_executor:
                return response
            
            # Add assistant response with tool calls
            messages.append(LLMMessage.assistant(response.content))
            
            # Execute tools and add results
            for tool_call in response.tool_calls:
                result = tool_executor(tool_call)
                messages.append(LLMMessage.tool_result(
                    tool_call_id=tool_call.id,
                    content=result.to_content(),
                    name=tool_call.name
                ))
        
        # Final completion after max rounds
        return self.complete(messages, tools=tools, **kwargs)
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Default implementation uses rough approximation.
        Override for accurate counting.
        """
        # Rough approximation: ~4 characters per token
        return len(text) // 4


class ProviderRegistry:
    """Registry for managing LLM providers."""
    
    _providers: Dict[str, Type[BaseLLMProvider]] = {}
    
    @classmethod
    def register(cls, provider_class: Type[BaseLLMProvider]) -> Type[BaseLLMProvider]:
        """
        Register a provider class. Can be used as a decorator.
        
        Args:
            provider_class: The provider class to register
            
        Returns:
            The same provider class (for decorator usage)
        """
        # Create temporary instance to get name
        temp_config = ProviderConfig(api_key="temp", model="temp")
        try:
            instance = provider_class(temp_config)
            cls._providers[instance.name] = provider_class
        except Exception:
            # If instantiation fails, use class name
            name = provider_class.__name__.lower().replace("provider", "")
            cls._providers[name] = provider_class
        return provider_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseLLMProvider]]:
        """Get a registered provider by name."""
        return cls._providers.get(name)
    
    @classmethod
    def get_instance(
        cls, 
        name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseLLMProvider]:
        """Get an instance of a registered provider."""
        provider_class = cls.get(name)
        if provider_class:
            provider_config = ProviderConfig.from_dict(config or {})
            return provider_class(provider_config)
        return None
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered provider names."""
        return list(cls._providers.keys())
