# File Vault Tool

The File Vault Tool provides secure temporary file storage and retrieval capabilities for agents. It creates an isolated, controlled environment where agents can safely store and access files without security risks.

## Overview

The File Vault Tool addresses the need for agents to have temporary file storage capabilities while maintaining strict security boundaries. It prevents:

- Execution of malicious files
- Access to files outside the vault
- Path traversal attacks
- Unauthorized system access

## Key Features

### 🔒 Security Features
- **Executable File Blocking**: Prevents storage of executable files (.exe, .bat, .sh, .py, etc.)
- **Path Traversal Protection**: Ensures files can only be accessed within the vault
- **Filename Sanitization**: Removes dangerous characters and normalizes filenames
- **Vault Isolation**: Each vault instance is completely isolated
- **Automatic Cleanup**: Vaults are automatically cleaned up when destroyed

### 📁 File Operations
- **Write**: Store text or binary files (base64 encoded)
- **Read**: Retrieve file contents with automatic content type detection
- **List**: Browse files with optional metadata and pattern matching
- **Delete**: Remove files from the vault
- **Info**: Get detailed file metadata
- **Cleanup**: Remove entire vault contents

### 🔧 Technical Features
- **Content Type Support**: Text files (UTF-8) and binary files (base64)
- **Metadata Tracking**: File size, creation/modification times, MD5 hashes
- **Pattern Matching**: List files using glob patterns
- **Unique Vault IDs**: Each vault gets a unique identifier
- **Restrictive Permissions**: Vault directories have 700 permissions

## Usage

### Basic Operations

```python
from agentic_ai_framework.tools.file_vault import FileVaultTool

# Create vault instance
vault = FileVaultTool()

# Write a text file
result = await vault.execute({
    "action": "write",
    "filename": "data.txt",
    "content": "Hello, world!",
    "content_type": "text"
})

# Read the file
result = await vault.execute({
    "action": "read",
    "filename": "data.txt"
})

# List all files
result = await vault.execute({
    "action": "list",
    "include_metadata": True
})
```

### Binary File Handling

```python
import base64

# Write binary file
binary_data = b"Binary content with \x00\x01\x02 bytes"
base64_content = base64.b64encode(binary_data).decode('utf-8')

result = await vault.execute({
    "action": "write",
    "filename": "data.bin",
    "content": base64_content,
    "content_type": "binary"
})

# Read binary file (returns base64 encoded content)
result = await vault.execute({
    "action": "read",
    "filename": "data.bin"
})

# Decode binary content
decoded_data = base64.b64decode(result['content'])
```

### Advanced Operations

```python
# Write with overwrite
result = await vault.execute({
    "action": "write",
    "filename": "config.json",
    "content": '{"setting": "value"}',
    "content_type": "text",
    "overwrite": True
})

# List files with pattern
result = await vault.execute({
    "action": "list",
    "pattern": "*.json"
})

# Get file information
result = await vault.execute({
    "action": "info",
    "filename": "config.json"
})

# Delete file
result = await vault.execute({
    "action": "delete",
    "filename": "data.txt"
})

# Clean up entire vault
result = await vault.execute({
    "action": "cleanup"
})
```

## Security Measures

### Executable File Blocking

The tool blocks files with executable extensions:

```python
# This will fail
try:
    result = await vault.execute({
        "action": "write",
        "filename": "malicious.exe",
        "content": "harmful code",
        "content_type": "text"
    })
except Exception as e:
    print(f"Blocked: {e}")
```

Blocked extensions include:
- `.exe`, `.bat`, `.cmd`, `.com`, `.pif`, `.scr`, `.vbs`, `.js`
- `.jar`, `.msi`, `.app`, `.command`, `.sh`
- `.py`, `.pl`, `.rb`, `.php`, `.asp`, `.aspx`, `.jsp`, `.cgi`
- `.dll`, `.so`, `.dylib`

### Path Traversal Protection

The tool prevents access to files outside the vault:

```python
# This will fail
try:
    result = await vault.execute({
        "action": "read",
        "filename": "../../../etc/passwd"
    })
except Exception as e:
    print(f"Blocked: {e}")
```

### Filename Sanitization

