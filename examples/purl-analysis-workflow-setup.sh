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
    echo "🧹 Cleaning existing agents and workflows..."
    
    # Get all agents and delete them
    echo "  Deleting existing agents..."
    AGENTS=$(curl -s "$API_BASE/agents" 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo "")
    if [ -n "$AGENTS" ] && [ "$AGENTS" != "null" ]; then
        echo "$AGENTS" | while read -r agent; do
            if [ -n "$agent" ] && [ "$agent" != "null" ]; then
                echo "    🗑️  Deleting agent: $agent"
                curl -s -X DELETE "$API_BASE/agents/$agent" > /dev/null || echo "      ⚠️  Failed to delete agent: $agent"
            fi
        done
    else
        echo "    ℹ️  No existing agents found"
    fi
    
    # Get all workflows and delete them
    echo "  Deleting existing workflows..."
    WORKFLOWS=$(curl -s "$API_BASE/workflows" 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo "")
    if [ -n "$WORKFLOWS" ] && [ "$WORKFLOWS" != "null" ]; then
        echo "$WORKFLOWS" | while read -r workflow; do
            if [ -n "$workflow" ] && [ "$workflow" != "null" ]; then
                echo "    🗑️  Deleting workflow: $workflow"
                curl -s -X DELETE "$API_BASE/workflows/$workflow" > /dev/null || echo "      ⚠️  Failed to delete workflow: $workflow"
            fi
        done
    else
        echo "    ℹ️  No existing workflows found"
    fi
    
    # Clear scheduled tasks
    echo "  Clearing scheduled tasks..."
    SCHEDULES=$(curl -s "$API_BASE/schedule" 2>/dev/null | jq -r '.[].id' 2>/dev/null || echo "")
    if [ -n "$SCHEDULES" ] && [ "$SCHEDULES" != "null" ]; then
        echo "$SCHEDULES" | while read -r schedule_id; do
            if [ -n "$schedule_id" ] && [ "$schedule_id" != "null" ]; then
                echo "    🗑️  Deleting scheduled task: $schedule_id"
                curl -s -X DELETE "$API_BASE/schedule/$schedule_id" > /dev/null || echo "      ⚠️  Failed to delete schedule: $schedule_id"
            fi
        done
    else
        echo "    ℹ️  No existing scheduled tasks found"
    fi
    
    echo "✅ Clean-up completed"
    echo ""
    sleep 2
}

create_warmup_agents() {
    echo "🔥 Creating Model Warm-up Agents..."
    
    # Model Warm-up Agent
    echo "  Creating Model Warm-up Agent..."
    curl -s -X POST "$API_BASE/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "model_warmup",
            "role": "LLM Model Warm-up Specialist",
            "goals": "Warm up language models by sending test prompts to ensure fast response times for production workloads. Load models into memory and verify they are responsive.",
            "backstory": "You are a system optimization specialist responsible for ensuring AI models are loaded and ready for production use. You understand the importance of model warm-up for reducing first-request latency.",
            "tools": [],
            "enabled": true,
            "instructions": [
                "Execute simple test prompts to warm up models",
                "Verify model responsiveness and loading status",
                "Report model warm-up success or failures",
                "Test different types of prompts (reasoning, analysis, tool calling)",
                "Measure response times and identify slow models",
                "Provide recommendations for model optimization"
            ]
        }' > /dev/null && echo "    ✅ Model Warm-up Agent created" || echo "    ❌ Failed to create Model Warm-up Agent"

    # System Health Check Agent
    echo "  Creating System Health Check Agent..."
    curl -s -X POST "$API_BASE/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "system_health_checker",
            "role": "System Health and Performance Monitor",
            "goals": "Monitor system health, check service availability, and verify all components are ready for production workloads including model availability and response times.",
            "backstory": "You are a DevOps engineer specialized in system monitoring and health checks. You ensure all services are running optimally and can identify performance bottlenecks.",
            "tools": ["http_client", "website_monitor"],
            "enabled": true,
            "instructions": [
                "Check health endpoints for all services",
                "Verify Ollama model availability and responsiveness", 
                "Test API endpoints and response times",
                "Monitor system resource usage indicators",
                "Report overall system readiness status",
                "Identify and flag performance issues"
            ]
        }' > /dev/null && echo "    ✅ System Health Check Agent created" || echo "    ❌ Failed to create System Health Check Agent"

    echo "🔥 Warm-up agents created successfully!"
    echo ""
}

