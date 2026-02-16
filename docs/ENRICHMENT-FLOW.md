# Flux d'enrichissement des albums

Ce document décrit le flux complet d'enrichissement des albums dans AIME, incluant les URLs Spotify, Apple Music, les images et les informations IA.

## Vue d'ensemble

Tous les albums créés dans le système passent par un processus d'enrichissement automatique qui ajoute :

- **URL Spotify** : Lien direct vers l'album sur Spotify
- **URL Apple Music** : Lien de recherche vers l'album sur Apple Music
- **Année de publication** : Récupérée depuis Spotify
- **Images** : Depuis Spotify, Last.fm, Discogs (selon la source)
- **Informations IA** : Description générée par Euria AI

## Services d'enrichissement

### AppleMusicService
**Localisation** : `backend/app/services/apple_music_service.py`

Génère des URLs de recherche Apple Music basées sur le nom de l'artiste et le titre de l'album.

```python
url = AppleMusicService.generate_url_for_album(artist_name, album_title)
# Retourne: https://music.apple.com/search?term=Album+Title+Artist+Name
```

**Note** : Pour l'instant, génère des URLs de recherche. Peut être amélioré avec :
- Appel à l'API Apple Music pour obtenir des liens directs
- Utilisation de l'API Euria pour générer des URLs directes
- Cache des résultats

### SpotifyService
**Localisation** : `backend/app/services/spotify_service.py`

Récupère les détails complets de l'album depuis Spotify :
- URL directe
- Année de publication
- Image de couverture
- Genre (optionnel)

### AIService (Euria)
**Localisation** : `backend/app/services/external/ai_service.py`

Génère des descriptions AI complètes pour les albums via l'API Euria (Infomaniak + Mistral).

## Points d'entrée de création d'albums

### 1. TrackerService - Détection automatique Last.fm
**Localisation** : `backend/app/services/tracker_service.py` ligne 553-625

**Déclenchement** : Polling automatique Last.fm détecte un nouvel album

**Enrichissement effectué** :
- ✅ URL Spotify + année (via SpotifyService)
- ✅ URL Apple Music (via AppleMusicService)
- ✅ Priorité Last.fm pour les images (Last.fm > Spotify > Discogs)
- ✅ Informations IA (via Euria)
- ✅ Support='Lastfm' pour les détections Last.fm (non-Discogs)

**Pour les albums existants** (lignes 605-625) :
- ✅ Vérifie et ajoute URL Spotify si manquante
- ✅ Vérifie et ajoute année si manquante
- ✅ Vérifie et ajoute URL Apple Music si manquante
- ✅ Vérifie et ajoute images (Last.fm prioritaire)

**Nettoyage des images** :
- Supprime automatiquement les images Spotify quand une image Last.fm est définie
- Évite les doublons et la priorité incorrecte

## Gestion des images - Priorité et Cache-busting

### Priorité des sources d'images

L'enrichissement respecte cette hiérarchie pour les images d'album :

1. **Last.fm** - Images depuis Last.fm (priorité maximale pour détections Last.fm)
2. **Spotify** - Images depuis l'API Spotify (fallback)
3. **Discogs** - Images depuis Discogs (fallback)

### Cache-busting des images

Pour forcer le navigateur à recharger les images lors de mises à jour, tous les URLs d'images incluent un paramètre timestamp :

```
https://example.com/cover.jpg?t=1707900000
```

**Fichiers concernés** :
- `backend/app/services/collection/album_service.py` (lignes 241, 279, 716) - Albums et artistes
- `backend/app/api/v1/content/history.py` (lignes 130, 139, 143) - Timeline et Journal

Le timestamp est généré à partir de l'`updated_at` de l'image dans la base de données. Lors de chaque modification d'image, le timestamp change automatiquement, invalidant le cache du navigateur.

## Scripts d'enrichissement rétroactif

### enrich_lastfm_latest_detection.py
**Localisation** : `backend/enrich_lastfm_latest_detection.py`

Script pour enrichir rétroactivement les N détections Last.fm les plus récentes avec les images et métadonnées correctes.

```bash
cd backend
python3 enrich_lastfm_latest_detection.py
```

**Fonctionnalités** :
- Recherche les 2 dernières détections Last.fm
- Appelle l'API Spotify pour valider l'album et obtenir l'image
- Appelle l'API Last.fm pour obtenir l'image Last.fm
- Priorité Last.fm > Spotify
- Supprime les images Spotify quand une image Last.fm est trouvée
- Génère les métadonnées IA (description)
- Définit support='Lastfm' pour les albums non-Discogs

**Configuration requise** :
- Secrets dans `config/secrets.json`
- Services API : Spotify, Last.fm, Euria

**Actions possibles** :
- Modifier la limite de détections : modifier `limit=2` ligne 58
- Ajouter un filtre d'artiste : modifier la clause `filter_by()`

### 2. AlbumService - Création manuelle via API
**Localisation** : `backend/app/services/collection/album_service.py` ligne 298-320

**Déclenchement** : POST `/api/v1/collection/albums`

**Enrichissement effectué** :
- ✅ URL Apple Music (si non fournie)
- ⚠️ URL Spotify (si fournie par l'utilisateur)

**Note** : L'enrichissement Spotify n'est pas automatique pour la création manuelle. L'utilisateur doit fournir l'URL ou l'ajouter ultérieurement.

### 3. DiscogsService - Synchronisation Discogs
**Localisation** : `backend/app/api/v1/tracking/services.py` ligne 1769-1790

**Déclenchement** : POST `/api/v1/tracking/discogs-sync`

**Enrichissement effectué** :
- ✅ URL Spotify
- ✅ URL Apple Music
- ✅ Image Discogs
- ✅ Métadonnées (labels, formats, etc.)
- ⚠️ IA enrichie APRÈS avec `/ai/enrich-all`

### 4. LastFMService - Import CSV/historique
**Localisation** : `backend/app/api/v1/tracking/services.py` ligne 3016-3180

**Déclenchement** : POST `/api/v1/tracking/lastfm-import`

**Enrichissement effectué** :
- ⚠️ Création minimale (title uniquement)
- ✅ Enrichissement différé via `SchedulerService.enrich_imported_albums()`

**Note** : Les albums créés ici sont marqués pour enrichissement en arrière-plan. L'enrichissement complet est effectué par le TrackerService.

### 5. AlbumCollectionService - Collections IA
**Localisation** : `backend/app/services/album_collection_service.py` ligne 992-1040

**Déclenchement** : Création de collections via IA (découverte web)

**Enrichissement effectué** :
- ✅ URL Spotify + année + image Spotify
- ✅ URL Apple Music
- ⚠️ Image Last.fm (fallback si Spotify échoue)
- ⚠️ Exclut les albums sans image

## Statistiques actuelles

D'après l'analyse du 2026-02-14 :

- **Albums totaux** : 1690
- **Avec URL Spotify** : 275 (16%)
- **Avec URL Apple Music** : 1690 (100%)

## Scripts d'enrichissement batch

### enrich_apple_music_urls.py
**Localisation** : `scripts/enrichment/enrich_apple_music_urls.py`

Script pour enrichir tous les albums existants avec des URLs Apple Music.

```bash
cd /path/to/backend
python3 ../scripts/enrichment/enrich_apple_music_urls.py
```

**Résultat dernière exécution** :
- 1690 albums traités
- 474 URLs directes trouvées via Euria
- 1216 URLs de recherche générées

### update_all_album_descriptions.py
**Localisation** : `backend/update_all_album_descriptions.py`

Script pour regénérer les descriptions longues d'albums via EurIA.

```bash
cd backend
python3 update_all_album_descriptions.py
```

**Options utiles** :
- `--only-missing` : ne traite que les albums sans `metadata.ai_info`
- `--only-discogs` : ne traite que les albums importés depuis Discogs
- `--limit 50` : limite le nombre d'albums traités
- `--delay 1.0` : pause entre les appels IA (secondes)
- `--dry-run` : exécution sans écriture en base

### Enrichissement Spotify
**Endpoint API** : POST `/api/v1/tracking/enrich-spotify`

Enrichit tous les albums existants avec des URLs Spotify et années de publication.

## Logs d'enrichissement

Les logs utilisent des emojis pour faciliter le suivi :

- 🎵 : URL Spotify ajoutée
- 🍎 : URL Apple Music ajoutée
- 📅 : Année ajoutée
- 🎨 : Image ajoutée
- 🤖 : Informations IA générées

## Prochaines améliorations

1. **Apple Music direct URLs** : Utiliser l'API Apple Music ou Euria pour obtenir des liens directs
2. **Cache des enrichissements** : Éviter les appels API redondants
3. **Enrichissement Spotify automatique** : Ajouter l'enrichissement Spotify à la création manuelle
4. **File d'attente d'enrichissement** : Gérer l'enrichissement asynchrone avec une queue
5. **Détection des échecs** : Marquer les albums qui ont échoué l'enrichissement pour réessayer

## Tests

Vérifier l'enrichissement complet d'un album :

```bash
curl 'http://localhost:8000/api/v1/collection/albums/1' | jq '{
  title: .title,
  spotify_url: .spotify_url,
  apple_music_url: .apple_music_url,
  year: .year,
  images: (.images | length),
  ai_info: (.ai_info != null)
}'
```

Résultat attendu :
```json
{
  "title": "Album Title",
  "spotify_url": "https://open.spotify.com/album/...",
  "apple_music_url": "https://music.apple.com/...",
  "year": 2020,
  "images": 2,
  "ai_info": true
}
```
