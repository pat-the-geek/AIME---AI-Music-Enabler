# 📊 AIME iOS - Résumé API & Diagrammes

**Version:** 1.0  
**Date:** 9 février 2026  
**Usage:** Référence rapide pour l'implémentation iOS

---

## 🗺️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AIME iOS App                                │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      SwiftUI Interface                          │ │
│  │                                                                  │ │
│  │  TabView:                                                       │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │ │
│  │  │Collection│ Magazine │ Journal  │ Timeline │ Settings │      │ │
│  │  │  View    │  View    │  View    │  View    │  View    │      │ │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ↕                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      ViewModels (MVVM)                          │ │
│  │  @Published var albums: [Album]                                 │ │
│  │  @Published var magazines: [Magazine]                           │ │
│  │  @Published var tracks: [ListeningTrack]                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ↕                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Services (Business Logic)                    │ │
│  │                                                                  │ │
│  │  NetworkService ←→ CacheService ←→ ImageCacheService           │ │
│  │       ↓                 ↓                    ↓                   │ │
│  │   URLSession       CoreData              NSCache + Disk         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ HTTPS/REST
┌─────────────────────────────────────────────────────────────────────┐
│                     AIME Backend (FastAPI)                           │
│                     http://your-server:8000/api/v1                  │
│                                                                       │
│  /collection/*  /magazines/*  /tracking/*  /analytics/*             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📡 Table des API Endpoints

### Priorité 1: Collection (Bibliothèque Discogs)

| Endpoint | Méthode | Description | Cache |
|----------|---------|-------------|-------|
| `/collection/albums` | GET | Liste paginée d'albums | 24h |
| `/collection/albums/{id}` | GET | Détails d'un album | 24h |
| `/collection/artists` | GET | Liste des artistes | 24h |
| `/collection/search` | GET | Recherche textuelle | - |

**Paramètres de pagination:**
- `page` (int): Numéro de page (défaut: 1)
- `per_page` (int): Résultats par page (défaut: 50, max: 100)
- `search` (string): Recherche textuelle
- `support` (string): Filtrage (CD, Vinyl, Digital)
- `sort` (string): Tri (title, artist, year)
- `order` (string): asc / desc

**Exemple de requête:**
```swift
let url = "\(baseURL)/collection/albums?page=1&per_page=50&search=Beatles&support=CD&sort=year&order=desc"
```

---

### Priorité 1: Magazines (5 éditions)

| Endpoint | Méthode | Description | Cache |
|----------|---------|-------------|-------|
| `/magazines/editions` | GET | Liste des 5 derniers magazines | Manuel |
| `/magazines/editions/{id}` | GET | Détails d'une édition | Permanent |
| `/magazines/generate` | GET | Génère un nouveau magazine | - |

**Paramètres:**
- `limit` (int): Nombre de magazines (défaut: 5)

**Structure d'une édition:**
```json
{
  "id": "edition-20260209-120000",
  "generated_at": "2026-02-09T12:00:00Z",
  "pages": [
    {
      "page_number": 1,
      "type": "artist_spotlight",
      "artist": { "name": "...", "image_url": "...", "bio": "..." },
      "albums": [...]
    },
    {
      "page_number": 2,
      "type": "album_spotlight",
      "album": { "title": "...", "long_description": "..." }
    }
  ]
}
```

**Types de pages:**
1. `artist_spotlight` - Artiste + ses albums + haïku
2. `album_spotlight` - Album du jour + description longue
3. `haikus` - 3 albums avec haïkus IA
4. `timeline` - Récapitulatif d'écoutes
5. `playlist` - Thème + albums + description

---

### Priorité 1: Journal d'Écoute

| Endpoint | Méthode | Description | Cache |
|----------|---------|-------------|-------|
| `/tracking/listening-history` | GET | Historique des écoutes | 30min |
| `/tracking/listening-history/{id}/favorite` | POST | Toggle favori | Sync immédiat |

**Paramètres:**
- `page` (int): Numéro de page
- `per_page` (int): Résultats (défaut: 100)
- `from_date` (ISO8601): Date de début
- `to_date` (ISO8601): Date de fin

**Structure d'un track:**
```json
{
  "id": 1001,
  "played_at": "2026-02-09T10:30:00Z",
  "track": {
    "title": "Track Name",
    "artist": "Artist Name",
    "album": "Album Name"
  },
  "album_image_url": "https://...",
  "artist_image_url": "https://...",
  "is_favorite": false,
  "source": "Roon ARC"
}
```

**Body pour toggle favori:**
```json
{
  "is_favorite": true
}
```

---

### Priorité 1: Timeline

| Endpoint | Méthode | Description | Cache |
|----------|---------|-------------|-------|
| `/analytics/timeline` | GET | Timeline des écoutes | 1h |

**Paramètres:**
- `date` (ISO8601): Date à afficher (défaut: aujourd'hui)
- `period` (string): "day" / "week" / "month"

**Structure de réponse:**
```json
{
  "date": "2026-02-09",
  "period": "day",
  "hourly_stats": [
    {
      "hour": 10,
      "tracks_count": 5,
      "albums": [
        {
          "id": 1,
          "title": "Album",
          "artist": "Artist",
          "image_url": "https://...",
          "plays": 3
        }
      ]
    }
  ],
  "daily_total": 42
}
```

---

## 🗄️ Schéma CoreData

### Entité: Album

```
Album
├── id: Int64 (Primary Key)
├── title: String
├── artistNames: String (JSON array)
├── year: Int32
├── support: String (CD, Vinyl, Digital)
├── imageURL: String?
├── spotifyURL: String?
├── discogsURL: String?
├── aiDescription: String?
├── genres: String? (JSON array)
├── label: String?
├── catalogNumber: String?
├── tracksCount: Int32
└── cachedAt: Date
```

**Index:** `id`, `title`, `cachedAt`

---

### Entité: Magazine

```
Magazine
├── id: String (Primary Key, ex: "edition-20260209-120000")
├── generatedAt: Date
├── pagesData: Binary Data (JSON encoded)
└── cachedAt: Date
```

**Index:** `id`, `generatedAt`

---

### Entité: ListeningHistory

```
ListeningHistory
├── id: Int64 (Primary Key)
├── playedAt: Date
├── trackTitle: String
├── artistName: String
├── albumName: String
├── albumImageURL: String?
├── artistImageURL: String?
├── isFavorite: Bool
├── source: String
└── cachedAt: Date
```

**Index:** `id`, `playedAt`, `isFavorite`

---

### Entité: TimelineData

```
TimelineData
├── date: Date (Primary Key)
├── period: String
├── hourlyStatsData: Binary Data (JSON encoded)
├── dailyTotal: Int32
└── cachedAt: Date
```

**Index:** `date`

---

## 🔄 Flux de Données

### 1. Premier Lancement (Cold Start)

```
┌────────────┐
│  App Start │
└──────┬─────┘
       │
       ▼
┌─────────────────┐
│ Check Cache     │ ← CoreData
│ Is Empty?       │
└────┬───────┬────┘
     │ YES   │ NO
     │       │
     ▼       ▼
┌────────┐ ┌─────────────┐
│Network │ │Show Cached  │
│Fetch   │ │Data         │
└────┬───┘ └──────┬──────┘
     │            │
     ▼            ▼
┌─────────────┐ ┌──────────────┐
│Save to      │ │Background    │
│CoreData     │ │Refresh (30s) │
└──────┬──────┘ └──────┬───────┘
       │                │
       └────────┬───────┘
                ▼
       ┌────────────────┐
       │Display in UI   │
       └────────────────┘
```

---

### 2. Pull-to-Refresh

```
┌────────────────┐
│User pulls down │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│Show Spinner    │
└───────┬────────┘
        │
        ▼
┌────────────────────┐
│Check lastSync time │
└──────┬─────────────┘
       │
       ▼
┌────────────────────┐    ┌─────────────┐
│If > threshold      │───▶│Fetch from   │
│(24h for albums)    │    │Backend API  │
└────────────────────┘    └──────┬──────┘
                                 │
                                 ▼
                          ┌──────────────┐
                          │Merge with    │
                          │Local Cache   │
                          └──────┬───────┘
                                 │
                                 ▼
                          ┌──────────────┐
                          │Update UI     │
                          │Hide Spinner  │
                          └──────────────┘
```

---

### 3. Toggle Favori (Offline-First)

```
┌────────────────┐
│User taps ♡     │
└───────┬────────┘
        │
        ▼
┌─────────────────┐
│Update local DB  │ ← Immediate UI feedback
│Set isFavorite   │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│Queue for sync   │ ← Background queue
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│When online:     │
│POST /favorite   │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│On success:      │
│Mark as synced   │
└─────────────────┘
```

---

## ⚡ Stratégies d'Optimisation

### 1. Cache des Images

```swift
// Utilisation de Kingfisher
import Kingfisher

// Dans une vue SwiftUI
AsyncImage(url: URL(string: album.imageURL)) { image in
    image
        .resizable()
        .aspectRatio(contentMode: .fill)
} placeholder: {
    Color.gray.opacity(0.3)
}
.frame(width: 150, height: 150)
.cornerRadius(8)

// Ou avec Kingfisher (recommandé)
KFImage(URL(string: album.imageURL))
    .placeholder { ProgressView() }
    .cacheOriginalImage()
    .fade(duration: 0.25)
    .resizable()
    .frame(width: 150, height: 150)
```

**Configuration Kingfisher:**
```swift
// Dans AppDelegate ou App struct
let cache = ImageCache.default
cache.memoryStorage.config.totalCostLimit = 300 * 1024 * 1024 // 300 MB
cache.diskStorage.config.sizeLimit = 1000 * 1024 * 1024 // 1 GB
cache.diskStorage.config.expiration = .days(7)
```

---

### 2. Pagination Infinie

```swift
struct CollectionView: View {
    @StateObject var viewModel = CollectionViewModel()
    
    var body: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))]) {
                ForEach(viewModel.albums) { album in
                    AlbumCardView(album: album)
                        .onAppear {
                            // Load more when reaching last item
                            if album == viewModel.albums.last {
                                viewModel.loadMore()
                            }
                        }
                }
                
                // Loading indicator
                if viewModel.isLoadingMore {
                    ProgressView()
                }
            }
        }
    }
}
```

---

### 3. Debounce Search

```swift
class CollectionViewModel: ObservableObject {
    @Published var searchText = ""
    @Published var albums: [Album] = []
    
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        // Debounce search: wait 0.5s after user stops typing
        $searchText
            .debounce(for: .milliseconds(500), scheduler: RunLoop.main)
            .removeDuplicates()
            .sink { [weak self] searchText in
                self?.performSearch(searchText)
            }
            .store(in: &cancellables)
    }
    
    private func performSearch(_ text: String) {
        Task {
            albums = try await NetworkService.shared.fetchAlbums(search: text)
        }
    }
}
```

---

## 📊 Indicateurs de Performance

### Objectifs de Cache

| Type | Quantité | Taille Estimée | Durée de Vie |
|------|----------|----------------|--------------|
| Albums (métadonnées) | 5000 | ~5 MB | 24h |
| Albums (images) | 5000 | ~500 MB | 7 jours |
| Magazines | 5 | ~10 MB | Manuel |
| Journal tracks | 1000 | ~1 MB | 30min |
| Timeline | 7 jours | ~500 KB | 1h |
| **TOTAL** | - | **~516 MB** | Variable |

---

### Temps de Réponse Cibles

| Action | Sans Cache | Avec Cache | Objectif |
|--------|------------|------------|----------|
| Afficher collection | 2-5s | <100ms | <500ms |
| Ouvrir magazine | 1-3s | <50ms | <200ms |
| Charger journal | 1-2s | <100ms | <500ms |
| Afficher timeline | 1-2s | <100ms | <500ms |
| Toggle favori | 200ms | 50ms | <100ms |

---

## 🔐 Sécurité & Permissions

### Info.plist Requis

```xml
<!-- Network Security -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
    <!-- Pour serveur local HTTP -->
</dict>

<!-- Background Refresh -->
<key>UIBackgroundModes</key>
<array>
    <string>fetch</string>
    <string>processing</string>
</array>
```

---

### Gestion des Erreurs

```swift
enum NetworkError: LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case serverError(Int)
    case decodingError
    case noInternetConnection
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "URL invalide"
        case .invalidResponse:
            return "Réponse du serveur invalide"
        case .unauthorized:
            return "Non autorisé - Vérifiez votre configuration"
        case .serverError(let code):
            return "Erreur serveur: \(code)"
        case .decodingError:
            return "Erreur de décodage des données"
        case .noInternetConnection:
            return "Pas de connexion Internet"
        }
    }
}
```

---

## 🧪 Tests à Implémenter

### Tests Unitaires

```swift
import XCTest
@testable import AIME

final class NetworkServiceTests: XCTestCase {
    
    func testFetchAlbums() async throws {
        let service = NetworkService.shared
        let response = try await service.fetchAlbums(page: 1, perPage: 10)
        
        XCTAssertGreaterThan(response.items.count, 0)
        XCTAssertEqual(response.page, 1)
    }
    
    func testCacheAlbums() async throws {
        let albums = [
            Album(id: 1, title: "Test", artistNames: ["Artist"], year: 2020)
        ]
        
        await CacheService.shared.cacheAlbums(albums)
        let cached = CacheService.shared.getCachedAlbums()
        
        XCTAssertEqual(cached.count, 1)
    }
}
```

---

### Tests UI

```swift
import XCTest

final class CollectionUITests: XCTestCase {
    
    func testSearchAlbums() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Aller sur l'onglet Collection
        app.tabBars.buttons["Collection"].tap()
        
        // Taper dans la barre de recherche
        let searchField = app.searchFields.firstMatch
        searchField.tap()
        searchField.typeText("Beatles")
        
        // Vérifier que des résultats apparaissent
        let albumCard = app.otherElements["AlbumCard"].firstMatch
        XCTAssertTrue(albumCard.waitForExistence(timeout: 5))
    }
}
```

---

## 📝 Checklist d'Implémentation

### Phase 1: Setup ✅
- [ ] Projet Xcode créé
- [ ] CoreData configuré (4 entités)
- [ ] Info.plist configuré
- [ ] Kingfisher ajouté

### Phase 2: Collection 🎯
- [ ] CollectionView (grille + recherche)
- [ ] CollectionViewModel
- [ ] AlbumDetailView
- [ ] Cache albums (CoreData)
- [ ] Cache images (Kingfisher)

### Phase 3: Magazine 📖
- [ ] MagazineView (TabView)
- [ ] MagazineViewModel
- [ ] MagazinePageView
- [ ] Cache 5 magazines

### Phase 4: Journal ⏰
- [ ] JournalView (liste)
- [ ] JournalViewModel
- [ ] Toggle favoris
- [ ] Cache 1000 tracks

### Phase 5: Timeline 📊
- [ ] TimelineView
- [ ] TimelineViewModel
- [ ] Graphiques (Charts)
- [ ] Cache 7 jours

### Phase 6: Offline & Sync 🔄
- [ ] Background refresh
- [ ] Offline detection
- [ ] Sync queue pour favoris
- [ ] Indicateurs de cache

---

## 🎯 Points d'Attention

### ⚠️ Limitations iOS

1. **Taille du cache**: Limiter à 1 GB total
2. **Background refresh**: iOS décide quand exécuter
3. **Memory**: Limiter le cache mémoire à 300 MB
4. **Battery**: Éviter trop de syncs en arrière-plan

### ✅ Best Practices

1. **Offline-first**: Toujours afficher le cache d'abord
2. **Optimistic UI**: Mettre à jour l'UI immédiatement
3. **Pagination**: Charger par chunks de 50
4. **Images**: Utiliser Kingfisher pour tout
5. **Error handling**: Toujours gérer les erreurs réseau

---

**Version:** 1.0  
**Usage:** Référence rapide pour développement iOS  
**Date:** 9 février 2026
