# 🎉 CHANGELOG v4.7.0 - "Apple Music Integration"

**Date de Sortie:** 14 février 2026  
**Version Précédente:** 4.6.3  
**Prochaine Version:** 4.8.0

---

## 🎯 Vue d'ensemble

Intégration complète d'Apple Music à côté de Spotify pour offrir une expérience multi-plateforme cohérente de lecture musicale.

---

## ✨ Nouvelles Fonctionnalités

### 1. 🎵 Boutons Apple Music sur toutes les pages d'albums

#### Implémentation
- **Pages concernées :**
  - 📱 **Magazine** : 5 types de pages (artist_showcase, album_detail, albums_haikus, timeline_stats, playlist_theme)
  - 📚 **Collection** : Vue grille + vue détail modal
  - 📖 **Journal** : Historique d'écoute avec timeline
  - 📚 **Collections** : Vue grille + vue détail modal

#### Fonctionnalités
- ✅ Lien direct vers Apple Music (si URL disponible via Euria)
- ✅ Fallback recherche Apple Music (titre + artiste)
- ✅ Fermeture automatique de la fenêtre vide après 1 seconde
- ✅ Styled avec couleur Apple (#FA243C)
- ✅ Comportement cohérent avec les autres services (Spotify, Roon)

### 2. 🗄️ Nouvelle colonne base de données

#### Modification du schéma
```sql
ALTER TABLE albums ADD COLUMN apple_music_url VARCHAR(500) NULL;
CREATE INDEX idx_albums_apple_music_url ON albums(apple_music_url);
```

#### Détails
- **Colonne** : `apple_music_url`
- **Type** : VARCHAR(500), nullable
- **Index** : Créé pour optimiser les requêtes
- **Migration** : Script Python direct (Alembic non configuré en standard)
- **Status** : ✅ Exécutée avec succès le 14 février 2026

### 3. 🔌 Intégration Backend

#### Model (Album)
```python
# backend/app/models/album.py
apple_music_url = Column(String(500), nullable=True)
```

#### Service (Magazine Generator)
- Ajout de `apple_music_url` à 5 pages de magazine
- Propagation du champ depuis la BD vers l'API
- Format JSON cohérent avec autres services

#### Routes API
- `GET /api/v1/magazines/{id}` : Retourne `apple_music_url` pour tous les albums
- `GET /api/v1/albums` : Inclut `apple_music_url` dans les réponses

---

## 🔧 Développement Technique

### Frontend (React/TypeScript)

#### Handler `handleOpenAppleMusic`
```typescript
const handleOpenAppleMusic = (
  event: React.MouseEvent,
  albumTitle?: string,
  artistName?: string,
  appleMusicUrl?: string | null
) => {
  event.stopPropagation()
  
  // Option 1 : Lien direct depuis Euria
  if (appleMusicUrl) {
    const w = window.open(appleMusicUrl, '_blank')
    if (w) setTimeout(() => w.close(), 1000)
    return
  }
  
  // Option 2 : Recherche par titre + artiste
  if (!albumTitle || !artistName) return
  const searchQuery = `${albumTitle} ${artistName}`.trim()
  const encodedQuery = encodeURIComponent(searchQuery)
  const appleMusicSearchUrl = `https://music.apple.com/search?term=${encodedQuery}`
  const w = window.open(appleMusicSearchUrl, '_blank')
  if (w) setTimeout(() => w.close(), 1000)
}
```

#### Style Button
```tsx
<Button
  sx={{
    color: '#FA243C',
    '&:hover': {
      backgroundColor: '#FA243C',
      color: 'white'
    }
  }}
>
  Apple
</Button>
```

### Fichiers Modifiés

| Fichier | Changement |
|---------|-----------|
| `frontend/src/components/MagazinePage.tsx` | Ajout handler + boutons 5 pages |
| `frontend/src/pages/Collection.tsx` | Ajout handler + boutons 2 locations |
| `frontend/src/pages/Journal.tsx` | Ajout handler + boutons |
| `frontend/src/pages/Collections.tsx` | Ajout interface field, handlers + boutons |
| `backend/app/models/album.py` | Colonne + index |
| `backend/app/services/magazine_generator_service.py` | Propagation URL x5 pages |
| `backend/alembic/versions/007_add_apple_music_url.py` | Migration Alembic |
| `backend/migrate_add_apple_music_url.py` | Migration directe SQLite |

---

## 📊 Architecture

### Flux d'Intégration

```
[Euria API] → Génère apple_music_url
      ↓
[Magazine Service] → Inclut dans réponse JSON
      ↓
[Frontend API Call] → Reçoit données avec apple_music_url
      ↓
[Album Components] → Affichent bouton Apple
      ↓
[User Click] → window.open(url) ou recherche Apple
      ↓
