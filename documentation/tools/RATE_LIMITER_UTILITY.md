# Rate Limiter Utility

The Rate Limiter Utility provides sophisticated rate limiting capabilities for managing API requests and preventing rate limit violations. It supports multiple rate limiters, configurable time windows, and automatic throttling.

## Overview

The Rate Limiter Utility offers:
- Multiple rate limiter instances
- Configurable request limits and time windows
- Automatic request throttling
- Statistics and monitoring
- Pre-configured limits for common APIs
- Thread-safe async operations

## Configuration

### Basic Usage
```python
from tools.rate_limiter import RateLimiter, rate_limit_manager

# Create a rate limiter
limiter = RateLimiter(max_requests=100, time_window=60.0)

# Use in async context
async def make_request():
    if await limiter.acquire():
        # Make API request
        pass
    else:
        # Wait for available slot
        await limiter.wait_for_slot()
```

### Advanced Configuration
```python
from tools.rate_limiter import rate_limit_manager, setup_common_rate_limits

# Setup common rate limits
setup_common_rate_limits()

# Get specific limiter
github_limiter = rate_limit_manager.get_limiter("github_api")

# Use with automatic waiting
async def github_request():
    await rate_limit_manager.wait_for_slot("github_api")
    # Make GitHub API request
```

## Parameters

### RateLimiter Class
- **max_requests**: Maximum requests allowed in time window
- **time_window**: Time window in seconds
- **requests**: Internal deque for tracking requests
- **_lock**: Async lock for thread safety

### RateLimitManager Class
- **limiters**: Dictionary of named rate limiters
- **add_limiter()**: Add new rate limiter
- **get_limiter()**: Get existing limiter
- **remove_limiter()**: Remove limiter
- **acquire()**: Check if request is allowed
- **wait_for_slot()**: Wait for available slot

## Usage Examples

### 1. Basic Rate Limiting
```python
import asyncio
from tools.rate_limiter import RateLimiter

async def basic_example():
    limiter = RateLimiter(max_requests=10, time_window=60.0)
    
    for i in range(15):
        if await limiter.acquire():
            print(f"Request {i+1}: Allowed")
            # Make API request
        else:
            print(f"Request {i+1}: Rate limited")
            await limiter.wait_for_slot()
            print(f"Request {i+1}: Now allowed after waiting")

# Run example
asyncio.run(basic_example())
```

### 2. Named Rate Limiters
```python
import asyncio
from tools.rate_limiter import rate_limit_manager

async def named_limiter_example():
    # Add custom rate limiters
    rate_limit_manager.add_limiter("my_api", max_requests=50, time_window=60.0)
    rate_limit_manager.add_limiter("external_service", max_requests=20, time_window=300.0)
    
    # Use specific limiters
    for i in range(10):
        await rate_limit_manager.wait_for_slot("my_api")
        print(f"My API request {i+1}")
        
        await rate_limit_manager.wait_for_slot("external_service")
        print(f"External service request {i+1}")

# Run example
asyncio.run(named_limiter_example())
```

### 3. Statistics and Monitoring
```python
import asyncio
from tools.rate_limiter import RateLimiter

async def statistics_example():
    limiter = RateLimiter(max_requests=100, time_window=60.0)
    
    # Make some requests
    for i in range(25):
        await limiter.acquire()
    
    # Get statistics
    stats = limiter.get_stats()
    print(f"Current requests: {stats['current_requests']}")
    print(f"Available slots: {stats['available_slots']}")
    print(f"Utilization: {stats['utilization_percent']:.1f}%")

# Run example
asyncio.run(statistics_example())
```

### 4. Integration with HTTP Client
```python
import asyncio
from tools.rate_limiter import rate_limit_manager
from tools.http_client import HttpClientTool

async def http_with_rate_limiting():
    # Setup rate limit for API
    rate_limit_manager.add_limiter("api_service", max_requests=10, time_window=60.0)
    
    http_client = HttpClientTool({})
    
    urls = [
        "https://api.example.com/endpoint1",
        "https://api.example.com/endpoint2",
        "https://api.example.com/endpoint3"
    ]
    
    for url in urls:
        # Wait for rate limit slot
        await rate_limit_manager.wait_for_slot("api_service")
        
        # Make HTTP request
        response = await http_client.execute({
            "method": "GET",
            "url": url
        })
        
        print(f"Request to {url}: {response['status_code']}")

# Run example
asyncio.run(http_with_rate_limiting())
```

