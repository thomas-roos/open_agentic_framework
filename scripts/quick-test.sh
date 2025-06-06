#!/bin/bash
# optimized-model-test.sh - Enhanced with detailed message output

# Configuration for production environment
API_BASE="http://localhost:8000"
MAX_MODELS=10
INITIAL_TIMEOUT=180    # 3 minutes for first test (model loading)
SUBSEQUENT_TIMEOUT=120  # 2 minutes for subsequent tests
WARMUP_TIMEOUT=60      # 1 minute for model warmup
LOG_DIR="/tmp/model_test_logs"

# New options for detailed output
SHOW_FULL_RESPONSE=true  # Set to false to use truncated output
SHOW_TOOL_CALLS=true     # Highlight tool calls specifically
SHOW_TIMING_DETAILS=true # Show detailed timing information

echo "🚀 Enhanced Model Performance Test (DigitalOcean)"
echo "================================================="
echo "💻 Configured for production environment"
echo "⏱️  Initial timeout: ${INITIAL_TIMEOUT}s (includes model loading)"
echo "⏱️  Subsequent timeout: ${SUBSEQUENT_TIMEOUT}s"
echo "🔥 Pre-warming models before testing"
echo "📝 Full response details: $([ "$SHOW_FULL_RESPONSE" = true ] && echo "ENABLED" || echo "DISABLED")"
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
MAGENTA='\033[0;95m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print colored output with enhanced formatting
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
            echo -e "${GREEN}✓${NC} ${BOLD}$model${NC}: ${GREEN}WORKS${NC}$time_info - $message"
            ;;
        "FAILED")
            echo -e "${RED}✗${NC} ${BOLD}$model${NC}: ${RED}FAILED${NC}$time_info - $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} ${BOLD}$model${NC}: ${BLUE}INFO${NC}$time_info - $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠${NC} ${BOLD}$model${NC}: ${YELLOW}WARNING${NC}$time_info - $message"
            ;;
        "TIMEOUT")
            echo -e "${PURPLE}⏱${NC} ${BOLD}$model${NC}: ${PURPLE}TIMEOUT${NC}$time_info - $message"
            ;;
        "WARMUP")
            echo -e "${CYAN}🔥${NC} ${BOLD}$model${NC}: ${CYAN}WARMUP${NC}$time_info - $message"
            ;;
    esac
}

# Enhanced system resource check
check_system_resources() {
    echo "🔍 Checking system resources..."
    
    # Memory info with usage percentage
    local total_mem_kb=$(free | awk '/^Mem:/ {print $2}')
    local available_mem_kb=$(free | awk '/^Mem:/ {print $7}')
    local used_mem_kb=$((total_mem_kb - available_mem_kb))
    local mem_usage_percent=$((used_mem_kb * 100 / total_mem_kb))
    
    local total_mem=$(free -h | awk '/^Mem:/ {print $2}')
    local available_mem=$(free -h | awk '/^Mem:/ {print $7}')
    echo "💾 Memory: $available_mem available of $total_mem total (${mem_usage_percent}% used)"
    
    # CPU info with load
    local cpu_count=$(nproc)
    local load_1min=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
    local load_percentage=$(echo "$load_1min * 100 / $cpu_count" | bc -l 2>/dev/null | cut -d'.' -f1)
    echo "🖥️  CPUs: $cpu_count cores (Load: ${load_percentage:-0}%)"
    
    # Disk space
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    echo "💿 Disk usage: ${disk_usage}%"
    
    # Check if Ollama is using significant resources
    echo "🔧 Checking Ollama status..."
    if docker ps | grep -q ollama; then
        echo "✅ Ollama container is running"
        local ollama_stats=$(docker stats --no-stream --format "{{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}" | grep ollama)
        if [ -n "$ollama_stats" ]; then
            local ollama_mem=$(echo "$ollama_stats" | awk '{print $2}')
            local ollama_cpu=$(echo "$ollama_stats" | awk '{print $3}')
            echo "💾 Ollama memory: $ollama_mem"
            echo "🖥️  Ollama CPU: $ollama_cpu"
        fi
    else
        echo "❌ Ollama container not found"
    fi
    
    echo ""
}

