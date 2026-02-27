# Configuration de la Source d'Images Albums

**Version :** 4.7.5  
**Date :** 27 février 2026

---

## Description

AIME peut récupérer les images de couverture des albums depuis deux sources différentes :

| Source | Description |
|--------|-------------|
| **Spotify** (défaut) | Images depuis l'API Spotify (haute résolution, très couverture) |
| **Last.fm** | Images depuis l'API Last.fm (`album.getinfo`) |

Ce paramètre est global et s'applique à toutes les pages de l'application (Collection, Magazine, Journal, Collections).

---

## Accès dans l'Interface

**Settings → Section "Configuration des images"**

Un sélecteur (Spotify / Last.fm) permet de basculer entre les deux sources. Le changement est appliqué immédiatement et persisté.

---

## API

### Lire la configuration

```http
GET /api/v1/services/config/image-source
```

**Réponse :**
```json
{
  "image_album_source": "spotify"
}
```

### Modifier la configuration

```http
PATCH /api/v1/services/config/image-source
Content-Type: application/json

{
  "image_album_source": "lastfm"
}
```

**Valeurs acceptées :** `spotify`, `lastfm`  
**Réponse :** même structure que GET

---

## Persistance

La valeur est stockée dans `config/app.json` :

```json
{
  "image_album_source": "spotify"
}
```

Le fichier est lu au démarrage via `get_settings()` et écrit via `settings.save_app_config()`.

---

## Architecture

```
frontend/src/hooks/useImageSource.ts
  → GET  /api/v1/services/config/image-source
  → PATCH /api/v1/services/config/image-source

backend/app/api/v1/tracking/services.py
  → router GET  /config/image-source
  → router PATCH /config/image-source  (monté sous préfixe /services)

backend/app/core/config.py
  → get_settings() → settings.app_config["image_album_source"]
  → settings.save_app_config()

config/app.json
  → {"image_album_source": "spotify"}
```

---

## Hook Frontend — `useImageSource`

```ts
// frontend/src/hooks/useImageSource.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'

export function useImageSource() {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['imageSource'],
    queryFn: () => apiClient.get('/services/config/image-source').then(r => r.data),
  })

  const mutation = useMutation({
    mutationFn: (source: 'spotify' | 'lastfm') =>
      apiClient.patch('/services/config/image-source', { image_album_source: source }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['imageSource'] }),
  })

  return {
    source: query.data?.image_album_source as 'spotify' | 'lastfm' | undefined,
    isLoading: query.isLoading,
    error: query.error,
    setSource: mutation.mutate,
  }
}
```

---

## Notes

- Si la clé `image_album_source` est absente de `app.json`, la valeur par défaut est `"spotify"`.
- Le service Last.fm nécessite la variable d'environnement `LASTFM_API_KEY` pour fonctionner.
- L'endpoint PATCH retourne HTTP 400 si une valeur autre que `spotify` ou `lastfm` est envoyée.
