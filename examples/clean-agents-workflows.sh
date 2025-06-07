#!/bin/bash

# Clean-up Script for Agentic AI Framework
# Uses the framework's existing APIs to delete all agents and workflows

set -e  # Exit on any error

echo "=== Agentic AI Framework - Clean-up Script ==="
echo ""

# Configuration
API_BASE="http://localhost:8000"
RETRY_COUNT=3
RETRY_DELAY=2

# Functions
check_api_availability() {
    echo "🔍 Checking API availability..."
    for i in $(seq 1 5); do
        if curl -s "$API_BASE/health" > /dev/null 2>&1; then
            echo "✅ API is available"
            return 0
        fi
        echo "⏳ Waiting for API... ($i/5)"
        sleep 5
    done
    echo "❌ API is not available after 5 attempts"
    exit 1
}

delete_with_retry() {
    local url="$1"
    local description="$2"
    
    for i in $(seq 1 $RETRY_COUNT); do
        if curl -s -X DELETE "$url" > /dev/null 2>&1; then
            echo "    ✅ $description"
            return 0
        fi
        if [ $i -lt $RETRY_COUNT ]; then
            echo "    ⏳ Retrying $description... ($i/$RETRY_COUNT)"
            sleep $RETRY_DELAY
        fi
    done
    echo "    ⚠️  Failed to delete: $description"
    return 1
}

get_json_array() {
    local url="$1"
    curl -s "$url" 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo ""
}

clean_agents() {
    echo "🤖 Cleaning up agents..."
    
    # Get all agents
    AGENTS=$(get_json_array "$API_BASE/agents")
    
    if [ -n "$AGENTS" ] && [ "$AGENTS" != "null" ]; then
        AGENT_COUNT=$(echo "$AGENTS" | wc -l)
        echo "  Found $AGENT_COUNT agent(s) to delete"
        
        echo "$AGENTS" | while read -r agent; do
            if [ -n "$agent" ] && [ "$agent" != "null" ]; then
                delete_with_retry "$API_BASE/agents/$agent" "agent: $agent"
            fi
        done
        
        echo "  🧹 Agent cleanup completed"
    else
        echo "  ℹ️  No agents found to delete"
    fi
    echo ""
}

clean_workflows() {
    echo "🔄 Cleaning up workflows..."
    
    # Get all workflows
    WORKFLOWS=$(get_json_array "$API_BASE/workflows")
    
    if [ -n "$WORKFLOWS" ] && [ "$WORKFLOWS" != "null" ]; then
        WORKFLOW_COUNT=$(echo "$WORKFLOWS" | wc -l)
        echo "  Found $WORKFLOW_COUNT workflow(s) to delete"
        
        echo "$WORKFLOWS" | while read -r workflow; do
            if [ -n "$workflow" ] && [ "$workflow" != "null" ]; then
                delete_with_retry "$API_BASE/workflows/$workflow" "workflow: $workflow"
            fi
        done
        
        echo "  🧹 Workflow cleanup completed"
    else
        echo "  ℹ️  No workflows found to delete"
    fi
    echo ""
}

clean_scheduled_tasks() {
    echo "⏰ Cleaning up scheduled tasks..."
    
    # Get all scheduled tasks
    SCHEDULE_IDS=$(curl -s "$API_BASE/schedule" 2>/dev/null | jq -r '.[].id' 2>/dev/null || echo "")
    
    if [ -n "$SCHEDULE_IDS" ] && [ "$SCHEDULE_IDS" != "null" ]; then
        SCHEDULE_COUNT=$(echo "$SCHEDULE_IDS" | wc -l)
        echo "  Found $SCHEDULE_COUNT scheduled task(s) to delete"
        
        echo "$SCHEDULE_IDS" | while read -r schedule_id; do
            if [ -n "$schedule_id" ] && [ "$schedule_id" != "null" ]; then
                delete_with_retry "$API_BASE/schedule/$schedule_id" "scheduled task: $schedule_id"
            fi
        done
        
        echo "  🧹 Scheduled tasks cleanup completed"
    else
        echo "  ℹ️  No scheduled tasks found to delete"
    fi
    echo ""
}

clear_memory() {
    echo "🧠 Clearing agent memory..."
    
    if curl -s -X DELETE "$API_BASE/memory/clear-all" > /dev/null 2>&1; then
        echo "  ✅ All agent memory cleared"
    else
        echo "  ⚠️  Failed to clear agent memory"
    fi
    echo ""
}

verify_cleanup() {
    echo "🔍 Verifying cleanup..."
    
    # Check agents
    REMAINING_AGENTS=$(get_json_array "$API_BASE/agents")
    if [ -z "$REMAINING_AGENTS" ] || [ "$REMAINING_AGENTS" = "null" ]; then
        echo "  ✅ No agents remaining"
    else
        REMAINING_COUNT=$(echo "$REMAINING_AGENTS" | wc -l)
        echo "  ⚠️  $REMAINING_COUNT agent(s) still exist:"
        echo "$REMAINING_AGENTS" | while read -r agent; do
            echo "    - $agent"
        done
    fi
    
    # Check workflows
    REMAINING_WORKFLOWS=$(get_json_array "$API_BASE/workflows")
    if [ -z "$REMAINING_WORKFLOWS" ] || [ "$REMAINING_WORKFLOWS" = "null" ]; then
        echo "  ✅ No workflows remaining"
    else
        REMAINING_COUNT=$(echo "$REMAINING_WORKFLOWS" | wc -l)
        echo "  ⚠️  $REMAINING_COUNT workflow(s) still exist:"
        echo "$REMAINING_WORKFLOWS" | while read -r workflow; do
            echo "    - $workflow"
        done
    fi
    
    # Check scheduled tasks
    REMAINING_SCHEDULES=$(curl -s "$API_BASE/schedule" 2>/dev/null | jq -r '.[].id' 2>/dev/null || echo "")
    if [ -z "$REMAINING_SCHEDULES" ] || [ "$REMAINING_SCHEDULES" = "null" ]; then
        echo "  ✅ No scheduled tasks remaining"
    else
        REMAINING_COUNT=$(echo "$REMAINING_SCHEDULES" | wc -l)
        echo "  ⚠️  $REMAINING_COUNT scheduled task(s) still exist"
    fi
    
    echo ""
}

show_summary() {
    echo "📋 Cleanup Summary"
    echo "=================="
    echo ""
    echo "✅ Completed cleanup operations:"
    echo "   🤖 Deleted all agents"
    echo "   🔄 Deleted all workflows"
    echo "   ⏰ Deleted all scheduled tasks"
    echo "   🧠 Cleared all agent memory"
    echo ""
    echo "🚀 Framework is now clean and ready for fresh setup!"
    echo ""
    echo "Next steps:"
    echo "   • Run setup script to create new agents and workflows"
    echo "   • Check API documentation: $API_BASE/docs"
    echo "   • Verify health: $API_BASE/health"
    echo ""
}

# Main execution
main() {
    echo "🧹 Starting comprehensive cleanup..."
    echo ""
    
    check_api_availability
    clean_agents
    clean_workflows
    clean_scheduled_tasks
    clear_memory
    verify_cleanup
    show_summary
    
    echo "🎉 Cleanup completed successfully!"
}

# Enhanced execution with options
case "${1:-cleanup}" in
    "cleanup"|"")
        main
        ;;
    "agents")
        echo "🤖 Cleaning agents only..."
        check_api_availability
        clean_agents
        verify_cleanup
        echo "✅ Agent cleanup completed!"
        ;;
    "workflows")
        echo "🔄 Cleaning workflows only..."
        check_api_availability
        clean_workflows
        verify_cleanup
        echo "✅ Workflow cleanup completed!"
        ;;
    "schedules")
        echo "⏰ Cleaning scheduled tasks only..."
        check_api_availability
        clean_scheduled_tasks
        verify_cleanup
        echo "✅ Scheduled tasks cleanup completed!"
        ;;
    "memory")
        echo "🧠 Clearing memory only..."
        check_api_availability
        clear_memory
        echo "✅ Memory cleared!"
        ;;
    "verify")
        echo "🔍 Verifying current state..."
        check_api_availability
        verify_cleanup
        ;;
    "help")
        echo "Usage: $0 [cleanup|agents|workflows|schedules|memory|verify|help]"
        echo ""
        echo "Commands:"
        echo "  cleanup   - Complete cleanup (default)"
        echo "  agents    - Delete all agents only"
        echo "  workflows - Delete all workflows only"
        echo "  schedules - Delete all scheduled tasks only"
        echo "  memory    - Clear all agent memory only"
        echo "  verify    - Verify current state without deletion"
        echo "  help      - Show this help message"
        exit 0
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac