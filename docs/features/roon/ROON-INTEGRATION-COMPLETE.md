# 🎵 Intégration Roon Complète - Version 4.3.1

## 🎯 Vue d'Ensemble

L'application AIME intègre maintenant un **contrôle complet de Roon**, permettant de visualiser et contrôler la lecture musicale directement depuis l'interface web, en plus du tracking automatique des écoutes.

## ✨ Fonctionnalités Roon

### 1. Widget Flottant (FloatingRoonController)

Widget en temps réel affichant le morceau en cours de lecture sur Roon.

**Caractéristiques:**
- 🎨 **Design Glassmorphism** moderne et élégant
- 📍 **Position personnalisable** (coin bas-droit par défaut)
- 🔄 **Mise à jour automatique** toutes les 3 secondes
- 📱 **Minimizable** pour libérer l'espace écran
- ✨ **Animations fluides** avec transitions CSS

**Affichage:**
```
┌─────────────────────────────┐
│  🎵 Now Playing - Roon      │
│  ────────────────────────   │
│  Title: The Song            │
│  Artist: The Artist         │
│  Album: The Album           │
│  Zone: Living Room          │
│  ────────────────────────   │
│  ⏮️  ⏸️  ⏭️  ⏹️  ➖         │
└─────────────────────────────┘
```

**Contrôles:**
- ⏮️ Previous - Morceau précédent
- ⏸️ Play/Pause - Lecture/pause
- ⏭️ Next - Morceau suivant
- ⏹️ Stop - Arrêter la lecture
- ➖ Minimize - Réduire le widget

**Fichier:** `frontend/src/components/FloatingRoonController.tsx` (500+ lignes)

### 2. Contrôles Inline dans Playlists

Chaque playlist peut maintenant être lancée directement sur Roon avec des contrôles intégrés.

**Fonctionnalités:**
- 🎯 **Track Display** sur la playlist active uniquement
- 💾 **Persistence** de la playlist active (localStorage)
- 🎮 **Contrôles directs** : Play/Pause/Next depuis la carte playlist
- ⏱️ **Timeout adapté** : 120s pour génération playlists IA

**Interface:**
```
┌─────────────────────────────────────┐
│ 📀 Ma Playlist                      │
│ ────────────────────────────────    │
│ 15 tracks • 1h 23min               │
│                                     │
│ 🎵 Now Playing:                    │
│ The Song - The Artist              │
│                                     │
│ [⏮️] [⏸️] [⏭️]  [Launch on Roon] │
└─────────────────────────────────────┘
```

**Fichier:** `frontend/src/pages/Playlists.tsx` (modifié)

### 3. Contexte Global Roon (RoonContext)

Gestion centralisée de l'état Roon dans toute l'application.

**État géré:**
```typescript
{
  nowPlaying: {
    title: string
    artist: string
    album: string
    zone_id: string
    zone_name: string
  } | null,
  zones: Zone[],
  isConnected: boolean,
  playbackControl: (action: string, zoneId?: string) => Promise<void>
}
```

**Actions disponibles:**
- `play` - Démarrer lecture
- `pause` - Mettre en pause
- `next` - Morceau suivant
- `previous` - Morceau précédent
- `stop` - Arrêter lecture

**Polling:** Mise à jour automatique toutes les 3 secondes

**Fichier:** `frontend/src/contexts/RoonContext.tsx` (nouveau)

### 4. Tracker Roon Automatique

Service background qui surveille l'activité Roon et enregistre les écoutes.

**Caractéristiques:**
- 🔄 **Polling automatique** toutes les 120 secondes (configurable)
- 🎯 **Détection multi-zones** pour systèmes Roon multi-pièces
- 💾 **Enregistrement automatique** dans listening_history
- 🔗 **Enrichissement automatique** via Spotify + IA
- 🚀 **Auto-restart** après redémarrage serveur

**Gestion des zones:**
- Attente automatique du chargement des zones (5s max)
- Vérification de la disponibilité avant démarrage
- Cache des zones pour performance

**Fichier:** `backend/app/services/roon_tracker_service.py`

### 5. API Roon Control

Endpoints REST complets pour contrôler Roon depuis n'importe quelle interface.

