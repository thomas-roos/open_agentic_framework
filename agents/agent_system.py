# agents/agent_system.py
import asyncio
import aiohttp
import json
import os
import subprocess
import tempfile
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Import memory components
from ..memory.memory_system import MemoryManager, ConversationMemory, KnowledgeMemory, ExperienceMemory

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    description: str
    agent: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    result: str = ""
    error: str = ""
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Message:
    sender: str
    recipient: str
    content: str
    timestamp: datetime
    message_type: str = "text"
    task_id: str = None

class ToolRegistry:
    """Enhanced tool registry with memory integration"""
    
    def __init__(self, memory_manager: MemoryManager = None):
        self.tools = {}
        self.memory_manager = memory_manager
        self._register_default_tools()
    
    def register_tool(self, name: str, func: Callable, description: str, schema: Dict = None):
        """Register a new tool"""
        self.tools[name] = {
            'function': func,
            'description': description,
            'schema': schema or {}
        }
    
    def _register_default_tools(self):
        """Register default tools with enhanced capabilities"""
        
        # File operations
        self.register_tool(
            'read_file',
            self._read_file,
            'Read contents of a file',
            {'filepath': 'string'}
        )
        
        self.register_tool(
            'write_file',
            self._write_file,
            'Write content to a file',
            {'filepath': 'string', 'content': 'string'}
        )
        
        self.register_tool(
            'list_files',
            self._list_files,
            'List files in a directory',
            {'directory': 'string'}
        )
        
        self.register_tool(
            'search_files',
            self._search_files,
            'Search for files containing specific text',
            {'directory': 'string', 'pattern': 'string'}
        )
        
        # System operations
        self.register_tool(
            'run_command',
            self._run_command,
            'Execute a shell command safely',
            {'command': 'string'}
        )
        
        self.register_tool(
            'get_system_info',
            self._get_system_info,
            'Get system information',
            {}
        )
        
        # Data operations
        self.register_tool(
            'calculate',
            self._calculate,
            'Perform mathematical calculations',
            {'expression': 'string'}
        )
        
        self.register_tool(
            'analyze_data',
            self._analyze_data,
            'Analyze structured data',
            {'data': 'object', 'analysis_type': 'string'}
        )
        
        # Web operations
        self.register_tool(
            'http_request',
            self._http_request,
            'Make HTTP requests',
            {'url': 'string', 'method': 'string', 'data': 'object'}
        )
        
        self.register_tool(
            'web_search',
            self._web_search,
            'Search the web (mock implementation)',
            {'query': 'string'}
        )
        
        # Memory operations
        self.register_tool(
            'remember_fact',
            self._remember_fact,
            'Store a fact in long-term memory',
            {'topic': 'string', 'information': 'string', 'agent_name': 'string'}
        )
        
        self.register_tool(
            'recall_knowledge',
            self._recall_knowledge,
            'Recall knowledge about a topic',
            {'topic': 'string', 'agent_name': 'string'}
        )
    
    async def _read_file(self, filepath: str) -> str:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remember this file access
            if self.memory_manager:
                await self.memory_manager.remember(
                    agent_name="system",
                    content=f"Accessed file: {filepath}",
                    memory_type="file_access",
                    metadata={"filepath": filepath, "action": "read"}
                )
            
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    async def _write_file(self, filepath: str, content: str) -> str:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Remember this file operation
            if self.memory_manager:
                await self.memory_manager.remember(
                    agent_name="system",
                    content=f"Created/modified file: {filepath}",
                    memory_type="file_operation",
                    metadata={"filepath": filepath, "action": "write", "size": len(content)}
                )
            
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    async def _list_files(self, directory: str = ".") -> str:
        try:
            files = os.listdir(directory)
            return json.dumps(files)
        except Exception as e:
            return f"Error listing files: {str(e)}"
    
    async def _search_files(self, directory: str, pattern: str) -> str:
        try:
            import glob
            matches = glob.glob(os.path.join(directory, f"*{pattern}*"))
            return json.dumps(matches)
        except Exception as e:
            return f"Error searching files: {str(e)}"
    
    async def _run_command(self, command: str) -> str:
        try:
            # Enhanced safety check
            dangerous_commands = [
                'rm -rf', 'del *', 'format', 'mkfs', 'dd if=',
                'sudo rm', 'chmod 777', '> /dev/', 'shutdown', 'reboot'
            ]
            
            if any(cmd in command.lower() for cmd in dangerous_commands):
                return "Command rejected for safety reasons"
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            # Remember command execution
            if self.memory_manager:
                await self.memory_manager.remember(
                    agent_name="system",
                    content=f"Executed command: {command}",
                    memory_type="command_execution",
                    metadata={
                        "command": command,
                        "exit_code": result.returncode,
                        "success": result.returncode == 0
                    }
                )
            
            return f"Exit code: {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    async def _get_system_info(self) -> str:
        try:
            import platform
            info = {
                "system": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
            return json.dumps(info)
        except Exception as e:
            return f"Error getting system info: {str(e)}"
    
    async def _calculate(self, expression: str) -> str:
        try:
            # Enhanced safe evaluation
            import ast
            import operator
            
            # Supported operations
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
            }
            
            def eval_expr(node):
                if isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.BinOp):
                    return ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
                elif isinstance(node, ast.UnaryOp):
                    return ops[type(node.op)](eval_expr(node.operand))
                else:
                    raise TypeError(node)
            
            result = eval_expr(ast.parse(expression, mode='eval').body)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _analyze_data(self, data: Any, analysis_type: str = "summary") -> str:
        try:
            if isinstance(data, list):
                if analysis_type == "summary":
                    return f"List with {len(data)} items. Sample: {data[:3] if data else 'empty'}"
                elif analysis_type == "statistics" and all(isinstance(x, (int, float)) for x in data):
                    import statistics
                    return f"Count: {len(data)}, Mean: {statistics.mean(data):.2f}, Median: {statistics.median(data):.2f}"
            elif isinstance(data, dict):
                return f"Dictionary with keys: {list(data.keys())}"
            else:
                return f"Data type: {type(data).__name__}, Value: {str(data)[:100]}"
        except Exception as e:
            return f"Error analyzing data: {str(e)}"
    
    async def _http_request(self, url: str, method: str = "GET", data: Dict = None) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=data) as response:
                    result = await response.text()
                    return f"Status: {response.status}\nResponse: {result[:500]}..."
        except Exception as e:
            return f"HTTP request failed: {str(e)}"
    
    async def _web_search(self, query: str) -> str:
        # Mock implementation - replace with real search API
        return f"Mock search results for '{query}': [Integrate with real search API]"
    
    async def _remember_fact(self, topic: str, information: str, agent_name: str) -> str:
        if not self.memory_manager:
            return "Memory manager not available"
        
        try:
            knowledge_memory = KnowledgeMemory(self.memory_manager)
            await knowledge_memory.add_knowledge(
                agent_name=agent_name,
                topic=topic,
                information=information,
                source="tool_input"
            )
            return f"Stored knowledge about {topic}"
        except Exception as e:
            return f"Error storing knowledge: {str(e)}"
    
    async def _recall_knowledge(self, topic: str, agent_name: str) -> str:
        if not self.memory_manager:
            return "Memory manager not available"
        
        try:
            knowledge_memory = KnowledgeMemory(self.memory_manager)
            knowledge = await knowledge_memory.query_knowledge(agent_name, topic)
            if knowledge:
                return f"Knowledge about {topic}: " + "; ".join(knowledge[:3])
            else:
                return f"No knowledge found about {topic}"
        except Exception as e:
            return f"Error recalling knowledge: {str(e)}"
    
    async def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        try:
            return await self.tools[tool_name]['function'](**kwargs)
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return f"Tool execution failed: {str(e)}"
    
    def get_tool_descriptions(self) -> str:
        """Get descriptions of all available tools"""
        descriptions = []
        for name, tool in self.tools.items():
            schema_str = ", ".join([f"{k}: {v}" for k, v in tool['schema'].items()])
            descriptions.append(f"- {name}({schema_str}): {tool['description']}")
        return "\n".join(descriptions)

