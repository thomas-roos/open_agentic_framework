#!/bin/bash

# Test the improved agent
echo
echo "Testing improved agent with pkg:npm/lodash@4.17.21..."
curl -X POST "http://localhost:8000/agents/purl_parser/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "pkg:npm/lodash@4.17.21",
    "context": {}
  }'

echo
echo
echo "Testing improved agent with pkg:npm/@types/node@18.0.0..."
curl -X POST "http://localhost:8000/agents/purl_parser/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "pkg:npm/@types/node@18.0.0", 
    "context": {}
  }'

echo
echo
echo "Testing improved agent with pkg:pypi/requests@2.28.1..."
curl -X POST "http://localhost:8000/agents/purl_parser/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "pkg:pypi/requests@2.28.1",
    "context": {}
  }'