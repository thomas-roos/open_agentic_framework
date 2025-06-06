#!/bin/bash
# optimized-model-test.sh - Optimized for DigitalOcean performance

# Configuration for production environment
API_BASE="http://localhost:8000"
MAX_MODELS=10
INITIAL_TIMEOUT=180    # 3 minutes for first test (model loading)
SUBSEQUENT_TIMEOUT=120  # 2 minutes for subsequent tests
WARMUP_TIMEOUT=60      # 1 minute for model warmup
LOG_DIR="/tmp/model_test_logs"

echo "🚀 Optimized Model Performance Test (DigitalOcean)"
echo "================================================="
echo "💻 Configured for production environment"
echo "⏱️  Initial timeout: ${INITIAL_TIMEOUT}s (includes model loading)"
echo "⏱️  Subsequent timeout: ${SUBSEQUENT_TIMEOUT}s"
echo "🔥 Pre-warming models before testing"
echo ""

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
    local time_taken=${4:-""}
    
    local time_info=""
    if [ -n "$time_taken" ]; then
        time_info=" (${time_taken}s)"
    fi
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✓${NC} $model: ${GREEN}WORKS${NC}$time_info - $message"
            ;;
        "FAILED")
            echo -e "${RED}✗${NC} $model: ${RED}FAILED${NC}$time_info - $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} $model: ${BLUE}INFO${NC}$time_info - $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠${NC} $model: ${YELLOW}WARNING${NC}$time_info - $message"
            ;;
        "TIMEOUT")
            echo -e "${PURPLE}⏱${NC} $model: ${PURPLE}TIMEOUT${NC}$time_info - $message"
            ;;
        "WARMUP")
            echo -e "${CYAN}🔥${NC} $model: ${CYAN}WARMUP${NC}$time_info - $message"
            ;;
    esac
}

# Check system resources
check_system_resources() {
    echo "🔍 Checking system resources..."
    
    # Memory info
    local total_mem=$(free -h | awk '/^Mem:/ {print $2}')
    local available_mem=$(free -h | awk '/^Mem:/ {print $7}')
    echo "💾 Memory: $available_mem available of $total_mem total"
    
    # CPU info
    local cpu_count=$(nproc)
    echo "🖥️  CPUs: $cpu_count cores"
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    echo "📊 Load average:$load_avg"
    
    # Check if Ollama is using significant resources
    echo "🔧 Checking Ollama status..."
    if docker ps | grep -q ollama; then
        echo "✅ Ollama container is running"
        local ollama_mem=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | grep ollama | awk '{print $2}' || echo "Unknown")
        echo "💾 Ollama memory usage: $ollama_mem"
    else
        echo "❌ Ollama container not found"
    fi
    
    echo ""
}

# Wait for API to be ready
wait_for_api() {
    echo "Checking API availability..."
    local retries=60  # Increased retries for production
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s "$API_BASE/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} API is ready!"
            
            # Check API health details
            local health_response=$(curl -s "$API_BASE/health" 2>/dev/null)
            local ollama_status=$(echo "$health_response" | jq -r '.ollama_status' 2>/dev/null)
            if [ "$ollama_status" = "true" ]; then
                echo -e "${GREEN}✓${NC} Ollama is healthy"
            else
                echo -e "${YELLOW}⚠${NC} Ollama health check failed"
            fi
            
            return 0
        fi
        echo -n "."
        sleep 3  # Longer sleep for production
        ((count++))
    done
    
    echo -e "${RED}✗${NC} API not available after $((retries * 3)) seconds"
    exit 1
}

