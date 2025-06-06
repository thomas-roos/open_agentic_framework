#!/bin/bash
# warmup-manager.sh - Model Warmup Management Script

API_BASE="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}🔥 Model Warmup Manager${NC}"
    echo -e "${CYAN}========================${NC}"
}

print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "FAILED")
            echo -e "${RED}✗${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
    esac
}

check_api() {
    if ! curl -s "$API_BASE/health" >/dev/null 2>&1; then
        print_status "FAILED" "API not available at $API_BASE"
        exit 1
    fi
}

warmup_all_agent_models() {
    print_header
    echo "🔥 Warming up all agent models..."
    echo ""
    
    check_api
    
    response=$(curl -s -X POST "$API_BASE/models/warmup" -H "Content-Type: application/json")
    
    if echo "$response" | jq -e '.successful' >/dev/null 2>&1; then
        successful=$(echo "$response" | jq -r '.successful[]' 2>/dev/null)
        failed=$(echo "$response" | jq -r '.failed[]' 2>/dev/null)
        total=$(echo "$response" | jq -r '.total_models' 2>/dev/null)
        
        echo -e "${GREEN}🎉 Warmup Complete!${NC}"
        echo "Total models: $total"
        echo ""
        
        if [ -n "$successful" ]; then
            echo -e "${GREEN}✅ Successfully warmed:${NC}"
            echo "$successful" | while read -r model; do
                warmup_time=$(echo "$response" | jq -r ".results[\"$model\"].warmup_time" 2>/dev/null)
                echo "  🔥 $model (${warmup_time}s)"
            done
            echo ""
        fi
        
        if [ -n "$failed" ]; then
            echo -e "${RED}❌ Failed to warm:${NC}"
            echo "$failed" | while read -r model; do
                error=$(echo "$response" | jq -r ".results[\"$model\"].error" 2>/dev/null)
                echo "  ✗ $model - $error"
            done
            echo ""
        fi
    else
        print_status "FAILED" "Warmup request failed"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    fi
}

warmup_specific_models() {
    print_header
    echo "🔥 Warming up specific models: $*"
    echo ""
    
    check_api
    
    # Create JSON array of model names
    models_json=$(printf '%s\n' "$@" | jq -R . | jq -s .)
    
    response=$(curl -s -X POST "$API_BASE/models/warmup" \
        -H "Content-Type: application/json" \
        -d "$models_json")
    
    if echo "$response" | jq -e '.successful' >/dev/null 2>&1; then
        successful=$(echo "$response" | jq -r '.successful[]' 2>/dev/null)
        failed=$(echo "$response" | jq -r '.failed[]' 2>/dev/null)
        
        echo -e "${GREEN}🎉 Warmup Complete!${NC}"
        echo ""
        
        if [ -n "$successful" ]; then
            echo -e "${GREEN}✅ Successfully warmed:${NC}"
            echo "$successful" | while read -r model; do
                warmup_time=$(echo "$response" | jq -r ".results[\"$model\"].warmup_time" 2>/dev/null)
                echo "  🔥 $model (${warmup_time}s)"
            done
            echo ""
        fi
        
        if [ -n "$failed" ]; then
            echo -e "${RED}❌ Failed to warm:${NC}"
            echo "$failed" | while read -r model; do
                error=$(echo "$response" | jq -r ".results[\"$model\"].error" 2>/dev/null)
                echo "  ✗ $model - $error"
            done
        fi
    else
        print_status "FAILED" "Warmup request failed"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    fi
}

show_warmup_status() {
    print_header
    echo "📊 Model Warmup Status"
    echo ""
    
    check_api
    
    response=$(curl -s "$API_BASE/models/warmup/status")
    
    if echo "$response" | jq -e '.stats' >/dev/null 2>&1; then
        # Extract stats
        total=$(echo "$response" | jq -r '.stats.total_models')
        active=$(echo "$response" | jq -r '.stats.active_models')
        failed=$(echo "$response" | jq -r '.stats.failed_models')
        success_rate=$(echo "$response" | jq -r '.stats.success_rate')
        avg_time=$(echo "$response" | jq -r '.stats.average_warmup_time_seconds')
        total_usage=$(echo "$response" | jq -r '.stats.total_usage_count')
        
        echo -e "${BLUE}📈 Overall Statistics:${NC}"
        echo "  Total models: $total"
        echo "  Active models: $active"
        echo "  Failed models: $failed"
        echo "  Success rate: ${success_rate}%"
        echo "  Average warmup time: ${avg_time}s"
        echo "  Total usage count: $total_usage"
        echo ""
        
        # Show individual model status
        if [ "$total" -gt 0 ]; then
            echo -e "${BLUE}📋 Individual Model Status:${NC}"
            echo "$response" | jq -r '.models | to_entries[] | "\(.key) \(.value.is_active) \(.value.warmup_time_seconds) \(.value.usage_count) \(.value.last_used)"' | \
            while read -r model is_active warmup_time usage last_used; do
                if [ "$is_active" = "true" ]; then
                    status_icon="🟢"
                    status_text="ACTIVE"
                else
                    status_icon="🔴"
                    status_text="INACTIVE"
                fi
                
                # Format last used time
                last_used_formatted=$(date -d "$last_used" "+%H:%M:%S" 2>/dev/null || echo "$last_used")
                
                echo "  $status_icon $model - $status_text (${warmup_time}s warmup, ${usage} uses, last: $last_used_formatted)"
            done
        fi
    else
        print_status "FAILED" "Failed to get warmup status"
        echo "$response"
    fi
}

show_available_models() {
    print_header
    echo "📋 Available Models"
    echo ""
    
    check_api
    
    models=$(curl -s "$API_BASE/models" | jq -r '.[]' 2>/dev/null)
    
    if [ -n "$models" ]; then
        echo -e "${BLUE}Available models for warmup:${NC}"
        echo "$models" | while read -r model; do
            # Check if model is warmed
            warmup_status=$(curl -s "$API_BASE/models/warmup/status/$model" | jq -r '.is_warmed' 2>/dev/null)
            if [ "$warmup_status" = "true" ]; then
                echo "  🔥 $model (warmed)"
            else
                echo "  ❄️  $model (cold)"
            fi
        done
    else
        print_status "WARNING" "No models found"
    fi
}

show_usage() {
    echo "Usage: $0 [COMMAND] [ARGS...]"
    echo ""
    echo "Commands:"
    echo "  warmup-all              Warm up all agent models"
    echo "  warmup MODEL [MODEL...] Warm up specific models"
    echo "  status                  Show warmup status"
    echo "  models                  Show available models"
    echo "  stats                   Show warmup statistics only"
    echo "  help                    Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 warmup-all"
    echo "  $0 warmup deepseek-r1:1.5b granite3.2:2b"
    echo "  $0 status"
    echo "  $0 models"
}

# Main command handling
case "${1:-}" in
    "warmup-all")
        warmup_all_agent_models
        ;;
    "warmup")
        if [ $# -lt 2 ]; then
            print_status "FAILED" "Please specify model names to warm up"
            echo ""
            show_usage
            exit 1
        fi
        shift
        warmup_specific_models "$@"
        ;;
    "status")
        show_warmup_status
        ;;
    "models")
        show_available_models
        ;;
    "stats")
        check_api
        curl -s "$API_BASE/models/warmup/stats" | jq '.' 2>/dev/null
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    "")
        show_warmup_status
        ;;
    *)
        print_status "FAILED" "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac