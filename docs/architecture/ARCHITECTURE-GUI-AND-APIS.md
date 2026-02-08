# 🏗️ Architecture AIME - Interface Graphique & API Externes

**Status:** Architecture Current (7 février 2026)  
**Document:** Architecture globale avec focus sur GUI et API externes  
**Version:** 2.0

---

## 📊 Vue d'ensemble: Flux complet client-serveur

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          INTERFACE GRAPHIQUE (React/TSX)                    │
│                                                                               │
│  Pages:                           Composants Principaux:                    │
│  ├─ Collection.tsx               ├─ AlbumDetailDialog                       │
│  ├─ Magazine.tsx                 ├─ MagazinePage                           │
│  ├─ Playlists.tsx                ├─ FloatingRoonController                 │
│  ├─ ArtistArticle.tsx            ├─ ArtistPortraitModal                    │
│  ├─ Journal.tsx                  └─ ErrorBoundary                          │
│  ├─ Analytics.tsx                                                           │
│  ├─ Settings.tsx                                                            │
│  └─ Timeline.tsx                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                      ↓
                    ┌─────────────────────────────────┐
                    │    API Client (axios)           │
                    │  apiClient.get/post/put/delete  │
                    └─────────────────────────────────┘
                                      ↓
┌────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI/Python)                            │
│                   /api/v1 - Endpoints Organisés par Domaine               │
│                                                                               │
│  ├─ /collection/               ├─ /content/              ├─ /playback/    │
│  │  ├─ /albums                 │  ├─ /articles           │  ├─ /playlists│
│  │  ├─ /artists                │  ├─ /haikus             │  ├─ /roon      │
│  │  ├─ /search                 │  ├─ /descriptions       │  └─ /queue     │
│  │  └─ /export                 └─ /magazines            │                 │
│  │                               └─ /journals            │                 │
│  ├─ /analytics/                ├─ /tracking/            │                 │
│  │  ├─ /stats                  │  └─ /listening-history  │                 │
│  │  └─ /patterns               └────────────────────────  │                 │
│  └────────────────────────────────────────────────────────────────────────  │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│                 SERVICES (Métier + API Externes)                           │
│                                                                               │
│  External APIs:               Collection Services:     Content Services:   │
│  ├─ EurIA (Infomaniak AI)     ├─ artist_service.py    ├─ haiku_service  │
│  ├─ Spotify API               ├─ album_service.py     ├─ article_service│
│  ├─ Last.fm API               ├─ track_service.py     ├─ description_svc│
│  ├─ Discogs API               ├─ search_service.py    └─ magazine_gen   │
│  ├─ Roon Core API             └─ collection_service.py│                 │
│  └─ PostgreSQL DB                                     Playback Services:│
│                             Analytics Services:      ├─ playlist_service│
│                             ├─ stats_service.py      ├─ queue_service  │
│                             ├─ patterns_service.py   ├─ roon_playback  │
│                             └─ tracking_service.py   └─ roon_tracker   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 INTERFACE GRAPHIQUE (Frontend)

### 📄 Pages Principales

#### 1. **Collection.tsx** - Bibliothèque musicale
**Affiche:** Grille d'albums avec filtrage et recherche
- **Éléments:** Albums (titre, artistes, année, support)
- **Actions:** Search, Filter (genre, support), Sort, Details, Export
- **Dialogues:** `AlbumDetailDialog` (détails album complet)
- **APIs appelées:**
  - `GET /collection/albums?search=...&support=...&page=...` → Backend
    - Utilise: `ai_service` (enrichissement des descriptions) → **EurIA**
    - Utilise: `spotify_service` (images albums) → **Spotify**

**Interface Elements:**
```
┌─────────────────────────────────────────────────┐
│  Search: [_______________]  Support: [Filter▼]  │
│  Sort: [Title▼] [Order▼]                        │
│─────────────────────────────────────────────────┤
│  ┌──────────┬──────────┬──────────┐             │
│  │ Album 1  │ Album 2  │ Album 3  │  ← Cards   │
│  │ Art + Yr │ Art + Yr │ Art + Yr │             │
│  └──────────┴──────────┴──────────┘             │
│  ┌─────────────────────────────────────┐        │
│  │ < Page 1 of 50 > [Random] [Export▼] │        │
│  └─────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
```

---

#### 2. **Magazine.tsx** - Magazines auto-générés
**Affiche:** Lecteur de magazine (albums avec critiques IA et visuels)
- **Éléments:** Pages multi-album, descriptions IA, haïkus, critiques
- **Actions:** Parcourir pages, Éditions aléatoires, Refresh, Télécharger
- **Composants:** `MagazinePage` (affichage page magazine)
- **APIs appelées:**
  - `GET /magazines/editions/random` ou `/magazines/editions/{id}` → Backend
  - `POST /magazines/refresh` → Déclenche enrichissement
    - Utilise: `ai_service` (génération haïkus, articles) → **EurIA**
    - Utilise: `spotify_service` (artwork) → **Spotify**

**Interface Elements:**
```
┌──────────────────────────────────────────────────┐
│  [◀] Magazine #42  Page 1/32  [▶]  [🔄] [⬇]    │
├──────────────────────────────────────────────────┤
│                                                   │
│     [Album Cover]     Album Title                │
│                       by Artists                 │
│                       Year • Genre               │
│                                                   │
│     "Haïku by AI:"                              │
│     Beautiful autumn notes...                   │
│                                                   │
│     "Critique: ..."                             │
│                                                   │
└──────────────────────────────────────────────────┘

Actions: 
- Scroll/Navigation: ◀ | ▶ entre pages
- Random Edition: 🎲 select aléatoire édition
- Refresh: 🔄 regénère avec enrichissement
- Download: ⬇ exporte en PDF/Markdown
```

---

#### 3. **Playlists.tsx** - Gestion des playlists
**Affiche:** Liste des playlists créées, génération d'albums aléatoires
- **Éléments:** Nom playlist, nombre d'albums, actions création
- **Actions:** Créer, Éditer, Supprimer, Ajouter albums
- **APIs appelées:**
  - `GET /playback/playlists` → Backend
  - `POST /playback/playlists` → Crée playlist
  - `PUT /playback/playlists/{id}` → Met à jour
  - `POST /playback/roon/play/{zone_id}` → **Roon Bridge** pour lecture

**Interface Elements:**
```
┌─────────────────────────────────────────┐
│  Mes Playlists        [+ Nouvelle]      │
├─────────────────────────────────────────┤
│  ✓ "Chill Vibes"        15 albums [▶]   │
│  ✓ "Rock Classique"     28 albums [▶]   │
│  ✓ "Découvertes 2025"    42 albums [▶]  │
│  ✓ "Jazz Standards"      18 albums [▶]  │
└─────────────────────────────────────────┘

Clic [▶] = Play in Roon Zone
```

---

#### 4. **ArtistArticle.tsx** - Articles sur artistes
**Affiche:** Biographie et histoire musicale générée par IA
- **Éléments:** Portrait artiste, biographie, parcours musical, albums
- **Composants:** `ArtistPortraitModal` (modal détail)
- **APIs appelées:**
  - `GET /collection/artists/{artist_id}` → Backend
  - `GET /content/articles/{artist_id}` → Génère article IA
    - Utilise: `ai_service` → **EurIA** pour biographie
    - Utilise: `spotify_service` → **Spotify** pour image artiste

---

