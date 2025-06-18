# Open Agentic Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)

A sample framework implementation for creating and orchestrating AI agents, featuring multi-provider LLM support, intelligent memory management, and advanced workflow capabilities.

## Features

- **AI Agent Management** - Create agents with specific roles, goals, and capabilities
- **Multi-Provider LLM Support** - Ollama, OpenAI, OpenRouter with automatic fallback
- **Extensible Tool System** - Built-in tools with plugin architecture for custom integrations
- **Advanced Workflow Orchestration** - Chain agents and tools with intelligent variable resolution
- **Smart Memory Management** - Automatic memory limits, cleanup, and context filtering
- **Model Warmup System** - Pre-load models for instant response times
- **Task Scheduling** - Automated execution of agents and workflows
- **Website Monitoring** - Real-world example with email alerting capabilities
- **Production Ready** - Docker deployment with comprehensive monitoring
- **Interactive API Documentation** - Complete Swagger UI with live testing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 4GB+ available RAM
- Internet connection for downloading models

### 1. Clone and Deploy

```bash
# Clone the repository
git clone https://github.com/oscarvalenzuelab/open_agentic_framework.git
cd open_agentic_framework

# Start the framework
docker-compose up -d

# Wait for models to download (5-10 minutes)
docker-compose logs -f model-downloader
```

### 2. Access the Framework & Documentation

- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Provider Status**: http://localhost:8000/providers
- **Available Models**: http://localhost:8000/models
- **Memory Statistics**: http://localhost:8000/memory/stats

> **Tip**: The Swagger documentation at `/docs` provides a complete interactive interface to explore and test all API endpoints with live examples!

### 3. Create Your First Agent

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_guardian",
    "role": "Website Monitoring Specialist", 
    "goals": "Monitor websites and send alerts when issues are detected",
    "backstory": "You are an experienced system administrator responsible for ensuring high availability.",
    "tools": ["website_monitor", "email_sender"],
    "ollama_model": "granite3.2:2b",
    "enabled": true
  }'
```

### 4. Execute Your First Task

```bash
curl -X POST "http://localhost:8000/agents/website_guardian/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://google.com is online and report the status",
    "context": {}
  }'
```

## Multi-Provider LLM Support

The framework supports multiple LLM providers with automatic fallback and intelligent routing:

### Supported Providers

- **Ollama** - Local models (default)
- **OpenAI** - GPT models via API
- **OpenRouter** - Access to 100+ models

### Environment Configuration

```bash
# Core LLM Configuration
DEFAULT_LLM_PROVIDER=ollama                    # Primary provider
LLM_FALLBACK_ENABLED=true                      # Enable automatic fallback
LLM_FALLBACK_ORDER=ollama,openai,openrouter    # Fallback priority order

# Ollama Provider (Default)
OLLAMA_ENABLED=true
OLLAMA_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=granite3.2:2b

# OpenAI Provider
OPENAI_ENABLED=false                           # Set to true to enable
OPENAI_API_KEY=your-openai-api-key
OPENAI_DEFAULT_MODEL=gpt-3.5-turbo
OPENAI_ORGANIZATION=your-org-id                # Optional

# OpenRouter Provider
OPENROUTER_ENABLED=false                       # Set to true to enable
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_DEFAULT_MODEL=openai/gpt-3.5-turbo
```

### Dynamic Provider Management

```bash
# Configure providers without restart
curl -X POST "http://localhost:8000/providers/openai/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "api_key": "your-new-api-key",
    "default_model": "gpt-4"
  }'

# Check all provider status
curl http://localhost:8000/providers

