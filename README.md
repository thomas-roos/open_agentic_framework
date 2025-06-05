# 🤖 Agentic AI Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)

A powerful, production-ready framework for creating and orchestrating AI agents with natural language processing capabilities, built-in tools, and intelligent memory management.

## ✨ Features

- 🤖 **AI Agent Management** - Create agents with specific roles, goals, and capabilities
- 🔧 **Extensible Tool System** - Built-in tools with plugin architecture for custom integrations
- 📋 **Workflow Orchestration** - Chain agents and tools in complex, conditional sequences
- 🧠 **Smart Memory Management** - Automatic memory limits and cleanup for optimal performance
- ⏰ **Task Scheduling** - Automated execution of agents and workflows
- 🌐 **Website Monitoring** - Real-world example with email alerting capabilities
- 🐳 **Production Ready** - Docker deployment with comprehensive monitoring
- 🔄 **Multi-Model Support** - Easy switching between different LLM models via Ollama

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 4GB+ available RAM
- Internet connection for downloading models

### 1. Clone and Deploy

```bash
# Clone the repository
git clone https://github.com/yourusername/agentic-ai-framework.git
cd agentic-ai-framework

# Start the framework
docker-compose up -d

# Wait for models to download (5-10 minutes)
docker-compose logs -f model-downloader
```

### 2. Access the Framework & Documentation

- **🌐 API Documentation (Swagger)**: http://localhost:8000/docs
- **📊 Health Check**: http://localhost:8000/health
- **🤖 Available Models**: http://localhost:8000/models
- **💾 Memory Statistics**: http://localhost:8000/memory/stats

> **💡 Tip**: The Swagger documentation at `/docs` provides an interactive interface to explore and test all API endpoints!

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

## 📖 Core Concepts

Understanding the framework's key components:

### 🤖 **Agent**
An intelligent entity with a specific role, goals, and capabilities. Agents can use tools to accomplish tasks and maintain conversation memory.

```json
{
  "name": "website_guardian",
  "role": "Website Monitoring Specialist", 
  "goals": "Monitor websites and send alerts when issues detected",
  "backstory": "Experienced system administrator with 10+ years experience",
  "tools": ["website_monitor", "email_sender"],
  "ollama_model": "granite3.2:2b"
}
```

### 📋 **Task**
A specific instruction or request given to an agent. Tasks are processed by agents using their available tools and knowledge.

```bash
# Example task
"Check if https://google.com is online and send an email alert if it's down"
```

### 🔧 **Tool**
A specific capability or function that agents can use to interact with external systems, APIs, or perform specific operations.

**Built-in Tools:**
- `website_monitor` - Check website availability and response time
- `email_sender` - Send emails via SMTP
- `http_client` - Make HTTP requests to APIs

### 🔄 **Workflow**
A sequence of steps that can include both agent tasks and tool executions, with variable passing between steps.

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
      "task": "Analyze status: {status} and send alerts if needed"
    }
  ]
}
```

### 🧠 **Memory**
Conversation history and context maintained for each agent, automatically managed with configurable limits (default: 5 entries per agent).

### 📅 **Scheduled Task**
Automated execution of agents or workflows at specified times or intervals.

```json
{
  "task_type": "workflow",
  "workflow_name": "website_health_check",
  "scheduled_time": "2024-01-15T10:00:00Z"
}
```

## 🔄 Creating Workflows

Workflows allow you to chain multiple agents and tools together for complex automation.

### Basic Workflow Structure

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data_processing_pipeline",
    "description": "Process data through multiple steps",
    "steps": [
      {
        "type": "tool",
        "name": "http_client",
        "parameters": {
          "url": "https://api.example.com/data",
          "method": "GET"
        },
        "context_key": "raw_data"
      },
      {
        "type": "agent", 
        "name": "data_analyst",
        "task": "Analyze this data: {raw_data} and provide insights",
        "context_key": "analysis"
      },
      {
        "type": "agent",
        "name": "report_generator", 
        "task": "Create a summary report based on: {analysis}",
        "context_key": "final_report"
      }
    ],
    "enabled": true
  }'
```

### Workflow Step Types

