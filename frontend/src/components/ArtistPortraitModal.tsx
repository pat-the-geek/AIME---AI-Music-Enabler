import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  CircularProgress,
  Alert,
  Typography,
  IconButton,
} from '@mui/material'
import { Close as CloseIcon } from '@mui/icons-material'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'
import apiClient from '@/api/client'
import rehypeRaw from 'rehype-raw'

interface ArtistPortraitModalProps {
  open: boolean
  artistId: number | null
  artistName?: string
  onClose: () => void
}

export default function ArtistPortraitModal({
  open,
  artistId,
  artistName,
  onClose,
}: ArtistPortraitModalProps) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamedContent, setStreamedContent] = useState('')
  const [streamMetadata, setStreamMetadata] = useState<any>({})
  const [streamError, setStreamError] = useState<string | null>(null)

  useEffect(() => {
    if (!open || !artistId) return

    const generatePortrait = async () => {
      setIsStreaming(true)
      setStreamedContent('')
      setStreamMetadata({})
      setStreamError(null)

      try {
        const baseURL = apiClient.defaults.baseURL
        const response = await fetch(
          `${baseURL}/artists/${artistId}/article/stream`,
          {
            headers: {
              Accept: 'text/event-stream',
            },
          }
        )

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

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()

              if (!data) continue

              try {
                const parsed = JSON.parse(data)

                if (parsed.type === 'metadata') {
                  setStreamMetadata({
                    artist_name: parsed.artist_name,
                    artist_image_url: parsed.artist_image_url,
                    albums_count: parsed.albums_count,
                  })
                } else if (parsed.type === 'chunk') {
                  // Accumulate markdown content while preserving formatting
                  setStreamedContent((prev) => {
                    const newContent = prev + parsed.content
                    console.log('📄 Portrait chunk received, size:', parsed.content.length)
                    return newContent
                  })
                } else if (parsed.type === 'error') {
                  setStreamError(parsed.message)
                  setIsStreaming(false)
                } else if (parsed.type === 'done') {
                  setIsStreaming(false)
                }
              } catch (e) {
                console.warn('⚠️ Parse error:', data)
              }
            }
          }
        }
      } catch (error) {
        console.error('Erreur streaming:', error)
        setStreamError(
          error instanceof Error ? error.message : 'Erreur inconnue'
        )
        setIsStreaming(false)
      }
    }

    generatePortrait()
  }, [open, artistId])

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      sx={{
        '& .MuiDialog-paper': {
          maxHeight: '90vh',
          overflow: 'auto',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography variant="h6">Portrait d'Artiste</Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pt: 2 }}>
        {isStreaming && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={24} />
              <Typography>
                ✨ Génération de l'article en streaming...
              </Typography>
            </Box>
          </Alert>
        )}

        {streamError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Erreur: {streamError}
          </Alert>
        )}

        {streamMetadata.artist_image_url && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <Box
              component="img"
              src={streamMetadata.artist_image_url}
              alt={streamMetadata.artist_name || artistName}
              sx={{
                maxWidth: '300px',
                width: '100%',
                height: 'auto',
                borderRadius: 2,
                boxShadow: 2,
              }}
            />
          </Box>
        )}

        {streamedContent && (
          <Box
            sx={{
              '& h1': {
                fontSize: '1.8rem',
                fontWeight: 700,
                mb: 2.5,
                mt: 3,
                color: 'primary.main',
              },
              '& h2': {
                fontSize: '1.4rem',
                fontWeight: 600,
                mb: 2,
                mt: 2.5,
                color: 'text.primary',
                borderLeft: '3px solid #1976d2',
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
                color: '#1a1a1a',
              },
              '& em': {
                fontStyle: 'italic',
              },
              '& blockquote': {
                borderLeft: '3px solid #1976d2',
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
              '& pre': {
                backgroundColor: 'rgba(0, 0, 0, 0.08)',
                padding: '12px',
                borderRadius: '4px',
                overflow: 'auto',
                mb: 1.5,
                '& code': {
                  backgroundColor: 'transparent',
                  padding: 0,
                }
              },
              '& hr': {
                border: 'none',
                borderTop: '2px solid #e0e0e0',
                my: 2.5,
              },
              '& a': {
                color: '#1976d2',
                textDecoration: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                }
              },
              '& table': {
                borderCollapse: 'collapse',
                width: '100%',
                mb: 1.5,
              },
              '& th, & td': {
                border: '1px solid #ddd',
                padding: '8px 12px',
                textAlign: 'left',
              },
              '& th': {
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                fontWeight: 700,
              },
            }}
          >
            <ReactMarkdown 
              remarkPlugins={[remarkGfm, remarkBreaks]}
              rehypePlugins={[rehypeRaw]}
            >
              {streamedContent}
            </ReactMarkdown>
          </Box>
        )}

        {!streamedContent && !isStreaming && !streamError && (
          <Typography color="text.secondary" align="center">
            Aucun contenu à afficher
          </Typography>
        )}
      </DialogContent>
    </Dialog>
  )
}
