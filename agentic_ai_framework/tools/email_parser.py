"""
tools/email_parser.py - Email Parser Tool

Tool for parsing email content and extracting different content types.
Works with email data from EmailCheckerTool to parse subject, body, headers, etc.
"""

import logging
import tempfile
import os
from typing import Dict, Any, List, Optional
from email import message_from_bytes, message_from_string
from email.header import decode_header
from email.utils import parsedate_to_datetime
import mimetypes
import base64

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class EmailParserTool(BaseTool):
    """Tool for parsing email content and extracting metadata"""
    
    @property
    def name(self) -> str:
        return "email_parser"
    
    @property
    def description(self) -> str:
        return "Parse email content and extract different content types (subject, body text/html, headers, recipients, attachments info). Works with email data from email_checker tool."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "email_data": {
                    "type": "object",
                    "description": "Email data object from email_checker tool"
                },
                "parse_headers": {
                    "type": "boolean",
                    "description": "Whether to parse and include email headers",
                    "default": True
                },
                "parse_body": {
                    "type": "boolean",
                    "description": "Whether to parse email body content",
                    "default": True
                },
                "parse_attachments": {
                    "type": "boolean",
                    "description": "Whether to parse attachment information",
                    "default": True
                },
                "extract_links": {
                    "type": "boolean",
                    "description": "Whether to extract links from email body",
                    "default": False
                },
                "extract_emails": {
                    "type": "boolean",
                    "description": "Whether to extract email addresses from content",
                    "default": False
                }
            },
            "required": ["email_data"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse email content and extract different content types
        
        Args:
            parameters: Parsing parameters including email_data
            
        Returns:
            Dictionary with parsed email content
            
        Raises:
            Exception: If parsing fails
        """
        email_data = parameters["email_data"]
        parse_headers = parameters.get("parse_headers", True)
        parse_body = parameters.get("parse_body", True)
        parse_attachments = parameters.get("parse_attachments", True)
        extract_links = parameters.get("extract_links", False)
        extract_emails = parameters.get("extract_emails", False)
        
        try:
            # Parse the email message
            parsed_email = self._parse_email_message(email_data, parse_headers, parse_body, parse_attachments)
            
            # Extract additional information if requested
            if extract_links:
                parsed_email["extracted_links"] = self._extract_links(parsed_email.get("body_text", "") + parsed_email.get("body_html", ""))
            
            if extract_emails:
                parsed_email["extracted_emails"] = self._extract_email_addresses(parsed_email.get("body_text", "") + parsed_email.get("body_html", ""))
            
            return {
                "status": "parsed",
                "parsed_email": parsed_email,
                "message": f"Successfully parsed email: {parsed_email.get('subject', 'No subject')}"
            }
            
        except Exception as e:
            error_msg = f"Failed to parse email: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _parse_email_message(self, email_data: Dict[str, Any], parse_headers: bool, parse_body: bool, parse_attachments: bool) -> Dict[str, Any]:
        """Parse email message and extract content"""
        # Get the email content from the email_data
        if "email" in email_data:
            # If email_data contains a parsed email object
            email_message = email_data["email"]
        elif "content" in email_data:
            # If email_data contains raw content
            if isinstance(email_data["content"], bytes):
                email_message = message_from_bytes(email_data["content"])
            else:
                email_message = message_from_string(str(email_data["content"]))
        else:
            raise Exception("Email data must contain 'email' or 'content' field")
        
        # Initialize result
        result = {
            "id": email_data.get("id"),
            "protocol": email_data.get("protocol"),
            "size": email_data.get("size")
        }
        
        # Parse headers if requested
        if parse_headers:
            result.update(self._parse_headers(email_message))
        
        # Parse body if requested
        if parse_body:
            result.update(self._parse_body(email_message))
        
        # Parse attachments if requested
        if parse_attachments:
            result.update(self._parse_attachments(email_message))
        
        return result
    
    def _parse_headers(self, email_message) -> Dict[str, Any]:
        """Parse email headers"""
        headers = {}
        
        # Common headers
        common_headers = [
            "Subject", "From", "To", "Cc", "Bcc", "Date", "Message-ID",
            "Reply-To", "In-Reply-To", "References", "Content-Type",
            "Content-Transfer-Encoding", "MIME-Version", "X-Mailer",
            "X-Priority", "X-MSMail-Priority", "Importance"
        ]
        
        for header_name in common_headers:
            value = email_message.get(header_name)
            if value:
                headers[header_name.lower()] = self._decode_header(value)
        
        # Parse date
        if "date" in headers:
            try:
                parsed_date = parsedate_to_datetime(headers["date"])
                headers["parsed_date"] = parsed_date.isoformat()
                headers["date_timestamp"] = parsed_date.timestamp()
            except Exception as e:
                logger.warning(f"Failed to parse date: {e}")
        
        # Parse recipients
        recipients = {
            "to": self._parse_recipients(email_message.get("To", "")),
            "cc": self._parse_recipients(email_message.get("Cc", "")),
            "bcc": self._parse_recipients(email_message.get("Bcc", "")),
            "from": self._parse_recipients(email_message.get("From", ""))
        }
        
        return {
            "headers": headers,
            "recipients": recipients
        }
    
    def _parse_body(self, email_message) -> Dict[str, Any]:
        """Parse email body content"""
        body_text = ""
        body_html = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Parse body content
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        content = payload.decode(charset, errors="ignore")
                        if content_type == "text/plain":
                            body_text = content
                        elif content_type == "text/html":
                            body_html = content
                    except Exception as e:
                        logger.warning(f"Failed to decode part: {e}")
        else:
            # Single part message
            payload = email_message.get_payload(decode=True)
            if payload:
                content_type = email_message.get_content_type()
                charset = email_message.get_content_charset() or "utf-8"
                try:
                    content = payload.decode(charset, errors="ignore")
                    if content_type == "text/plain":
                        body_text = content
                    elif content_type == "text/html":
                        body_html = content
                    else:
                        body_text = content
                except Exception as e:
                    logger.warning(f"Failed to decode body: {e}")
        
        return {
            "body_text": body_text,
            "body_html": body_html,
            "has_text_body": bool(body_text),
            "has_html_body": bool(body_html)
        }
    
    def _parse_attachments(self, email_message) -> Dict[str, Any]:
        """Parse attachment information"""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        
                        attachment_info = {
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0,
                            "content_id": part.get("Content-ID", ""),
                            "content_disposition": content_disposition
                        }
                        
                        # Try to determine file extension
                        if filename:
                            _, ext = os.path.splitext(filename)
                            attachment_info["extension"] = ext.lower()
                        
                        attachments.append(attachment_info)
        
        return {
            "attachments": attachments,
            "has_attachments": len(attachments) > 0,
            "attachment_count": len(attachments)
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
    
    def _parse_recipients(self, recipient_string: str) -> List[Dict[str, str]]:
        """Parse recipient string into structured format"""
        if not recipient_string:
            return []
        
        recipients = []
        try:
            # Simple parsing - can be enhanced with email.utils.parseaddr
            import re
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_pattern, recipient_string)
            
            for email in emails:
                recipients.append({
                    "email": email,
                    "name": "",  # Could be enhanced to extract names
                    "full": email
                })
        except Exception as e:
            logger.warning(f"Failed to parse recipients: {e}")
        
        return recipients
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract links from content"""
        import re
        links = []
        try:
            # URL pattern
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            links = re.findall(url_pattern, content)
        except Exception as e:
            logger.warning(f"Failed to extract links: {e}")
        
        return links
    
    def _extract_email_addresses(self, content: str) -> List[str]:
        """Extract email addresses from content"""
        import re
        emails = []
        try:
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, content)
        except Exception as e:
            logger.warning(f"Failed to extract emails: {e}")
        
        return emails 