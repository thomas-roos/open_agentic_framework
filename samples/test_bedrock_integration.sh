#!/bin/bash

echo "=== Testing AWS Bedrock Integration ==="

# Check if the framework is running
echo "1. Checking framework health..."
curl -s http://localhost:8000/health | jq .

# Check providers (should include bedrock if enabled)
echo -e "\n2. Checking available providers..."
curl -s http://localhost:8000/providers | jq .

# Test Bedrock provider specifically (if enabled)
echo -e "\n3. Testing Bedrock provider..."
curl -s http://localhost:8000/providers/bedrock | jq . 2>/dev/null || echo "Bedrock provider not configured or not available"

# List all models (should include Bedrock models if available)
echo -e "\n4. Listing all available models..."
curl -s http://localhost:8000/models/detailed | jq .

# Test Bedrock model (if available)
echo -e "\n5. Testing Bedrock model..."
curl -s -X POST "http://localhost:8000/models/test/anthropic.claude-3-sonnet-20240229-v1:0" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, this is a test of AWS Bedrock integration.", "max_tokens": 50}' | jq . 2>/dev/null || echo "Bedrock model test failed or model not available"

echo -e "\n=== Bedrock Integration Test Complete ==="
echo "Note: Bedrock will only work if:"
echo "1. BEDROCK_ENABLED=true is set in environment"
echo "2. AWS credentials are properly configured"
echo "3. Bedrock access is enabled in your AWS account" 