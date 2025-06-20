#!/bin/bash

# Open Agentic Framework - Web UI Startup Script

echo "🚀 Starting Open Agentic Framework with Web UI..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start the containers
echo "📦 Building and starting containers..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if the main service is healthy
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Services are ready!"
    echo ""
    echo "🌐 Access your services:"
    echo "   Web UI:        http://localhost:8000/ui"
    echo "   API Docs:      http://localhost:8000/docs"
    echo "   Health Check:  http://localhost:8000/health"
    echo ""
    echo "📊 Monitor logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
else
    echo "❌ Services are not ready yet. Check logs with: docker-compose logs"
    exit 1
fi 