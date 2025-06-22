"""
tools/rate_limiter.py - Rate Limiting Utility

Utility for managing API rate limits and request throttling.
Can be used by other tools to prevent hitting API rate limits.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, max_requests: int = 100, time_window: float = 60.0):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        Acquire permission to make a request
        
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Check if we can make a new request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    async def wait_for_slot(self) -> float:
        """
        Wait until a request slot is available
        
        Returns:
            Time waited in seconds
        """
        start_time = time.time()
        
        while not await self.acquire():
            # Calculate wait time
            if self.requests:
                oldest_request = self.requests[0]
                wait_time = max(0.1, oldest_request + self.time_window - time.time())
            else:
                wait_time = 0.1
            
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        return time.time() - start_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics"""
        now = time.time()
        
        # Clean old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        return {
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "current_requests": len(self.requests),
            "available_slots": max(0, self.max_requests - len(self.requests)),
            "utilization_percent": (len(self.requests) / self.max_requests) * 100
        }

class RateLimitManager:
    """Manager for multiple rate limiters"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
    
    def add_limiter(self, name: str, max_requests: int, time_window: float) -> RateLimiter:
        """Add a new rate limiter"""
        limiter = RateLimiter(max_requests, time_window)
        self.limiters[name] = limiter
        return limiter
    
    def get_limiter(self, name: str) -> Optional[RateLimiter]:
        """Get a rate limiter by name"""
        return self.limiters.get(name)
    
    def remove_limiter(self, name: str) -> bool:
        """Remove a rate limiter"""
        if name in self.limiters:
            del self.limiters[name]
            return True
        return False
    
    async def acquire(self, name: str) -> bool:
        """Acquire permission from a specific limiter"""
        limiter = self.get_limiter(name)
        if limiter:
            return await limiter.acquire()
        return True  # No limiter means no limit
    
    async def wait_for_slot(self, name: str) -> float:
        """Wait for a slot in a specific limiter"""
        limiter = self.get_limiter(name)
        if limiter:
            return await limiter.wait_for_slot()
        return 0.0  # No limiter means no wait
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all limiters"""
        return {name: limiter.get_stats() for name, limiter in self.limiters.items()}

# Global rate limit manager instance
rate_limit_manager = RateLimitManager()

# Common rate limit configurations
COMMON_RATE_LIMITS = {
    "github_api": {"max_requests": 5000, "time_window": 3600},  # 5000 requests per hour
    "npm_registry": {"max_requests": 100, "time_window": 60},   # 100 requests per minute
    "pypi": {"max_requests": 100, "time_window": 60},           # 100 requests per minute
    "maven_central": {"max_requests": 50, "time_window": 60},   # 50 requests per minute
    "default": {"max_requests": 100, "time_window": 60}         # Default rate limit
}

def setup_common_rate_limits():
    """Setup common rate limit configurations"""
    for name, config in COMMON_RATE_LIMITS.items():
        rate_limit_manager.add_limiter(name, config["max_requests"], config["time_window"])
    logger.info("Common rate limits configured")

# Initialize common rate limits
setup_common_rate_limits() 