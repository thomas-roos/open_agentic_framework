# Agentic AI Framework

A powerful framework for creating and managing AI agents with natural language processing capabilities.

## Quick Start

```bash
# Deploy with Docker
./deploy.sh

# Access API documentation
open http://localhost:8000/docs
```

## Features

- 🤖 AI Agents with natural language processing
- 🔧 Extensible tool system
- 📋 Workflow orchestration
- ⏰ Task scheduling
- 🌐 Website monitoring
- 📧 Email alerts
- 🐳 Docker ready

## Documentation

- [Quick Start Guide](QUICK_START.md)
- [User Manual](USER_MANUAL.md)  
- [Developer Guide](DEVELOPER_MANUAL.md)

## Example: Website Monitoring

Create an agent that monitors websites and sends email alerts:

```bash
# Create monitoring agent
curl -X POST "http://localhost:8000/agents" -H "Content-Type: application/json" -d '{
  "name": "website_monitor",
  "role": "Website Monitor",
  "goals": "Monitor websites and send alerts",
  "backstory": "Experienced system administrator",
  "tools": ["website_monitor", "email_sender"]
}'

# Monitor a website
curl -X POST "http://localhost:8000/agents/website_monitor/execute" -H "Content-Type: application/json" -d '{
  "task": "Check if https://example.com is online and send alert if down"
}'
```

## Architecture

- **FastAPI**: REST API framework
- **Ollama**: Local LLM integration
- **SQLite**: Persistent storage
- **Docker**: Containerization
- **Tools**: Extensible plugin system

## License

MIT License
