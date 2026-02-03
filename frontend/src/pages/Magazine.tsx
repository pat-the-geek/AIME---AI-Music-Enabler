import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Button,
  Container,
  CircularProgress,
  Stack,
  Paper,
  Snackbar,
  Alert,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material'
import { Refresh, History, Casino, List as ListIcon } from '@mui/icons-material'
import apiClient from '@/api/client'
import MagazinePage from '@/components/MagazinePage'

interface MagazinePage {
  page_number: number
  type: string
  title: string
  layout: string
  content: any
  dimensions?: any
}

interface Magazine {
  id: string
  edition_number?: number
  generated_at: string
  pages: MagazinePage[]
  total_pages: number
}

interface EditionMeta {
  id: string
  edition_number: number
  generated_at: string
  album_count: number
  page_count: number
  enrichment_completed: boolean
}

export default function Magazine() {
  const [currentPage, setCurrentPage] = useState(0)
  const [nextRefreshIn, setNextRefreshIn] = useState(900) // 15 minutes en secondes
  const [snackbar, setSnackbar] = useState({ open: false, message: '', type: 'info' as 'success' | 'error' | 'info' })
  const [usePregenerated, setUsePregenerated] = useState(true) // Par défaut, utiliser les éditions pré-générées
  const [selectedEditionId, setSelectedEditionId] = useState<string | null>(null)
  const [editionsMenuAnchor, setEditionsMenuAnchor] = useState<null | HTMLElement>(null)

  // Charger la liste des éditions disponibles
  const { data: editionsList } = useQuery({
    queryKey: ['magazine-editions'],
    queryFn: async () => {
      const response = await apiClient.get<{ count: number; editions: EditionMeta[] }>('/magazines/editions?limit=20')
      return response.data
    },
    enabled: usePregenerated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Charger le magazine
  const { data: magazine, isLoading, error, refetch } = useQuery({
    queryKey: ['magazine', usePregenerated, selectedEditionId],
    queryFn: async () => {
      if (usePregenerated) {
        // Charger une édition pré-générée (aléatoire ou spécifique)
        const endpoint = selectedEditionId 
          ? `/magazines/editions/${selectedEditionId}`
          : '/magazines/editions/random'
        
        try {
          const response = await apiClient.get<Magazine>(endpoint)
          return response.data
        } catch (error: any) {
          // Si aucune édition n'est disponible, générer un nouveau magazine
          if (error.response?.status === 404) {
            console.log('Aucune édition disponible, génération d\'un nouveau magazine...')
            const response = await apiClient.get<Magazine>('/magazines/generate')
            return response.data
          }
          throw error
        }
      } else {
        // Générer un nouveau magazine
        const response = await apiClient.get<Magazine>('/magazines/generate')
        return response.data
      }
    },
    staleTime: Infinity,
    retry: false, // Ne pas réessayer automatiquement
  })

  // Minuteur pour le rafraîchissement automatique
  useEffect(() => {
    const timer = setInterval(() => {
      setNextRefreshIn(prev => {
        if (prev <= 1) {
          // Rafraîchir le magazine
          refetch()
          setCurrentPage(0)
          showSnackbar('📖 Nouvelle édition générée !', 'success')
          return 900 // Reset à 15 minutes
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [refetch])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleNewEdition = () => {
    setSelectedEditionId(null)
    setUsePregenerated(true)
    refetch()
    setCurrentPage(0)
    setNextRefreshIn(900)
    showSnackbar('🎲 Nouvelle édition aléatoire chargée !', 'success')
  }

  const handleGenerateNew = () => {
    setSelectedEditionId(null)
    setUsePregenerated(false)
    refetch()
    setCurrentPage(0)
    setNextRefreshIn(900)
    showSnackbar('🔄 Nouvelle édition en cours de génération...', 'info')
  }

  const handleSelectEdition = (editionId: string) => {
    setSelectedEditionId(editionId)
    setUsePregenerated(true)
    setEditionsMenuAnchor(null)
    refetch()
    setCurrentPage(0)
    showSnackbar(`📖 Édition ${editionId} chargée !`, 'success')
  }

  const showSnackbar = (message: string, type: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, type })
  }

  const handleNavigate = (direction: 'next' | 'prev') => {
    if (!magazine) return

    const targetPage = direction === 'next' 
      ? Math.min(currentPage + 1, magazine.total_pages - 1)
      : Math.max(currentPage - 1, 0)
    
    setCurrentPage(targetPage)
    
    // Scroll vers la page
    const pageElement = document.getElementById(`page-${targetPage}`)
    if (pageElement) {
      pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  // Détecter la page visible lors du scroll naturel
  useEffect(() => {
    if (!magazine) return

    const options = {
      root: null,
      rootMargin: '-45% 0px -45% 0px',
      threshold: 0
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const pageIndex = parseInt(entry.target.id.split('-')[1])
          if (!isNaN(pageIndex)) {
            setCurrentPage(pageIndex)
          }
        }
      })
    }, options)

    // Observer chaque page
    magazine.pages.forEach((_, index) => {
      const element = document.getElementById(`page-${index}`)
      if (element) {
        observer.observe(element)
      }
    })

    return () => observer.disconnect()
  }, [magazine])

  if (isLoading) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        flexDirection: 'column',
        gap: 2
      }}>
        <CircularProgress size={60} />
        <Typography variant="h6">Génération du magazine...</Typography>
      </Box>
    )
  }

  if (error || !magazine) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        flexDirection: 'column',
        gap: 2
      }}>
        <Typography variant="h6" color="error">
          Erreur lors de la génération du magazine
        </Typography>
        <Button variant="contained" onClick={handleNewEdition}>
          Réessayer
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{
      width: '100%',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#ffffff',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <Paper elevation={3} sx={{
        position: 'sticky',
        top: 0,
        zIndex: 10,
        backgroundColor: '#ffffff',
        backdropFilter: 'blur(10px)',
        borderBottom: '2px solid #c41e3a',
        padding: '16px 24px'
      }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4" sx={{
              fontFamily: '"Playfair Display", "Georgia", serif',
              fontWeight: 700,
              background: 'linear-gradient(135deg, #c41e3a 0%, #8b0000 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              📰 Magazine AIME
            </Typography>
            <Typography variant="caption" sx={{ color: '#2c3e50', fontWeight: 600 }}>
              {usePregenerated ? (
                <>Édition #{magazine.edition_number || '001'} • {new Date(magazine.generated_at).toLocaleDateString('fr-FR')}</>
              ) : (
                <>Édition Live • {new Date(magazine.generated_at).toLocaleDateString('fr-FR')}</>
              )}
            </Typography>
          </Box>

          <Stack direction="row" spacing={2} alignItems="center">
            {/* Bouton pour ouvrir le menu des éditions */}
            {usePregenerated && editionsList && (
              <>
                <Tooltip title="Choisir une édition">
                  <IconButton
                    onClick={(e) => setEditionsMenuAnchor(e.currentTarget)}
                    sx={{
                      backgroundColor: '#f8f8f8',
                      border: '1px solid #d0d0d0',
                      '&:hover': { backgroundColor: '#e8e8e8' }
                    }}
                  >
                    <ListIcon />
                  </IconButton>
                </Tooltip>

                <Menu
                  anchorEl={editionsMenuAnchor}
                  open={Boolean(editionsMenuAnchor)}
                  onClose={() => setEditionsMenuAnchor(null)}
                  PaperProps={{
                    sx: { maxHeight: 400, width: 300 }
                  }}
                >
                  <MenuItem disabled>
                    <Typography variant="caption" sx={{ fontWeight: 700 }}>
                      {editionsList.count} éditions disponibles
                    </Typography>
                  </MenuItem>
                  <Divider />
                  {editionsList.editions.map((edition) => (
                    <MenuItem
                      key={edition.id}
                      onClick={() => handleSelectEdition(edition.id)}
                      selected={selectedEditionId === edition.id}
                    >
                      <ListItemText
                        primary={`Édition #${edition.edition_number}`}
                        secondary={`${new Date(edition.generated_at).toLocaleDateString('fr-FR')} • ${edition.album_count} albums`}
                      />
                    </MenuItem>
                  ))}
                </Menu>
              </>
            )}

            <Box sx={{
              textAlign: 'right',
              padding: '8px 16px',
              backgroundColor: '#f8f8f8',
              borderRadius: '4px',
              border: '1px solid #d0d0d0'
            }}>
              <Typography variant="caption" display="block" sx={{ color: '#6c757d', fontWeight: 600 }}>
                Prochain refresh
              </Typography>
              <Typography variant="h6" sx={{ fontFamily: 'monospace', color: '#c41e3a', fontWeight: 700 }}>
                {formatTime(nextRefreshIn)}
              </Typography>
            </Box>

            <Tooltip title="Édition aléatoire">
              <Button
                variant="outlined"
                startIcon={<Casino />}
                onClick={handleNewEdition}
                sx={{
                  textTransform: 'none',
                  fontWeight: 600,
                  borderColor: '#c41e3a',
                  color: '#c41e3a',
                  '&:hover': {
                    borderColor: '#a01527',
                    backgroundColor: 'rgba(196, 30, 58, 0.04)'
                  }
                }}
              >
                Aléatoire
              </Button>
            </Tooltip>

            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={handleGenerateNew}
              sx={{
                background: 'linear-gradient(135deg, #c41e3a 0%, #8b0000 100%)',
                textTransform: 'none',
                fontWeight: 600,
                '&:hover': {
                  background: 'linear-gradient(135deg, #a01527 0%, #6d0000 100%)'
                }
              }}
            >
              Générer Live
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {/* Magazine Content */}
      <Box sx={{
        flex: 1,
        overflow: 'auto',
        scrollBehavior: 'smooth'
      }}>
        {magazine.pages.map((page, index) => (
          <Box 
            key={index} 
            id={`page-${index}`}
            sx={{
              minHeight: 'auto',
              scrollSnapAlign: 'start'
            }}
          >
            <MagazinePage page={page} index={index} />
          </Box>
        ))}
      </Box>

      {/* Footer Navigation */}
      <Paper elevation={3} sx={{
        position: 'sticky',
        bottom: 0,
        backgroundColor: '#ffffff',
        backdropFilter: 'blur(10px)',
        borderTop: '2px solid #c41e3a',
        padding: '16px 24px'
      }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
        >
          <Button
            variant="outlined"
            disabled={currentPage === 0}
            onClick={() => handleNavigate('prev')}
          >
            ← Précédente
          </Button>

          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" sx={{ color: '#2c3e50', fontWeight: 600 }}>
              Page {currentPage + 1} / {magazine.total_pages}
            </Typography>
            <Box sx={{
              display: 'flex',
              gap: 1,
              justifyContent: 'center',
              marginTop: '8px'
            }}>
              {magazine.pages.map((_, index) => (
                <Box
                  key={index}
                  onClick={() => setCurrentPage(index)}
                  sx={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: currentPage === index
                      ? '#c41e3a'
                      : '#d0d0d0',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      backgroundColor: currentPage === index ? '#c41e3a' : '#a0a0a0'
                    }
                  }}
                />
              ))}
            </Box>
          </Box>

          <Button
            variant="outlined"
            disabled={currentPage === magazine.total_pages - 1}
            onClick={() => handleNavigate('next')}
          >
            Suivante →
          </Button>
        </Stack>
      </Paper>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity={snackbar.type} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
