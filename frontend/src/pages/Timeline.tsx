import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Paper,
  Avatar,
  Chip,
  IconButton,
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
  Stack,
  Divider,
  Card,
  CardContent,
} from '@mui/material'
import {
  NavigateBefore,
  NavigateNext,
  ViewList,
  ViewModule,
  Favorite,
} from '@mui/icons-material'
import apiClient from '@/api/client'
import AlbumDetailDialog from '@/components/AlbumDetailDialog'

interface TimelineData {
  date: string
  hours: Record<string, Array<{
    id: number
    time: string
    artist: string
    title: string
    album: string
    album_id?: number
    loved: boolean
    album_image?: string
    album_lastfm_image?: string
    year?: number
    spotify_url?: string
    discogs_url?: string
  }>>
  stats: {
    total_tracks: number
    unique_artists: number
    unique_albums: number
    peak_hour: number | null
  }
}

export default function Timeline() {
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [viewMode, setViewMode] = useState<'detailed' | 'compact'>('detailed')
  const [selectedAlbumId, setSelectedAlbumId] = useState<number | null>(null)
  const [albumDialogOpen, setAlbumDialogOpen] = useState(false)

  const { data, isLoading } = useQuery<TimelineData>({
    queryKey: ['timeline', selectedDate],
    queryFn: async () => {
      const response = await apiClient.get(`/history/timeline?date=${selectedDate}`)
      return response.data
    },
  })

  const handlePrevDay = () => {
    const date = new Date(selectedDate)
    date.setDate(date.getDate() - 1)
    setSelectedDate(date.toISOString().split('T')[0])
  }

  const handleNextDay = () => {
    const date = new Date(selectedDate)
    date.setDate(date.getDate() + 1)
    setSelectedDate(date.toISOString().split('T')[0])
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('fr-FR', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(date)
  }

  const getHourColor = (hour: number) => {
    // Alternance de couleurs pour faciliter la lecture
    return hour % 2 === 0 ? 'background.default' : 'action.hover'
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

  // Plage horaire 6h-23h (configurable)
  const hourRange = Array.from({ length: 18 }, (_, i) => i + 6)

  return (
    <Box>
      {/* Header avec navigation */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <IconButton onClick={handlePrevDay}>
            <NavigateBefore />
          </IconButton>
          
          <Typography variant="h5" sx={{ textTransform: 'capitalize' }}>
            {formatDate(selectedDate)}
          </Typography>
          
          <IconButton onClick={handleNextDay} disabled={selectedDate >= new Date().toISOString().split('T')[0]}>
            <NavigateNext />
          </IconButton>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Stack direction="row" spacing={3}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Total écoutes
              </Typography>
              <Typography variant="h6">
                {data?.stats.total_tracks || 0}
              </Typography>
            </Box>
            
            <Divider orientation="vertical" flexItem />
            
            <Box>
              <Typography variant="caption" color="text.secondary">
                Artistes uniques
              </Typography>
              <Typography variant="h6">
                {data?.stats.unique_artists || 0}
              </Typography>
            </Box>
            
            <Divider orientation="vertical" flexItem />
            
            <Box>
              <Typography variant="caption" color="text.secondary">
                Albums uniques
              </Typography>
              <Typography variant="h6">
                {data?.stats.unique_albums || 0}
              </Typography>
            </Box>
            
            {data?.stats?.peak_hour !== null && (
              <>
                <Divider orientation="vertical" flexItem />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Heure de pointe
                  </Typography>
                  <Typography variant="h6">
                    {data?.stats?.peak_hour}h
                  </Typography>
                </Box>
              </>
            )}
          </Stack>

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
        </Box>
      </Paper>

      {/* Timeline horaire avec scroll horizontal */}
      <Box sx={{ overflowX: 'auto', pb: 2 }}>
        <Box sx={{ display: 'flex', minWidth: 'max-content', gap: 0 }}>
          {hourRange.map((hour) => {
            const tracks = data?.hours[String(hour)] || []
            const displayTracks = tracks.slice(0, 20) // Limite 20 tracks/heure
            const hasMore = tracks.length > 20

            return (
              <Paper
                key={hour}
                sx={{
                  minWidth: viewMode === 'detailed' ? 320 : 180,
                  backgroundColor: getHourColor(hour),
                  borderRadius: 0,
                  borderRight: '1px solid',
                  borderColor: 'divider',
                }}
              >
                {/* Header heure */}
                <Box
                  sx={{
                    p: 1.5,
                    backgroundColor: hour === data?.stats.peak_hour ? 'primary.main' : 'action.selected',
                    color: hour === data?.stats.peak_hour ? 'primary.contrastText' : 'text.primary',
                    textAlign: 'center',
                    fontWeight: 'bold',
                  }}
                >
                  <Typography variant="h6">
                    {hour}h
                  </Typography>
                  <Typography variant="caption">
                    {tracks.length} {tracks.length > 1 ? 'écoutes' : 'écoute'}
                  </Typography>
                </Box>

                {/* Liste des tracks */}
                <Box sx={{ p: viewMode === 'detailed' ? 1.5 : 0.5 }}>
                  {displayTracks.length === 0 ? (
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: 'block', textAlign: 'center', py: 2 }}
                    >
                      Aucune écoute
                    </Typography>
                  ) : (
                    <Stack spacing={viewMode === 'detailed' ? 1.5 : 0.5}>
                      {displayTracks.map((track) => (
                        <Card
                          key={track.id}
                          variant="outlined"
                          sx={{ 
                            ...(viewMode === 'compact' && { py: 0.5 }),
                            cursor: track.album_id ? 'pointer' : 'default',
                            '&:hover': track.album_id ? {
                              backgroundColor: 'action.hover',
                            } : {}
                          }}
                          onClick={() => handleOpenAlbumDetail(track.album_id)}
                        >
                          <CardContent sx={{ p: viewMode === 'detailed' ? 1.5 : 1, '&:last-child': { pb: viewMode === 'detailed' ? 1.5 : 1 } }}>
                            {viewMode === 'detailed' ? (
                              <Box>
                                <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
                                  {/* Pochette album */}
                                  {(track.album_image || track.album_lastfm_image) && (
                                    <Avatar
                                      src={track.album_image || track.album_lastfm_image}
                                      alt={track.album}
                                      variant="rounded"
                                      sx={{ width: 56, height: 56 }}
                                    />
                                  )}
                                  
                                  {/* Métadonnées */}
                                  <Box sx={{ flex: 1, minWidth: 0 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                                      <Chip label={track.time} size="small" />
                                      {track.loved && <Favorite color="error" fontSize="small" />}
                                    </Box>
                                    <Typography variant="subtitle2" noWrap>
                                      {track.title}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary" noWrap>
                                      {track.artist}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary" display="block" noWrap>
                                      {track.album}{track.year ? ` (${track.year})` : ''}
                                    </Typography>
                                    {(track.spotify_url || track.discogs_url) && (
                                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                                        {track.spotify_url && (
                                          <Chip
                                            label="🎵"
                                            size="small"
                                            color="success"
                                            sx={{ height: 20, fontSize: '0.7rem' }}
                                          />
                                        )}
                                        {track.discogs_url && (
                                          <Chip
                                            label="📀"
                                            size="small"
                                            color="info"
                                            sx={{ height: 20, fontSize: '0.7rem' }}
                                          />
                                        )}
                                      </Box>
                                    )}
                                  </Box>
                                </Box>
                              </Box>
                            ) : (
                              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                {/* Pochette compacte */}
                                {(track.album_image || track.album_lastfm_image) && (
                                  <Avatar
                                    src={track.album_image || track.album_lastfm_image}
                                    alt={track.album}
                                    variant="rounded"
                                    sx={{ width: 40, height: 40 }}
                                  />
                                )}
                                
                                {/* Métadonnées compactes */}
                                <Box sx={{ flex: 1, minWidth: 0 }}>
                                  <Typography variant="caption" display="block" noWrap>
                                    {track.time} {track.loved && '❤️'}
                                  </Typography>
                                  <Typography variant="caption" fontWeight="bold" display="block" noWrap>
                                    {track.title}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" display="block" noWrap>
                                    {track.artist}
                                  </Typography>
                                </Box>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                      
                      {hasMore && (
                        <Typography variant="caption" color="text.secondary" textAlign="center">
                          + {tracks.length - 20} écoutes supplémentaires
                        </Typography>
                      )}
                    </Stack>
                  )}
                </Box>
              </Paper>
            )
          })}
        </Box>
      </Box>

      {/* Légende */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          💡 <strong>Astuce :</strong> Faites défiler horizontalement pour voir toutes les heures. 
          La limite est de 20 écoutes affichées par heure pour des raisons de performance.
          {data?.stats?.peak_hour !== null && ` L'heure de pointe (${data?.stats?.peak_hour}h) est mise en évidence.`}
          {' '}Cliquez sur une écoute pour voir les détails de l'album.
        </Typography>
      </Paper>

      {/* Dialog de détail d'album */}
      <AlbumDetailDialog
        albumId={selectedAlbumId}
        open={albumDialogOpen}
        onClose={handleCloseAlbumDetail}
      />
    </Box>
  )
}