#### 5. **Journal.tsx** - Journal personnel/Écoutes
**Affiche:** Historique d'écoute, statistiques personnalisées
- **Éléments:** Timeline des albums écoutés, dates, durées
- **APIs appelées:**
  - `GET /tracking/listening-history` → Backend (données d'écoute)
  - Récupère depuis: **Roon API** (via roon_service.py)

---

#### 6. **Analytics.tsx** & **AnalyticsAdvanced.tsx** - Statistiques
**Affiche:** Graphiques de genres, artistes favoris, tendances
- **Éléments:** Charts, percentages, top 10 artistes/genres
- **APIs appelées:**
  - `GET /analytics/stats` → Statistiques globales
  - `GET /analytics/patterns` → Analyses de tendances

---

#### 7. **Settings.tsx** - Configuration
**Affiche:** Paramètres Roon, API Keys, Préférences
- **Actions:** Config Roon, Régénérer magazines, Nettoyer cache
- **APIs appelées:**
  - `POST /settings/*` → Mise à jour configuration

---

#### 8. **Timeline.tsx** - Historique chronologique
**Affiche:** Frise temporelle des albums par décade/année
- **Éléments:** Albums groupés par période, visualisations temporelles
- **APIs appelées:**
  - `GET /analytics/timeline` → Données chronologiques

---

### 🧩 Composants Réutilisables

#### **AlbumDetailDialog.tsx**
Modal affichant détails complets d'un album:
- Artwork (de Spotify ou Last.fm)
- Métadonnées (année, genre, label, durée)
- Description enrichie (via EurIA)
- Bouton "Play in Roon" → appelle `/playback/roon/play/{zone_id}`

#### **MagazinePage.tsx**
Affiche une page de magazine:
- Titre page
- Album + artwork + artiste
- Haïku généré (EurIA)
- Description/critique (EurIA)
- Année, genre, tags

#### **FloatingRoonController.tsx**
Widget flottant de contrôle Roon:
- Zone actuelle
- Play/Pause/Prev/Next
- Volume
- Appelle `/playback/roon/*` endpoints

#### **ArtistPortraitModal.tsx**
Modal d'artiste:
- Photo artiste (Spotify)
- Biographie (EurIA)
- Statistiques (# albums, genres)

---

## 🔌 API EXTERNES APPELÉES

### Key External APIs Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    AIME ARCHITECTURE                          │
│                                                                │
│                  ┌──────────────────────┐                     │
│                  │   React Frontend     │                     │
│                  │   (Collection,etc)   │                     │
│                  └──────────┬───────────┘                     │
│                             │                                 │
│                    ┌────────▼────────┐                        │
│                    │  FastAPI Backend │                       │
│                    │    /api/v1/*     │                       │
│                    └────────┬────────┘                        │
│       ┌────────────────────┼────────────────────┐             │
│       │                    │                    │             │
│       ▼                    ▼                    ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │ EurIA API   │    │ Spotify API │    │ Roon Bridge │      │
│  │ (Infomaniak)│    │             │    │ (Node.js)   │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│       │                    │                    │             │
│  Haïkus, Arts,        Images, URLs,      Playback,          │
│  Reviews, Search      Details, Browse    Zones, Tracks       │
│                                                                │
│       ┌──────────────────┐         ┌──────────────┐          │
│       ▼                  ▼         ▼              ▼          │
│  ┌──────────┐    ┌──────────┐ ┌─────────┐  ┌──────────┐     │
│  │ Last.fm  │    │ Discogs  │ │ PostgreSQL  │ Roon Core│     │
│  │ (Fallback)     │ (Metadata)  │ (Local DB)  │ (Network)    │
│  └──────────┘    └──────────┘ └─────────┘  └──────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

### 1. 🧠 **EurIA API** (Infomaniak AI)
**URL:** `https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions`  
**Auth:** Bearer Token (secrets.json)  
**Service Backend:** `backend/app/services/external/ai_service.py`

**Utilisé par:**
- **haiku_service.py** → Génération haïkus (streaming SSE)
- **article_service.py** → Biographies d'artistes
- **description_service.py** → Descriptions albums
- **album_collection_service.py** → Recherche albums par requête naturelle
- **magazine_generator_service.py** → Critiques et contenu magazine

**Endpoints Frontend Concernés:**
```
POST /content/haikus → EurIA génère haïku
POST /content/articles/{artist_id} → EurIA génère biographie
POST /content/descriptions → EurIA enrichit descriptions
POST /collection/search/ai → EurIA trouve albums via requête
POST /magazines/refresh → EurIA regénère contenu magazine
```

**Format de Requête:**
```python
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "Tu es un critique musical..."},
    {"role": "user", "content": "Écris un haïku sur..."}
  ],
  "max_tokens": 500,
  "temperature": 0.7,
  "stream": true  # SSE streaming
}
```

---

### 2. 🎵 **Spotify API**
**URL:** `https://api.spotify.com/v1`  
**Auth:** OAuth 2.0 Client Credentials (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)  
**Service Backend:** `backend/app/services/spotify_service.py`

**Utilisé par:**
- **album_collection_service.py** → Images albums, URLs
- **Collection.tsx** → Artwork dans la grille
- **MagazinePage.tsx** → Couvertures de magazines
- **ArtistPortraitModal.tsx** → Photos d'artistes

**Endpoints Spotify Appelés:**
```
GET /v1/search?q={artist}%20{album}&type=album&limit=1
  → Cherche album et retourne:
     - image_url (couvre album)
     - spotify_url (lien direct)
     - year (année publication)

GET /v1/search?q={artist}&type=artist&limit=1
  → Cherche artiste pour image profil
     - images[0].url (photo)
```

**Configuration Factory Pattern:**
```python
spotify_service = SpotifyService(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET')
)
image_url = await spotify_service.search_album_details_sync(artist, album)
```

---

### 3. 🎧 **Last.fm API**
**URL:** `http://ws.audioscrobbler.com/2.0/`  
**Auth:** API Key (API_KEY env var)  
**Service Backend:** `backend/app/services/lastfm_service.py` + fallback dans `spotify_service.py`

**Fallback Usage:**
- Si Spotify ne trouve pas l'image → Last.fm fallback
- Utilisé dans: `spotify_service.get_lastfm_image(artist, album)`

**Endpoints Appelés:**
```
GET /2.0/?method=album.getinfo&artist={artist}&album={album}&api_key=...
  → Retourne:
     - image[].#text (liste d'images)
```

---

### 4. 📀 **Discogs API**
**URL:** `https://api.discogs.com/`  
**Auth:** User-Agent + parfois API Token  
**Service Backend:** `backend/app/services/discogs_service.py`

**Utilisé pour:**
- Enrichissement métadonnées (labels, formats, numérotations)
- Synchronisation collection (import depuis Discogs)
- Recherche avancée

**Endpoints:**
```
GET /database/search?q={album}&type=release&per_page=100
  → Trouve éditions album
  
GET /releases/{release_id}
  → Détails complets édition (label, barcode, format, etc.)
```

---

### 5. 🎼 **Roon API** (via Node.js Bridge)
**Bridge:** `/Users/.../roon-bridge/app.js`  
**Port:** 3330 (local)  
**URL:** `http://localhost:3330`  
**Service Backend:** `backend/app/services/roon_service.py` + `backend/app/services/playback/roon_playback_service.py`

**Utilisé pour:**
- Récupérer zones de lecture
- Lancer lectures d'albums/playlists
- Contrôler playback (play/pause/next/prev)
- Récupérer historique d'écoute (pour Journal)
- Synchroniser état avec interface

**Bridge Endpoints:**
```
GET /status
  → {"connected": true, "core_name": "...", "zones": [...]}

GET /zones
  → {"zone_id": {...}, ...}

POST /zones/{zone_id}/play
  → {"uri": "qobuz://...", "type": "album"}

POST /zones/{zone_id}/control/{action}
  → action: "play", "pause", "next", "prev"

GET /browser
  → Navigation dans source (Qobuz, Tidal, etc.)
```

**Roon Integration Points:**
```tsx
// Frontend: FloatingRoonController.tsx
const playInRoon = async (zoneId, albumUri) => {
  await apiClient.post(`/playback/roon/zones/${zoneId}/play`, {
    uri: albumUri
  })
}

// Backend: api/v1/playback/roon.py
@router.post("/zones/{zone_id}/play")
async def play_in_zone(zone_id: str, request: PlayRequest):
  return roon_service.play(zone_id, request.uri)
```

---

### 6. 💾 **PostgreSQL Database**
**Role:** Stockage local (albums, artistes, historique)
**Service:** `backend/app/database.py`
**Modèles:** `backend/app/models/`

**Tables Principales:**
```sql
-- Collection
albums (id, title, artists, year, genre, support)
artists (id, name, image_url, description)
tracks (id, album_id, title, duration)

-- Content
magazine_editions (id, edition_number, generated_at, pages)
articles (id, artist_id, content, generated_at)

-- Analytics & Tracking
listening_history (id, track_id, zone_id, played_at, duration)
listening_stats (id, artist_id, play_count, total_duration)
```

---

## 🔄 Flux Principaux Requête-Réponse

### Flux 1: Affichage Collection (Collection.tsx)
```
1. Frontend: GET /collection/albums?search=jazz&page=1
   ↓
2. Backend: api/v1/collection/albums.py:list_albums()
   ├─ Query DB: albums WHERE LIKE search
   ├─ Pour chaque album:
   │  ├─ Fetch description via ai_service.py → EurIA
   │  ├─ Fetch image via spotify_service.py → Spotify
   │  └─ Fallback image via lastfm (if Spotify fails)
   ├─ Format response: AlbumResponse[]
   ↓
3. Frontend: Display grid avec
   - Album cover (Spotify)
   - Title, Artists
   - Year, Genre
   - Description enrichie (EurIA)
```

### Flux 2: Génération Magazine (Magazine.tsx)
```
1. Frontend: GET /magazines/editions/random
   ↓
2. Backend: api/v1/magazines/editions.py:get_random_edition()
   ├─ Query DB: SELECT random magazine_edition
   ├─ Load pages (prégenérées)
   ├─ Pour chaque page:
   │  ├─ Haïku: From DB (généré par haiku_service)
   │  ├─ Description: From DB (EurIA)
   │  ├─ Artwork: Spotify
   ↓
3. Frontend: MagazinePage.tsx
   ├─ Affiche cover
   ├─ Page-flip navigation
   ├─ Options refresh/download
   
3b. Click "🔄 Refresh":
   ├─ POST /magazines/refresh
   ├─ Backend regénère:
   │  ├─ haiku_service.stream() → EurIA (SSE stream)
   │  ├─ description_service → EurIA
   │  ├─ album images → Spotify
   ├─ Frontend recharge nouvelle édition
```

### Flux 3: Lecture dans Roon (FloatingRoonController.tsx)
```
1. Frontend: User click "Play" on Album Card
   ├─ Call: POST /playback/roon/zones/{zoneId}/play
   │  payload: {uri: "qobuz://album/12345"}
   ↓
2. Backend: api/v1/playback/roon.py:play()
   ├─ Resolve album URI (from Roon metadata, or search)
   ├─ Call: roon_service.play(zone_id, uri)
   │  ├─ HTTP POST to Bridge: http://localhost:3330/zones/{zone_id}/play
   │  ├─ Bridge forwards to Roon Core API
   ├─ Return: {"status": "playing", "zone_id": "...", "track": "..."}
   ↓
3. Frontend: FloatingRoonController.tsx
   ├─ Update zone status
   ├─ Show current track/artist
   ├─ Enable play/pause/next/prev buttons
   ├─ Poll /playback/roon/zones/{zoneId} every 2s
```

### Flux 4: Recherche IA d'Albums (Collection.tsx → Search)
```
1. Frontend: User types "Jazz fusion albums from 70s"
   ├─ Debounce 500ms
   ├─ POST /collection/search/ai
   │  payload: {"query": "Jazz fusion albums from 70s"}
   ↓
2. Backend: api/v1/collection/search.py:search_ai()
   ├─ Call: ai_service.search_albums(query)
   │  ├─ Prompt EurIA: "Donne-moi 10 albums jazz fusion années 70"
   │  ├─ EurIA returns: [{"artist": "...", "album": "..."}]
   ├─ Para chaque album:
   │  ├─ Get image via Spotify
   │  ├─ Get metadata via Discogs (optional)
   │  ├─ Get description via EurIA (optional)
   ├─ Return: AlbumResponse[]
   ↓
3. Frontend: Display results in grid
```

---

## 📊 Matrice: Composants Frontend → Services Backend → APIs Externes

| Frontend Component | API Endpoint | Backend Service | External APIs |
|---|---|---|---|
| Collection.tsx | GET /collection/albums | album_service.py | Spotify, EurIA, Last.fm |
| Collection.tsx | GET /collection/artists | artist_service.py | Spotify, EurIA |
| Magazine.tsx | GET /magazines/editions/{id} | magazine_gen_service.py | EurIA (haiku, description) |
| Magazine.tsx | POST /magazines/refresh | magazine_gen_service.py | EurIA, Spotify |
| Playlists.tsx | GET /playback/playlists | playlist_service.py | (Local DB) |
| Playlists.tsx | POST /playback/roon/play | roon_playback_service.py | Roon API via Bridge |
| FloatingRoonController | GET /playback/roon/zones | roon_service.py | Roon API via Bridge |
| FloatingRoonController | POST /playback/roon/control | roon_service.py | Roon API via Bridge |
| ArtistArticle.tsx | GET /content/articles/{id} | article_service.py | EurIA, Spotify |
| ArtistArticle.tsx | GET /content/haikus | haiku_service.py | EurIA (streaming) |
| Journal.tsx | GET /tracking/history | tracking_service.py | Roon API (via sync) |
| Analytics.tsx | GET /analytics/stats | stats_service.py | (Local DB) |
| Analytics.tsx | GET /analytics/patterns | patterns_service.py | (Local DB) |
| Timeline.tsx | GET /analytics/timeline | stats_service.py | (Local DB) |

---

## 🔐 Configuration & Secrets

### Location: `/Users/.../config/secrets.json`

```json
{
  "euria": {
    "url": "https://api.infomaniak.com/2/ai/...",
    "bearer": "sk-..."
  },
  "spotify": {
    "client_id": "...",
    "client_secret": "..."
  },
  "lastfm": {
    "api_key": "..."
  },
  "discogs": {
    "token": "...",
    "user_agent": "AIME/1.0"
  },
  "roon": {
    "bridge_url": "http://localhost:3330"
  }
}
```

### Env Vars (Fallback)

```bash
export EURIA_API_URL="https://api.infomaniak.com/..."
export EURIA_BEARER_TOKEN="sk-..."
export SPOTIFY_CLIENT_ID="..."
export SPOTIFY_CLIENT_SECRET="..."
export API_KEY="..."  # Last.fm
export ROON_BRIDGE_URL="http://localhost:3330"
```

---

## 🎯 Résumé: Qui Appelle Qui

### EurIA
- ✅ haiku_service.py (haïkus)
- ✅ article_service.py (biographies)
- ✅ description_service.py (descriptions)
- ✅ collection_service.py (recherche IA)
- ✅ magazine_generator_service.py (contenu magazine)

### Spotify
- ✅ album_collection_service.py (images)
- ✅ artist_service.py (photos artistes)
- ✅ AlbumDetailDialog (artwork album)
- ✅ MagazinePage (couvertures)

### Last.fm
- ✅ Fallback pour Spotify (get_lastfm_image)
- ✅ Données enrichissement (optional)

### Discogs
- ✅ Synchronisation collection (import)
- ✅ Enrichissement métadonnées

### Roon API
- ✅ Playback (play/pause/next)
- ✅ Zone management
- ✅ Listening history
- ✅ FloatingRoonController (widget contrôle)

### PostgreSQL
- ✅ Toutes les pages (DB cache local)
- ✅ Recherche rapide
- ✅ Historique d'écoute

---

## 🚀 Points d'Amélioration Future

1. **Caching Strategy**
   - [ ] Mettre en cache descriptions EurIA (5 jours TTL)
   - [ ] Mettre en cache images Spotify (10 jours TTL)
   - [ ] Redis pour réponses fréquentes

2. **Rate Limiting**
   - [ ] EurIA: 100 requêtes/heure max
   - [ ] Spotify: Respecter ses limites officielles
   - [ ] Roon: Pas de limite (local)

3. **Error Handling**
   - [ ] Graceful degradation si EurIA unavailable
   - [ ] Fallback Spotify → Last.fm → DB
   - [ ] Retry logic avec exponential backoff

4. **Performance**
   - [ ] Query optimization (DB indexes)
   - [ ] Parallel requests (asyncio)
   - [ ] Streaming responses (SSE) pour génération

5. **Monitoring**
   - [ ] Logs des appels API externes
   - [ ] Alertes si services down
   - [ ] Metrics réponse temps

---

## 📚 Fichiers Référence

- Frontend entrypoint: `frontend/src/main.tsx`
- Backend entrypoint: `backend/app/main.py`
- API Client: `frontend/src/api/client.ts`
- Routes: `backend/app/api/v1/`
- Services: `backend/app/services/`
- Models: `backend/app/models/`

---

**Last Updated:** 7 février 2026  
**Next Review:** après Phase 3 refactoring complet