# Wait for API to be ready with enhanced feedback
wait_for_api() {
    echo "Checking API availability..."
    local retries=60
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s "$API_BASE/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} API is ready!"
            
            # Check API health details
            local health_response=$(curl -s "$API_BASE/health" 2>/dev/null)
            local ollama_status=$(echo "$health_response" | jq -r '.ollama_status' 2>/dev/null)
            local uptime=$(echo "$health_response" | jq -r '.uptime // "unknown"' 2>/dev/null)
            
            if [ "$ollama_status" = "true" ]; then
                echo -e "${GREEN}✓${NC} Ollama is healthy (uptime: $uptime)"
            else
                echo -e "${YELLOW}⚠${NC} Ollama health check failed"
            fi
            
            return 0
        fi
        echo -n "."
        sleep 3
        ((count++))
    done
    
    echo -e "${RED}✗${NC} API not available after $((retries * 3)) seconds"
    exit 1
}

# Enhanced warmup with detailed feedback
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
    echo "  📝 Creating warmup agent..."
    local create_response
    create_response=$(timeout $WARMUP_TIMEOUT curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "$warmup_payload" 2>/dev/null)
    
    if [ $? -ne 0 ] || echo "$create_response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        print_status "WARNING" "$model" "Warmup agent creation failed"
        return 1
    fi
    
    # Simple warmup task
    echo "  🎯 Executing warmup task..."
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
    
    # Show warmup response if detailed output is enabled
    if [ "$SHOW_FULL_RESPONSE" = true ] && [ $warmup_exit_code -eq 0 ]; then
        local warmup_result=$(echo "$warmup_response" | jq -r '.result // "No result"' 2>/dev/null)
        echo "  💬 Warmup response: $warmup_result"
    fi
    
    # Cleanup warmup agent
    echo "  🧹 Cleaning up warmup agent..."
    curl -s -X DELETE "$API_BASE/agents/$warmup_agent" >/dev/null 2>&1
    
    if [ $warmup_exit_code -eq 0 ] && ! echo "$warmup_response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        print_status "WARMUP" "$model" "Pre-warmed successfully" "$warmup_time"
        return 0
    else
        print_status "WARNING" "$model" "Warmup failed or timed out" "$warmup_time"
        return 1
    fi
}

# Get list of available models with enhanced feedback
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

# Enhanced test function with detailed output
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
    echo -e "${BOLD}${BLUE}Testing model: $model${NC}"
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
        sleep 2
    fi
    
    echo "📝 Creating optimized test agent: $agent_name"
    
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
    
    # Create agent with timing
    echo "🔧 Creating agent..."
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
    
    # Execute test with detailed timing
    echo "🎯 Executing test task..."
    local exec_start=$(date +%s)
    local test_response
    test_response=$(timeout $test_timeout curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d "$task_payload" 2>/dev/null)
    
    local curl_exit_code=$?
    local exec_end=$(date +%s)
    local exec_time=$((exec_end - exec_start))
    local total_time=$((exec_time + create_time))
    
    if [ "$SHOW_TIMING_DETAILS" = true ]; then
        echo -e "${CYAN}⏱️  Timing breakdown:${NC}"
        echo "   Agent creation: ${create_time}s"
        echo "   Task execution: ${exec_time}s"
        echo "   Total time: ${total_time}s"
    fi
    
    # Always cleanup
    echo "🧹 Cleaning up agent..."
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

# Enhanced analysis with full response display
analyze_test_result() {
    local model="$1"
    local response="$2" 
    local log_file="$3"
    local total_time="$4"
    
    echo ""
    echo -e "${BOLD}${YELLOW}📋 Detailed Response Analysis for $model:${NC}"
    echo "=================================================================="
    
    # Check for API errors first
    if echo "$response" | jq -e '.error or .detail' >/dev/null 2>&1; then
        local error_msg
        error_msg=$(echo "$response" | jq -r '.detail // .error // .message' 2>/dev/null)
        print_status "FAILED" "$model" "API Error: $error_msg" "$total_time"
        echo -e "${RED}❌ Full error response:${NC}"
        echo "$response" | jq . 2>/dev/null || echo "$response"
        return 1
    fi
    
    # Extract result
    local result_content
    result_content=$(echo "$response" | jq -r '.result' 2>/dev/null)
    
    if [ -z "$result_content" ] || [ "$result_content" = "null" ]; then
        print_status "FAILED" "$model" "No result content" "$total_time"
        echo -e "${RED}❌ Empty response structure:${NC}"
        echo "$response" | jq . 2>/dev/null || echo "$response"
        return 1
    fi
    
    # Show full response or truncated based on setting
    if [ "$SHOW_FULL_RESPONSE" = true ]; then
        echo -e "${BOLD}${CYAN}📄 COMPLETE RESPONSE:${NC}"
        echo "=================================================================="
        echo "$result_content"
        echo "=================================================================="
    else
        echo -e "${CYAN}📄 RESPONSE (first 300 chars):${NC}"
        echo "$(echo "$result_content" | head -c 300)..."
        echo ""
        echo -e "${BLUE}💡 Full response saved to: $log_file${NC}"
    fi
    
    # Enhanced tool call detection
    if [ "$SHOW_TOOL_CALLS" = true ]; then
        echo ""
        echo -e "${BOLD}${MAGENTA}🔧 Tool Call Analysis:${NC}"
        echo "------------------------------------------------"
        
        # Look for various tool call patterns
        if echo "$result_content" | grep -qi "TOOL_CALL.*website_monitor"; then
            echo -e "${GREEN}✓${NC} Found explicit TOOL_CALL format"
            local tool_call_line=$(echo "$result_content" | grep -i "TOOL_CALL.*website_monitor" | head -1)
            echo -e "${CYAN}   Pattern: $tool_call_line${NC}"
        fi
        
        if echo "$result_content" | grep -qi "website_monitor.*url"; then
            echo -e "${GREEN}✓${NC} Found website_monitor tool usage"
        fi
        
        if echo "$result_content" | grep -qi "status_code.*200"; then
            echo -e "${GREEN}✓${NC} Found HTTP status code in response"
        fi
        
        if echo "$result_content" | grep -qi "response_time\|elapsed"; then
            echo -e "${GREEN}✓${NC} Found timing information"
        fi
        
        if echo "$result_content" | grep -qi "google\.com"; then
            echo -e "${GREEN}✓${NC} Target URL (google.com) mentioned"
        fi
        
        if echo "$result_content" | grep -qi "import\|def \|python\|http\.client"; then
            echo -e "${RED}⚠${NC} Found code generation (not desired)"
        fi
    fi
    
    # Detailed success analysis
    echo ""
    echo -e "${BOLD}${BLUE}🎯 Success Criteria Analysis:${NC}"
    echo "------------------------------------------------"
    
    local success=false
    local reason=""
    local score=0
    
    # Multiple success criteria with scoring
    if echo "$result_content" | grep -qi "TOOL_CALL.*website_monitor"; then
        score=$((score + 30))
        echo -e "${GREEN}✓${NC} [30 pts] Perfect TOOL_CALL format detected"
    fi
    
    if echo "$result_content" | grep -qi "status_code.*200\|HTTP.*200"; then
        score=$((score + 25))
        echo -e "${GREEN}✓${NC} [25 pts] HTTP 200 status detected"
    fi
    
    if echo "$result_content" | grep -qi "response_time\|elapsed.*ms"; then
        score=$((score + 20))
        echo -e "${GREEN}✓${NC} [20 pts] Response timing data found"
    fi
    
    if echo "$result_content" | grep -qi "google\.com.*online\|google\.com.*accessible\|website.*up"; then
        score=$((score + 15))
        echo -e "${GREEN}✓${NC} [15 pts] Website accessibility confirmed"
    fi
    
    if echo "$result_content" | grep -qi "tool.*executed\|using.*tool"; then
        score=$((score + 10))
        echo -e "${GREEN}✓${NC} [10 pts] Tool execution mentioned"
    fi
    
    # Penalty for code generation
    if echo "$result_content" | grep -qi "import\|def \|python\|http\.client\|requests\.get"; then
        score=$((score - 50))
        echo -e "${RED}✗${NC} [-50 pts] Code generation detected (major penalty)"
    fi
    
    echo ""
    echo -e "${BOLD}📊 Total Score: $score/100${NC}"
    
    # Determine success based on score
    if [ $score -ge 50 ]; then
        success=true
        if [ $score -ge 80 ]; then
            reason="Excellent tool usage (Score: $score/100)"
        elif [ $score -ge 65 ]; then
            reason="Good tool usage (Score: $score/100)"
        else
            reason="Acceptable tool usage (Score: $score/100)"
        fi
    else
        success=false
        if [ $score -le 0 ]; then
            reason="Poor response - code generation detected (Score: $score/100)"
        else
            reason="Insufficient tool usage (Score: $score/100)"
        fi
    fi
    
    # Final status
    echo ""
    if [ "$success" = true ]; then
        print_status "SUCCESS" "$model" "$reason" "$total_time"
        return 0
    else
        print_status "FAILED" "$model" "$reason" "$total_time"
        return 1
    fi
}

