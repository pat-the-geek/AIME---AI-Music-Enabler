# Migration Guide - Contrôle Roon Conditionnel & Création Playlists

## 🔄 Changements apportés

### 1. Contrôle Roon conditionnel

Le contrôle Roon est désormais **activable/désactivable** via la configuration.

#### Configuration requise

Dans `config/app.json`, ajoutez la section `roon_control` :

```json
{
  "roon_control": {
    "enabled": true
  }
}
```

**Par défaut :** Le contrôle Roon est **activé** si la configuration existe.

#### Nouveau endpoint de statut

```bash
GET /api/v1/roon/status
```

**Réponse quand activé et disponible :**
```json
{
  "enabled": true,
  "available": true,
  "message": "Roon disponible"
}
```

**Réponse quand désactivé :**
```json
{
  "enabled": false,
  "available": false,
  "message": "Contrôle Roon désactivé"
}
```

#### Comportement des endpoints

Tous les endpoints Roon (`/api/v1/roon/*` sauf `/status`) retournent maintenant une **erreur 403** si `roon_control.enabled = false` :

```json
{
  "detail": "Le contrôle Roon n'est pas activé. Activez-le dans config/app.json (roon_control.enabled)"
}
```

### 2. Création de playlists manuelles

Un nouvel endpoint a été ajouté pour créer des playlists **manuellement** (sans IA ni algorithme).

#### Nouveau schéma Pydantic

```python
class PlaylistCreate(BaseModel):
    name: str  # Nom de la playlist
    track_ids: List[int]  # Liste des IDs de tracks
```

#### Nouvel endpoint

```bash
POST /api/v1/playlists
Content-Type: application/json

{
  "name": "Ma Playlist Rock",
  "track_ids": [123, 456, 789, 1011]
}
```

**Réponse (201 Created) :**
```json
{
  "id": 42,
  "name": "Ma Playlist Rock",
  "algorithm": "manual",
  "ai_prompt": null,
  "track_count": 4,
  "created_at": "2026-02-01T14:30:00Z"
}
```

### 3. Lecture d'un track sur Roon depuis son ID

Nouvel endpoint simplifié pour jouer un track directement depuis l'interface web.

```bash
POST /api/v1/roon/play-track
Content-Type: application/json

{
  "zone_name": "Living Room",
  "track_id": 123
}
```

**Avantage :** Pas besoin de récupérer manuellement les métadonnées (titre, artiste, album) - tout est fait automatiquement depuis la base de données.

---

## 🎨 Intégration Frontend

### Vérifier si Roon est activé

```typescript
// Service pour vérifier le statut Roon
async function checkRoonStatus() {
  const response = await fetch('http://localhost:8000/api/v1/roon/status');
  const data = await response.json();
  return data.enabled && data.available;
}

// Utilisation dans un composant React
const [roonAvailable, setRoonAvailable] = useState(false);

useEffect(() => {
  checkRoonStatus().then(setRoonAvailable);
}, []);
```

### Bouton "Écouter sur Roon" par track

```typescript
// Composant TrackItem
interface TrackItemProps {
  track: {
    id: number;
    title: string;
    artist: string;
    album: string;
  };
}

function TrackItem({ track }: TrackItemProps) {
  const [roonAvailable, setRoonAvailable] = useState(false);
  const [defaultZone, setDefaultZone] = useState('Living Room');

  useEffect(() => {
    // Vérifier si Roon est disponible
    fetch('http://localhost:8000/api/v1/roon/status')
      .then(res => res.json())
      .then(data => setRoonAvailable(data.enabled && data.available));
    
    // Charger la zone par défaut depuis les préférences utilisateur
    const savedZone = localStorage.getItem('roon_default_zone');
    if (savedZone) setDefaultZone(savedZone);
  }, []);

  const playOnRoon = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/roon/play-track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_name: defaultZone,
          track_id: track.id
        })
      });

      if (!response.ok) {
        const error = await response.json();
        alert(`Erreur: ${error.detail}`);
        return;
      }

      const result = await response.json();
      console.log('Lecture démarrée:', result.message);
      
      // Notification succès (toast, snackbar, etc.)
      showNotification(`Lecture de "${track.title}" sur ${defaultZone}`);
    } catch (error) {
      console.error('Erreur lecture Roon:', error);
      alert('Impossible de démarrer la lecture sur Roon');
    }
  };

  return (
    <div className="track-item">
      <div className="track-info">
        <h3>{track.title}</h3>
        <p>{track.artist} - {track.album}</p>
      </div>
      
      {roonAvailable && (
        <button
          onClick={playOnRoon}
          className="btn-roon"
          title={`Écouter sur Roon (${defaultZone})`}
        >
          🎵 Écouter sur Roon
        </button>
      )}
    </div>
  );
}
```

### Sélecteur de zone Roon

```typescript
// Composant pour choisir la zone
function RoonZoneSelector() {
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState('');

  useEffect(() => {
    // Charger les zones disponibles
    fetch('http://localhost:8000/api/v1/roon/zones')
      .then(res => res.json())
      .then(data => {
        setZones(data.zones);
        
        // Charger la zone sauvegardée ou prendre la première
        const saved = localStorage.getItem('roon_default_zone');
        setSelectedZone(saved || data.zones[0]?.name || '');
      });
  }, []);

  const handleZoneChange = (zoneName: string) => {
    setSelectedZone(zoneName);
    localStorage.setItem('roon_default_zone', zoneName);
  };

  return (
    <select
      value={selectedZone}
      onChange={(e) => handleZoneChange(e.target.value)}
      className="zone-selector"
    >
      {zones.map((zone: any) => (
        <option key={zone.zone_id} value={zone.name}>
          {zone.name} ({zone.state})
        </option>
      ))}
    </select>
  );
}
```

### Création de playlist depuis l'interface

```typescript
// Service de création de playlist
async function createPlaylist(name: string, trackIds: number[]) {
  const response = await fetch('http://localhost:8000/api/v1/playlists', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      track_ids: trackIds
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
}

// Composant de création
function PlaylistCreator() {
  const [name, setName] = useState('');
  const [selectedTracks, setSelectedTracks] = useState<number[]>([]);

  const handleCreate = async () => {
    if (!name.trim()) {
      alert('Veuillez donner un nom à la playlist');
      return;
    }

    if (selectedTracks.length === 0) {
      alert('Veuillez sélectionner au moins un morceau');
      return;
    }

    try {
      const playlist = await createPlaylist(name, selectedTracks);
      console.log('Playlist créée:', playlist);
      showNotification(`Playlist "${name}" créée avec ${playlist.track_count} morceaux`);
      
      // Réinitialiser le formulaire
      setName('');
      setSelectedTracks([]);
    } catch (error) {
      console.error('Erreur création playlist:', error);
      alert(`Erreur: ${error.message}`);
    }
  };

  return (
    <div className="playlist-creator">
      <input
        type="text"
        placeholder="Nom de la playlist"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      
      <TrackSelector
        selectedTracks={selectedTracks}
        onSelectionChange={setSelectedTracks}
      />
      
      <button onClick={handleCreate}>
        Créer la playlist ({selectedTracks.length} morceaux)
      </button>
    </div>
  );
}
```

---

## 📋 Checklist de migration

### Backend

- [x] Ajouter `roon_control.enabled` dans `config/app.json`
- [x] Vérifier que tous les endpoints Roon utilisent `check_roon_enabled()`
- [x] Tester `/api/v1/roon/status`
- [x] Tester création de playlist avec `POST /api/v1/playlists`
- [x] Tester lecture de track avec `POST /api/v1/roon/play-track`

### Frontend

- [ ] Implémenter `checkRoonStatus()` au démarrage de l'app
- [ ] Ajouter bouton "Écouter sur Roon" sur chaque track
- [ ] Conditionner l'affichage du bouton sur `roonAvailable`
- [ ] Implémenter le sélecteur de zone Roon
- [ ] Créer le formulaire de création de playlist manuelle
- [ ] Tester le workflow complet : créer playlist → jouer sur Roon

---

## 🎯 Scénarios d'utilisation

### Scénario 1 : Désactiver Roon temporairement

**Cas :** Maintenance du serveur Roon ou déplacement du matériel.

**Action :**
1. Éditer `config/app.json`
2. Mettre `roon_control.enabled: false`
3. Redémarrer le backend
4. Les boutons Roon disparaissent automatiquement du frontend

### Scénario 2 : Créer et jouer une playlist

**Workflow :**
1. Sélectionner des tracks dans l'historique d'écoute
2. Cliquer "Créer une playlist"
3. Nommer la playlist
4. Valider → Playlist créée
5. Cliquer "Jouer sur Roon"
6. Choisir la zone
7. La playlist démarre sur Roon

### Scénario 3 : Écoute rapide depuis l'historique

**Workflow :**
1. Parcourir l'historique d'écoute
2. Voir un morceau intéressant
3. Cliquer "🎵 Écouter sur Roon"
4. Le morceau démarre immédiatement sur la zone par défaut

---

## 🔧 Configuration recommandée

### Production

```json
{
  "roon_control": {
    "enabled": true
  },
  "roon_tracker": {
    "enabled": true,
    "interval_seconds": 120
  }
}
```

### Développement

```json
{
  "roon_control": {
    "enabled": true
  },
  "roon_tracker": {
    "enabled": false
  }
}
```

### Sans Roon

```json
{
  "roon_control": {
    "enabled": false
  },
  "roon_tracker": {
    "enabled": false
  }
}
```

---

## 📝 Notes techniques

- **Thread-safe :** Les endpoints Roon utilisent des sessions de base de données dédiées
- **Cache :** Le statut Roon devrait être mis en cache côté frontend (TTL: 30s)
- **Zones :** La liste des zones change rarement, cache possible (TTL: 5min)
- **Erreurs 403 :** Intercepter et afficher un message convivial à l'utilisateur
- **Performance :** `/roon/status` est rapide (~50ms), peut être appelé fréquemment
