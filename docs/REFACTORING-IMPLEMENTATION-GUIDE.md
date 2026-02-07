# 📖 GUIDE D'IMPLÉMENTATION - Nouvelle Architecture Services

**Version:** 1.0  
**Date:** 7 février 2026  
**Status:** En cours de refactorisation

---

## ✅ Étapes Complétées (Phase 0-1)

- ✅ Audit complet des duplications (doc: `REFACTORING-AUDIT-2026-02-07.md`)
- ✅ Plan d'action créé (doc: `REFACTORING-ACTION-PLAN.md`)
- ✅ Doublon critique supprimé: `stream_artist_article()` dans `artists.py`
- ✅ Répertoires services créés:
  - `services/dialog/` (modules de dialogue)
  - `services/external/` (intégrations externes)
  - `services/collection/` (collection & library)
  - `services/content/` (génération contenu IA)
  - `services/playback/` (lecture audio)
  - `services/analytics/` (statistiques)
- ✅ Modules dialogue implémentés:
  - `dialog/error_dialog.py` - Erreurs centralisées
  - `dialog/success_dialog.py` - Succès centraliséss
  - `dialog/streaming_dialog.py` - SSE/Streaming centralisé

---

## 🚀 Prochaines Étapes

### PHASE 2A: Consolider AI Service (1h)

#### Contexte
Actuellement: `ai_service.py` ET `euria_service.py` existent tous deux
- `ai_service.py` (450 lignes) - Service Euria
- `euria_service.py` (?) - Doublon probable

#### Action
1. Examiner `euria_service.py` pour comprendre les différences
2. Consolider en UN SEUL `external/ai_service.py`
3. Supprimer l'ancien `euria_service.py`

#### Code Pattern
```python
# backend/app/services/external/ai_service.py
from app.core.config import get_settings
import httpx

class AIService:
    """Unified AI/LLM service for all content generation."""
    
    def __init__(self, url: str, bearer: str):
        self.url = url
        self.bearer = bearer
        self.http_client = httpx.AsyncClient()
    
    async def generate_haiku(self, album_data: dict) -> str:
        """Generate haiku for album."""
        # Implementation
        pass
    
    async def generate_article(self, context: dict) -> str:
        """Generate long-form article."""
        # Implementation
        pass
    
    async def generate_description(self, item: dict) -> str:
        """Generate description for any item."""
        # Implementation
        pass
    
    async def stream_generation(self, prompt: str):
        """Stream content generation."""
        # Async generator
        pass
```

---

### PHASE 2B: Migrer Services Existants (4h)

#### Pattern de Migration

1. **OLD SERVICE** (exemple: `playlist_service.py`)
   ```
   Location: backend/app/services/playlist_service.py
   Lines: ~200
   Dependencies: db, SQLAlchemy, models
   Used by: api/v1/playlists.py
   ```

2. **NEW SERVICE** (même fonctionnalité)
   ```
   Location: backend/app/services/playback/playlist_service.py
   Lines: ~200 (refactored for clarity)
   Dependencies: same + dialog service
   Used by: api/v1/playback/playlists.py
   ```

#### Services à Migrer (Ordre)

##### Group 1: Collection Services (2h)

```
AVANT:
├── album_collection_service.py    (250 lines)
└── (logique ailleurs)

APRÈS:
├── collection/
│   ├── album_service.py          (150 lines - focused)
│   ├── artist_service.py         (150 lines - focused)
│   ├── track_service.py          (150 lines - focused)
│   ├── search_service.py         (200 lines - from collection.py + collections.py)
│   └── collection_service.py     (100 lines - aggregation)
```

**Actions:**
1. Créer `collection/artist_service.py` - extract artist logic
2. Créer `collection/album_service.py` - extract album logic
3. Créer `collection/track_service.py` - extract track logic
4. Créer `collection/search_service.py` - merge search logic from collection.py + collections.py
5. Adapter imports dans api/v1/

---

##### Group 2: Content Services (1h 30min)

```
AVANT:
├── artist_article_service.py     (200 lines)
└── (haiku logic in history.py - 50 lines)

APRÈS:
├── content/
│   ├── article_service.py        (refactored artist_article_service.py)
│   ├── haiku_service.py          (extracted from history.py)
│   └── description_service.py    (extracted from metadata service)
```

**Actions:**
1. Créer `content/article_service.py` (move artist_article_service code)
2. Créer `content/haiku_service.py` (extract haiku generation from history.py)
3. Créer `content/description_service.py`
4. Adapter imports dans api/v1/

---

##### Group 3: Playback Services (1h)

```
AVANT:
├── playlist_service.py           (200 lines)
├── playlist_queue_service.py     (150 lines)
├── playlist_generator.py         (100 lines)
└── roon_service.py               (500+ lines)

APRÈS:
├── playback/
│   ├── playlist_service.py       (consolidated 1 file)
│   ├── queue_service.py          (from playlist_queue_service.py)
│   ├── roon_playback_service.py  (extracted from roon_service.py)
│   └── now_playing_service.py    (new)
```

**Actions:**
1. Consolidate `playlist_service.py` + `playlist_queue_service.py`
   - Remove `playlist_generator.py` (logic should be in main service)
   - Keep playlist CRUD, generation, queue in one file
2. Extract Roon playback logic → `roon_playback_service.py`
3. Keep core Roon ops (zones, now_playing) in `external/roon_service.py`

---

##### Group 4: Analytics Services (30min)

