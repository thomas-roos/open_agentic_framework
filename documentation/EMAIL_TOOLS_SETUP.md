# Email Tools Setup and Configuration

This document provides comprehensive setup instructions for the email tools in the Agentic AI Framework, including both email sending (SMTP) and email checking (POP3/IMAP) capabilities.

## Overview

The framework provides two main email tools:

1. **EmailSenderTool** - Send emails via SMTP with SSL/TLS support
2. **EmailCheckerTool** - Check emails via POP3 and IMAP protocols with SSL support

## Dynamic Configuration

**Important**: Configuration for these tools happens **dynamically** through the agent system. The agent can set the configuration at runtime using the `set_config()` method on the tool instances. This allows for flexible, per-agent configuration without requiring static configuration files.

### How Dynamic Configuration Works

```python
# The agent can configure tools dynamically
email_sender = EmailSenderTool()
email_sender.set_config({
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "agent-email@gmail.com",
    "smtp_password": "app-password",
    "smtp_use_tls": True
})

email_checker = EmailCheckerTool()
email_checker.set_config({
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_username": "agent-email@gmail.com",
    "imap_password": "app-password",
    "imap_use_ssl": True
})
```

## Email Sender Tool (SMTP)

### Configuration Parameters

The EmailSenderTool can be configured dynamically with the following parameters:

```python
{
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "your-email@gmail.com",
    "smtp_password": "your-app-password",
    "smtp_use_tls": True,
    "smtp_use_ssl": False,
    "smtp_verify_ssl": True,
    "from_email": "your-email@gmail.com"
}
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `smtp_host` | string | required | SMTP server hostname |
| `smtp_port` | integer | 587 | SMTP server port |
| `smtp_username` | string | required | SMTP username/email |
| `smtp_password` | string | required | SMTP password or app password |
| `smtp_use_tls` | boolean | True | Use STARTTLS encryption |
| `smtp_use_ssl` | boolean | False | Use SSL connection from start |
| `smtp_verify_ssl` | boolean | True | Verify SSL certificates |
| `from_email` | string | smtp_username | From email address |

### Common SMTP Server Settings

#### Gmail
```python
{
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_use_tls": True,
    "smtp_use_ssl": False
}
```

#### Outlook/Hotmail
```python
{
    "smtp_host": "smtp-mail.outlook.com",
    "smtp_port": 587,
    "smtp_use_tls": True,
    "smtp_use_ssl": False
}
```

#### Yahoo
```python
{
    "smtp_host": "smtp.mail.yahoo.com",
    "smtp_port": 587,
    "smtp_use_tls": True,
    "smtp_use_ssl": False
}
```

#### Custom SMTP Server (SSL)
```python
{
    "smtp_host": "mail.yourdomain.com",
    "smtp_port": 465,
    "smtp_use_tls": False,
    "smtp_use_ssl": True
}
```

### Usage Example

```python
# Create and configure the tool
email_sender = EmailSenderTool()
email_sender.set_config({
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "agent@example.com",
    "smtp_password": "app-password",
    "smtp_use_tls": True
})

# Send a simple email
result = await email_sender.execute({
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email from the Agentic AI Framework."
})

# Send HTML email with CC and BCC
result = await email_sender.execute({
    "to": "recipient@example.com",
    "subject": "HTML Test Email",
    "body": "<h1>Hello</h1><p>This is an HTML email.</p>",
    "html": True,
    "cc": "cc@example.com",
    "bcc": "bcc@example.com",
    "priority": "high"
})
```

## Email Checker Tool (POP3/IMAP)

### Configuration Parameters

The EmailCheckerTool supports both POP3 and IMAP protocols. The agent can configure both if needed:

```python
{
    # IMAP Configuration
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_username": "your-email@gmail.com",
    "imap_password": "your-app-password",
    "imap_use_ssl": True,
    
    # POP3 Configuration
    "pop3_host": "pop.gmail.com",
    "pop3_port": 995,
    "pop3_username": "your-email@gmail.com",
    "pop3_password": "your-app-password",
    "pop3_use_ssl": True
}
```

### Configuration Options

#### IMAP Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `imap_host` | string | required | IMAP server hostname |
| `imap_port` | integer | 993 | IMAP server port |
| `imap_username` | string | required | IMAP username/email |
| `imap_password` | string | required | IMAP password or app password |
| `imap_use_ssl` | boolean | True | Use SSL connection |

#### POP3 Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pop3_host` | string | required | POP3 server hostname |
| `pop3_port` | integer | 995 | POP3 server port |
| `pop3_username` | string | required | POP3 username/email |
| `pop3_password` | string | required | POP3 password or app password |
| `pop3_use_ssl` | boolean | True | Use SSL connection |

### Common Server Settings

#### Gmail
```python
# IMAP
{
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_use_ssl": True
}

# POP3
{
    "pop3_host": "pop.gmail.com",
    "pop3_port": 995,
    "pop3_use_ssl": True
}
```

#### Outlook/Hotmail
```python
# IMAP
{
    "imap_host": "outlook.office365.com",
    "imap_port": 993,
    "imap_use_ssl": True
}

# POP3
{
    "pop3_host": "outlook.office365.com",
    "pop3_port": 995,
    "pop3_use_ssl": True
}
```

#### Yahoo
```python
# IMAP
{
    "imap_host": "imap.mail.yahoo.com",
    "imap_port": 993,
    "imap_use_ssl": True
}

# POP3
{
    "pop3_host": "pop.mail.yahoo.com",
    "pop3_port": 995,
    "pop3_use_ssl": True
}
```

### Usage Examples

