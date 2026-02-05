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
  
  // Vérifier le texte exact
  if (EMPTY_MESSAGES.includes(trimmed)) return true
  
  // Vérifier aussi avec les balises markdown (**, *, etc.)
  // Nettoyer le texte de toutes les balises markdown courantes
  const cleaned = trimmed
    .replace(/\*\*/g, '')  // Enlever **gras**
    .replace(/\*/g, '')    // Enlever *italique*
    .replace(/_/g, '')     // Enlever _italique_
    .replace(/`/g, '')     // Enlever `code`
    .trim()
  
  return EMPTY_MESSAGES.includes(cleaned)
}

/**
 * Retourne les styles sx pour masquer le contenu vide (1x1 pixels invisible)
 */
export const hiddenContentSx = {
  width: '1px',
  height: '1px',
  overflow: 'hidden',
  visibility: 'hidden',
  position: 'absolute',
  margin: 0,
  padding: 0,
  border: 'none',
  clipPath: 'inset(100%)',
  clip: 'rect(0, 0, 0, 0)'
} as const

/**
 * Vérifie si un contenu doit être masqué et retourne les styles appropriés
 */
export const getHiddenContentSx = (content: string | undefined) => {
  return isEmptyContent(content) ? hiddenContentSx : {}
}
