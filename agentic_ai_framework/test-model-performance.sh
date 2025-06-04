#!/bin/bash
# test-model-performance.sh - Comprehensive Model Performance Testing
# Tests all 4 models with detailed agent configurations and tool calling

set -e

# Configuration
API_BASE="http://localhost:8000"
MODELS=("smollm:135m" "tinyllama:1.1b" "granite3.2:1b" "deepseek-coder:1.3b" "deepseek-r1:1.5b")
TEST_URLS=("https://google.com" "https://httpbin.org/status/200" "https://httpbin.org/status/404")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

print_result() {
    echo -e "${PURPLE}[RESULT]${NC} $1"
}

# Function to wait for API to be ready
wait_for_api() {
    print_status "Waiting for API to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$API_BASE/health" >/dev/null 2>&1; then
            print_status "API is ready!"
            break
        fi
        echo "Waiting for API... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "API did not become ready in time"
        exit 1
    fi
}

# Function to create comprehensive agent with detailed tool instructions
create_test_agent() {
    local model_name=$1
    local agent_name="test_${model_name//[:.]/_}"
    
    print_status "Creating test agent for model: $model_name"
    
    curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"$agent_name\",
        \"role\": \"Website Monitoring and Tool Testing Specialist\",
        \"goals\": \"Execute website monitoring tasks using available tools. Always use the TOOL_CALL format for tool execution. Test and demonstrate tool calling capabilities.\",
        \"backstory\": \"SYSTEM CONTEXT: You are an AI agent operating within the Agentic AI Framework. You have access to tools that extend your capabilities beyond text generation.\\n\\nTOOL CALLING MECHANISM:\\nTo use a tool, you MUST use this exact format: TOOL_CALL: tool_name(parameter1=value1, parameter2=value2)\\n\\nAVAILABLE TOOLS:\\n\\n1. WEBSITE_MONITOR TOOL:\\n   - Purpose: Check if websites are online and measure response time\\n   - Parameters:\\n     * url (required): The website URL to check (must include http:// or https://)\\n     * expected_status (optional): Expected HTTP status code (default: 200)\\n     * timeout (optional): Request timeout in seconds (default: 10)\\n     * check_content (optional): Text to look for in response content\\n   - Usage Examples:\\n     * Basic check: TOOL_CALL: website_monitor(url=https://google.com, expected_status=200)\\n     * With timeout: TOOL_CALL: website_monitor(url=https://example.com, expected_status=200, timeout=15)\\n     * Content check: TOOL_CALL: website_monitor(url=https://httpbin.org, expected_status=200, check_content=httpbin)\\n\\n2. HTTP_CLIENT TOOL:\\n   - Purpose: Make HTTP requests to APIs and websites\\n   - Parameters:\\n     * url (required): The URL to request\\n     * method (optional): HTTP method (GET, POST, PUT, DELETE, default: GET)\\n     * headers (optional): HTTP headers as key-value pairs\\n     * timeout (optional): Request timeout in seconds (default: 30)\\n   - Usage Examples:\\n     * GET request: TOOL_CALL: http_client(url=https://api.github.com, method=GET)\\n     * With headers: TOOL_CALL: http_client(url=https://httpbin.org/headers, method=GET, headers={\\\"User-Agent\\\": \\\"TestBot\\\"})\\n\\nTOOL EXECUTION RULES:\\n1. Always respond with the TOOL_CALL format when asked to check websites or make HTTP requests\\n2. Never write Python code or import statements\\n3. Never explain how to use requests library or other programming approaches\\n4. The framework will execute the tool and return results automatically\\n5. You can make multiple tool calls in sequence if needed\\n6. Always include the expected_status parameter for website_monitor calls\\n\\nEXAMPLE INTERACTIONS:\\nUser: \\\"Check if google.com is online\\\"\\nYou: \\\"TOOL_CALL: website_monitor(url=https://google.com, expected_status=200)\\\"\\n\\nUser: \\\"Test if httpbin.org returns 404 for /status/404\\\"\\nYou: \\\"TOOL_CALL: website_monitor(url=https://httpbin.org/status/404, expected_status=404)\\\"\\n\\nUser: \\\"Check multiple sites\\\"\\nYou: \\\"I'll check multiple sites for you.\\nTOOL_CALL: website_monitor(url=https://google.com, expected_status=200)\\nTOOL_CALL: website_monitor(url=https://github.com, expected_status=200)\\\"\\n\\nREMEMBER: Your primary job is to use tools via the TOOL_CALL format. Do not write code or provide manual solutions.\",
        \"tools\": [\"website_monitor\", \"http_client\"],
        \"ollama_model\": \"$model_name\",
        \"enabled\": true
      }" >/dev/null
    
    if [ $? -eq 0 ]; then
        print_status "✓ Agent '$agent_name' created successfully"
        echo "$agent_name"
    else
        print_error "✗ Failed to create agent for $model_name"
        echo ""
    fi
}

