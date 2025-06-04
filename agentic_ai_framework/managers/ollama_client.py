"""
managers/ollama_client.py - Ollama LLM Client

Handles communication with the local Ollama instance for LLM capabilities.
Provides methods for text generation and model management.
"""

import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for communicating with Ollama instance"""
    
    def __init__(self, ollama_url: str, default_model: str = "llama3"):
        """
        Initialize Ollama client
        
        Args:
            ollama_url: URL of the Ollama instance
            default_model: Default model to use for generation
        """
        self.ollama_url = ollama_url.rstrip('/')
        self.default_model = default_model
        logger.info(f"Initialized Ollama client for {self.ollama_url}")
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False
    ) -> str:
        """
        Generate a response using Ollama
        
        Args:
            prompt: The input prompt
            model: Model to use (defaults to default_model)
            chat_history: Previous conversation context
            stream: Whether to stream the response
            
        Returns:
            Generated response text
            
        Raises:
            Exception: If Ollama API call fails
        """
        model = model or self.default_model
        
        try:
            async with aiohttp.ClientSession() as session:
                if chat_history:
                    # Use chat endpoint for conversation context
                    messages = chat_history + [{"role": "user", "content": prompt}]
                    payload = {
                        "model": model,
                        "messages": messages,
                        "stream": stream
                    }
                    url = f"{self.ollama_url}/api/chat"
                else:
                    # Use generate endpoint for single prompt
                    payload = {
                        "model": model,
                        "prompt": prompt,
                        "stream": stream
                    }
                    url = f"{self.ollama_url}/api/generate"
                
                logger.debug(f"Sending request to {url} with model {model}")
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if chat_history:
                            return result.get("message", {}).get("content", "")
                        else:
                            return result.get("response", "")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error communicating with Ollama: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Ollama is accessible
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    is_healthy = response.status == 200
                    logger.debug(f"Ollama health check: {'OK' if is_healthy else 'FAILED'}")
                    return is_healthy
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        List available models in Ollama
        
        Returns:
            List of available model names
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        models = [model["name"] for model in result.get("models", [])]
                        logger.info(f"Available models: {models}")
                        return models
                    return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model to Ollama
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": model_name}
                async with session.post(
                    f"{self.ollama_url}/api/pull", 
                    json=payload
                ) as response:
                    success = response.status == 200
                    if success:
                        logger.info(f"Successfully pulled model: {model_name}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to pull model {model_name}: {error_text}")
                    return success
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    async def delete_model(self, model_name: str) -> bool:
        """
        Delete a model from Ollama
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": model_name}
                async with session.delete(
                    f"{self.ollama_url}/api/delete", 
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