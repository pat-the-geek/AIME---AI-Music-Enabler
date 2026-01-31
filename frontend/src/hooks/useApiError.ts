import { AxiosError } from 'axios'
import { getErrorMessage } from '../api/client'

export interface ApiError {
  message: string
  statusCode?: number
  details?: any
}

/**
 * Convertir une erreur Axios en message utilisateur
 */
export function useApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    return {
      message: getErrorMessage(error),
      statusCode: error.response?.status,
      details: error.response?.data,
    }
  }

  if (error instanceof Error) {
    return {
      message: error.message,
    }
  }

  return {
    message: 'Une erreur inconnue s\'est produite',
  }
}

/**
 * Hook pour gérer les erreurs réseau courantes
 */
export function useNetworkError() {
  const isNetworkError = (error: unknown): boolean => {
    if (error instanceof AxiosError) {
      return !error.response || error.code === 'ERR_NETWORK'
    }
    return false
  }

  const isTimeoutError = (error: unknown): boolean => {
    if (error instanceof AxiosError) {
      return error.code === 'ECONNABORTED' || error.response?.status === 504
    }
    return false
  }

  const isServerError = (error: unknown): boolean => {
    if (error instanceof AxiosError) {
      return error.response?.status ? error.response.status >= 500 : false
    }
    return false
  }

  const isRetryableError = (error: unknown): boolean => {
    return isNetworkError(error) || isTimeoutError(error) || isServerError(error)
  }

  return {
    isNetworkError,
    isTimeoutError,
    isServerError,
    isRetryableError,
  }
}

/**
 * Hook pour exécuter une fonction avec retry automatique
 */
export function useRetry() {
  const retry = async <T,>(
    fn: () => Promise<T>,
    maxAttempts: number = 3,
    delayMs: number = 1000
  ): Promise<T> => {
    let lastError: Error | null = null

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        return await fn()
      } catch (error) {
        lastError = error as Error
        console.warn(`Attempt ${attempt + 1}/${maxAttempts} failed:`, lastError)

        if (attempt < maxAttempts - 1) {
          const delay = delayMs * Math.pow(2, attempt)
          await new Promise((resolve) => setTimeout(resolve, delay))
        }
      }
    }

    throw lastError
  }

  return { retry }
}
