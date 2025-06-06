"""
config.py - Enhanced Configuration with Model Warmup Support

Configuration management for the Agentic AI Framework with proper syntax.
"""

import os
from typing import Dict, Any

class Config:
    """Enhanced configuration with model warmup support"""
    
    def __init__(self):
        # Core API Configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = os.getenv("DEFAULT_MODEL", "granite3.2:2b")
        self.database_path = os.getenv("DATABASE_PATH", "data/agentic_ai.db")
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        
        # Agent Configuration
        self.max_agent_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))
        self.scheduler_interval = int(os.getenv("SCHEDULER_INTERVAL", "60"))
        self.tools_directory = os.getenv("TOOLS_DIRECTORY", "tools")
        
        # Memory Management Configuration
        self.max_agent_memory_entries = int(os.getenv("MAX_AGENT_MEMORY_ENTRIES", "20"))
        self.clear_memory_on_startup = os.getenv("CLEAR_MEMORY_ON_STARTUP", "false").lower() == "true"
        self.memory_cleanup_interval = int(os.getenv("MEMORY_CLEANUP_INTERVAL", "3600"))  # 1 hour
        self.memory_retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", "7"))
        
        # Model Warmup Configuration
        self.model_warmup_timeout = int(os.getenv("MODEL_WARMUP_TIMEOUT", "60"))
        self.max_concurrent_warmups = int(os.getenv("MAX_CONCURRENT_WARMUPS", "2"))
        self.auto_warmup_on_startup = os.getenv("AUTO_WARMUP_ON_STARTUP", "true").lower() == "true"
        self.warmup_interval_hours = int(os.getenv("WARMUP_INTERVAL_HOURS", "6"))
        self.max_idle_hours = int(os.getenv("MAX_IDLE_HOURS", "24"))
        self.warmup_enabled = os.getenv("WARMUP_ENABLED", "true").lower() == "true"
        self.background_maintenance = os.getenv("BACKGROUND_MAINTENANCE", "true").lower() == "true"
        self.log_warmup_details = os.getenv("LOG_WARMUP_DETAILS", "true").lower() == "true"
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            # Core API settings
            "ollama_url": self.ollama_url,
            "default_model": self.default_model,
            "database_path": self.database_path,
            "api_host": self.api_host,
            "api_port": self.api_port,
            
            # Agent settings
            "max_agent_iterations": self.max_agent_iterations,
            "scheduler_interval": self.scheduler_interval,
            "tools_directory": self.tools_directory,
            
            # Memory management settings
            "max_agent_memory_entries": self.max_agent_memory_entries,
            "clear_memory_on_startup": self.clear_memory_on_startup,
            "memory_cleanup_interval": self.memory_cleanup_interval,
            "memory_retention_days": self.memory_retention_days,
            
            # Model warmup settings
            "model_warmup_timeout": self.model_warmup_timeout,
            "max_concurrent_warmups": self.max_concurrent_warmups,
            "auto_warmup_on_startup": self.auto_warmup_on_startup,
            "warmup_interval_hours": self.warmup_interval_hours,
            "max_idle_hours": self.max_idle_hours,
            "warmup_enabled": self.warmup_enabled,
            "background_maintenance": self.background_maintenance,
            "log_warmup_details": self.log_warmup_details,
            
            # Logging settings
            "log_level": self.log_level,
            "log_format": self.log_format
        }
    
    def update(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    def validate(self):
        """Validate configuration values"""
        errors = []
        
        # Validate ports
        if not (1 <= self.api_port <= 65535):
            errors.append(f"Invalid API port: {self.api_port}")
        
        # Validate timeouts and intervals
        if self.max_agent_iterations < 1:
            errors.append(f"max_agent_iterations must be >= 1, got {self.max_agent_iterations}")
        
        if self.scheduler_interval < 30:
            errors.append(f"scheduler_interval must be >= 30, got {self.scheduler_interval}")
        
        if self.memory_cleanup_interval < 300:
            errors.append(f"memory_cleanup_interval must be >= 300, got {self.memory_cleanup_interval}")
        
        if self.model_warmup_timeout < 10:
            errors.append(f"model_warmup_timeout must be >= 10, got {self.model_warmup_timeout}")
        
        if self.max_concurrent_warmups < 1:
            errors.append(f"max_concurrent_warmups must be >= 1, got {self.max_concurrent_warmups}")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
    
    def __str__(self) -> str:
        """String representation of config (safe for logging)"""
        safe_config = self.to_dict().copy()
        # Don't expose sensitive information in string representation
        return f"Config(api_port={self.api_port}, default_model={self.default_model}, warmup_enabled={self.warmup_enabled})"