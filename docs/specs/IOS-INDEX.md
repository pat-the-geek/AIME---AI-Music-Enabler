# 📱 AIME iOS Application - Index de Documentation

**Version:** 1.0  
**Date:** 9 février 2026  
**Status:** Spécifications complètes pour génération dans Xcode

---

## 📚 Documents Disponibles

### 1. 📋 [IOS-APP-SPECIFICATIONS.md](./IOS-APP-SPECIFICATIONS.md)
**Document Principal - Spécifications Complètes**

Contenu:
- ✅ Architecture iOS complète (MVVM + Combine)
- ✅ API Endpoints détaillés avec exemples
- ✅ Modèles CoreData (4 entités)
- ✅ Interface SwiftUI (5 vues principales)
- ✅ Stratégie de cache offline
- ✅ NetworkService & CacheService
- ✅ Estimations de développement

**À utiliser pour:** Comprendre l'architecture globale et tous les détails techniques.

---

### 2. 🛠️ [IOS-XCODE-SETUP-GUIDE.md](./IOS-XCODE-SETUP-GUIDE.md)
**Guide Pratique - Configuration Xcode Étape par Étape**

Contenu:
- ✅ Création du projet Xcode
- ✅ Configuration Info.plist
- ✅ Ajout de Kingfisher (SPM)
- ✅ Configuration CoreData (4 entités)
- ✅ Structure des dossiers
- ✅ Code de base à copier-coller
- ✅ Dépannage

**À utiliser pour:** Suivre les étapes de configuration initiale dans Xcode.

---

### 3. 📊 [IOS-API-QUICK-REFERENCE.md](./IOS-API-QUICK-REFERENCE.md)
**Référence Rapide - API & Diagrammes**

Contenu:
- ✅ Table des API endpoints
- ✅ Diagrammes de flux de données
- ✅ Schémas CoreData visuels
- ✅ Stratégies d'optimisation
- ✅ Exemples de code
- ✅ Checklist d'implémentation

**À utiliser pour:** Référence rapide pendant le développement.

---

## 🎯 Parcours Recommandé

### Pour démarrer immédiatement dans Xcode:

1. **Lire d'abord:** [IOS-XCODE-SETUP-GUIDE.md](./IOS-XCODE-SETUP-GUIDE.md)
   - Suivre les étapes 1 à 7
   - Configurer le projet Xcode
   - Tester la connexion au backend

2. **Consulter ensuite:** [IOS-APP-SPECIFICATIONS.md](./IOS-APP-SPECIFICATIONS.md)
   - Comprendre l'architecture MVVM
   - Voir les ViewModels à implémenter
   - Étudier la stratégie de cache

3. **Garder sous la main:** [IOS-API-QUICK-REFERENCE.md](./IOS-API-QUICK-REFERENCE.md)
   - Référence pendant le développement
   - API endpoints
   - Exemples de code

---

## 🏗️ Architecture Résumée

```
AIME iOS App (SwiftUI + CoreData)
│
├── Views (5 onglets)
│   ├── CollectionView - Bibliothèque Discogs
│   ├── MagazineView - 5 magazines éditoriaux
│   ├── JournalView - Historique d'écoute
│   ├── TimelineView - Timeline horaire
│   └── SettingsView - Configuration
│
├── ViewModels (MVVM)
│   ├── CollectionViewModel
│   ├── MagazineViewModel
│   ├── JournalViewModel
│   └── TimelineViewModel
│
├── Services
│   ├── NetworkService - API calls (URLSession)
│   ├── CacheService - CoreData persistence
│   └── ImageCacheService - Kingfisher
│
└── CoreData
    ├── Album (5000 albums)
    ├── Magazine (5 magazines)
    ├── ListeningHistory (1000 tracks)
    └── TimelineData (7 jours)
```

---

## 📡 API Backend Requises

### Base URL
```
http://your-server:8000/api/v1
```

### Endpoints Essentiels

| Endpoint | Méthode | Usage | Cache |
|----------|---------|-------|-------|
| `/collection/albums` | GET | Liste d'albums | 24h |
| `/collection/albums/{id}` | GET | Détails album | 24h |
| `/magazines/editions` | GET | 5 magazines | Manuel |
| `/tracking/listening-history` | GET | Journal | 30min |
| `/tracking/listening-history/{id}/favorite` | POST | Toggle favori | Sync |
| `/analytics/timeline` | GET | Timeline | 1h |

Voir [IOS-API-QUICK-REFERENCE.md](./IOS-API-QUICK-REFERENCE.md) pour tous les détails.

---

## 💾 Capacités de Cache Offline

### Données Mises en Cache

1. **Bibliothèque Discogs**: Tous les albums (mise à jour 1x/jour)
2. **5 Magazines**: Dernières éditions (refresh manuel)
3. **Journal**: 1000 derniers tracks (sync toutes les 30min)
4. **Timeline**: 7 derniers jours (sync toutes les heures)

### Taille Totale Estimée
- Métadonnées: ~6 MB
- Images: ~500 MB
- **Total: ~516 MB**

### Mode Offline
- ✅ Lecture complète des données en cache
- ✅ Toggle favoris (sync en background)
- ✅ Recherche dans le cache local
- ✅ Navigation complète sans connexion

---

## 🚀 Phases de Développement

### Phase 1: Setup (1-2 jours)
- Configuration projet Xcode
- CoreData + Info.plist
- NetworkService basique

### Phase 2: Collection (2-3 jours)
- CollectionView + grille d'albums
- Recherche et filtres
- AlbumDetailView
- Cache local

