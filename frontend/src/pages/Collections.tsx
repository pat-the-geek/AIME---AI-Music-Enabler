import { useState } from 'react'
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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Stack,
  Snackbar,
  IconButton,
  Tooltip,
  CardMedia,
} from '@mui/material'
import { 
  Add, 
  PlayArrow, 
  Delete, 
  Search,
  LibraryMusic,
  Person,
  DateRange,
  Psychology,
} from '@mui/icons-material'
import apiClient from '../api/client'
import { useRoon } from '../contexts/RoonContext'
import { getHiddenContentSx, isEmptyContent } from '../utils/hideEmptyContent'

interface Collection {
  id: number
  name: string
  search_type: string | null
  search_criteria: Record<string, any> | null
  ai_query: string | null
  album_count: number
  created_at: string
}

interface Album {
  id: number
  title: string
  artist_name: string | null
  year: number | null
  image_url: string | null
  ai_description: string | null
}

const SEARCH_TYPES = [
  { value: 'genre', label: 'Par Genre', icon: <LibraryMusic />, description: 'Rock, Jazz, Electronic...' },
  { value: 'artist', label: 'Par Artiste', icon: <Person />, description: 'The Beatles, Miles Davis...' },
  { value: 'period', label: 'Par Période', icon: <DateRange />, description: 'Années 60, 90s...' },
  { value: 'ai_query', label: 'Recherche IA', icon: <Psychology />, description: 'Musique mélancolique, énergique...' },
]

