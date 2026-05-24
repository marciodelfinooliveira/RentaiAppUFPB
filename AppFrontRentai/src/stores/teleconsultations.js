import { defineStore } from 'pinia'
import { ref } from 'vue'
import { teleconsultationsApi } from '@/api'

export const useTeleconsultationsStore = defineStore('teleconsultations', () => {
  const items = ref([])
  const loading = ref(false)
  const refreshing = ref(false)
  const lastFetch = ref(null)
  const listVersion = ref(0)
  const listQueryParams = ref({})

  async function fetchList(params, { silent = false } = {}) {
    const query =
      params !== undefined ? params : { ...listQueryParams.value }
    if (params !== undefined) {
      listQueryParams.value = { ...query }
    }
    if (silent) {
      refreshing.value = true
    } else {
      loading.value = true
    }

    try {
      const { data } = await teleconsultationsApi.list(query)
      const next = Array.isArray(data)
        ? data.map((item) => ({
            ...item,
            patient: item.patient ? { ...item.patient } : undefined,
            files: Array.isArray(item.files)
              ? item.files.map((f) => ({ ...f }))
              : [],
          }))
        : []
      items.value = next
      lastFetch.value = Date.now()
      listVersion.value += 1
      return items.value
    } finally {
      if (silent) {
        refreshing.value = false
      } else {
        loading.value = false
      }
    }
  }

  function findById(id) {
    if (!id) return null
    return items.value.find((t) => String(t.id) === String(id)) ?? null
  }

  function upsertItem(tele) {
    if (!tele?.id) return
    const entry = {
      ...tele,
      patient: tele.patient ? { ...tele.patient } : undefined,
      files: Array.isArray(tele.files)
        ? tele.files.map((f) => ({ ...f }))
        : [],
    }
    const idx = items.value.findIndex((t) => String(t.id) === String(tele.id))
    if (idx >= 0) {
      items.value[idx] = entry
    } else {
      items.value = [entry, ...items.value]
    }
    listVersion.value += 1
    lastFetch.value = Date.now()
  }

  return {
    items,
    loading,
    refreshing,
    lastFetch,
    listVersion,
    listQueryParams,
    fetchList,
    findById,
    upsertItem,
  }
})