### Phase 3: Magazine (2-3 jours)
- MagazineView avec pages défilables
- Cache des 5 magazines
- Navigation entre éditions

### Phase 4: Journal (1-2 jours)
- JournalView avec liste
- Toggle favoris
- Cache 1000 tracks

### Phase 5: Timeline (1-2 jours)
- TimelineView avec graphiques
- Visualisation horaire
- Cache 7 jours

### Phase 6: Cache & Offline (2-3 jours)
- CacheService complet
- Background refresh
- Sync queue

### Phase 7: Polish (2-3 jours)
- Tests unitaires & UI
- Optimisations
- Documentation

**Total: 11-18 jours**

---

## 🛠️ Technologies Utilisées

### Frameworks iOS
- **SwiftUI** - Interface utilisateur
- **Combine** - Programmation réactive
- **CoreData** - Persistance locale
- **URLSession** - Networking
- **BackgroundTasks** - Refresh en arrière-plan

### Dépendances Externes
- **Kingfisher 7.10+** - Cache et chargement d'images

### Prérequis
- **Xcode 15.0+**
- **iOS 16.0+**
- **Swift 5.9+**
- **Backend AIME** fonctionnel

---

## 📋 Checklist Rapide

### Configuration Initiale
- [ ] Projet Xcode créé (SwiftUI + CoreData)
- [ ] Info.plist configuré (Network, Background Modes)
- [ ] Kingfisher ajouté via Swift Package Manager
- [ ] 4 entités CoreData créées
- [ ] Structure de dossiers organisée

### Implémentation
- [ ] TabView avec 5 onglets
- [ ] NetworkService avec async/await
- [ ] CacheService avec CoreData
- [ ] CollectionView + ViewModel
- [ ] MagazineView + ViewModel
- [ ] JournalView + ViewModel
- [ ] TimelineView + ViewModel
- [ ] SettingsView

### Tests & Validation
- [ ] Connexion au backend testée
- [ ] Cache fonctionne offline
- [ ] Images se chargent avec Kingfisher
- [ ] Pagination infinie fonctionne
- [ ] Toggle favoris sync en background
- [ ] Background refresh activé

---

## 📞 Support

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

## 🎨 Captures d'Écran de Référence

Les captures d'écran de l'interface web AIME sont disponibles dans:
```
/docs/screenshots/Screen captures/
```

À utiliser comme référence pour le design iOS:
- Collection - Albums.png
- Journal.png
- TimeLine.png
- Magazine 1.png, Magazine 2.png, Magazine 3.png

---

## ✅ Validation

### Avant de Commencer
- [ ] Backend AIME démarré et accessible
- [ ] Test de l'API avec curl ou Postman
- [ ] Xcode 15.0+ installé
- [ ] Compte développeur Apple configuré

### Après Configuration
- [ ] App compile sans erreur (⌘B)
- [ ] App se lance dans le simulateur (⌘R)
- [ ] Settings permet de configurer l'URL serveur
- [ ] Premier album s'affiche dans Collection

### Après Implémentation
- [ ] Toutes les vues fonctionnent
- [ ] Cache fonctionne offline
- [ ] Images se chargent rapidement
- [ ] Aucune fuite mémoire
- [ ] Tests unitaires passent

---

## 📊 Indicateurs de Succès

### Performance
- ✅ Affichage collection: <500ms
- ✅ Chargement magazine: <200ms
- ✅ Scroll fluide: 60 FPS
- ✅ Cache hit rate: >80%

### Qualité
- ✅ 0 crash sur 100 lancements
- ✅ Mode offline complet fonctionnel
- ✅ Sync favoris 100% fiable
- ✅ Images toujours en cache

### Expérience Utilisateur
- ✅ Interface intuitive (TabBar claire)
- ✅ Feedback visuel immédiat
- ✅ Pas de blocage UI
- ✅ Erreurs gérées élégamment

---

## 🎯 Prochaines Étapes

### Après avoir lu ce document:

1. **Suivre** [IOS-XCODE-SETUP-GUIDE.md](./IOS-XCODE-SETUP-GUIDE.md) pour créer le projet
2. **Implémenter** les ViewModels selon [IOS-APP-SPECIFICATIONS.md](./IOS-APP-SPECIFICATIONS.md)
3. **Référencer** [IOS-API-QUICK-REFERENCE.md](./IOS-API-QUICK-REFERENCE.md) pendant le développement
4. **Tester** à chaque phase complétée
5. **Itérer** selon les retours utilisateurs

---

## 📝 Notes Importantes

### Configuration Serveur
- L'URL du serveur est configurable dans SettingsView
- Par défaut: `http://localhost:8000`
- Pour réseau local: `http://192.168.1.x:8000`
- Pour production: `https://your-domain.com`

### Sécurité
- NSAppTransportSecurity configuré pour HTTP local
- En production: utiliser HTTPS obligatoirement
- Pas de stockage de credentials dans l'app (API publique)

### Cache
- Images: 1 GB max sur disque
- Métadonnées: 100 MB max
- Auto-nettoyage après 7 jours
- Manuel via SettingsView

---

**Version:** 1.0  
**Auteur:** Spécifications iOS pour AIME  
**Date:** 9 février 2026  
**Contact:** Voir README.md principal du projet AIME

---

**🚀 Prêt à commencer? Ouvrez [IOS-XCODE-SETUP-GUIDE.md](./IOS-XCODE-SETUP-GUIDE.md)!**
