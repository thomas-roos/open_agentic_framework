# 🚀 Quick Start Guide - Agentic AI Framework

Get your AI agent framework running in **10 minutes** with this step-by-step guide!

## ⚡ What You'll Build

By the end of this guide, you'll have:
- ✅ A running AI agent framework
- ✅ A website monitoring agent that can check if sites are online
- ✅ An automated workflow that monitors websites and sends alerts
- ✅ A scheduled task that runs monitoring every 5 minutes

## 📋 Prerequisites (2 minutes)

**What you need:**
- Docker and Docker Compose installed
- 4GB+ available RAM
- Internet connection
- A terminal/command prompt

**Don't have Docker?** Install it quickly:
- **Windows/Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**: `curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh`

## 🎯 Step 1: Get the Framework Running (3 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/agentic-ai-framework.git
cd agentic-ai-framework

# 2. Start the framework (this downloads models automatically)
docker-compose up -d

# 3. Wait for the models to download (grab a coffee ☕)
# This takes 3-5 minutes depending on your internet speed
docker-compose logs -f model-downloader
```

**⏳ While waiting**, the framework is downloading these AI models:
- `granite3.2:2b` (700MB) - Your main AI brain
- `deepseek-r1:1.5b` (1.1GB) - For reasoning and tool usage
- `tinyllama:1.1b` (637MB) - Lightweight backup model

**✅ Success indicators:**
- No error messages in the logs
- Models downloaded successfully
- All containers running

## 🎯 Step 2: Verify Everything Works (1 minute)

```bash
# Check system health
curl http://localhost:8000/health

# Should return something like:
# {
#   "status": "healthy",
#   "timestamp": "2024-06-05T14:30:00Z",
#   "ollama_status": true,
#   "memory_entries": 0
# }

# Check available AI models
curl http://localhost:8000/models

# Should return a list like:
# ["granite3.2:2b", "deepseek-r1:1.5b", "tinyllama:1.1b"]
```

**🌐 Access the interactive docs:**
Open your browser and go to: **http://localhost:8000/docs**

This gives you a complete interactive interface to test all API endpoints!

## 🎯 Step 3: Create Your First AI Agent (2 minutes)

Let's create a website monitoring agent that can check if websites are online:

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website_guardian",
    "role": "Website Monitoring Specialist",
    "goals": "Monitor websites and report their status accurately",
    "backstory": "You are an experienced system administrator who specializes in monitoring web services. You check websites systematically and provide clear status reports.",
    "tools": ["website_monitor"],
    "ollama_model": "granite3.2:2b",
    "enabled": true
  }'
```

**✅ Expected response:**
```json
{
  "id": 1,
  "name": "website_guardian", 
  "message": "Agent created successfully"
}
```

## 🎯 Step 4: Test Your Agent (1 minute)

Now let's test our agent by asking it to check if Google is online:

```bash
curl -X POST "http://localhost:8000/agents/website_guardian/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://google.com is online and tell me the response time",
    "context": {}
  }'
```

**✅ Expected response (after ~10-30 seconds):**
```json
{
  "agent_name": "website_guardian",
  "task": "Check if https://google.com is online and tell me the response time", 
  "result": "I checked https://google.com and it is online. The website responded with HTTP status 200 in 156ms. The website is functioning normally.",
  "timestamp": "2024-06-05T14:35:00Z"
}
```

**🎉 Congratulations!** Your AI agent just:
1. Understood your request
2. Used the website monitoring tool
3. Checked Google's status
4. Reported back with detailed results

## 🎯 Step 5: Create an Advanced Workflow (2 minutes)

Let's create a workflow that monitors multiple websites and makes decisions:

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "multi_site_monitor",
    "description": "Monitor multiple critical websites",
    "steps": [
      {
        "type": "tool",
        "name": "website_monitor",
        "parameters": {
          "url": "https://google.com",
          "expected_status": 200,
          "timeout": 10
        },
        "context_key": "google_status"
      },
      {
        "type": "tool", 
        "name": "website_monitor",
        "parameters": {
          "url": "https://github.com",
          "expected_status": 200,
          "timeout": 10
        },
        "context_key": "github_status"
      },
      {
        "type": "agent",
        "name": "website_guardian",
        "task": "Analyze these website statuses: Google: {google_status}, GitHub: {github_status}. Provide a summary report of which sites are online and any issues detected.",
        "context_key": "summary_report"
      }
    ],
    "enabled": true
  }'
