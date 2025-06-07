# 🚀 DigitalOcean Production Deployment Guide

This guide provides detailed instructions for deploying the Agentic AI Framework to DigitalOcean for production use.

## 📋 Prerequisites

- DigitalOcean account
- SSH key uploaded to DigitalOcean
- Basic knowledge of Linux/Docker
- Domain name (optional, for SSL)

## 💰 Cost Planning

### Recommended Droplet Specifications

| Configuration | Droplet Size | Monthly Cost | RAM | CPU | Storage | Use Case |
|---------------|--------------|--------------|-----|-----|---------|----------|
| **Development** | s-1vcpu-2gb | ~$12 | 2GB | 1 vCPU | 25GB SSD | Testing, SmolLM only |
| **Production** | s-2vcpu-4gb | ~$24 | 4GB | 2 vCPU | 25GB SSD | **Recommended** |
| **High Performance** | s-4vcpu-8gb | ~$48 | 8GB | 4 vCPU | 25GB SSD | Heavy workloads |
| **Enterprise** | s-8vcpu-16gb | ~$96 | 16GB | 8 vCPU | 50GB SSD | Large scale deployment |

### Model Recommendations by Droplet Size

| Droplet RAM | Recommended Models | Max Agents | Memory Settings |
|-------------|-------------------|------------|-----------------|
| 2GB | `smollm:135m`, `tinyllama:1.1b` | 2-3 | `MAX_AGENT_MEMORY_ENTRIES=3` |
| 4GB | `granite3.2:2b`, `deepseek-r1:1.5b` | 5-10 | `MAX_AGENT_MEMORY_ENTRIES=5` |
| 8GB+ | Any model, multiple concurrent | 10+ | `MAX_AGENT_MEMORY_ENTRIES=10` |

## 🏗 Deployment Steps

### Step 1: Create DigitalOcean Droplet

1. **Log into DigitalOcean Dashboard**
   - Go to https://cloud.digitalocean.com/

2. **Create New Droplet**
   - Click "Create" → "Droplets"
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Regular Intel (Shared CPU)
   - **Size**: s-2vcpu-4gb ($24/month) - **Recommended**
   - **Datacenter**: Choose closest to your users
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
apt install -y curl wget git htop ufw fail2ban

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

#### Production Environment Configuration

```bash
# .env - Production Configuration
# Core Settings
OLLAMA_URL=http://ollama:11434
DEFAULT_MODEL=granite3.2:2b
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_PATH=data/agentic_ai.db

# Memory Management (Optimized for production)
MAX_AGENT_MEMORY_ENTRIES=5
CLEAR_MEMORY_ON_STARTUP=false
MEMORY_CLEANUP_INTERVAL=3600
MEMORY_RETENTION_DAYS=7

# Performance Settings
MAX_AGENT_ITERATIONS=3
SCHEDULER_INTERVAL=60
TOOLS_DIRECTORY=tools

# Security (Add your values)
API_KEY_ENABLED=true
API_KEY=your-secure-api-key-here

# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

```bash
# 4. Run the automated deployment script
chmod +x deploy-digitalocean.sh
./deploy-digitalocean.sh
```

### Step 5: Verify Deployment

```bash
# 1. Check service status
docker-compose ps

# 2. View logs
docker-compose logs -f

# 3. Test health endpoint
curl http://localhost:8000/health

# 4. Test from external access
curl http://your-droplet-ip:8000/health
```

## 🔧 Manual Deployment (Alternative)

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
```

## 🌐 Access Your Deployment

After successful deployment, your framework will be accessible at:

- **🏠 Main API**: `http://your-droplet-ip:8000`
- **📚 API Documentation**: `http://your-droplet-ip:8000/docs`
- **💖 Health Check**: `http://your-droplet-ip:8000/health`
- **🤖 Models List**: `http://your-droplet-ip:8000/models`
- **📊 Memory Stats**: `http://your-droplet-ip:8000/memory/stats`

## 🧪 Testing Your Production Deployment

### 1. Health and System Checks

```bash
# Test health endpoint
curl http://your-droplet-ip:8000/health

# Check available models
curl http://your-droplet-ip:8000/models

# Check memory statistics
curl http://your-droplet-ip:8000/memory/stats

# View system configuration
curl http://your-droplet-ip:8000/config
```

### 2. Create and Test an Agent

```bash
# Create a monitoring agent
curl -X POST "http://your-droplet-ip:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod_monitor",
    "role": "Production Monitor",
    "goals": "Monitor system health and website availability",
    "backstory": "Experienced production monitoring specialist",
    "tools": ["website_monitor"],
    "ollama_model": "granite3.2:2b",
    "enabled": true
  }'

# Test the agent
curl -X POST "http://your-droplet-ip:8000/agents/prod_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://google.com is accessible and report the status",
    "context": {}
  }'
```

### 3. Test Website Monitoring

```bash
# Direct tool test
curl -X POST "http://your-droplet-ip:8000/tools/website_monitor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "url": "https://httpbin.org/status/200",
      "expected_status": 200,
      "timeout": 10
    }
  }'
```

## 🔒 SSL Certificate Setup (Recommended)

### Using Nginx and Let's Encrypt

```bash
# 1. Install Nginx and Certbot
apt install nginx certbot python3-certbot-nginx -y

# 2. Create Nginx configuration
cat > /etc/nginx/sites-available/agentic-ai << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
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
- **🔒 HTTPS API**: `https://your-domain.com`
- **📚 Secure Docs**: `https://your-domain.com/docs`

