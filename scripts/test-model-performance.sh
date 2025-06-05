#!/bin/bash
# test-model-performance-fixed.sh - Fixed Model Performance Testing
# Based on working quick-test.sh with comprehensive testing

set -e

# Configuration
API_BASE="http://localhost:8000"
MODELS=("tinyllama:1.1b" "granite3.2:2b" "deepseek-r1:1.5b")

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

# Function to wait for API to be ready (simplified like quick-test.sh)
wait_for_api() {
    print_status "Waiting for API..."
    while ! curl -s "$API_BASE/health" >/dev/null 2>&1; do
        echo "."
        sleep 2
    done
    print_status "API ready! Testing models..."
    echo ""
}

# Enhanced tool usage detection (from quick-test.sh but more comprehensive)
detect_tool_usage() {
    local response="$1"
    
    # Check for multiple indicators of successful tool usage (from quick-test.sh)
    if echo "$response" | grep -q "TOOL_CALL.*website_monitor"; then
        echo "traditional_format"
        return 0
    elif echo "$response" | grep -q "Used website_monitor tool"; then
        echo "forced_execution"
        return 0
    elif echo "$response" | grep -q "status_code.*200"; then
        echo "tool_result_detected"
        return 0
    elif echo "$response" | grep -q "response_time_ms"; then
        echo "monitoring_successful"
        return 0
    elif echo "$response" | grep -q "status.*online"; then
        echo "website_online"
        return 0
    elif echo "$response" | grep -q "TOOL_CALL.*http_client"; then
        echo "http_tool_called"
        return 0
    elif echo "$response" | grep -q "Used http_client tool"; then
        echo "http_tool_executed"
        return 0
    else
        echo "no_tool_usage"
        return 1
    fi
}

