import { ref, onUnmounted } from 'vue'
import { wsNotificationsUrl } from '@/api/client'
import {
  parseNotificationPayload,
  isHeartbeatPayload,
  NOTIFICATION_TYPES,
} from '@/utils/notifications'

const BASE_RECONNECT_MS = 1000
const MAX_RECONNECT_MS = 10000
const HEARTBEAT_INTERVAL_MS = 30_000

export function useNotifications(initialUserId, onMessage) {
  const connected = ref(false)
  const reconnecting = ref(false)
  const lastMessage = ref(null)

  let userId = initialUserId
  let socket = null
  let reconnectTimer = null
  let heartbeatTimer = null
  let reconnectAttempts = 0
  let intentionalClose = false
  let connectedUserId = null

  function setUserId(id) {
    userId = id ? String(id) : null
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  function sendPing() {
    if (!socket || socket.readyState !== WebSocket.OPEN) return
    try {
      socket.send(JSON.stringify({ type: NOTIFICATION_TYPES.PING }))
    } catch {
      scheduleReconnect()
    }
  }

  function startHeartbeat() {
    stopHeartbeat()
    sendPing()
    heartbeatTimer = setInterval(sendPing, HEARTBEAT_INTERVAL_MS)
  }

  function detachSocket() {
    stopHeartbeat()
    if (!socket) return
    socket.onopen = null
    socket.onmessage = null
    socket.onclose = null
    socket.onerror = null
    socket = null
    connectedUserId = null
  }

  function closeSocket() {
    stopHeartbeat()
    if (!socket) return
    const ws = socket
    socket.onopen = null
    socket.onmessage = null
    socket.onclose = null
    socket.onerror = null
    socket = null
    connectedUserId = null
    if (
      ws.readyState === WebSocket.OPEN ||
      ws.readyState === WebSocket.CONNECTING
    ) {
      ws.close()
    }
  }

  function dispatchPayload(payload) {
    if (isHeartbeatPayload(payload)) {
      return
    }

    lastMessage.value = payload.message || payload.raw
    onMessage?.(payload)
  }

  function handleIncoming(raw) {
    const payload = parseNotificationPayload(raw)
    dispatchPayload(payload)
    return payload
  }

  function scheduleReconnect() {
    if (intentionalClose || !userId) return
    if (reconnectTimer) return

    reconnecting.value = true
    const delay = Math.min(
      BASE_RECONNECT_MS * 2 ** reconnectAttempts,
      MAX_RECONNECT_MS
    )
    reconnectAttempts += 1

    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      openSocket()
    }, delay)
  }

  function openSocket() {
    if (!userId) return

    if (
      socket?.readyState === WebSocket.OPEN &&
      connectedUserId === userId
    ) {
      return
    }

    if (socket?.readyState === WebSocket.CONNECTING) {
      return
    }

    closeSocket()
    reconnecting.value = true

    const url = wsNotificationsUrl(userId)
    try {
      socket = new WebSocket(url)
      const openingForUser = userId

      socket.onopen = () => {
        if (userId !== openingForUser) return
        connected.value = true
        reconnecting.value = false
        reconnectAttempts = 0
        connectedUserId = openingForUser
        startHeartbeat()
      }

      socket.onmessage = (ev) => {
        handleIncoming(ev.data)
      }

      socket.onerror = () => {
        connected.value = false
      }

      socket.onclose = () => {
        connected.value = false
        reconnecting.value = !intentionalClose
        detachSocket()
        if (!intentionalClose && userId) {
          scheduleReconnect()
        }
      }
    } catch {
      connected.value = false
      detachSocket()
      scheduleReconnect()
    }
  }

  function connect() {
    if (!userId) return
    if (
      socket?.readyState === WebSocket.OPEN &&
      connectedUserId === userId
    ) {
      return
    }

    intentionalClose = false
    reconnectAttempts = 0
    clearReconnectTimer()
    openSocket()
  }

  function disconnect() {
    intentionalClose = true
    clearReconnectTimer()
    closeSocket()
    connected.value = false
    reconnecting.value = false
    reconnectAttempts = 0
  }

  function onVisibilityChange() {
    if (document.visibilityState !== 'visible' || !userId) return
    if (socket?.readyState === WebSocket.OPEN) {
      sendPing()
      return
    }
    reconnectAttempts = 0
    clearReconnectTimer()
    intentionalClose = false
    openSocket()
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', onVisibilityChange)
  }

  onUnmounted(() => {
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
    intentionalClose = true
    clearReconnectTimer()
    closeSocket()
    connected.value = false
    reconnecting.value = false
  })

  return {
    connected,
    reconnecting,
    lastMessage,
    setUserId,
    connect,
    disconnect,
    handleIncoming,
  }
}