#### Tool Steps
Execute a tool with specific parameters:
```json
{
  "type": "tool",
  "name": "website_monitor",
  "parameters": {
    "url": "https://example.com",
    "timeout": 10,
    "expected_status": 200
  },
  "context_key": "website_status"
}
```

#### Agent Steps  
Execute an agent with a task:
```json
{
  "type": "agent",
  "name": "monitoring_agent",
  "task": "Review the website status: {website_status} and determine if action is needed",
  "context_key": "decision"
}
```

### Variable Substitution

Use `{variable_name}` syntax to pass data between workflow steps:

```json
{
  "task": "Process the API response: {api_data} and send results to {email_address}"
}
```

Variables are automatically substituted from the workflow context based on previous step results.

### Conditional Workflows

Create workflows with conditional logic by using agent decision-making:

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "conditional_monitoring",
    "description": "Monitor website and conditionally send alerts",
    "steps": [
      {
        "type": "tool",
        "name": "website_monitor",
        "parameters": {"url": "https://example.com"},
        "context_key": "status"
      },
      {
        "type": "agent",
        "name": "decision_agent",
        "task": "Based on website status: {status}, determine if an alert email should be sent. Only send if status is not OK.",
        "context_key": "should_alert"
      },
      {
        "type": "agent", 
        "name": "notification_agent",
        "task": "If the decision was to alert ({should_alert}), send an email to admin@company.com about the website issue: {status}",
        "context_key": "notification_result"
      }
    ],
    "enabled": true
  }'
```

### Executing Workflows

```bash
# Execute workflow immediately
curl -X POST "http://localhost:8000/workflows/data_processing_pipeline/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "email_address": "admin@company.com",
      "priority": "high"
    }
  }'

# Schedule workflow execution
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "workflow",
    "workflow_name": "data_processing_pipeline",
    "scheduled_time": "2024-01-15T09:00:00Z",
    "context": {
      "email_address": "reports@company.com"
    }
  }'
```

### Workflow Best Practices

1. **Keep Steps Focused** - Each step should have a single, clear purpose
2. **Use Descriptive Names** - Make workflow and step names self-explanatory
3. **Handle Errors Gracefully** - Include error handling in agent instructions
4. **Test Incrementally** - Test individual steps before combining into workflows
5. **Document Context Variables** - Clearly document what data is passed between steps

### Advanced Workflow Example: E-commerce Order Processing

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "order_processing",
    "description": "Complete e-commerce order processing pipeline",
    "steps": [
      {
        "type": "tool",
        "name": "http_client",
        "parameters": {
          "url": "https://api.store.com/orders/pending",
          "method": "GET",
          "headers": {"Authorization": "Bearer {api_token}"}
        },
        "context_key": "pending_orders"
      },
      {
        "type": "agent",
        "name": "order_validator", 
        "task": "Validate these pending orders: {pending_orders}. Check for completeness, payment status, and inventory availability.",
        "context_key": "validation_results"
      },
      {
        "type": "agent",
        "name": "fulfillment_coordinator",
        "task": "Based on validation results: {validation_results}, create fulfillment instructions for valid orders and flag issues for manual review.",
        "context_key": "fulfillment_plan"
      },
      {
        "type": "tool",
        "name": "email_sender",
        "parameters": {
          "to": "fulfillment@company.com",
          "subject": "Daily Order Processing Results",
          "body": "Fulfillment plan: {fulfillment_plan}"
        },
        "context_key": "notification_sent"
      }
    ],
    "enabled": true
  }'
```

## 🌐 API Documentation

### Interactive Swagger Documentation

Access the complete API documentation with interactive testing capabilities:

**🔗 http://localhost:8000/docs**

The Swagger interface provides:
- 📝 Complete endpoint documentation
- 🧪 Interactive API testing
- 📋 Request/response schemas
- 🔧 Authentication options
- 💡 Example requests and responses

### Alternative Documentation Formats

- **ReDoc**: http://localhost:8000/redoc (Alternative documentation interface)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (Raw OpenAPI specification)

### Key API Sections

1. **Agents** (`/agents`) - Create and manage AI agents
2. **Models** (`/models`) - List and manage Ollama models  
3. **Tools** (`/tools`) - Execute and manage tools
4. **Workflows** (`/workflows`) - Create and execute workflows
5. **Memory** (`/memory`) - Manage agent memory and cleanup
6. **Schedule** (`/schedule`) - Schedule automated tasks
7. **System** (`/health`, `/config`) - System monitoring and configuration

