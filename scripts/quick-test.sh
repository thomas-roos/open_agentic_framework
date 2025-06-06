#!/bin/bash
# api-troubleshoot.sh - Comprehensive API troubleshooting for DigitalOcean

echo "🔧 API Troubleshooting Script"
echo "============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_section() {
    echo ""
    echo -e "${CYAN}$1${NC}"
    echo "$(printf '%.0s-' {1..50})"
}

print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "OK")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}✗${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
    esac
}

# Check system resources
print_section "1. System Resources"
echo "Memory usage:"
free -h
echo ""
echo "CPU usage:"
top -bn1 | head -15
echo ""
echo "Disk usage:"
df -h
echo ""
echo "Load average:"
uptime

# Check Docker
print_section "2. Docker Status"
if command -v docker >/dev/null 2>&1; then
    print_status "OK" "Docker is installed"
    
    if systemctl is-active --quiet docker; then
        print_status "OK" "Docker service is running"
    else
        print_status "ERROR" "Docker service is not running"
        echo "Try: sudo systemctl start docker"
        exit 1
    fi
    
    echo ""
    echo "Docker system info:"
    docker system df
    echo ""
    echo "Docker containers:"
    docker ps -a
    
else
    print_status "ERROR" "Docker is not installed"
    exit 1
fi

# Check Docker Compose
print_section "3. Docker Compose Status"
if command -v docker-compose >/dev/null 2>&1; then
    print_status "OK" "Docker Compose is installed"
    docker-compose --version
else
    print_status "ERROR" "Docker Compose is not installed"
fi

# Check containers
print_section "4. Container Analysis"
echo "All containers:"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Container resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check specific containers
echo ""
if docker ps | grep -q "agentic-ai"; then
    print_status "OK" "Agentic AI container is running"
    
    echo ""
    echo "Agentic AI container details:"
    docker inspect $(docker ps -q --filter "name=agentic-ai") | jq '.[0] | {State, Config: {Env}, NetworkSettings: {Ports}}' 2>/dev/null || echo "jq not available for detailed inspection"
    
else
    print_status "ERROR" "Agentic AI container is not running"
    
    # Check if container exists but stopped
    if docker ps -a | grep -q "agentic-ai"; then
        print_status "WARNING" "Agentic AI container exists but is stopped"
        
        echo ""
        echo "Last container logs:"
        docker logs --tail 50 $(docker ps -aq --filter "name=agentic-ai") 2>/dev/null || echo "No logs available"
    else
        print_status "ERROR" "Agentic AI container does not exist"
    fi
fi

echo ""
if docker ps | grep -q "ollama"; then
    print_status "OK" "Ollama container is running"
    
    echo ""
    echo "Ollama container details:"
    ollama_container=$(docker ps -q --filter "name=ollama")
    echo "Container ID: $ollama_container"
    echo "Container status:"
    docker inspect $ollama_container | jq '.[0].State' 2>/dev/null || docker inspect $ollama_container | grep -A 10 '"State"'
    
else
    print_status "ERROR" "Ollama container is not running"
    
    if docker ps -a | grep -q "ollama"; then
        print_status "WARNING" "Ollama container exists but is stopped"
        
        echo ""
        echo "Ollama container logs:"
        docker logs --tail 50 $(docker ps -aq --filter "name=ollama") 2>/dev/null || echo "No logs available"
    else
        print_status "ERROR" "Ollama container does not exist"
    fi
fi

# Check ports and networking
print_section "5. Network & Port Analysis"
echo "Checking port 8000 (API):"
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    print_status "OK" "Port 8000 is listening"
    netstat -tlnp | grep ":8000 "
else
    print_status "ERROR" "Port 8000 is not listening"
fi

echo ""
echo "Checking port 11434 (Ollama):"
if netstat -tlnp 2>/dev/null | grep -q ":11434 "; then
    print_status "OK" "Port 11434 is listening"
    netstat -tlnp | grep ":11434 "
else
    print_status "ERROR" "Port 11434 is not listening"
fi

echo ""
echo "All listening ports:"
netstat -tlnp 2>/dev/null | grep LISTEN | head -20

# Check logs
print_section "6. Application Logs"
if docker ps -q --filter "name=agentic-ai" >/dev/null; then
    echo "Recent Agentic AI logs:"
    docker logs --tail 100 $(docker ps -q --filter "name=agentic-ai") 2>&1 | tail -50
else
    echo "Agentic AI container not running - checking stopped container logs:"
    if docker ps -aq --filter "name=agentic-ai" >/dev/null; then
        docker logs --tail 100 $(docker ps -aq --filter "name=agentic-ai") 2>&1 | tail -50
    else
        print_status "ERROR" "No Agentic AI container found"
    fi
fi

echo ""
if docker ps -q --filter "name=ollama" >/dev/null; then
    echo "Recent Ollama logs:"
    docker logs --tail 50 $(docker ps -q --filter "name=ollama") 2>&1 | tail -30
