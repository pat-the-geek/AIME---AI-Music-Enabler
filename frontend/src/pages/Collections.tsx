import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Stack,
  Snackbar,
  IconButton,
  Tooltip,
  CardMedia,
  FormControlLabel,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import { 
  Add, 
  PlayArrow, 
  Delete, 
  Search,
  MusicNote,
  FindInPage,
} from '@mui/icons-material'
import apiClient from '../api/client'
import { useRoon } from '../contexts/RoonContext'
import { getHiddenContentSx, isEmptyContent } from '../utils/hideEmptyContent'
import ArtistPortraitModal from '@/components/ArtistPortraitModal'

interface Collection {
  id: number
  name: string
  search_type: string | null
  search_criteria: Record<string, any> | null
  ai_query: string | null
  album_count: number
  created_at: string
  sample_album_images: string[]  // Images d'albums pour illustrer la collection
}

interface Album {
  id: number
  title: string
  artist_name: string | null
  year: number | null
  image_url: string | null
  ai_description: string | null
  spotify_url?: string | null
  apple_music_url?: string | null
}

// Nettoyer le nom de l'artiste en supprimant les parenthèses et tout ce qui suit
const cleanArtistName = (name: string): string => {
  if (!name) return name
  const parenIndex = name.indexOf('(')
  return parenIndex !== -1 ? name.substring(0, parenIndex).trim() : name
}

