# 🛠️ Guide de Configuration Xcode pour AIME iOS

**Version:** 1.0  
**Date:** 9 février 2026  
**Plateforme:** Xcode 15.0+ / iOS 16.0+

Ce document fournit les instructions détaillées pour configurer un projet Xcode et générer l'application iOS AIME.

---

## 📋 Table des Matières

1. [Création du Projet Xcode](#1-création-du-projet-xcode)
2. [Configuration du Projet](#2-configuration-du-projet)
3. [Ajout des Dépendances](#3-ajout-des-dépendances)
4. [Configuration CoreData](#4-configuration-coredata)
5. [Structure des Fichiers](#5-structure-des-fichiers)
6. [Configuration Info.plist](#6-configuration-infoplist)
7. [Build & Run](#7-build--run)

---

## 1. Création du Projet Xcode

### Étape 1.1: Nouveau Projet

1. Ouvrir **Xcode**
2. Sélectionner **File > New > Project** (⌘⇧N)
3. Choisir **iOS** > **App**
4. Cliquer **Next**

### Étape 1.2: Configuration Initiale

Remplir les champs suivants:

| Champ | Valeur |
|-------|---------|
| **Product Name** | AIME |
| **Team** | (Votre équipe de développement) |
| **Organization Identifier** | com.yourcompany.aime |
| **Bundle Identifier** | com.yourcompany.aime |
| **Interface** | SwiftUI |
| **Language** | Swift |
| **Storage** | ✅ Use Core Data |
| **Include Tests** | ✅ Coché |

Cliquer **Next** puis choisir l'emplacement du projet.

---

## 2. Configuration du Projet

### Étape 2.1: General Settings

Dans l'onglet **General** du projet:

| Setting | Valeur |
|---------|---------|
| **Display Name** | AIME |
| **Minimum Deployments** | iOS 16.0 |
| **Supported Destinations** | iPhone, iPad |
| **Supports Multiple Windows** | Non |
| **Device Orientation** | Portrait, Landscape |

### Étape 2.2: Capabilities

Dans l'onglet **Signing & Capabilities**:

1. Cliquer **+ Capability**
2. Ajouter **Background Modes**
   - ✅ Background fetch
   - ✅ Background processing

### Étape 2.3: Build Settings

Dans **Build Settings**, rechercher et configurer:

| Setting | Valeur |
|---------|---------|
| **Swift Language Version** | Swift 5 |
| **Optimization Level** | Debug: None, Release: Optimize for Speed |
| **Enable Bitcode** | Non |

---

## 3. Ajout des Dépendances

### Étape 3.1: Swift Package Manager

1. Sélectionner le projet dans le navigateur
2. Aller dans l'onglet **Package Dependencies**
3. Cliquer sur **+** (en bas)

### Étape 3.2: Ajouter Kingfisher

1. Dans le champ de recherche, entrer:
   ```
   https://github.com/onevcat/Kingfisher.git
   ```
2. Cliquer **Add Package**
3. Sélectionner **Kingfisher** dans la liste
4. Règle de version: **Up to Next Major Version** > 7.10.0
5. Cliquer **Add Package**

**Kingfisher** sera utilisé pour:
- Cache d'images en mémoire (NSCache)
- Cache d'images sur disque
- Chargement asynchrone des images
- Placeholder automatiques

---

## 4. Configuration CoreData

### Étape 4.1: Ouvrir le Modèle CoreData

1. Dans le navigateur de projet, ouvrir **AIME.xcdatamodeld**
2. Le Data Model Editor s'ouvre

### Étape 4.2: Créer l'Entité "Album"

1. Cliquer sur **Add Entity** (en bas)
2. Nommer l'entité **Album**
3. Ajouter les attributs suivants (cliquer **+** dans la section Attributes):

| Attribute Name | Type | Optional | Default |
|----------------|------|----------|---------|
| id | Integer 64 | Non | 0 |
| title | String | Non | - |
| artistNames | String | Non | - |
| year | Integer 32 | Non | 0 |
| support | String | Non | CD |
| imageURL | String | Oui | - |
| spotifyURL | String | Oui | - |
| discogsURL | String | Oui | - |
| aiDescription | String | Oui | - |
| genres | String | Oui | - |
| label | String | Oui | - |
| catalogNumber | String | Oui | - |
| tracksCount | Integer 32 | Non | 0 |
| cachedAt | Date | Non | - |

4. Dans l'onglet **Data Model Inspector** (⌥⌘4), configurer:
   - **Class > Codegen**: Manual/None (nous allons créer nos propres extensions)

### Étape 4.3: Créer l'Entité "Magazine"

1. Ajouter une nouvelle entité **Magazine**
2. Attributs:

| Attribute Name | Type | Optional |
|----------------|------|----------|
| id | String | Non |
| generatedAt | Date | Non |
| pagesData | Binary Data | Non |
| cachedAt | Date | Non |

### Étape 4.4: Créer l'Entité "ListeningHistory"

1. Ajouter une nouvelle entité **ListeningHistory**
2. Attributs:

| Attribute Name | Type | Optional |
|----------------|------|----------|
| id | Integer 64 | Non |
| playedAt | Date | Non |
| trackTitle | String | Non |
| artistName | String | Non |
| albumName | String | Non |
| albumImageURL | String | Oui |
| artistImageURL | String | Oui |
| isFavorite | Boolean | Non |
| source | String | Non |
| cachedAt | Date | Non |

### Étape 4.5: Créer l'Entité "TimelineData"

1. Ajouter une nouvelle entité **TimelineData**
2. Attributs:

| Attribute Name | Type | Optional |
|----------------|------|----------|
| date | Date | Non |
| period | String | Non |
| hourlyStatsData | Binary Data | Non |
| dailyTotal | Integer 32 | Non |
| cachedAt | Date | Non |

### Étape 4.6: Sauvegarder

Sauvegarder (⌘S) le fichier AIME.xcdatamodeld.

---

## 5. Structure des Fichiers

### Étape 5.1: Créer la Structure de Dossiers

Dans le navigateur de projet, créer les groupes suivants (clic droit > New Group):

```
AIME/
├── App/
│   ├── AIMEApp.swift (déjà existant)
│   └── ContentView.swift (déjà existant)
├── Models/
│   ├── Album.swift
│   ├── Magazine.swift
│   ├── ListeningTrack.swift
│   └── Timeline.swift
├── ViewModels/
│   ├── CollectionViewModel.swift
│   ├── MagazineViewModel.swift
│   ├── JournalViewModel.swift
│   └── TimelineViewModel.swift
├── Views/
│   ├── Collection/
│   │   ├── CollectionView.swift
│   │   ├── AlbumCardView.swift
│   │   └── AlbumDetailView.swift
│   ├── Magazine/
│   │   ├── MagazineView.swift
│   │   └── MagazinePageView.swift
│   ├── Journal/
│   │   ├── JournalView.swift
│   │   └── JournalRowView.swift
│   ├── Timeline/
│   │   ├── TimelineView.swift
│   │   └── HourlyStatsView.swift
│   └── Settings/
│       └── SettingsView.swift
├── Services/
│   ├── NetworkService.swift
│   ├── CacheService.swift
│   └── ImageCacheService.swift
├── Utilities/
│   ├── Extensions.swift
│   └── Constants.swift
└── Resources/
    ├── Assets.xcassets
    └── AIME.xcdatamodeld
```

### Étape 5.2: Créer les Fichiers Swift

Pour chaque fichier listé ci-dessus, faire:
1. Clic droit sur le groupe > **New File**
2. Choisir **Swift File**
3. Nommer selon la structure

---

## 6. Configuration Info.plist

### Étape 6.1: Ouvrir Info.plist

1. Dans le navigateur, sélectionner **Info.plist**
2. Clic droit > **Open As** > **Source Code**

### Étape 6.2: Ajouter les Configurations

Remplacer le contenu avec:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- App Configuration -->
    <key>CFBundleDevelopmentRegion</key>
    <string>$(DEVELOPMENT_LANGUAGE)</string>
    
    <key>CFBundleDisplayName</key>
    <string>AIME</string>
    
    <key>CFBundleExecutable</key>
    <string>$(EXECUTABLE_NAME)</string>
    
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
    
    <key>CFBundlePackageType</key>
    <string>$(PRODUCT_BUNDLE_PACKAGE_TYPE)</string>
    
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    
    <key>CFBundleVersion</key>
    <string>1</string>
    
    <!-- UI Configuration -->
    <key>UIApplicationSceneManifest</key>
    <dict>
        <key>UIApplicationSupportsMultipleScenes</key>
        <false/>
        <key>UISceneConfigurations</key>
        <dict>
            <key>UIWindowSceneSessionRoleApplication</key>
            <array>
                <dict>
                    <key>UISceneConfigurationName</key>
                    <string>Default Configuration</string>
                    <key>UISceneDelegateClassName</key>
                    <string>$(PRODUCT_MODULE_NAME).SceneDelegate</string>
                </dict>
            </array>
        </dict>
    </dict>
    
    <!-- Supported Orientations -->
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    
    <key>UISupportedInterfaceOrientations~ipad</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationPortraitUpsideDown</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    
    <!-- Network Security -->
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
    
    <!-- Background Modes -->
    <key>UIBackgroundModes</key>
    <array>
        <string>fetch</string>
        <string>processing</string>
    </array>
    
    <!-- Background Task Identifiers -->
    <key>BGTaskSchedulerPermittedIdentifiers</key>
    <array>
        <string>com.yourcompany.aime.refresh</string>
    </array>
    
    <!-- Required device capabilities -->
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>armv7</string>
    </array>
    
    <!-- Launch Screen -->
    <key>UILaunchScreen</key>
    <dict>
        <key>UIColorName</key>
        <string>LaunchScreenBackground</string>
        <key>UIImageName</key>
        <string>LaunchIcon</string>
    </dict>
</dict>
</plist>
```

**Note:** Remplacer `com.yourcompany.aime` par votre identifiant de bundle réel.

---

## 7. Build & Run

### Étape 7.1: Vérifier la Configuration

1. Sélectionner le schéma **AIME** (en haut)
2. Choisir un simulateur (ex: iPhone 15 Pro)
3. Vérifier qu'il n'y a pas d'erreurs de compilation

### Étape 7.2: Build

1. Appuyer sur **⌘B** pour compiler
2. Résoudre les éventuelles erreurs de compilation

### Étape 7.3: Run

1. Appuyer sur **⌘R** pour lancer l'app
2. L'app devrait s'ouvrir dans le simulateur

### Étape 7.4: Configuration du Serveur

Au premier lancement:
1. L'app ouvre automatiquement sur **SettingsView**
2. Entrer l'URL de votre serveur AIME:
   - Local: `http://localhost:8000`
   - Réseau: `http://192.168.1.x:8000`
   - Production: `https://your-domain.com`
3. Appuyer sur **Enregistrer**

### Étape 7.5: Test de Connexion

1. Aller sur l'onglet **Collection**
2. Tirer vers le bas pour rafraîchir (pull-to-refresh)
3. Les albums devraient se charger depuis le serveur

---

## 📚 Code de Base à Copier

### AIMEApp.swift

```swift
import SwiftUI

@main
struct AIMEApp: App {
    let persistenceController = PersistenceController.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
        }
    }
}
```

### PersistenceController.swift (nouveau fichier)

```swift
import CoreData

struct PersistenceController {
    static let shared = PersistenceController()
    
    let container: NSPersistentContainer
    
    init(inMemory: Bool = false) {
        container = NSPersistentContainer(name: "AIME")
        
        if inMemory {
            container.persistentStoreDescriptions.first?.url = URL(fileURLWithPath: "/dev/null")
        }
        
        container.loadPersistentStores { description, error in
            if let error = error {
                fatalError("Unable to load persistent stores: \(error)")
            }
        }
        
        container.viewContext.automaticallyMergesChangesFromParent = true
    }
}
```

### ContentView.swift

```swift
import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            CollectionView()
                .tabItem {
                    Label("Collection", systemImage: "music.note.list")
                }
            
            MagazineView()
                .tabItem {
                    Label("Magazines", systemImage: "book.fill")
                }
            
            JournalView()
                .tabItem {
                    Label("Journal", systemImage: "clock.fill")
                }
            
            TimelineView()
                .tabItem {
                    Label("Timeline", systemImage: "chart.bar.fill")
                }
            
            SettingsView()
                .tabItem {
                    Label("Réglages", systemImage: "gear")
                }
        }
    }
}

#Preview {
    ContentView()
}
```

### Constants.swift

```swift
import Foundation

struct Constants {
    // API Configuration
    static let defaultBaseURL = "http://localhost:8000/api/v1"
    static let apiTimeout: TimeInterval = 30
    
    // Cache Configuration
    static let cacheMaxAge: TimeInterval = 86400 // 24 hours
    static let maxCachedAlbums = 5000
    static let maxCachedMagazines = 5
    static let maxCachedTracks = 1000
    static let maxCachedTimelineDays = 7
    
    // Pagination
    static let defaultPageSize = 50
    static let journalPageSize = 100
    
    // Background Refresh
    static let backgroundRefreshTaskID = "com.yourcompany.aime.refresh"
    static let minBackgroundRefreshInterval: TimeInterval = 3600 // 1 hour
    
    // UserDefaults Keys
    struct Keys {
        static let serverURL = "serverURL"
        static let cacheEnabled = "cacheEnabled"
        static let autoRefresh = "autoRefresh"
        static let lastSyncAlbums = "lastSync_albums"
        static let lastSyncMagazines = "lastSync_magazines"
        static let lastSyncJournal = "lastSync_journal"
        static let lastSyncTimeline = "lastSync_timeline"
    }
}
```

---

## 🧪 Test Rapide

### Script de Test Backend

Avant de lancer l'app, vérifier que le backend est accessible:

```bash
# Terminal
curl http://localhost:8000/api/v1/collection/albums?page=1&per_page=5
```

Si le backend répond correctement, vous verrez un JSON avec des albums.

### Test dans Xcode

1. Lancer l'app (⌘R)
2. Ouvrir la console Xcode (⌘⇧Y)
3. Observer les logs de NetworkService
4. Vérifier que les requêtes réussissent

---

## ❓ Dépannage

### Problème 1: "Cannot connect to backend"

**Solution:**
- Vérifier que le backend AIME est démarré
- Vérifier l'URL dans Settings
- Vérifier NSAppTransportSecurity dans Info.plist

### Problème 2: "CoreData error"

**Solution:**
- Supprimer l'app du simulateur
- Clean Build Folder (⌘⇧K)
- Rebuild (⌘B)

### Problème 3: "Package dependency failed"

**Solution:**
- File > Packages > Reset Package Caches
- File > Packages > Update to Latest Package Versions

### Problème 4: "Signing error"

**Solution:**
- Aller dans Signing & Capabilities
- Sélectionner votre équipe de développement
- Ou cocher "Automatically manage signing"

---

## 📋 Checklist Finale

Avant de considérer le projet prêt:

- [ ] Projet Xcode créé avec SwiftUI + CoreData
- [ ] Info.plist configuré (Network, Background Modes)
- [ ] Kingfisher ajouté via SPM
- [ ] 4 entités CoreData créées (Album, Magazine, ListeningHistory, TimelineData)
- [ ] Structure de dossiers organisée
- [ ] TabView configurée avec 5 onglets
- [ ] Settings permet de configurer URL du serveur
- [ ] Test de connexion au backend réussi
- [ ] Premier album chargé et affiché

---

## 🎯 Prochaines Étapes

Après cette configuration:

1. Implémenter chaque ViewModel (voir IOS-APP-SPECIFICATIONS.md)
2. Créer les Views selon les maquettes
3. Implémenter CacheService complet
4. Ajouter la gestion offline
5. Tests unitaires et UI

---

## 📚 Ressources

### Documentation Apple

- [SwiftUI Tutorials](https://developer.apple.com/tutorials/swiftui)
- [CoreData Programming Guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CoreData/)
- [URLSession](https://developer.apple.com/documentation/foundation/urlsession)
- [Background Tasks](https://developer.apple.com/documentation/backgroundtasks)

### AIME Backend

- Swagger API: `http://localhost:8000/docs`
- Architecture: `docs/ARCHITECTURE-GUI-AND-APIS.md`
- Spécifications iOS complètes: `docs/specs/IOS-APP-SPECIFICATIONS.md`

---

**Version:** 1.0  
**Auteur:** Guide de configuration Xcode pour AIME iOS  
**Date:** 9 février 2026
