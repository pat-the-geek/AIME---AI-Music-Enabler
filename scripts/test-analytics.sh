#!/bin/bash

echo "🧪 Testing Advanced Analytics Endpoints..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="http://localhost:8000"

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local params=$3
    
    echo -e "${YELLOW}Testing: $method $endpoint${NC}"
    
    if [ -z "$params" ]; then
        response=$(curl -s -X "$method" "$BASE_URL$endpoint" -H "Content-Type: application/json")
    else
        response=$(curl -s -X "$method" "$BASE_URL$endpoint?$params" -H "Content-Type: application/json")
    fi
    
    # Check if response is valid JSON and not empty
    if echo "$response" | grep -q '.' && ! echo "$response" | grep -q 'error'; then
        echo -e "${GREEN}✓ Success${NC}"
        # Pretty print first 200 chars of response
        echo "$response" | head -c 200
        echo -e "\n"
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "$response"
        echo -e "\n"
    fi
}

# Wait for services to be ready
echo "Checking if services are running..."
sleep 2

# Test health first
echo -e "${YELLOW}=== HEALTH CHECK ===${NC}"
curl -s "$BASE_URL/health" | jq '.' 2>/dev/null || echo "Health check endpoint not responding"
echo ""

# Test Analytics Endpoints
echo -e "${YELLOW}=== ANALYTICS ENDPOINTS ===${NC}"

# Advanced Stats
test_endpoint "/api/v1/analytics/advanced-stats" GET "start_date=2025-01-01&end_date=2025-01-31"

# Discovery Stats
test_endpoint "/api/v1/analytics/discovery-stats" GET "days=30"

# Listening Heatmap
test_endpoint "/api/v1/analytics/listening-heatmap" GET "days=90"

# Mood Timeline
test_endpoint "/api/v1/analytics/mood-timeline" GET "days=30"

# Comparison (requires periods)
test_endpoint "/api/v1/analytics/comparison" GET "period1_start=2025-01-01&period1_end=2025-01-15&period2_start=2025-01-16&period2_end=2025-01-31"

echo -e "${YELLOW}=== EXISTING ENDPOINTS ===${NC}"

# Patterns
test_endpoint "/api/v1/history/patterns"

# Haiku
test_endpoint "/api/v1/history/haiku" GET "days=7"

echo -e "${GREEN}✓ Analytics test suite complete!${NC}"