# Function to test agent with various scenarios
test_agent_performance() {
    local agent_name=$1
    local model_name=$2
    local test_results=()
    local start_time
    local end_time
    local duration
    local success_count=0
    local total_tests=0
    
    print_test "Testing agent: $agent_name (Model: $model_name)"
    echo ""
    
    # Test 1: Basic website check
    print_test "Test 1: Basic website monitoring"
    start_time=$(date +%s)
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check if https://google.com is online and returns HTTP 200",
        "context": {}
      }')
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    if echo "$response" | grep -q "TOOL_CALL.*website_monitor"; then
        print_result "✓ PASS - Tool call detected (${duration}s)"
        ((success_count++))
        test_results+=("Test 1: PASS (${duration}s)")
    else
        print_result "✗ FAIL - No tool call detected (${duration}s)"
        test_results+=("Test 1: FAIL (${duration}s)")
        echo "Response: $(echo "$response" | jq -r '.result' 2>/dev/null || echo "$response")"
    fi
    ((total_tests++))
    echo ""
    
    # Test 2: Status code specification
    print_test "Test 2: Specific status code check"
    start_time=$(date +%s)
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check if https://httpbin.org/status/404 returns HTTP 404",
        "context": {}
      }')
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    if echo "$response" | grep -q "TOOL_CALL.*website_monitor.*404"; then
        print_result "✓ PASS - Correct status code specified (${duration}s)"
        ((success_count++))
        test_results+=("Test 2: PASS (${duration}s)")
    else
        print_result "✗ FAIL - Incorrect or missing status code (${duration}s)"
        test_results+=("Test 2: FAIL (${duration}s)")
        echo "Response: $(echo "$response" | jq -r '.result' 2>/dev/null || echo "$response")"
    fi
    ((total_tests++))
    echo ""
    
    # Test 3: Multiple tool calls
    print_test "Test 3: Multiple website checks"
    start_time=$(date +%s)
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check both https://google.com and https://github.com to see if they are online",
        "context": {}
      }')
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    tool_call_count=$(echo "$response" | grep -o "TOOL_CALL.*website_monitor" | wc -l)
    if [ "$tool_call_count" -ge 2 ]; then
        print_result "✓ PASS - Multiple tool calls detected ($tool_call_count calls, ${duration}s)"
        ((success_count++))
        test_results+=("Test 3: PASS ($tool_call_count calls, ${duration}s)")
    else
        print_result "✗ FAIL - Expected 2+ tool calls, got $tool_call_count (${duration}s)"
        test_results+=("Test 3: FAIL ($tool_call_count calls, ${duration}s)")
        echo "Response: $(echo "$response" | jq -r '.result' 2>/dev/null || echo "$response")"
    fi
    ((total_tests++))
    echo ""
    
    # Test 4: Template following
    print_test "Test 4: Direct template execution"
    start_time=$(date +%s)
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Execute this exact command: TOOL_CALL: website_monitor(url=https://httpbin.org/status/200, expected_status=200)",
        "context": {}
      }')
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    if echo "$response" | grep -q "TOOL_CALL.*website_monitor.*httpbin.org/status/200.*200"; then
        print_result "✓ PASS - Template followed correctly (${duration}s)"
        ((success_count++))
        test_results+=("Test 4: PASS (${duration}s)")
    else
        print_result "✗ FAIL - Template not followed (${duration}s)"
        test_results+=("Test 4: FAIL (${duration}s)")
        echo "Response: $(echo "$response" | jq -r '.result' 2>/dev/null || echo "$response")"
    fi
    ((total_tests++))
    echo ""
    
    # Test 5: HTTP Client tool
    print_test "Test 5: HTTP client tool usage"
    start_time=$(date +%s)
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Make a GET request to https://httpbin.org/get using the http_client tool",
        "context": {}
      }')
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    if echo "$response" | grep -q "TOOL_CALL.*http_client"; then
        print_result "✓ PASS - HTTP client tool called (${duration}s)"
        ((success_count++))
        test_results+=("Test 5: PASS (${duration}s)")
    else
        print_result "✗ FAIL - HTTP client tool not called (${duration}s)"
        test_results+=("Test 5: FAIL (${duration}s)")
        echo "Response: $(echo "$response" | jq -r '.result' 2>/dev/null || echo "$response")"
    fi
    ((total_tests++))
    echo ""
    
    # Calculate success rate
    local success_rate=$((success_count * 100 / total_tests))
    
    # Store results
    echo "$model_name,$success_count,$total_tests,$success_rate" >> test_results.csv
    
    print_result "Agent Performance Summary:"
    print_result "Model: $model_name"
    print_result "Success Rate: $success_count/$total_tests ($success_rate%)"
    for result in "${test_results[@]}"; do
        print_result "  $result"
    done
    echo ""
    
    return $success_rate
}

