# 🎵 AIME - AI Music Enabler - Version 4.5.0

Application web moderne pour tracker et analyser l'historique d'écoute musicale depuis Last.fm, avec enrichissement automatique via Spotify, Discogs et IA.

## � Développement

**Développé avec Vibe Coding** en utilisant **VS Code** et **GitHub Copilot**

Cette application a été entièrement développée en exploitant les capacités d'assistance par IA de GitHub Copilot dans VS Code, démontrant la puissance du "Vibe Coding" - une approche de développement fluide et productive basée sur la collaboration homme-IA.

## 🏗️ Architecture

- **Frontend**: React 18 + TypeScript + Material-UI
- **Backend**: FastAPI + Python 3.10+
- **Base de données**: SQLite
- **APIs Intégrées**: 
  - **Last.fm**: Agrégation multi-sources (Roon ARC, PlexAmp, Quobuz, etc.)
  - **Roon**: Contrôle direct via pyroon, zones, lecture en cours, commandes playback
  - **Spotify**: URLs, images, métadonnées tracks
  - **Discogs**: Collection, vinyl records
  - **EurIA** (Infomaniak AI): Descriptions automatiques

## 📋 Fonctionnalités

### ✅ Implémentées

1. **Tracking Temps Réel - Multi-Source**
   - Surveillance automatique Last.fm toutes les 2 minutes (agrège données de multiples sources)
   - Support des sources : **Roon ARC**, **PlexAmp**, **Quobuz**, et autres services compatibles Last.fm
   - Détection nouveaux tracks écoutés en temps réel
   - Enrichissement métadonnées (images artistes/albums de Spotify, Last.fm, Discogs)
   - Génération automatique descriptions IA

2. **Gestion Collection Discogs**
   - Import collection depuis Discogs API
   - Synchronisation manuelle
   - Visualisation avec pochettes
   
   ![Albums Collection](docs/screenshots/Screen%20captures/Collection%20-%20Albums.png)

