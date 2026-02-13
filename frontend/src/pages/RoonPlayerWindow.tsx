import { useState, useEffect, useRef } from 'react'
import {
  Box,
  IconButton,
  Typography,
  Stack,
  CircularProgress,
  Slider,
  Snackbar,
  Alert,
  Chip,
  Divider,
} from '@mui/material'
import { PlayArrow, Pause, SkipNext, SkipPrevious, Stop } from '@mui/icons-material'

interface NowPlaying {
  title: string
  artist: string
  album: string
  image_url?: string
  state: 'playing' | 'paused' | 'stopped'
  position_seconds?: number
  duration_seconds?: number
  volume?: number
  zone_id?: string
  zone_name?: string
  fetchedAt?: number
}

export default function RoonPlayerWindow() {
  const [nowPlaying, setNowPlaying] = useState<NowPlaying | null>(null)
  const [volume, setVolume] = useState(50)
  const [lastFetchTime, setLastFetchTime] = useState(Date.now())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSeeking, setIsSeeking] = useState(false)
  const [isAdjustingVolume, setIsAdjustingVolume] = useState(false)
  const [lastSeekTime, setLastSeekTime] = useState(0)
  const [messageCount, setMessageCount] = useState(0)
  const [lastUpdateTime, setLastUpdateTime] = useState<string>('')
  const [basePosition, setBasePosition] = useState(0)
  const [stateVersion, setStateVersion] = useState(0)
  const [isRemotePlaying, setIsRemotePlaying] = useState(true)

  const isSeekingRef = useRef(false)
  const isAdjustingVolumeRef = useRef(false)
  const lastSeekTimeRef = useRef(0)
  const lastReceivedPositionRef = useRef<number | null>(null)
  const basePositionRef = useRef(0)
  const lastFetchTimeRef = useRef(Date.now())
  const isInitializedRef = useRef(false)
  const stateVersionRef = useRef(0)
  const lastUpdateTsRef = useRef(Date.now())
  const lastUpdatePerfRef = useRef(performance.now())

  useEffect(() => { isSeekingRef.current = isSeeking }, [isSeeking])
  useEffect(() => { isAdjustingVolumeRef.current = isAdjustingVolume }, [isAdjustingVolume])
  useEffect(() => { lastSeekTimeRef.current = lastSeekTime }, [lastSeekTime])
  useEffect(() => { basePositionRef.current = basePosition }, [basePosition])
  useEffect(() => { lastFetchTimeRef.current = lastFetchTime }, [lastFetchTime])
  useEffect(() => { stateVersionRef.current = stateVersion }, [stateVersion])

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'ROON_UPDATE') {
        const updatedPlaying = event.data.nowPlaying as NowPlaying
        const incomingVersion = typeof event.data.stateVersion === 'number' ? event.data.stateVersion : 0
        if (incomingVersion < stateVersionRef.current) {
          return
        }
        const nowWall = Date.now()
        const lastUpdateTs = typeof event.data.lastUpdateTs === 'number' ? event.data.lastUpdateTs : nowWall
        const baseRaw = typeof event.data.basePositionSeconds === 'number'
          ? event.data.basePositionSeconds
          : (typeof event.data.derivedPosition === 'number'
            ? event.data.derivedPosition
            : (typeof event.data.basePosition === 'number'
              ? event.data.basePosition
              : updatedPlaying?.position_seconds ?? 0))
        const duration = typeof event.data.durationSeconds === 'number' ? event.data.durationSeconds : updatedPlaying?.duration_seconds
        const isPlayingFlag = typeof event.data.isPlaying === 'boolean'
          ? event.data.isPlaying
          : (updatedPlaying?.state !== 'paused' && updatedPlaying?.state !== 'stopped')
        const derived = isPlayingFlag
          ? baseRaw + Math.max(0, (nowWall - lastUpdateTs) / 1000)
          : baseRaw
        const clamped = duration ? Math.min(derived, duration) : derived

        stateVersionRef.current = incomingVersion
        setStateVersion(incomingVersion)
        setMessageCount((prev) => prev + 1)
        setLastUpdateTime(new Date().toLocaleTimeString())
        setIsRemotePlaying(!!isPlayingFlag)
        setNowPlaying({ ...updatedPlaying, duration_seconds: duration })

        if (!isAdjustingVolumeRef.current && updatedPlaying?.volume != null) {
          setVolume(updatedPlaying.volume)
        }

        const timeSinceSeek = nowWall - lastSeekTimeRef.current
        if (!isSeekingRef.current && timeSinceSeek > 300) {
          lastReceivedPositionRef.current = clamped
          basePositionRef.current = baseRaw
          lastFetchTimeRef.current = lastUpdateTs
          lastUpdateTsRef.current = lastUpdateTs
          lastUpdatePerfRef.current = performance.now()
          setBasePosition(baseRaw)
          setLastFetchTime(lastUpdateTs)
        }
      }
    }

    window.addEventListener('message', handleMessage)
    if (window.opener) {
      window.opener.postMessage({ type: 'POPUP_READY' }, '*')
    }
    return () => window.removeEventListener('message', handleMessage)
  }, [])

  useEffect(() => {
    if (nowPlaying?.title) {
      isInitializedRef.current = false
    }
  }, [nowPlaying?.title])

  useEffect(() => {
    if (!nowPlaying || nowPlaying.position_seconds == null) return
    const now = Date.now()
    const timeSinceSeek = now - lastSeekTime
    const currentInterpolated = basePositionRef.current + Math.max(0, (now - lastUpdateTsRef.current) / 1000)
    const drift = Math.abs(currentInterpolated - nowPlaying.position_seconds)

    if (timeSinceSeek > 2000 && (!isInitializedRef.current || drift > 0.7)) {
      const derived = nowPlaying.position_seconds
      basePositionRef.current = derived
      lastUpdateTsRef.current = nowPlaying.fetchedAt ?? now
      lastUpdatePerfRef.current = performance.now()
      setBasePosition(derived)
      setLastFetchTime(nowPlaying.fetchedAt ?? now)
      lastReceivedPositionRef.current = derived
      isInitializedRef.current = true
    }
  }, [nowPlaying?.title, nowPlaying?.position_seconds, lastSeekTime])

  const handleControl = async (control: 'play' | 'pause' | 'next' | 'previous' | 'stop') => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch('/api/v1/playback/roon/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_name: nowPlaying?.zone_name,
          control,
        }),
      })

      if (!response.ok) {
        throw new Error(`Erreur ${control}`)
      }

      const messages: Record<string, string> = {
        play: 'Lecture démarrée',
        pause: 'Pause',
        stop: 'Arrêté',
        next: 'Suivant',
        previous: 'Précédent',
      }

      setSuccess(messages[control])

      if (window.opener) {
        window.opener.postMessage({ type: 'CONTROL_ACTION', control }, '*')
      }
    } catch (error: any) {
      setError(error.message || 'Erreur de contrôle')
    } finally {
      setLoading(false)
    }
  }

  const handleVolumeChange = async (newVolume: number) => {
    try {
      if (!nowPlaying?.zone_id) return

      setVolume(newVolume)

      const response = await fetch('/api/v1/playback/roon/volume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_id: nowPlaying.zone_id,
          how: 'absolute',
          value: newVolume,
        }),
      })

      if (!response.ok) {
        throw new Error('Impossible de changer le volume')
      }

      setSuccess('Volume mis à jour')

      if (window.opener) {
        window.opener.postMessage({ type: 'VOLUME_CHANGED', volume: newVolume }, '*')
      }
    } catch (error) {
      setError('Erreur de volume')
    }
  }

  const handleProgressChange = async (newPosition: number) => {
    try {
      const now = Date.now()
      setLastSeekTime(now)

      const response = await fetch('/api/v1/playback/roon/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_name: nowPlaying?.zone_name,
          seconds: Math.floor(newPosition),
        }),
      })

      if (!response.ok) {
        throw new Error('Impossible de changer la position')
      }

      basePositionRef.current = newPosition
      lastUpdateTsRef.current = now
      lastUpdatePerfRef.current = performance.now()
      setBasePosition(newPosition)
      setLastFetchTime(now)
      setSuccess('Position mise à jour')

      if (window.opener) {
        window.opener.postMessage({
          type: 'POSITION_CHANGED',
          position: newPosition,
          timestamp: now,
        }, '*')
      }
    } catch (error) {
      setError('Erreur de position')
    } finally {
      setIsSeeking(false)
    }
  }

  if (!nowPlaying) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: 'linear-gradient(135deg, #0a0f1f 0%, #0f1c33 50%, #0b1428 100%)',
          color: '#e5ecff',
          fontFamily: 'Space Grotesk, "DM Sans", "Helvetica Neue", sans-serif',
        }}
      >
        <Typography>En attente de données Roon...</Typography>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'radial-gradient(circle at 20% 20%, rgba(77,208,225,0.08), transparent 30%), linear-gradient(135deg, #0a0f1f 0%, #0f1c33 50%, #0b1428 100%)',
        color: '#e5ecff',
        fontFamily: 'Space Grotesk, "DM Sans", "Helvetica Neue", sans-serif',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 3,
          py: 2,
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          backdropFilter: 'blur(8px)',
        }}
      >
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Chip
            label={nowPlaying.state === 'playing' ? 'Lecture en cours' : nowPlaying.state === 'paused' ? 'En pause' : 'Arrêté'}
            size="small"
            sx={{
              height: 26,
              fontSize: 12,
              backgroundColor: nowPlaying.state === 'playing' ? 'rgba(77,208,225,0.2)' : 'rgba(255,255,255,0.08)',
              color: '#c4d6ff',
            }}
          />
          {nowPlaying.zone_name && (
            <Chip
              label={nowPlaying.zone_name}
              size="small"
              variant="outlined"
              sx={{
                height: 26,
                fontSize: 12,
                borderColor: 'rgba(255,255,255,0.18)',
                color: '#c4d6ff',
              }}
            />
          )}
        </Stack>

        <Typography variant="caption" sx={{ color: 'rgba(229,236,255,0.75)' }}>
          🔄 {messageCount} messages • Dernière MAJ {lastUpdateTime || '–'}
        </Typography>
      </Box>

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2.5, p: 3 }}>
        <Box
          sx={{
            width: '100%',
            height: 320,
            borderRadius: 0,
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.08)',
            background: 'linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {nowPlaying.image_url ? (
            <Box
              component="img"
              src={nowPlaying.image_url}
              alt={nowPlaying.album}
              sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <Typography variant="h6" sx={{ color: 'rgba(229,236,255,0.7)' }}>
              Pas d'artwork
            </Typography>
          )}
        </Box>

        <Box sx={{ textAlign: 'center' }}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              color: '#f4f6ff',
              mb: 0.5,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={nowPlaying.title}
          >
            {nowPlaying.title}
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: 'rgba(229,236,255,0.75)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={`${nowPlaying.artist} • ${nowPlaying.album}`}
          >
            {nowPlaying.artist} • {nowPlaying.album}
          </Typography>
        </Box>

        <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)' }} />

        <Stack direction="row" spacing={1.5} justifyContent="center" alignItems="center">
          <IconButton
            onClick={() => handleControl('previous')}
            disabled={loading}
            sx={{ color: '#e5ecff', width: 52, height: 52 }}
          >
            <SkipPrevious fontSize="medium" />
          </IconButton>

          <IconButton
            onClick={() => handleControl(nowPlaying.state === 'playing' ? 'pause' : 'play')}
            disabled={loading}
            sx={{
              color: '#0b1224',
              backgroundColor: '#4dd0e1',
              width: 72,
              height: 72,
              '&:hover': { backgroundColor: '#5be2f3' },
            }}
          >
            {loading ? <CircularProgress size={30} sx={{ color: '#0b1224' }} /> : nowPlaying.state === 'playing' ? <Pause fontSize="large" /> : <PlayArrow fontSize="large" />}
          </IconButton>

          <IconButton
            onClick={() => handleControl('next')}
            disabled={loading}
            sx={{ color: '#e5ecff', width: 52, height: 52 }}
          >
            <SkipNext fontSize="medium" />
          </IconButton>

          <IconButton
            onClick={() => handleControl('stop')}
            disabled={loading}
            sx={{ color: 'rgba(229,236,255,0.7)', width: 52, height: 52 }}
          >
            <Stop fontSize="medium" />
          </IconButton>
        </Stack>

        <Box sx={{ pt: 1 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.75 }}>
            <Typography variant="caption" sx={{ color: 'rgba(229,236,255,0.75)' }}>
              Volume {volume}%
            </Typography>
          </Stack>
          <Slider
            value={volume}
            onChange={(_, value) => {
              setIsAdjustingVolume(true)
              setVolume(value as number)
            }}
            onChangeCommitted={(_, value) => {
              handleVolumeChange(value as number)
              setIsAdjustingVolume(false)
            }}
            min={0}
            max={100}
            sx={{
              color: '#7c4dff',
              '& .MuiSlider-rail': { backgroundColor: 'rgba(255,255,255,0.15)' },
              '& .MuiSlider-thumb': { boxShadow: '0 0 0 8px rgba(124,77,255,0.16)' },
            }}
          />
        </Box>
      </Box>

      <Snackbar
        open={!!error}
        autoHideDuration={4000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error" variant="filled">
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={2000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success" variant="filled">
          {success}
        </Alert>
      </Snackbar>
    </Box>
  )
}
