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
  Chip,
  IconButton,
  Button,
  Menu,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Alert,
} from '@mui/material'
import { 
  Info as InfoIcon,
  FileDownload as FileDownloadIcon,
  Description as DescriptionIcon,
  Album as AlbumIcon,
} from '@mui/icons-material'
import apiClient from '@/api/client'
import type { Album, PaginatedResponse } from '@/types/models'
import AlbumDetailDialog from '@/components/AlbumDetailDialog'

export default function Collection() {
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [support, setSupport] = useState('')
  const [sortBy, setSortBy] = useState('title')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [selectedAlbum, setSelectedAlbum] = useState<number | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null)
  const [randomMode, setRandomMode] = useState(false)
  const [randomCount, setRandomCount] = useState(5)
  const [randomAlbums, setRandomAlbums] = useState<Album[]>([])
  const [markdownGenerating, setMarkdownGenerating] = useState(false)
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarMessage, setSnackbarMessage] = useState('')
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info'>('info')

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

  const handleOpenDetail = (albumId: number) => {
    setSelectedAlbum(albumId)
    setDetailOpen(true)
  }

  const handleCloseDetail = () => {
    setDetailOpen(false)
    setSelectedAlbum(null)
  }

  const handleRandomAlbums = () => {
    if (!data?.items || data.items.length === 0) return
    
    const count = Math.min(randomCount, data.items.length)
    const shuffled = [...data.items].sort(() => Math.random() - 0.5)
    setRandomAlbums(shuffled.slice(0, count))
    setRandomMode(true)
  }

  const handleCloseRandom = () => {
    setRandomMode(false)
    setRandomAlbums([])
  }

  const handleGenerateMarkdownPresentation = async () => {
    if (randomAlbums.length === 0) {
      setSnackbarMessage('Aucun album sélectionné')
      setSnackbarSeverity('error')
      setSnackbarOpen(true)
      return
    }

    setMarkdownGenerating(true)
    try {
      setSnackbarMessage('Génération de la présentation en cours...')
      setSnackbarSeverity('info')
      setSnackbarOpen(true)

      const response = await apiClient.post('/collection/markdown/presentation', {
        album_ids: randomAlbums.map(a => a.id),
        include_haiku: true,
      })

      const markdown = response.data.markdown
      
      // Créer un Blob et télécharger le fichier
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `presentation-albums-${new Date().toISOString().split('T')[0]}.md`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setSnackbarMessage(`✅ Présentation générée avec ${randomAlbums.length} albums`)
      setSnackbarSeverity('success')
      setSnackbarOpen(true)
    } catch (error) {
      console.error('Erreur lors de la génération du markdown:', error)
      setSnackbarMessage('❌ Erreur lors de la génération de la présentation')
      setSnackbarSeverity('error')
      setSnackbarOpen(true)
    } finally {
      setMarkdownGenerating(false)
    }
  }

  const handleExportMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget)
  }

  const handleExportMenuClose = () => {
    setExportMenuAnchor(null)
  }

  const handleExportCollection = async () => {
    try {
      const response = await apiClient.get('/collection/export/markdown', {
        responseType: 'blob',
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'collection-discogs.md')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Erreur lors de l\'export:', error)
    } finally {
      handleExportMenuClose()
    }
  }

  const handleExportVinyl = async () => {
    try {
      const response = await apiClient.get('/collection/export/markdown/support/Vinyle', {
        responseType: 'blob',
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'collection-vinyle.md')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Erreur lors de l\'export:', error)
    } finally {
      handleExportMenuClose()
    }
  }

  const handleExportCD = async () => {
    try {
      const response = await apiClient.get('/collection/export/markdown/support/CD', {
        responseType: 'blob',
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'collection-cd.md')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Erreur lors de l\'export:', error)
    } finally {
      handleExportMenuClose()
    }
  }

  const handleExportCollectionJSON = async () => {
    console.log('🔍 handleExportCollectionJSON appelé')
    try {
      console.log('📡 Appel API: /collection/export/json')
      const response = await apiClient.get('/collection/export/json', {
        responseType: 'blob',
      })
      console.log('✅ Réponse reçue:', response.status, response.data.size, 'bytes')
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'collection-discogs.json')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      console.log('💾 Téléchargement lancé')
    } catch (error) {
      console.error('❌ Erreur lors de l\'export:', error)
    } finally {
      handleExportMenuClose()
    }
  }

  const handleExportVinylJSON = async () => {
    console.log('🔍 handleExportVinylJSON appelé')
    try {
      console.log('📡 Appel API: /collection/export/json/support/Vinyle')
      const response = await apiClient.get('/collection/export/json/support/Vinyle', {
        responseType: 'blob',
      })
      console.log('✅ Réponse reçue:', response.status, response.data.size, 'bytes')
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'collection-vinyle.json')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      console.log('💾 Téléchargement lancé')
    } catch (error) {
      console.error('❌ Erreur lors de l\'export:', error)
    } finally {
      handleExportMenuClose()
    }
  }

  const handleExportCDJSON = async () => {
    console.log('🔍 handleExportCDJSON appelé')
    try {
      console.log('📡 Appel API: /collection/export/json/support/CD')
      const response = await apiClient.get('/collection/export/json/support/CD', {
        responseType: 'blob',
      })
      console.log('✅ Réponse reçue:', response.status, response.data.size, 'bytes')
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'collection-cd.json')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      console.log('💾 Téléchargement lancé')
    } catch (error) {
      console.error('❌ Erreur lors de l\'export:', error)
    } finally {
      handleExportMenuClose()
    }
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="h4">
          Collection Discogs
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            onClick={() => {
              const input = prompt(`Nombre d'albums aléatoires (max ${data?.items?.length || 30}):`, randomCount.toString())
              if (input) {
                const count = Math.min(parseInt(input) || 5, data?.items?.length || 30)
                setRandomCount(count)
                // Déclenche après mise à jour du count
                setTimeout(() => {
                  if (!data?.items || data.items.length === 0) return
                  const c = Math.min(count, data.items.length)
                  const shuffled = [...data.items].sort(() => Math.random() - 0.5)
                  setRandomAlbums(shuffled.slice(0, c))
                  setRandomMode(true)
                }, 0)
              }
            }}
          >
            🎲 Random
          </Button>
          
          <Button
            variant="contained"
            startIcon={<FileDownloadIcon />}
            onClick={handleExportMenuOpen}
          >
            Exporter
          </Button>
        </Box>
        
        <Menu
          anchorEl={exportMenuAnchor}
          open={Boolean(exportMenuAnchor)}
          onClose={handleExportMenuClose}
        >
          <MenuItem onClick={handleExportCollection}>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Collection complète" secondary={`${data?.total || 0} albums`} />
          </MenuItem>
          
          <MenuItem onClick={handleExportVinyl}>
            <ListItemIcon>
              <AlbumIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Vinyles uniquement" />
          </MenuItem>
          
          <MenuItem onClick={handleExportCD}>
            <ListItemIcon>
              <AlbumIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="CD uniquement" />
          </MenuItem>
          
          <MenuItem onClick={handleExportCollectionJSON}>
            <ListItemIcon>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Collection complète (JSON)" secondary={`${data?.total || 0} albums`} />
          </MenuItem>
          
          <MenuItem onClick={handleExportVinylJSON}>
            <ListItemIcon>
              <AlbumIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Vinyles uniquement (JSON)" />
          </MenuItem>
          
          <MenuItem onClick={handleExportCDJSON}>
            <ListItemIcon>
              <AlbumIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="CD uniquement (JSON)" />
          </MenuItem>
        </Menu>
      </Box>

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
        {randomMode && randomAlbums.length > 0 ? (
          <>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6">
                  🎲 {randomAlbums.length} albums aléatoires
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button 
                    size="small" 
                    onClick={handleGenerateMarkdownPresentation}
                    variant="contained"
                    disabled={markdownGenerating}
                    startIcon={markdownGenerating ? <CircularProgress size={20} /> : <DescriptionIcon />}
                  >
                    {markdownGenerating ? 'Génération...' : '📄 Générer Markdown'}
                  </Button>
                  <Button 
                    size="small" 
                    onClick={handleCloseRandom}
                    variant="text"
                  >
                    Fermer le mode random
                  </Button>
                </Box>
              </Box>
            </Grid>
            {randomAlbums.map((album) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={album.id}>
                <Card 
                  sx={{ 
                    cursor: 'pointer', 
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': { 
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => handleOpenDetail(album.id)}
                >
                  <CardMedia
                    component="img"
                    height="200"
                    image={album.images?.[0] || 'https://via.placeholder.com/200'}
                    alt={album.title}
                    sx={{ objectFit: 'cover' }}
                  />
                  <CardContent>
                    <Typography variant="h6" noWrap>
                      {album.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {album.artists?.join(', ')}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1, gap: 1, flexWrap: 'wrap' }}>
                      {album.year && (
                        <Chip label={album.year} size="small" />
                      )}
                      <Chip label={album.support} size="small" variant="outlined" />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </>
        ) : (
          <>
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
          </>
        )}
      </Grid>

      {!randomMode && (
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
          <Pagination
            count={data?.pages || 0}
            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}
      <AlbumDetailDialog
        albumId={selectedAlbum}
        open={detailOpen}
        onClose={handleCloseDetail}
      />

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  )
}
