"""
tools/email_sender.py - Email Sending Tool

Tool for sending emails via SMTP with agent-specific configuration.
Supports HTML and plain text emails with attachments support.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class EmailSenderTool(BaseTool):
    """Tool for sending emails using SMTP"""
    
    @property
    def name(self) -> str:
        return "email_sender"
    
    @property
    def description(self) -> str:
        return "Send emails using SMTP. Requires SMTP configuration in agent tool_configs (smtp_host, smtp_username, smtp_password)."
    
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
                }
            },
            "required": ["to", "subject", "body"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email using SMTP configuration
        
        Args:
            parameters: Email parameters (to, subject, body, etc.)
            
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
            
            # Prepare recipient list
            recipients = [to_email]
            if cc_emails:
                recipients.extend([email.strip() for email in cc_emails.split(",")])
            if bcc_emails:
                recipients.extend([email.strip() for email in bcc_emails.split(",")])
            
            # Connect to SMTP server and send
            logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port}")
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_use_tls:
                    server.starttls()
                    logger.debug("Started TLS connection")
                
                server.login(smtp_username, smtp_password)
                logger.debug("SMTP login successful")
                
                server.send_message(msg, to_addrs=recipients)
                logger.info(f"Email sent successfully to {len(recipients)} recipients")
            
            return {
                "status": "sent",
                "to": to_email,
                "cc": cc_emails if cc_emails else None,
                "bcc": bcc_emails if bcc_emails else None,
                "subject": subject,
                "priority": priority,
                "html": is_html,
                "recipients_count": len(recipients),
                "message": f"Email sent successfully to {to_email}"
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