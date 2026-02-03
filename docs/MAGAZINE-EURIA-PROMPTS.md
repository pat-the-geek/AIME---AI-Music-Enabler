## 🧪 Prompts d'Éxécution pour Tester Euria

### 📋 Comment Utiliser

Ces prompts sont prêts à être envoyés à l'API Euria. Adaptez-les selon vos besoins !

---

## 1️⃣ Haïkus Basiques

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

## 3️⃣ Layouts et Composition

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

## 4️⃣ Playlists Thématiques

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

## 5️⃣ Poésie et Narration

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

## 6️⃣ Analyse et Insights

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

## 7️⃣ Interactive & Engagement

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

## 🎯 Testing Checklist

### Phase 1: Validation Euria
- [ ] Testez un haïku simple (copy-paste directement dans Euria)
- [ ] Vérifiez le format et la qualité
- [ ] Testez avec 3 albums différents (genres variés)
- [ ] Vérifiez la cohérence des réponses

### Phase 2: Intégration Backend
- [ ] Créez `test_magazine_generation.py` pour tester les endpoints
- [ ] Vérifiez les temps de réponse (~5-10s)
- [ ] Testez avec BD vide/petite
- [ ] Validez les fallbacks si Euria indisponible

### Phase 3: Frontend
- [ ] Navigation scroll fonctionne
- [ ] Tous les types de pages s'affichent
- [ ] Minuteur compte à rebours
- [ ] "Nouvelle édition" regénère correctement
- [ ] Responsive design mobile

### Phase 4: Qualité
- [ ] Pas d'erreurs de typage TypeScript
- [ ] Pas de console errors
- [ ] Performance: <3s par page
- [ ] Les images chargent correctement

---

## 📊 Métriques Attendues

### Euria
- Latence haïku: 0.5-2s
- Latence description: 2-4s
- Latence playlist: 1-3s
- Taux succès: >95%

### Magazine Complet
- Génération: 3-10s (dépend Euria)
- First paint: <1s
- Navigation: <100ms
- Memory: 2-5MB

---

## 🔧 Debugging Tips

Si une réponse Euria n'est pas au format attendu :
1. Vérifiez le `max_tokens` (peut être trop bas)
2. Ajoutez "Réponds uniquement avec [format]"
3. Testez le prompt directement dans Euria/ChatGPT
4. Vérifiez la connexion Euria (circuit breaker)

---

**Prêt à tester ? 🚀**

Commencez par copier les prompts 1-3 et testez directement dans Euria pour validation !
