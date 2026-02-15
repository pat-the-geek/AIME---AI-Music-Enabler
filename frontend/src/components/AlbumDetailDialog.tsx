import { useState, useEffect } from 'react'
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
  Tooltip,
} from '@mui/material'
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  PlayArrow,
  Code as CodeIcon,
  Preview as PreviewIcon,
  Person as PersonIcon,
} from '@mui/icons-material'
import ReactMarkdown from 'react-markdown'
import apiClient from '@/api/client'
import { useRoon } from '@/contexts/RoonContext'
import { getHiddenContentSx, isEmptyContent } from '@/utils/hideEmptyContent'
import ArtistPortraitModal from '@/components/ArtistPortraitModal'
import type { AlbumDetail } from '@/types/models'

interface AlbumDetailDialogProps {
  albumId: number | null
  open: boolean
  onClose: () => void
}

export default function AlbumDetailDialog({ albumId, open, onClose }: AlbumDetailDialogProps) {
  const [editSpotifyUrl, setEditSpotifyUrl] = useState(false)
  const [spotifyUrlInput, setSpotifyUrlInput] = useState('')
  const [zoneDialogOpen, setZoneDialogOpen] = useState(false)
  const [selectedZone, setSelectedZone] = useState<string>('')
  const [resumeViewMode, setResumeViewMode] = useState<'markdown' | 'raw'>('markdown')
  const [snackbar, setSnackbar] = useState({ 
    open: false, 
    message: '', 
    severity: 'success' as 'success' | 'error' 
  })
  const [refreshKey, setRefreshKey] = useState(0)
  const [portraitOpen, setPortraitOpen] = useState(false)
  const [portraitArtistId, setPortraitArtistId] = useState<number | null>(null)
  const [portraitArtistName, setPortraitArtistName] = useState('')
  
  const queryClient = useQueryClient()
  const roon = useRoon()

  const { data: albumDetail, isLoading, refetch } = useQuery<AlbumDetail>({
    queryKey: ['album', albumId, refreshKey],
    queryFn: async () => {
      const response = await apiClient.get(`/collection/albums/${albumId}`)
      return response.data
    },
    enabled: albumId !== null && open,
  })

  // Debug: log albumDetail quand elle change
  useEffect(() => {
    if (albumDetail) {
      console.log('📸 AlbumDetail reçue:', {
        title: albumDetail.title,
        artists: albumDetail.artists,
        artist_images: albumDetail.artist_images,
        has_artist_images: albumDetail.artist_images && Object.keys(albumDetail.artist_images).length > 0,
        ai_info: albumDetail.ai_info ? `"${albumDetail.ai_info.substring(0, 100)}..."` : null,
        ai_info_exists: 'ai_info' in albumDetail,
        ai_info_type: typeof albumDetail.ai_info,
        ai_info_is_empty: albumDetail.ai_info ? isEmptyContent(albumDetail.ai_info) : 'no-ai_info'
      })
    }
  }, [albumDetail])

  // Récupérer les zones Roon
  const { data: roonZones } = useQuery({
    queryKey: ['roon-zones'],
    queryFn: async () => {
      const response = await apiClient.get('/playback/roon/zones')
      return response.data?.zones || []
    },
    enabled: roon?.enabled && roon?.available,
    refetchInterval: 10000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  })

  // Mutation pour enrichir complètement l'album
  const enrichAlbumMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.post(`/services/ai/enrich-album/${id}`)
      return response.data
    },
    onSuccess: async () => {
      // Invalider toutes les queries liées aux albums pour forcer un refresh complet
      await queryClient.invalidateQueries({ queryKey: ['album', albumId] })
      queryClient.invalidateQueries({ queryKey: ['albums'] })
      // Forcer un refresh immédiat
      await refetch()
      setSnackbar({ open: true, message: '✅ Album enrichi avec succès ! Description IA régénérée avec EurIA (1800-2000 caractères)', severity: 'success' })
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

  // Mutation pour jouer l'album sur Roon
  const playAlbumMutation = useMutation({
    mutationFn: async ({ albumId, zoneName }: { albumId: number; zoneName: string }) => {
      const response = await apiClient.post('/playback/roon/play-album', {
        zone_name: zoneName,
        album_id: albumId
      })
      return response.data
    },
    onSuccess: () => {
      setZoneDialogOpen(false)
      setSnackbar({ open: true, message: '🎵 Album en lecture sur Roon !', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ open: true, message: `❌ ${error.response?.data?.detail || error.message}`, severity: 'error' })
    },
  })

  const handleRefreshEnrichment = () => {
    if (albumId) {
      enrichAlbumMutation.mutate(albumId)
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

  const handleZoneClickedForAlbum = (zoneName: string) => {
    if (albumId) {
      setSelectedZone(zoneName)
      playAlbumMutation.mutate({ albumId, zoneName })
    }
  }

  const handleOpenAppleMusic = () => {
    if (!albumDetail) return
    
    if (albumDetail.apple_music_url) {
      const w = window.open(albumDetail.apple_music_url, '_blank')
      if (w) setTimeout(() => w.close(), 1000)
      return
    }
    
    const albumTitle = albumDetail.title
    const artistName = albumDetail.artists?.[0]
    if (!albumTitle || !artistName) return
    
    const searchQuery = `${albumTitle} ${artistName}`.trim()
    const encodedQuery = encodeURIComponent(searchQuery)
    const appleMusicSearchUrl = `https://music.apple.com/search?term=${encodedQuery}`
    const w = window.open(appleMusicSearchUrl, '_blank')
    if (w) setTimeout(() => w.close(), 1000)
  }

  const handleOpenArtistPortrait = async () => {
    if (!albumDetail?.artists?.[0]) return
    const artistName = albumDetail.artists[0]
    try {
      const response = await apiClient.get('/collection/artists/list', {
        params: { search: artistName, limit: 1 }
      })
      if (response.data?.artists?.[0]) {
        setPortraitArtistId(response.data.artists[0].id)
        setPortraitArtistName(response.data.artists[0].name)
        setPortraitOpen(true)
      }
    } catch (error) {
      console.error('Erreur recherche artiste:', error)
    }
  }

  return (
    <>
      <Dialog 
        open={open} 
        onClose={handleClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ position: 'relative' }}>
          <Typography variant="h5">
            {albumDetail?.title || 'Chargement...'}
          </Typography>
          
          {/* Bouton fermer */}
          <IconButton 
            onClick={handleClose}
            sx={{ position: 'absolute', top: 12, right: 12 }}
          >
            <CloseIcon />
          </IconButton>
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
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="overline" color="text.secondary">
                          Artiste(s)
                        </Typography>
                        <Typography variant="h6">
                          {albumDetail.artists.join(', ')}
                        </Typography>
                      </Box>
                      
                      {/* Vignette de l'artiste */}
                      {albumDetail.artist_images && 
                        Object.keys(albumDetail.artist_images).length > 0 && 
                        albumDetail.artist_images[Object.keys(albumDetail.artist_images)[0]] && (
                          <Tooltip title={albumDetail.artists?.[0] || 'Artiste'}>
                            <Box
                              component="img"
                              src={albumDetail.artist_images[Object.keys(albumDetail.artist_images)[0]]}
                              alt={albumDetail.artists?.[0] || 'Artiste'}
                              sx={{
                                width: 70,
                                height: 70,
                                borderRadius: 1.5,
                                objectFit: 'cover',
                                boxShadow: 2,
                                border: '2px solid',
                                borderColor: 'primary.main',
                                cursor: 'pointer',
                                flexShrink: 0
                              }}
                            />
                          </Tooltip>
                        )}
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

                    {/* Liens externes */}
                    {(albumDetail.discogs_url || albumDetail.spotify_url || !editSpotifyUrl) && (
                      <Box sx={{ display: 'flex', gap: 1, flexDirection: 'column' }}>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {albumDetail.discogs_url && (
                            <Button 
                              variant="outlined" 
                              size="small"
                              href={albumDetail.discogs_url}
                              target="_blank"
                            >
                              📀 Voir sur Discogs
                            </Button>
                          )}
                          {albumDetail.spotify_url && !editSpotifyUrl && (
                            <Button 
                              variant="outlined" 
                              size="small"
                              href={albumDetail.spotify_url}
                              target="_blank"
                              color="success"
                            >
                              ▶️ Jouer sur Spotify
                            </Button>
                          )}
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={handleOpenAppleMusic}
                            sx={{
                              color: '#FA243C',
                              borderColor: '#FA243C',
                              '&:hover': { 
                                color: '#E01B2F', 
                                borderColor: '#E01B2F',
                                backgroundColor: 'rgba(250, 36, 60, 0.1)' 
                              }
                            }}
                          >
                            🎵 Apple Music
                          </Button>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={handleOpenArtistPortrait}
                            startIcon={<PersonIcon />}
                            color="primary"
                          >
                            Portrait
                          </Button>
                          {roon?.enabled && (
                            <Button 
                              variant="contained" 
                              color="success"
                              size="small"
                              startIcon={<PlayArrow />}
                              disabled={playAlbumMutation.isPending}
                              onClick={() => {
                                setSelectedZone(roon?.zone || '')
                                setZoneDialogOpen(true)
                              }}
                              title={!roon?.available ? "Roon n'est pas disponible - Vérifiez la connexion au serveur Roon" : "Lancer la lecture sur Roon"}
                            >
                              {playAlbumMutation.isPending ? <CircularProgress size={16} /> : 'Roon'}
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

              {/* Section Enrichissement */}
              <Divider sx={{ my: 3 }} />
              <Box sx={isEmptyContent(albumDetail.ai_info) ? getHiddenContentSx(albumDetail.ai_info) : {}}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {albumDetail.ai_info ? '🤖 Description IA' : '✨ Enrichissement'}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={handleRefreshEnrichment}
                    disabled={enrichAlbumMutation.isPending}
                    startIcon={enrichAlbumMutation.isPending ? <CircularProgress size={16} /> : <RefreshIcon />}
                    title="Régénérer la description IA avec EurIA (description longue 1800-2000 caractères)"
                  >
                    Rafraîchir
                  </Button>
                </Box>
                {albumDetail.ai_info && !isEmptyContent(albumDetail.ai_info) ? (
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
                ) : (
                  <Box
                    sx={{
                      backgroundColor: 'action.hover',
                      p: 2,
                      borderRadius: 1,
                      textAlign: 'center',
                      color: 'text.secondary',
                    }}
                  >
                    <Typography variant="body2">
                      Cliquez sur &quot;Rafraîchir&quot; pour enrichir cet album avec des images, des liens Spotify et une description IA
                    </Typography>
                  </Box>
                )}
              </Box>

              {/* Résumé */}
              {albumDetail.resume && !isEmptyContent(albumDetail.resume) && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="h6" gutterBottom sx={{ mb: 0 }}>
                        📝 Résumé
                      </Typography>
                      <Tooltip title={resumeViewMode === 'markdown' ? 'Afficher le texte brut' : 'Afficher formaté'}>
                        <IconButton
                          size="small"
                          onClick={() => setResumeViewMode(resumeViewMode === 'markdown' ? 'raw' : 'markdown')}
                          color={resumeViewMode === 'markdown' ? 'primary' : 'default'}
                        >
                          {resumeViewMode === 'markdown' ? <CodeIcon fontSize="small" /> : <PreviewIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                    </Box>
                    {resumeViewMode === 'markdown' ? (
                      <Box 
                        sx={{ 
                          backgroundColor: 'action.hover',
                          p: 2,
                          borderRadius: 1,
                          '& p': { mb: 1.5 },
                          '& p:last-child': { mb: 0 },
                          '& em': { fontStyle: 'italic' },
                          '& strong': { fontWeight: 'bold' },
                          '& h1, & h2, & h3': { mt: 2, mb: 1 },
                          '& h1:first-child, & h2:first-child, & h3:first-child': { mt: 0 },
                          '& ul, & ol': { mb: 1.5, pl: 2 },
                          '& li': { mb: 0.5 },
                          '& blockquote': { borderLeft: '3px solid', borderColor: 'primary.main', pl: 2, fontStyle: 'italic' },
                          '& code': { backgroundColor: 'rgba(0, 0, 0, 0.05)', p: '2px 6px', borderRadius: '4px', fontFamily: 'monospace' },
                        }}
                      >
                        <ReactMarkdown>{albumDetail.resume}</ReactMarkdown>
                      </Box>
                    ) : (
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7, backgroundColor: 'action.hover', p: 2, borderRadius: 1, fontFamily: 'monospace' }}>
                        {albumDetail.resume}
                      </Typography>
                    )}
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

      {/* Dialog de sélection de zone Roon - Compact */}
      <Dialog open={zoneDialogOpen} onClose={() => {
        setZoneDialogOpen(false)
        setSelectedZone('')
      }} maxWidth="xs" fullWidth>
        <DialogTitle>Choisir une zone Roon</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Stack spacing={1}>
            {roonZones && roonZones.length > 0 ? (
              roonZones.map((zone: any) => (
                <Button
                  key={zone.zone_id}
                  onClick={() => handleZoneClickedForAlbum(zone.name)}
                  variant="outlined"
                  fullWidth
                  sx={{
                    py: 1.5,
                    textAlign: 'left',
                    justifyContent: 'flex-start',
                    '&:hover': {
                      backgroundColor: '#f5f5f5',
                      borderColor: 'primary.main',
                    }
                  }}
                  disabled={playAlbumMutation.isPending}
                >
                  {zone.name}
                </Button>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">Aucune zone disponible</Typography>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'flex-end' }}>
          <Button 
            onClick={() => {
              setZoneDialogOpen(false)
              setSelectedZone('')
            }}
          >
            Annuler
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

      {/* Modal Portrait de l'artiste */}
      <ArtistPortraitModal
        open={portraitOpen}
        artistId={portraitArtistId}
        artistName={portraitArtistName}
        onClose={() => setPortraitOpen(false)}
      />
    </>
  )
}
