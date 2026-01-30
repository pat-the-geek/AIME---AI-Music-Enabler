# 🎵 MUSIC TRACKER - SPÉCIFICATION COMPLÈTE POUR REBUILD FROM SCRATCH

**Version: 4.0.0 React Rebuild**  
**Date: 30 janvier 2026**  
**Auteur: Patrick Ostertag**  
**Objectif: Reconstruction complète avec React + SQLite**

---

## 📋 RÉSUMÉ EXÉCUTIF

Ce document spécifie la reconstruction complète du projet "Musique Collection & Listening Tracker" avec:
- **Frontend**: React + TypeScript (au lieu de Streamlit)
- **Backend**: FastAPI + Python 3.10+
- **Base de données**: SQLite (au lieu de JSON)
- **Configuration**: JSON uniquement pour paramètres

**Architecture cible**: SPA (Single Page Application) moderne avec API REST.

---

## 🎯 OBJECTIFS DU PROJET

### Vision Générale
Créer une application web moderne pour tracker et analyser l'historique d'écoute musicale depuis Last.fm, avec enrichissement automatique via:
- Spotify API (images artistes/albums)
- Discogs API (métadonnées collection)
- EurIA API (descriptions générées par IA)

### Fonctionnalités Principales

1. **Tracking Temps Réel**
   - Surveillance automatique Last.fm toutes les 2 minutes
   - Détection nouveaux tracks écoutés
   - Enrichissement métadonnées (images, infos album)
   - Génération automatique descriptions IA

2. **Gestion Collection Discogs**
   - Import collection depuis Discogs API
   - Synchronisation automatique ou manuelle
   - Édition métadonnées inline
   - Gestion bandes originales (cross-référence films)

3. **Visualisation Avancée**
   - Journal chronologique d'écoute (mode liste)
   - Timeline horaire (visualisation par heure de la journée)
   - Statistiques temps réel (artistes/albums uniques, peak hours)
   - Filtres avancés (date, artiste, album, favoris)

4. **Analyse Intelligente**
   - Génération playlists basées sur patterns d'écoute (7 algorithmes)
   - Détection sessions d'écoute continues
   - Analyse corrélations artistes
   - Génération présentations IA (haïkus)

5. **Intégration IA**
   - Descriptions albums automatiques (EurIA API)
   - Fallback intelligent Discogs → IA (80% hits cache)
   - Génération playlists thématiques par prompt
   - Journal technique quotidien avec rétention 24h

---

## 🏗️ ARCHITECTURE SYSTÈME

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           React App (TypeScript + Vite)                 │ │
│  │  - React Router (navigation)                            │ │
│  │  - TanStack Query (cache API)                           │ │
│  │  - Material-UI / Tailwind CSS                           │ │
│  │  - Axios (HTTP client)                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP REST API (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Server)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                        │ │
│  │  - API Routes (/api/v1/...)                            │ │
│  │  - Business Logic                                       │ │
│  │  - Authentication (JWT optional)                        │ │
│  │  - CORS middleware                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌─────────────────┬─────────┴────────┬──────────────────┐ │
│  │  Services       │   Database       │   Background     │ │
│  │  - Spotify      │   SQLAlchemy ORM │   Tasks          │ │
│  │  - Last.fm      │   SQLite DB      │   - Tracker      │ │
│  │  - Discogs      │   Migrations     │   - Scheduler    │ │
│  │  - EurIA AI     │   Backup         │   - Queue        │ │
│  └─────────────────┴──────────────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   SQLite File     │
                    │   musique.db      │
                    └──────────────────┘
```

### Stack Technique

#### Frontend
- **Framework**: React 18.2+ avec TypeScript 5.0+
- **Bundler**: Vite 5.0+ (dev server rapide, HMR)
- **Routing**: React Router v6 (navigation SPA)
- **State Management**: 
  - TanStack Query v5 (cache API, synchronisation serveur)
  - Zustand (état global léger si nécessaire)
- **UI Library**: Material-UI v5 OU Tailwind CSS v3 (au choix)
- **Charts**: Chart.js v4 ou Recharts (visualisations)
- **HTTP Client**: Axios avec interceptors
- **Form**: React Hook Form avec Zod validation
- **Date**: date-fns (manipulation dates)

#### Backend
- **Framework**: FastAPI 0.109+
- **ORM**: SQLAlchemy 2.0+ avec Alembic (migrations)
- **Database**: SQLite 3.35+ (production: PostgreSQL option)
- **Auth**: python-jose (JWT), passlib (hashing)
- **Validation**: Pydantic v2
- **Background**: APScheduler (tâches périodiques)
- **HTTP**: httpx (client async)
- **Testing**: pytest + pytest-asyncio

#### APIs Externes
- **Last.fm API**: pylast library
- **Spotify Web API**: spotipy ou custom client
- **Discogs API**: python3-discogs-client
- **EurIA API**: custom client (Infomaniak AI)

---

## 📊 SCHÉMA BASE DE DONNÉES (SQLite)

### Modèle Relationnel

```sql
-- Table: artists (artistes musicaux)
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    spotify_id VARCHAR(100),
    lastfm_url VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_artist_name ON artists(name);

-- Table: albums (albums musicaux)
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(500) NOT NULL,
    year INTEGER,
    support VARCHAR(50),  -- Vinyle, CD, Digital
    discogs_id VARCHAR(100) UNIQUE,
    spotify_url VARCHAR(500),
    discogs_url VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_album_title ON albums(title);
CREATE INDEX idx_album_title_year ON albums(title, year);

-- Table: album_artist (liaison Many-to-Many)
CREATE TABLE album_artist (
    album_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (album_id, artist_id),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

-- Table: tracks (pistes musicales)
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    track_number INTEGER,
    duration_seconds INTEGER,
    spotify_id VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
CREATE INDEX idx_track_album_title ON tracks(album_id, title);

-- Table: listening_history (historique d'écoute)
CREATE TABLE listening_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,  -- Unix timestamp
    date VARCHAR(20) NOT NULL,   -- Format: YYYY-MM-DD HH:MM
    source VARCHAR(20) NOT NULL, -- 'roon' ou 'lastfm'
    loved BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);
CREATE INDEX idx_history_timestamp ON listening_history(timestamp);
CREATE INDEX idx_history_source ON listening_history(source);
CREATE INDEX idx_history_date ON listening_history(date);

-- Table: images (URLs d'images)
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url VARCHAR(1000) NOT NULL,
    image_type VARCHAR(50) NOT NULL,  -- 'artist', 'album'
    source VARCHAR(50) NOT NULL,       -- 'spotify', 'lastfm', 'discogs'
    artist_id INTEGER,
    album_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    CHECK ((artist_id IS NOT NULL AND album_id IS NULL) OR 
           (artist_id IS NULL AND album_id IS NOT NULL))
);
CREATE INDEX idx_image_artist ON images(artist_id);
CREATE INDEX idx_image_album ON images(album_id);

-- Table: metadata (métadonnées supplémentaires)
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL UNIQUE,
    ai_info TEXT,              -- Description générée par IA (500 chars max)
    resume TEXT,               -- Résumé long (Discogs/IA)
    labels TEXT,               -- JSON array: ["Label1", "Label2"]
    film_title VARCHAR(500),   -- Si BOF: titre du film
    film_year INTEGER,         -- Si BOF: année du film
    film_director VARCHAR(255), -- Si BOF: réalisateur
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
CREATE INDEX idx_metadata_album ON metadata(album_id);
CREATE INDEX idx_metadata_film ON metadata(film_title);

-- Table: playlists (playlists générées)
CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    algorithm VARCHAR(50) NOT NULL,  -- 'top_sessions', 'ai_generated', etc.
    ai_prompt TEXT,                  -- Si algorithm='ai_generated'
    track_count INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: playlist_tracks (tracks dans playlists)
CREATE TABLE playlist_tracks (
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, track_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);
```

### Relations Clés

- **Artist ↔ Album**: Many-to-Many (albums multi-artistes)
- **Album → Track**: One-to-Many (pistes d'un album)
- **Track → ListeningHistory**: One-to-Many (historique d'écoute)
- **Album → Metadata**: One-to-One (métadonnées enrichies)
- **Album/Artist → Image**: One-to-Many (images multiples par source)

---

## 🔧 CONFIGURATION (JSON)

### Fichier: `config/app.json`
```json
{
  "app": {
    "name": "Music Tracker",
    "version": "4.0.0",
    "environment": "development"
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "cors_origins": ["http://localhost:5173"]
  },
  "database": {
    "url": "sqlite:///data/musique.db",
    "echo": false,
    "pool_size": 5
  },
  "tracker": {
    "enabled": true,
    "interval_seconds": 120,
    "listen_start_hour": 6,
    "listen_end_hour": 23
  },
  "scheduler": {
    "enabled": true,
    "tasks": [
      {
        "name": "generate_haiku",
        "enabled": true,
        "frequency": 1,
        "unit": "week"
      },
      {
        "name": "analyze_patterns",
        "enabled": true,
        "frequency": 1,
        "unit": "week"
      },
      {
        "name": "sync_discogs",
        "enabled": true,
        "frequency": 1,
        "unit": "month"
      }
    ]
  }
}
```

### Fichier: `config/secrets.json` (GITIGNORE)
```json
{
  "lastfm": {
    "api_key": "YOUR_LASTFM_API_KEY",
    "api_secret": "YOUR_LASTFM_API_SECRET",
    "username": "YOUR_LASTFM_USERNAME"
  },
  "spotify": {
    "client_id": "YOUR_SPOTIFY_CLIENT_ID",
    "client_secret": "YOUR_SPOTIFY_CLIENT_SECRET"
  },
  "discogs": {
    "api_key": "YOUR_DISCOGS_API_KEY",
    "username": "YOUR_DISCOGS_USERNAME"
  },
  "euria": {
    "url": "https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions",
    "bearer": "YOUR_EURIA_BEARER_TOKEN",
    "max_attempts": 5
  }
}
```

---

## 🌐 API REST (FastAPI)

### Endpoints Principaux

#### **Collection**
```
GET    /api/v1/collection/albums          # Liste albums avec filtres
GET    /api/v1/collection/albums/{id}     # Détail album
POST   /api/v1/collection/albums          # Créer album
PUT    /api/v1/collection/albums/{id}     # Modifier album
DELETE /api/v1/collection/albums/{id}     # Supprimer album
GET    /api/v1/collection/artists         # Liste artistes
GET    /api/v1/collection/stats           # Statistiques collection
```

#### **Historique d'Écoute**
```
GET    /api/v1/history/tracks              # Journal chronologique (pagination)
GET    /api/v1/history/timeline            # Timeline horaire (par jour)
GET    /api/v1/history/stats               # Statistiques (artistes uniques, etc.)
GET    /api/v1/history/sessions            # Détection sessions continues
POST   /api/v1/history/tracks/{id}/love    # Marquer favori
```

#### **Playlists**
```
GET    /api/v1/playlists                   # Liste playlists
POST   /api/v1/playlists/generate          # Générer playlist (algorithme + params)
GET    /api/v1/playlists/{id}              # Détail playlist
DELETE /api/v1/playlists/{id}              # Supprimer playlist
GET    /api/v1/playlists/{id}/export       # Export (M3U, JSON, CSV)
```

#### **Services Externes**
```
POST   /api/v1/services/discogs/sync       # Synchroniser collection Discogs
POST   /api/v1/services/ai/generate-info   # Générer description IA pour album
GET    /api/v1/services/tracker/status     # Statut tracker Last.fm
POST   /api/v1/services/tracker/start      # Démarrer tracker
POST   /api/v1/services/tracker/stop       # Arrêter tracker
```

#### **Recherche**
```
GET    /api/v1/search?q={query}&type={type}  # Recherche globale
```

### Modèles Pydantic (Exemples)

```python
# schemas/album.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ArtistBase(BaseModel):
    name: str = Field(..., max_length=255)
    spotify_id: Optional[str] = None

class AlbumBase(BaseModel):
    title: str = Field(..., max_length=500)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    support: Optional[str] = Field(None, max_length=50)
    discogs_id: Optional[str] = None
    spotify_url: Optional[str] = None
    discogs_url: Optional[str] = None

class AlbumCreate(AlbumBase):
    artist_ids: List[int] = Field(..., min_items=1)
    
class AlbumResponse(AlbumBase):
    id: int
    artists: List[ArtistBase]
    images: List[str]
    ai_info: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ListeningHistoryResponse(BaseModel):
    id: int
    timestamp: int
    date: str
    artist: str
    title: str
    album: str
    loved: bool
    source: str  # 'roon' | 'lastfm'
    artist_image: Optional[str]
    album_image: Optional[str]
```

---

## 🎨 INTERFACE REACT

### Structure des Composants

```
src/
├── App.tsx                      # Composant racine
├── main.tsx                     # Point d'entrée
├── routes/                      # Configuration React Router
│   └── index.tsx
├── pages/                       # Pages principales
│   ├── Collection/              # Page collection Discogs
│   │   ├── index.tsx
│   │   ├── AlbumCard.tsx
│   │   ├── AlbumDetail.tsx
│   │   ├── FilterBar.tsx
│   │   └── EditModal.tsx
│   ├── Journal/                 # Journal d'écoute
│   │   ├── index.tsx
│   │   ├── TrackList.tsx
│   │   ├── TrackCard.tsx
│   │   └── Filters.tsx
│   ├── Timeline/                # Timeline horaire
│   │   ├── index.tsx
│   │   ├── HourlyView.tsx
│   │   ├── DaySelector.tsx
│   │   └── Stats.tsx
│   ├── Playlists/               # Gestion playlists
│   │   ├── index.tsx
│   │   ├── GenerateModal.tsx
│   │   ├── PlaylistCard.tsx
│   │   └── ExportMenu.tsx
│   ├── Analytics/               # Analyses et stats
│   │   ├── index.tsx
│   │   ├── SessionsChart.tsx
│   │   ├── CorrelationsGraph.tsx
│   │   └── StatsCards.tsx
│   └── Settings/                # Configuration
│       ├── index.tsx
│       ├── TrackerConfig.tsx
│       ├── SchedulerConfig.tsx
│       └── APIKeys.tsx
├── components/                  # Composants réutilisables
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Modal.tsx
│   │   ├── Loader.tsx
│   │   └── ErrorBoundary.tsx
│   └── music/
│       ├── AlbumCover.tsx
│       ├── ArtistAvatar.tsx
│       ├── TrackRow.tsx
│       └── AudioPlayer.tsx
├── hooks/                       # Custom hooks React
│   ├── useAlbums.ts
│   ├── useListeningHistory.ts
│   ├── usePlaylists.ts
│   ├── useTracker.ts
│   └── useDebounce.ts
├── api/                         # Clients API
│   ├── client.ts                # Axios instance configurée
│   ├── albums.ts
│   ├── history.ts
│   ├── playlists.ts
│   └── services.ts
├── store/                       # État global (Zustand optionnel)
│   ├── authStore.ts
│   └── settingsStore.ts
├── utils/                       # Utilitaires
│   ├── date.ts
│   ├── format.ts
│   └── validators.ts
├── types/                       # Types TypeScript
│   ├── api.ts
│   ├── models.ts
│   └── index.ts
└── styles/                      # Styles globaux
    ├── globals.css
    └── theme.ts
```

### Pages Principales

#### 1. **Collection (Page Albums Discogs)**
**Route**: `/collection`

**Fonctionnalités**:
- Grid d'albums avec pochettes (Discogs + Spotify)
- Recherche temps réel (titre, artiste)
- Filtres: année, support (Vinyle/CD), BOF
- Tri: titre, artiste, année, date d'ajout
- Pagination (30 albums par page)
- Vue détail modal avec:
  - Métadonnées complètes
  - Images multi-sources
  - Résumé/Info IA (expandable)
  - Liens Spotify/Discogs
  - Édition inline (titre, année, support)
  - Badge "🎬 SOUNDTRACK" si BOF

**État TanStack Query**:
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['albums', { page, search, filters }],
  queryFn: () => api.albums.list({ page, search, ...filters }),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

#### 2. **Journal d'Écoute (Listening History)**
**Route**: `/journal`

**Fonctionnalités**:
- Liste chronologique inversée (plus récent en haut)
- Affichage compact et détaillé (toggle)
- Triple images: artiste, album Spotify, album Last.fm
- Filtres: source (Last.fm), date range, artiste, album, favoris
- Recherche temps réel
- Info IA expandable par track
- Pagination infinie (scroll)
- Marquage favoris (❤️)
- Stats temps réel (sidebar):
  - Total tracks today
  - Artistes uniques
  - Albums uniques
  - Peak hour

**Composant TrackCard**:
```typescript
interface TrackCardProps {
  track: ListeningHistory;
  compact?: boolean;
}

const TrackCard: React.FC<TrackCardProps> = ({ track, compact }) => {
  return (
    <Card className="track-card">
      <div className="images">
        <img src={track.artist_image} alt="Artist" />
        <img src={track.album_image} alt="Album" />
      </div>
      <div className="metadata">
        <Typography variant="h6">{track.title}</Typography>
        <Typography variant="body2">{track.artist}</Typography>
        <Typography variant="caption">{track.album}</Typography>
        <Typography variant="caption">{track.date}</Typography>
        {!compact && track.ai_info && (
          <Accordion>
            <AccordionSummary>🤖 Info IA</AccordionSummary>
            <AccordionDetails>{track.ai_info}</AccordionDetails>
          </Accordion>
        )}
      </div>
      <IconButton onClick={() => toggleLove(track.id)}>
        {track.loved ? <FavoriteIcon /> : <FavoriteBorderIcon />}
      </IconButton>
    </Card>
  );
};
```

#### 3. **Timeline Horaire**
**Route**: `/timeline`

**Fonctionnalités**:
- Visualisation horaire des écoutes (6h-23h configurable)
- Scroll horizontal par heure
- Alternance couleurs par heure (gris/blanc)
- Mode compact (pochettes seules) vs détaillé (+ métadonnées)
- Sélecteur de date avec navigation (prev/next)
- Stats journalières:
  - Total tracks
  - Artistes uniques
  - Albums uniques
  - Peak hour (heure la plus active)
- Limite: 20 tracks max par heure (performance)

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  < Prev Day  |  Mardi 30 Janvier 2026  |  Next > │
├─────────────────────────────────────────────────┤
│  Compact [ ] Détaillé [x]                       │
├─────────────────────────────────────────────────┤
│  Stats: 45 tracks | 12 artistes | 8 albums     │
│  Peak Hour: 18h (8 tracks)                      │
├─────────────────────────────────────────────────┤
│ Scroll Horizontal ➜                             │
│ ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐ │
│ │06h│07h│08h│09h│10h│11h│12h│13h│14h│15h│16h│ │
│ ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤ │
│ │🎵 │   │🎵 │🎵 │   │🎵 │🎵 │   │🎵 │🎵 │🎵 │ │
│ │🎵 │   │🎵 │🎵 │   │🎵 │🎵 │   │🎵 │   │   │ │
│ └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘ │
└─────────────────────────────────────────────────┘
```

#### 4. **Playlists**
**Route**: `/playlists`

**Fonctionnalités**:
- Liste playlists générées
- Génération via modal:
  - Sélection algorithme (7 options + IA)
  - Nombre de tracks (5-50)
  - Prompt IA (si algorithm='ai_generated')
  - Formats export (M3U, JSON, CSV, TXT)
- Détail playlist:
  - Liste tracks ordonnée
  - Statistiques (durée totale, artistes, albums)
  - Player preview (optionnel)
  - Export multi-formats
- Suppression avec confirmation

**Algorithmes Disponibles**:
1. `top_sessions`: Pistes des sessions les plus longues
2. `artist_correlations`: Artistes souvent écoutés ensemble
3. `artist_flow`: Transitions naturelles entre artistes
4. `time_based`: Basé sur peak hours ou weekend
5. `complete_albums`: Albums écoutés en entier
6. `rediscovery`: Pistes aimées mais pas écoutées récemment
7. `ai_generated`: Génération par IA avec prompt personnalisé

#### 5. **Analytics (Statistiques)**
**Route**: `/analytics`

**Fonctionnalités**:
- Détection sessions continues (gap < 30 min)
- Corrélations artistes (heatmap)
- Top 10 artistes/albums (période sélectionnable)
- Distribution temporelle:
  - Par heure de la journée (bar chart)
  - Par jour de la semaine (radar chart)
  - Tendances mensuelles (line chart)
- Albums complets écoutés (≥5 tracks)
- Statistiques globales:
  - Durée totale écoute
  - Diversité (ratio artistes uniques)
  - Score d'engagement

**Librairie Charts**: Chart.js ou Recharts

#### 6. **Settings (Configuration)**
**Route**: `/settings`

**Sections**:
- **Tracker Last.fm**:
  - Start/Stop tracker
  - Interval polling (60-300 seconds)
  - Listening hours (start/end)
  - Statut temps réel (running/stopped)
  
- **Scheduler**:
  - Enable/Disable tasks (haiku, analyse, sync)
  - Fréquence (1 jour, 1 semaine, 1 mois)
  - Dernière exécution
  - Prochaine exécution estimée
  
- **API Keys** (masquées):
  - Last.fm, Spotify, Discogs, EurIA
  - Test connexion (bouton)
  
- **Database**:
  - Backup manuel (export JSON)
  - Vacuum SQLite
  - Statistiques (taille DB, nombre d'enregistrements)

---

## 🔄 SERVICES BACKEND (Python)

### Structure des Fichiers

```
backend/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── config.py                # Configuration (Pydantic Settings)
│   ├── database.py              # Connexion SQLAlchemy
│   ├── dependencies.py          # Dépendances FastAPI (DB session)
│   ├── models/                  # Modèles SQLAlchemy
│   │   ├── __init__.py
│   │   ├── artist.py
│   │   ├── album.py
│   │   ├── track.py
│   │   ├── listening_history.py
│   │   ├── image.py
│   │   ├── metadata.py
│   │   └── playlist.py
│   ├── schemas/                 # Schémas Pydantic (validation)
│   │   ├── __init__.py
│   │   ├── album.py
│   │   ├── artist.py
│   │   ├── track.py
│   │   ├── history.py
│   │   └── playlist.py
│   ├── api/                     # Routes API
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── collection.py    # /collection/albums, /artists
│   │   │   ├── history.py       # /history/tracks, /timeline
│   │   │   ├── playlists.py     # /playlists
│   │   │   ├── services.py      # /services (tracker, discogs, ai)
│   │   │   └── search.py        # /search
│   ├── services/                # Logique métier
│   │   ├── __init__.py
│   │   ├── spotify_service.py   # Spotify API client
│   │   ├── lastfm_service.py    # Last.fm API client
│   │   ├── discogs_service.py   # Discogs API client
│   │   ├── ai_service.py        # EurIA API client
│   │   ├── tracker_service.py   # Tracker Last.fm (background)
│   │   ├── scheduler_service.py # Planificateur tâches
│   │   ├── playlist_generator.py # Génération playlists
│   │   └── analytics_service.py # Analyses patterns
│   ├── utils/                   # Utilitaires
│   │   ├── __init__.py
│   │   ├── metadata_cleaner.py  # Nettoyage noms artistes/albums
│   │   ├── date_utils.py        # Manipulation dates
│   │   └── cache.py             # Cache mémoire
│   └── core/                    # Configuration centrale
│       ├── __init__.py
│       ├── config.py            # Settings Pydantic
│       ├── security.py          # JWT, hashing (optionnel)
│       └── logging.py           # Configuration logging
├── alembic/                     # Migrations DB
│   ├── versions/
│   └── env.py
├── tests/                       # Tests pytest
│   ├── __init__.py
│   ├── conftest.py              # Fixtures
│   ├── test_api/
│   │   ├── test_collection.py
│   │   ├── test_history.py
│   │   └── test_playlists.py
│   └── test_services/
│       ├── test_spotify.py
│       ├── test_lastfm.py
│       └── test_ai.py
├── requirements.txt             # Dépendances Python
├── Dockerfile                   # Image Docker
├── docker-compose.yml           # Orchestration
└── pytest.ini                   # Config pytest
```

### Service: Tracker Last.fm (Background)

**Fichier**: `app/services/tracker_service.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pylast
from datetime import datetime, timezone
from app.database import SessionLocal
from app.services.spotify_service import SpotifyService
from app.services.ai_service import AIService
from app.models import Track, ListeningHistory, Artist, Album

class LastFMTrackerService:
    """Service de tracking Last.fm en arrière-plan."""
    
    def __init__(self, config: dict):
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.network = pylast.LastFMNetwork(
            api_key=config['lastfm']['api_key'],
            api_secret=config['lastfm']['api_secret'],
            username=config['lastfm']['username']
        )
        self.spotify = SpotifyService(config['spotify'])
        self.ai = AIService(config['euria'])
        self.is_running = False
        self.last_track_key = None
    
    async def start(self):
        """Démarrer le tracker."""
        if self.is_running:
            return
        
        interval = self.config['tracker']['interval_seconds']
        self.scheduler.add_job(
            self._poll_lastfm,
            trigger=IntervalTrigger(seconds=interval),
            id='lastfm_tracker',
            replace_existing=True
        )
        self.scheduler.start()
        self.is_running = True
    
    async def stop(self):
        """Arrêter le tracker."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
    
    async def _poll_lastfm(self):
        """Interroger Last.fm et enregistrer les nouveaux tracks."""
        try:
            user = pylast.User(self.config['lastfm']['username'], self.network)
            current_track = user.get_now_playing()
            
            if not current_track:
                return
            
            # Créer clé unique pour éviter doublons
            track_key = f"{current_track.artist}|{current_track.title}|{current_track.album}"
            
            if track_key == self.last_track_key:
                return  # Même track qu'avant, skip
            
            self.last_track_key = track_key
            
            # Extraire métadonnées
            artist_name = str(current_track.artist)
            track_title = str(current_track.title)
            album_title = str(current_track.album) if current_track.album else "Unknown"
            
            # Enrichir avec Spotify
            artist_image = await self.spotify.search_artist_image(artist_name)
            album_image = await self.spotify.search_album_image(artist_name, album_title)
            
            # Générer info IA
            ai_info = await self.ai.generate_album_info(artist_name, album_title)
            
            # Sauvegarder en DB
            db = SessionLocal()
            try:
                # Créer/récupérer artiste
                artist = db.query(Artist).filter_by(name=artist_name).first()
                if not artist:
                    artist = Artist(name=artist_name)
                    db.add(artist)
                    db.flush()
                
                # Créer/récupérer album
                album = db.query(Album).filter_by(title=album_title).first()
                if not album:
                    album = Album(title=album_title)
                    album.artists.append(artist)
                    db.add(album)
                    db.flush()
                
                # Créer track
                track = Track(
                    album_id=album.id,
                    title=track_title
                )
                db.add(track)
                db.flush()
                
                # Créer entrée historique
                history = ListeningHistory(
                    track_id=track.id,
                    timestamp=int(datetime.now(timezone.utc).timestamp()),
                    date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    source='lastfm',
                    loved=False
                )
                db.add(history)
                db.commit()
                
                print(f"✅ Track enregistré: {artist_name} - {track_title}")
                
            except Exception as e:
                db.rollback()
                print(f"❌ Erreur DB: {e}")
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Erreur polling Last.fm: {e}")
```

### Service: Génération Playlists

**Fichier**: `app/services/playlist_generator.py`

```python
from typing import List, Dict, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Track, ListeningHistory
from app.services.ai_service import AIService

class PlaylistGenerator:
    """Générateur de playlists basées sur patterns d'écoute."""
    
    ALGORITHMS = [
        'top_sessions',
        'artist_correlations',
        'artist_flow',
        'time_based',
        'complete_albums',
        'rediscovery',
        'ai_generated'
    ]
    
    def __init__(self, ai_service: AIService):
        self.ai = ai_service
    
    async def generate(
        self, 
        algorithm: str, 
        max_tracks: int = 25,
        ai_prompt: Optional[str] = None
    ) -> List[int]:
        """Générer playlist selon algorithme choisi.
        
        Returns:
            Liste d'IDs de tracks
        """
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Algorithme invalide: {algorithm}")
        
        if algorithm == 'top_sessions':
            return await self._top_sessions(max_tracks)
        elif algorithm == 'artist_correlations':
            return await self._artist_correlations(max_tracks)
        elif algorithm == 'artist_flow':
            return await self._artist_flow(max_tracks)
        elif algorithm == 'time_based':
            return await self._time_based(max_tracks)
        elif algorithm == 'complete_albums':
            return await self._complete_albums(max_tracks)
        elif algorithm == 'rediscovery':
            return await self._rediscovery(max_tracks)
        elif algorithm == 'ai_generated':
            if not ai_prompt:
                raise ValueError("Prompt IA requis pour ai_generated")
            return await self._ai_generated(max_tracks, ai_prompt)
    
    async def _top_sessions(self, max_tracks: int) -> List[int]:
        """Pistes des sessions d'écoute les plus longues."""
        db = SessionLocal()
        try:
            # Récupérer tout l'historique trié
            history = db.query(ListeningHistory).order_by(
                ListeningHistory.timestamp
            ).all()
            
            # Détecter sessions (gap < 30 min)
            sessions = []
            current_session = []
            last_timestamp = 0
            
            for entry in history:
                if last_timestamp and (entry.timestamp - last_timestamp) > 1800:
                    # Nouvelle session
                    if current_session:
                        sessions.append(current_session)
                    current_session = []
                
                current_session.append(entry.track_id)
                last_timestamp = entry.timestamp
            
            if current_session:
                sessions.append(current_session)
            
            # Trier sessions par longueur
            sessions.sort(key=len, reverse=True)
            
            # Prendre tracks des sessions les plus longues
            track_ids = []
            for session in sessions:
                track_ids.extend(session)
                if len(track_ids) >= max_tracks:
                    break
            
            return track_ids[:max_tracks]
            
        finally:
            db.close()
    
    async def _ai_generated(self, max_tracks: int, prompt: str) -> List[int]:
        """Génération playlist par IA avec prompt personnalisé."""
        # Récupérer liste de tous les artistes/albums disponibles
        db = SessionLocal()
        try:
            # Construire contexte pour IA
            artists = db.query(Artist).limit(100).all()
            albums = db.query(Album).limit(100).all()
            
            context = "Artistes disponibles: " + ", ".join([a.name for a in artists])
            context += "\nAlbums disponibles: " + ", ".join([a.title for a in albums])
            
            # Appeler IA avec prompt + contexte
            ai_prompt_full = f"{prompt}\n\nContexte:\n{context}\n\nGénère une liste de {max_tracks} tracks qui correspondent."
            
            response = await self.ai.ask_for_ia(ai_prompt_full)
            
            # Parser réponse IA et matcher avec tracks en DB
            # (logique de parsing à implémenter selon format réponse)
            
            # Pour l'instant, retourner tracks aléatoires (fallback)
            tracks = db.query(Track).limit(max_tracks).all()
            return [t.id for t in tracks]
            
        finally:
            db.close()
```

---

## 📦 STRUCTURE PROJET COMPLÈTE

```
music-tracker/
├── frontend/                    # Application React
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── (voir structure détaillée ci-dessus)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env.example
│
├── backend/                     # API FastAPI
│   ├── app/
│   │   ├── (voir structure détaillée ci-dessus)
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── config/                      # Configuration JSON
│   ├── app.json                 # Config application
│   ├── secrets.json             # API keys (GITIGNORE)
│   └── app.example.json
│
├── data/                        # Données persistantes
│   ├── musique.db               # Base SQLite
│   └── backups/                 # Sauvegardes JSON
│
├── scripts/                     # Scripts utilitaires
│   ├── setup.sh                 # Installation complète
│   ├── start-dev.sh             # Lancement dev (frontend + backend)
│   ├── migrate-from-json.py     # Migration JSON → SQLite
│   └── backup-db.py             # Export SQLite → JSON
│
├── docs/                        # Documentation
│   ├── API.md                   # Documentation API
│   ├── ARCHITECTURE.md          # Architecture détaillée
│   ├── DEPLOYMENT.md            # Guide déploiement
│   └── MIGRATION-GUIDE.md       # Guide migration JSON
│
├── docker-compose.yml           # Orchestration Docker
├── .gitignore
├── README.md
└── LICENSE
```

---

## 🚀 INSTALLATION ET DÉMARRAGE

### Prérequis

- **Node.js**: 18.0+ (avec npm 9+)
- **Python**: 3.10+
- **Git**: 2.30+

### Installation Rapide

```bash
# Cloner le repository
git clone https://github.com/username/music-tracker.git
cd music-tracker

# Exécuter script d'installation
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configuration des secrets
cp config/app.example.json config/app.json
cp config/secrets.example.json config/secrets.json
# Éditer config/secrets.json avec vos API keys

# Démarrer en mode développement
./scripts/start-dev.sh
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
alembic upgrade head

# Démarrer serveur (dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Installer dépendances
npm install

# Démarrer serveur dev
npm run dev

# Build production
npm run build
```

---

## 🧪 TESTS

### Backend (pytest)

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend (Vitest)

```bash
cd frontend
npm run test
npm run test:coverage
```

---

## 🔒 SÉCURITÉ

### Fichiers à GITIGNORE

```gitignore
# Secrets
config/secrets.json
backend/.env
frontend/.env

# Base de données
data/musique.db
data/musique.db-journal

# Build
frontend/dist/
frontend/node_modules/
backend/.venv/
backend/__pycache__/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

### Bonnes Pratiques

1. **API Keys**: Jamais en dur dans le code
2. **SQLite**: Permissions 600 sur `musique.db`
3. **CORS**: Configurer origins autorisés en production
4. **Rate Limiting**: Limiter requêtes API (ex: 100/min)
5. **Input Validation**: Pydantic + Zod pour valider toutes les entrées
6. **SQL Injection**: Utiliser ORM (SQLAlchemy) exclusivement
7. **XSS**: React échappe automatiquement, mais attention aux `dangerouslySetInnerHTML`

---

## 📊 MIGRATION DEPUIS JSON

### Script de Migration

**Fichier**: `scripts/migrate-from-json.py`

```python
#!/usr/bin/env python3
"""Script de migration JSON → SQLite.

Migre les données depuis les fichiers JSON historiques vers la nouvelle base SQLite.

Fichiers sources:
    - discogs-collection.json → albums, artists, metadata
    - chk-roon.json → tracks, listening_history
    - soundtrack.json → metadata (film info)

Usage:
    python migrate-from-json.py --backup --verify
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from app.database import SessionLocal, engine
from app.models import Base, Artist, Album, Track, ListeningHistory, Image, Metadata

def backup_database():
    """Créer backup de la DB avant migration."""
    db_path = Path("data/musique.db")
    if db_path.exists():
        backup_path = Path(f"data/backups/musique-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup créé: {backup_path}")

def migrate_discogs_collection(json_path: str):
    """Migrer discogs-collection.json."""
    with open(json_path, 'r', encoding='utf-8') as f:
        albums_data = json.load(f)
    
    db = SessionLocal()
    try:
        for album_data in albums_data:
            # Créer artistes
            artist_names = album_data.get('Artiste', [])
            if isinstance(artist_names, str):
                artist_names = [artist_names]
            
            artists = []
            for artist_name in artist_names:
                artist = db.query(Artist).filter_by(name=artist_name).first()
                if not artist:
                    artist = Artist(name=artist_name)
                    db.add(artist)
                    db.flush()
                artists.append(artist)
            
            # Créer album
            album = Album(
                title=album_data['Titre'],
                year=album_data.get('Année'),
                support=album_data.get('Support'),
                discogs_id=str(album_data.get('release_id')),
                spotify_url=album_data.get('Spotify_URL'),
                discogs_url=f"https://www.discogs.com/release/{album_data.get('release_id')}"
            )
            album.artists = artists
            db.add(album)
            db.flush()
            
            # Métadonnées
            metadata = Metadata(
                album_id=album.id,
                resume=album_data.get('Resume'),
                ai_info=album_data.get('ai_info'),
                labels=json.dumps(album_data.get('Labels', []))
            )
            db.add(metadata)
            
            # Images
            if album_data.get('Pochette'):
                img_discogs = Image(
                    url=album_data['Pochette'],
                    image_type='album',
                    source='discogs',
                    album_id=album.id
                )
                db.add(img_discogs)
            
            if album_data.get('Spotify_Cover_URL'):
                img_spotify = Image(
                    url=album_data['Spotify_Cover_URL'],
                    image_type='album',
                    source='spotify',
                    album_id=album.id
                )
                db.add(img_spotify)
        
        db.commit()
        print(f"✅ {len(albums_data)} albums migrés depuis Discogs")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur migration Discogs: {e}")
        raise
    finally:
        db.close()

def migrate_listening_history(json_path: str):
    """Migrer chk-roon.json."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tracks_data = data.get('tracks', [])
    
    db = SessionLocal()
    try:
        for track_data in tracks_data:
            artist_name = track_data['artist']
            album_title = track_data['album']
            track_title = track_data['title']
            
            # Récupérer/créer artiste
            artist = db.query(Artist).filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.add(artist)
                db.flush()
            
            # Récupérer/créer album
            album = db.query(Album).filter_by(title=album_title).first()
            if not album:
                album = Album(title=album_title)
                album.artists.append(artist)
                db.add(album)
                db.flush()
            
            # Créer track
            track = db.query(Track).filter_by(
                album_id=album.id,
                title=track_title
            ).first()
            if not track:
                track = Track(
                    album_id=album.id,
                    title=track_title
                )
                db.add(track)
                db.flush()
            
            # Créer entrée historique
            history = ListeningHistory(
                track_id=track.id,
                timestamp=track_data['timestamp'],
                date=track_data['date'],
                source=track_data.get('source', 'roon'),
                loved=track_data.get('loved', False)
            )
            db.add(history)
            
            # Images artiste
            if track_data.get('artist_spotify_image'):
                img_artist = Image(
                    url=track_data['artist_spotify_image'],
                    image_type='artist',
                    source='spotify',
                    artist_id=artist.id
                )
                db.add(img_artist)
            
            # Images album
            if track_data.get('album_spotify_image'):
                img_album_spotify = Image(
                    url=track_data['album_spotify_image'],
                    image_type='album',
                    source='spotify',
                    album_id=album.id
                )
                db.add(img_album_spotify)
            
            if track_data.get('album_lastfm_image'):
                img_album_lastfm = Image(
                    url=track_data['album_lastfm_image'],
                    image_type='album',
                    source='lastfm',
                    album_id=album.id
                )
                db.add(img_album_lastfm)
        
        db.commit()
        print(f"✅ {len(tracks_data)} tracks d'historique migrés")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur migration historique: {e}")
        raise
    finally:
        db.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Migrer JSON → SQLite')
    parser.add_argument('--backup', action='store_true', help='Créer backup avant migration')
    parser.add_argument('--verify', action='store_true', help='Vérifier après migration')
    args = parser.parse_args()
    
    if args.backup:
        backup_database()
    
    # Créer tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées")
    
    # Migrer données
    migrate_discogs_collection("data-legacy/discogs-collection.json")
    migrate_listening_history("data-legacy/chk-roon.json")
    
    print("✅ Migration terminée")

if __name__ == "__main__":
    main()
```

---

## 📈 PERFORMANCE ET OPTIMISATIONS

### Frontend
- **Code Splitting**: React.lazy() pour pages
- **Image Lazy Loading**: Intersection Observer API
- **Virtual Scrolling**: Pour listes >1000 éléments (react-window)
- **Debounce**: Sur recherches (300ms)
- **Memoization**: React.memo() sur composants lourds

### Backend
- **Index Database**: Sur artist_name, album_title, timestamp
- **Query Pagination**: Limit/Offset systématiques
- **Cache HTTP**: ETags sur GET endpoints
- **Connection Pool**: SQLAlchemy (5 connexions)
- **Async I/O**: FastAPI + httpx pour APIs externes

### Base de Données
- **VACUUM**: Périodique (1x/mois)
- **ANALYZE**: Après gros imports
- **WAL Mode**: Pour concurrence (SQLite)
- **Index Composite**: (artist, album) pour recherches

---

## 🐳 DÉPLOIEMENT DOCKER

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### Backend Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 📚 DOCUMENTATION API

### Swagger UI
Accessible sur: `http://localhost:8000/docs`

### Exemples de Requêtes

#### Récupérer albums avec pagination
```bash
curl -X GET "http://localhost:8000/api/v1/collection/albums?page=1&page_size=30&search=nina&support=Vinyle"
```

Response:
```json
{
  "items": [
    {
      "id": 42,
      "title": "Pastel Blues",
      "year": 1965,
      "support": "Vinyle",
      "artists": [{"id": 12, "name": "Nina Simone"}],
      "images": ["https://i.scdn.co/image/..."],
      "ai_info": "Pastel Blues est un album de Nina Simone...",
      "created_at": "2026-01-30T10:00:00Z"
    }
  ],
  "total": 142,
  "page": 1,
  "page_size": 30,
  "pages": 5
}
```

#### Générer playlist
```bash
curl -X POST "http://localhost:8000/api/v1/playlists/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "ai_generated",
    "max_tracks": 25,
    "ai_prompt": "Musique jazz cool pour soirée entre amis"
  }'
```

#### Démarrer tracker
```bash
curl -X POST "http://localhost:8000/api/v1/services/tracker/start"
```

---

## ✅ CHECKLIST IMPLÉMENTATION

### Phase 1: Infrastructure (Semaine 1-2)
- [ ] Setup projet (monorepo frontend + backend)
- [ ] Configuration Vite + React + TypeScript
- [ ] Configuration FastAPI + SQLAlchemy
- [ ] Schéma DB SQLite complet
- [ ] Migrations Alembic (init)
- [ ] Docker setup (dev)
- [ ] Script migration JSON → SQLite

### Phase 2: Backend API (Semaine 3-4)
- [ ] Models SQLAlchemy (7 tables)
- [ ] Schemas Pydantic (validation)
- [ ] CRUD albums (GET, POST, PUT, DELETE)
- [ ] CRUD listening history
- [ ] Service Spotify (images)
- [ ] Service Last.fm (polling)
- [ ] Service AI (EurIA)
- [ ] Tracker background (APScheduler)
- [ ] Tests pytest (>80% coverage)

### Phase 3: Frontend Core (Semaine 5-6)
- [ ] Layout (Navbar, Sidebar, Footer)
- [ ] Page Collection (liste + filtres)
- [ ] Page Journal (liste chronologique)
- [ ] Composants réutilisables (Card, Modal, etc.)
- [ ] Integration TanStack Query
- [ ] Gestion erreurs (ErrorBoundary)
- [ ] Loader states

### Phase 4: Features Avancées (Semaine 7-8)
- [ ] Page Timeline horaire
- [ ] Page Playlists
- [ ] Génération playlists (7 algorithmes)
- [ ] Page Analytics (stats + charts)
- [ ] Page Settings (config tracker)
- [ ] Export playlists (M3U, JSON, CSV)

### Phase 5: Polish & Tests (Semaine 9-10)
- [ ] Tests frontend (Vitest)
- [ ] Responsive mobile
- [ ] Dark mode (optionnel)
- [ ] Performance optimization
- [ ] Documentation API (Swagger)
- [ ] Guide utilisateur
- [ ] Déploiement prod (Docker)

---

## 📞 SUPPORT

**Auteur**: Patrick Ostertag  
**Email**: patrick.ostertag@gmail.com  
**GitHub**: https://github.com/pat-the-geek/music-tracker

---

**Date**: 30 janvier 2026  
**Version**: 4.0.0 React Rebuild Specification  
**Statut**: ✅ Prêt pour implémentation
