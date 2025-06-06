#!/bin/bash
# enhanced-model-test.sh - Enhanced model test with better prompting and full output

# Configuration
API_BASE="http://localhost:8000"
MAX_MODELS=10
TIMEOUT=120
LOG_DIR="/tmp/model_test_logs"

echo "🚀 Enhanced Model Performance Test"
echo "=================================="

# Create log directory
mkdir -p "$LOG_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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
        "TIMEOUT")
            echo -e "${PURPLE}⏱${NC} $model: ${PURPLE}TIMEOUT${NC} - $message"
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
    
    # Get models from API
    local models_response
    models_response=$(curl -s "$API_BASE/models" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$models_response" ]; then
        echo -e "${RED}✗${NC} Failed to fetch available models"
        return 1
    fi
    
    # Check if response is valid JSON array
    if ! echo "$models_response" | jq -e 'type == "array"' >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} Invalid response format from models API"
        echo "Response: $models_response"
        return 1
    fi
    
    # Parse JSON array and extract model names
    local models
    models=$(echo "$models_response" | jq -r '.[]' 2>/dev/null | grep -v '^null$' | head -n "$MAX_MODELS")
    
    if [ -z "$models" ]; then
        echo -e "${RED}✗${NC} No models found in API response"
        echo "Response: $models_response"
        return 1
    fi
    
    # Count models
    local model_count
    model_count=$(echo "$models" | wc -l)
    
    echo -e "${GREEN}✓${NC} Found $model_count available models:"
    echo "$models" | sed 's/^/  - /'
    echo ""
    
    # Store models in a temporary file for iteration
    echo "$models" > /tmp/models_to_test.txt
    return 0
}

# Test individual model with enhanced prompting
test_model() {
    local model="$1"
    local test_timeout=${2:-$TIMEOUT}
    
    echo ""
    echo -e "${CYAN}===========================================${NC}"
    echo -e "${BLUE}Testing model: $model${NC}"
    echo -e "${CYAN}===========================================${NC}"
    
    # Validate model name
    if [ -z "$model" ] || [ "$model" = "null" ]; then
        print_status "FAILED" "$model" "Invalid model name"
        return 1
    fi
    
    # Sanitize model name for agent name
    local agent_name="enhanced_test_$(echo "$model" | sed 's/[^a-zA-Z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//g' | sed 's/_$//g')"
    
    # Ensure agent name is valid
    if [ ${#agent_name} -gt 50 ]; then
        agent_name="${agent_name:0:50}"
    fi
    
    echo "Creating enhanced test agent: $agent_name"
    
    # Enhanced agent payload with very explicit tool usage instructions
    local agent_payload
    agent_payload=$(jq -n \
        --arg name "$agent_name" \
        --arg model "$model" \
        '{
            name: $name,
            role: "Tool-Using Website Monitor",
            goals: "ALWAYS use the website_monitor tool to check websites. Never write code or explain how to do it manually. Only use tools.",
            backstory: "You are a specialized agent that MUST use tools to complete tasks. When asked to check a website, you MUST use the website_monitor tool in this exact format: TOOL_CALL: website_monitor(url=\"https://example.com\", expected_status=200). You never write Python code or explain manual methods. You only use the available tools. If a task requires checking a website, you immediately use the website_monitor tool.",
            tools: ["website_monitor"],
            ollama_model: $model,
            enabled: true
        }')
    
    # Create agent with timeout
    echo "Creating agent..."
    local create_response
    create_response=$(timeout $test_timeout curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "$agent_payload" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_status "TIMEOUT" "$model" "Agent creation timed out"
        return 1
    fi
    
    # Check if agent was created successfully
    if echo "$create_response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        local error_msg
        error_msg=$(echo "$create_response" | jq -r '.detail // .error // .message' 2>/dev/null)
        print_status "FAILED" "$model" "Agent creation failed: $error_msg"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} Agent created successfully"
    
    # Enhanced task payload with very explicit instructions
    local task_payload
    task_payload=$(jq -n '{
        task: "Use the website_monitor tool to check if https://google.com returns HTTP 200 status. You MUST use the website_monitor tool - do not write code or explain how to do it manually. Use this exact format: TOOL_CALL: website_monitor(url=\"https://google.com\", expected_status=200)",
        context: {
            "instruction": "MANDATORY: Use website_monitor tool only",
            "format": "TOOL_CALL: website_monitor(url=URL, expected_status=200)",
            "no_code": "Never write Python/code, only use tools"
        }
    }')
    
    # Test the agent with extended timeout
    echo "Executing test task (timeout: ${test_timeout}s)..."
    echo "Task: Check https://google.com using website_monitor tool"
    
    local start_time=$(date +%s)
    local test_response
    test_response=$(timeout $test_timeout curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d "$task_payload" 2>/dev/null)
    
    local curl_exit_code=$?
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))
    
    echo "Execution time: ${execution_time}s"
    
    # Always cleanup agent
    echo "Cleaning up agent..."
    curl -s -X DELETE "$API_BASE/agents/$agent_name" >/dev/null 2>&1
    
    if [ $curl_exit_code -ne 0 ]; then
        print_status "TIMEOUT" "$model" "Test execution timed out after ${test_timeout}s"
        return 1
    fi
    
    # Save full response to log file
    local log_file="$LOG_DIR/${model//[^a-zA-Z0-9]/_}_response.json"
    echo "$test_response" > "$log_file"
    
    # Analyze response
    analyze_test_result "$model" "$test_response" "$log_file"
}

