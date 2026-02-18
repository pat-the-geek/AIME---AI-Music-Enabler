#!/bin/bash
# health_check.sh - Vérification santé du déploiement Docker AIME - AI Music Enabler

set -e

# Vérifie que les conteneurs sont up
containers=(music-tracker-backend music-tracker-frontend)
for c in "${containers[@]}"; do
  status=$(docker inspect -f '{{.State.Health.Status}}' $c 2>/dev/null || echo "unknown")
  echo "Conteneur $c : $status"
  if [[ "$status" != "healthy" && "$status" != "running" ]]; then
    echo "❌ $c n'est pas healthy !"
    exit 1
  fi
done

# Vérifie la présence des variables d'environnement essentielles
for var in SPOTIFY_CLIENT_ID SPOTIFY_CLIENT_SECRET EURIA_API_URL EURIA_BEARER_TOKEN; do
  val=$(docker exec music-tracker-backend printenv $var 2>/dev/null || echo "")
  if [[ -z "$val" ]]; then
    echo "❌ Variable $var absente dans backend !"
    exit 1
  else
    echo "✅ $var présent"
  fi
done

# Test API backend
curl -s http://localhost:8000/health | grep 'healthy' && echo "✅ API backend OK" || { echo "❌ API backend KO"; exit 1; }

# Test création collection IA (simulation)
resp=$(curl -s -X POST http://localhost:8000/api/v1/collections/ -H 'Content-Type: application/json' --data '{"ai_query": "albums pour cuisiner", "search_type": "ai_query"}')
echo "$resp" | grep 'id' && echo "✅ Création collection IA OK" || { echo "❌ Création collection IA KO"; exit 1; }

# Test récupération albums
coll_id=$(echo "$resp" | jq .id)
albums=$(curl -s http://localhost:8000/api/v1/collections/$coll_id/albums)
echo "$albums" | grep 'title' && echo "✅ Albums associés à la collection" || { echo "❌ Aucun album associé"; exit 1; }

echo "---\nTous les checks sont OK. Déploiement validé."
