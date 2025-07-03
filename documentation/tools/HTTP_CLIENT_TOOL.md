# HTTP Client Tool

The HTTP Client Tool provides a robust interface for making HTTP requests to external APIs and services. It supports various HTTP methods, authentication, error handling, and request customization.

## Overview

The HTTP Client Tool is designed to handle web requests with features like:
- Multiple HTTP methods (GET, POST, PUT, DELETE, etc.)
- Authentication support (Basic, Bearer, API Key)
- Request/response headers management
- Error handling and retry logic
- Request timeout configuration
- Response validation

## Configuration

### Basic Configuration
```json
{
  "name": "http_request",
  "tool": "http_client",
  "config": {
    "method": "GET",
    "url": "https://api.example.com/data",
    "timeout": 30,
    "max_retries": 3
  }
}
```

### Advanced Configuration
```json
{
  "name": "api_request",
  "tool": "http_client",
  "config": {
    "method": "POST",
    "url": "https://api.example.com/submit",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer your-token"
    },
    "data": {
      "key": "value",
      "nested": {
        "data": "example"
      }
    },
    "timeout": 60,
    "max_retries": 5,
    "retry_delay": 1,
    "verify_ssl": true
  }
}
```

## Parameters

### Required Parameters
- **method**: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- **url**: Target URL for the request

### Optional Parameters
- **headers**: Dictionary of HTTP headers
- **data**: Request body data (for POST, PUT, PATCH)
- **params**: URL query parameters
- **timeout**: Request timeout in seconds (default: 30)
- **max_retries**: Maximum number of retry attempts (default: 3)
- **retry_delay**: Delay between retries in seconds (default: 1)
- **verify_ssl**: Whether to verify SSL certificates (default: true)
- **auth**: Authentication credentials
- **cookies**: Request cookies

## Authentication

### Basic Authentication
```json
{
  "config": {
    "method": "GET",
    "url": "https://api.example.com/protected",
    "auth": {
      "type": "basic",
      "username": "user",
      "password": "pass"
    }
  }
}
```

### Bearer Token Authentication
```json
{
  "config": {
    "method": "GET",
    "url": "https://api.example.com/protected",
    "headers": {
      "Authorization": "Bearer your-token-here"
    }
  }
}
```

### API Key Authentication
```json
{
  "config": {
    "method": "GET",
    "url": "https://api.example.com/data",
    "headers": {
      "X-API-Key": "your-api-key-here"
    }
  }
}
```

## Examples

### Simple GET Request
```json
{
  "name": "fetch_data",
  "tool": "http_client",
  "config": {
    "method": "GET",
    "url": "https://jsonplaceholder.typicode.com/posts/1"
  }
}
```

### POST Request with JSON Data
```json
{
  "name": "create_post",
  "tool": "http_client",
  "config": {
    "method": "POST",
    "url": "https://jsonplaceholder.typicode.com/posts",
    "headers": {
      "Content-Type": "application/json"
    },
    "data": {
      "title": "New Post",
      "body": "This is the content of the post",
      "userId": 1
    }
  }
}
```

### File Upload
```json
{
  "name": "upload_file",
  "tool": "http_client",
  "config": {
    "method": "POST",
    "url": "https://api.example.com/upload",
    "headers": {
      "Content-Type": "multipart/form-data"
    },
    "data": {
      "file": "@/path/to/file.txt",
      "description": "Uploaded file"
    }
  }
}
```

### API with Query Parameters
```json
{
  "name": "search_api",
  "tool": "http_client",
  "config": {
    "method": "GET",
    "url": "https://api.example.com/search",
    "params": {
      "q": "search term",
      "limit": 10,
      "offset": 0
    }
  }
}
```

## Response Format

The tool returns a structured response with the following format:

```json
{
  "success": true,
  "status_code": 200,
  "headers": {
    "content-type": "application/json",
    "content-length": "1234"
  },
  "data": {
    "id": 1,
    "title": "Example Response",
    "content": "Response data here"
  },
  "url": "https://api.example.com/data",
  "method": "GET",
  "elapsed_time": 0.234
}
```

## Error Handling

### HTTP Error Responses
```json
{
  "success": false,
  "status_code": 404,
  "error": "Not Found",
  "data": null,
  "url": "https://api.example.com/missing",
  "method": "GET"
}
```

### Network Errors
```json
{
  "success": false,
  "error": "Connection timeout",
  "status_code": null,
  "data": null,
  "url": "https://api.example.com/timeout",
  "method": "GET"
}
```

## Best Practices

### 1. Timeout Configuration
Always set appropriate timeouts to prevent hanging requests:
```json
{
  "timeout": 30,
  "max_retries": 3
}
```

### 2. Error Handling
Implement proper error handling in workflows:
```json
{
  "name": "api_call",
  "tool": "http_client",
  "config": {
    "method": "GET",
    "url": "https://api.example.com/data",
    "max_retries": 3
  },
  "error_handling": {
    "on_failure": "continue",
    "fallback": "default_data"
  }
}
```

### 3. Rate Limiting
Use the Rate Limiter utility for API calls:
```json
{
  "name": "rate_limited_api_call",
  "tool": "http_client",
  "config": {
    "method": "GET",
    "url": "https://api.github.com/repos",
    "rate_limit": "github_api"
  }
}
```

### 4. Security
- Use HTTPS for all requests
- Store sensitive data in environment variables
- Validate SSL certificates
- Use appropriate authentication methods

## Integration with Other Tools

### With Rate Limiter
```json
{
  "steps": [
    {
      "name": "wait_for_rate_limit",
      "tool": "rate_limiter",
      "config": {
        "limiter": "github_api"
      }
    },
    {
      "name": "api_request",
      "tool": "http_client",
      "config": {
        "method": "GET",
        "url": "https://api.github.com/user"
      }
    }
  ]
}
```

### With JSON Validator
```json
{
  "steps": [
    {
      "name": "fetch_data",
      "tool": "http_client",
      "config": {
        "method": "GET",
        "url": "https://api.example.com/data"
      }
    },
    {
      "name": "validate_response",
      "tool": "json_validator",
      "input": {
        "source": "step_output",
        "step": "fetch_data",
        "field": "data"
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   - Set `verify_ssl: false` for self-signed certificates
   - Ensure proper certificate chain

2. **Timeout Errors**
   - Increase timeout value
   - Check network connectivity
   - Verify server response times

3. **Authentication Errors**
   - Verify credentials
   - Check token expiration
   - Ensure proper header format

4. **Rate Limiting**
   - Implement retry logic with exponential backoff
   - Use rate limiter utility
   - Check API documentation for limits

### Debug Information
Enable debug logging to troubleshoot issues:
```json
{
  "config": {
    "method": "GET",
    "url": "https://api.example.com/data",
    "debug": true
  }
}
```

## Performance Considerations

- Use connection pooling for multiple requests
- Implement caching for frequently accessed data
- Consider async requests for parallel processing
- Monitor response times and error rates

---

*For more information about HTTP client usage, see the [Agent Tooling Examples](AGENT_TOOLING_EXAMPLES.md) or explore [workflow examples](../workflows/).* 