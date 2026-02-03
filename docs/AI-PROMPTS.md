# 🤖 Catalogue des Prompts IA - AIME

**Date:** 3 février 2026  
**Version:** 4.3.1  
**Service IA:** EurIA (Infomaniak AI) - Modèle Mistral3

---

## 📋 Vue d'ensemble

Ce document recense tous les prompts utilisés pour communiquer avec l'IA EurIA dans l'application AIME - AI Music Enabler. L'IA est utilisée pour générer des descriptions d'albums, des haïkus, et enrichir automatiquement le contenu.

**Configuration:**
- **API:** Infomaniak AI (EurIA)
- **Modèle:** mistral3
- **Température:** 0.7
- **Timeout:** 45 secondes
- **Retry:** 3 tentatives avec backoff exponentiel
- **Circuit Breaker:** Activé (5 échecs → pause 5min)

---

## 🎵 Prompts de Description d'Albums

### 1. Description Longue (2000 caractères)

**Fichier:** `backend/app/services/ai_service.py` → `generate_album_info()`

**Contexte d'utilisation:**
- Import de nouveaux albums (Last.fm, Roon, Discogs)
- Enrichissement automatique de la collection
- Tâche scheduler d'optimisation quotidienne

**Prompt:**
```
Tu es un expert musical. Décris l'album "{album_title}" de {artist_name}.

IMPORTANT : Ta réponse doit faire EXACTEMENT entre 1800 et 2000 caractères. Ne dépasse JAMAIS 2000 caractères. Termine proprement tes phrases, ne t'arrête pas au milieu d'une phrase.

Inclus dans ta description :
- Le contexte historique et culturel de l'album
- Le style musical et les influences
- Les thèmes principaux et l'atmosphère
- L'impact culturel et la réception
- Les morceaux marquants si pertinent
- L'héritage et l'influence sur la musique

Sois factuel, précis et captivant. Structure ton texte en paragraphes courts.
```

**Paramètres:**
- `max_tokens`: 750
- Variables: `{album_title}`, `{artist_name}`

**Post-traitement:**
- Troncature de sécurité à 2000 caractères
- Conservation de la dernière phrase complète
- Fallback: `null` si erreur

**Exemple de sortie:**
```
Pastel Blues est le sixième album studio de Nina Simone, sorti en 1965. Cet album marque un tournant dans la carrière de l'artiste, avec des morceaux puissants et engagés. Le contexte de l'époque, marqué par la lutte pour les droits civiques aux États-Unis, transparaît dans chaque note...
```

---

### 2. Description Courte (35 mots - Haïku Scheduler)

**Fichier:** `backend/app/services/scheduler_service.py` → `_generate_random_haikus()`

**Contexte d'utilisation:**
- Génération quotidienne de haïkus à 6h00
- Export vers `data/scheduled-output/generate-haiku-YYYYMMDD-HHMMSS.md`
- Utilisé pour présentation iA Presenter

**Prompt:**
```
Présente moi l'album {album_lower} de {artist_lower}. 
N'ajoute pas de questions ou de commentaires. 
Limite ta réponse à 35 mots maximum.
Réponds uniquement en français.
```

**Paramètres:**
- `max_tokens`: 100
- Variables: `{album_lower}` (titre en minuscules), `{artist_lower}` (artiste en minuscules)

**Fallback:**
```
Album {album.title} sorti en {album.year}. Œuvre musicale enrichissante, à découvrir absolument.
```

**Exemple de sortie:**
```
Pastel Blues de Nina Simone est un chef-d'œuvre de 1965. Blues et jazz s'entrelacent pour créer une œuvre puissante, portée par la voix inimitable de l'artiste.
```

---

## 🎋 Prompts de Haïkus

### 1. Haïku Global (Scheduler)

**Fichier:** `backend/app/services/scheduler_service.py` → `_generate_random_haikus()`

**Contexte d'utilisation:**
- Haïku d'introduction pour la présentation quotidienne
- Généré une fois par jour à 6h00

**Prompt:**
```
Génère un haïku court sur la musique et les albums. Réponds uniquement avec le haïku en 3 lignes, sans numérotation.
```

**Paramètres:**
- `max_tokens`: 100
- Format attendu: 3 lignes (structure 5-7-5 syllabes implicite)

**Fallback:**
```
Musique qui danse,
albums en harmonie,
cœur qui s'envole.
```

