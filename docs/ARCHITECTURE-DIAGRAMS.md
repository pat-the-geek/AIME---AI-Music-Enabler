```mermaid
graph TB
    subgraph FRONTEND["🎨 Frontend React/TSX"]
        direction LR
        GUI["Pages:
        - Collection.tsx
        - Magazine.tsx
        - Playlists.tsx
        - ArtistArticle.tsx
        - Journal.tsx
        - Analytics.tsx
        - Settings.tsx"]
        
        COMP["Components:
        - AlbumDetailDialog
        - MagazinePage
        - FloatingRoonController
        - ArtistPortraitModal
        - ErrorBoundary"]
        
        API_CLIENT["API Client
        axios"]
        
        GUI --> API_CLIENT
        COMP --> API_CLIENT
    end
    
    subgraph BACKEND["⚙️ Backend FastAPI"]
        direction LR
        
        ROUTES["API Routes /v1:
        /collection/*
        /content/*
        /playback/*
        /analytics/*
        /tracking/*"]
        
        SERVICES["Services Domaine:
        collection/
        content/
        playback/
        analytics/"]
        
        EXTERNAL["Service API Externes:
        external/ai_service.py
        spotify_service.py
        lastfm_service.py
        discogs_service.py
        roon_service.py"]
        
        DB["PostgreSQL DB:
        albums, artists
        magazine_editions
        listening_history
        listening_stats"]
        
        ROUTES --> SERVICES
        SERVICES --> EXTERNAL
        SERVICES --> DB
        EXTERNAL --> DB
    end
    
    subgraph EXTERNAL_APIS["🌐 External APIs"]
        direction TB
        EURIA["🧠 EurIA<br/>Infomaniak AI<br/>
        - Haïkus
        - Articles
        - Descriptions
        - Recherche IA"]
        
        SPOTIFY["🎵 Spotify<br/>
        - Images albums
        - Métadonnées
        - Artistes"]
        
        LASTFM["🎧 Last.fm<br/>
        - Fallback images"]
        
        DISCOGS["📀 Discogs<br/>
        - Métadonnées complètes
        - Synchronisation"]
        
        ROON["🎼 Roon API<br/>via Bridge Node.js<br/>
        - Playback
        - Zones
        - Historique écoute"]
    end
    
    subgraph BRIDGE["🌉 Integration"]
        ROON_BRIDGE["roon-bridge/
        app.js
        (Node.js)
        Port: 3330"]
    end
    
    API_CLIENT -->|HTTP| BACKEND
    
    EXTERNAL -->|API Calls| EURIA
    EXTERNAL -->|API Calls| SPOTIFY
    EXTERNAL -->|API Calls| LASTFM
    EXTERNAL -->|API Calls| DISCOGS
    EXTERNAL -->|HTTP| ROON_BRIDGE
    
    ROON_BRIDGE -->|Roon API| ROON
    
    style FRONTEND fill:#e1f5ff
    style BACKEND fill:#fff3e0
    style EXTERNAL_APIS fill:#f3e5f5
    style BRIDGE fill:#e8f5e9
    style DB fill:#fce4ec

```

### Data Flow Examples

```mermaid
sequenceDiagram
    participant Browser as 🌐 Browser<br/>Collection.tsx
    participant Backend as ⚙️ Backend<br/>API v1
    participant Service as 📦 Services
    participant Spotify as 🎵 Spotify
    participant EurIA as 🧠 EurIA
    participant DB as 💾 Database

    Browser->>Backend: GET /collection/albums<br/>?search=jazz&page=1
    activate Backend
    
    Backend->>DB: SELECT albums WHERE LIKE 'jazz'<br/>LIMIT 30
    DB-->>Backend: [album_1, album_2, ...]
    
    Backend->>Service: enrich_albums(albums)
    activate Service
    
    loop For Each Album
        Service->>Spotify: GET /v1/search?q=artist album
        Spotify-->>Service: image_url, spotify_url
        
        par Parallel AI Enrichment
            Service->>EurIA: "Describe this album..."
            EurIA-->>Service: description_text
        and Get Metadata
            Service->>DB: SELECT enrichment WHERE album_id=X
            DB-->>Service: cached_data
        end
        
        Service->>Service: merge_results()
    end
    
    Service-->>Backend: [enriched_albums]
    deactivate Service
    
    Backend-->>Browser: HTTP 200<br/>{items: [...], total: 500}
    deactivate Backend
    
    Browser->>Browser: render grid<br/>with images & descriptions

```

```mermaid
sequenceDiagram
    participant Browser as 📄 Magazine.tsx
    participant Backend as ⚙️ Backend
    participant Generator as 📾 Magazine Generator
    participant AI as 🧠 EurIA (Streaming)
    participant Spotify as 🎵 Spotify

    Browser->>Backend: POST /magazines/refresh
    activate Backend
    
    Backend->>Generator: generate_new_edition()
    activate Generator
    
    Generator->>Generator: fetch_random_albums(20)
    
    loop For Each Album (Parallel)
        par Generate Haiku (Streaming)
            Generator->>AI: POST /chat/completions<br/>stream=true
            AI->>Browser: SSE: "Autumn leaves..."
        and Fetch Image
            Generator->>Spotify: GET /v1/search
            Spotify-->>Generator: image_url
        and Enrich Data
            Generator->>AI: Generate description<br/>POST stream
            AI-->>Browser: SSE: "This album..."
        end
    end
    
    Generator->>Generator: save_magazine_edition()
    Generator-->>Backend: new_edition_id
    deactivate Generator
    
    Backend-->>Browser: HTTP 200<br/>{edition_id: "...", pages: 32}
    deactivate Backend
    
    Browser->>Browser: Load MagazinePage component

```

