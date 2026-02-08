import { useState, useEffect } from 'react'
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
  Paper,
} from '@mui/material'
import {
  PlayArrow,
  Stop,
  CloudDownload,
  Sync,
  AutoAwesome,
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
  const [syncProgress, setSyncProgress] = useState<any>(null)
  const [lastfmImportProgress, setLastfmImportProgress] = useState<any>(null)
  const [normalizationDialogOpen, setNormalizationDialogOpen] = useState(false)
  const [simulationResults, setSimulationResults] = useState<any>(null)
  const [normalizationInProgress, setNormalizationInProgress] = useState(false)
  const [isLoadingSimulationResults, setIsLoadingSimulationResults] = useState(false)
  
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
  const roonConfigQuery = useQuery({
    queryKey: ['roon-config'],
    queryFn: async () => {
      const response = await apiClient.get('/services/roon/config')
      return response.data
    },
  })

  useEffect(() => {
    if (roonConfigQuery.data?.server) {
      setRoonServer(roonConfigQuery.data.server)
    }
  }, [roonConfigQuery.data?.server])

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
      const response = await apiClient.get('/playback/roon/zones')
      return response.data
    },
    enabled: roonEnabled && roonAvailable,
    refetchInterval: 10000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  })

  // Récupérer la configuration du scheduler
  const schedulerConfigQuery = useQuery({
    queryKey: ['scheduler-config'],
    queryFn: async () => {
      const response = await apiClient.get('/services/scheduler/config')
      return response.data
    },
  })

  const schedulerConfig = schedulerConfigQuery.data
  const refetchScheduler = schedulerConfigQuery.refetch

  useEffect(() => {
    if (schedulerConfig?.max_files_per_type) {
      setMaxFilesPerType(schedulerConfig.max_files_per_type)
    }
  }, [schedulerConfig?.max_files_per_type])

  // Récupérer le statut de normalisation Roon
  const { data: normalizationStatus, refetch: refetchNormalizationStatus } = useQuery({
    queryKey: ['normalization-status'],
    queryFn: async () => {
      const response = await apiClient.get('/services/roon/normalize/status')
      return response.data
    },
    refetchInterval: 5000,
  })

  // Récupérer les résultats de simulation
  const { data: normalizationSimulationResults } = useQuery({
    queryKey: ['normalization-simulation-results'],
    queryFn: async () => {
      const response = await apiClient.get('/services/roon/normalize/simulate-results')
      return response.data
    },
    enabled: normalizationDialogOpen,
    // Continuer le polling jusqu'à ce que asynchrone complété ou erreur
    refetchInterval: (data: any) => {
      // Si status est 'completed' ou 'error', ARRÊTER le polling (retourner undefined)
      if (data?.status === 'completed' || data?.status === 'error') {
        return undefined // ✓ Arrête le polling proprement
      }
      // Sinon, refetch toutes les 500ms
      return 500
    },
  })

  useEffect(() => {
    if (normalizationSimulationResults) {
      setSimulationResults(normalizationSimulationResults)
      // Arrêter le loading dès que les résultats arrivent
      if (normalizationSimulationResults.status === 'completed' || normalizationSimulationResults.status === 'error') {
        setIsLoadingSimulationResults(false)
      }
    }
  }, [normalizationSimulationResults])

  // Récupérer les résultats d'optimisation IA
  const { data: optimizationResults, refetch: refetchOptimization } = useQuery({
    queryKey: ['scheduler-optimization-results'],
    queryFn: async () => {
      const response = await apiClient.get('/services/scheduler/optimization-results')
      return response.data
    },
    refetchInterval: 60000, // Rafraîchir toutes les minutes
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
      
      // Polling pour suivre la progression
      return new Promise((resolve, reject) => {
        const pollInterval = setInterval(async () => {
          try {
            const progressResponse = await apiClient.get('/services/lastfm/import/progress')
            const progress = progressResponse.data
            
            // Mettre à jour l'état de progression
            setLastfmImportProgress(progress)
            
            // Vérifier si terminé
            if (progress.status === 'completed') {
              clearInterval(pollInterval)
              setLastfmImportProgress(null)
              resolve(progress)
            } else if (progress.status === 'error') {
              clearInterval(pollInterval)
              setLastfmImportProgress(null)
              reject(new Error('Erreur lors de l\'importation'))
            }
          } catch (error) {
            clearInterval(pollInterval)
            setLastfmImportProgress(null)
            reject(error)
          }
        }, 1000) // Vérifier toutes les secondes
        
        // Timeout de sécurité
        setTimeout(() => {
          clearInterval(pollInterval)
          setLastfmImportProgress(null)
          reject(new Error('Timeout de l\'importation'))
        }, 600000)
      })
    },
    onSuccess: (data: any) => {
      setImportDialogOpen(false)
      queryClient.invalidateQueries({ queryKey: ['history'] })
      setSnackbar({
        open: true,
        message: `✅ Import terminé! ${data.imported} tracks importés, ${data.skipped} ignorés`,
        severity: 'success'
      })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur import: ${error.message}`, severity: 'error' })
    },
  })

  const syncDiscogsMatch = useMutation({
    mutationFn: async () => {
      // Démarrer la synchronisation en arrière-plan
      const response = await apiClient.post('/services/discogs/sync', null, {
        timeout: 600000 // 10 minutes
      })
      
      // Polling pour suivre la progression
      return new Promise((resolve, reject) => {
        const pollInterval = setInterval(async () => {
          try {
            const progressResponse = await apiClient.get('/services/discogs/sync/progress')
            const progress = progressResponse.data
            
            // Mettre à jour l'état de progression
            setSyncProgress(progress)
            
            // Vérifier si terminé
            if (progress.status === 'completed') {
              clearInterval(pollInterval)
              setSyncProgress(null)
              resolve(progress)
            } else if (progress.status === 'error') {
              clearInterval(pollInterval)
              setSyncProgress(null)
              reject(new Error(progress.current_album))
            }
          } catch (error) {
            clearInterval(pollInterval)
            setSyncProgress(null)
            reject(error)
          }
        }, 1000) // Vérifier toutes les secondes
        
        // Timeout de sécurité
        setTimeout(() => {
          clearInterval(pollInterval)
          setSyncProgress(null)
          reject(new Error('Timeout de synchronisation'))
        }, 600000)
      })
    },
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['albums'] })
      setSnackbar({
        open: true,
        message: `✅ ${data.synced} albums synchronisés depuis Discogs (${data.skipped} déjà présents, ${data.errors} erreurs)`,
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

  const simulateNormalizationMutation = useMutation({
    mutationFn: async (limit?: number) => {
      // Réinitialiser l'état de loading
      setIsLoadingSimulationResults(true)
      setSimulationResults(null) // Effacer les résultats précédents
      
      // CRITIQUE: Reset COMPLET du cache React Query pour éviter les données stale
      // On ne peut pas juste invalider, il faut effacer les données du cache
      queryClient.setQueryData(['normalization-simulation-results'], {
        status: 'simulating',
        changes: { artists: [], albums: [] },
        stats: { artists_total: 0, artists_would_update: 0, albums_total: 0, albums_would_update: 0, no_matches: 0 },
        error: null
      })
      
      const response = await apiClient.post(
        `/services/roon/normalize/simulate`,
        {},
        { params: limit ? { limit } : {} }
      )
      return response.data
    },
    onSuccess: () => {
      setNormalizationDialogOpen(true)
      setSnackbar({
        open: true,
        message: '🔍 Simulation lancée en arrière-plan...',
        severity: 'success'
      })
    },
    onError: (error: any) => {
      setIsLoadingSimulationResults(false) // Arrêter le loading en cas d'erreur
      setSnackbar({ 
        open: true, 
        message: `Erreur simulation: ${error.response?.data?.detail || error.message}`, 
        severity: 'error' 
      })
    },
  })

  const normalizeWithRoonMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/services/roon/normalize', {})
      return response.data
    },
    onSuccess: () => {
      // Ne pas fermer tout de suite - garder le dialog ouvert pour montrer que c'est en cours
      setSnackbar({
        open: true,
        message: '⏳ Normalisation lancée en arrière-plan... (cela peut prendre quelques secondes)',
        severity: 'success'
      })
      
      // Attendre 2 secondes avant de fermer pour laisser le temps au backend
      setTimeout(() => {
        setNormalizationDialogOpen(false)
        setSimulationResults(null)
        setIsLoadingSimulationResults(false)
        
        // CRITIQUE: Invalider les caches React Query pour forcer le refretch des données mises à jour
        queryClient.invalidateQueries({ queryKey: ['artists'] })
        queryClient.invalidateQueries({ queryKey: ['albums'] })
        queryClient.invalidateQueries({ queryKey: ['history'] })
        
        refetchNormalizationStatus()
        
        setSnackbar({
          open: true,
          message: '✅ Normalisation appliquée! La bibliothèque a été mise à jour.',
          severity: 'success'
        })
      }, 2000)
    },
    onError: (error: any) => {
      setSnackbar({ 
        open: true, 
        message: `Erreur normalisation: ${error.response?.data?.detail || error.message}`, 
        severity: 'error' 
      })
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
                {roonZones?.zones?.map((zoneObj: { zone_id: string; name: string; state: string }) => (
                  <MenuItem key={zoneObj.zone_id} value={zoneObj.name}>
                    {zoneObj.name} ({zoneObj.state})
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

      {/* Scheduler - Tâches automatiques */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            📅 Scheduler - Tâches Automatiques
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          {isLoading ? (
            <CircularProgress />
          ) : schedulerStatus?.running ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              ✅ Le scheduler est actif et exécute les tâches planifiées
            </Alert>
          ) : (
            <Alert severity="warning" sx={{ mb: 2 }}>
              ⏸️ Le scheduler est arrêté - Aucune tâche automatique n'est exécutée
            </Alert>
          )}

          {schedulerStatus?.jobs && schedulerStatus.jobs.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
                📋 Tâches planifiées ({schedulerStatus.job_count}) :
              </Typography>
              <Stack spacing={2}>
                {schedulerStatus.jobs.map((job: any) => (
                  <Paper 
                    key={job.id} 
                    elevation={1} 
                    sx={{ 
                      p: 2, 
                      backgroundColor: '#f8f8f8',
                      border: '1px solid #d0d0d0',
                      borderRadius: '8px'
                    }}
                  >
                    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#2c3e50' }}>
                        {job.id === 'daily_enrichment' && '🔄 Enrichissement quotidien'}
                        {job.id === 'generate_haiku_scheduled' && '🎋 Génération de haïkus'}
                        {job.id === 'export_collection_markdown' && '📝 Export Markdown'}
                        {job.id === 'export_collection_json' && '💾 Export JSON'}
                        {job.id === 'weekly_haiku' && '🎋 Haïku hebdomadaire'}
                        {job.id === 'monthly_analysis' && '📊 Analyse mensuelle'}
                        {job.id === 'optimize_ai_descriptions' && '🤖 Optimisation IA'}
                        {job.id === 'generate_magazine_editions' && '📰 Génération de magazines'}
                        {job.id === 'sync_discogs_daily' && '💿 Sync Discogs'}
                        {!['daily_enrichment', 'generate_haiku_scheduled', 'export_collection_markdown', 
                            'export_collection_json', 'weekly_haiku', 'monthly_analysis', 
                            'optimize_ai_descriptions', 'generate_magazine_editions', 'sync_discogs_daily'].includes(job.id) && `📌 ${job.id}`}
                      </Typography>
                      <Chip 
                        label="Planifiée" 
                        size="small" 
                        color="primary"
                        sx={{ fontSize: '0.7rem' }}
                      />
                    </Stack>

                    {job.next_run && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        🕐 Prochaine exécution : {formatLastActivity(job.next_run)}
                      </Typography>
                    )}

                    {job.last_execution && (
                      <Typography variant="caption" color="success.main" sx={{ display: 'block' }}>
                        ✓ Dernière exécution : {formatLastActivity(job.last_execution)}
                      </Typography>
                    )}

                    {!job.last_execution && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Jamais exécutée
                      </Typography>
                    )}
                  </Paper>
                ))}
              </Stack>
            </Box>
          )}

          <Stack spacing={1} sx={{ mt: 3 }}>
            <Typography variant="caption" color="text.secondary">
              💡 Le scheduler exécute automatiquement des tâches comme l'enrichissement des albums, 
              la génération de haïkus, l'export de la collection et la création de magazines pré-générés.
            </Typography>
            
            {schedulerConfig && (
              <Typography variant="caption" color="text.secondary">
                📝 Configuration : {schedulerConfig.max_files_per_type || 5} fichiers maximum par type d'export
              </Typography>
            )}
          </Stack>

          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => refetchScheduler()}
            >
              Actualiser
            </Button>
            <Button
              variant="text"
              size="small"
              onClick={() => {
                apiClient.get('/services/scheduler/status').then((res) => {
                  setSnackbar({
                    open: true,
                    message: `Scheduler: ${res.data.running ? 'Actif' : 'Inactif'} - ${res.data.job_count || 0} tâches`,
                    severity: 'success'
                  })
                })
              }}
            >
              Vérifier le statut
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {/* Normalisation Roon */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            📚 Normalisation Roon
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          {!normalizationStatus?.roon_connected ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              ❌ Roon n'est pas connecté. Vérifiez votre configuration et le Bridge Roon.
            </Alert>
          ) : (
            <Alert severity="success" sx={{ mb: 2 }}>
              ✅ Roon est connecté et prêt pour la normalisation
            </Alert>
          )}

          <Typography variant="body2" sx={{ mb: 2 }}>
            Alignez les noms d'artistes et d'albums de votre base de données avec ceux de Roon 
            pour améliorer la compatibilité de lecture à 100%. Cette opération remplace les noms locaux 
            par les noms canoniques de Roon.
          </Typography>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <Button
              variant="contained"
              color="secondary"
              onClick={() => simulateNormalizationMutation.mutate(undefined)}
              disabled={!normalizationStatus?.roon_connected || simulateNormalizationMutation.isPending}
              startIcon={simulateNormalizationMutation.isPending ? <CircularProgress size={20} /> : undefined}
            >
              👁️ Prévisualiser tout
            </Button>
          </Stack>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            💡 Cliquez sur "Prévisualiser tout" pour vérifier l'impact complet. Vous pouvez toujours 
            appliquer après avoir révisé les changements.
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

          {manualOps?.lastfm_import && (
            <Typography variant="caption" color="success.main" sx={{ display: 'block', mb: 2 }}>
              🕐 Dernière importation : {formatLastActivity(manualOps.lastfm_import)}
            </Typography>
          )}

          {lastfmImportProgress && (lastfmImportProgress.status === 'running' || lastfmImportProgress.status === 'starting') && (
            <Box sx={{ mb: 2, p: 2, backgroundColor: 'background.paper', border: '1px solid', borderColor: 'primary.main', borderRadius: 1 }}>
              <Typography variant="body2" color="primary" gutterBottom>
                📥 Import en cours... Batch {lastfmImportProgress.current_batch}/{lastfmImportProgress.total_batches}
              </Typography>
              {lastfmImportProgress.total_batches > 0 && (
                <LinearProgress 
                  variant="determinate" 
                  value={(lastfmImportProgress.current_batch / lastfmImportProgress.total_batches) * 100} 
                  sx={{ mb: 1 }}
                />
              )}
              {lastfmImportProgress.total_batches === 0 && (
                <LinearProgress sx={{ mb: 1 }} />
              )}
              <Typography variant="caption" color="text.secondary" display="block">
                📊 Total: {lastfmImportProgress.total_scrobbles} scrobbles
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary">
                ✅ {lastfmImportProgress.imported} importés | ⏭️ {lastfmImportProgress.skipped} ignorés | ❌ {lastfmImportProgress.errors} erreurs
              </Typography>
            </Box>
          )}

          <Button
            variant="contained"
            onClick={() => setImportDialogOpen(true)}
            disabled={importHistoryMutation.isPending || (lastfmImportProgress && (lastfmImportProgress.status === 'running' || lastfmImportProgress.status === 'starting'))}
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

          {syncProgress && (syncProgress.status === 'running' || syncProgress.status === 'starting') && (
            <Box sx={{ mb: 2, p: 2, backgroundColor: 'background.paper', border: '1px solid', borderColor: 'primary.main', borderRadius: 1 }}>
              <Typography variant="body2" color="primary" gutterBottom>
                📥 Synchronisation en cours... {syncProgress.current}/{syncProgress.total}
              </Typography>
              {syncProgress.total > 0 && (
                <LinearProgress 
                  variant="determinate" 
                  value={(syncProgress.current / syncProgress.total) * 100} 
                  sx={{ mb: 1 }}
                />
              )}
              {syncProgress.total === 0 && (
                <LinearProgress sx={{ mb: 1 }} />
              )}
              <Typography variant="caption" color="text.secondary" display="block">
                {syncProgress.current_album}
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary">
                ✅ {syncProgress.synced} synchronisés | ⏭️ {syncProgress.skipped} ignorés | ❌ {syncProgress.errors} erreurs
              </Typography>
            </Box>
          )}

          <Button
            variant="contained"
            onClick={() => syncDiscogsMatch.mutate()}
            disabled={syncDiscogsMatch.isPending || (syncProgress && (syncProgress.status === 'running' || syncProgress.status === 'starting'))}
            startIcon={syncDiscogsMatch.isPending ? <CircularProgress size={20} /> : <Sync />}
            color="secondary"
          >
            Synchroniser Discogs
          </Button>
        </CardContent>
      </Card>

      {/* Enrichissement Euria + Spotify */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            🤖 Enrichissement Euria + Spotify
          </Typography>
          
          <Divider sx={{ mb: 2 }} />
          
          <Alert severity="success" sx={{ mb: 2 }}>
            ✨ Générez automatiquement des descriptions IA (Euria) et récupérez les images haute résolution (Spotify)
          </Alert>

          {manualOps?.enrichment && (
            <Typography variant="caption" color="success.main" sx={{ display: 'block', mb: 2 }}>
              🕐 Dernier enrichissement : {formatLastActivity(manualOps.enrichment)}
            </Typography>
          )}

          <Stack spacing={2} sx={{ mb: 2 }}>
            <Typography variant="body2">
              Cet enrichissement combine deux sources :
            </Typography>
            
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                📝 <strong>Euria IA</strong> - Génère des descriptions textuelles détaillées et naturelles
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ pl: 4, display: 'block', mb: 1 }}>
                Crée des synopsis personnalisés pour chaque album basés sur le titre, les artistes et l'année.
              </Typography>
              
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                🖼️ <strong>Spotify API</strong> - Récupère les images artiste haute résolution
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ pl: 4, display: 'block' }}>
                Améliore les couvertures d'album avec les images officielles de haute qualité de Spotify.
              </Typography>
            </Box>
          </Stack>

          <Button
            variant="contained"
            onClick={() => {
              setSnackbar({
                open: true,
                message: '🤖 Enrichissement démarré en arrière-plan avec Euria + Spotify...',
                severity: 'success'
              })
              apiClient.post('/services/discogs/enrich', null, {
                timeout: 1800000 // 30 minutes
              }).then(() => {
                // Polling pour suivre la progression
                const pollInterval = setInterval(async () => {
                  try {
                    const progressResponse = await apiClient.get('/services/discogs/enrich/progress')
                    const progress = progressResponse.data
                    
                    if (progress.status === 'completed') {
                      clearInterval(pollInterval)
                      setSnackbar({
                        open: true,
                        message: `✅ Enrichissement complété! ${progress.descriptions_added} descriptions + ${progress.images_added} images ajoutées`,
                        severity: 'success'
                      })
                      // Invalider les caches
                      queryClient.invalidateQueries({ queryKey: ['albums'] })
                      queryClient.invalidateQueries({ queryKey: ['artists'] })
                    } else if (progress.status === 'error') {
                      clearInterval(pollInterval)
                      setSnackbar({
                        open: true,
                        message: `❌ Erreur enrichissement: ${progress.errors} erreurs détectées`,
                        severity: 'error'
                      })
                    }
                  } catch (error) {
                    // Continue polling en cas d'erreur réseau temporaire
                  }
                }, 2000)
              }).catch((error) => {
                setSnackbar({
                  open: true,
                  message: `❌ Erreur: ${error.response?.data?.detail || error.message}`,
                  severity: 'error'
                })
              })
            }}
            disabled={syncProgress && (syncProgress.status === 'running' || syncProgress.status === 'starting')}
            startIcon={<AutoAwesome />}
            color="primary"
          >
            🤖 Enrichir avec Euria + Spotify
          </Button>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            💡 Nécessite les clés API Euria et Spotify configurées dans les secrets. Cela peut prendre plusieurs minutes selon le nombre d'albums.
          </Typography>
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

      {/* Résultats d'Optimisation IA */}
      {optimizationResults?.optimization?.status && optimizationResults.optimization.status !== 'NOT_AVAILABLE' && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              🤖 Résultats d'Optimisation IA
            </Typography>
            
            <Divider sx={{ mb: 2 }} />
            
            <Alert severity="success" sx={{ mb: 2 }}>
              ✅ Optimisation complétée le {new Date(optimizationResults.optimization.last_run).toLocaleString('fr-FR')}
            </Alert>

            {/* Configuration Actuelle */}
            <Box sx={{ mb: 3, p: 2, backgroundColor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="subtitle2" gutterBottom>
                📊 Configuration Optimisée Actuellement Appliquée:
              </Typography>
              <Stack spacing={1} sx={{ mt: 1 }}>
                <Typography variant="body2">
                  ⏰ <strong>Heure d'exécution:</strong> {optimizationResults.optimization?.current_configuration?.execution_time}
                </Typography>
                <Typography variant="body2">
                  📦 <strong>Taille des lots:</strong> {optimizationResults.optimization?.current_configuration?.batch_size} albums
                </Typography>
                <Typography variant="body2">
                  ⏱️ <strong>Délai d'attente:</strong> {optimizationResults.optimization?.current_configuration?.timeout_seconds}s
                </Typography>
                <Typography variant="body2">
                  📅 <strong>Planification:</strong> {optimizationResults.optimization?.current_configuration?.schedule}
                </Typography>
              </Stack>
            </Box>

            {/* État de la Base de Données */}
            {optimizationResults.optimization?.database_analysis && (
              <Box sx={{ mb: 3, p: 2, backgroundColor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom>
                  📈 État de la Base de Données:
                </Typography>
                <Stack spacing={1} sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    💿 <strong>Albums:</strong> {optimizationResults.optimization.database_analysis.total_albums}
                  </Typography>
                  <Typography variant="body2">
                    🎤 <strong>Artistes:</strong> {optimizationResults.optimization.database_analysis.total_artists}
                  </Typography>
                  <Typography variant="body2">
                    🎵 <strong>Morceaux:</strong> {optimizationResults.optimization.database_analysis.total_tracks}
                  </Typography>
                  <Typography variant="body2">
                    🖼️ <strong>Couvertures d'image:</strong> {optimizationResults.optimization.database_analysis.images_coverage_pct.toFixed(1)}% ({optimizationResults.optimization.database_analysis.images_missing} manquantes)
                  </Typography>
                  <Typography variant="body2">
                    📊 <strong>Écoutes (7j):</strong> {optimizationResults.optimization.database_analysis.listening_7days} ({optimizationResults.optimization.database_analysis.daily_avg.toFixed(1)}/jour)
                  </Typography>
                  <Typography variant="body2">
                    ⏰ <strong>Heures de pointe:</strong> {optimizationResults.optimization.database_analysis.peak_hours?.join(', ')}h
                  </Typography>
                </Stack>
              </Box>
            )}

            {/* Améliorations Apportées */}
            {optimizationResults.optimization?.improvements && (
              <Box sx={{ mb: 3, p: 2, backgroundColor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom>
                  ✨ Améliorations Appliquées:
                </Typography>
                <Stack spacing={2} sx={{ mt: 1 }}>
                  {optimizationResults.optimization.improvements.execution_time && (
                    <Box>
                      <Typography variant="body2" color="primary.main">
                        <strong>⏰ Heure d'exécution</strong>
                      </Typography>
                      <Typography variant="caption">
                        Avant: {optimizationResults.optimization.improvements.execution_time.before} → Après: <strong>{optimizationResults.optimization.improvements.execution_time.after}</strong>
                        <br/>
                        Raison: {optimizationResults.optimization.improvements.execution_time.reason}
                      </Typography>
                    </Box>
                  )}
                  {optimizationResults.optimization.improvements.timeout && (
                    <Box>
                      <Typography variant="body2" color="primary.main">
                        <strong>⏱️ Délai d'attente</strong>
                      </Typography>
                      <Typography variant="caption">
                        Avant: {optimizationResults.optimization.improvements.timeout.before}s → Après: <strong>{optimizationResults.optimization.improvements.timeout.after}s</strong>
                        <br/>
                        Raison: {optimizationResults.optimization.improvements.timeout.reason}
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </Box>
            )}

            {/* Recommandations IA */}
            {optimizationResults.optimization?.ai_recommendations && (
              <Box sx={{ mb: 3, p: 2, backgroundColor: '#e3f2fd', borderRadius: 1, border: '1px solid', borderColor: 'primary.light' }}>
                <Typography variant="subtitle2" gutterBottom sx={{ color: 'primary.main' }}>
                  💡 Recommandations IA (Euria):
                </Typography>
                <Stack spacing={1} sx={{ mt: 1 }}>
                  <Typography variant="caption">
                    <strong>Heure optimale:</strong> {optimizationResults.optimization.ai_recommendations.optimal_execution_time}
                  </Typography>
                  <Typography variant="caption">
                    <strong>Taille optimale des lots:</strong> {optimizationResults.optimization.ai_recommendations.optimal_batch_size}
                  </Typography>
                  <Typography variant="caption">
                    <strong>Délai d'attente recommandé:</strong> {optimizationResults.optimization.ai_recommendations.recommended_timeout}
                  </Typography>
                  {optimizationResults.optimization.ai_recommendations.enrichment_priority && (
                    <Typography variant="caption">
                      <strong>Priorité d'enrichissement:</strong> {optimizationResults.optimization.ai_recommendations.enrichment_priority.join(' → ')}
                    </Typography>
                  )}
                </Stack>
              </Box>
            )}

            {/* Prochaine Optimisation */}
            <Box sx={{ p: 2, backgroundColor: 'success.light', borderRadius: 1, border: '1px solid', borderColor: 'success.main' }}>
              <Typography variant="body2" sx={{ color: 'success.dark' }}>
                <strong>📅 Prochaine ré-optimisation IA:</strong><br/>
                {new Date(optimizationResults.optimization?.next_run).toLocaleString('fr-FR')}
                <br/>
                <Typography variant="caption" component="div" sx={{ mt: 1 }}>
                  Fréquence: {optimizationResults.optimization?.frequency}
                </Typography>
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

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

      {/* Dialog Normalisation */}
      <Dialog 
        open={normalizationDialogOpen} 
        onClose={() => {
          if (!simulateNormalizationMutation.isPending && !normalizeWithRoonMutation.isPending && !isLoadingSimulationResults) {
            setNormalizationDialogOpen(false)
            setIsLoadingSimulationResults(false)
            setSimulationResults(null) // Nettoyer les résultats quand on ferme
          }
        }}
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Résultats de la Normalisation Roon</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            {(simulateNormalizationMutation.isPending || isLoadingSimulationResults) && (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <CircularProgress sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  ⏳ Simulation en cours... Veuillez patienter.
                </Typography>
              </Box>
            )}

            {!isLoadingSimulationResults && normalizationSimulationResults?.status === 'completed' && normalizationSimulationResults?.changes && (
              <Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  ✅ Simulation terminée avec succès!
                </Alert>

                <Box sx={{ p: 2, backgroundColor: '#f5f5f5', borderRadius: 1, mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    📊 Résumé des changements prévus:
                  </Typography>
                  <Stack spacing={1} sx={{ mt: 1 }}>
                    <Typography variant="body2">
                      🎤 <strong>Artistes:</strong> {normalizationSimulationResults.changes.artists?.length || 0} changements
                    </Typography>
                    <Typography variant="body2">
                      💿 <strong>Albums:</strong> {normalizationSimulationResults.changes.albums?.length || 0} changements
                    </Typography>
                    {normalizationSimulationResults.stats && (
                      <>
                        <Typography variant="body2">
                          📈 <strong>Artistes affectés:</strong> {normalizationSimulationResults.stats.artists_would_update || 0}
                        </Typography>
                        <Typography variant="body2">
                          📈 <strong>Albums affectés:</strong> {normalizationSimulationResults.stats.albums_would_update || 0}
                        </Typography>
                      </>
                    )}
                  </Stack>
                </Box>

                {(normalizationSimulationResults.changes.artists?.length > 0 || normalizationSimulationResults.changes.albums?.length > 0) && (
                  <Box sx={{ maxHeight: 300, overflow: 'auto', border: '1px solid #ddd', borderRadius: 1, p: 1, mb: 2 }}>
                    {normalizationSimulationResults.changes.artists?.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                          🎤 Artistes à mettre à jour:
                        </Typography>
                        {normalizationSimulationResults.changes.artists?.slice(0, 10).map((change: any, idx: number) => (
                          <Typography key={idx} variant="caption" display="block" sx={{ mb: 0.5 }}>
                            {change.local_name} → <strong>{change.roon_name}</strong>
                          </Typography>
                        ))}
                        {(normalizationSimulationResults.changes.artists?.length || 0) > 10 && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            ... et {(normalizationSimulationResults.changes.artists?.length || 0) - 10} autres
                          </Typography>
                        )}
                      </Box>
                    )}

                    {normalizationSimulationResults.changes.albums?.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                          💿 Albums à mettre à jour:
                        </Typography>
                        {normalizationSimulationResults.changes.albums?.slice(0, 10).map((change: any, idx: number) => (
                          <Typography key={idx} variant="caption" display="block" sx={{ mb: 0.5 }}>
                            {change.local_name} → <strong>{change.roon_name}</strong>
                          </Typography>
                        ))}
                        {(normalizationSimulationResults.changes.albums?.length || 0) > 10 && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            ... et {(normalizationSimulationResults.changes.albums?.length || 0) - 10} autres
                          </Typography>
                        )}
                      </Box>
                    )}
                  </Box>
                )}

                {normalizationSimulationResults.changes.artists?.length === 0 && normalizationSimulationResults.changes.albums?.length === 0 && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    ℹ️ Aucune modification détectée. Votre bibliothèque est déjà alignée avec Roon.
                  </Alert>
                )}
              </Box>
            )}

            {!isLoadingSimulationResults && normalizationSimulationResults?.status === 'error' && (
              <Alert severity="error" sx={{ mb: 2 }}>
                ❌ Erreur lors de la simulation: {normalizationSimulationResults?.error}
              </Alert>
            )}

            {!isLoadingSimulationResults && !normalizationSimulationResults && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                ⚠️ Impossible de récupérer le statut de la simulation. Veuillez vérifier votre connexion.
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setNormalizationDialogOpen(false)
              setIsLoadingSimulationResults(false)
            }}
            disabled={simulateNormalizationMutation.isPending || normalizeWithRoonMutation.isPending || isLoadingSimulationResults}
          >
            Annuler
          </Button>
          {normalizationSimulationResults?.status === 'completed' && 
           (normalizationSimulationResults.changes.artists?.length > 0 || normalizationSimulationResults.changes.albums?.length > 0) && (
            <Button
              variant="contained"
              color="success"
              onClick={() => normalizeWithRoonMutation.mutate()}
              disabled={normalizeWithRoonMutation.isPending}
              startIcon={normalizeWithRoonMutation.isPending ? <CircularProgress size={20} /> : undefined}
            >
              {normalizeWithRoonMutation.isPending ? 'Application...' : '✅ Appliquer'}
            </Button>
          )}
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
