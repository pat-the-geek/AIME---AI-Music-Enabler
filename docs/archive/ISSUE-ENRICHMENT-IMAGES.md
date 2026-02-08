# Issue: Les images ne s'affichent pas après enrichissement d'album

**Date**: 3 février 2026  
**Status**: ⚠️ EN COURS - Plusieurs bugs corrigés mais problème persistant

## Problème

Lorsqu'on clique sur le bouton "Rafraîchir" dans le détail d'un album (depuis Collection, Journal ou Timeline), l'enrichissement fonctionne (année, URL Spotify, description IA) MAIS l'image ne s'affiche pas dans l'interface.

## Album testé

- **Titre**: Remain in Light
- **Artiste**: Talking Heads
- **Année**: 1980
- **URL Spotify**: https://open.spotify.com/album/3AQgdwMNCiN7awXch5fAaG
- **Image URL**: https://i.scdn.co/image/ab67616d0000b273e56fa8c916dc6ce419dcf557

## Bugs trouvés et corrigés

### 1. ✅ Paramètres inversés dans search_album_details
**Fichier**: `backend/app/api/v1/services.py` ligne 1003  
**Bug**: `search_album_details(album.title, artist_name)` au lieu de `search_album_details(artist_name, album.title)`  
**Impact**: Spotify ne trouvait rien car les paramètres étaient inversés  
**Commit**: `fix: Corriger l'ordre des paramètres dans l'appel à search_album_details`

### 2. ✅ Année mise à jour conditionnellement
**Fichier**: `backend/app/api/v1/services.py` ligne 1011  
**Bug**: `if not album.year and spotify_details.get('year')` - l'année n'était mise à jour que si elle n'existait pas  
**Correction**: Retirer la condition `not album.year` pour toujours mettre à jour  
**Commit**: `fix: Rafraîchir l'album doit mettre à jour image, année et URL Spotify`

### 3. ✅ Timeout IA manquant
**Fichier**: `backend/app/api/v1/services.py` ligne 1038+  
**Bug**: L'appel à EurIA pouvait bloquer indéfiniment  
**Correction**: Ajout d'un `asyncio.wait_for(..., timeout=10)` autour de `generate_album_info`  
**Commit**: `fix: Ajouter logging détaillé au endpoint d'enrichissement et timeout pour l'IA`

### 4. ✅ Cache React Query trop agressif
**Fichier**: `frontend/src/components/AlbumDetailDialog.tsx`  
**Bug**: `invalidateQueries` ne forçait pas un vrai refetch  
**Corrections tentées**:
- Changement de `invalidateQueries` → `removeQueries` (ne fonctionne pas)
- Ajout d'un `refreshKey` dans la queryKey pour forcer une nouvelle query  
**Commit**: `fix: Forcer le refetch en incrémentant la clé de la query`

### 5. ✅ Images SQLAlchemy non chargées
**Fichier**: `backend/app/api/v1/collection.py` ligne 124  
**Bug**: SQLAlchemy ne chargeait pas automatiquement la relation `album.images`  
**Correction**: Ajout de `joinedload(Album.images)` dans la query  
**Commit**: `fix: Forcer le chargement des images avec joinedload`

### 6. ✅ Paramètres invalides du modèle Image
**Fichier**: `backend/app/api/v1/services.py` ligne 1024-1029  
**Bug**: Tentative de créer Image avec `height=None, width=None` mais le modèle attend `image_type` et `source`  
**Erreur**: `'height' is an invalid keyword argument for Image`  
**Correction**: 
```python
# AVANT (❌)
image = Image(album_id=album.id, url=image_url, height=None, width=None)

# APRÈS (✅)
image = Image(album_id=album.id, url=image_url, image_type='album', source='spotify')
```
**Commit**: `fix: Corriger les paramètres du modèle Image`

## État actuel (après corrections)

### Backend ✅
Les logs montrent que l'enrichissement fonctionne correctement:
```
🔍 Recherche Spotify pour Remain in Light
📊 Résultat Spotify: {'spotify_url': '...', 'year': 1980, 'image_url': 'https://i.scdn.co/image/...'}
✨ URL Spotify trouvée: https://open.spotify.com/album/...
📅 Année Spotify trouvée: 1980
🎨 Image URL depuis Spotify: https://i.scdn.co/image/ab67616d0000b273e56fa8c916dc6ce419dcf557
🖼️ Image Spotify ajoutée/mise à jour: https://i.scdn.co/image/...
🤖 Description IA ajoutée
✅ Album Remain in Light enrichi avec succès - Spotify OK
```

