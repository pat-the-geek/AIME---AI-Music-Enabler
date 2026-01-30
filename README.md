# 🎵 AIME - AI Music Enabler - Version 4.0.0

Application web moderne pour tracker et analyser l'historique d'écoute musicale depuis Last.fm, avec enrichissement automatique via Spotify, Discogs et IA.

## 🏗️ Architecture

- **Frontend**: React 18 + TypeScript + Material-UI
- **Backend**: FastAPI + Python 3.10+
- **Base de données**: SQLite
- **APIs**: Last.fm, Spotify, Discogs, EurIA (Infomaniak AI)

## 📋 Fonctionnalités

### ✅ Implémentées

1. **Tracking Temps Réel**
   - Surveillance automatique Last.fm toutes les 2 minutes
   - Détection nouveaux tracks écoutés
   - Enrichissement métadonnées (images artistes/albums)
   - Génération automatique descriptions IA

2. **Gestion Collection Discogs**
   - Import collection depuis Discogs API
   - Synchronisation manuelle
   - Visualisation avec pochettes

3. **Journal d'Écoute**
   - Liste chronologique inversée
   - Marquage favoris
   - Affichage images multiples (artiste, album Spotify, album Last.fm)
   - Info IA expandable

4. **API REST Complète**
   - Endpoints pour collection, historique, playlists, services
   - Documentation Swagger auto-générée
   - Validation Pydantic

### 🚧 En Développement

- Timeline horaire par jour
- Génération playlists (7 algorithmes)
- Analytics et statistiques avancées
- Export playlists (M3U, JSON, CSV)

## 🚀 Installation

### Prérequis

- Python 3.10-3.13 (⚠️ Python 3.14 nécessite SQLAlchemy dev - voir [TROUBLESHOOTING](docs/TROUBLESHOOTING.md#problème-1-python-314-incompatible-avec-sqlalchemy))
- Node.js 18+
- Git

### Installation Rapide

```bash
# Cloner le repository
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"

# Donner les permissions d'exécution aux scripts
chmod +x scripts/*.sh

# Exécuter l'installation
./scripts/setup.sh
```

### Installation Manuelle

#### Backend

```bash
cd backend

# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Initialiser base de données
python3 -c "from app.database import init_db; init_db()"
```

#### Frontend

```bash
cd frontend

# Installer dépendances
npm install
```

## 🎯 Démarrage

### Mode Développement

```bash
# Démarrer backend + frontend
./scripts/start-dev.sh
```

Ou manuellement:

```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### URLs

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs

## 📁 Structure du Projet

```
music-tracker/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/v1/         # Routes API
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── schemas/        # Schémas Pydantic
│   │   ├── services/       # Services (Spotify, Last.fm, etc.)
│   │   └── main.py         # Point d'entrée
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Application React
│   ├── src/
│   │   ├── pages/         # Pages principales
│   │   ├── components/    # Composants réutilisables
│   │   ├── api/           # Client API
│   │   └── types/         # Types TypeScript
│   ├── package.json
│   └── Dockerfile
├── config/                 # Configuration
│   ├── app.json           # Config application
│   └── secrets.json       # API keys (GITIGNORE)
├── data/                   # Données
│   └── musique.db         # Base SQLite
├── scripts/               # Scripts utilitaires
│   ├── setup.sh
│   └── start-dev.sh
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

Les API keys sont déjà configurées dans `config/secrets.json`:

- **Last.fm**: Tracking d'écoute
- **Spotify**: Images artistes/albums
- **Discogs**: Collection musicale
- **EurIA**: Génération descriptions IA

## 🐳 Docker

```bash
# Construire et lancer avec Docker Compose
docker-compose up -d

# Arrêter
docker-compose down
```

## 📚 Documentation API

Endpoints principaux:

### Collection
- `GET /api/v1/collection/albums` - Liste albums avec pagination
- `GET /api/v1/collection/albums/{id}` - Détail album
- `POST /api/v1/collection/albums` - Créer album
- `PUT /api/v1/collection/albums/{id}` - Modifier album
- `DELETE /api/v1/collection/albums/{id}` - Supprimer album

### Historique
- `GET /api/v1/history/tracks` - Journal chronologique
- `GET /api/v1/history/timeline` - Timeline horaire
- `GET /api/v1/history/stats` - Statistiques
- `POST /api/v1/history/tracks/{id}/love` - Marquer favori

### Playlists
- `GET /api/v1/playlists` - Liste playlists
- `POST /api/v1/playlists/generate` - Générer playlist
- `GET /api/v1/playlists/{id}` - Détail playlist
- `GET /api/v1/playlists/{id}/export` - Exporter playlist

### Services
- `GET /api/v1/services/tracker/status` - Statut tracker
- `POST /api/v1/services/tracker/start` - Démarrer tracker
- `POST /api/v1/services/tracker/stop` - Arrêter tracker
- `POST /api/v1/services/discogs/sync` - Synchroniser Discogs
- `POST /api/v1/services/ai/generate-info` - Générer info IA

Documentation complète: http://localhost:8000/docs

## 🧪 Tests

```bash
# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm run test
```

## 🔧 Dépannage

Si vous rencontrez des problèmes lors de l'installation ou du démarrage:

- **Base de données ne se crée pas**: Voir [Problème 4](docs/TROUBLESHOOTING.md#problème-4-chemin-de-base-de-données-incorrect)
- **Python 3.14 incompatibilité**: Voir [Problème 1](docs/TROUBLESHOOTING.md#problème-1-python-314-incompatible-avec-sqlalchemy)
- **Reloads infinis**: Voir [Problème 6](docs/TROUBLESHOOTING.md#problème-6-reloads-infinis-duvicorn)
- **Autres problèmes**: Consultez le [Guide de Dépannage Complet](docs/TROUBLESHOOTING.md)

### Problèmes Connus Résolus

1. ✅ Python 3.14 incompatibilité avec SQLAlchemy (solution: SQLAlchemy dev version)
2. ✅ Attribut `metadata` réservé dans modèle Album (solution: renommé en `album_metadata`)
3. ✅ Import ForeignKey manquant (solution: ajouté à playlist.py)
4. ✅ Chemin base de données incorrect (solution: variable d'environnement PROJECT_ROOT)
5. ✅ Reloads infinis d'Uvicorn (solution: --reload-dir app)

## 📝 TODO

- [ ] Implémenter Timeline horaire complète
- [ ] Implémenter page Analytics avec charts
- [ ] Implémenter générateur de playlists
- [ ] Ajouter tests frontend
- [ ] Ajouter migration script JSON → SQLite
- [ ] Dark mode
- [ ] Responsive mobile complet

## 🤝 Contribution

Projet personnel de Patrick Ostertag.

## 📄 License

MIT License

---

**Version**: 4.0.0  
**Date**: 30 janvier 2026  
**Auteur**: Patrick Ostertag
