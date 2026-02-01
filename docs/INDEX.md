# 📚 Index de la Documentation - AIME v4.3.1

**Date:** 1er février 2026

---

## 🚀 Démarrage Rapide

**Nouveau sur le projet ?** Parcours recommandé :

1. 📖 **[QUICKSTART.md](QUICKSTART.md)** - Installation en 5 minutes
2. 🏗️ **[architecture/ARCHITECTURE-COMPLETE.md](architecture/ARCHITECTURE-COMPLETE.md)** - Vue d'ensemble technique
3. 🗄️ **[architecture/DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)** - Modèle de données (diagramme Mermaid)
4. 🔧 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions aux problèmes ⭐

---

## 📂 Structure Complète

### 📖 Documentation Principale

| Fichier | Description |
|---------|-------------|
| **[API.md](API.md)** | Documentation API REST complète |
| **[QUICKSTART.md](QUICKSTART.md)** | Guide de démarrage rapide |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Résolution problèmes courants |
| **[PROJECT-SUMMARY.md](PROJECT-SUMMARY.md)** | Résumé complet du projet |
| **[STATUS.md](STATUS.md)** | État actuel de l'application |
| **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** | Référence rapide |
| **[INSTALLATION-CHECKLIST.md](INSTALLATION-CHECKLIST.md)** | Checklist installation |
| **[RELIABILITY-GUIDE.md](RELIABILITY-GUIDE.md)** | Guide fiabilité système |
| **[GITHUB-REPO-INFO.md](GITHUB-REPO-INFO.md)** | Info GitHub (SEO, topics) |

### 🏗️ Architecture ⭐ **v4.3.1**

| Fichier | Description |
|---------|-------------|
| **[ARCHITECTURE-COMPLETE.md](architecture/ARCHITECTURE-COMPLETE.md)** | Architecture complète (200+ lignes) |
| **[ARCHITECTURE-SCHEMA.md](architecture/ARCHITECTURE-SCHEMA.md)** | Schémas visuels ASCII art |
| **[DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)** | Modèle relationnel Mermaid ER |

**Contenu Architecture:**
- 3 tiers (Frontend React / Backend FastAPI / DB SQLite)
- 10 tables + 2 tables liaison
- Auto-restart services (service_states)
- Intégration Roon complète
- Flow de contrôle détaillé

### 📖 Guides Utilisateur

| Fichier | Description |
|---------|-------------|
| **[AUTO-RESTART-TEST-GUIDE.md](guides/AUTO-RESTART-TEST-GUIDE.md)** | Test auto-restart services |
| **[TESTING.md](guides/TESTING.md)** | Guide de test complet |

### 🎵 Fonctionnalités

#### Général
| Fichier | Description |
|---------|-------------|
| **[NOUVELLES-FONCTIONNALITES.md](features/NOUVELLES-FONCTIONNALITES.md)** | Nouvelles fonctionnalités v4.0.0 |
| **[JOURNAL-TIMELINE-DOC.md](features/JOURNAL-TIMELINE-DOC.md)** | Vue Journal/Timeline |
| **[LASTFM-IMPORT-TRACKER-DOC.md](features/LASTFM-IMPORT-TRACKER-DOC.md)** | Tracker Last.fm |
| **[ROON-TRACKER-DOC.md](features/ROON-TRACKER-DOC.md)** | Tracker Roon |

#### 🎛️ Intégration Roon ⭐ **v4.3.1**

| Fichier | Description |
|---------|-------------|
| **[ROON-INTEGRATION-COMPLETE.md](features/roon/ROON-INTEGRATION-COMPLETE.md)** | Guide complet (300+ lignes) |
| **[ROON-ZONES-FIX.md](features/roon/ROON-ZONES-FIX.md)** | Fix zones au démarrage |
| **[ROON-BUGS-TRACKING.md](features/roon/ROON-BUGS-TRACKING.md)** | Suivi bugs actifs 🔴 |
| **[ROON-FINAL-STATUS.md](features/roon/ROON-FINAL-STATUS.md)** | Statut final |
| **[ROON-IMPLEMENTATION-COMPLETE.md](features/roon/ROON-IMPLEMENTATION-COMPLETE.md)** | Documentation implémentation |
| **[ROON-IMPLEMENTATION-SUMMARY.md](features/roon/ROON-IMPLEMENTATION-SUMMARY.md)** | Résumé implémentation |
| **[FRONTEND-CHANGES-ROON-PLAYLISTS.md](features/roon/FRONTEND-CHANGES-ROON-PLAYLISTS.md)** | Modifications frontend |

**Bugs Roon Connus:**
- 🔴 Démarrage lectures instable
- 🔴 Désynchronisation état AIME ↔ Roon
- 💡 Workarounds documentés dans ROON-BUGS-TRACKING.md

### 📝 Changelogs

| Fichier | Description |
|---------|-------------|
| **[CHANGELOG.md](changelogs/CHANGELOG.md)** | Journal principal |
| **[CHANGELOG-UI-ENRICHMENT.md](changelogs/CHANGELOG-UI-ENRICHMENT.md)** | Améliorations UI |
| **[CHANGELOG-UNIFIED-ALBUM-DISPLAY.md](changelogs/CHANGELOG-UNIFIED-ALBUM-DISPLAY.md)** | Affichage albums unifié |

### 🔧 Configuration

| Fichier | Description |
|---------|-------------|
| **[TRACKER-CONFIG-OPTIMALE.md](config/TRACKER-CONFIG-OPTIMALE.md)** | Configuration optimale tracker |

