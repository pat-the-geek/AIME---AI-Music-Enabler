#!/bin/bash

# Script de démarrage robuste pour AIME
# Gère le démarrage et le redémarrage automatique du backend et frontend

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV="$PROJECT_DIR/.venv"

BACKEND_LOG="/tmp/aime_backend.log"
FRONTEND_LOG="/tmp/aime_frontend.log"
PID_DIR="/tmp/aime_pids"

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Créer le répertoire des PIDs
mkdir -p "$PID_DIR"

# Fonction pour arrêter proprement
cleanup() {
    echo -e "${YELLOW}Arrêt des services...${NC}"
    
    if [ -f "$PID_DIR/backend.pid" ]; then
        kill $(cat "$PID_DIR/backend.pid") 2>/dev/null || true
    fi
    
    if [ -f "$PID_DIR/frontend.pid" ]; then
        kill $(cat "$PID_DIR/frontend.pid") 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Services arrêtés${NC}"
    exit 0
}

# Trap pour Ctrl+C
trap cleanup SIGINT SIGTERM

# Fonction pour démarrer le backend avec retry
start_backend() {
    echo -e "${YELLOW}Démarrage du backend...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Vérifier les dépendances
    if ! "$VENV/bin/python" -c "import fastapi" 2>/dev/null; then
        echo -e "${YELLOW}Installation des dépendances backend...${NC}"
        "$VENV/bin/pip" install -q -r requirements.txt
    fi
    
    # Tuer les processus précédents sur le port 8000
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
    
    # Démarrer le backend
    nohup "$VENV/bin/python" -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --loop uvloop \
        --timeout-keep-alive 75 \
        > "$BACKEND_LOG" 2>&1 &
    
    echo $! > "$PID_DIR/backend.pid"
    sleep 2
    
    # Vérifier que le backend a démarré
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend démarré (PID: $(cat $PID_DIR/backend.pid))${NC}"
        return 0
    else
        echo -e "${RED}❌ Échec du démarrage du backend${NC}"
        tail -20 "$BACKEND_LOG"
        return 1
    fi
}

# Fonction pour démarrer le frontend avec retry
start_frontend() {
    echo -e "${YELLOW}Démarrage du frontend...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # Vérifier les dépendances
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installation des dépendances frontend...${NC}"
        npm ci --silent
    fi
    
    # Tuer les processus précédents sur le port 5173
    lsof -ti :5173 | xargs kill -9 2>/dev/null || true
    sleep 1
    
    # Démarrer le frontend
    nohup npm run dev \
        > "$FRONTEND_LOG" 2>&1 &
    
    echo $! > "$PID_DIR/frontend.pid"
    sleep 3
    
    # Vérifier que le frontend a démarré
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend démarré (PID: $(cat $PID_DIR/frontend.pid))${NC}"
        return 0
    else
        echo -e "${RED}❌ Échec du démarrage du frontend${NC}"
        tail -20 "$FRONTEND_LOG"
        return 1
    fi
}

# Fonction de santé
check_health() {
    local backend_ok=0
    local frontend_ok=0
    
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        backend_ok=1
    fi
    
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        frontend_ok=1
    fi
    
    echo "$backend_ok:$frontend_ok"
}

# Démarrer les services
echo -e "${GREEN}=== AIME - Démarrage des services ===${NC}"
echo "Répertoire du projet: $PROJECT_DIR"
echo ""

# Démarrer backend
if ! start_backend; then
    echo -e "${RED}Impossible de démarrer le backend${NC}"
    exit 1
fi

sleep 2

# Démarrer frontend
if ! start_frontend; then
    echo -e "${RED}Impossible de démarrer le frontend${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Services démarrés ===${NC}"
echo -e "${GREEN}Backend: http://localhost:8000${NC}"
echo -e "${GREEN}Frontend: http://localhost:5173${NC}"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter les services"
echo ""

# Boucle de monitoring
max_retries=5
backend_failures=0
frontend_failures=0

while true; do
    sleep 10
    
    # Vérifier le backend
    if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
        backend_failures=$((backend_failures + 1))
        echo -e "${YELLOW}⚠️  Backend ne répond pas (tentative $backend_failures/$max_retries)${NC}"
        
        if [ $backend_failures -ge $max_retries ]; then
            echo -e "${YELLOW}Redémarrage du backend...${NC}"
            if start_backend; then
                backend_failures=0
            fi
        fi
    else
        backend_failures=0
    fi
    
    # Vérifier le frontend
    if ! curl -s http://localhost:5173 >/dev/null 2>&1; then
        frontend_failures=$((frontend_failures + 1))
        echo -e "${YELLOW}⚠️  Frontend ne répond pas (tentative $frontend_failures/$max_retries)${NC}"
        
        if [ $frontend_failures -ge $max_retries ]; then
            echo -e "${YELLOW}Redémarrage du frontend...${NC}"
            if start_frontend; then
                frontend_failures=0
            fi
        fi
    else
        frontend_failures=0
    fi
done
