# 🤖 Documentation Complète - Prompts Euria v4.7.0

**Mise à jour:** 14 février 2026  
**Version:** 4.7.0 (Apple Music Integration)  
**Dernière révision:** Intégration Apple Music + Documentation API complète

---

## 📚 Table des Matières

1. [API Euria - Méthode d'Appel](#api-euria)
2. [Prompts Haïkus](#haikus)
3. [Prompts Descriptions](#descriptions)
4. [Prompts Apple Music (v4.7.0)](#apple-music)
5. [Prompts Layouts](#layouts)
6. [Prompts Playlists](#playlists)
7. [Prompts Poésie](#poesie)
8. [Testing Checklist](#testing)

---

## 🔌 API Euria - Méthode d'Appel {#api-euria}

### Configuration

L'API Euria est fournie par **Infomaniak** avec OpenAI compatible endpoint.

#### Variables d'environnement requises
```env
# .env à la racine du projet
EURIA_API_URL=https://api.infomaniak.com/2/ai/[MODEL_ID]/openai/v1/chat/completions
EURIA_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxx
EURIA_MODEL=gpt-4o  # ou autres modèles disponibles
```

### Méthode d'Appel - cURL

```bash
curl -X POST \
  https://api.infomaniak.com/2/ai/[MODEL_ID]/openai/v1/chat/completions \
  -H "Authorization: Bearer [YOUR_API_KEY]" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "system",
        "content": "Tu es un expert en musique et poésie."
      },
      {
        "role": "user",
        "content": "Crée un haïku (5-7-5 syllabes) sur l'album \"Purple\" de Deep Purple."
      }
    ],
    "max_tokens": 150,
    "temperature": 0.7,
    "top_p": 0.9
  }'
```

### Méthode d'Appel - Python (Backend)

#### Installation
```bash
pip install openai
```

#### Code Backend
```python
import os
from openai import OpenAI

# Configuration
client = OpenAI(
    api_key=os.getenv("EURIA_API_KEY"),
    base_url="https://api.infomaniak.com/2/ai/[MODEL_ID]/openai/v1"
)

async def call_euria(prompt: str, system_prompt: str = None, max_tokens: int = 500) -> str:
    """
    Appel à l'API Euria
    
    Args:
        prompt: Le prompt utilisateur
        system_prompt: Instructions système (optionnel)
        max_tokens: Limite de tokens (défaut: 500)
    
    Returns:
        Texte généré par Euria
    """
    messages = []
    
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("EURIA_MODEL", "gpt-4o"),
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Erreur Euria: {e}")
        return None
```

### Méthode d'Appel - Frontend (JavaScript/TypeScript)

```typescript
async function callEuria(
  prompt: string,
  systemPrompt?: string,
  maxTokens: number = 500
): Promise<string> {
  try {
    const response = await fetch('/api/v1/ai/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TOKEN}` // Token depuis backend
      },
      body: JSON.stringify({
        prompt,
        system_prompt: systemPrompt,
        max_tokens: maxTokens
      })
    })
    
    if (!response.ok) {
      throw new Error(`Euria API error: ${response.status}`)
    }
    
    const data = await response.json()
    return data.result
  } catch (error) {
    console.error('Erreur appel Euria:', error)
    return null
  }
}
```

### Paramètres Recommandés

| Paramètre | Valeur | Usage |
|-----------|--------|-------|
| `model` | `gpt-4o` | Tous les prompts |
| `temperature` | `0.7` | Créativité modérée |
| `top_p` | `0.9` | Diversité élevée |
| `max_tokens` | `150-500` | Selon type (voir ci-dessous) |
| `frequency_penalty` | `0.2` | Réduire répétitions |
| `presence_penalty` | `0.1` | Diversité légère |

---

## 🧪 Prompts d'Éxécution pour Tester Euria

### 📋 Comment Utiliser

Ces prompts sont prêts à être envoyés à l'API Euria. Adaptez-les selon vos besoins !

---

## 1️⃣ Haïkus Basiques {#haikus}

### Simple Haïku Album
```
Crée un haïku (5-7-5 syllabes) qui capture l'essence de l'album "Purple" de Deep Purple (1972). 
Soit poétique et spécifique à cet album. 
Réponds uniquement avec les 3 lignes, sans numérotation ni explication.
```

**Réponse attendue** :
```
Pourpre électrique
Riffs résonnent éternels
Rêves enflammés
```

---

### Haïku Artiste
```
Tu es un poète musical. Crée un haïku (5-7-5) qui résume l'essence musicale de Pink Floyd.
Captures: expérimentation, philosophie, majesté sonore.
Réponds uniquement avec 3 lignes.
```

---

### Série de Haïkus
```
Crée 3 haïkus distincts (5-7-5 chacun) pour ces albums:
1. Thriller - Michael Jackson
2. Abbey Road - The Beatles
3. Nevermind - Nirvana

Chaque haïku doit être unique et spécifique à l'atmosphère de l'album.
Format: Chaque haïku séparé par une ligne vide.
Réponds uniquement avec les haïkus.
```

---

## 2️⃣ Descriptions Créatives

### Présentation d'Album
```
Écris une présentation accrocheur (80-100 mots) de l'album "Hotel California" 
des Eagles. Sois storyteller. Inclus:
- Ambiance générale
- Impact culturel (le succès massif, les critiques, l'influence)
- Pourquoi ça reste pertinent aujourd'hui

Sois captivant et musicalement informé.
```

---

### Contexte Historique
```
Fournis le contexte musical et culturel de l'album "Rumours" de Fleetwood Mac (1977). 
50-80 mots. Explique:
- Quelle était la scène musicale à cette époque ?
- Quels étaient les tensions internes ?
- Quel impact a eu la musique des Fleetwood Mac sur les années 70 ?

Sois précis mais aussi poétique.
```

---

### Légende Poétique (Caption)
```
Écris une légende poétique courte (15-25 mots) pour la couverture de l'album 
"The Wall" de Pink Floyd. Soit évocatrice et mélancolique.
Pas de ponctuation finale.

Réponds uniquement avec la légende.
```

---

## 2️⃣🍎 Apple Music Integration (v4.7.0) {#apple-music}

### Vue d'ensemble

Cette section documente les prompts utilisés pour générer des **URLs Apple Music valides** et des **descriptions intégrées Apple Music** pour améliorer l'expérience utilisateur multi-plateforme.

**Fonctionnalité v4.7.0 :** Ajout de boutons Apple Music sur tous les albums avec lien direct + recherche intelligente.

### Prompt: Générer Slug Apple Music

**Objectif:** Créer un slug ASCII-compatible pour URL Apple Music directe

```
Tu es un expert en normalisation d'URL Apple Music. 
Génère un slug valide pour cet album:
- Titre: {album_title}
- Artiste: {artist_name}

Le slug doit:
1. Être en minuscules
2. Remplacer espaces par des tirets
3. Supprimer caractères spéciaux (garder alphanumériques et tirets)
4. Être court (20-40 caractères idéalement)
5. Rester lisible et représentatif de l'album

Exemple: "thriller-michael-jackson"

Réponds uniquement avec le slug, sans guillemets ni explications.
```

**Paramètres API :**
- `max_tokens`: 50
- `temperature`: 0.3 (faible créativité)
- `top_p`: 0.5

**Utilisation Backend:**
```python
async def generate_apple_music_slug(album_title: str, artist_name: str) -> str:
    prompt = f"""Tu es un expert en normalisation d'URL Apple Music. 
Génère un slug valide pour cet album:
- Titre: {album_title}
- Artiste: {artist_name}

Le slug doit:
1. Être en minuscules
2. Remplacer espaces par des tirets
3. Supprimer caractères spéciaux (garder alphanumériques et tirets)
4. Être court (20-40 caractères idéalement)
5. Rester lisible et représentatif de l'album

Exemple: "thriller-michael-jackson"

Réponds uniquement avec le slug, sans guillemets ni explications."""
    
    slug = await call_euria(
        prompt=prompt,
        max_tokens=50,
        temperature=0.3
    )
    return slug.strip()
```

### Prompt: Amélioration Description pour Apple Music

**Objectif:** Enrichir descriptif album pour affichage Apple Music

```
Améliore cette description d'album pour Apple Music (80-120 mots):
Album: {album_title}
Artiste: {artist_name}
Année: {year}
Genre: {genre}

Description actuelle:
"{current_description}"

Améliorations requises:
- Ajouter contexte Apple ecosystem si pertinent
- Inclure compatibilité Lossless/Spatial Audio si applicable
- Format attractif pour mobile et desktop
- Inclure 1 phrase sur "Pourquoi l'écouter sur Apple Music"

Réponds uniquement avec la description améliorée.
```

**Paramètres API :**
- `max_tokens`: 200
- `temperature`: 0.6
- `top_p`: 0.8

### Prompt: Recommandations Apple Music Croisées

**Objectif:** Proposer des albums complémentaires disponibles sur Apple Music

```
Basé sur l'album "{album_title}" de {artist_name}, propose 5 albums complémentaires 
disponibles sur Apple Music que l'utilisateur devrait écouter.

Format JSON:
[
  {
    "title": "Album Title",
    "artist": "Artist Name",
    "reason": "Pourquoi cet album serait apprécié (20-30 mots)",
    "vibe": "Similar / Contraste / Inspiration"
  }
]

Critères:
- Tous les albums doivent être réels et disponibles sur Apple Music
- Mix entre artistes connus et découverte
- Diversité de genres ligérément
```

**Paramètres API :**
- `max_tokens`: 400
- `temperature`: 0.7
- `top_p`: 0.9

### Implémentation Frontend

```typescript
// handleOpenAppleMusic - Interface unifiée
const handleOpenAppleMusic = (
  event: React.MouseEvent,
  albumTitle?: string,
  artistName?: string,
  appleMusicUrl?: string | null
) => {
  event.stopPropagation()
  
  // Option 1: URL directe depuis Euria (future)
  if (appleMusicUrl) {
    const w = window.open(appleMusicUrl, '_blank')
    if (w) setTimeout(() => w.close(), 1000)
    return
  }
  
  // Option 2: Recherche intelligente (actuelle)
  if (!albumTitle || !artistName) return
  const searchQuery = `${albumTitle} ${artistName}`.trim()
  const encodedQuery = encodeURIComponent(searchQuery)
  const appleMusicSearchUrl = `https://music.apple.com/search?term=${encodedQuery}`
  const w = window.open(appleMusicSearchUrl, '_blank')
  if (w) setTimeout(() => w.close(), 1000)
}
```

### Status de Peuplement v4.7.0

| Feature | Status | Notes |
|---------|--------|-------|
| URL Slug Generation | 🟡 Prêt (Euria) | Prompts testés, implémentation future |
| Direct Link (apple_music_url) | 🟡 Infrastructure BD | Colonne ajoutée, attente peuplement Euria |
| Search Fallback | ✅ Actif | Fonctionne immédiatement |
| Desktop App Integration | ✅ Support complet | Détection OS, deep link vers app locale |
| Responsive Design | ✅ Complète | Mobile, tablet, desktop optimisés |

---

## 4️⃣ Layouts et Composition {#layouts}

### Layouts Dynamiques
```
Tu es designer UX pour une page magazine musicale. Propose 3 layouts différents 
pour afficher 4 albums avec un titre et une description.

Pour chaque layout, décris:
1. Grid: "1 col", "2 cols", "masonry", etc
2. Image position: "top", "left", "right", "center"
3. Image size: "small (20%)", "medium (40%)", "large (60%)"
4. Text position: relative to images
5. Spacing: "tight", "normal", "spacious"
6. Visual emphasis: which element stands out

Réponds en JSON valide et structuré.
```

**Réponse attendue** :
```json
[
  {
    "name": "Classic Stack",
    "grid": "1 col",
    "image_position": "top",
    "image_size": "large (60%)",
    "text_position": "bottom",
    "spacing": "normal"
  },
  {
    "name": "Side by Side",
    "grid": "2 cols",
    "image_position": "left",
    "image_size": "medium (40%)",
    "text_position": "right",
    "spacing": "spacious"
  }
]
```

---

### Palette de Couleurs
```
Propose 3 palettes de couleurs pour une page magazine musicale sombre et moderne.
Chacune doit avoir:
- Background color (hex)
- Accent color (hex)
- Text color (hex)
- Border color (hex)

Contexte: Album de rock progressif des années 70.

Réponds en JSON.
```

---

## 5️⃣ Playlists Thématiques {#playlists}

### Playlist Thématique Description
```
Crée une description accrocheur (80-100 mots) pour une playlist intitulée 
"Rainy Sunday Mornings - Introspection Sonore".

La playlist devrait :
- Capturer l'ambiance d'une pluie douce
- Mélanger calme et réflexion
- Inspirer l'écoute et la détente

Soit poétique et évocateur.
```

---

### Recommandations de Playlist
```
Basé sur ces préférences musicales:
- Genres favoris: Progressive Rock, Psychédélique, Jazz Fusion
- Artistes: Pink Floyd, Yes, King Crimson
- Mood: Réflexif, majestueux, expérimental

Propose 4 concepts de playlist thématiques différentes.
Pour chacun: 
- Titre court et accrocheur
- Description 50 mots
- Mood emoji
- 3 albums recommandés

Format JSON.
```

---

### Playlist Corrélative (Par Listening History)
```
Un utilisateur a écouté récemment:
- Thriller - Michael Jackson (pop 80s)
- Nevermind - Nirvana (grunge)
- Kind of Blue - Miles Davis (jazz)

Propose une playlist qui CONNECTE ces trois univers musicaux totalement différents.
- Titre: (créatif et unificateur)
- Concept: (comment relier MJ, Nirvana, et Miles Davis ?)
- Mood: (quelle ambiance générale ?)
- 5 albums/artistes de liaison

Sois créatif et justifie tes choix.
```

---

## 6️⃣ Poésie et Narration {#poesie}

### Haïku Récapitulatif Magazine
```
Tu reçois 5 albums de magazine musical:
1. The Dark Side of the Moon - Pink Floyd
2. Hotel California - Eagles
3. Bohemian Rhapsody - Queen
4. Stairway to Heaven - Led Zeppelin
5. Purple Haze - Jimi Hendrix

Crée un haïku unique (5-7-5) qui capture l'essence combinée de tous ces albums.
Soit épique et mélancolique à la fois.

Réponds uniquement avec le haïku.
```

---

### Poème Multi-Strophe
```
Écris un poème de 2 strophes (4 lignes chacune) qui capture l'essence musicale 
des années 1970 à travers ces albums emblématiques:
- Rumours (Fleetwood Mac)
- Boston (Boston)
- Night at the Opera (Queen)

Chaque strophe doit explorer un aspect différent (création, innovation, héritage).
Sois poétique et musiculièrement informé.
```

---

## 7️⃣ Analyse et Insights

### Analyse Culturelle
```
Analyse l'impact culturel de l'album "Nevermind" de Nirvana (1991).
Considère:
- Impact sur le grunge et la culture jeune
- Changement dans l'industrie musicale
- Pertinence aujourd'hui

80-100 mots. Sois critique mais équilibré.
```

---

### Comparaison d'Albums
```
Compare les albums "Sgt. Pepper's" (Beatles) et "Pink Floyd: The Wall".
Quels sont les points communs et différences en termes de:
- Innovation musicale
- Concept album approach
- Impact générationnel

100-150 mots. Sois nuancé.
```

---

## 8️⃣ Interactive & Engagement

### Appel à l'Action Poétique
```
Écris un appel à l'action poétique (40-60 mots) pour une playlist 
dont le thème est "Soirée Mélancolique Urbaine".

L'objectif: inspirer quelqu'un à cliquer et écouter.
Soit émotionnel et introspectif.

Réponds uniquement avec le texte.
```

---

### Teaser de Découverte
```
Écris un teaser mystery (30-50 mots) pour découvrir 
un album "caché" qui mérite d'être redécouvert.

Format: Énigmatique, intrigant, sans révéler le titre.
Exemple: "Écouté par 3 personnes seulement... une symphonie cachée vous attend..."

Sois accrocheur.
```

---

## 🎯 Testing Checklist {#testing}

### Phase 0: Configuration v4.7.0 (Apple Music)
- [ ] Vérifier colonne `apple_music_url` ajoutée à DB
- [ ] Testez les boutons Apple Music sur Magazine page
- [ ] Testez les boutons Apple Music sur Collection page
- [ ] Testez les boutons Apple Music sur Journal page
- [ ] Testez les boutons Apple Music sur Collections page
- [ ] Vérifier fermeture auto fenêtre après ~1s
- [ ] Vérifier recherche fallback Apple Music fonctionne

### Phase 1: Validation Euria (API & Prompts)
- [ ] Vérifier configuration `EURIA_API_KEY` et `EURIA_API_URL`
- [ ] Testez un haïku simple (copy-paste directement via API)
- [ ] Testez via cURL endpoint
- [ ] Testez via backend Python
- [ ] Testez via frontend JavaScript
- [ ] Vérifiez le format et la qualité
- [ ] Testez avec 3 albums différents (genres variés)
- [ ] Vérifiez la cohérence des réponses
- [ ] Testez les paramètres (temperature, max_tokens, top_p)

### Phase 2: Intégration Backend
- [ ] Créez `test_magazine_generation_v470.py` pour tester v4.7.0
- [ ] Testez haïku + descriptions
- [ ] Testez Apple Music slug generation (v4.7)
- [ ] Testez Apple Music improvements prompt (v4.7)
- [ ] Vérifiez les temps de réponse (~5-10s)
- [ ] Testez avec BD vide/petite
- [ ] Validez les fallbacks si Euria indisponible
- [ ] Testez error handling (timeout, rate limit, invalid key)

### Phase 3: Frontend (Magazine + Apple Music)
- [ ] Navigation scroll fonctionne
- [ ] Tous les types de pages s'affichent
- [ ] Minuteur compte à rebours
- [ ] "Nouvelle édition" regénère correctement
- [ ] Responsive design mobile
- [ ] **Apple Music buttons visible et clickables (v4.7)**
- [ ] **Apple Music buttons auto-close window (v4.7)**
- [ ] **Apple Music search fallback works (v4.7)**
- [ ] Boutons Spotify + Apple coexist sans conflict

### Phase 4: Qualité & Performance
- [ ] Pas d'erreurs de typage TypeScript
- [ ] Pas de console errors
- [ ] Performance: <3s par page
- [ ] Les images chargent correctement
- [ ] Memory leaks: monitorer avec Dev Tools
- [ ] Accessibility: boutons keyboard-navigable

---

## 📊 Métriques Attendues

### Euria (API)
- Latence haïku: 0.5-2s
- Latence description: 2-4s  
- Latence playlist: 1-3s
- Latence Apple Music slug: 0.3-1s (température basse)
- Taux succès: >95%
- Rate limit: Gérer selon abonnement Infomaniak

### Magazine Complet
- Génération: 3-10s (dépend Euria)
- First paint: <1s
- Navigation: <100ms
- Memory: 2-5MB

### Apple Music Integration v4.7.0
- Bouton click → Apple app open: <100ms
- Window auto-close: ~1000ms
- Search fallback: <100ms (pas d'API)
- Database query (apple_music_url): <50ms (avec index)

---

## 🔧 Debugging Tips

Si une réponse Euria n'est pas au format attendu :
1. Vérifiez le `max_tokens` (peut être trop bas)
2. Ajoutez "Réponds uniquement avec [format]"
3. Testez le prompt directement dans Euria dashboard
4. Vérifiez la connexion Euria (authentication, rate limit)
5. Consultez logs backend pour erreurs API

### Apple Music Specific (v4.7.0)

Si buttons Apple Music ne s'affichent pas :
1. Vérifier `apple_music_url` présent dans API response
2. Vérifier colonne DB créée: `sqlite3 data/musique.db "PRAGMA table_info(albums);"`
3. Vérifier index créé: `sqlite3 data/musique.db ".indices albums;"`
4. Vérifier album model includes field: `backend/app/models/album.py`

Si window ne se ferme pas :
1. Vérifier timeout 1000ms n'est pas trop court
2. Vérifier que `window.close()` ne bloque pas
3. Vérifier permissions pop-up not blocked par browser

Si recherche fallback ne marche pas :
1. Tester URL directement dans browser
2. Vérifier encodeURIComponent() appliqué correctement  
3. Vérifier album_title et artist_name pas null/undefined

---

## 🎯 Roadmap v4.8.0+

### Euria Population (v4.8.0)
- [ ] Batch generation apple_music_url pour toute collection
- [ ] Smart scheduling (off-peak when Euria less busy)
- [ ] Progressive UI updates
- [ ] Retry logic avec exponential backoff

### Multi-Service Support (v4.9.0)
- [ ] YouTube Music buttons
- [ ] Tidal buttons
- [ ] Amazon Music buttons
- [ ] Unified multiservice search

### Advanced Features (v5.0+)
- [ ] User service preferences
- [ ] Service availability detection (per country)
- [ ] Deep linking optimization
- [ ] Sharing with service selector

---

**Prêt à tester ? 🚀**

Commencez par :
1. Vérifier configuration Euria (EURIA_API_KEY, EURIA_API_URL)
2. Tester API avec cURL example fourni
3. Copier prompts 1-3 et testez dans dashboard Euria
4. Tester Apple Music buttons sur pages (v4.7.0)
