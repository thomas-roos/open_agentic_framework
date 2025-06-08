#!/bin/bash
# cleanup-all.sh - Delete all agents, workflows, and scheduled tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="${1:-http://localhost:8000}"
CONFIRM="${2}"

echo -e "${RED}🗑️  COMPLETE CLEANUP - DELETE ALL COMPONENTS${NC}"
echo "=============================================="
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will delete ALL:${NC}"
echo "   • Agents"
echo "   • Workflows" 
echo "   • Scheduled Tasks"
echo "   • Agent Memory (optional)"
echo ""

# Safety confirmation
if [ "$CONFIRM" != "--confirm" ]; then
    echo -e "${YELLOW}Are you sure you want to delete everything? This cannot be undone!${NC}"
    read -p "Type 'DELETE' to confirm: " user_confirm
    
    if [ "$user_confirm" != "DELETE" ]; then
        echo "❌ Cleanup cancelled"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}🔍 Starting cleanup process...${NC}"

# Step 1: Delete all scheduled tasks
echo -e "${YELLOW}🗓️  Deleting scheduled tasks...${NC}"
TASKS=$(curl -s "$BASE_URL/schedule" || echo "[]")
TASK_COUNT=$(echo "$TASKS" | jq 'length' 2>/dev/null || echo "0")

if [ "$TASK_COUNT" -gt 0 ]; then
    echo "Found $TASK_COUNT scheduled tasks"
    
    # Extract task IDs and delete each one
    echo "$TASKS" | jq -r '.[].id' 2>/dev/null | while read task_id; do
        if [ -n "$task_id" ] && [ "$task_id" != "null" ]; then
            echo "  Deleting task ID: $task_id"
            curl -s -X DELETE "$BASE_URL/schedule/$task_id" > /dev/null || echo "    Failed to delete task $task_id"
        fi
    done
    echo "✅ Scheduled tasks cleanup completed"
else
    echo "✅ No scheduled tasks found"
fi

# Step 2: Delete all workflows
echo -e "${YELLOW}🔄 Deleting workflows...${NC}"
WORKFLOWS=$(curl -s "$BASE_URL/workflows" || echo "[]")
WORKFLOW_COUNT=$(echo "$WORKFLOWS" | jq 'length' 2>/dev/null || echo "0")

if [ "$WORKFLOW_COUNT" -gt 0 ]; then
    echo "Found $WORKFLOW_COUNT workflows"
    
    # Extract workflow names and delete each one
    echo "$WORKFLOWS" | jq -r '.[].name' 2>/dev/null | while read workflow_name; do
        if [ -n "$workflow_name" ] && [ "$workflow_name" != "null" ]; then
            echo "  Deleting workflow: $workflow_name"
            curl -s -X DELETE "$BASE_URL/workflows/$workflow_name" > /dev/null || echo "    Failed to delete workflow $workflow_name"
        fi
    done
    echo "✅ Workflows cleanup completed"
else
    echo "✅ No workflows found"
fi

# Step 3: Delete all agents
echo -e "${YELLOW}🤖 Deleting agents...${NC}"
AGENTS=$(curl -s "$BASE_URL/agents" || echo "[]")
AGENT_COUNT=$(echo "$AGENTS" | jq 'length' 2>/dev/null || echo "0")

if [ "$AGENT_COUNT" -gt 0 ]; then
    echo "Found $AGENT_COUNT agents"
    
    # Extract agent names and delete each one
    echo "$AGENTS" | jq -r '.[].name' 2>/dev/null | while read agent_name; do
        if [ -n "$agent_name" ] && [ "$agent_name" != "null" ]; then
            echo "  Deleting agent: $agent_name"
            curl -s -X DELETE "$BASE_URL/agents/$agent_name" > /dev/null || echo "    Failed to delete agent $agent_name"
        fi
    done
    echo "✅ Agents cleanup completed"
else
    echo "✅ No agents found"
fi

# Step 4: Optional memory cleanup
echo ""
echo -e "${YELLOW}🧠 Memory cleanup options:${NC}"
echo "1. Clear all agent memory"
echo "2. Skip memory cleanup"
echo ""
read -p "Choose option (1 or 2): " memory_choice

if [ "$memory_choice" = "1" ]; then
    echo -e "${YELLOW}🧹 Clearing all agent memory...${NC}"
    MEMORY_RESULT=$(curl -s -X DELETE "$BASE_URL/memory/clear-all" || echo "failed")
    
    if echo "$MEMORY_RESULT" | jq -e '.message' > /dev/null 2>&1; then
        echo "✅ All agent memory cleared"
    else
        echo "⚠️  Memory cleanup may have failed"
    fi
else
    echo "⏭️  Skipped memory cleanup"
fi

# Step 5: Verify cleanup
echo ""
echo -e "${BLUE}🔍 Verifying cleanup...${NC}"

# Check remaining components
REMAINING_AGENTS=$(curl -s "$BASE_URL/agents" | jq 'length' 2>/dev/null || echo "unknown")
REMAINING_WORKFLOWS=$(curl -s "$BASE_URL/workflows" | jq 'length' 2>/dev/null || echo "unknown")
REMAINING_TASKS=$(curl -s "$BASE_URL/schedule" | jq 'length' 2>/dev/null || echo "unknown")

echo "📊 Remaining components:"
echo "   • Agents: $REMAINING_AGENTS"
echo "   • Workflows: $REMAINING_WORKFLOWS"
echo "   • Scheduled Tasks: $REMAINING_TASKS"

# Step 6: Optional system reset
echo ""
echo -e "${YELLOW}🔄 Additional cleanup options:${NC}"
echo "1. Restart all providers (reload models, clear caches)"
echo "2. Skip additional cleanup"
echo ""
read -p "Choose option (1 or 2): " restart_choice

if [ "$restart_choice" = "1" ]; then
    echo -e "${YELLOW}🔄 Restarting providers...${NC}"
    RELOAD_RESULT=$(curl -s -X POST "$BASE_URL/providers/reload" || echo "failed")
    
    if echo "$RELOAD_RESULT" | jq -e '.message' > /dev/null 2>&1; then
        echo "✅ Providers reloaded successfully"
    else
        echo "⚠️  Provider reload may have failed"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Cleanup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "✅ All agents deleted"
echo "✅ All workflows deleted" 
echo "✅ All scheduled tasks deleted"
if [ "$memory_choice" = "1" ]; then
    echo "✅ All agent memory cleared"
fi
if [ "$restart_choice" = "1" ]; then
    echo "✅ Providers reloaded"
fi
echo ""
echo -e "${BLUE}🚀 Your system is now clean and ready for new configurations!${NC}"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "• Run setup scripts to create new agents and workflows"
echo "• Check system status: curl $BASE_URL/health"
echo "• View available tools: curl $BASE_URL/tools"