# 📥 Import Historique Last.fm & Tracker - Documentation

## Date : 30 janvier 2026

---

## 🎯 Vue d'Ensemble

Nouvelle fonctionnalité majeure permettant :
1. **Import de l'historique existant** depuis Last.fm (écoutes passées)
2. **Tracker en temps réel** pour les nouvelles écoutes
3. **Interface de contrôle** dans les Paramètres

---

## 🎧 Scrobbling Apple Music (Last.fm)

Pour scrobbler vos écoutes Apple Music sur Last.fm, plusieurs solutions recommandées :

- **Sur iOS** : [Last.fm (app officielle)](https://apps.apple.com/ch/app/last-fm/id1188681944?l=fr-FR) — Application officielle de Last.fm pour iOS, permettant de scrobbler vos écoutes et de suivre votre historique musical en temps réel.
- **Sur iOS** : [Marvis Pro](https://apps.apple.com/ch/app/marvis-pro/id1447768809?l=fr-FR) — Application puissante permettant de scrobbler automatiquement vos lectures Apple Music vers Last.fm.
- **Sur iOS** : [QuietScrob - Last.fm Scrobbler](https://apps.apple.com/ch/app/quietscrob-last-fm-scrobbler/id741599377?l=fr-FR) — Alternative légère et discrète pour scrobbler automatiquement vos écoutes vers Last.fm avec une interface minimaliste.
- **Sur Mac OS X** : [NepTunes for Last.fm](https://apps.apple.com/ch/app/neptunes-for-last-fm/id1006739057?l=fr-FR&mt=12) — Utilitaire léger pour scrobbler Apple Music (et d'autres lecteurs) directement sur votre Mac.

Ces outils assurent que toutes vos écoutes Apple Music sont bien envoyées à Last.fm, et donc agrégées dans AIME.

Cette fonctionnalité complète le système en permettant de récupérer tout l'historique d'écoute et de continuer le tracking en temps réel.

---

## 📥 Import Historique Last.fm

### Fonctionnement

L'import récupère l'historique d'écoute depuis Last.fm par batches de 200 tracks (limite API Last.fm) et :
1. Crée les artistes, albums et tracks en base de données
2. Enregistre chaque écoute avec son timestamp exact
3. Enrichit automatiquement les nouveaux albums avec :
   - Images Spotify
   - Images Last.fm
   - Descriptions IA (EurIA)
4. Ignore automatiquement les doublons (basé sur timestamp)

### Endpoints Backend

#### POST `/api/v1/services/lastfm/import-history`

**Paramètres** :
- `limit` (int, optionnel) : Nombre maximum de tracks à importer (défaut: 1000)
- `skip_existing` (bool, optionnel) : Ignorer les doublons (défaut: true)

**Exemple** :
```bash
curl -X POST "http://localhost:8000/api/v1/services/lastfm/import-history?limit=500&skip_existing=true"
```

**Réponse** :
```json
{
  "status": "success",§
  "tracks_imported": 500,
  "tracks_skipped": 0,
  "tracks_errors": 0,
  "albums_enriched": 50,
  "total_albums_to_enrich": 123,
  "total_scrobbles": 2003
}
```

### Script d'Import

#### `scripts/import_lastfm_history.py`

Script Python pratique pour import en ligne de commande.

**Usage** :
```bash
# Importer 500 tracks
python scripts/import_lastfm_history.py 500

# Importer 2000 tracks sans ignorer doublons
python scripts/import_lastfm_history.py 2000 --no-skip-existing

# Avec URL custom
python scripts/import_lastfm_history.py 1000 --url http://localhost:8080
```

**Options** :
- `limit` : Nombre de tracks (défaut: 1000)
- `--no-skip-existing` : Réimporter même les doublons
- `--url` : URL du backend (défaut: http://localhost:8000)

**Exemple de sortie** :
```
🎵 Import de l'historique Last.fm
📊 Limite: 500 tracks
⚙️  Skip existing: True
--------------------------------------------------
🔄 Envoi de la requête...

==================================================
✅ IMPORT TERMINÉ!
==================================================
⏱️  Durée: 45.2s
📥 Tracks importés: 500
⏭️  Tracks ignorés: 0
❌ Erreurs: 0
🎨 Albums enrichis: 50
📀 Total albums à enrichir: 123
📊 Total scrobbles Last.fm: 2003
==================================================
```

### Interface Web (Settings)

#### Section "📥 Import Historique Last.fm"

**Fonctionnalités** :
1. Bouton "Importer l'Historique"
2. Dialog avec configuration :
   - Champ "Nombre de tracks à importer"
   - Barre de progression pendant l'import
   - Messages d'info et d'avertissement
3. Notifications de succès/erreur avec détails

**Workflow** :
1. Aller dans Settings (`/settings`)
2. Section "Import Historique Last.fm"
3. Cliquer "Importer l'Historique"
4. Configurer le nombre de tracks (ex: 1000)
5. Cliquer "Démarrer l'Import"
6. Attendre la fin (barre de progression)
7. Notification avec résultats

---

## 🎵 Tracker Temps Réel

### Fonctionnement

Le tracker surveille Last.fm toutes les X secondes (configurable, défaut: 120s) :
1. Récupère le track en cours de lecture ("now playing")
2. Compare avec le dernier track enregistré
3. Si nouveau track → enregistre avec enrichissements
4. Enrichissement automatique :
   - Images artiste (Spotify)
   - Images album (Spotify + Last.fm)
   - Description IA (EurIA)

### Endpoints Backend

#### GET `/api/v1/services/tracker/status`

Obtenir le statut du tracker.

**Réponse** :
```json
{
  "running": true,
  "last_track": "Pink Floyd|Comfortably Numb|The Wall",
  "interval_seconds": 120
}
```

#### POST `/api/v1/services/tracker/start`

Démarrer le tracker.

**Réponse** :
```json
{
  "status": "started"
}
```

#### POST `/api/v1/services/tracker/stop`

Arrêter le tracker.

**Réponse** :
```json
{
  "status": "stopped"
}
```

### Interface Web (Settings)

#### Section "🎵 Tracker Last.fm"

**Fonctionnalités** :
1. **Statut en temps réel** :
   - ✅ Actif (vert) / ⏸️ Arrêté (jaune)
   - Affichage de l'intervalle (ex: 120s)
   - Dernier track détecté
   - Rafraîchissement automatique toutes les 5s

2. **Contrôles** :
   - Bouton "Démarrer/Arrêter le Tracker"
   - Bouton "Actualiser le statut"
   - Couleurs dynamiques (vert/rouge)
   - Icônes Play/Stop

3. **Info contextuelle** :
   - Explication du fonctionnement
   - Intervalle de polling

**Workflow** :
1. Aller dans Settings (`/settings`)
2. Section "Tracker Last.fm"
3. Cliquer "Démarrer le Tracker"
4. Vérifier le statut (vert = actif)
5. Le tracker enregistre automatiquement les nouvelles écoutes
6. Pour arrêter : cliquer "Arrêter le Tracker"

---

## 🔧 Architecture Technique

### Backend

#### LastFMService (`backend/app/services/lastfm_service.py`)

**Nouvelles méthodes** :

```python
def get_user_history(
    self,
    limit: int = 200,
    from_timestamp: Optional[int] = None,
    to_timestamp: Optional[int] = None
) -> list:
    """Récupérer l'historique complet d'écoute."""
    # Utilise pylast.User.get_recent_tracks()
    # Filtre les tracks "now playing" (sans timestamp)
    # Retourne liste de dicts avec artist, title, album, timestamp
```

```python
def get_total_scrobbles(self) -> int:
    """Obtenir le nombre total de scrobbles."""
    # Utilise pylast.User.get_playcount()
```

#### Endpoint Import (`backend/app/api/v1/services.py`)

**Logique** :
1. Initialiser services (LastFM, Spotify, IA)
2. Récupérer total scrobbles
3. Calculer nombre de batches (200 tracks/batch)
4. Pour chaque batch :
   - Récupérer tracks depuis Last.fm
   - Pour chaque track :
     - Vérifier si déjà importé (timestamp)
     - Créer artiste/album/track si nécessaire
     - Créer entrée ListeningHistory
   - Commit par lots de 50 tracks
5. Enrichir les nouveaux albums (max 50 par import)
6. Retourner statistiques

**Optimisations** :
- Commits fréquents (évite timeout)
- Délais entre batches (1s)
- Délais entre enrichissements IA (1s)
- Limite enrichissement (50 albums max par import)
- Skip doublons automatique

### Frontend

#### Settings Page (`frontend/src/pages/Settings.tsx`)

**Nouveautés** :

**États** :
```typescript
const [importLimit, setImportLimit] = useState(1000)
const [importDialogOpen, setImportDialogOpen] = useState(false)
const [snackbar, setSnackbar] = useState(...)
```

**Queries** :
```typescript
// Tracker status avec refetch auto 5s
const { data: trackerStatus } = useQuery({
  queryKey: ['tracker-status'],
  refetchInterval: 5000
})
```

**Mutations** :
```typescript
// Démarrer/arrêter tracker
const startTrackerMutation = useMutation(...)
const stopTrackerMutation = useMutation(...)

// Import historique avec timeout 10 min
const importHistoryMutation = useMutation({
  mutationFn: async (limit) => {
    const response = await apiClient.post(
      `/services/lastfm/import-history?limit=${limit}`,
      null,
      { timeout: 600000 }
    )
    return response.data
  }
})

// Sync Discogs
const syncDiscogsMatch = useMutation(...)
```

**Composants** :
1. Card Tracker avec statut et boutons
2. Card Import avec bouton et dialog
3. Card Sync Discogs
4. Dialog configuration import
5. Snackbar notifications

---

## 📊 Cas d'Usage

### 1. Premier Import Historique

**Objectif** : Importer tout l'historique existant depuis Last.fm

**Étapes** :
1. Ouvrir `/settings`
2. Section "Import Historique Last.fm"
3. Cliquer "Importer l'Historique"
4. Configurer limite (ex: 2000 pour tout récupérer)
5. Démarrer l'import
6. Attendre (peut prendre 5-10 minutes pour 2000 tracks)
7. Vérifier résultats dans notification
8. Aller dans `/journal` pour voir les écoutes

**Résultat** :
- Historique complet importé
- Albums enrichis avec images et IA
- Visible dans Journal et Timeline

### 2. Tracking Continu

**Objectif** : Enregistrer automatiquement les nouvelles écoutes

**Étapes** :
1. Ouvrir `/settings`
2. Section "Tracker Last.fm"
3. Cliquer "Démarrer le Tracker"
4. Vérifier statut vert
5. Écouter de la musique sur Last.fm
6. Les tracks apparaissent automatiquement dans `/journal`

**Résultat** :
- Nouvelle écoute = nouvelle entrée en base
- Enrichissement automatique
- Visible en temps réel

### 3. Workflow Complet

**Objectif** : Setup complet du système

**Étapes** :
1. **Import initial** : Importer historique (ex: 1000 dernières écoutes)
2. **Attendre fin** : Import + enrichissement (5-15 min)
3. **Démarrer tracker** : Activer tracking temps réel
4. **Utiliser l'app** :
   - Consulter Journal (`/journal`)
   - Analyser Timeline (`/timeline`)
   - Voir collection Discogs (`/collection`)
   - Générer playlists (`/playlists`)
   - Analyser stats (`/analytics`)

**Résultat** :
- Système complet et opérationnel
- Historique + tracking actif
- Toutes les fonctionnalités disponibles

---

## 🧪 Tests Effectués

### Backend

```bash
# Test import avec petite limite
curl -X POST "http://localhost:8000/api/v1/services/lastfm/import-history?limit=10&skip_existing=true"

# Résultat
{
  "status": "success",
  "tracks_imported": 10,
  "tracks_skipped": 0,
  "tracks_errors": 0,
  "albums_enriched": 10,
  "total_albums_to_enrich": 10,
  "total_scrobbles": 2003
}

# Vérification base de données
sqlite3 data/musique.db "SELECT COUNT(*) FROM listening_history;"
# Résultat: 10

# Test tracker status
curl "http://localhost:8000/api/v1/services/tracker/status"
# Résultat: {"running": false, "last_track": null, "interval_seconds": 120}
```

### Frontend

- ✅ Page Settings s'affiche correctement
- ✅ Statut tracker affiché (vert/jaune)
- ✅ Boutons Démarrer/Arrêter fonctionnels
- ✅ Dialog import s'ouvre et se ferme
- ✅ Configuration limite fonctionne
- ✅ Notifications s'affichent
- ✅ Journal affiche les 10 tracks importés
- ✅ Timeline vide (normal, tracks tous le même jour)

### Script CLI

```bash
python scripts/import_lastfm_history.py 10
# ✅ Fonctionne, import 10 tracks avec barre de progression et stats
```

---

## ⚠️ Points d'Attention

### Limites API Last.fm

- **Max 200 tracks/requête** : Import par batches
- **Rate limiting** : Délai 1s entre batches recommandé
- **Total scrobbles** : Peut être limité par l'API (souvent ~2000-5000 max)

### Performance

- **Import long** : 1000 tracks ≈ 3-5 minutes
- **Enrichissement** : Limité à 50 albums par import (évite timeout)
- **Timeout frontend** : 10 minutes max pour l'import
- **Commit fréquents** : Par lots de 50 tracks (évite perte données)

### Doublons

- **Détection** : Basée sur timestamp uniquement
- **Skip automatique** : Si `skip_existing=true`
- **Réimport** : Possible avec `skip_existing=false`

### Tracker

- **Intervalle** : 120s par défaut (ne pas mettre trop bas)
- **Démarrage** : Manuel, pas automatique au démarrage backend
- **Arrêt** : Perte du dernier track en mémoire

---

## 🚀 Améliorations Futures

### Import

- [ ] Import incrémental (depuis dernière écoute)
- [ ] Import par plage de dates
- [ ] Import en arrière-plan (worker)
- [ ] Progression en temps réel (WebSocket)
- [ ] Pause/Resume de l'import
- [ ] Export des tracks importés (CSV/JSON)

### Tracker

- [ ] Démarrage automatique au boot backend
- [ ] Configuration intervalle dans UI
- [ ] Historique des tracks détectés
- [ ] Notifications desktop (nouveaux tracks)
- [ ] Mode "catch-up" (récupère manquées si arrêté)

### Interface

- [ ] Graphique progression import
- [ ] Liste des derniers imports
- [ ] Logs d'import consultables
- [ ] Gestion des erreurs plus détaillée
- [ ] Estimation temps restant

---

## 📝 Notes Techniques

### Dépendances

**Backend** :
- `pylast` : Client API Last.fm
- Pas de nouvelle dépendance nécessaire

**Frontend** :
- Pas de nouvelle dépendance

### Configuration Required

**config.json** :
```json
{
  "secrets": {
    "lastfm": {
      "api_key": "YOUR_API_KEY",
      "api_secret": "YOUR_API_SECRET",
      "username": "YOUR_USERNAME"
    },
    "tracker": {
      "interval_seconds": 120
    }
  }
}
```

### Base de Données

**Table `listening_history`** :
- Nouvelle contrainte : timestamp unique (évite doublons)
- Index sur timestamp (performance requêtes temporelles)
- Index sur date (Timeline)

---

## 🎓 Ressources

### Code

- `backend/app/services/lastfm_service.py` : Service Last.fm
- `backend/app/services/tracker_service.py` : Tracker background
- `backend/app/api/v1/services.py` : Endpoints API
- `frontend/src/pages/Settings.tsx` : Interface paramètres
- `scripts/import_lastfm_history.py` : Script CLI

### Documentation

- `SPECIFICATION-REACT-REBUILD.md` : Spécifications projet
- `JOURNAL-TIMELINE-DOC.md` : Doc Journal/Timeline
- `CHANGELOG-UI-ENRICHMENT.md` : Changelog enrichissement UI

---

**✅ Fonctionnalité complète et opérationnelle !**

**Workflow recommandé** :
1. Import historique (1000-2000 tracks)
2. Démarrer tracker
3. Profiter de l'application !
