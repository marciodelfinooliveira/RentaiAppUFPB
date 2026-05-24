const apiBase = import.meta.env.VITE_API_BASE_URL

if (!apiBase) {
  throw new Error('VITE_API_BASE_URL não está definida.')
}

if (typeof window !== 'undefined') {
  try {
    new URL(apiBase, window.location.origin)
  } catch {
    throw new Error(`VITE_API_BASE_URL inválida: ${apiBase}`)
  }
} else if (!/^https?:\/\//.test(apiBase) && !apiBase.startsWith('/')) {
  throw new Error(`VITE_API_BASE_URL inválida: ${apiBase}`)
}

export const API_BASE_URL = apiBase.replace(/\/$/, '')
