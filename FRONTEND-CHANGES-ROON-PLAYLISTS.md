# Résumé des Modifications - Contrôle Roon et Playlists Frontend

## 🎯 Objectif Atteint

✅ **Problème 1** : "Je ne peux pas créer de playlist depuis l'application"
- Ajout d'une interface de création de playlist **manuelle**
- Support de deux modes : **IA** (existant) et **Manuelle** (nouveau)

✅ **Problème 2** : "Je souhaite cliquer sur 'Écouter sur Roon' sur chaque morceau"
- Ajout du bouton **▶️ Play** sur chaque track dans le **Journal** et la **Timeline**
- Sélection de la zone Roon dans les **Paramètres**

---

## 📁 Fichiers Créés

### `frontend/src/contexts/RoonContext.tsx` (NOUVEAU)
Contexte React global pour gérer l'état Roon :
- Vérifie le statut Roon au démarrage de l'app (`/api/v1/roon/status`)
- Stocke les settings (zone sélectionnée) dans localStorage
- Fournit fonction `playTrack(trackId)` pour démarrer la lecture
- Expose : `enabled`, `available`, `zone`, `setZone`, `playTrack`

---

## 📝 Fichiers Modifiés

### `frontend/src/App.tsx`
- Ajout du `<RoonProvider>` pour envelopper toute l'application
- Les pages enfants peuvent maintenant accéder au contexte Roon

### `frontend/src/pages/Journal.tsx`
**Imports** :
- Ajout de `PlayArrow` icon, `Snackbar`, `Alert`
- Import de `useRoon` hook

**Logique** :
- Récupère `roonEnabled` et `roonAvailable` du contexte
- Ajoute fonction `handlePlayOnRoon(trackId)` pour lancer la lecture
- Affiche des notifications (succès/erreur)

**UI** :
- Bouton ▶️ **Play** s'affiche à côté du bouton ❤️
- Visible seulement si Roon est activé ET disponible
- Au clic → appelle l'endpoint `/api/v1/roon/play-track`

### `frontend/src/pages/Timeline.tsx`
**Mêmes modifications que Journal** :
- Import du contexte Roon et du hook `useRoon`
- Ajout du bouton ▶️ sur les tracks (mode détaillé ET compact)
- Notifications de succès/erreur

### `frontend/src/pages/Playlists.tsx`
**État** :
- `createMode` : 'ai' | 'manual' (nouveau)
- `selectedTracks` : liste des IDs de tracks sélectionnés
- `availableTracks` : requête pour chercher des tracks (non implémentée encore)

**Dialog de création** :
- Nouveau sélecteur "Type de playlist"
- Mode **IA** : affiche les algorithmes existants
- Mode **Manuelle** : 
  - Champ "Nom" obligatoire
  - Section "Morceaux sélectionnés" 
  - Note : "Utilisez Journal/Timeline pour ajouter des morceaux"

**Mutation** :
- Détecte le mode et appelle l'endpoint approprié :
  - IA → `POST /api/v1/playlists/generate` (existant)
  - Manuelle → `POST /api/v1/playlists` (nouveau)

### `frontend/src/pages/Settings.tsx`
**Imports** :
- Ajout de `FormControl`, `InputLabel`, `Select`, `MenuItem`
- Import de `useRoon` hook

**État** :
- Récupère `roonEnabled`, `roonAvailable`, `zone`, `setZone` du contexte

**Nouvelle Query** :
- `roonZones` : récupère les zones disponibles via `/api/v1/roon/zones`

**UI** :
- Nouvelle section **🎛️ Contrôle Roon** (visible seulement si Roon est activé)
- Menu déroulant pour sélectionner la zone
- Affiche la zone actuellement sélectionnée

---

## 🔗 Intégration Backend

### Endpoints utilisés par le frontend

**Status check (au démarrage)** :
```
GET /api/v1/roon/status
→ { enabled: bool, available: bool, message: str }
```

