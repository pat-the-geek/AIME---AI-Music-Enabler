/**
 * Utilitaire pour masquer le contenu "vide" qui doit être rendu invisible
 */

const EMPTY_MESSAGES = [
  'Aucune information disponible',
  'No information available',
  'Nenhuma informação disponível'
]

/**
 * Vérifie si le contenu est un message "vide"
 */
export const isEmptyContent = (content: string | undefined): boolean => {
  if (!content || typeof content !== 'string') return false
  const trimmed = content.trim()
  return EMPTY_MESSAGES.includes(trimmed)
}

/**
 * Retourne les styles sx pour masquer le contenu vide
 */
export const hiddenContentSx = {
  width: '1px',
  height: '1px',
  overflow: 'hidden',
  visibility: 'hidden',
  position: 'absolute',
  left: '-9999px',
  top: '-9999px'
} as const

/**
 * Vérifie si un contenu doit être masqué et retourne les styles appropriés
 */
export const getHiddenContentSx = (content: string | undefined) => {
  return isEmptyContent(content) ? hiddenContentSx : {}
}
