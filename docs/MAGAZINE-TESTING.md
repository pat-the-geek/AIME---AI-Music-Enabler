## 🧪 Guide de Testing - Magazine

### ✅ Pré-requis

- [ ] Backend lancé (`python -m uvicorn app.main:app --reload`)
- [ ] Frontend lancé (`npm run dev`)
- [ ] Base de données avec albums et haikus
- [ ] Euria configuré dans `secrets.json`

---

## 1️⃣ Test Quick Start (2 minutes)

### Backend Test
```bash
# Dans le dossier backend/
curl http://localhost:8000/api/v1/magazines/generate
```

**Résultat attendu** :
```json
{
  "id": "magazine-1706..."
  "generated_at": "2026-02-03T10:15:30.123456",
  "pages": [
    {
      "page_number": 1,
      "type": "artist_showcase",
      "title": "🎤 Artiste Name",
      ...
    },
    ...
  ],
  "total_pages": 5
}
```

### Frontend Test
1. Allez sur `http://localhost:5173/magazine`
2. Attendez 3-10s (génération en cours)
3. Vérifiez que la page 1 s'affiche

---

## 2️⃣ Test Complet (15 minutes)

### Test de Navigation
```
✓ Page 1 affichée
✓ Scroll souris → Page 2
✓ Scroll souris → Page 3
✓ Bouton "Précédente" → Page 2
✓ Bouton "Suivante" → Page 3
✓ Dots pagination → direct à Page 4
✓ Tous les dots cliquables
```

### Test du Minuteur
```
✓ Minuteur visible (15:00 au départ)
✓ Décompte visible en temps réel
✓ Format MM:SS correct
```

### Test "Nouvelle édition"
```
✓ Cliquer le bouton
✓ Snackbar "en cours de génération"
✓ Attendre 3-10s
✓ Nouvelle édition chargée
✓ Retour à page 1
✓ Minuteur reset à 15:00
✓ Contenu différent (albums, artistes, haikus)
```

### Test Responsive
```
Desktop (1920x1080)  : ✓ Full-width, tous les éléments visibles
Tablet (768x1024)    : ✓ Adaptations layout
Mobile (375x667)     : ✓ Stack vertical, navigation accessible
```

---

## 3️⃣ Test Pages Individuelles

### Page 1 - Artiste
```
Vérifications:
□ Titre avec emoji "🎤"
□ Nom artiste lisible
□ Haïku affiché en 3 lignes
□ Albums listés avec images
□ Hover effect sur albums
□ Couleurs cohérentes
```

### Page 2 - Album Detail
```
Vérifications:
□ Image centrage correct
□ Titre et artiste lisibles
□ Année affichée
□ Genre en chip
□ Description complète
□ Pas de texte tronqué
```

### Page 3 - Albums + Haikus
```
Vérifications:
□ Titre "🎋 Haïkus Musicaux"
□ 3 albums affichés
□ Haïkus en italique
□ Format 5-7-5 visible
□ Grid responsive
□ Transition hover smooth
```

### Page 4 - Timeline & Stats
```
Vérifications:
□ 3 cartes stats (listens, artistes, albums)
□ Nombres corrects et affichés
□ Listes "Top Artistes" et "Top Albums"
□ Couleurs distinctes (bleu, rose)
□ Classement visible (1, 2, 3...)
```

### Page 5 - Playlist Theme
```
Vérifications:
□ Titre avec thème aléatoire
□ Description playlist lisible
□ Albums de la playlist listés
□ Images chargées
□ Hover effect
□ Nombre albums = 5-7
```

---

## 4️⃣ Test de Variabilité (Éxecuter 3x)

```
1ère génération:
- Note les artistes affichés
- Note les couleurs (dark/light/vibrant)
- Note les layouts

2ème génération (cliquer "Nouvelle édition"):
- Vérifiez que TOUT a changé
- Artistes différents
- Couleurs potentiellement différentes
- Albums différents
- Haïkus différents

3ème génération:
- Vérifiez à nouveau la variation
```

**Résultat** : Chaque magazine doit être unique ! 🎲

---

## 5️⃣ Test de Performance

### Timing
```
Mesure 1: Ouverture /magazine
- Temps = ? (cible < 1s pour affichage initial)

Mesure 2: Génération complète
- Temps = ? (cible < 10s)
- Breakdown: Haïkus Euria = 5-8s typiquement

Mesure 3: Navigation page
- Temps = ? (cible < 100ms)

Mesure 4: Refresh automatique (attendre 15 min OU simuler)
- Temps = ? (doit être instant)
```