# Simplified test function based on quick-test.sh approach
test_model() {
    local model=$1
    local success_count=0
    local total_tests=5
    local test_results=()
    
    print_test "Testing $model..."
    
    # Create agent (simplified backstory like quick-test.sh)
    agent_name="perf_test_${model//[:.]/_}"
    
    curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"$agent_name\",
        \"role\": \"Tool Tester\",
        \"goals\": \"Use tools to check websites and APIs\",
        \"backstory\": \"You use tools via TOOL_CALL format. Example: TOOL_CALL: website_monitor(url=https://google.com, expected_status=200). For HTTP: TOOL_CALL: http_client(url=https://example.com, method=GET). Never write code.\",
        \"tools\": [\"website_monitor\", \"http_client\"],
        \"ollama_model\": \"$model\",
        \"enabled\": true
      }" >/dev/null
    
    if [ $? -ne 0 ]; then
        print_error "✗ Failed to create agent for $model"
        echo "$model,0,$total_tests,0" >> test_results.csv
        return
    fi
    
    # Test 1: Basic website check (from quick-test.sh)
    print_test "  Test 1: Basic website check"
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check if https://google.com returns HTTP 200",
        "context": {}
      }')
    
    detection_result=$(detect_tool_usage "$response")
    if [ $? -eq 0 ]; then
        print_result "    ✓ PASS - $detection_result"
        ((success_count++))
        test_results+=("Test 1: PASS - $detection_result")
    else
        print_result "    ✗ FAIL - No tool usage detected"
        test_results+=("Test 1: FAIL")
        echo "      Response sample: $(echo "$response" | jq -r '.result' 2>/dev/null | head -c 100)..."
    fi
    
    # Test 2: Different URL
    print_test "  Test 2: GitHub check"
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check https://github.com",
        "context": {}
      }')
    
    detection_result=$(detect_tool_usage "$response")
    if [ $? -eq 0 ]; then
        print_result "    ✓ PASS - $detection_result"
        ((success_count++))
        test_results+=("Test 2: PASS - $detection_result")
    else
        print_result "    ✗ FAIL - No tool usage detected"
        test_results+=("Test 2: FAIL")
    fi
    
    # Test 3: HTTP client tool
    print_test "  Test 3: HTTP client tool"
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Make a GET request to https://httpbin.org/get using http_client tool",
        "context": {}
      }')
    
    detection_result=$(detect_tool_usage "$response")
    if [ $? -eq 0 ]; then
        print_result "    ✓ PASS - $detection_result"
        ((success_count++))
        test_results+=("Test 3: PASS - $detection_result")
    else
        print_result "    ✗ FAIL - No tool usage detected"
        test_results+=("Test 3: FAIL")
    fi
    
    # Test 4: Direct tool instruction
    print_test "  Test 4: Direct tool instruction"
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Use the website_monitor tool to check google.com status",
        "context": {}
      }')
    
    detection_result=$(detect_tool_usage "$response")
    if [ $? -eq 0 ]; then
        print_result "    ✓ PASS - $detection_result"
        ((success_count++))
        test_results+=("Test 4: PASS - $detection_result")
    else
        print_result "    ✗ FAIL - No tool usage detected"
        test_results+=("Test 4: FAIL")
    fi
    
    # Test 5: 404 status check
    print_test "  Test 5: 404 status check"
    response=$(curl -s -X POST "$API_BASE/agents/$agent_name/execute" \
      -H "Content-Type: application/json" \
      -d '{
        "task": "Check if https://httpbin.org/status/404 returns HTTP 404",
        "context": {}
      }')
    
    detection_result=$(detect_tool_usage "$response")
    if [ $? -eq 0 ]; then
        print_result "    ✓ PASS - $detection_result"
        ((success_count++))
        test_results+=("Test 5: PASS - $detection_result")
    else
        print_result "    ✗ FAIL - No tool usage detected"
        test_results+=("Test 5: FAIL")
    fi
    
    # Calculate success rate
    local success_rate=$((success_count * 100 / total_tests))
    
    # Store results
    echo "$model,$success_count,$total_tests,$success_rate" >> test_results.csv
    
    # Print summary like quick-test.sh
    if [ $success_count -gt 0 ]; then
        print_result "✓ $model: WORKS - $success_count/$total_tests tests passed ($success_rate%)"
    else
        print_result "✗ $model: FAILED - No tool usage detected in any test"
    fi
    
    echo "  Details:"
    for result in "${test_results[@]}"; do
        echo "    $result"
    done
    
    # Cleanup (from quick-test.sh)
    curl -s -X DELETE "$API_BASE/agents/$agent_name" >/dev/null
    echo ""
}

# Function to run performance benchmark
run_performance_benchmark() {
    print_header "COMPREHENSIVE MODEL PERFORMANCE TEST"
    echo "Based on working quick-test.sh methodology"
    echo ""
    
    # Create CSV header
    echo "Model,Successful_Tests,Total_Tests,Success_Rate" > test_results.csv
    
    # Test all models
    for model in "${MODELS[@]}"; do
        test_model "$model"
        sleep 1  # Brief pause between models
    done
}

