#!/bin/bash

cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"

echo "=========================================="
echo "NORMALIZATION COMPLETE TEST SUITE"
echo "=========================================="
echo ""

# Kill old processes
echo "[1] Cleaning up old processes..."
pkill -9 python 2>/dev/null
pkill -9 uvicorn 2>/dev/null
sleep 2

# Start backend
echo "[2] Starting backend..."
cd backend
python -m uvicorn app.main:app --port 8000 > /tmp/norm_test_full.log 2>&1 &
BACKEND_PID=$!
sleep 8

# Test health
echo "[3] Testing backend health..."
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$HEALTH" = "healthy" ]; then
    echo "  ✓ Backend healthy"
else
    echo "  ✗ Backend not responding"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Run normalization
echo "[4] Triggering normalization..."
NORM_RESP=$(curl -s -X POST 'http://localhost:8000/api/v1/services/roon/normalize' -H 'Content-Type: application/json' -d '{}')
echo "  Response: $NORM_RESP" | head -c 80
echo ""

# Wait for completion
echo "[5] Waiting for normalization to complete..."
sleep 10

# Check logs for results
echo "[6] Checking results from backend logs..."
RESULTS=$(tail -50 /tmp/norm_test_full.log 2>/dev/null | grep "artists_updated\|albums_updated" | tail -1)
echo "  $RESULTS"

# Message
echo ""
echo "=========================================="
echo "✓ TEST COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Check if database has been updated"
echo "2. Run simulation to see changes needed"
echo "3. Apply normalization from frontend"
echo ""

# Cleanup
kill $BACKEND_PID 2>/dev/null
