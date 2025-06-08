"""
managers/agent_manager.py - FIXED: Enhanced Agent Manager with Proper Context Passing

Fixed the _build_simple_system_prompt method to include all agent context:
- Backstory (contains the critical PURL parsing rules)
- Goals
- Execution context
- Proper role definition
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from providers.base_llm_provider import Message, GenerationConfig

logger = logging.getLogger(__name__)

class AgentManager:
    """Enhanced agent execution manager with multi-provider LLM support"""
    
    def __init__(self, llm_manager, memory_manager, tool_manager, config):
        self.llm_manager = llm_manager
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.config = config
        logger.info("Initialized enhanced agent manager with multi-provider LLM support")
    
    async def execute_agent(
        self, 
        agent_name: str, 
        task: str, 
        context: Dict[str, Any] = None
    ) -> str:
        """Execute agent with memory limits and automatic cleanup"""
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
        
        # Get recent conversation history (LIMITED to max entries)
        memory_limit = self.config.max_agent_memory_entries
        memory_entries = self.memory_manager.get_agent_memory(agent_name, limit=memory_limit)
        chat_history = self._build_chat_history(memory_entries)
        
        # Build comprehensive system prompt with all agent context
        system_prompt = self._build_comprehensive_system_prompt(agent, task, context)
        
        iteration = 0
        max_iterations = min(self.config.max_agent_iterations, 3)
        
        try:
            while iteration < max_iterations:
                iteration += 1
                logger.debug(f"Agent {agent_name} iteration {iteration}")
                
                # Generate response using the LLM manager
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
                    # If no tools are available, this is likely the final answer
                    if not agent.get("tools"):
                        logger.info(f"Agent {agent_name} completed without tools (no tools available)")
                        break
                    
                    # Try to force tool usage if iteration 1 and tools available
                    if iteration == 1 and agent.get("tools"):
                        logger.info(f"No tool calls found, re-prompting LLM with explicit instructions")
                        
                        # Add explicit tool instruction to chat history
                        tool_instruction = self._create_explicit_tool_instruction(agent, task)
                        chat_history.append({"role": "assistant", "content": response})
                        chat_history.append({"role": "user", "content": tool_instruction})
                        
                        # Generate new response with explicit tool instruction
                        forced_response = await self._generate_with_messages(
                            agent, chat_history, system_prompt
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
                        break
                
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
                    final_response = await self._generate_with_messages(
                        agent, chat_history, system_prompt
                    )
                    
                    # Log final response
                    self.memory_manager.add_memory_entry(
                        agent_name, "assistant", final_response, 
                        {"iteration": f"{iteration}-final", "task": task}
                    )
                    
                    response = final_response
                    break
            
            # ENHANCED: Cleanup old memory entries after execution
            self.memory_manager.cleanup_agent_memory(
                agent_name, 
                keep_last=self.config.max_agent_memory_entries
            )
            
            return response
                        
        except Exception as e:
            error_msg = f"Error in agent execution: {e}"
            logger.error(error_msg)
            self.memory_manager.add_memory_entry(
                agent_name, "thought", error_msg,
                {"error": str(e), "task": task}
            )
            
            # Still cleanup memory even on error
            try:
                self.memory_manager.cleanup_agent_memory(
                    agent_name, 
                    keep_last=self.config.max_agent_memory_entries
                )
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup memory after error: {cleanup_error}")
            
            raise
    
    def _build_comprehensive_system_prompt(
        self, 
        agent: Dict[str, Any], 
        task: str, 
        context: Dict[str, Any]
    ) -> str:
        """Build comprehensive system prompt with ALL agent context"""
        tools_list = self._get_simple_tool_list(agent["tools"])
        
        # Start with agent identity and role
        prompt_parts = [
            f"You are {agent['name']}: {agent['role']}"
        ]
        
        # Add agent's goals if available
        if agent.get("goals"):
            prompt_parts.append(f"\nYour Goals:\n{agent['goals']}")
        
        # Add agent's backstory - THIS IS CRITICAL for your PURL parsing rules
        if agent.get("backstory"):
            prompt_parts.append(f"\nYour Background and Rules:\n{agent['backstory']}")
        
        # Add the current task
        prompt_parts.append(f"\nCurrent Task: {task}")
        
        # Add execution context if provided
        if context:
            context_str = ""
            for key, value in context.items():
                if isinstance(value, (dict, list)):
                    context_str += f"\n- {key}: {json.dumps(value, indent=2)}"
                else:
                    context_str += f"\n- {key}: {value}"
            
            if context_str:
                prompt_parts.append(f"\nExecution Context:{context_str}")
        
        # Add tool information if tools are available
        if agent.get("tools"):
            prompt_parts.append(f"\nAvailable Tools: {tools_list}")
            prompt_parts.append("""
IMPORTANT: To use a tool, use this exact format:
TOOL_CALL: tool_name(parameter=value)

Examples:
- TOOL_CALL: website_monitor(url=https://google.com, expected_status=200)
- TOOL_CALL: http_client(url=https://api.example.com, method=GET)

If the task requires checking a website or URL, you MUST use the website_monitor tool.
If the task requires making HTTP requests, you MUST use the http_client tool.""")
        else:
            prompt_parts.append("\nYou have no tools available. Respond directly using your knowledge and the rules provided.")
        
        # Final instruction
        prompt_parts.append("""
Follow the rules and formats specified in your background. Be precise and accurate.
If you need to return structured data (like JSON), format it correctly.""")
        
        final_prompt = "\n".join(prompt_parts)
        
        # Log the system prompt for debugging (truncated)
        logger.debug(f"System prompt for {agent['name']} (first 500 chars): {final_prompt[:500]}...")
        
        return final_prompt
    
    def _create_explicit_tool_instruction(self, agent: Dict[str, Any], task: str) -> str:
        """Create explicit instruction to force the LLM to use tools"""
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
                
                return f"""You MUST use the website_monitor tool to complete this task.

Respond with EXACTLY this format (no extra text):
TOOL_CALL: website_monitor(url={url}, expected_status=200)"""
        
        elif any(keyword in task.lower() for keyword in ["api", "request", "get", "post"]):
            if "http_client" in available_tools:
                url_match = re.search(r'https?://[^\s]+', task)
                url = url_match.group(0) if url_match else "https://httpbin.org/get"
                
                return f"""You MUST use the http_client tool to complete this task.

Respond with EXACTLY this format (no extra text):
TOOL_CALL: http_client(url={url}, method=GET)"""
        
        # Generic tool instruction
        tool_list = ", ".join(available_tools)
        return f"""You have these tools available: {tool_list}

You MUST use one of these tools. Respond with EXACTLY this format:
TOOL_CALL: tool_name(parameter=value)

For website checking: TOOL_CALL: website_monitor(url=https://example.com, expected_status=200)
For HTTP requests: TOOL_CALL: http_client(url=https://api.example.com, method=GET)

Use the appropriate tool for: "{task}" """
    
    def _create_minimal_tool_call(self, agent: Dict[str, Any], task: str) -> Optional[Dict[str, Any]]:
        """Create minimal tool call as absolute last resort"""
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
    
    # Keep the old method for backward compatibility but mark it as deprecated
    def _build_simple_system_prompt(
        self, 
        agent: Dict[str, Any], 
        task: str, 
        context: Dict[str, Any]
    ) -> str:
        """DEPRECATED: Use _build_comprehensive_system_prompt instead"""
        logger.warning("Using deprecated _build_simple_system_prompt. Please use _build_comprehensive_system_prompt")
        return self._build_comprehensive_system_prompt(agent, task, context)
    
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
        """Generate response with explicit task instruction using LLM manager"""
        model_name = agent.get("ollama_model", self.config.default_model)
        
        # Add task to chat history for first iteration
        if iteration == 1:
            chat_history.append({"role": "user", "content": task})
        
        # Use the new LLM manager interface
        response = await self.llm_manager.generate_response(
            prompt=system_prompt,
            model=model_name,
            chat_history=chat_history
        )
        
        return response
    
    async def _generate_with_messages(
        self, 
        agent: Dict[str, Any], 
        chat_history: List[Dict[str, str]], 
        system_prompt: str
    ) -> str:
        """Generate response using chat history and system prompt"""
        model_name = agent.get("ollama_model", self.config.default_model)
        
        # Convert chat history to messages for the LLM manager
        messages = []
        
        # Add system message first if we have a system prompt
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        
        # Add chat history
        for msg in chat_history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        
        # Create generation config
        config = GenerationConfig(
            temperature=0.7,
            max_tokens=None,
            stream=False
        )
        
        # Generate using the provider directly for more control
        provider_name, resolved_model = self.llm_manager._resolve_model(model_name)
        provider = self.llm_manager.get_provider(provider_name)
        
        if provider:
            response_obj = await provider.generate_response(messages, resolved_model, config)
            return response_obj.content
        else:
            # Fallback to the simpler interface
            return await self.llm_manager.generate_response(
                prompt=chat_history[-1]["content"] if chat_history else "",
                model=model_name,
                chat_history=chat_history[:-1] if chat_history else []
            )
    
    def _parse_tool_calls_aggressive(self, response: str) -> List[Dict[str, Any]]:
        """Aggressive tool call parsing with multiple patterns and duplicate prevention"""
        tool_calls = []
        
        logger.debug(f"Parsing response for tool calls: {response[:200]}...")
        
        # Primary pattern - most reliable
        primary_pattern = r'TOOL_CALL:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)'
        matches = re.findall(primary_pattern, response, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            try:
                tool_name, params_str = match
                tool_name = tool_name.strip()
                
                # Skip if tool name is invalid
                if tool_name.lower() in ['tool_name', 'tool', 'name']:
                    continue
                
                # Validate tool exists
                if not self.memory_manager.get_tool(tool_name):
                    logger.warning(f"Tool {tool_name} not found, skipping")
                    continue
                
                parameters = self._parse_parameters_simple(params_str)
                
                # Validate URL parameter for website_monitor
                if tool_name == "website_monitor" and "url" in parameters:
                    url = str(parameters["url"]).strip().strip('"\'')
                    
                    # Skip if URL is actually the tool name (parsing error)
                    if url == "website_monitor" or url == tool_name:
                        logger.warning(f"Skipping invalid URL parameter: {url}")
                        continue
                    
                    # Fix URL format
                    if not url.startswith(('http://', 'https://')):
                        if url.startswith('www.'):
                            url = f"https://{url}"
                        elif '.' in url and not url.startswith(('ftp://', 'file://')):
                            url = f"https://{url}"
                    
                    parameters["url"] = url
                
                # Create tool call
                tool_call = {
                    "tool_name": tool_name,
                    "parameters": parameters
                }
                
                # Strict duplicate checking - exact match on tool name and parameters
                is_duplicate = False
                for existing_call in tool_calls:
                    if (existing_call["tool_name"] == tool_name and 
                        existing_call["parameters"] == parameters):
                        is_duplicate = True
                        logger.debug(f"Skipping duplicate tool call: {tool_name}")
                        break
                
                if not is_duplicate:
                    tool_calls.append(tool_call)
                    logger.info(f"Parsed tool call: {tool_name} with {parameters}")
            
            except Exception as e:
                logger.error(f"Failed to parse tool call from match {match}: {e}")
                continue
        
        # If no matches found with primary pattern, try fallback patterns
        if not tool_calls:
            logger.debug("No matches with primary pattern, trying fallback patterns")
            
            fallback_patterns = [
                r'TOOL_CALL\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)',
                r'tool_call:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)',
            ]
            
            for pattern in fallback_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        tool_name, params_str = match
                        tool_name = tool_name.strip()
                        
                        if not self.memory_manager.get_tool(tool_name):
                            continue
                        
                        parameters = self._parse_parameters_simple(params_str)
                        
                        # Same validation as primary pattern
                        if tool_name == "website_monitor" and "url" in parameters:
                            url = str(parameters["url"]).strip().strip('"\'')
                            if url == "website_monitor" or url == tool_name:
                                continue
                            
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
                        is_duplicate = False
                        for existing_call in tool_calls:
                            if (existing_call["tool_name"] == tool_name and 
                                existing_call["parameters"] == parameters):
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            tool_calls.append(tool_call)
                            logger.info(f"Parsed tool call (fallback): {tool_name} with {parameters}")
                            break  # Stop at first successful fallback parse
                    
                    except Exception as e:
                        logger.error(f"Failed to parse fallback tool call: {e}")
                        continue
                
                if tool_calls:  # Stop if we found something
                    break
        
        logger.info(f"Total tool calls parsed: {len(tool_calls)}")
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
        """Build chat history from memory entries"""
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
        """Get agent status with memory information"""
        agent = self.memory_manager.get_agent(agent_name)
        if not agent:
            return {"status": "not_found"}
        
        recent_memory = self.memory_manager.get_agent_memory(
            agent_name, 
            limit=self.config.max_agent_memory_entries
        )
        
        memory_stats = self.memory_manager.get_memory_stats()
        agent_memory_count = memory_stats.get("memory_per_agent", {}).get(agent_name, 0)
        
        return {
            "status": "active" if agent["enabled"] else "disabled",
            "name": agent["name"],
            "role": agent["role"],
            "tools": agent["tools"],
            "model": agent["ollama_model"],
            "recent_activity": len(recent_memory),
            "total_memory_entries": agent_memory_count,
            "memory_limit": self.config.max_agent_memory_entries,
            "last_update": agent["updated_at"]
        }