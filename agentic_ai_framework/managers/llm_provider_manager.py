"""
managers/llm_provider_manager.py - LLM Provider Management System
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

from providers.base_llm_provider import (
    BaseLLMProvider, ModelInfo, GenerationConfig, Message, GenerationResponse,
    LLMProviderError, ModelNotFoundError
)
from providers.ollama_provider import OllamaProvider
from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider

logger = logging.getLogger(__name__)

@dataclass
class ProviderStatus:
    """Status information for a provider"""
    name: str
    is_healthy: bool
    is_initialized: bool
    last_check: datetime
    error_message: Optional[str] = None
    model_count: int = 0

class LLMProviderManager:
    """Manages multiple LLM providers with routing and fallback capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider manager
        
        Args:
            config: Configuration dictionary with provider settings
        """
        self.config = config
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.provider_models: Dict[str, List[ModelInfo]] = {}
        self.model_to_provider: Dict[str, str] = {}
        self.default_provider = config.get("default_provider", "ollama")
        self.fallback_enabled = config.get("fallback_enabled", True)
        self.fallback_order = config.get("fallback_order", ["ollama", "openai"])
        
        logger.info("Initializing LLM Provider Manager")
    
    async def initialize(self) -> bool:
        """Initialize all configured providers"""
        success_count = 0
        
        # Initialize providers based on configuration
        provider_configs = self.config.get("providers", {})
        
        for provider_name, provider_config in provider_configs.items():
            if not provider_config.get("enabled", True):
                logger.info(f"Provider {provider_name} is disabled")
                continue
            
            try:
                provider = self._create_provider(provider_name, provider_config)
                if provider:
                    self.providers[provider_name] = provider
                    
                    # Initialize the provider
                    if await provider.initialize():
                        success_count += 1
                        logger.info(f"Successfully initialized {provider_name} provider")
                        
                        # Load models for this provider
                        await self._load_provider_models(provider_name)
                    else:
                        logger.warning(f"Failed to initialize {provider_name} provider")
                        
            except Exception as e:
                logger.error(f"Error setting up {provider_name} provider: {e}")
        
        if success_count == 0:
            logger.error("No providers were successfully initialized")
            return False
        
        logger.info(f"Initialized {success_count}/{len(provider_configs)} providers")
        return True
    
    def _create_provider(self, provider_name: str, config: Dict[str, Any]) -> Optional[BaseLLMProvider]:
        """Create a provider instance based on its name and configuration"""
        if provider_name == "ollama":
            return OllamaProvider(config)
        elif provider_name == "openai":
            return OpenAIProvider(config)
        elif provider_name == "openrouter":
            return OpenRouterProvider(config)
        else:
            logger.error(f"Unknown provider type: {provider_name}")
            return None
    
    async def _load_provider_models(self, provider_name: str):
        """Load and cache models for a specific provider"""
        try:
            provider = self.providers[provider_name]
            models = await provider.list_models()
            
            self.provider_models[provider_name] = models
            
            # Update model-to-provider mapping
            for model in models:
                # Use provider:model format for unique identification
                model_key = f"{provider_name}:{model.name}"
                self.model_to_provider[model_key] = provider_name
                
                # Also map just the model name if it's not already taken
                if model.name not in self.model_to_provider:
                    self.model_to_provider[model.name] = provider_name
            
            logger.info(f"Loaded {len(models)} models for {provider_name}")
            
        except Exception as e:
            logger.error(f"Error loading models for {provider_name}: {e}")
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[GenerationResponse, str]:
        """
        Generate a response using the appropriate provider
        
        This method maintains backward compatibility with the original OllamaClient interface
        while adding multi-provider support.
        
        Args:
            prompt: The input prompt
            model: Model to use (can include provider prefix like "openai:gpt-4")
            chat_history: Previous conversation context
            stream: Whether to stream the response
            **kwargs: Additional generation parameters
            
        Returns:
            GenerationResponse object or string (for backward compatibility)
        """
        # Convert to new message format
        messages = []
        
        # Add chat history
        if chat_history:
            for msg in chat_history:
                messages.append(Message(
                    role=msg["role"],
                    content=msg["content"]
                ))
        
        # Add current prompt
        messages.append(Message(role="user", content=prompt))
        
        # Determine provider and model
        provider_name, model_name = self._resolve_model(model)
        
        # Create generation config from kwargs
        config = GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
            stream=stream,
            **{k: v for k, v in kwargs.items() if k in [
                "top_p", "top_k", "frequency_penalty", "presence_penalty", "stop_sequences"
            ]}
        )
        
        # Try to generate with the primary provider
        try:
            provider = self.providers[provider_name]
            
            if stream:
                # Return the async generator directly for streaming
                return provider.generate_response_stream(messages, model_name, config)
            else:
                response = await provider.generate_response(messages, model_name, config)
                # Return just the content for backward compatibility
                return response.content
                
        except Exception as e:
            logger.warning(f"Error with {provider_name} provider: {e}")
            
            # Try fallback if enabled
            if self.fallback_enabled:
                return await self._try_fallback(messages, model_name, config, stream, provider_name)
            else:
                raise
    
    async def _try_fallback(
        self,
        messages: List[Message],
        original_model: str,
        config: GenerationConfig,
        stream: bool,
        failed_provider: str
    ) -> Union[GenerationResponse, str]:
        """Try fallback providers in order"""
        for fallback_provider_name in self.fallback_order:
            if fallback_provider_name == failed_provider:
                continue  # Skip the provider that already failed
            
            if fallback_provider_name not in self.providers:
                continue
            
            try:
                logger.info(f"Trying fallback provider: {fallback_provider_name}")
                provider = self.providers[fallback_provider_name]
                
                # Try to find a similar model in the fallback provider
                fallback_model = self._find_similar_model(original_model, fallback_provider_name)
                
                if stream:
                    return provider.generate_response_stream(messages, fallback_model, config)
                else:
                    response = await provider.generate_response(messages, fallback_model, config)
                    return response.content
                    
            except Exception as e:
                logger.warning(f"Fallback provider {fallback_provider_name} also failed: {e}")
                continue
        
        raise LLMProviderError("All providers failed", provider="all")
    
    def _resolve_model(self, model: Optional[str]) -> tuple[str, str]:
        """
        Resolve model string to provider and model name
        
        Args:
            model: Model specification (e.g., "gpt-4", "openai:gpt-4", "ollama:llama3")
            
        Returns:
            Tuple of (provider_name, model_name)
        """
        if not model:
            # Use default provider and its default model
            default_provider = self.providers[self.default_provider]
            return self.default_provider, default_provider.default_model
        
        # Check if model includes provider prefix
        if ":" in model:
            provider_name, model_name = model.split(":", 1)
            if provider_name in self.providers:
                return provider_name, model_name
            else:
                logger.warning(f"Provider {provider_name} not found, using default")
        
        # Try to find the model in our mapping
        if model in self.model_to_provider:
            provider_name = self.model_to_provider[model]
            return provider_name, model
        
        # Fallback to default provider
        logger.warning(f"Model {model} not found in any provider, using default provider")
        return self.default_provider, model
    
    def _find_similar_model(self, original_model: str, provider_name: str) -> str:
        """Find a similar model in the given provider"""
        if provider_name not in self.provider_models:
            # Return provider's default model
            return self.providers[provider_name].default_model
        
        models = self.provider_models[provider_name]
        
        # Try exact match first
        for model in models:
            if model.name == original_model:
                return model.name
        
        # Try partial matches for common model families
        original_lower = original_model.lower()
        
        # GPT model mappings
        if "gpt-4" in original_lower:
            for model in models:
                if "gpt-4" in model.name.lower():
                    return model.name
        elif "gpt-3.5" in original_lower or "gpt3.5" in original_lower:
            for model in models:
                if "gpt-3.5" in model.name.lower():
                    return model.name
        
        # Llama model mappings
        elif "llama" in original_lower:
            for model in models:
                if "llama" in model.name.lower():
                    return model.name
        
        # Return the first available model as ultimate fallback
        if models:
            return models[0].name
        
        # Return provider's default model
        return self.providers[provider_name].default_model
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        health_status = {}
        
        for provider_name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                health_status[provider_name] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
                health_status[provider_name] = False
        
        return health_status
    
    async def list_models(self, provider: Optional[str] = None) -> List[ModelInfo]:
        """List models from all providers or a specific provider"""
        if provider:
            if provider in self.provider_models:
                return self.provider_models[provider]
            else:
                return []
        
        # Return models from all providers
        all_models = []
        for provider_name, models in self.provider_models.items():
            all_models.extend(models)
        
        return all_models
    
    def get_provider_status(self) -> Dict[str, ProviderStatus]:
        """Get status of all providers"""
        status = {}
        
        for provider_name, provider in self.providers.items():
            model_count = len(self.provider_models.get(provider_name, []))
            
            status[provider_name] = ProviderStatus(
                name=provider_name,
                is_healthy=True,  # This would be updated by periodic health checks
                is_initialized=provider.is_initialized,
                last_check=datetime.now(),
                model_count=model_count
            )
        
        return status
    
    def get_provider(self, provider_name: str) -> Optional[BaseLLMProvider]:
        """Get a specific provider instance"""
        return self.providers.get(provider_name)
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Get information about a specific model"""
        provider_name, model_name = self._resolve_model(model)
        
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            return provider.get_model_info(model_name)
        
        return None
    
    async def reload_models(self):
        """Reload models from all providers"""
        logger.info("Reloading models from all providers")
        
        for provider_name in self.providers.keys():
            await self._load_provider_models(provider_name)
        
        logger.info("Model reload completed")
    
    def supports_streaming(self, model: Optional[str] = None) -> bool:
        """Check if the given model/provider supports streaming"""
        provider_name, _ = self._resolve_model(model)
        
        if provider_name in self.providers:
            return self.providers[provider_name].supports_feature("streaming")
        
        return False
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())
    
    def set_default_provider(self, provider_name: str):
        """Set the default provider"""
        if provider_name in self.providers:
            self.default_provider = provider_name
            logger.info(f"Default provider set to: {provider_name}")
        else:
            raise ValueError(f"Provider {provider_name} not found")