class BaseAgent:
    """Enhanced base agent with memory integration"""
    
    def __init__(self, name: str, role: str, model: str = "llama3.2:1b", base_url: str = "http://localhost:11434"):
        self.name = name
        self.role = role
        self.model = model
        self.base_url = base_url
        self.tool_registry = None
        self.memory_manager = None
        self.conversation_memory = None
        self.knowledge_memory = None
        self.experience_memory = None
        self.context = {}
        self.capabilities = []
        self.performance_stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "average_response_time": 0.0
        }
    
    def set_memory_manager(self, memory_manager: MemoryManager):
        """Set memory manager and initialize memory components"""
        self.memory_manager = memory_manager
        self.conversation_memory = ConversationMemory(memory_manager)
        self.knowledge_memory = KnowledgeMemory(memory_manager)
        self.experience_memory = ExperienceMemory(memory_manager)
    
    def set_tool_registry(self, registry: ToolRegistry):
        """Set tool registry for this agent"""
        self.tool_registry = registry
    
    async def call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """Call Ollama LLM with enhanced context"""
        
        # Add relevant memories to context
        context_memories = ""
        if self.memory_manager:
            # Get recent relevant memories
            memories = await self.memory_manager.recall(
                agent_name=self.name,
                query=prompt[:100],  # Use first part of prompt as query
                limit=3
            )
            
            if memories:
                context_memories = "\n\nRelevant memories:\n"
                for memory in memories:
                    context_memories += f"- {memory.content[:100]}...\n"
        
        # Enhanced prompt with memory context
        enhanced_prompt = f"{prompt}{context_memories}"
        
        payload = {
            "model": self.model,
            "prompt": enhanced_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        if system_prompt:
            # Enhanced system prompt with capabilities and tools
            enhanced_system_prompt = f"""{system_prompt}

Your capabilities: {', '.join(self.capabilities)}

Available tools: {self.tool_registry.get_tool_descriptions() if self.tool_registry else 'None'}

When you need to use tools, format as: TOOL_CALL: tool_name(param1=value1, param2=value2)

When you learn something important, use: TOOL_CALL: remember_fact(topic=topic, information=info, agent_name={self.name})

Always consider your past experiences and knowledge when responding."""
            
            payload["system"] = enhanced_system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["response"]
                    else:
                        return f"Error: {response.status}"
        except Exception as e:
            logger.error(f"LLM call failed for {self.name}: {e}")
            return f"Error calling LLM: {str(e)}"
    
    async def process_task(self, task: Task) -> str:
        """Process a task with memory integration"""
        start_time = datetime.now()
        
        try:
            # Get relevant past experiences
            if self.experience_memory:
                similar_experiences = await self.experience_memory.get_similar_experiences(
                    agent_name=self.name,
                    task_type=task.metadata.get("task_type", "general"),
                    limit=3
                )
                
                if similar_experiences:
                    logger.info(f"{self.name} found {len(similar_experiences)} similar experiences")
            
            # Process the task (to be overridden by subclasses)
            result = await self._process_task_impl(task)
            
            # Record successful experience
            if self.experience_memory:
                await self.experience_memory.add_experience(
                    agent_name=self.name,
                    task_type=task.metadata.get("task_type", "general"),
                    approach=f"Processed: {task.description[:100]}",
                    outcome=result[:200],
                    success=True,
                    lessons_learned="Task completed successfully"
                )
            
            # Update performance stats
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            self.performance_stats["tasks_completed"] += 1
            self.performance_stats["total_execution_time"] += execution_time
            self.performance_stats["average_response_time"] = (
                self.performance_stats["total_execution_time"] / 
                (self.performance_stats["tasks_completed"] + self.performance_stats["tasks_failed"])
            )
            
            return result
            
        except Exception as e:
            # Record failed experience
            if self.experience_memory:
                await self.experience_memory.add_experience(
                    agent_name=self.name,
                    task_type=task.metadata.get("task_type", "general"),
                    approach=f"Attempted: {task.description[:100]}",
                    outcome=f"Failed: {str(e)}",
                    success=False,
                    lessons_learned=f"Error encountered: {str(e)}"
                )
            
            # Update performance stats
            self.performance_stats["tasks_failed"] += 1
            
            logger.error(f"Task failed for {self.name}: {e}")
            raise
    
    async def _process_task_impl(self, task: Task) -> str:
        """Default task processing - to be overridden by subclasses"""
        return f"{self.name} processed task: {task.description}"
    
    def extract_tool_calls(self, text: str) -> List[Dict]:
        """Extract tool calls from LLM response"""
        import re
        
        # Look for TOOL_CALL: tool_name(param1=value1, param2=value2)
        pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        tool_calls = []
        for tool_name, params_str in matches:
            # Parse parameters
            params = {}
            if params_str.strip():
                # Simple parameter parsing
                param_pairs = params_str.split(',')
                for pair in param_pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        params[key] = value
            
            tool_calls.append({
                'tool': tool_name,
                'parameters': params
            })
        
        return tool_calls
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get agent performance summary"""
        total_tasks = self.performance_stats["tasks_completed"] + self.performance_stats["tasks_failed"]
        success_rate = (
            self.performance_stats["tasks_completed"] / total_tasks * 100 
            if total_tasks > 0 else 0
        )
        
        # Get memory stats
        memory_stats = {}
        if self.memory_manager:
            memory_stats = await self.memory_manager.memory_system.get_memory_stats(self.name)
        
        return {
            "agent_name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "performance": {
                **self.performance_stats,
                "success_rate_percent": round(success_rate, 2)
            },
            "memory": memory_stats
        }

# Specialized agent classes with enhanced capabilities
class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Planner", "Strategic Planning and Coordination")
        self.capabilities = [
            "task_decomposition", "workflow_planning", "resource_allocation",
            "dependency_management", "strategic_thinking"
        ]
    
    async def _process_task_impl(self, task: Task) -> str:
        system_prompt = f"""You are {self.name}, an advanced AI planning agent. Your role is to:
1. Analyze complex tasks and break them into smaller, manageable subtasks
2. Create efficient execution workflows with proper dependencies
3. Assign tasks to appropriate specialized agents based on their capabilities
4. Optimize resource allocation and coordination strategies
5. Learn from past planning experiences to improve future plans

You have access to memory systems to recall similar past planning scenarios and successful strategies."""

        prompt = f"Create a comprehensive plan for: {task.description}"
        response = await self.call_llm(prompt, system_prompt)
        
        # Execute tool calls
        tool_calls = self.extract_tool_calls(response)
        for call in tool_calls:
            if self.tool_registry:
                tool_result = await self.tool_registry.execute_tool(
                    call['tool'], 
                    **call['parameters']
                )
                response += f"\n\n[Tool Result - {call['tool']}]: {tool_result}"
        
        return response

class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__("DataAgent", "Data Analysis and Processing")
        self.capabilities = [
            "data_analysis", "file_processing", "statistical_analysis",
            "data_visualization", "database_operations", "data_mining"
        ]
    
    async def _process_task_impl(self, task: Task) -> str:
        system_prompt = f"""You are {self.name}, an expert data scientist and analyst. Your capabilities include:
- Advanced data analysis and statistical processing
- File operations and data format conversion
- Database queries and data mining
- Data visualization and reporting
- Pattern recognition and anomaly detection
- Predictive analytics and machine learning

You have access to comprehensive tools and can remember insights from previous data analysis tasks."""

        prompt = f"Analyze and process the following data task: {task.description}"
        response = await self.call_llm(prompt, system_prompt)
        
        # Execute tool calls
        tool_calls = self.extract_tool_calls(response)
        for call in tool_calls:
            if self.tool_registry:
                tool_result = await self.tool_registry.execute_tool(
                    call['tool'], 
                    **call['parameters']
                )
                response += f"\n\n[Tool Result - {call['tool']}]: {tool_result}"
        
        return response

class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__("CodeAgent", "Software Development and Programming")
        self.capabilities = [
            "code_generation", "debugging", "code_review", "testing",
            "architecture_design", "optimization", "documentation"
        ]
    
    async def _process_task_impl(self, task: Task) -> str:
        system_prompt = f"""You are {self.name}, an expert software engineer and developer. Your capabilities include:
- Writing high-quality code in multiple programming languages
- Debugging and troubleshooting complex issues
- Code review and optimization
- Software architecture and design patterns
- Test-driven development and quality assurance
- Documentation and technical writing

You can access past coding experiences and successful implementation patterns from memory."""

        prompt = f"Handle this programming task: {task.description}"
        response = await self.call_llm(prompt, system_prompt)
        
        # Execute tool calls
        tool_calls = self.extract_tool_calls(response)
        for call in tool_calls:
            if self.tool_registry:
                tool_result = await self.tool_registry.execute_tool(
                    call['tool'], 
                    **call['parameters']
                )
                response += f"\n\n[Tool Result - {call['tool']}]: {tool_result}"
        
        return response

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResearchAgent", "Information Gathering and Analysis")
        self.capabilities = [
            "web_research", "document_analysis", "information_synthesis",
            "fact_checking", "competitive_analysis", "trend_analysis"
        ]
    
    async def _process_task_impl(self, task: Task) -> str:
        system_prompt = f"""You are {self.name}, an expert researcher and information analyst. Your capabilities include:
- Comprehensive web research and information gathering
- Document analysis and summarization
- Information synthesis and fact-checking
- Competitive analysis and market research
- Trend analysis and forecasting
- Academic and technical research

You can build upon previous research findings stored in your memory system."""

        prompt = f"Research and analyze: {task.description}"
        response = await self.call_llm(prompt, system_prompt)
        
        # Execute tool calls
        tool_calls = self.extract_tool_calls(response)
        for call in tool_calls:
            if self.tool_registry:
                tool_result = await self.tool_registry.execute_tool(
                    call['tool'], 
                    **call['parameters']
                )
                response += f"\n\n[Tool Result - {call['tool']}]: {tool_result}"
        
        return response

class SystemAgent(BaseAgent):
    def __init__(self):
        super().__init__("SystemAgent", "System Operations and Infrastructure")
        self.capabilities = [
            "command_execution", "system_monitoring", "infrastructure_management",
            "deployment", "security_analysis", "performance_optimization"
        ]
    
    async def _process_task_impl(self, task: Task) -> str:
        system_prompt = f"""You are {self.name}, an expert system administrator and DevOps engineer. Your capabilities include:
- Safe command execution and system operations
- Infrastructure management and deployment
- System monitoring and performance optimization
- Security analysis and hardening
- Automation and scripting
- Troubleshooting and incident response

You prioritize security and can learn from past system operations and issues."""

        prompt = f"Handle this system task: {task.description}"
        response = await self.call_llm(prompt, system_prompt)
        
        # Execute tool calls
        tool_calls = self.extract_tool_calls(response)
        for call in tool_calls:
            if self.tool_registry:
                tool_result = await self.tool_registry.execute_tool(
                    call['tool'], 
                    **call['parameters']
                )
                response += f"\n\n[Tool Result - {call['tool']}]: {tool_result}"
        
        return response