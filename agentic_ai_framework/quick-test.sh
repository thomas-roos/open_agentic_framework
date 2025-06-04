#!/bin/bash
# quick-test.sh - Quick model performance test

# Simple script to quickly test which model works best
API_BASE="http://localhost:8000"

echo "🚀 Quick Model Performance Test"
echo "==============================="

# Test each model with a simple task
test_model() {
    local model=$1
    echo "Testing $model..."
    
    # Create agent
    agent_name="quick_test_${model//[:.]/_}"
    
    curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"$agent_name\",
        \"role\": \"Tool Tester\",
        \"goals\": \"Use website_monitor tool to check websites\",
        \"backstory\": \"You use tools via TOOL_CALL format. Example: TOOL_CALL: website_monitor(url=https://google.com, expected_status=200). Never write code.\",
        \"tools\": [\"website_monitor\"],
        \"ollama_model\": \"$model\",
        \"enabled\": true
      }" >/dev/null
    
    # Test the agent
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check if https://google.com returns HTTP 200",
        "context": {}
      }')
    
    # Check if it used the tool correctly
    if echo "$response" | grep -q "TOOL_CALL.*website_monitor"; then
        echo "✓ $model: WORKS - Tool call detected"
    else
        echo "✗ $model: FAILED - No tool call"
    fi
    
    # Cleanup
    curl -s -X DELETE "$API_BASE/agents/$agent_name" >/dev/null
}

# Wait for API
echo "Waiting for API..."
while ! curl -s "$API_BASE/health" >/dev/null 2>&1; do
    echo "."
    sleep 2
done

echo "API ready! Testing models..."
echo ""

# Test all models
test_model "smollm:135m"
test_model "tinyllama:1.1b"
test_model "granite3.2:1b"
test_model "deepseek-coder:1.3b"
test_model "deepseek-r1:1.5b"

echo ""
echo "Quick test complete!"
echo "Run ./test-model-performance.sh for detailed analysis"