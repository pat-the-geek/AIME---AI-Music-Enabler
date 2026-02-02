# Affichage de la Progression d'Importation Last.fm

## Date de mise en œuvre
2 février 2026

## Contexte
L'importation Discogs affichait déjà une progression en temps réel. Cette fonctionnalité a été étendue à l'importation Last.fm pour offrir une meilleure visibilité sur le processus d'importation qui peut prendre plusieurs minutes.

## Modifications Backend

### Fichier: `backend/app/api/v1/services.py`

#### 1. Variable Globale de Progression
Ajout d'une nouvelle variable globale pour tracker la progression de l'importation Last.fm :

```python
_lastfm_import_progress = {
    "status": "idle",           # idle, starting, running, completed, error
    "current_batch": 0,         # Batch actuel
    "total_batches": 0,         # Nombre total de batches
    "imported": 0,              # Nombre de tracks importés
    "skipped": 0,               # Nombre de tracks ignorés (doublons)
    "errors": 0,                # Nombre d'erreurs
    "total_scrobbles": 0        # Nombre total de scrobbles à importer
}
```

#### 2. Nouveau Endpoint API
Ajout d'un endpoint GET pour récupérer la progression :

```python
@router.get("/lastfm/import/progress")
async def get_lastfm_import_progress():
    """Obtenir la progression de l'importation Last.fm."""
    return _lastfm_import_progress
```

#### 3. Mise à Jour de la Progression
La fonction `import_lastfm_history` met à jour la progression :
- Au démarrage : `status = "starting"`
- Pendant l'exécution : `status = "running"` + mise à jour des compteurs
- À la fin : `status = "completed"` ou `status = "error"`

Les mises à jour se font :
- Au début de chaque batch (toutes les 200 tracks)
- Mise à jour des compteurs d'importation, d'erreurs et de doublons

## Modifications Frontend

### Fichier: `frontend/src/pages/Settings.tsx`

#### 1. État Local
Ajout d'un état pour stocker la progression :

```typescript
const [lastfmImportProgress, setLastfmImportProgress] = useState<any>(null)
```

#### 2. Mutation avec Polling
La mutation d'import a été modifiée pour inclure un système de polling :

```typescript
const importHistoryMutation = useMutation({
  mutationFn: async (limit: number | null) => {
    // Démarrer l'import
    await apiClient.post(url, null, { timeout: 600000 })
    
    // Polling pour suivre la progression
    return new Promise((resolve, reject) => {
      const pollInterval = setInterval(async () => {
        const progressResponse = await apiClient.get('/services/lastfm/import/progress')
        const progress = progressResponse.data
        
        setLastfmImportProgress(progress)
        
        if (progress.status === 'completed') {
          clearInterval(pollInterval)
          resolve(progress)
        }
      }, 1000) // Vérifier toutes les secondes
    })
  }
})
```

#### 3. Interface Utilisateur
Ajout d'un encadré de progression similaire à Discogs :

```tsx
{lastfmImportProgress && (lastfmImportProgress.status === 'running' || lastfmImportProgress.status === 'starting') && (
  <Box sx={{ mb: 2, p: 2, backgroundColor: 'background.paper', border: '1px solid', borderColor: 'primary.main', borderRadius: 1 }}>
    <Typography variant="body2" color="primary" gutterBottom>
      📥 Import en cours... Batch {lastfmImportProgress.current_batch}/{lastfmImportProgress.total_batches}
    </Typography>
    <LinearProgress 
      variant="determinate" 
      value={(lastfmImportProgress.current_batch / lastfmImportProgress.total_batches) * 100} 
    />
    <Typography variant="caption" color="text.secondary" display="block">
      📊 Total: {lastfmImportProgress.total_scrobbles} scrobbles
    </Typography>
    <Typography variant="caption" display="block" color="text.secondary">
      ✅ {lastfmImportProgress.imported} importés | 
      ⏭️ {lastfmImportProgress.skipped} ignorés | 
      ❌ {lastfmImportProgress.errors} erreurs
    </Typography>
  </Box>
)}
```

#### 4. Désactivation du Bouton
Le bouton d'import est désactivé pendant l'importation :

```tsx
disabled={importHistoryMutation.isPending || (lastfmImportProgress && (lastfmImportProgress.status === 'running' || lastfmImportProgress.status === 'starting'))}
```

## Fonctionnement

### Workflow
1. L'utilisateur clique sur "Importer l'Historique"
2. Le frontend envoie une requête POST à `/services/lastfm/import-history`
3. Le backend initialise `_lastfm_import_progress` avec `status: "starting"`
4. Le backend commence l'import par batches de 200 tracks
5. À chaque batch, le backend met à jour la progression
6. Le frontend poll l'endpoint `/services/lastfm/import/progress` toutes les secondes
7. L'interface affiche une barre de progression et les statistiques en temps réel
8. Quand le statut passe à "completed" ou "error", le polling s'arrête

### Affichage
- **Barre de progression** : Indique le pourcentage de batches complétés
- **Compteur de batches** : `Batch X/Y` où Y = total scrobbles / 200
- **Total de scrobbles** : Nombre total d'écoutes à importer
- **Statistiques** : Nombre de tracks importés, ignorés et en erreur

## Cohérence avec Discogs
Cette implémentation suit exactement le même modèle que la synchronisation Discogs :
- Structure de données similaire
- Même système de polling
- Interface utilisateur cohérente
- Gestion d'erreur identique

## Avantages
✅ Visibilité en temps réel sur le processus d'import  
✅ Estimation du temps restant grâce au compteur de batches  
✅ Détection rapide des erreurs  
✅ Retour utilisateur immédiat et rassurant  
✅ Cohérence avec l'interface de synchronisation Discogs  

## Tests Recommandés
1. Import avec limite (ex: 500 tracks)
2. Import complet (tous les scrobbles)
3. Import avec connexion réseau instable
4. Comportement en cas d'erreur
5. Refresh de la page pendant l'import