```
AVANT:
├── (scattered in history.py:
│   ├── listening_patterns()
│   ├── detect_sessions()
│   ├── get_stats())

APRÈS:
├── analytics/
│   ├── listening_history_service.py
│   ├── stats_service.py
│   └── patterns_service.py
```

---

### PHASE 3: Migrer Routes API (2h)

```
Current Structure:
├── api/v1/
│   ├── artists.py                (list, article/stream)
│   ├── history.py                (haikus, patterns, stats, timeline)
│   ├── collection.py             (albums, artists, exports)
│   ├── collections.py            (search - DUPLICATE!)
│   ├── playlists.py              (CRUD + generation)
│   ├── roon.py                   (playback control)
│   ├── magazines.py              (magazine generation)
│   ├── analytics.py              (advanced stats)
│   └── services.py               (service state)

New Structure:
├── api/v1/
│   ├── collection/
│   │   ├── __init__.py           (register routes)
│   │   ├── albums.py             (GET /collection/albums/*)
│   │   ├── artists.py            (GET /collection/artists/*, unified)
│   │   ├── search.py             (GET /collection/search, consolidated)
│   │   └── tracks.py             (GET /collection/tracks/*)
│   ├── content/
│   │   ├── __init__.py
│   │   ├── articles.py           (GET /content/articles/{artist_id})
│   │   ├── haikus.py             (GET /content/haikus)
│   │   └── descriptions.py       (GET /content/descriptions/{id})
│   ├── playback/
│   │   ├── __init__.py
│   │   ├── playlists.py          (GET/POST /playback/playlists/*)
│   │   ├── roon.py               (RENAMED - Roon playback control)
│   │   └── now_playing.py        (GET /playback/now-playing)
│   ├── magazines.py              (keep as is - well organized)
│   ├── analytics.py              (refactored - use new services)
│   ├── history.py                (DEPRECATED - move to analytics)
│   ├── services.py               (keep as is)
│   └── __init__.py               (consolidated router registration)
```

#### Exemple de Consolidation d'uRoute

**BEFORE:** `api/v1/artists.py`
```python
@router.get("/list")
async def list_artists(...):
    # Go to collection.py for list_albums - inconsistent!

@router.get("/{artist_id}/article")
async def generate_artist_article(...):
    # Article generation

@router.get("/{artist_id}/article/stream")
async def stream_artist_article(...):  # NEW - unified dialog module
    # Streaming article (FIXED - was duplicated)
```

**AFTER:** `api/v1/collection/artists.py`
```python
from app.services.collection import artist_service
from app.services.content import article_service
from app.services.dialog import create_streaming_response

@router.get("/")
async def list_artists(...):
    service = artist_service.ArtistService(db)
    artists = await service.list_all()
    return create_success_response(artists)

@router.get("/{artist_id}/article")
async def generate_artist_article(...):
    service = article_service.ArticleService(db, ai_service)
    article = await service.generate_artist_article(artist_id)
    return create_success_response(article)

@router.get("/{artist_id}/article/stream")
async def stream_artist_article(...):
    async def generate():
        service = article_service.ArticleService(db, ai_service)
        async for chunk in service.stream_article(artist_id):
            yield chunk
    return create_streaming_response(generate())
```

---

## 📋 Codebase Checklist

Avant de merger:
- [ ] Zero `.bak` files
- [ ] Zero doublon routes
- [ ] Zero circular imports
- [ ] All imports updated
- [ ] Tests pass (at least smoke tests)
- [ ] Backend starts without errors
- [ ] At least 5 endpoints tested from frontend

---

## 🔗 Architecture de Dépendances Finale

```
models/ & schemas/
    ↓
dialog/           (INDEPENDENT - no deps except logging)
    ↓
external/         (Depends: dialog, config)
    ↓
collection/       (Depends: external, dialog, models, schemas)
    ↓
analytics/        (Depends: collection)
    ↓
content/          (Depends: external, collection)
    ↓
playback/         (Depends: external, collection, dialog)
    └─→ magazine/  (Depends: ALL of above)
    └─→ tracking/  (Depends: external, collection)
    └─→ scheduling/ (Depends: ALL above)
    ↓
api/v1/           (Depends: ALL services)
```

---

## 🎯 Résumé Prochainement

### IMMÉDIAT (Aujourd'hui)
1. ✅ Audit & cleanup (DONE)
2. ✅ Créer structure + dialog (DONE)
3. **Consolider AI service** (NEXT)
4. **Migrer collection services** (1-2h)

### COURT TERME (Demain-Après-Demain)
5. Migrer content services
6. Migrer playback services
7. Migrer routes API

### MOYEN TERME
8. Validation complète
9. Tests
10. Documentation finalisée
11. PR & Merge

---

## 📞 Questions Fréquentes

### Q: Comment migrer un service existant?
**A:** Copier le code du service OLD, refactoriser en module séparé, mettre à jour imports, tester.

### Q: Quand supprimer les anciens fichiers?
**A:** APRÈS avoir validé que les nouveaux modules fonctionnent + imports mis à jour.

### Q: Impacts sur le Frontend?
**A:** Endpoints URLs changent légèrement:
- `/api/v1/artists/list` → `/api/v1/collection/artists/`
- `/api/v1/playlists/` → `/api/v1/playback/playlists/`
Créer wrapper API pour backward compatibility si nécessaire.

### Q: Et les services existants comme Magazine?
**A:** Laisser tels quels pour l'instant - bien organisés déjà. Refactor après la migration globale si temps.

---

