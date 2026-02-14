# Discover - Collections d'Albums

## Vue d'ensemble

**Discover** est la nouvelle fonctionnalité permettant aux utilisateurs de découvrir et organiser des **collections d'albums** basées sur différents critères de recherche.

### 📍 Accès
- **Menu**: Sidebar/Navbar - "Discover" 
- **Route**: `/discover` (chemin interne: `/collections`)
- **Icône**: 🔍 (représente la découverte)

## Types de Collections

Quatre modes de recherche disponibles:

### 1. 🎵 Par Genre
**Recherche**: Entrez un genre musical (ex: "Jazz", "Rock", "Electronic")
- Filtre sur la colonne `Album.genre`
- Limite: 50 albums par collection
- Exemple: "Jazz Cool" retourne 20 albums

### 2. 👤 Par Artiste  
**Recherche**: Entrez un nom d'artiste (ex: "The Beatles", "Miles Davis")
- Recherche avec variantes de noms
- Supporte les variantes "The Artist" ↔ "Artist"
- Limite: 50 albums par collection

### 3. 📅 Par Période
**Recherche**: Sélectionnez une plage d'années (ex: 1990-1999)
- Filtre sur `Album.year` entre start_year et end_year
- Limite: 50 albums par collection

### 4. 🧠 Recherche IA Sémantique
**Recherche**: Décrivez le type de musique (ex: "musique mélancolique et atmosphérique")
- Recherche multi-champs enrichie:
  - `ai_description` - Description générée par IA
  - `ai_style` - Style/ambiance
  - `genre` - Genre musical
  - `title` - Titre de l'album
  - Artists - Noms d'artistes
- Tous les termes doivent matcher (AND logic)
- Limite: 50 albums par collection

## Fonctionnalités

### 🖼️ Aperçu Visuel des Collections
Chaque collection affiche un aperçu visuel avec jusqu'à 5 images d'albums:
- **Illustration automatique**: Les 5 premières couvertures d'albums de la collection
- **Présentation en grille**: Affichées horizontalement en haut de la carte
- **Interactivité**: Survolez pour voir les détails
- **Visibilité**: Permet d'identifier rapidement le contenu de la collection

### ➕ Créer une Collection
1. Cliquez "Nouvelle Collection"
2. Remplissez le nom (ex: "Rock des années 90")
3. Sélectionnez le type de recherche
4. Entrez le critère (genre, artiste, période, ou requête IA)
5. Validez - la collection est **auto-peuplée** avec 20 albums

### 👁️ Voir les Albums
1. Cliquez "Détails" sur une collection
2. Visualisez les 20 albums avec:
   - Couverture (si disponible)
   - Titre de l'album
   - Artiste principal
   - Année de sortie

### ▶️ Jouer sur Roon
1. Cliquez "Jouer" sur une collection
2. Sélectionnez la zone Roon (si plusieurs zones)
3. Le premier album commence immédiatement
4. Les albums suivants sont dans la queue Roon

> **Note**: Roon joue chaque album en entier. Utilisez les contrôles Roon pour passer au suivant.

### 🗑️ Supprimer une Collection
Cliquez l'icône corbeille pour supprimer la collection et ses albums.

## API Endpoints

### GET `/api/v1/collections/`
Liste toutes les collections
```bash
curl http://localhost:8000/api/v1/collections/
```

**Réponse:**
```json
[
  {
    "id": 1,
    "name": "Jazz Cool",
    "search_type": "genre",
    "search_criteria": {"genre": "Jazz"},
    "ai_query": null,
    "album_count": 20,
    "created_at": "2026-02-01T20:51:22",
    "sample_album_images": [
      "https://example.com/album1.jpg",
      "https://example.com/album2.jpg",
      "https://example.com/album3.jpg",
      "https://example.com/album4.jpg",
      "https://example.com/album5.jpg"
    ]
  }
]
```

### POST `/api/v1/collections/`
Créer une nouvelle collection
```bash
curl -X POST http://localhost:8000/api/v1/collections/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jazz Cool",
    "search_type": "genre",
    "search_criteria": {"genre": "Jazz"}
  }'
```

### GET `/api/v1/collections/{id}/albums`
Récupérer les albums d'une collection
```bash
curl http://localhost:8000/api/v1/collections/1/albums
```

### POST `/api/v1/collections/{id}/play`
Jouer une collection sur Roon
```bash
curl -X POST http://localhost:8000/api/v1/collections/1/play \
  -H "Content-Type: application/json" \
  -d '{"zone_name": "Living Room"}'
```

### DELETE `/api/v1/collections/{id}`
Supprimer une collection
```bash
curl -X DELETE http://localhost:8000/api/v1/collections/1
```

### POST `/api/v1/collections/search/{type}`
Rechercher des albums (genre, artist, ai, period)
```bash
# Recherche par genre
curl -X POST http://localhost:8000/api/v1/collections/search/genre \
  -H "Content-Type: application/json" \
  -d '{"query": "Jazz", "limit": 50}'

# Recherche IA
curl -X POST http://localhost:8000/api/v1/collections/search/ai \
  -H "Content-Type: application/json" \
  -d '{"query": "mélancolique et atmosphérique", "limit": 50}'
```

## Données Requises

Pour que Discover fonctionne pleinement, les albums doivent avoir:
- ✅ `genre` - Type de musique
- ✅ `ai_description` - Description générée par IA
- ✅ `ai_style` - Style/ambiance
- ✅ `image_url` - URL de la couverture (requis pour l'aperçu visuel des collections)

> **Disponible**: 200+ albums ont été peuplés avec ces données lors du déploiement initial.

## Migration depuis Playlists

**Changement**: La page "Playlists" a été remplacée par "Discover"
- Ancienne route: `/playlists` → **Nouvelle route**: `/collections`
- Les playlists algorithmiques ont été remplacées par collections basées sur critères
- Aucune donnée n'a été perdue - reconversion possible si nécessaire

## Exemples de Collections

Exemples de collections que vous pouvez créer:

| Nom | Type | Critère | Description |
|-----|------|---------|-------------|
| Jazz Cool | Genre | "Jazz" | Musique jazz sophistiquée |
| Rock 90s | IA | "rock alternatif années 90" | Rock alternatif emblématique |
| Miles Davis | Artiste | "Miles Davis" | Tous les albums de Miles Davis |
| 80s Hits | Période | 1980-1989 | Musique des années 80 |
| Smooth Vibes | IA | "musique calme et relaxante" | Musique relaxante |

## Détails Techniques

### Service Backend
Fichier: `app/services/album_collection_service.py`
- `create_collection()` - Crée et peuple automatiquement
- `search_by_genre()` - Recherche par genre
- `search_by_artist()` - Recherche par artiste
- `search_by_period()` - Recherche par période
- `search_by_ai_query()` - Recherche sémantique multi-champs

### Modèles
- `AlbumCollection` - Table des collections
- `CollectionAlbum` - Relation many-to-many avec position

### Limite de 20 Albums
- Représente un lot de musique découvrable
- Peut être ajustée dans `create_collection()` (paramètre `limit`)
- Optimisé pour UX: assez riche sans être accablant

## Troubleshooting

### Aucun album retourné
**Cause**: Recherche ne correspond à aucun album
**Solution**: Vérifiez que les albums existent avec le critère de recherche
```bash
# Vérifier les genres existants
curl http://localhost:8000/api/v1/collections/search/genre \
  -H "Content-Type: application/json" \
  -d '{"query": "Rock", "limit": 5}'
```

### Collection vide
**Cause**: Recherche IA ne trouve rien
**Solution**: Utilisez un genre/artiste connu ou reformulez la requête IA
- Essayez: "rock", "jazz", "electronic", "metal" comme genres
- Pour IA: utilisez des adjectifs concrets: "mélancolique", "énergique", "atmosphérique"

### Lecture Roon ne fonctionne pas
**Cause**: Roon non connecté
**Solution**: 
1. Vérifiez que Roon Core est en ligne
2. Vérifiez `http://localhost:8000/roon/status`
3. L'endpoint `/play` retournera erreur 503 si Roon indisponible
