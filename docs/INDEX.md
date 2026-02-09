# 📚 Index de la Documentation - AIME v4.6.3

**Date:** 9 février 2026  
**Dernière réorganisation:** 9 février 2026

---

## 🚀 Démarrage Rapide

**Nouveau sur le projet ?** Parcours recommandé :

1. 📖 **[README.md](README.md)** - Présentation générale
2. 🚀 **[guides/utilisateur/QUICKSTART.md](guides/utilisateur/QUICKSTART.md)** - Installation en 5 minutes
3. 🏗️ **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Vue d'ensemble technique
4. 🗄️ **[architecture/DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)** - Modèle de données (diagramme Mermaid)
5. 🔧 **[guides/troubleshooting/TROUBLESHOOTING.md](guides/troubleshooting/TROUBLESHOOTING.md)** - Solutions aux problèmes

---

## 📂 Structure de la Documentation

### 📖 Documents Racine

| Fichier | Description |
|---------|-------------|
| **[README.md](README.md)** | Documentation principale du projet |
| **[INDEX.md](INDEX.md)** | Ce fichier - Index complet |
| **[STRUCTURE.md](archive/STRUCTURE.md)** | Structure du projet |
| **[PROJECT-SUMMARY.md](archive/PROJECT-SUMMARY.md)** | Résumé complet du projet |
| **[STATUS.md](archive/STATUS.md)** | État actuel de l'application |
| **[GITHUB-REPO-INFO.md](archive/GITHUB-REPO-INFO.md)** | Info GitHub (SEO, topics) |

---

## 🏗️ Architecture

**Répertoire:** `architecture/`

| Fichier | Description |
|---------|-------------|
| **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** | Architecture complète de l'application |
| **[ARCHITECTURE-SCHEMA.md](architecture/ARCHITECTURE-SCHEMA.md)** | Schémas visuels ASCII art |
| **[DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)** | Modèle relationnel avec diagramme Mermaid ER |
| **[TYPES-SUPPORT.md](architecture/TYPES-SUPPORT.md)** | Support des types et formats |

**Contenu:**
- 3 tiers (Frontend React / Backend FastAPI / DB SQLite)
- 11 tables (albums, artists, tracks, listening_history, metadata, images, service_states, album_artist, album_collections, collection_albums, alembic_version)
- Auto-restart services
- Intégration Roon, Last.fm, Discogs, Spotify
- Flow de contrôle détaillé

---

## 🌐 API

**Répertoire:** `api/`

| Fichier | Description |
|---------|-------------|
| **[API.md](api/API.md)** | Documentation API REST complète |

**Endpoints:**
- `/albums` - Gestion albums
- `/artists` - Gestion artistes  
- `/history` - Historique d'écoute
- `/services` - Services externes (Last.fm, Roon, Discogs, Spotify)
- `/analytics` - Statistiques avancées
- `/collection` - Collections et exports

---

## 📚 Guides

### 👤 Guides Utilisateur

**Répertoire:** `guides/utilisateur/`

| Fichier | Description |
|---------|-------------|
| **[QUICKSTART.md](guides/utilisateur/QUICKSTART.md)** | Guide de démarrage rapide |
| **[QUICK-REFERENCE.md](guides/utilisateur/QUICK-REFERENCE.md)** | Référence rapide |
| **[DISCOVER-GUIDE.md](guides/utilisateur/DISCOVER-GUIDE.md)** | Guide de découverte |
| **[GUIDE-UTILISATEUR-TRACKER-CONFIGURATION.md](guides/utilisateur/GUIDE-UTILISATEUR-TRACKER-CONFIGURATION.md)** | Configuration du tracker (stations de radio, horaires) |
| **[GUIDE-UTILISATEUR-OPTIMIZATION-SETTINGS.md](guides/utilisateur/GUIDE-UTILISATEUR-OPTIMIZATION-SETTINGS.md)** | Guide optimisation settings |
| **[GUIDE-UTILISATEUR-ROON-PLAYLISTS.md](guides/utilisateur/GUIDE-UTILISATEUR-ROON-PLAYLISTS.md)** | Guide playlists Roon |

### 🔧 Installation

**Répertoire:** `guides/installation/`

| Fichier | Description |
|---------|-------------|
| **[INSTALLATION-CHECKLIST.md](guides/installation/INSTALLATION-CHECKLIST.md)** | Checklist d'installation |
| **[INSTALLATION-CORRECTION.md](guides/installation/INSTALLATION-CORRECTION.md)** | Corrections d'installation |

### 🐛 Troubleshooting

**Répertoire:** `guides/troubleshooting/`

| Fichier | Description |
|---------|-------------|
| **[TROUBLESHOOTING.md](guides/troubleshooting/TROUBLESHOOTING.md)** | Guide de dépannage général |
| **[TROUBLESHOOTING-INFRASTRUCTURE.md](guides/troubleshooting/TROUBLESHOOTING-INFRASTRUCTURE.md)** | Dépannage infrastructure |
| **[RELIABILITY-GUIDE.md](guides/troubleshooting/RELIABILITY-GUIDE.md)** | Guide de fiabilité système |
| **[ROBUSTNESS-IMPROVEMENTS.md](guides/troubleshooting/ROBUSTNESS-IMPROVEMENTS.md)** | Améliorations robustesse |
| **[ROBUSTNESS-IMPROVEMENTS-V4.md](guides/troubleshooting/ROBUSTNESS-IMPROVEMENTS-V4.md)** | Améliorations v4 |
| **[ROBUSTNESS-QUICKSTART.md](guides/troubleshooting/ROBUSTNESS-QUICKSTART.md)** | Démarrage rapide robustesse |
| **[ROBUSTNESS-SUMMARY.md](guides/troubleshooting/ROBUSTNESS-SUMMARY.md)** | Résumé améliorations |

### 🧪 Tests

**Répertoire:** `guides/`

| Fichier | Description |
|---------|-------------|
| **[TESTING.md](guides/TESTING.md)** | Guide de test complet |
| **[AUTO-RESTART-TEST-GUIDE.md](guides/AUTO-RESTART-TEST-GUIDE.md)** | Test auto-restart services |

---

## 🎵 Fonctionnalités

### 🤖 Intelligence Artificielle (AI/IA)

**Répertoire:** `features/ai/`

| Fichier | Description |
|---------|-------------|
| **[AI-PROMPTS.md](features/ai/AI-PROMPTS.md)** | 🌟 Catalogue complet des prompts IA (EurIA) |
| **[SCHEDULER-IA-PROMPTS.md](features/ai/SCHEDULER-IA-PROMPTS.md)** | Prompts spécifiques au scheduler |
| **[SCHEDULER-IA-SUMMARY.txt](features/ai/SCHEDULER-IA-SUMMARY.txt)** | Résumé scheduler IA |
| **[SCHEDULER-AI-OPTIMIZATION.md](features/ai/SCHEDULER-AI-OPTIMIZATION.md)** | Optimisation scheduler par IA |

**Contenu:**
- Description d'albums (2000 caractères)
- Descriptions courtes (35 mots)
- Génération de haïkus (global et contextuel)
- Optimisation automatique des paramètres
- Circuit breaker et retry logic

### 📊 Analytics

**Répertoire:** `features/analytics/`

| Fichier | Description |
|---------|-------------|
| **[ANALYTICS-ADVANCED-API.md](features/analytics/ANALYTICS-ADVANCED-API.md)** | API analytics avancée |
| **[ANALYTICS-IMPLEMENTATION-SUMMARY.md](features/analytics/ANALYTICS-IMPLEMENTATION-SUMMARY.md)** | Résumé implémentation |
| **[ANALYTICS-USER-GUIDE.md](features/analytics/ANALYTICS-USER-GUIDE.md)** | Guide utilisateur analytics |

### 📤 Export

**Répertoire:** `features/export/`

| Fichier | Description |
|---------|-------------|
| **[EXPORT-MARKDOWN.md](features/export/EXPORT-MARKDOWN.md)** | Export Markdown |
| **[EXPORT-MARKDOWN-FEATURE.md](features/export/EXPORT-MARKDOWN-FEATURE.md)** | Fonctionnalité export |
| **[EXPORT-MARKDOWN-FRONTEND.md](features/export/EXPORT-MARKDOWN-FRONTEND.md)** | Intégration frontend |

### 🎛️ Roon

**Répertoire:** `features/roon/`

