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
}

interface RoonContextType {
  enabled: boolean
  available: boolean
  zone: string
  setZone: (zone: string) => void
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
  const [isLoading, setIsLoading] = useState(true)
  const [nowPlaying, setNowPlaying] = useState<NowPlayingTrack | null>(null)

  // Vérifier le statut Roon au démarrage et périodiquement
  useEffect(() => {
    const checkRoonStatus = async () => {
      try {
        const response = await apiClient.get('/roon/status')
        const data = response.data
        setEnabled(data.enabled)
        setAvailable(data.available)
      } catch (error) {
        console.error('Erreur lors de la vérification du statut Roon:', error)
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
        const response = await apiClient.get('/roon/now-playing')
        if (response.data?.title) {
          setNowPlaying(response.data as NowPlayingTrack)
        } else {
          setNowPlaying(null)
        }
      } catch (error) {
        console.debug('Aucun track en cours de lecture')
        setNowPlaying(null)
      }
    }

    // Vérification initiale
    if (enabled && available) {
      fetchNowPlaying()
    }

    // Polling toutes les 3 secondes quand Roon est disponible
    const interval = enabled && available ? setInterval(fetchNowPlaying, 3000) : null
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [enabled, available])

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
    
    await apiClient.post('/roon/play-track', {
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
    
    await apiClient.post('/roon/play-playlist', {
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
      
      await apiClient.post('/roon/control', {
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
    <RoonContext.Provider value={{ enabled, available, zone, setZone: handleSetZone, playTrack, playPlaylist, isLoading, nowPlaying, playbackControl }}>
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