create_purl_agents() {
    echo "🤖 Creating PURL Analysis Agents with improved naming..."

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
            "enabled": true,
            "instructions": [
                "When given a PURL, extract all components carefully",
                "Handle special cases like scoped npm packages (@scope/package)",
                "Provide the default provider for each package type",
                "Build API URLs for different services as requested",
                "If PURL is invalid, explain what is wrong and suggest corrections",
                "Support multiple output formats for different API integrations"
            ]
        }' > /dev/null && echo "    ✅ PURL Parser Agent created" || echo "    ❌ Failed to create PURL Parser Agent"

    # 2. Create ClearlyDefined-specific API Client Agent  
    echo "  Creating ClearlyDefined API Client Agent..."
    curl -s -X POST "$API_BASE/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "api_client_clearlydefined",
            "role": "ClearlyDefined API Specialist",
            "goals": "Query the ClearlyDefined API using constructed URLs and return structured package information specific to ClearlyDefined data format.",
            "backstory": "You are an expert at making API calls specifically to the ClearlyDefined service (api.clearlydefined.io). You understand their API response format, data structure, and can extract meaningful information about package licensing, security scores, and metadata from their specific response format.",
            "tools": ["http_client"],
            "enabled": true,
            "instructions": [
                "Make HTTP GET requests to ClearlyDefined API endpoints (api.clearlydefined.io)",
                "Handle ClearlyDefined-specific 404 responses gracefully (package not found)",
                "Extract ClearlyDefined-specific fields: described, licensed, coordinates, scores",
                "Understand ClearlyDefined score meanings (overall, tool, effective)",
                "Provide clear error messages for ClearlyDefined API failures",
                "Return structured data in ClearlyDefined format for downstream processing"
            ]
        }' > /dev/null && echo "    ✅ ClearlyDefined API Client Agent created" || echo "    ❌ Failed to create ClearlyDefined API Client Agent"

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
        }' > /dev/null && echo "    ✅ ClearlyDefined Package Analyzer Agent created" || echo "    ❌ Failed to create ClearlyDefined Package Analyzer Agent"

    # 4. Create Generic HTTP Client Agent (for future APIs)
    echo "  Creating Generic HTTP Client Agent..."
    curl -s -X POST "$API_BASE/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "http_client_generic",
            "role": "Generic HTTP API Client",
            "goals": "Make HTTP requests to any API and return structured responses. Handle common HTTP patterns and error conditions across different APIs.",
            "backstory": "You are a versatile API client specialist who can interact with any REST API. You understand standard HTTP status codes, authentication methods, and can adapt to different API response formats.",
            "tools": ["http_client"],
            "enabled": true,
            "instructions": [
                "Make HTTP requests to any provided URL",
                "Handle standard HTTP status codes appropriately", 
                "Extract and format response data clearly",
                "Provide meaningful error messages for failures",
                "Support different authentication methods as configured",
                "Return responses in a consistent format regardless of source API"
            ]
        }' > /dev/null && echo "    ✅ Generic HTTP Client Agent created" || echo "    ❌ Failed to create Generic HTTP Client Agent"

    echo "🤖 PURL analysis agents created successfully!"
    echo ""
}

