# 🚀 Guide de Démarrage et Tests - AIME - AI Music Enabler

## ✅ Démarrer l'Application

### Option 1: Script automatique (recommandé)

```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
./scripts/start-dev.sh
```

**Note**: Ce script lance le backend ET le frontend. Laissez le terminal ouvert.

### Option 2: Démarrage manuel (2 terminaux)

**Terminal 1 - Backend:**
```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
export PROJECT_ROOT="$(pwd)"
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
cd frontend
npm run dev
```

## 🌐 Accès à l'Application

Une fois démarrée, l'application est accessible sur :

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Interface web principale |
| **API Backend** | http://localhost:8000 | API REST |
| **Documentation API** | http://localhost:8000/docs | Swagger UI (interactive) |
| **Alternative API Docs** | http://localhost:8000/redoc | ReDoc (lecture) |

### Ouvrir dans le navigateur (macOS)

```bash
# Ouvrir l'interface web
open http://localhost:5173

# Ouvrir la documentation API
open http://localhost:8000/docs
```

## 🧪 Tests de Base

### 1. Vérifier que tout fonctionne

```bash
# Test 1: Health check
curl http://localhost:8000/health
# Résultat attendu: {"status":"ok","version":"4.0.0"}

# Test 2: Frontend répond
curl -I http://localhost:5173
# Résultat attendu: HTTP/1.1 200 OK

# Test 3: Documentation API
curl -I http://localhost:8000/docs
# Résultat attendu: HTTP/1.1 200 OK
```

### 2. Tester les endpoints API

```bash
# Lister les albums (devrait être vide au début)
curl http://localhost:8000/api/v1/collection/albums

# Lister les artistes
curl http://localhost:8000/api/v1/collection/artists

# Voir l'historique d'écoute
curl http://localhost:8000/api/v1/history/tracks

# Statut du tracker Last.fm
curl http://localhost:8000/api/v1/services/tracker/status
```

### 3. Tester via l'interface web

1. **Ouvrir**: http://localhost:5173

2. **Explorer les pages**:
   - 📀 Collection : Voir vos albums
   - 📝 Journal : Historique d'écoute en temps réel
   - ⚙️ Settings : Configuration du tracker

3. **Démarrer le tracker Last.fm**:
   - Aller dans Settings
   - Cliquer sur "Démarrer le Tracker"
   - Le tracker interrogera Last.fm toutes les 2 minutes

### 4. Ajouter des données de test

#### Via l'API (Swagger UI)

1. Ouvrir http://localhost:8000/docs
2. Développer un endpoint (ex: POST /api/v1/collection/albums)
3. Cliquer "Try it out"
4. Modifier le JSON d'exemple
5. Cliquer "Execute"

#### Via curl

```bash
# Créer un artiste
curl -X POST http://localhost:8000/api/v1/collection/artists \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pink Floyd",
    "country": "GB",
    "year_formed": 1965
  }'

# Créer un album
curl -X POST http://localhost:8000/api/v1/collection/albums \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Dark Side of the Moon",
    "year": 1973,
    "genre": "Progressive Rock",
    "format": "Vinyl",
    "label": "Harvest Records"
  }'
```

## 🔍 Tests Avancés

### Synchroniser avec Discogs

```bash
# Déclencher la synchronisation de votre collection Discogs
curl -X POST http://localhost:8000/api/v1/services/discogs/sync

# Vérifier que des albums ont été importés
curl http://localhost:8000/api/v1/collection/albums?limit=10
```

### Enrichir tous les albums avec Spotify et IA

```bash
# Enrichir TOUS les albums existants avec URLs Spotify et descriptions IA
curl -X POST http://localhost:8000/api/v1/services/ai/enrich-all

# Ou utiliser le script Python
python scripts/enrich_albums.py
```

### Générer une description IA

```bash
# Générer une description IA pour un album
curl -X POST http://localhost:8000/api/v1/services/ai/generate-info \
  -H "Content-Type: application/json" \
  -d '{
    "album_id": 1,
    "artist_name": "Pink Floyd",
    "album_title": "The Dark Side of the Moon",
    "year": 1973,
    "genre": "Progressive Rock"
  }'
```

### Tester le tracker en mode manuel

```bash
# Démarrer le tracker
curl -X POST http://localhost:8000/api/v1/services/tracker/start

# Vérifier le statut
curl http://localhost:8000/api/v1/services/tracker/status

# Arrêter le tracker
curl -X POST http://localhost:8000/api/v1/services/tracker/stop
```

## 📊 Vérifier la Base de Données

```bash
# Voir les tables
sqlite3 data/musique.db ".tables"

# Compter les albums
sqlite3 data/musique.db "SELECT COUNT(*) FROM albums;"

# Voir les dernières écoutes
sqlite3 data/musique.db "SELECT * FROM listening_history ORDER BY listened_at DESC LIMIT 5;"

# Voir les artistes
sqlite3 data/musique.db "SELECT * FROM artists LIMIT 10;"
```

## 🛑 Arrêter l'Application

### Si lancée avec start-dev.sh

Appuyer sur `Ctrl+C` dans le terminal où le script s'exécute.

### Si lancée manuellement

```bash
# Arrêter tous les processus
killall uvicorn
killall node

# Ou trouver et tuer les processus
ps aux | grep -E "(uvicorn|vite)"
# Puis kill <PID>
```

## ⚙️ Personnaliser les Tests

### Modifier les configurations

```bash
# Éditer la config backend
nano config/app.json

# Éditer les secrets (API keys)
nano config/secrets.json

# Variables d'environnement
nano .env
```

### Activer les logs détaillés

```bash
# Backend avec logs debug
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app --log-level debug

# Frontend avec logs
cd frontend
npm run dev -- --debug
```

## 📝 Scénarios de Test Complets

### Scénario 1: Premier lancement complet

1. ✅ Démarrer l'application
2. ✅ Vérifier health check
3. ✅ Ouvrir l'interface web
4. ✅ Configurer Last.fm dans Settings
5. ✅ Démarrer le tracker
6. ✅ Écouter de la musique sur Last.fm
7. ✅ Vérifier que les tracks apparaissent dans le Journal

### Scénario 2: Import collection Discogs

1. ✅ Configurer token Discogs dans config/secrets.json
2. ✅ Lancer la synchronisation
3. ✅ Vérifier les albums dans Collection
4. ✅ Voir les pochettes importées

### Scénario 3: Génération descriptions IA

1. ✅ Avoir des albums dans la collection
2. ✅ Configurer EurIA API key
3. ✅ Demander génération pour un album
4. ✅ Vérifier la description dans l'interface

## 🔗 Ressources

- **Documentation complète**: [README.md](../README.md)
- **Guide de dépannage**: [TROUBLESHOOTING.md](../guides/troubleshooting/TROUBLESHOOTING.md)
- **API Reference**: [API.md](../api/API.md)

## 📞 En cas de problème

1. Vérifier les logs dans le terminal
2. Consulter [TROUBLESHOOTING.md](../guides/troubleshooting/TROUBLESHOOTING.md)
3. Vérifier que la base de données existe: `ls -lh data/musique.db`
4. Tester le health check: `curl http://localhost:8000/health`

---

**Prêt à tester ?** Lancez `./scripts/start-dev.sh` et ouvrez http://localhost:5173 ! 🎵
