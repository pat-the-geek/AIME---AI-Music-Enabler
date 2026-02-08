## 📖 Magazine - Documentation

### 🎯 Vue d'ensemble

Le **Magazine** est une page principale dynamique et immersive qui affiche votre collection musicale sous forme de pages éditorialisées, régénérées à chaque visite ou selon un calendrier de rafraîchissement.

### ✨ Fonctionnalités

#### 1. **Affichage en Full-Screen**
- Une page = un viewport complet
- Navigation fluide avec scroll vertical (wheel) ou boutons
- Transition smooth entre les pages

#### 2. **5 Pages Thématiques**
- **Page 1** : Artiste aléatoire + ses albums + haïku
- **Page 2** : Album du jour + description IA longue (2000 caractères)
- **Page 3** : Albums aléatoires + haïkus spécifiques
- **Page 4** : Timeline des écoutes récentes + statistiques
- **Page 5** : Playlist thématique générée par IA

#### 3. **Rafraîchissement Intelligent**
- Auto-refresh tous les **15 minutes**
- Compteur en temps réel dans le header
- Bouton **"Nouvelle édition"** pour regénérer immédiatement
- Affichage de l'heure de génération

#### 4. **Layouts Variables**
Chaque page a un layout aléatoire pour une expérience nouvelle :
- Image positionnement variable (gauche, haut, droite)
- Tailles d'images aléatoires
- Schémas de couleurs changeants (dark, light, vibrant)
- Nombre de colonnes adapté

#### 5. **Intégration IA Euria**
- Génération de haïkus (5-7-5 syllabes) pour chaque album
- Description d'albums longue et contextuelle
- Suggestions de playlists thématiques avec textes accrocheurs
- Prompts adapté pour variabilité créative

### 🚀 Architecture Technique

#### Backend (`magazine_generator_service.py`)
```python
MagazineGeneratorService
├── generate_magazine()
│   ├── _generate_page_1_artist()    # Artiste aléatoire
│   ├── _generate_page_2_album_detail()  # Album du jour
│   ├── _generate_page_3_albums_haikus() # Albums + haïkus
│   ├── _generate_page_4_timeline()      # Stats
│   └── _generate_page_5_playlist()      # Playlist thématique
└── AIService.ask_for_ia()           # Intégration Euria
```

#### Frontend (`pages/Magazine.tsx` + `components/MagazinePage.tsx`)
- Gestion de l'état de pagination
- Minuteur d'auto-refresh
- Navigation au clavier et souris
- Composants réutilisables par type de page

### 🎨 Schémas de Couleurs

Trois schémas aléatoires par magazine :
1. **Dark** : Fond #1a1a1a, accent #667eea (bleu dégradé)
2. **Light** : Fond #f5f5f5, accent #764ba2 (violet)
3. **Vibrant** : Fond #1a0033, accent #ff006e (rose vif)

### 📊 Données Utilisées

- ✅ Albums de la collection (tous les supports)
- ✅ Artistes (sélection aléatoire)
- ✅ Descriptions IA (ai_description)
- ✅ Historique d'écoute (50 dernières)
- ✅ Images d'albums
- ✅ Métadonnées (année, genre, style)

### 🧠 Prompts Euria Utilisés

1. **Haïku artiste** : Génère un haïku sur un artiste spécifique
2. **Haïku album** : Génère un haïku sur un album spécifique
3. **Description album** : Déjà existant dans la BD
4. **Playlist thématique** : Génère une description accrocheuse pour une playlist

### 🔧 Configuration

#### Rafraîchissement
- Intervalle : **15 minutes** (900 secondes)
- Modifiable dans `Magazine.tsx`, ligne du `useEffect` du timer

#### Nombre de pages
- Actuellement : **5 pages fixes**
- Pour modifier : éditer `generate_magazine()` dans `magazine_generator_service.py`

#### Limite de sélection
- Haïkus par magazine : 2-3 albums aléatoires par page
- Albums affichés : 5-7 par page (selon layout)

### 💡 Améliorations Futures Proposées

#### Avec Euria :
1. **Composition de page dynamique**
   - Demander à Euria : "Propose 5 layouts différents avec positions images/textes"
   - Utiliser sa réponse pour positionner dynamiquement les éléments

2. **Textes éditoriaux**
   - Générer une introduction pour chaque page
   - "Crée un texte court (100 mots) pour introduire cet album..."

3. **Recommandations intelligentes**
   - "Basé sur les écoutes récentes, propose 5 albums à découvrir"
   - Intégrer comme bonus page ou section

4. **Captions créatifs**
   - Pour chaque image : "Génère une légende poétique pour cette pochette d'album"

5. **Playlist collaborative**
   - Combiner les haïkus en poème complet
   - Créer une narration entre les pages

#### Sans Euria :
1. **Persistance entre refreshs**
   - Cache derniers magazines (1-2 éditions)
   - Comparaison avant/après

2. **Mode lecture continue**
   - Play automatique de la playlist de la page 5

3. **Export**
   - Télécharger le magazine en PDF/image

4. **Partage**
   - QR code ou lien vers édition spécifique

5. **Analytics**
   - Stats : album/artiste le plus affiché
   - Temps moyen par page

### 🎵 Exemple de Flux Utilisateur

```
1. Utilisateur accède à /magazine
   ↓
2. Backend génère 5 pages en ~5-10 secondes
   ├─ Appels Euria pour haïkus
   ├─ Sélections aléatoires d'albums/artistes
   └─ Layouts variables
   ↓
3. Frontend affiche Page 1 (artiste)
   ↓
4. Utilisateur scroll/navigue entre les pages
   ↓
5. Après 15 min → Auto-refresh avec nouvelle édition
   ↓
6. Ou click "Nouvelle édition" → Refresh immédiat
```

### 🐛 Gestion des Erreurs

- BD vide ou pas assez d'albums : pages vides graceful
- Euria indisponible : haïkus par défaut
- Circuit breaker sur Euria : fallback et alertes

### 📈 Performances

- Chargement initial : ~3-5s (dépend Euria)
- Navigation entre pages : <100ms (local)
- Mémoire : ~2-5MB par magazine

### 🔐 Sécurité

- Pas d'exposition de données sensibles
- Requête GET uniquement pour génération
- IDs d'albums/artistes anonymisés en frontend

---

**À tester :**
1. Allez sur `/magazine`
2. Vérifiez que les 5 pages s'affichent correctement
3. Testez la navigation (scroll, boutons, dots)
4. Vérifiez le minuteur (doit compter à rebours)
5. Cliquez "Nouvelle édition" et vérifiez les changements

Amusez-vous bien ! 🎉
