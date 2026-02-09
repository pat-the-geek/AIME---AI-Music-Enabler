# 📱 AIME iOS Application - Spécifications Techniques

**Version:** 1.0  
**Date:** 9 février 2026  
**Plateforme:** iOS 16.0+  
**Framework:** SwiftUI + Swift 5.9+  
**Architecture:** MVVM + Combine

---

## 📋 Vue d'ensemble

Application iOS native pour AIME (AI Music Enabler) permettant de consulter et gérer sa collection musicale, consulter des magazines musicaux, suivre son journal d'écoute et sa timeline, avec capacités de mise en cache offline.

### Fonctionnalités principales

1. **Collection Discogs** - Consultation de la bibliothèque musicale avec recherche et filtrage
2. **Magazines** - Lecture de 5 magazines éditoriaux générés automatiquement
3. **Journal d'Écoute** - Historique chronologique des écoutes avec favoris
4. **Timeline** - Visualisation temporelle des écoutes par heure/jour
5. **Mode Hors-Ligne** - Mise en cache locale pour consultation sans connexion

---

## 🏗️ Architecture iOS

```
┌─────────────────────────────────────────────────────────────────┐
│                         AIME iOS App                             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    SwiftUI Views                          │   │
│  │  ├─ CollectionView                                        │   │
│  │  ├─ MagazineView (5 magazines)                           │   │
│  │  ├─ JournalView                                           │   │
│  │  ├─ TimelineView                                          │   │
│  │  └─ SettingsView                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↕                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ViewModels (MVVM)                      │   │
│  │  ├─ CollectionViewModel                                   │   │
│  │  ├─ MagazineViewModel                                     │   │
│  │  ├─ JournalViewModel                                      │   │
│  │  └─ TimelineViewModel                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↕                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Services Layer                         │   │
│  │  ├─ NetworkService (URLSession + Combine)                │   │
│  │  ├─ CacheService (CoreData)                              │   │
│  │  ├─ ImageCacheService (NSCache + Disk)                   │   │
│  │  └─ SyncService (Background refresh)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↕                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Data Layer                             │   │
│  │  ├─ CoreData Stack (Persistent Storage)                  │   │
│  │  ├─ UserDefaults (Settings, Last Sync)                   │   │
│  │  └─ Keychain (API Credentials)                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↕
         ┌──────────────────────────────────────┐
         │   AIME Backend API (FastAPI)          │
         │   http://your-server:8000/api/v1/*   │
         └──────────────────────────────────────┘
```

---

## 🔌 API Endpoints à Intégrer

### Base URL
```swift
let baseURL = "http://your-server:8000/api/v1"
```

### 1. Collection / Discogs Library

#### GET `/collection/albums`
**Description:** Liste paginée des albums de la collection  
**Paramètres:**
- `page` (Int, optionnel): Numéro de page (défaut: 1)
- `per_page` (Int, optionnel): Résultats par page (défaut: 50)
- `search` (String, optionnel): Recherche textuelle
- `support` (String, optionnel): Filtrage par support (CD, Vinyl, Digital)
- `sort` (String, optionnel): Tri (title, artist, year)
- `order` (String, optionnel): Ordre (asc, desc)

