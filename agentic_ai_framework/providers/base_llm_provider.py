"""
providers/base_llm_provider.py - Base LLM Provider Interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Standard model information across providers"""
    name: str
    provider: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    max_tokens: Optional[int] = None
    cost_per_1k_tokens: Optional[float] = None
    supports_streaming: bool = True
    supports_tools: bool = False
    model_type: str = "text"  # text, chat, embedding, etc.

@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    top_k: Optional[int] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    stream: bool = False

@dataclass
class Message:
    """Standard message format"""
    role: str  # user, assistant, system, tool
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class GenerationResponse:
    """Standard response format"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """
        Initialize the provider
        
        Args:
            provider_name: Name of the provider (e.g., "ollama", "openai")
            config: Provider-specific configuration
        """
        self.provider_name = provider_name
        self.config = config
        self.is_initialized = False
        logger.info(f"Initializing {provider_name} provider")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider (connect, authenticate, etc.)
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is accessible and healthy
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """
        List available models from this provider
        
        Returns:
            List of ModelInfo objects
        """
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate a response using the specified model
        
        Args:
            messages: List of messages in the conversation
            model: Model name to use
            config: Generation configuration
            
        Returns:
            GenerationResponse object
        """
        pass
    
    @abstractmethod
    async def generate_response_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response
        
        Args:
            messages: List of messages in the conversation
            model: Model name to use
            config: Generation configuration
            
        Yields:
            Response chunks as they arrive
        """
        pass
    
    async def validate_model(self, model: str) -> bool:
        """
        Validate that a model exists and is accessible
        
        Args:
            model: Model name to validate
            
        Returns:
            True if model is valid, False otherwise
        """
        try:
            models = await self.list_models()
            return any(m.name == model for m in models)
        except Exception as e:
            logger.error(f"Error validating model {model}: {e}")
            return False
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model (sync version for cached data)
        
        Args:
            model: Model name
            
        Returns:
            ModelInfo object or None if not found
        """
        # This is a default implementation that can be overridden
        return ModelInfo(
            name=model,
            provider=self.provider_name,
            description=f"Model {model} from {self.provider_name}"
        )
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if provider supports a specific feature
        
        Args:
            feature: Feature name (e.g., "streaming", "tools", "embeddings")
            
        Returns:
            True if supported, False otherwise
        """
        supported_features = self.config.get("supported_features", [])
        return feature in supported_features
    
    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update provider configuration"""
        self.config.update(new_config)
    
    def __str__(self) -> str:
        return f"{self.provider_name}Provider"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider_name='{self.provider_name}')"

class LLMProviderError(Exception):
    """Base exception for LLM provider errors"""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}")

class ModelNotFoundError(LLMProviderError):
    """Raised when a model is not found"""
    pass

class AuthenticationError(LLMProviderError):
    """Raised when authentication fails"""
    pass

class RateLimitError(LLMProviderError):
    """Raised when rate limit is exceeded"""
    pass

class InvalidConfigError(LLMProviderError):
    """Raised when provider configuration is invalid"""
    pass