"""
main.py - FastAPI Application Entry Point (Enhanced with Fixed Model Installation)

Added features:
- Fixed Ollama models installation with proper error handling
- Memory management and cleanup
- Automatic memory clearing on startup
- Memory statistics and cleanup endpoints
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
import time
from datetime import datetime
from typing import List

from config import Config
from models import *
from managers.ollama_client import OllamaClient
from managers.memory_manager import MemoryManager
from managers.tool_manager import ToolManager
from managers.agent_manager import AgentManager
from managers.workflow_manager import WorkflowManager
from managers.model_warmup_manager import ModelWarmupManager, ModelWarmupStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Framework",
    description="A robust framework for managing AI agents and workflows with enhanced memory management",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global configuration
config = Config()

# Initialize managers
ollama_client = OllamaClient(config.ollama_url, config.default_model)
memory_manager = MemoryManager(config.database_path)
tool_manager = ToolManager(memory_manager, config.tools_directory)
agent_manager = AgentManager(ollama_client, memory_manager, tool_manager, config)
workflow_manager = WorkflowManager(agent_manager, tool_manager, memory_manager)
warmup_manager = ModelWarmupManager(ollama_client, memory_manager, config)


# Enhanced Background scheduler with memory cleanup
class BackgroundScheduler:
    """Enhanced background scheduler with memory management"""
    
    def __init__(self, memory_manager, agent_manager, workflow_manager, config, interval=60):
        self.memory_manager = memory_manager
        self.agent_manager = agent_manager
        self.workflow_manager = workflow_manager
        self.config = config
        self.interval = interval
        self.running = False
        self._last_memory_cleanup = time.time()
    
    async def start(self):
        """Start the background scheduler"""
        self.running = True
        logger.info("Enhanced background scheduler started with memory management")
        
        while self.running:
            try:
                await self._process_pending_tasks()
                await self._check_memory_cleanup()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self.interval)
    
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        logger.info("Background scheduler stopped")
    
    async def _process_pending_tasks(self):
        """Process pending scheduled tasks"""
        pending_tasks = self.memory_manager.get_pending_scheduled_tasks()
        
        for task in pending_tasks:
            try:
                logger.info(f"Executing scheduled task {task['id']}: {task['task_type']}")
                
                if task['task_type'] == "agent":
                    result = await self.agent_manager.execute_agent(
                        task['agent_name'], 
                        task['task_description'],
                        context=task['context'] or {}
                    )
                elif task['task_type'] == "workflow":
                    result = await self.workflow_manager.execute_workflow(
                        task['workflow_name'],
                        context=task['context'] or {}
                    )
                else:
                    raise ValueError(f"Unknown task type: {task['task_type']}")
                
                self.memory_manager.update_scheduled_task_status(
                    task['id'], "completed", str(result)
                )
                logger.info(f"Completed scheduled task {task['id']}")
                
            except Exception as e:
                error_msg = str(e)
                self.memory_manager.update_scheduled_task_status(
                    task['id'], "failed", error_msg
                )
                logger.error(f"Failed scheduled task {task['id']}: {error_msg}")
    
    async def _check_memory_cleanup(self):
        """Check if periodic memory cleanup is needed"""
        current_time = time.time()
        
        if current_time - self._last_memory_cleanup >= self.config.memory_cleanup_interval:
            await self._cleanup_memory_periodic()
            self._last_memory_cleanup = current_time
    
    async def _cleanup_memory_periodic(self):
        """Periodic memory cleanup for all agents"""
        try:
            logger.info("Starting periodic memory cleanup...")
            agents = self.memory_manager.get_all_agents()
            
            for agent in agents:
                self.memory_manager.cleanup_agent_memory(
                    agent["name"], 
                    keep_last=self.config.max_agent_memory_entries
                )
            
            logger.info(f"Completed periodic memory cleanup for {len(agents)} agents")
        except Exception as e:
            logger.error(f"Error during periodic memory cleanup: {e}")

# Initialize enhanced background scheduler
background_scheduler = BackgroundScheduler(
    memory_manager, agent_manager, workflow_manager, config, config.scheduler_interval
)

@app.on_event("startup")
async def startup_event():
    """Initialize the framework on startup with memory cleanup"""
    try:
        # Initialize database tables
        memory_manager.initialize_database()
        
        # Clear all agent memory on startup if configured
        if config.clear_memory_on_startup:
            logger.info("Clearing all agent memory on startup...")
            memory_manager.clear_all_agent_memory()
        
        # Load and register tools
        tool_manager.discover_and_register_tools()
        
        # Start background scheduler
        asyncio.create_task(background_scheduler.start())
        
        logger.info("Agentic AI Framework started successfully with enhanced memory management")
        
        # Start model warmup manager
        await warmup_manager.start()
        
        logger.info("Agentic AI Framework started successfully with model warmup")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    background_scheduler.stop()
    logger.info("Agentic AI Framework shutdown complete")
    await warmup_manager.stop()
    logger.info("Agentic AI Framework shutdown complete")

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Agentic AI Framework",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health",
        "models": "/models",
        "memory_stats": "/memory/stats"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with warmup info"""
    warmup_stats = warmup_manager.get_warmup_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "ollama_status": await ollama_client.health_check(),
        "memory_entries": memory_manager.get_memory_stats()["total_memory_entries"],
        "warmup_stats": {
            "active_models": warmup_stats["active_models"],
            "total_models": warmup_stats["total_models"],
            "success_rate": warmup_stats["success_rate"]
        }
    }

