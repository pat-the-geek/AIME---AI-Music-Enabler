import axios, { AxiosError } from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 secondes timeout
})

// Configuration retry
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 seconde

interface RetryConfig {
  count: number
  delay: number
}

const retryConfig: Map<string, RetryConfig> = new Map()

/**
 * Véri fier si une erreur est réessayable
 */
function isRetryableError(error: AxiosError): boolean {
  if (!error.response) {
    // Erreurs réseau (pas de réponse)
    return true
  }

  const status = error.response.status
  // Réessayer sur : timeout (408), 429 (rate limit), 5xx (serveur)
  return status === 408 || status === 429 || (status >= 500 && status < 600)
}

/**
 * Attendre avec délai exponentiel + jitter
 */
function getRetryDelay(attempt: number): number {
  const baseDelay = RETRY_DELAY * Math.pow(2, attempt)
  const jitter = Math.random() * 0.1 * baseDelay
  return baseDelay + jitter
}

/**
 * Formater le message d'erreur pour l'utilisateur
 */
export function getErrorMessage(error: AxiosError): string {
  if (!error.response) {
    // Erreur réseau
    if (error.code === 'ECONNABORTED') {
      return 'La requête a dépassé le délai d\'attente. Vérifiez votre connexion réseau.'
    }
    if (error.message === 'Network Error') {
      return 'Erreur réseau. Vérifiez votre connexion à Internet.'
    }
    return 'Impossible de se connecter au serveur. Vérifiez votre connexion réseau.'
  }

  const status = error.response.status
  const data = error.response.data as any

  // Réponse du serveur avec détails
  if (data?.message) {
    return data.message
  }

  // Messages par code HTTP
  const statusMessages: { [key: number]: string } = {
    400: 'Requête invalide',
    401: 'Non authentifié',
    403: 'Accès refusé',
    404: 'Ressource non trouvée',
    408: 'Délai d\'attente dépassé',
    429: 'Trop de requêtes. Veuillez attendre.',
    500: 'Erreur serveur interne',
    502: 'Erreur passerelle',
    503: 'Service indisponible. Réessai en cours...',
    504: 'Délai d\'attente passerelle',
  }

  return statusMessages[status] || `Erreur ${status}`
}

// Intercepteur de requête
apiClient.interceptors.request.use(
  (config) => {
    // Ajouter un ID de requête pour le traçage
    config.headers['X-Request-ID'] = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Intercepteur de réponse avec retry logic
apiClient.interceptors.response.use(
  (response) => {
    // Succès - réinitialiser le compteur de retry
    const key = response.config.url || ''
    retryConfig.delete(key)
    return response
  },
  async (error: AxiosError) => {
    const config = error.config

    if (!config) {
      console.error('API Error:', error)
      return Promise.reject(error)
    }

    // Ne pas réessayer les GET avec body ou les requests non-HTTP
    if (!isRetryableError(error)) {
      console.error('Non-retryable API Error:', error)
      return Promise.reject(error)
    }

    // Déterminer le nombre de tentatives
    const key = config.url || ''
    const currentRetry = retryConfig.get(key)?.count ?? 0

    if (currentRetry >= MAX_RETRIES) {
      console.error(`Max retries (${MAX_RETRIES}) reached for ${key}:`, error)
      return Promise.reject(error)
    }

    // Calculer le délai d'attente
    const delay = getRetryDelay(currentRetry)
    retryConfig.set(key, { count: currentRetry + 1, delay })

    console.warn(
      `Retry ${currentRetry + 1}/${MAX_RETRIES} for ${config.method?.toUpperCase()} ${key} after ${delay.toFixed(0)}ms`
    )

    // Attendre avant de réessayer
    await new Promise((resolve) => setTimeout(resolve, delay))

    // Réessayer
    return apiClient.request(config)
  }
)

export default apiClient
