#!/bin/bash

# Vérification rapide de l'intégration Settings - Résultats d'Optimisation

echo "🔍 VÉRIFICATION DE L'INTÉGRATION"
echo "================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Compteur
total=0
passed=0

# Test 1: Fichier config/OPTIMIZATION-RESULTS.json existe
echo -n "1. Fichier config/OPTIMIZATION-RESULTS.json... "
((total++))
if [ -f "config/OPTIMIZATION-RESULTS.json" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

# Test 2: Fichier est du JSON valide
echo -n "2. JSON valide... "
((total++))
if python3 -c "import json; json.load(open('config/OPTIMIZATION-RESULTS.json'))" 2>/dev/null; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ INVALIDE${NC}"
fi

# Test 3: Fichier services.py modifié
echo -n "3. Backend endpoint /services/scheduler/optimization-results... "
((total++))
if grep -q "get_optimization_results" backend/app/api/v1/services.py; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

# Test 4: Syntaxe Python OK
echo -n "4. Syntaxe Python backend/app/api/v1/services.py... "
((total++))
if python3 -m py_compile backend/app/api/v1/services.py 2>/dev/null; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ ERREUR${NC}"
fi

# Test 5: Fichier Settings.tsx modifié
echo -n "5. Frontend hook useQuery('scheduler-optimization-results')... "
((total++))
if grep -q "scheduler-optimization-results" frontend/src/pages/Settings.tsx; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

# Test 6: Section UI dans Settings
echo -n "6. Section UI 'Résultats d'Optimisation IA'... "
((total++))
if grep -q "Résultats d'Optimisation IA" frontend/src/pages/Settings.tsx; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

# Test 7: Documentation technique existe
echo -n "7. Documentation technique (SETTINGS-OPTIMIZATION-DISPLAY.md)... "
((total++))
if [ -f "docs/SETTINGS-OPTIMIZATION-DISPLAY.md" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

# Test 8: Guide utilisateur existe
echo -n "8. Guide utilisateur (GUIDE-UTILISATEUR-OPTIMIZATION-SETTINGS.md)... "
((total++))
if [ -f "docs/GUIDE-UTILISATEUR-OPTIMIZATION-SETTINGS.md" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

# Test 9: Résumé d'intégration existe
echo -n "9. Résumé d'intégration (INTEGRATION-SETTINGS-OPTIMIZATION.md)... "
((total++))
if [ -f "docs/INTEGRATION-SETTINGS-OPTIMIZATION.md" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

# Test 10: Données de base dans le JSON
echo -n "10. Données de base dans JSON (status, database_analysis)... "
((total++))
if grep -q '"status".*"COMPLETED"' config/OPTIMIZATION-RESULTS.json && \
   grep -q '"database_analysis"' config/OPTIMIZATION-RESULTS.json; then
    echo -e "${GREEN}✅ OK${NC}"
    ((passed++))
else
    echo -e "${RED}❌ MANQUANT${NC}"
fi

echo ""
echo "================================="
echo -e "${BLUE}Résultat: $passed/$total tests réussis${NC}"
echo "================================="

if [ $passed -eq $total ]; then
    echo -e "${GREEN}🎉 INTÉGRATION COMPLÈTE ET VÉRIFIÉE!${NC}"
    echo ""
    echo "Prochaines étapes:"
    echo "1. Déployer le backend (services.py modifié)"
    echo "2. Déployer le frontend (Settings.tsx modifié)"
    echo "3. Redémarrer les services"
    echo "4. Accéder à Settings pour voir la nouvelle section"
    exit 0
else
    echo -e "${YELLOW}⚠️  QUELQUES TESTS ONT ÉCHOUÉ${NC}"
    echo ""
    echo "Vérifiez les points marqués ❌"
    exit 1
fi
