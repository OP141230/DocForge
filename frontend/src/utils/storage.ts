import { DocumentRequirements } from '../types/document'

const STORAGE_KEYS = {
  DOCUMENT_CONFIG: 'docforge_last_document_config',
}

export function saveDocumentConfig(config: DocumentRequirements): void {
  try {
    localStorage.setItem(STORAGE_KEYS.DOCUMENT_CONFIG, JSON.stringify(config))
  } catch (error) {
    console.error('Failed to save document config to localStorage:', error)
  }
}

export function loadDocumentConfig(): DocumentRequirements | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.DOCUMENT_CONFIG)
    if (!stored) return null
    return JSON.parse(stored) as DocumentRequirements
  } catch (error) {
    console.error('Failed to load document config from localStorage:', error)
    return null
  }
}
