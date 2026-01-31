# Correction: Séparation des albums Discogs des écoutes

## Résumé des modifications

La collection Discogs contenait des albums provenant des écoutes (Last.fm, Roon) avec des types de support invalides. Cette correction sépare correctement les albums Discogs des albums d'écoutes.

## Modifications effectuées

### 1. Modèle Album (backend/app/models/album.py)
- **Ajout d'une colonne `source`** : identifie l'origine de chaque album
  - `discogs` : Albums de la collection Discogs
  - `lastfm` : Albums importés des écoutes Last.fm
  - `roon` : Albums importés des écoutes Roon
  - `spotify` : Albums importés depuis Spotify
  - `manual` : Albums ajoutés manuellement (par défaut)

- **Ajout de méthodes de validation** :
  - `is_collection_album()` : vérifie si c'est un album Discogs
  - `is_valid_support()` : valide que le support est approprié pour la source
    - **Pour Discogs** : accepte uniquement Vinyle, CD, Digital, Cassette ou NULL
    - **Pour autres sources** : tous les supports sont acceptés

- **Nouvelle énumération `AlbumSource`** : définit les sources possibles

### 2. Service de synchronisation Discogs (backend/app/api/v1/services.py)
- Les albums créés lors de la synchronisation Discogs sont maintenant marqués avec `source='discogs'`

### 3. Services de tracking
- **tracker_service.py** : Les albums Last.fm sont marqués avec `source='lastfm'`
- **roon_tracker_service.py** : Les albums Roon sont marqués avec `source='roon'` avec `support='Roon'`

### 4. API Collection (backend/app/api/v1/collection.py)
- Le endpoint `/albums` filtre maintenant **uniquement les albums Discogs** (`source='discogs'`)
- Les albums d'écoutes sont complètement séparés

### 5. Migration de base de données (backend/migrate_add_source.py)
Migration appliquée à la base de données existante :

```
📊 Résumé après migration:
Albums par source:
  - discogs: 235 ✓
  - manual: 159
  - roon: 1
Albums Discogs par support:
  - Vinyle: 154
  - CD: 78
  - Unknown: 3
```

## Résultats

### État avant correction
- ❌ 236 albums Discogs mélangés avec les écoutes
- ❌ Impossible de distinguer les sources
- ❌ Type de support erroné (Roon) dans les albums Discogs

### État après correction
- ✅ 235 albums Discogs identifiés et marqués
- ✅ Support valide pour tous les albums Discogs (Vinyle, CD, Unknown)
- ✅ 1 album Roon identifié comme provenant de l'historique d'écoute
- ✅ Collection Discogs clean et séparée des écoutes
- ✅ API collection retourne uniquement les albums Discogs

## Fichiers modifiés

1. **backend/app/models/album.py**
   - Ajout colonne `source`
   - Ajout classe `AlbumSource`
   - Ajout méthodes de validation

2. **backend/app/api/v1/services.py**
   - Ajout `source='discogs'` lors de la création d'albums Discogs

3. **backend/app/api/v1/collection.py**
   - Filtre sur `source='discogs'` dans l'endpoint de liste

4. **backend/app/services/tracker_service.py**
   - Ajout `source='lastfm'` lors de la création d'albums Last.fm

5. **backend/app/services/roon_tracker_service.py**
   - Ajout `source='roon'` lors de la création d'albums Roon

6. **backend/migrate_add_source.py** (nouveau)
   - Script de migration pour ajouter la colonne `source`

7. **backend/alembic/versions/001_add_source_column.py** (nouveau)
   - Migration Alembic pour versioning

8. **backend/alembic/versions/002_fix_invalid_supports.py** (nouveau)
   - Correction des supports invalides

9. **backend/init_db.py** (nouveau)
   - Script d'initialisation de la BD

## Fonctionnement

### Lors de la synchronisation Discogs
```python
album = Album(
    title=title,
    source='discogs',  # ← Marqué comme Discogs
    support=support,   # Vinyle, CD, Digital
    discogs_id=discogs_id,
    ...
)
```

### Lors du tracking Last.fm
```python
album = Album(
    title=title,
    source='lastfm',   # ← Marqué comme Last.fm
    ...
)
```

### Lors du tracking Roon
```python
album = Album(
    title=title,
    source='roon',     # ← Marqué comme Roon
    support='Roon',    # Support Roon, pas Vinyle/CD/Digital
    ...
)
```

### API Collection
```python
# Filtre automatique sur les albums Discogs uniquement
query = db.query(Album).filter(Album.source == 'discogs')
```

## Validation

La collection Discogs est maintenant:
- ✅ Clairement séparée des écoutes
- ✅ Avec source correctement identifiée
- ✅ Avec supports valides (Vinyle/CD/Digital)
- ✅ Accessible via l'API sans mélange avec les autres sources

Les albums d'écoutes peuvent désormais être:
- Gérés dans une collection séparée si souhaité
- Utilisés pour l'historique d'écoute
- Analysés indépendamment des albums Discogs
