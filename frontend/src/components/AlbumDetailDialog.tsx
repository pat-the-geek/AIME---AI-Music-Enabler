import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  CardMedia,
  Stack,
  Chip,
  Divider,
  IconButton,
  CircularProgress,
  TextField,
  Alert,
  Snackbar,
} from '@mui/material'
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Save as SaveIcon,
} from '@mui/icons-material'
import ReactMarkdown from 'react-markdown'
import apiClient from '@/api/client'
import type { AlbumDetail } from '@/types/models'

interface AlbumDetailDialogProps {
  albumId: number | null
  open: boolean
  onClose: () => void
}

export default function AlbumDetailDialog({ albumId, open, onClose }: AlbumDetailDialogProps) {
  const [editSpotifyUrl, setEditSpotifyUrl] = useState(false)
  const [spotifyUrlInput, setSpotifyUrlInput] = useState('')
  const [snackbar, setSnackbar] = useState({ 
    open: false, 
    message: '', 
    severity: 'success' as 'success' | 'error' 
  })
  
  const queryClient = useQueryClient()

  const { data: albumDetail, isLoading } = useQuery<AlbumDetail>({
    queryKey: ['album', albumId],
    queryFn: async () => {
      const response = await apiClient.get(`/collection/albums/${albumId}`)
      return response.data
    },
    enabled: albumId !== null && open,
  })

  // Mutation pour rafraîchir les enrichissements
  const refreshEnrichmentMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.post(`/services/ai/generate-info?album_id=${id}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['album', albumId] })
      setSnackbar({ open: true, message: 'Enrichissements rafraîchis avec succès !', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur: ${error.message}`, severity: 'error' })
    },
  })

  // Mutation pour sauvegarder l'URL Spotify
  const saveSpotifyUrlMutation = useMutation({
    mutationFn: async ({ id, url }: { id: number; url: string }) => {
      const response = await apiClient.patch(`/collection/albums/${id}`, { spotify_url: url })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['album', albumId] })
      queryClient.invalidateQueries({ queryKey: ['albums'] })
      setEditSpotifyUrl(false)
      setSpotifyUrlInput('')
      setSnackbar({ open: true, message: 'URL Spotify sauvegardée !', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `Erreur: ${error.message}`, severity: 'error' })
    },
  })

  const handleRefreshEnrichment = () => {
    if (albumId) {
      refreshEnrichmentMutation.mutate(albumId)
    }
  }

  const handleSaveSpotifyUrl = () => {
    if (albumId && spotifyUrlInput.trim()) {
      saveSpotifyUrlMutation.mutate({ id: albumId, url: spotifyUrlInput.trim() })
    }
  }

  const handleStartEditSpotifyUrl = () => {
    setEditSpotifyUrl(true)
    setSpotifyUrlInput(albumDetail?.spotify_url || '')
  }

  const handleClose = () => {
    setEditSpotifyUrl(false)
    setSpotifyUrlInput('')
    onClose()
  }

  return (
    <>
      <Dialog 
        open={open} 
        onClose={handleClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h5">
              {albumDetail?.title || 'Chargement...'}
            </Typography>
            <IconButton onClick={handleClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers>
          {isLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : albumDetail ? (
            <Box>
              {/* Image et infos principales */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={5}>
                  <CardMedia
                    component="img"
                    image={albumDetail.images[0] || 'https://via.placeholder.com/300'}
                    alt={albumDetail.title}
                    sx={{ 
                      width: '100%', 
                      borderRadius: 2,
                      boxShadow: 2
                    }}
                  />
                </Grid>
                
                <Grid item xs={12} md={7}>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="overline" color="text.secondary">
                        Artiste(s)
                      </Typography>
                      <Typography variant="h6">
                        {albumDetail.artists.join(', ')}
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="overline" color="text.secondary">
                        Année
                      </Typography>
                      <Typography variant="body1">
                        {albumDetail.year || 'Non spécifiée'}
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="overline" color="text.secondary">
                        Support
                      </Typography>
                      <Box>
                        <Chip label={albumDetail.support || 'Unknown'} />
                      </Box>
                    </Box>

                    {albumDetail.labels && albumDetail.labels.length > 0 && (
                      <Box>
                        <Typography variant="overline" color="text.secondary">
                          Label(s)
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {albumDetail.labels.map((label, idx) => (
                            <Chip key={idx} label={label} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}

                    {albumDetail.discogs_url && (
                      <Box sx={{ display: 'flex', gap: 1, flexDirection: 'column' }}>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button 
                            variant="outlined" 
                            size="small"
                            href={albumDetail.discogs_url}
                            target="_blank"
                          >
                            Voir sur Discogs
                          </Button>
                          {albumDetail.spotify_url && !editSpotifyUrl && (
                            <Button 
                              variant="outlined" 
                              size="small"
                              href={albumDetail.spotify_url}
                              target="_blank"
                              color="success"
                            >
                              🎵 Écouter sur Spotify
                            </Button>
                          )}
                          {!albumDetail.spotify_url && !editSpotifyUrl && (
                            <Button 
                              variant="outlined" 
                              size="small"
                              onClick={handleStartEditSpotifyUrl}
                              startIcon={<EditIcon />}
                            >
                              Ajouter URL Spotify
                            </Button>
                          )}
                          {albumDetail.spotify_url && !editSpotifyUrl && (
                            <IconButton 
                              size="small"
                              onClick={handleStartEditSpotifyUrl}
                              color="primary"
                              title="Modifier l'URL Spotify"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          )}
                        </Box>
                        {editSpotifyUrl && (
                          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <TextField
                              size="small"
                              fullWidth
                              label="URL Spotify"
                              value={spotifyUrlInput}
                              onChange={(e) => setSpotifyUrlInput(e.target.value)}
                              placeholder="https://open.spotify.com/album/..."
                            />
                            <Button
                              variant="contained"
                              size="small"
                              onClick={handleSaveSpotifyUrl}
                              disabled={saveSpotifyUrlMutation.isPending || !spotifyUrlInput.trim()}
                              startIcon={<SaveIcon />}
                            >
                              Sauver
                            </Button>
                            <Button
                              variant="outlined"
                              size="small"
                              onClick={() => {
                                setEditSpotifyUrl(false)
                                setSpotifyUrlInput('')
                              }}
                            >
                              Annuler
                            </Button>
                          </Box>
                        )}
                      </Box>
                    )}
                  </Stack>
                </Grid>
              </Grid>

              {/* Description IA */}
              {albumDetail.ai_info && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        🤖 Description IA
                      </Typography>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={handleRefreshEnrichment}
                        disabled={refreshEnrichmentMutation.isPending}
                        startIcon={refreshEnrichmentMutation.isPending ? <CircularProgress size={16} /> : <RefreshIcon />}
                      >
                        Rafraîchir
                      </Button>
                    </Box>
                    <Box 
                      sx={{ 
                        backgroundColor: 'action.hover',
                        p: 2,
                        borderRadius: 1,
                        '& p': { mb: 1.5 },
                        '& p:last-child': { mb: 0 },
                        '& em': { fontStyle: 'italic' },
                        '& strong': { fontWeight: 'bold' },
                      }}
                    >
                      <ReactMarkdown>{albumDetail.ai_info}</ReactMarkdown>
                    </Box>
                  </Box>
                </>
              )}

              {/* Résumé */}
              {albumDetail.resume && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      📝 Résumé
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>
                      {albumDetail.resume}
                    </Typography>
                  </Box>
                </>
              )}

              {/* Info film si BO */}
              {albumDetail.film_title && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      🎬 Bande Originale
                    </Typography>
                    <Stack spacing={1}>
                      <Typography variant="body1">
                        <strong>Film :</strong> {albumDetail.film_title}
                      </Typography>
                      {albumDetail.film_year && (
                        <Typography variant="body1">
                          <strong>Année :</strong> {albumDetail.film_year}
                        </Typography>
                      )}
                      {albumDetail.film_director && (
                        <Typography variant="body1">
                          <strong>Réalisateur :</strong> {albumDetail.film_director}
                        </Typography>
                      )}
                    </Stack>
                  </Box>
                </>
              )}

              {/* Dates */}
              <Divider sx={{ my: 3 }} />
              <Box sx={{ display: 'flex', gap: 3 }}>
                <Typography variant="caption" color="text.secondary">
                  Ajouté le : {new Date(albumDetail.created_at).toLocaleDateString('fr-FR')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Modifié le : {new Date(albumDetail.updated_at).toLocaleDateString('fr-FR')}
                </Typography>
              </Box>
            </Box>
          ) : null}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleClose}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar pour les notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  )
}
