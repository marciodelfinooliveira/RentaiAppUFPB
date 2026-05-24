import { resolveUploadErrorMessage } from '@/utils/aiDocumentValidation'

export function parseApiError(error) {
  const uploadMessage = resolveUploadErrorMessage(error)
  if (uploadMessage) return uploadMessage
  const data = error?.response?.data
  if (!data) return error?.message || 'Erro de conexão'

  if (data.detalhe && Array.isArray(data.detalhe)) {
    return data.detalhe
      .map((d) => {
        const campo = (d.campo || '').replace(/^body\./, '')
        return campo ? `${campo}: ${d.mensagem}` : d.mensagem
      })
      .join('; ')
  }

  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  }

  return 'Erro inesperado'
}

export function fieldErrorsFrom422(error) {
  const data = error?.response?.data
  if (!data?.detalhe || !Array.isArray(data.detalhe)) return {}
  const map = {}
  for (const item of data.detalhe) {
    const key = (item.campo || '').replace(/^body\./, '')
    if (key) map[key] = item.mensagem
  }
  return map
}

export function fieldErrorsFromApi(error) {
  const map = fieldErrorsFrom422(error)
  const status = error?.response?.status
  const detail = error?.response?.data?.detail
  if (status === 409 && typeof detail === 'string') {
    if (detail.toLowerCase().includes('e-mail') || detail.toLowerCase().includes('email')) {
      map.email = detail
    }
  }
  if (status === 400 && typeof detail === 'string') {
    if (detail.toLowerCase().includes('cpf')) {
      map.cpf = detail
    }
  }
  return map
}