**Endpoints disponibles:**

```
GET  /api/v1/roon/status
     → Statut connexion Roon
     
GET  /api/v1/roon/zones
     → Liste toutes les zones disponibles
     
GET  /api/v1/roon/now-playing
     → Morceau en cours de lecture
     
POST /api/v1/roon/play
     body: { zone_id, track_title, artist, album }
     → Démarrer lecture d'un morceau
     
POST /api/v1/roon/pause
     body: { zone_id }
     → Mettre en pause
     
POST /api/v1/roon/next
     body: { zone_id }
     → Morceau suivant
     
POST /api/v1/roon/previous
     body: { zone_id }
     → Morceau précédent
     
POST /api/v1/roon/stop
     body: { zone_id }
     → Arrêter lecture
```

**Fichier:** `backend/app/api/v1/roon.py`

### 6. Service Roon Core (RoonService)

Service Python utilisant la bibliothèque `pyroon` pour communiquer avec Roon Core.

**Connexion:**
- Adresse serveur configurable (ex: 192.168.1.100)
- Port par défaut: 9330
- Token d'authentification sauvegardé automatiquement
- Timeout: 15 secondes
- Callback pour changements d'état

**Gestion zones:**
- Cache local des zones disponibles
- Mise à jour automatique via callbacks
- Attente chargement zones après connexion (3s max)

**Fichier:** `backend/app/services/roon_service.py`

## 🔄 Auto-Restart des Services

### Fonctionnalité

Tous les services background (Trackers Last.fm/Roon, Scheduler) redémarrent automatiquement après un redémarrage du serveur s'ils étaient actifs.

### Implémentation

**1. Modèle de Persistance**
```sql
CREATE TABLE service_states (
    service_name VARCHAR PRIMARY KEY,
    is_active BOOLEAN NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
```

**2. Sauvegarde Automatique**

À chaque start/stop d'un service :
```python
# backend/app/api/v1/services.py
@router.post("/tracker/start")
async def start_tracker():
    tracker = get_tracker()
    await tracker.start()
    save_service_state('tracker', True)  # ← Sauvegarde
    return {"status": "started"}
```

**3. Restauration au Démarrage**

Dans le cycle de vie de l'application :
```python
# backend/app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    await restore_active_services()  # ← Restauration automatique
    yield
    # Shutdown
    engine.dispose()
```

**4. Gestion Zones Roon**

Le tracker Roon attend que les zones soient disponibles :
```python
# backend/app/services/roon_tracker_service.py
async def start(self):
    zones = self.roon.get_zones()
    if not zones:
        # Attendre jusqu'à 5 secondes
        for i in range(5):
            await asyncio.sleep(1)
            zones = self.roon.get_zones()
            if zones:
                break
    
    if not zones:
        logger.error("Aucune zone disponible")
        return
```

### Logs de Démarrage

```
2026-02-01 18:00:00 - app.main - INFO - 🚀 Démarrage de l'application AIME
2026-02-01 18:00:00 - app.main - INFO - ✅ Base de données initialisée
2026-02-01 18:00:00 - app.api.v1.services - INFO - 🔄 Restauration des services actifs...
2026-02-01 18:00:00 - app.api.v1.services - INFO - ⏳ Attente connexion Roon...
2026-02-01 18:00:02 - app.services.roon_service - INFO - ✅ 2 zone(s) Roon disponible(s)
2026-02-01 18:00:02 - app.services.roon_tracker_service - INFO - 🎵 Tracker Roon démarré
2026-02-01 18:00:02 - app.api.v1.services - INFO - ✅ Tracker Roon restauré
```

## 📚 Documentation

### Guides Disponibles

- **[AUTO-RESTART-TEST-GUIDE.md](AUTO-RESTART-TEST-GUIDE.md)** - Guide complet test auto-restart
- **[ROON-ZONES-FIX.md](ROON-ZONES-FIX.md)** - Correction zones vides au démarrage
- **[ARCHITECTURE-COMPLETE.md](ARCHITECTURE-COMPLETE.md)** - Architecture détaillée v4.3.1
- **[docs/features/ROON-TRACKER-DOC.md](docs/features/ROON-TRACKER-DOC.md)** - Documentation tracker Roon