[Apple Music App] → Ouvre album / affiche résultats
```

### Format d'URL

#### URL Directe (via Euria)
```
https://music.apple.com/[locale]/album/[slug]/[id]
Exemple: https://music.apple.com/fr/album/thriller/123456
```

#### URL Recherche (fallback)
```
https://music.apple.com/search?term=[album]+[artist]
Exemple: https://music.apple.com/search?term=Thriller+Michael+Jackson
```

---

## 🎨 UI/UX

### Styling
- **Couleur** : #FA243C (Apple Red)
- **Hover State** : Arrière-plan rouge + texte blanc
- **Position** : À côté du bouton Spotify
- **Taille** : Cohérente avec autres boutons (size="small")
- **Label** : "Apple" ou "Ouvrir sur Apple Music" (tooltip)

### Comportement
1. Utilisateur clique sur "Apple"
2. Fenêtre s'ouvre avec l'album Apple Music
3. La fenêtre vide se ferme automatiquement après 1 sec
4. Utilisateur reste sur l'application AIME
5. Apple Music affiche l'album détecté

---

## 🚀 Utilisation

### Cas d'Utilisation 1 : Via Magazine
```
1. Ouvrir Magazine
2. Voir album avec boutons Spotify + Apple
3. Cliquer "Apple" → Ouvre album dans Apple Music app
```

### Cas d'Utilisation 2 : Via Collection
```
1. Ouvrir Collection (Discogs)
2. Survoler album
3. Cliquer "Apple" → Ouvre dans Apple Music
```

### Cas d'Utilisation 3 : Via Journal
```
1. Ouvrir Journal (historique écoute)
2. Voir track écouté
3. Cliquer "Apple" → Cherche et affiche dans Apple Music
```

---

## 🔄 Intégration Euria (Futur)

### Structure Prévue
```json
{
  "album_id": 12345,
  "title": "Thriller",
  "artist": "Michael Jackson",
  "spotify_url": "https://open.spotify.com/album/...",
  "apple_music_url": "https://music.apple.com/fr/album/thriller/123456"
}
```

### Avantages
- URL directe plus rapide que recherche
- Pas de latence de recherche
- UX optimisée pour lecteurs Apple Music
- Infrastructure prête pour population future

---

## ✅ Tests

### Test Manuel
```bash
# 1. Magazine page
http://localhost:5173/magazine
→ Cliquer bouton Apple sur albums
→ Doit ouvrir album dans Apple Music

# 2. Collection page
http://localhost:5173/collection
→ Survoler album
→ Cliquer Apple
→ Doit ouvrir dans Apple Music

# 3. Journal page
http://localhost:5173/journal
→ Voir historique d'écoute
→ Cliquer Apple sur track
→ Doit ouvrir recherche Apple Music
```

### Validation Base de Données
```bash
# Vérifier colonne ajoutée
sqlite3 data/musique.db "PRAGMA table_info(albums);"
→ apple_music_url colonne visible

# Vérifier index
sqlite3 data/musique.db ".indices albums"
→ idx_albums_apple_music_url présent
```

---

## 📈 Impact

### Performance
- ✅ Index sur apple_music_url optimise requêtes
- ✅ Champ nullable = pas d'impact si vide
- ✅ Fallback recherche très rapide (pas d'API call)

### UX
- ✅ Multi-service cohérent (Spotify + Apple)
- ✅ Fermeture auto fenêtre = expérience fluide
- ✅ Compatible avec écosystème Apple
- ✅ Reduce friction pour utilisateurs Apple

### Maintenabilité
- ✅ Code centralisé par handler
- ✅ Patterns cohérents avec Spotify
- ✅ Documentation complète
- ✅ Extensible pour services futurs

---

## 🔮 Évolutions Futures

### Phase 2 : Population Euria
- Euria génère apple_music_url pour albums
- Croissant coverage over time
- Utilisateurs bénéficient d'URLs directes

### Phase 3 : Autres Services
- YouTube Music
- Tidal
- Amazon Music
- Same pattern pour chaque service

### Phase 4 : Smart Service Selection
- Détecter service préféré utilisateur
- Highlighter le bouton préféré
- Deep linking depuis partage

---

## 📝 Notes

### Limitations Actuelles
- apple_music_url populée seulement par Euria (en attente)
- Fallback recherche fonctionne mais moins direct
- Pas de détection locale Apple Music vs web

### Considérations Future
- Monitoring usage (quel % clique Apple vs Spotify)
- AB testing UI/UX placement
- Support pour Apple Music Family Share
- Integration avec Siri Shortcuts

---

## ✨ Version History

| Version | Date | Changement |
|---------|------|-----------|
| 4.7.0 | 14 fév 2026 | 🎉 Apple Music integration initiale |
| 4.6.3 | 9 fév 2026 | Documentation consistency |
| 4.6.0 | 8 fév 2026 | Magazine page release |
