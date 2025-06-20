"""
Tests for configuration module
"""

import os
import pytest
from unittest.mock import patch
from config import Config


class TestConfig:
    """Test configuration loading and validation"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.api_host == "0.0.0.0"
            assert config.api_port == 8000
            assert config.database_path == "data/agentic_ai.db"
            assert config.max_agent_iterations == 10
            assert config.scheduler_interval == 60
            assert config.tools_directory == "tools"
            assert config.max_agent_memory_entries == 20
            assert config.clear_memory_on_startup is False
            assert config.memory_cleanup_interval == 3600
            assert config.memory_retention_days == 7
    
    def test_environment_override(self):
        """Test environment variable overrides"""
        test_env = {
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "DATABASE_PATH": "test.db",
            "MAX_AGENT_ITERATIONS": "5",
            "SCHEDULER_INTERVAL": "30",
            "TOOLS_DIRECTORY": "test_tools",
            "MAX_AGENT_MEMORY_ENTRIES": "10",
            "CLEAR_MEMORY_ON_STARTUP": "true",
            "MEMORY_CLEANUP_INTERVAL": "1800",
            "MEMORY_RETENTION_DAYS": "3"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            
            assert config.api_host == "127.0.0.1"
            assert config.api_port == 9000
            assert config.database_path == "test.db"
            assert config.max_agent_iterations == 5
            assert config.scheduler_interval == 30
            assert config.tools_directory == "test_tools"
            assert config.max_agent_memory_entries == 10
            assert config.clear_memory_on_startup is True
            assert config.memory_cleanup_interval == 1800
            assert config.memory_retention_days == 3
    
    def test_llm_config_default(self):
        """Test default LLM configuration"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            llm_config = config.llm_config
            
            assert llm_config["default_provider"] == "ollama"
            assert llm_config["default_model"] == "granite3.2:2b"
            assert llm_config["fallback_enabled"] is True
            assert "ollama" in llm_config["providers"]
            assert llm_config["providers"]["ollama"]["enabled"] is True
            assert llm_config["providers"]["ollama"]["url"] == "http://localhost:11434"
    
    def test_llm_config_openai_enabled(self):
        """Test OpenAI provider configuration"""
        test_env = {
            "OPENAI_ENABLED": "true",
            "OPENAI_API_KEY": "test-key",
            "OPENAI_DEFAULT_MODEL": "gpt-4",
            "OPENAI_ORGANIZATION": "test-org"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            llm_config = config.llm_config
            
            assert "openai" in llm_config["providers"]
            assert llm_config["providers"]["openai"]["enabled"] is True
            assert llm_config["providers"]["openai"]["api_key"] == "test-key"
            assert llm_config["providers"]["openai"]["default_model"] == "gpt-4"
            assert llm_config["providers"]["openai"]["organization"] == "test-org"
    
    def test_llm_config_bedrock_enabled(self):
        """Test AWS Bedrock provider configuration"""
        test_env = {
            "BEDROCK_ENABLED": "true",
            "AWS_ACCESS_KEY_ID": "test-access-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret-key",
            "BEDROCK_REGION": "us-west-2",
            "BEDROCK_DEFAULT_MODEL": "anthropic.claude-3-haiku-20240307-v1:0"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            llm_config = config.llm_config
            
            assert "bedrock" in llm_config["providers"]
            assert llm_config["providers"]["bedrock"]["enabled"] is True
            assert llm_config["providers"]["bedrock"]["aws_access_key_id"] == "test-access-key"
            assert llm_config["providers"]["bedrock"]["aws_secret_access_key"] == "test-secret-key"
            assert llm_config["providers"]["bedrock"]["region_name"] == "us-west-2"
            assert llm_config["providers"]["bedrock"]["default_model"] == "anthropic.claude-3-haiku-20240307-v1:0"
    
    def test_fallback_order(self):
        """Test LLM fallback order configuration"""
        test_env = {
            "LLM_FALLBACK_ORDER": "openai,bedrock,ollama"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            llm_config = config.llm_config
            
            assert llm_config["fallback_order"] == ["openai", "bedrock", "ollama"]
    
    def test_fallback_order_with_ollama_auto_add(self):
        """Test that Ollama is automatically added to fallback order if enabled"""
        test_env = {
            "LLM_FALLBACK_ORDER": "openai,bedrock"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            llm_config = config.llm_config
            
            # Ollama should be automatically added to the beginning
            assert llm_config["fallback_order"] == ["ollama", "openai", "bedrock"]
    
    def test_model_warmup_config(self):
        """Test model warmup configuration"""
        test_env = {
            "MODEL_WARMUP_TIMEOUT": "120",
            "MAX_CONCURRENT_WARMUPS": "3",
            "AUTO_WARMUP_ON_STARTUP": "false",
            "WARMUP_INTERVAL_HOURS": "12",
            "MAX_IDLE_HOURS": "48",
            "WARMUP_ENABLED": "false",
            "BACKGROUND_MAINTENANCE": "false",
            "LOG_WARMUP_DETAILS": "false"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = Config()
            
            assert config.model_warmup_timeout == 120
            assert config.max_concurrent_warmups == 3
            assert config.auto_warmup_on_startup is False
            assert config.warmup_interval_hours == 12
            assert config.max_idle_hours == 48
            assert config.warmup_enabled is False
            assert config.background_maintenance is False
            assert config.log_warmup_details is False
    
    def test_to_dict_method(self):
        """Test configuration to_dict method"""
        config = Config()
        config_dict = config.to_dict()
        
        # Check that all expected keys are present
        expected_keys = [
            "api_host", "api_port", "database_path", "max_agent_iterations",
            "scheduler_interval", "tools_directory", "max_agent_memory_entries",
            "clear_memory_on_startup", "memory_cleanup_interval", "memory_retention_days",
            "model_warmup_timeout", "max_concurrent_warmups", "auto_warmup_on_startup",
            "warmup_interval_hours", "max_idle_hours", "warmup_enabled",
            "background_maintenance", "log_warmup_details", "llm_config",
            "ollama_url", "default_model", "log_level", "log_format"
        ]
        
        for key in expected_keys:
            assert key in config_dict
        
        # Check that llm_config is properly structured
        assert "default_provider" in config_dict["llm_config"]
        assert "providers" in config_dict["llm_config"]
        assert "fallback_order" in config_dict["llm_config"]
    
    def test_backward_compatibility(self):
        """Test backward compatibility properties"""
        config = Config()
        
        # These should match the LLM config values
        assert config.ollama_url == config.llm_config["providers"]["ollama"]["url"]
        assert config.default_model == config.llm_config["default_model"] 