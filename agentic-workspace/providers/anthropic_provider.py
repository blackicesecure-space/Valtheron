"""
Anthropic Provider Implementation.
Connects the agentic workspace to Claude models via the Anthropic API.
"""
import os
import json
import time
from typing import Any, Dict, List, Optional, Iterator
from dataclasses import dataclass

from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMMessage,
    ToolCall,
    ToolDefinition,
    ProviderConfig,
    ProviderRegistry,
    MessageRole
)


class AnthropicAPIError(Exception):
    """Exception for Anthropic API errors."""
    
    def __init__(self, message: str, status_code: int = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic API provider for Claude models.
    
    Supports all Claude 4.5 models with full tool use capabilities.
    """
    
    SUPPORTED_MODELS = [
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-5-20250929", 
        "claude-haiku-4-5-20251001",
        # Aliases
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
    ]
    
    MODEL_ALIASES = {
        "claude-opus-4-5": "claude-opus-4-5-20251101",
        "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5": "claude-haiku-4-5-20251001",
        "opus": "claude-opus-4-5-20251101",
        "sonnet": "claude-sonnet-4-5-20250929",
        "haiku": "claude-haiku-4-5-20251001",
    }
    
    DEFAULT_API_BASE = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"
    
    def __init__(self, config: ProviderConfig):
        """Initialize the Anthropic provider."""
        self._client = None
        super().__init__(config)
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    @property
    def supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS
    
    def _validate_config(self) -> None:
        """Validate Anthropic-specific configuration."""
        # Get API key from config or environment
        if not self.config.api_key:
            self.config.api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not self.config.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key in config."
            )
        
        # Set default model if not specified
        if not self.config.model:
            self.config.model = "claude-sonnet-4-5-20250929"
        
        # Resolve model alias
        self.config.model = self.MODEL_ALIASES.get(
            self.config.model, 
            self.config.model
        )
        
        # Set API base
        if not self.config.api_base:
            self.config.api_base = self.DEFAULT_API_BASE
    
    def _get_client(self):
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.config.api_key,
                    base_url=self.config.api_base,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries
                )
            except ImportError:
                raise ImportError(
                    "The 'anthropic' package is required. "
                    "Install it with: pip install anthropic"
                )
        return self._client
    
    def _convert_messages(self, messages: List[LLMMessage]) -> tuple[Optional[str], List[Dict]]:
        """
        Convert LLMMessage list to Anthropic format.
        
        Returns:
            Tuple of (system_prompt, messages_list)
        """
        system_prompt = None
        converted = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            elif msg.role == MessageRole.USER:
                converted.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == MessageRole.ASSISTANT:
                converted.append({
                    "role": "assistant",
                    "content": msg.content
                })
            elif msg.role == MessageRole.TOOL:
                # Tool results in Anthropic format
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content
                    }]
                })
        
        return system_prompt, converted
    
    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict]:
        """Convert tool definitions to Anthropic format."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            }
            for tool in tools
        ]
    
    def _parse_response(self, response) -> LLMResponse:
        """Parse Anthropic API response into LLMResponse."""
        content_parts = []
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))
        
        return LLMResponse(
            content="\n".join(content_parts),
            model=response.model,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            raw_response=response
        )
    
    def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion using Claude.
        
        Args:
            messages: Conversation messages
            tools: Optional tools for function calling
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with completion
        """
        client = self._get_client()
        
        # Convert messages
        system_prompt, converted_messages = self._convert_messages(messages)
        
        # Build request parameters
        params = {
            "model": kwargs.get("model", self.config.model),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": converted_messages,
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        elif self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        
        # Add tools if provided
        if tools:
            params["tools"] = self._convert_tools(tools)
        
        # Make API call with retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = client.messages.create(**params)
                return self._parse_response(response)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                continue
        
        raise AnthropicAPIError(
            f"API call failed after {self.config.max_retries} attempts: {last_error}",
            response=last_error
        )
    
    def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream a completion from Claude.
        
        Args:
            messages: Conversation messages
            tools: Optional tools (note: tool use with streaming has limitations)
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they are generated
        """
        client = self._get_client()
        
        # Convert messages
        system_prompt, converted_messages = self._convert_messages(messages)
        
        # Build request parameters
        params = {
            "model": kwargs.get("model", self.config.model),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": converted_messages,
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        elif self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        
        if tools:
            params["tools"] = self._convert_tools(tools)
        
        # Stream response
        with client.messages.stream(**params) as stream:
            for text in stream.text_stream:
                yield text
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Anthropic's tokenizer.
        Falls back to estimation if tokenizer unavailable.
        """
        try:
            client = self._get_client()
            # Use the count_tokens endpoint if available
            response = client.count_tokens(text)
            return response.tokens
        except Exception:
            # Fallback to estimation (~4 chars per token for Claude)
            return len(text) // 4
    
    def create_tool_definition(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> ToolDefinition:
        """
        Helper to create a tool definition.
        
        Args:
            name: Tool name
            description: What the tool does
            parameters: JSON schema for parameters
            
        Returns:
            ToolDefinition ready for use
        """
        return ToolDefinition(
            name=name,
            description=description,
            parameters=parameters
        )


# Register the provider
ProviderRegistry.register(AnthropicProvider)


# Convenience function for quick usage
def create_claude_client(
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-5-20250929",
    **kwargs
) -> AnthropicProvider:
    """
    Create a configured Claude client.
    
    Args:
        api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        model: Model to use (default: claude-sonnet-4-5)
        **kwargs: Additional configuration options
        
    Returns:
        Configured AnthropicProvider instance
        
    Example:
        client = create_claude_client()
        response = client.chat("Hello, Claude!")
        print(response.content)
    """
    config = ProviderConfig(
        api_key=api_key,
        model=model,
        max_tokens=kwargs.get("max_tokens", 4096),
        temperature=kwargs.get("temperature", 0.7),
        timeout=kwargs.get("timeout", 120),
        max_retries=kwargs.get("max_retries", 3)
    )
    return AnthropicProvider(config)