### Memory
```
Chrome DevTools → Memory
- Avant magazine: ? MB
- Après navigation 5 pages: ? MB
- Après 2-3 regénérations: ? MB

Cible: Pas de fuite > 50MB
```

### CPU
```
Pendant génération magazine:
- CPU utilisation: ?
- GPU utilisation: ?

Pendant navigation:
- CPU utilisation: ? (minimal)
```

---

## 6️⃣ Test Cas d'Erreur

### Euria Indisponible
```
1. Arrêtez le service Euria
2. Régénérez le magazine
3. Vérifiez:
   □ Les pages s'affichent quand même
   □ Haïkus par défaut affichés
   □ Pas d'erreur console
   □ Snackbar d'info utile
```

### Base de Données Vide
```
1. Supprimez les albums de test
2. Allez sur /magazine
3. Vérifiez:
   □ Pages "empty" graceful
   □ Pas de crash
   □ Message utilisateur clair
```

### Images Manquantes
```
1. Modifiez une image_url en NULL
2. Régénérez le magazine
3. Vérifiez:
   □ Page s'affiche quand même
   □ Pas d'image: acceptable
   □ Texte quand même lisible
```

### Connexion Internet Lente
```
1. DevTools → Network → Fast 3G
2. Régénérez le magazine
3. Vérifiez:
   □ Loader s'affiche
   □ Pas de timeout < 30s
   □ Peut annuler et remonter une erreur
```

---

## 7️⃣ Test Cross-Browser

```
Chrome       : ✓ Flex, Grid, CSS modern
Firefox      : ✓ Animations, transitions
Safari       : ✓ WebKit prefixes OK ?
Edge         : ✓ Chromium-based
```

---

## 8️⃣ Test Accessibilité

```
Keyboard Navigation:
□ Tab entre les éléments
□ Enter/Space sur les boutons
□ Espace sur "Nouvelle édition"

Screen Reader (NVDA/JAWS simulation):
□ Titres sont h1/h2 appropriés
□ Images ont alt text
□ Boutons ont description

Colors:
□ Texte blanc sur fond sombre = bon contraste
□ Pas uniquement couleur pour info (ex: "page active")
```

---

## 🔍 Debugging Checklist

Si quelque chose ne fonctionne pas :

### Frontend
```
□ Console browser: erreurs TypeScript ?
□ Network tab: API call réussie ? (200, <10s)
□ Application tab: state Redux OK ?
□ Performance tab: long tasks ?
□ Elements: CSS appliquée correctement ?
```

### Backend
```
□ Logs FastAPI: erreurs Euria ?
□ Circuit breaker: ouvert ? (check logs)
□ Database: albums > 0 ?
□ Response JSON: format valide ? (check Network)
```

### Euria
```
□ Bearer token valide dans secrets.json ?
□ URL Euria correcte ?
□ Requête arrive à Euria ? (check logs)
□ Réponse bien formée ?
```

---

## 📊 Test Coverage Matrix

| Feature | Desktop | Tablet | Mobile | Offline | Notes |
|---------|---------|--------|--------|---------|-------|
| Page affichage | ✅ | ✅ | ✅ | ❌ | Besoin internet |
| Navigation scroll | ✅ | ✅ | ✅ | ✅ | Local |
| Boutons nav | ✅ | ✅ | ✅ | ✅ | Local |
| Auto-refresh | ✅ | ✅ | ✅ | ✅ | Timer local |
| Minuteur | ✅ | ✅ | ✅ | ✅ | Local |
| Haïkus Euria | ✅ | ✅ | ✅ | ❌ | API |
| Images | ✅ | ✅ | ✅ | ❌ | Réseau |
| Animations | ✅ | ✅ | ⚠️ | ✅ | Mobile peut être ralenti |

---

## 🚀 Quick Test Commands

```bash
# Backend only
curl -X GET http://localhost:8000/api/v1/magazines/generate | jq .

# Check Euria connectivity
curl -X POST https://api.euria.infomaniak.com \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral3",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 50
  }'

# Monitor logs
# Backend:
tail -f backend/logs/app.log | grep -i magazine

# Frontend:
# DevTools → Console
```

---

## ✅ Sign-Off Checklist

Avant de déclarer "Magazine: DONE" :

- [ ] Tous les tests 1-4 passent
- [ ] Pas d'erreurs console ou backend
- [ ] Performance < 10s génération
- [ ] Responsive sur 3 breakpoints
- [ ] Haïkus générés par Euria ✓
- [ ] Navigation fluide
- [ ] Minuteur décrémente
- [ ] Régénération fonctionne
- [ ] Pas de fuite mémoire
- [ ] Documentation complète

---

**Amusez-vous bien avec votre Magazine ! 🎵📖**
