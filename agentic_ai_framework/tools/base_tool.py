"""
tools/base_tool.py - Abstract Base Tool Class

Defines the interface that all tools must implement.
All custom tools should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """Abstract base class for all tools in the framework"""
    
    def __init__(self):
        """Initialize the tool with empty configuration"""
        self.config = {}
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique name for the tool
        
        Returns:
            Tool name as string
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what the tool does
        
        Returns:
            Tool description as string
        """
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        JSON schema defining the tool's parameters
        
        Returns:
            JSON schema dictionary defining expected parameters
        """
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """
        Execute the tool with given parameters
        
        Args:
            parameters: Dictionary of parameters matching the tool's schema
            
        Returns:
            Tool execution result (can be any type)
            
        Raises:
            Exception: If tool execution fails
        """
        pass
    
    def set_config(self, config: Dict[str, Any]):
        """
        Set tool-specific configuration
        
        This method allows agents to provide tool-specific configuration
        such as API keys, server URLs, credentials, etc.
        
        Args:
            config: Dictionary containing tool configuration
        """
        self.config = config
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def validate_config(self, required_keys: list) -> bool:
        """
        Validate that required configuration keys are present
        
        Args:
            required_keys: List of required configuration keys
            
        Returns:
            True if all required keys are present, False otherwise
        """
        for key in required_keys:
            if key not in self.config:
                return False
        return True
    
    def __str__(self) -> str:
        """String representation of the tool"""
        return f"{self.name}: {self.description}"
    
    def __repr__(self) -> str:
        """Developer representation of the tool"""
        return f"<{self.__class__.__name__}(name='{self.name}')>"