### 🐛 Debug et Corrections

| Fichier | Description |
|---------|-------------|
| **[DEBUG-DISCOGS.md](debug/DEBUG-DISCOGS.md)** | Debug intégration Discogs |
| **[EXPLICATION-404-DISCOGS.md](debug/EXPLICATION-404-DISCOGS.md)** | Gestion erreurs 404 Discogs |
| **[CORRECTIONS-SYNC-DISCOGS.md](debug/CORRECTIONS-SYNC-DISCOGS.md)** | Corrections synchronisation |
| **[AMELIORATIONS-SYNC-ENRICHIE.md](debug/AMELIORATIONS-SYNC-ENRICHIE.md)** | Améliorations sync enrichie |
| **[ENRICHISSEMENT-RETROACTIF.md](debug/ENRICHISSEMENT-RETROACTIF.md)** | Enrichissement rétroactif |
| **[LASTFM-IMPORT-CHANGES.md](debug/LASTFM-IMPORT-CHANGES.md)** | Modifications import Last.fm |
| **[LASTFM-IMPORT-COMPLETE.md](debug/LASTFM-IMPORT-COMPLETE.md)** | Import Last.fm complet |
| **[LASTFM-IMPORT-ENHANCEMENT.md](debug/LASTFM-IMPORT-ENHANCEMENT.md)** | Améliorations import Last.fm |
| **[PLAYLIST-CREATION-TROUBLESHOOT.md](debug/PLAYLIST-CREATION-TROUBLESHOOT.md)** | Dépannage playlists |

**Logs disponibles:**
- `app.log` - Logs application
- `backend.log` - Logs backend
- `backend-restart.log` - Logs redémarrages
- `startup.log` - Logs démarrage

### 🔨 Scripts Utilitaires

**Scripts Python de maintenance:**
- `analyze_duplicates.py` - Analyse doublons
- `apply_10min_dedup.py` - Déduplication 10 min
- `check_db_final.py` - Vérification finale DB
- `cleanup_duplicates.py` - Nettoyage doublons
- `find_album_dups.py` - Recherche albums dupliqués
- `merge_duplicate_albums.py` - Fusion albums
- `merge_duplicate_tracks.py` - Fusion tracks
- `test_lastfm_import.py` - Test import Last.fm
- `verify_db.py` - Vérification DB
- `test-playlist-endpoints.sh` - Test endpoints

### 🏗️ Spécifications Techniques

| Fichier | Description |
|---------|-------------|
| **[SPECIFICATION-REACT-REBUILD.md](specs/SPECIFICATION-REACT-REBUILD.md)** | Spécifications rebuild React/TypeScript |

---

## 🎯 Parcours par Thème

### 🆕 Nouveaux Utilisateurs
1. [QUICKSTART.md](QUICKSTART.md)
2. [architecture/ARCHITECTURE-COMPLETE.md](architecture/ARCHITECTURE-COMPLETE.md)
3. [features/NOUVELLES-FONCTIONNALITES.md](features/NOUVELLES-FONCTIONNALITES.md)

### 👨‍💻 Développeurs
1. [architecture/ARCHITECTURE-COMPLETE.md](architecture/ARCHITECTURE-COMPLETE.md)
2. [architecture/DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)
3. [API.md](API.md)
4. [guides/TESTING.md](guides/TESTING.md)

### 🎛️ Intégration Roon
1. [features/roon/ROON-INTEGRATION-COMPLETE.md](features/roon/ROON-INTEGRATION-COMPLETE.md)
2. [features/roon/ROON-ZONES-FIX.md](features/roon/ROON-ZONES-FIX.md)
3. [features/roon/ROON-BUGS-TRACKING.md](features/roon/ROON-BUGS-TRACKING.md) ⚠️

### 🔧 Maintenance
1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. [debug/](debug/)
3. [scripts-util/](scripts-util/)

### 📊 Architecture & Design
1. [architecture/ARCHITECTURE-COMPLETE.md](architecture/ARCHITECTURE-COMPLETE.md)
2. [architecture/ARCHITECTURE-SCHEMA.md](architecture/ARCHITECTURE-SCHEMA.md)
3. [architecture/DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)

---

## 📊 Statistiques Documentation

- **77 fichiers** de documentation
- **10 catégories** thématiques
- **7 guides** Roon détaillés
- **3 schémas** d'architecture
- **1 diagramme** ER complet (Mermaid)
- **900+ lignes** de documentation v4.3.1

---

## 🔗 Liens Rapides

**Essentiels:**
- 🏠 [README principal](../README.md)
- 📁 [STRUCTURE.md](../STRUCTURE.md)
- 🚀 [Démarrage rapide](QUICKSTART.md)

**Architecture:**
- 🏗️ [Architecture complète](architecture/ARCHITECTURE-COMPLETE.md)
- 📊 [Schémas visuels](architecture/ARCHITECTURE-SCHEMA.md)
- 🗄️ [Base de données](architecture/DATABASE-SCHEMA.md)

**Roon:**
- 🎛️ [Guide complet](features/roon/ROON-INTEGRATION-COMPLETE.md)
- 🐛 [Bugs tracking](features/roon/ROON-BUGS-TRACKING.md)
- 🔧 [Fix zones](features/roon/ROON-ZONES-FIX.md)

---

**Version:** 4.3.1  
**Date:** 1er février 2026  
**Auteur:** Patrick Ostertag
