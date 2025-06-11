# Quick Start Guide - Agentic AI Framework

Get your **multi-provider AI agent framework** running in **10 minutes** with this step-by-step guide!

## What You'll Build

By the end of this guide, you'll have:
- A running AI agent framework with **multi-provider LLM support**
- A website monitoring agent that can check if sites are online
- An automated workflow with **intelligent variable resolution**
- A scheduled task that runs monitoring every 5 minutes
- **Model warmup system** for instant responses

## Prerequisites (2 minutes)

**What you need:**
- Docker and Docker Compose installed
- 4GB+ available RAM
- Internet connection
- A terminal/command prompt
- API keys for additional providers (optional)

**Don't have Docker?** Install it quickly:
- **Windows/Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**: `curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh`

## Step 1: Get the Framework Running (3 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/agentic-ai-framework.git
cd agentic-ai-framework

# 2. Start the framework (this downloads models automatically)
docker-compose up -d

# 3. Wait for the models to download (grab a coffee)
# This takes 3-5 minutes depending on your internet speed
docker-compose logs -f model-downloader
```

**While waiting**, the framework is downloading these AI models:
- `granite3.2:2b` (700MB) - Your main AI brain
- `deepseek-r1:1.5b` (1.1GB) - For reasoning and tool usage
- `tinyllama:1.1b` (637MB) - Lightweight backup model

**Success indicators:**
- No error messages in the logs
- Models downloaded successfully
- All containers running
- Model warmup system activated

## Step 2: Verify Everything Works (1 minute)

```bash
# Check comprehensive system health
curl http://localhost:8000/health

# Should return something like:
# {
#   "status": "healthy",
#   "timestamp": "2024-06-05T14:30:00Z",
#   "providers": {
#     "ollama": true
#   },
#   "memory_entries": 0,
#   "warmup_stats": {
#     "active_models": 3,
#     "total_models": 3,
#     "success_rate": 100.0
#   }
# }

# Check available AI models across all providers
curl http://localhost:8000/models/detailed

# Check provider status
curl http://localhost:8000/providers
```

**Access the interactive docs:**
Open your browser and go to: **http://localhost:8000/docs**

This gives you a complete interactive interface to test all API endpoints with **live examples**!

## Step 3: Create Your First AI Agent (2 minutes)

Let's create a website monitoring agent with **tool configuration**:

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_guardian",
    "role": "Website Monitoring Specialist",
    "goals": "Monitor websites and report their status accurately with detailed analysis",
    "backstory": "You are an experienced system administrator who specializes in monitoring web services. You check websites systematically and provide clear status reports with performance analysis.",
    "tools": ["website_monitor"],
    "ollama_model": "granite3.2:2b",
    "enabled": true
  }'
```

**Expected response:**
```json
{
  "id": 1,
  "name": "website_guardian", 
  "message": "Agent created successfully"
}
```

## Step 4: Test Your Agent (1 minute)

Now let's test our agent with **intelligent analysis**:

```bash
curl -X POST "http://localhost:8000/agents/website_guardian/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://google.com is online and provide a detailed analysis including response time, status, and any performance concerns",
    "context": {}
  }'
```

**Expected response (after ~5-15 seconds thanks to warmup):**
```json
{
  "agent_name": "website_guardian",
  "task": "Check if https://google.com is online...", 
  "result": "I checked https://google.com and it is online. The website responded with HTTP status 200 in 156ms. Performance is excellent - response time is well within acceptable limits (<1000ms). The website is functioning normally with no issues detected.",
  "timestamp": "2024-06-05T14:35:00Z"
}
```

**Congratulations!** Your AI agent just:
1. **Understood** your request with natural language
2. **Used tools** to check the website
3. **Analyzed performance** with intelligent assessment
4. **Reported back** with detailed, actionable insights

## Step 5: Create an Advanced Workflow with Variable Resolution (2 minutes)

