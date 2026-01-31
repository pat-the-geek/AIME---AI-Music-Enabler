#!/bin/bash

# Script de démarrage robuste pour AIME
# Gère le démarrage et le redémarrage automatique du backend et frontend
# Avec validation complète et gestion des erreurs

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DATA_DIR="$PROJECT_DIR/data"
CONFIG_DIR="$PROJECT_DIR/config"
VENV="$PROJECT_DIR/.venv"

# Vérifier l'existence du venv
if [ ! -d "$VENV" ]; then
    echo "❌ Virtual environment not found at $VENV"
    echo "Run: python3 -m venv $VENV && source $VENV/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

BACKEND_LOG="/tmp/aime_backend.log"
FRONTEND_LOG="/tmp/aime_frontend.log"
PID_DIR="/tmp/aime_pids"

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Créer le répertoire des PIDs
mkdir -p "$PID_DIR"

# Créer les répertoires de données
mkdir -p "$DATA_DIR"
mkdir -p "$CONFIG_DIR"

# Fonction pour arrêter proprement
cleanup() {
    echo -e "${YELLOW}Arrêt des services...${NC}"
    
    if [ -f "$PID_DIR/backend.pid" ]; then
        PID=$(cat "$PID_DIR/backend.pid")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${BLUE}Stopping backend (PID: $PID)...${NC}"
            kill $PID 2>/dev/null || true
            sleep 2
            kill -9 $PID 2>/dev/null || true
        fi
    fi
    
    if [ -f "$PID_DIR/frontend.pid" ]; then
        PID=$(cat "$PID_DIR/frontend.pid")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${BLUE}Stopping frontend (PID: $PID)...${NC}"
            kill $PID 2>/dev/null || true
            sleep 2
            kill -9 $PID 2>/dev/null || true
        fi
    fi
    
    # Tuer les processus restants sur les ports
    lsof -ti :8000 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti :5173 2>/dev/null | xargs kill -9 2>/dev/null || true
    
    echo -e "${GREEN}Services arrêtés${NC}"
    exit 0
}

# Trap pour Ctrl+C
trap cleanup SIGINT SIGTERM EXIT

# Fonction pour vérifier les prérequis
check_prerequisites() {
    echo -e "${BLUE}=== Vérification des prérequis ===${NC}"
    
    # Vérifier Python
    if ! "$VENV/bin/python" --version > /dev/null 2>&1; then
        echo -e "${RED}❌ Python not found in venv${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Python available${NC}"
    
    # Vérifier les imports critiques
    if ! "$VENV/bin/python" -c "import fastapi; import sqlalchemy; import uvicorn" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Installing backend dependencies...${NC}"
        cd "$BACKEND_DIR"
        "$VENV/bin/pip" install -q -r requirements.txt --timeout=60
        cd "$PROJECT_DIR"
    fi
    echo -e "${GREEN}✅ Backend dependencies OK${NC}"
    
    # Vérifier Node.js si le frontend existe
    if [ -d "$FRONTEND_DIR" ]; then
        if ! command -v npm &> /dev/null; then
            echo -e "${RED}❌ npm not found (frontend requires Node.js)${NC}"
            return 1
        fi
        echo -e "${GREEN}✅ npm available${NC}"
    fi
    
    # Vérifier les permissions
    if [ ! -w "$DATA_DIR" ]; then
        echo -e "${RED}❌ No write permission for data directory: $DATA_DIR${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Permissions OK${NC}"
    
    return 0
}

# Fonction pour démarrer le backend avec retry
start_backend() {
    echo ""
    echo -e "${BLUE}=== Démarrage du backend ===${NC}"
    
    cd "$BACKEND_DIR"
    
    # Tuer les processus précédents sur le port 8000
    lsof -ti :8000 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 1
    
    # Démarrer le backend
    nohup "$VENV/bin/python" -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --loop uvloop \
        --timeout-keep-alive 75 \
        --timeout-graceful-shutdown 30 \
        > "$BACKEND_LOG" 2>&1 &
    
    local backend_pid=$!
    echo $backend_pid > "$PID_DIR/backend.pid"
    
    # Attendre le démarrage avec retry
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        sleep 1
        
        # Vérifier que le processus est toujours actif
        if ! kill -0 $backend_pid 2>/dev/null; then
            echo -e "${RED}❌ Backend process died${NC}"
            echo "Last 30 lines of log:"
            tail -30 "$BACKEND_LOG"
            return 1
        fi
        
        # Vérifier la santé
        if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend started (PID: $backend_pid)${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $((attempt % 5)) -eq 0 ]; then
            echo -e "${YELLOW}Waiting for backend... ($attempt/$max_attempts)${NC}"
        fi
    done
    
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "Last 30 lines of log:"
    tail -30 "$BACKEND_LOG"
    return 1
}

