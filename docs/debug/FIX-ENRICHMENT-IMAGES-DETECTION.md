# Correction: Enrichissement des images lors de la détection de lecture

**Date**: 3 février 2026  
**Problème**: Les artistes et albums détectés lors de la lecture ne récupèrent pas leurs images depuis Spotify  
**Exemple**: Durand Bernarr / BLOOM

## 🔍 Analyse du problème

### Symptômes
L'artiste "Durand Bernarr" et l'album "BLOOM" existent dans Spotify avec des URLs valides:
- Artiste: https://open.spotify.com/intl-fr/artist/2d6ggH1oVt4z2zCuY2u5DW
- Album: https://open.spotify.com/intl-fr/album/756LreEk5nDrKn0FyiVJNH

Mais lors de la détection de lecture, les images n'étaient pas récupérées.

### Cause racine
Dans les services de tracking (`roon_tracker_service.py` et `tracker_service.py`), la logique d'enrichissement Spotify était exécutée **uniquement pour les nouveaux artistes et albums** lors de leur création:

```python
# Ancien code - PROBLÉMATIQUE
artist = db.query(Artist).filter_by(name=artist_name).first()
if not artist:
    # Création + enrichissement Spotify
    artist = Artist(name=artist_name)
    db.add(artist)
    artist_image = await self.spotify.search_artist_image(artist_name)
    # ...
# ❌ Si l'artiste existe déjà, rien n'est fait!
```

Si un artiste ou album était créé **avant l'activation du service Spotify** ou si l'enrichissement avait échoué précédemment, il restait sans image même lors des lectures suivantes.

## ✅ Solution implémentée

### Modifications dans `roon_tracker_service.py`

#### 1. Enrichissement des artistes existants (lignes 274-307)
Ajout d'un bloc `else` pour enrichir les artistes existants sans images:

```python
artist = db.query(Artist).filter_by(name=artist_name).first()
if not artist:
    # Nouveau artiste : création + enrichissement
    artist = Artist(name=artist_name)
    db.add(artist)
    db.flush()
    
    artist_image = await self.spotify.search_artist_image(artist_name)
    if artist_image:
        img = Image(url=artist_image, image_type='artist', 
                   source='spotify', artist_id=artist.id)
        db.add(img)
        logger.info(f"🎤 Image artiste créée pour nouveau artiste: {artist_name}")
else:
    # ✅ NOUVEAU: Artiste existant sans image
    has_artist_image = db.query(Image).filter_by(
        artist_id=artist.id,
        image_type='artist'
    ).first() is not None
    
    if not has_artist_image:
        artist_image = await self.spotify.search_artist_image(artist_name)
        if artist_image:
            img = Image(url=artist_image, image_type='artist',
                       source='spotify', artist_id=artist.id)
            db.add(img)
            logger.info(f"🎤 Image artiste ajoutée pour artiste existant: {artist_name}")
```

#### 2. Enrichissement des albums existants (lignes 310-396)
Ajout d'une logique complète pour enrichir les albums existants:

```python
album = db.query(Album).filter(
    Album.title == album_title,
    Album.artists.any(Artist.id == artist.id)
).first()

if not album:
    # Nouvel album : création + enrichissement complet
    # ...
else:
    # ✅ NOUVEAU: Album existant - enrichissement si manquant
    needs_update = False
    
    # Vérifier URL Spotify et année
    if not album.spotify_url or not album.year:
        spotify_details = await self.spotify.search_album_details(artist_name, album_title)
        if spotify_details:
            if not album.spotify_url and spotify_details.get("spotify_url"):
                album.spotify_url = spotify_details["spotify_url"]
                logger.info(f"🎵 URL Spotify ajoutée pour album existant: {album_title}")
                needs_update = True
            
            if not album.year and spotify_details.get("year"):
                album.year = spotify_details["year"]
                logger.info(f"📅 Année ajoutée pour album existant: {album_title}")
                needs_update = True
            
            # Vérifier image Spotify
            if spotify_details.get("image_url"):
                has_album_image = db.query(Image).filter_by(
                    album_id=album.id,
                    image_type='album',
                    source='spotify'
                ).first() is not None
                
                if not has_album_image:
                    img = Image(url=spotify_details["image_url"],
                               image_type='album', source='spotify',
                               album_id=album.id)
                    db.add(img)
                    logger.info(f"🖼️ Image album ajoutée pour album existant: {album_title}")
                    needs_update = True
    else:
        # Si URL et année existent, vérifier uniquement l'image
        has_album_image = db.query(Image).filter_by(
            album_id=album.id,
            image_type='album',
            source='spotify'
        ).first() is not None
        
        if not has_album_image:
            album_image = await self.spotify.search_album_image(artist_name, album_title)
            if album_image:
                img = Image(url=album_image, image_type='album',
                           source='spotify', album_id=album.id)
                db.add(img)
                logger.info(f"🖼️ Image album ajoutée pour album existant: {album_title}")
                needs_update = True
```

### Modifications dans `tracker_service.py`

Ajout de la même logique pour les artistes existants (lignes 238-271):

```python
artist = db.query(Artist).filter_by(name=artist_name).first()
if not artist:
    # Nouveau artiste : création + enrichissement
    # ...
else:
    # ✅ NOUVEAU: Artiste existant sans image
    has_artist_image = db.query(Image).filter_by(
        artist_id=artist.id,
        image_type='artist'
    ).first() is not None
    
    if not has_artist_image:
        artist_image = await self.spotify.search_artist_image(artist_name)
        if artist_image:
            img = Image(url=artist_image, image_type='artist',
                       source='spotify', artist_id=artist.id)
            db.add(img)
            logger.info(f"🎤 Image artiste ajoutée pour artiste existant: {artist_name}")
```

**Note**: Le `tracker_service.py` avait déjà une bonne gestion pour les albums existants (lignes 296-345), seule la gestion des artistes a été ajoutée.

## 🧪 Validation

### Script de test créé: `scripts/test_durand_bernarr.py`

Le script effectue:
1. ✅ Recherche directe sur l'API Spotify
2. ✅ Vérification de l'état en base de données
3. ✅ Simulation de l'enrichissement automatique
4. ✅ Affichage de l'état final

### Résultats du test

```
======================================================================
🔍 TEST RECHERCHE SPOTIFY DIRECTE
======================================================================

🎤 Recherche artiste 'Durand Bernarr'...
✅ Image artiste trouvée: https://i.scdn.co/image/ab6761610000e5ebb6f813bbf413ca4864b8c5aa

📀 Recherche album 'BLOOM' par 'Durand Bernarr'...
✅ Album trouvé:
   - URL: https://open.spotify.com/album/756LreEk5nDrKn0FyiVJNH
   - Année: 2025
   - Image: https://i.scdn.co/image/ab67616d0000b2739ea37a683bcf3f56b9f42a9f

======================================================================
📊 ÉTAT FINAL
======================================================================

🎤 Artiste: Durand Bernarr
   - Images: 1

📀 Album: BLOOM
   - URL Spotify: https://open.spotify.com/album/756LreEk5nDrKn0FyiVJNH
   - Année: 2025
   - Images: 1
```

### Vérification en base de données

```sql
-- Artiste
SELECT a.id, a.name, i.source, i.url 
FROM artists a 
LEFT JOIN images i ON a.id = i.artist_id 
WHERE a.name='Durand Bernarr';

-- Résultat:
669|Durand Bernarr|spotify|https://i.scdn.co/image/ab6761610000e5ebb6f813bbf413ca4864b8c5aa

-- Album
SELECT al.id, al.title, al.spotify_url, al.year, i.source, i.url 
FROM albums al 
LEFT JOIN images i ON al.id = i.album_id 
WHERE al.title='BLOOM';

-- Résultat:
1408|BLOOM|https://open.spotify.com/album/756LreEk5nDrKn0FyiVJNH|2025|spotify|https://i.scdn.co/image/ab67616d0000b2739ea37a683bcf3f56b9f42a9f
```

## 📊 Impact

### Bénéfices
1. **Auto-réparation**: Les artistes/albums existants sans images sont maintenant enrichis automatiquement lors de la prochaine lecture
2. **Cohérence**: Tous les artistes/albums auront systématiquement leurs images Spotify
3. **Robustesse**: Le système récupère automatiquement les échecs d'enrichissement passés

### Cas d'usage corrigés
- ✅ Artistes créés avant l'activation du service Spotify
- ✅ Albums dont l'enrichissement Spotify avait échoué (timeout, rate limit, etc.)
- ✅ Données importées sans enrichissement (import Discogs, etc.)

### Performance
- Impact minimal : une seule requête Spotify par artiste/album manquant, uniquement lors de la première lecture après correction
- Les images sont mises en cache en base, aucun appel répété

## 🎯 Prochaines lectures

Lors de la **prochaine lecture** d'un morceau de "Durand Bernarr" ou de l'album "BLOOM":
1. Le tracker détectera l'artiste et l'album existants
2. Vérifiera qu'ils ont maintenant leurs images
3. Ne fera **aucun appel Spotify supplémentaire** (optimisation)
4. L'interface affichera correctement les images

## 📝 Notes techniques

### Optimisations implémentées
1. **Vérification d'existence** avant chaque appel Spotify
2. **Requêtes conditionnelles**: on ne cherche que ce qui manque (URL, année, ou image)
3. **Logs explicites** pour suivre l'enrichissement automatique
4. **Transaction unique**: tous les ajouts sont dans la même transaction DB

### Logs à surveiller
```
🎤 Image artiste ajoutée pour artiste existant: [nom]
🎵 URL Spotify ajoutée pour album existant: [titre]
📅 Année ajoutée pour album existant: [titre]
🖼️ Image album ajoutée pour album existant: [titre]
```

## ✅ Conclusion

Le problème est **complètement résolu**. Le système enrichit maintenant automatiquement les artistes et albums existants lors de la détection de lecture, garantissant que toutes les données Spotify (images, URL, année) sont progressivement complétées pour l'ensemble de la collection.

---

## 🔧 Correction supplémentaire : Stratégie de fallback pour la recherche Spotify

**Date**: 3 février 2026  
**Problème additionnel**: L'album "Wicked: One Wonderful Night (Live) – The Soundtrack" n'est pas trouvé sur Spotify  
**URL Spotify**: https://open.spotify.com/intl-fr/album/39ixJY2rOByyed4OmCmAe2

### 🔍 Analyse du problème

#### Test de recherche
```python
# Recherche avec artiste "Various Artists"
query = "artist:Various Artists album:Wicked: One Wonderful Night (Live) – The Soundtrack"
# Résultat: 0 albums trouvés ❌

# Recherche sans filtre d'artiste
query = "album:Wicked One Wonderful Night Live"
# Résultat: 1 album trouvé ✅
```

#### Cause racine
L'album existe bien sur Spotify (ID: `39ixJY2rOByyed4OmCmAe2`) mais les vrais artistes sont **Ariana Grande** et **Cynthia Erivo**, pas "Various Artists".

Quand un album est détecté dans Roon/Last.fm avec un artiste générique ("Various Artists", "Original Cast", etc.), la recherche Spotify avec `artist:Various Artists` échoue car ce n'est pas l'artiste enregistré sur Spotify.

### ✅ Solution : Stratégie de recherche en deux étapes

Modification du fichier [spotify_service.py](backend/app/services/spotify_service.py) :

#### 1. Fonction `search_album_image` (lignes 59-105)

```python
async def search_album_image(self, artist_name: str, album_title: str) -> Optional[str]:
    """Rechercher l'image d'un album sur Spotify."""
    try:
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            # Stratégie 1: Recherche avec artiste et album
            query = f"artist:{artist_name} album:{album_title}"
            response = await client.get(
                f"{self.api_base_url}/search",
                params={"q": query, "type": "album", "limit": 1},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            albums = data.get("albums", {}).get("items", [])
            if albums and albums[0].get("images"):
                logger.info(f"✅ Album trouvé avec artiste: {albums[0]['name']}")
                return albums[0]["images"][0]["url"]
            
            # ✅ NOUVEAU: Stratégie 2 - Recherche uniquement par titre (fallback)
            logger.info(f"⚠️ Recherche avec artiste échouée, essai sans artiste...")
            query_fallback = f"album:{album_title}"
            response = await client.get(
                f"{self.api_base_url}/search",
                params={"q": query_fallback, "type": "album", "limit": 1},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            
            albums = data.get("albums", {}).get("items", [])
            if albums and albums[0].get("images"):
                logger.info(f"✅ Album trouvé sans artiste: {albums[0]['name']}")
                return albums[0]["images"][0]["url"]
            
            return None
```

#### 2. Fonction `search_album_details` (lignes 113-173)

Même logique de fallback ajoutée pour récupérer URL, année et image.

### 🎯 Fonctionnement

1. **Première tentative** : Recherche avec `artist:{artist_name} album:{album_title}`
   - Si trouvé → Retour immédiat ✅
   - Si non trouvé → Passage à l'étape 2

2. **Deuxième tentative (fallback)** : Recherche avec `album:{album_title}` uniquement
   - Ignore le filtre d'artiste
   - Plus permissif mais toujours efficace pour les albums avec des titres distincts

### 🧪 Validation

Test avec l'album "Wicked" :

```
🔍 Test recherche album Wicked
   Artiste: Various Artists
   Album: Wicked: One Wonderful Night (Live) – The Soundtrack

📸 Test search_album_image...
✅ Image trouvée: https://i.scdn.co/image/ab67616d0000b273c111a1f33d362055e786fdf1

📊 Test search_album_details...
✅ Détails trouvés:
   URL: https://open.spotify.com/album/39ixJY2rOByyed4OmCmAe2
   Année: 2025
   Image: https://i.scdn.co/image/ab67616d0000b273c111a1f33d362055e786fdf1
```

### 📊 Impact

#### Cas d'usage corrigés
- ✅ Albums avec artistes génériques ("Various Artists", "Original Cast", "Soundtrack", etc.)
- ✅ Albums dont l'artiste diffère entre Roon/Last.fm et Spotify
- ✅ Compilations et bandes originales

#### Avantages
1. **Robustesse** : Le système trouve maintenant les albums même avec des métadonnées d'artiste imprécises
2. **Automatique** : Aucune intervention manuelle requise
3. **Performance** : Le fallback n'est appelé que si la première recherche échoue

#### Limitations potentielles
- Pour des titres d'albums très génériques, le fallback pourrait retourner un mauvais album
- Solution : Spotify retourne les albums les plus populaires en premier, ce qui minimise les faux positifs

### 📝 Logs à surveiller

```
⚠️ Recherche avec artiste échouée, essai sans artiste...
✅ Album trouvé sans artiste: [titre album]
```

Ces logs indiquent qu'un album a été trouvé grâce au fallback.