Let's create a workflow with **intelligent variable substitution**:

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "intelligent_site_monitor",
    "description": "Advanced website monitoring with variable resolution",
    "steps": [
      {
        "type": "tool",
        "name": "website_monitor",
        "parameters": {
          "url": "{{target_url}}",
          "expected_status": 200,
          "timeout": 10
        },
        "context_key": "primary_status"
      },
      {
        "type": "tool", 
        "name": "website_monitor",
        "parameters": {
          "url": "{{backup_url}}",
          "expected_status": 200,
          "timeout": 10
        },
        "context_key": "backup_status"
      },
      {
        "type": "agent",
        "name": "website_guardian",
        "task": "Analyze these monitoring results: Primary site {{target_url}} status: {{primary_status.status}} with {{primary_status.response_time}}ms response. Backup site {{backup_url}} status: {{backup_status.status}} with {{backup_status.response_time}}ms response. Provide comprehensive analysis and recommendations.",
        "context_key": "comprehensive_analysis"
      }
    ],
    "enabled": true
  }'
```

**Test the workflow with context variables:**
```bash
curl -X POST "http://localhost:8000/workflows/intelligent_site_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "target_url": "https://google.com",
      "backup_url": "https://github.com"
    }
  }'
```

**What happens:**
1. Checks Google.com status with variables
2. Checks GitHub.com status with variables  
3. AI agent analyzes both results using **nested variable access**
4. Provides intelligent comparative analysis

## Step 6: Schedule Automated Monitoring (1 minute)

Let's schedule our workflow to run automatically every 5 minutes:

```bash
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "workflow",
    "workflow_name": "intelligent_site_monitor", 
    "scheduled_time": "2024-12-20T10:00:00Z",
    "context": {
      "recurring": "every_5_minutes",
      "target_url": "https://google.com",
      "backup_url": "https://github.com",
      "description": "Automated intelligent website monitoring"
    }
  }'
```

**Result:** Your workflow now runs automatically every 5 minutes with intelligent analysis!

## Success! What You've Accomplished

In just 10 minutes, you've built a sophisticated AI automation system:

### **AI Agent Created**
- Smart website monitoring specialist
- Natural language understanding
- Tool integration capabilities
- Intelligent performance analysis

### **Advanced Workflow** 
- Multiple website monitoring simultaneously
- **Variable substitution** with `{{variable}}` syntax
- **Nested object access** like `{{status.response_time}}`
- Intelligent comparative analysis

### **Scheduled Automation**
- Runs monitoring every 5 minutes automatically
- Completely hands-off operation
- Scales to monitor dozens of websites
- **Model warmup** ensures instant responses

### **Production-Ready Features**
- **Multi-provider LLM support** (Ollama, OpenAI, OpenRouter)
- **Intelligent memory management** with context filtering
- **Model warmup system** for optimal performance
- **Enhanced error handling** and recovery
- **Complete REST API** with interactive documentation
- **Docker-based deployment** for easy scaling

## Next Steps - Level Up Your Setup

### **Explore the Interactive Docs**
Visit **http://localhost:8000/docs** to:
- Test all API endpoints interactively
- See request/response examples
- Generate code snippets for your language
- Explore the multi-provider system

### **Add Multi-Provider Support**
Enable additional LLM providers:

<details>
<summary>Click to expand multi-provider setup</summary>

```bash
# Stop the framework
docker-compose down

# Edit environment file
nano .env

# Add these lines to enable OpenAI:
OPENAI_ENABLED=true
OPENAI_API_KEY=your-openai-api-key
OPENAI_DEFAULT_MODEL=gpt-3.5-turbo

# Restart framework
docker-compose up -d

# Test OpenAI integration
curl -X POST "http://localhost:8000/models/test/gpt-3.5-turbo"

# Create agent with OpenAI model
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gpt_analyst",
    "role": "Advanced Data Analyst",
    "goals": "Provide sophisticated analysis using GPT models",
    "backstory": "Expert analyst with access to cutting-edge AI models",
    "tools": ["http_client"],
    "ollama_model": "gpt-3.5-turbo",
    "enabled": true
  }'
