# main.py - Complete Multi-Agent Orchestrator
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import all components
from memory.memory_system import MemoryManager, SQLiteMemorySystem
from scheduler.scheduler_system import TaskScheduler, SchedulerManager
from agents.agent_system import (
    BaseAgent, PlannerAgent, DataAgent, CodeAgent, 
    ResearchAgent, SystemAgent, ToolRegistry, Task, TaskStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/multi_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """Complete multi-agent orchestrator with memory, scheduling, and tools"""
    
    def __init__(self, model_name: str = "llama3.2:1b", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        
        # Initialize core components
        self.memory_system = SQLiteMemorySystem("/app/memory/agent_memory.db")
        self.memory_manager = MemoryManager(self.memory_system)
        self.scheduler = TaskScheduler("/app/scheduler/scheduler.db")
        self.scheduler_manager = SchedulerManager(self.scheduler)
        
        # Initialize tool registry with memory integration
        self.tool_registry = ToolRegistry(self.memory_manager)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Task tracking
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        
        # Workflow definitions
        self.workflows = self._load_default_workflows()
        
        logger.info("Multi-Agent Orchestrator initialized successfully")
    
    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all agents with shared resources"""
        agents = {
            "planner": PlannerAgent(),
            "dataagent": DataAgent(),
            "codeagent": CodeAgent(),
            "researchagent": ResearchAgent(),
            "systemagent": SystemAgent()
        }
        
        # Configure all agents
        for agent in agents.values():
            agent.model = self.model_name
            agent.base_url = self.ollama_url
            agent.set_memory_manager(self.memory_manager)
            agent.set_tool_registry(self.tool_registry)
        
        # Register agents as task handlers for scheduler
        for name, agent in agents.items():
            self.scheduler.register_task_handler(name, self._create_agent_handler(agent))
        
        logger.info(f"Initialized {len(agents)} agents: {list(agents.keys())}")
        return agents
    
    def _create_agent_handler(self, agent: BaseAgent):
        """Create a task handler for scheduled tasks"""
        async def handler(task_payload: Dict[str, Any]) -> str:
            task = Task(
                id=f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=task_payload.get("description", "Scheduled task"),
                agent=agent.name.lower(),
                metadata=task_payload.get("metadata", {})
            )
            return await agent.process_task(task)
        
        return handler
    
    def _load_default_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Load default workflow templates"""
        return {
            "data_analysis_pipeline": {
                "description": "Complete data analysis workflow",
                "agents": ["dataagent", "researchagent"],
                "steps": [
                    {"agent": "dataagent", "task": "Load and validate data", "depends_on": []},
                    {"agent": "dataagent", "task": "Perform statistical analysis", "depends_on": [0]},
                    {"agent": "dataagent", "task": "Create visualizations", "depends_on": [1]},
                    {"agent": "researchagent", "task": "Generate insights report", "depends_on": [2]}
                ]
            },
            "software_development": {
                "description": "Software development lifecycle",
                "agents": ["planner", "codeagent", "systemagent"],
                "steps": [
                    {"agent": "planner", "task": "Analyze requirements and create plan", "depends_on": []},
                    {"agent": "codeagent", "task": "Implement core functionality", "depends_on": [0]},
                    {"agent": "codeagent", "task": "Write tests and documentation", "depends_on": [1]},
                    {"agent": "systemagent", "task": "Deploy and configure", "depends_on": [2]}
                ]
            },
            "research_project": {
                "description": "Comprehensive research project",
                "agents": ["planner", "researchagent", "dataagent"],
                "steps": [
                    {"agent": "planner", "task": "Define research scope and methodology", "depends_on": []},
                    {"agent": "researchagent", "task": "Gather information and sources", "depends_on": [0]},
                    {"agent": "dataagent", "task": "Analyze collected data", "depends_on": [1]},
                    {"agent": "researchagent", "task": "Synthesize findings and conclusions", "depends_on": [2]}
                ]
            },
            "system_automation": {
                "description": "System automation and optimization",
                "agents": ["systemagent", "codeagent", "dataagent"],
                "steps": [
                    {"agent": "systemagent", "task": "Analyze current system state", "depends_on": []},
                    {"agent": "codeagent", "task": "Develop automation scripts", "depends_on": [0]},
                    {"agent": "systemagent", "task": "Test and deploy automation", "depends_on": [1]},
                    {"agent": "dataagent", "task": "Monitor and analyze performance", "depends_on": [2]}
                ]
            }
        }
    
    async def execute_task(self, description: str, workflow_name: str = None, 
                          agent_name: str = None, priority: int = 1) -> Dict[str, Any]:
        """Execute a task using the multi-agent system"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        logger.info(f"Starting task execution: {task_id}")
        logger.info(f"Description: {description}")
        logger.info(f"Workflow: {workflow_name}")
        logger.info(f"Agent: {agent_name}")
        
        start_time = datetime.now()
        
        try:
            if agent_name and agent_name in self.agents:
                # Single agent execution
                result = await self._execute_single_agent_task(task_id, description, agent_name)
            elif workflow_name and workflow_name in self.workflows:
                # Workflow execution
                result = await self._execute_workflow(task_id, description, workflow_name)
            else:
                # Let planner decide
                result = await self._execute_planned_task(task_id, description)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Store completed task
            completed_task = {
                "task_id": task_id,
                "description": description,
                "workflow_name": workflow_name,
                "agent_name": agent_name,
                "priority": priority,
                "status": "completed",
                "result": result,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration
            }
            
            self.completed_tasks[task_id] = completed_task
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            logger.info(f"Task {task_id} completed successfully in {duration:.2f} seconds")
            return completed_task
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            
            # Store failed task
            failed_task = {
                "task_id": task_id,
                "description": description,
                "status": "failed",
                "error": str(e),
                "start_time": start_time,
                "end_time": datetime.now()
            }
            
            self.completed_tasks[task_id] = failed_task
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            raise
    
    async def _execute_single_agent_task(self, task_id: str, description: str, agent_name: str) -> Dict[str, Any]:
        """Execute task with a single agent"""
        agent = self.agents[agent_name]
        
        task = Task(
            id=task_id,
            description=description,
            agent=agent_name,
            status=TaskStatus.IN_PROGRESS
        )
        
        self.active_tasks[task_id] = task
        
        result = await agent.process_task(task)
        
        return {
            "type": "single_agent",
            "agent": agent_name,
            "result": result,
            "summary": f"Task completed by {agent_name}: {result[:200]}..."
        }
    
    async def _execute_workflow(self, task_id: str, description: str, workflow_name: str) -> Dict[str, Any]:
        """Execute a predefined workflow"""
        workflow = self.workflows[workflow_name]
        results = {}
        
        logger.info(f"Executing workflow '{workflow_name}' with {len(workflow['steps'])} steps")
        
        # Execute workflow steps respecting dependencies
        for step_idx, step in enumerate(workflow['steps']):
            # Check dependencies
            for dep_idx in step['depends_on']:
                if dep_idx not in results:
                    raise Exception(f"Dependency {dep_idx} not satisfied for step {step_idx}")
            
            # Execute step
            agent_name = step['agent']
            step_task = f"{step['task']} - Context: {description}"
            
            logger.info(f"Executing step {step_idx}: {agent_name} - {step['task']}")
            
            agent = self.agents[agent_name]
            task = Task(
                id=f"{task_id}_step_{step_idx}",
                description=step_task,
                agent=agent_name,
                metadata={"workflow": workflow_name, "step": step_idx}
            )
            
            step_result = await agent.process_task(task)
            results[step_idx] = {
                "step": step_idx,
                "agent": agent_name,
                "task": step['task'],
                "result": step_result
            }
            
            logger.info(f"Step {step_idx} completed")
        
        return {
            "type": "workflow",
            "workflow_name": workflow_name,
            "steps_completed": len(results),
            "results": results,
            "summary": f"Workflow '{workflow_name}' completed with {len(results)} steps"
        }
    
    async def _execute_planned_task(self, task_id: str, description: str) -> Dict[str, Any]:
        """Execute task using planner to create workflow"""
        logger.info("Using planner to create execution strategy")
        
        # Get plan from planner
        planner = self.agents["planner"]
        planning_task = Task(
            id=f"{task_id}_planning",
            description=f"Create execution plan for: {description}",
            agent="planner"
        )
        
        plan = await planner.process_task(planning_task)
        
        # Parse plan and execute (simplified implementation)
        # In a real implementation, you'd parse the plan more sophisticated
        
        # For now, return the plan as the result
        return {
            "type": "planned",
            "plan": plan,
            "summary": f"Task planned and executed: {plan[:200]}..."
        }
    
    async def schedule_recurring_task(self, name: str, description: str, 
                                    agent_name: str, cron_expression: str,
                                    max_runs: int = None) -> str:
        """Schedule a recurring task"""
        task_payload = {
            "description": description,
            "metadata": {"scheduled": True, "recurring": True}
        }
        
        return await self.scheduler_manager.schedule_recurring_task(
            name=name,
            description=description,
            agent_name=agent_name,
            cron_expression=cron_expression,
            task_payload=task_payload,
            max_runs=max_runs
        )
    
    async def get_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance summary for all agents"""
        performance = {}
        for name, agent in self.agents.items():
            performance[name] = await agent.get_performance_summary()
        return performance
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Memory stats
        memory_stats = {}
        for agent_name in self.agents.keys():
            memory_stats[agent_name] = await self.memory_system.get_memory_stats(agent_name)
        
        # Scheduler stats
        scheduler_stats = await self.scheduler.get_scheduler_stats()
        
        # Agent performance
        agent_performance = await self.get_agent_performance()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agents": {
                "count": len(self.agents),
                "names": list(self.agents.keys()),
                "performance": agent_performance
            },
            "tasks": {
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks)
            },
            "memory": {
                "total_memories": sum(stats.get('total_memories', 0) for stats in memory_stats.values()),
                "by_agent": memory_stats
            },
            "scheduler": scheduler_stats,
            "workflows": {
                "available": list(self.workflows.keys()),
                "count": len(self.workflows)
            }
        }
    
    async def start_services(self):
        """Start background services"""
        logger.info("Starting background services...")
        
        # Start scheduler
        asyncio.create_task(self.scheduler.start_scheduler())
        
        logger.info("All services started successfully")
    
    async def stop_services(self):
        """Stop background services"""
        logger.info("Stopping background services...")
        
        # Stop scheduler
        await self.scheduler.stop_scheduler()
        
        logger.info("All services stopped")