Dangerous characters are automatically sanitized:

```python
# Input: "file<name>.txt"
# Output: "file_name_.txt"
result = await vault.execute({
    "action": "write",
    "filename": "file<name>.txt",
    "content": "content",
    "content_type": "text"
})
```

## Agent Integration

### Dynamic Configuration

Agents can configure the vault tool dynamically:

```python
# Agent sets up vault configuration
vault.set_config({
    "max_file_size": 10485760,  # 10MB limit
    "allowed_extensions": [".txt", ".json", ".csv"],
    "retention_days": 7
})
```

### Workflow Example

```python
# Agent workflow using file vault
async def process_data_workflow():
    vault = FileVaultTool()
    
    # Step 1: Store raw data
    await vault.execute({
        "action": "write",
        "filename": "raw_data.csv",
        "content": raw_csv_data,
        "content_type": "text"
    })
    
    # Step 2: Process data and store results
    processed_data = process_csv_data(raw_csv_data)
    await vault.execute({
        "action": "write",
        "filename": "processed_results.json",
        "content": json.dumps(processed_data),
        "content_type": "text"
    })
    
    # Step 3: Store analysis report
    report = generate_report(processed_data)
    await vault.execute({
        "action": "write",
        "filename": "analysis_report.txt",
        "content": report,
        "content_type": "text"
    })
    
    # Step 4: List all generated files
    result = await vault.execute({
        "action": "list",
        "include_metadata": True
    })
    
    return result['files']
```

## API Reference

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | Operation: 'write', 'read', 'list', 'delete', 'info', 'cleanup' |
| `filename` | string | For write/read/delete/info | Name of the file to operate on |
| `content` | string | For write | File content to write |
| `content_type` | string | For write | 'text' or 'binary' (default: 'text') |
| `encoding` | string | For write | Text encoding (default: 'utf-8') |
| `overwrite` | boolean | For write | Overwrite existing files (default: false) |
| `pattern` | string | For list | File pattern (default: '*') |
| `include_metadata` | boolean | For list | Include file metadata (default: false) |

### Response Format

All operations return a dictionary with:

```python
{
    "status": "operation_result",
    "message": "Human readable message",
    # ... operation-specific fields
}
```

### File Metadata

File metadata includes:

```python
{
    "size": 1234,                    # File size in bytes
    "created": 1640995200.0,         # Creation timestamp
    "modified": 1640995200.0,        # Modification timestamp
    "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",  # MD5 hash
    "content_type": "text/plain"     # MIME type
}
```

## Best Practices

### 1. Use Descriptive Filenames
```python
# Good
"user_data_2024_01_15.json"
"processed_results_batch_001.csv"

# Avoid
"data.txt"
"file1.json"
```

### 2. Handle Large Files Appropriately
```python
# For large files, consider chunking
if len(content) > 1000000:  # 1MB
    # Split into chunks or compress
    pass
```

### 3. Clean Up Regularly
```python
# Clean up vault when done
await vault.execute({"action": "cleanup"})
```

### 4. Validate File Types
```python
# Check file extension before writing
allowed_extensions = ['.txt', '.json', '.csv']
if not any(filename.endswith(ext) for ext in allowed_extensions):
    raise Exception("File type not allowed")
```

### 5. Use Appropriate Content Types
```python
# For text data
"content_type": "text"

# For binary data (images, documents, etc.)
"content_type": "binary"
```

## Testing

Run the test script to verify functionality:

```bash
cd samples
python test_file_vault.py
```

The test script demonstrates:
- Basic file operations
- Security features
- Error handling
- Agent usage patterns

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure filename is correct and file exists
2. **Permission Denied**: Check vault directory permissions
3. **Invalid Content**: For binary files, ensure content is base64 encoded
4. **Security Blocked**: Check if filename contains executable extensions

### Debug Information

Enable debug logging to see detailed vault operations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Other Tools

The File Vault Tool works well with other framework tools:

- **Email Tools**: Store email attachments temporarily
- **HTTP Client**: Cache downloaded files
- **Data Extractor**: Store extracted data
- **Website Monitor**: Store monitoring results

This creates a comprehensive file management ecosystem for agents while maintaining security boundaries. 