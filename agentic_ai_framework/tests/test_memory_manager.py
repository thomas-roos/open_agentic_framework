"""
Tests for memory manager module
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from managers.memory_manager import MemoryManager
from models import AgentMemory, ConversationMemory


class TestMemoryManager:
    """Test memory management functionality"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_memory.db")
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)
    
    @pytest.fixture
    def memory_manager(self, temp_db_path):
        """Create a memory manager instance for testing"""
        return MemoryManager(temp_db_path)
    
    def test_initialization(self, memory_manager):
        """Test memory manager initialization"""
        assert memory_manager.database_path is not None
        assert memory_manager.engine is not None
        assert memory_manager.Session is not None
    
    def test_database_initialization(self, memory_manager):
        """Test database table creation"""
        memory_manager.initialize_database()
        
        # Check that tables exist by trying to query them
        with memory_manager.Session() as session:
            # Should not raise an exception
            session.query(AgentMemory).first()
            session.query(ConversationMemory).first()
    
    def test_add_agent_memory(self, memory_manager):
        """Test adding agent memory"""
        memory_manager.initialize_database()
        
        agent_name = "test_agent"
        memory_data = {
            "role": "Test Role",
            "goals": "Test Goals",
            "backstory": "Test Backstory",
            "tools": ["tool1", "tool2"],
            "model": "test-model"
        }
        
        memory_manager.add_agent_memory(agent_name, memory_data)
        
        # Verify memory was added
        retrieved_memory = memory_manager.get_agent_memory(agent_name)
        assert retrieved_memory is not None
        assert retrieved_memory.agent_name == agent_name
        assert retrieved_memory.role == "Test Role"
        assert retrieved_memory.goals == "Test Goals"
        assert retrieved_memory.backstory == "Test Backstory"
        assert retrieved_memory.tools == ["tool1", "tool2"]
        assert retrieved_memory.model == "test-model"
    
    def test_add_conversation_memory(self, memory_manager):
        """Test adding conversation memory"""
        memory_manager.initialize_database()
        
        agent_name = "test_agent"
        conversation_data = {
            "role": "user",
            "content": "Hello, how are you?",
            "timestamp": datetime.now()
        }
        
        memory_manager.add_conversation_memory(agent_name, conversation_data)
        
        # Verify conversation was added
        conversations = memory_manager.get_conversation_memory(agent_name)
        assert len(conversations) == 1
        assert conversations[0].agent_name == agent_name
        assert conversations[0].role == "user"
        assert conversations[0].content == "Hello, how are you?"
    
    def test_get_agent_memory_nonexistent(self, memory_manager):
        """Test getting memory for non-existent agent"""
        memory_manager.initialize_database()
        
        memory = memory_manager.get_agent_memory("nonexistent_agent")
        assert memory is None
    
    def test_get_conversation_memory_empty(self, memory_manager):
        """Test getting conversation memory for agent with no conversations"""
        memory_manager.initialize_database()
        
        conversations = memory_manager.get_conversation_memory("new_agent")
        assert conversations == []
    
    def test_update_agent_memory(self, memory_manager):
        """Test updating existing agent memory"""
        memory_manager.initialize_database()
        
        agent_name = "test_agent"
        initial_data = {
            "role": "Initial Role",
            "goals": "Initial Goals",
            "backstory": "Initial Backstory",
            "tools": ["tool1"],
            "model": "initial-model"
        }
        
        # Add initial memory
        memory_manager.add_agent_memory(agent_name, initial_data)
        
        # Update memory
        updated_data = {
            "role": "Updated Role",
            "goals": "Updated Goals",
            "backstory": "Updated Backstory",
            "tools": ["tool1", "tool2", "tool3"],
            "model": "updated-model"
        }
        
        memory_manager.add_agent_memory(agent_name, updated_data)
        
        # Verify memory was updated
        retrieved_memory = memory_manager.get_agent_memory(agent_name)
        assert retrieved_memory.role == "Updated Role"
        assert retrieved_memory.goals == "Updated Goals"
        assert retrieved_memory.backstory == "Updated Backstory"
        assert retrieved_memory.tools == ["tool1", "tool2", "tool3"]
        assert retrieved_memory.model == "updated-model"
    
    def test_clear_agent_memory(self, memory_manager):
        """Test clearing agent memory"""
        memory_manager.initialize_database()
        
        agent_name = "test_agent"
        memory_data = {
            "role": "Test Role",
            "goals": "Test Goals",
            "backstory": "Test Backstory",
            "tools": ["tool1"],
            "model": "test-model"
        }
        
        # Add memory
        memory_manager.add_agent_memory(agent_name, memory_data)
        
        # Add conversation
        conversation_data = {
            "role": "user",
            "content": "Test message",
            "timestamp": datetime.now()
        }
        memory_manager.add_conversation_memory(agent_name, conversation_data)
        
        # Clear memory
        memory_manager.clear_agent_memory(agent_name)
        
        # Verify memory is cleared
        agent_memory = memory_manager.get_agent_memory(agent_name)
        conversations = memory_manager.get_conversation_memory(agent_name)
        
        assert agent_memory is None
        assert conversations == []
    
    def test_clear_all_agent_memory(self, memory_manager):
        """Test clearing all agent memory"""
        memory_manager.initialize_database()
        
        # Add multiple agents
        agents = ["agent1", "agent2", "agent3"]
        for agent in agents:
            memory_data = {
                "role": f"Role for {agent}",
                "goals": f"Goals for {agent}",
                "backstory": f"Backstory for {agent}",
                "tools": ["tool1"],
                "model": "test-model"
            }
            memory_manager.add_agent_memory(agent, memory_data)
            
            conversation_data = {
                "role": "user",
                "content": f"Message for {agent}",
                "timestamp": datetime.now()
            }
            memory_manager.add_conversation_memory(agent, conversation_data)
        
        # Clear all memory
        memory_manager.clear_all_agent_memory()
        
        # Verify all memory is cleared
        for agent in agents:
            agent_memory = memory_manager.get_agent_memory(agent)
            conversations = memory_manager.get_conversation_memory(agent)
            
            assert agent_memory is None
            assert conversations == []
    
    def test_get_all_agents(self, memory_manager):
        """Test getting all agent names"""
        memory_manager.initialize_database()
        
        # Add multiple agents
        agents = ["agent1", "agent2", "agent3"]
        for agent in agents:
            memory_data = {
                "role": f"Role for {agent}",
                "goals": f"Goals for {agent}",
                "backstory": f"Backstory for {agent}",
                "tools": ["tool1"],
                "model": "test-model"
            }
            memory_manager.add_agent_memory(agent, memory_data)
        
        # Get all agents
        all_agents = memory_manager.get_all_agents()
        
        # Verify all agents are returned
        assert len(all_agents) == 3
        for agent in agents:
            assert agent in all_agents
    
    def test_memory_cleanup_old_conversations(self, memory_manager):
        """Test cleanup of old conversations"""
        memory_manager.initialize_database()
        
        agent_name = "test_agent"
        
        # Add old conversation (more than 7 days old)
        old_conversation = {
            "role": "user",
            "content": "Old message",
            "timestamp": datetime.now() - timedelta(days=10)
        }
        memory_manager.add_conversation_memory(agent_name, old_conversation)
        
        # Add recent conversation
        recent_conversation = {
            "role": "user",
            "content": "Recent message",
            "timestamp": datetime.now()
        }
        memory_manager.add_conversation_memory(agent_name, recent_conversation)
        
        # Run cleanup
        memory_manager.cleanup_old_conversations()
        
        # Verify only recent conversation remains
        conversations = memory_manager.get_conversation_memory(agent_name)
        assert len(conversations) == 1
        assert conversations[0].content == "Recent message"
    
    def test_memory_statistics(self, memory_manager):
        """Test memory statistics"""
        memory_manager.initialize_database()
        
        # Add multiple agents with conversations
        agents = ["agent1", "agent2"]
        for i, agent in enumerate(agents):
            memory_data = {
                "role": f"Role for {agent}",
                "goals": f"Goals for {agent}",
                "backstory": f"Backstory for {agent}",
                "tools": ["tool1"],
                "model": "test-model"
            }
            memory_manager.add_agent_memory(agent, memory_data)
            
            # Add multiple conversations per agent
            for j in range(i + 1):
                conversation_data = {
                    "role": "user",
                    "content": f"Message {j} for {agent}",
                    "timestamp": datetime.now()
                }
                memory_manager.add_conversation_memory(agent, conversation_data)
        
        # Get statistics
        stats = memory_manager.get_memory_statistics()
        
        # Verify statistics
        assert stats["total_agents"] == 2
        assert stats["total_conversations"] == 3  # 1 + 2
        assert stats["agents"] == ["agent1", "agent2"]
        assert stats["conversations_per_agent"]["agent1"] == 1
        assert stats["conversations_per_agent"]["agent2"] == 2
    
    def test_conversation_limit_enforcement(self, memory_manager):
        """Test that conversation limit is enforced"""
        memory_manager.initialize_database()
        
        agent_name = "test_agent"
        max_entries = 3
        
        # Add more conversations than the limit
        for i in range(5):
            conversation_data = {
                "role": "user",
                "content": f"Message {i}",
                "timestamp": datetime.now()
            }
            memory_manager.add_conversation_memory(agent_name, conversation_data, max_entries=max_entries)
        
        # Verify only the most recent conversations are kept
        conversations = memory_manager.get_conversation_memory(agent_name)
        assert len(conversations) == max_entries
        
        # Verify the most recent messages are kept (last 3)
        expected_messages = ["Message 2", "Message 3", "Message 4"]
        actual_messages = [conv.content for conv in conversations]
        assert actual_messages == expected_messages
    
    def test_memory_persistence(self, temp_db_path):
        """Test that memory persists across manager instances"""
        # Create first manager and add data
        manager1 = MemoryManager(temp_db_path)
        manager1.initialize_database()
        
        agent_name = "persistent_agent"
        memory_data = {
            "role": "Persistent Role",
            "goals": "Persistent Goals",
            "backstory": "Persistent Backstory",
            "tools": ["tool1"],
            "model": "persistent-model"
        }
        manager1.add_agent_memory(agent_name, memory_data)
        
        # Create second manager and verify data persists
        manager2 = MemoryManager(temp_db_path)
        manager2.initialize_database()
        
        retrieved_memory = manager2.get_agent_memory(agent_name)
        assert retrieved_memory is not None
        assert retrieved_memory.role == "Persistent Role"
        assert retrieved_memory.goals == "Persistent Goals" 