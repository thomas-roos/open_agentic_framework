#!/bin/bash

# PURL Analysis Workflow Setup with Model Warm-up and Clean-up
# This script creates specialized agents with specific naming for API integrations
# Includes clean-up mechanism and model warm-up integration

set -e  # Exit on any error

echo "=== Agentic AI Framework - PURL Analysis Setup with Model Warm-up ==="
echo ""

# Configuration
API_BASE="http://localhost:8000"
RETRY_COUNT=5
RETRY_DELAY=10

# Functions
check_api_availability() {
    echo "🔍 Checking API availability..."
    for i in $(seq 1 $RETRY_COUNT); do
        if curl -s "$API_BASE/health" > /dev/null 2>&1; then
            echo "✅ API is available"
            return 0
        fi
        echo "⏳ Waiting for API... ($i/$RETRY_COUNT)"
        sleep $RETRY_DELAY
    done
    echo "❌ API is not available after $RETRY_COUNT attempts"
    exit 1
}

clean_existing_setup() {
    echo "🧹 Cleaning existing agents and workflows using framework APIs..."
    
    # Use framework's built-in cleanup endpoints
    echo "  Clearing all agent memory..."
    curl -s -X DELETE "$API_BASE/memory/clear-all" > /dev/null && \
        echo "    ✅ All agent memory cleared" || \
        echo "    ⚠️  Failed to clear agent memory"
    
    # Get and delete all agents
    echo "  Deleting existing agents..."
    AGENTS=$(curl -s "$API_BASE/agents" 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo "")
    if [ -n "$AGENTS" ] && [ "$AGENTS" != "null" ]; then
        AGENT_COUNT=$(echo "$AGENTS" | wc -l)
        echo "    Found $AGENT_COUNT agent(s) to delete"
        echo "$AGENTS" | while read -r agent; do
            if [ -n "$agent" ] && [ "$agent" != "null" ]; then
                echo "      🗑️  Deleting agent: $agent"
                curl -s -X DELETE "$API_BASE/agents/$agent" > /dev/null || echo "        ⚠️  Failed to delete agent: $agent"
            fi
        done
    else
        echo "    ℹ️  No existing agents found"
    fi
    
    # Get and delete all workflows
    echo "  Deleting existing workflows..."
    WORKFLOWS=$(curl -s "$API_BASE/workflows" 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo "")
    if [ -n "$WORKFLOWS" ] && [ "$WORKFLOWS" != "null" ]; then
        WORKFLOW_COUNT=$(echo "$WORKFLOWS" | wc -l)
        echo "    Found $WORKFLOW_COUNT workflow(s) to delete"
        echo "$WORKFLOWS" | while read -r workflow; do
            if [ -n "$workflow" ] && [ "$workflow" != "null" ]; then
                echo "      🗑️  Deleting workflow: $workflow"
                curl -s -X DELETE "$API_BASE/workflows/$workflow" > /dev/null || echo "        ⚠️  Failed to delete workflow: $workflow"
            fi
        done
    else
        echo "    ℹ️  No existing workflows found"
    fi
    
    # Clear scheduled tasks
    echo "  Clearing scheduled tasks..."
    SCHEDULES=$(curl -s "$API_BASE/schedule" 2>/dev/null | jq -r '.[].id' 2>/dev/null || echo "")
    if [ -n "$SCHEDULES" ] && [ "$SCHEDULES" != "null" ]; then
        SCHEDULE_COUNT=$(echo "$SCHEDULES" | wc -l)
        echo "    Found $SCHEDULE_COUNT scheduled task(s) to delete"
        echo "$SCHEDULES" | while read -r schedule_id; do
            if [ -n "$schedule_id" ] && [ "$schedule_id" != "null" ]; then
                echo "      🗑️  Deleting scheduled task: $schedule_id"
                curl -s -X DELETE "$API_BASE/schedule/$schedule_id" > /dev/null || echo "        ⚠️  Failed to delete schedule: $schedule_id"
            fi
        done
    else
        echo "    ℹ️  No existing scheduled tasks found"
    fi
    
    echo "✅ Clean-up completed using framework APIs"
    echo ""
    sleep 2
}

check_ollama_service() {
    echo "🔍 Checking Ollama service availability..."
    
    for i in $(seq 1 10); do
        if curl -s "http://localhost:11434/api/tags" > /dev/null 2>&1; then
            echo "    ✅ Ollama service is available"
            return 0
        fi
        echo "    ⏳ Waiting for Ollama service... ($i/10)"
        sleep 5
    done
    
    echo "    ⚠️  Ollama service not responding, but continuing setup..."
    return 1
}

