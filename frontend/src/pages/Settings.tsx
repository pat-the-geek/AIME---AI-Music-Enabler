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
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  PlayArrow,
  Stop,
  CloudDownload,
  Sync,
} from '@mui/icons-material'
import apiClient from '@/api/client'
import { useRoon } from '@/contexts/RoonContext'

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
  const [importLimit, setImportLimit] = useState<number | null>(null) // null = import ALL
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })
  const [roonServer, setRoonServer] = useState('')
  const [testingRoonConnection, setTestingRoonConnection] = useState(false)
  const [maxFilesPerType, setMaxFilesPerType] = useState(5)
  
  const queryClient = useQueryClient()
  const { enabled: roonEnabled, available: roonAvailable, zone, setZone } = useRoon()

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
  useQuery({
    queryKey: ['roon-config'],
    queryFn: async () => {
      const response = await apiClient.get('/services/roon/config')
      const data = response.data
      if (data?.server) {
        setRoonServer(data.server)
      }
      return data
    },
  })

  // Récupérer le statut de connexion Roon (avec rafraîchissement)
  const { data: roonStatus, refetch: refetchRoonStatus } = useQuery({
    queryKey: ['roon-status'],
    queryFn: async () => {
      const response = await apiClient.get('/services/roon/status')
      return response.data
    },
    refetchInterval: 5000, // Rafraîchir toutes les 5 secondes
  })

  // Récupérer les zones Roon disponibles
  const { data: roonZones } = useQuery({
    queryKey: ['roon-zones'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/roon/zones')
      return response.data
    },
    enabled: roonEnabled && roonAvailable,
  })

  // Récupérer la configuration du scheduler
  const { data: schedulerConfig, refetch: refetchScheduler } = useQuery({
    queryKey: ['scheduler-config'],
    queryFn: async () => {
      const response = await apiClient.get('/services/scheduler/config')
      const data = response.data
      if (data?.max_files_per_type) {
        setMaxFilesPerType(data.max_files_per_type)
      }
      return data
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
    mutationFn: async (limit: number | null) => {
      // Si limit est null, on n'ajoute pas le paramètre limit (backend importera TOUS les scrobbles)
      // skip_existing par défaut: false (pour importer complètement)
      const url = limit === null ? `/services/lastfm/import-history?skip_existing=false` : `/services/lastfm/import-history?limit=${limit}&skip_existing=false`
      const response = await apiClient.post(url, null, {
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
      queryClient.invalidateQueries({ queryKey: ['roon-status'] })
      queryClient.invalidateQueries({ queryKey: ['all-services-status'] })
      refetchRoonStatus()
      setSnackbar({
        open: true,
        message: '✅ Configuration Roon sauvegardée. Vérifiez Roon → Settings → Extensions',
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
          severity: 'error'
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
      setSnackbar({ open: true, message: '⚠️ Veuillez saisir une adresse serveur', severity: 'error' })
      return
    }
    setTestingRoonConnection(true)
    await testRoonConnectionMutation.mutateAsync(roonServer)
    setTestingRoonConnection(false)
  }

  const updateSchedulerConfigMutation = useMutation({
    mutationFn: async (maxFiles: number) => {
      const response = await apiClient.patch('/services/scheduler/config', null, {
        params: { max_files_per_type: maxFiles }
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler-config'] })
      setSnackbar({
        open: true,
        message: `✅ Configuration mise à jour! Limite: ${maxFilesPerType} fichiers par type`,
        severity: 'success'
      })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur: ${error.message}`, severity: 'error' })
    },
  })

  const handleSaveRoonConfig = () => {
    if (!roonServer.trim()) {
      setSnackbar({ open: true, message: '⚠️ Veuillez saisir une adresse serveur', severity: 'error' })
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
          
          {roonStatus?.configured && roonStatus?.connected && (
            roonStatus.authorized ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                ✅ Extension autorisée dans Roon ! ({roonStatus.zones_count} zone(s) détectée(s))
              </Alert>
            ) : (
              <Alert severity="warning" sx={{ mb: 2 }}>
                ⏳ Extension connectée mais en attente d'autorisation. 
                Allez dans Roon → Settings → Extensions pour autoriser "AIME - AI Music Enabler".
              </Alert>
            )
          )}
          
          {roonStatus?.configured && !roonStatus?.connected && (
            <Alert severity="error" sx={{ mb: 2 }}>
              ❌ Impossible de se connecter au serveur Roon. Vérifiez l'adresse et que Roon Core est démarré.
            </Alert>
          )}
          
          {!roonStatus?.configured && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Configurez l'adresse de votre serveur Roon pour activer le tracking local. 
              L'extension doit être autorisée dans les paramètres Roon.
            </Alert>
          )}

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
              
              {roonStatus?.configured && (
                <Button
                  variant="text"
                  onClick={() => refetchRoonStatus()}
                  size="small"
                >
                  Actualiser
                </Button>
              )}
            </Stack>

            <Typography variant="caption" color="text.secondary">
              💡 Après avoir enregistré, l'extension "AIME - AI Music Enabler" devrait apparaître dans 
              Roon → Settings → Extensions. Autorisez-la pour activer le tracking.
            </Typography>
          </Stack>
        </CardContent>
      </Card>

      {/* Zone Roon pour le contrôle */}
      {roonEnabled && roonAvailable && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              🎛️ Contrôle Roon
            </Typography>
            
            <Divider sx={{ mb: 2 }} />
            
            <Alert severity="info" sx={{ mb: 2 }}>
              Sélectionnez la zone Roon à utiliser pour le contrôle de lecture depuis l'application.
            </Alert>

            <FormControl fullWidth>
              <InputLabel>Zone de lecture</InputLabel>
              <Select
                value={zone}
                label="Zone de lecture"
                onChange={(e) => setZone(e.target.value)}
              >
                {roonZones?.zones?.map((zoneName: string) => (
                  <MenuItem key={zoneName} value={zoneName}>
                    {zoneName}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {zone && (
              <Typography variant="caption" color="success.main" sx={{ display: 'block', mt: 2 }}>
                ✅ Zone sélectionnée : {zone}
              </Typography>
            )}

            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
              💡 Cette zone sera utilisée lorsque vous cliquez sur "Écouter sur Roon" dans le Journal ou la Timeline.
            </Typography>
          </CardContent>
        </Card>
      )}

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

          {roonStatus?.configured && !roonStatus?.connected && (
            <Alert severity="error" sx={{ mb: 2 }}>
              ❌ Non connecté au serveur Roon ({roonStatus?.server || 'non configuré'})
            </Alert>
          )}

          {roonStatus?.connected && (
            <Alert severity="info" sx={{ mb: 2 }}>
              📡 Connecté au serveur Roon - {roonStatus?.zones_count || 0} zone(s) disponible(s)
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
                📋 Tâches Planifiées Configuration:
              </Typography>
              {schedulerConfig?.tasks && schedulerConfig.tasks.map((task: any) => {
                const jobStatus = schedulerStatus?.jobs?.find((j: any) => j.id === task.name)
                const isEnabled = task.enabled !== false
                
                return (
                  <Alert key={task.name} severity={isEnabled ? "info" : "warning"} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                      <Box>
                        <Typography variant="body2">
                          <strong>{task.name}</strong>
                          {task.description && (
                            <Typography variant="caption" display="block" color="text.secondary">
                              {task.description}
                            </Typography>
                          )}
                        </Typography>
                        <Typography variant="caption" component="div">
                          {task.time ? `⏰ ${task.time}` : `📅 Toutes les ${task.frequency}${task.unit === 'day' ? 'j' : task.unit === 'week' ? 'sem' : 'mois'}`}
                        </Typography>
                        {jobStatus?.next_run && (
                          <Typography variant="caption" display="block" color="success.main">
                            Prochaine: {new Date(jobStatus.next_run).toLocaleString('fr-FR')}
                          </Typography>
                        )}
                      </Box>
                      <Chip
                        size="small"
                        label={isEnabled ? '✅ Activée' : '⏸️ Désactivée'}
                        color={isEnabled ? 'success' : 'error'}
                      />
                    </Box>
                  </Alert>
                )
              })}
            </Box>
          )}

          {!schedulerConfig?.tasks && schedulerStatus?.jobs && schedulerStatus.jobs.length > 0 && (
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
            💡 <strong>Nouvelles tâches automatiques quotidiennes:</strong>
            <br/>
            🎋 <strong>6h00</strong> - Génération haikus pour 5 albums aléatoires
            <br/>
            📝 <strong>8h00</strong> - Export collection en markdown
            <br/>
            📊 <strong>10h00</strong> - Export collection en JSON
            <br/>
            Les fichiers générés sont sauvegardés dans le répertoire "Scheduled Output" avec des noms horodatés.
          </Typography>

          <Divider sx={{ my: 3 }} />

          {/* Configuration fichiers générés */}
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            ⚙️ Configuration des fichiers générés
          </Typography>

          <Box sx={{ mt: 2, p: 2, backgroundColor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
            <Typography variant="body2" gutterBottom>
              Nombre maximum de fichiers à conserver par type (haikus, markdown, JSON):
            </Typography>
            
            <Stack direction="row" spacing={2} sx={{ mt: 2, alignItems: 'center' }}>
              <TextField
                type="number"
                value={maxFilesPerType}
                onChange={(e) => setMaxFilesPerType(Math.max(1, parseInt(e.target.value) || 1))}
                inputProps={{ min: 1, max: 50 }}
                variant="outlined"
                size="small"
                sx={{ width: 100 }}
                label="Limite"
              />
              
              <Button
                variant="contained"
                color="primary"
                onClick={() => updateSchedulerConfigMutation.mutate(maxFilesPerType)}
                disabled={updateSchedulerConfigMutation.isPending}
              >
                {updateSchedulerConfigMutation.isPending ? 'Mise à jour...' : 'Appliquer'}
              </Button>

              <Typography variant="caption" color="text.secondary">
                Les {maxFilesPerType} derniers fichiers de chaque type seront conservés
              </Typography>
            </Stack>
          </Box>
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
      <Dialog open={importDialogOpen} onClose={() => !importHistoryMutation.isPending && setImportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Importer l'historique Last.fm</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="warning" sx={{ mb: 3 }}>
              ⚠️ L'import peut prendre plusieurs minutes. Ne fermez pas cette fenêtre pendant l'opération.
            </Alert>

            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
              Choisissez le nombre de scrobbles à importer:
            </Typography>

            <Stack spacing={2} sx={{ mb: 3 }}>
              <Button
                variant={importLimit === null ? "contained" : "outlined"}
                onClick={() => setImportLimit(null)}
                disabled={importHistoryMutation.isPending}
                sx={{ justifyContent: 'flex-start' }}
              >
                🌟 Importer TOUS les scrobbles (par défaut)
              </Button>
              <Button
                variant={importLimit === 1000 ? "contained" : "outlined"}
                onClick={() => setImportLimit(1000)}
                disabled={importHistoryMutation.isPending}
                sx={{ justifyContent: 'flex-start' }}
              >
                ⚡ Importer les 1000 derniers scrobbles
              </Button>
              <Button
                variant={importLimit === 500 ? "contained" : "outlined"}
                onClick={() => setImportLimit(500)}
                disabled={importHistoryMutation.isPending}
                sx={{ justifyContent: 'flex-start' }}
              >
                📊 Importer les 500 derniers scrobbles
              </Button>
            </Stack>

            <Divider sx={{ my: 2 }} />

            <TextField
              fullWidth
              type="number"
              label="Ou entrez une limite personnalisée"
              value={importLimit === null ? '' : importLimit}
              onChange={(e) => {
                const val = e.target.value.trim()
                setImportLimit(val === '' ? null : Math.max(1, parseInt(val) || 1))
              }}
              disabled={importHistoryMutation.isPending}
              placeholder="Laissez vide pour tout importer"
              helperText="Last.fm limite à 200 tracks par requête. L'import se fera par batches automatiquement."
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
