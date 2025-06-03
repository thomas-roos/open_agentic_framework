# workflows/predefined/website_monitoring.py - Extensible monitoring workflow

import asyncio
import aiohttp
import smtplib
import logging
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Any, List
import os
import sys

# Add parent directory to path to import WorkflowBase
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from workflows.registry import WorkflowBase

logger = logging.getLogger(__name__)

class WebsiteMonitoringWorkflow(WorkflowBase):
    """Website monitoring workflow that extends the base workflow class"""
    
    def __init__(self):
        super().__init__()
        
        # Workflow metadata
        self.name = "website_monitoring"
        self.description = "Monitor websites and send email alerts when they go down or come back up"
        self.version = "1.0.0"
        self.author = "Multi-Agent System"
        self.tags = ["monitoring", "website", "alerts", "email"]
        
        # Define expected parameters
        self.parameters = {
            "url": {
                "type": "string",
                "required": True,
                "description": "Website URL to monitor"
            },
            "email_to": {
                "type": "string", 
                "required": True,
                "description": "Email address for notifications"
            },
            "email_from": {
                "type": "string",
                "required": False,
                "description": "Sender email address"
            },
            "email_password": {
                "type": "string",
                "required": False,
                "description": "Email password/app password"
            },
            "check_interval": {
                "type": "integer",
                "required": False,
                "default": 300,
                "description": "Check interval in seconds (default 5 minutes)"
            },
            "smtp_host": {
                "type": "string",
                "required": False,
                "default": "smtp.gmail.com",
                "description": "SMTP server host"
            },
            "smtp_port": {
                "type": "integer",
                "required": False,
                "default": 587,
                "description": "SMTP server port"
            },
            "timeout": {
                "type": "integer",
                "required": False,
                "default": 30,
                "description": "Request timeout in seconds"
            },
            "alert_after_failures": {
                "type": "integer",
                "required": False,
                "default": 3,
                "description": "Send alert after N consecutive failures"
            }
        }
        
        # Internal state
        self.running_monitors = {}
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate input parameters"""
        url = kwargs.get('url')
        email_to = kwargs.get('email_to')
        check_interval = kwargs.get('check_interval', 300)
        
        if not url:
            return {"valid": False, "message": "URL is required"}
        
        if not email_to:
            return {"valid": False, "message": "Email address is required for notifications"}
        
        if not url.startswith(('http://', 'https://')):
            return {"valid": False, "message": "URL must start with http:// or https://"}
        
        if check_interval < 60:
            return {"valid": False, "message": "Check interval must be at least 60 seconds"}
        
        return {"valid": True}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the monitoring workflow"""
        
        # Validate parameters
        validation = self.validate_parameters(**kwargs)
        if not validation["valid"]:
            return {"error": validation["message"]}
        
        url = kwargs.get('url')
        email_to = kwargs.get('email_to')
        check_interval = kwargs.get('check_interval', 300)
        
        # Generate unique monitor ID
        monitor_id = f"monitor_{len(self.running_monitors) + 1}_{int(datetime.now().timestamp())}"
        
        # Start monitoring task
        task = asyncio.create_task(
            self._monitor_website(
                monitor_id=monitor_id,
                url=url,
                email_to=email_to,
                check_interval=check_interval,
                **kwargs
            )
        )
        
        # Store monitor info
        self.running_monitors[monitor_id] = {
            'task': task,
            'url': url,
            'email_to': email_to,
            'started_at': datetime.now(),
            'status': 'running',
            'last_check': None,
            'last_status': None,
            'consecutive_failures': 0,
            'total_checks': 0,
            'total_failures': 0
        }
        
        logger.info(f"🔍 Started monitoring {url} with ID {monitor_id}")
        
        return {
            "success": True,
            "monitor_id": monitor_id,
            "message": f"Started monitoring {url} every {check_interval} seconds",
            "details": {
                "url": url,
                "email_notifications": email_to,
                "check_interval": check_interval,
                "started_at": self.running_monitors[monitor_id]['started_at'].isoformat()
            }
        }
    
    async def _monitor_website(self, monitor_id: str, url: str, email_to: str, 
                              check_interval: int, **kwargs):
        """Main monitoring loop for a website"""
        
        # Extract email configuration
        email_from = kwargs.get('email_from', os.getenv('EMAIL_FROM', ''))
        email_password = kwargs.get('email_password', os.getenv('EMAIL_PASSWORD', ''))
        smtp_host = kwargs.get('smtp_host', 'smtp.gmail.com')
        smtp_port = kwargs.get('smtp_port', 587)
        timeout = kwargs.get('timeout', 30)
        alert_after_failures = kwargs.get('alert_after_failures', 3)
        
        monitor = self.running_monitors[monitor_id]
        consecutive_failures = 0
        last_status = None
        
        logger.info(f"🔍 Started monitoring {url} every {check_interval} seconds")
        
        while True:
            try:
                # Check website
                is_up, status_code, error_msg, response_time = await self._check_website(url, timeout)
                
                current_time = datetime.now()
                current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Update monitor stats
                monitor['last_check'] = current_time
                monitor['total_checks'] += 1
                
                if is_up:
                    # Website is up
                    if last_status == 'down':
                        # Website came back up - send recovery notification
                        await self._send_recovery_email(
                            email_from, email_password, email_to,
                            url, status_code, response_time, current_time_str,
                            consecutive_failures, smtp_host, smtp_port
                        )
                        logger.info(f"✅ {url} is back online!")
                    
                    consecutive_failures = 0
                    last_status = 'up'
                    monitor['last_status'] = 'up'
                    monitor['consecutive_failures'] = 0
                    
                    logger.debug(f"✅ {url} is up (HTTP {status_code}, {response_time:.2f}s)")
                
                else:
                    # Website is down
                    consecutive_failures += 1
                    monitor['total_failures'] += 1
                    monitor['consecutive_failures'] = consecutive_failures
                    monitor['last_status'] = 'down'
                    
                    # Send alert after specified number of failures
                    if consecutive_failures == alert_after_failures and last_status != 'down':
                        await self._send_alert_email(
                            email_from, email_password, email_to,
                            url, error_msg, current_time_str, consecutive_failures,
                            smtp_host, smtp_port
                        )
                        logger.error(f"🚨 {url} is DOWN! Email alert sent.")
                        last_status = 'down'
                    
                    logger.warning(f"❌ {url} failed check {consecutive_failures}: {error_msg}")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                logger.info(f"🛑 Monitoring stopped for {url}")
                monitor['status'] = 'stopped'
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop for {url}: {e}")
                await asyncio.sleep(check_interval)
    
    async def _check_website(self, url: str, timeout: int = 30):
        """Check if website is responding"""
        start_time = datetime.now()
        
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(url) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    # Consider 2xx and 3xx status codes as "up"
                    is_up = 200 <= response.status < 400
                    
                    return is_up, response.status, None, response_time
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return False, None, str(e), response_time
    
    async def _send_alert_email(self, email_from: str, email_password: str, email_to: str,
                               url: str, error_msg: str, current_time: str, consecutive_failures: int,
                               smtp_host: str, smtp_port: int):
        """Send website down alert email"""
        subject = f"🚨 Website DOWN: {url}"
        body = f"""🔴 ALERT: Your website is down!

Website: {url}
Status: DOWN
Error: {error_msg}
Failed At: {current_time}
Consecutive Failures: {consecutive_failures}

Please check your website immediately.

This alert was sent after {consecutive_failures} consecutive failed checks.
You will be notified when the website comes back online.

---
Multi-Agent Monitoring System"""
        
        await self._send_email(email_from, email_password, email_to, subject, body, smtp_host, smtp_port)
    
    async def _send_recovery_email(self, email_from: str, email_password: str, email_to: str,
                                  url: str, status_code: int, response_time: float, current_time: str,
                                  downtime_checks: int, smtp_host: str, smtp_port: int):
        """Send website recovery email"""
        subject = f"✅ Website RESTORED: {url}"
        body = f"""🟢 GOOD NEWS! Your website is back online.

Website: {url}
Status: Online (HTTP {status_code})
Response Time: {response_time:.2f}s
Restored At: {current_time}
Downtime: {downtime_checks} failed checks

Your website is now responding normally.

---
Multi-Agent Monitoring System"""
        
        await self._send_email(email_from, email_password, email_to, subject, body, smtp_host, smtp_port)
    
    async def _send_email(self, email_from: str, email_password: str, email_to: str,
                         subject: str, body: str, smtp_host: str = 'smtp.gmail.com',
                         smtp_port: int = 587):
        """Send email notification"""
        try:
            if not email_from or not email_password:
                logger.warning("Email credentials not configured - skipping email notification")
                return
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            # Send email in thread to avoid blocking
            def send_sync_email():
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(email_from, email_password)
                    server.send_message(msg)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_sync_email)
            
            logger.info(f"📧 Email notification sent to {email_to}")
        
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
    
    def get_monitor_status(self, monitor_id: str = None) -> Dict[str, Any]:
        """Get status of monitors"""
        if monitor_id:
            if monitor_id in self.running_monitors:
                monitor = self.running_monitors[monitor_id]
                return {
                    "monitor_id": monitor_id,
                    "url": monitor['url'],
                    "email_to": monitor['email_to'],
                    "started_at": monitor['started_at'].isoformat(),
                    "status": monitor['status'],
                    "last_check": monitor['last_check'].isoformat() if monitor['last_check'] else None,
                    "last_status": monitor['last_status'],
                    "consecutive_failures": monitor['consecutive_failures'],
                    "total_checks": monitor['total_checks'],
                    "total_failures": monitor['total_failures'],
                    "uptime_percentage": self._calculate_uptime(monitor)
                }
            else:
                return {"error": "Monitor not found"}
        else:
            return {
                "total_monitors": len(self.running_monitors),
                "monitors": {
                    mid: {
                        "url": monitor['url'],
                        "status": monitor['status'],
                        "started_at": monitor['started_at'].isoformat(),
                        "uptime_percentage": self._calculate_uptime(monitor)
                    }
                    for mid, monitor in self.running_monitors.items()
                }
            }
    
    def _calculate_uptime(self, monitor: Dict[str, Any]) -> float:
        """Calculate uptime percentage"""
        total_checks = monitor.get('total_checks', 0)
        total_failures = monitor.get('total_failures', 0)
        
        if total_checks == 0:
            return 100.0
        
        return round(((total_checks - total_failures) / total_checks) * 100, 2)
    
    def stop_monitor(self, monitor_id: str) -> bool:
        """Stop a specific monitor"""
        if monitor_id in self.running_monitors:
            monitor = self.running_monitors[monitor_id]
            monitor['task'].cancel()
            monitor['status'] = 'stopped'
            logger.info(f"🛑 Stopped monitoring {monitor['url']}")
            return True
        return False
    
    def stop_all_monitors(self):
        """Stop all running monitors"""
        for monitor_id in list(self.running_monitors.keys()):
            self.stop_monitor(monitor_id)
        logger.info("🛑 Stopped all monitors")
    
    async def start(self) -> Dict[str, Any]:
        """Called when workflow is enabled"""
        logger.info("✅ Website monitoring workflow started")
        return {"status": "started", "message": "Website monitoring workflow is ready"}
    
    async def stop(self) -> Dict[str, Any]:
        """Called when workflow is disabled"""
        self.stop_all_monitors()
        logger.info("🛑 Website monitoring workflow stopped")
        return {"status": "stopped", "message": "All monitors stopped"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the workflow"""
        active_monitors = sum(1 for m in self.running_monitors.values() if m['status'] == 'running')
        
        return {
            "healthy": True,
            "total_monitors": len(self.running_monitors),
            "active_monitors": active_monitors,
            "workflow_enabled": self.enabled
        }