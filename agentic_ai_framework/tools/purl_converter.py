"""
tools/purl_converter.py - PURL to ClearlyDefined URL Converter Tool

A simple tool that converts Package URLs (PURLs) to ClearlyDefined API URLs.
This handles the string manipulation that agents seem to struggle with.
"""

import re
import logging
from typing import Dict, Any

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class PurlConverterTool(BaseTool):
    """Tool for converting PURLs to ClearlyDefined API URLs"""
    
    @property
    def name(self) -> str:
        return "purl_converter"
    
    @property
    def description(self) -> str:
        return "Convert Package URLs (PURLs) to ClearlyDefined API URLs. Handles npm, maven, pypi, nuget, and other package ecosystems."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "purl": {
                    "type": "string",
                    "description": "Package URL in format pkg:type/namespace/name@version or pkg:type/name@version"
                }
            },
            "required": ["purl"]
        }
    
    def _get_provider_for_type(self, package_type: str) -> str:
        """Get the provider name for a given package type"""
        provider_map = {
            "npm": "npmjs",
            "maven": "mavencentral",
            "pypi": "pypi",
            "nuget": "nuget",
            "gem": "rubygems",
            "cargo": "cratesio",
            "composer": "packagist",
            "conda": "conda-forge",
            "go": "golang",
            "cocoapods": "cocoapods"
        }
        return provider_map.get(package_type, package_type)
    
    def _parse_purl(self, purl: str) -> Dict[str, str]:
        """Parse a PURL into its components"""
        # PURL format: pkg:type/namespace/name@version or pkg:type/name@version
        if not purl.startswith("pkg:"):
            raise ValueError(f"Invalid PURL format: {purl} (must start with 'pkg:')")
        
        # Remove 'pkg:' prefix
        purl_content = purl[4:]
        
        # Split on '@' to separate version
        if '@' not in purl_content:
            raise ValueError(f"Invalid PURL format: {purl} (missing version)")
        
        package_part, version = purl_content.rsplit('@', 1)
        
        # Split package part into components
        parts = package_part.split('/')
        
        if len(parts) < 2:
            raise ValueError(f"Invalid PURL format: {purl} (missing package type or name)")
        
        package_type = parts[0]
        
        if len(parts) == 2:
            # pkg:type/name@version
            namespace = ""
            name = parts[1]
        elif len(parts) == 3:
            # pkg:type/namespace/name@version
            namespace = parts[1]
            name = parts[2]
        else:
            # More complex namespace like pkg:maven/group/subgroup/artifact@version
            # For maven, everything except the last part is namespace
            namespace = "/".join(parts[1:-1])
            name = parts[-1]
        
        # Handle special cases
        if package_type == "npm" and name.startswith("@"):
            # Scoped npm package like pkg:npm/@types/node@version
            # In this case, @types is the namespace and node is the name
            if namespace:
                # This shouldn't happen but handle it
                namespace = f"{namespace}/{name[1:].split('/')[0]}"
                name = name.split('/')[1]
            else:
                scope_and_name = name[1:]  # Remove @
                if '/' in scope_and_name:
                    namespace, name = scope_and_name.split('/', 1)
                else:
                    namespace = scope_and_name
                    name = ""
        
        return {
            "type": package_type,
            "namespace": namespace,
            "name": name,
            "version": version
        }
    
    def _build_clearlydefined_url(self, package_type: str, provider: str, namespace: str, name: str, version: str) -> str:
        """Build ClearlyDefined API URL from components"""
        base_url = "https://api.clearlydefined.io/definitions"
        
        # Handle namespace
        if namespace:
            namespace_part = namespace
        else:
            namespace_part = "-"
        
        url = f"{base_url}/{package_type}/{provider}/{namespace_part}/{name}/{version}"
        return url
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert PURL to ClearlyDefined API URL
        
        Args:
            parameters: Tool parameters with PURL
            
        Returns:
            Dictionary with parsed components and ClearlyDefined URL
        """
        purl = parameters["purl"].strip()
        
        try:
            # Parse PURL
            components = self._parse_purl(purl)
            
            # Get provider
            provider = self._get_provider_for_type(components["type"])
            
            # Build ClearlyDefined URL
            clearlydefined_url = self._build_clearlydefined_url(
                components["type"],
                provider,
                components["namespace"],
                components["name"],
                components["version"]
            )
            
            result = {
                "purl": purl,
                "components": {
                    "type": components["type"],
                    "provider": provider,
                    "namespace": components["namespace"] or "-",
                    "name": components["name"],
                    "version": components["version"]
                },
                "clearlydefined_url": clearlydefined_url,
                "success": True,
                "message": f"Successfully converted PURL to ClearlyDefined URL"
            }
            
            logger.info(f"Converted PURL {purl} to {clearlydefined_url}")
            return result
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"PURL parsing error: {error_msg}")
            return {
                "purl": purl,
                "success": False,
                "error": error_msg,
                "message": f"Failed to parse PURL: {error_msg}"
            }
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"PURL conversion error: {error_msg}")
            return {
                "purl": purl,
                "success": False,
                "error": error_msg,
                "message": f"Failed to convert PURL: {error_msg}"
            }