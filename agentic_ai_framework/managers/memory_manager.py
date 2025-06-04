"""
managers/memory_manager.py - Database Management (FIXED)

Manages SQLite database operations for persistent storage using SQLAlchemy ORM.
Handles agents, tools, workflows, memory entries, and scheduled tasks.

FIXED: Renamed 'metadata' column to 'entry_metadata' to avoid SQLAlchemy conflict.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MemoryEntry(Base):
    """SQLAlchemy model for memory entries - FIXED: renamed metadata to entry_metadata"""
    __tablename__ = "memory_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, tool_output, thought
    content = Column(Text, nullable=False)
    entry_metadata = Column(JSON, default={})  # FIXED: renamed from 'metadata'
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class ScheduledTask(Base):
    """SQLAlchemy model for scheduled tasks"""
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String, nullable=False)  # agent or workflow
    agent_name = Column(String, nullable=True)
    workflow_name = Column(String, nullable=True)
    task_description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    context = Column(JSON, default={})
    status = Column(String, default="pending")  # pending, completed, failed
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MemoryManager:
    """Manages SQLite database operations for persistent storage"""
    
    def __init__(self, database_path: str):
        """
        Initialize memory manager
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.engine = create_engine(f"sqlite:///{database_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"Initialized memory manager with database: {database_path}")
    
    def initialize_database(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    # Agent Management Methods
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
        """
        Register a new agent
        
        Args:
            name: Agent name
            role: Agent role
            goals: Agent goals
            backstory: Agent backstory
            tools: List of tool names
            ollama_model: LLM model to use
            enabled: Whether agent is enabled
            tool_configs: Tool-specific configurations
            
        Returns:
            Agent ID
        """
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
        """Delete an agent"""
        with self.get_session() as session:
            agent = session.query(Agent).filter(Agent.name == name).first()
            if not agent:
                raise ValueError(f"Agent {name} not found")
            session.delete(agent)
            session.commit()
            logger.info(f"Deleted agent: {name}")
    
    # Tool Management Methods
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
    
    # Workflow Management Methods
    def register_workflow(
        self, 
        name: str, 
        description: str, 
        steps: List[Dict[str, Any]],
        enabled: bool = True
    ) -> int:
        """Register a new workflow"""
        with self.get_session() as session:
            workflow = Workflow(
                name=name,
                description=description,
                steps=steps,
                enabled=enabled
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
    
    # Memory Management Methods - FIXED: using entry_metadata
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
                entry_metadata=metadata or {}  # FIXED: using entry_metadata
            )
            session.add(memory_entry)
            session.commit()
    
    def get_agent_memory(self, agent_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get agent's memory/conversation history"""
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
                    "metadata": memory.entry_metadata,  # FIXED: using entry_metadata
                    "timestamp": memory.timestamp
                }
                for memory in reversed(memories)  # Return in chronological order
            ]
    
    # Scheduled Task Management Methods
    def schedule_task(
        self,
        task_type: str,
        scheduled_time: datetime,
        agent_name: str = None,
        workflow_name: str = None,
        task_description: str = None,
        context: Dict[str, Any] = None
    ) -> int:
        """Schedule a task for execution"""
        with self.get_session() as session:
            task = ScheduledTask(
                task_type=task_type,
                agent_name=agent_name,
                workflow_name=workflow_name,
                task_description=task_description,
                scheduled_time=scheduled_time,
                context=context or {}
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.info(f"Scheduled {task_type} task for {scheduled_time}")
            return task.id
    
    def get_pending_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks scheduled for execution"""
        current_time = datetime.utcnow()
        with self.get_session() as session:
            tasks = (
                session.query(ScheduledTask)
                .filter(
                    ScheduledTask.scheduled_time <= current_time,
                    ScheduledTask.status == "pending"
                )
                .all()
            )
            return [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "agent_name": task.agent_name,
                    "workflow_name": task.workflow_name,
                    "task_description": task.task_description,
                    "scheduled_time": task.scheduled_time,
                    "context": task.context
                }
                for task in tasks
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
                    "created_at": task.created_at
                }
                for task in tasks
            ]
    
    def update_scheduled_task_status(self, task_id: int, status: str, result: str = None):
        """Update scheduled task status"""
        with self.get_session() as session:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if task:
                task.status = status
                if result:
                    task.result = result
                session.commit()
                logger.info(f"Updated task {task_id} status to {status}")
    
    def delete_scheduled_task(self, task_id: int):
        """Delete a scheduled task"""
        with self.get_session() as session:
            task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task:
                raise ValueError(f"Scheduled task {task_id} not found")
            session.delete(task)
            session.commit()
            logger.info(f"Deleted scheduled task: {task_id}")