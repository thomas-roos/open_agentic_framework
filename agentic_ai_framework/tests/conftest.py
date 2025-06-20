"""
Pytest configuration and shared fixtures
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import the main modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def test_config():
    """Test configuration for all tests"""
    return {
        "database_path": ":memory:",
        "api_host": "127.0.0.1",
        "api_port": 8001,
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


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database path"""
    return os.path.join(temp_dir, "test.db")


@pytest.fixture
def temp_tools_dir(temp_dir):
    """Create a temporary tools directory"""
    tools_dir = os.path.join(temp_dir, "test_tools")
    os.makedirs(tools_dir)
    return tools_dir


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "response": "Test response from LLM",
        "model": "test-model",
        "provider": "test-provider",
        "tokens_used": 10,
        "response_time": 0.5
    }


@pytest.fixture
def mock_agent_data():
    """Mock agent data for testing"""
    return {
        "name": "test_agent",
        "role": "Test Role",
        "goals": "Test Goals",
        "backstory": "Test Backstory",
        "tools": ["test_tool"],
        "ollama_model": "test-model",
        "enabled": True
    }


@pytest.fixture
def mock_workflow_data():
    """Mock workflow data for testing"""
    return {
        "name": "test_workflow",
        "description": "Test workflow",
        "steps": [
            {
                "type": "agent",
                "name": "test_agent",
                "task": "Test task"
            }
        ],
        "enabled": True
    }


@pytest.fixture
def mock_conversation_data():
    """Mock conversation data for testing"""
    return {
        "role": "user",
        "content": "Hello, how are you?",
        "timestamp": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_memory_data():
    """Mock memory data for testing"""
    return {
        "role": "Test Role",
        "goals": "Test Goals",
        "backstory": "Test Backstory",
        "tools": ["test_tool"],
        "model": "test-model"
    }


@pytest.fixture
def mock_provider_status():
    """Mock provider status for testing"""
    return {
        "providers": {
            "ollama": {
                "is_healthy": True,
                "models": ["test-model"],
                "url": "http://localhost:11434"
            },
            "openai": {
                "is_healthy": False,
                "models": [],
                "error": "API key not configured"
            }
        }
    }


@pytest.fixture
def mock_memory_stats():
    """Mock memory statistics for testing"""
    return {
        "total_agents": 2,
        "total_conversations": 10,
        "agents": ["agent1", "agent2"],
        "conversations_per_agent": {"agent1": 5, "agent2": 5}
    }


@pytest.fixture
def mock_tools_list():
    """Mock tools list for testing"""
    return [
        {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            }
        }
    ]


@pytest.fixture
def mock_agents_list():
    """Mock agents list for testing"""
    return [
        {
            "name": "agent1",
            "role": "Test Agent 1",
            "goals": "Test goals 1",
            "enabled": True
        },
        {
            "name": "agent2",
            "role": "Test Agent 2",
            "goals": "Test goals 2",
            "enabled": False
        }
    ]


@pytest.fixture
def mock_workflows_list():
    """Mock workflows list for testing"""
    return [
        {
            "name": "workflow1",
            "description": "Test workflow 1",
            "enabled": True
        },
        {
            "name": "workflow2",
            "description": "Test workflow 2",
            "enabled": False
        }
    ]


@pytest.fixture
def mock_warmup_status():
    """Mock warmup status for testing"""
    return {
        "warmup_enabled": True,
        "active_models": ["test-model"],
        "warmup_stats": {
            "total_warmups": 1,
            "successful_warmups": 1,
            "failed_warmups": 0
        }
    }


# Environment variable fixtures
@pytest.fixture
def test_env_vars():
    """Test environment variables"""
    return {
        "API_HOST": "127.0.0.1",
        "API_PORT": "8001",
        "DATABASE_PATH": ":memory:",
        "MAX_AGENT_ITERATIONS": "3",
        "SCHEDULER_INTERVAL": "10",
        "TOOLS_DIRECTORY": "test_tools",
        "MAX_AGENT_MEMORY_ENTRIES": "5",
        "CLEAR_MEMORY_ON_STARTUP": "true",
        "MEMORY_CLEANUP_INTERVAL": "60",
        "MEMORY_RETENTION_DAYS": "1",
        "MODEL_WARMUP_TIMEOUT": "10",
        "MAX_CONCURRENT_WARMUPS": "1",
        "AUTO_WARMUP_ON_STARTUP": "false",
        "WARMUP_INTERVAL_HOURS": "1",
        "MAX_IDLE_HOURS": "1",
        "WARMUP_ENABLED": "false",
        "BACKGROUND_MAINTENANCE": "false",
        "LOG_WARMUP_DETAILS": "false",
        "LOG_LEVEL": "DEBUG",
        "DEFAULT_LLM_PROVIDER": "ollama",
        "DEFAULT_MODEL": "test-model",
        "LLM_FALLBACK_ENABLED": "true",
        "LLM_FALLBACK_ORDER": "ollama,openai",
        "OLLAMA_ENABLED": "true",
        "OLLAMA_URL": "http://localhost:11434",
        "OLLAMA_DEFAULT_MODEL": "test-model"
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_environment():
    """Clean up environment after each test"""
    yield
    # Clean up any test files or state
    pass


# Skip tests that require external services
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "external: marks tests that require external services"
    )


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark tests that use external services
        if "external" in item.nodeid.lower():
            item.add_marker(pytest.mark.external)
        
        # Mark slow tests
        if any(keyword in item.nodeid.lower() for keyword in ["slow", "integration"]):
            item.add_marker(pytest.mark.slow) 