export default function Collections() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [selectedAlbumId, setSelectedAlbumId] = useState<number | null>(null)
  const [aiQuery, setAiQuery] = useState('')
  const [roonZoneDialogOpen, setRoonZoneDialogOpen] = useState(false)
  const [pendingCollectionId, setPendingCollectionId] = useState<number | null>(null)
  const [pendingAlbumId, setPendingAlbumId] = useState<number | null>(null)
  const [selectedRoonZone, setSelectedRoonZone] = useState<string>('')
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  })
  
  // Recherche d'album dans Roon
  const [searchAlbumDialogOpen, setSearchAlbumDialogOpen] = useState(false)
  const [searchArtist, setSearchArtist] = useState('')
  const [searchAlbumTitle, setSearchAlbumTitle] = useState('')
  const [searchResult, setSearchResult] = useState<any>(null)
  const [searchingForAlbum, setSearchingForAlbum] = useState<{ artist: string; title: string } | null>(null)
  const [playingFromSearch, setPlayingFromSearch] = useState(false)
  const [playingFromSearchWithZone, setPlayingFromSearchWithZone] = useState(false)
  const [groupByImage, setGroupByImage] = useState(() => {
    const stored = localStorage.getItem('discover-group-by-image')
    return stored ? stored === 'true' : true
  })

  useEffect(() => {
    localStorage.setItem('discover-group-by-image', String(groupByImage))
  }, [groupByImage])

  const [portraitOpen, setPortraitOpen] = useState(false)
  const [portraitArtistId, setPortraitArtistId] = useState<number | null>(null)
  const [portraitArtistName, setPortraitArtistName] = useState('')
  const [descriptionOpen, setDescriptionOpen] = useState(false)
  const [descriptionAlbum, setDescriptionAlbum] = useState<Album | null>(null)
  
  const queryClient = useQueryClient()
  const roon = useRoon()

  // Récupérer les collections
  const { data: collections, isLoading } = useQuery<Collection[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const response = await apiClient.get('/collections/')
      return response.data
    }
  })

  // Récupérer les albums d'une collection
  const { data: collectionAlbums, isLoading: albumsLoading } = useQuery<Album[]>({
    queryKey: ['collection-albums', selectedCollectionId],
    queryFn: async () => {
      if (!selectedCollectionId) return []
      const response = await apiClient.get(`/collections/${selectedCollectionId}/albums`)
      return response.data
    },
    enabled: !!selectedCollectionId
  })

  const groupedAlbums = useMemo(() => {
    if (!collectionAlbums || collectionAlbums.length === 0) return []
    const groups = new Map<string, Album[]>()
    for (const album of collectionAlbums) {
      const key = album.image_url || 'no-image'
      const existing = groups.get(key)
      if (existing) {
        existing.push(album)
      } else {
        groups.set(key, [album])
      }
    }
    return Array.from(groups.entries()).map(([imageUrl, albums]) => ({
      imageUrl,
      albums
    }))
  }, [collectionAlbums])

  // Récupérer les zones Roon
  const { data: roonZones } = useQuery({
    queryKey: ['roon-zones'],
    queryFn: async () => {
      const response = await apiClient.get('/playback/roon/zones')
      return response.data?.zones || []
    },
    enabled: roon?.enabled && roon?.available,
    refetchInterval: 10000,
  })

  // Créer une collection
  const createCollectionMutation = useMutation({
    mutationFn: async (payload: {
      name: string
      search_type: string
      search_criteria?: Record<string, any>
      ai_query?: string
    }) => {
      const response = await apiClient.post('/collections/', payload)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      setCreateDialogOpen(false)
      resetForm()
      setSnackbar({ open: true, message: 'Collection créée avec succès!', severity: 'success' })
    },
    onError: (error: any) => {
      setSnackbar({ 
        open: true, 
        message: error.response?.data?.detail || 'Erreur lors de la création', 
        severity: 'error' 
      })
    }
  })

  // Supprimer une collection
  const deleteCollectionMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/collections/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      setSnackbar({ open: true, message: 'Collection supprimée', severity: 'success' })
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Erreur lors de la suppression', severity: 'error' })
    }
  })

  // Jouer une collection sur Roon
  const playCollectionMutation = useMutation({
    mutationFn: async ({ collectionId, zoneName }: { collectionId: number; zoneName?: string }) => {
      const response = await apiClient.post(`/collections/${collectionId}/play`, {
        zone_name: zoneName
      })
      return response.data
    },
    onSuccess: (data) => {
      setRoonZoneDialogOpen(false)
      setSnackbar({ 
        open: true, 
        message: `Lecture lancée: ${data.current_album} (${data.album_count} albums)`, 
        severity: 'success' 
      })
    },
    onError: (error: any) => {
      setSnackbar({ 
        open: true, 
        message: error.response?.data?.detail || 'Erreur lors de la lecture', 
        severity: 'error' 
      })
    }
  })

  // Jouer un album sur Roon
  const playAlbumMutation = useMutation({
    mutationFn: async ({ albumId, zoneName }: { albumId: number; zoneName?: string }) => {
      const response = await apiClient.post(`/playback/roon/play-album`, {
        album_id: albumId,
        zone_name: zoneName
      })
      return response.data
    },
    onSuccess: (data) => {
      setRoonZoneDialogOpen(false)
      setSnackbar({ 
        open: true, 
        message: `Lecture lancée: ${data.album.title}`, 
        severity: 'success' 
      })
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail
      const statusCode = error.response?.status
      
      let message = 'Erreur lors de la lecture'
      
      if (statusCode === 422) {
        // Album non disponible dans Roon
        message = errorDetail || 'Cet album n\'existe pas dans votre bibliothèque Roon'
      } else if (statusCode === 503) {
        // Problème avec le bridge Roon
        message = 'Roon n\'est pas accessible. Vérifiez que le bridge Roon est actif.'
      } else {
        message = errorDetail || 'Erreur lors de la lecture'
      }
      
      setSnackbar({ 
        open: true, 
        message, 
        severity: 'error' 
      })
    }
  })

  const searchAlbumMutation = useMutation({
    mutationFn: async ({ artist, album }: { artist: string; album: string }) => {
      const response = await apiClient.post(`/playback/roon/search-album`, {
        artist,
        album
      })
      return response.data
    },
    onSuccess: (data) => {
      setSearchResult(data)
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail
      setSearchResult({
        found: false,
        message: errorDetail || 'Erreur lors de la recherche',
        error: true
      })
    }
  })

  const playAlbumByNameMutation = useMutation({
    mutationFn: async ({ artist, album, zoneName }: { artist: string; album: string; zoneName?: string }) => {
      // Nettoyer le titre et l'artiste en supprimant les parenthèses et tout ce qui suit
      const cleanedAlbum = album.indexOf('(') !== -1 ? album.substring(0, album.indexOf('(')).trim() : album
      const cleanedArtist = cleanArtistName(artist)
      const response = await apiClient.post(`/playback/roon/play-album-by-name`, {
        artist_name: cleanedArtist,
        album_title: cleanedAlbum,
        zone_name: zoneName
      })
      return response.data
    },
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: `Lecture lancée: ${data.message || 'Album en cours de lecture'}`,
        severity: 'success'
      })
      setSearchAlbumDialogOpen(false)
      setRoonZoneDialogOpen(false)
      setPlayingFromSearch(false)
      setPlayingFromSearchWithZone(false)
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail
      const statusCode = error.response?.status
      
      let message = 'Erreur lors de la lecture'
      
      if (statusCode === 422) {
        message = errorDetail || 'Album non trouvé dans votre bibliothèque Roon'
      } else if (statusCode === 503) {
        message = 'Roon n\'est pas accessible'
      } else {
        message = errorDetail || message
      }
      
      setSnackbar({
        open: true,
        message,
        severity: 'error'
      })
      setPlayingFromSearch(false)
      setPlayingFromSearchWithZone(false)
    }
  })

  const resetForm = () => {
    setAiQuery('')
  }

  const handleCreateCollection = () => {
    if (!aiQuery.trim()) {
      setSnackbar({ open: true, message: 'Requête de recherche IA requise', severity: 'error' })
      return
    }

    const payload: any = {
      name: null,  // Sera généré automatiquement par le backend
      search_type: 'ai_query',
      ai_query: aiQuery
    }

    createCollectionMutation.mutate(payload)
  }

  const handlePlayCollection = (collectionId: number) => {
    setPendingCollectionId(collectionId)
    setSelectedRoonZone('')
    setRoonZoneDialogOpen(true)
  }

  const handlePlayAlbum = (albumId: number) => {
    setPendingAlbumId(albumId)
    setSelectedRoonZone('')
    setRoonZoneDialogOpen(true)
  }

  const handleZoneClicked = (zoneName: string) => {
    // Sélectionner la zone et lancer la lecture directement
    setSelectedRoonZone(zoneName)
    
    // La fonction handleRoonZoneSelected utilisera selectedRoonZone qui a été mis à jour
    // Mais comme setState est asynchrone, on doit passer la zone en paramètre
    // Alors on refactorise handleRoonZoneSelected en passant la zone
    handleRoonZoneSelectedWithZone(zoneName)
  }

  const handleRoonZoneSelectedWithZone = (zoneName: string) => {
    // Cas 1: Lecture d'album depuis la recherche
    if (playingFromSearchWithZone && searchResult?.found && searchResult?.exact_name) {
      setPlayingFromSearch(true)
      playAlbumByNameMutation.mutate({
        artist: searchResult.artist || searchArtist,
        album: searchResult.exact_name,
        zoneName: zoneName || undefined
      })
      setRoonZoneDialogOpen(false)
      setPlayingFromSearchWithZone(false)
      setSelectedRoonZone('')
    }
    // Cas 2: Lecture de collection
    else if (pendingCollectionId) {
      playCollectionMutation.mutate({ 
        collectionId: pendingCollectionId, 
        zoneName: zoneName || undefined 
      })
      setRoonZoneDialogOpen(false)
      setPendingCollectionId(null)
      setSelectedRoonZone('')
    }
    // Cas 3: Lecture d'album
    else if (pendingAlbumId) {
      playAlbumMutation.mutate({ 
        albumId: pendingAlbumId, 
        zoneName: zoneName || undefined 
      })
      setRoonZoneDialogOpen(false)
      setPendingAlbumId(null)
      setSelectedRoonZone('')
    }
  }

  const handleRoonZoneSelected = () => {
    handleRoonZoneSelectedWithZone(selectedRoonZone)
  }

  const handleSearchAlbum = (artist: string, album: string) => {
    setSearchingForAlbum({ artist, title: album })
    searchAlbumMutation.mutate({ artist, album })
  }

  const handleOpenSearchDialog = (album: Album) => {
    setSearchArtist(album.artist_name || '')
    setSearchAlbumTitle(album.title || '')
    setSearchResult(null)
    setSearchAlbumDialogOpen(true)
  }

  const handleSearchAlbumSubmit = () => {
    if (!searchArtist.trim() || !searchAlbumTitle.trim()) {
      setSnackbar({
        open: true,
        message: 'Veuillez remplir le nom de l\'artiste et l\'album',
        severity: 'error'
      })
      return
    }
    handleSearchAlbum(searchArtist, searchAlbumTitle)
  }

  const handlePlayAlbumFromSearch = () => {
    if (searchResult?.found && searchResult?.exact_name) {
      setPlayingFromSearchWithZone(true)
      setSearchAlbumDialogOpen(false)
      setSelectedRoonZone('')
      setRoonZoneDialogOpen(true)
    }
  }

  const handleOpenSpotify = (event: React.MouseEvent, url?: string | null) => {
    event.stopPropagation()
    if (!url) return
    window.open(url, '_blank')
  }

  const handleOpenAppleMusic = (event: React.MouseEvent, albumTitle?: string, artistName?: string, appleMusicUrl?: string | null) => {
    event.stopPropagation()
    if (appleMusicUrl) {
      const w = window.open(appleMusicUrl, '_blank')
      if (w) setTimeout(() => w.close(), 1000)
      return
    }
    if (!albumTitle || !artistName) return
    const searchQuery = `${albumTitle} ${artistName}`.trim()
    const encodedQuery = encodeURIComponent(searchQuery)
    const appleMusicSearchUrl = `https://music.apple.com/search?term=${encodedQuery}`
    const w = window.open(appleMusicSearchUrl, '_blank')
    if (w) setTimeout(() => w.close(), 1000)
  }

  const handleOpenArtistPortrait = async (event: React.MouseEvent, artistName?: string) => {
    event.stopPropagation()
    if (!artistName) return
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

  const handleOpenAlbumDescription = (event: React.MouseEvent, album: Album) => {
    event.stopPropagation()
    setDescriptionAlbum(album)
    setDescriptionOpen(true)
  }

  const handleDescriptionClose = () => {
    setDescriptionOpen(false)
  }

  const handleViewDetails = (collectionId: number) => {
    setSelectedCollectionId(collectionId)
    setSelectedAlbumId(null)
    setDetailDialogOpen(true)
  }

  const handleDetailDialogClose = (
    _event: object,
    reason: 'backdropClick' | 'escapeKeyDown'
  ) => {
    if (selectedAlbumId) {
      setSelectedAlbumId(null)
      return
    }
    setDetailDialogOpen(false)
  }

  const getSearchTypeLabel = (type: string | null) => {
    switch (type) {
      case 'ai_query': return 'Recherche IA'
      default: return 'IA'
    }
  }

  const getSearchTypeColor = (type: string | null): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (type) {
      case 'genre': return 'primary'
      case 'artist': return 'secondary'
      case 'period': return 'info'
      case 'ai_query': return 'success'
      default: return 'default'
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
        <Typography variant="h4" component="h1">
          � Discover - Collections d'Albums
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Nouvelle Collection
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" mb={3}>
        Découvrez de nouvelles collections d'albums basées sur des critères de recherche: genre, artiste, période, ou recherche IA sémantique.
      </Typography>

      {collections && collections.length === 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Aucune collection. Créez votre première collection d'albums pour commencer votre découverte!
        </Alert>
      )}

      <Grid container spacing={3}>
        {collections?.map((collection) => (
          <Grid item xs={12} sm={6} md={4} key={collection.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              {/* Images d'albums en grille avec transparence */}
              {collection.sample_album_images && collection.sample_album_images.length > 0 && (
                <Box 
                  sx={{ 
                    position: 'relative',
                    height: 120,
                    overflow: 'hidden',
                    display: 'flex',
                    gap: 0.5,
                    p: 1,
                    backgroundColor: 'action.hover'
                  }}
                >
                  {collection.sample_album_images.slice(0, 5).map((imageUrl, index) => (
                    <Box
                      key={index}
                      component="img"
                      src={imageUrl}
                      alt={`Album ${index + 1}`}
                      sx={{
                        width: `${100 / Math.min(collection.sample_album_images.length, 5)}%`,
                        height: '100%',
                        objectFit: 'cover',
                        borderRadius: 1
                      }}
                    />
                  ))}
                </Box>
              )}
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" gutterBottom>
                  {collection.name}
                </Typography>
                <Stack direction="row" spacing={1} mb={2}>
                  <Chip 
                    label={getSearchTypeLabel(collection.search_type)} 
                    size="small" 
                    color={getSearchTypeColor(collection.search_type)}
                  />
                  <Chip 
                    label={`${collection.album_count} albums`} 
                    size="small" 
                    variant="outlined"
                  />
                </Stack>
                {collection.ai_query && (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    "{collection.ai_query}"
                  </Typography>
                )}
                {collection.search_criteria && (
                  <Typography variant="body2" color="text.secondary">
                    {JSON.stringify(collection.search_criteria)}
                  </Typography>
                )}
                <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                  Créée le {new Date(collection.created_at).toLocaleDateString('fr-FR')}
                </Typography>
              </CardContent>
              <CardActions>
                <Tooltip title="Voir les albums">
                  <Button 
                    size="small" 
                    onClick={() => handleViewDetails(collection.id)}
                    startIcon={<Search />}
                  >
                    Détails
                  </Button>
                </Tooltip>
                {roon?.enabled && (
                  <Tooltip title="Jouer sur Roon">
                    <Button
                      size="small"
                      onClick={() => handlePlayCollection(collection.id)}
                      startIcon={<PlayArrow />}
                      disabled={collection.album_count === 0 || playCollectionMutation.isPending}
                    >
                      Jouer
                    </Button>
                  </Tooltip>
                )}
                <Tooltip title="Supprimer">
                  <IconButton
                    size="small"
                    onClick={() => deleteCollectionMutation.mutate(collection.id)}
                    disabled={deleteCollectionMutation.isPending}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </Tooltip>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Dialog: Créer une collection */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Créer une Collection par IA</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Décrivez la collection d'albums que vous souhaitez découvrir. L'IA recherchera les albums correspondants sur le web et les enrichira avec des images et descriptions.
          </Alert>
          <Stack spacing={3} mt={2}>
            <TextField
              label="Requête IA"
              fullWidth
              multiline
              rows={4}
              value={aiQuery}
              onChange={(e) => setAiQuery(e.target.value)}
              placeholder="Exemple: Fais moi une sélection d'album qui sont agréable pour faire du vibe coding à la maison"
              helperText="Décrivez le type de musique que vous recherchez. L'IA trouvera les albums correspondants sur le web."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Annuler</Button>
          <Button 
            onClick={handleCreateCollection} 
            variant="contained"
            disabled={createCollectionMutation.isPending}
          >
            {createCollectionMutation.isPending ? <CircularProgress size={24} /> : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Détails de la collection */}
      <Dialog 
        open={detailDialogOpen} 
        onClose={handleDetailDialogClose}
        maxWidth="xl"
        fullWidth
        sx={{
          '& .MuiDialog-paper': {
            maxWidth: '95vw'
          }
        }}
      >
        <DialogTitle>
          {selectedAlbumId ? 'Détail de l\'album' : 'Albums de la Collection'}
        </DialogTitle>
        <DialogContent>
          {selectedAlbumId && collectionAlbums ? (
            // Vue détail d'un album sélectionné
            (() => {
              const selectedAlbum = collectionAlbums.find((a) => a.id === selectedAlbumId)
              return selectedAlbum ? (
                <Box>
                  <Box display="flex" gap={3} mb={3} mt={2}>
                    {selectedAlbum.image_url && (
                      <Box
                        component="img"
                        src={selectedAlbum.image_url}
                        alt={selectedAlbum.title}
                        sx={{
                          width: 200,
                          height: 200,
                          objectFit: 'cover',
                          borderRadius: 1
                        }}
                      />
                    )}
                    <Box flex={1}>
                      <Typography variant="h5" gutterBottom fontWeight="bold">
                        {selectedAlbum.title}
                      </Typography>
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        {selectedAlbum.artist_name || 'Unknown Artist'}
                      </Typography>
                      {selectedAlbum.year && (
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Année: {selectedAlbum.year}
                        </Typography>
                      )}
                      {(selectedAlbum.spotify_url || selectedAlbum.apple_music_url) && (
                        <Box mt={2} sx={{ display: 'flex', gap: 1 }}>
                          {selectedAlbum.spotify_url && (
                            <Button
                              variant="contained"
                              color="success"
                              startIcon={<PlayArrow />}
                              onClick={(e) => handleOpenSpotify(e, selectedAlbum.spotify_url)}
                            >
                              Spotify
                            </Button>
                          )}
                          <Button
                            variant="contained"
                            sx={{
                              backgroundColor: '#FA243C',
                              '&:hover': { backgroundColor: '#E01B2F' }
                            }}
                            onClick={(e) => handleOpenAppleMusic(e, selectedAlbum.title, selectedAlbum.artist_name, selectedAlbum.apple_music_url)}
                          >
                            🎵 Apple
                          </Button>
                        </Box>
                      )}
                    </Box>
                  </Box>
                  {selectedAlbum.ai_description && (
                    <Box mt={3}>
                      <Typography variant="h6" gutterBottom>
                        Description
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph style={{ whiteSpace: 'pre-wrap' }}>
                        {selectedAlbum.ai_description}
                      </Typography>
                    </Box>
                  )}
                </Box>
              ) : null
            })()
          ) : albumsLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : groupedAlbums.length > 0 ? (
            <Box mt={1} display="flex" flexDirection="column" gap={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={groupByImage}
                    onChange={(e) => setGroupByImage(e.target.checked)}
                  />
                }
                label={groupByImage ? 'Groupé par image' : 'Liste simple'}
                sx={{ alignSelf: 'flex-start' }}
              />
              {groupByImage ? (
                groupedAlbums.map((group) => (
                  <Box key={group.imageUrl}>
                    <Box display="flex" alignItems="center" gap={2} mb={1}>
                      {group.imageUrl !== 'no-image' && (
                        <CardMedia
                          component="img"
                          sx={{ width: 64, height: 64, objectFit: 'cover', borderRadius: 1 }}
                          image={group.imageUrl}
                          alt="Album cover"
                        />
                      )}
                      <Typography variant="subtitle2" color="text.secondary">
                        {group.imageUrl === 'no-image'
                          ? `Sans image (${group.albums.length})`
                          : `Visuel partage (${group.albums.length})`}
                      </Typography>
                    </Box>
                    <Grid container spacing={2}>
                      {group.albums.map((album) => (
                        <Grid item xs={12} sm={6} md={3} key={album.id}>
                          <Card 
                            variant="outlined"
                            onClick={() => setSelectedAlbumId(album.id)}
                            sx={{ 
                              height: '100%', 
                              cursor: 'pointer',
                              transition: 'all 0.3s',
                              '&:hover': {
                                transform: 'translateY(-4px)',
                                boxShadow: 3
                              }
                            }}
                          >
                            <Box display="flex" flexDirection="column" height="100%">
                              {album.image_url && (
                                <CardMedia
                                  component="img"
                                  sx={{ height: 150, objectFit: 'cover' }}
                                  image={album.image_url}
                                  alt={album.title}
                                />
                              )}
                              <CardContent sx={{ flex: 1 }}>
                                <Typography variant="subtitle1" fontWeight="bold" noWrap>
                                  {album.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" noWrap>
                                  {album.artist_name || 'Unknown Artist'}
                                </Typography>
                                {album.year && (
                                  <Typography variant="caption" color="text.secondary" display="block">
                                    {album.year}
                                  </Typography>
                                )}
                              </CardContent>
                              <CardActions>
                                <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
                                  {album.spotify_url && (
                                    <Tooltip title="Jouer sur Spotify">
                                      <Button
                                        size="small"
                                        onClick={handleOpenSpotify}
                                        startIcon={<MusicNote />}
                                      >
                                        Spotify
                                      </Button>
                                    </Tooltip>
                                  )}
                                  {(album.apple_music_url || album.title) && (
                                    <Tooltip title="Ouvrir sur Apple Music">
                                      <Button
                                        size="small"
                                        onClick={(e) =>
                                          handleOpenAppleMusic(
                                            e,
                                            album.title,
                                            album.artist_name,
                                            album.apple_music_url
                                          )
                                        }
                                        sx={{
                                          color: '#FA243C',
                                          '&:hover': {
                                            backgroundColor: '#FA243C',
                                            color: 'white'
                                          }
                                        }}
                                      >
                                        Apple
                                      </Button>
                                    </Tooltip>
                                  )}
                                  {album.artist_name && (
                                    <Tooltip title="Profil artiste">
                                      <Button
                                        size="small"
                                        onClick={(e) => handleOpenArtistPortrait(e, album.artist_name || undefined)}
                                      >
                                        Profil
                                      </Button>
                                    </Tooltip>
                                  )}
                                  <Tooltip title="Description EurIA">
                                    <Button
                                      size="small"
                                      onClick={(e) => handleOpenAlbumDescription(e, album)}
                                    >
                                      Description
                                    </Button>
                                  </Tooltip>
                                </Box>
                                {roon?.enabled && (
                                  <Tooltip title="Lancer la lecture sur Roon">
                                    <Button
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleOpenSearchDialog(album)
                                      }}
                                      startIcon={<Search />}
                                    >
                                      Lecture Roon
                                    </Button>
                                  </Tooltip>
                                )}
                              </CardActions>
                            </Box>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                ))
              ) : (
                <Grid container spacing={2}>
                  {collectionAlbums?.map((album) => (
                    <Grid item xs={12} sm={6} md={3} key={album.id}>
                      <Card 
                        variant="outlined"
                        onClick={() => setSelectedAlbumId(album.id)}
                        sx={{ 
                          height: '100%', 
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: 3
                          }
                        }}
                      >
                        <Box display="flex" flexDirection="column" height="100%">
                          {album.image_url && (
                            <CardMedia
                              component="img"
                              sx={{ height: 150, objectFit: 'cover' }}
                              image={album.image_url}
                              alt={album.title}
                            />
                          )}
                          <CardContent sx={{ flex: 1 }}>
                            <Typography variant="subtitle1" fontWeight="bold" noWrap>
                              {album.title}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" noWrap>
                              {album.artist_name || 'Unknown Artist'}
                            </Typography>
                            {album.year && (
                              <Typography variant="caption" color="text.secondary" display="block">
                                {album.year}
                              </Typography>
                            )}
                          </CardContent>
                          <CardActions>
                            <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
                              {album.spotify_url && (
                                <Tooltip title="Jouer sur Spotify">
                                  <Button
                                    size="small"
                                    onClick={handleOpenSpotify}
                                    startIcon={<MusicNote />}
                                  >
                                    Spotify
                                  </Button>
                                </Tooltip>
                              )}
                              {(album.apple_music_url || album.title) && (
                                <Tooltip title="Ouvrir sur Apple Music">
                                  <Button
                                    size="small"
                                    onClick={(e) =>
                                      handleOpenAppleMusic(
                                        e,
                                        album.title,
                                        album.artist_name,
                                        album.apple_music_url
                                      )
                                    }
                                    sx={{
                                      color: '#FA243C',
                                      '&:hover': {
                                        backgroundColor: '#FA243C',
                                        color: 'white'
                                      }
                                    }}
                                  >
                                    Apple
                                  </Button>
                                </Tooltip>
                              )}
                              {album.artist_name && (
                                <Tooltip title="Profil artiste">
                                  <Button
                                    size="small"
                                    onClick={(e) => handleOpenArtistPortrait(e, album.artist_name || undefined)}
                                  >
                                    Profil
                                  </Button>
                                </Tooltip>
                              )}
                              <Tooltip title="Description EurIA">
                                <Button
                                  size="small"
                                  onClick={(e) => handleOpenAlbumDescription(e, album)}
                                >
                                  Description
                                </Button>
                              </Tooltip>
                            </Box>
                            {roon?.enabled && (
                              <Tooltip title="Lancer la lecture sur Roon">
                                <Button
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleOpenSearchDialog(album)
                                  }}
                                  startIcon={<Search />}
                                >
                                  Lecture Roon
                                </Button>
                              </Tooltip>
                            )}
                          </CardActions>
                        </Box>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>
          ) : (
            <Alert severity="info">Aucun album dans cette collection</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            if (selectedAlbumId) {
              setSelectedAlbumId(null)
              return
            }
            setDetailDialogOpen(false)
          }}>
            {selectedAlbumId ? 'Retour' : 'Fermer'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Description album */}
      <Dialog
        open={descriptionOpen}
        onClose={handleDescriptionClose}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Description de l'album</DialogTitle>
        <DialogContent>
          {descriptionAlbum?.ai_description ? (
            <Typography variant="body2" color="text.secondary" style={{ whiteSpace: 'pre-wrap' }}>
              {descriptionAlbum.ai_description}
            </Typography>
          ) : (
            <Alert severity="info">Aucune description disponible pour cet album.</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDescriptionClose}>Fermer</Button>
        </DialogActions>
      </Dialog>

      <ArtistPortraitModal
        open={portraitOpen}
        artistId={portraitArtistId}
        artistName={portraitArtistName}
        onClose={() => setPortraitOpen(false)}
      />

      {/* Dialog: Sélection de zone Roon (utilisé pour Collection, Album et Recherche) */}
      <Dialog open={roonZoneDialogOpen} onClose={() => {
        setRoonZoneDialogOpen(false)
        setPlayingFromSearchWithZone(false)
      }} maxWidth="sm" fullWidth>
        <DialogTitle>Choisir une zone Roon</DialogTitle>
        <DialogContent>
          <Stack spacing={1} sx={{ mt: 2 }}>
            {(roonZones || []).map((zone: any) => (
              <Button
                key={zone.zone_id}
                onClick={() => handleZoneClicked(zone.name)}
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
                disabled={playCollectionMutation.isPending || playAlbumMutation.isPending || playAlbumByNameMutation.isPending}
              >
                {zone.name}
              </Button>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'flex-end' }}>
          <Button onClick={() => {
            setRoonZoneDialogOpen(false)
            setPlayingFromSearchWithZone(false)
            setSelectedRoonZone('')
          }}>
            Annuler
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Recherche d'album dans Roon */}
      <Dialog open={searchAlbumDialogOpen} onClose={() => setSearchAlbumDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Rechercher un album dans Roon</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <TextField
              label="Artiste"
              value={searchArtist}
              onChange={(e) => setSearchArtist(e.target.value)}
              fullWidth
              disabled={searchAlbumMutation.isPending}
            />
            <TextField
              label="Titre de l'album"
              value={searchAlbumTitle}
              onChange={(e) => setSearchAlbumTitle(e.target.value)}
              fullWidth
              disabled={searchAlbumMutation.isPending}
            />
            
            {searchResult && (
              <Box sx={{
                p: 2,
                borderRadius: 1,
                backgroundColor: searchResult.found ? '#e8f5e9' : '#ffebee',
                border: `1px solid ${searchResult.found ? '#4caf50' : '#f44336'}`
              }}>
                {searchResult.found ? (
                  <Stack spacing={1}>
                    <Typography variant="body2" color="success.dark" sx={{ fontWeight: 'bold' }}>
                      ✓ Album trouvé!
                    </Typography>
                    <Typography variant="body2">
                      <strong>Nom exact:</strong> {searchResult.exact_name}
                    </Typography>
                    {searchResult.artist && (
                      <Typography variant="body2">
                        <strong>Artiste:</strong> {searchResult.artist}
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.secondary">
                      Vous pouvez maintenant jouer cet album sur Roon.
                    </Typography>
                  </Stack>
                ) : (
                  <Stack spacing={1}>
                    <Typography variant="body2" color="error.dark" sx={{ fontWeight: 'bold' }}>
                      ✗ Album non trouvé
                    </Typography>
                    <Typography variant="body2">
                      {searchResult.message || `Album '${searchResult.album}' non trouvé pour '${searchResult.artist}'`}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Vérifiez que cet album est importé dans votre bibliothèque Roon.
                    </Typography>
                  </Stack>
                )}
              </Box>
            )}

            {searchAlbumMutation.isPending && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                <CircularProgress size={20} />
                <Typography variant="body2">Recherche en cours...</Typography>
              </Box>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setSearchAlbumDialogOpen(false)} 
            disabled={searchAlbumMutation.isPending || playingFromSearch}
          >
            Fermer
          </Button>
          {searchResult?.found && (
            <Button 
              onClick={handlePlayAlbumFromSearch} 
              variant="contained"
              color="success"
              disabled={playingFromSearch || searchAlbumMutation.isPending}
            >
              {playingFromSearch ? 'Lancement...' : '▶️ Jouer sur Roon'}
            </Button>
          )}
          <Button 
            onClick={handleSearchAlbumSubmit} 
            variant="contained"
            disabled={searchAlbumMutation.isPending || !searchArtist.trim() || !searchAlbumTitle.trim()}
          >
            Rechercher
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar pour les notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
