# Multi-Agent System Deployment Guide

## Features

✅ **Long-term Memory**: SQLite-based memory system with importance scoring and retrieval  
✅ **Scheduled Execution**: Cron-based task scheduling with retry logic  
✅ **REST API**: Complete HTTP API for all agent operations  
✅ **Multiple Agents**: Specialized agents for different domains  
✅ **Tool Integration**: Comprehensive tool registry with safety checks  
✅ **Workflow Engine**: Predefined and custom workflows  
✅ **Lightweight LLM**: Uses Ollama with llama3.2:1b model  

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd multi-agent-system
```

### 2. Build and Run with Docker

```bash
# Build the image
docker-compose build

# Start the system
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 3. Verify Installation

```bash
# Check health
curl http://localhost:8080/health

# List agents
curl http://localhost:8080/agents
```

## Directory Structure

```
multi-agent-system/
├── memory/
│   ├── __init__.py
│   └── memory_system.py
├── scheduler/
│   ├── __init__.py
│   └── scheduler_system.py
├── agents/
│   ├── __init__.py
│   └── agent_system.py
├── api/
│   ├── __init__.py
│   └── rest_server.py
├── docker/
│   └── start.sh
├── data/
├── logs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── main.py
```

## API Usage Examples

### Execute Tasks

```bash
# Simple task execution
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Analyze the sales data from last quarter",
    "agent_name": "dataagent",
    "priority": 1
  }'

# Workflow execution
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a web application for inventory management",
    "workflow_name": "software_development",
    "priority": 2
  }'

# Check task status
curl http://localhost:8080/tasks/{task_id}
```

### Chat with Agents

```bash
# Chat with specific agent
curl -X POST http://localhost:8080/agents/dataagent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "dataagent",
    "message": "What are the best practices for data visualization?",
    "context": {"topic": "data_science"}
  }'
```

### Memory Operations

```bash
# Store memory
curl -X POST http://localhost:8080/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "dataagent",
    "content": "PostgreSQL is excellent for OLTP workloads",
    "memory_type": "knowledge",
    "tags": ["database", "postgresql", "performance"]
  }'

# Query memory
curl -X POST http://localhost:8080/memory/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database performance",
    "agent_name": "dataagent",
    "limit": 5
  }'

# Get memory stats
curl http://localhost:8080/memory/stats/dataagent
```

### Scheduled Tasks

```bash
# Schedule daily task
curl -X POST http://localhost:8080/schedule/task \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily_backup",
    "description": "Perform daily database backup",
    "agent_name": "systemagent",
    "schedule_type": "cron",
    "schedule_expression": "0 2 * * *",
    "task_payload": {
      "description": "Run database backup script",
      "metadata": {"backup_type": "daily"}
    }
  }'

# Schedule one-time task
curl -X POST http://localhost:8080/schedule/task \
  -H "Content-Type: application/json" \
  -d '{
    "name": "maintenance_window",
    "description": "System maintenance",
    "agent_name": "systemagent",
    "schedule_type": "once",
    "schedule_expression": "2024-12-25T02:00:00",
    "task_payload": {
      "description": "Perform system maintenance during low traffic"
    }
  }'

# List scheduled tasks
curl http://localhost:8080/schedule/tasks

# Pause/resume tasks
curl -X PUT http://localhost:8080/schedule/tasks/{task_id}/pause
curl -X PUT http://localhost:8080/schedule/tasks/{task_id}/resume
```

### System Information

```bash
# System statistics
curl http://localhost:8080/system/stats

# Available workflows
curl http://localhost:8080/workflows

# List all tasks
curl http://localhost:8080/tasks?limit=20
```

## Agent Capabilities

### PlannerAgent
- Task decomposition
- Workflow planning  
- Resource allocation
- Strategic thinking

### DataAgent
- Data analysis
- Statistical processing
- File operations
- Data visualization

