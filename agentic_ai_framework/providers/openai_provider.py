"""
providers/openai_provider.py - OpenAI LLM Provider

Implementation of the BaseLLMProvider for OpenAI's API.
Supports chat completions, streaming, and all OpenAI models.
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

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI provider
        
        Args:
            config: Configuration dictionary with keys:
                - api_key: OpenAI API key
                - base_url: API base URL (optional, defaults to OpenAI)
                - organization: Organization ID (optional)
                - timeout: Request timeout (optional)
                - default_model: Default model name (optional)
        """
        super().__init__("openai", config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.openai.com/v1").rstrip('/')
        self.organization = config.get("organization")
        self.timeout = config.get("timeout", 300)
        self.default_model = config.get("default_model", "gpt-3.5-turbo")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # OpenAI-specific features
        self.config["supported_features"] = [
            "streaming", "chat", "tools", "embeddings", "vision", "audio"
        ]
        
        # Common OpenAI models with their specifications
        self.known_models = {
            "gpt-4": ModelInfo(
                name="gpt-4",
                provider="openai",
                description="Most capable GPT-4 model",
                context_length=8192,
                max_tokens=4096,
                cost_per_1k_tokens=0.03,
                supports_streaming=True,
                supports_tools=True,
                model_type="chat"
            ),
            "gpt-4-turbo": ModelInfo(
                name="gpt-4-turbo",
                provider="openai",
                description="Latest GPT-4 Turbo model",
                context_length=128000,
                max_tokens=4096,
                cost_per_1k_tokens=0.01,
                supports_streaming=True,
                supports_tools=True,
                model_type="chat"
            ),
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                provider="openai",
                description="Fast and efficient GPT-3.5 model",
                context_length=16384,
                max_tokens=4096,
                cost_per_1k_tokens=0.001,
                supports_streaming=True,
                supports_tools=True,
                model_type="chat"
            ),
            "gpt-4o": ModelInfo(
                name="gpt-4o",
                provider="openai",
                description="GPT-4 Omni multimodal model",
                context_length=128000,
                max_tokens=4096,
                cost_per_1k_tokens=0.005,
                supports_streaming=True,
                supports_tools=True,
                model_type="chat"
            )
        }
    
    async def initialize(self) -> bool:
        """Initialize and test connection to OpenAI"""
        try:
            is_healthy = await self.health_check()
            if is_healthy:
                self.is_initialized = True
                logger.info("OpenAI provider initialized successfully")
                return True
            else:
                logger.error("OpenAI health check failed during initialization")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
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
                        logger.warning(f"OpenAI health check failed: {response.status} - {error_text}")
                    else:
                        logger.debug("OpenAI health check: OK")
                    return is_healthy
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenAI"""
        try:
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
                            
                            # Use known model info if available, otherwise create basic info
                            if model_id in self.known_models:
                                models.append(self.known_models[model_id])
                            else:
                                model_info = ModelInfo(
                                    name=model_id,
                                    provider="openai",
                                    description=f"OpenAI model: {model_id}",
                                    context_length=self._estimate_context_length(model_id),
                                    supports_streaming=True,
                                    supports_tools="gpt" in model_id.lower(),
                                    model_type="chat" if "gpt" in model_id else "text"
                                )
                                models.append(model_info)
                        
                        logger.info(f"Found {len(models)} OpenAI models")
                        return models
                    else:
                        await self._handle_api_error(response)
                        return []
        except Exception as e:
            logger.error(f"Error listing OpenAI models: {e}")
            return []
    
    def _estimate_context_length(self, model_name: str) -> int:
        """Estimate context length based on model name"""
        model_lower = model_name.lower()
        
        if "gpt-4-turbo" in model_lower or "gpt-4o" in model_lower:
            return 128000
        elif "gpt-4" in model_lower:
            return 8192
        elif "gpt-3.5-turbo" in model_lower:
            return 16384
        elif "text-" in model_lower:
            return 4096
        else:
            return 4096  # Default assumption
    
    async def generate_response(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """Generate a response using OpenAI"""
        if not config:
            config = GenerationConfig()
        
        try:
            headers = self._build_headers()
            
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            payload = {
                "model": model,
                "messages": openai_messages,
                "stream": False,
                **self._build_openai_options(config)
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
                            model=result["model"],
                            provider="openai",
                            usage={
                                "prompt_tokens": usage.get("prompt_tokens", 0),
                                "completion_tokens": usage.get("completion_tokens", 0),
                                "total_tokens": usage.get("total_tokens", 0)
                            },
                            finish_reason=choice.get("finish_reason"),
                            metadata={
                                "id": result.get("id"),
                                "created": result.get("created"),
                                "system_fingerprint": result.get("system_fingerprint")
                            }
                        )
                    else:
                        await self._handle_api_error(response)
                        
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {e}")
            raise LLMProviderError(f"Generation failed: {e}", provider="openai")
    
    async def generate_response_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response using OpenAI"""
        if not config:
            config = GenerationConfig()
        
        try:
            headers = self._build_headers()
            
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            payload = {
                "model": model,
                "messages": openai_messages,
                "stream": True,
                **self._build_openai_options(config)
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
            logger.error(f"Error in OpenAI streaming response: {e}")
            raise LLMProviderError(f"Streaming failed: {e}", provider="openai")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for OpenAI API requests"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        return headers
    
    def _build_openai_options(self, config: GenerationConfig) -> Dict[str, Any]:
        """Build OpenAI-specific options from GenerationConfig"""
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
        """Handle OpenAI API errors"""
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
                provider="openai",
                error_code=error_code
            )
        elif response.status == 429:
            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                provider="openai",
                error_code=error_code
            )
        elif response.status == 404:
            raise ModelNotFoundError(
                f"Model not found: {error_message}",
                provider="openai",
                error_code=error_code
            )
        else:
            raise LLMProviderError(
                f"OpenAI API error: {response.status} - {error_message}",
                provider="openai",
                error_code=error_code
            )
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Get information about a specific OpenAI model"""
        if model in self.known_models:
            return self.known_models[model]
        
        # Create basic info for unknown models
        return ModelInfo(
            name=model,
            provider="openai",
            description=f"OpenAI model: {model}",
            context_length=self._estimate_context_length(model),
            supports_streaming=True,
            supports_tools="gpt" in model.lower(),
            model_type="chat" if "gpt" in model else "text"
        )