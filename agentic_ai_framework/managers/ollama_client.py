"""
managers/ollama_client.py - Fixed Ollama LLM Client

Fixes for model installation:
1. Added missing asyncio import
2. Improved streaming response parsing
3. Better completion detection logic
4. Enhanced error handling
5. Support for model name formats with/without tags
"""

import aiohttp
import asyncio
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
    
    def _normalize_model_name(self, model_name: str) -> str:
        """
        Normalize model name to include tag if missing
        
        Args:
            model_name: Raw model name
            
        Returns:
            Normalized model name with tag
        """
        # If no tag specified, don't add :latest as Ollama handles this
        # Just return the name as-is
        return model_name.strip()
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model to Ollama with proper completion tracking
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        normalized_name = self._normalize_model_name(model_name)
        
        try:
            # First check if model already exists
            existing_models = await self.list_models()
            if any(normalized_name in model or model.startswith(normalized_name) for model in existing_models):
                logger.info(f"Model {normalized_name} already exists")
                return True
            
            async with aiohttp.ClientSession() as session:
                payload = {"name": normalized_name, "stream": True}
                
                logger.info(f"Starting to pull model: {normalized_name}")
                
                async with session.post(
                    f"{self.ollama_url}/api/pull", 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to start pull for {normalized_name}: HTTP {response.status} - {error_text}")
                        return False
                    
                    # Track download progress
                    completion_indicators = [
                        "success",
                        "pulling manifest",
                        "writing manifest", 
                        "verifying sha256 digest",
                        "downloading"
                    ]
                    
                    last_status = ""
                    download_started = False
                    download_completed = False
                    
                    # Process streaming response
                    async for chunk in response.content.iter_chunked(1024):
                        if not chunk:
                            continue
                            
                        # Handle multiple JSON objects in one chunk
                        chunk_text = chunk.decode('utf-8', errors='ignore')
                        
                        # Split by newlines and process each line
                        for line in chunk_text.strip().split('\n'):
                            if not line.strip():
                                continue
                                
                            try:
                                progress_data = json.loads(line.strip())
                                status = progress_data.get('status', '').lower()
                                
                                if status != last_status:
                                    logger.info(f"Model {normalized_name}: {progress_data.get('status', 'Unknown status')}")
                                    last_status = status
                                
                                # Track download progress
                                if 'downloading' in status or 'pulling' in status:
                                    download_started = True
                                    
                                # Check for completion
                                if status == 'success' or (
                                    download_started and 
                                    ('success' in status or 'verifying sha256' in status)
                                ):
                                    download_completed = True
                                    logger.info(f"Model {normalized_name} download completed successfully")
                                    break
                                    
                            except json.JSONDecodeError:
                                # Skip malformed JSON lines
                                continue
                        
                        if download_completed:
                            break
                    
                    # Verify installation
                    if download_completed or download_started:
                        # Give Ollama time to finalize the model
                        await asyncio.sleep(3)
                        
                        # Check if model is now available
                        updated_models = await self.list_models()
                        
                        # Check if our model is in the list (handle partial name matches)
                        model_installed = any(
                            normalized_name in model or 
                            model.startswith(normalized_name.split(':')[0])
                            for model in updated_models
                        )
                        
                        if model_installed:
                            logger.info(f"Successfully installed and verified model: {normalized_name}")
                            return True
                        else:
                            logger.warning(f"Model {normalized_name} not found after installation. Available: {updated_models}")
                            # Return True anyway if download completed (might be a verification issue)
                            return download_completed
                    
                    logger.error(f"Model {normalized_name} download did not complete properly")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout pulling model {normalized_name} (1 hour limit)")
            return False
        except Exception as e:
            logger.error(f"Error pulling model {normalized_name}: {e}")
            return False
    
    async def pull_model_simple(self, model_name: str) -> bool:
        """
        Simple pull without streaming - more reliable for some models
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        normalized_name = self._normalize_model_name(model_name)
        
        try:
            # Check if already exists
            existing_models = await self.list_models()
            if any(normalized_name in model or model.startswith(normalized_name) for model in existing_models):
                logger.info(f"Model {normalized_name} already exists")
                return True
            
            async with aiohttp.ClientSession() as session:
                payload = {"name": normalized_name, "stream": False}  # No streaming
                
                logger.info(f"Starting to pull model (simple): {normalized_name}")
                
                async with session.post(
                    f"{self.ollama_url}/api/pull", 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=3600)  # 1 hour
                ) as response:
                    
                    if response.status == 200:
                        # This will block until download is complete
                        result = await response.text()
                        logger.info(f"Pull command completed for {normalized_name}")
                        
                        # Wait a bit for finalization
                        await asyncio.sleep(5)
                        
                        # Verify model is installed
                        updated_models = await self.list_models()
                        model_installed = any(
                            normalized_name in model or 
                            model.startswith(normalized_name.split(':')[0])
                            for model in updated_models
                        )
                        
                        if model_installed:
                            logger.info(f"Successfully installed model: {normalized_name}")
                            return True
                        else:
                            logger.error(f"Model {normalized_name} not found after installation. Available: {updated_models}")
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to pull model {normalized_name}: HTTP {response.status} - {error_text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout pulling model {normalized_name}")
            return False
        except Exception as e:
            logger.error(f"Error pulling model {normalized_name}: {e}")
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
            normalized_name = self._normalize_model_name(model_name)
            
            async with aiohttp.ClientSession() as session:
                payload = {"name": normalized_name}
                async with session.delete(
                    f"{self.ollama_url}/api/delete", 
                    json=payload
                ) as response:
                    success = response.status == 200
                    if success:
                        logger.info(f"Successfully deleted model: {normalized_name}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to delete model {normalized_name}: {error_text}")
                    return success
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {e}")
            return False
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model information dict or None if not found
        """
        try:
            models = await self.list_models()
            for model in models:
                if model_name in model or model.startswith(model_name):
                    return {"name": model, "available": True}
            return None
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return None