"""
models.py - Enhanced Pydantic Data Models with Recurring Task Support

Added new models for:
- Recurring task scheduling
- Task execution tracking
- Enhanced scheduling with cron and simple patterns
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from datetime import datetime, timezone


# Agent Models (existing, unchanged)
class AgentDefinition(BaseModel):
    """Model for creating a new agent"""
    name: str = Field(..., description="Unique agent name")
    role: str = Field(..., description="Agent's role description")
    goals: str = Field(..., description="Agent's goals and objectives")
    backstory: str = Field(..., description="Agent's background story")
    tools: List[str] = Field(default=[], description="List of tool names the agent can use")
    ollama_model: str = Field(default="granite3.2:2b", description="Preferred LLM model")
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

# Tool Models (existing, unchanged)
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

# Workflow Models (existing, unchanged)
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
    use_previous_output: Optional[bool] = Field(
        default=False, description="Whether to use previous step output as input"
    )

class WorkflowDefinition(BaseModel):
    """Model for creating a new workflow"""
    name: str = Field(..., description="Unique workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[WorkflowStep] = Field(..., description="List of workflow steps")
    enabled: bool = Field(default=True, description="Whether the workflow is enabled")
    input_schema: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="JSON schema defining workflow input parameters"
    )

class WorkflowUpdate(BaseModel):
    """Model for updating an existing workflow"""
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    enabled: Optional[bool] = None
    input_schema: Optional[Dict[str, Any]] = None

class WorkflowInfo(BaseModel):
    """Model for workflow information response"""
    id: int
    name: str
    description: str
    steps: List[WorkflowStep]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    input_schema: Optional[Dict[str, Any]] = None

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

# ENHANCED: Scheduling Models with Recurring Support
class TaskType(str, Enum):
    """Enumeration of task types"""
    AGENT = "agent"
    WORKFLOW = "workflow"

class RecurrenceType(str, Enum):
    """Enumeration of recurrence types"""
    SIMPLE = "simple"
    CRON = "cron"

class ScheduledTaskDefinition(BaseModel):
    """Model for creating a scheduled task with recurring support"""
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
    
    # Recurring task fields with proper defaults
    is_recurring: bool = Field(default=False, description="Whether this is a recurring task")
    recurrence_pattern: Optional[str] = Field(
        default=None, 
        description="Recurrence pattern (e.g., '5m', '1h', '0 */6 * * *')"
    )
    recurrence_type: Optional[RecurrenceType] = Field(
        default=RecurrenceType.SIMPLE, 
        description="Type of recurrence pattern"
    )
    max_executions: Optional[int] = Field(
        default=None, 
        description="Maximum number of executions (None for unlimited)",
        ge=1
    )
    max_failures: int = Field(
        default=3, 
        description="Maximum consecutive failures before disabling",
        ge=1,
        le=10
    )

    @validator('recurrence_pattern')
    def validate_recurrence_pattern(cls, v, values):
        """Validate recurrence pattern based on type"""
        if values.get('is_recurring') and not v:
            raise ValueError('recurrence_pattern is required for recurring tasks')
        
        if v and values.get('recurrence_type') == RecurrenceType.SIMPLE:
            # Validate simple patterns like "5m", "2h", "1d"
            import re
            if not re.match(r'^\d+[mhd]$', v.lower()):
                raise ValueError('Simple pattern must be in format: number + m/h/d (e.g., "5m", "2h", "1d")')
        
        return v
    
    @validator('agent_name')
    def validate_agent_name(cls, v, values):
        """Validate agent_name is provided for agent tasks"""
        if values.get('task_type') == TaskType.AGENT and not v:
            raise ValueError('agent_name is required for agent tasks')
        return v
    
    @validator('workflow_name')
    def validate_workflow_name(cls, v, values):
        """Validate workflow_name is provided for workflow tasks"""
        if values.get('task_type') == TaskType.WORKFLOW and not v:
            raise ValueError('workflow_name is required for workflow tasks')
        return v

    class Config:
        # Allow extra fields for future compatibility
        extra = "forbid"
        # Ensure proper JSON serialization
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScheduledTaskUpdate(BaseModel):
    """Model for updating a scheduled task"""
    task_description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    recurrence_type: Optional[RecurrenceType] = None
    max_executions: Optional[int] = Field(default=None, ge=1)
    max_failures: Optional[int] = Field(default=None, ge=1, le=10)
    enabled: Optional[bool] = None

class ScheduledTaskInfo(BaseModel):
    """Model for scheduled task information with recurring details"""
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
    
    # NEW: Recurring task info
    is_recurring: bool
    recurrence_pattern: Optional[str]
    recurrence_type: Optional[str]
    next_execution: Optional[datetime]
    last_execution: Optional[datetime]
    execution_count: int
    failure_count: int
    max_executions: Optional[int]
    max_failures: int
    enabled: bool

class TaskExecutionInfo(BaseModel):
    """Model for individual task execution information"""
    id: int
    execution_time: datetime
    status: str
    result: Optional[str]
    error_message: Optional[str]
    duration_seconds: Optional[int]

class ScheduleResponse(BaseModel):
    """Model for schedule operation response"""
    id: int
    message: str
    is_recurring: bool = False
    next_execution: Optional[datetime] = None

# Memory Models (existing, unchanged)
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

# Model Info and Status Models (existing, unchanged)
class ModelInfo(BaseModel):
    """Model for Ollama model information"""
    name: str = Field(..., description="Model name")
    size: Optional[str] = Field(default=None, description="Model size")
    modified_at: Optional[datetime] = Field(default=None, description="Last modified date")
    digest: Optional[str] = Field(default=None, description="Model digest/hash")

class ModelsStatusResponse(BaseModel):
    """Model for models status response"""
    ollama_healthy: bool = Field(..., description="Whether Ollama is accessible")
    total_models: int = Field(..., description="Total number of available models")
    available_models: List[str] = Field(..., description="List of available model names")
    default_model: str = Field(..., description="Default model configured")
    recommended_models: List[str] = Field(..., description="Recommended models for production")

# Memory Management Models (existing, unchanged)
class MemoryStatsResponse(BaseModel):
    """Model for memory statistics response"""
    total_memory_entries: int = Field(..., description="Total memory entries across all agents")
    agents_with_memory: int = Field(..., description="Number of agents with memory")
    memory_per_agent: Dict[str, int] = Field(..., description="Memory count per agent")
    oldest_entry: Optional[datetime] = Field(default=None, description="Timestamp of oldest entry")
    newest_entry: Optional[datetime] = Field(default=None, description="Timestamp of newest entry")

class MemoryCleanupRequest(BaseModel):
    """Model for memory cleanup request"""
    keep_last: int = Field(default=5, description="Number of recent entries to keep per agent", ge=1, le=50)

class MemoryCleanupResponse(BaseModel):
    """Model for memory cleanup response"""
    message: str = Field(..., description="Cleanup result message")
    agents_processed: int = Field(..., description="Number of agents processed")
    kept_entries_per_agent: int = Field(..., description="Number of entries kept per agent")

# Enhanced Configuration Models (existing, unchanged)
class ConfigUpdate(BaseModel):
    """Model for updating configuration"""
    ollama_url: Optional[str] = None
    default_model: Optional[str] = None
    max_agent_iterations: Optional[int] = Field(default=None, ge=1, le=10)
    scheduler_interval: Optional[int] = Field(default=None, ge=30)
    max_agent_memory_entries: Optional[int] = Field(default=None, ge=1, le=100)
    clear_memory_on_startup: Optional[bool] = None
    memory_cleanup_interval: Optional[int] = Field(default=None, ge=300)
    memory_retention_days: Optional[int] = Field(default=None, ge=1, le=365)

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
    max_agent_memory_entries: int
    clear_memory_on_startup: bool
    memory_cleanup_interval: int
    memory_retention_days: int

class MemoryConfigUpdate(BaseModel):
    """Model for updating only memory-related configuration"""
    max_agent_memory_entries: Optional[int] = Field(default=None, ge=1, le=100)
    clear_memory_on_startup: Optional[bool] = None
    memory_cleanup_interval: Optional[int] = Field(default=None, ge=300)
    memory_retention_days: Optional[int] = Field(default=None, ge=1, le=365)

# Enhanced Health Check (existing, unchanged)
class HealthCheckResponse(BaseModel):
    """Enhanced health check response"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    ollama_status: bool = Field(..., description="Ollama service status")
    memory_entries: int = Field(..., description="Total memory entries in system")
    version: str = Field(default="1.2.0", description="Framework version")