**Exemple de sortie:**
```
Notes en dansant,
vinyles qui tournent lentement,
âme en liberté.
```

---

### 2. Haïku Contextuel (API)

**Fichier:** `backend/app/services/ai_service.py` → `generate_haiku()`

**Contexte d'utilisation:**
- API endpoint `/history/haiku`
- Génération de haïku basée sur les statistiques d'écoute

**Prompt:**
```
Tu es un poète spécialisé en haïkus. Crée un haïku qui capture l'essence des écoutes musicales suivantes:

Artistes principaux: {top_artists}
Albums principaux: {top_albums}
Nombre total d'écoutes: {total_tracks}

Le haïku doit respecter la structure 5-7-5 syllabes et capturer l'ambiance musicale.
```

**Paramètres:**
- `max_tokens`: 100
- Variables: 
  - `{top_artists}`: Liste des 5 artistes les plus écoutés (séparés par virgule)
  - `{top_albums}`: Liste des 5 albums les plus écoutés (séparés par virgule)
  - `{total_tracks}`: Nombre total de pistes écoutées

**Fallback:**
```
Musique écoute / Notes qui dansent dans le temps / L'âme en harmonie
```

**Exemple de sortie:**
```
Nina résonne,
Pastel Blues en boucle,
jazz dans les veines.
```

---

## 🎶 Prompts de Playlists (Désactivé)

### Génération de Playlist par Prompt IA

**Fichier:** `backend/app/services/ai_service.py` → `generate_playlist_by_prompt()`

**Statut:** ⚠️ Temporairement désactivé (fonctionnalité playlists en migration)

**Contexte d'utilisation:**
- Génération de playlist basée sur un prompt utilisateur libre
- Endpoint `/playlists/generate` avec `algorithm=ai_generated`

**Prompt:**
```
Tu es un DJ expert. Sélectionne les meilleurs tracks pour créer une playlist correspondant à: "{user_prompt}"

Tracks disponibles:
{tracks_list}

Réponds uniquement avec les IDs des tracks séparés par des virgules (ex: 1,5,12,3). Sélectionne entre 20 et 30 tracks.
```

**Paramètres:**
- `max_tokens`: 200
- Variables:
  - `{user_prompt}`: Prompt libre de l'utilisateur (ex: "musique énergique pour le matin")
  - `{tracks_list}`: Liste des 100 premiers tracks disponibles (format: `id: artiste - titre (album)`)

**Post-traitement:**
- Parsing des IDs séparés par virgules
- Validation que les IDs existent dans la liste disponible
- Fallback: Top 25 tracks si parsing échoue

**Exemple de sortie:**
```
1,5,12,3,8,15,23,27,34,41,45,52,58,63,67,72,79,84,88,91,95,102,108,115,120
```

---

## 🔧 Gestion des Erreurs et Fallbacks

### Circuit Breaker

L'application utilise un **Circuit Breaker** pour protéger contre les défaillances du service IA:

**Configuration:**
- **Seuil d'échec:** 5 erreurs consécutives
- **Seuil de succès:** 3 succès pour réouverture
- **Timeout:** 60 secondes
- **Période de récupération:** 300 secondes (5 minutes)

**États:**
- **CLOSED**: Service normal
- **OPEN**: Service désactivé temporairement (utilise fallbacks)
- **HALF_OPEN**: Test de récupération

### Retry Logic

**Stratégie:** Backoff exponentiel
- **Tentatives max:** 3
- **Délai initial:** 2 secondes
- **Délai max:** 15 secondes

**Erreurs réessayées:**
- `httpx.TimeoutException` (timeout 45s)
- `httpx.HTTPError` (erreurs serveur 5xx)
- `httpx.ConnectError` (erreurs de connexion)

**Erreurs non réessayées:**
- HTTP 4xx (erreurs client)
- Retour: `default_error_message` = "Aucune information disponible"

### Messages de Fallback

| Contexte | Fallback |
|----------|----------|
| **Description album longue** | `null` (pas de métadonnée créée) |
| **Description album courte** | `"Album {titre} sorti en {année}. Œuvre musicale enrichissante, à découvrir absolument."` |
| **Haïku global** | `"Musique qui danse, / albums en harmonie, / cœur qui s'envole."` |
| **Haïku contextuel** | `"Musique écoute / Notes qui dansent dans le temps / L'âme en harmonie"` |
| **Playlist IA** | Top 25 tracks de la liste disponible |

---