```mermaid
sequenceDiagram
    participant UI as 🎮 FloatingRoonController
    participant Backend as ⚙️ Backend<br/>Playback Service
    participant Bridge as 🌉 roon-bridge<br/>Node.js
    participant RoonCore as 🎼 Roon Core<br/>Network

    UI->>Backend: POST /playback/roon/zones<br/>{zone_id: "living_room"}<br/>/play<br/>{uri: "qobuz://album/..."}
    activate Backend
    
    Backend->>Bridge: HTTP POST<br/>http://localhost:3330/zones/living_room/play
    activate Bridge
    
    Bridge->>RoonCore: node-roon-api<br/>instance.playback.play(...)
    RoonCore-->>Bridge: {"status": "playing", track: "..."}
    Bridge-->>Backend: HTTP 200
    deactivate Bridge
    
    Backend-->>UI: HTTP 200<br/>{status: "playing"}
    deactivate Backend
    
    UI->>UI: Update zone status<br/>show playing track
    
    loop Poll Every 2s
        UI->>Backend: GET /playback/roon/zones
        Backend->>Bridge: GET /zones
        Bridge->>RoonCore: Check zone state
        RoonCore-->>Bridge: current track
        Bridge-->>Backend: zone_data
        Backend-->>UI: zone_status
        UI->>UI: Update display
    end

```

### Architecture Layer Diagram

```mermaid
graph TB
    U["👥 Users"]
    
    UI["🎨 User Interface Layer
    - React Components
    - State Management
    - User Events"]
    
    APIC["📡 API Client Layer
    - axios
    - Error Handling
    - Request/Response"]
    
    BE["⚙️ API Gateway Layer
    - FastAPI Routes
    - Input Validation
    - Error Formatting"]
    
    BIZ["📦 Business Logic Layer
    - Collection Services
    - Content Services
    - Playback Services
    - Analytics Services"]
    
    EXT["🌐 External Integration Layer
    - AI Service (EurIA)
    - Spotify Service
    - Last.fm Service
    - Discogs Service
    - Roon Service (Bridge)"]
    
    DATA["💾 Data Layer
    - PostgreSQL
    - Query Builder
    - ORM (SQLAlchemy)"]
    
    EX["🔌 External Systems
    - EurIA API
    - Spotify API
    - Last.fm API
    - Discogs API
    - Roon Core
    - Roon Bridge"]
    
    U -->|Click/Input| UI
    UI -->|HTTP Requests| APIC
    APIC -->|REST API| BE
    BE -->|Route to Handler| BIZ
    BIZ -->|Call Methods| EXT
    BIZ -->|Query/Update| DATA
    EXT -->|API Calls| EX
    EXT -->|Local Cache| DATA
    DATA -->|Cache| EX
    EX -->|Response| EXT
    EXT -->|Enrich/Format| BIZ
    BIZ -->|Response DTO| BE
    BE -->|JSON Response| APIC
    APIC -->|Update State| UI
    UI -->|Render| U
    
    style U fill:#ffe0b2
    style UI fill:#e1f5ff
    style APIC fill:#c8e6c9
    style BE fill:#fff3e0
    style BIZ fill:#f3e5f5
    style EXT fill:#fce4ec
    style DATA fill:#b3e5fc
    style EX fill:#ffccbc

```

---

## 🔁 Common Integration Patterns

### Pattern 1: Simple Data Fetch + Enrich
```
Frontend Page Request
    ↓
Backend Route Handler
    ├─ Query DB (cache)
    ├─ Missing data?
    │  └─ Call External API
    └─ Return enriched data
    ↓
Frontend Render
```
**Used by:** Collection.tsx, Analytics.tsx, Journal.tsx

### Pattern 2: Stream Generation
```
Frontend Action (e.g., "Generate")
    ↓
Backend POST Handler
    ├─ Validate input
    ├─ Start Stream to Frontend
    └─ For Each Item:
       ├─ Call AI/External API
       ├─ Send SSE chunk
       └─ Save to DB
    ↓
Frontend Receive Chunks
    ├─ Display in real-time
    ├─ Accumulate results
    └─ Final refresh
```
**Used by:** Magazine.tsx refresh, Haiku generation

### Pattern 3: Real-time Control
```
Frontend User Action
    ↓
Backend Handler (Playback)
    ├─ Translate to Bridge command
    ├─ HTTP call to Bridge
    ├─ Bridge calls Roon Core
    └─ Return status
    ↓
Frontend Poll Loop
    ├─ GET /zones every 2s
    ├─ Update local state
    └─ Render controls
```
**Used by:** FloatingRoonController, Playback controls

---
