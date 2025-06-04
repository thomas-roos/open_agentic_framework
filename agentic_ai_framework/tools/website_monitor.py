"""
tools/website_monitor.py - Website Monitoring Tool

A tool that checks if a website is online and responsive.
This tool demonstrates the framework's capabilities and serves as an example
for the website monitoring use case described in the documentation.
"""

import aiohttp
import time
import logging
from typing import Dict, Any

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class WebsiteMonitorTool(BaseTool):
    """Tool for monitoring website availability and response time"""
    
    @property
    def name(self) -> str:
        return "website_monitor"
    
    @property
    def description(self) -> str:
        return "Monitor website availability and response time. Checks if a website is online and measures response time."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to monitor (must include http:// or https://)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 10
                },
                "expected_status": {
                    "type": "integer",
                    "description": "Expected HTTP status code",
                    "default": 200
                },
                "check_content": {
                    "type": "string",
                    "description": "Optional text to check for in the response content",
                    "default": ""
                }
            },
            "required": ["url"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute website monitoring check
        
        Args:
            parameters: Tool parameters including url, timeout, etc.
            
        Returns:
            Dictionary containing monitoring results
        """
        url = parameters["url"]
        timeout = parameters.get("timeout", 10)
        expected_status = parameters.get("expected_status", 200)
        check_content = parameters.get("check_content", "")
        
        logger.info(f"Monitoring website: {url}")
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    end_time = time.time()
                    response_time = round((end_time - start_time) * 1000, 2)  # milliseconds
                    
                    # Get response details
                    status_code = response.status
                    content = await response.text()
                    
                    # Check if status code matches expected
                    status_ok = status_code == expected_status
                    
                    # Check content if specified
                    content_ok = True
                    if check_content:
                        content_ok = check_content in content
                    
                    # Determine overall status
                    is_online = status_ok and content_ok
                    
                    result = {
                        "url": url,
                        "status": "online" if is_online else "offline",
                        "status_code": status_code,
                        "response_time_ms": response_time,
                        "expected_status": expected_status,
                        "status_ok": status_ok,
                        "content_ok": content_ok,
                        "timestamp": time.time(),
                        "error": None
                    }
                    
                    if check_content:
                        result["content_check"] = check_content
                        result["content_found"] = content_ok
                    
                    # Add summary message
                    if is_online:
                        result["message"] = f"Website {url} is online (HTTP {status_code}, {response_time}ms)"
                    else:
                        issues = []
                        if not status_ok:
                            issues.append(f"HTTP {status_code} (expected {expected_status})")
                        if not content_ok:
                            issues.append(f"Content check failed")
                        result["message"] = f"Website {url} has issues: {', '.join(issues)}"
                    
                    logger.info(result["message"])
                    return result
                    
        except aiohttp.ClientTimeout:
            error_msg = f"Website {url} timed out after {timeout} seconds"
            logger.warning(error_msg)
            return {
                "url": url,
                "status": "timeout",
                "status_code": None,
                "response_time_ms": timeout * 1000,
                "expected_status": expected_status,
                "status_ok": False,
                "content_ok": False,
                "timestamp": time.time(),
                "error": "timeout",
                "message": error_msg
            }
            
        except aiohttp.ClientError as e:
            error_msg = f"Website {url} connection error: {str(e)}"
            logger.warning(error_msg)
            return {
                "url": url,
                "status": "error",
                "status_code": None,
                "response_time_ms": None,
                "expected_status": expected_status,
                "status_ok": False,
                "content_ok": False,
                "timestamp": time.time(),
                "error": str(e),
                "message": error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error monitoring {url}: {str(e)}"
            logger.error(error_msg)
            return {
                "url": url,
                "status": "error",
                "status_code": None,
                "response_time_ms": None,
                "expected_status": expected_status,
                "status_ok": False,
                "content_ok": False,
                "timestamp": time.time(),
                "error": str(e),
                "message": error_msg
            }