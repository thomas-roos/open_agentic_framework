# Production Deployment Guide

This guide provides detailed instructions for deploying the Agentic AI Framework to Cloud Provider for production use with **multi-provider LLM support** and advanced monitoring.

## Prerequisites

- Cloud Provider account
- Basic knowledge of Linux/Docker
- Domain name (optional, for SSL)
- API keys for additional providers (optional)

## Cost Planning

### Recommended Droplet Specifications

| Configuration | Droplet Size | RAM | CPU | Storage | Use Case |
|---------------|--------------|--------------|-----|-----|---------|----------|
| **Development** | s-1vcpu-2gb | 2GB | 1 vCPU | 25GB SSD | Testing, Ollama only |
| **Production** | s-2vcpu-4gb | 4GB | 2 vCPU | 25GB SSD | **Recommended** |
| **High Performance** | s-4vcpu-8gb | 8GB | 4 vCPU | 25GB SSD | Multi-provider, heavy workloads |
| **Enterprise** | s-8vcpu-16gb | 16GB | 8 vCPU | 50GB SSD | Large scale, multiple models |

### Model Recommendations by Droplet Size

| Droplet RAM | Recommended Models | Max Agents | Memory Settings | Provider Mix |
|-------------|-------------------|------------|-----------------|--------------|
| 2GB | `tinyllama:1.1b` | 2-3 | `MAX_AGENT_MEMORY_ENTRIES=3` | Ollama only |
| 4GB | `granite3.2:2b` | 5-10 | `MAX_AGENT_MEMORY_ENTRIES=5` | Ollama primary |
| 8GB+ | Multi-model setup | 10+ | `MAX_AGENT_MEMORY_ENTRIES=10` | Ollama + OpenAI |
| 16GB+ | `gpt-4` + local models | 20+ | `MAX_AGENT_MEMORY_ENTRIES=15` | Full multi-provider |

## Deployment Steps

### Step 1: Create a Linux Host

2. **Create New Instance**
   - **Image**: Ubuntu 22.04 LTS
   - **Authentication**: SSH keys (recommended) or Password
   - **Hostname**: `agentic-ai-prod` (or your preference)

3. **Configure Firewall (Optional but Recommended)**
   - Create new firewall or use existing
   - **Inbound Rules**:
     - SSH (22) - Your IP only
     - HTTP (80) - All IPv4, All IPv6
     - HTTPS (443) - All IPv4, All IPv6
     - Custom (8000) - All IPv4, All IPv6 (API access)

### Step 2: Initial Server Setup

```bash
# 1. SSH into your droplet
ssh root@your-droplet-ip

# 2. Update system packages
apt update && apt upgrade -y

# 3. Install essential packages
apt install -y curl wget git htop ufw fail2ban jq

# 4. Configure firewall
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 8000
ufw --force enable

# 5. Create non-root user (optional but recommended)
adduser deploy
usermod -aG sudo deploy
usermod -aG docker deploy  # We'll install Docker next
```

### Step 3: Install Docker and Docker Compose

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 3. Verify installation
docker --version
docker-compose --version

# 4. Start Docker service
systemctl start docker
systemctl enable docker
```

### Step 4: Deploy the Application

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/agentic-ai-framework.git
cd agentic-ai-framework

# 2. Configure environment for production
cp .env.production .env

# 3. Edit configuration (use nano or your preferred editor)
nano .env
```

#### Enhanced Production Environment Configuration

```bash
# .env - Production Configuration with Multi-Provider Support

# Core Settings
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_PATH=data/agentic_ai.db

# Multi-Provider LLM Configuration
DEFAULT_LLM_PROVIDER=ollama
LLM_FALLBACK_ENABLED=true
LLM_FALLBACK_ORDER=ollama,openai,openrouter

# Ollama Provider (Primary)
OLLAMA_ENABLED=true
OLLAMA_URL=http://ollama:11434
OLLAMA_DEFAULT_MODEL=granite3.2:2b

# OpenAI Provider (Optional - uncomment to enable)
# OPENAI_ENABLED=true
# OPENAI_API_KEY=your-openai-api-key-here
# OPENAI_DEFAULT_MODEL=gpt-3.5-turbo
# OPENAI_ORGANIZATION=your-org-id  # Optional

# OpenRouter Provider (Optional - uncomment to enable)
# OPENROUTER_ENABLED=true
# OPENROUTER_API_KEY=your-openrouter-api-key-here
# OPENROUTER_DEFAULT_MODEL=openai/gpt-3.5-turbo

# Memory Management (Optimized for production)
MAX_AGENT_MEMORY_ENTRIES=5
CLEAR_MEMORY_ON_STARTUP=false
MEMORY_CLEANUP_INTERVAL=3600
MEMORY_RETENTION_DAYS=7

# Model Warmup System
MODEL_WARMUP_TIMEOUT=60
MAX_CONCURRENT_WARMUPS=2
AUTO_WARMUP_ON_STARTUP=true
WARMUP_INTERVAL_HOURS=6
MAX_IDLE_HOURS=24

# Performance Settings
MAX_AGENT_ITERATIONS=3
SCHEDULER_INTERVAL=60
TOOLS_DIRECTORY=tools

# Security (Recommended for production)
API_KEY_ENABLED=true
API_KEY=your-secure-api-key-here-minimum-32-characters

# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO
```

```bash


### Step 5: Verify Enhanced Deployment

```bash
# 1. Check service status
docker-compose ps

# 2. View logs
docker-compose logs -f

# 3. Test comprehensive health endpoint
curl http://localhost:8000/health

# 4. Check provider status
curl http://localhost:8000/providers

# 5. Test from external access
curl http://your-droplet-ip:8000/health

# 6. Verify model warmup system
curl http://your-droplet-ip:8000/health | jq '.warmup_stats'
```

## Manual Deployment (Alternative)

If the automated script fails, you can deploy manually:

```bash
# 1. Create necessary directories
mkdir -p data logs tools

# 2. Set proper permissions
chmod 755 data logs tools

# 3. Start services
docker-compose -f docker-compose.production.yml up -d

# 4. Wait for models to download (5-10 minutes)
docker-compose logs -f model-downloader

# 5. Verify all services are running
docker-compose ps

# 6. Check provider initialization
curl http://localhost:8000/providers
```

## Access Your Enhanced Deployment

After successful deployment, your framework will be accessible at:

- **Main API**: `http://your-droplet-ip:8000`
- **Interactive API Documentation**: `http://your-droplet-ip:8000/docs`
- **Alternative Docs (ReDoc)**: `http://your-droplet-ip:8000/redoc`
- **Health Check**: `http://your-droplet-ip:8000/health`
- **Provider Status**: `http://your-droplet-ip:8000/providers`
- **Models List**: `http://your-droplet-ip:8000/models`
- **Memory Stats**: `http://your-droplet-ip:8000/memory/stats`

## Testing Your Production Deployment

### 1. Enhanced Health and System Checks

```bash
# Test comprehensive health endpoint
curl http://your-droplet-ip:8000/health

# Check all provider status
curl http://your-droplet-ip:8000/providers

# Check detailed model information
curl http://your-droplet-ip:8000/models/detailed

# Check memory statistics
curl http://your-droplet-ip:8000/memory/stats

# View system configuration
curl http://your-droplet-ip:8000/config
```

### 2. Test Multi-Provider Setup

```bash
# Test default provider (Ollama)
curl -X POST "http://your-droplet-ip:8000/models/test/granite3.2:2b"

# If OpenAI is enabled, test it
curl -X POST "http://your-droplet-ip:8000/models/test/gpt-3.5-turbo"

# Configure a new provider dynamically (if needed)
curl -X POST "http://your-droplet-ip:8000/providers/openai/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "api_key": "your-openai-key",
    "default_model": "gpt-3.5-turbo"
  }'
```

### 3. Create and Test Advanced Agent

