import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'

interface NowPlayingTrack {
  title: string
  artist: string
  album: string
  zone_name: string
  zone_id: string
  image_url?: string
  state?: string
  duration_seconds?: number
  position_seconds?: number
}

interface RoonZone {
  zone_id: string
  name: string
  state: string
}

interface RoonContextType {
  enabled: boolean
  available: boolean
  zone: string
  setZone: (zone: string) => void
  playbackZone: string
  setPlaybackZone: (zone: string) => void
  zones: RoonZone[]
  playTrack: (trackId: number) => Promise<void>
  playPlaylist: (playlistId: number) => Promise<void>
  isLoading: boolean
  nowPlaying: NowPlayingTrack | null
  playbackControl: (control: 'play' | 'pause' | 'next' | 'previous' | 'stop') => Promise<void>
}

const RoonContext = createContext<RoonContextType | undefined>(undefined)

export function RoonProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [enabled, setEnabled] = useState(false)
  const [available, setAvailable] = useState(false)
  const [zone, setZone] = useState<string>(() => {
    return localStorage.getItem('roon_zone') || ''
  })
  const [playbackZone, setPlaybackZone] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [nowPlaying, setNowPlaying] = useState<NowPlayingTrack | null>(null)
  const [zones, setZones] = useState<RoonZone[]>([])

  // Vérifier le statut Roon au démarrage et périodiquement
  useEffect(() => {
    const checkRoonStatus = async () => {
      try {
        const response = await apiClient.get('/playback/roon/status')
        const data = response.data
        setEnabled(data.enabled)
        setAvailable(data.available)
      } catch (error) {
        setEnabled(false)
        setAvailable(false)
      } finally {
        setIsLoading(false)
      }
    }
    
    // Vérification initiale
    checkRoonStatus()
    
    // Vérification périodique toutes les 10 secondes
    const interval = setInterval(checkRoonStatus, 10000)
    
    // Cleanup
    return () => clearInterval(interval)
  }, [])

  // Polling pour le track actuellement joué
  useEffect(() => {
    const fetchNowPlaying = async () => {
      if (!enabled || !available) {
        setNowPlaying(null)
        return
      }
      
      try {
        const params = playbackZone ? { zone_name: playbackZone } : {}
        const response = await apiClient.get('/playback/roon/now-playing', { params })
        if (response.data?.title) {
          setNowPlaying(response.data as NowPlayingTrack)
        } else {
          setNowPlaying(null)
        }
      } catch (error) {
        setNowPlaying(null)
      }
    }

    // Vérification initiale + immédiate quand zone change
    if (enabled && available) {
      fetchNowPlaying()
    }

    // Polling toutes les 3 secondes quand Roon est disponible
    const interval = enabled && available ? setInterval(fetchNowPlaying, 3000) : null
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [enabled, available, playbackZone])

  // Récupérer la liste des zones disponibles
  useEffect(() => {
    const fetchZones = async () => {
      if (!enabled || !available) {
        setZones([])
        return
      }
      
      try {
        const response = await apiClient.get('/playback/roon/zones')
        if (response.data?.zones) {
          setZones(response.data.zones as RoonZone[])
        }
      } catch (error) {
        setZones([])
      }
    }

    // Vérification initiale
    if (enabled && available) {
      fetchZones()
    }

    // Polling toutes les 10 secondes quand Roon est disponible
    const interval = enabled && available ? setInterval(fetchZones, 10000) : null
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [enabled, available])

  // Initialiser playbackZone avec la zone en lecture, ou la première zone si aucune n'est en lecture
  useEffect(() => {
    if (!playbackZone && zones.length > 0) {
      // Chercher une zone qui est en lecture ou en pause
      const playingZone = zones.find(z => z.state === 'playing' || z.state === 'paused')
      const zoneToSelect = playingZone || zones[0]
      setPlaybackZone(zoneToSelect.name)
    } else if (playbackZone && zones.length > 0) {
      // Vérifier que la zone sélectionnée existe toujours dans la liste
      const zoneExists = zones.some(z => z.name === playbackZone)
      if (!zoneExists) {
        // Si la zone n'existe plus, chercher une zone en lecture ou sélectionner la première
        const playingZone = zones.find(z => z.state === 'playing' || z.state === 'paused')
        setPlaybackZone(playingZone ? playingZone.name : zones[0].name)
      }
    }
  }, [zones])

  // Sauvegarder la zone dans localStorage
  const handleSetZone = (newZone: string) => {
    setZone(newZone)
    localStorage.setItem('roon_zone', newZone)
  }

  // Jouer un track sur Roon
  const playTrack = async (trackId: number) => {
    if (!enabled || !available) {
      throw new Error('Roon n\'est pas disponible')
    }
    if (!zone) {
      throw new Error('Aucune zone Roon sélectionnée. Allez dans Paramètres pour choisir une zone.')
    }
    
    await apiClient.post('/playback/roon/play-track', {
      zone_name: zone,
      track_id: trackId
    })
  }

  // Jouer une playlist entière sur Roon
  const playPlaylist = async (playlistId: number) => {
    if (!enabled || !available) {
      throw new Error('Roon n\'est pas disponible')
    }
    if (!zone) {
      throw new Error('Aucune zone Roon sélectionnée. Allez dans Paramètres pour choisir une zone.')
    }
    
    await apiClient.post('/playback/roon/play-playlist', {
      zone_name: zone,
      playlist_id: playlistId
    })
  }

  // Contrôler la lecture (play, pause, next, previous, stop) avec retry automatique
  const playbackControl = async (control: 'play' | 'pause' | 'next' | 'previous' | 'stop', retryCount = 0, maxRetries = 2) => {
    if (!enabled || !available) {
      throw new Error('Roon n\'est pas disponible')
    }
    
    // Utiliser la zone du track en cours si disponible, sinon la zone sauvegardée
    const targetZone = nowPlaying?.zone_name || zone
    
    if (!targetZone) {
      throw new Error('Aucune zone Roon disponible. Veuillez d\'abord lancer un album.')
    }

    try {
      // Timeout de 5 secondes
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      await apiClient.post('/playback/roon/control', {
        zone_name: targetZone,
        control
      }, {
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      // Forcer un refresh des zones après 500ms pour avoir le nouvel état
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['roon-zones'] })
      }, 500)
    } catch (error) {
      console.error(`❌ Erreur contrôle Roon (tentative ${retryCount + 1}):`, error)
      
      // Retry automatique si possible
      if (retryCount < maxRetries) {
        console.log(`🔄 Nouvelle tentative contrôle '${control}' (${retryCount + 2}/${maxRetries + 1})...`)
        await new Promise(resolve => setTimeout(resolve, 500)) // Attendre 500ms avant retry
        return playbackControl(control, retryCount + 1, maxRetries)
      }
      
      // Échec final
      throw error
    }
  }

  return (
    <RoonContext.Provider value={{ enabled, available, zone, setZone: handleSetZone, playbackZone, setPlaybackZone, zones, playTrack, playPlaylist, isLoading, nowPlaying, playbackControl }}>
      {children}
    </RoonContext.Provider>
  )
}

export function useRoon() {
  const context = useContext(RoonContext)
  if (context === undefined) {
    throw new Error('useRoon must be used within a RoonProvider')
  }
  return context
}
