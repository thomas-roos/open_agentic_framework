"""
managers/agent_manager.py - Agent Execution Manager

Manages agent execution loops, reasoning, and tool integration.
Handles the core logic for running AI agents with natural language processing.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages agent execution and reasoning loops"""
    
    def __init__(self, ollama_client, memory_manager, tool_manager, config):
        """
        Initialize agent manager
        
        Args:
            ollama_client: Ollama client for LLM communication
            memory_manager: Memory manager for persistence
            tool_manager: Tool manager for tool execution
            config: Framework configuration
        """
        self.ollama_client = ollama_client
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.config = config
        logger.info("Initialized agent manager")
    
    async def execute_agent(
        self, 
        agent_name: str, 
        task: str, 
        context: Dict[str, Any] = None
    ) -> str:
        """
        Execute an agent's task with reasoning loop
        
        Args:
            agent_name: Name of the agent to execute
            task: Task description for the agent
            context: Additional context for the task
            
        Returns:
            Agent's final response
            
        Raises:
            ValueError: If agent not found or disabled
            Exception: If execution fails
        """
        context = context or {}
        
        # Get agent definition
        agent = self.memory_manager.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")
        
        if not agent.get("enabled", True):
            raise ValueError(f"Agent {agent_name} is disabled")
        
        logger.info(f"Starting execution for agent {agent_name}: {task}")
        
        # Log task start
        self.memory_manager.add_memory_entry(
            agent_name, "user", task, {"context": context}
        )
        
        # Get recent conversation history
        memory_entries = self.memory_manager.get_agent_memory(agent_name, limit=20)
        chat_history = self._build_chat_history(memory_entries)
        
        # Build system prompt
        system_prompt = self._build_system_prompt(agent, task, context)
        
        iteration = 0
        max_iterations = self.config.max_agent_iterations
        
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Agent {agent_name} iteration {iteration}")
            
            try:
                # Generate response from LLM
                response = await self.ollama_client.generate_response(
                    system_prompt,
                    model=agent.get("ollama_model", "llama3"),
                    chat_history=chat_history
                )
                
                # Log agent's response
                self.memory_manager.add_memory_entry(
                    agent_name, "assistant", response, 
                    {"iteration": iteration, "task": task}
                )
                
                # Parse response for tool calls
                tool_calls = self._parse_tool_calls(response)
                
                if not tool_calls:
                    # No tool calls, agent is done
                    logger.info(f"Agent {agent_name} completed task in {iteration} iterations")
                    return response
                
                # Execute tool calls
                tool_results = await self._execute_tool_calls(
                    tool_calls, agent_name, iteration
                )
                
                # Update chat history with tool results
                chat_history.append({"role": "assistant", "content": response})
                for result in tool_results:
                    if "error" in result:
                        chat_history.append({
                            "role": "user", 
                            "content": f"Tool {result['tool']} failed: {result['error']}"
                        })
                    else:
                        chat_history.append({
                            "role": "user",
                            "content": f"Tool {result['tool']} returned: {result['result']}"
                        })
                
            except Exception as e:
                error_msg = f"Error in agent iteration {iteration}: {e}"
                logger.error(error_msg)
                self.memory_manager.add_memory_entry(
                    agent_name, "thought", error_msg,
                    {"iteration": iteration, "error": str(e)}
                )
                raise
        
        # Max iterations reached
        final_msg = f"Agent {agent_name} reached maximum iterations ({max_iterations})"
        logger.warning(final_msg)
        self.memory_manager.add_memory_entry(
            agent_name, "thought", final_msg,
            {"max_iterations_reached": True}
        )
        return f"Task incomplete - reached maximum iterations. Last response: {response}"
    
    async def _execute_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]], 
        agent_name: str, 
        iteration: int
    ) -> List[Dict[str, Any]]:
        """
        Execute a list of tool calls
        
        Args:
            tool_calls: List of tool calls to execute
            agent_name: Name of the calling agent
            iteration: Current iteration number
            
        Returns:
            List of tool execution results
        """
        tool_results = []
        
        for tool_call in tool_calls:
            try:
                logger.debug(f"Executing tool {tool_call['tool_name']} for agent {agent_name}")
                
                result = await self.tool_manager.execute_tool(
                    tool_call["tool_name"],
                    tool_call["parameters"],
                    agent_name
                )
                
                tool_results.append({
                    "tool": tool_call["tool_name"],
                    "result": result
                })
                
                # Log tool execution
                self.memory_manager.add_memory_entry(
                    agent_name, "tool_output", 
                    f"Tool: {tool_call['tool_name']}\nResult: {result}",
                    {
                        "tool_name": tool_call["tool_name"],
                        "parameters": tool_call["parameters"],
                        "iteration": iteration
                    }
                )
                
            except Exception as e:
                error_msg = f"Error executing tool {tool_call['tool_name']}: {e}"
                logger.warning(error_msg)
                
                tool_results.append({
                    "tool": tool_call["tool_name"],
                    "error": str(e)
                })
                
                # Log tool error
                self.memory_manager.add_memory_entry(
                    agent_name, "tool_output", error_msg,
                    {
                        "tool_name": tool_call["tool_name"],
                        "parameters": tool_call["parameters"],
                        "error": str(e),
                        "iteration": iteration
                    }
                )
        
        return tool_results
    
    def _build_system_prompt(
        self, 
        agent: Dict[str, Any], 
        task: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Build system prompt for the agent
        
        Args:
            agent: Agent configuration
            task: Current task
            context: Task context
            
        Returns:
            Formatted system prompt
        """
        available_tools = self._get_available_tools(agent["tools"])
        
        prompt = f"""You are {agent['name']}, an AI assistant with the following characteristics:

ROLE: {agent['role']}

GOALS: {agent['goals']}

BACKSTORY: {agent['backstory']}

CURRENT TASK: {task}

CONTEXT: {json.dumps(context, indent=2) if context else "No additional context"}

AVAILABLE TOOLS:
{available_tools}

INSTRUCTIONS:
1. Analyze the task and determine what actions are needed
2. Use available tools when necessary to complete the task
3. When using tools, format your response as: TOOL_CALL: tool_name(parameter1=value1, parameter2=value2)
4. You can make multiple tool calls in a single response
5. Always explain your reasoning before making tool calls
6. Provide a clear final answer once the task is complete

Remember: You are helpful, thorough, and always explain your thought process."""

        return prompt
    
    def _get_available_tools(self, tool_names: List[str]) -> str:
        """
        Get formatted description of available tools
        
        Args:
            tool_names: List of tool names available to the agent
            
        Returns:
            Formatted tool descriptions
        """
        if not tool_names:
            return "No tools available"
        
        tool_descriptions = []
        for tool_name in tool_names:
            tool = self.memory_manager.get_tool(tool_name)
            if tool and tool.get("enabled", True):
                schema = tool["parameters_schema"]
                params = ", ".join([
                    f"{k}: {v.get('type', 'any')}" 
                    for k, v in schema.get("properties", {}).items()
                ])
                tool_descriptions.append(
                    f"- {tool_name}: {tool['description']}\n  Parameters: {params}"
                )
        
        return "\n".join(tool_descriptions) if tool_descriptions else "No enabled tools available"
    
    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from agent response
        
        Args:
            response: Agent's response text
            
        Returns:
            List of parsed tool calls
        """
        tool_calls = []
        
        # Pattern to match TOOL_CALL: tool_name(param1=value1, param2=value2)
        pattern = r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)'
        matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
        
        for tool_name, params_str in matches:
            try:
                # Parse parameters
                parameters = self._parse_parameters(params_str)
                
                tool_calls.append({
                    "tool_name": tool_name,
                    "parameters": parameters
                })
                
                logger.debug(f"Parsed tool call: {tool_name} with parameters: {parameters}")
                
            except Exception as e:
                logger.warning(f"Failed to parse tool call parameters: {e}")
        
        return tool_calls
    
    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """
        Parse parameters from tool call string
        
        Args:
            params_str: Parameter string from tool call
            
        Returns:
            Dictionary of parsed parameters
        """
        parameters = {}
        
        if not params_str.strip():
            return parameters
        
        # Simple parameter parsing (can be enhanced for complex cases)
        param_pairs = [p.strip() for p in params_str.split(',')]
        
        for pair in param_pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Try to parse as JSON if possible
                try:
                    if value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                    else:
                        # Try JSON parsing for complex types
                        try:
                            value = json.loads(value)
                        except:
                            pass  # Keep as string
                except:
                    pass  # Keep as string
                
                parameters[key] = value
        
        return parameters
    
    def _build_chat_history(self, memory_entries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Build chat history from memory entries
        
        Args:
            memory_entries: List of memory entries
            
        Returns:
            Chat history formatted for Ollama
        """
        chat_history = []
        
        for entry in memory_entries:
            role = entry["role"]
            content = entry["content"]
            
            if role == "user":
                chat_history.append({"role": "user", "content": content})
            elif role == "assistant":
                chat_history.append({"role": "assistant", "content": content})
            elif role == "tool_output":
                # Add tool outputs as user messages
                chat_history.append({"role": "user", "content": f"Tool output: {content}"})
        
        return chat_history
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """
        Get current status of an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent status information
        """
        agent = self.memory_manager.get_agent(agent_name)
        if not agent:
            return {"status": "not_found"}
        
        recent_memory = self.memory_manager.get_agent_memory(agent_name, limit=5)
        
        return {
            "status": "active" if agent["enabled"] else "disabled",
            "name": agent["name"],
            "role": agent["role"],
            "tools": agent["tools"],
            "model": agent["ollama_model"],
            "recent_activity": len(recent_memory),
            "last_update": agent["updated_at"]
        }