"""
tools/file_vault.py - Secure File Vault Tool

Tool for securely storing and retrieving files in a temporary vault.
Provides controlled access to files with security restrictions to prevent
execution of malicious files and unauthorized access to system files.
"""

import os
import tempfile
import shutil
import hashlib
import logging
import mimetypes
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import base64

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class FileVaultTool(BaseTool):
    """Secure file vault for temporary file storage and retrieval"""
    
    def __init__(self):
        """Initialize the file vault with a secure temporary directory"""
        super().__init__()
        self.vault_path = None
        self.vault_id = None
        self._initialize_vault()
    
    @property
    def name(self) -> str:
        return "file_vault"
    
    @property
    def description(self) -> str:
        return "Secure file vault for storing and retrieving temporary files. Files are stored in a controlled environment with security restrictions."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'write', 'read', 'list', 'delete', 'info'",
                    "enum": ["write", "read", "list", "delete", "info", "cleanup"]
                },
                "filename": {
                    "type": "string",
                    "description": "Name of the file to operate on (required for write, read, delete, info)"
                },
                "content": {
                    "type": "string",
                    "description": "File content (required for write action)"
                },
                "content_type": {
                    "type": "string",
                    "description": "Type of content: 'text' or 'binary' (base64 encoded)",
                    "enum": ["text", "binary"],
                    "default": "text"
                },
                "encoding": {
                    "type": "string",
                    "description": "Text encoding for text files",
                    "default": "utf-8"
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Whether to overwrite existing files",
                    "default": False
                },
                "pattern": {
                    "type": "string",
                    "description": "File pattern for listing files (e.g., '*.txt')",
                    "default": "*"
                },
                "include_metadata": {
                    "type": "boolean",
                    "description": "Include file metadata in list results",
                    "default": False
                }
            },
            "required": ["action"]
        }
    
    def _initialize_vault(self):
        """Initialize the secure vault directory"""
        # Create a unique vault ID
        import uuid
        self.vault_id = str(uuid.uuid4())[:8]
        
        # Create vault directory in system temp location
        vault_name = f"agentic_vault_{self.vault_id}"
        self.vault_path = os.path.join(tempfile.gettempdir(), vault_name)
        
        # Create the vault directory
        os.makedirs(self.vault_path, exist_ok=True)
        
        # Set restrictive permissions (read/write for owner only)
        os.chmod(self.vault_path, 0o700)
        
        logger.info(f"Initialized file vault: {self.vault_path}")
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file vault operation
        
        Args:
            parameters: Operation parameters
            
        Returns:
            Dictionary with operation results
            
        Raises:
            Exception: If operation fails or security check fails
        """
        action = parameters["action"]
        
        if action == "write":
            return await self._write_file(parameters)
        elif action == "read":
            return await self._read_file(parameters)
        elif action == "list":
            return await self._list_files(parameters)
        elif action == "delete":
            return await self._delete_file(parameters)
        elif action == "info":
            return await self._get_file_info(parameters)
        elif action == "cleanup":
            return await self._cleanup_vault()
        else:
            raise Exception(f"Unknown action: {action}")
    
    async def _write_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Write a file to the vault"""
        filename = parameters.get("filename")
        content = parameters.get("content")
        content_type = parameters.get("content_type", "text")
        encoding = parameters.get("encoding", "utf-8")
        overwrite = parameters.get("overwrite", False)
        
        if not filename:
            raise Exception("filename is required for write action")
        
        if content is None:
            raise Exception("content is required for write action")
        
        # Validate filename
        safe_filename = self._sanitize_filename(filename)
        if safe_filename != filename:
            logger.warning(f"Filename sanitized: {filename} -> {safe_filename}")
        
        # Check for executable extensions
        if self._is_executable_extension(safe_filename):
            raise Exception(f"Executable files are not allowed: {safe_filename}")
        
        # Build file path
        file_path = os.path.join(self.vault_path, safe_filename)
        
        # Check if file exists
        if os.path.exists(file_path) and not overwrite:
            raise Exception(f"File already exists: {safe_filename}. Use overwrite=true to overwrite.")
        
        try:
            # Write content based on type
            if content_type == "text":
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(content)
            elif content_type == "binary":
                # Decode base64 content
                try:
                    binary_content = base64.b64decode(content)
                except Exception as e:
                    raise Exception(f"Invalid base64 content: {e}")
                
                with open(file_path, 'wb') as f:
                    f.write(binary_content)
            else:
                raise Exception(f"Unsupported content type: {content_type}")
            
            # Get file info
            file_info = self._get_file_metadata(file_path)
            
            return {
                "status": "written",
                "filename": safe_filename,
                "file_path": file_path,
                "size": file_info["size"],
                "content_type": content_type,
                "md5_hash": file_info["md5_hash"],
                "message": f"File written successfully: {safe_filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to write file {safe_filename}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _read_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file from the vault"""
        filename = parameters.get("filename")
        
        if not filename:
            raise Exception("filename is required for read action")
        
        # Validate filename
        safe_filename = self._sanitize_filename(filename)
        file_path = os.path.join(self.vault_path, safe_filename)
        
        # Security check: ensure file is within vault
        if not self._is_file_in_vault(file_path):
            raise Exception(f"Access denied: {filename}")
        
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {safe_filename}")
        
        try:
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            is_text = content_type and (content_type.startswith('text/') or content_type == 'application/json')
            
            # Read file content
            if is_text:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content_type = "text"
            else:
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                content = base64.b64encode(binary_content).decode('utf-8')
                content_type = "binary"
            
            # Get file info
            file_info = self._get_file_metadata(file_path)
            
            return {
                "status": "read",
                "filename": safe_filename,
                "content": content,
                "content_type": content_type,
                "size": file_info["size"],
                "md5_hash": file_info["md5_hash"],
                "message": f"File read successfully: {safe_filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to read file {safe_filename}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _list_files(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List files in the vault"""
        pattern = parameters.get("pattern", "*")
        include_metadata = parameters.get("include_metadata", False)
        
        try:
            import glob
            
            # Build pattern path
            pattern_path = os.path.join(self.vault_path, pattern)
            
            # Get matching files
            matching_files = glob.glob(pattern_path)
            
            files = []
            for file_path in matching_files:
                # Only include files (not directories)
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    
                    file_info = {
                        "filename": filename,
                        "file_path": file_path
                    }
                    
                    if include_metadata:
                        metadata = self._get_file_metadata(file_path)
                        file_info.update(metadata)
                    
                    files.append(file_info)
            
            return {
                "status": "listed",
                "files": files,
                "count": len(files),
                "pattern": pattern,
                "vault_path": self.vault_path,
                "message": f"Found {len(files)} files matching pattern: {pattern}"
            }
            
        except Exception as e:
            error_msg = f"Failed to list files: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _delete_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file from the vault"""
        filename = parameters.get("filename")
        
        if not filename:
            raise Exception("filename is required for delete action")
        
        # Validate filename
        safe_filename = self._sanitize_filename(filename)
        file_path = os.path.join(self.vault_path, safe_filename)
        
        # Security check: ensure file is within vault
        if not self._is_file_in_vault(file_path):
            raise Exception(f"Access denied: {filename}")
        
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {safe_filename}")
        
        try:
            # Get file info before deletion
            file_info = self._get_file_metadata(file_path)
            
            # Delete the file
            os.remove(file_path)
            
            return {
                "status": "deleted",
                "filename": safe_filename,
                "size": file_info["size"],
                "message": f"File deleted successfully: {safe_filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to delete file {safe_filename}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _get_file_info(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a file in the vault"""
        filename = parameters.get("filename")
        
        if not filename:
            raise Exception("filename is required for info action")
        
        # Validate filename
        safe_filename = self._sanitize_filename(filename)
        file_path = os.path.join(self.vault_path, safe_filename)
        
        # Security check: ensure file is within vault
        if not self._is_file_in_vault(file_path):
            raise Exception(f"Access denied: {filename}")
        
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {safe_filename}")
        
        try:
            file_info = self._get_file_metadata(file_path)
            
            return {
                "status": "info",
                "filename": safe_filename,
                "file_path": file_path,
                **file_info,
                "message": f"File info retrieved: {safe_filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to get file info for {safe_filename}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _cleanup_vault(self) -> Dict[str, Any]:
        """Clean up the entire vault"""
        try:
            if os.path.exists(self.vault_path):
                shutil.rmtree(self.vault_path)
                logger.info(f"Cleaned up vault: {self.vault_path}")
            
            return {
                "status": "cleaned",
                "vault_path": self.vault_path,
                "message": "Vault cleaned up successfully"
            }
            
        except Exception as e:
            error_msg = f"Failed to cleanup vault: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security"""
        import re
        
        # Remove or replace problematic characters
        # Windows: < > : " | ? * \
        # Unix: / (null byte)
        # Common: control characters
        
        # Replace problematic characters with underscores
        sanitized = re.sub(r'[<>:"|?*\\/\x00-\x1f]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed_file"
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            max_name_length = 255 - len(ext)
            sanitized = name[:max_name_length] + ext
        
        return sanitized
    
    def _is_executable_extension(self, filename: str) -> bool:
        """Check if file has executable extension"""
        executable_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.msi', '.app', '.command', '.sh', '.py', '.pl', '.rb',
            '.php', '.asp', '.aspx', '.jsp', '.cgi', '.dll', '.so', '.dylib'
        }
        
        _, ext = os.path.splitext(filename.lower())
        return ext in executable_extensions
    
    def _is_file_in_vault(self, file_path: str) -> bool:
        """Check if file is within the vault directory"""
        try:
            # Resolve paths to handle symlinks
            vault_real = os.path.realpath(self.vault_path)
            file_real = os.path.realpath(file_path)
            
            # Check if file is within vault directory
            return file_real.startswith(vault_real + os.sep)
        except Exception:
            return False
    
    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        try:
            stat = os.stat(file_path)
            
            # Calculate MD5 hash
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "md5_hash": md5_hash.hexdigest(),
                "content_type": content_type or "application/octet-stream"
            }
            
        except Exception as e:
            logger.warning(f"Failed to get file metadata for {file_path}: {e}")
            return {
                "size": 0,
                "created": 0,
                "modified": 0,
                "md5_hash": "",
                "content_type": "unknown"
            }
    
    def get_vault_info(self) -> Dict[str, Any]:
        """Get vault information"""
        return {
            "vault_id": self.vault_id,
            "vault_path": self.vault_path,
            "exists": os.path.exists(self.vault_path) if self.vault_path else False
        }
    
    def __del__(self):
        """Cleanup vault on deletion"""
        try:
            if hasattr(self, 'vault_path') and self.vault_path and os.path.exists(self.vault_path):
                shutil.rmtree(self.vault_path)
                logger.info(f"Cleaned up vault on deletion: {self.vault_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup vault on deletion: {e}") 