3. **Journal d'Écoute**
   - Liste chronologique inversée
   - Marquage favoris
   - Affichage images multiples (artiste, album Spotify, album Last.fm)
   - Info IA expandable
   
   ![Journal d'Écoute](docs/screenshots/Screen%20captures/Journal.png)
   
   ![Détail Album](docs/screenshots/Screen%20captures/Collection%20-%20Album%20-%20Detail.png)

4. **Timeline Horaire**
   - Visualisation par heure et par jour
   - Vue d'ensemble des écoutes
   
   ![Timeline](docs/screenshots/Screen%20captures/TimeLine.png)
   ![Détail Timeline](docs/screenshots/Screen%20captures/TimeLine%20-%20Detail.png)

5. **Gestion des Trackers**
   - Configuration Last.fm et Roon
   - Suivi automatique des écoutes
   - **✨ Auto-restart** : Les trackers redémarrent automatiquement après un redémarrage serveur
   
   ![Paramètres Trackers](docs/screenshots/Screen%20captures/Settings%20-%20Roon%20-%20Lastfm%20-%20Trackers.png)

6. **Scheduler et Exports Automatiques** ✨ **v4.5 - Auto-Start Garanti**
   - 🎋 Génération quotidienne de haikus pour 5 albums aléatoires (6h00)
   - 📝 Export automatique de la collection en Markdown (8h00)
   - 📊 Export automatique de la collection en JSON (10h00)
   - 📖 **Génération automatique de 10 magazines** chaque jour à 3h00
   - 🗑️ Gestion automatique des fichiers (garde les 5 derniers de chaque type)
   - ⚙️ Configuration modifiable des limites de fichiers
   - 🛡️ **Auto-Start Garanti** : Le scheduler redémarre automatiquement même si non marqué actif en DB
   - ✨ Formats scheduler identiques à l'API (haiku, json, markdown)
     - Tables des matières avec liens internes
     - Métadonnées complètes (images, résumés IA, labels)
     - Source unique pour tous les exports (cohérence garantie)
   
   ![Paramètres Scheduler](docs/screenshots/Screen%20captures/Settings%20-%20Scheduler.png)

7. **Contrôle Roon Direct** ✨ **v4.5 - Robustesse Améliorée**
   - **Widget Flottant** : Affichage en temps réel du morceau en cours
   - **Contrôles Intégrés** : Play, Pause, Next, Previous, Stop depuis les playlists
   - **Tracking Multi-Zone** : Détection automatique des zones Roon actives
   - **Démarrage Automatique** : Le tracker Roon redémarre après un reboot serveur
   - **🛡️ Robustesse** : 
     - Retry automatique (2 tentatives) sur tous les contrôles
     - 3 niveaux de fallback pour le démarrage d'albums
     - Timeout de 5-10s pour éviter les blocages
     - Feedback visuel avec Snackbar (plus d'alertes)
     - Génération de 50+ variantes artiste/album pour recherche
   - **Interface Moderne** : Glassmorphism design avec animations fluides
   
   ![Paramètres Roon](docs/screenshots/Screen%20captures/Settings%20-%20Trackers%20-%20Roon.png)

8. **📖 Magazine Éditorial** ✨ **NOUVEAU v4.5** (5 février 2026)
   - **Format Éditorial** : 5 pages scrollables avec contenu aléatoire
   - **Page 1 - Artiste Aléatoire** : Présentation complète + albums + haïku IA
   - **Page 2 - Album du Jour** : Album spotlight + description IA longue (2000+ caractères)
   - **Page 3 - Haïkus** : 3 albums aléatoires + haïkus générés EurIA
   - **Page 4 - Timeline** : Récapitulatif écoutes récentes + statistiques
   - **Page 5 - Playlist Thème** : Thème aléatoire + albums + description créative
   - **Auto-Refresh** : Nouvelle édition automatique toutes les 15 minutes
   - **Navigation Fluide** : Scroll souris, boutons, pagination
   - **🎨 Portraits d'Artistes** : Boutons "Portrait" sur chaque artiste avec génération IA en streaming
   - **📊 Scroll Indicator** : Affichage "Page n sur x" pendant le scrolling
   - **🎲 Éditions Multiples** : 10 magazines générés automatiquement chaque jour à 3h
   - **Design Moderne** : Glassmorphism avec couleurs variables et layouts aléatoires
   - **Responsive** : Desktop, Tablet, Mobile optimisés
   
   ![Magazine Page 1](docs/screenshots/Screen%20captures/Magazine%201.png)
   ![Magazine Page 2](docs/screenshots/Screen%20captures/Magazine%202.png)
   ![Magazine Page 3](docs/screenshots/Screen%20captures/Magazine%203.png)

9. **🎭 Portrait d'Artiste** ✨ **NOUVEAU v4.5**
   - **Génération IA Streaming** : Texte généré progressivement par EurIA
   - **Format Markdown** : Support complet avec titres, listes, emphases
   - **Accessible Partout** : Boutons "Portrait" sur tous les artistes du magazine
   - **Interface Modal** : Affichage élégant avec image d'artiste
   - **Temps Réel** : Voir le texte se construire phrase par phrase
   
   ![Portrait Artiste](docs/screenshots/Screen%20captures/Portrait%20-%20Artiste.png)

10. **API REST Complète**
   - Endpoints pour collection, historique, playlists, services, Roon, magazines
   - Documentation Swagger auto-générée
   - Validation Pydantic

### 🚧 En Développement

- Timeline horaire par jour
- Génération playlists (7 algorithmes)
- Analytics et statistiques avancées
- Export playlists (M3U, JSON, CSV)

### ⚠️ Limitations Connues

**Intégration Roon:**
- � **Robustesse améliorée v4.5** : Retry automatique, fallback multi-niveaux, timeout
- 🟡 Taux de succès: ~90-95% (vs 60-70% avant v4.5)
- 💡 **Si échec**: Le système réessaie automatiquement 2 fois avant d'afficher une erreur
- 📖 **Détails**: Voir [ROON-IMPROVEMENTS-SUMMARY-ROOT.md](ROON-IMPROVEMENTS-SUMMARY-ROOT.md)

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
- `GET /api/v1/services/tracker/status` - Statut tracker Last.fm
- `POST /api/v1/services/tracker/start` - Démarrer tracker Last.fm
- `POST /api/v1/services/tracker/stop` - Arrêter tracker Last.fm
- `GET /api/v1/services/roon-tracker/status` - Statut tracker Roon
- `POST /api/v1/services/roon-tracker/start` - Démarrer tracker Roon
- `POST /api/v1/services/roon-tracker/stop` - Arrêter tracker Roon
- `POST /api/v1/services/discogs/sync` - Synchroniser Discogs
- `POST /api/v1/services/ai/generate-info` - Générer info IA

### Roon Control ✨ **NOUVEAU**
- `GET /api/v1/roon/status` - Statut connexion Roon
- `GET /api/v1/roon/zones` - Liste des zones disponibles
- `GET /api/v1/roon/now-playing` - Morceau en cours de lecture
- `POST /api/v1/roon/play` - Démarrer lecture
- `POST /api/v1/roon/pause` - Mettre en pause
- `POST /api/v1/roon/next` - Morceau suivant
- `POST /api/v1/roon/previous` - Morceau précédent
- `POST /api/v1/roon/stop` - Arrêter lecture

### Magazine ✨ **NOUVEAU**
- `GET /api/v1/magazines/generate` - Générer nouveau magazine éditorial
- `POST /api/v1/magazines/regenerate` - Alias pour générer nouveau magazine

### Scheduler (Tâches Automatiques)
- `GET /api/v1/services/scheduler/config` - Configuration scheduler + max_files_per_type
- `PATCH /api/v1/services/scheduler/config` - Mettre à jour max_files_per_type
- `POST /api/v1/services/scheduler/start` - Démarrer scheduler
- `POST /api/v1/services/scheduler/stop` - Arrêter scheduler
- `POST /api/v1/services/scheduler/trigger/{task_name}` - Déclencher tâche manuel
  - `generate_haiku_scheduled` - Générer haikus
  - `export_collection_markdown` - Export Markdown
  - `export_collection_json` - Export JSON

Documentation complète: http://localhost:8000/docs

## 📅 Tâches Automatiques (Scheduler)

Le scheduler exécute automatiquement trois tâches quotidiennes:

### 🎋 Génération de Haikus (6h00)
```
POST /api/v1/services/scheduler/trigger/generate_haiku_scheduled
```
- Sélectionne 5 albums aléatoires
- Génère un haiku IA pour chaque
- Export en fichier Markdown horodaté
- Format: `generate-haiku-YYYYMMDD-HHMMSS.md`

### 📝 Export Markdown (8h00)
```
POST /api/v1/services/scheduler/trigger/export_collection_markdown
```
- Exporte la collection complète
- Groupée par artiste
- Inclut année et support
- Format: `export-markdown-YYYYMMDD-HHMMSS.md`

### 📊 Export JSON (10h00)
```
POST /api/v1/services/scheduler/trigger/export_collection_json
```
- Exporte la collection complète
- Format JSON avec métadonnées
- Inclut ID, titre, année, support, artistes, nombre de tracks
- Format: `export-json-YYYYMMDD-HHMMSS.json`

### ⚙️ Configuration Fichiers
```
PATCH /api/v1/services/scheduler/config?max_files_per_type=5
```
- Modifiable dans les Settings de l'application
- Valeur par défaut: 5 fichiers par type
- Les anciens fichiers sont automatiquement supprimés
- Les logs affichent les suppressions (🗑️)

**Stockage**: Tous les fichiers générés dans le répertoire `Scheduled Output/`

## 🧪 Tests

```bash
# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm run test
```

## � Documentation

- **[Guide de Démarrage Rapide](docs/QUICKSTART.md)** - Installation en 5 minutes
- **[Documentation Complète](docs/)** - Guide complet avec index
- **[Structure du Projet](docs/STRUCTURE.md)** - Organisation des fichiers
- **[Architecture Complète](docs/architecture/ARCHITECTURE-COMPLETE.md)** - Architecture système détaillée
- **[Schéma Base de Données](docs/architecture/DATABASE-SCHEMA.md)** - Modèle relationnel (Mermaid)
- **[Catalogue Prompts IA](docs/AI-PROMPTS.md)** - 🤖 Tous les prompts EurIA utilisés
- **[Dépannage](docs/TROUBLESHOOTING.md)** - Solutions aux problèmes courants
- **[Architecture](docs/ARCHITECTURE.md)** - Détails techniques
- **[API REST](docs/API.md)** - Documentation endpoints
- **[Nouvelles Fonctionnalités](docs/features/NOUVELLES-FONCTIONNALITES.md)** - Version 4.0.0

### Documentation des Fonctionnalités

- **[Tracker Last.fm](docs/features/LASTFM-IMPORT-TRACKER-DOC.md)** - Configuration et import
- **[Tracker Roon](docs/features/ROON-TRACKER-DOC.md)** - Intégration Roon
- **[Intégration Roon Complète](docs/features/roon/ROON-INTEGRATION-COMPLETE.md)** - Guide complet Roon
- **[Bugs Roon](docs/features/roon/ROON-BUGS-TRACKING.md)** - Suivi bugs et workarounds
- **[Journal/Timeline](docs/features/JOURNAL-TIMELINE-DOC.md)** - Vue chronologique
- **[Scheduler et Exports](docs/SCHEDULER.md)** - Tâches automatiques et configuration
- **[Magazine Éditorial](docs/MAGAZINE-README.md)** - Guide complet du Magazine (10 pages)
- **[Magazine - Guide d'Utilisation](docs/MAGAZINE-GUIDE.md)** - Guide de démarrage (15 pages)
- **[Magazine - Implémentation](docs/MAGAZINE-IMPLEMENTATION.md)** - Architecture technique (12 pages)
- **[Magazine - Améliorations](docs/MAGAZINE-IMPROVEMENTS.md)** - Roadmap et idées futures (20 pages)
- **[Magazine - Prompts EurIA](docs/MAGAZINE-EURIA-PROMPTS.md)** - Catalogue des prompts IA (18 pages)
- **[Magazine - Testing](docs/MAGAZINE-TESTING.md)** - Guide de test complet (16 pages)
- **[Magazine - Vue Visuelle](docs/MAGAZINE-VISUAL.md)** - Mockups et designs (14 pages)

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

## 📝 Roadmap

- [ ] Exports avancés (M3U, Spotify, Apple Music)
- [ ] Visualisations avancées (genres, découverte)
- [ ] Recommandations IA personnalisées
- [ ] Notifications (email, alertes nouveaux albums)
- [ ] Application mobile (React Native)
- [ ] Partage de playlists
- [ ] Dark mode amélioré
- [ ] Responsive mobile complet
- [ ] Planification custom des tâches scheduler

## 🤝 Contribution

Projet personnel de Patrick Ostertag.

## 📄 License

MIT License

---

**Version**: 4.4.0  
**Date**: 3 février 2026  
**Auteur**: Patrick Ostertag

### Changelog 4.4.0

**Magazine Éditorial (03/02/2026)**
- 📖 **Nouvelle Page Magazine** : Interface éditorial moderne avec 5 pages scrollables
- 🎨 **Format Rich Media** : Images, textes, haïkus générés par EurIA
- 🎯 **5 Sections** :
  1. Artiste Aléatoire avec ses albums et haïku IA
  2. Album Spotlight avec description longue (2000+ caractères)
  3. Haïkus : 3 albums aléatoires avec haïkus EurIA
  4. Timeline : Récapitulatif des écoutes récentes
  5. Playlist Thème : Thème créatif avec albums et description
- ⏱️ **Auto-Refresh** : Nouvelle édition toutes les 15 minutes + minuteur visible
- 🎨 **Design Moderne** : Glassmorphism avec couleurs et layouts variables
- 📱 **Responsive** : Desktop, Tablet, Mobile optimisés
- 📚 **Documentation Complète** : 7 fichiers de documentation (125+ pages)
- 🔌 **Endpoints API** : `/api/v1/magazines/generate` et `/api/v1/magazines/regenerate`

### Changelog 4.3.1

**Intégration Roon Complète + Auto-Restart (01/02/2026)**
- 🎛️ **Contrôle Roon Direct**: Widget flottant avec affichage temps réel du morceau en cours
- ▶️ **Commandes Playback**: Play, Pause, Next, Previous, Stop intégrés dans les playlists
- 🔄 **Auto-Restart des Services**: Trackers (Last.fm, Roon) et Scheduler redémarrent automatiquement
- 🗄️ **Persistance États**: Nouvelle table `service_states` pour la restauration automatique
- 🎯 **Gestion Zones Roon**: Détection automatique et attente du chargement des zones
- 🐛 **Fix Zones Vides**: Correction du problème de zones non disponibles au démarrage
- 📱 **Interface Moderne**: Glassmorphism design avec animations fluides
- 📚 **Documentation**: [Auto-Restart Guide](docs/guides/AUTO-RESTART-TEST-GUIDE.md), [Roon Zones Fix](docs/features/roon/ROON-ZONES-FIX.md)

### Changelog 4.3.0

**Synchronisation Complète des Formats (31/01/2026)**
- ✨ Les fichiers générés par le scheduler sont maintenant strictement identiques aux fichiers de l'API
- 🎋 Format Haiku enrichi: table des matières, métadonnées complètes, images (4x enrichi)
- 📝 Format Markdown: utilise MarkdownExportService, TOC, résumés IA (12x complet)
- 📊 Format JSON: images, métadonnées IA, timestamps, Discogs URL (18x riche)
- 🔧 Correction alignement interface Settings (tâches planifiées cadrées à gauche)
- 📚 Documentation complète: 6 nouveaux fichiers de documentation
- ✅ Tests et scripts de vérification automatiques
