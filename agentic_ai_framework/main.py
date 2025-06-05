"""
main.py - FastAPI Application Entry Point (Enhanced with Models & Memory Management)

Added features:
- Ollama models listing endpoint
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
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    background_scheduler.stop()
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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "ollama_status": await ollama_client.health_check(),
        "memory_entries": memory_manager.get_memory_stats()["total_memory_entries"]
    }

# NEW: Models endpoints
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
    """Execute an agent task"""
    try:
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