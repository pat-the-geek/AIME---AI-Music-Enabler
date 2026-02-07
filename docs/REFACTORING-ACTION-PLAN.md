# 🚀 PLAN D'ACTION - Refactorisation Immédiate

**Date:** 7 février 2026  
**Priorité:** CRITIQUE - Bugs causés par duplications

---

## 🔴 PROBLÈMES CRITIQUES À CORRIGER MAINTENANT

### 1. **DOUBLON EXACT: `artists.py` - `stream_artist_article()` (lignes 84 & 163)**

#### Problème
```python
# Ligne 84
@router.get("/{artist_id}/article/stream")
async def stream_artist_article(...):
    # Logique complète

# Ligne 163 - EXACT DOUBLON
@router.get("/{artist_id}/article/stream")
async def stream_artist_article(...):
    # Même logique (+ ListeningHistory import)
```

**Impact:** La 2ème écrase la 1ère. Les 2 sont identiques à 99%.

#### Solution: SUPPRIMER la 2ème, garder la 1ère

---

### 2. **DUPLICATION: `playlist_service.py` vs `playlist_queue_service.py`**

À vérifier et consolider.

---

### 3. **DUPLICATION: `ai_service.py` vs `euria_service.py`**

À vérifier et consolider.

---

## 📋 ÉTAPES IMMÉDIATES (ORDRE D'EXÉCUTION)

### ÉTAPE 1: Corriger le Doublon Critical
- [ ] Supprimer `stream_artist_article()` lignes 163-235 dans `artists.py`
- [ ] Garder la version ligne 84-151
- [ ] Tester l'endpoint

### ÉTAPE 2: Créer la Nouvelle Structure
- [ ] Créer répertoires:
  ```
  backend/app/services/external/
  backend/app/services/collection/
  backend/app/services/content/
  backend/app/services/analytics/
  backend/app/services/playback/
  backend/app/services/tracking/
  backend/app/services/dialog/
  ```

### ÉTAPE 3: Créer Services de Base (Ordre Dépendances)

1. **Dialog Service** (aucune dépendance)
   ```python
   backend/app/services/dialog/
   ├── __init__.py
   ├── error_dialog.py
   ├── success_dialog.py
   └── streaming_dialog.py
   ```

2. **AI Service Centralisé**
   ```python
   backend/app/services/external/ai_service.py
   (Remplace euria_service.py)
   ```

3. **Collection Services**
   ```python
   backend/app/services/collection/
   ├── artist_service.py
   ├── album_service.py
   ├── track_service.py
   └── search_service.py
   ```

4. **Content Services** (Haiku, Article, Desc)
   ```python
   backend/app/services/content/
   ├── haiku_service.py      (NEW - consolidate logic from history.py)
   ├── article_service.py    (Move/refactor artist_article_service.py)
   └── description_service.py
   ```

5. **Playback Services**
   ```python
   backend/app/services/playback/
   ├── playlist_service.py   (CONSOLIDATE playlist_service.py + playlist_queue_service.py)
   └── roon_playback_service.py
   ```

### ÉTAPE 4: Créer Routes API Restructurées

```python
backend/app/api/v1/
├── collection/
│   ├── __init__.py
│   ├── albums.py         (NEW)
│   ├── artists.py        (REFACTOR - supprimer doublon)
│   └── search.py         (MERGE collection.py + collections.py)
├── content/
│   ├── __init__.py
│   ├── articles.py       (NEW)
│   ├── haikus.py         (NEW)
│   └── descriptions.py   (NEW)
├── playback/
│   ├── __init__.py
│   └── playlists.py      (CONSOLIDATE)
├── playlists.py          (SUPPRIMER - moved to playback/)
└── ...
```

### ÉTAPE 5: Cleanup

- [ ] Supprimer `roon_service.py.bak`
- [ ] Supprimer `euria_service.py` (remplacée)
- [ ] Supprimer `collections.py` (fusionnée avec `collection.py`)
- [ ] Supprimer `playlist_queue_service.py` (fusionnée)

---

## 📂 FILES À CRÉER (ORDER)

### Phase 0: Dialog Module (No dependencies)

```python
# backend/app/services/dialog/__init__.py
# backend/app/services/dialog/error_dialog.py
# backend/app/services/dialog/success_dialog.py
# backend/app/services/dialog/streaming_dialog.py
```

### Phase 1: External Services (Minor dependencies)

```python
# backend/app/services/external/ai_service.py (consolidates euria_service.py)
```

### Phase 2: Collection Services

```python
# backend/app/services/collection/__init__.py
# backend/app/services/collection/artist_service.py
# backend/app/services/collection/album_service.py
# backend/app/services/collection/track_service.py
# backend/app/services/collection/search_service.py
```

### Phase 3: Content Services

```python
# backend/app/services/content/__init__.py
# backend/app/services/content/haiku_service.py
# backend/app/services/content/article_service.py
# backend/app/services/content/description_service.py
```

### Phase 4: Playback Services

```python
# backend/app/services/playback/__init__.py
# backend/app/services/playback/playlist_service.py (CONSOLIDATED)
# backend/app/services/playback/roon_playback_service.py
```

### Phase 5: API Routes

