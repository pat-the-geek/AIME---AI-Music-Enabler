#!/usr/bin/env bash
# Script pour exécuter la suite de tests avec coverage

set -e  # Exit on error

echo "🧪 AIME - AI Music Enabler - Test Suite"
echo "========================================"

# Créer le répertoire de rapports
mkdir -p test-reports

# Run different test categories
echo ""
echo "📋 Exécution des tests..."
echo ""

# 1. Tests unitaires
echo "✅ Tests unitaires..."
pytest tests/unit -v --tb=short

# 2. Tests d'intégration
echo ""
echo "✅ Tests d'intégration..."
pytest tests/integration -v --tb=short

# 3. Tests E2E (plus lents)
echo ""
echo "✅ Tests E2E..."
pytest tests/e2e -v --tb=short -m "not slow"

# 4. Tous les tests avec coverage
echo ""
echo "✅ Tous les tests avec coverage..."
pytest tests/ \
    --cov=app \
    --cov-report=html:test-reports/coverage \
    --cov-report=term-missing \
    --cov-report=xml \
    --junit-xml=test-reports/junit.xml \
    -v

# Afficher le résumé
echo ""
echo "📊 Résumé des résultats:"
echo "========================"

if [ -f "test-reports/coverage/.index.html" ]; then
    echo "✅ Coverage report: test-reports/coverage/index.html"
fi

if [ -f "test-reports/junit.xml" ]; then
    echo "✅ JUnit report: test-reports/junit.xml"
fi

if [ -f "test-reports/pytest.log" ]; then
    echo "✅ Pytest log: test-reports/pytest.log"
fi

echo ""
echo "✨ Tests terminés!"
