#!/bin/bash
# dynamic-quick-test.sh - Dynamic model performance test that discovers available models

# Configuration
API_BASE="http://localhost:8000"
MAX_MODELS=10  # Limit number of models to test to prevent overload
TIMEOUT=30     # Timeout for each model test in seconds

echo "🚀 Dynamic Model Performance Test"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local model=$2
    local message=$3
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✓${NC} $model: ${GREEN}WORKS${NC} - $message"
            ;;
        "FAILED")
            echo -e "${RED}✗${NC} $model: ${RED}FAILED${NC} - $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} $model: ${BLUE}INFO${NC} - $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠${NC} $model: ${YELLOW}WARNING${NC} - $message"
            ;;
    esac
}

# Wait for API to be ready
wait_for_api() {
    echo "Checking API availability..."
    local retries=30
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s "$API_BASE/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} API is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        ((count++))
    done
    
    echo -e "${RED}✗${NC} API not available after $((retries * 2)) seconds"
    exit 1
}

# Get list of available models
get_available_models() {
    echo "Discovering available models..."
    
    local models_response
    models_response=$(curl -s "$API_BASE/models" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$models_response" ]; then
        echo -e "${RED}✗${NC} Failed to fetch available models"
        exit 1
    fi
    
    # Parse JSON array and extract model names
    local models
    models=$(echo "$models_response" | jq -r '.[]' 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$models" ]; then
        echo -e "${RED}✗${NC} Failed to parse models response"
        echo "Raw response: $models_response"
        exit 1
    fi
    
    # Count models
    local model_count
    model_count=$(echo "$models" | wc -l)
    
    echo -e "${GREEN}✓${NC} Found $model_count available models:"
    echo "$models" | sed 's/^/  - /'
    echo ""
    
    # Limit number of models if too many
    if [ "$model_count" -gt "$MAX_MODELS" ]; then
        echo -e "${YELLOW}⚠${NC} Too many models ($model_count). Testing only first $MAX_MODELS models."
        models=$(echo "$models" | head -n "$MAX_MODELS")
    fi
    
    echo "$models"
}

# Test individual model
test_model() {
    local model=$1
    local test_timeout=${2:-$TIMEOUT}
    
    echo ""
    echo -e "${BLUE}Testing model: $model${NC}"
    echo "$(printf '%.0s-' {1..50})"
    
    # Sanitize model name for agent name (replace special chars with underscores)
    local agent_name="quick_test_$(echo "$model" | sed 's/[^a-zA-Z0-9]/_/g')"
    
    # Create agent with timeout
    echo "Creating test agent: $agent_name"
    local create_response
    create_response=$(timeout $test_timeout curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"$agent_name\",
        \"role\": \"Tool Tester\",
        \"goals\": \"Use website_monitor tool to check websites efficiently\",
        \"backstory\": \"You are a testing agent that uses tools via TOOL_CALL format. Example: TOOL_CALL: website_monitor(url=https://google.com, expected_status=200). Always use tools, never write code.\",
        \"tools\": [\"website_monitor\"],
        \"ollama_model\": \"$model\",
        \"enabled\": true
      }" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_status "FAILED" "$model" "Agent creation timed out"
        return 1
    fi
    
    # Check if agent was created successfully
    if echo "$create_response" | grep -q "error\|Error\|failed\|Failed"; then
        print_status "FAILED" "$model" "Agent creation failed: $(echo "$create_response" | jq -r '.detail // .error // .message' 2>/dev/null)"
        return 1
    fi
    
    # Test the agent with timeout
    echo "Executing test task..."
    local test_response
    test_response=$(timeout $test_timeout curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check if https://google.com returns HTTP 200 status. Use the website_monitor tool.",
        "context": {}
      }' 2>/dev/null)
    
    local curl_exit_code=$?
    
    # Cleanup agent (always attempt cleanup)
    curl -s -X DELETE "$API_BASE/agents/$agent_name" >/dev/null 2>&1
    
    if [ $curl_exit_code -ne 0 ]; then
        print_status "FAILED" "$model" "Test execution timed out after ${test_timeout}s"
        return 1
    fi
    
    # Analyze response
    analyze_test_result "$model" "$test_response"
}

# Analyze test results
analyze_test_result() {
    local model=$1
    local response=$2
    
    # Check for API errors first
    if echo "$response" | grep -q "error\|Error\|failed\|Failed\|exception\|Exception"; then
        local error_msg
        error_msg=$(echo "$response" | jq -r '.detail // .error // .message' 2>/dev/null | head -c 100)
        print_status "FAILED" "$model" "API Error: $error_msg"
        return 1
    fi
    
    # Extract result content
    local result_content
    result_content=$(echo "$response" | jq -r '.result' 2>/dev/null)
    
    if [ -z "$result_content" ] || [ "$result_content" = "null" ]; then
        print_status "FAILED" "$model" "No result content in response"
        return 1
    fi
    
    # Show first 150 characters of response for debugging
    echo "Response preview: $(echo "$result_content" | head -c 150)..."
    
    # Multiple success indicators (ordered by preference)
    if echo "$result_content" | grep -qi "TOOL_CALL.*website_monitor"; then
        print_status "SUCCESS" "$model" "Perfect tool call format detected"
        return 0
    elif echo "$result_content" | grep -qi "status_code.*200\|\"status_code\": 200"; then
        print_status "SUCCESS" "$model" "HTTP 200 status detected (tool executed)"
        return 0
    elif echo "$result_content" | grep -qi "response_time_ms\|response_time"; then
        print_status "SUCCESS" "$model" "Response time data detected (tool executed)"
        return 0
    elif echo "$result_content" | grep -qi "website.*online\|site.*online\|status.*online"; then
        print_status "SUCCESS" "$model" "Website online status detected"
        return 0
    elif echo "$result_content" | grep -qi "google\.com.*accessible\|google\.com.*reachable"; then
        print_status "SUCCESS" "$model" "Website accessibility confirmed"
        return 0
    elif echo "$result_content" | grep -qi "successfully.*checked\|check.*successful"; then
        print_status "SUCCESS" "$model" "Successful check detected"
        return 0
    elif echo "$result_content" | grep -qi "used.*website_monitor\|website_monitor.*tool"; then
        print_status "SUCCESS" "$model" "Tool usage detected"
        return 0
    else
        print_status "FAILED" "$model" "No tool usage indicators detected"
        echo "  Full result: $(echo "$result_content" | head -c 200)..."
        return 1
    fi
}

# Get model performance summary
get_model_summary() {
    echo ""
    echo "📊 Model Performance Summary"
    echo "============================"
    echo ""
    echo "SUCCESS INDICATORS (in order of preference):"
    echo "1. 🎯 Perfect tool call format (TOOL_CALL: website_monitor(...))"
    echo "2. ✅ HTTP 200 status detected (tool actually executed)"
    echo "3. ⏱️  Response time data (tool provided metrics)"
    echo "4. 🌐 Website online status (tool result interpreted)"
    echo "5. 🔗 Website accessibility confirmed"
    echo "6. ✓ Successful check detected"
    echo "7. 🔧 Tool usage detected"
    echo ""
    echo "Best models show indicator #1 or #2"
    echo "Acceptable models show indicators #3-#7"
    echo "Failed models show none of these indicators"
}

# Enhanced model installation check
check_and_install_models() {
    echo "Checking for recommended models..."
    
    local recommended_models=("tinyllama:1.1b" "granite3.2:2b" "deepseek-r1:1.5b")
    local available_models
    
    # Get current models
    available_models=$(curl -s "$API_BASE/models" | jq -r '.[]' 2>/dev/null)
    
    for rec_model in "${recommended_models[@]}"; do
        if ! echo "$available_models" | grep -q "$rec_model"; then
            echo -e "${YELLOW}⚠${NC} Recommended model '$rec_model' not found."
            read -p "Install $rec_model? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "Installing $rec_model..."
                curl -X POST "$API_BASE/models/install" \
                  -H "Content-Type: application/json" \
                  -d "{\"model_name\": \"$rec_model\", \"wait_for_completion\": true}"
                echo ""
            fi
        fi
    done
}

# Main execution
main() {
    # Check for required tools
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}✗${NC} jq is required but not installed. Please install jq first."
        echo "Ubuntu/Debian: sudo apt-get install jq"
        echo "macOS: brew install jq"
        exit 1
    fi
    
    # Wait for API
    wait_for_api
    
    # Check for recommended models
    if [ "${1:-}" = "--install" ]; then
        check_and_install_models
    fi
    
    # Get available models
    local available_models
    available_models=$(get_available_models)
    
    if [ -z "$available_models" ]; then
        echo -e "${RED}✗${NC} No models available for testing"
        exit 1
    fi
    
    # Test each model
    local total_models=0
    local successful_models=0
    local failed_models=0
    
    echo "Starting model tests..."
    
    while IFS= read -r model; do
        if [ -n "$model" ]; then
            ((total_models++))
            if test_model "$model"; then
                ((successful_models++))
            else
                ((failed_models++))
            fi
        fi
    done <<< "$available_models"
    
    # Final summary
    echo ""
    echo "🎉 Testing Complete!"
    echo "===================="
    echo -e "Total models tested: ${BLUE}$total_models${NC}"
    echo -e "Successful: ${GREEN}$successful_models${NC}"
    echo -e "Failed: ${RED}$failed_models${NC}"
    echo ""
    
    if [ $successful_models -gt 0 ]; then
        echo -e "${GREEN}✓${NC} You have working models! Use them for your agents."
    else
        echo -e "${YELLOW}⚠${NC} No models are working properly. Consider:"
        echo "  1. Installing recommended models: $0 --install"
        echo "  2. Checking Ollama is running: docker logs ollama"
        echo "  3. Reviewing agent manager configuration"
    fi
    
    get_model_summary
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [--install] [--help]"
        echo ""
        echo "Options:"
        echo "  --install    Offer to install recommended models if missing"
        echo "  --help       Show this help message"
        echo ""
        echo "This script dynamically discovers available models and tests each one"
        echo "for proper tool usage with the website_monitor tool."
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac