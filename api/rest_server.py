# api/rest_server.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import asyncio
import uuid
from datetime import datetime, timedelta
import logging

# Import our multi-agent components
from ..memory.memory_system import MemoryManager, SQLiteMemorySystem
from ..scheduler.scheduler_system import TaskScheduler, SchedulerManager, ScheduledTask, ScheduleType
from ..agents.agent_system import MultiAgentOrchestrator
from ..workflow.workflow_engine import WorkflowEngine

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
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    subtasks: List[Dict[str, Any]]

class ScheduleTaskRequest(BaseModel):
    name: str
    description: str
    agent_name: str
    schedule_type: str = Field(..., description="'once', 'cron', or 'interval'")
    schedule_expression: str = Field(..., description="Cron expression, datetime ISO string, or interval in seconds")
    task_payload: Dict[str, Any]
    max_runs: Optional[int] = None
    timeout_seconds: int = 300

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

class AgentConversation(BaseModel):
    agent_name: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)

class ConversationResponse(BaseModel):
    agent_name: str
    response: str
    conversation_id: str
    timestamp: datetime

class APIError(BaseModel):
    error: str
    details: str
    timestamp: datetime

# Authentication (simple bearer token for demo)
security = HTTPBearer(auto_error=False)

class MultiAgentAPI:
    """REST API wrapper for the multi-agent system"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Multi-Agent System API",
            description="REST API for interacting with the multi-agent system",
            version="1.0.0"
        )
        
        # Initialize components
        self.memory_system = SQLiteMemorySystem("api_memory.db")
        self.memory_manager = MemoryManager(self.memory_system)
        self.scheduler = TaskScheduler("api_scheduler.db")
        self.scheduler_manager = SchedulerManager(self.scheduler)
        self.orchestrator = MultiAgentOrchestrator()
        
        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_results: Dict[str, TaskResult] = {}
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
        
        # Start background services
        self._start_background_services()
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "memory": "active",
                    "scheduler": "active" if self.scheduler.running else "inactive",
                    "agents": len(self.orchestrator.agents)
                }
            }
        
        # Task execution endpoints
        @self.app.post("/tasks", response_model=TaskResponse)
        async def execute_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
            """Execute a task using the multi-agent system"""
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
            
            # Execute task in background
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
            if task_id in self.task_results:
                return self.task_results[task_id]
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
            
            self.task_results[task_id] = task_result
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def _create_agent_task_handler(self, agent_name: str):
        """Create a task handler for scheduled tasks"""
        async def handler(task_payload: Dict[str, Any]) -> str:
            if agent_name not in self.orchestrator.agents:
                raise Exception(f"Agent {agent_name} not found")
            
            agent = self.orchestrator.agents[agent_name]
            
            # Create task from payload
            from ..agents.agent_system import Task
            task = Task(
                id=f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=task_payload.get("description", "Scheduled task"),
                agent=agent_name,
                metadata=task_payload.get("metadata", {})
            )
            
            # Execute task
            result = await agent.process_task(task)
            return result
        
        return handler
    
    def _start_background_services(self):
        """Start background services"""
        # Start scheduler in background
        asyncio.create_task(self.scheduler.start_scheduler())

# Main application factory
def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    api = MultiAgentAPI()
    return api.app

# For running with uvicorn
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
            for task_id, result in self.task_results.items():
                if not status or result.status == status:
                    tasks.append(TaskResponse(
                        task_id=task_id,
                        status=result.status,
                        created_at=result.created_at,
                        description="Completed task"  # Could store description in results
                    ))
            
            # Sort by creation time and limit
            tasks.sort(key=lambda x: x.created_at, reverse=True)
            return tasks[:limit]
        
        # Agent conversation endpoints
        @self.app.post("/agents/{agent_name}/chat", response_model=ConversationResponse)
        async def chat_with_agent(agent_name: str, conversation: AgentConversation):
            """Have a conversation with a specific agent"""
            if agent_name not in self.orchestrator.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            conversation_id = str(uuid.uuid4())
            
            # Get agent
            agent = self.orchestrator.agents[agent_name]
            
            # Create a simple task for the conversation
            from ..agents.agent_system import Task
            task = Task(
                id=conversation_id,
                description=conversation.message,
                agent=agent_name,
                metadata=conversation.context
            )
            
            # Process the message
            response = await agent.process_task(task)
            
            # Store conversation in memory
            await self.memory_manager.remember(
                agent_name=agent_name,
                content=f"User: {conversation.message}\nAgent: {response}",
                memory_type="conversation",
                metadata={
                    "conversation_id": conversation_id,
                    "user_message": conversation.message,
                    "agent_response": response,
                    "context": conversation.context
                },
                tags=["conversation", "chat"]
            )
            
            return ConversationResponse(
                agent_name=agent_name,
                response=response,
                conversation_id=conversation_id,
                timestamp=datetime.now()
            )
        
        @self.app.get("/agents")
        async def list_agents():
            """List available agents and their capabilities"""
            agents_info = {}
            for name, agent in self.orchestrator.agents.items():
                agents_info[name] = {
                    "name": agent.name,
                    "role": agent.role,
                    "capabilities": getattr(agent, 'capabilities', [])
                }
            return agents_info
        
        # Memory endpoints
        @self.app.post("/memory/store")
        async def store_memory(memory: MemoryEntry):
            """Store a memory entry"""
            memory_id = await self.memory_manager.remember(
                agent_name=memory.agent_name,
                content=memory.content,
                memory_type=memory.memory_type,
                metadata=memory.metadata,
                tags=memory.tags
            )
            return {"memory_id": memory_id, "status": "stored"}
        
        @self.app.post("/memory/query")
        async def query_memory(query: MemoryQuery):
            """Query agent memories"""
            memories = await self.memory_manager.recall(
                agent_name=query.agent_name,
                query=query.query,
                memory_type=query.memory_type,
                limit=query.limit
            )
            
            return {
                "memories": [
                    {
                        "id": memory.id,
                        "content": memory.content,
                        "memory_type": memory.memory_type,
                        "importance": memory.importance,
                        "created_at": memory.created_at.isoformat(),
                        "tags": memory.tags
                    }
                    for memory in memories
                ],
                "count": len(memories)
            }
        
        @self.app.get("/memory/stats/{agent_name}")
        async def get_memory_stats(agent_name: str):
            """Get memory statistics for an agent"""
            stats = await self.memory_system.get_memory_stats(agent_name)
            return stats
        
        # Scheduler endpoints
        @self.app.post("/schedule/task")
        async def schedule_task(schedule_request: ScheduleTaskRequest):
            """Schedule a task for future execution"""
            # Map schedule type
            schedule_type_map = {
                "once": ScheduleType.ONCE,
                "cron": ScheduleType.CRON,
                "interval": ScheduleType.INTERVAL
            }
            
            if schedule_request.schedule_type not in schedule_type_map:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid schedule_type. Must be 'once', 'cron', or 'interval'"
                )
            
            # Create scheduled task
            scheduled_task = ScheduledTask(
                id=str(uuid.uuid4()),
                name=schedule_request.name,
                description=schedule_request.description,
                schedule_type=schedule_type_map[schedule_request.schedule_type],
                schedule_expression=schedule_request.schedule_expression,
                agent_name=schedule_request.agent_name,
                task_payload=schedule_request.task_payload,
                max_runs=schedule_request.max_runs,
                timeout_seconds=schedule_request.timeout_seconds
            )
            
            # Register task handler if not already registered
            if schedule_request.agent_name not in self.scheduler.task_handlers:
                self.scheduler.register_task_handler(
                    schedule_request.agent_name,
                    self._create_agent_task_handler(schedule_request.agent_name)
                )
            
            task_id = await self.scheduler.schedule_task(scheduled_task)
            
            return {
                "task_id": task_id,
                "status": "scheduled",
                "next_run": scheduled_task.next_run.isoformat() if scheduled_task.next_run else None
            }
        
        @self.app.get("/schedule/tasks")
        async def list_scheduled_tasks(agent_name: Optional[str] = None):
            """List scheduled tasks"""
            tasks = await self.scheduler.get_scheduled_tasks(agent_name=agent_name)
            
            return {
                "tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "agent_name": task.agent_name,
                        "schedule_type": task.schedule_type.value,
                        "schedule_expression": task.schedule_expression,
                        "status": task.status.value,
                        "next_run": task.next_run.isoformat() if task.next_run else None,
                        "run_count": task.run_count
                    }
                    for task in tasks
                ]
            }
        
        @self.app.put("/schedule/tasks/{task_id}/pause")
        async def pause_scheduled_task(task_id: str):
            """Pause a scheduled task"""
            success = await self.scheduler.pause_task(task_id)
            if not success:
                raise HTTPException(status_code=404, detail="Task not found")
            return {"status": "paused"}
        
        @self.app.put("/schedule/tasks/{task_id}/resume")
        async def resume_scheduled_task(task_id: str):
            """Resume a paused scheduled task"""
            success = await self.scheduler.resume_task(task_id)
            if not success:
                raise HTTPException(status_code=404, detail="Task not found")
            return {"status": "resumed"}
        
        @self.app.delete("/schedule/tasks/{task_id}")
        async def cancel_scheduled_task(task_id: str):
            """Cancel a scheduled task"""
            success = await self.scheduler.cancel_task(task_id)
            if not success:
                raise HTTPException(status_code=404, detail="Task not found")
            return {"status": "cancelled"}
        
        @self.app.get("/schedule/executions/{task_id}")
        async def get_task_executions(task_id: str, limit: int = Query(50, le=100)):
            """Get execution history for a scheduled task"""
            executions = await self.scheduler.get_task_executions(task_id, limit)
            
            return {
                "executions": [
                    {
                        "execution_id": execution.execution_id,
                        "started_at": execution.started_at.isoformat(),
                        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                        "status": execution.status,
                        "duration_seconds": execution.duration_seconds,
                        "result": execution.result,
                        "error": execution.error
                    }
                    for execution in executions
                ]
            }
        
        # System information endpoints
        @self.app.get("/system/stats")
        async def get_system_stats():
            """Get system statistics"""
            scheduler_stats = await self.scheduler.get_scheduler_stats()
            
            return {
                "scheduler": scheduler_stats,
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.task_results),
                "agents": len(self.orchestrator.agents),
                "uptime": "N/A"  # Could track actual uptime
            }
        
        @self.app.get("/workflows")
        async def list_workflows():
            """List available workflows"""
            return {
                "workflows": list(self.orchestrator.workflow_engine.workflows.keys())
            }
    
    async def _execute_task_background(self, task_id: str, task_request: TaskRequest):
        """Execute task in background"""
        try:
            # Update status
            self.active_tasks[task_id]["status"] = "running"
            start_time = datetime.now()
            
            # Execute task
            result = await self.orchestrator.execute_task(
                description=task_request.description,
                workflow_name=task_request.workflow_name
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Store result
            task_result = TaskResult(
                task_id=task_id,
                status="completed",
                result=result.get("summary", "Task completed"),
                created_at=start_time,
                completed_at=end_time,
                duration_seconds=duration,
                subtasks=result.get("results", {})
            )
            
            self.task_results[task_id] = task_result
            
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
                created_at=self.active_tasks[task_id]["created_at"],
                completed_at=datetime.now(),
                duration_seconds=None,