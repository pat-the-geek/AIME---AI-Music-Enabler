# 🔧 Corrections Erreurs Synchronisation Discogs

**Date**: 30 janvier 2026  
**Erreurs rapportées**: 404 release not found + 500 Internal Server Error

## 🐛 Problèmes Identifiés

### Erreur 1: 404 Release Not Found
```
WARNING - ⚠️ Erreur traitement release: 404: That release does not exist or may have been deleted.
```

**Cause**: Certains releases Discogs référencés dans la collection n'existent plus ou sont privés.

**Impact**: ✅ **Déjà géré** - Le warning apparaît mais la synchronisation continue grâce au `try/except` dans `discogs_service.py`

### Erreur 2: 500 Internal Server Error sur `/discogs/sync`
```
"POST /api/v1/services/discogs/sync HTTP/1.1" 500 Internal Server Error
```

**Cause**: 
- Pas de gestion d'erreur dans la boucle d'import des albums
- Données invalides (année = 0, artistes vides, formats manquants) causaient des exceptions non gérées
- Un seul album invalide bloquait toute la synchronisation

**Solution appliquée**:
1. Ajout d'un `try/except` autour de chaque album
2. Validation des données avant insertion :
   - Artistes vides filtrés
   - Année 0 convertie en NULL
   - Utilisation de `.get()` pour les champs optionnels
3. Compteur d'erreurs pour le rapport final
4. `db.rollback()` pour chaque album en erreur (pas toute la transaction)

### Erreur 3: 500 Internal Server Error sur `/collection/albums`
```
"GET /api/v1/collection/albums?page=1&page_size=30 HTTP/1.1" 500 Internal Server Error
```

**Cause**:
- Utilisation de `query.join(Metadata)` qui excluait les albums sans métadonnées
- Pas de gestion d'erreur dans la boucle de formatage
- Albums avec relations manquantes causaient des exceptions

**Solution appliquée**:
1. Remplacement `join(Metadata)` → `outerjoin(Album.album_metadata)`
2. Ajout de vérifications `.if album.artists else []`
3. Ajout d'un `try/except` dans la boucle de formatage
4. Log des erreurs sans bloquer l'affichage des autres albums

## ✅ Corrections Apportées

### Fichier 1: `backend/app/api/v1/services.py`

#### Changement 1: Gestion d'erreur par album
```python
# ❌ Avant
for album_data in albums_data:
    # Pas de try/except
    album = Album(...)
    db.add(album)
    synced_count += 1

# ✅ Après
for album_data in albums_data:
    try:
        # Validation des données
        if not artists:
            logger.warning(f"⚠️ Album sans artiste ignoré: {title}")
            error_count += 1
            continue
        
        # Normaliser l'année
        year = album_data.get('year')
        if year == 0:
            year = None
        
        album = Album(...)
        db.add(album)
        synced_count += 1
        
    except Exception as e:
        logger.error(f"❌ Erreur import album: {e}")
        error_count += 1
        db.rollback()  # Rollback cet album seulement
        continue
```

#### Changement 2: Validation des données
```python
# Artistes vides filtrés
for artist_name in album_data['artists']:
    if not artist_name or not artist_name.strip():
        continue

# Année 0 = NULL
year = album_data.get('year')
if year == 0:
    year = None

# Champs optionnels avec .get()
discogs_url=album_data.get('discogs_url')
if album_data.get('cover_image'):
    # ...
```

#### Changement 3: Rapport détaillé
```python
# Nouveau champ error_count
return {
    "status": "success",
    "synced_albums": synced_count,
    "skipped_albums": skipped_count,
    "error_albums": error_count,  # ← NOUVEAU
    "total_albums": len(albums_data)
}
```

### Fichier 2: `backend/app/api/v1/collection.py`

#### Changement 1: Outer join pour métadonnées
```python
# ❌ Avant - exclut albums sans métadonnées
if is_soundtrack is not None:
    query = query.join(Metadata).filter(...)

# ✅ Après - inclut tous les albums
if is_soundtrack is not None:
    query = query.outerjoin(Album.album_metadata).filter(...)
```

#### Changement 2: Gestion d'erreur dans formatage
```python
# ❌ Avant
for album in albums:
    artists = [a.name for a in album.artists]
    # Si album.artists est None → CRASH

# ✅ Après
for album in albums:
    try:
        artists = [a.name for a in album.artists] if album.artists else []
        images = [img.url for img in album.images] if album.images else []
        # ...
    except Exception as e:
        logger.error(f"Erreur formatage album {album.id}: {e}")
        continue  # Passe au suivant
```

## 🧪 Tests à Réaliser

### 1. Redémarrer le backend
```bash
# Arrêter le backend actuel
killall uvicorn 2>/dev/null

# Redémarrer avec le script
cd "/Users/patrickostertag/Documents/DataForIA/AIME - AI Music Enabler"
./scripts/start-dev.sh
```

### 2. Test synchronisation complète
```bash
# Relancer la synchronisation (devrait gérer les erreurs)
curl -X POST "http://localhost:8000/api/v1/services/discogs/sync"

# Vérifier le rapport - devrait retourner:
# {
#   "status": "success",
#   "synced_albums": XX,
#   "skipped_albums": YY,
#   "error_albums": ZZ,
#   "total_albums": 235
# }
```

### 3. Test API albums
```bash
# Vérifier que la liste s'affiche
curl "http://localhost:8000/api/v1/collection/albums?page_size=10" | python3 -m json.tool

# Devrait retourner un JSON avec items[], pas d'erreur 500
```

### 4. Validation base de données
```bash
# Compter les albums
sqlite3 data/musique.db "SELECT COUNT(*) FROM albums;"

# Voir les albums avec/sans métadonnées
sqlite3 data/musique.db "
SELECT 'Albums avec metadata: ' || COUNT(*) FROM metadata;
SELECT 'Albums total: ' || COUNT(*) FROM albums;
"
```

### 5. Vérifier les logs
```bash
# Dans le terminal où tourne le backend, chercher:
# ⚠️ Album sans artiste ignoré: ...
# ❌ Erreur import album: ...
# ✅ Synchronisation terminée: X albums ajoutés, Y ignorés, Z erreurs
```

## 📊 Comportement Attendu

### Synchronisation Discogs
- ✅ Continue même si certains releases sont introuvables (404)
- ✅ Continue même si certains albums ont des données invalides
- ✅ Log les erreurs sans bloquer le processus
- ✅ Retourne un rapport détaillé avec compteurs

### API Collection Albums
- ✅ Affiche tous les albums, même sans métadonnées
- ✅ Gère les relations manquantes (artistes, images)
- ✅ Ne crash pas si un album pose problème
- ✅ Log les erreurs de formatage

## 🎯 Résumé

**Avant ces corrections**:
- ❌ Un release 404 → WARNING mais OK
- ❌ Un album invalide → CRASH de toute la synchronisation
- ❌ Un album sans metadata → Invisible dans l'API
- ❌ Un album avec relation cassée → 500 Error

**Après ces corrections**:
- ✅ Release 404 → WARNING, continue
- ✅ Album invalide → ERROR log, continue avec les autres
- ✅ Album sans metadata → Visible dans l'API avec metadata=null
- ✅ Album avec problème → Log error, continue avec les autres

**Résultat**: La synchronisation est maintenant **robuste et tolérante aux erreurs** 💪

## 🚀 Prochaines Étapes

1. **Redémarrer le backend** pour appliquer les corrections
2. **Relancer la synchronisation complète** Discogs
3. **Vérifier le rapport final** avec les compteurs d'erreurs
4. **Tester l'interface web** pour voir tous les albums

---

*Ces corrections garantissent que votre application continuera de fonctionner même avec des données Discogs imparfaites.*
