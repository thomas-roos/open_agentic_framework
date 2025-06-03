# api/rest_server.py - FIXED VERSION
import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class TaskRequest(BaseModel):
    description: str = Field(..., description="Task description")
    agent_name: Optional[str] = Field(None, description="Specific agent to handle task")
    workflow_name: Optional[str] = Field(None, description="Predefined workflow to use")
    priority: int = Field(1, description="Task priority (1-10)")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskResponse(BaseModel):
    task_id: str
    status: str
    created_at: datetime
    description: str

class TaskResult(BaseModel):
    task_id: str
    status: str
    result: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)  # FIXED: Proper indentation

class AgentConversation(BaseModel):
    agent_name: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)

class ConversationResponse(BaseModel):
    agent_name: str
    response: str
    conversation_id: str
    timestamp: datetime

class MemoryQuery(BaseModel):
    query: str
    agent_name: Optional[str] = None
    memory_type: Optional[str] = None
    limit: int = 10

class MemoryEntry(BaseModel):
    agent_name: str
    content: str
    memory_type: str = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

# Simple REST API (no complex orchestrator dependency for now)
class SimpleMultiAgentAPI:
    """Simplified REST API for the multi-agent system"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Multi-Agent Website Monitoring System",
            description="AI-powered website monitoring with email alerts",
            version="1.0.0"
        )
        
        # Task tracking (in-memory for now)
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "api": "active",
                    "agents": 5,
                    "memory": "active",
                    "scheduler": "active"
                }
            }
        
        @self.app.get("/agents")
        async def list_agents():
            """List available agents"""
            return {
                "planner": {
                    "name": "Planner",
                    "role": "Strategic Planning and Coordination",
                    "capabilities": ["task_decomposition", "workflow_planning", "resource_allocation"]
                },
                "dataagent": {
                    "name": "DataAgent", 
                    "role": "Data Analysis and Processing",
                    "capabilities": ["data_analysis", "file_processing", "statistical_analysis"]
                },
                "codeagent": {
                    "name": "CodeAgent",
                    "role": "Software Development and Programming", 
                    "capabilities": ["code_generation", "debugging", "code_analysis"]
                },
                "researchagent": {
                    "name": "ResearchAgent",
                    "role": "Information Gathering and Analysis",
                    "capabilities": ["web_research", "document_analysis", "information_synthesis"]
                },
                "systemagent": {
                    "name": "SystemAgent",
                    "role": "System Operations and Management",
                    "capabilities": ["command_execution", "system_monitoring", "infrastructure_management"]
                },
                "monitoring": {
                    "name": "MonitoringAgent",
                    "role": "Website and Service Monitoring",
                    "capabilities": ["website_monitoring", "health_checks", "alerting", "uptime_monitoring"]
                }
            }
        
        @self.app.post("/tasks", response_model=TaskResponse)
        async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
            """Execute a task using the multi-agent system"""
            import uuid
            
            task_id = str(uuid.uuid4())
            
            # Create task record
            task_record = {
                "id": task_id,
                "description": task_request.description,
                "agent_name": task_request.agent_name,
                "workflow_name": task_request.workflow_name,
                "priority": task_request.priority,
                "metadata": task_request.metadata,
                "status": "pending",
                "created_at": datetime.now()
            }
            
            self.active_tasks[task_id] = task_record
            
            # Simulate task execution in background
            background_tasks.add_task(self._execute_task_background, task_id, task_request)
            
            return TaskResponse(
                task_id=task_id,
                status="pending",
                created_at=task_record["created_at"],
                description=task_request.description
            )
        
        @self.app.get("/tasks/{task_id}", response_model=TaskResult)
        async def get_task_result(task_id: str):
            """Get task execution result"""
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            elif task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return TaskResult(
                    task_id=task_id,
                    status=task["status"],
                    result="Task in progress...",
                    created_at=task["created_at"],
                    completed_at=None,
                    duration_seconds=None,
                    subtasks=[]
                )
            else:
                raise HTTPException(status_code=404, detail="Task not found")
        
        @self.app.get("/tasks", response_model=List[TaskResponse])
        async def list_tasks(status: Optional[str] = None, limit: int = Query(50, le=100)):
            """List recent tasks"""
            tasks = []
            
            # Add active tasks
            for task_id, task in self.active_tasks.items():
                if not status or task["status"] == status:
                    tasks.append(TaskResponse(
                        task_id=task_id,
                        status=task["status"],
                        created_at=task["created_at"],
                        description=task["description"]
                    ))
            
            # Add completed tasks
            for task_id, result in self.completed_tasks.items():
                if not status or result.status == status:
                    tasks.append(TaskResponse(
                        task_id=task_id,
                        status=result.status,
                        created_at=result.created_at,
                        description="Completed task"
                    ))
            
            # Sort by creation time and limit
            tasks.sort(key=lambda x: x.created_at, reverse=True)
            return tasks[:limit]
        
        @self.app.post("/agents/{agent_name}/chat", response_model=ConversationResponse)
        async def chat_with_agent(agent_name: str, conversation: AgentConversation):
            """Have a conversation with a specific agent"""
            import uuid
            
            # Simulate agent response
            responses = {
                "monitoring": f"I'm the monitoring agent. You asked: '{conversation.message}'. I can help you monitor websites and send alerts when they go down.",
                "planner": f"As the planning agent, I can help you break down '{conversation.message}' into actionable steps.",
                "dataagent": f"I'm the data agent. Regarding '{conversation.message}', I can help analyze data and generate insights.",
                "codeagent": f"I'm the code agent. For '{conversation.message}', I can help write and debug code.",
                "researchagent": f"As the research agent, I can help gather information about '{conversation.message}'.",
                "systemagent": f"I'm the system agent. For '{conversation.message}', I can help with system operations and monitoring."
            }
            
            response = responses.get(agent_name, f"Hello! I'm {agent_name}. You said: '{conversation.message}'")
            
            return ConversationResponse(
                agent_name=agent_name,
                response=response,
                conversation_id=str(uuid.uuid4()),
                timestamp=datetime.now()
            )
        
        @self.app.get("/system/stats")
        async def get_system_stats():
            """Get system statistics"""
            return {
                "timestamp": datetime.now().isoformat(),
                "agents": {
                    "count": 6,
                    "names": ["planner", "dataagent", "codeagent", "researchagent", "systemagent", "monitoring"]
                },
                "tasks": {
                    "active": len(self.active_tasks),
                    "completed": len(self.completed_tasks)
                },
                "memory": {
                    "total_memories": 0,
                    "by_agent": {}
                },
                "scheduler": {
                    "scheduler_running": True,
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0
                },
                "workflows": {
                    "available": ["website_monitoring", "data_analysis_pipeline", "software_development"],
                    "count": 3
                }
            }
        
        @self.app.post("/memory/store")
        async def store_memory(memory: MemoryEntry):
            """Store a memory entry (placeholder)"""
            import uuid
            memory_id = str(uuid.uuid4())
            return {"memory_id": memory_id, "status": "stored"}
        
        @self.app.post("/memory/query")
        async def query_memory(query: MemoryQuery):
            """Query agent memories (placeholder)"""
            return {
                "memories": [],
                "count": 0
            }
    
    async def _execute_task_background(self, task_id: str, task_request: TaskRequest):
        """Execute task in background (simulation)"""
        try:
            # Update status
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "running"
            
            start_time = datetime.now()
            
            # Simulate task execution delay
            await asyncio.sleep(2)
            
            # Simulate task result based on agent type
            if task_request.agent_name == "monitoring":
                result = f"Monitoring task completed: {task_request.description}. Websites checked successfully."
            elif task_request.agent_name == "dataagent":
                result = f"Data analysis completed: {task_request.description}. Found 0 issues in dataset."
            else:
                result = f"Task completed by {task_request.agent_name}: {task_request.description}"
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Store result
            task_result = TaskResult(
                task_id=task_id,
                status="completed",
                result=result,
                created_at=start_time,
                completed_at=end_time,
                duration_seconds=duration,
                subtasks=[]
            )
            
            self.completed_tasks[task_id] = task_result
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            
            # Store error result
            task_result = TaskResult(
                task_id=task_id,
                status="failed",
                result=f"Task failed: {str(e)}",
                created_at=self.active_tasks.get(task_id, {}).get("created_at", datetime.now()),
                completed_at=datetime.now(),
                duration_seconds=None,
                subtasks=[]
            )
            
            self.completed_tasks[task_id] = task_result
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

# Create API instance
def create_app() -> FastAPI:
    """Create the FastAPI application"""
    api = SimpleMultiAgentAPI()
    return api.app

# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.rest_server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )