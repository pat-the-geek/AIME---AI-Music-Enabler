# API Documentation - Music Tracker

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Actuellement aucune authentification n'est requise. À implémenter pour la production.

## Endpoints

### Collection

#### Liste des albums

```http
GET /collection/albums
```

**Query Parameters:**
- `page` (int, default: 1): Numéro de page
- `page_size` (int, default: 30): Nombre d'éléments par page
- `search` (string, optional): Recherche dans titre ou artiste
- `support` (string, optional): Filtrer par support (Vinyle, CD, Digital)
- `year` (int, optional): Filtrer par année
- `is_soundtrack` (boolean, optional): Filtrer les BOF

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Pastel Blues",
      "year": 1965,
      "support": "Vinyle",
      "artists": ["Nina Simone"],
      "images": ["https://..."],
      "ai_info": "Description...",
      "created_at": "2026-01-30T10:00:00Z",
      "updated_at": "2026-01-30T10:00:00Z"
    }
  ],
  "total": 142,
  "page": 1,
  "page_size": 30,
  "pages": 5
}
```

#### Détail d'un album

```http
GET /collection/albums/{album_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Pastel Blues",
  "year": 1965,
  "support": "Vinyle",
  "artists": ["Nina Simone"],
  "images": ["https://..."],
  "ai_info": "Description...",
  "resume": "Résumé long...",
  "labels": ["Philips Records"],
  "film_title": null,
  "film_year": null,
  "film_director": null,
  "created_at": "2026-01-30T10:00:00Z",
  "updated_at": "2026-01-30T10:00:00Z"
}
```

### Historique

#### Journal d'écoute

```http
GET /history/tracks
```

**Query Parameters:**
- `page` (int): Numéro de page
- `page_size` (int): Nombre d'éléments
- `source` (string): Filtrer par source (lastfm)
- `loved` (boolean): Filtrer favoris
- `artist` (string): Filtrer par artiste
- `album` (string): Filtrer par album
- `start_date` (string): Date de début (YYYY-MM-DD)
- `end_date` (string): Date de fin (YYYY-MM-DD)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "timestamp": 1706612400,
      "date": "2026-01-30 14:00",
      "artist": "Nina Simone",
      "title": "I Put a Spell on You",
      "album": "Pastel Blues",
      "loved": false,
      "source": "lastfm",
      "artist_image": "https://...",
      "album_image": "https://...",
      "album_lastfm_image": "https://...",
      "ai_info": "Description..."
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 50,
  "pages": 25
}
```

#### Timeline horaire

```http
GET /history/timeline?date=2026-01-30
```

**Response:**
```json
{
  "date": "2026-01-30",
  "hours": {
    "14": [
      {
        "id": 1,
        "time": "14:00",
        "artist": "Nina Simone",
        "title": "I Put a Spell on You",
        "album": "Pastel Blues",
        "loved": false
      }
    ]
  },
  "stats": {
    "total_tracks": 45,
    "unique_artists": 12,
    "unique_albums": 8,
    "peak_hour": 18
  }
}
```

#### Statistiques

```http
GET /history/stats
```

**Query Parameters:**
- `start_date` (string, optional)
- `end_date` (string, optional)

**Response:**
```json
{
  "total_tracks": 1250,
  "unique_artists": 150,
  "unique_albums": 200,
  "peak_hour": 18,
  "total_duration_seconds": 245000
}
```

### Playlists

> ⚠️ **Note:** Les endpoints de playlists sont temporairement désactivés durant la migration.

#### Générer une playlist (Désactivé)

```http
POST /playlists/generate
```

**Request Body:**
```json
{
  "algorithm": "top_sessions",
  "max_tracks": 25,
  "ai_prompt": null,
  "name": "My Playlist"
}
```

**Algorithmes disponibles:**
- `top_sessions`: Pistes des sessions les plus longues
- `artist_correlations`: Artistes souvent écoutés ensemble
- `artist_flow`: Transitions naturelles entre artistes
- `time_based`: Basé sur peak hours
- `complete_albums`: Albums écoutés en entier
- `rediscovery`: Pistes aimées mais pas écoutées récemment
- `ai_generated`: Génération par IA (nécessite `ai_prompt`)

**Response:**
```json
{
  "id": 1,
  "name": "My Playlist",
  "algorithm": "top_sessions",
  "ai_prompt": null,
  "track_count": 25,
  "created_at": "2026-01-30T14:00:00Z"
}
```

#### Détail d'une playlist

```http
GET /playlists/{playlist_id}
```

**Response:**
```json
{
  "id": 1,
  "name": "My Playlist",
  "algorithm": "top_sessions",
  "track_count": 25,
  "tracks": [
    {
      "track_id": 1,
      "position": 1,
      "title": "I Put a Spell on You",
      "artist": "Nina Simone",
      "album": "Pastel Blues",
      "duration_seconds": 180
    }
  ],
  "total_duration_seconds": 4500,
  "unique_artists": 10,
  "unique_albums": 8,
  "created_at": "2026-01-30T14:00:00Z"
}
```

#### Exporter une playlist

```http
GET /playlists/{playlist_id}/export?format=m3u
```

**Formats disponibles:** m3u, json, csv, txt

### Services

#### Statut du tracker

```http
GET /services/tracker/status
```

**Response:**
```json
{
  "running": true,
  "last_track": "Nina Simone|I Put a Spell on You|Pastel Blues",
  "interval_seconds": 120
}
```

#### Démarrer le tracker

```http
POST /services/tracker/start
```

#### Arrêter le tracker

```http
POST /services/tracker/stop
```

#### Synchroniser Discogs

```http
POST /services/discogs/sync
```

**Response:**
```json
{
  "status": "success",
  "synced_albums": 25,
  "total_albums": 142
}
```

#### Générer info IA pour un album

```http
POST /services/ai/generate-info?album_id=1
```

**Response:**
```json
{
  "album_id": 1,
  "ai_info": "Pastel Blues est un album de Nina Simone..."
}
```

### Recherche

#### Recherche globale

```http
GET /search?q=nina&type=album&limit=20
```

**Query Parameters:**
- `q` (string, required): Requête de recherche
- `type` (string, optional): Type (album, artist, track)
- `limit` (int, default: 20): Nombre de résultats

**Response:**
```json
{
  "query": "nina",
  "albums": [...],
  "artists": [...],
  "tracks": [...]
}
```

## Codes d'erreur

- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error
