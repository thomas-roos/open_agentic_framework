#!/bin/bash
# docker/start.sh

set -e

echo "Starting Multi-Agent System..."

# Start Ollama service in background
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Ollama failed to start after 30 attempts"
        exit 1
    fi
    echo "Attempt $i: Ollama not ready yet, waiting..."
    sleep 2
done

# Pull the lightweight model
echo "Pulling lightweight LLM model..."
ollama pull llama3.2:1b

# Verify model is available
echo "Verifying model availability..."
ollama list

# Initialize the application
echo "Initializing Multi-Agent System..."
cd /app

# Run database migrations/setup if needed
python -c "
from memory.memory_system import SQLiteMemorySystem
from scheduler.scheduler_system import TaskScheduler

# Initialize memory system
print('Initializing memory system...')
memory = SQLiteMemorySystem('/app/memory/agent_memory.db')

# Initialize scheduler
print('Initializing scheduler...')
scheduler = TaskScheduler('/app/scheduler/scheduler.db')

print('Initialization complete!')
"

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn api.rest_server:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 1 \
    --log-level info \
    --access-log \
    --use-colors