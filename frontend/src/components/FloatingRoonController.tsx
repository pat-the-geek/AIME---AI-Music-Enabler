import { useState, useEffect, useRef, useCallback } from 'react'
import { useRoon } from '@/contexts/RoonContext'
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  IconButton,
  MenuItem,
  Paper,
  Select,
  Slider,
  Snackbar,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  Close,
  ExpandLess,
  ExpandMore,
  OpenInNew,
  Pause,
  PlayArrow,
  SkipNext,
  SkipPrevious,
  Stop,
} from '@mui/icons-material'

type ControlAction = 'play' | 'pause' | 'next' | 'previous' | 'stop'

export default function FloatingRoonController() {
  const { nowPlaying, playbackZone, setPlaybackZone, playbackControl, zones, enabled, available } = useRoon()
  const [expanded, setExpanded] = useState(true)
  const [hidden, setHidden] = useState(() => localStorage.getItem('roon_controller_hidden') === '1')
  const [volume, setVolume] = useState<number>(50)
  const [basePosition, setBasePosition] = useState(0)
  const [lastFetchTime, setLastFetchTime] = useState(Date.now())
  const [isSeeking, setIsSeeking] = useState(false)
  const [isAdjustingVolume, setIsAdjustingVolume] = useState(false)
  const [lastSeekTime, setLastSeekTime] = useState(0)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [messageCount, setMessageCount] = useState(0)
  const [lastUpdateTime, setLastUpdateTime] = useState('')
  const [stateVersion, setStateVersion] = useState(0)

  const popupRef = useRef<Window | null>(null)
  const basePositionRef = useRef(0)
  const lastFetchTimeRef = useRef(Date.now())
  const isSeekingRef = useRef(false)
  const isAdjustingVolumeRef = useRef(false)
  const lastSeekTimeRef = useRef(0)
  const stateVersionRef = useRef(0)
  const lastUpdateWallRef = useRef(Date.now())
  const lastUpdatePerfRef = useRef(performance.now())
  const lastUpdateTsRef = useRef(Date.now())

  useEffect(() => { basePositionRef.current = basePosition }, [basePosition])
  useEffect(() => { lastFetchTimeRef.current = lastFetchTime }, [lastFetchTime])
  useEffect(() => { isSeekingRef.current = isSeeking }, [isSeeking])
  useEffect(() => { isAdjustingVolumeRef.current = isAdjustingVolume }, [isAdjustingVolume])
  useEffect(() => { lastSeekTimeRef.current = lastSeekTime }, [lastSeekTime])
  useEffect(() => { stateVersionRef.current = stateVersion }, [stateVersion])
  useEffect(() => { localStorage.setItem('roon_controller_hidden', hidden ? '1' : '0') }, [hidden])

  const sendUpdateToPopup = useCallback((basePositionOverride?: number, lastUpdateOverride?: number, overrideVersion?: number) => {
    if (!popupRef.current || popupRef.current.closed || !nowPlaying) return
    const nowWall = Date.now()
    const version = overrideVersion ?? stateVersionRef.current
    const isPlaying = nowPlaying.state !== 'paused' && nowPlaying.state !== 'stopped'
    const lastUpdateTs = lastUpdateOverride ?? lastUpdateTsRef.current ?? nowWall
    const basePos = basePositionOverride ?? basePositionRef.current

    popupRef.current.postMessage({
      type: 'ROON_UPDATE',
      nowPlaying,
      basePositionSeconds: basePos,
      durationSeconds: nowPlaying.duration_seconds,
      isPlaying,
      lastUpdateTs,
      stateVersion: version,
      sentAt: nowWall,
    }, '*')
    setMessageCount((c) => c + 1)
    setLastUpdateTime(new Date(nowWall).toLocaleTimeString())
  }, [nowPlaying])

  const handleOpenPopup = useCallback(() => {
    const win = window.open('/roon-player', 'roon-player', 'width=440,height=860')
    if (win) {
      popupRef.current = win
      sendUpdateToPopup()
    } else {
      setError('Impossible d’ouvrir la fenêtre')
    }
  }, [sendUpdateToPopup])

  const handleControl = useCallback(async (control: ControlAction) => {
    try {
      setLoading(true)
      await playbackControl(control)
      const messages: Record<ControlAction, string> = {
        play: 'Lecture démarrée',
        pause: 'Pause',
        stop: 'Arrêté',
        next: 'Suivant',
        previous: 'Précédent',
      }
      setSuccess(messages[control])
      if (popupRef.current && !popupRef.current.closed) {
        popupRef.current.postMessage({ type: 'CONTROL_ACTION', control }, '*')
      }
    } catch (e: any) {
      setError(e?.message || 'Erreur de contrôle')
    } finally {
      setLoading(false)
    }
  }, [playbackControl])

  const handleVolumeChange = useCallback(async (newVolume: number) => {
    if (!nowPlaying?.zone_id) return
    try {
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
      if (!response.ok) throw new Error('Impossible de changer le volume')
      setSuccess('Volume mis à jour')
      if (popupRef.current && !popupRef.current.closed) {
        popupRef.current.postMessage({ type: 'VOLUME_CHANGED', volume: newVolume }, '*')
      }
    } catch (e: any) {
      setError(e?.message || 'Erreur de volume')
    } finally {
      setIsAdjustingVolume(false)
    }
  }, [nowPlaying?.zone_id])

  const handleProgressChange = useCallback(async (newPosition: number) => {
    const now = Date.now()
    setIsSeeking(false)
    setLastSeekTime(now)
    try {
      const response = await fetch('/api/v1/playback/roon/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_name: playbackZone || nowPlaying?.zone_name,
          seconds: Math.floor(newPosition),
        }),
      })
      if (!response.ok) throw new Error('Impossible de changer la position')
      const nextVersion = stateVersionRef.current + 1
      stateVersionRef.current = nextVersion
      setStateVersion(nextVersion)
      basePositionRef.current = newPosition
      lastFetchTimeRef.current = now
      lastUpdateWallRef.current = now
      lastUpdateTsRef.current = now
      lastUpdatePerfRef.current = performance.now()
      setBasePosition(newPosition)
      setLastFetchTime(now)
      setSuccess('Position mise à jour')
      if (popupRef.current && !popupRef.current.closed) {
        popupRef.current.postMessage({
          type: 'ROON_UPDATE',
          nowPlaying,
          basePositionSeconds: newPosition,
          durationSeconds: nowPlaying?.duration_seconds,
          isPlaying: true,
          lastUpdateTs: now,
          stateVersion: nextVersion,
          sentAt: now,
        }, '*')
      }
    } catch (e: any) {
      setError(e?.message || 'Erreur de position')
    }
  }, [playbackZone, nowPlaying?.zone_name, nowPlaying])

  useEffect(() => {
    if (!nowPlaying) return
    const nowWall = Date.now()
    const baseRaw = typeof nowPlaying.position_seconds === 'number' ? nowPlaying.position_seconds : 0
    const fetchedAt = nowPlaying.fetchedAt ?? nowWall
    const current = baseRaw + Math.max(0, (nowWall - fetchedAt) / 1000)

    if (nowPlaying.volume != null && !isAdjustingVolumeRef.current) {
      setVolume(nowPlaying.volume)
    }

    const timeSinceSeek = nowWall - lastSeekTimeRef.current
    if (!isSeekingRef.current && timeSinceSeek > 500) {
      const nextVersion = stateVersionRef.current + 1
      stateVersionRef.current = nextVersion
      setStateVersion(nextVersion)
      basePositionRef.current = baseRaw
      lastFetchTimeRef.current = fetchedAt
      lastUpdateWallRef.current = fetchedAt
      lastUpdateTsRef.current = fetchedAt
      lastUpdatePerfRef.current = performance.now()
      setBasePosition(baseRaw)
      setLastFetchTime(fetchedAt)
      sendUpdateToPopup(baseRaw, fetchedAt, nextVersion)
    }
  }, [nowPlaying, sendUpdateToPopup])

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (!event.data) return
      if (event.data.type === 'POPUP_READY') {
        sendUpdateToPopup()
      }
      if (event.data.type === 'POSITION_CHANGED' && typeof event.data.position === 'number') {
        const nextVersion = event.data.stateVersion && typeof event.data.stateVersion === 'number'
          ? Math.max(stateVersionRef.current + 1, event.data.stateVersion)
          : stateVersionRef.current + 1
        stateVersionRef.current = nextVersion
        setStateVersion(nextVersion)
        const ts = event.data.timestamp || Date.now()
        basePositionRef.current = event.data.position
        lastFetchTimeRef.current = ts
        lastUpdateWallRef.current = ts
        lastUpdateTsRef.current = ts
        lastUpdatePerfRef.current = performance.now()
        setBasePosition(event.data.position)
        setLastFetchTime(ts)
      }
      if (event.data.type === 'VOLUME_CHANGED' && typeof event.data.volume === 'number') {
        setVolume(event.data.volume)
      }
    }
    window.addEventListener('message', handleMessage)
    const interval = setInterval(() => {
      if (popupRef.current && popupRef.current.closed) {
        popupRef.current = null
      }
    }, 2000)
    return () => {
      window.removeEventListener('message', handleMessage)
      clearInterval(interval)
    }
  }, [sendUpdateToPopup])

  useEffect(() => {
    if (!nowPlaying) return
    const heartbeat = setInterval(() => {
      sendUpdateToPopup()
    }, 10000)
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        sendUpdateToPopup()
      }
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      clearInterval(heartbeat)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [nowPlaying, sendUpdateToPopup])

  if (!enabled || !available || !nowPlaying) {
    return null
  }

  if (hidden) {
    return (
      <Box
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1200,
        }}
      >
        <Paper
          elevation={8}
          sx={{
            borderRadius: 2,
            px: 2,
            py: 1,
            background: 'linear-gradient(135deg, #0a0f1f 0%, #0f1c33 50%, #0b1428 100%)',
            color: '#e5ecff',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <Typography variant="body2" sx={{ flex: 1 }}>
            Contrôleur Roon masqué
          </Typography>
          <IconButton size="small" onClick={() => setHidden(false)} sx={{ color: '#4dd0e1' }}>
            <ExpandMore />
          </IconButton>
        </Paper>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        zIndex: 1200,
        maxWidth: 440,
      }}
    >
      <Paper
        elevation={10}
        sx={{
          borderRadius: 18,
          overflow: 'hidden',
          border: '1px solid rgba(255,255,255,0.2)',
          background: 'linear-gradient(145deg, #0b1224 0%, #0f1b33 45%, #0c1429 100%)',
          color: '#e5ecff',
          backdropFilter: 'blur(12px)',
          boxShadow: '0 14px 36px rgba(0,0,0,0.35)',
          fontFamily: 'Space Grotesk, "DM Sans", "Helvetica Neue", sans-serif',
        }}
      >
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', p: 2 }}>
          <Box
            sx={{
              width: 70,
              height: 70,
              borderRadius: 0,
              overflow: 'hidden',
              flexShrink: 0,
              background: 'linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02))',
              border: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            {nowPlaying.image_url ? (
              <Box
                component="img"
                src={nowPlaying.image_url}
                alt={nowPlaying.album}
                sx={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              />
            ) : (
              <Box sx={{ width: '100%', height: '100%', background: 'linear-gradient(135deg, #1d2b4a, #0f162b)' }} />
            )}
          </Box>

          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
              <Chip
                label={nowPlaying.state === 'playing' ? 'Lecture' : 'En pause'}
                size="small"
                variant="filled"
                sx={{
                  height: 22,
                  fontSize: 11,
                  backgroundColor: nowPlaying.state === 'playing' ? 'rgba(77, 208, 225, 0.2)' : 'rgba(255,255,255,0.08)',
                  color: '#c4d6ff',
                }}
              />
              {playbackZone && (
                <Chip
                  label={playbackZone}
                  size="small"
                  variant="outlined"
                  sx={{
                    height: 22,
                    fontSize: 11,
                    borderColor: 'rgba(255,255,255,0.2)',
                    color: '#c4d6ff',
                  }}
                />
              )}
            </Stack>

            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 700,
                color: '#f4f6ff',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={nowPlaying.title}
            >
              {nowPlaying.title}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'rgba(229, 236, 255, 0.75)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={`${nowPlaying.artist} • ${nowPlaying.album}`}
            >
              {nowPlaying.artist} • {nowPlaying.album}
            </Typography>
          </Box>

          <Stack spacing={0.5} alignItems="center">
            <Tooltip title="Ouvrir dans une fenêtre">
              <IconButton size="small" onClick={handleOpenPopup} sx={{ color: '#c4d6ff' }}>
                <OpenInNew fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={expanded ? 'Réduire' : 'Déployer'}>
              <IconButton size="small" onClick={() => setExpanded(!expanded)} sx={{ color: '#c4d6ff' }}>
                {expanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Masquer le contrôleur">
              <IconButton size="small" onClick={() => setHidden(true)} sx={{ color: '#c4d6ff' }}>
                <Close fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {expanded && (
          <Box sx={{ px: 2, pb: 2 }}>
            <Divider sx={{ mb: 2, borderColor: 'rgba(255,255,255,0.08)' }} />

            {zones.length > 0 ? (
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <Select
                  value={playbackZone || ''}
                  onChange={(e) => setPlaybackZone(e.target.value as string)}
                  sx={{
                    color: '#e5ecff',
                    backgroundColor: 'rgba(255, 255, 255, 0.06)',
                    fontSize: '0.9rem',
                    borderRadius: 1.25,
                    '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.18)' },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.32)' },
                    '& .MuiSvgIcon-root': { color: '#e5ecff' },
                  }}
                  displayEmpty
                  renderValue={(value) => {
                    if (!value) return <span>📻 Sélectionner la zone</span>
                    const zone = zones.find((z) => z.name === value)
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
            ) : (
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', display: 'block', mb: 2 }}>
                ⚠️ Aucune zone disponible
              </Typography>
            )}

            <Stack direction="row" spacing={1} justifyContent="center" alignItems="center" sx={{ mb: 1.5 }}>
              <Tooltip title="Précédent">
                <IconButton
                  size="medium"
                  disabled={loading}
                  onClick={() => handleControl('previous')}
                  sx={{ color: '#e5ecff' }}
                >
                  <SkipPrevious />
                </IconButton>
              </Tooltip>

              {loading ? (
                <Box sx={{ display: 'flex', alignItems: 'center', px: 1 }}>
                  <CircularProgress size={26} sx={{ color: '#4dd0e1' }} />
                </Box>
              ) : nowPlaying.state === 'playing' ? (
                <Tooltip title="Pause">
                  <IconButton
                    size="large"
                    onClick={() => handleControl('pause')}
                    sx={{
                      color: '#0b1224',
                      backgroundColor: '#4dd0e1',
                      '&:hover': { backgroundColor: '#5be2f3' },
                    }}
                  >
                    <Pause />
                  </IconButton>
                </Tooltip>
              ) : (
                <Tooltip title="Lecture">
                  <IconButton
                    size="large"
                    onClick={() => handleControl('play')}
                    sx={{
                      color: '#0b1224',
                      backgroundColor: '#4dd0e1',
                      '&:hover': { backgroundColor: '#5be2f3' },
                    }}
                  >
                    <PlayArrow />
                  </IconButton>
                </Tooltip>
              )}

              <Tooltip title="Suivant">
                <IconButton
                  size="medium"
                  disabled={loading}
                  onClick={() => handleControl('next')}
                  sx={{ color: '#e5ecff' }}
                >
                  <SkipNext />
                </IconButton>
              </Tooltip>

              <Tooltip title="Stop">
                <IconButton
                  size="medium"
                  disabled={loading}
                  onClick={() => handleControl('stop')}
                  sx={{ color: 'rgba(229,236,255,0.65)' }}
                >
                  <Stop />
                </IconButton>
              </Tooltip>
            </Stack>

            <Box>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.75 }}>
                <Typography variant="caption" sx={{ color: 'rgba(229,236,255,0.75)' }}>
                  Volume {volume}%
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(229,236,255,0.6)' }}>
                  🔄 {messageCount} • {lastUpdateTime || '–'}
                </Typography>
              </Stack>
              <Slider
                size="small"
                min={0}
                max={100}
                value={volume}
                onChange={(_, val) => {
                  setIsAdjustingVolume(true)
                  setVolume(val as number)
                }}
                onChangeCommitted={(_, val) => handleVolumeChange(val as number)}
                sx={{
                  color: '#7c4dff',
                  '& .MuiSlider-rail': { backgroundColor: 'rgba(255,255,255,0.15)' },
                  '& .MuiSlider-thumb': { boxShadow: '0 0 0 6px rgba(124,77,255,0.18)' },
                }}
              />
            </Box>
          </Box>
        )}
      </Paper>

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
