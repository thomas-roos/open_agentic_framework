"""
models.py - Pydantic Data Models

Defines all data structures for API requests and responses using Pydantic.
These models provide type safety and automatic validation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# Agent Models
class AgentDefinition(BaseModel):
    """Model for creating a new agent"""
    name: str = Field(..., description="Unique agent name")
    role: str = Field(..., description="Agent's role description")
    goals: str = Field(..., description="Agent's goals and objectives")
    backstory: str = Field(..., description="Agent's background story")
    tools: List[str] = Field(default=[], description="List of tool names the agent can use")
    ollama_model: str = Field(default="llama3", description="Preferred LLM model")
    enabled: bool = Field(default=True, description="Whether the agent is enabled")
    tool_configs: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None, description="Tool-specific configurations"
    )

class AgentUpdate(BaseModel):
    """Model for updating an existing agent"""
    role: Optional[str] = None
    goals: Optional[str] = None
    backstory: Optional[str] = None
    tools: Optional[List[str]] = None
    ollama_model: Optional[str] = None
    enabled: Optional[bool] = None
    tool_configs: Optional[Dict[str, Dict[str, Any]]] = None

class AgentInfo(BaseModel):
    """Model for agent information response"""
    id: int
    name: str
    role: str
    goals: str
    backstory: str
    tools: List[str]
    ollama_model: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

class AgentExecutionRequest(BaseModel):
    """Model for agent execution request"""
    task: str = Field(..., description="Task description for the agent")
    context: Optional[Dict[str, Any]] = Field(
        default={}, description="Execution context"
    )

class AgentExecutionResponse(BaseModel):
    """Model for agent execution response"""
    agent_name: str
    task: str
    result: str
    timestamp: datetime

class AgentResponse(BaseModel):
    """Model for agent creation/operation response"""
    id: int
    name: str
    message: str

# Tool Models
class ToolRegistration(BaseModel):
    """Model for registering a new tool"""
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Tool description")
    parameters_schema: Dict[str, Any] = Field(
        ..., description="JSON schema for tool parameters"
    )
    class_name: str = Field(..., description="Python class name for the tool")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")

class ToolUpdate(BaseModel):
    """Model for updating an existing tool"""
    description: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None

class ToolInfo(BaseModel):
    """Model for tool information response"""
    id: int
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    class_name: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

class ToolExecutionRequest(BaseModel):
    """Model for tool execution request"""
    parameters: Dict[str, Any] = Field(..., description="Tool execution parameters")
    agent_name: Optional[str] = Field(
        default=None, description="Agent name for context"
    )

class ToolExecutionResponse(BaseModel):
    """Model for tool execution response"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    timestamp: datetime

class ToolResponse(BaseModel):
    """Model for tool creation/operation response"""
    id: int
    name: str
    message: str

# Workflow Models
class WorkflowStep(BaseModel):
    """Model for a single workflow step"""
    type: str = Field(..., description="Step type: 'agent' or 'tool'")
    name: str = Field(..., description="Agent or tool name")
    task: Optional[str] = Field(
        default=None, description="Task description for agent steps"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default={}, description="Parameters for tool steps"
    )
    context_key: Optional[str] = Field(
        default=None, description="Key to store result in context"
    )

class WorkflowDefinition(BaseModel):
    """Model for creating a new workflow"""
    name: str = Field(..., description="Unique workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStep] = Field(..., description="List of workflow steps")
    enabled: bool = Field(default=True, description="Whether the workflow is enabled")

class WorkflowUpdate(BaseModel):
    """Model for updating an existing workflow"""
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    enabled: Optional[bool] = None

class WorkflowInfo(BaseModel):
    """Model for workflow information response"""
    id: int
    name: str
    description: str
    steps: List[WorkflowStep]
    enabled: bool
    created_at: datetime
    updated_at: datetime

class WorkflowExecutionRequest(BaseModel):
    """Model for workflow execution request"""
    context: Optional[Dict[str, Any]] = Field(
        default={}, description="Initial workflow context"
    )

class WorkflowExecutionResponse(BaseModel):
    """Model for workflow execution response"""
    workflow_name: str
    context: Dict[str, Any]
    result: Any
    timestamp: datetime

class WorkflowResponse(BaseModel):
    """Model for workflow creation/operation response"""
    id: int
    name: str
    message: str

# Scheduling Models
class TaskType(str, Enum):
    """Enumeration of task types"""
    AGENT = "agent"
    WORKFLOW = "workflow"

class ScheduledTaskDefinition(BaseModel):
    """Model for creating a scheduled task"""
    task_type: TaskType = Field(..., description="Type of task to schedule")
    agent_name: Optional[str] = Field(
        default=None, description="Agent name for agent tasks"
    )
    workflow_name: Optional[str] = Field(
        default=None, description="Workflow name for workflow tasks"
    )
    task_description: Optional[str] = Field(
        default=None, description="Task description for agent tasks"
    )
    scheduled_time: datetime = Field(..., description="When to execute the task")
    context: Optional[Dict[str, Any]] = Field(
        default={}, description="Execution context"
    )

class ScheduledTaskInfo(BaseModel):
    """Model for scheduled task information"""
    id: int
    task_type: str
    agent_name: Optional[str]
    workflow_name: Optional[str]
    task_description: Optional[str]
    scheduled_time: datetime
    context: Dict[str, Any]
    status: str
    result: Optional[str]
    created_at: datetime

class ScheduleResponse(BaseModel):
    """Model for schedule operation response"""
    id: int
    message: str

# Memory Models
class MemoryEntry(BaseModel):
    """Model for a memory entry"""
    agent_name: str
    role: str = Field(..., description="user, assistant, tool_output, or thought")
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default={})

class MemoryEntryResponse(BaseModel):
    """Model for memory entry response"""
    id: int
    agent_name: str
    role: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime

# Configuration Models
class ConfigUpdate(BaseModel):
    """Model for updating configuration"""
    ollama_url: Optional[str] = None
    default_model: Optional[str] = None
    max_agent_iterations: Optional[int] = None
    scheduler_interval: Optional[int] = None

class ConfigResponse(BaseModel):
    """Model for configuration response"""
    ollama_url: str
    default_model: str
    database_path: str
    api_host: str
    api_port: int
    max_agent_iterations: int
    scheduler_interval: int
    tools_directory: str

# Generic Response Models
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None