```

**Test the workflow:**
```bash
curl -X POST "http://localhost:8000/workflows/multi_site_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{"context": {}}'
```

**✅ What happens:**
1. Checks Google.com status
2. Checks GitHub.com status  
3. AI agent analyzes both results
4. Provides intelligent summary report

## 🎯 Step 6: Schedule Automated Monitoring (1 minute)

Let's schedule our workflow to run automatically every 5 minutes:

```bash
curl -X POST "http://localhost:8000/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "workflow",
    "workflow_name": "multi_site_monitor", 
    "scheduled_time": "2024-12-20T10:00:00Z",
    "context": {
      "recurring": "every_5_minutes",
      "description": "Automated website monitoring"
    }
  }'
```

**✅ Result:** Your workflow now runs automatically every 5 minutes, monitoring your websites and generating intelligent reports!

## 🎉 Success! What You've Accomplished

In just 10 minutes, you've built a complete AI automation system:

### 🤖 **AI Agent Created**
- Smart website monitoring specialist
- Can understand natural language requests
- Uses tools to perform real tasks
- Provides intelligent analysis

### 🔄 **Automated Workflow** 
- Monitors multiple websites simultaneously
- Passes data between steps intelligently
- Generates comprehensive reports

### ⏰ **Scheduled Automation**
- Runs monitoring every 5 minutes
- Completely hands-off operation
- Scales to monitor dozens of websites

### 🛠 **Production-Ready Features**
- Memory management (keeps last 5 conversations)
- Error handling and recovery
- REST API with full documentation
- Docker-based deployment

## 🚀 Next Steps - Level Up Your Setup

### **Explore the Interactive Docs**
Visit **http://localhost:8000/docs** to:
- Test all API endpoints interactively
- See request/response examples
- Generate code snippets for your language

### **Add Email Alerts**
Want to get notified when websites go down? Add email capabilities:

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

### **Monitor More Complex Scenarios**

<details>
<summary>Click to expand advanced monitoring</summary>

```bash
# Create an advanced monitoring agent
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api_monitor",
    "role": "API Health Monitor",
    "goals": "Monitor API endpoints and detect performance issues",
    "backstory": "Expert in API monitoring with deep understanding of web service performance metrics",
    "tools": ["website_monitor", "http_client"],
    "ollama_model": "deepseek-r1:1.5b"
  }'

# Test API monitoring with custom headers
curl -X POST "http://localhost:8000/agents/api_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check the API at https://httpbin.org/get and verify it returns valid JSON with a response time under 1000ms",
    "context": {}
  }'
```

</details>

### **Scale to Production**
Ready for production? Check out:
- **[Production Deployment Guide](DEPLOYMENT.md)** - Deploy to DigitalOcean for $24/month
- **[Complete README](README.md)** - Full feature documentation
- **[Workflow Examples](README.md#creating-workflows)** - Advanced automation patterns

## 🔍 Quick Reference Commands

```bash
# Check system health
curl http://localhost:8000/health

# List all agents
curl http://localhost:8000/agents

# List all workflows  
curl http://localhost:8000/workflows

# Check memory usage
curl http://localhost:8000/memory/stats

# View logs
docker-compose logs -f

# Restart everything
docker-compose restart
```

## 🆘 Troubleshooting

**Agent not responding?**
```bash
# Check if models loaded properly
curl http://localhost:8000/models

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

**Out of memory?**
```bash
# Clear agent memory
curl -X DELETE http://localhost:8000/memory/clear-all

# Check Docker resources
docker stats
```

## 🎯 What's Next?

You now have a powerful AI automation framework! Here are some ideas:

1. **🌐 Website Monitoring** - Monitor your business-critical websites
2. **📧 Email Automation** - Automated customer service responses  
3. **📊 Data Processing** - Automated report generation
4. **🔔 Smart Alerts** - Intelligent notification systems
5. **🤝 Multi-Agent Systems** - Agents that work together

**Ready to build something amazing?** The framework gives you the building blocks - now let your creativity run wild! 🚀

---

**⭐ Tip**: Bookmark **http://localhost:8000/docs** - it's your command center for building AI automation!