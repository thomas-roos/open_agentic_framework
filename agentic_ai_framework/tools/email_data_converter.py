"""
tools/email_data_converter.py - Email Data Converter Tool

Tool for converting email data from string format to object format for use in workflows.
This tool helps work around template variable serialization issues.
"""

import json
import logging
from typing import Dict, Any, Union

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class EmailDataConverterTool(BaseTool):
    """Tool for converting and validating email data formats"""
    
    @property
    def name(self) -> str:
        return "email_data_converter"
    
    @property
    def description(self) -> str:
        return "Convert email data between different formats and ensure proper object structure for workflow steps"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "email_data": {
                    "type": "string",
                    "description": "Email data as JSON string or object reference"
                },
                "action": {
                    "type": "string",
                    "enum": ["convert_to_object", "extract_sender", "extract_attachments"],
                    "description": "Action to perform on the email data",
                    "default": "convert_to_object"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["object", "json_string"],
                    "description": "Output format for the converted data",
                    "default": "object"
                }
            },
            "required": ["email_data", "action"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email data conversion"""
        
        try:
            email_data = parameters.get("email_data")
            action = parameters.get("action", "convert_to_object")
            output_format = parameters.get("output_format", "object")
            
            if not email_data:
                raise Exception("email_data is required")
            
            # Handle different input formats
            if isinstance(email_data, str):
                parsed_data = self._parse_string_data(email_data)
            else:
                parsed_data = email_data
            
            # Perform the requested action
            if action == "convert_to_object":
                result = self._convert_to_object(parsed_data, output_format)
            elif action == "extract_sender":
                result = self._extract_sender(parsed_data)
            elif action == "extract_attachments":
                result = self._extract_attachments(parsed_data)
            else:
                raise Exception(f"Unknown action: {action}")
            
            return {
                "status": "converted",
                "action": action,
                "result": result,
                "message": f"Successfully performed {action} on email data"
            }
            
        except Exception as e:
            logger.error(f"Email data conversion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Email data conversion failed: {str(e)}"
            }
    
    def _parse_string_data(self, email_data: str) -> Any:
        """Parse string data using multiple methods"""
        
        # Method 1: Try JSON parsing first
        try:
            return json.loads(email_data)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Try Python literal evaluation (handles Python-style strings)
        try:
            import ast
            return ast.literal_eval(email_data)
        except (ValueError, SyntaxError):
            pass
        
        # Method 3: Try to fix common Python->JSON issues and parse again
        try:
            # Replace Python None with JSON null
            fixed_data = email_data.replace("None", "null")
            # Replace Python True/False with JSON true/false
            fixed_data = fixed_data.replace("True", "true").replace("False", "false")
            # Try JSON parsing again
            return json.loads(fixed_data)
        except json.JSONDecodeError:
            pass
        
        # Method 4: If all else fails, treat as template reference
        logger.warning(f"email_data could not be parsed as JSON or Python literal, treating as template reference: {email_data[:100]}...")
        return {
            "status": "template_reference",
            "email_data": email_data,
            "message": "Email data appears to be a template reference"
        }
    
    def _convert_to_object(self, data: Any, output_format: str) -> Any:
        """Convert email data to proper object format"""
        
        # If data is already an object, return as is
        if isinstance(data, dict):
            if output_format == "object":
                return data
            else:
                return json.dumps(data)
        
        # If data is a string, try to parse it
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                if output_format == "object":
                    return parsed
                else:
                    return data  # Already a JSON string
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON string: {data}")
        
        # For other types, convert to string
        if output_format == "object":
            return {"raw_data": str(data)}
        else:
            return json.dumps({"raw_data": str(data)})
    
    def _extract_sender(self, data: Any) -> str:
        """Extract sender email address from email data"""
        
        if isinstance(data, dict):
            # Try different possible paths for sender
            sender = (
                data.get("from") or 
                data.get("sender") or 
                data.get("email", {}).get("from") or
                data.get("parsed_email", {}).get("from")
            )
            
            if sender:
                # Extract email from "Name <email@domain.com>" format
                if "<" in sender and ">" in sender:
                    start = sender.find("<") + 1
                    end = sender.find(">")
                    return sender[start:end]
                return sender
            
            raise Exception("Sender email not found in email data")
        
        raise Exception("Email data must be a dictionary to extract sender")
    
    def _extract_attachments(self, data: Any) -> list:
        """Extract attachment information from email data"""
        
        if isinstance(data, dict):
            # Try different possible paths for attachments
            attachments = (
                data.get("attachments") or
                data.get("email", {}).get("attachments") or
                data.get("parsed_email", {}).get("attachments") or
                []
            )
            
            return attachments
        
        raise Exception("Email data must be a dictionary to extract attachments") 