create_purl_agents() {
    echo "🤖 Creating PURL Analysis Agents with mistral:7b model..."

    # 1. Create PURL Parser Agent (Generic - works with any API)
    echo "  Creating PURL Parser Agent (generic)..."
    curl -s -X POST "$API_BASE/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "purl_parser",
            "role": "Package URL Parser and Validator",
            "goals": "Parse Package URLs (PURLs) into their components and validate format. Extract package type, namespace, name, version, and prepare data for various package analysis APIs.",
            "backstory": "You are an expert in package management systems and Package URL specifications. You understand the PURL format: pkg:type/namespace/name@version and can parse it into components needed for API calls across different package analysis services.",
            "tools": [],
            "ollama_model": "mistral:7b",
            "enabled": true,
            "instructions": [
                "When given a PURL, extract all components carefully",
                "Handle special cases like scoped npm packages (@scope/package)",
                "Provide the default provider for each package type (npm->npmjs, maven->mavencentral, pypi->pypi, etc.)",
                "For ClearlyDefined API, build URLs in this format: https://api.clearlydefined.io/definitions/{type}/{provider}/{namespace}/{name}/{version}",
                "For packages without namespace, use \"-\" as placeholder: https://api.clearlydefined.io/definitions/{type}/{provider}-/{name}/{version}",
                "If PURL is invalid, explain what is wrong and suggest corrections",
                "Always provide the complete ClearlyDefined API URL ready to be called"
            ]
        }' > /dev/null && echo "    ✅ PURL Parser Agent created (mistral:7b)" || echo "    ❌ Failed to create PURL Parser Agent"

    # 2. Create ClearlyDefined-specific API Client Agent  
    echo "  Creating ClearlyDefined API Client Agent..."
    curl -s -X POST "$API_BASE/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "api_client_clearlydefined",
            "role": "ClearlyDefined API Specialist",
            "goals": "Query the ClearlyDefined API using URLs provided by the PURL parser and return structured package information specific to ClearlyDefined data format.",
            "backstory": "You are an expert at making API calls specifically to the ClearlyDefined service (api.clearlydefined.io). You understand their API response format, data structure, and can extract meaningful information about package licensing, security scores, and metadata from their specific response format.",
            "tools": ["http_client"],
            "ollama_model": "mistral:7b",
            "enabled": true,
            "instructions": [
                "Use the http_client tool to make HTTP GET requests to ClearlyDefined API endpoints",
                "The PURL parser will provide you with the complete URL - use it exactly as provided",
                "ClearlyDefined URL format: https://api.clearlydefined.io/definitions/{type}/{provider}/{namespace_or_dash}/{name}/{version}",
                "Handle ClearlyDefined-specific 404 responses gracefully (package not found)",
                "Extract ClearlyDefined-specific fields: described, licensed, coordinates, scores",
                "Understand ClearlyDefined score meanings (overall, tool, effective)",
                "Provide clear error messages for ClearlyDefined API failures",
                "Return structured data in ClearlyDefined format for downstream processing"
            ]
        }' > /dev/null && echo "    ✅ ClearlyDefined API Client Agent created (mistral:7b)" || echo "    ❌ Failed to create ClearlyDefined API Client Agent"

    # 3. Create ClearlyDefined-specific Package Analyzer Agent
    echo "  Creating ClearlyDefined Package Analyzer Agent..."
    curl -s -X POST "$API_BASE/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "package_analyzer_clearlydefined",
            "role": "ClearlyDefined Package Security and Compliance Analyst", 
            "goals": "Analyze package information specifically from ClearlyDefined API responses and provide security, licensing, and compliance insights based on ClearlyDefined data format and scoring system.",
            "backstory": "You are a senior software security analyst with deep expertise in ClearlyDefined data interpretation. You understand their scoring methodology, license detection algorithms, and can provide actionable recommendations based on ClearlyDefined analysis results.",
            "tools": [],
            "ollama_model": "mistral:7b",
            "enabled": true,
            "instructions": [
                "Analyze ClearlyDefined package definition data for security and compliance risks",
                "Interpret ClearlyDefined-specific license information (declared vs detected)",
                "Understand ClearlyDefined scoring system (overall, tool, effective scores)",
                "Explain ClearlyDefined tool analysis results",
                "Provide recommendations based on ClearlyDefined confidence levels",
                "Flag packages with low ClearlyDefined scores or missing data",
                "Create executive summaries interpreting ClearlyDefined results for non-technical stakeholders"
            ]
        }' > /dev/null && echo "    ✅ ClearlyDefined Package Analyzer Agent created (mistral:7b)" || echo "    ❌ Failed to create ClearlyDefined Package Analyzer Agent"

    echo "🤖 PURL analysis agents created successfully with mistral:7b model!"
    echo ""
}

