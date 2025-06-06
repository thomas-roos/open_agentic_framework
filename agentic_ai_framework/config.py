"""
config.py - Enhanced Configuration Management with Memory Settings

Added memory management configuration options:
- Max agent memory entries limit
- Clear memory on startup setting
- Memory cleanup interval
"""

import os
from typing import Dict, Any

class Config:
    """Enhanced framework configuration management class with memory settings"""
    
    def __init__(self):
        """Initialize configuration with environment variables or defaults"""
        # Original settings
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = os.getenv("DEFAULT_MODEL", "granite3.2:2b")
        self.database_path = os.getenv("DATABASE_PATH", "agentic_ai.db")
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.max_agent_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "3"))
        self.scheduler_interval = int(os.getenv("SCHEDULER_INTERVAL", "60"))
        self.tools_directory = os.getenv("TOOLS_DIRECTORY", "tools")
        
        # NEW: Memory management settings
        self.max_agent_memory_entries = int(os.getenv("MAX_AGENT_MEMORY_ENTRIES", "5"))
        self.clear_memory_on_startup = os.getenv("CLEAR_MEMORY_ON_STARTUP", "true").lower() == "true"
        self.memory_cleanup_interval = int(os.getenv("MEMORY_CLEANUP_INTERVAL", "3600"))  # 1 hour
        self.memory_retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", "7"))  # Keep 7 days
        
        # Validate memory settings
        self._validate_memory_settings()
        
        # Model Warmup Configuration
        self.model_warmup_timeout = int(os.getenv("MODEL_WARMUP_TIMEOUT", "60"))
        self.max_concurrent_warmups = int(os.getenv("MAX_CONCURRENT_WARMUPS", "2"))
        self.auto_warmup_on_startup = os.getenv("AUTO_WARMUP_ON_STARTUP", "true").lower() == "true"
        self.warmup_interval_hours = int(os.getenv("WARMUP_INTERVAL_HOURS", "6"))
        self.max_idle_hours = int(os.getenv("MAX_IDLE_HOURS", "24"))
        self.warmup_enabled = os.getenv("WARMUP_ENABLED", "true").lower() == "true"
        self.background_maintenance = os.getenv("BACKGROUND_MAINTENANCE", "true").lower() == "true"
        self.log_warmup_details = os.getenv("LOG_WARMUP_DETAILS", "true").lower() == "true"
    
    def _validate_memory_settings(self):
        """Validate memory-related configuration settings"""
        if self.max_agent_memory_entries < 1:
            raise ValueError("max_agent_memory_entries must be at least 1")
        
        if self.memory_cleanup_interval < 60:
            raise ValueError("memory_cleanup_interval must be at least 60 seconds")
        
        if self.memory_retention_days < 1:
            raise ValueError("memory_retention_days must be at least 1")
    
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
        
        # Re-validate after updates
        self.validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Dictionary containing all configuration values
        """
        return {
            # Original settings
            "ollama_url": self.ollama_url,
            "default_model": self.default_model,
            "database_path": self.database_path,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "max_agent_iterations": self.max_agent_iterations,
            "scheduler_interval": self.scheduler_interval,
            "tools_directory": self.tools_directory,
            
            # NEW: Memory management settings
            "max_agent_memory_entries": self.max_agent_memory_entries,
            "clear_memory_on_startup": self.clear_memory_on_startup,
            "memory_cleanup_interval": self.memory_cleanup_interval,
            "memory_retention_days": self.memory_retention_days
            
            # Model warmup settings
            "model_warmup_timeout": self.model_warmup_timeout,
            "max_concurrent_warmups": self.max_concurrent_warmups,
            "auto_warmup_on_startup": self.auto_warmup_on_startup,
            "warmup_interval_hours": self.warmup_interval_hours,
            "max_idle_hours": self.max_idle_hours,
            "warmup_enabled": self.warmup_enabled,
            "background_maintenance": self.background_maintenance,
            "log_warmup_details": self.log_warmup_details
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
        
        # Validate memory settings
        self._validate_memory_settings()
    
    def get_memory_config(self) -> Dict[str, Any]:
        """
        Get memory-specific configuration
        
        Returns:
            Dictionary with memory management settings
        """
        return {
            "max_agent_memory_entries": self.max_agent_memory_entries,
            "clear_memory_on_startup": self.clear_memory_on_startup,
            "memory_cleanup_interval": self.memory_cleanup_interval,
            "memory_retention_days": self.memory_retention_days
        }
    
    def update_memory_config(self, **kwargs):
        """
        Update memory-specific configuration
        
        Args:
            **kwargs: Memory configuration parameters to update
        """
        valid_memory_keys = {
            "max_agent_memory_entries",
            "clear_memory_on_startup", 
            "memory_cleanup_interval",
            "memory_retention_days"
        }
        
        for key, value in kwargs.items():
            if key in valid_memory_keys:
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid memory configuration key: {key}")
        
        # Validate after update
        self._validate_memory_settings()
    
    def get_recommended_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get recommended configuration settings for different use cases
        
        Returns:
            Dictionary with recommended settings for different scenarios
        """
        return {
            "development": {
                "max_agent_memory_entries": 10,
                "clear_memory_on_startup": True,
                "memory_cleanup_interval": 1800,  # 30 minutes
                "memory_retention_days": 1
            },
            "production": {
                "max_agent_memory_entries": 5,
                "clear_memory_on_startup": False,
                "memory_cleanup_interval": 3600,  # 1 hour
                "memory_retention_days": 7
            },
            "testing": {
                "max_agent_memory_entries": 3,
                "clear_memory_on_startup": True,
                "memory_cleanup_interval": 600,  # 10 minutes
                "memory_retention_days": 1
            },
            "high_volume": {
                "max_agent_memory_entries": 3,
                "clear_memory_on_startup": False,
                "memory_cleanup_interval": 1800,  # 30 minutes
                "memory_retention_days": 3
            }
        }