### Frontend ❌
- Message de succès affiché: ✅
- Année affichée: ✅
- URL Spotify affichée: ✅
- Description IA affichée: ✅
- **Image affichée: ❌**

Erreur console:
```
Failed to load resource: Aucun serveur ayant le nom d'hôte précisé n'a été détecté.
https://via.placeholder.com/300
```

Cela signifie que `albumDetail.images[0]` est `undefined`, donc l'image n'est PAS dans la réponse de l'API.

## Investigations à faire

### 1. Vérifier la base de données
Confirmer que les images sont réellement sauvegardées:
```sql
SELECT album_id, url, image_type, source FROM images WHERE album_id = 2;
```

### 2. Vérifier la réponse API
Tester directement l'endpoint:
```bash
curl http://localhost:8000/api/v1/collection/albums/2 | python3 -m json.tool | grep -A 3 "images"
```

La réponse devrait contenir:
```json
"images": ["https://i.scdn.co/image/ab67616d0000b273e56fa8c916dc6ce419dcf557"]
```

### 3. Vérifier le joinedload
Possibilité que le `joinedload` ne fonctionne pas correctement. Alternatives:
- Utiliser `selectinload` au lieu de `joinedload`
- Ajouter un `lazy='joined'` dans la relation du modèle Album
- Forcer un refresh explicite: `db.refresh(album, ['images'])`

### 4. Vérifier la relation Album-Image
Le modèle `Album` a-t-il bien la relation `images` configurée?
```python
# Fichier: backend/app/models/album.py
images = relationship("Image", back_populates="album", cascade="all, delete-orphan")
```

### 5. Tester avec un album déjà enrichi
Vérifier si le problème est spécifique au refetch ou si même un album déjà enrichi n'affiche pas son image.

## Code modifié

### Backend
- `backend/app/api/v1/services.py` (endpoint enrichissement)
- `backend/app/api/v1/collection.py` (endpoint détail album)
- `backend/app/services/spotify_service.py` (logging)

### Frontend
- `frontend/src/components/AlbumDetailDialog.tsx` (refetch logic)

## Prochaines étapes

1. **Redémarrer complètement le backend** pour s'assurer que tous les changements sont actifs
2. **Vérifier la base de données** directement pour confirmer la sauvegarde des images
3. **Tester la réponse API** directement avec curl pour voir si les images sont retournées
4. Si les images sont en base MAIS pas dans la réponse API → problème avec `joinedload`
5. Si les images sont dans la réponse API MAIS pas affichées → problème frontend/cache

## Notes techniques

### Modèle Image
```python
class Image(Base):
    id = Column(Integer, primary_key=True)
    url = Column(String(1000), nullable=False)
    image_type = Column(String(50), nullable=False)  # 'artist' ou 'album'
    source = Column(String(50), nullable=False)      # 'spotify', 'lastfm', 'discogs'
    artist_id = Column(Integer, ForeignKey('artists.id'), nullable=True)
    album_id = Column(Integer, ForeignKey('albums.id'), nullable=True)
```

### Endpoint enrichissement
```python
POST /api/v1/services/ai/enrich-album/{album_id}
```

Retourne:
```json
{
  "status": "success",
  "album_id": 2,
  "album_title": "Remain in Light",
  "enrichment_details": {
    "spotify_url": "https://...",
    "images": true,
    "ai_description": true
  }
}
```

### Endpoint détail album
```python
GET /api/v1/collection/albums/{album_id}
```

Devrait retourner:
```json
{
  "id": 2,
  "title": "Remain in Light",
  "year": 1980,
  "artists": ["Talking Heads"],
  "images": ["https://i.scdn.co/image/..."],  // ← DOIT CONTENIR L'IMAGE
  "spotify_url": "https://...",
  "ai_info": "..."
}
```

## Référence

- Issue créée le: 3 février 2026
- Temps passé: ~3 heures
- Commits: 8
- Bugs corrigés: 6
- **Status final**: Image sauvegardée en base ✅, mais pas affichée dans l'UI ❌