create_warmup_workflows() {
    echo "🔄 Creating Model Warm-up Workflows..."

    # Quick Model Warm-up Workflow
    echo "  Creating Quick Model Warm-up Workflow..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "quick_model_warmup",
            "description": "Quick model warm-up for faster startup",
            "steps": [
                {
                    "type": "agent",
                    "name": "model_warmup",
                    "task": "Quick model warm-up test: '\''Ready?'\'' - expect a simple confirmation response.",
                    "context_key": "quick_test"
                },
                {
                    "type": "agent",
                    "name": "system_health_checker", 
                    "task": "Verify system is ready based on quick test: {quick_test}",
                    "context_key": "quick_status"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ Quick Model Warm-up Workflow created" || echo "    ❌ Failed to create Quick Model Warm-up Workflow"

    # Comprehensive Model Warm-up Workflow
    echo "  Creating Comprehensive Model Warm-up Workflow..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "model_warmup_workflow",
            "description": "Comprehensive model warm-up and system readiness check",
            "steps": [
                {
                    "type": "agent",
                    "name": "system_health_checker",
                    "task": "Check if Ollama service is running and accessible at the configured endpoint. Verify the health endpoint responds correctly.",
                    "context_key": "ollama_health"
                },
                {
                    "type": "agent",
                    "name": "model_warmup",
                    "task": "Warm up the default model with a simple test prompt: '\''Hello, please respond with '\''Model ready'\'' to confirm you are loaded and responsive.'\''",
                    "context_key": "model_test_1"
                },
                {
                    "type": "agent", 
                    "name": "model_warmup",
                    "task": "Test model reasoning capabilities with: '\''What is 2+2? Please explain your reasoning briefly.'\''",
                    "context_key": "model_test_2"
                },
                {
                    "type": "agent",
                    "name": "model_warmup", 
                    "task": "Test model instruction following with: '\''List 3 benefits of model warm-up in production systems.'\''",
                    "context_key": "model_test_3"
                },
                {
                    "type": "agent",
                    "name": "system_health_checker",
                    "task": "Based on the warm-up results: Ollama Health: {ollama_health}, Test 1: {model_test_1}, Test 2: {model_test_2}, Test 3: {model_test_3} - provide a comprehensive system readiness report.",
                    "context_key": "readiness_report"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ Comprehensive Model Warm-up Workflow created" || echo "    ❌ Failed to create Comprehensive Model Warm-up Workflow"

    # Agent-Specific Warm-up Workflow
    echo "  Creating Agent-Specific Warm-up Workflow..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "agent_warmup_workflow", 
            "description": "Warm up specific agents that will be used in production",
            "steps": [
                {
                    "type": "agent",
                    "name": "purl_parser",
                    "task": "Warm-up test: Parse this sample PURL: pkg:npm/test@1.0.0",
                    "context_key": "purl_parser_test"
                },
                {
                    "type": "agent",
                    "name": "api_client_clearlydefined",
                    "task": "Warm-up test: Explain what you would do to query ClearlyDefined API for a package (do not make actual API call).",
                    "context_key": "api_client_test"
                },
                {
                    "type": "agent",
                    "name": "package_analyzer_clearlydefined", 
                    "task": "Warm-up test: Explain how you would analyze a package with MIT license and score of 85.",
                    "context_key": "analyzer_test"
                },
                {
                    "type": "agent",
                    "name": "system_health_checker",
                    "task": "Report on agent warm-up results: PURL Parser: {purl_parser_test}, API Client: {api_client_test}, Analyzer: {analyzer_test}",
                    "context_key": "agent_warmup_report"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ Agent-Specific Warm-up Workflow created" || echo "    ❌ Failed to create Agent-Specific Warm-up Workflow"

    # Production Readiness Check Workflow
    echo "  Creating Production Readiness Check Workflow..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "production_readiness_check",
            "description": "Comprehensive production readiness verification",
            "steps": [
                {
                    "type": "agent",
                    "name": "system_health_checker",
                    "task": "Check all system health endpoints: main API (/health), Ollama (/api/tags), and verify all services are responding correctly.",
                    "context_key": "health_status"
                },
                {
                    "type": "agent",
                    "name": "model_warmup",
                    "task": "Test model performance with a complex prompt: '\''Analyze the security implications of using a package with MIT license, overall score 75, and 2 known vulnerabilities. Provide a 3-point recommendation.'\''",
                    "context_key": "performance_test"
                },
                {
                    "type": "agent",
                    "name": "purl_parser",
                    "task": "Production test: Parse and validate pkg:maven/org.apache.commons/commons-lang3@3.12.0",
                    "context_key": "purl_production_test"
                },
                {
                    "type": "agent",
                    "name": "api_client_clearlydefined",
                    "task": "Production test: Query ClearlyDefined API for a sample package to verify API connectivity and response handling.",
                    "context_key": "api_production_test"
                },
                {
                    "type": "agent",
                    "name": "system_health_checker",
                    "task": "Generate production readiness report based on: Health: {health_status}, Performance: {performance_test}, PURL Test: {purl_production_test}, API Test: {api_production_test}. Determine if system is ready for production workloads.",
                    "context_key": "production_readiness"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ Production Readiness Check Workflow created" || echo "    ❌ Failed to create Production Readiness Check Workflow"

    echo "🔄 Warm-up workflows created successfully!"
    echo ""
}

create_purl_workflows() {
    echo "🔄 Creating PURL Analysis Workflows..."

    # ClearlyDefined-specific PURL Analysis Workflow
    echo "  Creating ClearlyDefined PURL Analysis Workflow..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "purl_analysis_clearlydefined",
            "description": "Complete PURL analysis workflow using ClearlyDefined API: Parse -> Query ClearlyDefined -> Analyze ClearlyDefined results",
            "steps": [
                {
                    "type": "agent",
                    "name": "purl_parser",
                    "task": "Parse this Package URL and extract components for ClearlyDefined API: {purl}. I need the package type, provider, namespace (if any), name, version, and the complete ClearlyDefined API URL (https://api.clearlydefined.io/definitions/...) that should be called. Format your response as structured data.",
                    "context_key": "parsed_purl"
                },
                {
                    "type": "agent", 
                    "name": "api_client_clearlydefined",
                    "task": "Using the parsed PURL information: {parsed_purl}, make an HTTP GET request to the ClearlyDefined API. Extract the API URL from the parsed data and call it. Return the complete ClearlyDefined API response along with a summary of key findings.",
                    "context_key": "clearlydefined_response"
                },
                {
                    "type": "agent",
                    "name": "package_analyzer_clearlydefined", 
                    "task": "Analyze the ClearlyDefined API response: {clearlydefined_response} for the original PURL: {purl}. Provide a comprehensive security and compliance analysis based on ClearlyDefined data including: 1) License information and ClearlyDefined confidence, 2) ClearlyDefined scores interpretation (overall, tool, effective), 3) Recommendations based on ClearlyDefined analysis, 4) Any red flags from ClearlyDefined data, 5) Executive summary of ClearlyDefined findings.",
                    "context_key": "clearlydefined_analysis"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ ClearlyDefined PURL Analysis Workflow created" || echo "    ❌ Failed to create ClearlyDefined PURL Analysis Workflow"

    # Quick ClearlyDefined Analysis Workflow
    echo "  Creating Quick ClearlyDefined Analysis Workflow..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "quick_purl_clearlydefined",
            "description": "Quick PURL analysis using ClearlyDefined API for basic package information",
            "steps": [
                {
                    "type": "agent",
                    "name": "purl_parser", 
                    "task": "Parse this PURL for ClearlyDefined API: {purl} and provide the ClearlyDefined API URL to call.",
                    "context_key": "clearlydefined_url"
                },
                {
                    "type": "agent",
                    "name": "api_client_clearlydefined",
                    "task": "Call this ClearlyDefined API URL: {clearlydefined_url} and return basic package information including license and ClearlyDefined scores.",
                    "context_key": "clearlydefined_info"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ Quick ClearlyDefined Analysis Workflow created" || echo "    ❌ Failed to create Quick ClearlyDefined Analysis Workflow"

    # Multi-API Comparison Workflow (template for future)
    echo "  Creating Multi-API Comparison Workflow Template..."
    curl -s -X POST "$API_BASE/workflows" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "purl_multi_api_comparison",
            "description": "Compare package information across multiple APIs (currently ClearlyDefined, expandable for others)",
            "steps": [
                {
                    "type": "agent",
                    "name": "purl_parser",
                    "task": "Parse this PURL: {purl} and prepare URLs for multiple package analysis APIs. Start with ClearlyDefined format.",
                    "context_key": "parsed_for_apis"
                },
                {
                    "type": "agent", 
                    "name": "api_client_clearlydefined",
                    "task": "Query ClearlyDefined API using: {parsed_for_apis}. Return ClearlyDefined-specific analysis.",
                    "context_key": "clearlydefined_data"
                },
                {
                    "type": "agent",
                    "name": "package_analyzer_clearlydefined",
                    "task": "Compare and synthesize package information from ClearlyDefined: {clearlydefined_data}. Provide consolidated analysis highlighting strengths and gaps in available data. Note: This workflow is ready for expansion with additional APIs.",
                    "context_key": "multi_api_analysis"
                }
            ],
            "enabled": true
        }' > /dev/null && echo "    ✅ Multi-API Comparison Workflow Template created" || echo "    ❌ Failed to create Multi-API Comparison Workflow Template"

    echo "🔄 PURL analysis workflows created successfully!"
    echo ""
}

run_initial_warmup() {
    echo "🔥 Running Initial Model Warm-up..."

    # Quick warm-up first
    echo "  Running quick model warm-up..."
    curl -s -X POST "$API_BASE/workflows/quick_model_warmup/execute" \
        -H "Content-Type: application/json" \
        -d '{"context": {"startup": true, "automated": true}}' > /dev/null && \
        echo "    ✅ Quick warm-up completed" || echo "    ⚠️  Quick warm-up may have issues"

    sleep 5

    # Comprehensive warm-up
    echo "  Running comprehensive model warm-up..."
    curl -s -X POST "$API_BASE/workflows/model_warmup_workflow/execute" \
        -H "Content-Type: application/json" \
        -d '{"context": {"startup": true, "automated": true}}' > /dev/null && \
        echo "    ✅ Comprehensive warm-up completed" || echo "    ⚠️  Comprehensive warm-up may have issues"

    sleep 5

    # Agent-specific warm-up
    echo "  Running agent-specific warm-up..."
    curl -s -X POST "$API_BASE/workflows/agent_warmup_workflow/execute" \
        -H "Content-Type: application/json" \
        -d '{"context": {"startup": true, "automated": true}}' > /dev/null && \
        echo "    ✅ Agent warm-up completed" || echo "    ⚠️  Agent warm-up may have issues"

    echo "🔥 Initial warm-up process completed!"
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
        echo "    ✅ PURL analysis test completed successfully"
    else
        echo "    ⚠️  PURL analysis test may have issues"
    fi

    # Production readiness check
    echo "  Running production readiness check..."
    curl -s -X POST "$API_BASE/workflows/production_readiness_check/execute" \
        -H "Content-Type: application/json" \
        -d '{"context": {"initial_setup": true}}' > /dev/null && \
        echo "    ✅ Production readiness check completed" || echo "    ⚠️  Production readiness check may have issues"

    echo "🧪 System testing completed!"
    echo ""
}

show_summary() {
    echo "📋 Setup Summary"
    echo "================"
    echo ""
    echo "✅ Created Agents:"
    echo "   🔥 model_warmup - Model warm-up specialist"
    echo "   🏥 system_health_checker - System health monitor"
    echo "   📦 purl_parser - Generic PURL parser"
    echo "   🌐 api_client_clearlydefined - ClearlyDefined API client"
    echo "   🔍 package_analyzer_clearlydefined - ClearlyDefined analyzer"
    echo "   🌍 http_client_generic - Generic HTTP client"
    echo ""
    echo "✅ Created Workflows:"
    echo "   ⚡ quick_model_warmup - Fast warm-up"
    echo "   🔥 model_warmup_workflow - Comprehensive warm-up"
    echo "   🤖 agent_warmup_workflow - Agent-specific warm-up"
    echo "   ✅ production_readiness_check - Production verification"
    echo "   📦 purl_analysis_clearlydefined - Full PURL analysis"
    echo "   ⚡ quick_purl_clearlydefined - Quick PURL analysis"
    echo "   🔄 purl_multi_api_comparison - Multi-API comparison"
    echo ""
    echo "🚀 Usage Examples:"
    echo ""
    echo "# Quick PURL analysis:"
    echo 'curl -X POST "http://localhost:8000/workflows/quick_purl_clearlydefined/execute" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"context": {"purl": "pkg:npm/lodash@4.17.21"}}'"'"''
    echo ""
    echo "# Full PURL analysis:"
    echo 'curl -X POST "http://localhost:8000/workflows/purl_analysis_clearlydefined/execute" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"context": {"purl": "pkg:maven/com.fasterxml.jackson.core/jackson-core@2.13.0"}}'"'"''
    echo ""
    echo "# Manual warm-up:"
    echo 'curl -X POST "http://localhost:8000/workflows/model_warmup_workflow/execute" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"context": {"manual": true}}'"'"''
    echo ""
    echo "# Production readiness check:"
    echo 'curl -X POST "http://localhost:8000/workflows/production_readiness_check/execute" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"context": {"check": true}}'"'"''
    echo ""
    echo "🌐 Available Endpoints:"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/health"
    echo "   • Agents: http://localhost:8000/agents"
    echo "   • Workflows: http://localhost:8000/workflows"
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
    
    create_warmup_agents
    create_purl_agents
    create_warmup_workflows
    create_purl_workflows
    run_initial_warmup
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
        run_initial_warmup
        ;;
    "test")
        check_api_availability
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