"""
Tests for API endpoints
"""

import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from main import app


class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_managers(self):
        """Mock all managers"""
        with patch('main.llm_manager') as mock_llm, \
             patch('main.memory_manager') as mock_memory, \
             patch('main.tool_manager') as mock_tools, \
             patch('main.agent_manager') as mock_agents, \
             patch('main.workflow_manager') as mock_workflows, \
             patch('main.warmup_manager') as mock_warmup:
            
            # Setup mock returns
            mock_llm.get_provider_status.return_value = {
                "providers": {
                    "ollama": {"is_healthy": True, "models": ["test-model"]},
                    "openai": {"is_healthy": False, "models": []}
                }
            }
            
            mock_memory.get_memory_statistics.return_value = {
                "total_agents": 2,
                "total_conversations": 10,
                "agents": ["agent1", "agent2"],
                "conversations_per_agent": {"agent1": 5, "agent2": 5}
            }
            
            mock_tools.list_tools.return_value = [
                {"name": "test_tool", "description": "A test tool"}
            ]
            
            mock_agents.get_all_agents.return_value = [
                {"name": "agent1", "role": "Test Agent", "enabled": True}
            ]
            
            mock_workflows.get_all_workflows.return_value = [
                {"name": "workflow1", "description": "Test workflow", "enabled": True}
            ]
            
            mock_warmup.get_warmup_status.return_value = {
                "warmup_enabled": True,
                "active_models": ["test-model"],
                "warmup_stats": {"total_warmups": 1, "successful_warmups": 1}
            }
            
            yield {
                'llm': mock_llm,
                'memory': mock_memory,
                'tools': mock_tools,
                'agents': mock_agents,
                'workflows': mock_workflows,
                'warmup': mock_warmup
            }
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Open Agentic Framework"
        assert data["version"] == "1.2.0"
        assert "web_ui" in data
        assert "api_docs" in data
        assert "health" in data
    
    def test_health_endpoint(self, client, mock_managers):
        """Test health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "providers" in data
        assert "memory_stats" in data
        assert "warmup_stats" in data
    
    def test_providers_endpoint(self, client, mock_managers):
        """Test providers endpoint"""
        response = client.get("/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "ollama" in data["providers"]
        assert "openai" in data["providers"]
        assert data["providers"]["ollama"]["is_healthy"] is True
        assert data["providers"]["openai"]["is_healthy"] is False
    
    def test_models_endpoint(self, client, mock_managers):
        """Test models endpoint"""
        # Mock the models response
        mock_managers['llm'].get_available_models.return_value = {
            "models": [
                {"name": "test-model", "provider": "ollama", "supports_streaming": True}
            ]
        }
        
        response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 1
        assert data["models"][0]["name"] == "test-model"
        assert data["models"][0]["provider"] == "ollama"
    
    def test_memory_stats_endpoint(self, client, mock_managers):
        """Test memory statistics endpoint"""
        response = client.get("/memory/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == 2
        assert data["total_conversations"] == 10
        assert "agents" in data
        assert "conversations_per_agent" in data
    
    def test_tools_endpoint(self, client, mock_managers):
        """Test tools endpoint"""
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "test_tool"
    
    def test_agents_endpoint_get(self, client, mock_managers):
        """Test GET agents endpoint"""
        response = client.get("/agents")
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "agent1"
    
    def test_agents_endpoint_post(self, client, mock_managers):
        """Test POST agents endpoint"""
        agent_data = {
            "name": "test_agent",
            "role": "Test Role",
            "goals": "Test Goals",
            "backstory": "Test Backstory",
            "tools": ["test_tool"],
            "ollama_model": "test-model",
            "enabled": True
        }
        
        # Mock successful agent creation
        mock_managers['agents'].create_agent.return_value = {
            "name": "test_agent",
            "role": "Test Role",
            "enabled": True
        }
        
        response = client.post("/agents", json=agent_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_agent"
        assert data["role"] == "Test Role"
        
        # Verify the manager was called with correct data
        mock_managers['agents'].create_agent.assert_called_once()
    
    def test_agents_endpoint_post_validation_error(self, client):
        """Test POST agents endpoint with validation error"""
        invalid_agent_data = {
            "name": "",  # Invalid empty name
            "role": "Test Role"
        }
        
        response = client.post("/agents", json=invalid_agent_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_agent_execute_endpoint(self, client, mock_managers):
        """Test agent execution endpoint"""
        execution_data = {
            "task": "Test task",
            "context": {"key": "value"}
        }
        
        # Mock successful execution
        mock_managers['agents'].execute_agent_task.return_value = {
            "result": "Task completed successfully",
            "agent_name": "test_agent",
            "execution_time": 1.5
        }
        
        response = client.post("/agents/test_agent/execute", json=execution_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Task completed successfully"
        assert data["agent_name"] == "test_agent"
        
        # Verify the manager was called with correct data
        mock_managers['agents'].execute_agent_task.assert_called_once_with(
            "test_agent", execution_data["task"], execution_data["context"]
        )
    
    def test_agent_execute_endpoint_not_found(self, client, mock_managers):
        """Test agent execution endpoint with non-existent agent"""
        execution_data = {
            "task": "Test task",
            "context": {}
        }
        
        # Mock agent not found
        mock_managers['agents'].execute_agent_task.side_effect = ValueError("Agent not found")
        
        response = client.post("/agents/nonexistent_agent/execute", json=execution_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "Agent not found" in data["error"]
    
    def test_workflows_endpoint_get(self, client, mock_managers):
        """Test GET workflows endpoint"""
        response = client.get("/workflows")
        
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert len(data["workflows"]) == 1
        assert data["workflows"][0]["name"] == "workflow1"
    
    def test_workflows_endpoint_post(self, client, mock_managers):
        """Test POST workflows endpoint"""
        workflow_data = {
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
        
        # Mock successful workflow creation
        mock_managers['workflows'].create_workflow.return_value = {
            "name": "test_workflow",
            "description": "Test workflow",
            "enabled": True
        }
        
        response = client.post("/workflows", json=workflow_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_workflow"
        assert data["description"] == "Test workflow"
        
        # Verify the manager was called
        mock_managers['workflows'].create_workflow.assert_called_once()
    
    def test_workflow_execute_endpoint(self, client, mock_managers):
        """Test workflow execution endpoint"""
        execution_data = {
            "context": {"input": "test input"}
        }
        
        # Mock successful workflow execution
        mock_managers['workflows'].execute_workflow.return_value = {
            "result": "Workflow completed",
            "workflow_name": "test_workflow",
            "execution_time": 2.5,
            "steps_executed": 1
        }
        
        response = client.post("/workflows/test_workflow/execute", json=execution_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Workflow completed"
        assert data["workflow_name"] == "test_workflow"
        
        # Verify the manager was called
        mock_managers['workflows'].execute_workflow.assert_called_once_with(
            "test_workflow", execution_data["context"]
        )
    
    def test_config_endpoint(self, client):
        """Test configuration endpoint"""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "api_host" in data
        assert "api_port" in data
        assert "database_path" in data
        assert "llm_config" in data
    
    def test_models_test_endpoint(self, client, mock_managers):
        """Test model testing endpoint"""
        test_data = {
            "prompt": "Hello, how are you?",
            "max_tokens": 100
        }
        
        # Mock successful model test
        mock_managers['llm'].test_model.return_value = {
            "response": "I'm doing well, thank you!",
            "model": "test-model",
            "provider": "ollama",
            "tokens_used": 10,
            "response_time": 0.5
        }
        
        response = client.post("/models/test/test-model", json=test_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "I'm doing well, thank you!"
        assert data["model"] == "test-model"
        assert data["provider"] == "ollama"
        
        # Verify the manager was called
        mock_managers['llm'].test_model.assert_called_once_with("test-model", test_data)
    
    def test_models_test_endpoint_invalid_model(self, client, mock_managers):
        """Test model testing endpoint with invalid model"""
        test_data = {
            "prompt": "Hello",
            "max_tokens": 100
        }
        
        # Mock model not found
        mock_managers['llm'].test_model.side_effect = ValueError("Model not found")
        
        response = client.post("/models/test/invalid-model", json=test_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "Model not found" in data["error"]
    
    def test_memory_cleanup_endpoint(self, client, mock_managers):
        """Test memory cleanup endpoint"""
        response = client.post("/memory/cleanup")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Memory cleanup completed"
        
        # Verify the manager was called
        mock_managers['memory'].cleanup_old_conversations.assert_called_once()
    
    def test_agent_memory_endpoint(self, client, mock_managers):
        """Test agent memory endpoint"""
        # Mock agent memory
        mock_managers['memory'].get_agent_memory.return_value = Mock(
            agent_name="test_agent",
            role="Test Role",
            goals="Test Goals",
            backstory="Test Backstory",
            tools=["test_tool"],
            model="test-model"
        )
        
        mock_managers['memory'].get_conversation_memory.return_value = [
            Mock(role="user", content="Hello", timestamp="2024-01-01T00:00:00"),
            Mock(role="assistant", content="Hi there!", timestamp="2024-01-01T00:00:01")
        ]
        
        response = client.get("/agents/test_agent/memory")
        
        assert response.status_code == 200
        data = response.json()
        assert "agent_memory" in data
        assert "conversation_memory" in data
        assert data["agent_memory"]["agent_name"] == "test_agent"
        assert len(data["conversation_memory"]) == 2
    
    def test_agent_memory_endpoint_not_found(self, client, mock_managers):
        """Test agent memory endpoint with non-existent agent"""
        # Mock agent not found
        mock_managers['memory'].get_agent_memory.return_value = None
        
        response = client.get("/agents/nonexistent_agent/memory")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "Agent not found" in data["error"]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get("/health")
        
        assert response.status_code == 200
        # CORS headers should be present (handled by FastAPI middleware)
        # The exact headers depend on the CORS configuration
    
    def test_error_handling(self, client, mock_managers):
        """Test error handling in endpoints"""
        # Mock an exception in the LLM manager
        mock_managers['llm'].get_provider_status.side_effect = Exception("Internal error")
        
        response = client.get("/providers")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Internal error" in data["error"] 