# Test specific model
curl -X POST "http://localhost:8000/models/test/gpt-3.5-turbo"
```

## Model Warmup System

Advanced model pre-loading for instant response times:

```bash
# Model warmup configuration
MODEL_WARMUP_TIMEOUT=60                        # Warmup timeout (seconds)
MAX_CONCURRENT_WARMUPS=2                       # Concurrent warmup operations
AUTO_WARMUP_ON_STARTUP=true                    # Auto-warm agent models
WARMUP_INTERVAL_HOURS=6                        # Re-warm interval
MAX_IDLE_HOURS=24                             # Remove unused models after
```

**Features:**
- **Instant Responses** - Pre-loaded models respond immediately
- **Usage Tracking** - Monitors which models are actively used
- **Automatic Cleanup** - Removes unused models to save memory
- **Smart Refresh** - Re-warms models periodically

## Core Concepts

Understanding the framework's key components:

### **Agent**
An intelligent entity with a specific role, goals, and capabilities. Agents can use tools to accomplish tasks and maintain conversation memory.

```json
{
  "name": "website_guardian",
  "role": "Website Monitoring Specialist", 
  "goals": "Monitor websites and send alerts when issues detected",
  "backstory": "Experienced system administrator with 10+ years experience",
  "tools": ["website_monitor", "email_sender"],
  "ollama_model": "granite3.2:2b",
  "tool_configs": {
    "email_sender": {
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "smtp_username": "alerts@company.com",
      "smtp_password": "app-password"
    }
  }
}
```

### **Task**
A specific instruction or request given to an agent. Tasks are processed by agents using their available tools and knowledge.

```bash
# Example task
"Check if https://google.com is online and send an email alert if it's down"
```

### **Tool**
A specific capability or function that agents can use to interact with external systems, APIs, or perform specific operations.

**Built-in Tools:**
- `website_monitor` - Check website availability and response time
- `email_sender` - Send emails via SMTP
- `http_client` - Make HTTP requests to APIs

### **Workflow**
A sequence of steps that can include both agent tasks and tool executions, with **advanced variable passing** between steps.

```json
{
  "name": "website_health_check",
  "steps": [
    {
      "type": "tool",
      "name": "website_monitor", 
      "parameters": {"url": "https://example.com"},
      "context_key": "status"
    },
    {
      "type": "agent",
      "name": "website_guardian",
      "task": "Analyze status: {{status.response_time}}ms response from {{status.url}} and send alerts if needed"
    }
  ]
}
```

### **Memory**
Conversation history and context maintained for each agent, with **intelligent context filtering** and automatic cleanup (default: 5 entries per agent).

### **Scheduled Task**
Automated execution of agents or workflows at specified times or intervals.

```json
{
  "task_type": "workflow",
  "workflow_name": "website_health_check",
  "scheduled_time": "2024-01-15T10:00:00Z"
}
```

## Creating Advanced Workflows

Workflows support sophisticated variable substitution and nested object access:

### Variable Substitution System

Use `{{variable}}` syntax to pass data between workflow steps:

```json
{
  "name": "data_processing_pipeline",
  "steps": [
    {
      "type": "tool",
      "name": "http_client",
      "parameters": {
        "url": "https://api.example.com/data/{{dataset_id}}",
        "headers": {"Authorization": "Bearer {{api_token}}"}
      },
      "context_key": "api_response"
    },
    {
      "type": "agent",
      "name": "data_analyst",
      "task": "Analyze this API response: {{api_response.data}} with status {{api_response.status}} for dataset {{dataset_id}}",
      "context_key": "analysis"
    }
  ]
}
```

### Nested Object Access

Access nested properties from previous workflow steps:

```json
{
  "task": "The API returned status {{api_response.status}} with {{api_response.data.total_records}} records. Send summary to {{user.email}}"
}
```

### Tool Configuration per Agent

Configure tools differently for each agent:

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "notification_agent",
    "tools": ["email_sender", "webhook_client"],
    "tool_configs": {
      "email_sender": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "from_email": "AI Assistant <notifications@company.com>",
        "default_template": "professional"
      },
      "webhook_client": {
        "default_timeout": 30,
        "retry_attempts": 3
      }
    }
  }'
```

## Enhanced Memory Management

Advanced memory features with intelligent cleanup:

### Memory Statistics & Cleanup

```bash
# Get detailed memory statistics
curl http://localhost:8000/memory/stats

# Example response:
{
  "total_memory_entries": 45,
  "agents_with_memory": 3,
  "memory_per_agent": {
    "website_guardian": 12,
    "data_analyst": 8,
    "license_assessor": 25
  },
  "oldest_entry": "2024-06-09T10:00:00Z",
  "newest_entry": "2024-06-10T14:30:00Z"
}

# Intelligent cleanup (keeps last N entries per agent)
curl -X POST "http://localhost:8000/memory/cleanup"

# Clear all memory (nuclear option)
curl -X DELETE "http://localhost:8000/memory/clear-all"

# Clear specific agent memory
curl -X DELETE "http://localhost:8000/agents/website_guardian/memory"
```

