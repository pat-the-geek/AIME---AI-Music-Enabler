# Contrôle Roon et Playlists - Guide d'utilisation

## 🎮 Contrôle de lecture Roon depuis AIME

AIME permet maintenant de contrôler la lecture sur Roon directement depuis l'interface web.

### Configuration

Dans `config/secrets.json`, configurez votre serveur Roon :

```json
{
  "roon": {
    "server": "192.168.1.100",
    "token": "votre_token_roon"
  }
}
```

### API Endpoints Roon

#### 1. Récupérer les zones disponibles

```bash
GET /api/v1/roon/zones
```

**Réponse :**
```json
{
  "zones": [
    {
      "zone_id": "12345",
      "name": "Living Room",
      "state": "playing"
    }
  ]
}
```

#### 2. Lecture en cours

```bash
GET /api/v1/roon/now-playing
```

**Réponse :**
```json
{
  "title": "The Logical Song",
  "artist": "Supertramp",
  "album": "Breakfast in America",
  "zone_id": "12345",
  "zone_name": "Living Room"
}
```

#### 3. Démarrer la lecture d'un morceau

```bash
POST /api/v1/roon/play
Content-Type: application/json

{
  "zone_name": "Living Room",
  "track_title": "The Logical Song",
  "artist": "Supertramp",
  "album": "Breakfast in America"
}
```

#### 4. Contrôler la lecture

```bash
POST /api/v1/roon/control
Content-Type: application/json

{
  "zone_name": "Living Room",
  "control": "pause"
}
```

**Contrôles disponibles :** `play`, `pause`, `stop`, `next`, `previous`

#### 5. Mettre en pause toutes les zones

```bash
POST /api/v1/roon/pause-all
```

---

## 📋 Playlists

### Créer une playlist

#### 1. Playlist manuelle

```bash
POST /api/v1/playlists
Content-Type: application/json

{
  "name": "Ma Playlist Rock",
  "algorithm": "manual",
  "track_ids": [123, 456, 789]
}
```

#### 2. Playlist IA générée

```bash
POST /api/v1/playlists/generate-ai
Content-Type: application/json

{
  "name": "Playlist Jazz Relaxant",
  "prompt": "Crée une playlist de jazz relaxant pour travailler",
  "track_count": 20
}
```

### Récupérer les playlists

```bash
GET /api/v1/playlists
```

### Détails d'une playlist

```bash
GET /api/v1/playlists/{playlist_id}
```

### Tracks d'une playlist

```bash
GET /api/v1/playlists/{playlist_id}/tracks
```

### Ajouter un track à une playlist

```bash
POST /api/v1/playlists/{playlist_id}/tracks
Content-Type: application/json

{
  "track_id": 123
}
```

### Retirer un track d'une playlist

```bash
DELETE /api/v1/playlists/{playlist_id}/tracks/{track_id}
```

---

## 🎵 Jouer une Playlist sur Roon

La fonctionnalité la plus puissante : jouer une playlist AIME directement sur Roon !

```bash
POST /api/v1/playlists/{playlist_id}/play-on-roon?zone_name=Living%20Room
```

**Réponse :**
```json
{
  "message": "Playlist 'Ma Playlist Rock' en lecture sur Living Room",
  "playlist_id": 42,
  "track_count": 15,
  "first_track": "The Logical Song",
  "zone": "Living Room"
}
```

---

## 📝 Exemples d'utilisation

### Workflow complet : Créer et jouer une playlist

```bash
# 1. Créer une playlist
curl -X POST "http://localhost:8000/api/v1/playlists" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Soirée Jazz",
    "algorithm": "manual",
    "track_ids": [123, 456, 789, 1011]
  }'

# 2. Vérifier les zones Roon disponibles
curl "http://localhost:8000/api/v1/roon/zones"

# 3. Jouer la playlist sur Roon
curl -X POST "http://localhost:8000/api/v1/playlists/1/play-on-roon?zone_name=Living%20Room"
```

### Contrôle de lecture pendant l'écoute

```bash
# Pause
curl -X POST "http://localhost:8000/api/v1/roon/control" \
  -H "Content-Type: application/json" \
  -d '{"zone_name": "Living Room", "control": "pause"}'

# Reprise
curl -X POST "http://localhost:8000/api/v1/roon/control" \
  -H "Content-Type: application/json" \
  -d '{"zone_name": "Living Room", "control": "play"}'

# Piste suivante
curl -X POST "http://localhost:8000/api/v1/roon/control" \
  -H "Content-Type: application/json" \
  -d '{"zone_name": "Living Room", "control": "next"}'
```

---

## 🔧 Intégration Frontend

### Exemple React/TypeScript

```typescript
// Service Roon
class RoonService {
  private baseUrl = 'http://localhost:8000/api/v1/roon';

  async getZones() {
    const response = await fetch(`${this.baseUrl}/zones`);
    return await response.json();
  }

  async playTrack(zoneName: string, track: { title: string; artist: string; album?: string }) {
    const response = await fetch(`${this.baseUrl}/play`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        zone_name: zoneName,
        track_title: track.title,
        artist: track.artist,
        album: track.album
      })
    });
    return await response.json();
  }

  async control(zoneName: string, control: 'play' | 'pause' | 'stop' | 'next' | 'previous') {
    const response = await fetch(`${this.baseUrl}/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone_name: zoneName, control })
    });
    return await response.json();
  }
}

// Service Playlists
class PlaylistService {
  private baseUrl = 'http://localhost:8000/api/v1/playlists';

  async createPlaylist(name: string, trackIds: number[]) {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        algorithm: 'manual',
        track_ids: trackIds
      })
    });
    return await response.json();
  }

  async playOnRoon(playlistId: number, zoneName: string) {
    const response = await fetch(
      `${this.baseUrl}/${playlistId}/play-on-roon?zone_name=${encodeURIComponent(zoneName)}`,
      { method: 'POST' }
    );
    return await response.json();
  }
}
```

---

## 🎯 Cas d'usage

### 1. Lecture contextuelle

Créer des playlists pour différentes ambiances et les jouer selon le contexte :

- **Travail concentré** : Jazz instrumental, musique classique
- **Sport** : Rock énergique, électro dynamique
- **Détente** : Ambient, chillout, jazz doux
- **Soirée** : Mix dansant, hits variés

### 2. Recommandations IA

Utiliser l'IA pour générer des playlists basées sur :
- Vos écoutes récentes
- Des critères d'ambiance
- Des découvertes musicales
- Des périodes historiques

### 3. Automatisation

Programmer des scénarios :
- Réveil en douceur avec playlist morning jazz
- Playlist énergique pour le sport
- Musique de fond pour le travail
- Playlist relaxante le soir

---

## ⚠️ Limitations actuelles

1. **Queue complète** : Actuellement, seul le premier track de la playlist est joué. L'ajout de la queue complète nécessite l'implémentation de l'API browse avancée de Roon.

2. **Recherche de tracks** : La recherche utilise la navigation hiérarchique de Roon (Artist -> Album -> Track), qui peut échouer si les métadonnées ne correspondent pas exactement.

3. **Zones multiples** : Impossible de jouer sur plusieurs zones simultanément (limitation Roon API).

---

## 🚀 Évolutions futures

- [ ] Queue complète de playlist sur Roon
- [ ] Synchronisation bidirectionnelle (Roon → AIME)
- [ ] Playlists intelligentes basées sur l'écoute
- [ ] Export playlists vers Spotify/Apple Music
- [ ] Contrôle vocal via intégration IA
- [ ] Playlist collaboratives
