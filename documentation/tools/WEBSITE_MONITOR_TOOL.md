# Website Monitor Tool

The Website Monitor Tool provides comprehensive website monitoring capabilities including availability checking, performance monitoring, and alerting. It can monitor multiple URLs and track various metrics.

## Overview

The Website Monitor Tool offers:
- URL availability monitoring
- Response time tracking
- HTTP status code monitoring
- Content validation
- Custom alerting
- Historical data tracking
- SSL certificate monitoring

## Configuration

### Basic Configuration
```json
{
  "name": "monitor_website",
  "tool": "website_monitor",
  "config": {
    "url": "https://example.com",
    "timeout": 30,
    "expected_status": 200
  }
}
```

### Advanced Configuration
```json
{
  "name": "comprehensive_monitoring",
  "tool": "website_monitor",
  "config": {
    "url": "https://example.com",
    "timeout": 30,
    "max_retries": 3,
    "expected_status": 200,
    "content_validation": {
      "required_text": ["Welcome", "Home"],
      "forbidden_text": ["Error", "Maintenance"]
    },
    "performance_thresholds": {
      "max_response_time": 2000,
      "max_size": 1048576
    },
    "ssl_check": true,
    "headers_check": {
      "required": ["X-Frame-Options"],
      "forbidden": ["Server"]
    }
  }
}
```

## Parameters

### Required Parameters
- **url**: The URL to monitor

### Optional Parameters
- **timeout**: Request timeout in seconds (default: 30)
- **max_retries**: Maximum retry attempts (default: 3)
- **expected_status**: Expected HTTP status code (default: 200)
- **content_validation**: Content validation rules
- **performance_thresholds**: Performance monitoring thresholds
- **ssl_check**: Whether to check SSL certificate (default: false)
- **headers_check**: HTTP headers validation
- **user_agent**: Custom user agent string
- **follow_redirects**: Whether to follow redirects (default: true)

## Monitoring Types

### 1. Basic Availability Monitoring
```json
{
  "config": {
    "url": "https://example.com",
    "timeout": 30,
    "expected_status": 200
  }
}
```

### 2. Content Validation
```json
{
  "config": {
    "url": "https://example.com",
    "content_validation": {
      "required_text": ["Welcome", "Home Page"],
      "forbidden_text": ["Error", "Maintenance", "Down"],
      "regex_patterns": {
        "title": "<title>.*</title>",
        "meta_description": "<meta name=\"description\".*?>"
      }
    }
  }
}
```

### 3. Performance Monitoring
```json
{
  "config": {
    "url": "https://example.com",
    "performance_thresholds": {
      "max_response_time": 2000,
      "max_size": 1048576,
      "min_size": 1000
    }
  }
}
```

### 4. SSL Certificate Monitoring
```json
{
  "config": {
    "url": "https://example.com",
    "ssl_check": true,
    "ssl_thresholds": {
      "min_days_until_expiry": 30,
      "required_protocols": ["TLSv1.2", "TLSv1.3"]
    }
  }
}
```

## Examples

### Simple Website Check
```json
{
  "name": "check_website",
  "tool": "website_monitor",
  "config": {
    "url": "https://example.com",
    "timeout": 30
  }
}
```

### E-commerce Site Monitoring
```json
{
  "name": "monitor_ecommerce",
  "tool": "website_monitor",
  "config": {
    "url": "https://shop.example.com",
    "content_validation": {
      "required_text": ["Add to Cart", "Checkout"],
      "forbidden_text": ["Out of Stock", "Maintenance"]
    },
    "performance_thresholds": {
      "max_response_time": 3000
    }
  }
}
```

### API Endpoint Monitoring
```json
{
  "name": "monitor_api",
  "tool": "website_monitor",
  "config": {
    "url": "https://api.example.com/health",
    "expected_status": 200,
    "content_validation": {
      "required_text": ["status", "healthy"],
      "regex_patterns": {
        "status": "\"status\":\\s*\"healthy\""
      }
    },
    "headers_check": {
      "required": ["Content-Type"],
      "expected_values": {
        "Content-Type": "application/json"
      }
    }
  }
}
```

### Multi-URL Monitoring
```json
{
  "name": "monitor_multiple_sites",
  "tool": "website_monitor",
  "config": {
    "urls": [
      "https://example.com",
      "https://api.example.com",
      "https://docs.example.com"
    ],
    "timeout": 30,
    "parallel_checks": true
  }
}
```

## Response Format

The tool returns comprehensive monitoring results:

