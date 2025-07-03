# Email Tools Architecture

This document explains the architecture of the email tools in the Agentic AI Framework and why we chose a modular approach.

## Architecture Overview

The email functionality is split into **three specialized tools** that work together:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  EmailChecker   │    │  EmailParser    │    │ AttachmentDown- │
│     Tool        │    │     Tool        │    │   loader Tool   │
│                 │    │                 │    │                 │
│ • Check emails  │───▶│ • Parse content │───▶│ • Download files│
│ • List folders  │    │ • Extract meta  │    │ • Temp storage  │
│ • Read emails   │    │ • Parse headers │    │ • File cleanup  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Tool Responsibilities

### 1. EmailCheckerTool
**Purpose**: Retrieve emails from email servers
- **Protocols**: POP3 and IMAP with SSL support
- **Actions**: List folders, check emails, read specific emails
- **Output**: Raw email data with basic metadata

### 2. EmailParserTool
**Purpose**: Parse and extract email content
- **Input**: Email data from EmailCheckerTool
- **Features**: Parse headers, body (text/HTML), recipients, attachments info
- **Extractions**: Links, email addresses, structured metadata
- **Output**: Structured email content

### 3. AttachmentDownloaderTool
**Purpose**: Download attachments to temporary locations
- **Input**: Email data from EmailCheckerTool
- **Features**: Download to temp directory, filename sanitization, size limits
- **Safety**: File size limits, filename sanitization, cleanup utilities
- **Output**: File paths and metadata

## Why Modular Architecture?

### ✅ Benefits

1. **Single Responsibility Principle**
   - Each tool has one clear purpose
   - Easier to understand and maintain
   - Simpler testing and debugging

2. **Flexibility and Reusability**
   - Tools can be used independently
   - Different agents can use different combinations
   - Easy to extend or modify individual components

3. **Performance Optimization**
   - Only parse what you need
   - Only download attachments when required
   - Configurable parsing options

4. **Error Isolation**
   - Failures in one tool don't affect others
   - Better error handling and recovery
   - Easier to diagnose issues

5. **Dynamic Configuration**
   - Each tool can be configured independently
   - Different email providers for different tools
   - Runtime configuration changes

### ❌ Alternative: Single Tool Approach

A single comprehensive tool would have these drawbacks:
- **Complexity**: Large, hard-to-maintain codebase
- **Coupling**: All functionality tightly coupled
- **Performance**: Always parse everything even when not needed
- **Testing**: Harder to test individual features
- **Reusability**: Can't use parsing without checking emails

## Workflow Examples

### Complete Email Processing
```python
# 1. Check emails
email_checker = EmailCheckerTool()
email_checker.set_config({...})
emails = await email_checker.execute({"action": "check_emails", ...})

# 2. Parse each email
email_parser = EmailParserTool()
for email in emails['emails']:
    email_detail = await email_checker.execute({"action": "read_email", ...})
    parsed = await email_parser.execute({"email_data": email_detail, ...})
    
    # 3. Download attachments if needed
    if parsed['parsed_email']['has_attachments']:
        downloader = AttachmentDownloaderTool()
        files = await downloader.execute({"email_data": email_detail, ...})
```

### Independent Usage
```python
# Use parser with existing email data
parser = EmailParserTool()
result = await parser.execute({
    "email_data": existing_email_data,
    "parse_headers": True,
    "parse_body": False  # Only parse headers
})

# Use downloader with specific files
downloader = AttachmentDownloaderTool()
result = await downloader.execute({
    "email_data": email_data,
    "attachment_filenames": ["document.pdf", "image.jpg"]
})
```

## Data Flow

```
Email Server
     │
     ▼
EmailCheckerTool (retrieves raw email)
     │
     ▼
EmailParserTool (extracts structured data)
     │
     ▼
AttachmentDownloaderTool (downloads files)
     │
     ▼
Temporary Files / Structured Data
```

## Configuration Strategy

Each tool can be configured independently:

```python
# Different configurations for different purposes
email_checker.set_config({
    "imap_host": "imap.gmail.com",
    "imap_username": "agent@example.com"
})

# Parser doesn't need email server config
email_parser = EmailParserTool()  # No config needed

# Downloader can have custom paths
attachment_downloader.set_config({
    "download_path": "/custom/path",
    "max_file_size": 50 * 1024 * 1024  # 50MB
})
```

## Error Handling

Each tool handles errors independently:

```python
try:
    # Check emails
    emails = await email_checker.execute({...})
except Exception as e:
    # Email checking failed, but parsing can still work with cached data
    pass

try:
    # Parse email
    parsed = await email_parser.execute({"email_data": cached_email_data})
except Exception as e:
    # Parsing failed, but attachment download can still work
    pass

try:
    # Download attachments
    files = await attachment_downloader.execute({"email_data": email_data})
except Exception as e:
    # Download failed, but other operations succeeded
    pass
```

## Performance Considerations

### Lazy Processing
- Only parse what you need
- Only download attachments when required
- Configurable parsing depth

### Memory Efficiency
- Process emails one at a time
- Clean up temporary files
- Stream large attachments

### Caching Strategy
- Cache parsed email data
- Reuse parsed results
- Avoid re-downloading attachments

## Security Features

### EmailParserTool
- Safe header decoding
- Content type validation
- Link extraction with validation

### AttachmentDownloaderTool
- Filename sanitization
- File size limits
- Temporary file cleanup
- MD5 hash verification

## Testing Strategy

Each tool can be tested independently:

```python
# Test email checker
def test_email_checker():
    checker = EmailCheckerTool()
    checker.set_config(test_config)
    result = await checker.execute(test_params)
    assert result['status'] == 'success'

# Test email parser
def test_email_parser():
    parser = EmailParserTool()
    result = await parser.execute({"email_data": test_email_data})
    assert 'parsed_email' in result

# Test attachment downloader
def test_attachment_downloader():
    downloader = AttachmentDownloaderTool()
    result = await downloader.execute({"email_data": test_email_with_attachments})
    assert result['total_files'] > 0
```

## Future Extensions

The modular architecture makes it easy to add new features:

### New Tools
- **EmailAnalyzerTool**: Sentiment analysis, spam detection
- **EmailArchiverTool**: Archive emails to different formats
- **EmailSearchTool**: Advanced email search capabilities

### Enhanced Existing Tools
- **EmailParserTool**: Add OCR for image attachments
- **AttachmentDownloaderTool**: Add virus scanning
- **EmailCheckerTool**: Add email filtering rules

## Conclusion

The modular email tools architecture provides:
- ✅ **Maintainability**: Easy to understand and modify
- ✅ **Flexibility**: Use tools independently or together
- ✅ **Performance**: Only process what you need
- ✅ **Reliability**: Isolated error handling
- ✅ **Extensibility**: Easy to add new features
- ✅ **Testability**: Each component can be tested separately

This approach follows software engineering best practices and provides a solid foundation for email processing in the Agentic AI Framework. 