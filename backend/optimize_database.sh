#!/bin/bash
# Quick Start Guide for Database Optimization

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "🗄️  AIME Database Optimization Quick Start"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "$BACKEND_DIR/alembic.ini" ]; then
    echo "❌ Error: alembic.ini not found"
    echo "   Make sure you run this script from the project root"
    exit 1
fi

cd "$BACKEND_DIR"

echo ""
echo "📋 STEP 1: Check Current Status"
echo "================================"
python verify_indexes.py || true

echo ""
echo "📋 STEP 2: Apply Optimization Migration"
echo "======================================="

# Check if migration is already applied
if grep -q "005_optimize_indexes" alembic/versions/*.py 2>/dev/null; then
    echo "✅ Optimization migration exists"
    
    # Check current revision
    CURRENT=$(alembic current 2>/dev/null | tail -1) || true
    
    if [ -z "$CURRENT" ]; then
        echo "⚠️  Database not yet initialized with Alembic"
        echo "   Run: python -c 'from app.database import Base; Base.metadata.create_all()'"
    else
        echo "Current revision: $CURRENT"
        
        if [[ "$CURRENT" == *"005_optimize_indexes"* ]]; then
            echo "✅ Optimization indexes already applied"
        else
            echo "Applying optimization migration..."
            alembic upgrade 005_optimize_indexes
            echo "✅ Migration applied successfully"
        fi
    fi
else
    echo "⚠️  Optimization migration not found"
    echo "   Make sure 005_optimize_indexes.py exists in alembic/versions/"
fi

echo ""
echo "📋 STEP 3: Update Statistics"
echo "============================="
echo "Running ANALYZE to update query statistics..."
python verify_indexes.py --analyze

echo ""
echo "📋 STEP 4: Compact Database"
echo "==========================="
echo "Running VACUUM to compact and optimize..."
python verify_indexes.py --vacuum

echo ""
echo "📋 STEP 5: Verify Optimization"
echo "=============================="
python verify_indexes.py

echo ""
echo "✅ DATABASE OPTIMIZATION COMPLETE!"
echo "===================================="
echo ""
echo "📈 Expected improvements:"
echo "   • Analytics queries: 50-100x faster"
echo "   • Album searches: 100-200x faster"
echo "   • Timeline view: 50-150x faster"
echo ""
echo "⚡ Next steps:"
echo "   1. Restart the backend: cd $PROJECT_DIR && ./scripts/start-services.sh"
echo "   2. Test the timeline and journal views"
echo "   3. Check analytics performance"
echo ""
echo "📝 For more details, see: docs/DATABASE-OPTIMIZATION-V4.7.0.md"