# FIXED: Models endpoints with proper error handling
@app.get("/models", response_model=List[str])
async def list_ollama_models():
    """List all available models in Ollama"""
    try:
        models = await ollama_client.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

@app.get("/models/status")
async def get_models_status():
    """Get detailed status of available models"""
    try:
        models = await ollama_client.list_models()
        health = await ollama_client.health_check()
        return {
            "ollama_healthy": health,
            "total_models": len(models),
            "available_models": models,
            "default_model": config.default_model,
            "recommended_models": [
                "deepseek-r1:1.5b",
                "granite3.2:2b", 
                "tinyllama:1.1b",
                "deepseek-coder:1.3b",
                "smollm:135m"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models status: {str(e)}")

@app.post("/models/install")
async def install_model(request: ModelInstallRequest, background_tasks: BackgroundTasks):
    """Install a new model in Ollama with improved error handling"""
    try:
        # Validate model name format
        model_name = request.model_name.strip()
        if not model_name:
            raise HTTPException(status_code=400, detail="Model name cannot be empty")
        
        # Check if model already exists
        models = await ollama_client.list_models()
        existing_model = None
        for model in models:
            if model_name in model or model.startswith(model_name.split(':')[0]):
                existing_model = model
                break
        
        if existing_model:
            return {
                "message": f"Model {existing_model} is already installed",
                "model_name": existing_model,
                "status": "already_installed"
            }
        
        logger.info(f"Starting installation of model: {model_name}")
        
        if request.wait_for_completion:
            # Wait for completion (blocking) - try simple method first
            try:
                success = await ollama_client.pull_model_simple(model_name)
                if not success:
                    # Fallback to streaming method
                    logger.info(f"Simple pull failed, trying streaming method for {model_name}")
                    success = await ollama_client.pull_model(model_name)
                
                if success:
                    # Verify installation one more time
                    updated_models = await ollama_client.list_models()
                    installed_model = None
                    for model in updated_models:
                        if model_name in model or model.startswith(model_name.split(':')[0]):
                            installed_model = model
                            break
                    
                    if installed_model:
                        return {
                            "message": f"Model {installed_model} installed successfully",
                            "model_name": installed_model,
                            "status": "installed"
                        }
                    else:
                        raise HTTPException(
                            status_code=500, 
                            detail=f"Model installation reported success but model {model_name} not found in model list"
                        )
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Failed to install model {model_name}. Check Ollama logs for details."
                    )
                    
            except Exception as e:
                logger.error(f"Model installation error for {model_name}: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Model installation failed: {str(e)}"
                )
        else:
            # Start installation in background
            async def background_install():
                try:
                    logger.info(f"Background installation started for {model_name}")
                    success = await ollama_client.pull_model_simple(model_name)
                    if success:
                        logger.info(f"Background installation completed for {model_name}")
                    else:
                        logger.error(f"Background installation failed for {model_name}")
                except Exception as e:
                    logger.error(f"Background installation error for {model_name}: {e}")
            
            background_tasks.add_task(background_install)
            return {
                "message": f"Model {model_name} installation started in background",
                "model_name": model_name,
                "status": "installing"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected model installation error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/models/status/{model_name}")
async def get_model_status(model_name: str):
    """Get status of a specific model"""
    try:
        models = await ollama_client.list_models()
        
        # Check if model exists (handle partial matches)
        found_model = None
        for model in models:
            if model_name in model or model.startswith(model_name.split(':')[0]):
                found_model = model
                break
        
        if found_model:
            return {
                "model_name": model_name,
                "found_as": found_model,
                "status": "installed",
                "available": True
            }
        else:
            return {
                "model_name": model_name,
                "found_as": None,
                "status": "not_installed",
                "available": False,
                "available_models": models
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking model status: {str(e)}")

@app.post("/models/test/{model_name}")
async def test_model(model_name: str):
    """Test if a model is working correctly"""
    try:
        # First check if model exists
        models = await ollama_client.list_models()
        found_model = None
        
        for model in models:
            if model_name in model or model.startswith(model_name.split(':')[0]):
                found_model = model
                break
        
        if not found_model:
            raise HTTPException(
                status_code=404, 
                detail=f"Model {model_name} not found. Available models: {models}"
            )
        
        # Test the model with a simple prompt
        test_prompt = "Hello, please respond with 'Model test successful' to confirm you are working."
        
        response = await ollama_client.generate_response(
            prompt=test_prompt,
            model=found_model
        )
        
        return {
            "model_name": found_model,
            "test_prompt": test_prompt,
            "response": response,
            "status": "working",
            "test_successful": True
        }
        
    except Exception as e:
        logger.error(f"Model test error for {model_name}: {e}")
        return {
            "model_name": model_name,
            "error": str(e),
            "status": "error",
            "test_successful": False
        }

@app.get("/models/installation-guide")
async def get_installation_guide():
    """Get guide for installing models"""
    return {
        "recommended_models": {
            "ultra_lightweight": {
                "name": "smollm:135m",
                "size": "~92MB",
                "use_case": "Ultra-lightweight tasks, very fast responses",
                "install_command": "curl -X POST 'http://localhost:8000/models/install' -H 'Content-Type: application/json' -d '{\"model_name\": \"smollm:135m\", \"wait_for_completion\": true}'"
            },
            "lightweight": {
                "name": "tinyllama:1.1b", 
                "size": "~637MB",
                "use_case": "General lightweight tasks, good balance",
                "install_command": "curl -X POST 'http://localhost:8000/models/install' -H 'Content-Type: application/json' -d '{\"model_name\": \"tinyllama:1.1b\", \"wait_for_completion\": true}'"
            },
            "recommended": {
                "name": "deepseek-r1:1.5b",
                "size": "~1.1GB", 
                "use_case": "Reasoning and tool calling (recommended default)",
                "install_command": "curl -X POST 'http://localhost:8000/models/install' -H 'Content-Type: application/json' -d '{\"model_name\": \"deepseek-r1:1.5b\", \"wait_for_completion\": true}'"
            },
            "coding": {
                "name": "deepseek-coder:1.3b",
                "size": "~776MB",
                "use_case": "Code-related tasks and programming",
                "install_command": "curl -X POST 'http://localhost:8000/models/install' -H 'Content-Type: application/json' -d '{\"model_name\": \"deepseek-coder:1.3b\", \"wait_for_completion\": true}'"
            }
        },
        "installation_steps": [
            "1. Choose a model from the recommended list above",
            "2. Use the provided curl command or API endpoint",
            "3. Wait for installation to complete (can take 5-15 minutes depending on model size)",
            "4. Test the model using /models/test/{model_name}",
            "5. Update your agent configurations to use the new model"
        ],
        "troubleshooting": {
            "installation_fails": "Check Ollama is running and accessible at the configured URL",
            "model_not_found": "Verify model name is correct and exists in Ollama registry",
            "timeout_errors": "Large models may take time to download, consider background installation",
            "memory_issues": "Ensure sufficient disk space and RAM for the model size"
        }
    }

@app.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a model from Ollama"""
    try:
        success = await ollama_client.delete_model(model_name)
        if success:
            return {
                "message": f"Model {model_name} deleted successfully",
                "model_name": model_name,
                "status": "deleted"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to delete model {model_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model Warmup endpoints
@app.post("/models/warmup")
async def warmup_models(model_names: List[str] = None, background_tasks: BackgroundTasks = None):
    """Warm up specific models or all agent models"""
    try:
        if model_names:
            # Warm up specific models
            if len(model_names) > 5:
                # For many models, do it in background
                if background_tasks:
                    background_tasks.add_task(warmup_manager.warmup_models, model_names)
                    return {
                        "message": f"Warming up {len(model_names)} models in background",
                        "models": model_names,
                        "status": "started"
                    }
            
            # Warm up synchronously for small lists
            results = await warmup_manager.warmup_models(model_names)
            successful = [name for name, status in results.items() if status.warmup_success]
            failed = [name for name, status in results.items() if not status.warmup_success]
            
            return {
                "message": f"Warmup completed for {len(model_names)} models",
                "successful": successful,
                "failed": failed,
                "results": {name: {
                    "success": status.warmup_success,
                    "warmup_time": status.warmup_time_seconds,
                    "error": status.error_message
                } for name, status in results.items()}
            }
        else:
            # Warm up all agent models
            results = await warmup_manager.warmup_agent_models()
            successful = [name for name, status in results.items() if status.warmup_success]
            failed = [name for name, status in results.items() if not status.warmup_success]
            
            return {
                "message": f"Warmed up {len(successful)} agent models",
                "successful": successful,
                "failed": failed,
                "total_models": len(results),
                "results": {name: {
                    "success": status.warmup_success,
                    "warmup_time": status.warmup_time_seconds,
                    "error": status.error_message
                } for name, status in results.items()}
            }
            
    except Exception as e:
        logger.error(f"Model warmup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/warmup/{model_name}")
async def warmup_single_model(model_name: str, force: bool = False):
    """Warm up a single model"""
    try:
        status = await warmup_manager.warmup_model(model_name, force=force)
        
        return {
            "model_name": model_name,
            "success": status.warmup_success,
            "warmup_time_seconds": status.warmup_time_seconds,
            "warmed_at": status.warmed_at.isoformat(),
            "is_active": status.is_active,
            "error": status.error_message
        }
        
    except Exception as e:
        logger.error(f"Error warming model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/warmup/status")
async def get_warmup_status():
    """Get warmup status for all models"""
    try:
        statuses = warmup_manager.get_warmup_status()
        stats = warmup_manager.get_warmup_stats()
        
        return {
            "stats": stats,
            "models": {
                name: {
                    "model_name": status.model_name,
                    "is_active": status.is_active,
                    "warmup_success": status.warmup_success,
                    "warmed_at": status.warmed_at.isoformat(),
                    "last_used": status.last_used.isoformat(),
                    "warmup_time_seconds": status.warmup_time_seconds,
                    "usage_count": status.usage_count,
                    "error_message": status.error_message
                } for name, status in statuses.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting warmup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/warmup/status/{model_name}")
async def get_model_warmup_status(model_name: str):
    """Get warmup status for a specific model"""
    try:
        status = warmup_manager.get_warmup_status(model_name).get(model_name)
        
        if not status:
            return {
                "model_name": model_name,
                "is_warmed": False,
                "message": "Model not warmed"
            }
        
        return {
            "model_name": model_name,
            "is_warmed": True,
            "is_active": status.is_active,
            "warmup_success": status.warmup_success,
            "warmed_at": status.warmed_at.isoformat(),
            "last_used": status.last_used.isoformat(),
            "warmup_time_seconds": status.warmup_time_seconds,
            "usage_count": status.usage_count,
            "error_message": status.error_message
        }
        
    except Exception as e:
        logger.error(f"Error getting status for model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/warmup/stats")
async def get_warmup_stats():
    """Get comprehensive warmup statistics"""
    try:
        return warmup_manager.get_warmup_stats()
    except Exception as e:
        logger.error(f"Error getting warmup stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/models/warmup/{model_name}")
async def remove_model_from_warmup(model_name: str):
    """Remove a model from the warmup cache"""
    try:
        if model_name in warmup_manager.warmed_models:
            del warmup_manager.warmed_models[model_name]
            return {
                "message": f"Model {model_name} removed from warmup cache",
                "model_name": model_name
            }
        else:
            return {
                "message": f"Model {model_name} was not in warmup cache",
                "model_name": model_name
            }
            
    except Exception as e:
        logger.error(f"Error removing model {model_name} from warmup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration endpoints
@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current framework configuration"""
    return ConfigResponse(**config.to_dict())

@app.put("/config")
async def update_config(config_update: ConfigUpdate):
    """Update framework configuration"""
    try:
        config.update(config_update.dict(exclude_unset=True))
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Agent endpoints (existing with memory limits applied)
@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent_def: AgentDefinition):
    """Create a new agent"""
    try:
        agent_id = memory_manager.register_agent(
            name=agent_def.name,
            role=agent_def.role,
            goals=agent_def.goals,
            backstory=agent_def.backstory,
            tools=agent_def.tools,
            ollama_model=agent_def.ollama_model,
            enabled=agent_def.enabled,
            tool_configs=agent_def.tool_configs or {}
        )
        return AgentResponse(id=agent_id, name=agent_def.name, message="Agent created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all agents"""
    return memory_manager.get_all_agents()

@app.get("/agents/{agent_name}", response_model=AgentInfo)
async def get_agent(agent_name: str):
    """Get agent details"""
    agent = memory_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.put("/agents/{agent_name}")
async def update_agent(agent_name: str, agent_update: AgentUpdate):
    """Update an existing agent"""
    try:
        memory_manager.update_agent(agent_name, agent_update.dict(exclude_unset=True))
        return {"message": "Agent updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/agents/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an agent"""
    try:
        memory_manager.delete_agent(agent_name)
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/{agent_name}/execute", response_model=AgentExecutionResponse)
async def execute_agent(agent_name: str, request: AgentExecutionRequest):
    """Execute an agent task with model usage tracking"""
    try:
        # Get agent info to track model usage
        agent = memory_manager.get_agent(agent_name)
        if agent:
            model_name = agent.get('ollama_model', config.default_model)
            await warmup_manager.mark_model_used(model_name)
        
        result = await agent_manager.execute_agent(
            agent_name, request.task, request.context or {}
        )
        return AgentExecutionResponse(
            agent_name=agent_name,
            task=request.task,
            result=result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/agents/{agent_name}/memory", response_model=List[MemoryEntryResponse])
async def get_agent_memory(agent_name: str, limit: int = 5):
    """Get agent's memory/conversation history (limited)"""
    return memory_manager.get_agent_memory(agent_name, limit)

# NEW: Memory management endpoints
@app.delete("/agents/{agent_name}/memory")
async def clear_agent_memory(agent_name: str):
    """Clear all memory for a specific agent"""
    try:
        agent = memory_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        memory_manager.clear_agent_memory(agent_name)
        return {"message": f"Memory cleared for agent {agent_name}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/{agent_name}/memory/cleanup")
async def cleanup_agent_memory_endpoint(agent_name: str, keep_last: int = 5):
    """Cleanup old memory entries for a specific agent"""
    try:
        agent = memory_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        memory_manager.cleanup_agent_memory(agent_name, keep_last)
        return {
            "message": f"Memory cleanup completed for agent {agent_name}",
            "kept_entries": keep_last
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory usage statistics"""
    try:
        stats = memory_manager.get_memory_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/clear-all")
async def clear_all_memory():
    """Clear memory for all agents"""
    try:
        memory_manager.clear_all_agent_memory()
        return {"message": "All agent memory cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/memory/cleanup")
async def cleanup_all_agent_memory():
    """Cleanup old memory entries for all agents, keeping only last entries"""
    try:
        agents = memory_manager.get_all_agents()
        cleaned_agents = 0
        
        for agent in agents:
            memory_manager.cleanup_agent_memory(agent["name"], keep_last=config.max_agent_memory_entries)
            cleaned_agents += 1
        
        return {
            "message": f"Memory cleanup completed for {cleaned_agents} agents",
            "agents_processed": cleaned_agents,
            "kept_entries_per_agent": config.max_agent_memory_entries
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Tool endpoints (existing, unchanged)
@app.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """List all tools"""
    return memory_manager.get_all_tools()

@app.get("/tools/{tool_name}", response_model=ToolInfo)
async def get_tool(tool_name: str):
    """Get tool details"""
    tool = memory_manager.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@app.post("/tools/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """Execute a tool directly"""
    try:
        result = await tool_manager.execute_tool(
            tool_name, request.parameters, request.agent_name
        )
        return ToolExecutionResponse(
            tool_name=tool_name,
            parameters=request.parameters,
            result=result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Workflow endpoints (existing, unchanged)
@app.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(workflow_def: WorkflowDefinition):
    """Create a new workflow"""
    try:
        steps_dict = []
        for step in workflow_def.steps:
            step_dict = {
                "type": step.type,
                "name": step.name,
                "task": step.task,
                "parameters": step.parameters or {},
                "context_key": step.context_key
            }
            steps_dict.append(step_dict)
        
        workflow_id = memory_manager.register_workflow(
            name=workflow_def.name,
            description=workflow_def.description,
            steps=steps_dict,
            enabled=workflow_def.enabled
        )
        return WorkflowResponse(id=workflow_id, name=workflow_def.name, message="Workflow created successfully")
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workflows", response_model=List[WorkflowInfo])
async def list_workflows():
    """List all workflows"""
    return memory_manager.get_all_workflows()

@app.get("/workflows/{workflow_name}", response_model=WorkflowInfo)
async def get_workflow(workflow_name: str):
    """Get workflow details"""
    workflow = memory_manager.get_workflow(workflow_name)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@app.put("/workflows/{workflow_name}")
async def update_workflow(workflow_name: str, workflow_update: WorkflowUpdate):
    """Update an existing workflow"""
    try:
        memory_manager.update_workflow(workflow_name, workflow_update.dict(exclude_unset=True))
        return {"message": "Workflow updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/workflows/{workflow_name}")
async def delete_workflow(workflow_name: str):
    """Delete a workflow"""
    try:
        memory_manager.delete_workflow(workflow_name)
        return {"message": "Workflow deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/workflows/{workflow_name}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(workflow_name: str, request: WorkflowExecutionRequest):
    """Execute a workflow"""
    try:
        result = await workflow_manager.execute_workflow(
            workflow_name, request.context or {}
        )
        return WorkflowExecutionResponse(
            workflow_name=workflow_name,
            context=request.context or {},
            result=result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Scheduling endpoints (existing, unchanged)
@app.post("/schedule", response_model=ScheduleResponse)
async def schedule_task(task: ScheduledTaskDefinition):
    """Schedule a task for execution"""
    try:
        task_id = memory_manager.schedule_task(
            task_type=task.task_type,
            agent_name=task.agent_name,
            workflow_name=task.workflow_name,
            task_description=task.task_description,
            scheduled_time=task.scheduled_time,
            context=task.context or {}
        )
        return ScheduleResponse(id=task_id, message="Task scheduled successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/schedule", response_model=List[ScheduledTaskInfo])
async def list_scheduled_tasks():
    """List all scheduled tasks"""
    return memory_manager.get_all_scheduled_tasks()

@app.delete("/schedule/{task_id}")
async def delete_scheduled_task(task_id: int):
    """Delete a scheduled task"""
    try:
        memory_manager.delete_scheduled_task(task_id)
        return {"message": "Scheduled task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )