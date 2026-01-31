#!/bin/bash

# Script de vérification robuste de l'état des services
# Utilisé pour les liveness et readiness probes Docker

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
TIMEOUT=5
RETRIES=2

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_backend() {
    local attempt=1
    
    while [ $attempt -le $RETRIES ]; do
        if timeout $TIMEOUT curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend health check passed${NC}"
            return 0
        fi
        
        if [ $attempt -lt $RETRIES ]; then
            echo -e "${YELLOW}⚠️  Backend health check failed (attempt $attempt/$RETRIES), retrying...${NC}"
            sleep 1
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ Backend health check failed after $RETRIES attempts${NC}"
    return 1
}

check_readiness() {
    if timeout $TIMEOUT curl -sf "$BACKEND_URL/ready" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend readiness check passed${NC}"
        return 0
    fi
    
    echo -e "${RED}❌ Backend readiness check failed${NC}"
    return 1
}

# Traiter les arguments
case "${1:-health}" in
    health)
        check_backend
        ;;
    ready)
        check_readiness
        ;;
    *)
        echo "Usage: $0 {health|ready}"
        exit 1
        ;;
esac
