"""
LLM Provider Package for the Agentic Workspace.
Provides interfaces and implementations for connecting to various LLM providers.
"""
from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMMessage,
    ToolCall,
    ToolResult,
    ProviderConfig,
    ProviderRegistry
)
from .anthropic_provider import AnthropicProvider

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "LLMMessage",
    "ToolCall",
    "ToolResult",
    "ProviderConfig",
    "ProviderRegistry",
    "AnthropicProvider",
]


def get_provider(name: str, config: dict = None) -> BaseLLMProvider:
    """
    Get a provider instance by name.
    
    Args:
        name: Provider name ('anthropic', 'openai', etc.)
        config: Optional provider configuration
        
    Returns:
        Configured provider instance
    """
    return ProviderRegistry.get_instance(name, config)
