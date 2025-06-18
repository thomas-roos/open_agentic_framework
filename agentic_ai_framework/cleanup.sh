#!/bin/bash

# Complete System Cleanup Script
# This removes EVERYTHING Docker-related for the Open Agentic Framework
# BUT preserves Ollama images to avoid re-downloading models

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Complete Open Agentic Framework Cleanup${NC}"
echo -e "${YELLOW}This will remove project containers, images, volumes, and networks!${NC}"
echo -e "${GREEN}✅ Ollama images will be preserved to avoid re-downloading models${NC}"
echo ""

# Warning prompt
read -p "Are you sure you want to proceed? This cannot be undone! (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}Starting cleanup (preserving Ollama images)...${NC}"

# Step 1: Stop and remove project containers
echo -e "${BLUE}1. Stopping and removing project containers...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true
docker stop agentic-ai-framework agentic-ai-ollama agentic-ai-model-downloader agentic-ai-model-setup 2>/dev/null || true
docker rm agentic-ai-framework agentic-ai-ollama agentic-ai-model-downloader agentic-ai-model-setup 2>/dev/null || true

# Step 2: Remove project-specific images (excluding Ollama)
echo -e "${BLUE}2. Removing project images (preserving Ollama)...${NC}"
docker rmi agentic_ai_framework-agentic-ai agentic_ai_framework_agentic-ai 2>/dev/null || true

# Remove project images but exclude Ollama images
PROJECT_IMAGES=$(docker images --filter "reference=agentic*" --format "{{.Repository}}:{{.Tag}}" | grep -v ollama || true)
if [ ! -z "$PROJECT_IMAGES" ]; then
    echo "$PROJECT_IMAGES" | xargs -r docker rmi 2>/dev/null || true
fi

# Step 3: Preserve Ollama images (skip removal)
echo -e "${GREEN}3. Preserving Ollama images and models...${NC}"
OLLAMA_IMAGES=$(docker images --filter "reference=ollama/*" --format "{{.Repository}}:{{.Tag}}" || true)
if [ ! -z "$OLLAMA_IMAGES" ]; then
    echo -e "${GREEN}   Found Ollama images to preserve:${NC}"
    echo "$OLLAMA_IMAGES" | sed 's/^/   - /'
else
    echo -e "${YELLOW}   No Ollama images found${NC}"
fi

# Step 4: Remove project volumes (but preserve Ollama data optionally)
echo -e "${BLUE}4. Handling project volumes...${NC}"
echo -e "${YELLOW}Do you want to preserve Ollama model data? (Recommended: y)${NC}"
read -p "Keep Ollama models and data to avoid re-downloading? (Y/n): " -r
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${GREEN}   Preserving Ollama data volume...${NC}"
    # Remove only non-Ollama project volumes
    docker volume ls --filter "name=agentic" --format "{{.Name}}" | grep -v ollama | xargs -r docker volume rm 2>/dev/null || true
else
    echo -e "${YELLOW}   Removing ALL project volumes including Ollama data...${NC}"
    docker volume rm agentic_ai_framework_ollama_data 2>/dev/null || true
    docker volume rm $(docker volume ls --filter "name=agentic" -q) 2>/dev/null || true
fi

# Step 5: Remove project networks
echo -e "${BLUE}5. Removing project networks...${NC}"
docker network rm agentic_ai_framework_agentic-network 2>/dev/null || true
docker network rm $(docker network ls --filter "name=agentic" -q) 2>/dev/null || true

# Step 6: Clean up dangling resources (but preserve Ollama)
echo -e "${BLUE}6. Cleaning up dangling resources...${NC}"
# First, get list of Ollama image IDs to exclude from cleanup
OLLAMA_IMAGE_IDS=$(docker images --filter "reference=ollama/*" -q | tr '\n' ' ' || true)

# Clean up dangling images, but be careful not to remove Ollama images
docker system prune -f
docker volume prune -f
docker network prune -f

