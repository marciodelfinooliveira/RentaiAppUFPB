export function parseAiRejectionFromError(error) {
  if (error?.response?.status !== 422) return null

  const detail = error?.response?.data?.detail
  if (typeof detail !== 'string') return null

  const lower = detail.toLowerCase()
  if (!lower.includes('rejeitado') || !lower.includes('ia')) {
    return null
  }

  const scoreMatch = detail.match(/Score:\s*([\d.]+)/i)
  const thresholdMatch = detail.match(/Limiar:\s*([\d.]+)/i)

  const score = scoreMatch ? scoreMatch[1] : null
  const threshold = thresholdMatch ? thresholdMatch[1] : null

  const message = score
    ? `Documento rejeitado pela IA (Score: ${score}). Por favor, verifique a qualidade do arquivo.`
    : 'Documento rejeitado pela IA. Por favor, verifique a qualidade do arquivo.'

  return { score, threshold, message, raw: detail }
}

export function resolveUploadErrorMessage(error) {
  const ai = parseAiRejectionFromError(error)
  if (ai) return ai.message
  return null
}

export function formatAiScoreDisplay(score) {
  if (score == null || score === '') return '—'
  const n = Number(score)
  if (Number.isNaN(n)) return String(score)
  return n.toFixed(2)
}

export function buildAiAuditTooltip(file) {
  if (!file || file.ai_score == null) return ''

  const parts = [`Score de confiança: ${formatAiScoreDisplay(file.ai_score)}`]
  if (file.ai_provider) parts.push(`Provedor: ${file.ai_provider}`)
  if (file.ai_threshold != null) {
    parts.push(`Limiar aplicado: ${formatAiScoreDisplay(file.ai_threshold)}`)
  }
  if (file.created_at) {
    parts.push(`Validado em: ${new Date(file.created_at).toLocaleString('pt-BR')}`)
  }
  return parts.join('\n')
}

export function hasAiAuditData(file) {
  return file != null && file.ai_score != null
}