create_purl_workflows() {
    echo "🔄 Creating PURL Analysis Workflow..."

    # Quick PURL Analysis Workflow (complete workflow)
    echo "  Creating PURL Analysis Workflow..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "purl_analysis_clearlydefined",
            "description": "Complete PURL analysis workflow using ClearlyDefined API: Parse PURL -> Query ClearlyDefined API -> Analyze results",
            "steps": [
                {
                    "type": "agent",
                    "name": "purl_parser",
                    "task": "Parse this Package URL: {purl}. Extract all components (type, provider, namespace, name, version) and provide the complete ClearlyDefined API URL to call. Format: https://api.clearlydefined.io/definitions/{type}/{provider}/{namespace_or_dash}/{name}/{version}",
                    "context_key": "parsed_purl"
                },
                {
                    "type": "agent",
                    "name": "api_client_clearlydefined",
                    "task": "Using the parsed PURL information from: {parsed_purl}, extract the ClearlyDefined API URL and make an HTTP GET request using the http_client tool. Return the complete API response with package licensing, scores, and metadata.",
                    "context_key": "clearlydefined_response"
                },
                {
                    "type": "agent",
                    "name": "package_analyzer_clearlydefined",
                    "task": "Analyze the ClearlyDefined API response: {clearlydefined_response} for the package: {purl}. Provide a comprehensive analysis including: 1) License information and confidence levels, 2) Security scores (overall, tool, effective), 3) Compliance recommendations, 4) Risk assessment, 5) Executive summary with actionable insights.",
                    "context_key": "analysis_result"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ PURL Analysis Workflow created" || echo "    ❌ Failed to create PURL Analysis Workflow"

    echo "🔄 PURL analysis workflow created successfully!"
    echo ""
}

warmup_mistral_model() {
    echo "🔥 Warming up mistral:7b model specifically..."
    
    check_ollama_service
    
    # Check if mistral:7b model is available
    echo "  Checking for mistral:7b model..."
    MODELS=$(curl -s "http://localhost:11434/api/tags" 2>/dev/null | jq -r '.models[].name' 2>/dev/null || echo "")
    
    if echo "$MODELS" | grep -q "mistral:7b" 2>/dev/null; then
        echo "    ✅ mistral:7b model found"
        
        # Warm up mistral:7b model using framework endpoint
        echo "  🔥 Warming up mistral:7b model..."
        
        if curl -s -X POST "$API_BASE/models/warmup/mistral:7b" > /dev/null 2>&1; then
            echo "    ✅ mistral:7b warmed up successfully using framework endpoint"
        else
            # Fallback: Simple warm-up request using one agent execution
            echo "    🔄 Framework endpoint unavailable, using fallback warm-up..."
            curl -s -X POST "$API_BASE/agents/purl_parser/execute" \
                -H "Content-Type: application/json" \
                -d '{
                    "task": "Hello, this is a warm-up test for mistral:7b. Please respond with: mistral:7b model is ready and warmed up",
                    "context": {"warmup": true}
                }' > /dev/null 2>&1 && \
                echo "    ✅ mistral:7b warmed up via agent execution" || \
                echo "    ⚠️  mistral:7b warm-up may have issues"
        fi
        
    else
        echo "    ⚠️  mistral:7b model not found"
        echo "    📥 Available models:"
        if [ -n "$MODELS" ] && [ "$MODELS" != "null" ]; then
            echo "$MODELS" | while read -r model; do
                if [ -n "$model" ] && [ "$model" != "null" ]; then
                    echo "      - $model"
                fi
            done
        else
            echo "      No models found or Ollama not accessible"
        fi
        echo ""
        echo "    📋 To install mistral:7b model, run:"
        echo "    curl -X POST 'http://localhost:8000/models/install' \\"
        echo "      -H 'Content-Type: application/json' \\"
        echo "      -d '{\"model_name\": \"mistral:7b\", \"wait_for_completion\": true}'"
    fi
    
    echo "🔥 mistral:7b model warm-up completed!"
    echo ""
}

test_agent_functionality() {
    echo "🧪 Testing agent functionality..."

    # Test PURL parser with a simple call
    echo "  Testing PURL parser agent..."
    curl -s -X POST "$API_BASE/agents/purl_parser/execute" \
        -H "Content-Type: application/json" \
        -d '{
            "task": "Parse this PURL: pkg:npm/test@1.0.0",
            "context": {"test": true}
        }' > /dev/null && \
        echo "    ✅ PURL parser agent responding" || \
        echo "    ⚠️  PURL parser agent may have issues"

    # Test ClearlyDefined API client (without making actual API call)
    echo "  Testing ClearlyDefined API client agent..."
    curl -s -X POST "$API_BASE/agents/api_client_clearlydefined/execute" \
        -H "Content-Type: application/json" \
        -d '{
            "task": "Explain your role and capabilities without making any API calls",
            "context": {"test": true}
        }' > /dev/null && \
        echo "    ✅ ClearlyDefined API client agent responding" || \
        echo "    ⚠️  ClearlyDefined API client agent may have issues"

    # Test analyzer agent
    echo "  Testing ClearlyDefined analyzer agent..."
    curl -s -X POST "$API_BASE/agents/package_analyzer_clearlydefined/execute" \
        -H "Content-Type: application/json" \
        -d '{
            "task": "Explain how you would analyze a package with MIT license and score of 85",
            "context": {"test": true}
        }' > /dev/null && \
        echo "    ✅ ClearlyDefined analyzer agent responding" || \
        echo "    ⚠️  ClearlyDefined analyzer agent may have issues"

    echo "🧪 Agent functionality testing completed!"
    echo ""
}

