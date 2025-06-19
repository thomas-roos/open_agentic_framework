"""
providers/openrouter_provider.py - OpenRouter LLM Provider
"""

import aiohttp
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from .base_llm_provider import (
    BaseLLMProvider, ModelInfo, GenerationConfig, Message, GenerationResponse,
    LLMProviderError, ModelNotFoundError, AuthenticationError, RateLimitError
)

logger = logging.getLogger(__name__)

class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter LLM provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenRouter provider
        
        Args:
            config: Configuration dictionary with keys:
                - api_key: OpenRouter API key
                - base_url: API base URL (optional, defaults to OpenRouter)
                - timeout: Request timeout (optional)
                - default_model: Default model name (optional)
                - app_name: Application name for OpenRouter (optional)
                - site_url: Site URL for OpenRouter (optional)
        """
        super().__init__("openrouter", config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1").rstrip('/')
        self.timeout = config.get("timeout", 300)
        self.default_model = config.get("default_model", "openai/gpt-3.5-turbo")
        self.app_name = config.get("app_name", "Open Agentic Framework")
        self.site_url = config.get("site_url", "https://github.com/your-repo")
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        # OpenRouter-specific features
        self.config["supported_features"] = [
            "streaming", "chat", "tools", "multiple_providers"
        ]
        
        # Cache for model information
        self.cached_models = {}
        self.models_cache_time = None
    
    async def initialize(self) -> bool:
        """Initialize and test connection to OpenRouter"""
        try:
            is_healthy = await self.health_check()
            if is_healthy:
                self.is_initialized = True
                logger.info("OpenRouter provider initialized successfully")
                return True
            else:
                logger.error("OpenRouter health check failed during initialization")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter provider: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if OpenRouter API is accessible"""
        try:
            headers = self._build_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    is_healthy = response.status == 200
                    if not is_healthy:
                        error_text = await response.text()
                        logger.warning(f"OpenRouter health check failed: {response.status} - {error_text}")
                    else:
                        logger.debug("OpenRouter health check: OK")
                    return is_healthy
        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {e}")
            return False
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenRouter"""
        try:
            # Use cached models if available and recent (5 minutes)
            import time
            current_time = time.time()
            if (self.cached_models and self.models_cache_time and 
                current_time - self.models_cache_time < 300):
                return list(self.cached_models.values())
            
            headers = self._build_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        models = []
                        
                        for model_data in result.get("data", []):
                            model_id = model_data["id"]
                            
                            # Extract model information from OpenRouter response
                            model_info = ModelInfo(
                                name=model_id,
                                provider="openrouter",
                                description=model_data.get("name", model_id),
                                context_length=model_data.get("context_length"),
                                max_tokens=model_data.get("max_completion_tokens"),
                                cost_per_1k_tokens=self._extract_cost(model_data),
                                supports_streaming=True,  # OpenRouter generally supports streaming
                                supports_tools=self._supports_tools(model_data),
                                model_type="chat"
                            )
                            models.append(model_info)
                            self.cached_models[model_id] = model_info
                        
                        self.models_cache_time = current_time
                        logger.info(f"Found {len(models)} OpenRouter models")
                        return models
                    else:
                        await self._handle_api_error(response)
                        return []
        except Exception as e:
            logger.error(f"Error listing OpenRouter models: {e}")
            return []
    
    def _extract_cost(self, model_data: Dict[str, Any]) -> Optional[float]:
        """Extract cost information from model data"""
        pricing = model_data.get("pricing", {})
        if pricing:
            # OpenRouter pricing is usually per 1M tokens, convert to 1K
            prompt_cost = pricing.get("prompt")
            completion_cost = pricing.get("completion")
            
            if prompt_cost:
                try:
                    # Convert from per 1M to per 1K tokens
                    return float(prompt_cost) / 1000
                except (ValueError, TypeError):
                    pass
        
        return None
    
    def _supports_tools(self, model_data: Dict[str, Any]) -> bool:
        """Determine if model supports tools/function calling"""
        model_id = model_data.get("id", "").lower()
        
        # Models known to support function calling
        tool_supporting_models = [
            "gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2",
            "mistral", "mixtral", "llama-3"
        ]
        
        return any(model_name in model_id for model_name in tool_supporting_models)
    
    async def generate_response(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """Generate a response using OpenRouter"""
        if not config:
            config = GenerationConfig()
        
        try:
            headers = self._build_headers()
            
            # Convert messages to OpenRouter format
            openrouter_messages = []
            for msg in messages:
                openrouter_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            payload = {
                "model": model,
                "messages": openrouter_messages,
                "stream": False,
                **self._build_openrouter_options(config)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        choice = result["choices"][0]
                        content = choice["message"]["content"]
                        
                        usage = result.get("usage", {})
                        
                        return GenerationResponse(
                            content=content,
                            model=result.get("model", model),
                            provider="openrouter",
                            usage={
                                "prompt_tokens": usage.get("prompt_tokens", 0),
                                "completion_tokens": usage.get("completion_tokens", 0),
                                "total_tokens": usage.get("total_tokens", 0)
                            },
                            finish_reason=choice.get("finish_reason"),
                            metadata={
                                "id": result.get("id"),
                                "created": result.get("created"),
                                "provider_name": result.get("provider", {}).get("name"),
                                "generation_time": result.get("provider", {}).get("generation_time")
                            }
                        )
                    else:
                        await self._handle_api_error(response)
                        
        except Exception as e:
            logger.error(f"Error generating response with OpenRouter: {e}")
            raise LLMProviderError(f"Generation failed: {e}", provider="openrouter")
    
    async def generate_response_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response using OpenRouter"""
        if not config:
            config = GenerationConfig()
        
        try:
            headers = self._build_headers()
            
            # Convert messages to OpenRouter format
            openrouter_messages = []
            for msg in messages:
                openrouter_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            payload = {
                "model": model,
                "messages": openrouter_messages,
                "stream": True,
                **self._build_openrouter_options(config)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        await self._handle_api_error(response)
                        return
                    
                    # Process streaming response
                    async for chunk in response.content.iter_chunked(1024):
                        if not chunk:
                            continue
                        
                        chunk_text = chunk.decode('utf-8', errors='ignore')
                        
                        for line in chunk_text.strip().split('\n'):
                            line = line.strip()
                            if not line or not line.startswith('data: '):
                                continue
                            
                            # Remove 'data: ' prefix
                            data_str = line[6:]
                            
                            if data_str == '[DONE]':
                                return
                            
                            try:
                                data = json.loads(data_str)
                                
                                if "choices" in data and data["choices"]:
                                    choice = data["choices"][0]
                                    delta = choice.get("delta", {})
                                    
                                    if "content" in delta:
                                        content = delta["content"]
                                        if content:
                                            yield content
                                    
                                    # Check if done
                                    if choice.get("finish_reason"):
                                        return
                                        
                            except json.JSONDecodeError:
                                continue
                        
        except Exception as e:
            logger.error(f"Error in OpenRouter streaming response: {e}")
            raise LLMProviderError(f"Streaming failed: {e}", provider="openrouter")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for OpenRouter API requests"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name
        }
        
        return headers
    
    def _build_openrouter_options(self, config: GenerationConfig) -> Dict[str, Any]:
        """Build OpenRouter-specific options from GenerationConfig"""
        options = {}
        
        if config.temperature is not None:
            options["temperature"] = config.temperature
        if config.max_tokens is not None:
            options["max_tokens"] = config.max_tokens
        if config.top_p is not None:
            options["top_p"] = config.top_p
        if config.frequency_penalty is not None:
            options["frequency_penalty"] = config.frequency_penalty
        if config.presence_penalty is not None:
            options["presence_penalty"] = config.presence_penalty
        if config.stop_sequences:
            options["stop"] = config.stop_sequences
        
        return options
    
    async def _handle_api_error(self, response: aiohttp.ClientResponse):
        """Handle OpenRouter API errors"""
        error_text = await response.text()
        
        try:
            error_data = json.loads(error_text)
            error_message = error_data.get("error", {}).get("message", error_text)
            error_code = error_data.get("error", {}).get("code")
        except json.JSONDecodeError:
            error_message = error_text
            error_code = None
        
        if response.status == 401:
            raise AuthenticationError(
                f"Authentication failed: {error_message}",
                provider="openrouter",
                error_code=error_code
            )
        elif response.status == 429:
            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                provider="openrouter",
                error_code=error_code
            )
        elif response.status == 404:
            raise ModelNotFoundError(
                f"Model not found: {error_message}",
                provider="openrouter",
                error_code=error_code
            )
        else:
            raise LLMProviderError(
                f"OpenRouter API error: {response.status} - {error_message}",
                provider="openrouter",
                error_code=error_code
            )
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Get information about a specific OpenRouter model"""
        # Check cached models first
        if model in self.cached_models:
            return self.cached_models[model]
        
        # Create basic info for unknown models
        return ModelInfo(
            name=model,
            provider="openrouter",
            description=f"OpenRouter model: {model}",
            context_length=self._estimate_context_length(model),
            supports_streaming=True,
            supports_tools=self._model_supports_tools(model),
            model_type="chat"
        )
    
    def _estimate_context_length(self, model_name: str) -> int:
        """Estimate context length based on model name"""
        model_lower = model_name.lower()
        
        # Common model context lengths
        if "gpt-4-turbo" in model_lower or "claude-3" in model_lower:
            return 128000
        elif "gpt-4" in model_lower:
            return 8192
        elif "gpt-3.5-turbo" in model_lower:
            return 16384
        elif "claude-2" in model_lower:
            return 100000
        elif "llama-3" in model_lower:
            return 8192
        elif "mixtral" in model_lower:
            return 32768
        else:
            return 4096  # Default assumption
    
    def _model_supports_tools(self, model_name: str) -> bool:
        """Check if a model supports tools/function calling"""
        model_lower = model_name.lower()
        
        tool_supporting_models = [
            "gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2",
            "mistral", "mixtral"
        ]
        
        return any(model_name in model_lower for model_name in tool_supporting_models)
    
    async def get_generation_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        """Calculate the cost of a generation"""
        model_info = await self._get_model_pricing(model)
        if not model_info:
            return None
        
        pricing = model_info.get("pricing", {})
        if not pricing:
            return None
        
        try:
            prompt_cost = float(pricing.get("prompt", 0))
            completion_cost = float(pricing.get("completion", 0))
            
            # OpenRouter pricing is per 1M tokens
            total_cost = (
                (prompt_tokens * prompt_cost / 1_000_000) +
                (completion_tokens * completion_cost / 1_000_000)
            )
            
            return total_cost
        except (ValueError, TypeError):
            return None
    
    async def _get_model_pricing(self, model: str) -> Optional[Dict[str, Any]]:
        """Get pricing information for a model"""
        try:
            headers = self._build_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models/{model}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
        except Exception as e:
            logger.error(f"Error getting model pricing for {model}: {e}")
            return None