export default function Collections() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [collectionName, setCollectionName] = useState('')
  const [searchType, setSearchType] = useState('ai_query')
  const [searchQuery, setSearchQuery] = useState('')
  const [startYear, setStartYear] = useState<number | null>(null)
  const [endYear, setEndYear] = useState<number | null>(null)
  const [zoneDialogOpen, setZoneDialogOpen] = useState(false)
  const [pendingCollectionId, setPendingCollectionId] = useState<number | null>(null)
  const [selectedZone, setSelectedZone] = useState<string>('')
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  })
  
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

  // Récupérer les zones Roon
  const { data: roonZones } = useQuery({
    queryKey: ['roon-zones'],
    queryFn: async () => {
      const response = await apiClient.get('/roon/zones')
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
      setZoneDialogOpen(false)
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

  const resetForm = () => {
    setCollectionName('')
    setSearchQuery('')
    setStartYear(null)
    setEndYear(null)
    setSearchType('ai_query')
  }

  const handleCreateCollection = () => {
    if (!collectionName.trim()) {
      setSnackbar({ open: true, message: 'Nom de collection requis', severity: 'error' })
      return
    }

    const payload: any = {
      name: collectionName,
      search_type: searchType
    }

    if (searchType === 'ai_query') {
      if (!searchQuery.trim()) {
        setSnackbar({ open: true, message: 'Requête de recherche requise', severity: 'error' })
        return
      }
      payload.ai_query = searchQuery
    } else if (searchType === 'period') {
      if (!startYear || !endYear) {
        setSnackbar({ open: true, message: 'Années de début et fin requises', severity: 'error' })
        return
      }
      payload.search_criteria = { start_year: startYear, end_year: endYear }
    } else {
      if (!searchQuery.trim()) {
        setSnackbar({ open: true, message: 'Critère de recherche requis', severity: 'error' })
        return
      }
      payload.search_criteria = { [searchType]: searchQuery }
    }

    createCollectionMutation.mutate(payload)
  }

  const handlePlayCollection = (collectionId: number) => {
    if (roonZones && roonZones.length > 0) {
      setPendingCollectionId(collectionId)
      setZoneDialogOpen(true)
    } else {
      playCollectionMutation.mutate({ collectionId })
    }
  }

  const handleZoneSelected = () => {
    if (pendingCollectionId) {
      setZoneDialogOpen(false)
      setPendingCollectionId(null)
      playCollectionMutation.mutate({ 
        collectionId: pendingCollectionId, 
        zoneName: selectedZone || undefined 
      })
    }
  }

  const handleViewDetails = (collectionId: number) => {
    setSelectedCollectionId(collectionId)
    setDetailDialogOpen(true)
  }

  const getSearchTypeLabel = (type: string | null) => {
    if (!type) return 'Personnalisée'
    const found = SEARCH_TYPES.find(st => st.value === type)
    return found ? found.label : type
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
        <DialogTitle>Découvrir une Nouvelle Collection</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Les albums proviennent de votre libraire Discogs et de votre historique des écoutes (Last.fm, Roon, etc).
          </Alert>
          <Stack spacing={3} mt={2}>
            <TextField
              label="Nom de la collection"
              fullWidth
              value={collectionName}
              onChange={(e) => setCollectionName(e.target.value)}
              placeholder="ex: Rock des années 90"
            />

            <FormControl fullWidth>
              <InputLabel>Type de recherche</InputLabel>
              <Select
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                label="Type de recherche"
              >
                {SEARCH_TYPES.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    <Box display="flex" alignItems="center" gap={1}>
                      {type.icon}
                      <Box>
                        <Typography variant="body1">{type.label}</Typography>
                        <Typography 
                          variant="caption" 
                          color="text.secondary"
                          sx={isEmptyContent(type.description) ? getHiddenContentSx(type.description) : {}}
                        >
                          {type.description}
                        </Typography>
                      </Box>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {searchType === 'period' ? (
              <Stack direction="row" spacing={2}>
                <TextField
                  label="Année de début"
                  type="number"
                  fullWidth
                  value={startYear || ''}
                  onChange={(e) => setStartYear(parseInt(e.target.value) || null)}
                  placeholder="1990"
                />
                <TextField
                  label="Année de fin"
                  type="number"
                  fullWidth
                  value={endYear || ''}
                  onChange={(e) => setEndYear(parseInt(e.target.value) || null)}
                  placeholder="1999"
                />
              </Stack>
            ) : (
              <TextField
                label={
                  searchType === 'ai_query' ? 'Requête IA' :
                  searchType === 'genre' ? 'Genre' :
                  searchType === 'artist' ? 'Artiste' :
                  'Recherche'
                }
                fullWidth
                multiline={searchType === 'ai_query'}
                rows={searchType === 'ai_query' ? 3 : 1}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={
                  searchType === 'ai_query' ? 'ex: musique mélancolique et atmosphérique' :
                  searchType === 'genre' ? 'ex: Rock, Jazz, Electronic' :
                  searchType === 'artist' ? 'ex: The Beatles' :
                  'Critère de recherche'
                }
                helperText={
                  searchType === 'ai_query' ? 
                    'Décrivez le type de musique que vous recherchez. L\'IA trouvera les albums correspondants.' :
                    undefined
                }
              />
            )}
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
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Albums de la Collection
        </DialogTitle>
        <DialogContent>
          {albumsLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : collectionAlbums && collectionAlbums.length > 0 ? (
            <Grid container spacing={2} mt={1}>
              {collectionAlbums.map((album) => (
                <Grid item xs={12} sm={6} key={album.id}>
                  <Card variant="outlined">
                    <Box display="flex">
                      {album.image_url && (
                        <CardMedia
                          component="img"
                          sx={{ width: 100, height: 100, objectFit: 'cover' }}
                          image={album.image_url}
                          alt={album.title}
                        />
                      )}
                      <CardContent sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {album.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {album.artist_name || 'Unknown Artist'}
                        </Typography>
                        {album.year && (
                          <Typography variant="caption" color="text.secondary">
                            {album.year}
                          </Typography>
                        )}
                      </CardContent>
                    </Box>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info">Aucun album dans cette collection</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Fermer</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Sélection de zone Roon */}
      <Dialog open={zoneDialogOpen} onClose={() => setZoneDialogOpen(false)}>
        <DialogTitle>Sélectionner une zone Roon</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Zone</InputLabel>
            <Select
              value={selectedZone}
              onChange={(e) => setSelectedZone(e.target.value)}
              label="Zone"
            >
              {(roonZones || []).map((zone: any) => (
                <MenuItem key={zone.zone_id} value={zone.name}>
                  {zone.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setZoneDialogOpen(false)}>Annuler</Button>
          <Button 
            onClick={handleZoneSelected} 
            variant="contained"
            disabled={!selectedZone || playCollectionMutation.isPending}
          >
            Jouer
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
