import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Chip,
  Stack,
  Divider,
  IconButton,
} from '@mui/material'
import { Close as CloseIcon, Info as InfoIcon } from '@mui/icons-material'
import apiClient from '@/api/client'
import type { Album, AlbumDetail, PaginatedResponse } from '@/types/models'

export default function Collection() {
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [support, setSupport] = useState('')
  const [sortBy, setSortBy] = useState('title')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [selectedAlbum, setSelectedAlbum] = useState<number | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  // Debounce de la recherche pour éviter de perdre le focus
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput)
      setPage(1)
    }, 500)

    return () => clearTimeout(timer)
  }, [searchInput])

  const { data, isLoading } = useQuery<PaginatedResponse<Album>>({
    queryKey: ['albums', page, search, support, sortBy, sortOrder],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '30',
      })
      if (search) params.append('search', search)
      if (support) params.append('support', support)
      
      const response = await apiClient.get(`/collection/albums?${params}`)
      
      // Tri côté client (en attendant l'implémentation backend)
      const sortedItems = [...response.data.items].sort((a, b) => {
        let aVal: any = a[sortBy as keyof Album]
        let bVal: any = b[sortBy as keyof Album]
        
        // Gestion spéciale pour les artistes (tableau)
        if (sortBy === 'artists') {
          aVal = a.artists[0] || ''
          bVal = b.artists[0] || ''
        }
        
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return sortOrder === 'asc' 
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal)
        }
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        }
        
        return 0
      })
      
      return { ...response.data, items: sortedItems }
    },
  })

  const { data: albumDetail, isLoading: detailLoading } = useQuery<AlbumDetail>({
    queryKey: ['album', selectedAlbum],
    queryFn: async () => {
      const response = await apiClient.get(`/collection/albums/${selectedAlbum}`)
      return response.data
    },
    enabled: selectedAlbum !== null,
  })

  const handleOpenDetail = (albumId: number) => {
    setSelectedAlbum(albumId)
    setDetailOpen(true)
  }

  const handleCloseDetail = () => {
    setDetailOpen(false)
    setSelectedAlbum(null)
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
        Collection Discogs
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            label="Rechercher"
            variant="outlined"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            sx={{ flexGrow: 1 }}
            placeholder="Recherche par titre, artiste..."
          />
          
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Support</InputLabel>
            <Select
              value={support}
              label="Support"
              onChange={(e) => {
                setSupport(e.target.value)
                setPage(1)
              }}
            >
              <MenuItem value="">Tous</MenuItem>
              <MenuItem value="Vinyle">Vinyle</MenuItem>
              <MenuItem value="CD">CD</MenuItem>
              <MenuItem value="Digital">Digital</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Trier par:
          </Typography>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Champ</InputLabel>
            <Select
              value={sortBy}
              label="Champ"
              onChange={(e) => setSortBy(e.target.value)}
            >
              <MenuItem value="title">Titre</MenuItem>
              <MenuItem value="artists">Artiste</MenuItem>
              <MenuItem value="year">Année</MenuItem>
              <MenuItem value="support">Support</MenuItem>
              <MenuItem value="created_at">Date d'ajout</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Ordre</InputLabel>
            <Select
              value={sortOrder}
              label="Ordre"
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
            >
              <MenuItem value="asc">Croissant</MenuItem>
              <MenuItem value="desc">Décroissant</MenuItem>
            </Select>
          </FormControl>

          <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
            {data?.total || 0} albums
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {data?.items.map((album) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={album.id}>
            <Card 
              sx={{ 
                cursor: 'pointer', 
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': { 
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={() => handleOpenDetail(album.id)}
            >
              <CardMedia
                component="img"
                height="200"
                image={album.images[0] || 'https://via.placeholder.com/200'}
                alt={album.title}
                sx={{ objectFit: 'cover' }}
              />
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="h6" sx={{ flexGrow: 1, pr: 1 }} noWrap>
                    {album.title}
                  </Typography>
                  <IconButton size="small" color="primary">
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Box>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {album.artists.join(', ')}
                </Typography>
                <Box sx={{ mt: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    {album.year || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">•</Typography>
                  <Chip label={album.support || 'Unknown'} size="small" />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Pagination
          count={data?.pages || 0}
          page={page}
          onChange={(_, value) => setPage(value)}
          color="primary"
        />
      </Box>

      {/* Modal de détails */}
      <Dialog 
        open={detailOpen} 
        onClose={handleCloseDetail}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h5">
              {albumDetail?.title || 'Chargement...'}
            </Typography>
            <IconButton onClick={handleCloseDetail}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers>
          {detailLoading ? (
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
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button 
                          variant="outlined" 
                          size="small"
                          href={albumDetail.discogs_url}
                          target="_blank"
                        >
                          Voir sur Discogs
                        </Button>
                        {albumDetail.spotify_url && (
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
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      🤖 Description IA
                    </Typography>
                    <Typography 
                      variant="body1" 
                      sx={{ 
                        whiteSpace: 'pre-wrap',
                        backgroundColor: 'action.hover',
                        p: 2,
                        borderRadius: 1,
                        lineHeight: 1.7
                      }}
                    >
                      {albumDetail.ai_info}
                    </Typography>
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
          <Button onClick={handleCloseDetail}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