**Réponse:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Album Title",
      "artist_names": ["Artist Name"],
      "year": 2020,
      "support": "CD",
      "image_url": "https://...",
      "spotify_url": "https://open.spotify.com/...",
      "ai_description": "Description générée par IA...",
      "genres": ["Rock", "Alternative"],
      "label": "Label Name",
      "tracks_count": 12
    }
  ],
  "total": 500,
  "page": 1,
  "per_page": 50,
  "total_pages": 10
}
```

**Cache Strategy:** 
- Cache local: ✅ Oui (24h)
- Offline access: ✅ Oui
- Auto-refresh: En arrière-plan (1x/jour)

---

#### GET `/collection/albums/{id}`
**Description:** Détails complets d'un album  
**Réponse:**
```json
{
  "id": 1,
  "title": "Album Title",
  "artists": [
    {
      "id": 10,
      "name": "Artist Name",
      "image_url": "https://..."
    }
  ],
  "year": 2020,
  "support": "CD",
  "image_url": "https://...",
  "spotify_url": "https://...",
  "discogs_url": "https://...",
  "ai_description": "...",
  "genres": ["Rock"],
  "label": "Label",
  "catalog_number": "CAT-123",
  "barcode": "1234567890123",
  "tracks": [
    {
      "position": "A1",
      "title": "Track Name",
      "duration": "3:45"
    }
  ]
}
```

**Cache Strategy:**
- Cache local: ✅ Oui
- Images: Cache séparé avec NSCache + Disk

---

### 2. Magazines

#### GET `/magazines/editions`
**Description:** Liste des 5 derniers magazines générés  
**Paramètres:**
- `limit` (Int): Nombre de magazines (défaut: 5)

**Réponse:**
```json
{
  "editions": [
    {
      "id": "edition-20260209-120000",
      "generated_at": "2026-02-09T12:00:00Z",
      "pages": [
        {
          "page_number": 1,
          "type": "artist_spotlight",
          "artist": {
            "name": "Artist Name",
            "image_url": "https://...",
            "bio": "..."
          },
          "albums": [
            {
              "id": 1,
              "title": "Album",
              "image_url": "https://...",
              "haiku": "Beautiful autumn notes..."
            }
          ]
        },
        {
          "page_number": 2,
          "type": "album_spotlight",
          "album": {
            "id": 2,
            "title": "Featured Album",
            "artist": "Artist",
            "image_url": "https://...",
            "long_description": "Description longue de 2000+ caractères..."
          }
        }
      ]
    }
  ]
}
```

**Cache Strategy:**
- Cache local: ✅ Oui (5 magazines les plus récents)
- Images: Cache agressif (rarement changent)
- Refresh: Manuel via pull-to-refresh

---

#### GET `/magazines/editions/{id}`
**Description:** Détails d'une édition spécifique de magazine

**Cache Strategy:**
- Cache local: ✅ Oui
- Offline: ✅ Complet

---

### 3. Journal d'Écoute

#### GET `/tracking/listening-history`
**Description:** Historique chronologique des écoutes  
**Paramètres:**
- `page` (Int): Numéro de page
- `per_page` (Int): Résultats par page (défaut: 100)
- `from_date` (String ISO8601, optionnel): Date de début
- `to_date` (String ISO8601, optionnel): Date de fin

**Réponse:**
```json
{
  "items": [
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
  ],
  "total": 5000,
  "page": 1
}
```

**Cache Strategy:**
- Cache local: ✅ Oui (derniers 1000 tracks)
- Offline: ✅ Lecture seule
- Sync: Incrémental (fetch nouveaux depuis last_sync_date)

---

#### POST `/tracking/listening-history/{id}/favorite`
**Description:** Marquer/démarquer un track comme favori  
**Body:**
```json
{
  "is_favorite": true
}
```

**Cache Strategy:**
- Update local immédiat
- Sync avec serveur en background

---

### 4. Timeline

#### GET `/analytics/timeline`
**Description:** Timeline des écoutes par heure et jour  
**Paramètres:**
- `date` (String ISO8601): Date à afficher (défaut: aujourd'hui)
- `period` (String): "day" ou "week" ou "month"

**Réponse:**
```json
{
  "date": "2026-02-09",
  "period": "day",
  "hourly_stats": [
    {
      "hour": 0,
      "tracks_count": 0,
      "albums": []
    },
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

**Cache Strategy:**
- Cache local: ✅ Oui (7 derniers jours)
- Offline: ✅ Oui
- Refresh: Auto (toutes les heures si app active)

---

### 5. Services / Synchronisation

#### GET `/services/sync-status`
**Description:** Statut de synchronisation Discogs/Last.fm  
**Réponse:**
```json
{
  "discogs": {
    "last_sync": "2026-02-09T06:00:00Z",
    "total_albums": 500,
    "status": "synced"
  },
  "lastfm": {
    "last_sync": "2026-02-09T10:35:00Z",
    "total_tracks": 5000,
    "status": "active"
  }
}
```

---

## 📦 Modèles de Données iOS (CoreData)

### Album Entity
```swift
@objc(Album)
public class Album: NSManagedObject {
    @NSManaged public var id: Int64
    @NSManaged public var title: String
    @NSManaged public var artistNames: String // JSON array
    @NSManaged public var year: Int32
    @NSManaged public var support: String
    @NSManaged public var imageURL: String?
    @NSManaged public var spotifyURL: String?
    @NSManaged public var aiDescription: String?
    @NSManaged public var genres: String? // JSON array
    @NSManaged public var label: String?
    @NSManaged public var tracksCount: Int32
    @NSManaged public var cachedAt: Date
}
```

### Magazine Entity
```swift
@objc(Magazine)
public class Magazine: NSManagedObject {
    @NSManaged public var id: String
    @NSManaged public var generatedAt: Date
    @NSManaged public var pagesData: Data // JSON encoded
    @NSManaged public var cachedAt: Date
}
```

### ListeningHistory Entity
```swift
@objc(ListeningHistory)
public class ListeningHistory: NSManagedObject {
    @NSManaged public var id: Int64
    @NSManaged public var playedAt: Date
    @NSManaged public var trackTitle: String
    @NSManaged public var artistName: String
    @NSManaged public var albumName: String
    @NSManaged public var albumImageURL: String?
    @NSManaged public var artistImageURL: String?
    @NSManaged public var isFavorite: Bool
    @NSManaged public var source: String
    @NSManaged public var cachedAt: Date
}
```

### TimelineData Entity
```swift
@objc(TimelineData)
public class TimelineData: NSManagedObject {
    @NSManaged public var date: Date
    @NSManaged public var period: String
    @NSManaged public var hourlyStatsData: Data // JSON encoded
    @NSManaged public var dailyTotal: Int32
    @NSManaged public var cachedAt: Date
}
```

---

## 🎨 Interface Utilisateur (SwiftUI)

### Navigation Structure
```
TabView
├─ CollectionView (Bibliothèque)
│  └─ AlbumDetailView
├─ MagazineView (Magazines)
│  └─ MagazinePageView
├─ JournalView (Journal)
├─ TimelineView (Timeline)
└─ SettingsView (Paramètres)
```

---

### 1. CollectionView

**Design:** Grille d'albums avec pochettes

**Composants:**
```swift
struct CollectionView: View {
    @StateObject var viewModel = CollectionViewModel()
    @State private var searchText = ""
    @State private var selectedSupport: Support? = nil
    
    var body: some View {
        NavigationStack {
            ScrollView {
                // Search Bar
                SearchBar(text: $searchText)
                
                // Filter Chips
                FilterChipsView(selectedSupport: $selectedSupport)
                
                // Albums Grid
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))]) {
                    ForEach(viewModel.albums) { album in
                        NavigationLink(destination: AlbumDetailView(album: album)) {
                            AlbumCardView(album: album)
                        }
                    }
                }
            }
            .navigationTitle("Ma Collection")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { viewModel.refresh() }) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .refreshable {
                await viewModel.refresh()
            }
        }
    }
}
```

**Features:**
- ✅ Recherche en temps réel
- ✅ Filtrage par support (CD, Vinyl, Digital, Tous)
- ✅ Tri (Titre, Artiste, Année)
- ✅ Pull-to-refresh
- ✅ Pagination infinie
- ✅ Mode offline (données en cache)

---

### 2. MagazineView

**Design:** Lecteur de magazine avec pages défilables

**Composants:**
```swift
struct MagazineView: View {
    @StateObject var viewModel = MagazineViewModel()
    @State private var selectedMagazineIndex = 0
    @State private var currentPage = 0
    
    var body: some View {
        NavigationStack {
            VStack {
                // Magazine Selector (5 magazines)
                Picker("Édition", selection: $selectedMagazineIndex) {
                    ForEach(0..<viewModel.magazines.count, id: \.self) { index in
                        Text("Magazine #\(index + 1)")
                    }
                }
                .pickerStyle(.segmented)
                .padding()
                
                // Page Viewer
                TabView(selection: $currentPage) {
                    ForEach(viewModel.currentMagazine?.pages ?? [], id: \.pageNumber) { page in
                        MagazinePageView(page: page)
                            .tag(page.pageNumber)
                    }
                }
                .tabViewStyle(.page(indexDisplayMode: .always))
                
                // Page Indicator
                Text("Page \(currentPage + 1) sur \(viewModel.currentMagazine?.pages.count ?? 0)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .navigationTitle("Magazines")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { viewModel.refresh() }) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
        }
    }
}
```

**Features:**
- ✅ 5 magazines en cache
- ✅ Navigation entre pages avec swipe
- ✅ Affichage textes + images + haïkus
- ✅ Mode offline complet
- ✅ Pull-to-refresh pour récupérer nouveaux magazines

---

### 3. JournalView

**Design:** Liste chronologique inversée

**Composants:**
```swift
struct JournalView: View {
    @StateObject var viewModel = JournalViewModel()
    
    var body: some View {
        NavigationStack {
            List {
                ForEach(viewModel.tracks) { track in
                    JournalRowView(track: track)
                        .onTapGesture {
                            viewModel.toggleFavorite(track)
                        }
                }
                
                // Load More
                if viewModel.hasMore {
                    ProgressView()
                        .onAppear {
                            viewModel.loadMore()
                        }
                }
            }
            .navigationTitle("Journal")
            .refreshable {
                await viewModel.refresh()
            }
        }
    }
}

struct JournalRowView: View {
    let track: ListeningTrack
    
    var body: some View {
        HStack(spacing: 12) {
            // Album Image
            AsyncImage(url: URL(string: track.albumImageURL ?? "")) { image in
                image.resizable()
            } placeholder: {
                Color.gray
            }
            .frame(width: 60, height: 60)
            .cornerRadius(8)
            
            // Track Info
            VStack(alignment: .leading, spacing: 4) {
                Text(track.trackTitle)
                    .font(.headline)
                Text(track.artistName)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                Text(track.playedAt, style: .time)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Favorite Button
            Image(systemName: track.isFavorite ? "heart.fill" : "heart")
                .foregroundColor(track.isFavorite ? .red : .gray)
        }
        .padding(.vertical, 4)
    }
}
```

**Features:**
- ✅ Liste chronologique inversée (plus récent en haut)
- ✅ Images album + artiste
- ✅ Bouton favori avec sync background
- ✅ Pagination infinie
- ✅ Mode offline (cache local des 1000 derniers tracks)

---

### 4. TimelineView

**Design:** Visualisation par heure avec graphiques

**Composants:**
```swift
struct TimelineView: View {
    @StateObject var viewModel = TimelineViewModel()
    @State private var selectedDate = Date()
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Date Picker
                    DatePicker("Date", selection: $selectedDate, displayedComponents: .date)
                        .datePickerStyle(.graphical)
                        .onChange(of: selectedDate) { newDate in
                            viewModel.loadTimeline(for: newDate)
                        }
                    
                    // Daily Summary
                    SummaryCardView(total: viewModel.dailyTotal)
                    
                    // Hourly Timeline
                    ForEach(0..<24, id: \.self) { hour in
                        if let stats = viewModel.hourlyStats[hour], stats.tracksCount > 0 {
                            HourlyStatsView(hour: hour, stats: stats)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Timeline")
            .refreshable {
                await viewModel.refresh()
            }
        }
    }
}

struct HourlyStatsView: View {
    let hour: Int
    let stats: HourlyStats
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("\(hour):00 - \(hour + 1):00")
                .font(.headline)
            
            Text("\(stats.tracksCount) écoutes")
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack {
                    ForEach(stats.albums) { album in
                        AlbumThumbnailView(album: album)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}
```

**Features:**
- ✅ Visualisation par heure
- ✅ Calendrier pour navigation
- ✅ Stats quotidiennes
- ✅ Albums joués par heure
- ✅ Cache 7 derniers jours

---

### 5. SettingsView

**Design:** Paramètres de l'app

**Composants:**
```swift
struct SettingsView: View {
    @AppStorage("serverURL") private var serverURL = "http://localhost:8000"
    @AppStorage("cacheEnabled") private var cacheEnabled = true
    @AppStorage("autoRefresh") private var autoRefresh = true
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Serveur") {
                    TextField("URL du serveur AIME", text: $serverURL)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                }
                
                Section("Cache") {
                    Toggle("Activer le cache", isOn: $cacheEnabled)
                    Toggle("Rafraîchissement auto", isOn: $autoRefresh)
                    
                    Button("Vider le cache") {
                        CacheService.shared.clearCache()
                    }
                    .foregroundColor(.red)
                }
                
                Section("Informations") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Taille du cache")
                        Spacer()
                        Text(CacheService.shared.getCacheSize())
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Paramètres")
        }
    }
}
```

---

## 💾 Stratégie de Cache

### Objectif
Permettre une consultation complète hors-ligne de:
1. **Bibliothèque Discogs** (tous les albums)
2. **5 Magazines** (dernières éditions)
3. **Timeline** (7 derniers jours)
4. **Journal** (1000 derniers tracks)

---

### CacheService Implementation

```swift
class CacheService {
    static let shared = CacheService()
    
    private let persistentContainer: NSPersistentContainer
    private let imageCache = NSCache<NSString, UIImage>()
    
    // MARK: - Cache Management
    
    func cacheAlbums(_ albums: [Album]) async {
        // Save to CoreData
        let context = persistentContainer.viewContext
        for album in albums {
            let entity = AlbumEntity(context: context)
            entity.id = Int64(album.id)
            entity.title = album.title
            entity.artistNames = album.artistNames.joined(separator: ",")
            entity.year = Int32(album.year)
            entity.support = album.support
            entity.imageURL = album.imageURL
            entity.cachedAt = Date()
        }
        try? context.save()
    }
    
    func getCachedAlbums() -> [Album] {
        let context = persistentContainer.viewContext
        let request: NSFetchRequest<AlbumEntity> = AlbumEntity.fetchRequest()
        
        // Return cached if < 24h old
        request.predicate = NSPredicate(format: "cachedAt > %@", Date().addingTimeInterval(-86400) as NSDate)
        
        guard let entities = try? context.fetch(request) else { return [] }
        return entities.map { $0.toAlbum() }
    }
    
    // MARK: - Image Cache
    
    func cacheImage(_ image: UIImage, for url: String) {
        imageCache.setObject(image, forKey: url as NSString)
        // Also save to disk
        saveImageToDisk(image, url: url)
    }
    
    func getCachedImage(for url: String) -> UIImage? {
        // Check memory cache first
        if let cached = imageCache.object(forKey: url as NSString) {
            return cached
        }
        // Check disk cache
        return loadImageFromDisk(url: url)
    }
    
    // MARK: - Sync Strategy
    
    func shouldRefresh(entity: String) -> Bool {
        let lastSync = UserDefaults.standard.object(forKey: "lastSync_\(entity)") as? Date ?? Date.distantPast
        
        switch entity {
        case "albums":
            return Date().timeIntervalSince(lastSync) > 86400 // 24h
        case "magazines":
            return Date().timeIntervalSince(lastSync) > 3600 // 1h
        case "journal":
            return Date().timeIntervalSince(lastSync) > 1800 // 30min
        case "timeline":
            return Date().timeIntervalSince(lastSync) > 3600 // 1h
        default:
            return true
        }
    }
    
    func updateLastSync(entity: String) {
        UserDefaults.standard.set(Date(), forKey: "lastSync_\(entity)")
    }
}
```

---

### Background Refresh

```swift
// AppDelegate or App struct
func application(_ application: UIApplication, performFetchWithCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
    
    Task {
        let networkService = NetworkService.shared
        
        // Refresh in background (WiFi only)
        if CacheService.shared.shouldRefresh(entity: "albums") {
            let albums = try? await networkService.fetchAlbums()
            if let albums = albums {
                await CacheService.shared.cacheAlbums(albums)
                CacheService.shared.updateLastSync(entity: "albums")
            }
        }
        
        completionHandler(.newData)
    }
}
```

---

## 🌐 NetworkService Implementation

```swift
import Foundation
import Combine

class NetworkService {
    static let shared = NetworkService()
    
    private let baseURL: String
    private let session: URLSession
    
    init() {
        self.baseURL = UserDefaults.standard.string(forKey: "serverURL") ?? "http://localhost:8000/api/v1"
        
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.waitsForConnectivity = true
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - Albums
    
    func fetchAlbums(page: Int = 1, perPage: Int = 50, search: String? = nil) async throws -> AlbumsResponse {
        var components = URLComponents(string: "\(baseURL)/collection/albums")!
        var queryItems = [
            URLQueryItem(name: "page", value: "\(page)"),
            URLQueryItem(name: "per_page", value: "\(perPage)")
        ]
        
        if let search = search, !search.isEmpty {
            queryItems.append(URLQueryItem(name: "search", value: search))
        }
        
        components.queryItems = queryItems
        
        let request = URLRequest(url: components.url!)
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
        
        return try JSONDecoder().decode(AlbumsResponse.self, from: data)
    }
    
    func fetchAlbumDetails(id: Int) async throws -> Album {
        let url = URL(string: "\(baseURL)/collection/albums/\(id)")!
        let request = URLRequest(url: url)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(Album.self, from: data)
    }
    
    // MARK: - Magazines
    
    func fetchMagazines(limit: Int = 5) async throws -> MagazinesResponse {
        var components = URLComponents(string: "\(baseURL)/magazines/editions")!
        components.queryItems = [URLQueryItem(name: "limit", value: "\(limit)")]
        
        let request = URLRequest(url: components.url!)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(MagazinesResponse.self, from: data)
    }
    
    // MARK: - Journal
    
    func fetchListeningHistory(page: Int = 1, perPage: Int = 100) async throws -> ListeningHistoryResponse {
        var components = URLComponents(string: "\(baseURL)/tracking/listening-history")!
        components.queryItems = [
            URLQueryItem(name: "page", value: "\(page)"),
            URLQueryItem(name: "per_page", value: "\(perPage)")
        ]
        
        let request = URLRequest(url: components.url!)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(ListeningHistoryResponse.self, from: data)
    }
    
    func toggleFavorite(trackId: Int, isFavorite: Bool) async throws {
        let url = URL(string: "\(baseURL)/tracking/listening-history/\(trackId)/favorite")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["is_favorite": isFavorite]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }
    }
    
    // MARK: - Timeline
    
    func fetchTimeline(date: Date, period: String = "day") async throws -> TimelineResponse {
        let dateFormatter = ISO8601DateFormatter()
        let dateString = dateFormatter.string(from: date)
        
        var components = URLComponents(string: "\(baseURL)/analytics/timeline")!
        components.queryItems = [
            URLQueryItem(name: "date", value: dateString),
            URLQueryItem(name: "period", value: period)
        ]
        
        let request = URLRequest(url: components.url!)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(TimelineResponse.self, from: data)
    }
}

enum NetworkError: Error {
    case invalidURL
    case invalidResponse
    case decodingError
}
```

---

## 📱 Configuration Xcode

### Info.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>UIApplicationSceneManifest</key>
    <dict>
        <key>UIApplicationSupportsMultipleScenes</key>
        <false/>
    </dict>
    
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>localhost</key>
            <dict>
                <key>NSIncludesSubdomains</key>
                <true/>
                <key>NSTemporaryExceptionAllowsInsecureHTTPLoads</key>
                <true/>
            </dict>
        </dict>
    </dict>
    
    <key>UIBackgroundModes</key>
    <array>
        <string>fetch</string>
        <string>processing</string>
    </array>
    
    <key>BGTaskSchedulerPermittedIdentifiers</key>
    <array>
        <string>com.aime.refresh</string>
    </array>
</dict>
</plist>
```

---

### Package Dependencies (Swift Package Manager)

Dans Xcode: File > Add Packages...

1. **Kingfisher** (Image loading & caching)
   - URL: `https://github.com/onevcat/Kingfisher.git`
   - Version: 7.10.0+

2. **SwiftUI Charts** (pour Timeline)
   - Intégré dans iOS 16+ (pas de package externe)

---

### CoreData Model (AIME.xcdatamodeld)

Créer les entités suivantes dans Xcode:

1. **Album**
   - Attributes: id (Integer 64), title (String), artistNames (String), year (Integer 32), support (String), imageURL (String), spotifyURL (String), aiDescription (String), genres (String), label (String), tracksCount (Integer 32), cachedAt (Date)

2. **Magazine**
   - Attributes: id (String), generatedAt (Date), pagesData (Binary Data), cachedAt (Date)

3. **ListeningHistory**
   - Attributes: id (Integer 64), playedAt (Date), trackTitle (String), artistName (String), albumName (String), albumImageURL (String), artistImageURL (String), isFavorite (Boolean), source (String), cachedAt (Date)

4. **TimelineData**
   - Attributes: date (Date), period (String), hourlyStatsData (Binary Data), dailyTotal (Integer 32), cachedAt (Date)

---

## 🧪 Tests à Implémenter

### Unit Tests

```swift
import XCTest
@testable import AIME

class NetworkServiceTests: XCTestCase {
    
    func testFetchAlbums() async throws {
        let service = NetworkService.shared
        let response = try await service.fetchAlbums(page: 1, perPage: 10)
        
        XCTAssertGreaterThan(response.items.count, 0)
        XCTAssertEqual(response.page, 1)
        XCTAssertEqual(response.per_page, 10)
    }
    
    func testCacheService() async {
        let albums = [
            Album(id: 1, title: "Test Album", artistNames: ["Test Artist"], year: 2020, support: "CD")
        ]
        
        await CacheService.shared.cacheAlbums(albums)
        let cached = CacheService.shared.getCachedAlbums()
        
        XCTAssertEqual(cached.count, 1)
        XCTAssertEqual(cached[0].title, "Test Album")
    }
}
```

---

## 📝 Documentation pour Xcode

### README.md (à placer dans le projet Xcode)

```markdown
# AIME iOS App

Application iOS pour consulter votre collection musicale AIME.

## Configuration

1. Cloner le repo
2. Ouvrir `AIME.xcodeproj`
3. Aller dans Settings > Serveur et configurer l'URL de votre serveur AIME
4. Build & Run (⌘R)

## Prérequis

- Xcode 15.0+
- iOS 16.0+
- Swift 5.9+
- Serveur AIME en cours d'exécution

## Architecture

- **SwiftUI** pour l'interface
- **Combine** pour la réactivité
- **CoreData** pour le cache local
- **URLSession** pour le réseau

## Features

- ✅ Collection Discogs avec recherche
- ✅ 5 Magazines éditoriaux
- ✅ Journal d'écoute avec favoris
- ✅ Timeline par heure
- ✅ Mode offline complet

## Cache

L'app met en cache automatiquement:
- Tous les albums (24h)
- 5 derniers magazines (refresh manuel)
- 1000 derniers tracks du journal (30min)
- Timeline des 7 derniers jours (1h)

## Contact

Patrick Ostertag - AIME Project
```

---

## 🚀 Étapes de Développement Recommandées

### Phase 1: Configuration de Base (1-2 jours)
1. ✅ Créer nouveau projet Xcode (SwiftUI)
2. ✅ Configurer CoreData avec les 4 entités
3. ✅ Implémenter NetworkService basique
4. ✅ Tester connexion avec backend

### Phase 2: Collection View (2-3 jours)
1. ✅ Implémenter CollectionView avec grille
2. ✅ Intégrer API `/collection/albums`
3. ✅ Ajouter recherche et filtres
4. ✅ Implémenter AlbumDetailView
5. ✅ Ajouter cache local

### Phase 3: Magazine View (2-3 jours)
1. ✅ Implémenter MagazineView avec TabView
2. ✅ Intégrer API `/magazines/editions`
3. ✅ Créer MagazinePageView
4. ✅ Cache des 5 magazines

### Phase 4: Journal View (1-2 jours)
1. ✅ Implémenter JournalView avec List
2. ✅ Intégrer API `/tracking/listening-history`
3. ✅ Ajouter toggle favoris
4. ✅ Cache 1000 derniers tracks

### Phase 5: Timeline View (1-2 jours)
1. ✅ Implémenter TimelineView
2. ✅ Intégrer API `/analytics/timeline`
3. ✅ Ajouter visualisations avec Charts
4. ✅ Cache 7 derniers jours

### Phase 6: Cache & Offline (2-3 jours)
1. ✅ Finaliser CacheService
2. ✅ Implémenter ImageCache
3. ✅ Ajouter background refresh
4. ✅ Gérer états offline/online

### Phase 7: Polish & Tests (2-3 jours)
1. ✅ Tests unitaires
2. ✅ Tests UI
3. ✅ Optimisations performance
4. ✅ Documentation

---

## 📊 Estimation Totale

**Durée estimée:** 11-18 jours de développement  
**Complexité:** Moyenne  
**Dépendances:** Backend AIME fonctionnel

---

## 📞 Support & Documentation

### Documentation Backend AIME
- API Swagger: `http://localhost:8000/docs`
- Architecture: `/docs/ARCHITECTURE-GUI-AND-APIS.md`

### Ressources iOS
- SwiftUI: https://developer.apple.com/documentation/swiftui
- CoreData: https://developer.apple.com/documentation/coredata
- Combine: https://developer.apple.com/documentation/combine

---

**Version:** 1.0  
**Auteur:** Spécifications pour projet iOS AIME  
**Date:** 9 février 2026