### Memory Configuration

```bash
# Memory Management Settings
MAX_AGENT_MEMORY_ENTRIES=5          # Max memory per agent
CLEAR_MEMORY_ON_STARTUP=false       # Clear memory on restart
MEMORY_CLEANUP_INTERVAL=3600        # Cleanup interval (seconds)
MEMORY_RETENTION_DAYS=7             # Days to keep old entries
```

## API Documentation

### Interactive Swagger Documentation

Access the complete API documentation with interactive testing capabilities:

**http://localhost:8000/docs**

The Swagger interface provides:
- Complete endpoint documentation
- **Live API Testing** - Test endpoints directly from the browser
- Request/response schemas with examples
- Authentication options
- **Code Generation** - Generate client code in multiple languages
- **Schema Explorer** - Browse all data models and their properties

### Alternative Documentation Formats

- **ReDoc**: http://localhost:8000/redoc (Clean, responsive documentation)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (Raw OpenAPI specification)

### Key API Sections

1. **Providers** (`/providers`) - Multi-provider LLM management
2. **Models** (`/models`) - Model discovery and testing
3. **Agents** (`/agents`) - Create and manage AI agents
4. **Tools** (`/tools`) - Execute and manage tools
5. **Workflows** (`/workflows`) - Create and execute workflows
6. **Memory** (`/memory`) - Advanced memory management
7. **Schedule** (`/schedule`) - Schedule automated tasks
8. **System** (`/health`, `/config`) - System monitoring and configuration

### Complete Website Monitoring Example

<details>
<summary>Click to expand complete monitoring system setup</summary>

```bash
# 1. Create monitoring agent with email configuration
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_guardian",
    "role": "Website Monitoring Guardian",
    "goals": "Ensure critical websites are always online and notify immediately when issues are detected",
    "backstory": "You are a vigilant system monitor with years of experience in maintaining high-availability systems. You check websites systematically and provide clear, actionable status reports.",
    "tools": ["website_monitor", "email_sender"],
    "ollama_model": "deepseek-r1:1.5b",
    "enabled": true,
    "tool_configs": {
      "email_sender": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "alerts@yourcompany.com",
        "smtp_password": "your-app-password",
        "from_email": "Website Guardian <alerts@yourcompany.com>"
      }
    }
  }'

# 2. Create monitoring workflow with intelligent analysis
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_health_check",
    "description": "Comprehensive website monitoring with intelligent alerts",
    "steps": [
      {
        "type": "tool",
        "name": "website_monitor",
        "parameters": {
          "url": "{{target_url}}",
          "timeout": 10,
          "expected_status": 200
        },
        "context_key": "website_status"
      },
      {
        "type": "agent", 
        "name": "website_guardian",
        "task": "Analyze the website monitoring result: {{website_status}}. Check response time (should be <2000ms), status code, and any errors. If there are issues, send an email alert to {{alert_email}} with detailed analysis.",
        "context_key": "alert_result"
      }
    ],
    "enabled": true
  }'

# 3. Execute monitoring workflow
curl -X POST "http://localhost:8000/workflows/website_health_check/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "target_url": "https://yourwebsite.com",
      "alert_email": "admin@yourcompany.com"
    }
  }'

# 4. Schedule regular monitoring (every 5 minutes)
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "workflow",
    "workflow_name": "website_health_check", 
    "scheduled_time": "2024-01-15T10:00:00Z",
    "context": {
      "recurring": "every_5_minutes",
      "target_url": "https://yourwebsite.com",
      "alert_email": "admin@yourcompany.com"
    }
  }'
```

</details>

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Ollama](https://ollama.ai/) for local LLM capabilities
- [OpenAI](https://openai.com/) for pioneering AI APIs
- [SQLAlchemy](https://www.sqlalchemy.org/) for robust database management
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
