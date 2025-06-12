"""
managers/memory_manager.py - Enhanced Database Management with Recurring Tasks

Added recurring task support:
- Database schema updates for recurring schedules
- Cron and simple pattern support
- Execution tracking and failure handling
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import logging
from croniter import croniter

logger = logging.getLogger(__name__)

Base = declarative_base()

class Agent(Base):
    """SQLAlchemy model for agents"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    role = Column(Text, nullable=False)
    goals = Column(Text, nullable=False)
    backstory = Column(Text, nullable=False)
    tools = Column(JSON, default=[])
    ollama_model = Column(String, default="llama3")
    enabled = Column(Boolean, default=True)
    input_schema = Column(JSON, default=None)
    tool_configs = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Tool(Base):
    """SQLAlchemy model for tools"""
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    parameters_schema = Column(JSON, nullable=False)
    class_name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Workflow(Base):
    """SQLAlchemy model for workflows"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    input_schema = Column(JSON, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MemoryEntry(Base):
    """SQLAlchemy model for memory entries"""
    __tablename__ = "memory_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, tool_output, thought
    content = Column(Text, nullable=False)
    entry_metadata = Column(JSON, default={})  # Fixed: renamed from 'metadata'
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class ScheduledTask(Base):
    """SQLAlchemy model for scheduled tasks with recurring support"""
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String, nullable=False)  # agent or workflow
    agent_name = Column(String, nullable=True)
    workflow_name = Column(String, nullable=True)
    task_description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    context = Column(JSON, default={})
    status = Column(String, default="pending")  # pending, completed, failed, disabled
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # NEW: Recurring task fields
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)  # cron expression or simple pattern
    recurrence_type = Column(String, nullable=True)  # 'cron' or 'simple'
    next_execution = Column(DateTime, nullable=True, index=True)
    last_execution = Column(DateTime, nullable=True)
    max_executions = Column(Integer, nullable=True)  # Optional limit
    execution_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    max_failures = Column(Integer, default=3)  # Stop after N failures
    enabled = Column(Boolean, default=True)

class TaskExecution(Base):
    """SQLAlchemy model for tracking individual task executions"""
    __tablename__ = "task_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    scheduled_task_id = Column(Integer, nullable=False, index=True)
    execution_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)  # completed, failed
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    execution_metadata = Column(JSON, default={})

class MemoryManager:
    """Enhanced memory manager with recurring task support"""
    
    def __init__(self, database_path: str):
        """
        Initialize memory manager
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.engine = create_engine(f"sqlite:///{database_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"Initialized enhanced memory manager with recurring tasks: {database_path}")
    
    def initialize_database(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully with recurring task support")
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    # Agent Management Methods (unchanged)
    def register_agent(
        self, 
        name: str, 
        role: str, 
        goals: str, 
        backstory: str, 
        tools: List[str] = None,
        ollama_model: str = "llama3",
        enabled: bool = True,
        tool_configs: Dict[str, Dict[str, Any]] = None
    ) -> int:
        """Register a new agent"""
        with self.get_session() as session:
            agent = Agent(
                name=name,
                role=role,
                goals=goals,
                backstory=backstory,
                tools=tools or [],
                ollama_model=ollama_model,
                enabled=enabled,
                tool_configs=tool_configs or {}
            )
            session.add(agent)
            session.commit()
            session.refresh(agent)
            logger.info(f"Registered agent: {name}")
            return agent.id
    
    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent by name"""
        with self.get_session() as session:
            agent = session.query(Agent).filter(Agent.name == name).first()
            if agent:
                return {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role,
                    "goals": agent.goals,
                    "backstory": agent.backstory,
                    "tools": agent.tools,
                    "ollama_model": agent.ollama_model,
                    "enabled": agent.enabled,
                    "tool_configs": agent.tool_configs,
                    "created_at": agent.created_at,
                    "updated_at": agent.updated_at
                }
            return None
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        with self.get_session() as session:
            agents = session.query(Agent).all()
            return [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role,
                    "goals": agent.goals,
                    "backstory": agent.backstory,
                    "tools": agent.tools,
                    "ollama_model": agent.ollama_model,
                    "enabled": agent.enabled,
                    "created_at": agent.created_at,
                    "updated_at": agent.updated_at
                }
                for agent in agents
            ]
    
    def update_agent(self, name: str, updates: Dict[str, Any]):
        """Update an agent"""
        with self.get_session() as session:
            agent = session.query(Agent).filter(Agent.name == name).first()
            if not agent:
                raise ValueError(f"Agent {name} not found")
            
            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            
            agent.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated agent: {name}")
    
    def delete_agent(self, name: str):
        """Delete an agent and its memory"""
        with self.get_session() as session:
            agent = session.query(Agent).filter(Agent.name == name).first()
            if not agent:
                raise ValueError(f"Agent {name} not found")
            
            # Also delete agent's memory
            session.query(MemoryEntry).filter(MemoryEntry.agent_name == name).delete()
            session.delete(agent)
            session.commit()
            logger.info(f"Deleted agent and memory: {name}")
    
    # Tool Management Methods (unchanged)
    def register_tool(
        self, 
        name: str, 
        description: str, 
        parameters_schema: Dict[str, Any],
        class_name: str,
        enabled: bool = True
    ) -> int:
        """Register a new tool"""
        with self.get_session() as session:
            # Check if tool already exists
            existing_tool = session.query(Tool).filter(Tool.name == name).first()
            if existing_tool:
                logger.debug(f"Tool {name} already exists")
                return existing_tool.id
            
            tool = Tool(
                name=name,
                description=description,
                parameters_schema=parameters_schema,
                class_name=class_name,
                enabled=enabled
            )
            session.add(tool)
            session.commit()
            session.refresh(tool)
            logger.info(f"Registered tool: {name}")
            return tool.id
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool by name"""
        with self.get_session() as session:
            tool = session.query(Tool).filter(Tool.name == name).first()
            if tool:
                return {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "parameters_schema": tool.parameters_schema,
                    "class_name": tool.class_name,
                    "enabled": tool.enabled,
                    "created_at": tool.created_at,
                    "updated_at": tool.updated_at
                }
            return None
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools"""
        with self.get_session() as session:
            tools = session.query(Tool).all()
            return [
                {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "parameters_schema": tool.parameters_schema,
                    "class_name": tool.class_name,
                    "enabled": tool.enabled,
                    "created_at": tool.created_at,
                    "updated_at": tool.updated_at
                }
                for tool in tools
            ]
    
    def update_tool(self, name: str, updates: Dict[str, Any]):
        """Update a tool"""
        with self.get_session() as session:
            tool = session.query(Tool).filter(Tool.name == name).first()
            if not tool:
                raise ValueError(f"Tool {name} not found")
            
            for key, value in updates.items():
                if hasattr(tool, key):
                    setattr(tool, key, value)
            
            tool.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated tool: {name}")
    
    def delete_tool(self, name: str):
        """Delete a tool"""
        with self.get_session() as session:
            tool = session.query(Tool).filter(Tool.name == name).first()
            if not tool:
                raise ValueError(f"Tool {name} not found")
            session.delete(tool)
            session.commit()
            logger.info(f"Deleted tool: {name}")
    
    # Workflow Management Methods (unchanged)
    def register_workflow(
        self, 
        name: str, 
        description: str, 
        steps: List[Dict[str, Any]],
        enabled: bool = True,
        input_schema: Dict[str, Any] = None
    ) -> int:
        """Register a new workflow"""
        with self.get_session() as session:
            workflow = Workflow(
                name=name,
                description=description,
                steps=steps,
                enabled=enabled,
                input_schema=input_schema
            )
            session.add(workflow)
            session.commit()
            session.refresh(workflow)
            logger.info(f"Registered workflow: {name}")
            return workflow.id
    
    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """Get workflow by name"""
        with self.get_session() as session:
            workflow = session.query(Workflow).filter(Workflow.name == name).first()
            if workflow:
                return {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "steps": workflow.steps,
                    "enabled": workflow.enabled,
                    "input_schema": workflow.input_schema,
                    "created_at": workflow.created_at,
                    "updated_at": workflow.updated_at
                }
            return None
    
    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows"""
        with self.get_session() as session:
            workflows = session.query(Workflow).all()
            return [
                {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "steps": workflow.steps,
                    "enabled": workflow.enabled,
                    "input_schema": workflow.input_schema,
                    "created_at": workflow.created_at,
                    "updated_at": workflow.updated_at
                }
                for workflow in workflows
            ]
    
    def update_workflow(self, name: str, updates: Dict[str, Any]):
        """Update a workflow"""
        with self.get_session() as session:
            workflow = session.query(Workflow).filter(Workflow.name == name).first()
            if not workflow:
                raise ValueError(f"Workflow {name} not found")
        
            for key, value in updates.items():
                if hasattr(workflow, key):
                    setattr(workflow, key, value)
        
            workflow.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated workflow: {name}")
    
    def delete_workflow(self, name: str):
        """Delete a workflow"""
        with self.get_session() as session:
            workflow = session.query(Workflow).filter(Workflow.name == name).first()
            if not workflow:
                raise ValueError(f"Workflow {name} not found")
            session.delete(workflow)
            session.commit()
            logger.info(f"Deleted workflow: {name}")
    
    # Memory Management Methods (unchanged)
    def add_memory_entry(
        self, 
        agent_name: str, 
        role: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ):
        """Add a memory entry"""
        with self.get_session() as session:
            memory_entry = MemoryEntry(
                agent_name=agent_name,
                role=role,
                content=content,
                entry_metadata=metadata or {}
            )
            session.add(memory_entry)
            session.commit()
    
    def get_agent_memory(self, agent_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get agent's memory/conversation history with limit"""
        with self.get_session() as session:
            memories = (
                session.query(MemoryEntry)
                .filter(MemoryEntry.agent_name == agent_name)
                .order_by(MemoryEntry.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": memory.id,
                    "agent_name": memory.agent_name,
                    "role": memory.role,
                    "content": memory.content,
                    "metadata": memory.entry_metadata,
                    "timestamp": memory.timestamp
                }
                for memory in reversed(memories)  # Return in chronological order
            ]
    
    # Memory cleanup methods (unchanged)
    def clear_agent_memory(self, agent_name: str):
        """Clear all memory entries for a specific agent"""
        with self.get_session() as session:
            deleted_count = (
                session.query(MemoryEntry)
                .filter(MemoryEntry.agent_name == agent_name)
                .delete()
            )
            session.commit()
            logger.info(f"Cleared {deleted_count} memory entries for agent {agent_name}")
            return deleted_count
    
    def clear_all_agent_memory(self):
        """Clear all memory entries for all agents"""
        with self.get_session() as session:
            deleted_count = session.query(MemoryEntry).delete()
            session.commit()
            logger.info(f"Cleared {deleted_count} total memory entries")
            return deleted_count
    
    def cleanup_agent_memory(self, agent_name: str, keep_last: int = 5):
        """Keep only the last N memory entries for an agent"""
        with self.get_session() as session:
            # Get all memory entries for the agent, ordered by timestamp desc
            all_entries = (
                session.query(MemoryEntry)
                .filter(MemoryEntry.agent_name == agent_name)
                .order_by(MemoryEntry.timestamp.desc())
                .all()
            )
            
            # If we have more entries than we want to keep
            if len(all_entries) > keep_last:
                entries_to_delete = all_entries[keep_last:]
                
                # Delete the older entries
                deleted_count = 0
                for entry in entries_to_delete:
                    session.delete(entry)
                    deleted_count += 1
                
                session.commit()
                logger.info(f"Cleaned up {deleted_count} old memory entries for agent {agent_name}, kept last {keep_last}")
                return deleted_count
            
            return 0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        with self.get_session() as session:
            total_entries = session.query(MemoryEntry).count()
            
            # Get memory count per agent
            agent_memory_counts = (
                session.query(MemoryEntry.agent_name, func.count(MemoryEntry.id))
                .group_by(MemoryEntry.agent_name)
                .all()
            )
            
            # Get oldest and newest entries
            oldest_entry = (
                session.query(MemoryEntry.timestamp)
                .order_by(MemoryEntry.timestamp.asc())
                .first()
            )
            
            newest_entry = (
                session.query(MemoryEntry.timestamp)
                .order_by(MemoryEntry.timestamp.desc())
                .first()
            )
            
            return {
                "total_memory_entries": total_entries,
                "agents_with_memory": len(agent_memory_counts),
                "memory_per_agent": {agent: count for agent, count in agent_memory_counts},
                "oldest_entry": oldest_entry[0] if oldest_entry else None,
                "newest_entry": newest_entry[0] if newest_entry else None
            }
    
    def cleanup_old_memory_entries(self, days_to_keep: int = 7):
        """Remove memory entries older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self.get_session() as session:
            deleted_count = (
                session.query(MemoryEntry)
                .filter(MemoryEntry.timestamp < cutoff_date)
                .delete()
            )
            session.commit()
            logger.info(f"Cleaned up {deleted_count} memory entries older than {days_to_keep} days")
            return deleted_count
    
    # ENHANCED: Scheduled Task Management with Recurring Support
    def schedule_task(
        self,
        task_type: str,
        scheduled_time: datetime,
        agent_name: str = None,
        workflow_name: str = None,
        task_description: str = None,
        context: Dict[str, Any] = None,
        is_recurring: bool = False,
        recurrence_pattern: str = None,
        recurrence_type: str = "simple",
        max_executions: int = None,
        max_failures: int = 3
    ) -> int:
        """Schedule a task for execution with optional recurring support"""
        with self.get_session() as session:
            # Calculate next execution time for recurring tasks
            next_execution = None
            if is_recurring and recurrence_pattern:
                next_execution = self._calculate_next_execution(
                    scheduled_time, recurrence_pattern, recurrence_type
                )
            
            task = ScheduledTask(
                task_type=task_type,
                agent_name=agent_name,
                workflow_name=workflow_name,
                task_description=task_description,
                scheduled_time=scheduled_time,
                context=context or {},
                is_recurring=is_recurring,
                recurrence_pattern=recurrence_pattern,
                recurrence_type=recurrence_type,
                next_execution=next_execution,
                max_executions=max_executions,
                max_failures=max_failures,
                enabled=True
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            log_msg = f"Scheduled {task_type} task for {scheduled_time}"
            if is_recurring:
                log_msg += f" (recurring: {recurrence_pattern})"
            logger.info(log_msg)
            return task.id
    
    def get_pending_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks scheduled for execution (including recurring)"""
        current_time = datetime.utcnow()
        with self.get_session() as session:
            # Get one-time pending tasks
            one_time_tasks = (
                session.query(ScheduledTask)
                .filter(
                    ScheduledTask.scheduled_time <= current_time,
                    ScheduledTask.status == "pending",
                    ScheduledTask.is_recurring == False,
                    ScheduledTask.enabled == True
                )
                .all()
            )
            
            # Get recurring tasks ready for execution
            recurring_tasks = (
                session.query(ScheduledTask)
                .filter(
                    ScheduledTask.next_execution <= current_time,
                    ScheduledTask.is_recurring == True,
                    ScheduledTask.enabled == True,
                    (ScheduledTask.max_executions.is_(None) | 
                     (ScheduledTask.execution_count < ScheduledTask.max_executions)),
                    ScheduledTask.failure_count < ScheduledTask.max_failures
                )
                .all()
            )
            
            all_tasks = one_time_tasks + recurring_tasks
            
            return [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "agent_name": task.agent_name,
                    "workflow_name": task.workflow_name,
                    "task_description": task.task_description,
                    "scheduled_time": task.scheduled_time,
                    "context": task.context,
                    "is_recurring": task.is_recurring,
                    "recurrence_pattern": task.recurrence_pattern,
                    "execution_count": task.execution_count
                }
                for task in all_tasks
            ]
    
    def get_all_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get all scheduled tasks"""
        with self.get_session() as session:
            tasks = session.query(ScheduledTask).order_by(ScheduledTask.scheduled_time).all()
            return [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "agent_name": task.agent_name,
                    "workflow_name": task.workflow_name,
                    "task_description": task.task_description,
                    "scheduled_time": task.scheduled_time,
                    "context": task.context,
                    "status": task.status,
                    "result": task.result,
                    "created_at": task.created_at,
                    "is_recurring": task.is_recurring,
                    "recurrence_pattern": task.recurrence_pattern,
                    "recurrence_type": task.recurrence_type,
                    "next_execution": task.next_execution,
                    "last_execution": task.last_execution,
                    "execution_count": task.execution_count,
                    "failure_count": task.failure_count,
                    "max_executions": task.max_executions,
                    "max_failures": task.max_failures,
                    "enabled": task.enabled
                }
                for task in tasks
            ]
    
    def update_scheduled_task_status(self, task_id: int, status: str, result: str = None):
        """Update scheduled task status and handle recurring logic"""
        with self.get_session() as session:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            execution_time = datetime.utcnow()
            
            # Create execution record
            execution = TaskExecution(
                scheduled_task_id=task_id,
                execution_time=execution_time,
                status=status,
                result=result,
                error_message=result if status == "failed" else None
            )
            session.add(execution)
            
            # Update task execution count and last execution
            task.execution_count += 1
            task.last_execution = execution_time
            
            if status == "completed":
                task.failure_count = 0  # Reset failure count on success
                if not task.is_recurring:
                    task.status = "completed"
                    task.result = result
                else:
                    # Calculate next execution for recurring task
                    if (task.max_executions is None or 
                        task.execution_count < task.max_executions):
                        next_exec = self._calculate_next_execution(
                            execution_time, 
                            task.recurrence_pattern, 
                            task.recurrence_type
                        )
                        task.next_execution = next_exec
                        logger.info(f"Recurring task {task_id} scheduled for next execution: {next_exec}")
                    else:
                        task.enabled = False
                        task.status = "completed"
                        logger.info(f"Recurring task {task_id} reached max executions ({task.max_executions})")
            
            elif status == "failed":
                task.failure_count += 1
                if not task.is_recurring:
                    task.status = "failed"
                    task.result = result
                else:
                    # Check if we should disable due to too many failures
                    if task.failure_count >= task.max_failures:
                        task.enabled = False
                        task.status = "failed"
                        logger.error(f"Recurring task {task_id} disabled after {task.failure_count} failures")
                    else:
                        # Still try next execution for recurring task
                        next_exec = self._calculate_next_execution(
                            execution_time,
                            task.recurrence_pattern,
                            task.recurrence_type
                        )
                        task.next_execution = next_exec
                        logger.warning(f"Recurring task {task_id} failed ({task.failure_count}/{task.max_failures}), next attempt: {next_exec}")
            
            session.commit()
            logger.info(f"Updated task {task_id} status to {status}")
    
    def delete_scheduled_task(self, task_id: int):
        """Delete a scheduled task and its execution history"""
        with self.get_session() as session:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                raise ValueError(f"Scheduled task {task_id} not found")
            
            # Delete execution history
            session.query(TaskExecution).filter(TaskExecution.scheduled_task_id == task_id).delete()
            
            # Delete the task
            session.delete(task)
            session.commit()
            logger.info(f"Deleted scheduled task: {task_id}")
    
    def enable_scheduled_task(self, task_id: int):
        """Enable a scheduled task"""
        with self.get_session() as session:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                raise ValueError(f"Scheduled task {task_id} not found")
            
            task.enabled = True
            if task.is_recurring and task.next_execution is None:
                # Recalculate next execution
                task.next_execution = self._calculate_next_execution(
                    datetime.utcnow(),
                    task.recurrence_pattern,
                    task.recurrence_type
                )
            session.commit()
            logger.info(f"Enabled scheduled task: {task_id}")
    
    def disable_scheduled_task(self, task_id: int):
        """Disable a scheduled task"""
        with self.get_session() as session:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                raise ValueError(f"Scheduled task {task_id} not found")
            
            task.enabled = False
            session.commit()
            logger.info(f"Disabled scheduled task: {task_id}")
    
    def get_task_executions(self, task_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history for a task"""
        with self.get_session() as session:
            executions = (
                session.query(TaskExecution)
                .filter(TaskExecution.scheduled_task_id == task_id)
                .order_by(TaskExecution.execution_time.desc())
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "id": execution.id,
                    "execution_time": execution.execution_time,
                    "status": execution.status,
                    "result": execution.result,
                    "error_message": execution.error_message,
                    "duration_seconds": execution.duration_seconds
                }
                for execution in executions
            ]
    
    def _calculate_next_execution(
        self, 
        base_time: datetime, 
        pattern: str, 
        pattern_type: str
    ) -> datetime:
        """Calculate next execution time based on recurrence pattern"""
        try:
            if pattern_type == "cron":
                # Use croniter for cron expressions
                cron = croniter(pattern, base_time)
                return cron.get_next(datetime)
            
            elif pattern_type == "simple":
                # Handle simple patterns like "5m", "1h", "1d"
                return self._parse_simple_pattern(base_time, pattern)
            
            else:
                raise ValueError(f"Unknown recurrence type: {pattern_type}")
                
        except Exception as e:
            logger.error(f"Error calculating next execution: {e}")
            # Fallback to 1 hour
            return base_time + timedelta(hours=1)
    
    def _parse_simple_pattern(self, base_time: datetime, pattern: str) -> datetime:
        """Parse simple patterns like '5m', '2h', '1d'"""
        pattern = pattern.strip().lower()
        
        if pattern.endswith('m'):
            # Minutes
            minutes = int(pattern[:-1])
            return base_time + timedelta(minutes=minutes)
        elif pattern.endswith('h'):
            # Hours
            hours = int(pattern[:-1])
            return base_time + timedelta(hours=hours)
        elif pattern.endswith('d'):
            # Days
            days = int(pattern[:-1])
            return base_time + timedelta(days=days)
        else:
            raise ValueError(f"Invalid simple pattern: {pattern}")
    
    def validate_recurrence_pattern(self, pattern: str, pattern_type: str) -> bool:
        """Validate a recurrence pattern"""
        try:
            if pattern_type == "cron":
                # Test cron expression
                croniter(pattern)
                return True
            elif pattern_type == "simple":
                # Test simple pattern
                self._parse_simple_pattern(datetime.utcnow(), pattern)
                return True
            else:
                return False
        except:
            return False