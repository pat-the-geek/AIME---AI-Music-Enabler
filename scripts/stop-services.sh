#!/bin/bash
# AIME - Stop All Services (Bridge + Backend + Frontend)
# Usage: ./scripts/stop-services.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../" && pwd)"
PID_DIR="/tmp/aime_pids"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}  Arrêt des services AIME${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo ""

# Arrêter le bridge
echo -n "🌉 Roon Bridge... "
if lsof -ti :3330 >/dev/null 2>&1; then
    lsof -ti :3330 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Stopped${NC}"
    rm -f "$PID_DIR/bridge.pid"
else
    echo -e "${YELLOW}(not running)${NC}"
fi

# Arrêter le backend
echo -n "🎵 Backend... "
if lsof -ti :8000 >/dev/null 2>&1; then
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Stopped${NC}"
    rm -f "$PID_DIR/backend.pid"
else
    echo -e "${YELLOW}(not running)${NC}"
fi

# Arrêter le frontend (si en développement)
echo -n "⚛️  Frontend... "
if lsof -ti :5173 >/dev/null 2>&1; then
    lsof -ti :5173 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Stopped${NC}"
    rm -f "$PID_DIR/frontend.pid"
else
    echo -e "${YELLOW}(not running)${NC}"
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo "To start again, run: ./scripts/start-services.sh"