## Pre-configured Rate Limits

The utility includes common rate limit configurations:

```python
COMMON_RATE_LIMITS = {
    "github_api": {"max_requests": 5000, "time_window": 3600},  # 5000 requests per hour
    "npm_registry": {"max_requests": 100, "time_window": 60},   # 100 requests per minute
    "pypi": {"max_requests": 100, "time_window": 60},           # 100 requests per minute
    "maven_central": {"max_requests": 50, "time_window": 60},   # 50 requests per minute
    "default": {"max_requests": 100, "time_window": 60}         # Default rate limit
}
```

### Using Pre-configured Limits
```python
import asyncio
from tools.rate_limiter import setup_common_rate_limits, rate_limit_manager

async def github_api_example():
    # Setup common limits
    setup_common_rate_limits()
    
    # Use GitHub API rate limiter
    for i in range(10):
        await rate_limit_manager.wait_for_slot("github_api")
        print(f"GitHub API request {i+1}")
        # Make GitHub API call

# Run example
asyncio.run(github_api_example())
```

## Workflow Integration

### 1. HTTP Client with Rate Limiting
```json
{
  "steps": [
    {
      "name": "wait_for_rate_limit",
      "tool": "rate_limiter",
      "config": {
        "limiter": "api_service",
        "max_requests": 10,
        "time_window": 60
      }
    },
    {
      "name": "api_request",
      "tool": "http_client",
      "config": {
        "method": "GET",
        "url": "https://api.example.com/data"
      }
    }
  ]
}
```

### 2. Multiple API Calls
```json
{
  "steps": [
    {
      "name": "github_rate_limit",
      "tool": "rate_limiter",
      "config": {
        "limiter": "github_api"
      }
    },
    {
      "name": "github_request",
      "tool": "http_client",
      "config": {
        "method": "GET",
        "url": "https://api.github.com/user/repos"
      }
    },
    {
      "name": "npm_rate_limit",
      "tool": "rate_limiter",
      "config": {
        "limiter": "npm_registry"
      }
    },
    {
      "name": "npm_request",
      "tool": "http_client",
      "config": {
        "method": "GET",
        "url": "https://registry.npmjs.org/package-name"
      }
    }
  ]
}
```

## Statistics and Monitoring

### Get Limiter Statistics
```python
import asyncio
from tools.rate_limiter import rate_limit_manager, setup_common_rate_limits

async def monitoring_example():
    setup_common_rate_limits()
    
    # Make some requests
    for i in range(5):
        await rate_limit_manager.wait_for_slot("github_api")
        print(f"GitHub request {i+1}")
    
    # Get all statistics
    all_stats = rate_limit_manager.get_all_stats()
    
    for limiter_name, stats in all_stats.items():
        print(f"\n{limiter_name}:")
        print(f"  Current requests: {stats['current_requests']}")
        print(f"  Available slots: {stats['available_slots']}")
        print(f"  Utilization: {stats['utilization_percent']:.1f}%")

# Run example
asyncio.run(monitoring_example())
```

### Real-time Monitoring
```python
import asyncio
import time
from tools.rate_limiter import RateLimiter

async def real_time_monitoring():
    limiter = RateLimiter(max_requests=10, time_window=60.0)
    
    while True:
        stats = limiter.get_stats()
        print(f"Time: {time.strftime('%H:%M:%S')}")
        print(f"Requests: {stats['current_requests']}/{stats['max_requests']}")
        print(f"Utilization: {stats['utilization_percent']:.1f}%")
        print("-" * 30)
        
        await asyncio.sleep(5)  # Update every 5 seconds

# Run example (Ctrl+C to stop)
# asyncio.run(real_time_monitoring())
```

