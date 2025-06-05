# Agentic AI Framework - User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Creating Agents](#creating-agents)
4. [Using Tools](#using-tools)
5. [Building Workflows](#building-workflows)
6. [Scheduling Tasks](#scheduling-tasks)
7. [Website Monitoring Example](#website-monitoring-example)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

## Introduction

The Agentic AI Framework is a powerful system for creating and managing AI agents that can perform complex tasks using natural language processing and tool integration. The framework allows you to:

- **Create AI Agents**: Define agents with specific roles, goals, and capabilities
- **Integrate Tools**: Use built-in tools or create custom ones for specific tasks
- **Build Workflows**: Chain agents and tools together in complex sequences
- **Schedule Tasks**: Automate agent and workflow execution
- **Monitor Systems**: Track website availability and system health

## Quick Start

### 1. Installation and Setup

Using Docker (Recommended):
```bash
# Clone the repository
git clone <repository-url>
cd agentic_ai_framework

# Start the services
docker-compose up -d

# Install the LLM model
docker exec -it agentic_ai_framework_ollama_1 ollama pull llama3

# Access the API documentation
open http://localhost:8000/docs
```

### 2. Your First Agent

Create a simple assistant agent:

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "assistant",
    "role": "General Assistant",
    "goals": "Help users with various tasks and questions",
    "backstory": "You are a helpful AI assistant with access to various tools",
    "tools": ["http_client", "website_monitor"],
    "enabled": true
  }'
```

### 3. Execute Your First Task

```bash
curl -X POST "http://localhost:8000/agents/assistant/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if google.com is online",
    "context": {}
  }'
```

## Creating Agents

Agents are the core entities that perform tasks in the framework. Each agent has:

- **Name**: Unique identifier
- **Role**: What the agent does
- **Goals**: What the agent aims to achieve
- **Backstory**: Background information for context
- **Tools**: List of tools the agent can use
- **Configuration**: Tool-specific settings

### Agent Definition Example

```json
{
  "name": "website_monitor_agent",
  "role": "Website Monitoring Specialist",
  "goals": "Monitor website availability and notify administrators of issues",
  "backstory": "You are an experienced system administrator responsible for monitoring critical websites and services. You check websites regularly and send alerts when problems are detected.",
  "tools": ["website_monitor", "email_sender"],
  "ollama_model": "llama3",
  "enabled": true,
  "tool_configs": {
    "email_sender": {
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "smtp_username": "alerts@yourcompany.com",
      "smtp_password": "your-app-password",
      "from_email": "alerts@yourcompany.com"
    }
  }
}
```

### Creating an Agent via API

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d @agent_definition.json
```

## Using Tools

Tools extend agent capabilities. The framework includes several built-in tools:

### Built-in Tools

1. **website_monitor**: Check website availability
2. **email_sender**: Send emails via SMTP
3. **http_client**: Make HTTP requests

### Tool Configuration

Tools can be configured per agent using the `tool_configs` field:

```json
{
  "tool_configs": {
    "email_sender": {
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "smtp_username": "your-email@gmail.com",
      "smtp_password": "your-app-password"
    },
    "http_client": {
      "api_key": "your-api-key",
      "api_key_header": "X-API-Key"
    }
  }
}
```

### Using Tools in Agent Tasks

Agents automatically determine when to use tools based on the task:

```bash
curl -X POST "http://localhost:8000/agents/website_monitor_agent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://example.com is online and send an email alert if it is down",
    "context": {
      "alert_email": "admin@yourcompany.com"
    }
  }'
```

## Building Workflows

Workflows chain multiple agents and tools together for complex automation:

### Workflow Structure

```json
{
  "name": "website_monitoring_workflow",
  "description": "Monitor multiple websites and send consolidated reports",
  "steps": [
    {
      "type": "tool",
      "name": "website_monitor",
      "parameters": {
        "url": "https://example.com",
        "timeout": 10
      },
      "context_key": "site1_status"
    },
    {
      "type": "tool",
      "name": "website_monitor",
      "parameters": {
        "url": "https://api.example.com",
        "timeout": 5
      },
      "context_key": "api_status"
    },
    {
      "type": "agent",
      "name": "website_monitor_agent",
      "task": "Analyze the monitoring results and send a summary report. Site 1 status: {site1_status}, API status: {api_status}",
      "context_key": "report"
    }
  ],
  "enabled": true
}
```

### Creating a Workflow

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d @workflow_definition.json
```

### Executing a Workflow

```bash
curl -X POST "http://localhost:8000/workflows/website_monitoring_workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "report_email": "team@yourcompany.com"
    }
  }'
```

## Scheduling Tasks

Automate agent and workflow execution with the scheduler:

### Schedule an Agent Task

```bash
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent",
    "agent_name": "website_monitor_agent",
    "task_description": "Check all critical websites and send alerts if any are down",
    "scheduled_time": "2024-01-15T10:00:00Z",
    "context": {
      "check_interval": "hourly"
    }
  }'
```

### Schedule a Workflow

```bash
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "workflow",
    "workflow_name": "website_monitoring_workflow",
    "scheduled_time": "2024-01-15T09:00:00Z",
    "context": {
      "daily_report": true
    }
  }'
```

## Website Monitoring Example

Here's a complete example that monitors a website and sends email alerts when it's down:

### Step 1: Create the Monitoring Agent

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_guardian",
    "role": "Website Monitoring Guardian",
    "goals": "Ensure critical websites are always online and notify immediately when issues are detected",
    "backstory": "You are a vigilant system monitor with years of experience in maintaining high-availability systems. You understand the importance of rapid response to outages.",
    "tools": ["website_monitor", "email_sender"],
    "ollama_model": "llama3",
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
```

