# Bugfixes & Améliorations - v4.7.5

**Date :** 27 février 2026  
**Version :** 4.7.5  
**Type :** Bugfixes critiques + nouvelles fonctionnalités

---

## 📋 Résumé

Cette version corrige plusieurs bugs critiques affectant la page Settings, la page Magazine, et la gestion des images depuis Last.fm. Elle introduit également un nouveau service de sélection de source d'images (Spotify vs Last.fm) et ajoute la colonne `lastfm_url` au modèle `Album`.

---

## 🐛 Bugs Corrigés

### 1. Settings.tsx — Crash « return outside of function »

**Problème :** La page Settings crashait au démarrage avec une erreur de compilation React :  
`Hooks can only be called inside of the body of a function component`

**Cause :** L'accolade ouvrant la fonction `Settings()` était absente ; tous les hooks (`useImageSource`, `useQuery`, `useMutation`, `useState`) et la structure JSX se trouvaient en dehors d'un composant React valide.

**Correction :**
- Ajout de `function Settings() {` avant les hooks
- Ajout de `export default Settings` en fin de fichier

**Fichier :** `frontend/src/pages/Settings.tsx`

---

### 2. Settings — « Erreur lors du chargement de la source d'images »

**Problème :** La page Settings affichait systématiquement une erreur au chargement de la configuration de la source d'images.

**Cause :** L'URL appelée dans le hook était `/config/image-source` au lieu de `/services/config/image-source`. De plus, dans `services.py`, les endpoints `GET /config/image-source` et `PATCH /config/image-source` étaient déclarés **avant** `router = APIRouter()`, les rendant inopérants.

**Corrections :**
- `frontend/src/hooks/useImageSource.ts` : URLs corrigées vers `/services/config/image-source`
- `backend/app/api/v1/tracking/services.py` : Endpoints déplacés après `router = APIRouter()`, imports corrigés (ajout de `Body`)

---

### 3. Magazine — « Erreur lors de la génération du magazine (données invalides) »

**Problème :** La page Magazine affichait une erreur « données invalides » et le contenu ne s'affichait pas.

**Cause 1 — Double préfixe URL :** Le frontend appelait `/api/v1/magazines/…` alors que `apiClient` a déjà `/api/v1` comme base URL, produisant des URLs en `/api/v1/api/v1/magazines/…`.

**Cause 2 — Champ `total_pages` absent :** L'API backend renvoyait `total_pages: null`. Le frontend validait `typeof magazine.total_pages !== 'number'`, ce qui rejetait la réponse comme invalide.

**Corrections :**
- `frontend/src/pages/Magazine.tsx` : 5 URLs `/api/v1/magazines/…` → `/magazines/…`
- `frontend/src/pages/Magazine.tsx` : Normalisation de `total_pages` dans `queryFn` :
  ```ts
  data.total_pages = data.total_pages ?? (Array.isArray(data.pages) ? data.pages.length : 0)
  ```
- Validation assouplie : vérification `magazine.pages.length === 0` plutôt que `typeof total_pages`

---

## ✨ Nouvelles Fonctionnalités

### 4. Sélection de la source d'images (Spotify vs Last.fm)

**Description :** Ajout d'un paramètre configurable permettant de choisir la source d'images pour les albums : **Spotify** ou **Last.fm**.

**Composants :**
- **Nouveau hook** `frontend/src/hooks/useImageSource.ts` — GET/PATCH de la configuration
- **Nouveaux endpoints API** :
  - `GET /api/v1/services/config/image-source` → retourne `{"image_album_source": "spotify"|"lastfm"}`
  - `PATCH /api/v1/services/config/image-source` → met à jour la source, valeurs acceptées : `spotify`, `lastfm`
- **Config persistée** dans `config/app.json` via `settings.app_config`
- **UI dans Settings** : sélecteur affiché dans la section « Configuration des images »

**Modèles Pydantic :**
```python
class ImageSourceResponse(BaseModel):
    image_album_source: str

class ImageSourceUpdateRequest(BaseModel):
    image_album_source: str  # "spotify" ou "lastfm"
```

---

### 5. Nouveau service Last.fm pour les images — `LastFMImageService`

**Fichier :** `backend/app/services/lastfm_image_service.py`

**Description :** Nouveau service asynchrone pour récupérer images et URLs Albums/Artistes depuis l'API Last.fm.

**Méthodes :**
- `get_album_image(artist_name, album_title)` — URL de la meilleure image d'album disponible
- `get_artist_image(artist_name)` — URL de l'image d'artiste
- `get_album_lastfm_url(artist_name, album_title)` — URL de la page album sur Last.fm

**Utilisation :**
```python
from app.services.lastfm_image_service import LastFMImageService
svc = LastFMImageService()
url = await svc.get_album_image("Pink Floyd", "The Wall")
```

---

### 6. Colonne `lastfm_url` sur la table `albums`

**Description :** Ajout de la colonne `lastfm_url` (VARCHAR 500, nullable) sur le modèle `Album` pour stocker le lien direct vers la page Last.fm de l'album.

**Migration Alembic :** `0802cd4cd3b7_ajout_champ_lastfm_url_sur_album.py`

**Utilisation dans les exports Markdown :**
```python
# markdown_export_service.py
elif getattr(album, 'lastfm_url', None):
    links.append(f"[Ouvrir sur Last.fm]({album.lastfm_url})")
```

---

## 🗄️ Base de Données

| Changement | Table | Colonne | Type |
|------------|-------|---------|------|
| Ajout | `albums` | `lastfm_url` | `VARCHAR(500)` nullable |

> **Note de restauration :** Si vous restaurez une sauvegarde antérieure à ce patch, la colonne `lastfm_url` sera absente. Exécutez la migration ou ajoutez-la manuellement :
> ```sql
> ALTER TABLE albums ADD COLUMN lastfm_url VARCHAR(500);
> ```

---

## 📁 Fichiers Modifiés

| Fichier | Type | Description |
|---------|------|-------------|
| `frontend/src/pages/Settings.tsx` | Correction | Composant React manquant |
| `frontend/src/pages/Magazine.tsx` | Correction | URLs + normalisation total_pages |
| `frontend/src/hooks/useImageSource.ts` | Nouveau | Hook GET/PATCH image source |
| `backend/app/api/v1/tracking/services.py` | Correction | Endpoints image-source repositionnés |
| `backend/app/models/album.py` | Amélioration | Colonne lastfm_url |
| `backend/app/services/lastfm_image_service.py` | Nouveau | Service images Last.fm |
| `backend/app/services/markdown_export_service.py` | Amélioration | Lien Last.fm dans exports |
| `backend/alembic/versions/0802cd4cd3b7_…py` | Migration | Ajout lastfm_url sur albums |

---

## ✅ Tests de Validation

```bash
# Vérifier les endpoints image-source
curl http://localhost:8000/api/v1/services/config/image-source
# Attendu : {"image_album_source":"spotify"}

curl -X PATCH http://localhost:8000/api/v1/services/config/image-source \
  -H "Content-Type: application/json" \
  -d '{"image_album_source":"lastfm"}'
# Attendu : {"image_album_source":"lastfm"}

# Vérifier l'API Collection (schéma OK)
curl "http://localhost:8000/api/v1/collection/albums?page=1&page_size=1"
# Attendu : {"items":[...],"total":N,...}
```
