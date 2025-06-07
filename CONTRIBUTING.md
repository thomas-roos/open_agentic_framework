# 🤝 Contributing to Agentic AI Framework

Thank you for your interest in contributing to the Agentic AI Framework! We welcome contributions from developers of all skill levels. This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Contributing Process](#contributing-process)
- [Contribution Types](#contribution-types)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## 📜 Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

### Our Standards

- **Be respectful** and considerate in your communication
- **Be collaborative** and help others learn and grow
- **Be inclusive** and welcome newcomers to the community
- **Focus on what's best** for the community and project
- **Show empathy** towards other community members

## 🚀 Getting Started

### Ways to Contribute

- 🐛 **Report bugs** and issues
- 💡 **Suggest new features** or improvements
- 📝 **Improve documentation**
- 🔧 **Submit code changes** and bug fixes
- 🎯 **Create new tools** and integrations
- 🧪 **Write tests** and improve coverage
- 🌟 **Share your use cases** and success stories

### Before You Start

1. **Check existing issues** to avoid duplicating work
2. **Read the documentation** to understand the project structure
3. **Join our community** discussions for questions and ideas
4. **Start small** with your first contribution

## 🛠 Development Environment

### Prerequisites

- **Python 3.8+**
- **Docker and Docker Compose**
- **Git**
- **Text editor or IDE** (VS Code, PyCharm, etc.)
- **4GB+ RAM** for running models locally

### Local Setup

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork locally
git clone https://github.com/YOUR_USERNAME/agentic-ai-framework.git
cd agentic-ai-framework

# 3. Add upstream remote
git remote add upstream https://github.com/original-owner/agentic-ai-framework.git

# 4. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install development dependencies
pip install -r requirements-dev.txt

# 6. Install pre-commit hooks
pre-commit install

# 7. Start the development environment
docker-compose up -d

# 8. Run tests to verify setup
pytest tests/ -v
```

### Development Tools

We use several tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **pytest** - Testing
- **pre-commit** - Git hooks

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .

# Run tests
pytest tests/ -v --cov=.
```

## 🔄 Contributing Process

### 1. Create an Issue (Recommended)

Before starting work, create an issue to discuss your proposed changes:

- **Bug reports**: Use the bug report template
- **Feature requests**: Use the feature request template
- **Questions**: Start a discussion in GitHub Discussions

### 2. Fork and Branch

```bash
# Create a new branch for your work
git checkout -b feature/amazing-new-feature

# Or for bug fixes
git checkout -b fix/bug-description

# Or for documentation
git checkout -b docs/update-contributing-guide
```

### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `test/description` - Test improvements
- `refactor/description` - Code refactoring
- `chore/description` - Maintenance tasks

### 3. Make Your Changes

Follow our [Development Guidelines](#development-guidelines) while making changes.

### 4. Test Your Changes

```bash
# Run the full test suite
pytest tests/ -v

# Run specific test files
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Test your changes manually
docker-compose up -d
curl http://localhost:8000/health
```

### 5. Commit Your Changes

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```bash
# Examples of good commit messages
git commit -m "feat: add email notification tool"
git commit -m "fix: resolve memory leak in agent execution"
git commit -m "docs: update quick start guide with new examples"
git commit -m "test: add unit tests for workflow manager"
git commit -m "refactor: simplify tool registration process"
```

#### Commit Types

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `style:` - Code style changes (formatting, etc.)
- `chore:` - Maintenance tasks
- `ci:` - CI/CD changes

### 6. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/amazing-new-feature

# Create a pull request on GitHub
# Use the pull request template and provide:
# - Clear description of changes
# - Link to related issues
# - Screenshots if applicable
# - Testing instructions
```

### 7. Code Review Process

- **Automated checks** run on every PR (tests, linting, type checking)
- **Maintainer review** for code quality and design
- **Community feedback** welcome on all PRs
- **Iterative improvement** based on feedback
- **Final approval** from project maintainers

## 🎯 Contribution Types

### 🐛 Bug Reports

When reporting bugs, please include:

```markdown
**Bug Description**
A clear description of what the bug is.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.9.5]
- Docker version: [e.g. 20.10.8]
- Framework version: [e.g. 1.1.0]

**Additional Context**
Logs, screenshots, or other helpful information.
```

### 💡 Feature Requests

For new features, please provide:

- **Use case** - Why is this feature needed?
- **Proposed solution** - How should it work?
- **Alternatives considered** - What other approaches did you consider?
- **Implementation ideas** - Any thoughts on how to implement it?

### 🔧 Code Contributions

#### New Tools

Creating a new tool is a great way to contribute! Tools extend agent capabilities:

```python
# Example: tools/my_awesome_tool.py
from tools.base_tool import BaseTool
from typing import Dict, Any

class MyAwesomeTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_awesome_tool"
    
    @property
    def description(self) -> str:
        return "Does something awesome for agents"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_text": {
                    "type": "string",
                    "description": "Text to process"
                },
                "option": {
                    "type": "string",
                    "enum": ["fast", "thorough"],
                    "default": "fast"
                }
            },
            "required": ["input_text"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters"""
        input_text = parameters["input_text"]
        option = parameters.get("option", "fast")
        
        # Your tool logic here
        result = f"Processed '{input_text}' with {option} mode"
        
        return {
            "result": result,
            "processed_length": len(input_text),
            "mode": option
        }
```

**Tool Contribution Checklist:**
- [ ] Inherits from `BaseTool`
- [ ] Has clear `name`, `description`, and `parameters`
- [ ] Includes proper error handling
- [ ] Has comprehensive tests
- [ ] Includes documentation and examples
- [ ] Follows security best practices

#### Core Framework Improvements

For core framework changes:

- **Discuss first** in an issue or discussion
- **Maintain backward compatibility** when possible
- **Update documentation** for any API changes
- **Add comprehensive tests**
- **Consider performance impact**

## 📏 Development Guidelines

### Code Style

We follow PEP 8 with these specific guidelines:

```python
# Good: Clear, descriptive names
async def execute_agent_with_memory_cleanup(
    agent_name: str, 
    task: str, 
    context: Dict[str, Any] = None
) -> str:
    """Execute agent and cleanup memory afterward."""
    pass

# Good: Type hints for all functions
def create_workflow_step(
    step_type: str,
    name: str,
    parameters: Optional[Dict[str, Any]] = None
) -> WorkflowStep:
    """Create a workflow step with validation."""
    pass

# Good: Descriptive docstrings
class AgentManager:
    """
    Manages agent execution and lifecycle.
    
    This class handles agent creation, execution, memory management,
    and tool integration. It provides both synchronous and asynchronous
    execution methods with built-in error handling and cleanup.
    """
    pass
```

### Error Handling

```python
# Good: Specific exceptions with context
try:
    result = await self.execute_tool(tool_name, parameters)
except ToolNotFoundError as e:
    logger.error(f"Tool {tool_name} not found: {e}")
    raise ValueError(f"Tool '{tool_name}' is not available")
except ToolExecutionError as e:
    logger.error(f"Tool execution failed: {e}")
    raise RuntimeError(f"Failed to execute {tool_name}: {e}")

# Good: Graceful degradation
async def get_model_status(self) -> Dict[str, Any]:
    """Get Ollama model status with fallback."""
    try:
        models = await self.ollama_client.list_models()
        return {"status": "healthy", "models": models}
    except Exception as e:
        logger.warning(f"Failed to get model status: {e}")
        return {"status": "unknown", "error": str(e)}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Good: Appropriate log levels
logger.debug("Detailed debug information")
logger.info("General information about execution")
logger.warning("Something unexpected but not critical")
logger.error("Error that prevented operation completion")
logger.critical("Serious error that may cause system failure")

# Good: Structured logging with context
logger.info(
    "Agent execution completed",
    extra={
        "agent_name": agent_name,
        "task": task,
        "execution_time": execution_time,
        "tools_used": tools_used
    }
)
```

### Database Operations

```python
# Good: Use context managers for database sessions
def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
    """Get agent by name with proper session handling."""
    with self.get_session() as session:
        agent = session.query(Agent).filter(Agent.name == name).first()
        if agent:
            return self._agent_to_dict(agent)
        return None

# Good: Handle database errors gracefully
def update_agent(self, name: str, updates: Dict[str, Any]) -> None:
    """Update agent with validation and error handling."""
    try:
        with self.get_session() as session:
            agent = session.query(Agent).filter(Agent.name == name).first()
            if not agent:
                raise ValueError(f"Agent {name} not found")
            
            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            
            session.commit()
            logger.info(f"Successfully updated agent {name}")
    except Exception as e:
        logger.error(f"Failed to update agent {name}: {e}")
        raise
```

## 🧪 Testing

We strive for high test coverage and quality. All contributions should include appropriate tests.

### Test Structure

```
tests/
├── unit/                 # Unit tests for individual components
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_workflows.py
│   └── test_memory.py
├── integration/          # Integration tests
│   ├── test_api.py
│   ├── test_workflows.py
│   └── test_deployment.py
├── fixtures/             # Test data and fixtures
│   ├── sample_agents.json
│   └── test_workflows.json
└── conftest.py          # Pytest configuration
```

### Writing Tests

```python
# tests/unit/test_tools.py
import pytest
from unittest.mock import Mock, AsyncMock
from tools.website_monitor import WebsiteMonitorTool

class TestWebsiteMonitorTool:
    """Test suite for WebsiteMonitorTool."""
    
    @pytest.fixture
    def tool(self):
        """Create a WebsiteMonitorTool instance."""
        return WebsiteMonitorTool()
    
    def test_tool_properties(self, tool):
        """Test tool basic properties."""
        assert tool.name == "website_monitor"
        assert "monitor website" in tool.description.lower()
        assert "url" in tool.parameters["properties"]
    
    @pytest.mark.asyncio
    async def test_successful_website_check(self, tool):
        """Test successful website monitoring."""
        parameters = {
            "url": "https://httpbin.org/status/200",
            "expected_status": 200,
            "timeout": 10
        }
        
        result = await tool.execute(parameters)
        
        assert result["status"] == "online"
        assert result["status_code"] == 200
        assert result["response_time_ms"] > 0
        assert "online" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_website_timeout(self, tool):
        """Test website timeout handling."""
        parameters = {
            "url": "https://httpbin.org/delay/30",
            "timeout": 1
        }
        
        result = await tool.execute(parameters)
        
        assert result["status"] == "timeout"
        assert result["error"] == "timeout"
        assert "timed out" in result["message"].lower()
    
    def test_parameter_validation(self, tool):
        """Test parameter validation."""
        # Missing required parameter
        with pytest.raises(ValueError, match="Required parameter 'url'"):
            tool._validate_parameters(tool.parameters, {})
        
        # Invalid URL format
        with pytest.raises(ValueError):
            tool._validate_parameters(tool.parameters, {"url": "not-a-url"})
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_tools.py -v

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# Run tests matching pattern
pytest tests/ -k "test_website" -v

# Run tests with debugging
pytest tests/ -v -s --pdb
```

### Test Guidelines

- **Write tests first** (TDD approach when possible)
- **Test both success and failure cases**
- **Use descriptive test names** that explain what's being tested
- **Mock external dependencies** (APIs, databases, file systems)
- **Test edge cases** and boundary conditions
- **Keep tests fast** and independent

## 📚 Documentation

Good documentation is crucial for project success. When contributing:

### Code Documentation

```python
class WorkflowManager:
    """
    Manages workflow execution and orchestration.
    
    The WorkflowManager handles the execution of complex workflows that
    can include both agent tasks and tool executions. It supports variable
    substitution between steps and provides comprehensive error handling.
    
    Attributes:
        agent_manager: Agent manager for executing agent steps
        tool_manager: Tool manager for executing tool steps
        memory_manager: Memory manager for persistence
    
    Example:
        >>> manager = WorkflowManager(agent_mgr, tool_mgr, memory_mgr)
        >>> result = await manager.execute_workflow("my_workflow", context)
    """
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow_name: Name of the workflow to execute
            context: Initial workflow context for variable substitution
            
        Returns:
            Dictionary containing execution results and final context
            
        Raises:
            ValueError: If workflow not found or disabled
            WorkflowExecutionError: If workflow execution fails
            
        Example:
            >>> result = await manager.execute_workflow(
            ...     "website_monitoring", 
            ...     {"alert_email": "admin@company.com"}
            ... )
            >>> print(result["status"])  # "completed"
        """
        pass
```

### API Documentation

All API endpoints should have comprehensive documentation:

```python
@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent_def: AgentDefinition):
    """
    Create a new AI agent.
    
    Creates a new agent with the specified configuration. The agent
    can be assigned tools and will be available for task execution
    immediately upon creation.
    
    Args:
        agent_def: Agent definition including name, role, goals, and tools
        
    Returns:
        AgentResponse with agent ID and creation confirmation
        
    Raises:
        HTTPException: 400 if agent creation fails
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/agents" \\
          -H "Content-Type: application/json" \\
          -d '{
            "name": "website_monitor",
            "role": "Website Monitoring Specialist",
            "tools": ["website_monitor"]
          }'
        ```
    """
    pass
