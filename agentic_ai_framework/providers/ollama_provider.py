"""
providers/ollama_provider.py - Ollama LLM Provider

Implementation of the BaseLLMProvider for Ollama, refactored from the original
OllamaClient to work with the new provider interface.
"""

import aiohttp
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from .base_llm_provider import (
    BaseLLMProvider, ModelInfo, GenerationConfig, Message, GenerationResponse,
    LLMProviderError, ModelNotFoundError
)

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama provider
        
        Args:
            config: Configuration dictionary with keys:
                - url: Ollama instance URL
                - timeout: Request timeout (optional)
                - default_model: Default model name (optional)
        """
        super().__init__("ollama", config)
        self.base_url = config.get("url", "http://localhost:11434").rstrip('/')
        self.timeout = config.get("timeout", 300)
        self.default_model = config.get("default_model", "llama3")
        
        # Ollama-specific features
        self.config["supported_features"] = [
            "streaming", "chat", "generate", "embeddings", "model_management"
        ]
    
    async def initialize(self) -> bool:
        """Initialize and test connection to Ollama"""
        try:
            is_healthy = await self.health_check()
            if is_healthy:
                self.is_initialized = True
                logger.info(f"Ollama provider initialized successfully at {self.base_url}")
                return True
            else:
                logger.error("Ollama health check failed during initialization")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Ollama is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    is_healthy = response.status == 200
                    logger.debug(f"Ollama health check: {'OK' if is_healthy else 'FAILED'}")
                    return is_healthy
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models in Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        models = []
                        
                        for model_data in result.get("models", []):
                            model_info = ModelInfo(
                                name=model_data["name"],
                                provider="ollama",
                                description=f"Ollama model: {model_data['name']}",
                                context_length=self._estimate_context_length(model_data["name"]),
                                supports_streaming=True,
                                supports_tools=False,  # Ollama doesn't have native tool support
                                model_type="chat"
                            )
                            models.append(model_info)
                        
                        logger.info(f"Found {len(models)} Ollama models")
                        return models
                    else:
                        logger.error(f"Failed to list models: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []
    
    def _estimate_context_length(self, model_name: str) -> int:
        """Estimate context length based on model name"""
        # Basic heuristics for common models
        model_lower = model_name.lower()
        
        if "llama3" in model_lower:
            return 8192
        elif "llama2" in model_lower:
            return 4096
        elif "codellama" in model_lower:
            return 16384
        elif "deepseek" in model_lower:
            return 4096
        elif "granite" in model_lower:
            return 8192
        elif "tinyllama" in model_lower:
            return 2048
        else:
            return 4096  # Default assumption
    
    async def generate_response(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """Generate a response using Ollama"""
        if not config:
            config = GenerationConfig()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Convert messages to Ollama format
                if len(messages) == 1 and messages[0].role == "user":
                    # Use generate endpoint for single prompt
                    payload = {
                        "model": model,
                        "prompt": messages[0].content,
                        "stream": False,
                        "options": self._build_ollama_options(config)
                    }
                    url = f"{self.base_url}/api/generate"
                else:
                    # Use chat endpoint for conversation
                    ollama_messages = []
                    for msg in messages:
                        ollama_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    
                    payload = {
                        "model": model,
                        "messages": ollama_messages,
                        "stream": False,
                        "options": self._build_ollama_options(config)
                    }
                    url = f"{self.base_url}/api/chat"
                
                logger.debug(f"Sending request to {url} with model {model}")
                
                async with session.post(
                    url, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract response content
                        if "message" in result:
                            content = result["message"].get("content", "")
                        else:
                            content = result.get("response", "")
                        
                        # Build usage information if available
                        usage = {}
                        if "eval_count" in result:
                            usage["completion_tokens"] = result["eval_count"]
                        if "prompt_eval_count" in result:
                            usage["prompt_tokens"] = result["prompt_eval_count"]
                        if usage:
                            usage["total_tokens"] = usage.get("completion_tokens", 0) + usage.get("prompt_tokens", 0)
                        
                        return GenerationResponse(
                            content=content,
                            model=model,
                            provider="ollama",
                            usage=usage if usage else None,
                            finish_reason=result.get("done_reason"),
                            metadata={
                                "total_duration": result.get("total_duration"),
                                "load_duration": result.get("load_duration"),
                                "eval_duration": result.get("eval_duration")
                            }
                        )
                    else:
                        error_text = await response.text()
                        raise LLMProviderError(
                            f"Ollama API error: {response.status} - {error_text}",
                            provider="ollama"
                        )
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with Ollama: {e}")
            raise LLMProviderError(f"Failed to connect to Ollama: {e}", provider="ollama")
        except Exception as e:
            logger.error(f"Error generating response with Ollama: {e}")
            raise LLMProviderError(f"Generation failed: {e}", provider="ollama")
    
    async def generate_response_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response using Ollama"""
        if not config:
            config = GenerationConfig()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Convert messages to Ollama format
                if len(messages) == 1 and messages[0].role == "user":
                    payload = {
                        "model": model,
                        "prompt": messages[0].content,
                        "stream": True,
                        "options": self._build_ollama_options(config)
                    }
                    url = f"{self.base_url}/api/generate"
                else:
                    ollama_messages = []
                    for msg in messages:
                        ollama_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    
                    payload = {
                        "model": model,
                        "messages": ollama_messages,
                        "stream": True,
                        "options": self._build_ollama_options(config)
                    }
                    url = f"{self.base_url}/api/chat"
                
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise LLMProviderError(
                            f"Ollama streaming API error: {response.status} - {error_text}",
                            provider="ollama"
                        )
                    
                    # Process streaming response
                    async for chunk in response.content.iter_chunked(1024):
                        if not chunk:
                            continue
                        
                        chunk_text = chunk.decode('utf-8', errors='ignore')
                        
                        for line in chunk_text.strip().split('\n'):
                            if not line.strip():
                                continue
                            
                            try:
                                data = json.loads(line.strip())
                                
                                # Extract content from response
                                content = ""
                                if "message" in data:
                                    content = data["message"].get("content", "")
                                elif "response" in data:
                                    content = data.get("response", "")
                                
                                if content:
                                    yield content
                                
                                # Check if done
                                if data.get("done", False):
                                    return
                                    
                            except json.JSONDecodeError:
                                continue
                        
        except Exception as e:
            logger.error(f"Error in Ollama streaming response: {e}")
            raise LLMProviderError(f"Streaming failed: {e}", provider="ollama")
    
    def _build_ollama_options(self, config: GenerationConfig) -> Dict[str, Any]:
        """Build Ollama-specific options from GenerationConfig"""
        options = {}
        
        if config.temperature is not None:
            options["temperature"] = config.temperature
        if config.top_p is not None:
            options["top_p"] = config.top_p
        if config.top_k is not None:
            options["top_k"] = config.top_k
        if config.max_tokens is not None:
            options["num_predict"] = config.max_tokens
        if config.stop_sequences:
            options["stop"] = config.stop_sequences
        
        return options
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model to Ollama instance
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": model_name, "stream": False}
                
                logger.info(f"Starting to pull model: {model_name}")
                
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully pulled model: {model_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to pull model {model_name}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    async def delete_model(self, model_name: str) -> bool:
        """
        Delete a model from Ollama instance
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": model_name}
                
                async with session.delete(
                    f"{self.base_url}/api/delete",
                    json=payload
                ) as response:
                    success = response.status == 200
                    if success:
                        logger.info(f"Successfully deleted model: {model_name}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to delete model {model_name}: {error_text}")
                    return success
                    
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {e}")
            return False
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Get information about a specific Ollama model"""
        return ModelInfo(
            name=model,
            provider="ollama",
            description=f"Ollama model: {model}",
            context_length=self._estimate_context_length(model),
            supports_streaming=True,
            supports_tools=False,
            model_type="chat"
        )