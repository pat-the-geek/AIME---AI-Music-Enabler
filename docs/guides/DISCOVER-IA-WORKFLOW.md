# 🎵 Recherche de Collections par IA Euria

**Version:** 4.7.1  
**Date:** 15 février 2026  
**Statut:** ✅ Production (web-only mode actif)

---

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

## Améliorations par Rapport à Spotify Only

| Aspect | Avant (Spotify) | Après (Euria v4.7.0+) |
|--------|-----------------|---------------|
| **Recherche** | Keywords simples | Requête naturelle complète |
| **Résultats** | Basés popularity | Basés sur compréhension IA |
| **Nombres** | ~25 albums max | ~50 albums optimisés |
| **New Albums** | Priorité | Garantie (Euria en premier) |
| **Descriptions** | Non générées | Générées par Euria |
| **Nom Collection** | Heuristique simple | Synthèse intelligente Euria |
| **Mode** | Hybride (web + local) | Web-only (pas complément local) |
| **Déduplication** | Par ID uniquement | Par ID + titre/artiste normalisé |

---

## Configuration (secrets.json)

Le fichier `config/secrets.json` à la racine du projet contient les credentials nécessaires:

```json
{
  "euria": {
    "url": "https://api.infomaniak.com/2/ai/YOUR_MODEL_ID/openai/v1/chat/completions",
    "bearer_token": "sk-xxxxxxxxxxxxxxxxxxxxxx"
  },
  "spotify": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  }
}
```

**Fallback legacy:** Variables d'environnement toujours supportées:
- `EURIA_URL` / `EURIA_API_URL`
- `EURIA_BEARER` / `EURIA_BEARER_TOKEN` / `EURIA_API_KEY`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

---

## Exemple d'Exécution (v4.7.1)

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
[15:31:30] 🎉 42 albums proposés par Euria - PAS DE COMPLÉMENT LOCAL
[15:31:30] 🎨 Nom généré par Euria: Vibe Coding Vibes
[15:31:30] 📚 Collection créée: Vibe Coding Vibes
[15:31:31] ✅ 42 albums ajoutés à la collection Vibe Coding Vibes (après déduplication)
```

**Note:** Depuis v4.7.0, le mode web-only est activé par défaut. Aucun complément de la bibliothèque locale n'est ajouté si EurIA retourne des résultats.

---

## Fonctionnalités UI (v4.7.1)

### Interface Collections

- **Dialog XL:** Largeur 95vw pour meilleur affichage
- **Grid 4 colonnes:** md={3} pour 4 albums par ligne sur desktop
- **Groupement par image:** Toggle pour grouper albums avec même cover
  - État persisté dans localStorage
  - Mode "flat" ou "grouped" au choix
- **Boutons d'action par album:**
  - 🎨 **Profil Artiste:** Ouvre le portrait/biographie (réutilise composant Magazine)
  - 📝 **Description Album:** Affiche la description générée par EurIA
- **Navigation améliorée:**
  - Échap / Retour depuis détail album → retour à collection (ne ferme pas dialog)
  - Échap depuis collection → ferme dialog complet
  - Backdrop click → ferme dialog complet

### Déduplication

Deux passes de déduplication:
1. **Par ID:** Albums déjà en collection (via collection_id + album_id)
2. **Par identité logique:** Normalisation titre + artiste (minuscules, trim)

```python
# Exemple déduplication
title_key = album.title.strip().lower()
artist_names = sorted([a.name.strip().lower() for a in album.artists])
album_key = (title_key, "|".join(artist_names))
# Si clé existe déjà → skip
```

---

## Changelog Discover

| Version | Date | Modifications |
|---------|------|---------------|
| 4.7.1 | 2026-02-15 | UI: Dialog XL (95vw), grid 4 cols, groupement images, boutons artiste/description |
| 4.7.0 | 2026-02-14 | Mode web-only par défaut, déduplication améliorée (ID + titre/artiste) |
| 4.6.5 | 2026-02-10 | Fix config loading (secrets.json multi-path search) |
| 4.6.0 | 2026-02-05 | Discover initial avec Spotify credentials fallback |

---

**Documentation complète des prompts:** Voir [AI-PROMPTS.md](../features/ai/AI-PROMPTS.md#prompts-de-recherche-de-collections-discover)

**Maintenu par:** Équipe AIME  
**Dernière mise à jour:** 15 février 2026
