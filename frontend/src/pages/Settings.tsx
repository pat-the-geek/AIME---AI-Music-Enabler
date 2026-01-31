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

// Helper pour formater les dates
const formatLastActivity = (isoDate: string | null | undefined): string => {
  if (!isoDate) return 'Jamais'
  try {
    const date = new Date(isoDate)
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return 'Date invalide'
  }
}

export default function Settings() {
  const [importLimit, setImportLimit] = useState(1000)
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })
  const [roonServer, setRoonServer] = useState('')
  const [testingRoonConnection, setTestingRoonConnection] = useState(false)
  
  const queryClient = useQueryClient()

  // Récupérer tous les statuts en une seule requête
  const { data: allServicesStatus, isLoading, refetch: refetchAllStatus } = useQuery({
    queryKey: ['all-services-status'],
    queryFn: async () => {
      const response = await apiClient.get('/services/status/all')
      return response.data
    },
    refetchInterval: 5000, // Rafraîchir toutes les 5 secondes
  })

  // Récupérer la configuration Roon
  const { data: roonConfig } = useQuery({
    queryKey: ['roon-config'],
    queryFn: async () => {
      const response = await apiClient.get('/services/roon/config')
      return response.data
    },
    onSuccess: (data) => {
      if (data?.server) {
        setRoonServer(data.server)
      }
    },
  })

  // Pour la compatibilité avec le code existant
  const trackerStatus = allServicesStatus?.tracker
  const schedulerStatus = allServicesStatus?.scheduler
  const manualOps = allServicesStatus?.manual_operations

  const refetchStatus = refetchAllStatus

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

  const saveRoonConfigMutation = useMutation({
    mutationFn: async (server: string) => {
      const response = await apiClient.post('/services/roon/config', { server })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roon-config'] })
      queryClient.invalidateQueries({ queryKey: ['all-services-status'] })
      setSnackbar({
        open: true,
        message: '✅ Configuration Roon sauvegardée',
        severity: 'success'
      })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur: ${error.message}`, severity: 'error' })
    },
  })

  const testRoonConnectionMutation = useMutation({
    mutationFn: async (server: string) => {
      const response = await apiClient.post('/services/roon/test-connection', { server })
      return response.data
    },
    onSuccess: (data) => {
      if (data.connected) {
        setSnackbar({
          open: true,
          message: `✅ Connexion réussie ! ${data.zones_found || 0} zone(s) détectée(s)`,
          severity: 'success'
        })
      } else {
        setSnackbar({
          open: true,
          message: `⚠️ Impossible de se connecter: ${data.error || 'Erreur inconnue'}`,
          severity: 'warning'
        })
      }
    },
    onError: (error: any) => {
      setSnackbar({ 
        open: true, 
        message: `❌ Erreur de connexion: ${error.response?.data?.detail || error.message}`, 
        severity: 'error' 
      })
    },
  })

  const handleTestRoonConnection = async () => {
    if (!roonServer.trim()) {
      setSnackbar({ open: true, message: '⚠️ Veuillez saisir une adresse serveur', severity: 'warning' })
      return
    }
    setTestingRoonConnection(true)
    await testRoonConnectionMutation.mutateAsync(roonServer)
    setTestingRoonConnection(false)
  }

  const handleSaveRoonConfig = () => {
    if (!roonServer.trim()) {
      setSnackbar({ open: true, message: '⚠️ Veuillez saisir une adresse serveur', severity: 'warning' })
      return
    }
    saveRoonConfigMutation.mutate(roonServer)
  }

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

          <Stack spacing={1} sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              💡 Le tracker surveille Last.fm toutes les {trackerStatus?.interval_seconds || 120} secondes 
              pour détecter les nouvelles écoutes et les enregistrer automatiquement.
            </Typography>
            
            {trackerStatus?.last_poll_time && (
              <Typography variant="caption" color="text.secondary">
                🕐 Dernière vérification : {new Date(trackerStatus.last_poll_time).toLocaleString('fr-FR', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </Typography>
            )}
            
            {trackerStatus?.last_track && (
              <Typography variant="caption" color="primary.main">
                🎵 Dernier morceau détecté : {trackerStatus.last_track}
              </Typography>
            )}
          </Stack>
        </CardContent>
      </Card>
      {/* Configuration Roon */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            🔧 Configuration Roon
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          <Alert severity="info" sx={{ mb: 2 }}>
            Configurez l'adresse de votre serveur Roon pour activer le tracking local. 
            L'extension doit être autorisée dans les paramètres Roon.
          </Alert>

          <Stack spacing={2}>
            <TextField
              label="Adresse du serveur Roon"
              placeholder="192.168.1.100 ou roon-core.local"
              value={roonServer}
              onChange={(e) => setRoonServer(e.target.value)}
              fullWidth
              helperText="Entrez l'adresse IP ou le hostname de votre Roon Core"
            />

            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                onClick={handleTestRoonConnection}
                disabled={testingRoonConnection || !roonServer.trim()}
                startIcon={testingRoonConnection ? <CircularProgress size={20} /> : null}
              >
                {testingRoonConnection ? 'Test en cours...' : 'Tester la connexion'}
              </Button>

              <Button
                variant="contained"
                onClick={handleSaveRoonConfig}
                disabled={saveRoonConfigMutation.isPending || !roonServer.trim()}
                color="primary"
              >
                Enregistrer
              </Button>
            </Stack>

            <Typography variant="caption" color="text.secondary">
              💡 Après avoir sauvegardé, allez dans les paramètres de Roon (Settings → Extensions) 
              pour autoriser l'extension "AIME - AI Music Enabler".
            </Typography>
          </Stack>
        </CardContent>
      </Card>
      {/* Tracker Roon */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            🎵 Tracker Roon
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          {isLoading ? (
            <CircularProgress />
          ) : allServicesStatus?.roon_tracker?.running ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              ✅ Le tracker Roon est actif et surveille vos écoutes
            </Alert>
          ) : (
            <Alert severity="warning" sx={{ mb: 2 }}>
              ⏸️ Le tracker Roon est arrêté - Aucune nouvelle écoute n'est enregistrée
            </Alert>
          )}

          {allServicesStatus?.roon_tracker && !allServicesStatus.roon_tracker.connected && (
            <Alert severity="error" sx={{ mb: 2 }}>
              ❌ Non connecté au serveur Roon ({allServicesStatus.roon_tracker.server || 'non configuré'})
            </Alert>
          )}

          {allServicesStatus?.roon_tracker?.connected && (
            <Alert severity="info" sx={{ mb: 2 }}>
              📡 Connecté au serveur Roon - {allServicesStatus.roon_tracker.zones_count || 0} zone(s) disponible(s)
            </Alert>
          )}

          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              onClick={() => {
                const action = allServicesStatus?.roon_tracker?.running ? 'stop' : 'start'
                apiClient.post(`/services/roon-tracker/${action}`).then(() => {
                  refetchStatus()
                  setSnackbar({
                    open: true,
                    message: `Tracker Roon ${action === 'start' ? 'démarré' : 'arrêté'}!`,
                    severity: 'success'
                  })
                }).catch((error) => {
                  setSnackbar({
                    open: true,
                    message: `Erreur: ${error.response?.data?.detail || error.message}`,
                    severity: 'error'
                  })
                })
              }}
              disabled={!allServicesStatus?.roon_tracker?.connected}
              startIcon={allServicesStatus?.roon_tracker?.running ? <Stop /> : <PlayArrow />}
              color={allServicesStatus?.roon_tracker?.running ? 'error' : 'success'}
            >
              {allServicesStatus?.roon_tracker?.running ? 'Arrêter' : 'Démarrer'} le Tracker
            </Button>
            
            <Button
              variant="outlined"
              onClick={() => refetchStatus()}
            >
              Actualiser le statut
            </Button>
          </Stack>

          <Stack spacing={1} sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              💡 Le tracker surveille Roon toutes les {allServicesStatus?.roon_tracker?.interval_seconds || 120} secondes 
              pour détecter les nouvelles écoutes et les enregistrer automatiquement.
            </Typography>
            
            {allServicesStatus?.roon_tracker?.last_poll_time && (
              <Typography variant="caption" color="text.secondary">
                🕐 Dernière vérification : {formatLastActivity(allServicesStatus.roon_tracker.last_poll_time)}
              </Typography>
            )}
            
            {allServicesStatus?.roon_tracker?.last_track && (
              <Typography variant="caption" color="primary.main">
                🎵 Dernier morceau détecté : {allServicesStatus.roon_tracker.last_track}
              </Typography>
            )}
          </Stack>
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

          {manualOps?.lastfm_import && (
            <Typography variant="caption" color="success.main" sx={{ display: 'block', mb: 2 }}>
              🕐 Dernière importation : {formatLastActivity(manualOps.lastfm_import)}
            </Typography>
          )}

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

          {manualOps?.discogs_sync && (
            <Typography variant="caption" color="success.main" sx={{ display: 'block', mb: 2 }}>
              🕐 Dernière synchronisation : {formatLastActivity(manualOps.discogs_sync)}
            </Typography>
          )}

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

      {/* Scheduler de tâches optimisé */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            📅 Scheduler Intelligent (IA)
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          {schedulerStatus?.running ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              ✅ Le scheduler est actif avec {schedulerStatus.job_count} tâches planifiées
            </Alert>
          ) : (
            <Alert severity="warning" sx={{ mb: 2 }}>
              ⏸️ Le scheduler est arrêté - Les tâches automatiques ne s'exécutent pas
            </Alert>
          )}

          {schedulerStatus?.jobs && schedulerStatus.jobs.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Tâches planifiées:
              </Typography>
              {schedulerStatus.jobs.map((job: any) => (
                <Alert key={job.id} severity="info" sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    <strong>{job.id}</strong>
                  </Typography>
                  <Typography variant="caption" component="div">
                    Prochaine exécution: {job.next_run ? new Date(job.next_run).toLocaleString('fr-FR') : 'Non planifiée'}
                  </Typography>
                  {job.last_execution && (
                    <Typography variant="caption" color="success.main" component="div">
                      🕐 Dernière exécution : {formatLastActivity(job.last_execution)}
                    </Typography>
                  )}
                </Alert>
              ))}
            </Box>
          )}

          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              onClick={() => {
                const action = schedulerStatus?.running ? 'stop' : 'start'
                apiClient.post(`/services/scheduler/${action}`).then(() => {
                  refetchScheduler()
                  setSnackbar({
                    open: true,
                    message: `Scheduler ${action === 'start' ? 'démarré' : 'arrêté'}!`,
                    severity: 'success'
                  })
                })
              }}
              startIcon={schedulerStatus?.running ? <Stop /> : <PlayArrow />}
              color={schedulerStatus?.running ? 'error' : 'success'}
            >
              {schedulerStatus?.running ? 'Arrêter' : 'Démarrer'} le Scheduler
            </Button>
          </Stack>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            💡 Le scheduler exécute automatiquement des tâches optimisées par IA :
            enrichissement quotidien, génération de haïkus hebdomadaires, analyse mensuelle et optimisation des descriptions.
          </Typography>
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
