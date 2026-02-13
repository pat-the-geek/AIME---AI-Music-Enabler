#!/bin/bash

# Script de démarrage du projet en mode développement

echo "🎵 AIME - AI Music Enabler - Démarrage Mode Développement"
echo "=========================================================="

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Variables
BACKEND_PORT=8000
FRONTEND_PORT=5173
MAX_RETRIES=3
RETRY_DELAY=2

# Fonction pour tuer les processus au Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Arrêt des services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    # Attendre 2 secondes puis forcer si nécessaire
    sleep 2
    kill -9 $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Fonction pour vérifier si un port est libre
check_port() {
    local port=$1
    lsof -i :$port >/dev/null 2>&1 && return 1 || return 0
}

# Fonction pour libérer un port
free_port() {
    local port=$1
    echo -e "${YELLOW}Tentative de libération du port $port...${NC}"
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 1
}

# Vérifier les ports
if ! check_port $BACKEND_PORT; then
    echo -e "${RED}⚠️  Port $BACKEND_PORT en cours d'utilisation${NC}"
    free_port $BACKEND_PORT
    sleep 1
    if ! check_port $BACKEND_PORT; then
        echo -e "${RED}❌ Impossible de libérer le port $BACKEND_PORT${NC}"
        exit 1
    fi
fi

# Démarrer le backend avec retry
echo -e "${BLUE}🚀 Démarrage Backend (Port $BACKEND_PORT)...${NC}"
export PROJECT_ROOT="$(pwd)"
cd backend

BACKEND_STARTED=0
for i in $(seq 1 $MAX_RETRIES); do
    source .venv/bin/activate 2>/dev/null || {
        echo -e "${RED}❌ Impossible d'activer le virtualenv${NC}"
        exit 1
    }
    
    uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port $BACKEND_PORT >/dev/null 2>&1 &
    BACKEND_PID=$!
    
    # Attendre que le backend se lance
    sleep 2
    
    # Vérifier si le backend est prêt
    if curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
        BACKEND_STARTED=1
        break
    else
        echo -e "${YELLOW}Tentative $i/$MAX_RETRIES échouée, nouvelle tentative...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        sleep $RETRY_DELAY
    fi
done

cd ..

if [ $BACKEND_STARTED -eq 0 ]; then
    echo -e "${RED}❌ Impossible de démarrer le backend après $MAX_RETRIES tentatives${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend démarré (PID: $BACKEND_PID)${NC}"

# Attendre que le backend soit complètement prêt
sleep 1

# Démarrer le frontend
echo -e "${BLUE}🚀 Démarrage Frontend (Port $FRONTEND_PORT)...${NC}"
cd frontend
npm run dev >/dev/null 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ Frontend démarré (PID: $FRONTEND_PID)${NC}"

echo -e "\n${GREEN}✅ Services démarrés avec succès!${NC}"
echo ""
echo -e "${YELLOW}Backend API:${NC}"
echo "  http://localhost:$BACKEND_PORT"
echo "  http://localhost:$BACKEND_PORT/docs (Documentation)"
echo ""
echo -e "${YELLOW}Frontend:${NC}"
echo "  http://localhost:$FRONTEND_PORT"
echo ""
echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"
echo ""

# Attendre les processus
wait
