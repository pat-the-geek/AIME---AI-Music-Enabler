# 🔧 Guide de Dépannage - Infrastructure Stable

## Table des Matières
1. [Problèmes de Démarrage](#problèmes-de-démarrage)
2. [Problèmes de Port](#problèmes-de-port)
3. [Problèmes de Base de Données](#problèmes-de-base-de-données)
4. [Problèmes d'API](#problèmes-dapi)
5. [Vérification de la Santé](#vérification-de-la-santé)

---

## Problèmes de Démarrage

### ❌ Le script start-dev.sh refuse de démarrer

**Symptôme**: `Permission denied` ou commande non trouvée

**Solution**:
```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

### ❌ Le backend ne démarre pas

**Symptôme**: `ERROR: [Errno 48] Address already in use`

**Solution 1 - Vérifier les processus actifs**:
```bash
ps aux | grep uvicorn
ps aux | grep vite
```

**Solution 2 - Tuer les processus zombie**:
```bash
killall -9 python3 2>/dev/null
killall -9 node 2>/dev/null
sleep 2
./scripts/start-dev.sh
```

**Solution 3 - Libérer le port 8000**:
```bash
lsof -ti:8000 | xargs kill -9
sleep 1
./scripts/start-dev.sh
```

---

## Problèmes de Port

### ❌ Port 8000 ou 5173 toujours occupé après arrêt

**Cause**: Socket en TIME_WAIT sur macOS (comportement normal)

**Solution**:
```bash
# Attendre 1-2 minutes OU libérer forcément
lsof -ti:8000 | xargs kill -9  # Port 8000
lsof -ti:5173 | xargs kill -9  # Port 5173
sleep 2
./scripts/start-dev.sh
```

### ✅ Vérifier disponibilité des ports

```bash
netstat -an | grep 8000  # Doit être vide
netstat -an | grep 5173  # Doit être vide
```

---

## Problèmes de Base de Données

### ❌ "Database is locked" ou erreurs SQLite

**Cause**: Plusieurs instances du backend accèdent la BD en même temps

**Solution**:
```bash
# 1. Arrêter tous les processus
killall -9 python3 2>/dev/null

# 2. Vérifier l'intégrité
cd backend
source .venv/bin/activate
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine); print('✅ BD OK')"

# 3. Redémarrer
cd ../..
./scripts/start-dev.sh
```

### ❌ "No such table" ou structure corrompue

**Solution - Réinitialiser la BD**:
```bash
rm -f data/music_tracker.db
./scripts/start-dev.sh  # Recréera la BD
```

---

## Problèmes d'API

### ❌ "Connection refused" vers le backend

**Diagnostic**:
```bash
# Vérifier que le backend écoute
lsof -i :8000

# Tester la connexion
curl -s http://localhost:8000/health | jq .

# Vérifier les logs
tail -50 nohup.out  # Si lancé avec nohup
```

### ❌ Erreurs 500 ou 422 sur les endpoints

**Solutions**:
```bash
# 1. Vérifier l'endpoint de santé
curl -s http://localhost:8000/health

# 2. Consulter les logs du backend
# (regarde la console où le backend s'exécute)

# 3. Tester un endpoint simple
curl -s http://localhost:8000/api/v1/history/stats | jq .

# 4. Vérifier la configuration
curl -s http://localhost:8000/docs  # Documentation Swagger
```

---

## Vérification de la Santé

### ✅ Checklist de démarrage réussi

```bash
echo "1️⃣ Backend Health Check"
curl -s http://localhost:8000/health | jq .

echo ""
echo "2️⃣ Timeline"
curl -s "http://localhost:8000/api/v1/history/timeline?date=$(date +%Y-%m-%d)" | jq '.stats'

echo ""
echo "3️⃣ Historique"
curl -s "http://localhost:8000/api/v1/history/tracks?page=1&page_size=2" | jq '.total'

echo ""
echo "4️⃣ Collection"
curl -s "http://localhost:8000/api/v1/collection/albums?page=1&page_size=2" | jq '.total'

echo ""
echo "5️⃣ Frontend Accessible"
curl -s http://localhost:5173 >/dev/null && echo "✅ Frontend OK" || echo "❌ Frontend KO"
```

### 🚀 Script de vérification complet

```bash
#!/bin/bash
echo "🔍 Vérification de la santé du système"
echo "======================================="

# Backend
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend: ACTIF"
else
    echo "❌ Backend: INACTIF"
    exit 1
fi

# Frontend
if curl -s http://localhost:5173 >/dev/null 2>&1; then
    echo "✅ Frontend: ACTIF"
else
    echo "❌ Frontend: INACTIF"
    exit 1
fi

# DB
if [ -f "data/music_tracker.db" ]; then
    echo "✅ Base de données: EXISTE"
else
    echo "⚠️  Base de données: À créer"
fi

echo ""
echo "✅ Tout semble bon!"
```

---

## Commandes Utiles

### 🧹 Nettoyage complet

```bash
# Arrêter tous les processus
killall -9 python3 2>/dev/null
killall -9 node 2>/dev/null

# Libérer les ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Attendre
sleep 2

# Démarrer frais
./scripts/start-dev.sh
```

### 📊 Monitorer les processus

```bash
# Terminal 1: Monitorer les processus
watch -n 1 'lsof -i :8000,:5173'

# Terminal 2: Logs en temps réel
tail -f nohup.out
```

### 🔍 Déboguer le backend

```bash
cd backend
source .venv/bin/activate
python -c "
from app.database import SessionLocal
from app.models import Track, Album
db = SessionLocal()
print(f'Tracks: {db.query(Track).count()}')
print(f'Albums: {db.query(Album).count()}')
"
```

---

## Variables d'Environnement

**Copier le fichier d'exemple**:
```bash
cp config/.env.example config/.env
# Éditer config/.env avec vos clés API
```

**Variables essentielles pour développement**:
```bash
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=sqlite:///./data/music_tracker.db
CORS_ORIGINS=["http://localhost:5173"]
```

---

## Ressources

- 📖 [Documentation API](docs/API.md)
- 🏗️ [Architecture](docs/ARCHITECTURE.md)
- ⚙️ [Configuration Tracker](docs/config/TRACKER-CONFIG-OPTIMALE.md)
- 🐛 [Rapporter un Bug](https://github.com/yourusername/AIME/issues)

---

**Dernière mise à jour**: 31 janvier 2026