```bash
# Create a monitoring agent with tool configurations
curl -X POST "http://your-droplet-ip:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod_monitor",
    "role": "Production Monitor",
    "goals": "Monitor system health and website availability with intelligent analysis",
    "backstory": "Experienced production monitoring specialist with deep understanding of system performance metrics",
    "tools": ["website_monitor", "email_sender"],
    "ollama_model": "granite3.2:2b",
    "enabled": true,
    "tool_configs": {
      "email_sender": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "from_email": "Production Monitor <alerts@yourcompany.com>"
      }
    }
  }'

# Test the agent with intelligent analysis
curl -X POST "http://your-droplet-ip:8000/agents/prod_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://google.com is accessible, analyze the response time, and provide a detailed status report including any performance concerns",
    "context": {}
  }'
```

### 4. Test Advanced Workflow

```bash
# Create workflow with variable substitution
curl -X POST "http://your-droplet-ip:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "comprehensive_monitoring",
    "description": "Advanced website monitoring with intelligent alerts",
    "steps": [
      {
        "type": "tool",
        "name": "website_monitor",
        "parameters": {
          "url": "{{target_url}}",
          "expected_status": 200,
          "timeout": 10
        },
        "context_key": "website_status"
      },
      {
        "type": "agent",
        "name": "prod_monitor",
        "task": "Analyze website status: {{website_status}}. Response time was {{website_status.response_time}}ms. If response time > 2000ms or status != 200, this is an issue requiring immediate attention.",
        "context_key": "analysis"
      }
    ],
    "enabled": true
  }'

# Execute workflow with context variables
curl -X POST "http://your-droplet-ip:8000/workflows/comprehensive_monitoring/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "target_url": "https://httpbin.org/status/200"
    }
  }'
```

## Enhanced SSL Certificate Setup

### Using Nginx with Let's Encrypt and Security Headers

```bash
# 1. Install Nginx and Certbot
apt install nginx certbot python3-certbot-nginx -y

# 2. Create enhanced Nginx configuration
cat > /etc/nginx/sites-available/agentic-ai << EOF
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 3. Enable the site
ln -s /etc/nginx/sites-available/agentic-ai /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# 4. Get SSL certificate
certbot --nginx -d your-domain.com

# 5. Test automatic renewal
certbot renew --dry-run
```

After SSL setup, your framework will be accessible via:
- **HTTPS API**: `https://your-domain.com`
- **Secure Docs**: `https://your-domain.com/docs`

## Enhanced Monitoring and Maintenance

### Advanced Resource Monitoring

```bash
# System resources with JSON output
htop

# Docker container stats with formatting
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Disk usage analysis
df -h
du -sh /var/lib/docker/

# Memory usage details
free -h
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable"

# Check framework-specific logs
docker-compose logs -f --tail=100
```

### Comprehensive Health Monitoring Script

```bash
# Create enhanced monitoring script
cat > /usr/local/bin/agentic-health-check.sh << 'EOF'
#!/bin/bash
# Enhanced Agentic AI Framework Health Check

HEALTH_URL="http://localhost:8000/health"
PROVIDERS_URL="http://localhost:8000/providers"
MEMORY_URL="http://localhost:8000/memory/stats"
LOG_FILE="/var/log/agentic-health.log"
DATE=$(date)
API_KEY="${API_KEY:-}"

# Add API key header if configured
AUTH_HEADER=""
if [ ! -z "$API_KEY" ]; then
    AUTH_HEADER="Authorization: Bearer $API_KEY"
fi

# Function to make API calls with optional auth
api_call() {
    local url=$1
    if [ ! -z "$AUTH_HEADER" ]; then
        curl -s -H "$AUTH_HEADER" "$url"
    else
        curl -s "$url"
    fi
}

# Check API health
if api_call "$HEALTH_URL" > /dev/null; then
    echo "[$DATE] API is healthy" >> "$LOG_FILE"
    
    # Check provider status
    PROVIDER_STATUS=$(api_call "$PROVIDERS_URL" | jq -r '.providers | to_entries[] | select(.value.is_healthy == false) | .key' 2>/dev/null)
    if [ ! -z "$PROVIDER_STATUS" ]; then
        echo "[$DATE] WARNING: Unhealthy providers: $PROVIDER_STATUS" >> "$LOG_FILE"
    fi
    
    # Check memory usage
    TOTAL_MEMORY=$(api_call "$MEMORY_URL" | jq -r '.total_memory_entries' 2>/dev/null)
    if [ ! -z "$TOTAL_MEMORY" ] && [ "$TOTAL_MEMORY" -gt 100 ]; then
        echo "[$DATE] WARNING: High memory usage: $TOTAL_MEMORY entries" >> "$LOG_FILE"
    fi
else
    echo "[$DATE] API is DOWN - attempting restart" >> "$LOG_FILE"
    cd /root/agentic-ai-framework
    docker-compose restart agentic-ai
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "[$DATE] WARNING: Disk usage is $DISK_USAGE%" >> "$LOG_FILE"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEMORY_USAGE" -gt 90 ]; then
    echo "[$DATE] WARNING: Memory usage is $MEMORY_USAGE%" >> "$LOG_FILE"
fi

# Check Docker container health
UNHEALTHY_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -v "Up" | wc -l)
if [ "$UNHEALTHY_CONTAINERS" -gt 1 ]; then  # Header line counts as 1
    echo "[$DATE] WARNING: $((UNHEALTHY_CONTAINERS-1)) containers are not running properly" >> "$LOG_FILE"
fi
EOF

chmod +x /usr/local/bin/agentic-health-check.sh

# Add to crontab (check every 5 minutes)
echo "*/5 * * * * /usr/local/bin/agentic-health-check.sh" | crontab -
```

