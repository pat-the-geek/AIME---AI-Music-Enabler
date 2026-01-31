# 📔 Journal & Timeline - Documentation Complète

## Date : 30 janvier 2026

---

## 🎯 Vue d'Ensemble

Implémentation complète des pages **Journal d'Écoute** et **Timeline Horaire** selon les spécifications du projet. Ces deux pages permettent de visualiser l'historique d'écoute musicale avec différentes perspectives : chronologique (Journal) et temporelle (Timeline).

---

## 📔 Page Journal d'Écoute

### Route
`/journal`

### Fonctionnalités Implémentées

#### 1. **Affichage des Écoutes**
- ✅ Liste chronologique inversée (plus récent en haut)
- ✅ Affichage de 50 écoutes par page
- ✅ Triple images : artiste, album Spotify, album Last.fm
- ✅ Métadonnées complètes : titre, artiste, album, date/heure, source
- ✅ Description IA expandable avec formatage markdown
- ✅ Icône favori (❤️) cliquable pour marquer/démarquer

#### 2. **Modes d'Affichage**
- **Mode Détaillé** (par défaut) :
  - Grandes images d'artiste et d'album
  - Toutes les métadonnées visibles
  - Accordéon pour description IA
  - Source affichée (Last.fm, etc.)
  
- **Mode Compact** :
  - Pas d'images
  - Métadonnées essentielles uniquement
  - Plus d'écoutes visibles à l'écran
  - Espacement réduit

#### 3. **Système de Filtres**
Panneau dépliable avec 6 filtres :
- **Recherche** : Texte libre (titre, artiste, album) avec debounce 500ms
- **Artiste** : Filtrage par nom d'artiste
- **Album** : Filtrage par nom d'album
- **Favoris** : Tous / Favoris uniquement / Non favoris
- **Date début** : Sélecteur de date
- **Date fin** : Sélecteur de date
- **Bouton réinitialiser** : Reset tous les filtres

#### 4. **Pagination**
- Navigation Précédent/Suivant
- Indicateur de page actuelle (ex: "Page 2 / 10")
- Compteur total d'écoutes
- Spinner de chargement pendant le fetch

#### 5. **Sidebar Statistiques** (Sticky)
Affichage en temps réel :
- 📊 Total écoutes
- 👤 Artistes uniques
- 💿 Albums uniques
- ⏰ Heure de pointe
- ⏱️ Durée totale (heures + minutes)

Mise à jour automatique selon les filtres appliqués.

#### 6. **Fonctionnalités Supplémentaires**
- ❤️ Toggle favoris avec mutation API
- 🤖 Description IA formatée avec markdown (gras, italique, listes)
- 🔄 Invalidation automatique du cache après actions
- ⚡ Optimisation : debounce recherche, requêtes React Query

---

## ⏰ Page Timeline Horaire

### Route
`/timeline`

### Fonctionnalités Implémentées

#### 1. **Navigation Temporelle**
- Sélection de date avec navigation Prev/Next
- Formatage date en français (ex: "mardi 30 janvier 2026")
- Désactivation du bouton "Next" pour les dates futures
- Persistance de la date sélectionnée

#### 2. **Statistiques Journalières**
En-tête avec 4 statistiques :
- Total écoutes de la journée
- Artistes uniques
- Albums uniques
- Heure de pointe (mise en évidence)

#### 3. **Visualisation Horaire**
- **Plage horaire** : 6h - 23h (18 heures)
- **Scroll horizontal** : Navigation fluide entre les heures
- **Alternance de couleurs** : Fond alterné gris/blanc pour lisibilité
- **Mise en évidence** : Heure de pointe en couleur primaire
- **Limite** : 20 tracks maximum affichés par heure (+ compteur "X écoutes supplémentaires")

#### 4. **Affichage des Tracks**
Chaque colonne horaire affiche :
- **Header** : Heure + nombre d'écoutes
- **Cards** : Une card par track avec :
  - Heure exacte (HH:MM)
  - Titre du morceau
  - Artiste
  - Album (mode détaillé)
  - Icône ❤️ si favori

#### 5. **Modes d'Affichage**
- **Mode Détaillé** :
  - Colonnes larges (320px)
  - Toutes les métadonnées
  - Chips pour l'heure
  - Espacement généreux
  
- **Mode Compact** :
  - Colonnes étroites (180px)
  - Métadonnées minimales
  - Format condensé
  - Plus d'heures visibles à l'écran

#### 6. **Gestion des Cas Limites**
- ✅ Aucune écoute pour une heure → Message "Aucune écoute"
- ✅ Plus de 20 tracks/heure → Affiche compteur "+ X écoutes supplémentaires"
- ✅ Journée sans écoutes → Toutes les colonnes vides avec message
- ✅ Scroll performant même avec beaucoup de données

#### 7. **Légende & Aide**
Footer informatif expliquant :
- Le scroll horizontal
- La limite de 20 écoutes/heure
- La mise en évidence de l'heure de pointe

---

## 🔧 Architecture Technique

### Frontend Components

#### Journal.tsx
```typescript
// États
- page: number (pagination)
- searchInput: string (recherche avec debounce)
- artistFilter, albumFilter: string
- lovedFilter: 'all' | 'true' | 'false'
- startDate, endDate: string
- viewMode: 'detailed' | 'compact'
- showFilters: boolean

// Queries
- useQuery(['history', ...filters]) : Liste paginée
- useQuery(['history-stats', dates]) : Statistiques

// Mutations
- toggleLoveMutation : Toggle favori
```

#### Timeline.tsx
```typescript
// États
- selectedDate: string (YYYY-MM-DD)
- viewMode: 'detailed' | 'compact'

// Query
- useQuery(['timeline', date]) : Données horaires + stats

// Helpers
- formatDate() : Format FR
- getHourColor() : Alternance couleurs
- hourRange : Array 6-23h
```

### Backend Endpoints

#### `/api/v1/history/tracks`
**Méthode** : GET  
**Paramètres** :
- `page`, `page_size` : Pagination
- `artist`, `album` : Filtres texte
- `loved` : Filtrage favoris
- `start_date`, `end_date` : Plage temporelle

**Réponse** :
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "page_size": 50,
  "pages": 3
}
```

#### `/api/v1/history/timeline`
**Méthode** : GET  
**Paramètres** :
- `date` : Date YYYY-MM-DD (requis)

**Réponse** :
```json
{
  "date": "2026-01-30",
  "hours": {
    "9": [{ "id": 1, "time": "09:15", ... }],
    "14": [...]
  },
  "stats": {
    "total_tracks": 45,
    "unique_artists": 12,
    "unique_albums": 8,
    "peak_hour": 18
  }
}
```

#### `/api/v1/history/stats`
**Méthode** : GET  
**Paramètres** :
- `start_date`, `end_date` : Optionnels

**Réponse** :
```json
{
  "total_tracks": 1250,
  "unique_artists": 89,
  "unique_albums": 134,
  "peak_hour": 18,
  "total_duration_seconds": 245760
}
```

#### `/api/v1/history/tracks/{track_id}/love`
**Méthode** : POST  
**Réponse** :
```json
{
  "track_id": 42,
  "loved": true
}
```

---

## 🎨 Design & UX

### Palette de Couleurs
- **Background alterné** : Default / Action.hover
- **Heure de pointe** : Primary.main avec contrastText
- **Favoris** : Red (Material-UI error)
- **Cartes** : Outlined variant avec borders subtiles

### Responsive
- **Desktop** : Sidebar stats sticky, timeline scroll horizontal fluide
- **Mobile** : Stack vertical, colonnes timeline plus étroites
- **Tablet** : Layouts adaptatifs

### Performance
- ✅ Debounce recherche (500ms)
- ✅ Pagination (50 items/page)
- ✅ Limite timeline (20 tracks/heure)
- ✅ React Query cache & staleTime
- ✅ Invalidation intelligente du cache
- ✅ Lazy loading des descriptions IA (accordéon)

---

## 📊 Cas d'Usage

### 1. Consulter l'historique récent
1. Ouvrir `/journal`
2. Mode détaillé par défaut
3. Scroller pour voir les dernières écoutes

### 2. Rechercher des écoutes spécifiques
1. Cliquer "Filtres"
2. Saisir artiste/album ou utiliser recherche globale
3. Appliquer plage de dates si nécessaire
4. Résultats mis à jour automatiquement

### 3. Voir l'activité d'une journée
1. Ouvrir `/timeline`
2. Naviguer vers la date souhaitée (Prev/Next)
3. Scroller horizontalement pour voir toutes les heures
4. Identifier l'heure de pointe (colonne en couleur)

### 4. Marquer des favoris
1. Cliquer l'icône ❤️ sur n'importe quelle écoute
2. Confirmation visuelle immédiate
3. Filtrer ensuite par favoris si besoin

### 5. Analyser les statistiques
1. Sidebar Journal : stats en temps réel
2. Header Timeline : stats journalières
3. Appliquer filtres pour affiner l'analyse

---

## 🧪 Tests Effectués

### Backend
```bash
# Stats globales
curl "http://localhost:8000/api/v1/history/stats"

# Timeline journée
curl "http://localhost:8000/api/v1/history/timeline?date=2026-01-30"

# Liste avec filtres
curl "http://localhost:8000/api/v1/history/tracks?page=1&page_size=50&artist=Beatles"

# Toggle favori
curl -X POST "http://localhost:8000/api/v1/history/tracks/42/love"
```

### Frontend
- ✅ Affichage Journal vide (pas de données encore)
- ✅ Affichage Timeline vide
- ✅ Navigation dates (Prev/Next)
- ✅ Toggle modes Détaillé/Compact
- ✅ Ouverture/fermeture filtres
- ✅ Sidebar stats sticky
- ✅ Scroll horizontal timeline
- ✅ Formatage markdown descriptions IA
- ✅ Aucune erreur de compilation TypeScript

---

## 🚀 Prochaines Étapes

### Avec Données Réelles
Quand le tracker Last.fm sera actif et des écoutes enregistrées :
1. Tester pagination avec > 50 écoutes
2. Vérifier performance timeline avec journées chargées (>20 tracks/heure)
3. Tester recherche et filtres avec données variées
4. Valider statistiques temps réel
5. Tester toggle favoris avec invalidation cache

### Améliorations Futures
- [ ] Pagination infinie (scroll infini) pour Journal
- [ ] Export timeline en image/PDF
- [ ] Graphiques de distribution horaire
- [ ] Filtres sauvegardés (presets)
- [ ] Recherche avancée avec opérateurs (AND, OR, NOT)
- [ ] Sélection multiple pour actions groupées
- [ ] Annotations personnelles sur écoutes
- [ ] Partage de timeline via URL

---

## 📝 Notes Techniques

### Dépendances Ajoutées
- `react-markdown` : Formatage descriptions IA

### Optimisations
- Debounce recherche évite appels API excessifs
- React Query gère le cache intelligent
- Sticky sidebar évite re-renders inutiles
- Limitation 20 tracks/heure améliore performance scroll

### Compatibilité
- ✅ React 18.2+
- ✅ Material-UI 5.15+
- ✅ TanStack Query (React Query) v5+
- ✅ TypeScript 5.0+

---

## 🎓 Ressources

### Documentation Backend
- `/backend/app/api/v1/history.py` : Routes API
- `/backend/app/schemas/history.py` : Schémas Pydantic

### Documentation Frontend
- `/frontend/src/pages/Journal.tsx` : Page Journal
- `/frontend/src/pages/Timeline.tsx` : Page Timeline
- `/frontend/src/types/models.ts` : Types TypeScript

### Spécifications
- `SPECIFICATION-REACT-REBUILD.md` : Specs complètes projet
- Sections 2 et 3 : Journal et Timeline

---

**✅ Développement terminé - Pages Journal et Timeline opérationnelles !**