```json
{
  "success": true,
  "url": "https://example.com",
  "status": "healthy",
  "response_time": 245,
  "status_code": 200,
  "content_size": 15420,
  "ssl_info": {
    "valid": true,
    "expires": "2024-12-31T23:59:59Z",
    "days_until_expiry": 180,
    "protocol": "TLSv1.3"
  },
  "content_validation": {
    "passed": true,
    "required_text_found": ["Welcome", "Home"],
    "forbidden_text_found": []
  },
  "performance": {
    "response_time_ok": true,
    "size_ok": true
  },
  "headers": {
    "content-type": "text/html; charset=utf-8",
    "server": "nginx/1.18.0"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Responses

### Website Down
```json
{
  "success": false,
  "url": "https://example.com",
  "status": "down",
  "error": "Connection timeout",
  "response_time": null,
  "status_code": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Content Validation Failed
```json
{
  "success": false,
  "url": "https://example.com",
  "status": "content_error",
  "response_time": 245,
  "status_code": 200,
  "content_validation": {
    "passed": false,
    "required_text_found": [],
    "forbidden_text_found": ["Maintenance"],
    "errors": ["Required text 'Welcome' not found", "Forbidden text 'Maintenance' found"]
  }
}
```

## Integration Examples

### With Email Sender for Alerts
```json
{
  "steps": [
    {
      "name": "check_website",
      "tool": "website_monitor",
      "config": {
        "url": "https://example.com",
        "timeout": 30
      }
    },
    {
      "name": "send_alert",
      "tool": "email_sender",
      "condition": {
        "step": "check_website",
        "status": "not_healthy"
      },
      "config": {
        "to": "admin@example.com",
        "subject": "Website Alert: {{step.status}}",
        "body": "Website {{step.url}} is {{step.status}}. Response time: {{step.response_time}}ms"
      }
    }
  ]
}
```

### With HTTP Client for Detailed Checks
```json
{
  "steps": [
    {
      "name": "basic_check",
      "tool": "website_monitor",
      "config": {
        "url": "https://example.com"
      }
    },
    {
      "name": "detailed_check",
      "tool": "http_client",
      "condition": {
        "step": "basic_check",
        "status": "healthy"
      },
      "config": {
        "method": "GET",
        "url": "https://example.com/api/health",
        "timeout": 10
      }
    }
  ]
}
```

## Best Practices

### 1. Monitoring Frequency
- Set appropriate monitoring intervals
- Avoid overwhelming servers with too frequent checks
- Use different intervals for different types of sites

### 2. Timeout Configuration
```json
{
  "config": {
    "url": "https://example.com",
    "timeout": 30,
    "max_retries": 3
  }
}
```

### 3. Content Validation
- Use specific, unique text for validation
- Avoid generic terms that might change
- Include both positive and negative checks

### 4. Performance Thresholds
```json
{
  "config": {
    "performance_thresholds": {
      "max_response_time": 2000,
      "max_size": 1048576
    }
  }
}
```

### 5. SSL Monitoring
```json
{
  "config": {
    "ssl_check": true,
    "ssl_thresholds": {
      "min_days_until_expiry": 30
    }
  }
}
```

## Alerting Configuration

### Email Alerts
```json
{
  "config": {
    "url": "https://example.com",
    "alerts": {
      "email": {
        "enabled": true,
        "recipients": ["admin@example.com"],
        "conditions": ["down", "slow", "content_error"]
      }
    }
  }
}
```

### Webhook Alerts
```json
{
  "config": {
    "url": "https://example.com",
    "alerts": {
      "webhook": {
        "enabled": true,
        "url": "https://hooks.slack.com/services/xxx/yyy/zzz",
        "conditions": ["down", "ssl_expiring"]
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **False Positives**
   - Adjust timeout values
   - Check network connectivity
   - Verify URL accessibility

2. **Content Validation Failures**
   - Review required/forbidden text
   - Check for dynamic content
   - Update validation rules

3. **Performance Issues**
   - Adjust performance thresholds
   - Consider network conditions
   - Monitor during peak hours

4. **SSL Certificate Issues**
   - Check certificate expiration
   - Verify certificate chain
   - Update SSL requirements

### Debug Mode
Enable debug mode for detailed monitoring information:
```json
{
  "config": {
    "url": "https://example.com",
    "debug": true,
    "verbose_logging": true
  }
}
```

## Advanced Features

### Custom Headers
```json
{
  "config": {
    "url": "https://api.example.com",
    "headers": {
      "Authorization": "Bearer token",
      "User-Agent": "CustomMonitor/1.0"
    }
  }
}
```

### Authentication
```json
{
  "config": {
    "url": "https://protected.example.com",
    "auth": {
      "type": "basic",
      "username": "monitor",
      "password": "password"
    }
  }
}
```

### Scheduled Monitoring
```json
{
  "config": {
    "url": "https://example.com",
    "schedule": {
      "interval": "5m",
      "timezone": "UTC",
      "business_hours_only": true
    }
  }
}
```

---

*For more information about website monitoring patterns and examples, see the [Agent Tooling Examples](AGENT_TOOLING_EXAMPLES.md) or explore [workflow examples](../workflows/).* 