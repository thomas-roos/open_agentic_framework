#!/bin/bash

# Agentic AI Framework - Development Setup Script
# This script sets up the development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    log_info "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    required_version="3.11"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        log_error "Python $required_version or higher is required. Current version: $python_version"
        exit 1
    fi
    
    log_success "Python $python_version is installed"
}

# Create virtual environment
create_venv() {
    log_info "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        log_info "Virtual environment already exists"
    else
        python3 -m venv venv
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    log_info "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Dependencies installed from requirements.txt"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

# Setup development tools
setup_dev_tools() {
    log_info "Setting up development tools..."
    
    # Install additional development dependencies
    pip install \
        pytest-cov \
        mypy \
        pre-commit \
        bandit \
        safety
    
    # Setup pre-commit hooks
    if [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install
        log_success "Pre-commit hooks installed"
    fi
    
    log_success "Development tools setup complete"
}

# Create project structure
create_structure() {
    log_info "Creating project structure..."
    
    # Create directories
    mkdir -p {data,logs,tools,tests,docs,scripts}
    mkdir -p {api,managers,background}
    
    # Create __init__.py files
    touch tools/__init__.py
    touch api/__init__.py
    touch managers/__init__.py
    touch background/__init__.py
    touch tests/__init__.py
    
    # Create tools/__init__.py with proper content
    cat > tools/__init__.py << 'EOF'
"""Tools package for the Agentic AI Framework"""

from .base_tool import BaseTool

__all__ = ['BaseTool']
EOF
    
    log_success "Project structure created"
}

# Setup environment files
setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Created .env file from .env.example"
        else
            cat > .env << 'EOF'
# Development Environment Configuration
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=llama3
DATABASE_PATH=data/agentic_ai.db
API_HOST=0.0.0.0
API_PORT=8000
MAX_AGENT_ITERATIONS=10
SCHEDULER_INTERVAL=60
TOOLS_DIRECTORY=tools
LOG_LEVEL=DEBUG
EOF
            log_success "Created basic .env file"
        fi
    else
        log_info ".env file already exists"
    fi
    
    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Data and Logs
data/
logs/
*.db
*.log

# Environment
.env
.env.local
.env.production

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Testing
.coverage
.pytest_cache/
htmlcov/

# Mypy
.mypy_cache/
.dmypy.json
dmypy.json
EOF
        log_success "Created .gitignore file"
    fi
}

# Setup Ollama for development
setup_ollama() {
    log_info "Checking Ollama installation..."
    
    if command -v ollama &> /dev/null; then
        log_success "Ollama is installed"
        
        # Check if Ollama is running
        if curl -f http://localhost:11434/api/tags &> /dev/null; then
            log_success "Ollama is running"
            
            # Check if default model is installed
            if ollama list | grep -q "llama3"; then
                log_success "llama3 model is installed"
            else
                log_info "Installing llama3 model..."
                ollama pull llama3
                log_success "llama3 model installed"
            fi
        else
            log_warning "Ollama is not running. Please start Ollama service."
            log_info "You can start Ollama with: ollama serve"
        fi
    else
        log_warning "Ollama is not installed."
        log_info "Please install Ollama from: https://ollama.ai"
        log_info "After installation, run: ollama serve && ollama pull llama3"
    fi
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    if [ -d "tests" ] && [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
        python -m pytest tests/ -v
        log_success "Tests completed"
    else
        log_warning "No tests found or pytest not configured"
    fi
}

# Create sample files
create_samples() {
    log_info "Creating sample files..."
    
    # Create sample test
    mkdir -p tests
    cat > tests/test_config.py << 'EOF'
"""Test configuration module."""

import pytest
from config import Config


def test_config_initialization():
    """Test that configuration initializes with defaults."""
    config = Config()
    assert config.api_host == "0.0.0.0"
    assert config.api_port == 8000
    assert config.max_agent_iterations == 10


def test_config_validation():
    """Test configuration validation."""
    config = Config()
    config.validate()  # Should not raise exception


def test_config_to_dict():
    """Test configuration conversion to dictionary."""
    config = Config()
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "api_host" in config_dict
    assert "api_port" in config_dict
EOF
    
    # Create sample tool
    if [ ! -f "tools/sample_tool.py" ]; then
        cat > tools/sample_tool.py << 'EOF'
"""
Sample tool for demonstration purposes.
This tool shows how to create custom tools for the framework.
"""

from typing import Dict, Any
from .base_tool import BaseTool


class SampleTool(BaseTool):
    """A sample tool that demonstrates the tool interface."""
    
    @property
    def name(self) -> str:
        return "sample_tool"
    
    @property
    def description(self) -> str:
        return "A sample tool for demonstration purposes. Returns a greeting message."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to include in the greeting"
                },
                "language": {
                    "type": "string",
                    "description": "Language for the greeting",
                    "default": "english"
                }
            },
            "required": ["name"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the sample tool."""
        name = parameters.get("name", "World")
        language = parameters.get("language", "english").lower()
        
        greetings = {
            "english": f"Hello, {name}!",
            "spanish": f"¡Hola, {name}!",
            "french": f"Bonjour, {name}!",
            "german": f"Hallo, {name}!"
        }
        
        greeting = greetings.get(language, greetings["english"])
        
        return {
            "greeting": greeting,
            "name": name,
            "language": language,
            "message": f"Sample tool executed successfully for {name}"
        }
EOF
        log_success "Created sample tool"
    fi
    
    log_success "Sample files created"
}

# Display setup status
show_status() {
    log_info "Development Setup Status:"
    echo ""
    
    echo "Environment:"
    echo "  • Python: $(python3 --version)"
    echo "  • Pip: $(pip --version | cut -d' ' -f2)"
    echo "  • Virtual environment: $([ -d "venv" ] && echo "✓ Created" || echo "✗ Not found")"
    echo ""
    
    echo "Project structure:"
    echo "  • Configuration: $([ -f ".env" ] && echo "✓ .env" || echo "✗ .env missing")"
    echo "  • Dependencies: $([ -f "requirements.txt" ] && echo "✓ requirements.txt" || echo "✗ requirements.txt missing")"
    echo "  • Git ignore: $([ -f ".gitignore" ] && echo "✓ .gitignore" || echo "✗ .gitignore missing")"
    echo ""
    
    echo "Services:"
    echo "  • Ollama: $(command -v ollama &> /dev/null && echo "✓ Installed" || echo "✗ Not installed")"
    echo "  • Ollama running: $(curl -f http://localhost:11434/api/tags &> /dev/null && echo "✓ Running" || echo "✗ Not running")"
    echo ""
    
    echo "Next steps:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Review and customize .env file"
    echo "  3. Start Ollama if not running: ollama serve"
    echo "  4. Pull required model: ollama pull llama3"
    echo "  5. Run the application: python main.py"
    echo "  6. Access API docs: http://localhost:8000/docs"
    echo ""
}

# Main setup function
main() {
    log_info "Setting up Agentic AI Framework development environment..."
    echo ""
    
    # Check prerequisites
    check_python
    
    # Setup environment
    create_venv
    install_dependencies
    setup_dev_tools
    
    # Setup project
    create_structure
    setup_environment
    create_samples
    
    # Setup external services
    setup_ollama
    
    # Show status
    show_status
    
    log_success "Development setup completed!"
}

# Handle script arguments
case "${1:-}" in
    "setup"|"")
        main
        ;;
    "test")
        source venv/bin/activate 2>/dev/null || true
        run_tests
        ;;
    "clean")
        log_warning "This will remove the virtual environment!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            log_success "Virtual environment removed"
        else
            log_info "Cleanup cancelled"
        fi
        ;;
    "activate")
        echo "To activate the virtual environment, run:"
        echo "source venv/bin/activate"
        ;;
    "help"|"-h"|"--help")
        echo "Agentic AI Framework Development Setup Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  setup             Setup development environment (default)"
        echo "  test              Run tests"
        echo "  clean             Remove virtual environment"
        echo "  activate          Show activation command"
        echo "  help              Show this help message"
        echo ""
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac