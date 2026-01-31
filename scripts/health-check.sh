#!/bin/bash

# 🏥 Script de Vérification de Santé du Système

echo "╔════════════════════════════════════════════════════════╗"
echo "║ 🏥 AIME - Vérification de Santé du Système             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Compteurs
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Fonction pour tester
test_check() {
    local name=$1
    local command=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $name"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌${NC} $name"
        return 1
    fi
}

# ============ BACKEND CHECKS ============
echo -e "${BLUE}🚀 Backend Checks${NC}"
echo "─────────────────"

test_check "Backend écoute port 8000" "lsof -i :8000 >/dev/null 2>&1"
test_check "Endpoint /health répond" "curl -s http://localhost:8000/health >/dev/null 2>&1"
test_check "Endpoint /api/v1/history/stats répond" "curl -s http://localhost:8000/api/v1/history/stats >/dev/null 2>&1"
test_check "Endpoint /api/v1/collection/albums répond" "curl -s http://localhost:8000/api/v1/collection/albums >/dev/null 2>&1"
test_check "Endpoint /api/v1/history/timeline répond" "curl -s http://localhost:8000/api/v1/history/timeline?date=$(date +%Y-%m-%d) >/dev/null 2>&1"

echo ""

# ============ FRONTEND CHECKS ============
echo -e "${BLUE}🎨 Frontend Checks${NC}"
echo "───────────────────"

test_check "Frontend écoute port 5173" "lsof -i :5173 >/dev/null 2>&1"
test_check "Frontend accessible" "curl -s http://localhost:5173 >/dev/null 2>&1"

echo ""

# ============ DATABASE CHECKS ============
echo -e "${BLUE}💾 Base de Données${NC}"
echo "──────────────────"

test_check "Fichier DB existe" "[ -f './data/music_tracker.db' ]"
test_check "DB accessible" "[ -r './data/music_tracker.db' ]"

echo ""

# ============ SYSTEM CHECKS ============
echo -e "${BLUE}⚙️  Système${NC}"
echo "──────────"

test_check "Python 3 installé" "python3 --version >/dev/null 2>&1"
test_check "Node.js installé" "node --version >/dev/null 2>&1"
test_check "npm installé" "npm --version >/dev/null 2>&1"

echo ""

# ============ DATA CHECKS ============
echo -e "${BLUE}📊 Données${NC}"
echo "──────────"

# Compter les données
TRACKS=$(curl -s http://localhost:8000/api/v1/history/tracks?page=1&page_size=1 2>/dev/null | jq '.total' 2>/dev/null || echo "?")
ALBUMS=$(curl -s http://localhost:8000/api/v1/collection/albums?page=1&page_size=1 2>/dev/null | jq '.total' 2>/dev/null || echo "?")

echo -e "  Tracks: ${BLUE}$TRACKS${NC}"
echo -e "  Albums: ${BLUE}$ALBUMS${NC}"

echo ""

# ============ RÉSUMÉ ============
echo "╔════════════════════════════════════════════════════════╗"

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "║ ${GREEN}✅ TOUS LES TESTS RÉUSSIS ($PASSED_CHECKS/$TOTAL_CHECKS)${NC}           ║"
    RESULT=0
else
    echo -e "║ ${YELLOW}⚠️  $PASSED_CHECKS/$TOTAL_CHECKS tests réussis${NC}                    ║"
    RESULT=1
fi

echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Conseils
if [ $RESULT -ne 0 ]; then
    echo -e "${YELLOW}💡 Conseils:${NC}"
    echo "  1. Vérifiez que ./scripts/start-dev.sh tourne"
    echo "  2. Consultez docs/TROUBLESHOOTING-INFRASTRUCTURE.md"
    echo "  3. Essayez: killall -9 python3; sleep 2; ./scripts/start-dev.sh"
    echo ""
fi

exit $RESULT