# Function to run performance benchmark
run_performance_benchmark() {
    print_header "PERFORMANCE BENCHMARK RESULTS"
    
    # Create CSV header
    echo "Model,Successful_Tests,Total_Tests,Success_Rate" > test_results.csv
    
    local overall_results=()
    
    for model in "${MODELS[@]}"; do
        print_header "TESTING MODEL: $model"
        
        # Check if model is available
        if ! curl -s "$API_BASE:11434/api/tags" | grep -q "\"$model\""; then
            print_warning "Model $model not found - skipping"
            echo "$model,0,0,0" >> test_results.csv
            continue
        fi
        
        # Create test agent
        agent_name=$(create_test_agent "$model")
        if [ -z "$agent_name" ]; then
            continue
        fi
        
        # Wait a moment for agent to be ready
        sleep 2
        
        # Test agent performance
        test_agent_performance "$agent_name" "$model"
        success_rate=$?
        
        overall_results+=("$model: $success_rate%")
        
        # Clean up agent
        curl -s -X DELETE "$API_BASE/agents/$agent_name" >/dev/null
        
        echo ""
        sleep 3
    done
    
    # Display overall results
    print_header "OVERALL PERFORMANCE SUMMARY"
    echo ""
    printf "%-20s | %-15s | %-10s | %-12s\\n" "Model" "Success Rate" "Size" "Recommendation"
    echo "-------------------|-----------------|-----------|---------------"
    printf "%-20s | %-15s | %-10s | %-12s\\n" "smollm:135m" "$(grep "smollm:135m" test_results.csv | cut -d, -f4)%" "92MB" "Ultra-light"
    printf "%-20s | %-15s | %-10s | %-12s\\n" "tinyllama:1.1b" "$(grep "tinyllama:1.1b" test_results.csv | cut -d, -f4)%" "637MB" "General use"
    printf "%-20s | %-15s | %-10s | %-12s\\n" "granite3.2:1b" "$(grep "granite3.2:1b" test_results.csv | cut -d, -f4)%" "700MB" "IBM efficient"
    printf "%-20s | %-15s | %-10s | %-12s\\n" "deepseek-coder:1.3b" "$(grep "deepseek-coder:1.3b" test_results.csv | cut -d, -f4)%" "776MB" "Code tasks"
    printf "%-20s | %-15s | %-10s | %-12s\\n" "deepseek-r1:1.5b" "$(grep "deepseek-r1:1.5b" test_results.csv | cut -d, -f4)%" "1.1GB" "Best reasoning"
    echo ""
    
    # Find best performing model
    local best_model=$(tail -n +2 test_results.csv | sort -t, -k4 -nr | head -n1 | cut -d, -f1)
    local best_rate=$(tail -n +2 test_results.csv | sort -t, -k4 -nr | head -n1 | cut -d, -f4)
    
    print_result "🏆 BEST PERFORMER: $best_model with $best_rate% success rate"
    echo ""
    
    print_status "Detailed results saved to: test_results.csv"
    print_status "Test completed!"
}

