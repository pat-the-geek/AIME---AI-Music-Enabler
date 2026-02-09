import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'

interface UIConfig {
  timeline_refresh_seconds: number
  journal_refresh_seconds: number
}

/**
 * Custom hook to fetch UI configuration from backend.
 * Caches configuration and syncs refresh intervals with tracker frequency.
 * 
 * @returns UI configuration object with refresh intervals in seconds
 */
export const useUIConfig = () => {
  const { data, isLoading } = useQuery<UIConfig>({
    queryKey: ['ui-config'],
    queryFn: async () => {
      const response = await apiClient.get('/services/config/ui')
      return response.data
    },
    staleTime: 60000, // Cache for 1 minute (config rarely changes)
    gcTime: 300000, // Keep in cache for 5 minutes
  })

  return {
    timelineRefreshMs: (data?.timeline_refresh_seconds ?? 120) * 1000,
    journalRefreshMs: (data?.journal_refresh_seconds ?? 120) * 1000,
    isLoading,
    rawConfig: data
  }
}