### CodeAgent
- Code generation
- Debugging
- Architecture design
- Testing

### ResearchAgent
- Information gathering
- Document analysis
- Fact checking
- Trend analysis

### SystemAgent
- Command execution
- Infrastructure management
- Security analysis
- Performance optimization

## Configuration

### Environment Variables

```bash
PYTHONPATH=/app
OLLAMA_HOST=0.0.0.0:11434
API_HOST=0.0.0.0
API_PORT=8080
LOG_LEVEL=INFO
MODEL_NAME=llama3.2:1b
```

### Model Configuration

The system uses `llama3.2:1b` by default for lightweight operation. To use a different model:

1. Pull the model: `docker exec -it multi-agent-system ollama pull llama3.2:3b`
2. Update environment variable: `MODEL_NAME=llama3.2:3b`
3. Restart: `docker-compose restart`

### Memory Configuration

- **Database**: SQLite (for development) or PostgreSQL (for production)
- **Retention**: Configurable memory consolidation rules
- **Importance Scoring**: Automatic importance calculation

### Scheduler Configuration

- **Backend**: SQLite with cron expressions
- **Retry Logic**: Exponential backoff with max retries
- **Monitoring**: Execution history and statistics

## Production Deployment

### Security Considerations

1. **API Authentication**: Implement proper JWT/OAuth
2. **Network Security**: Use HTTPS and firewalls
3. **Data Encryption**: Encrypt sensitive memory data
4. **Command Safety**: Review system command restrictions

### Scaling Options

1. **Horizontal Scaling**: Multiple agent containers
2. **Database Scaling**: Move to PostgreSQL cluster
3. **Load Balancing**: Nginx/HAProxy for API endpoints
4. **Resource Monitoring**: Prometheus + Grafana

### Production Docker Compose

```yaml
version: '3.8'
services:
  multi-agent-system:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/agents
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: agents
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - multi-agent-system

volumes:
  postgres_data:
```

## Advanced Usage Examples

### Python Client Example

```python
import requests
import asyncio
import aiohttp

class MultiAgentClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    async def execute_task(self, description, agent_name=None, workflow_name=None):
        """Execute a task and wait for completion"""
        payload = {"description": description}
        if agent_name:
            payload["agent_name"] = agent_name
        if workflow_name:
            payload["workflow_name"] = workflow_name
        
        async with aiohttp.ClientSession() as session:
            # Submit task
            async with session.post(f"{self.base_url}/tasks", json=payload) as resp:
                task_data = await resp.json()
                task_id = task_data["task_id"]
            
            # Poll for completion
            while True:
                async with session.get(f"{self.base_url}/tasks/{task_id}") as resp:
                    result = await resp.json()
                    if result["status"] in ["completed", "failed"]:
                        return result
                await asyncio.sleep(2)
    
    async def chat_with_agent(self, agent_name, message, context=None):
        """Have a conversation with an agent"""
        payload = {
            "agent_name": agent_name,
            "message": message,
            "context": context or {}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/agents/{agent_name}/chat", json=payload) as resp:
                return await resp.json()

# Usage example
async def main():
    client = MultiAgentClient()
    
    # Execute a data analysis task
    result = await client.execute_task(
        "Analyze website traffic patterns for the last month",
        agent_name="dataagent"
    )
    print(f"Analysis complete: {result['result']}")
    
    # Chat with the research agent
    response = await client.chat_with_agent(
        "researchagent",
        "What are the latest trends in AI?"
    )
    print(f"Research agent: {response['response']}")

asyncio.run(main())
```

### JavaScript/Node.js Client Example

