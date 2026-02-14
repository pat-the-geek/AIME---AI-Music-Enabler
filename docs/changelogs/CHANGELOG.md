# Changelog - AIME - AI Music Enabler

Tous les changements notables de ce projet sont documentés dans ce fichier.

## [4.7.0] - 2026-02-14

### 🎵 Apple Music Integration ✨

**Documentation détaillée:** [CHANGELOG-v4.7.0-APPLE-MUSIC.md](CHANGELOG-v4.7.0-APPLE-MUSIC.md)

#### ✨ Nouvelles Fonctionnalités
- 🎵 **Boutons Apple Music** sur toutes les pages d'albums (Magazine, Collection, Journal, Collections)
- 🔗 **Lien direct** vers Apple Music via Euria (quand disponible)
- 🔍 **Recherche intelligente** fallback (titre + artiste)
- 🪟 **Auto-fermeture** des fenêtres vides après 1 sec
- 🎨 **Styling cohérent** avec couleur Apple (#FA243C)

#### 🗄️ Base de Données
- Nouvelle colonne: `albums.apple_music_url` (VARCHAR(500), nullable)
- Nouvel index: `idx_albums_apple_music_url`
- Migration SQLite exécutée avec succès

#### 🔌 Backend
- Ajout champ Apple Music à Album model
- Propagation URL via magazine_generator_service (5 pages)
- API endpoints retournent apple_music_url

#### 🎨 Frontend
- Handler `handleOpenAppleMusic` cohérent cross-pages
- Intégration dans 4 pages: Magazine, Collection, Journal, Collections
- Support multi-locations (grille, modal, timeline)

### 📻 Radio Stations Detection

**Documentation détaillée:** [CHANGELOG-v4.7.0-RADIO-STATIONS.md](CHANGELOG-v4.7.0-RADIO-STATIONS.md)

#### ✨ Nouvelles Fonctionnalités
- Détection automatique des stations de radio
- Configuration flexible via `config/app.json`
- Smart matching (exact, partial, format variations)
- Support multi-sources (Last.fm, Roon)

---

## [4.0.1] - 2026-01-30

### 🐛 Corrections de Bugs

#### Compatibilité Python
- **Problème**: Incompatibilité de SQLAlchemy 2.0.25 avec Python 3.14.1
  - Erreur: `AttributeError: type object 'TypingOnly' has no attribute '__mro_entries__'`
  - **Solution**: Installation de SQLAlchemy 2.1.0b2.dev0 depuis GitHub main branch
  - Impact: Permet l'utilisation de Python 3.14.1 (bleeding edge)

#### Modèles de Base de Données
- **Problème**: Conflit avec attribut réservé `metadata` dans modèle Album
  - Erreur: `ArgumentError: Attribute name 'metadata' is reserved when using the Declarative API`
  - **Solution**: Renommé la relation en `album_metadata` dans `backend/app/models/album.py`
  - Fichier: `backend/app/models/album.py` ligne 27

- **Problème**: Import `ForeignKey` manquant dans modèle Playlist
  - Erreur: `NameError: name 'ForeignKey' is not defined`
  - **Solution**: Ajouté `ForeignKey` aux imports SQLAlchemy
  - Fichier: `backend/app/models/playlist.py` ligne 2

#### Configuration et Chemins
- **Problème**: Base de données SQLite ne se créait pas
  - Erreur: `sqlalchemy.exc.OperationalError: unable to open database file`
  - **Cause**: Calcul incorrect du chemin avec `Path(__file__).parent.parent.parent`
  - **Solutions multiples appliquées**:
    1. Ajout de variable d'environnement `PROJECT_ROOT` dans script de démarrage
    2. Conversion de `project_root` en propriété utilisant `PROJECT_ROOT` si disponible
    3. Conversion de `database_url` en propriété pour chemin absolu dynamique
    4. Ajout de logique de création de répertoire dans `init_db()`
  - Fichiers:
    - `backend/app/core/config.py` (lignes 12-30)
    - `backend/app/database.py` (lignes 31-44)
    - `scripts/start-dev.sh` (ligne 27)

#### Environnement de Développement
- **Problème**: Reloads infinis d'Uvicorn lors du développement
  - Cause: Surveillance de `.venv/` causant rechargements constants
  - **Solution**: Ajout de `--reload-dir app` pour limiter surveillance au code source
  - Impact: Backend stable sans rechargements intempestifs
  - Fichier: `scripts/start-dev.sh` ligne 29

### 📝 Documentation

#### Ajouts
- **TROUBLESHOOTING.md**: Guide complet de dépannage avec 7 problèmes documentés
  - Python 3.14 incompatibilité
  - Erreurs de base de données (3 problèmes)
  - Configuration et chemins
  - Reloads infinis Uvicorn
  - Node.js manquant
- **STATUS.md**: Document récapitulatif du statut du projet
- **CHANGELOG.md**: Ce fichier, historique des modifications

#### Mises à jour
- **README.md**: 
  - Ajout avertissement Python 3.14
  - Ajout section "Dépannage" avec liens vers TROUBLESHOOTING.md
  - Liste des problèmes connus résolus
- **QUICKSTART.md**:
  - Ajout avertissement Python 3.14
  - Section dépannage enrichie avec solutions rapides
  - Lien vers guide de dépannage complet

### 🔧 Améliorations Techniques

#### Configuration
- `backend/app/core/config.py`:
  - `project_root` converti en propriété avec support variable d'environnement
  - `config_dir` et `data_dir` convertis en propriétés
  - `database_url` converti en propriété avec chemin absolu dynamique
  - Ajout import `os` pour accès aux variables d'environnement

#### Scripts
- `scripts/start-dev.sh`:
  - Export de `PROJECT_ROOT="$(pwd)"` avant démarrage backend
  - Ajout `--reload-dir app` à uvicorn pour éviter surveillance .venv
  - Amélioration stabilité du développement

#### Base de Données
- `backend/app/database.py`:
  - Ajout logique automatique de création répertoire data/
  - Extraction et validation du chemin depuis URL SQLite
  - Création récursive des répertoires avec `os.makedirs(..., exist_ok=True)`

### ✅ Tests et Validation

- ✅ Backend démarre correctement sur port 8000
- ✅ Frontend démarre correctement sur port 5173
- ✅ Base de données créée avec 9 tables (140 KB)
- ✅ Health check endpoint répond: `{"status":"ok","version":"4.0.0"}`
- ✅ Documentation Swagger accessible
- ✅ Pas de reloads intempestifs

### 📊 Statistiques

- **Fichiers modifiés**: 5 fichiers
  - backend/app/core/config.py
  - backend/app/database.py
  - backend/app/models/album.py
  - backend/app/models/playlist.py
  - scripts/start-dev.sh

- **Fichiers créés**: 3 fichiers
  - docs/TROUBLESHOOTING.md (document de 400+ lignes)
  - STATUS.md
  - CHANGELOG.md

- **Documentation mise à jour**: 2 fichiers
  - README.md
  - docs/QUICKSTART.md

---

## [4.0.0] - 2026-01-30

### 🎉 Version Initiale

- ✨ Application complète fonctionnelle
- 🏗️ Architecture React 18 + FastAPI
- 📦 57 fichiers créés (backend: 35, frontend: 22)
- 🗄️ Base SQLite avec 9 tables
- 🔌 Intégration Last.fm, Spotify, Discogs, EurIA
- 📱 Interface Material-UI responsive
- 📚 Documentation complète (API, Architecture, Quickstart)

---

**Légende des types de changements:**
- 🎉 Nouvelle fonctionnalité
- 🐛 Correction de bug
- 📝 Documentation
- 🔧 Amélioration technique
- ⚠️ Breaking change
- 🔒 Sécurité
- ♻️ Refactoring
- ✅ Tests
