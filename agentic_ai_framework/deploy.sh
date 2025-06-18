#!/bin/bash

# Open Agentic Framework - Simple Deployment Script
# Now with automatic model download via docker-compose

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying Open Agentic Framework...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${YELLOW}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Create directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p data logs tools backups

# Create .env if not exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
    else
        cat > .env << 'EOF'
OLLAMA_URL=http://ollama:11434
DEFAULT_MODEL=llama3
DATABASE_PATH=/app/data/agentic_ai.db
API_HOST=0.0.0.0
API_PORT=8000
MAX_AGENT_ITERATIONS=10
SCHEDULER_INTERVAL=60
TOOLS_DIRECTORY=tools
EOF
        echo -e "${GREEN}✅ Created basic .env file${NC}"
    fi
fi

# Start services (model download happens automatically)
echo -e "${BLUE}📦 Starting services with automatic model download...${NC}"
docker-compose up -d

# Wait for services
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
echo "This may take a few minutes while models are downloaded..."

# Wait for Ollama
timeout=180
count=0
while [ $count -lt $timeout ]; do
    if curl -f http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✅ Ollama is ready${NC}"
        break
    fi
    
    if [ $((count % 30)) -eq 0 ]; then
        echo "Still waiting for Ollama... (${count}s/${timeout}s)"
    fi
    
    sleep 5
    count=$((count + 5))
done

# Wait for main app
timeout=120
count=0
while [ $count -lt $timeout ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✅ Main application is ready${NC}"
        break
    fi
    
    if [ $((count % 20)) -eq 0 ]; then
        echo "Still waiting for main app... (${count}s/${timeout}s)"
    fi
    
    sleep 5
    count=$((count + 5))
done

# Show status
echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo -e "${GREEN}🌐 Access points:${NC}"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo "  • Main API: http://localhost:8000"
echo ""
echo -e "${BLUE}🧪 Quick test:${NC}"
echo "curl http://localhost:8000/health"
echo ""
echo -e "${BLUE}📋 Useful commands:${NC}"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop: docker-compose down"
echo "  • Restart: docker-compose restart"