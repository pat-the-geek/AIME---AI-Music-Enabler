# 🤖 INTÉGRATION EURIA + SPOTIFY - GUIDE D'UTILISATION

## Vue d'ensemble

Vous avez maintenant intégré un **bouton "Enrichissement Euria + Spotify"** dans l'interface Paramètres qui vous permet d'enrichir automatiquement votre collection d'albums avec :

- **📝 Descriptions IA** (Euria) - Textes détaillés générés automatiquement
- **🖼️ Images Artiste Haute Résolution** (Spotify) - Couvertures professionnelles

## Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend (Settings.tsx)                    │
│  Bouton "Enrichir avec Euria + Spotify"    │
└────────────────┬────────────────────────────┘
                 │ POST /services/discogs/enrich
                 ▼
┌─────────────────────────────────────────────┐
│  Backend FastAPI (services.py)              │
│  Endpoint: /discogs/enrich                  │
│  └─ Lance tâche en arrière-plan             │
└────────────────┬────────────────────────────┘
                 │ async task
                 ▼
┌─────────────────────────────────────────────┐
│  Script: enrich_euria_spotify.py            │
│  ├─ Charge config (secrets.json)            │
│  ├─ Phase 1: EuriaProvider.generate_description()
│  ├─ Phase 2: SpotifyProvider.get_artist_image()
│  └─ Sauvegarde résultats en JSON           │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  API Externes                               │
│  ├─ https://euria.ai/api/v1 (Descriptions) │
│  └─ https://api.spotify.com (Images)       │
└─────────────────────────────────────────────┘
```

## Configuration Requise

### ✅ Configuration Automatique

Les credentials sont **automatiquement lus** depuis le fichier `config/.env`:

```env
# Euria via Infomaniak (déjà présent dans votre config/.env)
URL=https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions
bearer=votre_token_bearer_ici

# Spotify (déjà présent dans votre config/.env)
SPOTIFY_CLIENT_ID=votre_client_id_ici
SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
```

**Bonne nouvelle**: Les clés sont **déjà configurées** dans votre `config/.env` existant !

### Vérifier la Configuration

Pour voir quelles clés sont chargées:

```bash
# Via CLI
python3 enrich_euria_spotify.py

# Via interface
Settings → Enrichissement Euria + Spotify → Clic sur le bouton
```

Les clés présentes dans `config/.env` sont utilisées automatiquement.

```json
{
  "euria": {
    "api_url": "https://euria.ai/api/v1",
    "api_key": "euria_xxxxxxxxxxxx",
    "enabled": true
  },
  "spotify": {
    "client_id": "abcdef123456",
    "client_secret": "secret789abcdef",
    "enabled": true
  },
  "discogs": {
    "api_key": "...",
    "username": "..."
  }
}
```

## Utilisation - Interface Graphique

### Étape 1 : Accéder aux Paramètres

```
Menu → Paramètres → "Enrichissement Euria + Spotify"
```

### Étape 2 : Lancer l'enrichissement

```
Cliquer sur: 🤖 "Enrichir avec Euria + Spotify"
```

### Étape 3 : Suivi en arrière-plan

Le processus s'exécute en arrière-plan :

```
- Descriptions IA sont générées pour chaque album
- Images Spotify sont récupérées pour chaque artiste
- Résultats sont sauvegardés progressivement
- La page reste réactive (pas de blocage)
```

### Étape 4 : Notification de fin

Vous recevrez une notification :

```
✅ Enrichissement complété!
   📝 X descriptions Euria ajoutées
   🖼️  Y images Spotify ajoutées
```

## Utilisation - Script CLI (Optionnel)

Vous pouvez aussi lancer l'enrichissement manuellement :

```bash
# D'abord, configurer :
python3 setup_automation.py

# Puis enrichir :
python3 enrich_euria_spotify.py

# Avec affichage des erreurs :
python3 enrich_euria_spotify.py --verbose

# Limiter à un nombre d'albums (pour test) :
python3 -c "
import sys
sys.path.insert(0, './backend')
from enrich_euria_spotify import enrich_albums_euria_spotify
stats = enrich_albums_euria_spotify(limit=10)
print(f'✅ Complété: {stats}')
"
```

## Processus Détaillé

### Phase 1️⃣  : Génération Descriptions Euria

Pour chaque album :

1. **Détection d'existence**
   - Vérifie si description déjà remplie
   - Skip si déjà complète

2. **Appel API Euria**
   ```
   POST https://euria.ai/api/v1/generate/text
   {
     "prompt": "Generate 150-word review for album {title} by {artists} ({year})",
     "model": "euria-pro",
     "max_tokens": 200,
     "temperature": 0.7
   }
   ```

3. **Sauvegarde en BD**
   - `Album.ai_description` limité à 2000 caractères
   - Commit par batch de 10

4. **Cache JSON**
   - Sauvegardé dans `data/euria_descriptions.json`
   - Permet récupération ultérieure

### Phase 2️⃣  : Récupération Images Spotify

Pour chaque artiste :

1. **Authentification Spotify**
   ```
   POST https://accounts.spotify.com/api/token
   Body: grant_type=client_credentials
   Header: Basic {base64(client_id:client_secret)}
   ```

2. **Recherche Artiste**
   ```
   GET https://api.spotify.com/v1/search
   ?q=artist:{artist_name}&type=artist&limit=1
   ```

3. **Extraction Image**
   - Récupère la première image (meilleure résolution)
   - Valide URL (commence par https://)

4. **Sauvegarde en BD**
   - Table `Image` avec :
     - `artist_id` = lien artiste
     - `image_type` = 'artist'
     - `source` = 'spotify'
     - `url` = image URL
   - Commit par batch de 20

5. **Cache JSON**
   - Sauvegardé dans `data/artist_images.json`

## Résultats

### Fichiers générés

```
data/
├── euria_descriptions.json
│   └── {"data": {"Album Title": "Description texte...", ...}}
└── artist_images.json
    └── {"data": {"Artist Name": "https://image.url", ...}}
```

### Base de données modifiée

```
Album table:
├── ai_description: "Description Euria..." (2000 chars max)
└── (autres colonnes inchangées)

Image table:
├── NEW ROWS pour les images Spotify
├── image_type: 'artist'
├── source: 'spotify'
└── url: "https://..."
```

## Statistiques de Performance

### Temps estimé

```
236 albums × 0.5s (Euria) = 118 secondes
456 artistes × 0.2s (Spotify) = 91 secondes

Total : ~3-4 minutes
```

### Rate Limiting

```
Euria:   0.5s par description  (limite: selon plan)
Spotify: 0.2s par image        (limite: très généreux)
```

### Gestion des erreurs

```
- Erreurs Euria : Log + skip, continue
- Erreurs Spotify : Log + skip, continue
- Erreurs BD : Transaction rollback, log
- Final : Rapport statistiques
```

## Troubleshooting

### Erreur : "Euria API not configured"

```
✗ Vérifier: config/secrets.json
✓ Ajouter: section "euria" avec api_key
✓ Relancer l'enrichissement
```

### Erreur : "Spotify authentication failed"

```
✗ Vérifier: Client ID et Secret corrects
✗ Vérifier: Pas d'espaces cachés
✗ Vérifier: Pas de caractères spéciaux mal échappés
✓ Régénérer Client Secret dans Spotify Dashboard
✓ Mettre à jour config/secrets.json
```

### Aucune image Spotify trouvée

```
Possible causes:
- Artiste peu connu/nouveau
- Nom de l'artiste mal orthographié
- Nom local différent du nom Spotify

Solution: Enrichissement partiel est ok
          Les albums sans image conservent leur state
```

### Description Euria vide/courte

```
Possible causes:
- Timeout API Euria
- Limite de rate atteinte
- Problème de connexion

Solution: Relancer l'enrichissement
         (skip les albums déjà remplis)
```

## Optimisations Avancées

### Enrichissement limité

Enrichir seulement N albums (pour tester) :

```bash
# Via API
curl -X POST http://localhost:8000/services/discogs/enrich?limit=10

# Via Python
from enrich_euria_spotify import enrich_albums_euria_spotify
stats = enrich_albums_euria_spotify(limit=50)
```

### Vérifier progression

```bash
curl http://localhost:8000/services/discogs/enrich/progress
# Returns: {
#   "status": "running",
#   "phase": "descriptions",
#   "current": 45,
#   "total": 236,
#   "descriptions_added": 45,
#   "images_added": 0,
#   "errors": 0
# }
```

### Manuel : Éditer les JSON

Vous pouvez éditer manuellement les JSON avant de lancer :

```bash
# Ajouter descriptions manuellement
nano data/euria_descriptions.json

# Format:
{
  "data": {
    "Album Title 1": "My custom description text...",
    "Album Title 2": "Another description..."
  }
}

# Ensuite lancer refresh_complete.py pour appliquer
python3 refresh_complete.py
```

## Intégration avec Discogs Sync

### Workflow complet

```
1. Synchroniser Discogs
   └─ récupère 236 albums

2. Enrichir avec Euria + Spotify
   ├─ génère descriptions
   └─ récupère images artiste

3. Refresh complet
   └─ applique tous les changements

4. Vérifier:
   └─ voir les 236 albums enrichis
```

### Boutons disponibles (Paramètres)

```
┌─ Synchronisation Discogs ──────────┐
│ Button: "Synchroniser Discogs"     │
│ └─ 236 albums importés             │
└────────────────────────────────────┘

┌─ Enrichissement Euria + Spotify ───┐
│ Button: "Enrichir avec..."         │
│ Descriptions IA + Images HD        │
└────────────────────────────────────┘

┌─ Normalisation Roon ───────────────┐
│ Button: "Prévisualiser tout"       │
│ Aligne noms avec Roon              │
└────────────────────────────────────┘
```

## Cas d'usage

### Enrichissement quotidien

```bash
# Crontab Unix/Linux
0 2 * * * cd ~/AIME && python3 enrich_euria_spotify.py >> cron.log 2>&1
# Tous les jours à 2h du matin
```

### Enrichissement avec refresh complet

```python
# Script Python complèt
import subprocess

# 1. Enrichir
subprocess.run(['python3', 'enrich_euria_spotify.py'])

# 2. Refresh
subprocess.run(['python3', 'refresh_complete.py'])

# 3. Vérifier
subprocess.run(['python3', 'verify_enrichment.py'])

print("✅ Enrichissement complet done!")
```

## Support

### Ressources

- **Euria API**: https://euria.ai/docs
- **Spotify API**: https://developer.spotify.com/documentation/web-api
- **Script**: `enrich_euria_spotify.py`
- **Endpoint**: `POST /services/discogs/enrich`

### Questions fréquentes

**Q: Quel est le coût ?**
- Euria : selon votre plan
- Spotify : gratuit (API gratuite)
- Total : peut être < $10/mois avec Euria freemium

**Q: Combien de temps ça prend ?**
- 236 albums : ~3-4 minutes
- Peut être lancé en arrière-plan

**Q: Puis-je annuler ?**
- Oui : fermer la page ne stoppe pas le process
- Process continue en arrière-plan
- Vérifier progression via `/services/discogs/enrich/progress`

**Q: Que se passe-t-il en cas d'erreur ?**
- Erreurs loggées, process continue
- Rapport final inclut nombre d'erreurs
- Albums sans enrichissement conservent état précédent

---

*Dernière mise à jour: 2026-02-06*
*version 1.0 - INTÉGRATION GRAPHIQUE*
