import { useState, useEffect } from 'react'
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
  Snackbar,
  Alert,
  LinearProgress,
  Slider,
  FormControl,
  Select,
  MenuItem,
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
} from '@mui/icons-material'

export default function FloatingRoonController() {
  const { enabled, available, nowPlaying, playbackControl, playbackZone, setPlaybackZone, zones } = useRoon()
  const [expanded, setExpanded] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [hidden, setHidden] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [volume, setVolume] = useState(50)
  const [isSeeking, setIsSeeking] = useState(false)
  const [lastFetchTime, setLastFetchTime] = useState<number>(Date.now())
  const [interpolatedPosition, setInterpolatedPosition] = useState<number>(0)
  
  // Synchroniser isPlaying avec l'état réel de Roon
  useEffect(() => {
    if (nowPlaying) {
      const currentlyPlaying = nowPlaying.state === 'playing'
      setIsPlaying(currentlyPlaying)
    }
  }, [nowPlaying])

  // Synchroniser le volume avec Roon
  useEffect(() => {
    console.log('Volume sync effect triggered. nowPlaying:', nowPlaying)
    if (nowPlaying) {
      console.log('Volume value:', nowPlaying.volume, 'Type:', typeof nowPlaying.volume)
      // Check for null OR undefined (not just undefined)
      if (nowPlaying.volume != null) {
        console.log('Setting volume to:', nowPlaying.volume)
        setVolume(nowPlaying.volume)
      } else {
        console.log('Volume is null/undefined, not updating')
      }
    }
  }, [nowPlaying])

  // Mettre à jour la position de départ quand le track change
  useEffect(() => {
    if (nowPlaying) {
      setLastFetchTime(Date.now())
      setInterpolatedPosition(nowPlaying.position_seconds || 0)
    }
  }, [nowPlaying?.title])  // Déclenche juste quand le titre change (nouveau track)

  // Interpoler la position en temps réel pendant la lecture
  useEffect(() => {
    if (!isPlaying || !nowPlaying || isSeeking) {
      return
    }

    const interval = setInterval(() => {
      const elapsed = (Date.now() - lastFetchTime) / 1000  // Secondes écoulées
      let newPosition = (nowPlaying.position_seconds || 0) + elapsed
      
      // Ne pas dépasser la durée du track
      if (nowPlaying.duration_seconds && newPosition > nowPlaying.duration_seconds) {
        newPosition = nowPlaying.duration_seconds
      }
      
      setInterpolatedPosition(newPosition)
    }, 100)  // Mise à jour 10 fois par seconde pour une animation fluide

    return () => clearInterval(interval)
  }, [isPlaying, nowPlaying?.title, lastFetchTime, isSeeking])

  // Auto-show player when track is active, especially on system wake-up
  // Si un morceau est en cours de lecture, afficher automatiquement le player flottant
  useEffect(() => {
    if (nowPlaying && nowPlaying.title && hidden) {
      // Un morceau est en cours de lecture et le player est caché
      // Afficher le player automatiquement
      setHidden(false)
    }
  }, [nowPlaying])

  // Formater les secondes en MM:SS
  const formatTime = (seconds: number | undefined): string => {
    if (!seconds || seconds < 0) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Obtenir le pourcentage de progression
  const getProgressPercent = (): number => {
    if (!nowPlaying?.duration_seconds || nowPlaying.duration_seconds <= 0) return 0
    return (interpolatedPosition / nowPlaying.duration_seconds) * 100
  }

  const handleVolumeChange = async (newVolume: number) => {
    try {
      // Vérifier que zone_id existe
      if (!nowPlaying?.zone_id) {
        setError('Zone Roon non disponible. Aucun track en cours.')
        return
      }
      
      setVolume(newVolume)
      // Appel API pour changer le volume
      const response = await fetch('/api/v1/playback/roon/volume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_id: nowPlaying.zone_id,
          how: 'absolute',
          value: newVolume
        })
      })
      
      // Capturer et afficher l'erreur réelle du serveur
      if (!response.ok) {
        let errorMessage = 'Impossible de changer le volume'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.error || errorMessage
        } catch (e) {
          errorMessage = `Erreur serveur: ${response.statusText}`
        }
        throw new Error(errorMessage)
      }
      
      setSuccess('Volume mis à jour')
    } catch (error) {
      console.error('Erreur changement volume:', error)
      setError(error instanceof Error ? error.message : 'Impossible de changer le volume')
    }
  }

  const handleProgressChange = async (newPosition: number) => {
    try {
      setIsSeeking(true)
      // Appel API pour chercher
      const response = await fetch('/api/v1/playback/roon/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_name: nowPlaying?.zone_name,
          seconds: Math.floor(newPosition)
        })
      })
      if (!response.ok) {
        throw new Error('Impossible de changer la position')
      }
      
      // Mettre à jour la position interpolée immédiatement
      setInterpolatedPosition(newPosition)
      setLastFetchTime(Date.now())
      setSuccess('Position mise à jour')
    } catch (error) {
      console.error('Erreur changement position:', error)
      setError('Impossible de changer la position')
    } finally {
      setIsSeeking(false)
    }
  }

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
            <PlayArrow sx={{ color: 'rgba(255, 255, 255, 0.5)' }} />
          </Box>
        </Tooltip>
      </Box>
    )
  }

  const handleControl = async (control: 'play' | 'pause' | 'next' | 'previous' | 'stop') => {
    try {
      setLoading(true)
      setError(null)
      
      await playbackControl(control)
      
      // Afficher le message de succès seulement
      if (control === 'play') {
        setSuccess('Lecture démarrée')
      } else if (control === 'pause') {
        setSuccess('Lecture en pause')
      } else if (control === 'stop') {
        setSuccess('Lecture arrêtée')
      } else if (control === 'next') {
        setSuccess('Morceau suivant')
      } else if (control === 'previous') {
        setSuccess('Morceau précédent')
      }
      
      // NE PAS faire d'optimistic update manuelle
      // Laisser le backend via le contexte Roon décider du vrai state
      // Le polling toutes les 3 secondes mettra à jour nowPlaying
      // et le useEffect synchronisera isPlaying
      
    } catch (error: any) {
      console.error('Erreur contrôle Roon:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Erreur inconnue'
      setError(`Échec ${control}: ${errorMessage}`)
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
            backgroundColor: '#ffffff',
            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
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
                color: '#000000',
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
              sx={{ color: 'rgba(0, 0, 0, 0.5)' }}
            >
              <Close fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation()
                setExpanded(!expanded)
              }}
              sx={{ color: 'rgba(0, 0, 0, 0.5)' }}
            >
              {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
            </IconButton>
          </Stack>
        </Box>

        {/* Contenu détaillé */}
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <CardContent sx={{ py: 2 }}>
            {/* Image de l'album */}
            {nowPlaying.image_url && (
              <Box
                component="img"
                src={nowPlaying.image_url}
                alt={nowPlaying.album}
                sx={{
                  width: '100%',
                  height: 200,
                  objectFit: 'cover',
                  borderRadius: 1,
                  marginBottom: 2,
                }}
              />
            )}
            
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
                color: '#ffffff',
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
                color: '#ffffff',
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

            {/* Zone Selector */}
            {zones.length > 0 && (
              <FormControl fullWidth sx={{ mb: 2 }} size="small">
                <Select
                  value={playbackZone || ''}
                  onChange={(e) => {
                    setPlaybackZone(e.target.value)
                  }}
                  sx={{
                    color: '#ffffff',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    fontSize: '0.9rem',
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.2)',
                    },
                    '&:hover .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.4)',
                    },
                    '& .MuiSvgIcon-root': {
                      color: '#ffffff',
                    },
                  }}
                  displayEmpty
                  renderValue={(value) => {
                    if (!value) return <span>📻 Sélectionner zone</span>
                    const zone = zones.find(z => z.name === value)
                    return <span>📻 {zone?.name || value}</span>
                  }}
                >
                  {zones.map((z) => (
                    <MenuItem key={z.zone_id} value={z.name}>
                      {z.name} ({z.state})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            {zones.length === 0 && (
              <Typography
                variant="caption"
                sx={{
                  color: '#ffffff',
                  display: 'block',
                  mb: 2,
                  fontSize: '0.7rem',
                  fontWeight: 500,
                }}
              >
                ⚠️ Aucune zone disponible
              </Typography>
            )}

            {/* Barre de Progression */}
            {nowPlaying.duration_seconds && nowPlaying.duration_seconds > 0 && (
              <Box sx={{ mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1,
                  }}
                >
                  <Slider
                    size="small"
                    min={0}
                    max={nowPlaying.duration_seconds}
                    value={interpolatedPosition}
                    onChange={(e: any) => {
                      // Mise à jour simple du slider sans appel API
                      // (l'appel API sera fait au onChangeCommitted)
                    }}
                    onChangeCommitted={(e: any, newValue: any) => {
                      handleProgressChange(newValue)
                    }}
                    disabled={!isPlaying || isSeeking}
                    sx={{
                      flex: 1,
                      color: '#4caf50',
                      '& .MuiSlider-track': {
                        backgroundColor: '#4caf50',
                      },
                      '& .MuiSlider-rail': {
                        backgroundColor: 'rgba(255, 255, 255, 0.2)',
                      },
                      '& .MuiSlider-thumb': {
                        backgroundColor: '#4caf50',
                      },
                    }}
                  />
                </Box>
                <Typography
                  variant="caption"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    fontSize: '0.75rem',
                    display: 'block',
                    textAlign: 'center',
                  }}
                >
                  {formatTime(interpolatedPosition)} / {formatTime(nowPlaying.duration_seconds)}
                </Typography>
              </Box>
            )}

            {/* Contrôle du Volume */}
            <Box sx={{ mb: 2 }}>
              <Typography
                variant="caption"
                sx={{
                  color: '#ffffff',
                  display: 'block',
                  mb: 1,
                  fontSize: '0.75rem',
                  fontWeight: 500,
                }}
              >
                Volume: {volume}%
              </Typography>
              <Slider
                size="small"
                min={0}
                max={100}
                value={volume}
                onChange={(e: any, newValue: any) => {
                  setVolume(newValue)
                }}
                onChangeCommitted={(e: any, newValue: any) => {
                  handleVolumeChange(newValue)
                }}
                sx={{
                  color: '#ff9800',
                  '& .MuiSlider-track': {
                    backgroundColor: '#ff9800',
                  },
                  '& .MuiSlider-rail': {
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  },
                  '& .MuiSlider-thumb': {
                    backgroundColor: '#ff9800',
                  },
                }}
              />
            </Box>

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
      
      {/* Snackbar pour les succès */}
      <Snackbar
        open={!!success}
        autoHideDuration={2000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success" variant="filled">
          {success}
        </Alert>
      </Snackbar>
      
      {/* Snackbar pour les erreurs */}
      <Snackbar
        open={!!error}
        autoHideDuration={4000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert onClose={() => setError(null)} severity="error" variant="filled">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  )
}