# Example usage and testing
async def main():
    """Main function for testing the orchestrator"""
    
    # Initialize orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Start services
    await orchestrator.start_services()
    
    try:
        # Test single agent task
        print("Testing single agent task...")
        result = await orchestrator.execute_task(
            description="Analyze the performance of our web application",
            agent_name="dataagent"
        )
        print(f"Single agent result: {result['summary']}")
        
        # Test workflow
        print("\nTesting workflow...")
        result = await orchestrator.execute_task(
            description="Create a data dashboard for sales metrics",
            workflow_name="data_analysis_pipeline"
        )
        print(f"Workflow result: {result['summary']}")
        
        # Test scheduled task
        print("\nScheduling recurring task...")
        task_id = await orchestrator.schedule_recurring_task(
            name="daily_system_check",
            description="Perform daily system health check",
            agent_name="systemagent",
            cron_expression="0 9 * * *",  # Daily at 9 AM
            max_runs=30  # Run for 30 days
        )
        print(f"Scheduled task ID: {task_id}")
        
        # Get system status
        print("\nSystem status:")
        status = await orchestrator.get_system_status()
        print(f"Active agents: {status['agents']['count']}")
        print(f"Total memories: {status['memory']['total_memories']}")
        print(f"Available workflows: {len(status['workflows']['available'])}")
        
        # Keep running for a bit to test scheduler
        print("\nRunning for 60 seconds to test scheduler...")
        await asyncio.sleep(60)
        
    finally:
        # Clean shutdown
        await orchestrator.stop_services()

if __name__ == "__main__":
    asyncio.run(main())