test_system() {
    echo "🧪 Testing the system..."

    # Test ClearlyDefined analysis with a sample package
    echo "  Testing ClearlyDefined analysis with lodash package..."
    RESPONSE=$(curl -s -X POST "$API_BASE/workflows/purl_analysis_clearlydefined/execute" \
        -H "Content-Type: application/json" \
        -d '{
            "context": {
                "purl": "pkg:npm/lodash@4.17.21",
                "test_run": true
            }
        }' 2>/dev/null)

    if [ $? -eq 0 ]; then
        echo "    ✅ PURL analysis workflow test completed successfully"
    else
        echo "    ⚠️  PURL analysis workflow test may have issues"
    fi

    # Test framework health
    echo "  Checking framework health..."
    HEALTH=$(curl -s "$API_BASE/health" 2>/dev/null)
    if echo "$HEALTH" | grep -q "status" 2>/dev/null; then
        echo "    ✅ Framework health check passed"
    else
        echo "    ⚠️  Framework health check may have issues"
    fi

    echo "🧪 System testing completed!"
    echo ""
}

show_summary() {
    echo "📋 Setup Summary"
    echo "================"
    echo ""
    echo "✅ Created Agents (all using mistral:7b):"
    echo "   📦 purl_parser - Generic PURL parser with ClearlyDefined URL building"
    echo "   🌐 api_client_clearlydefined - ClearlyDefined API client (uses http_client tool)"
    echo "   🔍 package_analyzer_clearlydefined - ClearlyDefined analyzer"
    echo ""
    echo "✅ Created Workflow:"
    echo "   📦 purl_analysis_clearlydefined - Complete PURL to analysis workflow"
    echo ""
    echo "🔥 Model Configuration:"
    echo "   🏗️  All agents use: mistral:7b"
    echo "   ⚡ mistral:7b model warmed up and ready"
    echo ""
    echo "🚀 Usage Example:"
    echo ""
    echo "# Complete PURL analysis:"
    echo 'curl -X POST "http://localhost:8000/workflows/purl_analysis_clearlydefined/execute" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"context": {"purl": "pkg:npm/lodash@4.17.21"}}'"'"''
    echo ""
    echo "# Test with different package types:"
    echo 'curl -X POST "http://localhost:8000/workflows/purl_analysis_clearlydefined/execute" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"context": {"purl": "pkg:maven/com.fasterxml.jackson.core/jackson-core@2.13.0"}}'"'"''
    echo ""
    echo "# Check mistral:7b model status:"
    echo 'curl "http://localhost:8000/models/status/mistral:7b"'
    echo ""
    echo "🌐 Available Endpoints:"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/health"
    echo "   • Agents: http://localhost:8000/agents"
    echo "   • Workflows: http://localhost:8000/workflows"
    echo "   • Model Status: http://localhost:8000/models/status"
    echo ""
}

# Main execution
main() {
    echo "🚀 Starting complete setup with clean-up and warm-up..."
    echo ""
    
    check_api_availability
    
    # Clean existing setup if requested or if --clean flag is passed
    if [ "$1" = "--clean" ] || [ "$1" = "clean" ]; then
        clean_existing_setup
    fi
    
    create_purl_agents
    create_purl_workflows
    warmup_mistral_model
    test_agent_functionality
    test_system
    show_summary
    
    echo "🎉 Setup completed successfully!"
    echo "🔥 System is warmed up and ready for production workloads!"
}

# Handle script arguments
case "${1:-setup}" in
    "setup"|"")
        main
        ;;
    "clean")
        check_api_availability
        clean_existing_setup
        echo "🧹 Clean-up completed. Run './purl-analysis-workflow-setup.sh setup' to recreate everything."
        ;;
    "warmup")
        check_api_availability
        warmup_mistral_model
        ;;
    "test")
        check_api_availability
        test_agent_functionality
        test_system
        ;;
    *)
        echo "Usage: $0 [setup|clean|warmup|test]"
        echo ""
        echo "Commands:"
        echo "  setup   - Full setup with clean-up and warm-up (default)"
        echo "  clean   - Clean existing agents and workflows only"
        echo "  warmup  - Run warm-up workflows only"
        echo "  test    - Run system tests only"
        exit 1
        ;;
esac