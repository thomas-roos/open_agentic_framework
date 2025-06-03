# api/rest_server.py - Extensible API with dynamic workflow support

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import workflow registry
from workflows.registry import get_workflow_registry

logger = logging.getLogger(__name__)

# Pydantic models
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
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)

class WorkflowExecuteRequest(BaseModel):
    workflow_name: str = Field(..., description="Name of the workflow to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")

class WorkflowResponse(BaseModel):
    workflow_name: str
    status: str
    result: Dict[str, Any]
    executed_at: datetime

# Extensible API class
class ExtensibleMultiAgentAPI:
    """API that dynamically supports workflows through the registry"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Extensible Multi-Agent System",
            description="AI-powered multi-agent system with dynamic workflow support",
            version="2.0.0"
        )
        
        # Task tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        
        # Get workflow registry
        self.workflow_registry = get_workflow_registry()
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_dynamic_endpoints()
    
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
        """Setup core API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            workflow_health = await self.workflow_registry.health_check_all()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "api": "active",
                    "agents": 6,
                    "workflow_registry": "active",
                    "workflows": len(self.workflow_registry.workflows)
                },
                "workflow_health": workflow_health
            }
        
        @self.app.get("/agents")
        async def list_agents():
            """List available agents"""
            return {
                "monitoring": {
                    "name": "MonitoringAgent",
                    "role": "Website and Service Monitoring",
                    "capabilities": ["website_monitoring", "health_checks", "alerting"]
                },
                "planner": {
                    "name": "PlannerAgent", 
                    "role": "Strategic Planning",
                    "capabilities": ["task_decomposition", "workflow_planning"]
                },
                "dataagent": {
                    "name": "DataAgent",
                    "role": "Data Analysis",
                    "capabilities": ["data_analysis", "file_processing"]
                },
                "codeagent": {
                    "name": "CodeAgent",
                    "role": "Software Development",
                    "capabilities": ["code_generation", "debugging"]
                },
                "researchagent": {
                    "name": "ResearchAgent",
                    "role": "Information Gathering",
                    "capabilities": ["web_research", "document_analysis"]
                },
                "systemagent": {
                    "name": "SystemAgent",
                    "role": "System Operations",
                    "capabilities": ["command_execution", "system_monitoring"]
                }
            }
        
        # ============ WORKFLOW MANAGEMENT ENDPOINTS ============
        
        @self.app.get("/workflows")
        async def list_workflows(enabled_only: bool = Query(False, description="Show only enabled workflows")):
            """List all available workflows"""
            workflows = self.workflow_registry.list_workflows(enabled_only=enabled_only)
            return {
                "workflows": workflows,
                "total_count": len(workflows),
                "enabled_count": len([w for w in workflows.values() if w.get("enabled", False)])
            }
        
        @self.app.get("/workflows/{workflow_name}")
        async def get_workflow_info(workflow_name: str):
            """Get detailed information about a specific workflow"""
            workflow = self.workflow_registry.get_workflow(workflow_name)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return {
                "workflow": workflow.get_info(),
                "config": self.workflow_registry.workflow_configs.get(workflow_name, {}),
                "endpoints": self.workflow_registry.workflow_endpoints.get(workflow_name, [])
            }
        
        @self.app.post("/workflows/execute", response_model=WorkflowResponse)
        async def execute_workflow(request: WorkflowExecuteRequest):
            """Execute a workflow with given parameters"""
            try:
                result = await self.workflow_registry.execute_workflow(
                    request.workflow_name, 
                    **request.parameters
                )
                
                return WorkflowResponse(
                    workflow_name=request.workflow_name,
                    status="completed" if result.get("success", False) else "failed",
                    result=result,
                    executed_at=datetime.now()
                )
            
            except Exception as e:
                logger.error(f"Error executing workflow {request.workflow_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/workflows/{workflow_name}/enable")
        async def enable_workflow(workflow_name: str):
            """Enable a workflow"""
            success = self.workflow_registry.enable_workflow(workflow_name)
            if success:
                return {"message": f"Workflow '{workflow_name}' enabled successfully"}
            else:
                raise HTTPException(status_code=404, detail="Workflow not found")
        
        @self.app.post("/workflows/{workflow_name}/disable")
        async def disable_workflow(workflow_name: str):
            """Disable a workflow"""
            success = self.workflow_registry.disable_workflow(workflow_name)
            if success:
                return {"message": f"Workflow '{workflow_name}' disabled successfully"}
            else:
                raise HTTPException(status_code=404, detail="Workflow not found")
        
        @self.app.delete("/workflows/{workflow_name}")
        async def unregister_workflow(workflow_name: str):
            """Unregister a workflow"""
            success = self.workflow_registry.unregister_workflow(workflow_name)
            if success:
                return {"message": f"Workflow '{workflow_name}' unregistered successfully"}
            else:
                raise HTTPException(status_code=404, detail="Workflow not found")
        
        # ============ TASK MANAGEMENT ENDPOINTS ============
        
        @self.app.post("/tasks", response_model=TaskResponse)
        async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
            """Create and execute a task"""
            import uuid
            
            task_id = str(uuid.uuid4())
            
            task_record = {
                "id": task_id,
                "description": task_request.description,
                "agent_name": task_request.agent_name,
                "workflow_name": task_request.workflow_name,
                "status": "pending",
                "created_at": datetime.now()
            }
            
            self.active_tasks[task_id] = task_record
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
                    subtasks=[]
                )
            else:
                raise HTTPException(status_code=404, detail="Task not found")
        
        @self.app.get("/system/stats")
        async def get_system_stats():
            """Get comprehensive system statistics"""
            workflow_health = await self.workflow_registry.health_check_all()
            workflows = self.workflow_registry.list_workflows()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "agents": {"count": 6},
                "tasks": {
                    "active": len(self.active_tasks),
                    "completed": len(self.completed_tasks)
                },
                "workflows": {
                    "total": len(workflows),
                    "enabled": len([w for w in workflows.values() if w.get("enabled", False)]),
                    "health": workflow_health
                },
                "memory": {"total_memories": 0},
                "scheduler": {"scheduler_running": True}
            }
        
        # ============ WORKFLOW-SPECIFIC QUICK ACCESS ============
        
        @self.app.get("/monitoring/example")
        async def get_monitoring_example():
            """Get example of how to use website monitoring"""
            return {
                "workflow_name": "website_monitoring",
                "description": "Monitor websites and send email alerts",
                "example_request": {
                    "workflow_name": "website_monitoring",
                    "parameters": {
                        "url": "https://example.com",
                        "email_to": "alerts@example.com",
                        "email_from": "your-email@gmail.com",
                        "email_password": "your-app-password",
                        "check_interval": 300
                    }
                },
                "setup_instructions": {
                    "1": "Get Gmail app password: https://support.google.com/accounts/answer/185833",
                    "2": "Use your Gmail address as email_from",
                    "3": "Use the app password (not your regular password) as email_password",
                    "4": "Set check_interval in seconds (300 = 5 minutes)"
                },
                "curl_example": """curl -X POST "http://localhost:8080/workflows/execute" \\
     -H "Content-Type: application/json" \\
     -d '{
       "workflow_name": "website_monitoring",
       "parameters": {
         "url": "https://example.com",
         "email_to": "alerts@example.com",
         "email_from": "monitor@gmail.com",
         "email_password": "your-app-password",
         "check_interval": 300
       }
     }'"""
            }
    
    def _setup_dynamic_endpoints(self):
        """Setup dynamic endpoints from workflows"""
        # This method can be called to refresh dynamic endpoints
        # when new workflows are registered
        pass
    
    async def _execute_task_background(self, task_id: str, task_request: TaskRequest):
        """Execute task in background"""
        try:
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "running"
            
            start_time = datetime.now()
            
            # If workflow is specified, execute it
            if task_request.workflow_name:
                result = await self.workflow_registry.execute_workflow(
                    task_request.workflow_name,
                    **task_request.metadata
                )
                if result.get("success"):
                    result_text = f"Workflow '{task_request.workflow_name}' executed successfully: {result.get('message', '')}"
                else:
                    result_text = f"Workflow '{task_request.workflow_name}' failed: {result.get('error', 'Unknown error')}"
            else:
                # Simulate regular task execution
                await asyncio.sleep(2)
                
                if task_request.agent_name == "monitoring":
                    result_text = f"Monitoring task completed: {task_request.description}"
                else:
                    result_text = f"Task completed by {task_request.agent_name or 'system'}: {task_request.description}"
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            task_result = TaskResult(
                task_id=task_id,
                status="completed",
                result=result_text,
                created_at=start_time,
                completed_at=end_time,
                duration_seconds=duration,
                subtasks=[]
            )
            
            self.completed_tasks[task_id] = task_result
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            
            task_result = TaskResult(
                task_id=task_id,
                status="failed",
                result=f"Task failed: {str(e)}",
                created_at=self.active_tasks.get(task_id, {}).get("created_at", datetime.now()),
                completed_at=datetime.now(),
                subtasks=[]
            )
            
            self.completed_tasks[task_id] = task_result
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

def create_app() -> FastAPI:
    """Create the extensible FastAPI application"""
    api = ExtensibleMultiAgentAPI()
    return api.app

app = create_app()