# Pre-warm a model by making a simple request
warmup_model() {
    local model="$1"
    
    echo "🔥 Pre-warming model: $model"
    
    # Create a temporary simple agent for warmup
    local warmup_agent="warmup_$(echo "$model" | sed 's/[^a-zA-Z0-9]/_/g')"
    
    local warmup_payload
    warmup_payload=$(jq -n \
        --arg name "$warmup_agent" \
        --arg model "$model" \
        '{
            name: $name,
            role: "Simple Responder",
            goals: "Respond to simple questions",
            backstory: "You give brief responses to warm up the model",
            tools: [],
            ollama_model: $model,
            enabled: true
        }')
    
    local start_time=$(date +%s)
    
    # Create warmup agent
    local create_response
    create_response=$(timeout $WARMUP_TIMEOUT curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "$warmup_payload" 2>/dev/null)
    
    if [ $? -ne 0 ] || echo "$create_response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        print_status "WARNING" "$model" "Warmup agent creation failed"
        return 1
    fi
    
    # Simple warmup task
    local warmup_task
    warmup_task=$(jq -n '{
        task: "Say hello briefly",
        context: {}
    }')
    
    # Execute warmup
    local warmup_response
    warmup_response=$(timeout $WARMUP_TIMEOUT curl -s -X POST "$API_BASE/agents/$warmup_agent/execute" \
      -H "Content-Type: application/json" \
      -d "$warmup_task" 2>/dev/null)
    
    local warmup_exit_code=$?
    local end_time=$(date +%s)
    local warmup_time=$((end_time - start_time))
    
    # Cleanup warmup agent
    curl -s -X DELETE "$API_BASE/agents/$warmup_agent" >/dev/null 2>&1
    
    if [ $warmup_exit_code -eq 0 ] && ! echo "$warmup_response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        print_status "WARMUP" "$model" "Pre-warmed successfully" "$warmup_time"
        return 0
    else
        print_status "WARNING" "$model" "Warmup failed or timed out" "$warmup_time"
        return 1
    fi
}

# Get list of available models
get_available_models() {
    echo "Discovering available models..."
    
    local models_response
    models_response=$(curl -s "$API_BASE/models" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$models_response" ]; then
        echo -e "${RED}✗${NC} Failed to fetch available models"
        return 1
    fi
    
    if ! echo "$models_response" | jq -e 'type == "array"' >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} Invalid response format from models API"
        echo "Response: $models_response"
        return 1
    fi
    
    local models
    models=$(echo "$models_response" | jq -r '.[]' 2>/dev/null | grep -v '^null$' | head -n "$MAX_MODELS")
    
    if [ -z "$models" ]; then
        echo -e "${RED}✗${NC} No models found in API response"
        return 1
    fi
    
    local model_count
    model_count=$(echo "$models" | wc -l)
    
    echo -e "${GREEN}✓${NC} Found $model_count available models:"
    echo "$models" | sed 's/^/  - /'
    echo ""
    
    echo "$models" > /tmp/models_to_test.txt
    return 0
}

