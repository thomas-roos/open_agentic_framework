"""
Tests for tool manager module
"""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from managers.tool_manager import ToolManager
from tools.base_tool import BaseTool


class MockTool(BaseTool):
    """Mock tool for testing"""
    
    def __init__(self):
        super().__init__()
        self.name = "mock_tool"
        self.description = "A mock tool for testing"
        self.parameters = {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter"
                }
            },
            "required": ["input"]
        }
    
    def execute(self, parameters):
        return {"result": f"Mock tool executed with: {parameters.get('input', '')}"}


class TestToolManager:
    """Test tool management functionality"""
    
    @pytest.fixture
    def temp_tools_dir(self):
        """Create a temporary tools directory for testing"""
        temp_dir = tempfile.mkdtemp()
        tools_dir = os.path.join(temp_dir, "test_tools")
        os.makedirs(tools_dir)
        yield tools_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def tool_manager(self, temp_tools_dir):
        """Create a tool manager instance for testing"""
        return ToolManager(temp_tools_dir)
    
    def test_initialization(self, tool_manager):
        """Test tool manager initialization"""
        assert tool_manager.tools_directory is not None
        assert tool_manager.loaded_tools == {}
    
    def test_is_tool_class(self, tool_manager):
        """Test tool class detection"""
        # Should identify BaseTool subclasses as tools
        assert tool_manager._is_tool_class(MockTool) is True
        
        # Should not identify regular classes as tools
        class RegularClass:
            pass
        assert tool_manager._is_tool_class(RegularClass) is False
        
        # Should not identify BaseTool itself as a tool
        assert tool_manager._is_tool_class(BaseTool) is False
    
    def test_register_tool_instance(self, tool_manager):
        """Test tool instance registration"""
        mock_tool = MockTool()
        
        tool_manager._register_tool_instance(mock_tool, "test_tool")
        
        assert "test_tool" in tool_manager.loaded_tools
        assert tool_manager.loaded_tools["test_tool"] == mock_tool
    
    def test_discover_and_register_tools_empty_directory(self, tool_manager):
        """Test tool discovery in empty directory"""
        tool_manager.discover_and_register_tools()
        
        # Should not raise any exceptions
        assert tool_manager.loaded_tools == {}
    
    def test_discover_and_register_tools_with_valid_tool(self, temp_tools_dir):
        """Test discovering and registering a valid tool"""
        # Create a mock tool file
        tool_file = os.path.join(temp_tools_dir, "mock_tool.py")
        with open(tool_file, "w") as f:
            f.write("""
from tools.base_tool import BaseTool

class MockTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "mock_tool"
        self.description = "A mock tool for testing"
        self.parameters = {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter"
                }
            },
            "required": ["input"]
        }
    
    def execute(self, parameters):
        return {"result": f"Mock tool executed with: {parameters.get('input', '')}"}
""")
        
        tool_manager = ToolManager(temp_tools_dir)
        tool_manager.discover_and_register_tools()
        
        assert "MockTool" in tool_manager.loaded_tools
        tool = tool_manager.loaded_tools["MockTool"]
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
    
    def test_discover_and_register_tools_with_invalid_tool(self, temp_tools_dir):
        """Test discovering tools with invalid tool file"""
        # Create an invalid tool file (not inheriting from BaseTool)
        tool_file = os.path.join(temp_tools_dir, "invalid_tool.py")
        with open(tool_file, "w") as f:
            f.write("""
class InvalidTool:
    def __init__(self):
        self.name = "invalid_tool"
""")
        
        tool_manager = ToolManager(temp_tools_dir)
        tool_manager.discover_and_register_tools()
        
        # Should not register invalid tools
        assert tool_manager.loaded_tools == {}
    
    def test_discover_and_register_tools_with_syntax_error(self, temp_tools_dir):
        """Test discovering tools with syntax error"""
        # Create a tool file with syntax error
        tool_file = os.path.join(temp_tools_dir, "syntax_error_tool.py")
        with open(tool_file, "w") as f:
            f.write("""
from tools.base_tool import BaseTool

class SyntaxErrorTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "syntax_error_tool"
        # Missing closing parenthesis
        self.description = "A tool with syntax error"
""")
        
        tool_manager = ToolManager(temp_tools_dir)
        tool_manager.discover_and_register_tools()
        
        # Should not register tools with syntax errors
        assert tool_manager.loaded_tools == {}
    
    def test_get_tool(self, tool_manager):
        """Test getting a specific tool"""
        mock_tool = MockTool()
        tool_manager.loaded_tools["test_tool"] = mock_tool
        
        retrieved_tool = tool_manager.get_tool("test_tool")
        assert retrieved_tool == mock_tool
        
        # Test getting non-existent tool
        non_existent_tool = tool_manager.get_tool("non_existent")
        assert non_existent_tool is None
    
    def test_get_all_tools(self, tool_manager):
        """Test getting all tools"""
        mock_tool1 = MockTool()
        mock_tool1.name = "tool1"
        mock_tool2 = MockTool()
        mock_tool2.name = "tool2"
        
        tool_manager.loaded_tools["tool1"] = mock_tool1
        tool_manager.loaded_tools["tool2"] = mock_tool2
        
        all_tools = tool_manager.get_all_tools()
        
        assert len(all_tools) == 2
        assert "tool1" in all_tools
        assert "tool2" in all_tools
        assert all_tools["tool1"] == mock_tool1
        assert all_tools["tool2"] == mock_tool2
    
    def test_execute_tool(self, tool_manager):
        """Test executing a tool"""
        mock_tool = MockTool()
        tool_manager.loaded_tools["test_tool"] = mock_tool
        
        parameters = {"input": "test input"}
        result = tool_manager.execute_tool("test_tool", parameters)
        
        assert result["result"] == "Mock tool executed with: test input"
    
    def test_execute_tool_not_found(self, tool_manager):
        """Test executing a non-existent tool"""
        with pytest.raises(ValueError, match="Tool 'non_existent' not found"):
            tool_manager.execute_tool("non_existent", {})
    
    def test_execute_tool_execution_error(self, tool_manager):
        """Test tool execution error handling"""
        # Create a mock tool that raises an exception
        class ErrorTool(BaseTool):
            def __init__(self):
                super().__init__()
                self.name = "error_tool"
                self.description = "A tool that raises an error"
                self.parameters = {"type": "object", "properties": {}}
            
            def execute(self, parameters):
                raise Exception("Tool execution error")
        
        error_tool = ErrorTool()
        tool_manager.loaded_tools["error_tool"] = error_tool
        
        with pytest.raises(Exception, match="Tool execution error"):
            tool_manager.execute_tool("error_tool", {})
    
    def test_tool_reloading(self, temp_tools_dir):
        """Test tool reloading functionality"""
        # Create initial tool file
        tool_file = os.path.join(temp_tools_dir, "reloadable_tool.py")
        with open(tool_file, "w") as f:
            f.write("""
from tools.base_tool import BaseTool

class ReloadableTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "reloadable_tool"
        self.description = "Initial description"
        self.parameters = {"type": "object", "properties": {}}
    
    def execute(self, parameters):
        return {"result": "initial result"}
""")
        
        tool_manager = ToolManager(temp_tools_dir)
        tool_manager.discover_and_register_tools()
        
        assert "ReloadableTool" in tool_manager.loaded_tools
        initial_tool = tool_manager.loaded_tools["ReloadableTool"]
        assert initial_tool.description == "Initial description"
        
        # Update the tool file
        with open(tool_file, "w") as f:
            f.write("""
from tools.base_tool import BaseTool

class ReloadableTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "reloadable_tool"
        self.description = "Updated description"
        self.parameters = {"type": "object", "properties": {}}
    
    def execute(self, parameters):
        return {"result": "updated result"}
""")
        
        # Reload tools
        tool_manager.discover_and_register_tools()
        
        assert "ReloadableTool" in tool_manager.loaded_tools
        updated_tool = tool_manager.loaded_tools["ReloadableTool"]
        assert updated_tool.description == "Updated description"
        
        # Test execution with updated tool
        result = tool_manager.execute_tool("ReloadableTool", {})
        assert result["result"] == "updated result"
    
    def test_tool_parameter_validation(self, tool_manager):
        """Test tool parameter validation"""
        # Create a tool with required parameters
        class ParameterizedTool(BaseTool):
            def __init__(self):
                super().__init__()
                self.name = "parameterized_tool"
                self.description = "A tool with required parameters"
                self.parameters = {
                    "type": "object",
                    "properties": {
                        "required_param": {
                            "type": "string",
                            "description": "A required parameter"
                        },
                        "optional_param": {
                            "type": "string",
                            "description": "An optional parameter"
                        }
                    },
                    "required": ["required_param"]
                }
            
            def execute(self, parameters):
                return {"result": f"Executed with: {parameters}"}
        
        parameterized_tool = ParameterizedTool()
        tool_manager.loaded_tools["parameterized_tool"] = parameterized_tool
        
        # Test with valid parameters
        valid_params = {"required_param": "test_value", "optional_param": "optional_value"}
        result = tool_manager.execute_tool("parameterized_tool", valid_params)
        assert "Executed with:" in result["result"]
        
        # Test with missing required parameter
        invalid_params = {"optional_param": "optional_value"}
        with pytest.raises(ValueError):
            tool_manager.execute_tool("parameterized_tool", invalid_params)
    
    def test_tool_listing(self, tool_manager):
        """Test tool listing functionality"""
        mock_tool1 = MockTool()
        mock_tool1.name = "tool1"
        mock_tool1.description = "First tool"
        
        mock_tool2 = MockTool()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Second tool"
        
        tool_manager.loaded_tools["tool1"] = mock_tool1
        tool_manager.loaded_tools["tool2"] = mock_tool2
        
        tool_list = tool_manager.list_tools()
        
        assert len(tool_list) == 2
        tool_names = [tool["name"] for tool in tool_list]
        assert "tool1" in tool_names
        assert "tool2" in tool_names
        
        # Check tool details
        tool1_info = next(tool for tool in tool_list if tool["name"] == "tool1")
        assert tool1_info["description"] == "First tool"
        assert "parameters" in tool1_info 