#!/bin/bash

# Script de configuration et démarrage complet du projet Music Tracker

set -e

echo "🎵 Music Tracker - Installation Complète"
echo "========================================"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier les prérequis
echo -e "${YELLOW}Vérification des prérequis...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3.10+ requis${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 18+ requis${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prérequis OK${NC}"

# Installation Backend
echo -e "\n${YELLOW}📦 Installation Backend...${NC}"
cd backend

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dépendances Python installées${NC}"

# Initialiser la base de données
echo -e "\n${YELLOW}🗄️  Initialisation base de données...${NC}"
python3 -c "from app.database import init_db; init_db()"
echo -e "${GREEN}✅ Base de données initialisée${NC}"

cd ..

# Installation Frontend
echo -e "\n${YELLOW}📦 Installation Frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✅ Dépendances Node.js installées${NC}"
else
    echo -e "${GREEN}✅ node_modules existe déjà${NC}"
fi

cd ..

# Vérifier configuration
echo -e "\n${YELLOW}🔧 Vérification configuration...${NC}"

if [ ! -f "config/secrets.json" ]; then
    echo -e "${RED}❌ Fichier config/secrets.json manquant${NC}"
    echo "Veuillez créer config/secrets.json avec vos API keys"
    exit 1
fi

echo -e "${GREEN}✅ Configuration OK${NC}"

# Créer les dossiers nécessaires
mkdir -p data/backups

echo -e "\n${GREEN}✅ Installation terminée!${NC}"
echo -e "\n${YELLOW}Pour démarrer l'application:${NC}"
echo "  ./scripts/start-dev.sh"
echo ""
echo -e "${YELLOW}API Documentation:${NC}"
echo "  http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Frontend:${NC}"
echo "  http://localhost:5173"
