"""
tools/email_checker.py - Email Checking Tool

Tool for checking emails via POP3 and IMAP protocols with SSL support.
Supports reading emails, listing folders, and retrieving email content.
"""

import asyncio
import logging
import ssl
from typing import Dict, Any, List, Optional
from email import message_from_bytes
from email.header import decode_header
from datetime import datetime
import re

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class EmailCheckerTool(BaseTool):
    """Tool for checking emails using POP3 or IMAP protocols"""
    
    @property
    def name(self) -> str:
        return "email_checker"
    
    @property
    def description(self) -> str:
        return "Check emails using POP3 or IMAP protocols with SSL support. Supports reading emails, listing folders, and retrieving email content."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'list_folders', 'check_emails', 'read_email'",
                    "enum": ["list_folders", "check_emails", "read_email"]
                },
                "protocol": {
                    "type": "string",
                    "description": "Email protocol: 'pop3' or 'imap'",
                    "enum": ["pop3", "imap"],
                    "default": "imap"
                },
                "folder": {
                    "type": "string",
                    "description": "Email folder to check (e.g., 'INBOX', 'Sent', 'Drafts')",
                    "default": "INBOX"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of emails to retrieve",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "Only retrieve unread emails",
                    "default": False
                },
                "email_id": {
                    "type": "string",
                    "description": "Email ID to read (required for 'read_email' action)"
                },
                "include_attachments": {
                    "type": "boolean",
                    "description": "Include attachment information in email details",
                    "default": True
                }
            },
            "required": ["action"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute email checking operation
        
        Args:
            parameters: Operation parameters (action, protocol, folder, etc.)
            
        Returns:
            Dictionary with operation results
            
        Raises:
            Exception: If operation fails
        """
        action = parameters["action"]
        protocol = parameters.get("protocol", "imap")
        
        # Get email server configuration from tool config
        server_config = self._get_server_config(protocol)
        
        if action == "list_folders":
            if protocol == "pop3":
                return await self._list_pop3_folders(server_config)
            else:
                return await self._list_imap_folders(server_config)
        
        elif action == "check_emails":
            folder = parameters.get("folder", "INBOX")
            limit = parameters.get("limit", 10)
            unread_only = parameters.get("unread_only", False)
            
            if protocol == "pop3":
                return await self._check_pop3_emails(server_config, folder, limit, unread_only)
            else:
                return await self._check_imap_emails(server_config, folder, limit, unread_only)
        
        elif action == "read_email":
            email_id = parameters.get("email_id")
            if not email_id:
                raise Exception("email_id is required for 'read_email' action")
            
            include_attachments = parameters.get("include_attachments", True)
            folder = parameters.get("folder", "INBOX")
            
            if protocol == "pop3":
                return await self._read_pop3_email(server_config, email_id, include_attachments)
            else:
                return await self._read_imap_email(server_config, email_id, include_attachments, folder)
        
        else:
            raise Exception(f"Unknown action: {action}")
    
    def _get_server_config(self, protocol: str) -> Dict[str, Any]:
        """
        Get server configuration for the specified protocol
        
        Args:
            protocol: Email protocol ('pop3' or 'imap')
            
        Returns:
            Server configuration dictionary
            
        Raises:
            Exception: If required configuration is missing
        """
        if protocol == "pop3":
            host = self.get_config("pop3_host")
            port = self.get_config("pop3_port", 995)  # Default SSL port
            username = self.get_config("pop3_username")
            password = self.get_config("pop3_password")
            use_ssl = self.get_config("pop3_use_ssl", True)
            required_keys = ["pop3_host", "pop3_username", "pop3_password"]
        else:  # imap
            host = self.get_config("imap_host")
            port = self.get_config("imap_port", 993)  # Default SSL port
            username = self.get_config("imap_username")
            password = self.get_config("imap_password")
            use_ssl = self.get_config("imap_use_ssl", True)
            required_keys = ["imap_host", "imap_username", "imap_password"]
        
        if not self.validate_config(required_keys):
            missing_keys = [key for key in required_keys if not self.get_config(key)]
            raise Exception(
                f"{protocol.upper()} configuration missing. Please configure {', '.join(missing_keys)} "
                f"in the agent's tool_configs for email_checker."
            )
        
        return {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "use_ssl": use_ssl
        }
    
    async def _list_pop3_folders(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """List POP3 folders (POP3 doesn't support folders, so return basic info)"""
        return {
            "protocol": "pop3",
            "folders": ["INBOX"],  # POP3 only has one mailbox
            "message": "POP3 protocol doesn't support multiple folders. Only INBOX is available."
        }
    
    async def _list_imap_folders(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """List IMAP folders"""
        try:
            import imaplib
            
            # Create SSL context
            ssl_context = ssl.create_default_context()
            if not config["use_ssl"]:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to IMAP server
            if config["use_ssl"]:
                server = imaplib.IMAP4_SSL(config["host"], config["port"], ssl_context=ssl_context)
            else:
                server = imaplib.IMAP4(config["host"], config["port"])
            
            # Login
            server.login(config["username"], config["password"])
            
            # List folders
            status, folders = server.list()
            if status != "OK":
                raise Exception(f"Failed to list folders: {folders}")
            
            # Parse folder names
            folder_list = []
            for folder in folders:
                if folder is None:
                    continue
                
                # Convert to string and parse
                if isinstance(folder, bytes):
                    folder_str = folder.decode('utf-8')
                elif isinstance(folder, str):
                    folder_str = folder
                else:
                    continue
                
                # Extract folder name from IMAP LIST response
                # Format: (flags) "delimiter" "name"
                match = re.search(r'\(([^)]*)\) "([^"]*)" "([^"]*)"', folder_str)
                if match:
                    flags, delimiter, name = match.groups()
                    folder_list.append({
                        "name": name,
                        "flags": flags.split() if flags else [],
                        "delimiter": delimiter
                    })
            
            server.logout()
            
            return {
                "protocol": "imap",
                "folders": folder_list,
                "message": f"Found {len(folder_list)} folders"
            }
            
        except Exception as e:
            error_msg = f"Failed to list IMAP folders: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _check_pop3_emails(self, config: Dict[str, Any], folder: str, limit: int, unread_only: bool) -> Dict[str, Any]:
        """Check POP3 emails"""
        try:
            import poplib
            
            # Create SSL context
            ssl_context = ssl.create_default_context()
            if not config["use_ssl"]:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to POP3 server
            if config["use_ssl"]:
                server = poplib.POP3_SSL(config["host"], config["port"], context=ssl_context)
            else:
                server = poplib.POP3(config["host"], config["port"])
            
            # Login
            server.user(config["username"])
            server.pass_(config["password"])
            
            # Get email count and sizes
            num_messages = len(server.list()[1])
            
            # Get email list (POP3 doesn't support unread flags)
            emails = []
            start_index = max(1, num_messages - limit + 1)
            
            for i in range(start_index, num_messages + 1):
                try:
                    # Get email headers
                    resp, lines, octets = server.retr(i)
                    email_content = b'\n'.join(lines)
                    email_message = message_from_bytes(email_content)
                    
                    # Extract basic info
                    subject = self._decode_header(email_message.get("Subject", ""))
                    from_addr = self._decode_header(email_message.get("From", ""))
                    to_addr = self._decode_header(email_message.get("To", ""))
                    date = email_message.get("Date", "")
                    
                    emails.append({
                        "id": str(i),
                        "subject": subject,
                        "from": from_addr,
                        "to": to_addr,
                        "date": date,
                        "size": octets,
                        "read": True  # POP3 doesn't track read status
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to read email {i}: {e}")
                    continue
            
            server.quit()
            
            return {
                "protocol": "pop3",
                "folder": folder,
                "total_emails": num_messages,
                "retrieved_emails": len(emails),
                "emails": emails,
                "message": f"Retrieved {len(emails)} emails from POP3 server"
            }
            
        except Exception as e:
            error_msg = f"Failed to check POP3 emails: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _check_imap_emails(self, config: Dict[str, Any], folder: str, limit: int, unread_only: bool) -> Dict[str, Any]:
        """Check IMAP emails"""
        try:
            import imaplib
            
            # Create SSL context
            ssl_context = ssl.create_default_context()
            if not config["use_ssl"]:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to IMAP server
            if config["use_ssl"]:
                server = imaplib.IMAP4_SSL(config["host"], config["port"], ssl_context=ssl_context)
            else:
                server = imaplib.IMAP4(config["host"], config["port"])
            
            # Login
            server.login(config["username"], config["password"])
            
            # Select folder
            status, messages = server.select(folder)
            if status != "OK":
                raise Exception(f"Failed to select folder {folder}: {messages}")
            
            # Search for emails
            if unread_only:
                status, message_ids = server.search(None, "UNSEEN")
            else:
                status, message_ids = server.search(None, "ALL")
            
            if status != "OK":
                raise Exception(f"Failed to search emails: {message_ids}")
            
            # Get email IDs
            email_ids = message_ids[0].decode().split()
            if not email_ids:
                server.logout()
                return {
                    "protocol": "imap",
                    "folder": folder,
                    "total_emails": 0,
                    "retrieved_emails": 0,
                    "emails": [],
                    "message": f"No {'unread ' if unread_only else ''}emails found in {folder}"
                }
            
            # Limit the number of emails
            email_ids = email_ids[-limit:]  # Get the most recent emails
            
            emails = []
            for email_id in email_ids:
                try:
                    # Fetch email headers and flags (using PEEK to avoid marking as read)
                    status, msg_data = server.fetch(email_id, "(BODY.PEEK[HEADER] FLAGS)")
                    if status != "OK" or not msg_data:
                        continue
                    
                    # Parse the response - msg_data is a list of tuples
                    header_data = None
                    flags_data = None
                    
                    for item in msg_data:
                        if isinstance(item, tuple) and len(item) >= 2:
                            if item[1] is not None:
                                if isinstance(item[1], bytes):
                                    # This is the header data
                                    header_data = item[1]
                                elif isinstance(item[1], str) and item[1].startswith('FLAGS'):
                                    # This is the flags data
                                    flags_data = item[1]
                    
                    if not header_data:
                        continue
                    
                    # Parse email headers
                    email_message = message_from_bytes(header_data)
                    
                    # Extract basic info
                    subject = self._decode_header(email_message.get("Subject", ""))
                    from_addr = self._decode_header(email_message.get("From", ""))
                    to_addr = self._decode_header(email_message.get("To", ""))
                    date = email_message.get("Date", "")
                    
                    # Check if email is read by parsing flags
                    is_read = False
                    if flags_data:
                        # Parse flags string like "FLAGS (\\Seen \\Answered)"
                        flags_match = re.search(r'FLAGS \(([^)]*)\)', flags_data)
                        if flags_match:
                            flags = flags_match.group(1).split()
                            is_read = "\\Seen" in flags or "SEEN" in flags
                    
                    emails.append({
                        "id": email_id,
                        "subject": subject,
                        "from": from_addr,
                        "to": to_addr,
                        "date": date,
                        "read": is_read
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to read email {email_id}: {e}")
                    continue
            
            server.logout()
            
            return {
                "protocol": "imap",
                "folder": folder,
                "total_emails": len(email_ids),
                "retrieved_emails": len(emails),
                "emails": emails,
                "message": f"Retrieved {len(emails)} {'unread ' if unread_only else ''}emails from {folder}"
            }
            
        except Exception as e:
            error_msg = f"Failed to check IMAP emails: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _read_pop3_email(self, config: Dict[str, Any], email_id: str, include_attachments: bool) -> Dict[str, Any]:
        """Read a specific POP3 email"""
        try:
            import poplib
            ssl_context = ssl.create_default_context()
            if not config["use_ssl"]:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            if config["use_ssl"]:
                server = poplib.POP3_SSL(config["host"], config["port"], context=ssl_context)
            else:
                server = poplib.POP3(config["host"], config["port"])
            server.user(config["username"])
            server.pass_(config["password"])
            resp, lines, octets = server.retr(int(email_id))
            email_content = b'\n'.join(lines)
            email_message = message_from_bytes(email_content)
            email_data = self._parse_email_message(email_message, include_attachments)
            email_data["id"] = email_id
            email_data["size"] = octets
            email_data["raw_content"] = email_content  # Add raw content
            server.quit()
            return {
                "protocol": "pop3",
                "email": email_data,
                "message": f"Successfully read POP3 email {email_id}"
            }
        except Exception as e:
            error_msg = f"Failed to read POP3 email {email_id}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _read_imap_email(self, config: Dict[str, Any], email_id: str, include_attachments: bool, folder: str) -> Dict[str, Any]:
        """Read a specific IMAP email"""
        try:
            import imaplib
            
            # Create SSL context
            ssl_context = ssl.create_default_context()
            if not config["use_ssl"]:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to IMAP server
            if config["use_ssl"]:
                server = imaplib.IMAP4_SSL(config["host"], config["port"], ssl_context=ssl_context)
            else:
                server = imaplib.IMAP4(config["host"], config["port"])
            
            # Login
            server.login(config["username"], config["password"])
            
            # Select folder
            status, messages = server.select(folder)
            if status != "OK":
                raise Exception(f"Failed to select folder {folder}: {messages}")
            
            # Fetch email content (using PEEK to avoid marking as read)
            status, msg_data = server.fetch(email_id, "(RFC822.PEEK)")
            if status != "OK" or not msg_data:
                raise Exception(f"Failed to fetch email: {msg_data}")
            
            # Parse the response - msg_data is a list of tuples
            email_content = None
            for item in msg_data:
                if isinstance(item, tuple) and len(item) >= 2:
                    if item[1] is not None and isinstance(item[1], bytes):
                        email_content = item[1]
                        break
            
            if not email_content:
                raise Exception("No email content found in response")
            
            # Parse email message
            email_message = message_from_bytes(email_content)
            email_data = self._parse_email_message(email_message, include_attachments)
            email_data["id"] = email_id
            email_data["raw_content"] = email_content
            
            server.logout()
            
            return {
                "protocol": "imap",
                "email": email_data,
                "message": f"Successfully read IMAP email {email_id} from {folder}"
            }
            
        except Exception as e:
            error_msg = f"Failed to read IMAP email {email_id}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _parse_email_message(self, email_message, include_attachments: bool) -> Dict[str, Any]:
        """Parse email message and extract content"""
        # Extract headers
        subject = self._decode_header(email_message.get("Subject", ""))
        from_addr = self._decode_header(email_message.get("From", ""))
        to_addr = self._decode_header(email_message.get("To", ""))
        cc_addr = self._decode_header(email_message.get("Cc", ""))
        bcc_addr = self._decode_header(email_message.get("Bcc", ""))
        date = email_message.get("Date", "")
        message_id = email_message.get("Message-ID", "")
        
        # Extract body content
        body_text = ""
        body_html = ""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    if include_attachments:
                        filename = part.get_filename()
                        if filename:
                            filename = self._decode_header(filename)
                            attachments.append({
                                "filename": filename,
                                "content_type": content_type,
                                "size": len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                            })
                else:
                    payload = part.get_payload(decode=True)
                    if payload:
                        if content_type == "text/plain":
                            body_text = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                        elif content_type == "text/html":
                            body_html = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
        else:
            # Single part message
            payload = email_message.get_payload(decode=True)
            if payload:
                content_type = email_message.get_content_type()
                charset = email_message.get_content_charset() or "utf-8"
                content = payload.decode(charset, errors="ignore")
                
                if content_type == "text/plain":
                    body_text = content
                elif content_type == "text/html":
                    body_html = content
                else:
                    body_text = content
        
        return {
            "subject": subject,
            "from": from_addr,
            "to": to_addr,
            "cc": cc_addr if cc_addr else None,
            "bcc": bcc_addr if bcc_addr else None,
            "date": date,
            "message_id": message_id,
            "body_text": body_text,
            "body_html": body_html,
            "attachments": attachments if include_attachments else [],
            "has_attachments": len(attachments) > 0
        }
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header value"""
        if not header_value:
            return ""
        
        try:
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