```python
# backend/app/api/v1/collection/__init__.py
# backend/app/api/v1/collection/albums.py
# backend/app/api/v1/collection/artists.py (refactored)
# backend/app/api/v1/collection/search.py
# 
# backend/app/api/v1/content/__init__.py
# backend/app/api/v1/content/articles.py
# backend/app/api/v1/content/haikus.py
# 
# backend/app/api/v1/playback/__init__.py
# backend/app/api/v1/playback/playlists.py
```

---

## 🎯 Résultat Attendu

### AVANT (Confus)
```
services/
├── ai_service.py            # Call Euria
├── euria_service.py         # Also calls Euria? 🤔
├── artist_article_service.py # Uses ai_service
├── playlist_generator.py    # Génère playlist
├── playlist_service.py      # Gère playlist
├── playlist_queue_service.py # Queue playlist
└── roon_service.py + .bak

api/v1/
├── artists.py               # GET /list, POST /article/stream (x2!!!)
├── history.py               # generate_haiku() appelle quoi?
├── playlists.py             # generate_playlist() appelle quoi?
├── collection.py            # list_albums()
├── collections.py           # list_albums()???
└── roon.py
```

### APRÈS (CLAIR)
```
services/
├── dialog/
│   ├── error_dialog.py
│   ├── success_dialog.py
│   └── streaming_dialog.py
├── external/
│   ├── ai_service.py ✅ (UNIQUE SOURCE - Euria)
│   ├── spotify_service.py
│   ├── lastfm_service.py
│   ├── discogs_service.py
│   └── roon_service.py
├── collection/
│   ├── artist_service.py ✅
│   ├── album_service.py ✅
│   ├── track_service.py ✅
│   └── search_service.py ✅
├── content/
│   ├── haiku_service.py ✅
│   ├── article_service.py ✅
│   └── description_service.py ✅
├── playback/
│   ├── playlist_service.py ✅ (CONSOLIDATED)  
│   └── roon_playback_service.py ✅
├── analytics/
├── tracking/
└── scheduling/

api/v1/
├── collection/
│   ├── albums.py        ✅ GET /collection/albums
│   ├── artists.py       ✅ GET /collection/artists
│   └── search.py        ✅ GET /collection/search
├── content/
│   ├── articles.py      ✅ GET /content/articles/{id}
│   └── haikus.py        ✅ GET /content/haikus
├── playback/
│   └── playlists.py     ✅ GET /playback/playlists
├── magazines.py         ✅ (unchanged)
├── analytics.py         ✅ (refactored)
├── history.py           ✅ (refactored)
├── roon.py              ✅ (cleanup)
└── services.py          ✅ (unchanged)
```

---

## 🔗 Dépendances de Migration (Ordre Critique)

```
1. ✅ Supprimer doublon artists.py (FAIT EN PHASE 0)
2. ✅ Créer dialog/ (No deps)
3. ✅ Créer external/ (Min deps)
4. ✅ Créer collection/ (Depends: external)
5. ✅ Créer content/ (Depends: external, collection)
6. ✅ Créer analytics/ (Depends: collection)
7. ✅ Créer playback/ (Depends: external, collection)
8. ✅ Migrer api/v1/ (Depends: all services)
9. ✅ Cleanup = Supprimer anciens fichiers
10. ✅ Test & Validation
```

---

## ✅ CHECKLIST EXÉCUTION

### PRE-REFACTORING
- [ ] Commit: `git commit -m "Pre-refactoring backup point"`
- [ ] Créer branch: `git checkout -b refactor/code-organization`

### ÉTAPE 1: Fix Critical Bug (1h)
- [ ] ✅ Supprimer ligne 163-235 dans `artists.py`
- [ ] ✅ Test endpoint `/artists/{id}/article/stream`

### ÉTAPE 2: Créer Structure (1h)
- [ ] ✅ Créer répertoires services/
- [ ] ✅ Créer répertoires api/v1/

### ÉTAPE 3: Migrer Services (6h)
- [ ] ✅ dialog/
- [ ] ✅ external/ (ai_service.py consolidé)
- [ ] ✅ collection/
- [ ] ✅ content/
- [ ] ✅ playback/
- [ ] ✅ analytics/

### ÉTAPE 4: Migrer Routes (4h)
- [ ] ✅ api/v1/collection/
- [ ] ✅ api/v1/content/
- [ ] ✅ api/v1/playback/
- [ ] ✅ Refactor history.py, analytics.py

### ÉTAPE 5: Cleanup (1h)
- [ ] ✅ Supprimer .bak, euria_service.py, collections.py
- [ ] ✅ Valider imports
- [ ] ✅ Tests

### POST-REFACTORING
- [ ] ✅ Test backend startup
- [ ] ✅ Test 10+ endpoints critiques
- [ ] ✅ Commit: `git commit -m "refactor: reorganize code by domain"`
- [ ] ✅ Merge PR

---

## 📖 Documentation à Mettre à Jour

Après migration:
- [ ] `docs/architecture/ARCHITECTURE.md` - Ajouter nouvelle structure
- [ ] `docs/API.md` - Ajouter nouveau routing
- [ ] Créer `docs/REFACTORING-COMPLETE.md` (avant/après)

---

## ⚠️ Points d'Attention

1. **Imports dans main.py** - Router registration doit être mis à jour
2. **Frontend API calls** - Préfixes `/api/v1/` changeront légèrement
3. **Tests** - Tous les imports aaffectés
4. **Documentation** - A jour après.

---