## 📊 Statistiques et Monitoring

### Logs

Les appels IA génèrent des logs structurés:

**Succès:**
```
✅ Succès génération info album: {artist} - {album}
```

**Erreurs:**
```
❌ EurIA API Error {status_code}: {error_text}
⏱️ Timeout EurIA: {exception}
🔗 Erreur connexion EurIA: {exception}
⚠️ Circuit breaker EurIA ouvert - service indisponible temporairement
```

### Métriques

- **Nombre d'appels:** Tracked par le retry decorator
- **Taux de succès:** Monitored par le circuit breaker
- **Temps de réponse:** Timeout fixé à 45s
- **Coût tokens:** ~750 tokens/appel pour descriptions longues

---

## 🔐 Configuration

**Fichier:** `config/app.json`

```json
{
  "euria": {
    "url": "https://api.infomaniak.com/2/ai/106561/openai/v1/chat/completions",
    "bearer": "xAw7abygtFt9iB0cOJANoFPpkjPwjtSwTycaS_AGBd9sQedV11GH1ejHfYzL8zz3nWNNIL15pv18nkf2",
    "max_attempts": 5,
    "default_error_message": "Aucune information disponible"
  }
}
```

**Variables d'environnement:**
- Aucune (configuration centralisée dans `app.json`)

---

## 🎯 Bonnes Pratiques

### 1. Limites de Caractères

**Toujours spécifier une limite:**
```
IMPORTANT : Ta réponse doit faire EXACTEMENT entre 1800 et 2000 caractères.
```

**Raison:** Le modèle Mistral3 peut générer des réponses très longues si non contraint.

### 2. Format de Sortie

**Être explicite sur le format attendu:**
```
Réponds uniquement avec le haïku en 3 lignes, sans numérotation.
```

**Raison:** Évite les préambules, explications ou formatage indésirable.

### 3. Langue

**Spécifier la langue:**
```
Réponds uniquement en français.
```

**Raison:** Le modèle peut mélanger les langues selon le contexte.

### 4. Contexte Minimal

**Fournir juste les informations nécessaires:**
- Pas de contexte superflu
- Variables interpolées claires
- Instructions concises

**Raison:** Réduit le coût en tokens et améliore la cohérence.

### 5. Validation Post-IA

**Toujours valider la sortie:**
- Vérifier la longueur
- Parser et valider le format
- Avoir un fallback prêt

**Raison:** L'IA peut produire des sorties inattendues.

---

## 🔄 Cas d'Usage par Service

### TrackerService (Last.fm)
- **Prompt:** Description album longue
- **Fréquence:** À chaque nouveau track détecté
- **Asynchrone:** Oui (ne bloque pas le tracking)

### RoonTrackerService
- **Prompt:** Description album longue
- **Fréquence:** À chaque nouvel album Roon
- **Asynchrone:** Oui

### SchedulerService
- **Prompts:** 
  1. Haïku global (1x/jour)
  2. Description courte (5x/jour pour haïku albums)
  3. Description longue (enrichissement quotidien)
- **Fréquence:** Cron programmé
- **Asynchrone:** Oui

### API Endpoints
- **`/history/haiku`:** Haïku contextuel
- **`/services/ai/generate-info`:** Description album longue (manuel)
- **`/playlists/generate`:** Playlist IA (désactivé)

---

## 📝 Historique des Modifications

| Date | Version | Modification |
|------|---------|--------------|
| 2026-02-03 | 4.3.1 | Documentation initiale des prompts |
| 2026-02-01 | 4.3.0 | Ajout haïku scheduler quotidien |
| 2026-01-30 | 4.0.0 | Circuit breaker et retry logic |
| 2026-01-15 | 3.5.0 | Première version avec EurIA |

---

## 🚀 Évolutions Futures

**Prompts à développer:**
- [ ] Génération de tags/genres par IA
- [ ] Recommandations personnalisées par prompt
- [ ] Analyse de mood/ambiance d'album
- [ ] Génération de descriptions multilangues
- [ ] Résumés de sessions d'écoute

**Optimisations:**
- [ ] Cache des réponses IA (éviter les appels répétés)
- [ ] Fine-tuning du modèle avec données musicales
- [ ] Batch processing pour les enrichissements massifs
- [ ] A/B testing sur différents templates de prompts

---

**Maintenu par:** Équipe AIME  
**Contact:** Via GitHub Issues  
**Dernière mise à jour:** 3 février 2026