#### List IMAP Folders
```python
email_checker = EmailCheckerTool()
email_checker.set_config({
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_username": "agent@example.com",
    "imap_password": "app-password",
    "imap_use_ssl": True
})

result = await email_checker.execute({
    "action": "list_folders",
    "protocol": "imap"
})
```

#### Check Recent Emails
```python
result = await email_checker.execute({
    "action": "check_emails",
    "protocol": "imap",
    "folder": "INBOX",
    "limit": 10,
    "unread_only": False
})
```

#### Check Unread Emails Only
```python
result = await email_checker.execute({
    "action": "check_emails",
    "protocol": "imap",
    "folder": "INBOX",
    "limit": 5,
    "unread_only": True
})
```

#### Read Specific Email
```python
result = await email_checker.execute({
    "action": "read_email",
    "protocol": "imap",
    "email_id": "123",
    "include_attachments": True
})
```

#### POP3 Examples
```python
# Configure for POP3
email_checker.set_config({
    "pop3_host": "pop.gmail.com",
    "pop3_port": 995,
    "pop3_username": "agent@example.com",
    "pop3_password": "app-password",
    "pop3_use_ssl": True
})

# Check POP3 emails (POP3 only has INBOX)
result = await email_checker.execute({
    "action": "check_emails",
    "protocol": "pop3",
    "limit": 10
})

# Read POP3 email
result = await email_checker.execute({
    "action": "read_email",
    "protocol": "pop3",
    "email_id": "1"
})
```

## Agent Integration

### Tool Registration
Agents can register these tools dynamically:

```python
# Register email tools with agent
agent.register_tool(EmailSenderTool())
agent.register_tool(EmailCheckerTool())
```

### Configuration Management
Agents can manage tool configurations based on their needs:

```python
# Configure tools based on agent requirements
def setup_email_tools(agent):
    email_sender = EmailSenderTool()
    email_checker = EmailCheckerTool()
    
    # Set configurations based on agent's email provider
    if agent.email_provider == "gmail":
        email_sender.set_config({
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": agent.email_username,
            "smtp_password": agent.email_password,
            "smtp_use_tls": True
        })
        
        email_checker.set_config({
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "imap_username": agent.email_username,
            "imap_password": agent.email_password,
            "imap_use_ssl": True
        })
    
    agent.register_tool(email_sender)
    agent.register_tool(email_checker)
```

## Security Considerations

### App Passwords
For services like Gmail, Yahoo, and Outlook, you may need to:
1. Enable 2-factor authentication
2. Generate an app password
3. Use the app password instead of your regular password

### SSL/TLS Configuration
- Always use SSL/TLS for production environments
- Set `verify_ssl` to `False` only for testing with self-signed certificates
- Use appropriate ports (587 for STARTTLS, 465 for SSL, 993 for IMAP SSL, 995 for POP3 SSL)

### Secure Configuration Storage
Since configuration is dynamic, consider these approaches for secure credential storage:

```python
# Option 1: Environment variables
import os
email_sender.set_config({
    "smtp_host": os.getenv("SMTP_HOST"),
    "smtp_username": os.getenv("SMTP_USERNAME"),
    "smtp_password": os.getenv("SMTP_PASSWORD")
})

# Option 2: Secure credential manager
import keyring
email_sender.set_config({
    "smtp_host": "smtp.gmail.com",
    "smtp_username": "agent@example.com",
    "smtp_password": keyring.get_password("email_tools", "agent@example.com")
})

# Option 3: Encrypted configuration
from cryptography.fernet import Fernet
# Decrypt credentials and set configuration
```

## Troubleshooting

### Common SMTP Issues
1. **Authentication Failed**: Check username/password and ensure app passwords are used if required
2. **Connection Refused**: Verify host and port settings
3. **SSL Certificate Errors**: Set `smtp_verify_ssl` to `False` for testing (not recommended for production)

### Common IMAP/POP3 Issues
1. **Login Failed**: Verify credentials and ensure IMAP/POP3 is enabled in your email provider settings
2. **SSL Connection Errors**: Check port settings and SSL configuration
3. **Folder Not Found**: Ensure the folder name is correct (case-sensitive for some providers)

### Gmail Specific Setup
1. Enable "Less secure app access" or use App Passwords
2. Enable IMAP in Gmail settings
3. Use port 993 for IMAP SSL or 995 for POP3 SSL

### Testing Your Configuration
Create a simple test script to verify your email configuration:

```python
import asyncio
from tools.email_sender import EmailSenderTool
from tools.email_checker import EmailCheckerTool

async def test_email_tools():
    # Test email sender
    sender = EmailSenderTool()
    sender.set_config({
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "your-email@gmail.com",
        "smtp_password": "your-app-password",
        "smtp_use_tls": True
    })
    
    result = await sender.execute({
        "to": "test@example.com",
        "subject": "Test",
        "body": "Test email"
    })
    print("Email sent:", result)
    
    # Test email checker
    checker = EmailCheckerTool()
    checker.set_config({
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "imap_username": "your-email@gmail.com",
        "imap_password": "your-app-password",
        "imap_use_ssl": True
    })
    
    result = await checker.execute({
        "action": "list_folders",
        "protocol": "imap"
    })
    print("Folders:", result)

if __name__ == "__main__":
    asyncio.run(test_email_tools())
```

## Dependencies

The email tools require the following Python packages (already included in requirements.txt):
- `aiosmtplib` - For async SMTP operations
- `imaplib2` - For IMAP protocol support
- `poplib2` - For POP3 protocol support

These are standard Python libraries for email operations and are included in the framework's requirements. 