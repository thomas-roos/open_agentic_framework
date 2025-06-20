"""
Test package for Open Agentic Framework
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import the main modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG = {
    "database_path": ":memory:",  # Use in-memory database for tests
    "api_host": "127.0.0.1",
    "api_port": 8001,  # Different port to avoid conflicts
    "max_agent_iterations": 3,
    "scheduler_interval": 10,
    "tools_directory": "test_tools",
    "max_agent_memory_entries": 5,
    "clear_memory_on_startup": True,
    "memory_cleanup_interval": 60,
    "memory_retention_days": 1,
    "model_warmup_timeout": 10,
    "max_concurrent_warmups": 1,
    "auto_warmup_on_startup": False,
    "warmup_interval_hours": 1,
    "max_idle_hours": 1,
    "warmup_enabled": False,
    "background_maintenance": False,
    "log_warmup_details": False,
    "log_level": "DEBUG"
}

# Test utilities
class TestUtils:
    """Utility functions for testing"""
    
    @staticmethod
    def create_temp_directory():
        """Create a temporary directory for test files"""
        return tempfile.mkdtemp()
    
    @staticmethod
    def cleanup_temp_directory(temp_dir):
        """Clean up temporary directory"""
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @staticmethod
    def create_test_env_file(temp_dir):
        """Create a test environment file"""
        env_path = os.path.join(temp_dir, ".env")
        with open(env_path, "w") as f:
            for key, value in TEST_CONFIG.items():
                if isinstance(value, bool):
                    f.write(f"{key.upper()}={str(value).lower()}\n")
                elif isinstance(value, str):
                    f.write(f"{key.upper()}={value}\n")
                else:
                    f.write(f"{key.upper()}={value}\n")
        return env_path
    
    @staticmethod
    def mock_llm_response(response_text="Test response"):
        """Create a mock LLM response"""
        return {
            "response": response_text,
            "model": "test-model",
            "provider": "test-provider",
            "tokens_used": 10,
            "response_time": 0.5
        }