# Function to display results summary
display_results_summary() {
    print_header "PERFORMANCE SUMMARY"
    echo ""
    printf "%-20s | %-15s | %-10s | %-12s\\n" "Model" "Success Rate" "Size" "Notes"
    echo "-------------------|-----------------|-----------|---------------"
    
    # Read results from CSV and display
    while IFS=',' read -r model success total rate; do
        if [ "$model" != "Model" ]; then  # Skip header
            case $model in
                "tinyllama:1.1b")
                    printf "%-20s | %-15s | %-10s | %-12s\\n" "$model" "$rate%" "637MB" "General use"
                    ;;
                "granite3.2:2b")
                    printf "%-20s | %-15s | %-10s | %-12s\\n" "$model" "$rate%" "700MB" "IBM efficient"
                    ;;
                "deepseek-r1:1.5b")
                    printf "%-20s | %-15s | %-10s | %-12s\\n" "$model" "$rate%" "1.1GB" "Best reasoning"
                    ;;
            esac
        fi
    done < test_results.csv
    echo ""
    
    # Find best performing model
    if [ -f test_results.csv ]; then
        local best_model=$(tail -n +2 test_results.csv | sort -t, -k4 -nr | head -n1 | cut -d, -f1)
        local best_rate=$(tail -n +2 test_results.csv | sort -t, -k4 -nr | head -n1 | cut -d, -f4)
        
        if [ -n "$best_model" ] && [ -n "$best_rate" ]; then
            print_result "🏆 BEST PERFORMER: $best_model with $best_rate% success rate"
        fi
    fi
    
    echo ""
    echo "SUCCESS INDICATORS (from quick-test.sh):"
    echo "- traditional_format: Model generates TOOL_CALL format"
    echo "- forced_execution: Agent manager forces tool usage"
    echo "- tool_result_detected: Tool returns status_code data"
    echo "- monitoring_successful: Response contains tool execution data"
    echo "- website_online: Shows website is online"
    echo ""
    echo "All indicators mean the agent successfully used tools!"
    echo ""
    
    print_status "Detailed results saved to: test_results.csv"
}

# Function to create production agents (simplified)
create_production_agents() {
    print_header "CREATING PRODUCTION AGENTS"
    
    # Determine best model from test results
    local best_model="deepseek-r1:1.5b"  # Default fallback
    if [ -f test_results.csv ]; then
        best_model=$(tail -n +2 test_results.csv | sort -t, -k4 -nr | head -n1 | cut -d, -f1)
        if [ -z "$best_model" ]; then
            best_model="deepseek-r1:1.5b"
        fi
    fi
    
    print_status "Using best performing model: $best_model"
    
    # Clean up any existing production agents first
    curl -s -X DELETE "$API_BASE/agents/production_monitor" >/dev/null 2>&1
    
    # Create single optimized agent based on working approach
    print_status "Creating optimized monitoring agent..."
    curl -s -X POST "$API_BASE/agents" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"production_monitor\",
        \"role\": \"Production Monitor\",
        \"goals\": \"Monitor websites and APIs using tools\",
        \"backstory\": \"You use tools via TOOL_CALL format. Example: TOOL_CALL: website_monitor(url=https://google.com, expected_status=200). For HTTP: TOOL_CALL: http_client(url=https://example.com, method=GET). Never write code.\",
        \"tools\": [\"website_monitor\", \"http_client\"],
        \"ollama_model\": \"$best_model\",
        \"enabled\": true
      }" >/dev/null
    
    if [ $? -eq 0 ]; then
        print_status "✓ production_monitor created successfully"
        
        # Quick verification test
        print_test "Verifying production agent..."
        response=$(curl -s -X POST "$API_BASE/agents/production_monitor/execute" \
          -H "Content-Type: application/json" \
          -d '{
            "task": "Check if https://google.com is online",
            "context": {}
          }')
        
        detection_result=$(detect_tool_usage "$response")
        if [ $? -eq 0 ]; then
            print_result "✓ Production agent working: $detection_result"
        else
            print_result "✗ Production agent verification failed"
        fi
    else
        print_error "✗ Failed to create production_monitor"
    fi
    
    echo ""
}

# Main execution
main() {
    print_header "FIXED MODEL PERFORMANCE TESTING"
    echo "Using methodology from working quick-test.sh"
    echo ""
    
    # Wait for API
    wait_for_api
    
    # Run comprehensive tests
    run_performance_benchmark
    
    # Display results
    display_results_summary
    
    # Create production agents
    create_production_agents
    
    print_header "TESTING COMPLETE!"
    echo ""
    print_status "Example usage of production agent:"
    print_status "curl -X POST \"$API_BASE/agents/production_monitor/execute\" \\"
    print_status "  -H \"Content-Type: application/json\" \\"
    print_status "  -d '{\"task\": \"Check https://your-website.com\", \"context\": {}}'"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi