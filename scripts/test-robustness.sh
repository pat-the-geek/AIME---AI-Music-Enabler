#!/bin/bash

# Test complet de robustesse de l'application AIME
# Vérifie tous les composants critiques

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../" && pwd)"
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing: $name... "
    
    # Use separate curl calls for better compatibility
    http_code=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt "$url" 2>/dev/null)
    body=$(cat /tmp/curl_response.txt 2>/dev/null)
    
    if [ ! -z "$http_code" ]; then
        if [ "$http_code" = "$expected_code" ]; then
            echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $http_code)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Connection error)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     AIME Robustness Test Suite        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Vérifier si les services sont en cours d'exécution
echo -e "${YELLOW}Checking services...${NC}"

if ! curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend is not running on $BACKEND_URL${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend is running${NC}"

echo ""
echo -e "${BLUE}=== API Endpoint Tests ===${NC}"

# Tests des endpoints critiques
test_endpoint "GET /" "$BACKEND_URL/" 200
test_endpoint "GET /health" "$BACKEND_URL/health" 200
test_endpoint "GET /ready" "$BACKEND_URL/ready" 200
test_endpoint "GET /docs" "$BACKEND_URL/docs" 200

echo ""
echo -e "${BLUE}=== Collection Endpoints ===${NC}"

# Tests des collections
test_endpoint "GET /api/v1/collection/albums" "$BACKEND_URL/api/v1/collection/albums" 200
test_endpoint "GET /api/v1/collection/artists" "$BACKEND_URL/api/v1/collection/artists" 200
test_endpoint "GET /api/v1/collection/export/markdown" "$BACKEND_URL/api/v1/collection/export/markdown" 200

echo ""
echo -e "${BLUE}=== Database Health ===${NC}"

# Vérifier l'état de la base de données
if response=$(curl -s "$BACKEND_URL/health"); then
    db_status=$(echo "$response" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
    if [ "$db_status" = "healthy" ]; then
        echo -e "${GREEN}✅ Database is healthy${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ Database status: $db_status${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

echo ""
echo -e "${BLUE}=== Performance Tests ===${NC}"

# Test de latence
start_time=$(date +%s%N)
curl -s "$BACKEND_URL/health" > /dev/null
end_time=$(date +%s%N)
latency=$(( (end_time - start_time) / 1000000 ))  # en ms

echo "Health check latency: ${latency}ms"
if [ $latency -lt 1000 ]; then
    echo -e "${GREEN}✅ Latency OK${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Latency is high: ${latency}ms${NC}"
fi

echo ""
echo -e "${BLUE}=== System Resources ===${NC}"

# Vérifier les ressources
echo "Checking disk space..."
disk_usage=$(df "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -lt 90 ]; then
    echo -e "${GREEN}✅ Disk usage: ${disk_usage}%${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Disk usage: ${disk_usage}%${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Vérifier la base de données
echo "Checking database..."
if [ -f "$PROJECT_DIR/data/musique.db" ]; then
    db_size=$(du -h "$PROJECT_DIR/data/musique.db" | cut -f1)
    echo -e "${GREEN}✅ Database found: $db_size${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Database not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}=== Stress Test ===${NC}"

# Test de charge simple
echo "Running simple load test (10 requests)..."
for i in {1..10}; do
    curl -s "$BACKEND_URL/health" > /dev/null &
done
wait

echo -e "${GREEN}✅ Load test completed${NC}"
TESTS_PASSED=$((TESTS_PASSED + 1))

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Test Summary                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
TOTAL=$((TESTS_PASSED + TESTS_FAILED))
PERCENTAGE=$((TESTS_PASSED * 100 / TOTAL))

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! ($PERCENTAGE%)${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed ($PERCENTAGE%)${NC}"
    exit 1
fi
