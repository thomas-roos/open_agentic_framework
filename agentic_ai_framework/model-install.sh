#!/bin/bash
echo "Downloading TinyLlama 1.1B..."
docker exec -it agentic-ai-ollama ollama pull tinyllama:1.1b

echo "Downloading Granite 3.2 2B..."
docker exec -it agentic-ai-ollama ollama pull granite3.2:2b

echo "Downloading DeepSeek-R1 1.5B..."
docker exec -it agentic-ai-ollama ollama pull deepseek-r1:1.5b

echo "All models downloaded!"