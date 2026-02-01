#!/bin/bash
# Test des endpoints de playlist

echo "🔍 Test des endpoints de création de playlist"
echo "=============================================="

# Vérifier que le backend répond
echo ""
echo "1️⃣ Vérification du backend sur http://localhost:8000"
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Le backend n'est pas accessible sur le port 8000"
    exit 1
fi
echo "✅ Backend accessible"

# Test endpoint manuelle
echo ""
echo "2️⃣ Test POST /api/v1/playlists (mode manuelle)"
RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/playlists" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Manual","track_ids":[1,2]}')

if echo "$RESULT" | grep -q "\"id\""; then
    echo "✅ Succès:"
    echo "$RESULT" | python3 -m json.tool
else
    echo "❌ Erreur:"
    echo "$RESULT"
fi

# Test endpoint génération
echo ""
echo "3️⃣ Test POST /api/v1/playlists/generate (mode IA)"
RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/playlists/generate" \
  -H "Content-Type: application/json" \
  -d '{"algorithm":"top_sessions","max_tracks":10}')

if echo "$RESULT" | grep -q "\"id\""; then
    echo "✅ Succès:"
    echo "$RESULT" | python3 -m json.tool
else
    echo "❌ Erreur:"
    echo "$RESULT"
fi

# Test GET la liste
echo ""
echo "4️⃣ Test GET /api/v1/playlists"
RESULT=$(curl -s "http://localhost:8000/api/v1/playlists")

if echo "$RESULT" | grep -q "\"id\""; then
    echo "✅ Succès - playlists trouvées:"
    echo "$RESULT" | python3 -m json.tool 2>/dev/null | head -20
else
    echo "❌ Erreur:"
    echo "$RESULT"
fi

echo ""
echo "✅ Tests terminés"