> **💡 Pro Tip**: Use the Swagger interface to generate code snippets in multiple programming languages for easy integration!

### Website Monitoring with Email Alerts

Create a complete monitoring system that checks websites and sends email notifications:

<details>
<summary>Click to expand complete example</summary>

```bash
# 1. Create monitoring agent with email configuration
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_guardian",
    "role": "Website Monitoring Guardian",
    "goals": "Ensure critical websites are always online and notify immediately when issues are detected",
    "backstory": "You are a vigilant system monitor with years of experience in maintaining high-availability systems.",
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

# 2. Create monitoring workflow
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_health_check",
    "description": "Comprehensive website monitoring with email alerts",
    "steps": [
      {
        "type": "tool",
        "name": "website_monitor",
        "parameters": {
          "url": "https://yourwebsite.com",
          "timeout": 10,
          "expected_status": 200
        },
        "context_key": "website_status"
      },
      {
        "type": "agent", 
        "name": "website_guardian",
        "task": "Analyze the website monitoring result: {website_status}. If the website is down or has issues, send an immediate email alert to admin@yourcompany.com with details.",
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
      "alert_email": "admin@yourcompany.com"
    }
  }'
```

</details>

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Agent         │    │   Workflow      │
│   Web Server    │◄──►│   Manager       │◄──►│   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Memory        │    │   Tool          │    │   Background    │
│   Manager       │    │   Manager       │    │   Scheduler     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌─────────────────┐              
│   SQLite        │    │   Ollama        │              
│   Database      │    │   LLM Client    │              
└─────────────────┘    └─────────────────┘              
```

### Core Components

- **FastAPI Web Server** - REST API with automatic documentation
- **Agent Manager** - Handles agent lifecycle and execution with memory management
- **Tool Manager** - Dynamic tool discovery and execution engine
- **Workflow Engine** - Orchestrates complex multi-step processes
- **Memory Manager** - SQLite-based persistence with automatic cleanup
- **Background Scheduler** - Automated task execution and maintenance
- **Ollama Client** - Local LLM integration with model management

## 🔧 Built-in Tools

### Website Monitor
```json
{
  "name": "website_monitor", 
  "description": "Monitor website availability and response time",
  "parameters": {
    "url": "https://example.com",
    "timeout": 10,
    "expected_status": 200,
    "check_content": "optional text to verify"
  }
}
```

### Email Sender
```json
{
  "name": "email_sender",
  "description": "Send emails via SMTP",
  "configuration": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "your-email@gmail.com", 
    "smtp_password": "your-app-password"
  }
}
```

### HTTP Client
```json
{
  "name": "http_client",
  "description": "Make HTTP requests to APIs",
  "parameters": {
    "url": "https://api.example.com",
    "method": "GET",
    "headers": {},
    "data": {}
  }
}
```

## 📊 API Reference

### Agents
- `POST /agents` - Create new agent
- `GET /agents` - List all agents
- `GET /agents/{name}` - Get agent details
- `PUT /agents/{name}` - Update agent
- `DELETE /agents/{name}` - Delete agent
- `POST /agents/{name}/execute` - Execute agent task
- `GET /agents/{name}/memory` - Get conversation history

### Models
- `GET /models` - List available Ollama models
- `GET /models/status` - Detailed model status and health

### Memory Management
- `GET /memory/stats` - Memory usage statistics
- `DELETE /memory/clear-all` - Clear all agent memory
- `POST /memory/cleanup` - Cleanup old memory entries
- `DELETE /agents/{name}/memory` - Clear specific agent memory

### Tools
- `GET /tools` - List available tools
- `GET /tools/{name}` - Get tool details
- `POST /tools/{name}/execute` - Execute tool directly

### Workflows
- `POST /workflows` - Create workflow
- `GET /workflows` - List workflows
- `POST /workflows/{name}/execute` - Execute workflow

### Scheduling
- `POST /schedule` - Schedule task
- `GET /schedule` - List scheduled tasks
- `DELETE /schedule/{id}` - Delete scheduled task

### System
- `GET /health` - System health check
- `GET /config` - Get configuration
- `PUT /config` - Update configuration

## ⚙️ Configuration

### Environment Variables

```bash
# Core Settings
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=granite3.2:2b
API_HOST=0.0.0.0
API_PORT=8000

