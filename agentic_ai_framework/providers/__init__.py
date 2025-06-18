"""
providers/__init__.py - LLM Provider Package

This package contains all LLM provider implementations for the Open Agentic Framework.
"""

from .base_llm_provider import (
    BaseLLMProvider,
    ModelInfo,
    GenerationConfig,
    Message,
    GenerationResponse,
    LLMProviderError,
    ModelNotFoundError,
    AuthenticationError,
    RateLimitError,
    InvalidConfigError
)

from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider

__all__ = [
    # Base classes and types
    "BaseLLMProvider",
    "ModelInfo",
    "GenerationConfig", 
    "Message",
    "GenerationResponse",
    
    # Exceptions
    "LLMProviderError",
    "ModelNotFoundError", 
    "AuthenticationError",
    "RateLimitError",
    "InvalidConfigError",
    
    # Provider implementations
    "OllamaProvider",
    "OpenAIProvider", 
    "OpenRouterProvider"
]

# Version info
__version__ = "1.2.0"

# Available providers registry
AVAILABLE_PROVIDERS = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider
}

def get_provider_class(provider_name: str):
    """Get provider class by name"""
    return AVAILABLE_PROVIDERS.get(provider_name)

def list_available_providers():
    """List all available provider names"""
    return list(AVAILABLE_PROVIDERS.keys())