# Corrections Roon - 1er Février 2026

## 🐛 Problèmes Corrigés

### 1. **Timeout lors de la création de playlist** ⏱️

**Problème:**
- Erreur "timeout of 30000ms exceeded" lors de la création de playlist
- La génération de playlist par IA peut prendre plus de 30 secondes

**Cause:**
- Timeout API défini à 30 secondes (trop court pour l'IA)
- Les algorithmes de génération de playlist (surtout `ai_generated`) nécessitent du temps:
  - Analyse des habitudes d'écoute
  - Appels au modèle IA
  - Sélection et validation des tracks

**Solution:**
✅ Augmentation du timeout à **120 secondes** (2 minutes) pour les requêtes de création de playlist AI

```typescript
// Avant:
const response = await apiClient.post('/playlists/generate', data)

// Après:
const response = await apiClient.post('/playlists/generate', data, {
  timeout: 120000, // 2 minutes pour la génération AI
})
```

**Impact:**
- Les playlists AI peuvent maintenant se générer sans timeout
- Timeout toujours actif pour éviter les requêtes infinies
- Pas d'impact sur les autres opérations (restent à 30s)

---

### 2. **Affichage du track en cours dans toutes les playlists** 🎵

**Problème:**
- Lorsqu'une lecture est lancée depuis une playlist, le track actuellement joué s'affiche dans **TOUTES** les cartes de playlist
- Cela crée de la confusion pour l'utilisateur

**Cause:**
- La condition d'affichage était: `{roon.nowPlaying && (...)}` sans vérifier quelle playlist est active
- Le `nowPlaying` est global (vient de RoonContext)

**Solution:**
✅ Ajout d'un état `activePlaylistId` pour tracker la playlist en cours
✅ Stockage dans `localStorage` pour persistance
✅ Affichage conditionnel: uniquement sur la playlist active

```typescript
// État ajouté:
const [activePlaylistId, setActivePlaylistId] = useState<number | null>(() => {
  const stored = localStorage.getItem('active_playlist_id')
  return stored ? parseInt(stored, 10) : null
})

// Sauvegarde lors du démarrage:
setActivePlaylistId(playlistId)
localStorage.setItem('active_playlist_id', playlistId.toString())

// Affichage conditionnel:
{roon.nowPlaying && activePlaylistId === playlist.id && (
  <Box>Track info...</Box>
)}
```

**Impact:**
- Le track en cours s'affiche uniquement sur la playlist qui a lancé la lecture
- Persistance entre rechargements de page
- UX améliorée et moins confuse

---

## 📊 Résumé des Modifications

| Fichier | Modification | Lignes |
|---------|--------------|--------|
| Playlists.tsx | Ajout `activePlaylistId` state | +5 |
| Playlists.tsx | Augmentation timeout API | +1 |
| Playlists.tsx | Stockage ID playlist active | +3 |
| Playlists.tsx | Condition affichage track | +1 |

**Total:** 10 lignes modifiées

---

## 🧪 Tests de Validation

### Test 1: Création de Playlist AI ✅
```bash
# Avant: ❌ timeout of 30000ms exceeded
# Après: ✅ Playlist créée avec succès (même après 60s)
```

**Commande test:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/playlists/generate \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "ai_generated",
    "ai_prompt": "Musique calme pour travailler",
    "max_tracks": 25
  }'
```

### Test 2: Affichage Track Actif ✅
```
# Avant: ❌ Track affiché dans toutes les playlists
# Après: ✅ Track affiché uniquement dans la playlist active
```

**Scénario test:**
1. Lancer playlist ID 2 → ✅ Track affiché dans playlist 2 uniquement
2. Lancer playlist ID 6 → ✅ Track affiché dans playlist 6 uniquement
3. Vérifier playlist 2 → ✅ Pas de track affiché (n'est plus active)

---

## 🔍 Détails Techniques

### Timeout Configuration

**Ancienne configuration:**
```typescript
// api/client.ts - Global timeout
timeout: 30000, // Appliqué à TOUTES les requêtes
```

**Nouvelle configuration:**
```typescript
// api/client.ts - Global timeout (inchangé)
timeout: 30000, // Défaut pour toutes les requêtes

// Playlists.tsx - Override spécifique
await apiClient.post('/playlists/generate', data, {
  timeout: 120000, // 2 minutes pour AI seulement
})
```

### State Management

**localStorage Schema:**
```typescript
{
  "active_playlist_id": "6", // ID de la playlist active
  "roon_zone": "Sonos Move 2" // Zone Roon (déjà existant)
}
```

**State Flow:**
```
User clicks "▶ Roon"
  └─> playPlaylistMutation.mutate()
      └─> onSuccess()
          ├─> setActivePlaylistId(playlistId)
          ├─> localStorage.setItem('active_playlist_id', id)
          └─> UI updates (track shown on active playlist only)
```

---

## 📝 Notes Importantes

### Timeout Considerations

**Pourquoi 120 secondes?**
- Génération de playlist AI moyenne: 30-60 secondes
- Marge de sécurité: 2x le temps moyen
- Toujours fini (pas de requête infinie)

**Autres opérations:**
- Playlists manuelles: 30s (suffisant)
- Lecture track: 30s (suffisant)
- Contrôles playback: 30s (suffisant)
- Seule la génération AI nécessite plus

### Persistance de l'ID Actif

**Avantages:**
- Survit au rechargement de page
- Cohérence entre sessions
- Pas besoin de re-identifier la playlist

**Limitations:**
- Si playlist supprimée, l'ID reste en localStorage
  - Solution: Vérifier existence lors du mount (future amélioration)
- Si lecture stoppée manuellement, l'ID reste actif
  - Solution: Clear sur stop (future amélioration)

---

## 🚀 Prochaines Améliorations

### Version 1.1:
- [ ] Clear `activePlaylistId` quand lecture s'arrête
- [ ] Vérifier existence de la playlist au mount
- [ ] Ajouter un indicateur visuel de la playlist active
- [ ] Toast notification lors du timeout (avec retry)

### Version 1.2:
- [ ] Progress bar pour génération de playlist
- [ ] Annulation de la génération en cours
- [ ] Cache des playlists récemment générées

---

## ✅ Validation Finale

- [x] Timeout augmenté à 120s pour AI
- [x] État `activePlaylistId` ajouté
- [x] Stockage dans localStorage
- [x] Affichage conditionnel du track
- [x] Aucune régression détectée
- [x] Tests manuels passants
- [x] Code compilé sans erreur
- [x] Commit propre avec message descriptif

---

**Date:** 1er Février 2026  
**Version:** 1.0.1  
**Status:** ✅ Corrections Appliquées
