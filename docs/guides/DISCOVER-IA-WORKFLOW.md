# 🎵 Recherche de Collections par IA Euria

## Workflow Complet

Lorsqu'un utilisateur crée une collection avec une requête IA, voici le processus optimisé:

### 1️⃣ Recherche Euria IA
```
Requête utilisateur: "Fais moi une sélection d'album qui sont agréable pour faire du vibe coding à la maison"
        ↓
🧠 Appel à Euria IA avec prompt JSON
        ↓
Retour structuré: [
  {"artist": "The Beatles", "album": "Abbey Road", "year": 1969},
  {"artist": "Pink Floyd", "album": "Dark Side of the Moon", "year": 1973},
  ...
]
```

**Avantages:**
- Requête en langage naturel réelle
- Résultat structuré et fiable (JSON)
- IA comprend le contexte ("vibe coding à la maison")
- Pas de parsing page web fragile

### 2️⃣ Création en Base de Données
```
Provenance: "Discover IA"
Support: "Digital"
Données:
  - artist: Nom de l'artiste
  - title: Titre de l'album
  - year: Année (si retournée)
```

### 3️⃣ Enrichissement Spotify
Pour chaque album créé:
1. Recherche sur Spotify par artiste + album
2. Récupère:
   - URL Spotify du musicien
   - URL de l'album
   - Image de couverture haute résolution

### 4️⃣ Génération de Descriptions IA
```
Requête Euria: "Génère une brève description captivante pour l'album..."
        ↓
Réponse: "Description personnalisée de 2-3 phrases sur le style et l'ambiance"
```

Stored dans: `album.ai_description`

### 5️⃣ Génération du Nom de Collection
```
Requête Euria: "Crée un nom court et évocateur pour cette collection..."
        ↓
Réponse: "Vibe Coding à la Maison"
```

## Architecture du Code

### EuriaService (`backend/app/services/euria_service.py`)
Nouveau service dédié à l'IA Euria:
- `search_albums_web(query, limit)` - Recherche albums JSON
- `generate_album_description(artist, album, year)` - Description par album
- `generate_collection_name(query)` - Nom synthétique de collection

### AlbumCollectionService (modifié)
- `create_collection()` - Flux complet avec Euria + Spotify
- `_generate_collection_name()` - Délégué à EuriaService
- `_search_albums_web()` - Coordonne Euria → Spotify → BD

## Flux d'Appels

```
Frontend: Soumet requête IA
        ↓
API: POST /collections/ avec {ai_query}
        ↓
create_collection()
        ├─ _generate_collection_name() → EuriaService
        ├─ _search_albums_web()
        │   ├─ EuriaService.search_albums_web() → JSON albums
        │   ├─ Pour chaque album:
        │   │   ├─ Créer/Chercher artiste
        │   │   ├─ Créer album (provenance "Discover IA")
        │   │   ├─ SpotifyService.search_album_details() → URLs + image
        │   │   └─ EuriaService.generate_album_description() → description
        │   └─ Retour liste albums enrichis
        ├─ search_by_ai_query() → Compléter avec librairie locale si besoin
        └─ add_albums_to_collection()
        ↓
Retour collection avec albums enrichis
```

## Variables d'Environnement Requises

```env
# Euria IA
EURIA_API_URL=https://api.euria.infomaniak.com/v1/chat/completions
EURIA_BEARER_TOKEN=<token>
EURIA_MAX_ATTEMPTS=3

# Spotify (optionnel pour enrichissement)
SPOTIFY_CLIENT_ID=<id>
SPOTIFY_CLIENT_SECRET=<secret>
```

## Améliorations par Rapport à Spotify Only

| Aspect | Avant (Spotify) | Après (Euria) |
|--------|-----------------|---------------|
| **Recherche** | Keywords simples | Requête naturelle complète |
| **Résultats** | Basés popularity | Basés sur compréhension IA |
| **Nombres** | ~25 albums max | ~50 albums optimisés |
| **Néw Albums** | Priorité | Garantie (Euria en premier) |
| **Descriptions** | Non générées | Générées par Euria |
| **Nom Collection** | Heuristique simple | Synthèse intelligente Euria |

## Exemple d'Exécution

```
[15:30:42] 🌐 Recherche web via Euria pour: Fais moi une sélection d'album agréable pour faire du vibe coding
[15:30:42] 🧠 Requête à Euria...
[15:30:44] ✅ 42 albums trouvés via Euria
[15:30:44] 🎵 Service Spotify prêt pour enrichissement
[15:30:44]   [1/42] 📀 Création: Abbey Road - The Beatles
[15:30:45]     ✨ Enrichi avec Spotify
[15:30:46]     ✍️ Description générée
[15:30:46]     ✅ Album créé avec enrichissements
[15:30:47]   [2/42] 📀 Création: Dark Side of the Moon - Pink Floyd
[15:30:48]     ✨ Enrichi avec Spotify
[15:30:49]     ✍️ Description générée
[15:30:49]     ✅ Album créé avec enrichissements
...
[15:31:30] 🎉 42 albums créés et enrichis
[15:31:30] 🎨 Nom généré par Euria: Vibe Coding Vibes
[15:31:30] 📚 Collection créée: Vibe Coding Vibes
[15:31:31] 📚 Complément librairie locale (besoin 8 albums supplémentaires)
[15:31:32] ✅ 50 albums ajoutés à la collection Vibe Coding Vibes
```
