# 📱 AIME iOS Application Specifications

Ce dossier contient les spécifications complètes pour développer une application iOS native basée sur l'API AIME.

## 📚 Documents Disponibles

| Document | Taille | Description |
|----------|--------|-------------|
| **[IOS-VISUAL-SUMMARY.md](./IOS-VISUAL-SUMMARY.md)** ⭐ | 18 KB | Vue d'ensemble complète du projet avec statistiques |
| **[IOS-INDEX.md](./IOS-INDEX.md)** | 9 KB | Index de navigation entre les documents |
| **[IOS-APP-SPECIFICATIONS.md](./IOS-APP-SPECIFICATIONS.md)** | 37 KB | Spécifications techniques détaillées |
| **[IOS-XCODE-SETUP-GUIDE.md](./IOS-XCODE-SETUP-GUIDE.md)** | 17 KB | Guide configuration Xcode étape par étape |
| **[IOS-API-QUICK-REFERENCE.md](./IOS-API-QUICK-REFERENCE.md)** | 21 KB | Référence rapide API & diagrammes |

**Total:** 102 KB de documentation technique

---

## 🚀 Démarrage Rapide

### 1. Vue d'Ensemble (5 min)
Lire **[IOS-VISUAL-SUMMARY.md](./IOS-VISUAL-SUMMARY.md)** pour comprendre:
- Étendue du projet
- Architecture globale
- Documents disponibles
- Phases de développement

### 2. Configuration Xcode (1-2h)
Suivre **[IOS-XCODE-SETUP-GUIDE.md](./IOS-XCODE-SETUP-GUIDE.md)**:
- Créer projet Xcode
- Configurer CoreData (4 entités)
- Ajouter dépendances (Kingfisher)
- Configurer Info.plist
- Tester connexion backend

### 3. Implémentation (11-18 jours)
Référencer **[IOS-APP-SPECIFICATIONS.md](./IOS-APP-SPECIFICATIONS.md)**:
- Phase 1: Setup
- Phase 2: Collection
- Phase 3: Magazines
- Phase 4: Journal
- Phase 5: Timeline
- Phase 6: Cache & Offline
- Phase 7: Polish & Tests

### 4. Référence Continue
Garder ouvert **[IOS-API-QUICK-REFERENCE.md](./IOS-API-QUICK-REFERENCE.md)** pour:
- Endpoints API
- Exemples de code
- Diagrammes de flux
- Optimisations

---

## 🎯 Fonctionnalités iOS

### ✅ Capacités de Cache Offline

1. **Bibliothèque Discogs Complète**
   - 5,000 albums en cache local
   - Métadonnées + Images
   - Mise à jour automatique (24h)

2. **5 Magazines Éditoriaux**
   - Cache permanent
   - Refresh manuel via pull-to-refresh
   - ~10 MB par magazine

3. **Timeline des Écoutes**
   - 7 derniers jours en cache
   - Refresh automatique (1h)
   - Visualisation horaire

4. **Journal d'Écoute**
   - 1,000 derniers tracks
   - Toggle favoris offline
   - Sync automatique

**Total Cache:** ~516 MB

---

## 🏗️ Architecture Technique

```
AIME iOS App
├── SwiftUI Views (5 onglets)
│   ├── CollectionView - Bibliothèque
│   ├── MagazineView - Magazines
│   ├── JournalView - Journal
│   ├── TimelineView - Timeline
│   └── SettingsView - Configuration
│
├── ViewModels (MVVM)
│   └── @Published avec Combine
│
├── Services
│   ├── NetworkService (URLSession)
│   ├── CacheService (CoreData)
│   └── ImageCacheService (Kingfisher)
│
└── CoreData (4 entités)
    ├── Album
    ├── Magazine
    ├── ListeningHistory
    └── TimelineData
```

---

## 📡 API Backend

### Base URL
```
http://your-server:8000/api/v1
```

### Endpoints Principaux

| Endpoint | Méthode | Usage |
|----------|---------|-------|
| `/collection/albums` | GET | Liste albums |
| `/collection/albums/{id}` | GET | Détails album |
| `/magazines/editions` | GET | 5 magazines |
| `/tracking/listening-history` | GET | Journal |
| `/tracking/listening-history/{id}/favorite` | POST | Toggle favori |
| `/analytics/timeline` | GET | Timeline |

Voir **[IOS-API-QUICK-REFERENCE.md](./IOS-API-QUICK-REFERENCE.md)** pour détails complets.

---

## 💻 Prérequis

### Développement
- **Xcode:** 15.0+
- **iOS:** 16.0+
- **Swift:** 5.9+
- **macOS:** 13.0+ (Ventura)

### Backend
- **AIME Backend:** Fonctionnel et accessible
- **URL:** http://localhost:8000 ou réseau local
- **API:** Testée avec curl ou Postman

### Dépendances
- **Kingfisher:** 7.10+ (image caching)
- Ajouté via Swift Package Manager

---

## 📊 Contenu des Spécifications

### Code Swift Fourni
- **ViewModels:** 4 complets
- **Views:** 13 SwiftUI complètes
- **Services:** 2 complets (Network, Cache)
- **Models:** 4 entités CoreData
- **Utilities:** Constants, Extensions
- **Total:** ~2,000 lignes de code

### Documentation API
- **Endpoints:** 7 documentés
- **Paramètres:** 25+ détaillés
- **Réponses JSON:** 7 exemples
- **Code examples:** 15 snippets

### Diagrammes
- **Architecture:** 1 diagramme complet
- **Flux de données:** 3 diagrammes
- **CoreData:** 1 schéma visuel
- **Navigation:** 2 diagrammes

---

## 🎓 Pour les Développeurs

### Nouveaux sur iOS?

1. Commencer par la **[Vue d'ensemble](./IOS-VISUAL-SUMMARY.md)**
2. Lire les **[Spécifications](./IOS-APP-SPECIFICATIONS.md)** section par section
3. Suivre le **[Guide Xcode](./IOS-XCODE-SETUP-GUIDE.md)** étape par étape
4. Copier-coller les exemples de code
5. Adapter selon vos besoins

### Expérimentés?

1. Parcourir la **[Référence API](./IOS-API-QUICK-REFERENCE.md)**
2. Créer le projet avec le **[Guide Xcode](./IOS-XCODE-SETUP-GUIDE.md)**
3. Implémenter selon les **[Spécifications](./IOS-APP-SPECIFICATIONS.md)**
4. Utiliser le code fourni comme base

---

## 🧪 Tests & Validation

### Tests Unitaires
```swift
// NetworkService
func testFetchAlbums() async throws
func testFetchMagazines() async throws
func testToggleFavorite() async throws

// CacheService
func testCacheAlbums() async
func testGetCachedAlbums()
func testShouldRefresh()
```

### Tests UI
```swift
// CollectionView
func testSearchAlbums()
func testFilterBySupport()
func testAlbumDetails()

// JournalView
func testToggleFavorite()
func testLoadMore()
```

Voir **[IOS-APP-SPECIFICATIONS.md](./IOS-APP-SPECIFICATIONS.md)** pour exemples complets.

---

## 📈 Estimation de Développement

| Phase | Durée | Livrable |
|-------|-------|----------|
| Setup | 1-2 jours | Projet Xcode configuré |
| Collection | 2-3 jours | Bibliothèque complète |
| Magazine | 2-3 jours | Lecteur de magazines |
| Journal | 1-2 jours | Journal avec favoris |
| Timeline | 1-2 jours | Timeline horaire |
| Cache & Offline | 2-3 jours | Mode offline complet |
| Polish & Tests | 2-3 jours | App production-ready |
| **TOTAL** | **11-18 jours** | **App iOS complète** |

---

## 🎯 Objectifs de Performance

### Temps de Réponse
- Affichage collection: **<500ms**
- Chargement magazine: **<200ms**
- Scroll fluide: **60 FPS**
- Cache hit rate: **>80%**

### Qualité
- 0 crash sur 100 lancements
- Mode offline 100% fonctionnel
- Sync favoris fiable
- Images toujours disponibles

---

## 📞 Support & Ressources

### Backend AIME
- **API Documentation:** http://localhost:8000/docs
- **Architecture:** `/docs/ARCHITECTURE-GUI-AND-APIS.md`
- **README:** `/README.md`

### Documentation Apple
- **SwiftUI:** https://developer.apple.com/documentation/swiftui
- **CoreData:** https://developer.apple.com/documentation/coredata
- **Combine:** https://developer.apple.com/documentation/combine

### Dépendances
- **Kingfisher:** https://github.com/onevcat/Kingfisher

---

## ✅ Validation Finale

### Avant de Commencer
- [ ] Backend AIME accessible
- [ ] API testée avec curl
- [ ] Xcode 15.0+ installé
- [ ] Compte développeur Apple

### Après Configuration
- [ ] Projet compile (⌘B)
- [ ] App se lance (⌘R)
- [ ] Settings configuré
- [ ] Premier album s'affiche

### Après Implémentation
- [ ] 5 vues fonctionnelles
- [ ] Cache offline complet
- [ ] Images chargées rapidement
- [ ] Tests unitaires passent
- [ ] 0 fuite mémoire

---

## 🚀 Commencer Maintenant

```bash
# 1. Lire la vue d'ensemble
open docs/specs/IOS-VISUAL-SUMMARY.md

# 2. Suivre le guide Xcode
open docs/specs/IOS-XCODE-SETUP-GUIDE.md

# 3. Créer le projet
# (Ouvrir Xcode et suivre les étapes)

# 4. Tester la connexion backend
curl http://localhost:8000/api/v1/collection/albums?page=1&per_page=5
```

---

## 📝 Historique

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 9 février 2026 | Création des spécifications complètes |

---

**Version:** 1.0  
**Auteur:** Spécifications iOS pour AIME  
**Date:** 9 février 2026  
**Status:** ✅ Complet et Prêt

---

**🎯 Objectif:** Permettre le développement d'une application iOS native AIME avec capacités offline complètes pour la bibliothèque Discogs, 5 magazines, la timeline et le journal.

**📱 Résultat:** Une app iOS moderne, performante et offline-first en 11-18 jours de développement.
