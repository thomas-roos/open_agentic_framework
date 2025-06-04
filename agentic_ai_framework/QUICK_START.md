# Quick Start Guide - Agentic AI Framework

## 🚀 Get Started in 5 Minutes

This guide will get you up and running with the Agentic AI Framework quickly.

## Prerequisites

- Docker and Docker Compose installed
- 4GB+ available RAM
- Internet connection for downloading models

## Option 1: Automatic Deployment (Recommended)

### 1. Clone and Deploy
```bash
# Clone the repository
git clone <repository-url>
cd agentic_ai_framework

# Make deployment script executable and run
chmod +x deploy.sh
./deploy.sh
```

The script will automatically:
- ✅ Check Docker installation
- ✅ Create necessary directories
- ✅ Build and start containers
- ✅ Download the LLM model
- ✅ Set up sample configurations

### 2. Access the Framework
Once deployment is complete:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Main API**: http://localhost:8000

## Option 2: Manual Setup

### 1. Environment Setup
```bash
# Copy environment configuration
cp .env.example .env

# Create data directories
mkdir -p data logs tools
```

### 2. Start Services
```bash
# Build and start with Docker Compose
docker-compose up -d

# Install the LLM model
docker exec -it agentic_ai_framework_ollama_1 ollama pull llama3
```

## Option 3: Development Setup

### 1. Python Environment
```bash
# Run setup script
chmod +x setup.sh
./setup.sh

# Or use Makefile
make setup
```

### 2. Start Development Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start the application
python main.py
```

## 🎯 Your First Website Monitor

Let's create a complete website monitoring system that checks if a website is online and sends email alerts when it's down.

### Step 1: Create the Monitoring Agent

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_guardian",
    "role": "Website Monitoring Specialist",
    "goals": "Monitor critical websites and send immediate alerts when issues are detected",
    "backstory": "You are an experienced system administrator responsible for ensuring high availability of critical web services.",
    "tools": ["website_monitor", "email_sender"],
    "enabled": true,
    "tool_configs": {
      "email_sender": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "your-email@gmail.com",
        "smtp_password": "your-app-password",
        "from_email": "Website Monitor <alerts@yourcompany.com>"
      }
    }
  }'
```

### Step 2: Test Website Monitoring

```bash
curl -X POST "http://localhost:8000/agents/website_guardian/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://google.com is online. If there are any issues, send an email alert to admin@yourcompany.com with details.",
    "context": {
      "alert_email": "admin@yourcompany.com",
      "website_url": "https://google.com"
    }
  }'
```

### Step 3: Create Automated Monitoring Workflow

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_health_check",
    "description": "Automated website monitoring with email alerts",
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
        "task": "Analyze the website monitoring result: {website_status}. If the website is down or has issues, send an immediate email alert to admin@yourcompany.com with full details about the problem including status code, response time, and error description.",
        "context_key": "alert_sent"
      }
    ],
    "enabled": true
  }'
```

### Step 4: Execute the Monitoring Workflow

```bash
curl -X POST "http://localhost:8000/workflows/website_health_check/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "admin_email": "admin@yourcompany.com"
    }
  }'
```

### Step 5: Schedule Regular Monitoring

```bash
# Schedule monitoring every 5 minutes
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "workflow",
    "workflow_name": "website_health_check",
    "scheduled_time": "2024-01-15T10:00:00Z",
    "context": {
      "recurring": "every_5_minutes"
    }
  }'
```

## 🔧 Configuration

### Email Setup (Gmail Example)

1. **Enable 2-Factor Authentication** in your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Use the app password** in your agent configuration

### Environment Variables

Create or edit `.env` file:
```bash
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=llama3

# API Configuration  
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_PATH=data/agentic_ai.db

# Agent Configuration
MAX_AGENT_ITERATIONS=10
SCHEDULER_INTERVAL=60
```

## 📊 Monitoring and Management

### Check System Health
```bash
curl http://localhost:8000/health
```

### View All Agents
```bash
curl http://localhost:8000/agents
```

### View Agent Memory
```bash
curl http://localhost:8000/agents/website_guardian/memory
```

### View Scheduled Tasks
```bash
curl http://localhost:8000/schedule
```

## 🐛 Troubleshooting

### Common Issues

**1. Ollama not responding**
```bash
# Check Ollama container
docker logs agentic_ai_framework_ollama_1

# Restart Ollama
docker-compose restart ollama
```

**2. Email sending fails**
```bash
# Check agent configuration
curl http://localhost:8000/agents/website_guardian

# Verify SMTP settings in tool_configs
```

**3. API not accessible**
```bash
# Check application logs
docker logs agentic_ai_framework_agentic-ai_1

# Check if port 8000 is available
lsof -i :8000
```

### Reset Everything
```bash
# Stop and remove all containers
docker-compose down -v

# Clean up
./deploy.sh clean

# Redeploy
./deploy.sh
```

## 🎨 What's Included

After setup, you'll have:

- ✅ **FastAPI Web Interface** at http://localhost:8000/docs
- ✅ **Ollama LLM Service** running locally
- ✅ **SQLite Database** for persistence
- ✅ **Website Monitor Tool** for checking site availability
- ✅ **Email Sender Tool** for notifications
- ✅ **HTTP Client Tool** for API interactions
- ✅ **Background Scheduler** for automation
- ✅ **Sample Agent** ready to use

## 🔄 Development Workflow

### Using Makefile (Recommended)
```bash
# Setup development environment
make setup

# Run in development mode
make run

# Run tests
make test

# Format code
make format

# Deploy to production
make deploy
```

### Manual Commands
```bash
# Development mode
source venv/bin/activate
python main.py

# Run tests
pytest tests/ -v

# Check logs
docker-compose logs -f
```

## 📚 Next Steps

1. **Explore the API Documentation**: http://localhost:8000/docs
2. **Read the User Manual**: Complete guide with examples
3. **Check the Developer Manual**: Learn to extend the framework
4. **Create Custom Tools**: Build your own integrations
5. **Join the Community**: Contribute and get support

## 🆘 Getting Help

- **Documentation**: Check the user manual and developer guide
- **Logs**: `docker-compose logs -f` for troubleshooting
- **Health Check**: http://localhost:8000/health
- **API Explorer**: http://localhost:8000/docs

---

🎉 **Congratulations!** You now have a fully functional AI agent framework with website monitoring capabilities. The agent can intelligently monitor websites and send email alerts when issues are detected.

Try modifying the monitoring parameters, adding more websites to monitor, or creating new agents with different capabilities!