else
    echo "Ollama container not running - checking stopped container logs:"
    if docker ps -aq --filter "name=ollama" >/dev/null; then
        docker logs --tail 50 $(docker ps -aq --filter "name=ollama") 2>&1 | tail -30
    else
        print_status "ERROR" "No Ollama container found"
    fi
fi

# Check Docker Compose files
print_section "7. Docker Compose Configuration"
if [ -f "docker-compose.yml" ]; then
    print_status "OK" "docker-compose.yml found"
    echo ""
    echo "Docker Compose services:"
    docker-compose config --services 2>/dev/null || echo "Error reading docker-compose.yml"
    
    echo ""
    echo "Port mappings:"
    docker-compose config 2>/dev/null | grep -A 5 -B 5 "ports:" || echo "No port mappings found"
    
else
    print_status "ERROR" "docker-compose.yml not found in current directory"
    echo "Current directory: $(pwd)"
    echo "Files in current directory:"
    ls -la
fi

# Check environment
print_section "8. Environment Check"
if [ -f ".env" ]; then
    print_status "OK" ".env file found"
    echo ""
    echo "Environment variables (sensitive values hidden):"
    cat .env | sed 's/=.*/=***/' | head -20
else
    print_status "WARNING" ".env file not found"
fi

echo ""
echo "Current environment:"
env | grep -E "(API_|OLLAMA_|DATABASE_)" | head -10

# Quick connectivity tests
print_section "9. Connectivity Tests"
echo "Testing localhost connectivity:"

# Test direct curl to localhost
echo -n "Curl to localhost:8000: "
if curl -s --connect-timeout 5 http://localhost:8000 >/dev/null 2>&1; then
    print_status "OK" "Connected"
else
    print_status "ERROR" "Connection failed"
fi

echo -n "Curl to 127.0.0.1:8000: "
if curl -s --connect-timeout 5 http://127.0.0.1:8000 >/dev/null 2>&1; then
    print_status "OK" "Connected"
else
    print_status "ERROR" "Connection failed"
fi

echo -n "Curl to localhost:11434: "
if curl -s --connect-timeout 5 http://localhost:11434 >/dev/null 2>&1; then
    print_status "OK" "Connected"
else
    print_status "ERROR" "Connection failed"
fi

# Check firewall
print_section "10. Firewall Status"
if command -v ufw >/dev/null 2>&1; then
    echo "UFW status:"
    sudo ufw status verbose 2>/dev/null || echo "Cannot check UFW status (permission denied)"
else
    echo "UFW not installed"
fi

if command -v iptables >/dev/null 2>&1; then
    echo ""
    echo "Iptables rules (first 10):"
    sudo iptables -L -n 2>/dev/null | head -20 || echo "Cannot check iptables (permission denied)"
fi

# Provide recommendations
print_section "11. Recommendations"
echo -e "${BLUE}Based on the analysis above:${NC}"
echo ""

if ! docker ps | grep -q "agentic-ai"; then
    echo -e "${YELLOW}🔧 IMMEDIATE ACTIONS NEEDED:${NC}"
    echo "1. Start the containers:"
    echo "   docker-compose up -d"
    echo ""
    echo "2. If containers fail to start, check logs:"
    echo "   docker-compose logs agentic-ai"
    echo "   docker-compose logs ollama"
    echo ""
    echo "3. If containers are missing, rebuild:"
    echo "   docker-compose down"
    echo "   docker-compose build"
    echo "   docker-compose up -d"
    echo ""
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo -e "${YELLOW}🔧 PORT 8000 NOT LISTENING:${NC}"
    echo "- The API service is not running or not binding to port 8000"
    echo "- Check the agentic-ai container logs for startup errors"
    echo "- Verify the API_PORT environment variable"
    echo ""
fi

if ! docker ps | grep -q "ollama"; then
    echo -e "${YELLOW}🔧 OLLAMA NOT RUNNING:${NC}"
    echo "- Ollama container is required for the API to work"
    echo "- Start with: docker-compose up -d ollama"
    echo "- Check logs: docker logs ollama"
    echo ""
fi

echo -e "${GREEN}💡 GENERAL TIPS:${NC}"
echo "- Wait 2-3 minutes after starting containers for full initialization"
echo "- Check logs continuously: docker-compose logs -f"
echo "- Restart if needed: docker-compose restart"
echo "- Your system resources (16GB RAM, 8 CPU) are excellent for this workload"

print_section "12. Quick Commands"
echo "Useful commands for troubleshooting:"
echo ""
echo -e "${CYAN}# Check container status${NC}"
echo "docker-compose ps"
echo ""
echo -e "${CYAN}# View live logs${NC}"
echo "docker-compose logs -f"
echo ""
echo -e "${CYAN}# Restart everything${NC}"
echo "docker-compose restart"
echo ""
echo -e "${CYAN}# Complete rebuild${NC}"
echo "docker-compose down && docker-compose build && docker-compose up -d"
echo ""
echo -e "${CYAN}# Test API manually${NC}"
echo "curl -v http://localhost:8000/health"