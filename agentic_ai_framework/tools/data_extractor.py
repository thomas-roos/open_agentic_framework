"""
tools/data_extractor.py - Enhanced Data Extraction Tool with Dynamic Node Finding

This version can traverse arrays and find nodes based on criteria, not just fixed indices.
"""

import json
import re
import logging
from typing import Dict, Any, Union, List, Optional

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataExtractorTool(BaseTool):
    """Enhanced tool for extracting data with dynamic node finding capabilities"""
    
    @property
    def name(self) -> str:
        return "data_extractor"
    
    @property
    def description(self) -> str:
        return "Extract data from JSON objects and text using smart path queries that can find nodes dynamically."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_data": {
                    "type": "string",
                    "description": "Source data as JSON string"
                },
                "extractions": {
                    "type": "array",
                    "description": "List of extraction operations",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name for extracted value"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["path", "regex", "literal", "find"],
                                "description": "Extraction type"
                            },
                            "query": {
                                "type": "string", 
                                "description": "Path query, pattern, or find criteria"
                            },
                            "default": {
                                "type": "string",
                                "description": "Default value as string"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["text", "number", "boolean"],
                                "default": "text",
                                "description": "Output format"
                            },
                            "find_criteria": {
                                "type": "object",
                                "description": "Criteria for finding nodes in arrays",
                                "properties": {
                                    "array_path": {"type": "string"},
                                    "match_field": {"type": "string"},
                                    "match_value": {"type": "string"},
                                    "extract_field": {"type": "string"}
                                }
                            }
                        },
                        "required": ["name", "type", "query"]
                    }
                }
            },
            "required": ["source_data", "extractions"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data extraction with enhanced node finding"""
        
        try:
            # Convert everything to safe types immediately
            source_data_str = str(parameters.get("source_data", "{}"))
            extractions_raw = parameters.get("extractions", [])
            
            # Convert extractions to safe format
            safe_extractions = []
            if isinstance(extractions_raw, list):
                for item in extractions_raw:
                    if isinstance(item, dict):
                        safe_extraction = {
                            "name": str(item.get("name", "unknown")),
                            "type": str(item.get("type", "path")),
                            "query": str(item.get("query", "")),
                            "default": str(item.get("default", "")),
                            "format": str(item.get("format", "text")),
                            "find_criteria": item.get("find_criteria", {})
                        }
                        safe_extractions.append(safe_extraction)
            
            logger.info(f"Processing {len(safe_extractions)} extractions")
            
            # Parse JSON safely
            try:
                source_obj = json.loads(source_data_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {e}")
                source_obj = {"raw_text": source_data_str}
            
            # Process each extraction
            results = {}
            success_count = 0
            
            for extraction in safe_extractions:
                try:
                    name = extraction["name"]
                    ext_type = extraction["type"]
                    query = extraction["query"]
                    default_val = extraction["default"]
                    format_type = extraction["format"]
                    find_criteria = extraction["find_criteria"]
                    
                    # Extract value based on type
                    if ext_type == "path":
                        value = self._extract_path_safe(source_obj, query, default_val)
                    elif ext_type == "smart_path":
                        value = self._extract_smart_path(source_obj, query, default_val)
                    elif ext_type == "find":
                        value = self._find_in_data(source_obj, find_criteria, default_val)
                    elif ext_type == "regex":
                        value = self._extract_regex_safe(source_data_str, query, default_val)
                    elif ext_type == "literal":
                        value = query
                    else:
                        value = default_val
                    
                    # Format value
                    formatted_value = self._format_safe(value, format_type)
                    
                    # Store result (ensure key is string)
                    results[str(name)] = formatted_value
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Extraction failed for {name}: {e}")
                    results[str(extraction.get("name", "unknown"))] = extraction.get("default", "")
            
            # Return safe result
            return {
                "extracted_data": results,
                "extraction_count": len(safe_extractions),
                "success_count": success_count,
                "message": f"Extracted {success_count}/{len(safe_extractions)} values"
            }
            
        except Exception as e:
            logger.error(f"Data extraction completely failed: {e}")
            return {
                "extracted_data": {},
                "extraction_count": 0,
                "success_count": 0,
                "message": f"Extraction failed: {str(e)}",
                "error": str(e)
            }
    
    def _extract_path_safe(self, data: Any, path: str, default: str) -> str:
        """Ultra safe path extraction that always returns a string"""
        try:
            if not path or not isinstance(data, dict):
                return default
            
            current = data
            parts = str(path).split('.')
            
            for part in parts:
                if not part:
                    continue
                
                # Handle array indices
                if part.isdigit():
                    index = int(part)
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        return default
                elif isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    # If we hit an array but part is not a digit, try to find by key
                    found = False
                    for item in current:
                        if isinstance(item, dict) and part in item:
                            current = item[part]
                            found = True
                            break
                    if not found:
                        return default
                else:
                    return default
                    
                if current is None:
                    return default
            
            # Convert result to string
            return self._convert_to_string(current, default)
                
        except Exception as e:
            logger.debug(f"Path extraction error: {e}")
            return default
    
    def _extract_smart_path(self, data: Any, path: str, default: str) -> str:
        """Smart path extraction that can handle arrays by searching"""
        try:
            if not path:
                return default
                
            # Handle special syntax like results[name=http_client].result.content
            if '[' in path and ']' in path:
                return self._extract_with_array_search(data, path, default)
            else:
                return self._extract_path_safe(data, path, default)
                
        except Exception as e:
            logger.debug(f"Smart path extraction error: {e}")
            return default
    
    def _extract_with_array_search(self, data: Any, path: str, default: str) -> str:
        """Extract using array search syntax like: results[name=http_client].result.content"""
        try:
            parts = []
            current_part = ""
            in_brackets = False
            
            # Parse the path with bracket syntax
            for char in path:
                if char == '[':
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                    in_brackets = True
                elif char == ']':
                    if in_brackets and current_part:
                        parts.append(f"[{current_part}]")
                        current_part = ""
                    in_brackets = False
                elif char == '.' and not in_brackets:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                else:
                    current_part += char
            
            if current_part:
                parts.append(current_part)
            
            # Navigate through the path
            current = data
            for part in parts:
                if part.startswith('[') and part.endswith(']'):
                    # Array search syntax
                    search_criteria = part[1:-1]  # Remove brackets
                    if '=' in search_criteria:
                        field, value = search_criteria.split('=', 1)
                        current = self._find_in_array(current, field, value)
                    else:
                        # Treat as index
                        try:
                            index = int(search_criteria)
                            if isinstance(current, list) and 0 <= index < len(current):
                                current = current[index]
                            else:
                                return default
                        except ValueError:
                            return default
                else:
                    # Regular field access
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        return default
                
                if current is None:
                    return default
            
            return self._convert_to_string(current, default)
            
        except Exception as e:
            logger.debug(f"Array search extraction error: {e}")
            return default
    
    def _find_in_array(self, array_data: Any, field: str, value: str) -> Any:
        """Find an item in an array where field matches value"""
        if not isinstance(array_data, list):
            return None
        
        for item in array_data:
            if isinstance(item, dict):
                item_value = str(item.get(field, ""))
                if item_value == value:
                    return item
        
        return None
    
    def _find_in_data(self, data: Any, criteria: Dict[str, str], default: str) -> str:
        """Find data using flexible criteria"""
        try:
            array_path = criteria.get("array_path", "")
            match_field = criteria.get("match_field", "")
            match_value = criteria.get("match_value", "")
            extract_field = criteria.get("extract_field", "")
            
            if not all([array_path, match_field, match_value, extract_field]):
                return default
            
            # Get the array
            array_data = self._extract_path_safe(data, array_path, None)
            if array_data == default:  # Failed to get array
                return default
            
            # Parse array_data if it's a string representation
            if isinstance(array_data, str) and array_data.startswith('['):
                try:
                    array_data = json.loads(array_data)
                except:
                    return default
            
            # Find matching item
            if isinstance(array_data, list):
                for item in array_data:
                    if isinstance(item, dict):
                        if str(item.get(match_field, "")) == match_value:
                            result = item.get(extract_field)
                            return self._convert_to_string(result, default)
            
            return default
            
        except Exception as e:
            logger.debug(f"Find in data error: {e}")
            return default
    
    def _convert_to_string(self, value: Any, default: str) -> str:
        """Convert any value to string safely"""
        if value is None:
            return default
        elif isinstance(value, (str, int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return ", ".join(str(x) for x in value if x is not None)
        elif isinstance(value, dict):
            return json.dumps(value, separators=(',', ':'))
        else:
            return str(value)
    
    def _extract_regex_safe(self, text: str, pattern: str, default: str) -> str:
        """Ultra safe regex extraction"""
        try:
            if not text or not pattern:
                return default
            
            matches = re.findall(str(pattern), str(text))
            if not matches:
                return default
            elif len(matches) == 1:
                match = matches[0]
                return str(match) if isinstance(match, str) else str(match[0]) if match else default
            else:
                return ", ".join(str(m) for m in matches if m)
                
        except Exception as e:
            logger.debug(f"Regex extraction error: {e}")
            return default
    
    def _format_safe(self, value: str, format_type: str) -> Union[str, int, float, bool]:
        """Ultra safe formatting that handles type conversion"""
        try:
            if format_type == "number":
                try:
                    if '.' in str(value):
                        return float(value)
                    else:
                        return int(value)
                except (ValueError, TypeError):
                    return 0
            elif format_type == "boolean":
                return str(value).lower() in ('true', '1', 'yes', 'on', 'mit', 'apache')
            else:
                return str(value)
        except Exception:
            return str(value)