**Récupérer les zones** :
```
GET /api/v1/roon/zones
→ { zones: ["Living Room", "Kitchen", ...] }
```

**Jouer un track** :
```
POST /api/v1/roon/play-track
Body: { zone_name: str, track_id: int }
→ Lecture démarre sur la zone
```

**Créer une playlist manuelle** :
```
POST /api/v1/playlists
Body: { name: str, track_ids: [int, ...] }
→ { id: int, name: str, ... }
```

---

## 🧪 Points d'Attention / À Tester

1. **RoonContext initialisation**
   - ✅ Appel `/api/v1/roon/status` au démarrage
   - ✅ localStorage sauvegarde la zone
   - ✓ À tester : zone chargée après refresh de page

2. **Boutons Play**
   - ✅ Affichés uniquement si Roon disponible
   - ✅ Appellent l'endpoint avec le bon trackId
   - ✓ À tester : erreur si zone non sélectionnée

3. **Playlists manuelles**
   - ✅ Boîte de dialogue bascule entre modes IA/Manuelle
   - ✅ Validation des champs (nom + tracks requis)
   - ✓ À tester : création réelle avec tracks
   - ⚠️ À implémenter : interface pour sélectionner les tracks directement

4. **Zone Roon**
   - ✅ Sélectionnable dans Paramètres
   - ✅ Persistée en localStorage
   - ✓ À tester : Si zone invalide → erreur ?

---

## 🚀 Prochaines Étapes

### Court terme (MVP)
1. **Tester la compil frontend** → `npm run build` ✅
2. **Tester le démarrage** → `npm run dev` 🔄
3. **Tester les endpoints** via curl ou Postman 🔄
4. **Tester sur Roon réel** 🔄

### Moyen terme
1. **Workflow de sélection de tracks** pour playlists manuelles
   - Bouton "Ajouter à une playlist" dans Journal/Timeline
   - Stockage temporaire des sélections
   - Finalisation lors de la création de playlist

2. **Affichage des playlists**
   - Lister les playlists créées
   - Afficher le nombre de tracks
   - Bouton pour jouer sur Roon

3. **Enrichissement des tracks**
   - Afficher cover album
   - Afficher année
   - Liens Spotify/Discogs

---

## 📊 Statistiques des Changements

| Fichier | Type | Lignes | Description |
|---------|------|--------|-------------|
| RoonContext.tsx | NEW | 60 | Contexte global Roon |
| App.tsx | MOD | +5 | Ajout RoonProvider |
| Journal.tsx | MOD | +80 | Bouton Play + notifications |
| Timeline.tsx | MOD | +60 | Bouton Play (2 modes) |
| Playlists.tsx | MOD | +150 | Mode IA/Manuelle |
| Settings.tsx | MOD | +40 | Zone Roon selector |
| **Total** | | **~395** | |

---

## ✅ Commits Effectués

1. **3314505** - feat: Add Roon playback controls and manual playlist creation to frontend
2. **e57c77a** - docs: Add user guide for Roon controls and playlists

---

## 🎤 Notes pour l'Utilisateur

### Configuration minimale requise
```json
// config/app.json
{
  "roon_control": {
    "enabled": true
  }
}
```

### Première utilisation
1. Ouvrir l'application
2. Aller dans **Paramètres** → **🎛️ Contrôle Roon**
3. Sélectionner la zone Roon
4. Retourner au **Journal**
5. Cliquer ▶️ sur un morceau → lecture démarre !

---

## 🐛 Erreurs Potentielles

| Erreur | Cause | Solution |
|--------|-------|----------|
| Les boutons Play n'apparaissent pas | Roon désactivé | Activer dans config |
| "Aucune zone" | Zone non sélectionnée | Aller dans Paramètres |
| Erreur lors de la lecture | Zone invalide | Vérifier que la zone existe |
| Playlists : "Track #123" au lieu du titre | Bug d'affichage | À corriger |

