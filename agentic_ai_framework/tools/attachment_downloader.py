"""
tools/attachment_downloader.py - Attachment Downloader Tool

Tool for downloading email attachments to temporary locations.
Works with email data from EmailCheckerTool and attachment info from EmailParserTool.
"""

import logging
import tempfile
import os
import shutil
from typing import Dict, Any, List, Optional
from email import message_from_bytes, message_from_string
import mimetypes
import hashlib

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class AttachmentDownloaderTool(BaseTool):
    """Tool for downloading email attachments to temporary locations"""
    
    @property
    def name(self) -> str:
        return "attachment_downloader"
    
    @property
    def description(self) -> str:
        return "Download email attachments to temporary locations. Works with email data from email_checker tool and attachment info from email_parser tool."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "email_data": {
                    "type": "object",
                    "description": "Email data object from email_checker tool"
                },
                "attachment_filenames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attachment filenames to download (empty for all)",
                    "default": []
                },
                "download_path": {
                    "type": "string",
                    "description": "Custom download path (optional, uses temp directory if not specified)",
                    "default": ""
                },
                "create_subdirectories": {
                    "type": "boolean",
                    "description": "Create subdirectories for each email",
                    "default": True
                },
                "sanitize_filenames": {
                    "type": "boolean",
                    "description": "Sanitize filenames for filesystem safety",
                    "default": True
                },
                "max_file_size": {
                    "type": "integer",
                    "description": "Maximum file size in bytes (0 for no limit)",
                    "default": 0
                }
            },
            "required": ["email_data"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download email attachments to temporary location
        
        Args:
            parameters: Download parameters including email_data
            
        Returns:
            Dictionary with download results
            
        Raises:
            Exception: If download fails
        """
        email_data = parameters["email_data"]
        attachment_filenames = parameters.get("attachment_filenames", [])
        download_path = parameters.get("download_path", "")
        create_subdirectories = parameters.get("create_subdirectories", True)
        sanitize_filenames = parameters.get("sanitize_filenames", True)
        max_file_size = parameters.get("max_file_size", 0)
        
        try:
            # Get the email message
            email_message = self._get_email_message(email_data)
            
            # Create download directory
            base_download_path = self._create_download_directory(download_path, email_data, create_subdirectories)
            
            # Download attachments
            downloaded_files = await self._download_attachments(
                email_message, 
                base_download_path, 
                attachment_filenames, 
                sanitize_filenames,
                max_file_size
            )
            
            return {
                "status": "downloaded",
                "download_path": base_download_path,
                "downloaded_files": downloaded_files,
                "total_files": len(downloaded_files),
                "total_size": sum(f["size"] for f in downloaded_files),
                "message": f"Successfully downloaded {len(downloaded_files)} attachments"
            }
            
        except Exception as e:
            error_msg = f"Failed to download attachments: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _get_email_message(self, email_data: Dict[str, Any]):
        """Get email message from email data"""
        if "email" in email_data:
            # If email_data contains a parsed email object
            return email_data["email"]
        elif "content" in email_data:
            # If email_data contains raw content
            if isinstance(email_data["content"], bytes):
                return message_from_bytes(email_data["content"])
            else:
                return message_from_string(str(email_data["content"]))
        else:
            raise Exception("Email data must contain 'email' or 'content' field")
    
    def _create_download_directory(self, download_path: str, email_data: Dict[str, Any], create_subdirectories: bool) -> str:
        """Create download directory"""
        if download_path:
            # Use custom path
            base_path = download_path
        else:
            # Use temporary directory
            base_path = tempfile.gettempdir()
        
        if create_subdirectories:
            # Create subdirectory for this email
            email_id = email_data.get("id", "unknown")
            timestamp = email_data.get("headers", {}).get("date_timestamp", "")
            if timestamp:
                from datetime import datetime
                date_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
            else:
                date_str = "unknown_date"
            
            subdir_name = f"email_{email_id}_{date_str}"
            full_path = os.path.join(base_path, subdir_name)
        else:
            full_path = base_path
        
        # Create directory if it doesn't exist
        os.makedirs(full_path, exist_ok=True)
        
        return full_path
    
    async def _download_attachments(self, email_message, download_path: str, attachment_filenames: List[str], sanitize_filenames: bool, max_file_size: int) -> List[Dict[str, Any]]:
        """Download attachments from email message"""
        downloaded_files = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        
                        # Check if we should download this file
                        if attachment_filenames and filename not in attachment_filenames:
                            continue
                        
                        # Download the attachment
                        file_info = await self._download_attachment(
                            part, 
                            filename, 
                            download_path, 
                            sanitize_filenames,
                            max_file_size
                        )
                        
                        if file_info:
                            downloaded_files.append(file_info)
        
        return downloaded_files
    
    async def _download_attachment(self, part, filename: str, download_path: str, sanitize_filenames: bool, max_file_size: int) -> Optional[Dict[str, Any]]:
        """Download a single attachment"""
        try:
            # Get file content
            payload = part.get_payload(decode=True)
            if not payload:
                logger.warning(f"No payload found for attachment: {filename}")
                return None
            
            # Check file size
            file_size = len(payload)
            if max_file_size > 0 and file_size > max_file_size:
                logger.warning(f"Attachment {filename} exceeds max file size: {file_size} > {max_file_size}")
                return None
            
            # Sanitize filename if requested
            if sanitize_filenames:
                safe_filename = self._sanitize_filename(filename)
            else:
                safe_filename = filename
            
            # Create unique filename if file already exists
            file_path = os.path.join(download_path, safe_filename)
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(safe_filename)
                file_path = os.path.join(download_path, f"{name}_{counter}{ext}")
                counter += 1
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(payload)
            
            # Get file info
            file_info = {
                "original_filename": filename,
                "safe_filename": safe_filename,
                "file_path": file_path,
                "size": file_size,
                "content_type": part.get_content_type(),
                "content_id": part.get("Content-ID", ""),
                "md5_hash": hashlib.md5(payload).hexdigest()
            }
            
            # Try to determine file extension
            if filename:
                _, ext = os.path.splitext(filename)
                file_info["extension"] = ext.lower()
            
            logger.info(f"Downloaded attachment: {filename} -> {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to download attachment {filename}: {e}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header value"""
        if not header_value:
            return ""
        
        try:
            from email.header import decode_header
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors="ignore")
                    else:
                        decoded_string += part.decode("utf-8", errors="ignore")
                else:
                    decoded_string += str(part)
            return decoded_string
        except Exception:
            return str(header_value)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem safety"""
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
    
    def cleanup_temp_files(self, download_path: str):
        """Clean up temporary downloaded files"""
        try:
            if os.path.exists(download_path):
                shutil.rmtree(download_path)
                logger.info(f"Cleaned up temporary files: {download_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files {download_path}: {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a downloaded file"""
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            stat = os.stat(file_path)
            file_info = {
                "path": file_path,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "exists": True
            }
            
            # Try to determine content type
            import mimetypes
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type:
                file_info["content_type"] = content_type
            
            return file_info
            
        except Exception as e:
            return {"error": str(e)} 