## Best Practices

### 1. Appropriate Rate Limits
```python
# Conservative limits for external APIs
rate_limit_manager.add_limiter("external_api", max_requests=50, time_window=60.0)

# More generous limits for internal services
rate_limit_manager.add_limiter("internal_api", max_requests=1000, time_window=60.0)
```

### 2. Error Handling
```python
import asyncio
from tools.rate_limiter import RateLimiter

async def robust_rate_limiting():
    limiter = RateLimiter(max_requests=10, time_window=60.0)
    
    try:
        # Wait with timeout
        await asyncio.wait_for(limiter.wait_for_slot(), timeout=300.0)
        # Make request
    except asyncio.TimeoutError:
        print("Rate limit wait timeout - service may be overloaded")
    except Exception as e:
        print(f"Rate limiting error: {e}")

# Run example
asyncio.run(robust_rate_limiting())
```

### 3. Monitoring and Alerts
```python
import asyncio
from tools.rate_limiter import rate_limit_manager

async def monitor_rate_limits():
    while True:
        all_stats = rate_limit_manager.get_all_stats()
        
        for limiter_name, stats in all_stats.items():
            utilization = stats['utilization_percent']
            
            if utilization > 80:
                print(f"WARNING: {limiter_name} at {utilization:.1f}% utilization")
            elif utilization > 95:
                print(f"CRITICAL: {limiter_name} at {utilization:.1f}% utilization")
        
        await asyncio.sleep(30)  # Check every 30 seconds

# Run example
# asyncio.run(monitor_rate_limits())
```

## Troubleshooting

### Common Issues

1. **Rate Limit Too Aggressive**
   - Increase `max_requests` or `time_window`
   - Monitor actual API response headers
   - Adjust based on API documentation

2. **Performance Issues**
   - Use appropriate time windows
   - Avoid too frequent statistics calls
   - Consider caching for high-frequency operations

3. **Memory Usage**
   - Clean up old rate limiters when not needed
   - Monitor request history size
   - Use appropriate time windows

### Debug Mode
```python
import logging
from tools.rate_limiter import RateLimiter

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def debug_example():
    limiter = RateLimiter(max_requests=5, time_window=60.0)
    
    for i in range(10):
        await limiter.wait_for_slot()  # Debug logs will show wait times
        print(f"Request {i+1} completed")

# Run example
asyncio.run(debug_example())
```

## Advanced Features

### Custom Rate Limiting Strategies
```python
import asyncio
from tools.rate_limiter import RateLimiter

class AdaptiveRateLimiter(RateLimiter):
    def __init__(self, initial_max_requests, time_window):
        super().__init__(initial_max_requests, time_window)
        self.adaptive_limits = []
    
    async def adaptive_acquire(self):
        # Implement adaptive rate limiting based on response times
        if await self.acquire():
            return True
        else:
            # Adjust limits based on performance
            self.max_requests = max(1, self.max_requests - 1)
            return False

# Usage
async def adaptive_example():
    limiter = AdaptiveRateLimiter(max_requests=10, time_window=60.0)
    # Use adaptive rate limiting
```

### Multiple Time Windows
```python
import asyncio
from tools.rate_limiter import RateLimitManager

async def multi_window_example():
    manager = RateLimitManager()
    
    # Different limits for different time windows
    manager.add_limiter("per_minute", max_requests=60, time_window=60.0)
    manager.add_limiter("per_hour", max_requests=1000, time_window=3600.0)
    manager.add_limiter("per_day", max_requests=10000, time_window=86400.0)
    
    # Check all limits before making request
    await manager.wait_for_slot("per_minute")
    await manager.wait_for_slot("per_hour")
    await manager.wait_for_slot("per_day")
    
    # Make request
    print("All rate limits satisfied")

# Run example
asyncio.run(multi_window_example())
```

---

*For more information about rate limiting patterns and examples, see the [Agent Tooling Examples](AGENT_TOOLING_EXAMPLES.md) or explore [workflow examples](../workflows/).* 