## 📊 Monitoring and Maintenance

### Resource Monitoring

```bash
# System resources
htop

# Docker container stats
docker stats

# Disk usage
df -h

# Memory usage
free -h

# Check logs
docker-compose logs -f --tail=100
```

### Health Monitoring Script

Create a monitoring script to check system health:

```bash
# Create monitoring script
cat > /usr/local/bin/agentic-health-check.sh << 'EOF'
#!/bin/bash
# Agentic AI Framework Health Check

HEALTH_URL="http://localhost:8000/health"
LOG_FILE="/var/log/agentic-health.log"
DATE=$(date)

# Check API health
if curl -s "$HEALTH_URL" > /dev/null; then
    echo "[$DATE] API is healthy" >> "$LOG_FILE"
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
EOF

chmod +x /usr/local/bin/agentic-health-check.sh

# Add to crontab (check every 5 minutes)
echo "*/5 * * * * /usr/local/bin/agentic-health-check.sh" | crontab -
```

### Backup Strategy

```bash
# Create backup script
cat > /usr/local/bin/agentic-backup.sh << 'EOF'
#!/bin/bash
# Backup Agentic AI Framework data

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/root/agentic-ai-framework"

mkdir -p "$BACKUP_DIR"

# Backup database and configuration
tar -czf "$BACKUP_DIR/agentic-backup-$DATE.tar.gz" \
    -C "$PROJECT_DIR" \
    data/ \
    .env \
    docker-compose.yml

# Keep only last 7 backups
find "$BACKUP_DIR" -name "agentic-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: agentic-backup-$DATE.tar.gz"
EOF

chmod +x /usr/local/bin/agentic-backup.sh

# Schedule daily backups at 2 AM
echo "0 2 * * * /usr/local/bin/agentic-backup.sh" | crontab -
```

## 🔄 Updates and Maintenance

### Updating the Framework

```bash
# 1. Navigate to project directory
cd /root/agentic-ai-framework

# 2. Backup current state
./backup.sh

# 3. Pull latest changes
git pull origin main

# 4. Update Docker images
docker-compose pull

# 5. Restart services
docker-compose up -d

# 6. Verify deployment
curl http://localhost:8000/health
```

### Log Management

```bash
# View recent logs
docker-compose logs --tail=100 -f

# Check log sizes
docker system df

# Clean up old logs and containers
docker system prune -a

# Configure log rotation
cat > /etc/logrotate.d/docker << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size 10M
    missingok
    delaycompress
    copytruncate
}
EOF
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Service Won't Start
```bash
# Check Docker status
systemctl status docker

# Check compose file syntax
docker-compose config

# View detailed logs
docker-compose logs agentic-ai
```

#### 2. Models Not Loading
```bash
# Check Ollama container
docker logs agentic_ai_framework_ollama_1

# Manually pull model
docker exec -it agentic_ai_framework_ollama_1 ollama pull granite3.2:2b

# Check available space
df -h
```

#### 3. High Memory Usage
```bash
# Check memory stats
curl http://localhost:8000/memory/stats

# Clear all memory
curl -X DELETE http://localhost:8000/memory/clear-all

# Restart services
docker-compose restart
```

#### 4. API Not Accessible
```bash
# Check if service is running
docker-compose ps

# Check firewall
ufw status

# Check port binding
netstat -tlnp | grep 8000

# Test local access
curl http://localhost:8000/health
```

### Emergency Recovery

```bash
# Complete reset (nuclear option)
cd /root/agentic-ai-framework
docker-compose down -v
docker system prune -a -f
git pull origin main
docker-compose up -d
```

## 📞 Support and Monitoring

### Setting Up Alerts

For production deployments, consider setting up:

1. **Uptime Monitoring**: Use services like UptimeRobot or Pingdom
2. **Log Monitoring**: Configure log aggregation with ELK stack or similar
3. **Resource Alerts**: Set up DigitalOcean monitoring alerts
4. **Email Notifications**: Configure SMTP for system alerts

### Performance Optimization

```bash
# Optimize Docker daemon
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

systemctl restart docker
```

## 🎯 Production Checklist

- [ ] ✅ Droplet created with adequate resources (4GB+ recommended)
- [ ] ✅ Firewall configured properly
- [ ] ✅ Docker and Docker Compose installed
- [ ] ✅ Application deployed and running
- [ ] ✅ Health checks passing
- [ ] ✅ SSL certificate configured (if using domain)
- [ ] ✅ Monitoring and alerting set up
- [ ] ✅ Backup strategy implemented
- [ ] ✅ Log rotation configured
- [ ] ✅ Update procedure documented
- [ ] ✅ Emergency recovery plan tested

## 💡 Performance Tips

1. **Choose the Right Model**: Smaller models (granite3.2:2b) for better performance
2. **Limit Memory**: Set `MAX_AGENT_MEMORY_ENTRIES=5` or lower for high-volume use
3. **Monitor Resources**: Regular monitoring prevents performance issues
4. **Use SSD Storage**: DigitalOcean SSD droplets provide better I/O performance
5. **Regular Cleanup**: Automated memory and log cleanup maintains performance

Your Agentic AI Framework is now ready for production use! 🚀

For additional support, refer to the main [README.md](README.md) or create an issue in the project repository.