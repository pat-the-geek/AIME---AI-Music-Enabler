import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Stack,
  Divider,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Snackbar,
} from '@mui/material'
import {
  PlayArrow,
  Stop,
  CloudDownload,
  Sync,
} from '@mui/icons-material'
import apiClient from '@/api/client'

export default function Settings() {
  const [importLimit, setImportLimit] = useState(1000)
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })
  
  const queryClient = useQueryClient()

  const { data: trackerStatus, isLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['tracker-status'],
    queryFn: async () => {
      const response = await apiClient.get('/services/tracker/status')
      return response.data
    },
    refetchInterval: 5000, // Rafraîchir toutes les 5 secondes
  })

  const startTrackerMutation = useMutation({
    mutationFn: () => apiClient.post('/services/tracker/start'),
    onSuccess: () => {
      refetchStatus()
      setSnackbar({ open: true, message: 'Tracker démarré avec succès!', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur: ${error.message}`, severity: 'error' })
    },
  })

  const stopTrackerMutation = useMutation({
    mutationFn: () => apiClient.post('/services/tracker/stop'),
    onSuccess: () => {
      refetchStatus()
      setSnackbar({ open: true, message: 'Tracker arrêté', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur: ${error.message}`, severity: 'error' })
    },
  })

  const importHistoryMutation = useMutation({
    mutationFn: async (limit: number) => {
      const response = await apiClient.post(`/services/lastfm/import-history?limit=${limit}&skip_existing=true`, null, {
        timeout: 600000, // 10 minutes
      })
      return response.data
    },
    onSuccess: (data) => {
      setImportDialogOpen(false)
      queryClient.invalidateQueries({ queryKey: ['history'] })
      setSnackbar({
        open: true,
        message: `✅ Import terminé! ${data.tracks_imported} tracks importés, ${data.albums_enriched} albums enrichis`,
        severity: 'success'
      })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur import: ${error.message}`, severity: 'error' })
    },
  })

  const syncDiscogsMatch = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/services/discogs/sync?limit=10')
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['albums'] })
      setSnackbar({
        open: true,
        message: `✅ ${data.synced_albums} albums synchronisés depuis Discogs`,
        severity: 'success'
      })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur sync: ${error.message}`, severity: 'error' })
    },
  })

  const handleStartImport = () => {
    importHistoryMutation.mutate(importLimit)
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Paramètres
      </Typography>

      {/* Tracker Last.fm */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            🎵 Tracker Last.fm
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          {trackerStatus?.running ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              ✅ Le tracker est actif (intervalle: {trackerStatus.interval_seconds}s)
              {trackerStatus.last_track && (
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Dernier track: {trackerStatus.last_track}
                </Typography>
              )}
            </Alert>
          ) : (
            <Alert severity="warning" sx={{ mb: 2 }}>
              ⏸️ Le tracker est arrêté - Aucune nouvelle écoute n'est enregistrée
            </Alert>
          )}

          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              onClick={() => trackerStatus?.running ? stopTrackerMutation.mutate() : startTrackerMutation.mutate()}
              disabled={startTrackerMutation.isPending || stopTrackerMutation.isPending}
              startIcon={trackerStatus?.running ? <Stop /> : <PlayArrow />}
              color={trackerStatus?.running ? 'error' : 'success'}
            >
              {trackerStatus?.running ? 'Arrêter' : 'Démarrer'} le Tracker
            </Button>
            
            <Button
              variant="outlined"
              onClick={() => refetchStatus()}
              disabled={startTrackerMutation.isPending || stopTrackerMutation.isPending}
            >
              Actualiser le statut
            </Button>
          </Stack>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            💡 Le tracker surveille Last.fm toutes les {trackerStatus?.interval_seconds || 120} secondes 
            pour détecter les nouvelles écoutes et les enregistrer automatiquement.
          </Typography>
        </CardContent>
      </Card>

      {/* Import Historique */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            📥 Import Historique Last.fm
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          <Alert severity="info" sx={{ mb: 2 }}>
            Importez votre historique d'écoute existant depuis Last.fm. 
            Cette opération peut prendre plusieurs minutes selon le nombre de tracks.
          </Alert>

          <Button
            variant="contained"
            onClick={() => setImportDialogOpen(true)}
            disabled={importHistoryMutation.isPending}
            startIcon={importHistoryMutation.isPending ? <CircularProgress size={20} /> : <CloudDownload />}
            color="primary"
          >
            Importer l'Historique
          </Button>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            💡 L'import récupère vos écoutes passées et enrichit automatiquement les albums 
            avec Spotify et l'IA. Les doublons sont automatiquement ignorés.
          </Typography>
        </CardContent>
      </Card>

      {/* Synchronisation Discogs */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            💿 Synchronisation Discogs
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          <Alert severity="info" sx={{ mb: 2 }}>
            Synchronisez votre collection Discogs pour enrichir la base de données.
          </Alert>

          <Button
            variant="contained"
            onClick={() => syncDiscogsMatch.mutate()}
            disabled={syncDiscogsMatch.isPending}
            startIcon={syncDiscogsMatch.isPending ? <CircularProgress size={20} /> : <Sync />}
            color="secondary"
          >
            Synchroniser Discogs
          </Button>
        </CardContent>
      </Card>

      {/* À propos */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            ℹ️ À propos
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          <Stack spacing={1}>
            <Typography variant="body2">
              <strong>AIME - AI Music Enabler</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Version 4.0.0 - React + FastAPI
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Application de suivi et analyse d'écoute musicale avec enrichissement IA
            </Typography>
          </Stack>
        </CardContent>
      </Card>

      {/* Dialog Import */}
      <Dialog open={importDialogOpen} onClose={() => !importHistoryMutation.isPending && setImportDialogOpen(false)}>
        <DialogTitle>Importer l'historique Last.fm</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="warning" sx={{ mb: 3 }}>
              ⚠️ L'import peut prendre plusieurs minutes. Ne fermez pas cette fenêtre pendant l'opération.
            </Alert>

            <TextField
              fullWidth
              type="number"
              label="Nombre de tracks à importer"
              value={importLimit}
              onChange={(e) => setImportLimit(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={importHistoryMutation.isPending}
              helperText="Last.fm limite à 200 tracks par requête. L'import se fera par batches."
              sx={{ mb: 2 }}
            />

            {importHistoryMutation.isPending && (
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Import en cours... Cela peut prendre quelques minutes.
                </Typography>
                <LinearProgress />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)} disabled={importHistoryMutation.isPending}>
            Annuler
          </Button>
          <Button
            variant="contained"
            onClick={handleStartImport}
            disabled={importHistoryMutation.isPending}
            startIcon={importHistoryMutation.isPending ? <CircularProgress size={20} /> : <CloudDownload />}
          >
            {importHistoryMutation.isPending ? 'Import en cours...' : 'Démarrer l\'Import'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
