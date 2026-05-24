import { useTeleconsultationsStore } from '@/stores/teleconsultations'
import { shouldReloadTeleconsultationsTable } from '@/utils/notifications'

export function handleRealtimePayload(payload) {
  if (!shouldReloadTeleconsultationsTable(payload)) {
    return false
  }

  const teleStore = useTeleconsultationsStore()
  void teleStore.fetchList(undefined, { silent: true })
  return true
}
