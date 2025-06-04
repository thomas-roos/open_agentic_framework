# Agentic AI Framework - DigitalOcean Production Deployment

## 🚀 Quick Deployment

### Prerequisites
- DigitalOcean account
- SSH key uploaded to DigitalOcean
- Basic knowledge of Linux/Docker

### Recommended Droplet Specs
- **Type:** General Purpose
- **Size:** s-2vcpu-4gb (4GB RAM, 2 vCPU)
- **OS:** Ubuntu 22.04 LTS
- **Storage:** 25GB SSD
- **Cost:** ~$24/month

## 📦 What Gets Deployed

### 5 Optimized Small Models (Total: ~3.2GB)
1. **SmolLM 135M** (92MB) - Ultra-lightweight tasks
2. **TinyLlama 1.1B** (637MB) - General lightweight tasks
3. **Granite 3.2 1B** (700MB) - IBM's efficient model ⭐ NEW
4. **DeepSeek-Coder 1.3B** (776MB) - Code-related tasks
5. **DeepSeek-R1 1.5B** (1.1GB) - Reasoning and tool calling ⭐ Default

### Built-in Tools
- Website Monitor - Check website availability
- Email Sender - Send SMTP emails
- HTTP Client - Make API requests

### Pre-configured Agents
- Website Checker Agent - Monitor websites using DeepSeek-R1
- Echo Agent - Simple text echo functionality

## 🛠 Deployment Methods

### Method 1: Automated Script (Recommended)

```bash
# 1. Create DigitalOcean droplet (4GB RAM recommended)
# 2. SSH into your droplet
ssh root@your-droplet-ip

# 3. Upload your project files
git clone <your-repo> agentic_ai_framework
cd agentic_ai_framework

# 4. Run deployment script
chmod +x deploy-digitalocean.sh
./deploy-digitalocean.sh
```

### Method 2: Manual Deployment

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure firewall
ufw allow ssh && ufw allow 8000 && ufw allow 80 && ufw --force enable

# Deploy application
cp docker-compose.production.yml docker-compose.yml
cp .env.production .env
docker-compose up -d

# Wait for models to download (5-10 minutes)
docker-compose logs -f model-downloader
```

## 🌐 Access Your Deployment

After deployment, your framework will be available at:

- **API Documentation:** `http://your-droplet-ip:8000/docs`
- **Health Check:** `http://your-droplet-ip:8000/health` 
- **Web Interface:** `http://your-droplet-ip:8080`
- **Ollama API:** `http://your-droplet-ip:11434`

## 🧪 Testing Your Deployment

### Test Health Check
```bash
curl http://your-droplet-ip:8000/health
```

### Test Website Checker Agent
```bash
curl -X POST "http://your-droplet-ip:8000/agents/website_checker/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://google.com is online",
    "context": {}
  }'
```

### Test Echo Agent
```bash
curl -X POST "http://your-droplet-ip:8000/agents/echo_agent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Echo: Hello from DigitalOcean!",
    "context": {}
  }'
```

### Test Direct Tool Usage
```bash
curl -X POST "http://your-droplet-ip:8000/tools/website_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "url": "https://httpbin.org/status/200",
      "expected_status": 200
    }
  }'
```

## 📊 Monitoring & Management

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f agentic-ai
docker-compose logs -f ollama
```

### Resource Usage
```bash
# Monitor system resources
htop

# Docker stats
docker stats
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart agentic-ai
```

## 🔧 Configuration

### Switch Default Model
```bash
# Edit environment
nano .env

# Change DEFAULT_MODEL to any downloaded model:
# - tinyllama:1.1b  
# - granite3.2:2b
# - deepseek-coder:1.3b
# - deepseek-r1:1.5b

# Restart
docker-compose restart agentic-ai
```

### Add Custom Agents
```bash
curl -X POST "http://your-droplet-ip:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_agent",
    "role": "Custom Agent",
    "goals": "Perform custom tasks",
    "backstory": "Agent-specific instructions here",
    "tools": ["website_monitor"],
    "ollama_model": "deepseek-r1:1.5b",
    "enabled": true
  }'
```

## 📈 Scaling & Optimization

### Cost Optimization
- **2GB Droplet + SmolLM only:** $12/month
- **4GB Droplet + All 5 models:** $24/month  
- **8GB Droplet + Heavy usage:** $48/month

### Performance Tuning
```bash
# Limit memory usage
docker-compose down
nano docker-compose.yml
# Adjust deploy.resources.limits sections
docker-compose up -d
```

### SSL/HTTPS Setup
```bash
# Install Nginx + Certbot
apt install nginx certbot python3-certbot-nginx

# Configure reverse proxy
# (Add Nginx config for SSL termination)

# Get SSL certificate
certbot --nginx -d your-domain.com
```

## 🔐 Security

### Firewall Configuration
```bash
ufw status
# Should show: 22/ssh, 80, 8000, 8080, 11434 ALLOW
```

### Regular Updates
```bash
# Update system
apt update && apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

## 🆘 Troubleshooting

### Common Issues

**Models not downloading:**
```bash
# Check model downloader logs
docker-compose logs model-downloader

# Manual model download
docker exec -it agentic-ai-ollama-production ollama pull deepseek-r1:1.5b
```

**API not responding:**
```bash
# Check application logs
docker-compose logs agentic-ai

# Restart application
docker-compose restart agentic-ai
```

**Out of memory:**
```bash
# Check memory usage
free -h
docker stats

# Consider upgrading droplet or using smaller models
```

### Support Commands
```bash
# Complete reset
docker-compose down -v
docker system prune -a
./deploy-digitalocean.sh

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/
```

## 💰 Cost Breakdown

| Configuration | Monthly Cost | Use Case |
|---------------|--------------|----------|
| 2GB + SmolLM only | $12 | Light testing |
| 4GB + All 5 models | $24 | Production ready |
| 8GB + Heavy usage | $48 | High performance |

## 🎯 Production Checklist

- [ ] 4GB+ DigitalOcean droplet created
- [ ] Firewall configured (ports 22, 80, 8000, 8080, 11434)
- [ ] All 5 models downloaded successfully
- [ ] Health check returns 200 OK
- [ ] Website checker agent working
- [ ] Monitoring/logging configured
- [ ] Backup strategy in place
- [ ] SSL certificate (optional)

Your Agentic AI Framework is now production-ready on DigitalOcean! 🎉