# Progressive timeout test
test_model() {
    local model="$1"
    local is_first_model="$2"
    
    # Use longer timeout for first model (includes loading time)
    local test_timeout=$SUBSEQUENT_TIMEOUT
    if [ "$is_first_model" = "true" ]; then
        test_timeout=$INITIAL_TIMEOUT
    fi
    
    echo ""
    echo -e "${CYAN}===========================================${NC}"
    echo -e "${BLUE}Testing model: $model${NC}"
    echo -e "${CYAN}Timeout: ${test_timeout}s${NC}"
    echo -e "${CYAN}===========================================${NC}"
    
    # Validate model name
    if [ -z "$model" ] || [ "$model" = "null" ]; then
        print_status "FAILED" "$model" "Invalid model name"
        return 1
    fi
    
    # Sanitize model name for agent name
    local agent_name="prod_test_$(echo "$model" | sed 's/[^a-zA-Z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//g' | sed 's/_$//g')"
    
    if [ ${#agent_name} -gt 50 ]; then
        agent_name="${agent_name:0:50}"
    fi
    
    # Pre-warm model if it's the first time
    if [ "$is_first_model" = "true" ]; then
        warmup_model "$model"
        sleep 2  # Brief pause after warmup
    fi
    
    echo "Creating optimized test agent: $agent_name"
    
    # Ultra-explicit agent payload optimized for tool usage
    local agent_payload
    agent_payload=$(jq -n \
        --arg name "$agent_name" \
        --arg model "$model" \
        '{
            name: $name,
            role: "Mandatory Tool User",
            goals: "EXCLUSIVELY use website_monitor tool for ALL website checks. NEVER write code. NEVER explain manually. ONLY use tools.",
            backstory: "You are a tool-only agent. When asked to check any website, you MUST immediately respond with: TOOL_CALL: website_monitor(url=\"TARGET_URL\", expected_status=200). You have no other capabilities. You cannot write code. You cannot explain processes. You only execute tool calls. This is your only function.",
            tools: ["website_monitor"],
            ollama_model: $model,
            enabled: true
        }')
    
    # Create agent
    echo "Creating agent..."
    local create_start=$(date +%s)
    local create_response
    create_response=$(timeout $test_timeout curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "$agent_payload" 2>/dev/null)
    
    local create_end=$(date +%s)
    local create_time=$((create_end - create_start))
    
    if [ $? -ne 0 ]; then
        print_status "TIMEOUT" "$model" "Agent creation timed out" "$create_time"
        return 1
    fi
    
    if echo "$create_response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        local error_msg
        error_msg=$(echo "$create_response" | jq -r '.detail // .error // .message' 2>/dev/null)
        print_status "FAILED" "$model" "Agent creation failed: $error_msg" "$create_time"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} Agent created in ${create_time}s"
    
    # Ultra-simple task payload
    local task_payload
    task_payload=$(jq -n '{
        task: "TOOL_CALL: website_monitor(url=\"https://google.com\", expected_status=200)",
        context: {}
    }')
    
    # Execute test
    echo "Executing test task..."
    local exec_start=$(date +%s)
    local test_response
    test_response=$(timeout $test_timeout curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d "$task_payload" 2>/dev/null)
    
    local curl_exit_code=$?
    local exec_end=$(date +%s)
    local exec_time=$((exec_end - exec_start))
    local total_time=$((exec_time + create_time))
    
    # Always cleanup
    echo "Cleaning up agent..."
    curl -s -X DELETE "$API_BASE/agents/$agent_name" >/dev/null 2>&1
    
    if [ $curl_exit_code -ne 0 ]; then
        print_status "TIMEOUT" "$model" "Test execution timed out" "$total_time"
        return 1
    fi
    
    # Save and analyze response
    local log_file="$LOG_DIR/${model//[^a-zA-Z0-9]/_}_response.json"
    echo "$test_response" > "$log_file"
    
    analyze_test_result "$model" "$test_response" "$log_file" "$total_time"
}

# Simplified but thorough analysis
analyze_test_result() {
    local model="$1"
    local response="$2" 
    local log_file="$3"
    local total_time="$4"
    
    echo ""
    echo -e "${YELLOW}📋 Response Analysis for $model:${NC}"
    echo "----------------------------------------"
    
    # Check for API errors
    if echo "$response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        local error_msg
        error_msg=$(echo "$response" | jq -r '.detail // .error // .message' 2>/dev/null)
        print_status "FAILED" "$model" "API Error: $error_msg" "$total_time"
        return 1
    fi
    
    # Extract result
    local result_content
    result_content=$(echo "$response" | jq -r '.result' 2>/dev/null)
    
    if [ -z "$result_content" ] || [ "$result_content" = "null" ]; then
        print_status "FAILED" "$model" "No result content" "$total_time"
        return 1
    fi
    
    # Show result (truncated for readability, full version in log)
    echo -e "${CYAN}📄 RESPONSE (first 200 chars):${NC}"
    echo "$(echo "$result_content" | head -c 200)..."
    echo ""
    
    # Quick analysis
    local success=false
    local reason=""
    
    if echo "$result_content" | grep -qi "TOOL_CALL.*website_monitor"; then
        success=true
        reason="Perfect TOOL_CALL format"
    elif echo "$result_content" | grep -qi "status_code.*200\|response_time"; then
        success=true
        reason="Tool execution detected (status/timing data)"
    elif echo "$result_content" | grep -qi "google\.com.*online\|website.*accessible"; then
        success=true  
        reason="Website check completed"
    elif echo "$result_content" | grep -qi "import\|def \|python\|http\.client"; then
        success=false
        reason="Model wrote code instead of using tools"
    else
        success=false
        reason="No clear tool usage detected"
    fi
    
    if [ "$success" = true ]; then
        print_status "SUCCESS" "$model" "$reason" "$total_time"
        return 0
    else
        print_status "FAILED" "$model" "$reason" "$total_time"
        return 1
    fi
}

# Main execution
main() {
    # Check dependencies
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}✗${NC} jq is required but not installed."
        exit 1
    fi
    
    # System check
    check_system_resources
    
    # Clean and setup logs
    rm -rf "$LOG_DIR"
    mkdir -p "$LOG_DIR"
    
    # Wait for API
    wait_for_api
    
    # Get models
    if ! get_available_models; then
        echo -e "${RED}✗${NC} Failed to get available models"
        exit 1
    fi
    
    if [ ! -f /tmp/models_to_test.txt ] || [ ! -s /tmp/models_to_test.txt ]; then
        echo -e "${RED}✗${NC} No models available for testing"
        exit 1
    fi
    
    echo "🚀 Starting optimized model tests..."
    echo "📁 Logs will be saved to: $LOG_DIR"
    echo ""
    
    # Test models
    local total_models=0
    local successful_models=0
    local first_model=true
    local working_models=()
    local failed_models=()
    
    while IFS= read -r model; do
        if [ -n "$model" ] && [ "$model" != "null" ]; then
            ((total_models++))
            if test_model "$model" "$first_model"; then
                ((successful_models++))
                working_models+=("$model")
            else
                failed_models+=("$model")
            fi
            first_model=false
            
            # Brief pause between tests
            sleep 3
        fi
    done < /tmp/models_to_test.txt
    
    # Cleanup
    rm -f /tmp/models_to_test.txt
    
    # Final summary
    echo ""
    echo "🎉 Optimized Testing Complete!"
    echo "=============================="
    echo -e "Total models tested: ${BLUE}$total_models${NC}"
    echo -e "Successful: ${GREEN}$successful_models${NC}"  
    echo -e "Failed: ${RED}${#failed_models[@]}${NC}"
    echo ""
    
    if [ ${#working_models[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ WORKING MODELS:${NC}"
        for model in "${working_models[@]}"; do
            echo "  🎯 $model"
        done
        echo ""
        echo -e "${GREEN}💡 Use these models for your production agents!${NC}"
    else
        echo -e "${RED}❌ No models working properly${NC}"
        echo ""
        echo -e "${YELLOW}🔧 Troubleshooting suggestions:${NC}"
        echo "  1. Check individual log files in $LOG_DIR"
        echo "  2. Verify agent manager tool integration"
        echo "  3. Consider using smaller models first"
        echo "  4. Check system resources during peak usage"
    fi
    
    echo ""
    echo -e "${CYAN}📊 Performance Notes:${NC}"
    echo "• First model test includes loading time"
    echo "• Subsequent tests should be faster"
    echo "• Pre-warming improves performance"
    echo "• Full responses saved in log files"
}

# Run with help option
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [--help]"
        echo ""
        echo "Optimized model testing for DigitalOcean production environment:"
        echo "• Pre-warms models before testing"
        echo "• Progressive timeouts (3min first, 2min subsequent)"
        echo "• System resource monitoring"
        echo "• Production-optimized prompting"
        echo "• Full response logging"
        echo ""
        echo "Designed for 8vCPU/16GB DigitalOcean droplets"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac