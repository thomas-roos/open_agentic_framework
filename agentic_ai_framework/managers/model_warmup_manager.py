"""
managers/model_warmup_manager.py - Model Warmup System

Keeps models pre-loaded in memory for instant agent execution.
Manages model lifecycle, memory usage, and automatic warmup.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class ModelWarmupStatus:
    """Status of a warmed-up model"""
    model_name: str
    warmed_at: datetime
    last_used: datetime
    warmup_time_seconds: float
    usage_count: int
    is_active: bool
    warmup_success: bool
    error_message: Optional[str] = None

class ModelWarmupManager:
    """Manages model pre-warming and lifecycle"""
    
    def __init__(self, ollama_client, memory_manager, config):
        """
        Initialize the model warmup manager
        
        Args:
            ollama_client: OllamaClient instance
            memory_manager: MemoryManager instance
            config: Application configuration
        """
        self.ollama_client = ollama_client
        self.memory_manager = memory_manager
        self.config = config
        
        # Warmup configuration
        self.warmup_timeout = getattr(config, 'model_warmup_timeout', 60)
        self.max_concurrent_warmups = getattr(config, 'max_concurrent_warmups', 2)
        self.auto_warmup_on_startup = getattr(config, 'auto_warmup_on_startup', True)
        self.warmup_interval_hours = getattr(config, 'warmup_interval_hours', 6)
        self.max_idle_hours = getattr(config, 'max_idle_hours', 24)
        
        # State tracking
        self.warmed_models: Dict[str, ModelWarmupStatus] = {}
        self.warmup_queue: Set[str] = set()
        self.warmup_in_progress: Set[str] = set()
        self.background_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        logger.info("Model Warmup Manager initialized")
    
    async def start(self):
        """Start the warmup manager background tasks"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Model Warmup Manager...")
        
        # Start background maintenance task
        self.background_task = asyncio.create_task(self._background_maintenance())
        
        # Auto-warmup on startup if enabled
        if self.auto_warmup_on_startup:
            await self._auto_warmup_startup()
    
    async def stop(self):
        """Stop the warmup manager"""
        self.is_running = False
        
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Model Warmup Manager stopped")
    
    async def warmup_model(self, model_name: str, force: bool = False) -> ModelWarmupStatus:
        """
        Warm up a specific model
        
        Args:
            model_name: Name of the model to warm up
            force: Force warmup even if already warmed
            
        Returns:
            ModelWarmupStatus object
        """
        # Check if already warmed and recent
        if not force and model_name in self.warmed_models:
            status = self.warmed_models[model_name]
            if status.is_active and status.warmup_success:
                time_since_warmup = datetime.now() - status.warmed_at
                if time_since_warmup.total_seconds() < (self.warmup_interval_hours * 3600):
                    logger.info(f"Model {model_name} already warmed (age: {time_since_warmup})")
                    return status
        
        # Check if already in progress
        if model_name in self.warmup_in_progress:
            logger.info(f"Model {model_name} warmup already in progress")
            # Wait for completion
            while model_name in self.warmup_in_progress:
                await asyncio.sleep(1)
            return self.warmed_models.get(model_name)
        
        # Add to in-progress
        self.warmup_in_progress.add(model_name)
        
        try:
            logger.info(f"Starting warmup for model: {model_name}")
            start_time = time.time()
            
            # Create warmup status
            status = ModelWarmupStatus(
                model_name=model_name,
                warmed_at=datetime.now(),
                last_used=datetime.now(),
                warmup_time_seconds=0,
                usage_count=0,
                is_active=False,
                warmup_success=False
            )
            
            # Perform warmup by making a simple request
            success = await self._perform_warmup(model_name)
            
            # Update status
            end_time = time.time()
            status.warmup_time_seconds = end_time - start_time
            status.warmup_success = success
            status.is_active = success
            
            if not success:
                status.error_message = "Warmup request failed"
            
            # Store status
            self.warmed_models[model_name] = status
            
            if success:
                logger.info(f"✓ Model {model_name} warmed successfully in {status.warmup_time_seconds:.1f}s")
            else:
                logger.error(f"✗ Model {model_name} warmup failed after {status.warmup_time_seconds:.1f}s")
            
            return status
            
        except Exception as e:
            logger.error(f"Error warming model {model_name}: {e}")
            status = ModelWarmupStatus(
                model_name=model_name,
                warmed_at=datetime.now(),
                last_used=datetime.now(),
                warmup_time_seconds=time.time() - start_time,
                usage_count=0,
                is_active=False,
                warmup_success=False,
                error_message=str(e)
            )
            self.warmed_models[model_name] = status
            return status
            
        finally:
            self.warmup_in_progress.discard(model_name)
    
    async def warmup_models(self, model_names: List[str], max_concurrent: Optional[int] = None) -> Dict[str, ModelWarmupStatus]:
        """
        Warm up multiple models concurrently
        
        Args:
            model_names: List of model names to warm up
            max_concurrent: Maximum concurrent warmups (defaults to config value)
            
        Returns:
            Dictionary mapping model names to their warmup status
        """
        if not model_names:
            return {}
        
        max_concurrent = max_concurrent or self.max_concurrent_warmups
        logger.info(f"Warming up {len(model_names)} models (max concurrent: {max_concurrent})")
        
        # Create semaphore to limit concurrent warmups
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def warmup_with_semaphore(model_name: str):
            async with semaphore:
                return await self.warmup_model(model_name)
        
        # Execute warmups concurrently
        tasks = [warmup_with_semaphore(model) for model in model_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        status_dict = {}
        for model_name, result in zip(model_names, results):
            if isinstance(result, Exception):
                logger.error(f"Error warming model {model_name}: {result}")
                status_dict[model_name] = ModelWarmupStatus(
                    model_name=model_name,
                    warmed_at=datetime.now(),
                    last_used=datetime.now(),
                    warmup_time_seconds=0,
                    usage_count=0,
                    is_active=False,
                    warmup_success=False,
                    error_message=str(result)
                )
            else:
                status_dict[model_name] = result
        
        return status_dict
    
    async def warmup_agent_models(self) -> Dict[str, ModelWarmupStatus]:
        """
        Warm up all models used by registered agents
        
        Returns:
            Dictionary mapping model names to their warmup status
        """
        logger.info("Warming up models for all registered agents...")
        
        # Get all agents and their models
        agents = self.memory_manager.get_all_agents()
        agent_models = set()
        
        for agent in agents:
            if agent.get('enabled', True):
                model = agent.get('ollama_model', self.config.default_model)
                agent_models.add(model)
        
        logger.info(f"Found {len(agent_models)} unique models from {len(agents)} agents: {list(agent_models)}")
        
        if not agent_models:
            logger.warning("No agent models found to warm up")
            return {}
        
        return await self.warmup_models(list(agent_models))
    
    async def mark_model_used(self, model_name: str):
        """Mark a model as recently used"""
        if model_name in self.warmed_models:
            self.warmed_models[model_name].last_used = datetime.now()
            self.warmed_models[model_name].usage_count += 1
    
    def get_warmup_status(self, model_name: Optional[str] = None) -> Dict[str, ModelWarmupStatus]:
        """
        Get warmup status for models
        
        Args:
            model_name: Specific model name, or None for all models
            
        Returns:
            Dictionary of model statuses
        """
        if model_name:
            return {model_name: self.warmed_models.get(model_name)}
        else:
            return self.warmed_models.copy()
    
    def get_warmup_stats(self) -> Dict:
        """Get comprehensive warmup statistics"""
        now = datetime.now()
        total_models = len(self.warmed_models)
        active_models = sum(1 for status in self.warmed_models.values() if status.is_active)
        failed_models = sum(1 for status in self.warmed_models.values() if not status.warmup_success)
        
        avg_warmup_time = 0
        total_usage = 0
        
        if self.warmed_models:
            avg_warmup_time = sum(s.warmup_time_seconds for s in self.warmed_models.values()) / total_models
            total_usage = sum(s.usage_count for s in self.warmed_models.values())
        
        return {
            "total_models": total_models,
            "active_models": active_models,
            "failed_models": failed_models,
            "success_rate": (active_models / total_models * 100) if total_models > 0 else 0,
            "average_warmup_time_seconds": round(avg_warmup_time, 2),
            "total_usage_count": total_usage,
            "models_in_progress": len(self.warmup_in_progress),
            "manager_running": self.is_running
        }
    
    async def _perform_warmup(self, model_name: str) -> bool:
        """
        Perform the actual warmup by making a simple request to the model
        
        Args:
            model_name: Model to warm up
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Make a very simple request to load the model
            warmup_prompt = "Hello"
            
            response = await asyncio.wait_for(
                self.ollama_client.generate_response(
                    prompt=warmup_prompt,
                    model=model_name
                ),
                timeout=self.warmup_timeout
            )
            
            # Check if we got a reasonable response
            if response and len(response.strip()) > 0:
                logger.debug(f"Warmup response for {model_name}: {response[:50]}...")
                return True
            else:
                logger.warning(f"Empty warmup response for {model_name}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"Warmup timeout for model {model_name} after {self.warmup_timeout}s")
            return False
        except Exception as e:
            logger.error(f"Warmup error for model {model_name}: {e}")
            return False
    
    async def _auto_warmup_startup(self):
        """Automatically warm up agent models on startup"""
        logger.info("Auto-warming models on startup...")
        try:
            await self.warmup_agent_models()
        except Exception as e:
            logger.error(f"Error during startup warmup: {e}")
    
    async def _background_maintenance(self):
        """Background task for periodic maintenance"""
        logger.info("Starting background maintenance task")
        
        while self.is_running:
            try:
                await self._maintenance_cycle()
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background maintenance: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    async def _maintenance_cycle(self):
        """Perform maintenance tasks"""
        now = datetime.now()
        
        # Clean up old/inactive models
        models_to_remove = []
        for model_name, status in self.warmed_models.items():
            time_since_use = now - status.last_used
            
            if time_since_use.total_seconds() > (self.max_idle_hours * 3600):
                logger.info(f"Marking idle model {model_name} as inactive (idle for {time_since_use})")
                status.is_active = False
                models_to_remove.append(model_name)
        
        # Remove inactive models
        for model_name in models_to_remove:
            if self.warmed_models[model_name].usage_count == 0:
                logger.info(f"Removing unused model {model_name} from warmup cache")
                del self.warmed_models[model_name]
        
        # Re-warm models that need refreshing
        models_to_refresh = []
        for model_name, status in self.warmed_models.items():
            if status.is_active:
                time_since_warmup = now - status.warmed_at
                if time_since_warmup.total_seconds() > (self.warmup_interval_hours * 3600):
                    models_to_refresh.append(model_name)
        
        if models_to_refresh:
            logger.info(f"Refreshing {len(models_to_refresh)} models: {models_to_refresh}")
            await self.warmup_models(models_to_refresh)
        
        logger.debug(f"Maintenance complete. Active models: {len([s for s in self.warmed_models.values() if s.is_active])}")

# Configuration additions for config.py
class WarmupConfig:
    """Configuration for model warmup system"""
    
    def __init__(self):
        # Warmup settings
        self.model_warmup_timeout = 60  # seconds
        self.max_concurrent_warmups = 2  # concurrent warmup operations
        self.auto_warmup_on_startup = True  # warm up agent models on startup
        self.warmup_interval_hours = 6  # re-warm models every 6 hours
        self.max_idle_hours = 24  # remove models from cache after 24 hours of no use
        
        # Performance settings
        self.warmup_enabled = True  # enable/disable warmup system
        self.background_maintenance = True  # enable background maintenance
        self.log_warmup_details = True  # detailed logging