```javascript
class MultiAgentClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
    }
    
    async executeTask(description, options = {}) {
        const payload = { description, ...options };
        
        // Submit task
        const taskResponse = await fetch(`${this.baseUrl}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const taskData = await taskResponse.json();
        const taskId = taskData.task_id;
        
        // Poll for completion
        while (true) {
            const statusResponse = await fetch(`${this.baseUrl}/tasks/${taskId}`);
            const result = await statusResponse.json();
            
            if (['completed', 'failed'].includes(result.status)) {
                return result;
            }
            
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
    
    async scheduleTask(name, description, agentName, cronExpression) {
        const payload = {
            name,
            description,
            agent_name: agentName,
            schedule_type: 'cron',
            schedule_expression: cronExpression,
            task_payload: { description }
        };
        
        const response = await fetch(`${this.baseUrl}/schedule/task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        return await response.json();
    }
}

// Usage
const client = new MultiAgentClient();

// Execute workflow
client.executeTask(
    'Create a REST API for user management',
    { workflow_name: 'software_development' }
).then(result => {
    console.log('Development complete:', result.summary);
});

// Schedule daily report
client.scheduleTask(
    'daily_report',
    'Generate daily performance report',
    'dataagent',
    '0 8 * * *'  // Every day at 8 AM
).then(response => {
    console.log('Scheduled:', response.task_id);
});
```

## Workflow Customization

### Creating Custom Workflows

```python
# Add to main.py or create workflow_definitions.py

custom_workflows = {
    "ml_pipeline": {
        "description": "Machine learning pipeline",
        "agents": ["dataagent", "codeagent", "systemagent"],
        "steps": [
            {
                "agent": "dataagent",
                "task": "Prepare and clean training data",
                "depends_on": []
            },
            {
                "agent": "codeagent", 
                "task": "Implement ML model and training script",
                "depends_on": [0]
            },
            {
                "agent": "dataagent",
                "task": "Train and evaluate model",
                "depends_on": [1]
            },
            {
                "agent": "systemagent",
                "task": "Deploy model to production",
                "depends_on": [2]
            }
        ]
    },
    
    "security_audit": {
        "description": "Security audit workflow",
        "agents": ["systemagent", "codeagent", "researchagent"],
        "steps": [
            {
                "agent": "systemagent",
                "task": "Scan system for vulnerabilities",
                "depends_on": []
            },
            {
                "agent": "codeagent",
                "task": "Review code for security issues",
                "depends_on": []
            },
            {
                "agent": "researchagent",
                "task": "Research latest security threats",
                "depends_on": []
            },
            {
                "agent": "systemagent",
                "task": "Generate security report and recommendations",
                "depends_on": [0, 1, 2]
            }
        ]
    }
}

# Add to orchestrator
orchestrator.workflows.update(custom_workflows)
```

### Dynamic Workflow API

```bash
# Register new workflow via API (future enhancement)
curl -X POST http://localhost:8080/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_analysis",
    "description": "Custom data analysis workflow",
    "steps": [
      {
        "agent": "dataagent",
        "task": "Load data from source",
        "depends_on": []
      },
      {
        "agent": "researchagent",
        "task": "Analyze trends and patterns", 
        "depends_on": [0]
      }
    ]
  }'
```

## Monitoring and Debugging

### Health Monitoring

```bash
#!/bin/bash
# monitoring/health_check.sh

API_URL="http://localhost:8080"

# Check API health
if curl -f $API_URL/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "❌ API is down"
    exit 1
fi

# Check agent performance
STATS=$(curl -s $API_URL/system/stats)
ACTIVE_TASKS=$(echo $STATS | jq '.tasks.active')
SCHEDULER_RUNNING=$(echo $STATS | jq '.scheduler.scheduler_running')

echo "Active tasks: $ACTIVE_TASKS"
echo "Scheduler running: $SCHEDULER_RUNNING"

# Check memory usage
TOTAL_MEMORIES=$(echo $STATS | jq '.memory.total_memories')
echo "Total memories: $TOTAL_MEMORIES"

# Alert if too many failed tasks
FAILED_EXECUTIONS=$(echo $STATS | jq '.scheduler.failed_executions')
if [ "$FAILED_EXECUTIONS" -gt 10 ]; then
    echo "⚠️  High number of failed executions: $FAILED_EXECUTIONS"
fi
```

### Log Analysis

```bash
# View real-time logs
docker-compose logs -f multi-agent-system

# Search for specific patterns
docker-compose logs multi-agent-system | grep "ERROR"
docker-compose logs multi-agent-system | grep "Task.*completed"

# Memory usage analysis
docker-compose logs multi-agent-system | grep "memory" | tail -20
```

### Performance Metrics

```python
# performance_monitor.py
import asyncio
import aiohttp
import time
from datetime import datetime

async def monitor_performance():
    """Monitor system performance metrics"""
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Get system stats
                async with session.get('http://localhost:8080/system/stats') as resp:
                    stats = await resp.json()
                
                print(f"\n=== Performance Report {datetime.now()} ===")
                print(f"Active tasks: {stats['tasks']['active']}")
                print(f"Completed tasks: {stats['tasks']['completed']}")
                print(f"Total memories: {stats['memory']['total_memories']}")
                print(f"Scheduler running: {stats['scheduler']['scheduler_running']}")
                
                # Agent performance
                for agent_name, perf in stats['agents']['performance'].items():
                    success_rate = perf['performance']['success_rate_percent']
                    avg_time = perf['performance']['average_response_time']
                    print(f"{agent_name}: {success_rate}% success, {avg_time:.2f}s avg")
                
            except Exception as e:
                print(f"Monitoring error: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    asyncio.run(monitor_performance())
```

## Troubleshooting

### Common Issues

1. **Ollama not starting**
   ```bash
   # Check Ollama status
   docker exec -it multi-agent-system ollama list
   
   # Restart Ollama
   docker exec -it multi-agent-system pkill ollama
   docker-compose restart
   ```

2. **Model not found**
   ```bash
   # Pull model manually
   docker exec -it multi-agent-system ollama pull llama3.2:1b
   ```

3. **Memory issues**
   ```bash
   # Check database size
   docker exec -it multi-agent-system ls -la /app/memory/
   
   # Clear old memories
   curl -X POST http://localhost:8080/memory/cleanup \
     -H "Content-Type: application/json" \
     -d '{"older_than_days": 30, "importance_below": 0.3}'
   ```

4. **High resource usage**
   ```bash
   # Monitor resource usage
   docker stats multi-agent-system
   
   # Reduce concurrent tasks
   # Edit docker-compose.yml to limit CPU/memory
   ```

### Debug Mode

```bash
# Enable debug logging
docker-compose up -d
docker exec -it multi-agent-system python -c "
import logging
logging.getLogger().setLevel(logging.DEBUG)
"

# Or set environment variable
docker-compose down
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose up -d
```

## Contributing

### Development Setup

```bash
# Development environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Run tests
pytest tests/

# Format code
black .

# Type checking
mypy .
```

### Testing

```python
# tests/test_agents.py
import pytest
from agents.agent_system import DataAgent, Task

@pytest.mark.asyncio
async def test_data_agent():
    agent = DataAgent()
    task = Task(
        id="test_1",
        description="Analyze sample data",
        agent="dataagent"
    )
    
    result = await agent.process_task(task)
    assert isinstance(result, str)
    assert len(result) > 0

# Run specific tests
pytest tests/test_agents.py::test_data_agent -v
```

This comprehensive system provides:

- ✅ **Long-term memory** with SQLite storage and importance scoring
- ✅ **Cron scheduling** with retry logic and execution tracking  
- ✅ **Complete REST API** for all operations
- ✅ **Modular architecture** with specialized agents
- ✅ **Tool integration** with safety checks
- ✅ **Docker deployment** with lightweight LLM
- ✅ **Production-ready** monitoring and error handling

The system is designed to run efficiently on modest hardware while providing enterprise-grade features for agent coordination and task execution.