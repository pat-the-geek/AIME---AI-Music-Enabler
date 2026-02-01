import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import apiClient from '@/api/client'

interface RoonContextType {
  enabled: boolean
  available: boolean
  zone: string
  setZone: (zone: string) => void
  playTrack: (trackId: number) => Promise<void>
  isLoading: boolean
}

const RoonContext = createContext<RoonContextType | undefined>(undefined)

export function RoonProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(false)
  const [available, setAvailable] = useState(false)
  const [zone, setZone] = useState<string>(() => {
    return localStorage.getItem('roon_zone') || ''
  })
  const [isLoading, setIsLoading] = useState(true)

  // Vérifier le statut Roon au démarrage
  useEffect(() => {
    const checkRoonStatus = async () => {
      try {
        const response = await apiClient.get('/api/v1/roon/status')
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
    checkRoonStatus()
  }, [])

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
    
    await apiClient.post('/api/v1/roon/play-track', {
      zone_name: zone,
      track_id: trackId
    })
  }

  return (
    <RoonContext.Provider value={{ enabled, available, zone, setZone: handleSetZone, playTrack, isLoading }}>
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
