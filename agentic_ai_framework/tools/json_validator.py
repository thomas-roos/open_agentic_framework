"""
tools/json_validator.py - JSON Schema Validation Tool

Tool for validating JSON documents against schemas.
Supports SBOM format validation (SPDX, CycloneDX) and custom schemas.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from jsonschema import validate, ValidationError, SchemaError
from jsonschema.validators import Draft7Validator

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class JsonValidatorTool(BaseTool):
    """Tool for validating JSON documents against schemas"""
    
    @property
    def name(self) -> str:
        return "json_validator"
    
    @property
    def description(self) -> str:
        return "Validate JSON documents against schemas. Supports SBOM formats (SPDX, CycloneDX) and custom schemas."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'validate', 'get_schema', 'list_formats'",
                    "enum": ["validate", "get_schema", "list_formats"]
                },
                "json_data": {
                    "type": "string",
                    "description": "JSON data to validate (required for validate action)"
                },
                "schema_type": {
                    "type": "string",
                    "description": "Type of schema to use: 'spdx', 'cyclonedx', 'custom'",
                    "enum": ["spdx", "cyclonedx", "custom"],
                    "default": "spdx"
                },
                "custom_schema": {
                    "type": "object",
                    "description": "Custom JSON schema (required when schema_type is 'custom')"
                },
                "strict": {
                    "type": "boolean",
                    "description": "Whether to use strict validation (fail on warnings)",
                    "default": False
                },
                "extract_errors": {
                    "type": "boolean",
                    "description": "Extract and return detailed validation errors",
                    "default": True
                }
            },
            "required": ["action"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute JSON validation operation
        
        Args:
            parameters: Operation parameters
            
        Returns:
            Dictionary with validation results
            
        Raises:
            Exception: If validation fails or operation fails
        """
        action = parameters["action"]
        
        if action == "validate":
            return await self._validate_json(parameters)
        elif action == "get_schema":
            return await self._get_schema(parameters)
        elif action == "list_formats":
            return await self._list_formats()
        else:
            raise Exception(f"Unknown action: {action}")
    
    async def _validate_json(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON data against schema"""
        json_data = parameters.get("json_data")
        schema_type = parameters.get("schema_type", "spdx")
        custom_schema = parameters.get("custom_schema")
        strict = parameters.get("strict", False)
        extract_errors = parameters.get("extract_errors", True)
        
        if not json_data:
            raise Exception("json_data is required for validate action")
        
        try:
            # Parse JSON data
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            # Get schema
            if schema_type == "custom":
                if not custom_schema:
                    raise Exception("custom_schema is required when schema_type is 'custom'")
                schema = custom_schema
            else:
                schema = self._get_builtin_schema(schema_type)
            
            # Validate
            errors = []
            warnings = []
            
            try:
                validate(instance=data, schema=schema)
                is_valid = True
            except ValidationError as e:
                is_valid = False
                if extract_errors:
                    errors.append({
                        "path": " -> ".join(str(p) for p in e.path),
                        "message": e.message,
                        "validator": e.validator,
                        "validator_value": e.validator_value
                    })
            
            # Additional checks for SBOM formats
            if schema_type in ["spdx", "cyclonedx"] and is_valid:
                additional_checks = self._perform_sbom_checks(data, schema_type)
                warnings.extend(additional_checks.get("warnings", []))
                if strict and warnings:
                    is_valid = False
                    errors.extend(warnings)
            
            return {
                "status": "validated",
                "is_valid": is_valid,
                "schema_type": schema_type,
                "errors": errors if extract_errors else [],
                "warnings": warnings if extract_errors else [],
                "error_count": len(errors),
                "warning_count": len(warnings),
                "message": f"JSON validation {'passed' if is_valid else 'failed'} for {schema_type} schema"
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "is_valid": False,
                "error": f"Invalid JSON format: {e}",
                "message": "JSON data is not valid JSON format"
            }
        except Exception as e:
            error_msg = f"Validation failed: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _get_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema for specified type"""
        schema_type = parameters.get("schema_type", "spdx")
        
        try:
            schema = self._get_builtin_schema(schema_type)
            
            return {
                "status": "retrieved",
                "schema_type": schema_type,
                "schema": schema,
                "message": f"Retrieved {schema_type} schema"
            }
            
        except Exception as e:
            error_msg = f"Failed to get schema: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _list_formats(self) -> Dict[str, Any]:
        """List supported schema formats"""
        formats = [
            {
                "name": "spdx",
                "description": "SPDX (Software Package Data Exchange) format",
                "version": "2.2",
                "url": "https://spdx.github.io/spdx-spec/"
            },
            {
                "name": "cyclonedx",
                "description": "CycloneDX format for SBOM",
                "version": "1.4",
                "url": "https://cyclonedx.org/specification/overview/"
            },
            {
                "name": "custom",
                "description": "Custom JSON schema",
                "version": "Draft 7",
                "url": "https://json-schema.org/"
            }
        ]
        
        return {
            "status": "listed",
            "formats": formats,
            "count": len(formats),
            "message": f"Found {len(formats)} supported schema formats"
        }
    
    def _get_builtin_schema(self, schema_type: str) -> Dict[str, Any]:
        """Get built-in schema for specified type"""
        if schema_type == "spdx":
            return self._get_spdx_schema()
        elif schema_type == "cyclonedx":
            return self._get_cyclonedx_schema()
        else:
            raise Exception(f"Unknown schema type: {schema_type}")
    
    def _get_spdx_schema(self) -> Dict[str, Any]:
        """Get SPDX schema"""
        return {
            "type": "object",
            "required": ["spdxVersion", "dataLicense", "SPDXID", "name"],
            "properties": {
                "spdxVersion": {
                    "type": "string",
                    "pattern": "^SPDX-2\\.[0-9]+$"
                },
                "dataLicense": {
                    "type": "string"
                },
                "SPDXID": {
                    "type": "string",
                    "pattern": "^SPDXRef-"
                },
                "name": {
                    "type": "string"
                },
                "packages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["SPDXID", "name"],
                        "properties": {
                            "SPDXID": {
                                "type": "string",
                                "pattern": "^SPDXRef-"
                            },
                            "name": {
                                "type": "string"
                            },
                            "versionInfo": {
                                "type": "string"
                            },
                            "purl": {
                                "type": "string"
                            },
                            "licenseConcluded": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
        }
    
    def _get_cyclonedx_schema(self) -> Dict[str, Any]:
        """Get CycloneDX schema"""
        return {
            "type": "object",
            "required": ["bomFormat", "specVersion", "version"],
            "properties": {
                "bomFormat": {
                    "type": "string",
                    "enum": ["CycloneDX"]
                },
                "specVersion": {
                    "type": "string",
                    "pattern": "^[0-9]+\\.[0-9]+$"
                },
                "version": {
                    "type": "integer",
                    "minimum": 1
                },
                "components": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["type", "name"],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["application", "framework", "library", "container", "operating-system", "device", "firmware", "file"]
                            },
                            "name": {
                                "type": "string"
                            },
                            "version": {
                                "type": "string"
                            },
                            "purl": {
                                "type": "string"
                            },
                            "licenses": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "license": {
                                            "type": "object",
                                            "properties": {
                                                "id": {
                                                    "type": "string"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _perform_sbom_checks(self, data: Dict[str, Any], schema_type: str) -> Dict[str, List[str]]:
        """Perform additional SBOM-specific checks"""
        warnings = []
        
        if schema_type == "spdx":
            # Check for required SPDX fields
            if "packages" in data and isinstance(data["packages"], list):
                for i, pkg in enumerate(data["packages"]):
                    if not pkg.get("purl"):
                        warnings.append(f"Package {i} missing PURL (recommended for SBOM)")
                    if not pkg.get("licenseConcluded"):
                        warnings.append(f"Package {i} missing license information")
        
        elif schema_type == "cyclonedx":
            # Check for required CycloneDX fields
            if "components" in data and isinstance(data["components"], list):
                for i, comp in enumerate(data["components"]):
                    if not comp.get("purl"):
                        warnings.append(f"Component {i} missing PURL (recommended for SBOM)")
                    if not comp.get("licenses"):
                        warnings.append(f"Component {i} missing license information")
        
        return {"warnings": warnings} 