```

### Documentation Updates

When making changes, also update:

- **README.md** - For major feature additions
- **API documentation** - For endpoint changes
- **Code comments** - For complex logic
- **Examples** - For new functionality
- **Changelog** - For all changes

## 🌟 Community

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions, ideas, and general discussion
- **Pull Requests** - Code review and collaboration
- **Discord/Slack** - Real-time chat (if available)

### Getting Help

- **Start with documentation** - README, guides, and API docs
- **Search existing issues** - Your question might already be answered
- **Ask in discussions** - For general questions and ideas
- **Create an issue** - For specific bugs or feature requests

### Helping Others

- **Answer questions** in issues and discussions
- **Review pull requests** from other contributors
- **Share your use cases** and success stories
- **Improve documentation** based on common questions
- **Mentor newcomers** to the project

## 🎉 Recognition

We value all contributions and recognize contributors in several ways:

- **Contributors section** in README.md
- **Release notes** mention significant contributions
- **Hall of fame** for major contributors
- **Special badges** for different types of contributions

### Types of Recognition

- 🐛 **Bug Hunter** - Found and reported critical bugs
- 🔧 **Tool Creator** - Built useful tools for the community
- 📚 **Documentation Hero** - Significantly improved docs
- 🧪 **Test Champion** - Improved test coverage and quality
- 🌟 **Community Leader** - Helped grow and support the community

## 📝 Changelog and Releases

We follow [Semantic Versioning](https://semver.org/) and maintain a detailed changelog:

- **MAJOR** version for breaking changes
- **MINOR** version for new features
- **PATCH** version for bug fixes

### Contributing to Releases

- All changes go through pull requests
- Release notes are generated from commit messages
- Contributors are credited in release announcements

## ❓ FAQ

### Q: I'm new to open source. How can I contribute?

**A:** Start small! Look for issues labeled `good first issue` or `help wanted`. Documentation improvements and bug reports are great first contributions.

### Q: Can I add support for a new LLM provider?

**A:** Absolutely! We welcome integrations with different LLM providers. Please create an issue first to discuss the implementation approach.

### Q: How do I create a custom tool?

**A:** Check out the [tool creation guide](README.md#creating-custom-tools) and look at existing tools in the `tools/` directory for examples.

### Q: What if my PR gets rejected?

**A:** Feedback is part of the process! We'll provide specific suggestions for improvement. Don't take it personally - we're all working together to make the project better.

### Q: Can I work on multiple issues at once?

**A:** It's better to focus on one issue at a time, especially when starting out. This helps ensure quality and makes the review process smoother.

## 🙏 Thank You

Thank you for considering contributing to the Agentic AI Framework! Every contribution, no matter how small, helps make this project better for everyone.

Together, we're building the future of AI automation. 🚀

---

**Questions?** Feel free to reach out in [GitHub Discussions](https://github.com/yourusername/agentic-ai-framework/discussions) or create an issue if you need clarification on anything in this guide.