### Step 2: Create the Monitoring Workflow

```bash
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
          "expected_status": 200,
          "check_content": "Welcome"
        },
        "context_key": "website_status"
      },
      {
        "type": "agent",
        "name": "website_guardian",
        "task": "Analyze the website monitoring result: {website_status}. If the website is down or has issues, send an immediate email alert to admin@yourcompany.com with details about the problem. Include the status, response time, and any errors detected.",
        "context_key": "alert_result"
      }
    ],
    "enabled": true
  }'
```

### Step 3: Schedule Regular Monitoring

```bash
# Schedule the monitoring to run every 5 minutes
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "workflow",
    "workflow_name": "website_health_check",
    "scheduled_time": "2024-01-15T10:00:00Z",
    "context": {
      "monitoring_frequency": "every_5_minutes",
      "alert_email": "admin@yourcompany.com"
    }
  }'
```

### Step 4: Manual Test

Test the monitoring immediately:

```bash
curl -X POST "http://localhost:8000/workflows/website_health_check/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "test_run": true,
      "alert_email": "admin@yourcompany.com"
    }
  }'
```

### Expected Behavior

When the website is **online**:
- The agent receives a positive status report
- No email alert is sent
- Success is logged

When the website is **down**:
- The agent detects the failure
- An email alert is automatically sent to admin@yourcompany.com
- The email includes:
  - Website URL
  - Error details (timeout, HTTP error, etc.)
  - Timestamp of the failure
  - Response time information

## API Reference

### Agents Endpoints

- `POST /agents` - Create a new agent
- `GET /agents` - List all agents
- `GET /agents/{name}` - Get agent details
- `PUT /agents/{name}` - Update an agent
- `DELETE /agents/{name}` - Delete an agent
- `POST /agents/{name}/execute` - Execute agent task
- `GET /agents/{name}/memory` - Get agent conversation history

### Tools Endpoints

- `GET /tools` - List all available tools
- `GET /tools/{name}` - Get tool details
- `POST /tools/{name}/execute` - Execute a tool directly

### Workflows Endpoints

- `POST /workflows` - Create a new workflow
- `GET /workflows` - List all workflows
- `GET /workflows/{name}` - Get workflow details
- `PUT /workflows/{name}` - Update a workflow
- `DELETE /workflows/{name}` - Delete a workflow
- `POST /workflows/{name}/execute` - Execute a workflow

### Scheduling Endpoints

- `POST /schedule` - Schedule a task
- `GET /schedule` - List scheduled tasks
- `DELETE /schedule/{id}` - Delete a scheduled task

### Configuration Endpoints

- `GET /config` - Get current configuration
- `PUT /config` - Update configuration

### Health Check

- `GET /health` - Check system health
- `GET /` - Basic system information

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama instance URL |
| `DEFAULT_MODEL` | `llama3` | Default LLM model |
| `DATABASE_PATH` | `agentic_ai.db` | SQLite database path |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `MAX_AGENT_ITERATIONS` | `10` | Maximum agent reasoning iterations |
| `SCHEDULER_INTERVAL` | `60` | Scheduler check interval (seconds) |
| `TOOLS_DIRECTORY` | `tools` | Tools directory path |

### Email Configuration

For email functionality, configure these settings in agent `tool_configs`:

```json
{
  "email_sender": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "your-email@gmail.com",
    "smtp_password": "your-app-password",
    "smtp_use_tls": true,
    "from_email": "your-email@gmail.com"
  }
}
```

### Gmail Setup

1. Enable 2-factor authentication
2. Generate an app password
3. Use the app password in `smtp_password`

## Troubleshooting

### Common Issues

**1. Ollama Connection Failed**
```
Error: Failed to connect to Ollama
```
- Check if Ollama is running: `docker ps`
- Verify Ollama URL in configuration
- Pull required model: `ollama pull llama3`

**2. Email Sending Failed**
```
Error: SMTP authentication failed
```
- Verify SMTP credentials
- Check if 2FA is enabled (use app password)
- Confirm SMTP server settings

**3. Agent Not Responding**
```
Error: Agent reached maximum iterations
```
- Check agent configuration
- Verify tool availability
- Review agent memory for errors

**4. Tool Not Found**
```
Error: Tool 'tool_name' not found
```
- Check if tool is in tools directory
- Verify tool class inherits from BaseTool
- Restart the framework to reload tools

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Health Checks

Check system status:
```bash
curl http://localhost:8000/health
```

Check agent status:
```bash
curl http://localhost:8000/agents/agent_name
```

### Logs

View application logs:
```bash
docker logs agentic_ai_framework_agentic-ai_1
```

View Ollama logs:
```bash
docker logs agentic_ai_framework_ollama_1
```

### Support

For additional support:
1. Check the logs for detailed error messages
2. Verify configuration settings
3. Test components individually
4. Review the API documentation at `/docs`

## Best Practices

1. **Agent Design**: Keep agent roles focused and specific
2. **Tool Configuration**: Store sensitive credentials securely
3. **Workflow Testing**: Test workflows manually before scheduling
4. **Error Handling**: Include error handling in agent instructions
5. **Monitoring**: Regularly check system health and logs
6. **Security**: Use environment variables for sensitive data
7. **Performance**: Monitor agent iteration counts and response times