#!/bin/bash

# Test script for the data extractor tool

echo "Testing Data Extractor Tool..."

# Test 1: Simple JSON extraction
echo "Test 1: Simple JSON extraction"
curl -X POST "http://localhost:8000/tools/data_extractor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "source_data": "{\"licensed\": {\"declared\": \"MIT\"}, \"scores\": {\"overall\": 85}, \"described\": {\"sourceLocation\": {\"url\": \"https://github.com/lodash/lodash\"}}}",
      "extractions": [
        {
          "name": "license",
          "type": "path",
          "query": "licensed.declared",
          "default": "Unknown"
        },
        {
          "name": "score",
          "type": "path",
          "query": "scores.overall",
          "format": "number",
          "default": 0
        },
        {
          "name": "source_url",
          "type": "path",
          "query": "described.sourceLocation.url",
          "default": "Not found"
        }
      ],
      "output_format": "object"
    }
  }'

echo -e "\n\n"

# Test 2: Test with missing fields (should use defaults)
echo "Test 2: Missing fields with defaults"
curl -X POST "http://localhost:8000/tools/data_extractor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "source_data": "{\"some\": \"data\"}",
      "extractions": [
        {
          "name": "missing_field",
          "type": "path",
          "query": "nonexistent.field",
          "default": "DEFAULT_VALUE"
        }
      ]
    }
  }'

echo -e "\n\n"

# Test 3: Test the actual workflow step by step
echo "Test 3: Testing workflow components"

echo "Step 1: Parse PURL"
PURL_RESPONSE=$(curl -s -X POST "http://localhost:8000/agents/purl_parser/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "pkg:npm/lodash@4.17.21"
  }')

echo "PURL Response: $PURL_RESPONSE"

# Extract URL from PURL response (basic extraction)
URL=$(echo "$PURL_RESPONSE" | grep -o 'https://api.clearlydefined.io[^"]*' | head -1)
echo "Extracted URL: $URL"

if [ ! -z "$URL" ]; then
    echo "Step 2: Test HTTP Client"
    HTTP_RESPONSE=$(curl -s -X POST "http://localhost:8000/tools/http_client/execute" \
      -H "Content-Type: application/json" \
      -d "{
        \"parameters\": {
          \"url\": \"$URL\",
          \"method\": \"GET\",
          \"timeout\": 30
        }
      }")
    
    echo "HTTP Response status: $(echo "$HTTP_RESPONSE" | grep -o '\"status_code\":[0-9]*' | head -1)"
    
    echo "Step 3: Test Data Extractor with real API response"
    # Use a simple extraction that should work
    curl -X POST "http://localhost:8000/tools/data_extractor/execute" \
      -H "Content-Type: application/json" \
      -d "{
        \"parameters\": {
          \"source_data\": $(echo "$HTTP_RESPONSE" | jq '.content'),
          \"extractions\": [
            {
              \"name\": \"test_license\",
              \"type\": \"path\",
              \"query\": \"licensed.declared\",
              \"default\": \"Unknown\"
            }
          ]
        }
      }"
fi

echo -e "\n\nDone!"
