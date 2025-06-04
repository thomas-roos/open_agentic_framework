#!/bin/bash

# Complete System Cleanup Script
# This removes EVERYTHING Docker-related for the Agentic AI Framework

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Complete Agentic AI Framework Cleanup${NC}"
echo -e "${YELLOW}This will remove ALL Docker containers, images, volumes, and networks!${NC}"
echo ""

# Warning prompt
read -p "Are you sure you want to proceed? This cannot be undone! (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}Starting complete cleanup...${NC}"

# Step 1: Stop and remove project containers
echo -e "${BLUE}1. Stopping and removing project containers...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true
docker stop agentic-ai-framework agentic-ai-ollama agentic-ai-model-downloader agentic-ai-model-setup 2>/dev/null || true
docker rm agentic-ai-framework agentic-ai-ollama agentic-ai-model-downloader agentic-ai-model-setup 2>/dev/null || true

# Step 2: Remove project-specific images
echo -e "${BLUE}2. Removing project images...${NC}"
docker rmi agentic_ai_framework-agentic-ai agentic_ai_framework_agentic-ai 2>/dev/null || true
docker rmi $(docker images --filter "reference=agentic*" -q) 2>/dev/null || true

# Step 3: Remove Ollama images
echo -e "${BLUE}3. Removing Ollama images...${NC}"
docker rmi ollama/ollama:latest 2>/dev/null || true
docker rmi $(docker images --filter "reference=ollama/*" -q) 2>/dev/null || true

# Step 4: Remove project volumes
echo -e "${BLUE}4. Removing project volumes...${NC}"
docker volume rm agentic_ai_framework_ollama_data 2>/dev/null || true
docker volume rm $(docker volume ls --filter "name=agentic" -q) 2>/dev/null || true

# Step 5: Remove project networks
echo -e "${BLUE}5. Removing project networks...${NC}"
docker network rm agentic_ai_framework_agentic-network 2>/dev/null || true
docker network rm $(docker network ls --filter "name=agentic" -q) 2>/dev/null || true

# Step 6: Clean up dangling resources
echo -e "${BLUE}6. Cleaning up dangling resources...${NC}"
docker system prune -f
docker volume prune -f
docker network prune -f

# Step 7: Optional - Complete Docker cleanup
echo ""
echo -e "${YELLOW}Do you want to remove ALL Docker images and containers (not just this project)?${NC}"
read -p "This will clean your entire Docker system (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}7. Complete Docker system cleanup...${NC}"
    docker stop $(docker ps -aq) 2>/dev/null || true
    docker rm $(docker ps -aq) 2>/dev/null || true
    docker rmi $(docker images -q) 2>/dev/null || true
    docker volume rm $(docker volume ls -q) 2>/dev/null || true
    docker network rm $(docker network ls -q) 2>/dev/null || true
    docker system prune -af --volumes
else
    echo -e "${BLUE}7. Skipping complete Docker cleanup${NC}"
fi

# Step 8: Clean local data
echo -e "${BLUE}8. Cleaning local data files...${NC}"
read -p "Remove local data directory (database, logs)? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf data/
    rm -rf logs/
    rm -rf backups/
    echo -e "${GREEN}✅ Local data removed${NC}"
else
    echo -e "${BLUE}ℹ️ Keeping local data${NC}"
fi

# Step 9: Show final status
echo ""
echo -e "${GREEN}🎉 Cleanup completed!${NC}"
echo ""
echo -e "${BLUE}Current Docker status:${NC}"
echo "Containers:"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>/dev/null || echo "None"
echo ""
echo "Images:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null || echo "None" 
echo ""
echo "Volumes:"
docker volume ls --format "table {{.Name}}\t{{.Driver}}" 2>/dev/null || echo "None"
echo ""
echo -e "${GREEN}✅ System is now clean and ready for fresh deployment!${NC}"