# Agent Status Model (existing, unchanged)
class AgentStatusResponse(BaseModel):
    """Model for detailed agent status"""
    status: str = Field(..., description="Agent status: active, disabled, or not_found")
    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role")
    tools: List[str] = Field(..., description="Available tools")
    model: str = Field(..., description="LLM model being used")
    recent_activity: int = Field(..., description="Number of recent memory entries")
    total_memory_entries: int = Field(..., description="Total memory entries for this agent")
    memory_limit: int = Field(..., description="Memory limit configured for agents")
    last_update: datetime = Field(..., description="Last time agent was updated")

# Generic Response Models (existing, unchanged)
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None

# Batch Operations Models (existing, unchanged)
class BatchAgentCleanupRequest(BaseModel):
    """Model for batch agent memory cleanup"""
    agent_names: Optional[List[str]] = Field(default=None, description="Specific agents to cleanup, or all if None")
    keep_last: int = Field(default=5, description="Number of entries to keep", ge=1, le=50)

class BatchAgentCleanupResponse(BaseModel):
    """Model for batch cleanup response"""
    message: str
    agents_processed: int
    total_entries_removed: int
    agents_details: Dict[str, int]  # agent_name -> entries_removed

# System Statistics (existing, unchanged)
class SystemStatsResponse(BaseModel):
    """Model for comprehensive system statistics"""
    framework_version: str = Field(default="1.2.0")
    uptime_info: Dict[str, Any]
    agents: Dict[str, Any]
    tools: Dict[str, Any] 
    workflows: Dict[str, Any]
    memory: MemoryStatsResponse
    ollama: ModelsStatusResponse
    scheduled_tasks: Dict[str, Any]

class ModelInstallRequest(BaseModel):
    """Model for installing a new model"""
    model_name: str = Field(..., description="Name of the model to install")
    wait_for_completion: bool = Field(default=True, description="Wait for installation to complete")

class ModelDeleteRequest(BaseModel):
    """Model for deleting a model"""
    model_name: str = Field(..., description="Name of the model to delete")

# NEW: Recurring Task Utilities
class RecurrencePatternHelper(BaseModel):
    """Helper model for recurrence pattern validation and suggestions"""
    pattern: str
    pattern_type: RecurrenceType
    description: str
    next_execution_preview: Optional[datetime] = None

class RecurrencePatternSuggestions(BaseModel):
    """Model for suggesting common recurrence patterns"""
    simple_patterns: List[RecurrencePatternHelper]
    cron_patterns: List[RecurrencePatternHelper]

# NEW: Enhanced Task Statistics
class TaskStatistics(BaseModel):
    """Model for task execution statistics"""
    total_tasks: int
    one_time_tasks: int
    recurring_tasks: int
    active_recurring: int
    disabled_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: Optional[float] = None