# Only remove dangling images that are not Ollama images
DANGLING_IMAGES=$(docker images -f "dangling=true" -q || true)
if [ ! -z "$DANGLING_IMAGES" ] && [ ! -z "$OLLAMA_IMAGE_IDS" ]; then
    # Filter out Ollama images from dangling images
    SAFE_TO_REMOVE=$(echo "$DANGLING_IMAGES" | grep -v -F "$OLLAMA_IMAGE_IDS" || true)
    if [ ! -z "$SAFE_TO_REMOVE" ]; then
        echo "$SAFE_TO_REMOVE" | xargs -r docker rmi 2>/dev/null || true
    fi
elif [ ! -z "$DANGLING_IMAGES" ] && [ -z "$OLLAMA_IMAGE_IDS" ]; then
    # No Ollama images, safe to remove all dangling
    echo "$DANGLING_IMAGES" | xargs -r docker rmi 2>/dev/null || true
fi

# Step 7: Optional - Complete Docker cleanup (with Ollama preservation)
echo ""
echo -e "${YELLOW}Do you want to remove ALL other Docker images and containers?${NC}"
echo -e "${GREEN}(Ollama images will still be preserved)${NC}"
read -p "Clean entire Docker system except Ollama? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}7. Complete Docker system cleanup (preserving Ollama)...${NC}"
    
    # Stop and remove all containers
    docker stop $(docker ps -aq) 2>/dev/null || true
    docker rm $(docker ps -aq) 2>/dev/null || true
    
    # Remove all images except Ollama
    ALL_IMAGES=$(docker images -q || true)
    OLLAMA_IMAGES_TO_KEEP=$(docker images --filter "reference=ollama/*" -q || true)
    
    if [ ! -z "$ALL_IMAGES" ] && [ ! -z "$OLLAMA_IMAGES_TO_KEEP" ]; then
        IMAGES_TO_REMOVE=$(echo "$ALL_IMAGES" | grep -v -F "$OLLAMA_IMAGES_TO_KEEP" || true)
        if [ ! -z "$IMAGES_TO_REMOVE" ]; then
            echo "$IMAGES_TO_REMOVE" | xargs -r docker rmi -f 2>/dev/null || true
        fi
    elif [ ! -z "$ALL_IMAGES" ] && [ -z "$OLLAMA_IMAGES_TO_KEEP" ]; then
        echo "$ALL_IMAGES" | xargs -r docker rmi -f 2>/dev/null || true
    fi
    
    # Remove volumes and networks (with Ollama data preservation option handled above)
    docker volume prune -f
    docker network prune -f
else
    echo -e "${BLUE}7. Skipping complete Docker cleanup${NC}"
fi

# Step 8: Clean local data
echo -e "${BLUE}8. Cleaning local data files...${NC}"
read -p "Remove local data directory (database, logs)? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Preserve any Ollama-related local data if it exists
    if [ -d "data/ollama" ]; then
        echo -e "${YELLOW}   Found local Ollama data, creating backup...${NC}"
        mkdir -p backups/
        cp -r data/ollama backups/ollama_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    fi
    
    rm -rf data/
    rm -rf logs/
    # Keep one backup directory with Ollama data if it was backed up
    find backups/ -name "ollama_backup_*" -type d | head -1 | xargs -I {} sh -c 'echo "Keeping latest Ollama backup: {}"' || true
    find backups/ -name "ollama_backup_*" -type d | tail -n +2 | xargs -r rm -rf || true
    
    echo -e "${GREEN}✅ Local data removed (Ollama data backed up if found)${NC}"
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

# Show preserved Ollama status
PRESERVED_OLLAMA=$(docker images --filter "reference=ollama/*" --format "{{.Repository}}:{{.Tag}}" || true)
if [ ! -z "$PRESERVED_OLLAMA" ]; then
    echo -e "${GREEN}✅ Preserved Ollama images:${NC}"
    echo "$PRESERVED_OLLAMA" | sed 's/^/   - /'
    echo ""
fi

echo -e "${GREEN}✅ System is clean and ready for fresh deployment!${NC}"
echo -e "${GREEN}✅ Your Ollama models are preserved and ready to use!${NC}"