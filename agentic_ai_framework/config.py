"""
config.py - Configuration Management

Handles all framework configuration settings using environment variables
with sensible defaults. Allows dynamic updates via API.
"""

import os
from typing import Dict, Any

class Config:
    """Framework configuration management class"""
    
    def __init__(self):
        """Initialize configuration with environment variables or defaults"""
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = os.getenv("DEFAULT_MODEL", "granite3.2:2b")
        self.database_path = os.getenv("DATABASE_PATH", "agentic_ai.db")
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.max_agent_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "3"))
        self.scheduler_interval = int(os.getenv("SCHEDULER_INTERVAL", "60"))
        self.tools_directory = os.getenv("TOOLS_DIRECTORY", "tools")
    
    def update(self, updates: Dict[str, Any]):
        """
        Update configuration with new values
        
        Args:
            updates: Dictionary of configuration keys and new values
            
        Raises:
            ValueError: If unknown configuration key is provided
        """
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Dictionary containing all configuration values
        """
        return {
            "ollama_url": self.ollama_url,
            "default_model": self.default_model,
            "database_path": self.database_path,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "max_agent_iterations": self.max_agent_iterations,
            "scheduler_interval": self.scheduler_interval,
            "tools_directory": self.tools_directory
        }
    
    def validate(self):
        """
        Validate configuration values
        
        Raises:
            ValueError: If configuration values are invalid
        """
        if self.api_port < 1 or self.api_port > 65535:
            raise ValueError("API port must be between 1 and 65535")
        
        if self.max_agent_iterations < 1:
            raise ValueError("Max agent iterations must be at least 1")
        
        if self.scheduler_interval < 1:
            raise ValueError("Scheduler interval must be at least 1 second")
        
        if not self.ollama_url.startswith(("http://", "https://")):
            raise ValueError("Ollama URL must start with http:// or https://")