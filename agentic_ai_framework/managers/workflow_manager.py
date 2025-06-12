"""
managers/workflow_manager.py - Debug Version with Enhanced Logging

This version includes extensive debugging to identify variable resolution issues.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Debug workflow manager with enhanced logging"""
    
    def __init__(self, agent_manager, tool_manager, memory_manager):
        self.agent_manager = agent_manager
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager
        logger.info("Initialized debug workflow manager")
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute workflow with input schema support"""
        context = context or {}
    
        workflow = self.memory_manager.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow {workflow_name} not found")

        if not workflow.get("enabled", True):
            raise ValueError(f"Workflow {workflow_name} is disabled")

        logger.info(f"Starting workflow {workflow_name} with initial context: {context}")
    
        # NEW: Validate input against schema if present
        input_schema = workflow.get("input_schema")
        if input_schema:
            validation_error = self._validate_input_schema(input_schema, context)
            if validation_error:
                raise ValueError(f"Input validation failed: {validation_error}")
            logger.info("Input validation passed")
    
        results = []
        workflow_context = context.copy()
        previous_step_result = None  # NEW: Track previous step result
    
        for i, step in enumerate(workflow["steps"]):
            try:
                logger.info(f"=== STEP {i+1}/{len(workflow['steps'])} ===")
                logger.info(f"Step definition: {step}")
                logger.info(f"Current context keys: {list(workflow_context.keys())}")
            
                # NEW: Handle input source for this step
                step_input_context = self._prepare_step_input(
                    step, workflow_context, previous_step_result, i
                )
            
                # Resolve variables in step parameters
                resolved_step = self._resolve_variables(step, step_input_context)
                logger.info(f"Resolved step: {resolved_step}")
            
                if resolved_step["type"] == "agent":
                    result = await self._execute_agent_step(resolved_step, step_input_context)
                    # Try to parse JSON from agent response
                    result = self._parse_agent_result(result)
                
                elif resolved_step["type"] == "tool":
                    result = await self._execute_tool_step(resolved_step, step_input_context)
                    logger.info(f"Tool result type: {type(result)}")
                    logger.info(f"Tool result: {result}")
                else:
                    raise ValueError(f"Unknown step type: {resolved_step['type']}")
            
                # Store result in context if context_key is specified
                if resolved_step.get("context_key"):
                    context_key = resolved_step["context_key"]
                    workflow_context[context_key] = result
                    logger.info(f"Stored result in context key '{context_key}'")
            
                # Update previous step result
                previous_step_result = result
            
                results.append({
                    "step": i + 1,
                    "type": resolved_step["type"],
                    "name": resolved_step["name"],
                    "result": result,
                    "context_key": resolved_step.get("context_key")
                })
            
                logger.info(f"Step {i+1} completed successfully")
            
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
    
        return {
            "workflow_name": workflow_name,
            "status": "completed",
            "steps_executed": len(results),
            "results": results,
            "final_context": workflow_context
        }
    
    def _validate_input_schema(self, input_schema: Dict[str, Any], input_data: Dict[str, Any]) -> Optional[str]:
        """Validate input data against schema"""
        try:
            # Check required fields
            required_fields = input_schema.get("required", [])
            for field in required_fields:
                if field not in input_data:
                    return f"Required field '{field}' is missing"
            
                value = input_data[field]
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    return f"Required field '{field}' cannot be empty"
        
            # Basic type validation
            properties = input_schema.get("properties", {})
            for field_name, field_schema in properties.items():
                if field_name in input_data:
                    expected_type = field_schema.get("type")
                    value = input_data[field_name]
                
                    if expected_type and not self._validate_field_type(value, expected_type):
                        return f"Field '{field_name}' should be of type {expected_type}"
        
            return None
        
        except Exception as e:
            return f"Validation error: {str(e)}"

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate field type against JSON schema type"""
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
            return isinstance(value, expected_python_type)
    
        return True
    
    def _parse_agent_result(self, result: str) -> Any:
        """Parse agent result, trying to extract JSON if possible"""
        logger.info(f"Agent result type: {type(result)}")
        logger.info(f"Agent result (raw): {repr(result)}")
    
        original_result = result
        try:
            if isinstance(result, str):
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', result.strip(), re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"Extracted JSON string: {json_str}")
                    parsed_result = json.loads(json_str)
                    logger.info(f"Successfully parsed JSON: {parsed_result}")
                    return parsed_result
                elif result.strip().startswith('{') and result.strip().endswith('}'):
                    parsed_result = json.loads(result.strip())
                    logger.info(f"Successfully parsed full response as JSON: {parsed_result}")
                    return parsed_result
                else:
                    logger.info("Agent result doesn't look like JSON, keeping as string")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse agent result as JSON: {e}")
            logger.warning(f"Original result: {repr(original_result)}")
    
        return original_result
    
    def _prepare_step_input(
        self, 
        step: Dict[str, Any], 
        workflow_context: Dict[str, Any], 
        previous_step_result: Any, 
        step_index: int
    ) -> Dict[str, Any]:
        """Prepare input context for a step based on its configuration"""
    
        use_previous_output = step.get("use_previous_output", False)
    
        if use_previous_output and step_index > 0 and previous_step_result is not None:
            logger.info(f"Step {step_index + 1} using previous step output as input")
        
            # If previous result is a dict, merge it with workflow context
            if isinstance(previous_step_result, dict):
                step_context = {**workflow_context, **previous_step_result}
            else:
                # If previous result is not a dict, put it in a special key
                step_context = workflow_context.copy()
                step_context["previous_result"] = previous_step_result
        
            logger.info(f"Step input context: {step_context}")
            return step_context
        else:
            logger.info(f"Step {step_index + 1} using workflow input context")
            return workflow_context
    
    async def _execute_agent_step(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Execute an agent step in the workflow"""
        agent_name = step["name"]
        task = step.get("task", "Complete the assigned task")
        
        logger.info(f"Executing agent {agent_name} with task: {task}")
        
        return await self.agent_manager.execute_agent(agent_name, task, context)
    
    async def _execute_tool_step(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Any:
        """Execute a tool step with enhanced debugging"""
        tool_name = step["name"]
        parameters = step.get("parameters", {})
        
        logger.info(f"Tool step parameters before execution: {parameters}")
        
        # Check for None values in parameters
        for param_name, param_value in parameters.items():
            if param_value is None:
                logger.error(f"Parameter '{param_name}' is None! This will cause the tool to fail.")
                logger.error(f"Full parameters: {parameters}")
                raise ValueError(f"Tool parameter '{param_name}' resolved to None")
        
        logger.info(f"Executing tool {tool_name} with parameters: {parameters}")
        
        return await self.tool_manager.execute_tool(tool_name, parameters)
    
    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Enhanced variable substitution with debugging"""
        if not isinstance(text, str):
            return text
        
        logger.debug(f"Substituting variables in: '{text}'")
        logger.debug(f"Available context: {context}")
        
        # Pattern to match {{variable}} or {{object.property}}
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            logger.debug(f"Processing variable: {var_path}")
            
            try:
                # Handle nested property access (e.g., parsed_purl.url)
                if '.' in var_path:
                    parts = var_path.split('.')
                    value = context
                    
                    logger.debug(f"Navigating path: {parts}")
                    for i, part in enumerate(parts):
                        logger.debug(f"  Step {i}: accessing '{part}' in {type(value)}")
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                            logger.debug(f"  Found: {repr(value)}")
                        else:
                            logger.error(f"Cannot access {var_path}: '{part}' not found in {type(value)}")
                            if isinstance(value, dict):
                                logger.error(f"Available keys: {list(value.keys())}")
                            return match.group(0)  # Return original if not found
                    
                    result = str(value) if not isinstance(value, str) else value
                    logger.debug(f"Variable {var_path} resolved to: {repr(result)}")
                    return result
                
                # Simple variable access
                elif var_path in context:
                    value = context[var_path]
                    result = str(value) if not isinstance(value, str) else value
                    logger.debug(f"Variable {var_path} resolved to: {repr(result)}")
                    return result
                else:
                    logger.error(f"Variable {var_path} not found in context")
                    logger.error(f"Available variables: {list(context.keys())}")
                    return match.group(0)  # Keep original if not found
                    
            except Exception as e:
                logger.error(f"Error resolving variable {var_path}: {e}")
                return match.group(0)  # Keep original on error
        
        result = re.sub(pattern, replace_var, text)
        logger.debug(f"Final substitution result: '{result}'")
        return result
    
    def _resolve_variables(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve variables in step definition with debugging"""
        logger.debug(f"Resolving variables in step: {step}")
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
        
        logger.debug(f"Resolved step result: {resolved_step}")
        return resolved_step
    
    def _resolve_dict_variables(
        self, 
        data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively resolve variables in dictionary"""
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
        """Recursively resolve variables in list"""
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
    
    def validate_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a workflow definition"""
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
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_step(self, step: Dict[str, Any], step_number: int) -> List[str]:
        """Validate a single workflow step"""
        errors = []
        
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
    
    def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """Get status of a workflow"""
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