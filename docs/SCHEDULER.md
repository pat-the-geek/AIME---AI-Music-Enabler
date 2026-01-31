# 📅 Scheduler et Exports Automatiques

## Vue d'ensemble

Le scheduler d'AIME exécute automatiquement trois tâches quotidiennes pour générer des exports de votre collection musicale. Ces tâches peuvent être déclenchées manuellement ou s'exécutent selon un planning défini.

## 📋 Tâches Disponibles

### 1. 🎋 Génération de Haikus (6h00)

**Endpoint**: `POST /api/v1/services/scheduler/trigger/generate_haiku_scheduled`

Cette tâche:
- Sélectionne 5 albums aléatoires de votre collection
- Génère un haiku poétique pour chaque album via l'API EurIA
- Exporte les haikus en fichier Markdown avec horodatage
- Sauvegarde dans `Scheduled Output/generate-haiku-YYYYMMDD-HHMMSS.md`

**Exemple de sortie**:
```markdown
# 🎵 Haikus Générés - Sélection Aléatoire

Généré: 31/01/2026 21:01:57

## 1. 461 Ocean Boulevard - Eric Clapton

```
Silence épais
La playlist attend son premier
accord qui résonne
```

## 2. Classic Sinatra - Frank Sinatra

```
Silence épais
Pas une note ne s'échappe...
L'album dort encore.
```
```

### 2. 📝 Export Markdown (8h00)

**Endpoint**: `POST /api/v1/services/scheduler/trigger/export_collection_markdown`

Cette tâche:
- Exporte la collection complète en Markdown
- Groupe les albums par artiste (alphabétique)
- Inclut l'année et le support (Vinyle, CD, Digital, etc.)
- Sauvegarde dans `Scheduled Output/export-markdown-YYYYMMDD-HHMMSS.md`

**Exemple de sortie**:
```markdown
# 📚 Collection Complète

Exporté: 31/01/2026 21:02:16
Total albums: 395

## 🎤 AIR

- **The Virgin Suicides Redux** (2025) [Vinyle]
- **Moon Safari** (2023) [Vinyle]
- **Talkie Walkie** (2015) [Vinyle]

## 🎤 Alice Cooper

- **The Revenge Of Alice Cooper** (2025) [Vinyle]
- **Live From The Astroturf** (2022) [Vinyle]
```

### 3. 📊 Export JSON (10h00)

**Endpoint**: `POST /api/v1/services/scheduler/trigger/export_collection_json`

Cette tâche:
- Exporte la collection complète en format JSON
- Inclut métadonnées complètes (ID, titre, année, support, source, artistes)
- Idéal pour traitement programmatique
- Sauvegarde dans `Scheduled Output/export-json-YYYYMMDD-HHMMSS.json`

**Exemple de structure**:
```json
{
  "export_date": "2026-01-31T21:02:26.427520",
  "total_albums": 395,
  "albums": [
    {
      "id": 1,
      "title": "T.V. Sky",
      "year": 2022,
      "support": "Vinyle",
      "source": "discogs",
      "spotify_url": "https://open.spotify.com/album/...",
      "artists": ["The Young Gods"],
      "tracks_count": 0
    }
  ]
}
```

## ⚙️ Configuration

### Modifier le nombre de fichiers conservés

Par défaut, le scheduler garde les **5 derniers fichiers** de chaque type pour éviter de saturer le disque.

#### Via l'interface Settings

1. Allez à **Settings** (⚙️)
2. Scroll jusqu'à "⚙️ Configuration des fichiers générés"
3. Entrez le nombre de fichiers à conserver (1-50)
4. Cliquez "Appliquer"

#### Via l'API

```bash
# Modifier à 10 fichiers par type
curl -X PATCH "http://localhost:8000/api/v1/services/scheduler/config?max_files_per_type=10"

# Réponse
{
  "max_files_per_type": 10
}
```

### Récupérer la configuration actuelle

```bash
curl http://localhost:8000/api/v1/services/scheduler/config | jq .

# Réponse
{
  "enabled": true,
  "output_dir": "Scheduled Output",
  "max_files_per_type": 5,
  "tasks": [
    {
      "name": "generate_haiku_scheduled",
      "enabled": true,
      "frequency": 1,
      "unit": "day",
      "time": "06:00",
      "description": "Génération haikus pour 5 albums aléatoires"
    },
    ...
  ]
}
```

## 📂 Gestion des Fichiers

### Localisation

Tous les fichiers générés sont stockés dans le répertoire:
```
Scheduled Output/
```

Situé à la racine du projet AIME.

### Nettoyage Automatique

- **Avant**: Pas de limite, les fichiers s'accumulaient
- **Après**: Limite configurable (défaut: 5)
- **Mécanisme**: Après chaque génération, les anciens fichiers sont supprimés
- **Logs**: Les suppressions sont tracées dans les logs avec 🗑️

**Exemple de log**:
```
2026-01-31 21:09:50,265 - app.services.scheduler_service - INFO - 🗑️ Supprimé fichier ancien (haiku): generate-haiku-20260131-210202.md
2026-01-31 21:09:50,266 - app.services.scheduler_service - INFO - 🗑️ Supprimé fichier ancien (haiku): generate-haiku-20260131-210844.md
```

### .gitignore

Le répertoire `Scheduled Output/` est ignoré par Git pour éviter de versionner les exports générés:

```
# .gitignore
Scheduled Output/
```

## ⏱️ Planification

### Horaires par défaut

| Tâche | Heure | Fréquence |
|-------|-------|-----------|
| 🎋 Haikus | 06:00 | Quotidienne |
| 📝 Markdown | 08:00 | Quotidienne |
| 📊 JSON | 10:00 | Quotidienne |

### Déclenchement Manuel

Vous pouvez déclencher n'importe quelle tâche à tout moment:

```bash
# Générer haikus maintenant
curl -X POST http://localhost:8000/api/v1/services/scheduler/trigger/generate_haiku_scheduled

# Réponse
{
  "task": "generate_haiku_scheduled",
  "status": "completed",
  "timestamp": "2026-01-31T21:02:02.863355"
}
```

## 🔍 Dépannage

### Aucun fichier n'apparaît dans Scheduled Output

1. Vérifiez que le scheduler est actif (Settings → Tâches Planifiées)
2. Vérifiez les logs backend: `tail -f /tmp/backend.log`
3. Déclenchez manuellement une tâche pour tester
4. Vérifiez que la limite max_files_per_type n'est pas trop basse

### Les fichiers disparaissent rapidement

- C'est normal si max_files_per_type est bas
- Augmentez la limite dans les Settings si vous voulez conserver plus de fichiers
- Exemple: passer de 5 à 20 fichiers par type

### Format de fichier incorrect

- Les fichiers Markdown devraient être lisibles dans n'importe quel éditeur
- Les fichiers JSON doivent être valides (testez avec `jq` ou un validateur)
- Vérifiez que l'encodage est UTF-8

## 📊 Cas d'usage

### Sauvegarde régulière
```bash
# Créer une sauvegarde hebdomadaire
cp -r "Scheduled Output/" "backups/$(date +%Y%m%d-%H%M%S)/"
```

### Intégration avec d'autres outils
```bash
# Convertir JSON en CSV
jq -r '.albums[] | [.id, .title, .artists[0]] | @csv' export-json-*.json > collection.csv

# Trouver tous les albums de 2025
jq '.albums[] | select(.year == 2025)' export-json-*.json | jq -r '.title'
```

### Analyse de collection
```bash
# Compter albums par année
jq '.albums | group_by(.year) | map({year: .[0].year, count: length})' export-json-*.json

# Lister tous les artistes
jq -r '.albums[].artists[]' export-json-*.json | sort -u
```

## 🔗 Ressources

- **[Documentation API Complète](API.md)**
- **[Configuration](../config/app.json)**
- **[Services Backend](../backend/app/services/scheduler_service.py)**
