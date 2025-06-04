"""
tools/http_client.py - HTTP Client Tool

Tool for performing HTTP requests to web APIs and websites.
Supports GET, POST, PUT, DELETE methods with custom headers and authentication.
"""

import aiohttp
import json
import logging
from typing import Dict, Any, Optional

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class HttpClientTool(BaseTool):
    """Tool for performing HTTP requests"""
    
    @property
    def name(self) -> str:
        return "http_client"
    
    @property
    def description(self) -> str:
        return "Perform HTTP requests (GET, POST, PUT, DELETE) to web APIs and websites. Supports custom headers and authentication."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to request"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method: GET, POST, PUT, DELETE",
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "Optional HTTP headers as key-value pairs",
                    "default": {}
                },
                "data": {
                    "type": "object",
                    "description": "Request body data for POST/PUT requests",
                    "default": {}
                },
                "params": {
                    "type": "object",
                    "description": "URL query parameters as key-value pairs",
                    "default": {}
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Whether to follow HTTP redirects",
                    "default": True
                },
                "verify_ssl": {
                    "type": "boolean",
                    "description": "Whether to verify SSL certificates",
                    "default": True
                }
            },
            "required": ["url"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute HTTP request
        
        Args:
            parameters: Request parameters (url, method, headers, etc.)
            
        Returns:
            Dictionary with response details
            
        Raises:
            Exception: If request fails
        """
        url = parameters["url"]
        method = parameters.get("method", "GET").upper()
        headers = parameters.get("headers", {})
        data = parameters.get("data", {})
        params = parameters.get("params", {})
        timeout = parameters.get("timeout", 30)
        follow_redirects = parameters.get("follow_redirects", True)
        verify_ssl = parameters.get("verify_ssl", True)
        
        # Add authentication from config if available
        auth_headers = self._get_auth_headers()
        headers.update(auth_headers)
        
        logger.info(f"Making {method} request to {url}")
        
        try:
            # Configure aiohttp session
            connector = aiohttp.TCPConnector(
                verify_ssl=verify_ssl,
                limit=10
            )
            
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout_config
            ) as session:
                
                # Prepare request kwargs
                request_kwargs = {
                    "headers": headers,
                    "params": params,
                    "allow_redirects": follow_redirects
                }
                
                # Add data for POST/PUT requests
                if method in ["POST", "PUT", "PATCH"] and data:
                    if isinstance(data, dict):
                        request_kwargs["json"] = data
                    else:
                        request_kwargs["data"] = data
                
                # Make the request
                async with session.request(method, url, **request_kwargs) as response:
                    # Get response content
                    try:
                        # Try to parse as JSON first
                        content = await response.json()
                        content_type = "json"
                    except:
                        # Fall back to text
                        content = await response.text()
                        content_type = "text"
                    
                    # Build result
                    result = {
                        "url": str(response.url),
                        "method": method,
                        "status_code": response.status,
                        "status_text": response.reason,
                        "headers": dict(response.headers),
                        "content": content,
                        "content_type": content_type,
                        "content_length": len(str(content)),
                        "success": 200 <= response.status < 300,
                        "redirected": str(response.url) != url,
                        "encoding": response.get_encoding()
                    }
                    
                    # Add request details for debugging
                    result["request"] = {
                        "url": url,
                        "method": method,
                        "headers": {k: v for k, v in headers.items() if k.lower() not in ["authorization", "api-key"]},  # Don't log sensitive headers
                        "params": params
                    }
                    
                    if method in ["POST", "PUT", "PATCH"]:
                        result["request"]["data_sent"] = bool(data)
                    
                    # Add success message
                    if result["success"]:
                        result["message"] = f"HTTP {method} to {url} successful (status {response.status})"
                        logger.info(result["message"])
                    else:
                        result["message"] = f"HTTP {method} to {url} failed (status {response.status})"
                        logger.warning(result["message"])
                    
                    return result
                    
        except aiohttp.ClientTimeout:
            error_msg = f"HTTP request to {url} timed out after {timeout} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except aiohttp.ClientError as e:
            error_msg = f"HTTP client error for {url}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during HTTP request to {url}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers from configuration
        
        Returns:
            Dictionary of authentication headers
        """
        auth_headers = {}
        
        # API Key authentication
        api_key = self.get_config("api_key")
        if api_key:
            api_key_header = self.get_config("api_key_header", "X-API-Key")
            auth_headers[api_key_header] = api_key
        
        # Bearer token authentication
        bearer_token = self.get_config("bearer_token")
        if bearer_token:
            auth_headers["Authorization"] = f"Bearer {bearer_token}"
        
        # Basic authentication
        basic_username = self.get_config("basic_username")
        basic_password = self.get_config("basic_password")
        if basic_username and basic_password:
            import base64
            credentials = base64.b64encode(f"{basic_username}:{basic_password}".encode()).decode()
            auth_headers["Authorization"] = f"Basic {credentials}"
        
        # Custom headers from config
        custom_headers = self.get_config("custom_headers", {})
        if isinstance(custom_headers, dict):
            auth_headers.update(custom_headers)
        
        return auth_headers