| Fichier | Description |
|---------|-------------|
| **[ROON-TRACKER-DOC.md](features/roon/ROON-TRACKER-DOC.md)** | Documentation tracker Roon |
| **[ROON-BUGFIXES.md](features/roon/ROON-BUGFIXES.md)** | Corrections bugs Roon |
| **[ROON-CHANGELOG.md](features/roon/ROON-CHANGELOG.md)** | Changelog Roon |
| **[ROON-CONTROLS-GUIDE.md](features/roon/ROON-CONTROLS-GUIDE.md)** | Guide contrôles Roon |
| **[ROON-PLAYLISTS-GUIDE.md](features/roon/ROON-PLAYLISTS-GUIDE.md)** | Guide playlists Roon |
| **[MIGRATION-ROON-PLAYLISTS.md](features/roon/MIGRATION-ROON-PLAYLISTS.md)** | Migration playlists |

**Autres sous-dossiers Roon:** `features/roon/` (contient documentation détaillée d'intégration)

### ⏰ Scheduler

**Répertoire:** `features/scheduler/`

| Fichier | Description |
|---------|-------------|
| **[SCHEDULER.md](features/scheduler/SCHEDULER.md)** | Documentation scheduler |
| **[SCHEDULER-TASKS-GUIDE.md](features/scheduler/SCHEDULER-TASKS-GUIDE.md)** | Guide des tâches |
| **[SCHEDULER-CHECKLIST.md](features/scheduler/SCHEDULER-CHECKLIST.md)** | Checklist scheduler |
| **[SCHEDULER-FORMAT-SYNC.md](features/scheduler/SCHEDULER-FORMAT-SYNC.md)** | Synchronisation formats |
| **[SCHEDULER-FRONTEND-INTEGRATION.md](features/scheduler/SCHEDULER-FRONTEND-INTEGRATION.md)** | Intégration frontend |
| **[SCHEDULER-HAIKU-SYNC-COMPLETE.md](features/scheduler/SCHEDULER-HAIKU-SYNC-COMPLETE.md)** | Sync haïkus |
| **[SCHEDULER-IMPLEMENTATION-REPORT.md](features/scheduler/SCHEDULER-IMPLEMENTATION-REPORT.md)** | Rapport implémentation |
| **[SCHEDULER-OPTIMIZATION-REPORT.md](features/scheduler/SCHEDULER-OPTIMIZATION-REPORT.md)** | Rapport optimisation |
| **[SCHEDULER-SYNC-COMPLETE.md](features/scheduler/SCHEDULER-SYNC-COMPLETE.md)** | Sync complète |

**Tâches principales:**
- Génération haïkus (6h00)
- Export Markdown/JSON (8h00/10h00)
- Optimisation descriptions IA (2h00)
- Enrichissement quotidien

### 📁 Autres Fonctionnalités

**Répertoire:** `features/`

| Fichier | Description |
|---------|-------------|
| **[NOUVELLES-FONCTIONNALITES.md](features/NOUVELLES-FONCTIONNALITES.md)** | Nouvelles fonctionnalités v4.0.0 |
| **[JOURNAL-TIMELINE-DOC.md](features/JOURNAL-TIMELINE-DOC.md)** | Vue Journal/Timeline |
| **[LASTFM-IMPORT-TRACKER-DOC.md](features/LASTFM-IMPORT-TRACKER-DOC.md)** | Tracker Last.fm |

---

## 🔍 Audits et Corrections

**Répertoire:** `audits/`

| Fichier | Description |
|---------|-------------|
| **[AUDIT-2026-02-02.md](audits/AUDIT-2026-02-02.md)** | Audit 2 février 2026 |
| **[AUDIT-INFRASTRUCTURE-2026-01-31.md](audits/AUDIT-INFRASTRUCTURE-2026-01-31.md)** | Audit infrastructure |
| **[CORRECTION-COMPLETE.md](audits/CORRECTION-COMPLETE.md)** | Corrections complètes |
| **[CORRECTION-DISCOGS-SOURCE.md](audits/CORRECTION-DISCOGS-SOURCE.md)** | Correction source Discogs |
| **[CHECKLIST-CORRECTION.txt](audits/CHECKLIST-CORRECTION.txt)** | Checklist corrections |
| **[CLEANUP-REPORT-LASTFM-IMPORT.md](audits/CLEANUP-REPORT-LASTFM-IMPORT.md)** | Nettoyage imports Last.fm |
| **[COMPLETION-HAIKU-SYNC.md](audits/COMPLETION-HAIKU-SYNC.md)** | Complétion sync haïkus |
| **[REORGANISATION-2026-02-01.md](audits/REORGANISATION-2026-02-01.md)** | Réorganisation 1er février |
| **[RESULT.md](audits/RESULT.md)** | Résultats audits |
| **[RAPPORT-CORRECTION-DISCOGS.md](audits/RAPPORT-CORRECTION-DISCOGS.md)** | Rapport corrections Discogs |

### Last.fm Import

| Fichier | Description |
|---------|-------------|
| **[LASTFM-IMPORT-CHANGES-DETAILED.md](audits/LASTFM-IMPORT-CHANGES-DETAILED.md)** | Changements détaillés |
| **[LASTFM-IMPORT-FIXES.md](audits/LASTFM-IMPORT-FIXES.md)** | Corrections import |
| **[LASTFM-IMPORT-QUICK-FIX.md](audits/LASTFM-IMPORT-QUICK-FIX.md)** | Corrections rapides |
| **[LASTFM-IMPORT-SUMMARY.md](audits/LASTFM-IMPORT-SUMMARY.md)** | Résumé import |
| **[LASTFM-PROGRESS-FEATURE.md](audits/LASTFM-PROGRESS-FEATURE.md)** | Fonctionnalité progression |

---

## ⚙️ Settings et Configuration

**Répertoire:** `settings/`

| Fichier | Description |
|---------|-------------|
| **[README-SETTINGS-INTEGRATION.md](settings/README-SETTINGS-INTEGRATION.md)** | README intégration settings |
| **[SETTINGS-INTEGRATION-SUMMARY.txt](settings/SETTINGS-INTEGRATION-SUMMARY.txt)** | Résumé intégration |
| **[SETTINGS-OPTIMIZATION-DISPLAY.md](settings/SETTINGS-OPTIMIZATION-DISPLAY.md)** | Affichage optimisations |
| **[INTEGRATION-SETTINGS-OPTIMIZATION.md](settings/INTEGRATION-SETTINGS-OPTIMIZATION.md)** | Intégration optimisations |
| **[FILE-STRUCTURE-SETTINGS-INTEGRATION.md](settings/FILE-STRUCTURE-SETTINGS-INTEGRATION.md)** | Structure fichiers |
| **[INDEX-DOCUMENTATION-SETTINGS.md](settings/INDEX-DOCUMENTATION-SETTINGS.md)** | Index documentation settings |
| **[ACCES-DIRECT-SETTINGS-URL.md](settings/ACCES-DIRECT-SETTINGS-URL.md)** | Accès direct URL |
| **[ACCES-DIRECT-SETTINGS.txt](settings/ACCES-DIRECT-SETTINGS.txt)** | Accès direct (txt) |
| **[QUICK-START-SETTINGS.txt](settings/QUICK-START-SETTINGS.txt)** | Démarrage rapide |

**Fonctionnalités:**
- Interface de configuration centralisée
- Optimisations par IA (EurIA)
- Accès direct via URL
- Affichage des recommandations

---

## 🚀 Deployment

**Répertoire:** `deployment/`

| Fichier | Description |
|---------|-------------|
| **[DEPLOYMENT-GUIDE-SETTINGS-INTEGRATION.md](deployment/DEPLOYMENT-GUIDE-SETTINGS-INTEGRATION.md)** | Guide déploiement settings |
| **[DEPLOYMENT_SUMMARY.txt](deployment/DEPLOYMENT_SUMMARY.txt)** | Résumé déploiement |
| **[DEPLOYMENT_REPORT.json](deployment/DEPLOYMENT_REPORT.json)** | Rapport JSON |
| **[DEPLOYMENT-REPORT.sh](deployment/DEPLOYMENT-REPORT.sh)** | Script rapport |
| **[PRODUCTION.md](deployment/PRODUCTION.md)** | Guide production |
| **[PRODUCTION_GUIDE.md](deployment/PRODUCTION_GUIDE.md)** | Guide production détaillé |

---

## 📝 Changelogs

**Répertoire:** `changelogs/`

| Fichier | Description |
|---------|-------------|
| **[CHANGELOG.md](changelogs/CHANGELOG.md)** | Journal principal des changements |
| **[CHANGELOG-UI-ENRICHMENT.md](changelogs/CHANGELOG-UI-ENRICHMENT.md)** | Améliorations UI |
| **[CHANGELOG-UNIFIED-ALBUM-DISPLAY.md](changelogs/CHANGELOG-UNIFIED-ALBUM-DISPLAY.md)** | Affichage albums unifié |
| **[CHANGELOG-ANALYTICS-ADVANCED.md](changelogs/CHANGELOG-ANALYTICS-ADVANCED.md)** | Analytics avancés |
| **[CHANGELOG-v4.7.0-RADIO-STATIONS.md](changelogs/CHANGELOG-v4.7.0-RADIO-STATIONS.md)** | Détection stations de radio |
| **[CHANGELOG-v4.7.1-BUGFIX.md](changelogs/CHANGELOG-v4.7.1-BUGFIX.md)** | Bugfix: Portrait button endpoint |
| **[IMPROVEMENTS.md](changelogs/IMPROVEMENTS.md)** | Améliorations générales |

---

## 🔧 Autres Répertoires

### 📸 Screenshots

**Répertoire:** `screenshots/`

Captures d'écran de l'application et de l'interface.

### 🛠️ Scripts Utilitaires

**Répertoire:** `scripts-util/`

Scripts Python et shell de maintenance et tests.

### 🐛 Debug

**Répertoire:** `debug/`

Fichiers de debug et diagnostics.

### 📋 Config

**Répertoire:** `config/`

Fichiers de configuration et exemples.

### 📐 Specifications

**Répertoire:** `specs/`

Spécifications techniques et designs.

---

## 🎯 Parcours par Thème

### 🆕 Nouveaux Utilisateurs
1. [README.md](README.md)
2. [guides/utilisateur/QUICKSTART.md](guides/utilisateur/QUICKSTART.md)
3. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
4. [features/NOUVELLES-FONCTIONNALITES.md](features/NOUVELLES-FONCTIONNALITES.md)

### 👨‍💻 Développeurs
1. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
2. [architecture/DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)
3. [api/API.md](api/API.md)
4. [guides/TESTING.md](guides/TESTING.md)

### 🤖 Intelligence Artificielle
1. [features/ai/AI-PROMPTS.md](features/ai/AI-PROMPTS.md) ⭐
2. [features/ai/SCHEDULER-AI-OPTIMIZATION.md](features/ai/SCHEDULER-AI-OPTIMIZATION.md)
3. [features/scheduler/SCHEDULER-OPTIMIZATION-REPORT.md](features/scheduler/SCHEDULER-OPTIMIZATION-REPORT.md)

### 🎛️ Intégration Roon
1. [features/roon/ROON-TRACKER-DOC.md](features/roon/ROON-TRACKER-DOC.md)
2. [features/roon/ROON-CONTROLS-GUIDE.md](features/roon/ROON-CONTROLS-GUIDE.md)
3. [features/roon/ROON-PLAYLISTS-GUIDE.md](features/roon/ROON-PLAYLISTS-GUIDE.md)

### 🔧 Maintenance et Dépannage
1. [guides/troubleshooting/TROUBLESHOOTING.md](guides/troubleshooting/TROUBLESHOOTING.md)
2. [guides/troubleshooting/RELIABILITY-GUIDE.md](guides/troubleshooting/RELIABILITY-GUIDE.md)
3. [audits/](audits/)

### 📊 Architecture & Design
1. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
2. [architecture/ARCHITECTURE-SCHEMA.md](architecture/ARCHITECTURE-SCHEMA.md)
3. [architecture/DATABASE-SCHEMA.md](architecture/DATABASE-SCHEMA.md)

---

## 📊 Statistiques Documentation

- **110+ fichiers** de documentation
- **13 catégories** thématiques organisées
- **6 répertoires** principaux de fonctionnalités
- **3 schémas** d'architecture
- **1 diagramme** ER complet (Mermaid)
- **1 catalogue** complet des prompts IA

---

## 🔗 Liens Rapides

**Essentiels:**
- 🏠 [README principal](README.md)
- 📁 [STRUCTURE.md](archive/STRUCTURE.md)
- 🚀 [Démarrage rapide](guides/utilisateur/QUICKSTART.md)

**Architecture:**
- 🏗️ [Architecture complète](architecture/ARCHITECTURE.md)
- 📊 [Schémas visuels](architecture/ARCHITECTURE-SCHEMA.md)
- 🗄️ [Base de données](architecture/DATABASE-SCHEMA.md)

**Intelligence Artificielle:**
- 🤖 [Catalogue prompts IA](features/ai/AI-PROMPTS.md) ⭐
- 🔧 [Optimisation scheduler](features/ai/SCHEDULER-AI-OPTIMIZATION.md)

**Guides:**
- 📖 [Guide utilisateur](guides/utilisateur/)
- 🔧 [Installation](guides/installation/)
- 🐛 [Dépannage](guides/troubleshooting/)

---

**Version:** 4.6.0  
**Date de réorganisation:** 6 février 2026  
**Auteur:** Patrick Ostertag
