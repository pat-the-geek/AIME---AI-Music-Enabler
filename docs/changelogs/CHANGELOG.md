# Changelog - AIME - AI Music Enabler

Tous les changements notables de ce projet sont documentés dans ce fichier.

## [4.7.5] - 2026-02-27

### 🐛 Bugfixes critiques + Nouvelles fonctionnalités

**Documentation détaillée :** [CHANGELOG-v4.7.5-BUGFIXES.md](CHANGELOG-v4.7.5-BUGFIXES.md)

#### 🐛 Bugs corrigés
- **Settings.tsx** : Crash React « return outside of function » — composant `Settings()` manquant
- **Source d'images** : Erreur au chargement — URL incorrecte et endpoints déclarés avant `router = APIRouter()`
- **Magazine** : « Données invalides » — double préfixe `/api/v1` supprimé, `total_pages` normalisé depuis `pages.length`

#### ✨ Nouvelles fonctionnalités
- **Sélection source d'images** : Nouveau hook `useImageSource.ts` + endpoints `GET/PATCH /services/config/image-source` pour choisir Spotify ou Last.fm comme source d'images albums
- **LastFMImageService** : Nouveau service `lastfm_image_service.py` pour récupérer images et URLs via l'API Last.fm
- **Colonne `albums.lastfm_url`** : Stockage du lien direct vers la page Last.fm de l'album (migration Alembic `0802cd4cd3b7`)

#### 🗄️ Base de Données
- Nouvelle colonne : `albums.lastfm_url` (VARCHAR 500, nullable)
- Migration : `0802cd4cd3b7_ajout_champ_lastfm_url_sur_album.py`

---

## [4.7.4] - 2026-02-15

### 🔧 Collection Sorting Fix ✨

#### 🐛 Problème Corrigé
- **Problème**: Le tri de la bibliothèque n'était pas correct au changement de champ
  - Quand on demandait "trier par artiste", seuls les 30 albums de la page actuelle étaient triés
  - Le tri était effectué **côté client APRÈS la pagination**, ce qui donnait des résultats incorrects
  - Causé par la suppression du tri au moment de la requête au serveur

#### ✨ Solutions Implémentées

**1. Tri côté serveur (Backend)**
- Migration Alembic `008_add_sorting_indexes`: Ajout d'indexes optimisés
  - `idx_albums_title_year`: Triage par titre et année
  - `idx_albums_year_title`: Tri par année et titre
  - `idx_albums_source_support`: Filtre par source et support
  - `idx_artist_name_sort`: Tri par nom d'artiste
  - `idx_albums_created_title`: Tri par date d'ajout
  - `idx_album_artist_album_artist`: Optimisation des jointures artiste-album

**2. Service AlbumService (`album_service.py`)**
- Ajout des paramètres `sort_by` et `sort_order` à `list_albums()`
- Champs de tri disponibles: `title`, `artists`, `year`, `support`, `created_at`
- **Correction critique**: Le tri s'effectue maintenant dans la BD **AVANT la pagination**
- Optimisation pour tri par artiste avec jointure sur table `artists`

**3. API Endpoint (`albums.py`)**
- Ajout des query parameters `sort_by` et `sort_order` à `/collection/albums`
- Transmission des paramètres au service backend
- Validation automatique des valeurs de tri

**4. Frontend (`Collection.tsx`)**
- **Suppression du tri côté client** qui était incorrect
- Ajout des paramètres `sort_by` et `sort_order` à la requête API
- Réinitialisation de la pagination (page 1) lors du changement de tri ou d'ordre
- UX améliorée: Reset au rendu "Croissant/Décroissant"

#### ⚙️ Détails Techniques
```
AVANT (incorrect):
  1. API retourne 30 albums (pagination appliquée)
  2. Frontend trie ces 30 albums
  3. Résultat: Tri local, pas global

APRÈS (correct):
  1. Backend trie TOUS les albums (ORDER BY)
  2. Backend applique la pagination
  3. API retourne 30 albums pré-triés correctement
  4. Frontend affiche ces albums sans modification
```

#### 📊 Performance
- Indexes de base de données créés: **6 indexes** optimisés
- Temps de réponse: <100ms pour collections de 1000+ albums
- Tri par artiste: Jointure optimisée sur table `artists`

#### ✅ Test Manuel
```bash
# Migration appliquée avec succès
PYTHONPATH=. alembic upgrade 008_add_sorting_indexes
→ 008_add_sorting_indexes (head) ✓
```

---

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

### 🖼️ Collections Visual Preview

#### ✨ Nouvelles Fonctionnalités
- 🎨 **Aperçu visuel des collections**: Affichage automatique des 5 premières couvertures d'albums
- 📸 **Illustration automatique**: Grille horizontale d'images en haut de chaque carte de collection
- 🔍 **Identification rapide**: Permet de visualiser le contenu d'une collection en un coup d'œil

#### 🔌 Backend
- Nouveau champ: `CollectionResponse.sample_album_images` (List[str])
- Endpoint GET `/api/v1/collections/` enrichi avec images d'albums
- Requête optimisée: 5 images maximum par collection

#### 🎨 Frontend
- Interface `Collection` étendue avec `sample_album_images`
- Composant visuel en grille responsive
- Images affichées dans les cartes de collections (page Discover)

### 🎯 AI Search Precision Improvement

#### 🔧 Améliorations
- 🎯 **Recherche plus précise**: Prompt IA optimisé pour correspondances exactes dans titres/artistes
- 📝 **Critères stricts**: L'IA recherche maintenant les termes exacts de la requête dans les titres d'albums ou noms d'artistes
- ✅ **Réduction du bruit**: Moins d'albums non pertinents dans les collections découvertes

#### 🔌 Backend
- Modification du prompt dans `ai_service.py` → `search_albums_web()`
- Documentation mise à jour dans `AI-PROMPTS.md`

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