# Function to create production-ready agents based on test results
create_production_agents() {
    print_header "CREATING PRODUCTION-READY AGENTS"
    
    # Determine best model from test results
    local best_model="deepseek-r1:1.5b"  # Default fallback
    if [ -f test_results.csv ]; then
        best_model=$(tail -n +2 test_results.csv | sort -t, -k4 -nr | head -n1 | cut -d, -f1)
    fi
    
    print_status "Using best performing model: $best_model"
    
    # Create optimized website monitoring agent
    print_status "Creating optimized website monitoring agent..."
    curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"production_website_monitor\",
        \"role\": \"Production Website Monitoring Specialist\",
        \"goals\": \"Monitor website availability and performance using the website_monitor tool. Provide accurate and timely website status reports.\",
        \"backstory\": \"You are a production-grade website monitoring agent. Your job is to use the website_monitor tool to check website availability.\\n\\nTOOL USAGE: Always use TOOL_CALL: website_monitor(url=TARGET_URL, expected_status=STATUS_CODE)\\n\\nEXAMPLES:\\n- TOOL_CALL: website_monitor(url=https://google.com, expected_status=200)\\n- TOOL_CALL: website_monitor(url=https://api.example.com/health, expected_status=200, timeout=15)\\n\\nNever write code. Always use the tool.\",
        \"tools\": [\"website_monitor\"],
        \"ollama_model\": \"$best_model\",
        \"enabled\": true
      }" >/dev/null
    
    # Create API testing agent
    print_status "Creating API testing agent..."
    curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"production_api_tester\",
        \"role\": \"API Testing and HTTP Request Specialist\",
        \"goals\": \"Test APIs and web services using the http_client tool. Perform comprehensive API testing and validation.\",
        \"backstory\": \"You are an API testing specialist. Use the http_client tool to test APIs and web services.\\n\\nTOOL USAGE: TOOL_CALL: http_client(url=TARGET_URL, method=METHOD, headers=HEADERS)\\n\\nEXAMPLES:\\n- TOOL_CALL: http_client(url=https://api.github.com, method=GET)\\n- TOOL_CALL: http_client(url=https://httpbin.org/post, method=POST, headers={\\\"Content-Type\\\": \\\"application/json\\\"})\\n\\nAlways use tools, never write code.\",
        \"tools\": [\"http_client\"],
        \"ollama_model\": \"$best_model\",
        \"enabled\": true
      }" >/dev/null
    
    # Create multi-tool agent
    print_status "Creating multi-tool monitoring agent..."
    curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"production_multi_monitor\",
        \"role\": \"Comprehensive Monitoring and Testing Agent\",
        \"goals\": \"Perform comprehensive monitoring using multiple tools. Monitor websites, test APIs, and provide detailed reports.\",
        \"backstory\": \"You are a comprehensive monitoring agent with access to multiple tools.\\n\\nAVAILABLE TOOLS:\\n1. website_monitor - Check website availability\\n2. http_client - Make HTTP requests\\n\\nUSAGE EXAMPLES:\\n- Website check: TOOL_CALL: website_monitor(url=https://example.com, expected_status=200)\\n- API test: TOOL_CALL: http_client(url=https://api.example.com/health, method=GET)\\n\\nYou can use multiple tools in sequence for comprehensive testing.\",
        \"tools\": [\"website_monitor\", \"http_client\"],
        \"ollama_model\": \"$best_model\",
        \"enabled\": true
      }" >/dev/null
    
    print_status "✓ Production agents created successfully!"
    print_status "Available agents:"
    print_status "  - production_website_monitor: Website monitoring specialist"
    print_status "  - production_api_tester: API testing specialist"  
    print_status "  - production_multi_monitor: Multi-tool monitoring agent"
    echo ""
}

# Function to run quick verification tests
run_verification_tests() {
    print_header "VERIFICATION TESTS"
    
    print_test "Testing production_website_monitor agent..."
    response=$(curl -s -X POST "$API_BASE/agents/production_website_monitor/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check if https://google.com is online",
        "context": {}
      }')
    
    if echo "$response" | grep -q "TOOL_CALL.*website_monitor"; then
        print_result "✓ Production website monitor working correctly"
    else
        print_result "✗ Production website monitor failed"
    fi
    echo ""
}

# Main execution
main() {
    print_header "AGENTIC AI FRAMEWORK - MODEL PERFORMANCE TESTING"
    echo "This script will test all 4 models for tool calling performance"
    echo "and create optimized production agents based on results."
    echo ""
    
    # Wait for API
    wait_for_api
    
    # Run comprehensive tests
    run_performance_benchmark
    
    # Create production agents
    create_production_agents
    
    # Run verification
    run_verification_tests
    
    print_header "TESTING COMPLETE!"
    print_status "Results saved to: test_results.csv"
    print_status "Production agents created and verified"
    echo ""
    print_status "You can now use the production agents for reliable tool calling:"
    print_status "curl -X POST \"$API_BASE/agents/production_website_monitor/execute\" \\"
    print_status "  -H \"Content-Type: application/json\" \\"
    print_status "  -d '{\"task\": \"Check https://your-website.com\", \"context\": {}}'"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi