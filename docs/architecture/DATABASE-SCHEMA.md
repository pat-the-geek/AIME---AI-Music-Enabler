# Schéma Relationnel de la Base de Données

## Vue d'ensemble

Base de données SQLite pour AIME - AI Music Enabler avec 10 tables principales et 1 table de liaison.

## Diagramme ER (Entity Relationship)

```mermaid
---
title: AIME Database Schema
config:
    layout: elk
---
erDiagram
    %% Tables principales
    ALBUM {
        int id PK
        string title
        int year
        string support
        string source "discogs, lastfm, roon, spotify, manual"
        string discogs_id UK
        string spotify_url
        string discogs_url
        datetime created_at
        datetime updated_at
    }
    
    ARTIST {
        int id PK
        string name UK
        string spotify_id
        string lastfm_url
        datetime created_at
        datetime updated_at
    }
    
    TRACK {
        int id PK
        int album_id FK
        string title
        int track_number
        int duration_seconds
        string spotify_id
        datetime created_at
        datetime updated_at
    }
    
    LISTENING_HISTORY {
        int id PK
        int track_id FK
        int timestamp "Unix timestamp"
        string date "YYYY-MM-DD HH:MM"
        string source "roon or lastfm"
        boolean loved
        datetime created_at
    }
    
    PLAYLIST {
        int id PK
        string name
        string algorithm "top_sessions, ai_generated"
        text ai_prompt
        int track_count
        datetime created_at
    }
    
    PLAYLIST_TRACK {
        int playlist_id PK,FK
        int track_id PK,FK
        int position
    }
    
    METADATA {
        int id PK
        int album_id FK,UK
        text ai_info
        text resume
        text labels "JSON array"
        string film_title
        int film_year
        string film_director
        datetime created_at
        datetime updated_at
    }
    
    IMAGE {
        int id PK
        string url
        string image_type "artist, album"
        string source "spotify, lastfm, discogs"
        int artist_id FK
        int album_id FK
        datetime created_at
        datetime updated_at
    }
    
    SERVICE_STATE {
        string service_name PK "tracker, roon_tracker, scheduler"
        boolean is_active
        datetime last_updated
    }
    
    ALBUM_ARTIST {
        int album_id PK,FK
        int artist_id PK,FK
        datetime created_at
    }
    
    %% Relations
    ALBUM ||--o{ TRACK : contains
    ALBUM ||--o| METADATA : has
    ALBUM ||--o{ IMAGE : has
    ALBUM }o--o{ ARTIST : created_by
    
    ARTIST ||--o{ IMAGE : has
    
    TRACK ||--o{ LISTENING_HISTORY : logged_in
    TRACK }o--o{ PLAYLIST : included_in
    
    PLAYLIST ||--o{ PLAYLIST_TRACK : contains
    
    ALBUM_ARTIST }o--|| ALBUM : links
    ALBUM_ARTIST }o--|| ARTIST : links
    
    PLAYLIST_TRACK }o--|| PLAYLIST : belongs_to
    PLAYLIST_TRACK }o--|| TRACK : references
```

## Description des Tables

### 🎵 Tables Musicales

#### **albums**
Albums musicaux provenant de différentes sources (Discogs, Last.fm, Roon, Spotify).
- **PK**: `id`
- **UK**: `discogs_id`
- **Indexes**: `title`, `source`
- **Relations**: 
  - One-to-Many avec `tracks`
  - One-to-One avec `metadata`
  - One-to-Many avec `images`
  - Many-to-Many avec `artists` (via `album_artist`)

#### **artists**
Artistes musicaux avec enrichissement Spotify/Last.fm.
- **PK**: `id`
- **UK**: `name`
- **Relations**:
  - One-to-Many avec `images`
  - Many-to-Many avec `albums` (via `album_artist`)

#### **tracks**
Pistes musicales appartenant à des albums.
- **PK**: `id`
- **FK**: `album_id` (CASCADE DELETE)
- **Relations**:
  - Many-to-One avec `album`
  - One-to-Many avec `listening_history`
  - Many-to-Many avec `playlists` (via `playlist_tracks`)

### 📊 Tables de Données

#### **listening_history**
Historique d'écoute depuis Roon et Last.fm.
- **PK**: `id`
- **FK**: `track_id` (CASCADE DELETE)
- **Indexes**: `timestamp`, `date`, `source`
- **Relations**: Many-to-One avec `track`

#### **metadata**
Métadonnées enrichies (IA, Discogs, BOF).
- **PK**: `id`
- **FK+UK**: `album_id` (CASCADE DELETE, unique)
- **Indexes**: `album_id`, `film_title`
- **Relations**: One-to-One avec `album`

#### **images**
URLs d'images pour albums et artistes.
- **PK**: `id`
- **FK**: `artist_id` OR `album_id` (CASCADE DELETE, exclusive)
- **Indexes**: `artist_id`, `album_id`
- **Constraint**: Check que seulement artist_id OU album_id est rempli
- **Relations**: Many-to-One avec `artist` ou `album`

### 🎯 Tables Fonctionnelles

#### **playlists**
Playlists générées (top sessions, IA).
- **PK**: `id`
- **Relations**: One-to-Many avec `playlist_tracks`

#### **playlist_tracks**
Table de liaison playlists-tracks avec position.
- **PK Composite**: `playlist_id`, `track_id`
- **FK**: `playlist_id`, `track_id` (CASCADE DELETE)
- **Relations**: Many-to-One avec `playlist` et `track`

#### **service_states**
États de persistance des services background (auto-restart).
- **PK**: `service_name`
- **Values**: `tracker`, `roon_tracker`, `scheduler`

### 🔗 Tables de Liaison

#### **album_artist**
Table associative Many-to-Many entre albums et artistes.
- **PK Composite**: `album_id`, `artist_id`
- **FK**: `album_id`, `artist_id` (CASCADE DELETE)

## Statistiques

- **10 tables** principales + 2 tables de liaison
- **7 relations One-to-Many**
- **3 relations Many-to-Many**
- **1 relation One-to-One**
- **12 index** pour optimisation
- **2 contraintes** de validation

## Migrations

Les migrations Alembic sont dans `/backend/alembic/versions/`:
- `001_*` - Schema initial
- `002_*` - Add source column
- `003_*` - Add service_states table

---

*Dernière mise à jour: 1er février 2026 - v4.3.1*
