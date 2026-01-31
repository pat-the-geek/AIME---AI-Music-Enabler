# 📤 Export Markdown - Interface Frontend

## 🎯 Vue d'ensemble

Intégration complète de la fonctionnalité d'export markdown dans l'interface utilisateur de la Collection Discogs.

## 🖥️ Interface Utilisateur

### Emplacement
Page: **Collection Discogs** (`/collection`)

### Bouton Principal
Un bouton "**Exporter en Markdown**" avec icône 📥 situé en haut à droite de la page, à côté du titre.

### Menu d'Export (3 options)

```
┌─────────────────────────────────────┐
│ 📄 Collection complète              │
│    235 albums                        │
├─────────────────────────────────────┤
│ 💿 Vinyles uniquement               │
├─────────────────────────────────────┤
│ 💿 CD uniquement                    │
└─────────────────────────────────────┘
```

## 🔧 Fonctionnalités Implémentées

### 1. Export Collection Complète
- **Action:** Télécharge `collection-discogs.md`
- **Contenu:** Tous les 235 albums de la collection
- **Taille:** ~518 KB
- **Format:** Markdown enrichi avec métadonnées, résumés IA, liens

### 2. Export Vinyles
- **Action:** Télécharge `collection-vinyle.md`
- **Contenu:** Uniquement les albums en format Vinyle (~218 albums)
- **Filtre:** Support = "Vinyle"

### 3. Export CD
- **Action:** Télécharge `collection-cd.md`
- **Contenu:** Uniquement les albums en format CD (~78 albums)
- **Filtre:** Support = "CD"

## 💻 Code Technique

### Composant Modifié
**Fichier:** `frontend/src/pages/Collection.tsx`

### Imports Ajoutés
```typescript
import {
  Button,
  Menu,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import { 
  FileDownload as FileDownloadIcon,
  Description as DescriptionIcon,
  Album as AlbumIcon,
} from '@mui/icons-material'
```

### État du Composant
```typescript
const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null)
```

### Handlers Implémentés

#### 1. Gestion du Menu
```typescript
const handleExportMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
  setExportMenuAnchor(event.currentTarget)
}

const handleExportMenuClose = () => {
  setExportMenuAnchor(null)
}
```

#### 2. Export Collection Complète
```typescript
const handleExportCollection = async () => {
  try {
    const response = await apiClient.get('/collection/export/markdown', {
      responseType: 'blob',
    })
    
    // Téléchargement automatique
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'collection-discogs.md')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Erreur lors de l\'export:', error)
  } finally {
    handleExportMenuClose()
  }
}
```

#### 3. Export par Support (Vinyle/CD)
Même logique que l'export complet, avec routes différentes :
- Vinyle: `/collection/export/markdown/support/Vinyle`
- CD: `/collection/export/markdown/support/CD`

## 🎨 UI/UX

### Positionnement
```tsx
<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
  <Typography variant="h4">
    Collection Discogs
  </Typography>
  
  <Button
    variant="contained"
    startIcon={<FileDownloadIcon />}
    onClick={handleExportMenuOpen}
  >
    Exporter en Markdown
  </Button>
</Box>
```

### Menu Déroulant
```tsx
<Menu
  anchorEl={exportMenuAnchor}
  open={Boolean(exportMenuAnchor)}
  onClose={handleExportMenuClose}
>
  <MenuItem onClick={handleExportCollection}>
    <ListItemIcon>
      <DescriptionIcon fontSize="small" />
    </ListItemIcon>
    <ListItemText 
      primary="Collection complète" 
      secondary={`${data?.total || 0} albums`} 
    />
  </MenuItem>
  
  {/* Vinyle et CD ... */}
</Menu>
```

## 🚀 Utilisation

### Workflow Utilisateur

1. **Ouvrir la page Collection**
   - Naviguer vers `/collection` dans l'application

2. **Cliquer sur "Exporter en Markdown"**
   - Bouton visible en haut à droite

3. **Sélectionner le type d'export**
   - Collection complète (toute la collection)
   - Vinyles uniquement
   - CD uniquement

4. **Téléchargement automatique**
   - Le fichier `.md` se télécharge automatiquement
   - Nom du fichier: `collection-{type}.md`

## 📊 Informations Exportées

Chaque export inclut :
- ✅ Table des matières avec liens
- ✅ Groupement par artiste
- ✅ Métadonnées complètes (année, labels, support, IDs)
- ✅ Résumés IA générés
- ✅ Liens Spotify et Discogs
- ✅ Images de couverture (URLs)
- ✅ Horodatage de l'export

## 🔒 Gestion des Erreurs

```typescript
try {
  // Export...
} catch (error) {
  console.error('Erreur lors de l\'export:', error)
  // TODO: Ajouter un snackbar/toast pour notifier l'utilisateur
} finally {
  handleExportMenuClose()
}
```

**Future amélioration:** Ajouter des notifications visuelles (snackbar Material-UI) pour :
- ✅ Export réussi
- ❌ Erreur d'export
- ⏳ Export en cours (pour grandes collections)

## 🎯 Extensions Futures

### 1. Export par Artiste
Ajouter un bouton d'export dans la page de détail d'un album :
```typescript
const handleExportArtist = async (artistId: number) => {
  const response = await apiClient.get(
    `/collection/export/markdown/${artistId}`,
    { responseType: 'blob' }
  )
  // Téléchargement...
}
```

### 2. Filtres Avancés
Permettre l'export avec les filtres actuels de la page :
- Par année
- Par genre
- Par recherche

### 3. Format Additionnel
Bouton pour exporter en :
- PDF (avec mise en page)
- JSON (pour import/export)
- CSV (pour Excel)

### 4. Prévisualisation
Modal montrant un aperçu du markdown avant téléchargement.

## 📱 Responsive Design

Le bouton et le menu s'adaptent automatiquement :
- **Desktop:** Bouton complet avec texte
- **Mobile:** Possibilité de réduire en icône uniquement
- **Tablet:** Taille intermédiaire

## ✅ Checklist de Déploiement

- [x] Imports Material-UI ajoutés
- [x] État du menu géré
- [x] Handlers d'export implémentés
- [x] Bouton UI intégré
- [x] Menu déroulant créé
- [x] Téléchargement automatique configuré
- [x] Nettoyage des URLs
- [x] Gestion des erreurs basique
- [ ] Notifications utilisateur (toast/snackbar)
- [ ] Tests d'intégration
- [ ] Documentation utilisateur

## 🐛 Débogage

### Vérifier les Endpoints Backend
```bash
curl http://localhost:8000/api/v1/collection/export/markdown
```

### Vérifier la Console Navigateur
```javascript
// Dans la console Chrome/Firefox
console.log('Export menu anchor:', exportMenuAnchor)
```

### Vérifier le Téléchargement
- Vérifier que `responseType: 'blob'` est bien défini
- Vérifier que le fichier se télécharge dans le dossier Downloads
- Vérifier l'encodage UTF-8 du fichier

## 📚 Références

- [Backend API Documentation](./EXPORT-MARKDOWN.md)
- [Material-UI Menu](https://mui.com/material-ui/react-menu/)
- [Axios Blob Response](https://axios-http.com/docs/res_schema)
- [Download Attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a#attr-download)

---

**Statut:** ✅ Implémenté et fonctionnel
**Date:** 31 janvier 2026
**Version:** 1.0.0