```

</details>

### **Add Email Alerts**
Want to get notified when websites go down?

<details>
<summary>Click to expand email setup</summary>

```bash
# Update your agent with email capabilities
curl -X PUT "http://localhost:8000/agents/website_guardian" \
  -H "Content-Type: application/json" \
  -d '{
    "tools": ["website_monitor", "email_sender"],
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

# Test email alert
curl -X POST "http://localhost:8000/agents/website_guardian/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check https://httpbin.org/status/500 and if it has any issues, send an email alert to admin@yourcompany.com with the details",
    "context": {}
  }'
```

</details>

### **Monitor Complex Scenarios**

<details>
<summary>Click to expand advanced monitoring</summary>

```bash
# Create an advanced API monitoring agent
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api_monitor",
    "role": "API Health Monitor",
    "goals": "Monitor API endpoints and detect performance issues with intelligent analysis",
    "backstory": "Expert in API monitoring with deep understanding of web service performance metrics and SLA requirements",
    "tools": ["website_monitor", "http_client"],
    "ollama_model": "deepseek-r1:1.5b"
  }'

# Create workflow with nested variable access
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api_health_check",
    "steps": [
      {
        "type": "tool",
        "name": "http_client",
        "parameters": {
          "url": "{{api_endpoint}}/health",
          "method": "GET",
          "headers": {"Authorization": "Bearer {{api_token}}"}
        },
        "context_key": "health_response"
      },
      {
        "type": "agent",
        "name": "api_monitor",
        "task": "Analyze API health response: Status {{health_response.status}}, Response time {{health_response.response_time}}ms, Body: {{health_response.data}}. Determine if API is healthy and performing within SLA."
      }
    ]
  }'
```

</details>

### **Scale to Production**
Ready for production? Check out:
- **[Production Deployment Guide](PRODUCTION.md)** - Deploy to DigitalOcean for $24/month
- **[Complete README](README.md)** - Full feature documentation
- **[Workflow Examples](README.md#creating-workflows)** - Advanced automation patterns

## Quick Reference Commands

```bash
# Check comprehensive system health
curl http://localhost:8000/health

# List all agents
curl http://localhost:8000/agents

# Check provider status
curl http://localhost:8000/providers

# List all workflows  
curl http://localhost:8000/workflows

# Check memory usage with statistics
curl http://localhost:8000/memory/stats

# Test specific model
curl -X POST "http://localhost:8000/models/test/granite3.2:2b"

# View logs
docker-compose logs -f

# Restart everything
docker-compose restart
```

## Troubleshooting

**Agent not responding?**
```bash
# Check if models loaded properly
curl http://localhost:8000/models/detailed

# Check provider health
curl http://localhost:8000/providers

# View recent logs
docker-compose logs --tail=50 agentic-ai
```

**Website monitoring failing?**
```bash
# Test the tool directly
curl -X POST "http://localhost:8000/tools/website_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "url": "https://google.com",
      "expected_status": 200
    }
  }'
```

**Model warmup issues?**
```bash
# Check warmup status
curl http://localhost:8000/health | jq '.warmup_stats'

# Check which models are active
curl http://localhost:8000/models/detailed
```

**Out of memory?**
```bash
# Check memory statistics
curl http://localhost:8000/memory/stats

# Clear agent memory intelligently
curl -X POST "http://localhost:8000/memory/cleanup"

# Check Docker resources
docker stats
```

## What's Next?

You now have a powerful AI automation framework with **multi-provider support**! Here are some ideas:

1. **Website Monitoring** - Monitor your business-critical websites
2. **Email Automation** - Automated customer service responses  
3. **Data Processing** - Automated report generation with multiple models
4. **Smart Alerts** - Intelligent notification systems
5. **Multi-Agent Systems** - Agents that work together across providers

**Ready to build something amazing?** The framework gives you the building blocks - now let your creativity run wild!

---

**Tip**: Bookmark **http://localhost:8000/docs** - it's your command center for building AI automation with multi-provider support!