### Enhanced Backup Strategy

```bash
# Create comprehensive backup script
cat > /usr/local/bin/agentic-backup.sh << 'EOF'
#!/bin/bash
# Enhanced Agentic AI Framework Backup

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/root/agentic-ai-framework"
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"

# Backup database and configuration
echo "Starting backup: agentic-backup-$DATE"

# Create comprehensive backup
tar -czf "$BACKUP_DIR/agentic-backup-$DATE.tar.gz" \
    -C "$PROJECT_DIR" \
    data/ \
    .env \
    docker-compose.yml \
    tools/ \
    logs/ \
    --exclude="logs/*.log"

# Backup just the database separately for faster restores
cp "$PROJECT_DIR/data/agentic_ai.db" "$BACKUP_DIR/database-$DATE.db" 2>/dev/null || echo "Database file not found"

# Export current configuration
curl -s http://localhost:8000/config > "$BACKUP_DIR/config-$DATE.json" 2>/dev/null || echo "Could not export config"

# Keep only last N backups
find "$BACKUP_DIR" -name "agentic-backup-*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "database-*.db" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "config-*.json" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: agentic-backup-$DATE.tar.gz"
echo "Database backup: database-$DATE.db"
echo "Config backup: config-$DATE.json"
EOF

chmod +x /usr/local/bin/agentic-backup.sh

# Schedule daily backups at 2 AM
echo "0 2 * * * /usr/local/bin/agentic-backup.sh" | crontab -
```

## Updates and Maintenance

### Updating the Framework

```bash
# 1. Navigate to project directory
cd /root/agentic-ai-framework

# 2. Backup current state
/usr/local/bin/agentic-backup.sh

# 3. Pull latest changes
git pull origin main

# 4. Update Docker images
docker-compose pull

# 5. Restart services with zero-downtime
docker-compose up -d --no-deps agentic-ai

# 6. Verify deployment
curl http://localhost:8000/health
curl http://localhost:8000/providers

# 7. Test critical functionality
curl -X POST "http://localhost:8000/models/test/granite3.2:2b"
```

### Provider Management Updates

```bash
# Update provider configurations without restart
curl -X POST "http://localhost:8000/providers/reload" \
  -H "Authorization: Bearer $API_KEY"

# Test new provider configuration
curl -X POST "http://localhost:8000/providers/openai/health-check" \
  -H "Authorization: Bearer $API_KEY"
```

## Enhanced Troubleshooting

### Advanced Diagnostic Commands

#### 1. Service Won't Start
```bash
# Check Docker status
systemctl status docker

# Check compose file syntax
docker-compose config

# View detailed logs with timestamps
docker-compose logs --timestamps agentic-ai

# Check system resources
free -h && df -h
```

