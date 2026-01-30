#!/bin/bash

# Script de démarrage du projet en mode développement

set -e

echo "🎵 AIME - AI Music Enabler - Démarrage Mode Développement"
echo "=========================================================="

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonction pour tuer les processus au Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Arrêt des services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Démarrer le backend
echo -e "${BLUE}🚀 Démarrage Backend (Port 8000)...${NC}"
export PROJECT_ROOT="$(pwd)"
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Attendre que le backend démarre
sleep 3

# Démarrer le frontend
echo -e "${BLUE}🚀 Démarrage Frontend (Port 5173)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n${GREEN}✅ Services démarrés!${NC}"
echo ""
echo -e "${YELLOW}Backend API:${NC}"
echo "  http://localhost:8000"
echo "  http://localhost:8000/docs (Documentation)"
echo ""
echo -e "${YELLOW}Frontend:${NC}"
echo "  http://localhost:5173"
echo ""
echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"

# Attendre
wait