# Memory Management
MAX_AGENT_MEMORY_ENTRIES=5          # Max memory per agent
CLEAR_MEMORY_ON_STARTUP=true        # Clear memory on restart
MEMORY_CLEANUP_INTERVAL=3600        # Cleanup interval (seconds)
MEMORY_RETENTION_DAYS=7             # Days to keep old entries

# Performance
MAX_AGENT_ITERATIONS=3              # Max reasoning iterations
SCHEDULER_INTERVAL=60               # Background task interval
```

### Recommended Model Settings

| Deployment Size | RAM | Recommended Model | Memory Entries |
|----------------|-----|-------------------|----------------|
| Small | 2GB | `smollm:135m` | 3 |
| Standard | 4GB | `granite3.2:2b` | 5 |
| Performance | 8GB+ | `deepseek-r1:1.5b` | 10 |

## 🐳 Production Deployment

For detailed production deployment instructions, see the [DigitalOcean Deployment Guide](DEPLOYMENT.md).

### Quick Production Setup

```bash
# Local deployment (development)
docker-compose up -d

# Production deployment
./deploy-digitalocean.sh  # See DEPLOYMENT.md for details
```

## 🛠 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py
```

### Creating Custom Tools

```python
# tools/my_custom_tool.py
from tools.base_tool import BaseTool

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property 
    def description(self) -> str:
        return "Description of what my tool does"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "parameter1": {
                    "type": "string",
                    "description": "Description of parameter"
                }
            },
            "required": ["parameter1"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        # Your tool logic here
        return {"result": "Tool executed successfully"}
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_agents.py -v
```

## 📈 Monitoring & Observability

### Health Checks

```bash
# System health
curl http://localhost:8000/health

# Memory statistics  
curl http://localhost:8000/memory/stats

# Model status
curl http://localhost:8000/models/status
```

### Logs

```bash
# Application logs
docker logs agentic_ai_framework_agentic-ai_1

# Ollama logs
docker logs agentic_ai_framework_ollama_1

# Follow logs in real-time
docker-compose logs -f
```

### Performance Monitoring

```bash
# Container stats
docker stats

# System resources
htop

# Memory usage by agent
curl http://localhost:8000/memory/stats | jq '.memory_per_agent'
```

## 🚨 Troubleshooting

### Common Issues

**Ollama Connection Failed**
```bash
# Check Ollama health
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama
```

**Agent Not Responding**
```bash
# Check agent status
curl http://localhost:8000/agents/agent_name

# Clear agent memory
curl -X DELETE http://localhost:8000/agents/agent_name/memory
```

**Memory Issues**
```bash
# Force cleanup
curl -X DELETE http://localhost:8000/memory/clear-all

# Check memory stats
curl http://localhost:8000/memory/stats
```

**Model Not Found**
```bash
# List available models
curl http://localhost:8000/models

# Pull specific model
docker exec -it agentic_ai_framework_ollama_1 ollama pull granite3.2:2b
```

## 📋 Use Cases

### 🌐 Website Monitoring
- Monitor critical websites 24/7
- Automatic email/SMS alerts
- Response time tracking
- Content verification

### 📧 Email Automation
- Automated customer responses
- Alert notifications
- Newsletter management
- Support ticket routing

### 🔍 Data Processing
- Document analysis
- API integrations
- Data validation
- Report generation

### 🤖 Chatbots & Assistants
- Customer support bots
- Internal help desks
- Task automation
- Information retrieval

### 📊 Business Intelligence
- Automated reporting
- Data analysis
- Trend monitoring
- KPI tracking

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for classes and methods
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Ollama](https://ollama.ai/) for local LLM capabilities
- [SQLAlchemy](https://www.sqlalchemy.org/) for robust database management
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/yourusername/agentic-ai-framework/issues)
- 💬 [Discussions](https://github.com/yourusername/agentic-ai-framework/discussions)
- 📧 Email: support@yourcompany.com

---

**Ready to build intelligent automation? Start with the Quick Start guide above! 🚀**