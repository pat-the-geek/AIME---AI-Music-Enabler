import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Chip,
  Stack,
  Snackbar,
} from '@mui/material'
import { Add, PlayArrow, Delete } from '@mui/icons-material'
import apiClient from '../api/client'
import { useRoon } from '../contexts/RoonContext'

const ALGORITHMS = [
  { value: 'top_sessions', label: 'Top Sessions', description: 'Pistes des sessions les plus longues' },
  { value: 'artist_correlations', label: 'Corrélations Artistes', description: 'Artistes écoutés ensemble' },
  { value: 'artist_flow', label: 'Flux d\'Artistes', description: 'Transitions naturelles entre artistes' },
  { value: 'time_based', label: 'Basé sur l\'Heure', description: 'Écoutes aux heures de pointe' },
  { value: 'complete_albums', label: 'Albums Complets', description: 'Albums écoutés en entier' },
  { value: 'rediscovery', label: 'Redécouverte', description: 'Pistes aimées mais oubliées' },
  { value: 'ai_generated', label: 'Généré par IA', description: 'Sélection personnalisée par IA' }
]

export default function Playlists() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [createMode, setCreateMode] = useState<'ai' | 'manual'>('ai')
  const [playlistName, setPlaylistName] = useState('')
  const [algorithm, setAlgorithm] = useState('top_sessions')
  const [aiPrompt, setAiPrompt] = useState('')
  const [maxTracks, setMaxTracks] = useState(25)
  const [selectedTracks, setSelectedTracks] = useState<number[]>([])
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null)
  const [playingPlaylistId, setPlayingPlaylistId] = useState<number | null>(null)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  })
  
  const queryClient = useQueryClient()
  const roon = useRoon()

  // Récupérer playlists
  const { data: playlists, isLoading } = useQuery({
    queryKey: ['playlists'],
    queryFn: async () => {
      const response = await apiClient.get('/playlists')
      return response.data
    }
  })



  // Créer playlist
  const createPlaylistMutation = useMutation({
    mutationFn: async (payload: { mode: 'ai' | 'manual'; data: any }) => {
      const { mode, data } = payload
      
      if (mode === 'manual') {
        // Création manuelle
        console.log('Creating manual playlist:', data)
        const response = await apiClient.post('/playlists', {
          name: data.name,
          track_ids: data.track_ids
        })
        return response.data
      } else {
        // Création par IA
        console.log('Creating AI playlist:', data)
        const response = await apiClient.post('/playlists/generate', data)
        return response.data
      }
    },
    onSuccess: (data) => {
      console.log('Playlist created successfully:', data)
      queryClient.invalidateQueries({ queryKey: ['playlists'] })
      setCreateDialogOpen(false)
      setPlaylistName('')
      setAiPrompt('')
      setSelectedTracks([])
      setSnackbar({
        open: true,
        message: `✅ Playlist "${data.name}" créée avec succès !`,
        severity: 'success'
      })
    },
    onError: (error: any) => {
      console.error('Error creating playlist:', error)
      console.error('Error response:', error.response)
      console.error('Error message:', error.message)
      const message = error.response?.data?.detail || error.message || 'Erreur lors de la création de la playlist'
      setSnackbar({
        open: true,
        message: `❌ ${message}`,
        severity: 'error'
      })
    }
  })

  // Supprimer playlist
  const deletePlaylistMutation = useMutation({
    mutationFn: async (id: number) => {
      console.log('Deleting playlist:', id)
      await apiClient.delete(`/playlists/${id}`)
    },
    onSuccess: (data, playlistId) => {
      console.log('Playlist deleted successfully:', playlistId)
      // Attendre un peu avant de recharger
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['playlists'] })
        queryClient.invalidateQueries({ queryKey: ['playlist'] })
      }, 300)
      setSnackbar({
        open: true,
        message: '✅ Playlist supprimée avec succès',
        severity: 'success'
      })
    },
    onError: (error: any) => {
      console.error('Error deleting playlist:', error)
      const message = error.response?.data?.detail || error.message || 'Erreur lors de la suppression'
      setSnackbar({
        open: true,
        message: `❌ ${message}`,
        severity: 'error'
      })
    }
  })

  // Jouer playlist sur Roon
  const playPlaylistMutation = useMutation({
    mutationFn: async (playlistId: number) => {
      setPlayingPlaylistId(playlistId)
      await roon.playPlaylist(playlistId)
    },
    onSuccess: (data, playlistId) => {
      console.log('Playlist playback started:', playlistId)
      setSnackbar({
        open: true,
        message: '✅ Lecture de la playlist démarrée sur Roon',
        severity: 'success'
      })
      setPlayingPlaylistId(null)
    },
    onError: (error: any) => {
      console.error('Error playing playlist:', error)
      const message = error.response?.data?.detail || error.message || 'Erreur lors du démarrage de la lecture'
      setSnackbar({
        open: true,
        message: `❌ ${message}`,
        severity: 'error'
      })
      setPlayingPlaylistId(null)
    }
  })

  // Récupérer les détails d'une playlist
  const { data: playlistDetail } = useQuery({
    queryKey: ['playlist', selectedPlaylistId],
    queryFn: async () => {
      if (!selectedPlaylistId) return null
      const response = await apiClient.get(`/playlists/${selectedPlaylistId}`)
      return response.data
    },
    enabled: !!selectedPlaylistId
  })

  const handleCreatePlaylist = () => {
    if (createMode === 'manual') {
      if (!playlistName || selectedTracks.length === 0) {
        setSnackbar({
          open: true,
          message: '❌ Veuillez entrer un nom et sélectionner au moins un morceau',
          severity: 'error'
        })
        return
      }
      createPlaylistMutation.mutate({
        mode: 'manual',
        data: {
          name: playlistName,
          track_ids: selectedTracks
        }
      })
    } else {
      if (algorithm === 'ai_generated' && !aiPrompt) {
        setSnackbar({
          open: true,
          message: '❌ Veuillez entrer un prompt pour la génération IA',
          severity: 'error'
        })
        return
      }
      
      const data: any = {
        name: playlistName || undefined,
        algorithm,
        max_tracks: maxTracks
      }
      
      if (algorithm === 'ai_generated' && aiPrompt) {
        data.ai_prompt = aiPrompt
      }
      
      createPlaylistMutation.mutate({
        mode: 'ai',
        data
      })
    }
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <div>
          <Typography variant="h4">🎵 Playlists Intelligentes</Typography>
          <Typography variant="body2" color="text.secondary">
            Générez des playlists basées sur vos habitudes d'écoute
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Créer une Playlist
        </Button>
      </Box>

      {playlists && playlists.length === 0 ? (
        <Alert severity="info">
          Aucune playlist créée. Cliquez sur "Créer une Playlist" pour commencer !
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {playlists?.map((playlist: any) => (
            <Grid item xs={12} md={6} lg={4} key={playlist.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {playlist.name}
                  </Typography>
                  
                  <Stack direction="row" spacing={1} mb={2}>
                    <Chip
                      label={ALGORITHMS.find(a => a.value === playlist.algorithm)?.label || playlist.algorithm}
                      size="small"
                      color="primary"
                    />
                    <Chip
                      label={`${playlist.track_count} tracks`}
                      size="small"
                    />
                  </Stack>

                  {playlist.ai_prompt && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
                      "{playlist.ai_prompt}"
                    </Typography>
                  )}

                  <Typography variant="caption" color="text.secondary">
                    Créée le {new Date(playlist.created_at).toLocaleDateString('fr-FR')}
                  </Typography>

                  <Stack direction="row" spacing={1} mt={2}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<PlayArrow />}
                      fullWidth
                      onClick={() => {
                        setSelectedPlaylistId(playlist.id)
                        setDetailDialogOpen(true)
                      }}
                    >
                      Voir les Tracks
                    </Button>
                    {roon.enabled && (
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        startIcon={<PlayArrow />}
                        disabled={playPlaylistMutation.isPending || playingPlaylistId === playlist.id || !roon.available}
                        onClick={() => playPlaylistMutation.mutate(playlist.id)}
                        title={!roon.available ? "Roon n'est pas disponible - Vérifiez la connexion au serveur Roon" : "Lancer la lecture sur Roon"}
                      >
                        {playingPlaylistId === playlist.id ? <CircularProgress size={16} /> : '▶ Roon'}
                      </Button>
                    )}
                    <IconButton
                      size="small"
                      color="error"
                      disabled={deletePlaylistMutation.isPending}
                      onClick={() => {
                        console.log('Delete button clicked for playlist:', playlist.id)
                        if (confirm('Supprimer cette playlist ?')) {
                          console.log('Confirmed deletion, calling mutate...')
                          deletePlaylistMutation.mutate(playlist.id)
                        }
                      }}
                    >
                      {deletePlaylistMutation.isPending ? <CircularProgress size={20} /> : <Delete />}
                    </IconButton>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Dialog création playlist */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Créer une Playlist</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {/* Mode de création */}
            <FormControl fullWidth>
              <InputLabel>Type de playlist</InputLabel>
              <Select
                value={createMode}
                label="Type de playlist"
                onChange={(e) => setCreateMode(e.target.value as 'ai' | 'manual')}
              >
                <MenuItem value="ai">
                  <Box>
                    <Typography variant="body2">🤖 Intelligente (IA)</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Générée automatiquement selon un algorithme
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="manual">
                  <Box>
                    <Typography variant="body2">✋ Manuelle</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Sélectionnez vos morceaux
                    </Typography>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>

            {createMode === 'manual' ? (
              <>
                {/* Création manuelle */}
                <TextField
                  label="Nom de la playlist"
                  value={playlistName}
                  onChange={(e) => setPlaylistName(e.target.value)}
                  fullWidth
                  required
                  placeholder="Ma playlist"
                />

                <Box>
                  <Typography variant="body2" gutterBottom>
                    Morceaux sélectionnés ({selectedTracks.length})
                  </Typography>
                  {selectedTracks.length === 0 ? (
                    <Alert severity="info">
                      Utilisez le Journal ou la Timeline pour ajouter des morceaux à votre playlist.
                      Cliquez sur "Ajouter à une playlist" pour sélectionner des morceaux.
                    </Alert>
                  ) : (
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {selectedTracks.map((trackId) => (
                        <Chip
                          key={trackId}
                          label={`Track #${trackId}`}
                          onDelete={() => setSelectedTracks(prev => prev.filter(id => id !== trackId))}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              </>
            ) : (
              <>
                {/* Création IA */}
                <TextField
                  label="Nom de la playlist (optionnel)"
                  value={playlistName}
                  onChange={(e) => setPlaylistName(e.target.value)}
                  fullWidth
                  placeholder="Laisser vide pour auto-génération"
                />

                <FormControl fullWidth>
                  <InputLabel>Algorithme</InputLabel>
                  <Select
                    value={algorithm}
                    label="Algorithme"
                    onChange={(e) => setAlgorithm(e.target.value)}
                  >
                    {ALGORITHMS.map((algo) => (
                      <MenuItem key={algo.value} value={algo.value}>
                        <Box>
                          <Typography variant="body2">{algo.label}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {algo.description}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {algorithm === 'ai_generated' && (
                  <TextField
                    label="Prompt IA"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    multiline
                    rows={3}
                    fullWidth
                    placeholder="Ex: Une playlist énergique pour le sport avec du rock"
                    required
                  />
                )}

                <TextField
                  label="Nombre maximum de tracks"
                  type="number"
                  value={maxTracks}
                  onChange={(e) => setMaxTracks(Number(e.target.value))}
                  fullWidth
                  inputProps={{ min: 10, max: 100 }}
                />
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>
            Annuler
          </Button>
          <Button
            onClick={handleCreatePlaylist}
            variant="contained"
            disabled={
              createPlaylistMutation.isPending || 
              (createMode === 'manual' && (!playlistName || selectedTracks.length === 0)) ||
              (createMode === 'ai' && algorithm === 'ai_generated' && !aiPrompt)
            }
          >
            {createPlaylistMutation.isPending ? <CircularProgress size={24} /> : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog détails playlist */}
      <Dialog open={detailDialogOpen} onClose={() => setDetailDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Détails de la Playlist</DialogTitle>
        <DialogContent>
          {playlistDetail ? (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Typography variant="h6">{playlistDetail.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                Algorithme: {playlistDetail.algorithm}
              </Typography>
              {playlistDetail.ai_prompt && (
                <Typography variant="body2" color="text.secondary">
                  Prompt: {playlistDetail.ai_prompt}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                Nombre de morceaux: {playlistDetail.track_count}
              </Typography>

              {playlistDetail.tracks && playlistDetail.tracks.length > 0 ? (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Morceaux:
                  </Typography>
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {playlistDetail.tracks.map((track: any, idx: number) => (
                      <Box key={idx} sx={{ py: 1, borderBottom: '1px solid #eee' }}>
                        <Typography variant="body2">{idx + 1}. {track.title}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {track.artist}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Aucun morceau dans cette playlist
                </Typography>
              )}
            </Stack>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Fermer</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar pour les notifications */}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={3000} 
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

