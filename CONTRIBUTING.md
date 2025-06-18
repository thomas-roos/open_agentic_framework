# 🤝 Contributing to Open Agentic Framework

Thank you for your interest in contributing to the Open Agentic Framework! We welcome contributions from developers of all skill levels. This guide will help you get started.

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
git clone https://github.com/oscarvalenzuelab/open_agentic_framework.git
cd open_agentic_framework

# 3. Add upstream remote
git remote add upstream https://github.com/oscarvalenzuelab/open_agentic_framework.git

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

Thank you for considering contributing to the Open Agentic Framework! Every contribution, no matter how small, helps make this project better for everyone.
