import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Container,
  Paper,
  TextField,
  Autocomplete,
  CircularProgress,
  Button,
  Divider,
  Chip,
  Alert,
} from '@mui/material'
import {
  Article as ArticleIcon,
  Person as PersonIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import apiClient from '@/api/client'

interface Artist {
  id: number
  name: string
  spotify_id?: string
  image_url?: string
}

interface ArticleData {
  artist_id: number
  artist_name: string
  artist_image_url?: string
  generated_at: string
  word_count: number
  content: string
  albums_count: number
  listen_count: number
}

export default function ArtistArticle() {
  const [selectedArtist, setSelectedArtist] = useState<Artist | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [generateArticle, setGenerateArticle] = useState(false)
  const [dominantColor, setDominantColor] = useState<string>('#424242')
  
  // État pour le streaming
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamedContent, setStreamedContent] = useState('')
  const [streamMetadata, setStreamMetadata] = useState<{
    artist_name?: string
    artist_image_url?: string
    albums_count?: number
  }>({})
  const [streamError, setStreamError] = useState<string | null>(null)

  // Charger la liste des artistes
  const { data: artistsData, isLoading: artistsLoading } = useQuery({
    queryKey: ['artists-list', searchTerm],
    queryFn: async () => {
      const response = await apiClient.get('/artists/list', {
        params: { search: searchTerm || undefined, limit: 100 }
      })
      return response.data
    },
    enabled: searchTerm.length > 0,
  })

  // Générer l'article (mode non-streaming - gardé pour compatibilité)
  const { data: article, isLoading: articleLoading, error, refetch } = useQuery<ArticleData>({
    queryKey: ['artist-article', selectedArtist?.id],
    queryFn: async () => {
      if (!selectedArtist) throw new Error('Aucun artiste sélectionné')
      const response = await apiClient.get(`/artists/${selectedArtist.id}/article`)
      return response.data
    },
    enabled: false, // Désactivé par défaut, on préfère le streaming
    staleTime: Infinity,
  })

  // Fonction pour générer l'article en streaming
  const handleGenerateArticleStream = async () => {
    if (!selectedArtist) return
    
    setIsStreaming(true)
    setStreamedContent('')
    setStreamMetadata({})
    setStreamError(null)
    setGenerateArticle(true)
    
    try {
      const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${baseURL}/artists/${selectedArtist.id}/article/stream`, {
        headers: {
          'Accept': 'text/event-stream'
        }
      })
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('Stream non disponible')
      }
      
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          setIsStreaming(false)
          break
        }
        
        // Décoder le chunk
        buffer += decoder.decode(value, { stream: true })
        
        // Traiter les lignes complètes
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Garder la dernière ligne incomplète
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            
            if (!data) continue // Ignorer les lignes vides
            
            try {
              const parsed = JSON.parse(data)
              
              if (parsed.type === 'metadata') {
                setStreamMetadata({
                  artist_name: parsed.artist_name,
                  artist_image_url: parsed.artist_image_url,
                  albums_count: parsed.albums_count
                })
                console.log('📝 Métadonnées reçues:', parsed)
              } else if (parsed.type === 'chunk') {
                // Contenu texte du Markdown - accumulate to preserve markdown formatting
                setStreamedContent(prev => {
                  const newContent = prev + parsed.content
                  return newContent
                })
                console.log('📄 Chunk reçu, size:', parsed.content.length, 'Total:', streamedContent.length + parsed.content.length)
              } else if (parsed.type === 'error') {
                setStreamError(parsed.message)
                setIsStreaming(false)
                console.error('❌ Erreur API:', parsed.message)
              } else if (parsed.type === 'done') {
                setIsStreaming(false)
                console.log('✅ Streaming terminé')
              }
            } catch (e) {
              // JSON parsing failed
              console.warn('⚠️ Impossible de parser:', data, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Erreur streaming:', error)
      setStreamError(error instanceof Error ? error.message : 'Erreur inconnue')
      setIsStreaming(false)
    }
  }

  const handleGenerateArticle = () => {
    // Utiliser le streaming par défaut
    handleGenerateArticleStream()
  }

  // Extraire la couleur dominante de l'image de l'artiste
  useEffect(() => {
    const imageUrl = article?.artist_image_url || streamMetadata.artist_image_url
    if (imageUrl) {
      const img = new Image()
      img.crossOrigin = 'Anonymous'
      img.src = imageUrl
      
      img.onload = () => {
        try {
          const canvas = document.createElement('canvas')
          const ctx = canvas.getContext('2d')
          if (!ctx) return

          canvas.width = img.width
          canvas.height = img.height
          ctx.drawImage(img, 0, 0)

          // Échantillonner quelques pixels au centre de l'image
          const sampleSize = 10
          const centerX = Math.floor(img.width / 2)
          const centerY = Math.floor(img.height / 2)
          
          let r = 0, g = 0, b = 0, count = 0
          
          for (let x = centerX - sampleSize; x < centerX + sampleSize; x++) {
            for (let y = centerY - sampleSize; y < centerY + sampleSize; y++) {
              const pixel = ctx.getImageData(x, y, 1, 1).data
              r += pixel[0]
              g += pixel[1]
              b += pixel[2]
              count++
            }
          }
          
          r = Math.floor(r / count)
          g = Math.floor(g / count)
          b = Math.floor(b / count)
          
          // Assombrir la couleur pour les lignes de séparation
          const darken = 0.4
          r = Math.floor(r * darken)
          g = Math.floor(g * darken)
          b = Math.floor(b * darken)
          
          const color = `rgb(${r}, ${g}, ${b})`
          setDominantColor(color)
        } catch (error) {
          console.error('Erreur extraction couleur:', error)
        }
      }
    }
  }, [article?.artist_image_url, streamMetadata.artist_image_url])

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <ArticleIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Portrait d'Artiste
          </Typography>
        </Box>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Sélectionnez un artiste pour générer un article journalistique complet de 3000 mots
          incluant biographie, discographie, actualités et analyse musicale.
        </Typography>

        <Divider sx={{ mb: 4 }} />

        {/* Sélection d'artiste */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
          <Autocomplete
            fullWidth
            options={artistsData?.artists || []}
            getOptionLabel={(option) => option.name}
            loading={artistsLoading}
            value={selectedArtist}
            onChange={(_, newValue) => {
              setSelectedArtist(newValue)
              setGenerateArticle(false)
            }}
            onInputChange={(_, newValue) => {
              setSearchTerm(newValue)
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Rechercher un artiste"
                placeholder="Tapez le nom d'un artiste..."
                InputProps={{
                  ...params.InputProps,
                  startAdornment: (
                    <>
                      <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />
                      {params.InputProps.startAdornment}
                    </>
                  ),
                  endAdornment: (
                    <>
                      {artistsLoading && <CircularProgress size={20} />}
                      {params.InputProps.endAdornment}
                    </>
                  ),
                }}
              />
            )}
            renderOption={(props, option) => (
              <li {...props}>
                <Box>
                  <Typography variant="body1">{option.name}</Typography>
                  {option.spotify_id && (
                    <Typography variant="caption" color="text.secondary">
                      ID Spotify: {option.spotify_id}
                    </Typography>
                  )}
                </Box>
              </li>
            )}
          />

          <Button
            variant="contained"
            size="large"
            onClick={handleGenerateArticle}
            disabled={!selectedArtist || isStreaming}
            startIcon={isStreaming ? <CircularProgress size={20} /> : <ArticleIcon />}
            sx={{ minWidth: 200 }}
          >
            {isStreaming ? 'Génération...' : 'Générer'}
          </Button>

          {(article || streamedContent) && (
            <Button
              variant="outlined"
              size="large"
              onClick={handleGenerateArticle}
              disabled={isStreaming}
              startIcon={<RefreshIcon />}
            >
              Régénérer
            </Button>
          )}
        </Box>

        {/* État de chargement/streaming */}
        {isStreaming && (
          <Alert severity="info" sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={24} />
              <Typography>
                ✨ Génération de l'article en streaming... Le texte apparaît au fur et à mesure.
              </Typography>
            </Box>
          </Alert>
        )}

        {/* Erreur streaming */}
        {streamError && (
          <Alert severity="error" sx={{ mb: 4 }}>
            Erreur lors de la génération de l'article: {streamError}
          </Alert>
        )}
        
        {/* Erreur legacy */}
        {error && (
          <Alert severity="error" sx={{ mb: 4 }}>
            Erreur lors de la génération de l'article: {error.message}
          </Alert>
        )}

        {/* Métadonnées de l'article */}
        {streamedContent && streamMetadata.albums_count && (
          <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
            <Chip
              label={`~${Math.round(streamedContent.split(' ').length)} mots`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`${streamMetadata.albums_count} albums`}
              color="secondary"
              variant="outlined"
            />
            <Chip
              label={streamMetadata.artist_name || ''}
              color="default"
              variant="outlined"
            />
            {isStreaming && (
              <Chip
                icon={<CircularProgress size={16} />}
                label="En cours..."
                color="info"
                variant="filled"
              />
            )}
          </Box>
        )}
        
        {/* Métadonnées legacy */}
        {article && !articleLoading && (
          <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
            <Chip
              label={`${article.word_count} mots`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`${article.albums_count} albums`}
              color="secondary"
              variant="outlined"
            />
            <Chip
              label={`${article.listen_count} écoutes`}
              color="success"
              variant="outlined"
            />
            <Chip
              label={`Généré le ${new Date(article.generated_at).toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}`}
              variant="outlined"
            />
          </Box>
        )}
      </Paper>

      {/* Article streamé */}
      {streamedContent && (
        <Paper
          elevation={3}
          sx={{
            p: 6,
            backgroundColor: '#fafafa',
          }}
        >
          {/* Image de l'artiste */}
          {streamMetadata.artist_image_url && (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mb: 4,
              }}
            >
              <Box
                component="img"
                src={streamMetadata.artist_image_url}
                alt={streamMetadata.artist_name}
                sx={{
                  maxWidth: '400px',
                  width: '100%',
                  height: 'auto',
                  borderRadius: 2,
                  boxShadow: 3,
                }}
              />
            </Box>
          )}

          {/* Contenu Markdown streamé */}
          <Box
            sx={{
              '& h1': {
                fontSize: '1.8rem',
                fontWeight: 700,
                mb: 2.5,
                mt: 3,
                color: 'primary.main',
                borderBottom: `2px solid ${dominantColor}`,
                pb: 1.5,
              },
              '& h2': {
                fontSize: '1.4rem',
                fontWeight: 600,
                mb: 2,
                mt: 2.5,
                color: 'text.primary',
                borderLeft: `3px solid ${dominantColor}`,
                pl: 1.5,
              },
              '& h3': {
                fontSize: '1.15rem',
                fontWeight: 600,
                mb: 1.5,
                mt: 2,
                color: 'text.primary',
              },
              '& p': {
                fontSize: '1rem',
                lineHeight: 1.7,
                mb: 1.5,
                textAlign: 'justify',
                color: 'text.primary',
              },
              '& ul, & ol': {
                fontSize: '1rem',
                lineHeight: 1.7,
                mb: 1.5,
                pl: 3,
              },
              '& li': {
                mb: 1,
              },
              '& strong': {
                fontWeight: 700,
                color: 'text.primary',
              },
              '& em': {
                fontStyle: 'italic',
                color: 'text.secondary',
              },
              '& blockquote': {
                borderLeft: `3px solid ${dominantColor}`,
                pl: 1.5,
                py: 0.5,
                my: 1.5,
                fontStyle: 'italic',
                backgroundColor: 'rgba(0, 0, 0, 0.03)',
                fontSize: '0.95rem',
              },
              '& code': {
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                padding: '2px 6px',
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.9rem',
              },
            }}
          >
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              key={`article-${Math.floor(streamedContent.length / 100)}`}
            >
              {streamedContent}
            </ReactMarkdown>
            
            {/* Indicateur de streaming en cours */}
            {isStreaming && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, color: 'primary.main' }}>
                <CircularProgress size={16} />
                <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
                  Génération en cours...
                </Typography>
              </Box>
            )}
          </Box>
        </Paper>
      )}
      
      {/* Article legacy (mode non-streaming) */}
      {article && !articleLoading && !streamedContent && (
        <Paper
          elevation={3}
          sx={{
            p: 6,
            backgroundColor: '#fafafa',
          }}
        >
          {/* Image de l'artiste */}
          {article.artist_image_url && (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mb: 4,
              }}
            >
              <Box
                component="img"
                src={article.artist_image_url}
                alt={article.artist_name}
                sx={{
                  maxWidth: '400px',
                  width: '100%',
                  height: 'auto',
                  borderRadius: 2,
                  boxShadow: 3,
                  objectFit: 'cover',
                }}
              />
            </Box>
          )}

          <Box>
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({node, ...props}) => (
                  <Typography 
                    variant="h1" 
                    component="h1" 
                    sx={{
                      fontSize: '2.5rem',
                      fontWeight: 700,
                      mb: 3,
                      mt: 0,
                      color: dominantColor,
                      borderBottom: '3px solid',
                      borderColor: dominantColor,
                      pb: 2,
                    }}
                    {...props} 
                  />
                ),
                h2: ({node, ...props}) => (
                  <Typography 
                    variant="h2" 
                    component="h2" 
                    sx={{
                      fontSize: '2rem',
                      fontWeight: 600,
                      mt: 5,
                      mb: 2,
                      color: 'text.primary',
                      borderLeft: '4px solid',
                      borderColor: dominantColor,
                      pl: 2,
                    }}
                    {...props} 
                  />
                ),
                h3: ({node, ...props}) => (
                  <Typography 
                    variant="h3" 
                    component="h3" 
                    sx={{
                      fontSize: '1.5rem',
                      fontWeight: 600,
                      mt: 3,
                      mb: 2,
                      color: 'text.secondary',
                    }}
                    {...props} 
                  />
                ),
                p: ({node, ...props}) => (
                  <Typography 
                    variant="body1" 
                    component="p" 
                    sx={{
                      fontSize: '1.1rem',
                      lineHeight: 1.8,
                      mb: 2,
                      textAlign: 'justify',
                    }}
                    {...props} 
                  />
                ),
                strong: ({node, ...props}) => (
                  <Box 
                    component="strong" 
                    sx={{
                      fontWeight: 700,
                      color: 'text.primary',
                    }}
                    {...props} 
                  />
                ),
                em: ({node, ...props}) => (
                  <Box 
                    component="em" 
                    sx={{
                      fontStyle: 'italic',
                      color: 'text.secondary',
                    }}
                    {...props} 
                  />
                ),
                ul: ({node, ...props}) => (
                  <Box 
                    component="ul" 
                    sx={{
                      ml: 4,
                      mb: 2,
                    }}
                    {...props} 
                  />
                ),
                ol: ({node, ...props}) => (
                  <Box 
                    component="ol" 
                    sx={{
                      ml: 4,
                      mb: 2,
                    }}
                    {...props} 
                  />
                ),
                li: ({node, ...props}) => (
                  <Box 
                    component="li" 
                    sx={{
                      mb: 1,
                      fontSize: '1.1rem',
                      lineHeight: 1.6,
                    }}
                    {...props} 
                  />
                ),
                blockquote: ({node, ...props}) => (
                  <Box 
                    component="blockquote" 
                    sx={{
                      borderLeft: '4px solid',
                      borderColor: dominantColor,
                      pl: 3,
                      py: 1,
                      my: 3,
                      fontStyle: 'italic',
                      backgroundColor: 'grey.50',
                      borderRadius: 1,
                    }}
                    {...props} 
                  />
                ),
                code: ({node, inline, ...props}: any) => (
                  <Box 
                    component="code" 
                    sx={{
                      backgroundColor: inline ? 'grey.100' : 'transparent',
                      px: inline ? 1 : 0,
                      py: inline ? 0.5 : 0,
                      borderRadius: inline ? 0.5 : 0,
                      fontFamily: 'monospace',
                    }}
                    {...props} 
                  />
                ),
                pre: ({node, ...props}) => (
                  <Box 
                    component="pre" 
                    sx={{
                      backgroundColor: 'grey.900',
                      color: 'grey.100',
                      p: 2,
                      borderRadius: 1,
                      overflow: 'auto',
                      fontSize: '0.9rem',
                    }}
                    {...props} 
                  />
                ),
                a: ({node, ...props}) => (
                  <Box 
                    component="a" 
                    sx={{
                      color: 'primary.main',
                      textDecoration: 'none',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                    {...props} 
                  />
                ),
                hr: ({node, ...props}) => (
                  <Divider 
                    sx={{
                      my: 4,
                      borderColor: dominantColor,
                      borderWidth: '2px',
                    }}
                    {...props} 
                  />
                ),
                table: ({node, ...props}) => (
                  <Box 
                    component="table" 
                    sx={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      my: 3,
                    }}
                    {...props} 
                  />
                ),
                th: ({node, ...props}) => (
                  <Box 
                    component="th" 
                    sx={{
                      backgroundColor: 'primary.main',
                      color: 'white',
                      p: 2,
                      textAlign: 'left',
                      fontWeight: 600,
                    }}
                    {...props} 
                  />
                ),
                td: ({node, ...props}) => (
                  <Box 
                    component="td" 
                    sx={{
                      p: 2,
                      borderBottom: '1px solid',
                      borderColor: 'grey.300',
                    }}
                    {...props} 
                  />
                ),
              }}
            >
              {article.content}
            </ReactMarkdown>
          </Box>
        </Paper>
      )}

      {/* Placeholder si aucun article */}
      {!article && !articleLoading && !error && (
        <Paper
          elevation={1}
          sx={{
            p: 8,
            textAlign: 'center',
            backgroundColor: 'grey.50',
          }}
        >
          <PersonIcon sx={{ fontSize: 80, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Sélectionnez un artiste pour commencer
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Un article détaillé de 3000 mots sera généré avec l'IA
          </Typography>
        </Paper>
      )}
    </Container>
  )
}
