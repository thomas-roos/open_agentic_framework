"""
managers/workflow_manager.py - Workflow Orchestration

Manages workflow execution and orchestration.
Handles step-by-step execution of complex workflows with variable substitution.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manages workflow execution and orchestration"""
    
    def __init__(self, agent_manager, tool_manager, memory_manager):
        """
        Initialize workflow manager
        
        Args:
            agent_manager: Agent manager for executing agent steps
            tool_manager: Tool manager for executing tool steps
            memory_manager: Memory manager for persistence
        """
        self.agent_manager = agent_manager
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager
        logger.info("Initialized workflow manager")
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow
        
        Args:
            workflow_name: Name of the workflow to execute
            context: Initial workflow context
            
        Returns:
            Workflow execution result
            
        Raises:
            ValueError: If workflow not found or disabled
            Exception: If workflow execution fails
        """
        context = context or {}
        
        # Get workflow definition
        workflow = self.memory_manager.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow {workflow_name} not found")
        
        if not workflow.get("enabled", True):
            raise ValueError(f"Workflow {workflow_name} is disabled")
        
        logger.info(f"Starting workflow {workflow_name}")
        
        results = []
        workflow_context = context.copy()
        
        for i, step in enumerate(workflow["steps"]):
            try:
                logger.info(f"Executing workflow step {i+1}/{len(workflow['steps'])}: {step}")
                
                # Resolve variables in step parameters
                resolved_step = self._resolve_variables(step, workflow_context)
                
                if resolved_step["type"] == "agent":
                    # Execute agent step
                    result = await self._execute_agent_step(resolved_step, workflow_context)
                elif resolved_step["type"] == "tool":
                    # Execute tool step
                    result = await self._execute_tool_step(resolved_step, workflow_context)
                else:
                    raise ValueError(f"Unknown step type: {resolved_step['type']}")
                
                # Store result in context if context_key is specified
                if resolved_step.get("context_key"):
                    workflow_context[resolved_step["context_key"]] = result
                    logger.debug(f"Stored result in context key: {resolved_step['context_key']}")
                
                results.append({
                    "step": i + 1,
                    "type": resolved_step["type"],
                    "name": resolved_step["name"],
                    "result": result,
                    "context_key": resolved_step.get("context_key")
                })
                
                logger.info(f"Workflow step {i+1} completed successfully")
                
            except Exception as e:
                error_msg = f"Error in workflow step {i+1}: {e}"
                logger.error(error_msg)
                results.append({
                    "step": i + 1,
                    "type": step["type"],
                    "name": step["name"],
                    "error": str(e)
                })
                raise Exception(f"Workflow {workflow_name} failed at step {i+1}: {e}")
        
        logger.info(f"Workflow {workflow_name} completed successfully")
        
        return {
            "workflow_name": workflow_name,
            "status": "completed",
            "steps_executed": len(results),
            "results": results,
            "final_context": workflow_context
        }
    
    async def _execute_agent_step(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """
        Execute an agent step in the workflow
        
        Args:
            step: Step configuration
            context: Current workflow context
            
        Returns:
            Agent execution result
        """
        agent_name = step["name"]
        task = step.get("task", "Complete the assigned task")
        
        logger.debug(f"Executing agent {agent_name} with task: {task}")
        
        return await self.agent_manager.execute_agent(agent_name, task, context)
    
    async def _execute_tool_step(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool step in the workflow
        
        Args:
            step: Step configuration
            context: Current workflow context
            
        Returns:
            Tool execution result
        """
        tool_name = step["name"]
        parameters = step.get("parameters", {})
        
        logger.debug(f"Executing tool {tool_name} with parameters: {parameters}")
        
        return await self.tool_manager.execute_tool(tool_name, parameters)
    
    def _resolve_variables(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve variables in step definition using workflow context
        
        Args:
            step: Step configuration with variables
            context: Current workflow context
            
        Returns:
            Step configuration with resolved variables
        """
        resolved_step = {}
        
        for key, value in step.items():
            if isinstance(value, str):
                resolved_step[key] = self._substitute_variables(value, context)
            elif isinstance(value, dict):
                resolved_step[key] = self._resolve_dict_variables(value, context)
            elif isinstance(value, list):
                resolved_step[key] = self._resolve_list_variables(value, context)
            else:
                resolved_step[key] = value
        
        return resolved_step
    
    def _resolve_dict_variables(
        self, 
        data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively resolve variables in dictionary
        
        Args:
            data: Dictionary with potential variables
            context: Current workflow context
            
        Returns:
            Dictionary with resolved variables
        """
        resolved = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                resolved[key] = self._substitute_variables(value, context)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_dict_variables(value, context)
            elif isinstance(value, list):
                resolved[key] = self._resolve_list_variables(value, context)
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_list_variables(
        self, 
        data: List[Any], 
        context: Dict[str, Any]
    ) -> List[Any]:
        """
        Recursively resolve variables in list
        
        Args:
            data: List with potential variables
            context: Current workflow context
            
        Returns:
            List with resolved variables
        """
        resolved = []
        
        for item in data:
            if isinstance(item, str):
                resolved.append(self._substitute_variables(item, context))
            elif isinstance(item, dict):
                resolved.append(self._resolve_dict_variables(item, context))
            elif isinstance(item, list):
                resolved.append(self._resolve_list_variables(item, context))
            else:
                resolved.append(item)
        
        return resolved
    
    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """
        Substitute variables in text using context
        
        Variables are in the format {variable_name}
        
        Args:
            text: Text with potential variables
            context: Current workflow context
            
        Returns:
            Text with substituted variables
        """
        # Pattern to match {variable_name}
        pattern = r'\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name in context:
                value = context[var_name]
                # Convert to string if not already
                return str(value) if not isinstance(value, str) else value
            else:
                # Variable not found, keep original
                logger.warning(f"Variable {var_name} not found in context")
                return match.group(0)
        
        return re.sub(pattern, replace_var, text)
    
    def validate_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a workflow definition
        
        Args:
            workflow_definition: Workflow configuration to validate
            
        Returns:
            Validation result with status and any errors
        """
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["name", "description", "steps"]
        for field in required_fields:
            if field not in workflow_definition:
                errors.append(f"Missing required field: {field}")
        
        # Validate steps
        steps = workflow_definition.get("steps", [])
        if not steps:
            errors.append("Workflow must have at least one step")
        
        for i, step in enumerate(steps):
            step_errors = self._validate_step(step, i + 1)
            errors.extend(step_errors)
        
        # Check for circular dependencies or invalid variable references
        context_keys = set()
        for step in steps:
            if step.get("context_key"):
                context_keys.add(step["context_key"])
        
        for i, step in enumerate(steps):
            # Check if step references variables that don't exist yet
            referenced_vars = self._extract_variables(step)
            for var in referenced_vars:
                if var not in context_keys:
                    warnings.append(f"Step {i+1} references undefined variable: {var}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_step(self, step: Dict[str, Any], step_number: int) -> List[str]:
        """
        Validate a single workflow step
        
        Args:
            step: Step configuration
            step_number: Step number for error reporting
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        if "type" not in step:
            errors.append(f"Step {step_number}: Missing 'type' field")
            return errors
        
        if "name" not in step:
            errors.append(f"Step {step_number}: Missing 'name' field")
            return errors
        
        step_type = step["type"]
        if step_type not in ["agent", "tool"]:
            errors.append(f"Step {step_number}: Invalid type '{step_type}'. Must be 'agent' or 'tool'")
        
        # Validate agent steps
        if step_type == "agent":
            agent_name = step["name"]
            agent = self.memory_manager.get_agent(agent_name)
            if not agent:
                errors.append(f"Step {step_number}: Agent '{agent_name}' not found")
        
        # Validate tool steps
        elif step_type == "tool":
            tool_name = step["name"]
            tool = self.memory_manager.get_tool(tool_name)
            if not tool:
                errors.append(f"Step {step_number}: Tool '{tool_name}' not found")
        
        return errors
    
    def _extract_variables(self, data: Any) -> List[str]:
        """
        Extract variable names from data structure
        
        Args:
            data: Data to scan for variables
            
        Returns:
            List of variable names found
        """
        variables = []
        
        if isinstance(data, str):
            pattern = r'\{([^}]+)\}'
            matches = re.findall(pattern, data)
            variables.extend(matches)
        elif isinstance(data, dict):
            for value in data.values():
                variables.extend(self._extract_variables(value))
        elif isinstance(data, list):
            for item in data:
                variables.extend(self._extract_variables(item))
        
        return variables
    
    def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """
        Get status of a workflow
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Workflow status information
        """
        workflow = self.memory_manager.get_workflow(workflow_name)
        if not workflow:
            return {"status": "not_found"}
        
        validation = self.validate_workflow(workflow)
        
        return {
            "status": "active" if workflow["enabled"] else "disabled",
            "name": workflow["name"],
            "description": workflow["description"],
            "steps_count": len(workflow["steps"]),
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "last_update": workflow["updated_at"]
        }