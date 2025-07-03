# Email Reply Workflow Functionality

This document explains the email reply functionality that has been added to the SBOM analysis workflow, allowing the system to automatically send analysis results back to the original email sender.

## Overview

The `email_test_workflow_no_agent` workflow has been enhanced to include automatic email reply functionality. When a user sends an email with an SBOM attachment, the workflow will:

1. Process the email and extract the SBOM data
2. Analyze the PURLs for license and security information
3. Generate legal notices
4. **Automatically send the results back to the original sender**

## Workflow Steps

The updated workflow now includes these additional steps:

### 1. Email Parser Step (Early)
```json
{
  "type": "tool",
  "name": "email_parser",
  "parameters": {
    "email_data": "{{converted_email_data.result}}",
    "parse_headers": true,
    "parse_body": false,
    "parse_attachments": false,
    "extract_emails": true
  },
  "context_key": "parsed_email_info",
  "use_previous_output": false,
  "preserve_objects": false
}
```

**Purpose**: Extracts the original sender's email address and subject line from the incoming email headers.

### 2. Email Sender Step (Final)
```json
{
  "type": "tool",
  "name": "email_sender",
  "parameters": {
    "to": "{{parsed_email_info.parsed_email.recipients.from[0].email}}",
    "subject": "Re: {{parsed_email_info.parsed_email.headers.subject}} - SBOM Analysis Complete",
    "body": "Your SBOM analysis has been completed successfully.\n\nPlease find the legal notices and license assessment attached.\n\nWorkflow Results:\n{{legal_notices}}\n\nThis analysis was performed automatically by the Agentic AI Framework.\n\nBest regards,\nSBOM Analysis System",
    "html": false,
    "attachments": [
      {
        "filename": "legal_notices.txt",
        "content": "{{legal_notices}}",
        "content_type": "text/plain",
        "encoding": "utf-8"
      }
    ]
  },
  "context_key": "email_sent_confirmation",
  "use_previous_output": false,
  "preserve_objects": false
}
```

**Purpose**: Sends the analysis results back to the original sender with:
- Reply subject line with "SBOM Analysis Complete" suffix
- Professional email body explaining the results
- Legal notices attached as a text file
- Confirmation of automatic processing

## Configuration Requirements

### SMTP Configuration

The `email_sender` tool requires SMTP configuration. In the current setup, it's configured with Gmail SMTP:

```json
{
  "configuration": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "your-email@gmail.com",
    "smtp_password": "<EMAIL_PASSWORD>",
    "smtp_use_tls": true,
    "smtp_use_ssl": false,
    "from_email": "your-email@gmail.com"
  }
}
```

### Required Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `smtp_host` | SMTP server hostname | `smtp.gmail.com` |
| `smtp_port` | SMTP server port | `587` (TLS) or `465` (SSL) |
| `smtp_username` | Email account username | `your-email@gmail.com` |
| `smtp_password` | Email account password/app password | `your-app-password` |
| `smtp_use_tls` | Use STARTTLS encryption | `true` |
| `smtp_use_ssl` | Use SSL encryption | `false` (when using TLS) |
| `from_email` | From email address | `your-email@gmail.com` |

## How It Works

### 1. Email Reception
- Workflow checks for unread emails in the INBOX
- Reads the first unread email with attachments
- Converts email data to proper object format

### 2. Sender Information Extraction
- Email parser extracts sender information from headers
- Stores sender email address and original subject line
- This information is preserved for the reply step

### 3. SBOM Processing
- Downloads and processes email attachments
- Extracts PURLs from SBOM files
- Analyzes each PURL for license and security information
- Generates comprehensive legal notices

### 4. Automatic Reply
- Uses extracted sender information to send reply
- Includes analysis results in email body
- Attaches legal notices as text file
- Provides professional response with system branding

## Email Reply Features

### Subject Line Format
```
Re: [Original Subject] - SBOM Analysis Complete
```

### Email Body Content
- Professional greeting and explanation
- Summary of analysis completion
- Reference to attached legal notices
- System branding and contact information

### Attachments
- `legal_notices.txt` - Complete legal notices document
- Contains all license and copyright information
- Formatted for easy reading and compliance

## Security Considerations

### Email Credentials
- SMTP credentials are stored in tool configuration
- Consider using environment variables for production
- Use app passwords for Gmail (not regular passwords)

### Email Content
- No sensitive information is included in replies
- Only analysis results and legal notices are sent
- Original email content is not forwarded

### Rate Limiting
- Consider implementing rate limiting for email sending
- Monitor SMTP server limits and quotas
- Handle email sending failures gracefully

## Troubleshooting

### Common Issues

1. **SMTP Authentication Failed**
   - Check username and password
   - Ensure app password is used for Gmail
   - Verify SMTP settings

2. **Email Not Sent**
   - Check workflow execution logs
   - Verify sender email extraction worked
   - Ensure SMTP server is accessible

3. **Missing Attachments**
   - Check if legal notices were generated
   - Verify file encoding and content
   - Review attachment size limits

### Debugging Steps

1. Check workflow execution logs for each step
2. Verify email parser extracted sender information correctly
3. Test SMTP configuration independently
4. Review email sender tool response for errors

## Customization Options

### Email Template
You can customize the email body template by modifying the `body` parameter in the email sender step:

```json
"body": "Custom email body template with {{variables}}"
```

### Attachment Format
Modify the attachment configuration to change format or add multiple files:

```json
"attachments": [
  {
    "filename": "legal_notices.txt",
    "content": "{{legal_notices}}",
    "content_type": "text/plain"
  },
  {
    "filename": "analysis_report.json",
    "content": "{{sbom_license_information}}",
    "content_type": "application/json"
  }
]
```

### Subject Line
Customize the subject line format:

```json
"subject": "Custom Subject: {{parsed_email_info.parsed_email.headers.subject}}"
```

## Future Enhancements

### Potential Improvements

1. **HTML Email Support**
   - Format results as HTML for better presentation
   - Include tables and formatting for analysis results

2. **Multiple Recipients**
   - Support for CC/BCC in replies
   - Configurable recipient lists

3. **Email Templates**
   - Configurable email templates
   - Support for different analysis types

4. **Error Handling**
   - Retry logic for failed email sends
   - Fallback email addresses
   - Detailed error reporting

5. **Email Tracking**
   - Track email delivery status
   - Log email sending history
   - Monitor reply rates

## Conclusion

The email reply functionality provides a complete end-to-end workflow for SBOM analysis with automatic result delivery. Users can simply send an email with an SBOM attachment and receive comprehensive analysis results automatically, making the system more user-friendly and professional. 