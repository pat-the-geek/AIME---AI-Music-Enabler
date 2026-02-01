import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Avatar,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Paper,
  Stack,
  ToggleButtonGroup,
  ToggleButton,
  Divider,
  Snackbar,
  Alert,
} from '@mui/material'
import {
  Favorite,
  FavoriteBorder,
  ExpandMore,
  FilterList,
  ViewList,
  ViewModule,
  PlayArrow,
} from '@mui/icons-material'
import ReactMarkdown from 'react-markdown'
import apiClient from '@/api/client'
import type { ListeningHistory, PaginatedResponse } from '@/types/models'
import AlbumDetailDialog from '@/components/AlbumDetailDialog'
import { useRoon } from '@/contexts/RoonContext'

export default function Journal() {
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [artistFilter, setArtistFilter] = useState('')
  const [albumFilter, setAlbumFilter] = useState('')
  const [lovedFilter, setLovedFilter] = useState<string>('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [viewMode, setViewMode] = useState<'detailed' | 'compact'>('detailed')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedAlbumId, setSelectedAlbumId] = useState<number | null>(null)
  const [albumDialogOpen, setAlbumDialogOpen] = useState(false)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  })

  const queryClient = useQueryClient()
  const { enabled: roonEnabled, available: roonAvailable, playTrack } = useRoon()

  // Debounce de la recherche
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput)
      setPage(1)
    }, 500)
    return () => clearTimeout(timer)
  }, [searchInput])

  const { data, isLoading, isFetching } = useQuery<PaginatedResponse<ListeningHistory>>({
    queryKey: ['history', page, search, artistFilter, albumFilter, lovedFilter, startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '50',
      })
      if (artistFilter) params.append('artist', artistFilter)
      if (albumFilter) params.append('album', albumFilter)
      if (lovedFilter !== 'all') params.append('loved', lovedFilter)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      const response = await apiClient.get(`/history/tracks?${params}`)
      return response.data
    },
  })

  // Stats en temps réel
  const { data: stats } = useQuery({
    queryKey: ['history-stats', startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      const response = await apiClient.get(`/history/stats?${params}`)
      return response.data
    },
  })

  const toggleLoveMutation = useMutation({
    mutationFn: async (trackId: number) => {
      await apiClient.post(`/history/tracks/${trackId}/love`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
    },
  })

  const handleToggleLove = (trackId: number) => {
    toggleLoveMutation.mutate(trackId)
  }

  const handlePlayOnRoon = async (trackId: number) => {
    try {
      await playTrack(trackId)
      setSnackbar({ open: true, message: 'Lecture démarrée sur Roon', severity: 'success' })
    } catch (error: any) {
      setSnackbar({ open: true, message: error.message || 'Erreur lors de la lecture sur Roon', severity: 'error' })
    }
  }

  const handleResetFilters = () => {
    setSearchInput('')
    setSearch('')
    setArtistFilter('')
    setAlbumFilter('')
    setLovedFilter('all')
    setStartDate('')
    setEndDate('')
    setPage(1)
  }

  const handleOpenAlbumDetail = (albumId: number | undefined) => {
    if (albumId) {
      setSelectedAlbumId(albumId)
      setAlbumDialogOpen(true)
    }
  }

  const handleCloseAlbumDetail = () => {
    setAlbumDialogOpen(false)
    setSelectedAlbumId(null)
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', gap: 3 }}>
      {/* Contenu principal */}
      <Box sx={{ flex: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">
            Journal d'Écoute
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(_, newMode) => newMode && setViewMode(newMode)}
              size="small"
            >
              <ToggleButton value="detailed">
                <ViewList />
              </ToggleButton>
              <ToggleButton value="compact">
                <ViewModule />
              </ToggleButton>
            </ToggleButtonGroup>
            
            <Button
              variant="outlined"
              startIcon={<FilterList />}
              onClick={() => setShowFilters(!showFilters)}
            >
              Filtres
            </Button>
          </Box>
        </Box>

        {/* Filtres */}
        {showFilters && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Rechercher"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Titre, artiste, album..."
                  size="small"
                />
              </Grid>
              
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Artiste"
                  value={artistFilter}
                  onChange={(e) => setArtistFilter(e.target.value)}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Album"
                  value={albumFilter}
                  onChange={(e) => setAlbumFilter(e.target.value)}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={12} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Favoris</InputLabel>
                  <Select
                    value={lovedFilter}
                    label="Favoris"
                    onChange={(e) => setLovedFilter(e.target.value)}
                  >
                    <MenuItem value="all">Tous</MenuItem>
                    <MenuItem value="true">Favoris uniquement</MenuItem>
                    <MenuItem value="false">Non favoris</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Date début"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Date fin"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={handleResetFilters}
                >
                  Réinitialiser
                </Button>
              </Grid>
            </Grid>
          </Paper>
        )}

        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {data?.total || 0} écoutes {isFetching && <CircularProgress size={16} sx={{ ml: 1 }} />}
          </Typography>
          
          {data && data.pages > 1 && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                size="small"
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                Précédent
              </Button>
              <Typography variant="body2" sx={{ alignSelf: 'center', px: 2 }}>
                Page {page} / {data.pages}
              </Typography>
              <Button
                size="small"
                disabled={page >= data.pages}
                onClick={() => setPage(p => p + 1)}
              >
                Suivant
              </Button>
            </Box>
          )}
        </Box>

        {/* Liste des écoutes */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: viewMode === 'detailed' ? 2 : 1 }}>
          {data?.items.map((entry) => (
            <Card 
              key={entry.id} 
              sx={{ 
                ...(viewMode === 'compact' && { py: 0.5 }),
                cursor: entry.album_id ? 'pointer' : 'default',
                '&:hover': entry.album_id ? {
                  boxShadow: 2,
                  backgroundColor: 'action.hover'
                } : {}
              }}
            >
              <CardContent sx={{ ...(viewMode === 'compact' && { py: 1, '&:last-child': { pb: 1 } }) }}>
                <Grid container spacing={2} alignItems="center">
                  {viewMode === 'detailed' && (
                    <>
                      <Grid item>
                        <Avatar
                          src={entry.artist_image}
                          alt={entry.artist}
                          sx={{ width: 60, height: 60 }}
                        />
                      </Grid>
                      
                      <Grid item>
                        <Avatar
                          src={entry.album_image || entry.album_lastfm_image}
                          alt={entry.album}
                          sx={{ 
                            width: 60, 
                            height: 60,
                            cursor: entry.album_id ? 'pointer' : 'default',
                            '&:hover': entry.album_id ? {
                              opacity: 0.8,
                              transform: 'scale(1.05)'
                            } : {}
                          }}
                          variant="rounded"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenAlbumDetail(entry.album_id)
                          }}
                        />
                      </Grid>
                    </>
                  )}

                  <Grid item xs onClick={() => handleOpenAlbumDetail(entry.album_id)}>
                    <Typography variant={viewMode === 'detailed' ? 'h6' : 'body1'}>
                      {entry.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {entry.artist}
                    </Typography>
                    {viewMode === 'detailed' && (
                      <Typography variant="caption" color="text.secondary">
                        {entry.album}{entry.year ? ` (${entry.year})` : ''}
                      </Typography>
                    )}
                    <Box sx={{ mt: 0.5 }}>
                      <Chip
                        label={new Date(entry.timestamp * 1000).toLocaleString('fr-FR')}
                        size="small"
                        variant="outlined"
                      />
                      {viewMode === 'detailed' && (
                        <Chip
                          label={entry.source}
                          size="small"
                          variant="outlined"
                          sx={{ ml: 1 }}
                        />
                      )}
                      {viewMode === 'detailed' && entry.spotify_url && (
                        <Chip
                          label="🎵 Spotify"
                          size="small"
                          color="success"
                          variant="outlined"
                          sx={{ ml: 1 }}
                        />
                      )}
                      {viewMode === 'detailed' && entry.discogs_url && (
                        <Chip
                          label="📀 Discogs"
                          size="small"
                          color="info"
                          variant="outlined"
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Box>
                  </Grid>

                  <Grid item>
                    {roonEnabled && roonAvailable && (
                      <IconButton 
                        onClick={(e) => {
                          e.stopPropagation()
                          handlePlayOnRoon(entry.id)
                        }}
                        color="primary"
                        title="Écouter sur Roon"
                      >
                        <PlayArrow />
                      </IconButton>
                    )}
                    <IconButton onClick={() => handleToggleLove(entry.id)}>
                      {entry.loved ? (
                        <Favorite color="error" />
                      ) : (
                        <FavoriteBorder />
                      )}
                    </IconButton>
                  </Grid>
                </Grid>

                {viewMode === 'detailed' && entry.ai_info && (
                  <Accordion sx={{ mt: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography>🤖 Description IA</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box sx={{ '& p': { mb: 1 }, '& em': { fontStyle: 'italic' }, '& strong': { fontWeight: 'bold' } }}>
                        <ReactMarkdown>{entry.ai_info}</ReactMarkdown>
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      </Box>

      {/* Sidebar Stats */}
      <Paper sx={{ width: 280, p: 2, height: 'fit-content', position: 'sticky', top: 20 }}>
        <Typography variant="h6" gutterBottom>
          📊 Statistiques
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        {stats ? (
          <Stack spacing={2}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Total écoutes
              </Typography>
              <Typography variant="h4">
                {stats.total_tracks || 0}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="caption" color="text.secondary">
                Artistes uniques
              </Typography>
              <Typography variant="h5">
                {stats.unique_artists || 0}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="caption" color="text.secondary">
                Albums uniques
              </Typography>
              <Typography variant="h5">
                {stats.unique_albums || 0}
              </Typography>
            </Box>
            
            {stats.peak_hour !== null && (
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Heure de pointe
                </Typography>
                <Typography variant="h5">
                  {stats.peak_hour}h
                </Typography>
              </Box>
            )}
            
            {stats.total_duration_seconds && (
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Durée totale
                </Typography>
                <Typography variant="body1">
                  {Math.floor(stats.total_duration_seconds / 3600)}h {Math.floor((stats.total_duration_seconds % 3600) / 60)}min
                </Typography>
              </Box>
            )}
          </Stack>
        ) : (
          <CircularProgress size={24} />
        )}
      </Paper>

      {/* Dialog de détail d'album */}
      <AlbumDetailDialog
        albumId={selectedAlbumId}
        open={albumDialogOpen}
        onClose={handleCloseAlbumDetail}
      />

      {/* Snackbar pour les notifications */}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={4000} 
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
