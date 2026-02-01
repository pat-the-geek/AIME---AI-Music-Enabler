# Dépannage : Erreur "Not Found" lors de la création de playlist

## 1️⃣ Vérifier que le backend est démarré correctement

Depuis le répertoire `backend/` :
```bash
cd backend
./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Vous devriez voir :
```
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 2️⃣ Tester l'endpoint via curl

### Test mode MANUELLE :
```bash
curl -X POST "http://localhost:8000/api/v1/playlists" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ma Playlist","track_ids":[1,2,3]}'
```

✅ Réponse attendue (201 Created):
```json
{
  "id": 1,
  "name": "Ma Playlist",
  "algorithm": "manual",
  "ai_prompt": null,
  "track_count": 3,
  "created_at": "2026-02-01T13:51:43"
}
```

### Test mode IA :
```bash
curl -X POST "http://localhost:8000/api/v1/playlists/generate" \
  -H "Content-Type: application/json" \
  -d '{"algorithm":"top_sessions","max_tracks":25}'
```

✅ Réponse attendue (201 Created):
```json
{
  "id": 2,
  "name": "Playlist top_sessions",
  "algorithm": "top_sessions",
  "track_count": 25,
  "created_at": "2026-02-01T13:53:17"
}
```

## 3️⃣ Si les tests curl échouent

### Erreur "Connection refused" :
- Backend n'est pas lancé
- Vérifiez qu'il tourne : `lsof -i :8000`
- Relancez depuis le répertoire `backend/`

### Erreur "404 Not Found" via curl :
- C'est un problème backend
- Vérifiez les logs du backend
- Assurez-vous que le commit a bien été appliqué : 
  ```bash
  git log --oneline | head -5
  ```

## 4️⃣ Si les tests curl réussissent mais l'UI affiche "Not Found"

### Vérifier la console navigateur (F12 > Console/Network) :

**Onglet Network** :
1. Ouvrez la page Playlists
2. Cliquez sur "Créer une Playlist"
3. Remplissez le formulaire
4. Cliquez "Créer"
5. Dans l'onglet Network, cherchez la requête `playlists`
6. Vérifiez :
   - **URL** : Doit être `http://localhost:8000/api/v1/playlists` (ou `/generate`)
   - **Method** : POST
   - **Status** : Doit être 201 (pas 404)
   - **Response** : Doit contenir l'ID de la playlist créée

**Onglet Console** :
- Vous devriez voir les logs :
  ```
  Creating manual playlist: {name: "...", track_ids: [...]}
  Playlist created successfully: {id: 4, name: "...", ...}
  ```

### Si le status est 404 :
- Problème d'URL ou de routing
- Vérifiez que le backend a bien redémarré
- Vérifiez que `/api/v1/playlists` existe via curl

### Si vous voyez une erreur CORS :
```
Access to XMLHttpRequest blocked by CORS policy
```
- Le backend n'accepte pas les requêtes du frontend
- Vérifiez main.py ligne ~60 (configuration CORS)

## 5️⃣ Vérifier les logs du backend

Regardez les logs en direct pendant que vous testez :
```bash
tail -f backend.log
```

Pendant la création, vous devriez voir :
```
INFO:     127.0.0.1:56206 - "POST /api/v1/playlists HTTP/1.1" 201 Created
```

## 6️⃣ Rechargement complet du frontend

Si rien ne marche, forcez le rechargement complètement :
1. Fermer le navigateur complètement
2. Vider le cache : Cmd+Shift+Delete (ou vider manuellement)
3. Rouvrir le navigateur
4. Aller à http://localhost:5173 (ou votre URL)
5. Refaire un test

## 📋 Checklist finale

- [ ] Backend lancé et affiche "Application startup complete"
- [ ] `curl` vers `/api/v1/playlists` retourne 201
- [ ] `curl` vers `/api/v1/playlists/generate` retourne 201  
- [ ] Logs du backend affichent "201 Created"
- [ ] Frontend console shows "Creating manual playlist"
- [ ] Frontend console shows "Playlist created successfully"
- [ ] UI affiche notification ✅
- [ ] Nouvelle playlist apparaît dans la liste

Si tout échoue, activez le debug mode en ajoutant dans les logs :
```javascript
// Dans Playlists.tsx
console.log('Request URL:', '/api/v1/playlists')
console.log('Request payload:', payload)
```