### Configuration

**Fichier:** `config/app.json`

```json
{
  "roon_server": "192.168.1.100",
  "roon_token": "xxxxx-xxxxx-xxxxx",
  "roon_tracker": {
    "interval_seconds": 120,
    "enabled": true
  }
}
```

## 🧪 Tests

### Tests Automatisés

```bash
cd backend
python3 test_auto_restart.py
```

### Tests Manuels

1. **Widget Roon:**
   - Lancer Roon sur une zone
   - Observer l'affichage dans le widget flottant
   - Tester les contrôles Play/Pause/Next

2. **Contrôles Playlist:**
   - Créer une playlist
   - Cliquer sur les contrôles inline
   - Vérifier l'affichage du now-playing

3. **Auto-Restart:**
   - Démarrer le tracker Roon
   - Redémarrer le serveur
   - Vérifier que le tracker redémarre automatiquement

## 🐛 Problèmes Connus

### ⚠️ Bugs Actifs

#### 🔴 Démarrage des Lectures Roon

**Problème:** Le démarrage des lectures dans Roon via AIME peut échouer ou avoir un comportement incohérent.

**Symptômes:**
- Commande `/play` ne lance pas toujours la lecture
- Délai imprévisible entre commande et démarrage
- Réponse API "OK" mais lecture non effective

**Impact:** Contrôle Play/Pause/Next parfois non fonctionnel

**Workaround:** Utiliser directement les contrôles natifs Roon puis rafraîchir AIME

#### 🔴 Cohérence État AIME ↔ Roon

**Problème:** L'état affiché dans AIME ne reflète pas toujours l'état réel de Roon.

**Symptômes:**
- État "Playing" dans AIME alors que Roon est en pause
- Track affiché obsolète après changement manuel dans Roon
- Désynchronisation après actions hors AIME

**Impact:** Affichage incorrect du now-playing, contrôles désynchronisés

**Workaround:** Rafraîchir la page ou attendre le prochain cycle de polling (3-120s)

**Status:** 🔧 En cours d'investigation

---

## ✅ Problèmes Résolus

### ✅ Zones Vides au Démarrage

**Problème:** Après redémarrage, les zones Roon n'étaient pas disponibles

**Solution:**
- Attente de 2s avant restauration tracker Roon
- Attente zones dans RoonService (3s max)
- Vérification zones dans RoonTrackerService (5s max)

**Voir:** [ROON-ZONES-FIX.md](ROON-ZONES-FIX.md)

### ✅ Track Affiché sur Toutes les Playlists

**Problème:** Le now-playing s'affichait sur toutes les playlists

**Solution:**
- Ajout `activePlaylistId` dans state
- Persistence via localStorage
- Condition d'affichage: `activePlaylistId === playlist.id`

## 🔐 Sécurité

- Token Roon sauvegardé de manière sécurisée dans `config/app.json`
- Callback automatique pour nouveaux tokens
- Configuration serveur dans fichier ignoré par Git
- Validation Pydantic sur tous les endpoints

## 🚀 Performance

- Polling intelligent (3s frontend, 120s backend)
- Cache zones Roon pour éviter requêtes répétées
- Timeout connexion Roon (15s) pour éviter blocages
- APScheduler AsyncIO pour non-blocking

## 📊 Métriques

- **Widget Roon:** ~500 lignes TypeScript/React
- **Endpoints API:** 8 nouveaux endpoints
- **Services Backend:** 2 services (RoonService + RoonTrackerService)
- **Modèle DB:** 1 nouvelle table (service_states)
- **Documentation:** 3 nouveaux guides

## 🎯 Roadmap

- [ ] Reconnexion automatique en cas de perte Roon
- [ ] Gestion multi-zones avancée (sélection zone dans UI)
- [ ] Historique lecture Roon (statistiques)
- [ ] Synchronisation playlists Roon ↔ AIME
- [ ] Notifications push lors de nouvelles écoutes
- [ ] Widget mobile responsive

---

**Version:** 4.3.1  
**Date:** 1er février 2026  
**Auteur:** Patrick Ostertag  
**Technologie:** pyroon, FastAPI, React, Material-UI
