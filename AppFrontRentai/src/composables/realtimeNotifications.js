import { useNotifications } from '@/composables/useNotifications'
import { handleRealtimePayload } from '@/utils/realtimeSync'

function dispatchRealtimePayload(payload) {
  handleRealtimePayload(payload)

  window.dispatchEvent(
    new CustomEvent('v4h-notification', { detail: payload })
  )

  if (payload?.teleconsultation_id) {
    window.dispatchEvent(
      new CustomEvent('v4h-teleconsultation-updated', {
        detail: {
          teleconsultation_id: payload.teleconsultation_id,
          payload,
        },
      })
    )
  }
}

let singleton = null

export function getRealtimeNotifications() {
  if (!singleton) {
    singleton = useNotifications(null, dispatchRealtimePayload)
  }
  return singleton
}
