import { useState } from 'react'
import { useRoon } from '@/contexts/RoonContext'
import {
  Box,
  Card,
  CardContent,
  IconButton,
  Typography,
  Stack,
  CircularProgress,
  Tooltip,
  Collapse,
  Paper,
} from '@mui/material'
import {
  PlayArrow,
  Pause,
  SkipNext,
  SkipPrevious,
  Stop,
  ExpandMore,
  ExpandLess,
  Close,
  VolumeUp,
} from '@mui/icons-material'

export default function FloatingRoonController() {
  const { enabled, available, nowPlaying, playbackControl } = useRoon()
  const [expanded, setExpanded] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [hidden, setHidden] = useState(false)

  if (!enabled || !available || hidden) {
    return null
  }

  // Si aucun track en cours de lecture, afficher un mini contrôleur
  if (!nowPlaying) {
    return (
      <Box
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000,
        }}
      >
        <Tooltip title="Aucune lecture en cours">
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: 'rgba(200, 200, 200, 0.1)',
              backdropFilter: 'blur(10px)',
              cursor: 'pointer',
            }}
            onClick={() => setExpanded(!expanded)}
          >
            <VolumeUp sx={{ color: 'rgba(255, 255, 255, 0.5)' }} />
          </Box>
        </Tooltip>
      </Box>
    )
  }

  const handleControl = async (control: 'play' | 'pause' | 'next' | 'previous' | 'stop') => {
    try {
      setLoading(true)
      await playbackControl(control)
      if (control === 'play') setIsPlaying(true)
      if (control === 'pause' || control === 'stop') setIsPlaying(false)
    } catch (error) {
      console.error('Erreur contrôle Roon:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 1000,
        maxWidth: 350,
        animation: 'slideIn 0.3s ease-in-out',
        '@keyframes slideIn': {
          from: {
            transform: 'translateX(400px)',
            opacity: 0,
          },
          to: {
            transform: 'translateX(0)',
            opacity: 1,
          },
        },
      }}
    >
      <Paper
        elevation={8}
        sx={{
          borderRadius: 2,
          overflow: 'hidden',
          backgroundColor: 'rgba(30, 30, 30, 0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 1.5,
            backgroundColor: 'rgba(76, 175, 80, 0.2)',
            borderBottom: '1px solid rgba(76, 175, 80, 0.3)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
          }}
          onClick={() => setExpanded(!expanded)}
        >
          <Stack direction="row" spacing={1} alignItems="center" sx={{ flex: 1 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: '#4caf50',
                animation: 'pulse 1.5s ease-in-out infinite',
                '@keyframes pulse': {
                  '0%, 100%': {
                    opacity: 1,
                  },
                  '50%': {
                    opacity: 0.5,
                  },
                },
              }}
            />
            <Typography
              variant="caption"
              sx={{
                fontWeight: 600,
                color: '#4caf50',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              En cours de lecture
            </Typography>
          </Stack>
          <Stack direction="row" spacing={0.5}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation()
                setHidden(true)
              }}
              sx={{ color: 'rgba(255, 255, 255, 0.5)' }}
            >
              <Close fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation()
                setExpanded(!expanded)
              }}
              sx={{ color: 'rgba(255, 255, 255, 0.5)' }}
            >
              {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
            </IconButton>
          </Stack>
        </Box>

        {/* Contenu détaillé */}
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <CardContent sx={{ py: 2 }}>
            {/* Titre du track */}
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                color: '#fff',
                mb: 0.5,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={nowPlaying.title}
            >
              {nowPlaying.title}
            </Typography>

            {/* Artiste */}
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255, 255, 255, 0.7)',
                display: 'block',
                mb: 0.5,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={nowPlaying.artist}
            >
              {nowPlaying.artist}
            </Typography>

            {/* Album */}
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255, 255, 255, 0.5)',
                display: 'block',
                mb: 2,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={nowPlaying.album}
            >
              {nowPlaying.album}
            </Typography>

            {/* Zone */}
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(76, 175, 80, 0.8)',
                display: 'block',
                mb: 2,
                fontSize: '0.7rem',
                fontWeight: 500,
              }}
            >
              📻 {nowPlaying.zone_name}
            </Typography>

            {/* Contrôles */}
            <Stack
              direction="row"
              spacing={1}
              justifyContent="center"
              sx={{ mt: 2 }}
            >
              <Tooltip title="Précédent">
                <IconButton
                  size="small"
                  disabled={loading}
                  onClick={() => handleControl('previous')}
                  sx={{
                    color: '#fff',
                    '&:hover': { backgroundColor: 'rgba(76, 175, 80, 0.2)' },
                  }}
                >
                  <SkipPrevious fontSize="small" />
                </IconButton>
              </Tooltip>

              {loading ? (
                <Box sx={{ display: 'flex', alignItems: 'center', px: 1 }}>
                  <CircularProgress size={24} sx={{ color: '#4caf50' }} />
                </Box>
              ) : isPlaying ? (
                <Tooltip title="Pause">
                  <IconButton
                    size="small"
                    onClick={() => handleControl('pause')}
                    sx={{
                      color: '#4caf50',
                      backgroundColor: 'rgba(76, 175, 80, 0.2)',
                      '&:hover': { backgroundColor: 'rgba(76, 175, 80, 0.3)' },
                    }}
                  >
                    <Pause fontSize="small" />
                  </IconButton>
                </Tooltip>
              ) : (
                <Tooltip title="Play">
                  <IconButton
                    size="small"
                    onClick={() => handleControl('play')}
                    sx={{
                      color: '#fff',
                      '&:hover': { backgroundColor: 'rgba(76, 175, 80, 0.2)', color: '#4caf50' },
                    }}
                  >
                    <PlayArrow fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}

              <Tooltip title="Suivant">
                <IconButton
                  size="small"
                  disabled={loading}
                  onClick={() => handleControl('next')}
                  sx={{
                    color: '#fff',
                    '&:hover': { backgroundColor: 'rgba(76, 175, 80, 0.2)' },
                  }}
                >
                  <SkipNext fontSize="small" />
                </IconButton>
              </Tooltip>

              <Tooltip title="Arrêter">
                <IconButton
                  size="small"
                  disabled={loading}
                  onClick={() => handleControl('stop')}
                  sx={{
                    color: 'rgba(255, 255, 255, 0.5)',
                    '&:hover': { backgroundColor: 'rgba(244, 67, 54, 0.2)', color: '#f44336' },
                  }}
                >
                  <Stop fontSize="small" />
                </IconButton>
              </Tooltip>
            </Stack>
          </CardContent>
        </Collapse>
      </Paper>
    </Box>
  )
}
