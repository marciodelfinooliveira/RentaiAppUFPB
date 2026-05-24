export const NOTIFICATION_TYPES = {
  RELOAD_TABLE: 'RELOAD_TABLE',
  PING: 'ping',
  PONG: 'pong',
}

function normalizeMessageType(value) {
  if (value == null || value === '') return null
  const raw = String(value).trim()
  const lower = raw.toLowerCase()
  if (lower === 'ping') return NOTIFICATION_TYPES.PING
  if (lower === 'pong') return NOTIFICATION_TYPES.PONG
  if (raw.toUpperCase() === NOTIFICATION_TYPES.RELOAD_TABLE) {
    return NOTIFICATION_TYPES.RELOAD_TABLE
  }
  return raw
}

export function isHeartbeatPayload(payload) {
  const t = (payload?.type || '').toLowerCase()
  return t === NOTIFICATION_TYPES.PING || t === NOTIFICATION_TYPES.PONG
}

export function parseNotificationPayload(raw) {
  const text = raw == null ? '' : String(raw)
  if (!text) {
    return { type: null, message: '', teleconsultation_id: null, raw: text }
  }

  try {
    const data = JSON.parse(text)
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return {
        type: normalizeMessageType(data.type),
        message: data.message ?? data.detail ?? '',
        teleconsultation_id: data.teleconsultation_id
          ? String(data.teleconsultation_id)
          : null,
        raw: text,
        data,
      }
    }
  } catch {}

  return { type: null, message: text, teleconsultation_id: null, raw: text }
}

function messageImpliesTableReload(message) {
  const msg = (message || '').toLowerCase()
  if (!msg) return false
  return (
    msg.includes('teleconsult') ||
    msg.includes('parecer') ||
    msg.includes('andamento') ||
    msg.includes('cancelad')
  )
}

export function shouldReloadTeleconsultationsTable(payload) {
  if (!payload) return false
  if (isHeartbeatPayload(payload)) return false
  if (payload.type === NOTIFICATION_TYPES.RELOAD_TABLE) return true
  if (payload.teleconsultation_id) return true
  if (!payload.type && payload.message) return true
  return messageImpliesTableReload(payload.message)
}

export function notificationToastText(payload) {
  if (!payload) return 'Nova atualização'
  return payload.message || 'Nova atualização'
}

export function shouldReloadTeleconsultationDetail(
  payload,
  currentTeleId,
  { isAPS = false } = {}
) {
  if (!payload || !currentTeleId) return false
  if (isHeartbeatPayload(payload)) return false

  if (payload.type === NOTIFICATION_TYPES.RELOAD_TABLE) {
    if (!payload.teleconsultation_id) {
      return isAPS
    }
    return String(payload.teleconsultation_id) === String(currentTeleId)
  }

  if (!payload.type && payload.message) {
    return true
  }

  return false
}
