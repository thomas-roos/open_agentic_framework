"""
tools/email_sender.py - Email Sending Tool

Tool for sending emails via SMTP with agent-specific configuration.
Supports HTML and plain text emails with attachments support.
"""

import smtplib
import ssl
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class EmailSenderTool(BaseTool):
    """Tool for sending emails using SMTP"""
    
    @property
    def name(self) -> str:
        return "email_sender"
    
    @property
    def description(self) -> str:
        return "Send emails using SMTP with SSL/TLS support. Requires SMTP configuration in agent tool_configs (smtp_host, smtp_username, smtp_password)."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "cc": {
                    "type": "string",
                    "description": "CC recipients (comma-separated email addresses)",
                    "default": ""
                },
                "bcc": {
                    "type": "string",
                    "description": "BCC recipients (comma-separated email addresses)",
                    "default": ""
                },
                "html": {
                    "type": "boolean",
                    "description": "Whether the body content is HTML",
                    "default": False
                },
                "priority": {
                    "type": "string",
                    "description": "Email priority: low, normal, high",
                    "default": "normal"
                },
                "attachments": {
                    "type": "array",
                    "description": "List of attachments to include in the email",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the attachment file"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content of the attachment (text or base64 encoded)"
                            },
                            "content_type": {
                                "type": "string",
                                "description": "MIME type of the attachment (e.g., text/plain, application/json)",
                                "default": "text/plain"
                            },
                            "encoding": {
                                "type": "string",
                                "description": "Encoding of the content (e.g., utf-8, base64)",
                                "default": "utf-8"
                            }
                        },
                        "required": ["filename", "content"]
                    },
                    "default": []
                }
            },
            "required": ["to", "subject", "body"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email using SMTP configuration
        
        Args:
            parameters: Email parameters (to, subject, body, attachments, etc.)
            
        Returns:
            Dictionary with send status and details
            
        Raises:
            Exception: If SMTP configuration missing or send fails
        """
        # Get SMTP configuration from tool config
        smtp_host = self.get_config("smtp_host")
        smtp_port = self.get_config("smtp_port", 587)
        smtp_username = self.get_config("smtp_username")
        smtp_password = self.get_config("smtp_password")
        smtp_use_tls = self.get_config("smtp_use_tls", True)
        smtp_use_ssl = self.get_config("smtp_use_ssl", False)
        smtp_verify_ssl = self.get_config("smtp_verify_ssl", True)
        from_email = self.get_config("from_email", smtp_username)
        
        # Validate required configuration
        required_config = ["smtp_host", "smtp_username", "smtp_password"]
        if not self.validate_config(required_config):
            missing_keys = [key for key in required_config if not self.get_config(key)]
            raise Exception(
                f"SMTP configuration missing. Please configure {', '.join(missing_keys)} "
                "in the agent's tool_configs for email_sender."
            )
        
        # Extract parameters
        to_email = parameters["to"]
        subject = parameters["subject"]
        body = parameters["body"]
        cc_emails = parameters.get("cc", "")
        bcc_emails = parameters.get("bcc", "")
        is_html = parameters.get("html", False)
        priority = parameters.get("priority", "normal")
        attachments = parameters.get("attachments", [])
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Add CC and BCC if provided
            if cc_emails:
                msg["Cc"] = cc_emails
            
            # Set priority
            if priority.lower() == "high":
                msg["X-Priority"] = "1"
                msg["X-MSMail-Priority"] = "High"
            elif priority.lower() == "low":
                msg["X-Priority"] = "5"
                msg["X-MSMail-Priority"] = "Low"
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            # Add attachments if provided
            attachment_count = 0
            for attachment in attachments:
                try:
                    filename = attachment["filename"]
                    content = attachment["content"]
                    content_type = attachment.get("content_type", "text/plain")
                    encoding = attachment.get("encoding", "utf-8")
                    
                    # Create attachment part
                    part = MIMEBase('application', 'octet-stream')
                    
                    # Handle different encodings
                    if encoding.lower() == "base64":
                        part.set_payload(base64.b64decode(content))
                    else:
                        # Default to UTF-8 text
                        part.set_payload(content.encode(encoding))
                    
                    # Encode the attachment
                    encoders.encode_base64(part)
                    
                    # Set headers
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    
                    # Set content type if specified
                    if content_type and content_type != "application/octet-stream":
                        part.set_type(content_type)
                    
                    msg.attach(part)
                    attachment_count += 1
                    logger.debug(f"Added attachment: {filename}")
                    
                except Exception as e:
                    logger.warning(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {e}")
                    continue
            
            # Prepare recipient list
            recipients = [to_email]
            if cc_emails:
                recipients.extend([email.strip() for email in cc_emails.split(",")])
            if bcc_emails:
                recipients.extend([email.strip() for email in bcc_emails.split(",")])
            
            # Connect to SMTP server and send
            logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port}")
            
            # Create SSL context if needed
            ssl_context = None
            if smtp_use_ssl or smtp_use_tls:
                ssl_context = ssl.create_default_context()
                if not smtp_verify_ssl:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect using appropriate method
            if smtp_use_ssl:
                # SSL connection from the start
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=ssl_context)
                logger.debug("Established SSL connection")
            else:
                # Regular connection with optional STARTTLS
                server = smtplib.SMTP(smtp_host, smtp_port)
                if smtp_use_tls:
                    server.starttls(context=ssl_context)
                    logger.debug("Started TLS connection")
            
            # Login and send
            server.login(smtp_username, smtp_password)
            logger.debug("SMTP login successful")
            
            server.send_message(msg, to_addrs=recipients)
            logger.info(f"Email sent successfully to {len(recipients)} recipients with {attachment_count} attachments")
            
            server.quit()
            
            return {
                "status": "sent",
                "to": to_email,
                "cc": cc_emails if cc_emails else None,
                "bcc": bcc_emails if bcc_emails else None,
                "subject": subject,
                "priority": priority,
                "html": is_html,
                "recipients_count": len(recipients),
                "attachment_count": attachment_count,
                "connection_type": "SSL" if smtp_use_ssl else "STARTTLS" if smtp_use_tls else "plain",
                "message": f"Email sent successfully to {to_email} with {attachment_count} attachments"
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "SMTP authentication failed. Check username and password."
            logger.error(f"{error_msg}: {e}")
            raise Exception(error_msg)
            
        except smtplib.SMTPServerDisconnected as e:
            error_msg = "SMTP server disconnected. Check server configuration."
            logger.error(f"{error_msg}: {e}")
            raise Exception(error_msg)
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"SMTP server refused recipients: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)