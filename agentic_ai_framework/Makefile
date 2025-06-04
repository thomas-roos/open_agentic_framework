# Agentic AI Framework - Makefile
# Convenient commands for development and deployment

.PHONY: help setup deploy start stop restart logs status test clean lint format install build

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Variables
PROJECT_NAME := agentic-ai-framework
PYTHON := python3
PIP := pip
VENV := venv
DOCKER_COMPOSE := docker-compose

help: ## Show this help message
	@echo "$(BLUE)Agentic AI Framework - Development Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(setup|install)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Development Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(test|lint|format|run)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Docker Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(deploy|start|stop|restart|logs|status|build)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Utility Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -vE '(setup|install|test|lint|format|run|deploy|start|stop|restart|logs|status|build)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

# Setup Commands
setup: ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@chmod +x setup.sh
	@./setup.sh

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	@. $(VENV)/bin/activate && $(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

# Development Commands
run: ## Run the application in development mode
	@echo "$(BLUE)Starting development server...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) main.py

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) -m pytest tests/ -v --cov=. --cov-report=html

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) -m pytest tests/ -v --cov=. -f

lint: ## Run linting
	@echo "$(BLUE)Running linters...$(NC)"
	@. $(VENV)/bin/activate && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@. $(VENV)/bin/activate && mypy . --ignore-missing-imports
	@. $(VENV)/bin/activate && bandit -r . -x tests/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@. $(VENV)/bin/activate && black .
	@. $(VENV)/bin/activate && isort .
	@echo "$(GREEN)Code formatted successfully$(NC)"

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code format...$(NC)"
	@. $(VENV)/bin/activate && black --check .
	@. $(VENV)/bin/activate && isort --check-only .

# Docker Commands
deploy: ## Deploy using Docker Compose
	@echo "$(BLUE)Deploying with Docker Compose...$(NC)"
	@chmod +x deploy.sh
	@./deploy.sh

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache

start: ## Start services
	@echo "$(BLUE)Starting services...$(NC)"
	@$(DOCKER_COMPOSE) up -d

stop: ## Stop services
	@echo "$(BLUE)Stopping services...$(NC)"
	@$(DOCKER_COMPOSE) down

restart: ## Restart services
	@echo "$(BLUE)Restarting services...$(NC)"
	@$(DOCKER_COMPOSE) restart

logs: ## Show logs
	@$(DOCKER_COMPOSE) logs -f

status: ## Show service status
	@$(DOCKER_COMPOSE) ps

# Utility Commands
clean: ## Clean up development environment
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@rm -rf $(VENV)
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf htmlcov
	@rm -rf *.egg-info
	@find . -type d -name __pycache__ -delete
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Cleanup completed$(NC)"

clean-docker: ## Clean Docker containers and images
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	@$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)Docker cleanup completed$(NC)"

backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	@if [ -f "data/agentic_ai.db" ]; then \
		cp data/agentic_ai.db backups/agentic_ai_$$(date +%Y%m%d_%H%M%S).db; \
		echo "$(GREEN)Database backed up successfully$(NC)"; \
	else \
		echo "$(YELLOW)No database found to backup$(NC)"; \
	fi

health: ## Check system health
	@echo "$(BLUE)Checking system health...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)API not responding$(NC)"
	@curl -f http://localhost:11434/api/tags || echo "$(RED)Ollama not responding$(NC)"

shell: ## Open shell in container
	@$(DOCKER_COMPOSE) exec agentic-ai bash

ollama-shell: ## Open shell in Ollama container
	@$(DOCKER_COMPOSE) exec ollama bash

pull-models: ## Pull required models
	@echo "$(BLUE)Pulling required models...$(NC)"
	@$(DOCKER_COMPOSE) exec ollama ollama pull llama3
	@echo "$(GREEN)Models pulled successfully$(NC)"

dev-deps: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@. $(VENV)/bin/activate && $(PIP) install \
		pytest-cov \
		mypy \
		pre-commit \
		bandit \
		safety \
		black \
		isort \
		flake8
	@echo "$(GREEN)Development dependencies installed$(NC)"

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	@. $(VENV)/bin/activate && safety check
	@. $(VENV)/bin/activate && bandit -r . -x tests/

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@mkdir -p docs/generated
	@echo "$(YELLOW)Documentation generation not implemented yet$(NC)"

init: ## Initialize new project
	@echo "$(BLUE)Initializing new Agentic AI project...$(NC)"
	@cp .env.example .env
	@mkdir -p {data,logs,tools,tests}
	@echo "$(GREEN)Project initialized$(NC)"
	@echo "$(YELLOW)Please review and customize the .env file$(NC)"

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Python: $$(python3 --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@if [ -d "$(VENV)" ]; then \
		echo "Virtual Environment: Active"; \
	else \
		echo "Virtual Environment: Not found"; \
	fi

# Development workflow shortcuts
dev: setup run ## Quick development setup and run

prod: deploy ## Quick production deployment

ci: lint test ## Continuous integration checks

# Examples
example-agent: ## Create example monitoring agent
	@echo "$(BLUE)Creating example monitoring agent...$(NC)"
	@curl -X POST "http://localhost:8000/agents" \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "example_monitor", \
			"role": "Website Monitor", \
			"goals": "Monitor website availability", \
			"backstory": "Experienced system monitor", \
			"tools": ["website_monitor", "email_sender"], \
			"enabled": true \
		}' && echo "\n$(GREEN)Example agent created$(NC)" || echo "$(RED)Failed to create agent$(NC)"

example-workflow: ## Create example monitoring workflow
	@echo "$(BLUE)Creating example monitoring workflow...$(NC)"
	@curl -X POST "http://localhost:8000/workflows" \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "example_monitoring", \
			"description": "Example website monitoring workflow", \
			"steps": [ \
				{ \
					"type": "tool", \
					"name": "website_monitor", \
					"parameters": {"url": "https://google.com"}, \
					"context_key": "status" \
				} \
			], \
			"enabled": true \
		}' && echo "\n$(GREEN)Example workflow created$(NC)" || echo "$(RED)Failed to create workflow$(NC)"