#### 2. Provider Issues
```bash
# Check all provider status
curl http://localhost:8000/providers | jq '.providers'

# Test specific provider health
curl -X POST "http://localhost:8000/providers/ollama/health-check"

# Check provider configuration
curl http://localhost:8000/providers/ollama/config

# Reload all providers
curl -X POST "http://localhost:8000/providers/reload"
```

#### 3. Model Warmup Issues
```bash
# Check warmup status
curl http://localhost:8000/health | jq '.warmup_stats'

# Check which models are active
curl http://localhost:8000/models/detailed | jq '.models[] | select(.supports_streaming == true)'

# Test model directly
curl -X POST "http://localhost:8000/models/test/granite3.2:2b"
```

#### 4. Memory and Performance Issues
```bash
# Detailed memory statistics
curl http://localhost:8000/memory/stats | jq '.'

# Clear memory intelligently
curl -X POST "http://localhost:8000/memory/cleanup"

# Check agent-specific memory
curl http://localhost:8000/agents/website_guardian/memory

# Monitor Docker resource usage
docker stats --no-stream
```

### Emergency Recovery Procedures

```bash
# Complete system reset (nuclear option)
cd /root/agentic-ai-framework

# 1. Stop all services
docker-compose down -v

# 2. Clean Docker system
docker system prune -a -f

# 3. Restore from backup if needed
tar -xzf /root/backups/agentic-backup-LATEST.tar.gz

# 4. Restart services
docker-compose up -d

# 5. Verify all systems
./scripts/health-check-all.sh
```

## Enhanced Support and Monitoring

### Production Monitoring Setup

For enterprise deployments, consider:

1. **Application Monitoring**
   - Integrate with DataDog, New Relic, or Prometheus
   - Monitor API response times and error rates
   - Track memory usage and cleanup efficiency

2. **Alerting Systems**
   - Set up PagerDuty or similar for critical alerts
   - Configure Slack/Discord webhooks for notifications
   - Monitor provider health and automatic failover

3. **Performance Analytics**
   - Track model performance across providers
   - Monitor workflow execution times
   - Analyze memory usage patterns

4. **Security Monitoring**
   - Monitor API access patterns
   - Set up fail2ban for suspicious activity
   - Regular security audits

### Performance Optimization for Production

```bash
# Optimize Docker daemon for production
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true
}
EOF

systemctl restart docker

# Optimize Nginx for high traffic
cat >> /etc/nginx/nginx.conf << EOF
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
client_max_body_size 50M;
EOF
```

## Enhanced Production Checklist

- [ ] ✅ Droplet created with adequate resources (4GB+ recommended)
- [ ] ✅ Firewall configured properly
- [ ] ✅ Docker and Docker Compose installed
- [ ] ✅ Application deployed and running
- [ ] ✅ All providers initialized and healthy
- [ ] ✅ Model warmup system functioning
- [ ] ✅ Health checks passing (API, providers, memory)
- [ ] ✅ SSL certificate configured (if using domain)
- [ ] ✅ Rate limiting and security headers configured
- [ ] ✅ Enhanced monitoring and alerting set up
- [ ] ✅ Comprehensive backup strategy implemented
- [ ] ✅ Log rotation configured
- [ ] ✅ Update procedure documented and tested
- [ ] ✅ Emergency recovery plan tested
- [ ] ✅ API authentication configured
- [ ] ✅ Provider fallback tested

## Enhanced Performance Tips

1. **Provider Strategy**: Use Ollama for speed, OpenAI for quality, OpenRouter for variety
2. **Model Selection**: Choose the smallest model that meets your accuracy requirements
3. **Memory Management**: Set appropriate `MAX_AGENT_MEMORY_ENTRIES` based on usage patterns
4. **Warmup Optimization**: Configure warmup intervals based on your traffic patterns
5. **Monitoring**: Regular monitoring prevents performance degradation
6. **Resource Allocation**: Monitor and adjust based on actual usage patterns
7. **Caching**: Leverage model warmup for frequently used models
8. **Scaling**: Consider horizontal scaling for high-volume deployments

Your enhanced Agentic AI Framework with multi-provider support is now ready for production use!

For additional support, refer to the main [README.md](README.md) or create an issue in the project repository.