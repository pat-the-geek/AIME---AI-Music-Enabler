# Architecture du Projet Music Tracker

## Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           React App (Port 5173)                         │ │
│  │  - React Router (navigation)                            │ │
│  │  - TanStack Query (cache API)                           │ │
│  │  - Material-UI (composants)                             │ │
│  │  - Axios (HTTP client)                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP REST API (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Port 8000)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                        │ │
│  │  - API Routes (/api/v1/...)                            │ │
│  │  - Business Logic                                       │ │
│  │  - CORS middleware                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌─────────────────┬─────────┴────────┬──────────────────┐ │
│  │  Services       │   Database       │   Background     │ │
│  │  - Spotify      │   SQLAlchemy ORM │   TrackerService │ │
│  │  - Last.fm      │   SQLite DB      │   APScheduler    │ │
│  │  - Discogs      │                  │   (2 min poll)   │ │
│  │  - EurIA AI     │                  │                  │ │
│  └─────────────────┴──────────────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   SQLite File     │
                    │   data/musique.db │
                    └──────────────────┘
                              │
                              ▼
                ┌────────────────────────────┐
                │    External APIs           │
                │  - Last.fm (tracking)      │
                │  - Spotify (images)        │
                │  - Discogs (collection)    │
                │  - EurIA/Infomaniak (IA)   │
                └────────────────────────────┘
```

## Structure des Fichiers

### Backend (FastAPI + Python)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── database.py             # Configuration SQLAlchemy
│   │
│   ├── core/                   # Configuration centrale
│   │   ├── __init__.py
│   │   └── config.py           # Settings (Pydantic)
│   │
│   ├── models/                 # Modèles SQLAlchemy (ORM)
│   │   ├── __init__.py
│   │   ├── artist.py           # Table artists
│   │   ├── album.py            # Table albums
│   │   ├── album_artist.py     # Table de liaison M2M
│   │   ├── track.py            # Table tracks
│   │   ├── listening_history.py # Table listening_history
│   │   ├── image.py            # Table images
│   │   ├── metadata.py         # Table metadata
│   │   └── playlist.py         # Tables playlists + playlist_tracks
│   │
│   ├── schemas/                # Schémas Pydantic (validation)
│   │   ├── __init__.py
│   │   ├── artist.py           # DTO artistes
│   │   ├── album.py            # DTO albums
│   │   ├── track.py            # DTO tracks
│   │   ├── history.py          # DTO historique
│   │   └── playlist.py         # DTO playlists
│   │
│   ├── api/v1/                 # Routes API REST
│   │   ├── __init__.py
│   │   ├── collection.py       # /collection/albums, /artists
│   │   ├── history.py          # /history/tracks, /timeline
│   │   ├── playlists.py        # /playlists
│   │   ├── services.py         # /services (tracker, sync)
│   │   └── search.py           # /search
│   │
│   ├── services/               # Logique métier
│   │   ├── __init__.py
│   │   ├── spotify_service.py  # Client Spotify API
│   │   ├── lastfm_service.py   # Client Last.fm API
│   │   ├── discogs_service.py  # Client Discogs API
│   │   ├── ai_service.py       # Client EurIA/Infomaniak
│   │   ├── tracker_service.py  # Tracker background (APScheduler)
│   │   └── playlist_generator.py # Générateur playlists
│   │
│   └── utils/                  # Utilitaires
│       └── __init__.py
│
├── requirements.txt            # Dépendances Python
└── Dockerfile                  # Image Docker backend
```

### Frontend (React + TypeScript)

```
frontend/
├── src/
│   ├── main.tsx                # Point d'entrée React
│   ├── App.tsx                 # Composant racine + routing
│   │
│   ├── pages/                  # Pages principales
│   │   ├── Collection.tsx      # Page albums Discogs
│   │   ├── Journal.tsx         # Page historique d'écoute
│   │   ├── Timeline.tsx        # Page timeline horaire
│   │   ├── Playlists.tsx       # Page playlists
│   │   ├── Analytics.tsx       # Page statistiques
│   │   └── Settings.tsx        # Page configuration
│   │
│   ├── components/             # Composants réutilisables
│   │   └── layout/
│   │       └── Navbar.tsx      # Barre de navigation
│   │
│   ├── api/
│   │   └── client.ts           # Client Axios configuré
│   │
│   ├── types/
│   │   └── models.ts           # Types TypeScript (interfaces)
│   │
│   └── styles/
│       └── theme.ts            # Thème Material-UI
│
├── public/
│   └── vite.svg                # Logo
│
├── index.html                  # Point d'entrée HTML
├── package.json                # Dépendances Node.js
├── tsconfig.json               # Config TypeScript
├── vite.config.ts              # Config Vite
├── nginx.conf                  # Config Nginx (production)
└── Dockerfile                  # Image Docker frontend
```

### Configuration & Scripts

```
├── config/
│   ├── app.json                # Configuration application
│   └── secrets.json            # API keys (GITIGNORE)
│
├── data/
│   ├── musique.db              # Base SQLite (créée auto)
│   └── backups/                # Backups DB
│       └── .gitkeep
│
├── scripts/
│   ├── setup.sh                # Installation complète
│   └── start-dev.sh            # Démarrage dev
│
├── docs/
│   ├── API.md                  # Documentation API
│   └── QUICKSTART.md           # Guide démarrage
│
├── docker-compose.yml          # Orchestration Docker
├── .gitignore                  # Fichiers ignorés Git
├── README.md                   # Documentation principale
└── PROJECT-SUMMARY.md          # Résumé du projet
```

## Flux de Données

### 1. Tracking Last.fm

```
TrackerService (toutes les 2 min)
    │
    ├─> LastFMService.get_now_playing()
    │       │
    │       └─> Last.fm API
    │
    ├─> SpotifyService.search_artist_image()
    │       │
    │       └─> Spotify API
    │
    ├─> SpotifyService.search_album_image()
    │       │
    │       └─> Spotify API
    │
    ├─> AIService.generate_album_info()
    │       │
    │       └─> EurIA/Infomaniak API
    │
    └─> Save to SQLite
            ├─> artists
            ├─> albums
            ├─> tracks
            ├─> listening_history
            ├─> images
            └─> metadata
```

### 2. Requête Frontend → Backend

```
React Component
    │
    ├─> TanStack Query (cache)
    │       │
    │       ├─> Cache HIT → Retour immédiat
    │       │
    │       └─> Cache MISS
    │               │
    │               └─> Axios (apiClient)
    │                       │
    │                       └─> FastAPI Route
    │                               │
    │                               ├─> Validation Pydantic
    │                               │
    │                               ├─> Business Logic
    │                               │
    │                               ├─> SQLAlchemy Query
    │                               │       │
    │                               │       └─> SQLite DB
    │                               │
    │                               └─> Response (JSON)
    │
    └─> React Render (UI update)
```

### 3. Synchronisation Discogs

```
User clicks "Sync Discogs"
    │
    └─> POST /api/v1/services/discogs/sync
            │
            └─> DiscogsService.get_collection()
                    │
                    └─> Discogs API
                            │
                            └─> Pour chaque album:
                                    ├─> Créer/récupérer artistes
                                    ├─> Créer album
                                    ├─> Ajouter images
                                    └─> Ajouter métadonnées
```

## Base de Données (SQLite)

### Schéma Relationnel

```
artists (1) ←──────┐
    ↓              │
    │              │ (M2M)
    │              │
    └─> album_artist ←─┐
                       │
albums (1) ←───────────┘
    ↓
    ├─> tracks (N)
    │       ↓
    │       └─> listening_history (N)
    │
    ├─> images (N)
    │
    └─> metadata (1)

playlists (1)
    ↓
    └─> playlist_tracks (N) ──> tracks
```

### Tables Principales

1. **artists** - Artistes musicaux
   - id, name, spotify_id, lastfm_url

2. **albums** - Albums musicaux
   - id, title, year, support, discogs_id, spotify_url

3. **album_artist** - Liaison Many-to-Many
   - album_id, artist_id

4. **tracks** - Pistes musicales
   - id, album_id, title, track_number, duration_seconds

5. **listening_history** - Historique d'écoute
   - id, track_id, timestamp, date, source, loved

6. **images** - URLs d'images
   - id, url, image_type, source, artist_id, album_id

7. **metadata** - Métadonnées enrichies
   - id, album_id, ai_info, resume, labels, film_*

8. **playlists** - Playlists générées
   - id, name, algorithm, ai_prompt, track_count

9. **playlist_tracks** - Tracks dans playlists
   - playlist_id, track_id, position

## Services Externes

### Last.fm
- **Usage**: Tracking d'écoute en temps réel
- **Fréquence**: Polling toutes les 2 minutes
- **Endpoint**: `user.getNowPlaying()`

### Spotify
- **Usage**: Récupération images artistes/albums
- **Auth**: Client Credentials Flow
- **Cache**: Images stockées en DB

### Discogs
- **Usage**: Import collection musicale
- **Fréquence**: Manuelle (button "Sync")
- **Endpoint**: `user.collection()`

### EurIA (Infomaniak AI)
- **Usage**: Génération descriptions albums
- **Modèle**: mistral-large-latest
- **Cache**: 80% hit rate (descriptions en DB)

## Déploiement

### Développement
```bash
./scripts/start-dev.sh
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

### Production (Docker)
```bash
docker-compose up -d
```
- Backend: Container `music-tracker-backend`
- Frontend: Container `music-tracker-frontend` (Nginx)
- Accès: http://localhost:80

## Sécurité

- ✅ API keys dans `config/secrets.json` (GITIGNORE)
- ✅ CORS configuré pour origines autorisées
- ✅ Validation Pydantic sur toutes les entrées
- ✅ SQLAlchemy ORM (protection SQL injection)
- ⚠️ Pas d'authentification (à implémenter pour prod)

## Performance

### Backend
- Index DB sur artist_name, album_title, timestamp
- Pagination systématique (30-50 items)
- Connection pool SQLite (5 connexions)
- Cache HTTP (ETags) à implémenter

### Frontend
- TanStack Query cache (5 min stale time)
- Lazy loading images
- Pagination côté serveur
- Debounce recherche (300ms) à implémenter

## Monitoring

- ✅ Logs FastAPI (console)
- ✅ Statut tracker accessible via `/services/tracker/status`
- ⚠️ Métriques à implémenter (Prometheus)
- ⚠️ Health checks à améliorer

---

**Auteur**: Patrick Ostertag  
**Date**: 30 janvier 2026  
**Version**: 4.0.0
