# Guide de Démarrage Rapide - AIME - AI Music Enabler

## 📦 Installation Rapide

### 1. Vérifier les prérequis

```bash
# Vérifier Python 3.10-3.13 (recommandé)
python3 --version

# ⚠️ Si vous avez Python 3.14, voir [TROUBLESHOOTING.md#problème-1](../troubleshooting/TROUBLESHOOTING.md#problème-1)

# Vérifier Node.js 18+
node --version
```

### 2. Installation automatique

```bash
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
./scripts/setup.sh
```

### 3. Démarrage

```bash
./scripts/start-dev.sh
```

## 🎯 Accès

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs

## 🔧 Configuration

Les API keys sont déjà configurées dans `config/secrets.json`:

- ✅ Last.fm (tracking)
- ✅ Spotify (images)
- ✅ Discogs (collection)
- ✅ EurIA/Infomaniak (IA)

## 📝 Premières Étapes

### 1. Démarrer le Tracker Last.fm

1. Aller sur http://localhost:5173/settings
2. Cliquer sur "Démarrer le Tracker"
3. Le tracker va interroger Last.fm toutes les 2 minutes

### 2. Synchroniser la Collection Discogs

Via l'API:

```bash
curl -X POST http://localhost:8000/api/v1/services/discogs/sync
```

### 3. Explorer l'Application

- **Collection**: Voir vos albums Discogs
- **Journal**: Voir l'historique d'écoute en temps réel
- **Timeline**: Visualisation horaire (en développement)
- **Playlists**: Générer des playlists (en développement)
- **Analytics**: Statistiques d'écoute (en développement)

## 🐛 Dépannage Rapide

### Le backend ne démarre pas

```bash
cd backend
source .venv/bin/activate

# Vérifier les dépendances
pip install -r requirements.txt

# ⚠️ Si Python 3.14: installer SQLAlchemy dev
pip uninstall -y sqlalchemy
pip install git+https://github.com/sqlalchemy/sqlalchemy.git@main

# Initialiser la base
python3 -c "from app.database import init_db; init_db()"

# Démarrer
uvicorn app.main:app --reload --reload-dir app
```

### Le frontend ne démarre pas

```bash
cd frontend
npm install
npm run dev
```

### Base de données ne se crée pas

```bash
# Créer le répertoire data manuellement
mkdir -p data

# Définir la variable PROJECT_ROOT
export PROJECT_ROOT="$(pwd)"

# Initialiser la base
cd backend
source .venv/bin/activate
python3 -c "from app.database import init_db; init_db()"
```

### Reloads infinis du backend

Si le backend redémarre constamment, utilisez `--reload-dir app`:
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

### Erreur "metadata is reserved"

Si vous voyez cette erreur, votre version a le problème résolu dans les commits récents.
Vérifiez que `backend/app/models/album.py` utilise `album_metadata` et non `metadata`.

### Pour plus d'aide

Consultez le **[Guide de Dépannage Complet](./TROUBLESHOOTING.md)** qui documente tous les problèmes connus et leurs solutions détaillées.

## 📚 Plus d'Informations

- [README complet](../README.md)
- [Documentation API](./API.md)
- [Architecture du projet](./ARCHITECTURE.md)
- [**Guide de Dépannage**](./TROUBLESHOOTING.md) ⭐ **Nouveau!**
- [Spécification complète](../SPECIFICATION-REACT-REBUILD.md)

## 🎵 Bon Tracking Musical!
