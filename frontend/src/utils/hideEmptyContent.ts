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

/**
 * Détermine si un texte doit être masqué parce qu'il est beaucoup plus court 
 * qu'un autre texte affiché à côté (rapport de taille < 0.5)
 * @param textA - Le texte à vérifier
 * @param textB - Le texte de référence pour comparaison
 * @returns true si textA doit être affiché, false si doit être masqué
 */
export const shouldShowSmallText = (textA: string | undefined, textB: string | undefined): boolean => {
  if (!textA || !textB) return true
  
  // Nettoyer les textes (enlever markdown, espaces, etc.)
  const cleanedA = textA
    .replace(/\*\*/g, '').replace(/\*/g, '').replace(/_/g, '')
    .replace(/`/g, '').trim()
  const cleanedB = textB
    .replace(/\*\*/g, '').replace(/\*/g, '').replace(/_/g, '')
    .replace(/`/g, '').trim()
  
  if (!cleanedA || !cleanedB) return true
  
  // Si la différence de longueur est > 100% (2x), masquer le plus court
  const ratio = cleanedA.length / cleanedB.length
  return ratio >= 0.5
}

/**
 * Retourne les styles sx pour masquer un texte trop court à côté d'un plus grand
 */
export const shouldHideSmallTextSx = (textA: string | undefined, textB: string | undefined) => {
  return !shouldShowSmallText(textA, textB) ? hiddenContentSx : {}
}
