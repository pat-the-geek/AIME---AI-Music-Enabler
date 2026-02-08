#!/bin/bash
set -e

echo "🛑 Arrêt des services..."
killall -9 python3 python node 2>/dev/null || true
sleep 2

echo "🌉 Démarrage du bridge..."
cd /Users/patrickostertag/Documents/DataForIA/AIME\ -\ AI\ Music\ Enabler
node roon-bridge/app.js > /tmp/bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 3

echo "⚙️  Démarrage du backend..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 5

echo ""
echo "🔍 Test 1: Recherche d'album..."
curl -s -X POST http://localhost:8000/api/v1/roon/search-album \
  -H "Content-Type: application/json" \
  -d '{"artist":"Gold Panda","album":"Lucky Shiner"}' | jq .

echo ""
echo "▶️  Test 2: Lancer la lecture (devrait être RAPIDE)..."
START=$(date +%s%N)
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/roon/play-album-by-name \
  -H "Content-Type: application/json" \
  -d '{"artist_name":"Gold Panda","album_title":"Lucky Shiner (Deluxe Edition)"}')
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))

echo "$RESPONSE" | jq .
echo "⏱️  Durée: ${DURATION}ms"

if [ "$DURATION" -lt 1000 ]; then
    echo "✅ SUCCÈS: Réponse < 1 seconde!"
else
    echo "⚠️  LENT: ${DURATION}ms (attendu < 1000ms)"
fi

echo ""
echo "🧹 Nettoyage..."
kill $BACKEND_PID $BRIDGE_PID 2>/dev/null || true
echo "✓ Tests terminés"