# Enhanced result analysis
analyze_test_result() {
    local model="$1"
    local response="$2"
    local log_file="$3"
    
    echo ""
    echo -e "${YELLOW}📋 Full Response Analysis for $model:${NC}"
    echo "----------------------------------------"
    
    # Check for API errors first
    if echo "$response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        local error_msg
        error_msg=$(echo "$response" | jq -r '.detail // .error // .message' 2>/dev/null)
        print_status "FAILED" "$model" "API Error: $error_msg"
        echo -e "${RED}Error details saved to: $log_file${NC}"
        return 1
    fi
    
    # Extract result content
    local result_content
    result_content=$(echo "$response" | jq -r '.result' 2>/dev/null)
    
    if [ -z "$result_content" ] || [ "$result_content" = "null" ]; then
        print_status "FAILED" "$model" "No result content in response"
        echo -e "${RED}Empty response saved to: $log_file${NC}"
        return 1
    fi
    
    # Print full result with formatting
    echo -e "${CYAN}📄 FULL RESPONSE:${NC}"
    echo "=================="
    echo "$result_content"
    echo "=================="
    echo ""
    
    # Detailed analysis with multiple checks
    echo -e "${YELLOW}🔍 Analysis Results:${NC}"
    
    local success_score=0
    local indicators_found=()
    
    # Check for different success patterns
    if echo "$result_content" | grep -qi "TOOL_CALL.*website_monitor"; then
        indicators_found+=("Perfect TOOL_CALL format")
        success_score=$((success_score + 10))
    fi
    
    if echo "$result_content" | grep -qi "status_code.*200\|\"status_code\": 200\|status.*200"; then
        indicators_found+=("HTTP 200 status detected")
        success_score=$((success_score + 8))
    fi
    
    if echo "$result_content" | grep -qi "response_time_ms\|response_time\|time.*ms"; then
        indicators_found+=("Response time data")
        success_score=$((success_score + 6))
    fi
    
    if echo "$result_content" | grep -qi "website.*online\|site.*online\|status.*online\|google.*online"; then
        indicators_found+=("Website online status")
        success_score=$((success_score + 5))
    fi
    
    if echo "$result_content" | grep -qi "google\.com.*accessible\|google\.com.*reachable\|google.*accessible"; then
        indicators_found+=("Website accessibility")
        success_score=$((success_score + 4))
    fi
    
    if echo "$result_content" | grep -qi "successfully.*checked\|check.*successful\|monitoring.*successful"; then
        indicators_found+=("Successful check")
        success_score=$((success_score + 3))
    fi
    
    if echo "$result_content" | grep -qi "used.*website_monitor\|website_monitor.*tool\|tool.*executed"; then
        indicators_found+=("Tool usage detected")
        success_score=$((success_score + 2))
    fi
    
    if echo "$result_content" | grep -qi "https\?://google\.com"; then
        indicators_found+=("URL mentioned")
        success_score=$((success_score + 1))
    fi
    
    # Check for negative indicators (code writing)
    local negative_indicators=()
    if echo "$result_content" | grep -qi "import\|def \|python\|http\.client\|requests\|urllib"; then
        negative_indicators+=("Code writing detected")
        success_score=$((success_score - 5))
    fi
    
    if echo "$result_content" | grep -qi "here.*example\|here.*how\|you.*can\|example.*code"; then
        negative_indicators+=("Manual explanation instead of tool use")
        success_score=$((success_score - 3))
    fi
    
    # Display findings
    echo "Success Score: $success_score/10"
    echo ""
    
    if [ ${#indicators_found[@]} -gt 0 ]; then
        echo -e "${GREEN}✓ Positive Indicators Found:${NC}"
        for indicator in "${indicators_found[@]}"; do
            echo "  • $indicator"
        done
        echo ""
    fi
    
    if [ ${#negative_indicators[@]} -gt 0 ]; then
        echo -e "${RED}✗ Negative Indicators Found:${NC}"
        for indicator in "${negative_indicators[@]}"; do
            echo "  • $indicator"
        done
        echo ""
    fi
    
    # Final determination
    if [ $success_score -ge 8 ]; then
        print_status "SUCCESS" "$model" "Excellent tool usage (Score: $success_score/10)"
        echo -e "${GREEN}💾 Response saved to: $log_file${NC}"
        return 0
    elif [ $success_score -ge 5 ]; then
        print_status "SUCCESS" "$model" "Good tool usage (Score: $success_score/10)"
        echo -e "${GREEN}💾 Response saved to: $log_file${NC}"
        return 0
    elif [ $success_score -ge 2 ]; then
        print_status "WARNING" "$model" "Partial tool usage (Score: $success_score/10)"
        echo -e "${YELLOW}💾 Response saved to: $log_file${NC}"
        return 1
    else
        print_status "FAILED" "$model" "No effective tool usage (Score: $success_score/10)"
        echo -e "${RED}💾 Response saved to: $log_file${NC}"
        return 1
    fi
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
    
    # Clean previous logs
    rm -rf "$LOG_DIR"
    mkdir -p "$LOG_DIR"
    
    echo "📁 Log directory: $LOG_DIR"
    echo "⏱️  Timeout per model: ${TIMEOUT}s"
    echo ""
    
    # Wait for API
    wait_for_api
    
    # Get available models
    if ! get_available_models; then
        echo -e "${RED}✗${NC} Failed to get available models"
        exit 1
    fi
    
    # Check if models file was created
    if [ ! -f /tmp/models_to_test.txt ] || [ ! -s /tmp/models_to_test.txt ]; then
        echo -e "${RED}✗${NC} No models available for testing"
        exit 1
    fi
    
    echo "Starting enhanced model tests with full output logging..."
    echo ""
    
    # Test each model
    local total_models=0
    local successful_models=0
    local failed_models=0
    local working_models=()
    local failed_model_list=()
    
    while IFS= read -r model; do
        if [ -n "$model" ] && [ "$model" != "null" ]; then
            ((total_models++))
            if test_model "$model"; then
                ((successful_models++))
                working_models+=("$model")
            else
                ((failed_models++))
                failed_model_list+=("$model")
            fi
        fi
    done < /tmp/models_to_test.txt
    
    # Cleanup
    rm -f /tmp/models_to_test.txt
    
    # Final comprehensive summary
    echo ""
    echo "🎉 Enhanced Testing Complete!"
    echo "============================="
    echo -e "Total models tested: ${BLUE}$total_models${NC}"
    echo -e "Successful: ${GREEN}$successful_models${NC}"
    echo -e "Failed: ${RED}$failed_models${NC}"
    echo -e "Success rate: ${BLUE}$(( successful_models * 100 / total_models ))%${NC}"
    echo ""
    
    if [ ${#working_models[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ Working Models:${NC}"
        for model in "${working_models[@]}"; do
            echo "  • $model"
        done
        echo ""
    fi
    
    if [ ${#failed_model_list[@]} -gt 0 ]; then
        echo -e "${RED}❌ Failed Models:${NC}"
        for model in "${failed_model_list[@]}"; do
            echo "  • $model"
        done
        echo ""
    fi
    
    echo -e "${CYAN}📁 All responses saved in: $LOG_DIR${NC}"
    echo -e "${CYAN}💡 Review individual log files for detailed analysis${NC}"
    echo ""
    
    if [ $successful_models -gt 0 ]; then
        echo -e "${GREEN}🎯 Recommendation: Use the working models for your agents!${NC}"
    else
        echo -e "${YELLOW}⚠️  Troubleshooting needed:${NC}"
        echo "  1. Check agent manager configuration"
        echo "  2. Verify tool registration"
        echo "  3. Review Ollama model compatibility"
        echo "  4. Check individual response logs in $LOG_DIR"
    fi
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [--help]"
        echo ""
        echo "Enhanced model testing with:"
        echo "• Extended timeouts (90s per model)"
        echo "• Better tool usage prompting"
        echo "• Full response logging"
        echo "• Detailed success scoring"
        echo "• Comprehensive analysis"
        echo ""
        echo "Logs are saved in: $LOG_DIR"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac