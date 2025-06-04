"""
managers/agent_manager.py - Fixed Agent Execution Manager

Fixed version that properly engages the LLM during forced tool execution
instead of bypassing it entirely.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages agent execution and reasoning loops with proper LLM engagement"""
    
    def __init__(self, ollama_client, memory_manager, tool_manager, config):
        self.ollama_client = ollama_client
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.config = config
        logger.info("Initialized fixed agent manager with proper LLM engagement")
    
    async def execute_agent(
        self, 
        agent_name: str, 
        task: str, 
        context: Dict[str, Any] = None
    ) -> str:
        """Execute agent with proper LLM engagement for tool calling"""
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
        memory_entries = self.memory_manager.get_agent_memory(agent_name, limit=5)
        chat_history = self._build_chat_history(memory_entries)
        
        # Build system prompt
        system_prompt = self._build_simple_system_prompt(agent, task, context)
        
        iteration = 0
        max_iterations = min(self.config.max_agent_iterations, 3)
        
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Agent {agent_name} iteration {iteration}")
            
            try:
                # Generate response
                response = await self._generate_simple_response(
                    system_prompt, agent, task, chat_history, iteration
                )
                
                # Log agent's response
                self.memory_manager.add_memory_entry(
                    agent_name, "assistant", response, 
                    {"iteration": iteration, "task": task}
                )
                
                # Parse response for tool calls
                tool_calls = self._parse_tool_calls_aggressive(response)
                
                if not tool_calls:
                    # FIXED: Instead of bypassing LLM, re-prompt it with explicit instructions
                    if iteration == 1 and agent.get("tools"):
                        logger.info(f"No tool calls found, re-prompting LLM with explicit instructions")
                        
                        # Add explicit tool instruction to chat history
                        tool_instruction = self._create_explicit_tool_instruction(agent, task)
                        chat_history.append({"role": "assistant", "content": response})
                        chat_history.append({"role": "user", "content": tool_instruction})
                        
                        # Generate new response with explicit tool instruction
                        forced_response = await self.ollama_client.generate_response(
                            system_prompt,
                            model=agent.get("ollama_model", "llama3"),
                            chat_history=chat_history
                        )
                        
                        logger.info(f"LLM response to explicit instruction: {forced_response[:100]}...")
                        
                        # Try to parse tool calls from the forced response
                        tool_calls = self._parse_tool_calls_aggressive(forced_response)
                        
                        # If still no tool calls, create a minimal one as last resort
                        if not tool_calls:
                            logger.warning("LLM still didn't use tools after explicit instruction, creating minimal tool call")
                            minimal_tool_call = self._create_minimal_tool_call(agent, task)
                            if minimal_tool_call:
                                tool_calls = [minimal_tool_call]
                        
                        # Update response to the forced response
                        response = forced_response
                        
                        # Log the forced response
                        self.memory_manager.add_memory_entry(
                            agent_name, "assistant", forced_response, 
                            {"iteration": f"{iteration}-forced", "task": task, "forced": True}
                        )
                    
                    if not tool_calls:
                        # No tools available or couldn't force usage, treat as final answer
                        logger.info(f"Agent {agent_name} completed without tools")
                        return response
                
                # Execute tool calls
                tool_results = await self._execute_tool_calls(
                    tool_calls, agent_name, iteration
                )
                
                # Update chat history with results
                chat_history.append({"role": "assistant", "content": response})
                
                # Add tool results to chat history
                for result in tool_results:
                    if "error" in result:
                        result_msg = f"Tool {result['tool']} failed: {result['error']}"
                    else:
                        result_msg = f"Tool {result['tool']} result: {result['result']}"
                    
                    chat_history.append({"role": "user", "content": result_msg})
                
                # For small models, ask for final answer after tool execution
                if iteration >= 1:
                    completion_prompt = "Based on the tool results above, provide your final answer to the original task."
                    chat_history.append({"role": "user", "content": completion_prompt})
                    
                    # Generate final response
                    final_response = await self.ollama_client.generate_response(
                        system_prompt,
                        model=agent.get("ollama_model", "llama3"),
                        chat_history=chat_history
                    )
                    
                    # Log final response
                    self.memory_manager.add_memory_entry(
                        agent_name, "assistant", final_response, 
                        {"iteration": f"{iteration}-final", "task": task}
                    )
                    
                    return final_response
                
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
        return f"Task completed. Final response: {response}"
    
    def _create_explicit_tool_instruction(self, agent: Dict[str, Any], task: str) -> str:
        """
        Create explicit instruction to force the LLM to use tools
        This engages the LLM instead of bypassing it
        """
        available_tools = agent.get("tools", [])
        
        # Detect task type and create specific instruction
        if any(keyword in task.lower() for keyword in ["check", "http", "url", "website", "status"]):
            if "website_monitor" in available_tools:
                # Extract URL from task if possible
                url_match = re.search(r'https?://[^\s]+', task)
                if url_match:
                    url = url_match.group(0)
                elif "google.com" in task.lower():
                    url = "https://google.com"
                else:
                    url = "https://google.com"
                
                return f"""The task requires checking a website. You must use the website_monitor tool.

Please respond with exactly this format:
TOOL_CALL: website_monitor(url={url}, expected_status=200)

Do not write code or explanations, just the tool call."""
        
        elif any(keyword in task.lower() for keyword in ["api", "request", "get", "post"]):
            if "http_client" in available_tools:
                url_match = re.search(r'https?://[^\s]+', task)
                url = url_match.group(0) if url_match else "https://httpbin.org/get"
                
                return f"""The task requires making an HTTP request. You must use the http_client tool.

Please respond with exactly this format:
TOOL_CALL: http_client(url={url}, method=GET)

Do not write code or explanations, just the tool call."""
        
        # Generic tool instruction
        tool_list = ", ".join(available_tools)
        return f"""You have access to these tools: {tool_list}

The current task requires using one of these tools. Please use the TOOL_CALL format:
TOOL_CALL: tool_name(parameter=value)

Examples:
- TOOL_CALL: website_monitor(url=https://example.com, expected_status=200)
- TOOL_CALL: http_client(url=https://api.example.com, method=GET)

Please respond with the appropriate tool call for the task: "{task}" """
    
    def _create_minimal_tool_call(self, agent: Dict[str, Any], task: str) -> Optional[Dict[str, Any]]:
        """
        Create minimal tool call as absolute last resort
        This should only be used if LLM fails to respond to explicit instructions
        """
        available_tools = agent.get("tools", [])
        
        logger.warning("Creating minimal tool call as last resort - LLM engagement failed")
        
        # URL checking tasks
        if any(keyword in task.lower() for keyword in ["check", "http", "url", "website", "status"]):
            if "website_monitor" in available_tools:
                url_match = re.search(r'https?://[^\s]+', task)
                if url_match:
                    url = url_match.group(0)
                elif "google.com" in task.lower():
                    url = "https://google.com"
                else:
                    url = "https://google.com"
                
                return {
                    "tool_name": "website_monitor",
                    "parameters": {"url": url, "expected_status": 200}
                }
        
        # API/HTTP tasks
        if any(keyword in task.lower() for keyword in ["api", "request", "get", "post"]):
            if "http_client" in available_tools:
                url_match = re.search(r'https?://[^\s]+', task)
                url = url_match.group(0) if url_match else "https://httpbin.org/get"
                
                return {
                    "tool_name": "http_client",
                    "parameters": {"url": url, "method": "GET"}
                }
        
        return None
    
    def _build_simple_system_prompt(
        self, 
        agent: Dict[str, Any], 
        task: str, 
        context: Dict[str, Any]
    ) -> str:
        """Build simple system prompt optimized for small models"""
        tools_list = self._get_simple_tool_list(agent["tools"])
        
        prompt = f"""You are {agent['name']}: {agent['role']}

Your task: {task}

Available tools: {tools_list}

IMPORTANT: To use a tool, use this exact format:
TOOL_CALL: tool_name(parameter=value)

Examples:
- TOOL_CALL: website_monitor(url=https://google.com, expected_status=200)
- TOOL_CALL: http_client(url=https://api.example.com, method=GET)

If the task requires checking a website or URL, you MUST use the website_monitor tool.
If the task requires making HTTP requests, you MUST use the http_client tool.

Never write code. Use tools when available and appropriate."""
        
        return prompt
    
    def _get_simple_tool_list(self, tool_names: List[str]) -> str:
        """Get simple list of available tools"""
        if not tool_names:
            return "None"
        
        tool_info = []
        for tool_name in tool_names:
            tool = self.memory_manager.get_tool(tool_name)
            if tool and tool.get("enabled", True):
                tool_info.append(f"{tool_name}")
        
        return ", ".join(tool_info) if tool_info else "None"
    
    async def _generate_simple_response(
        self, 
        system_prompt: str, 
        agent: Dict[str, Any], 
        task: str, 
        chat_history: List[Dict[str, str]], 
        iteration: int
    ) -> str:
        """Generate response with explicit task instruction"""
        model_name = agent.get("ollama_model", "llama3")
        
        # Add task to chat history for first iteration
        if iteration == 1:
            chat_history.append({"role": "user", "content": task})
        
        response = await self.ollama_client.generate_response(
            system_prompt,
            model=model_name,
            chat_history=chat_history
        )
        
        return response
    
    def _parse_tool_calls_aggressive(self, response: str) -> List[Dict[str, Any]]:
        """Aggressive tool call parsing with multiple patterns"""
        tool_calls = []
        
        logger.debug(f"Parsing response for tool calls: {response[:200]}...")
        
        # Multiple patterns to catch various formats
        patterns = [
            r'TOOL_CALL:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)',
            r'TOOL_CALL\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)',
            r'tool_call:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)',
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*url\s*=\s*([^,)]+)(?:,\s*expected_status\s*=\s*(\d+))?\s*\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                try:
                    if len(match) == 2:
                        tool_name, params_str = match
                        tool_name = tool_name.strip()
                        
                        # Validate tool exists
                        if not self.memory_manager.get_tool(tool_name):
                            continue
                        
                        parameters = self._parse_parameters_simple(params_str)
                        
                    elif len(match) >= 2:
                        # Handle URL-specific parsing
                        if 'website_monitor' in response.lower():
                            tool_name = "website_monitor"
                            url = match[0] if match[0] else match[1]
                            status = match[2] if len(match) > 2 and match[2] else "200"
                            
                            parameters = {
                                "url": url.strip().strip('"\''),
                                "expected_status": int(status) if status.isdigit() else 200
                            }
                        else:
                            continue
                    else:
                        continue
                    
                    # Clean up URL parameter
                    if "url" in parameters:
                        url = str(parameters["url"]).strip().strip('"\'')
                        if not url.startswith(('http://', 'https://')):
                            if url.startswith('www.'):
                                url = f"https://{url}"
                            elif '.' in url:
                                url = f"https://{url}"
                        parameters["url"] = url
                    
                    tool_call = {
                        "tool_name": tool_name,
                        "parameters": parameters
                    }
                    
                    # Check for duplicates
                    if not any(tc["tool_name"] == tool_name and tc["parameters"] == parameters for tc in tool_calls):
                        tool_calls.append(tool_call)
                        logger.info(f"Parsed tool call: {tool_name} with {parameters}")
                
                except Exception as e:
                    logger.error(f"Failed to parse tool call from match {match}: {e}")
                    continue
        
        return tool_calls
    
    def _parse_parameters_simple(self, params_str: str) -> Dict[str, Any]:
        """Simplified parameter parsing"""
        parameters = {}
        
        if not params_str.strip():
            return parameters
        
        # Simple split on comma
        parts = [p.strip() for p in params_str.split(',')]
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Simple type conversion
                if value.isdigit():
                    parameters[key] = int(value)
                elif value.lower() in ['true', 'false']:
                    parameters[key] = value.lower() == 'true'
                else:
                    parameters[key] = value
        
        return parameters
    
    # Keep existing helper methods
    async def _execute_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]], 
        agent_name: str, 
        iteration: int
    ) -> List[Dict[str, Any]]:
        """Execute tool calls"""
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
        
        return tool_results
    
    def _build_chat_history(self, memory_entries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build chat history"""
        chat_history = []
        
        for entry in memory_entries:
            role = entry["role"]
            content = entry["content"]
            
            if role == "user":
                chat_history.append({"role": "user", "content": content})
            elif role == "assistant":
                chat_history.append({"role": "assistant", "content": content})
            elif role == "tool_output":
                chat_history.append({"role": "user", "content": f"Tool output: {content}"})
        
        return chat_history
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get agent status"""
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