# Fonction pour démarrer le frontend avec retry
start_frontend() {
    echo ""
    echo -e "${BLUE}=== Démarrage du frontend ===${NC}"
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${YELLOW}⚠️  Frontend directory not found, skipping${NC}"
        return 0
    fi
    
    cd "$FRONTEND_DIR"
    
    # Vérifier et installer les dépendances
    if [ ! -d "node_modules" ] || [ ! -f "package-lock.json" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm ci --silent --prefer-offline --no-audit 2>/dev/null || npm install --silent 2>/dev/null
    fi
    
    # Tuer les processus précédents sur le port 5173
    lsof -ti :5173 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 1
    
    # Démarrer le frontend
    nohup npm run dev \
        > "$FRONTEND_LOG" 2>&1 &
    
    local frontend_pid=$!
    echo $frontend_pid > "$PID_DIR/frontend.pid"
    
    # Attendre le démarrage avec retry
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        sleep 1
        
        # Vérifier que le processus est toujours actif
        if ! kill -0 $frontend_pid 2>/dev/null; then
            echo -e "${RED}❌ Frontend process died${NC}"
            echo "Last 30 lines of log:"
            tail -30 "$FRONTEND_LOG"
            return 1
        fi
        
        # Vérifier si le port répond
        if curl -sf http://localhost:5173 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend started (PID: $frontend_pid)${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $((attempt % 5)) -eq 0 ]; then
            echo -e "${YELLOW}Waiting for frontend... ($attempt/$max_attempts)${NC}"
        fi
    done
    
    echo -e "${YELLOW}⚠️  Frontend startup timeout (may still be starting)${NC}"
    return 0
}

# Fonction de monitoring
monitor_services() {
    echo ""
    echo -e "${GREEN}=== Services démarrés ===${NC}"
    echo -e "${GREEN}Backend:  http://localhost:8000${NC}"
    echo -e "${GREEN}Docs:     http://localhost:8000/docs${NC}"
    echo -e "${GREEN}Frontend: http://localhost:5173${NC}"
    echo ""
    echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"
    echo ""
    
    local max_consecutive_failures=3
    local backend_failures=0
    local frontend_failures=0
    
    while true; do
        sleep 15
        
        # Vérifier le backend
        if ! curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            backend_failures=$((backend_failures + 1))
            echo -e "${YELLOW}⚠️  Backend unhealthy ($backend_failures/$max_consecutive_failures)${NC}"
            
            if [ $backend_failures -ge $max_consecutive_failures ]; then
                echo -e "${YELLOW}🔄 Restarting backend...${NC}"
                if start_backend; then
                    backend_failures=0
                    echo -e "${GREEN}Backend restarted successfully${NC}"
                else
                    echo -e "${RED}Failed to restart backend${NC}"
                fi
            fi
        else
            if [ $backend_failures -gt 0 ]; then
                echo -e "${GREEN}✅ Backend recovered${NC}"
            fi
            backend_failures=0
        fi
        
        # Vérifier le frontend
        if [ -d "$FRONTEND_DIR" ] && [ -f "$PID_DIR/frontend.pid" ]; then
            if ! curl -sf http://localhost:5173 >/dev/null 2>&1; then
                frontend_failures=$((frontend_failures + 1))
                echo -e "${YELLOW}⚠️  Frontend unhealthy ($frontend_failures/$max_consecutive_failures)${NC}"
                
                if [ $frontend_failures -ge $max_consecutive_failures ]; then
                    echo -e "${YELLOW}🔄 Restarting frontend...${NC}"
                    if start_frontend; then
                        frontend_failures=0
                        echo -e "${GREEN}Frontend restarted successfully${NC}"
                    fi
                fi
            else
                if [ $frontend_failures -gt 0 ]; then
                    echo -e "${GREEN}✅ Frontend recovered${NC}"
                fi
                frontend_failures=0
            fi
        fi
    done
}

# Main execution
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  AIME - AI Music Enabler - Startup    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Vérifier les prérequis
if ! check_prerequisites; then
    echo -e "${RED}Prerequisite check failed${NC}"
    exit 1
fi

# Démarrer les services
if ! start_backend; then
    echo -e "${RED}Failed to start backend${NC}"
    exit 1
fi

sleep 2

if ! start_frontend; then
    echo -e "${RED}Failed to start frontend${NC}"
    exit 1
fi

# Monitorer les services
monitor_services