# Enhanced main execution with configuration options
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-full-response)
                SHOW_FULL_RESPONSE=false
                shift
                ;;
            --no-tool-calls)
                SHOW_TOOL_CALLS=false
                shift
                ;;
            --no-timing)
                SHOW_TIMING_DETAILS=false
                shift
                ;;
            --brief)
                SHOW_FULL_RESPONSE=false
                SHOW_TOOL_CALLS=false
                SHOW_TIMING_DETAILS=false
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Available options:"
                echo "  --no-full-response  : Show truncated responses"
                echo "  --no-tool-calls     : Hide tool call analysis"
                echo "  --no-timing         : Hide timing details"
                echo "  --brief             : Show minimal output"
                exit 1
                ;;
        esac
    done
    
    # Check dependencies
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}✗${NC} jq is required but not installed."
        exit 1
    fi
    
    if ! command -v bc &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} bc not found - some calculations may be disabled"
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
    
    echo "🚀 Starting enhanced model tests..."
    echo "📁 Logs will be saved to: $LOG_DIR"
    echo "🔧 Configuration:"
    echo "   Full responses: $([ "$SHOW_FULL_RESPONSE" = true ] && echo "ENABLED" || echo "DISABLED")"
    echo "   Tool call analysis: $([ "$SHOW_TOOL_CALLS" = true ] && echo "ENABLED" || echo "DISABLED")"
    echo "   Timing details: $([ "$SHOW_TIMING_DETAILS" = true ] && echo "ENABLED" || echo "DISABLED")"
    echo ""
    
    # Test models
    local total_models=0
    local successful_models=0
    local first_model=true
    local working_models=()
    local failed_models=()
    local model_scores=()
    
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
    
    # Enhanced final summary
    echo ""
    echo "🎉 Enhanced Testing Complete!"
    echo "============================="
    echo -e "Total models tested: ${BLUE}$total_models${NC}"
    echo -e "Successful: ${GREEN}$successful_models${NC}"  
    echo -e "Failed: ${RED}${#failed_models[@]}${NC}"
    echo -e "Success rate: ${BOLD}$((successful_models * 100 / total_models))%${NC}"
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
    fi
    
    if [ ${#failed_models[@]} -gt 0 ]; then
        echo ""
        echo -e "${RED}❌ FAILED MODELS:${NC}"
        for model in "${failed_models[@]}"; do
            echo "  ❌ $model"
        done
    fi
    
    echo ""
    echo -e "${CYAN}📊 Performance Summary:${NC}"
    echo "• First model test includes loading time"
    echo "• Subsequent tests should be faster"
    echo "• Pre-warming improves performance"
    echo "• Full responses saved in log files: $LOG_DIR"
    echo "• Detailed analysis shows tool usage patterns"
    
    echo ""
    echo -e "${BLUE}💡 Tips for better results:${NC}"
    echo "• Models scoring 80+ are excellent for production"
    echo "• Models scoring 50-79 are acceptable"
    echo "• Models scoring <50 may need different prompting"
    echo "• Check individual log files for debugging"
}

# Enhanced help with new options
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Enhanced model testing for DigitalOcean production environment"
        echo ""
        echo "Options:"
        echo "  --no-full-response  : Show truncated responses (default: show full)"
        echo "  --no-tool-calls     : Hide detailed tool call analysis"
        echo "  --no-timing         : Hide detailed timing information"
        echo "  --brief             : Show minimal output (combines all --no-* options)"
        echo "  --help, -h          : Show this help message"
        echo ""
        echo "Features:"
        echo "• Pre-warms models before testing"
        echo "• Progressive timeouts (3min first, 2min subsequent)"
        echo "• System resource monitoring"
        echo "• Production-optimized prompting"
        echo "• Full response logging and analysis"
        echo "• Detailed tool usage scoring"
        echo "• Enhanced timing breakdown"
        echo ""
        echo "Examples:"
        echo "  $0                    # Full detailed output"
        echo "  $0 --brief           # Minimal output"
        echo "  $0 --no-full-response # Show truncated responses"
        echo ""
        echo "Designed for 4GB+ DigitalOcean droplets with tool-capable models"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac