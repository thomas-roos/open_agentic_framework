"""
managers/tool_manager.py - Tool Discovery and Execution

Manages dynamic tool discovery, registration, and execution.
Handles loading tool classes from the tools directory and executing them with configurations.
"""

import os
import sys
import importlib
import inspect
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ToolManager:
    """Manages tool discovery, registration, and execution"""
    
    def __init__(self, memory_manager, tools_directory: str = "tools"):
        """
        Initialize tool manager
        
        Args:
            memory_manager: Memory manager for persistence
            tools_directory: Directory containing tool implementations
        """
        self.memory_manager = memory_manager
        self.tools_directory = tools_directory
        self.loaded_tools = {}
        logger.info(f"Initialized tool manager with directory: {tools_directory}")
    
    def discover_and_register_tools(self):
        """
        Discover and register all tools in the tools directory
        
        This method scans the tools directory for Python files,
        imports them, and registers any BaseTool subclasses found.
        """
        tools_path = os.path.abspath(self.tools_directory)
        
        if not os.path.exists(tools_path):
            logger.warning(f"Tools directory {tools_path} does not exist")
            return
        
        # Add tools directory to Python path
        parent_dir = os.path.dirname(tools_path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        logger.info(f"Scanning for tools in {tools_path}")
        
        # Discover tool files
        for filename in os.listdir(tools_path):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                
                try:
                    # Import the module
                    full_module_name = f"{self.tools_directory}.{module_name}"
                    
                    # Remove from cache if already imported (for reloading)
                    if full_module_name in sys.modules:
                        importlib.reload(sys.modules[full_module_name])
                    else:
                        module = importlib.import_module(full_module_name)
                    
                    module = sys.modules[full_module_name]
                    
                    # Find tool classes in the module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if self._is_tool_class(obj):
                            try:
                                # Instantiate and register the tool
                                tool_instance = obj()
                                self._register_tool_instance(tool_instance, name)
                                logger.info(f"Loaded tool: {tool_instance.name}")
                            except Exception as e:
                                logger.error(f"Error instantiating tool {name}: {e}")
                                
                except Exception as e:
                    logger.error(f"Error loading tool module {module_name}: {e}")
        
        logger.info(f"Loaded {len(self.loaded_tools)} tools")
    
    def _is_tool_class(self, obj) -> bool:
        """
        Check if a class is a tool class (inherits from BaseTool)
        
        Args:
            obj: Class object to check
            
        Returns:
            True if it's a tool class, False otherwise
        """
        try:
            return (hasattr(obj, '__bases__') and 
                    any(base.__name__ == 'BaseTool' for base in obj.__bases__) and
                    obj.__name__ != 'BaseTool')
        except:
            return False
    
    def _register_tool_instance(self, tool_instance, class_name: str):
        """
        Register a tool instance
        
        Args:
            tool_instance: Instance of the tool
            class_name: Name of the tool class
        """
        # Store in memory
        self.loaded_tools[tool_instance.name] = tool_instance
        
        # Register in database
        try:
            self.memory_manager.register_tool(
                name=tool_instance.name,
                description=tool_instance.description,
                parameters_schema=tool_instance.parameters,
                class_name=class_name,
                enabled=True
            )
            logger.debug(f"Registered tool {tool_instance.name} in database")
        except Exception as e:
            logger.error(f"Error registering tool {tool_instance.name} in database: {e}")
    
    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        agent_name: Optional[str] = None
    ) -> Any:
        """
        Execute a tool with given parameters
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for tool execution
            agent_name: Name of the calling agent (for configuration)
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        # Get tool from loaded tools
        if tool_name not in self.loaded_tools:
            # Try to reload tools
            logger.info(f"Tool {tool_name} not found, reloading tools...")
            self.discover_and_register_tools()
            
            if tool_name not in self.loaded_tools:
                raise ValueError(f"Tool {tool_name} not found or not loaded")
        
        tool_instance = self.loaded_tools[tool_name]
        
        # Get tool configuration if agent is specified
        config = self._get_tool_config(tool_name, agent_name)
        
        # Validate parameters against schema
        self._validate_parameters(tool_instance.parameters, parameters)
        
        # Execute the tool
        try:
            logger.info(f"Executing tool {tool_name} with parameters {parameters}")
            
            # Pass configuration to tool if it supports it
            if hasattr(tool_instance, 'set_config'):
                tool_instance.set_config(config)
            
            result = await tool_instance.execute(parameters)
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise
    
    def _get_tool_config(self, tool_name: str, agent_name: Optional[str]) -> Dict[str, Any]:
        """
        Get tool configuration for a specific agent
        
        Args:
            tool_name: Name of the tool
            agent_name: Name of the agent (optional)
            
        Returns:
            Tool configuration dictionary
        """
        config = {}
        
        if agent_name:
            agent = self.memory_manager.get_agent(agent_name)
            if agent and agent.get("tool_configs"):
                config = agent["tool_configs"].get(tool_name, {})
                logger.debug(f"Retrieved config for tool {tool_name} from agent {agent_name}")
        
        return config
    
    def _validate_parameters(self, schema: Dict[str, Any], parameters: Dict[str, Any]):
        """
        Validate parameters against JSON schema
        
        Args:
            schema: JSON schema for validation
            parameters: Parameters to validate
            
        Raises:
            ValueError: If validation fails
        """
        required_params = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"Required parameter '{param}' is missing")
        
        # Check parameter types (basic validation)
        for param, value in parameters.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type:
                    self._check_parameter_type(param, value, expected_type)
    
    def _check_parameter_type(self, param_name: str, value: Any, expected_type: str):
        """
        Check if parameter value matches expected type
        
        Args:
            param_name: Name of the parameter
            value: Parameter value
            expected_type: Expected type string
            
        Raises:
            ValueError: If type doesn't match
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        if expected_type in type_mapping:
            expected_python_type = type_mapping[expected_type]
            if not isinstance(value, expected_python_type):
                raise ValueError(
                    f"Parameter '{param_name}' should be of type {expected_type}, "
                    f"got {type(value).__name__}"
                )
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information or None if not found
        """
        return self.memory_manager.get_tool(tool_name)
    
    def list_available_tools(self) -> List[str]:
        """
        List all available tool names
        
        Returns:
            List of tool names
        """
        return list(self.loaded_tools.keys())
    
    def get_tool_instance(self, tool_name: str):
        """
        Get tool instance by name
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self.loaded_tools.get(tool_name)
    
    def reload_tools(self):
        """
        Reload all tools from the tools directory
        
        This method clears the loaded tools cache and rediscovers all tools.
        Useful for development and when tools are updated.
        """
        logger.info("Reloading all tools...")
        self.loaded_tools.clear()
        self.discover_and_register_tools()
        logger.info("Tools reloaded successfully")
    
    def get_tools_status(self) -> Dict[str, Any]:
        """
        Get status of all tools
        
        Returns:
            Dictionary with tool status information
        """
        return {
            "total_tools": len(self.loaded_tools),
            "loaded_tools": list(self.loaded_tools.keys()),
            "tools_directory": self.tools_directory
        }