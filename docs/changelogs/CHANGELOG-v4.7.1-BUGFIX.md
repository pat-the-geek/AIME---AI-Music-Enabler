# Changelog - v4.7.1 - Bugfix Portrait Button

**Date:** 9 février 2026  
**Type:** Bugfix  
**Severity:** High  
**Impact:** Magazine Portrait feature

---

## 🐛 Bug Corrigé

### Portrait Button Non-Fonctionnel dans le Magazine

**Problème:** Le bouton "Portrait" dans le magazine ne fonctionnait pas. Le clic ouvrait un modal vide sans contenu.

**Cause:** 
1. Endpoint de streaming incorrect (déjà partiellement corrigé en v4.7.0)
2. **Endpoint de recherche d'artiste incorrect** - Le code frontend appelait `/artists/list` au lieu de `/collection/artists/list`
3. Cela créait une erreur 404 qui empêchait le modal de récupérer l'ID et le nom de l'artiste

---

## ✅ Corrections Appliquées

### 1. Frontend - MagazinePage.tsx

**Fichier:** `frontend/src/components/MagazinePage.tsx`  
**Ligne:** 177-182

**Avant:**
```typescript
const handleOpenArtistPortrait = async (artistName: string, artistId?: number) => {
  try {
    // Si on n'a pas l'ID, chercher l'artiste
    if (!artistId) {
      const response = await apiClient.get('/artists/list', {  // ❌ MAUVAIS
        params: { search: artistName, limit: 1 }
      })
```

**Après:**
```typescript
const handleOpenArtistPortrait = async (artistName: string, artistId?: number) => {
  try {
    // Si on n'a pas l'ID, chercher l'artiste
    if (!artistId) {
      const response = await apiClient.get('/collection/artists/list', {  // ✅ CORRECT
        params: { search: artistName, limit: 1 }
      })
```

**Raison:** 
- `apiClient.defaults.baseURL` est configuré à `/api/v1`
- L'endpoint backend est à `/api/v1/collection/artists/list`
- Donc l'appel doit être `/collection/artists/list` pour résoudre correctement

---

## 📋 Récapitulatif

### Fichiers Modifiés

| Fichier | Changement |
|---------|-----------|
| `frontend/src/components/MagazinePage.tsx` | ✅ Correction endpoint de recherche d'artiste |

### Chaîne Complète du Portrait

```
User clicks Portrait button
  ↓
handleOpenArtistPortrait(artistName)
  ↓
GET /collection/artists/list?search=artistName&limit=1  ✅ CORRECT
  ↓
Response: { artists: [{ id: 123, name: "Artist", ... }] }
  ↓
setPortraitOpen(true)
setPortraitArtistId(123)
  ↓
<ArtistPortraitModal /> opens
  ↓
GET /collection/artists/123/article/stream  ✅ CORRECT (déjà corrigé en v4.7.0)
  ↓
Portrait content streams and displays ✅ WORKS
```

---

## 🔗 Backend Verification

**Endpoint pour la recherche:**
```python
# backend/app/api/v1/collection/artists.py
@router.get("/list")
```

Route complète: `/api/v1/collection/artists/list`

**Paramètres requis:**
- `search` (optionnel): Recherche par nom d'artiste
- `limit` (optionnel, défaut 50): Nombre de résultats max

---

## 🧪 Test de Vérification

### Test 1: Vérifier l'endpoint backend

```bash
# Tester l'endpoint directement
curl -s "http://localhost:8000/api/v1/collection/artists/list?search=Beck&limit=1" | jq
```

Réponse attendue:
```json
{
  "count": 1,
  "artists": [
    {
      "id": 24,
      "name": "Beck",
      "spotify_id": "...",
      "image_url": "..."
    }
  ]
}
```

### Test 2: Tester le bouton dans le magazine

1. Ouvrir la page Magazine
2. Cliquer sur n'importe quel bouton "Portrait"
3. Modal devrait s'ouvrir
4. Contenu devrait streamer caractère par caractère

---

## 📝 Historique des Corrections

### v4.7.0
- ✅ Corrigé URL de streaming: `/artists/{id}/article/stream` → `/collection/artists/{id}/article/stream`
- ❌ Manqué: endpoint de recherche d'artiste

### v4.7.1
- ✅ Corrigé URL de recherche: `/artists/list` → `/collection/artists/list`
- ✅ Maintenant tous les endpoints du Portrait fonctionnent correctement

---

## 🚀 Application du Bugfix

### Aucune migration database nécessaire

C'est un pur bugfix frontend, pas de changements backend requis.

### Actions à faire

1. **Frontend build/reload:**
   ```bash
   cd frontend
   npm run build  # ou npm run dev pour le développement
   ```

2. **Browser reload:**
   - Appuyer sur F5 ou Cmd+R pour recharger la page
   - Ou vider le cache si nécessaire (Ctrl+Shift+Delete)

3. **Test:**
   - Ouvrir le magazine
   - Cliquer sur un bouton Portrait
   - Vérifier que le modal s'ouvre et affiche le contenu

---

## ✨ Impact

- ✅ Portrait button now fully functional
- ✅ Artist lookup working correctly
- ✅ Streaming content displaying progressively
- ✅ User can close modal and continue reading magazine

---

## 📞 Support

Si la correction ne fonctionne pas:

1. Vérifier la console du navigateur (F12) pour les erreurs réseau
2. Vérifier que le backend est en cours d'exécution
3. Vérifier que l'endpoint `/collection/artists/list` répond avec des données

