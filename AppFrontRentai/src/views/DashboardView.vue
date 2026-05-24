<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTeleconsultationsStore } from '@/stores/teleconsultations'
import { patientsApi } from '@/api'
import { STATUS_FILTER_OPTIONS, TELECONSULTATION_STATUS } from '@/constants'
import StatusBadge from '@/components/StatusBadge.vue'
import { patientInitials, formatDate } from '@/utils/format'
import { parseApiError } from '@/utils/errors'
import { filterActivePatients } from '@/utils/patientValidation'
import { buildTeleconsultationListParams } from '@/utils/teleconsultationFilters'
import {
  shouldReloadTeleconsultationsTable,
  notificationToastText,
} from '@/utils/notifications'

const router = useRouter()
const auth = useAuthStore()
const teleStore = useTeleconsultationsStore()
const {
  items: storeItems,
  loading: storeLoading,
  refreshing: storeRefreshing,
  listVersion,
} = storeToRefs(teleStore)

const search = ref('')
const statusFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const patientsMap = ref({})
const error = ref('')
const toast = ref('')

const tableItems = ref([])

function buildListParams() {
  return buildTeleconsultationListParams({
    statusFilter: statusFilter.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
  })
}

function applySearchFilter(list) {
  const q = search.value.trim().toLowerCase()
  if (!q) return list

  return list.filter((t) => {
    const patient = resolvePatient(t)
    const name = patient?.nome?.toLowerCase() || ''
    return (
      name.includes(q) ||
      t.specialty?.toLowerCase().includes(q) ||
      t.id?.toLowerCase().includes(q)
    )
  })
}

function syncTableFromStore() {
  const mapped = storeItems.value.map((t) => ({
    ...t,
    patient: t.patient ? { ...t.patient } : undefined,
  }))
  tableItems.value = applySearchFilter(mapped)
}

const filteredItems = computed(() => tableItems.value)

function mergePatientsFromTeleconsultations(items = []) {
  const map = { ...patientsMap.value }
  for (const t of items) {
    if (t.patient?.id) {
      map[t.patient.id] = t.patient
    }
  }
  patientsMap.value = map
}

function resolvePatient(teleItem) {
  return teleItem?.patient || patientsMap.value[teleItem?.patient_id] || null
}

async function loadPatients() {
  mergePatientsFromTeleconsultations(storeItems.value)

  if (!auth.isDoctor) return

  try {
    const { data } = await patientsApi.list()
    const active = filterActivePatients(data)
    patientsMap.value = {
      ...patientsMap.value,
      ...Object.fromEntries(active.map((p) => [p.id, p])),
    }
  } catch {}
}

async function loadTeleconsultations({ silent = false } = {}) {
  error.value = ''

  try {
    await teleStore.fetchList(buildListParams(), { silent })
    mergePatientsFromTeleconsultations(storeItems.value)
    syncTableFromStore()
  } catch (e) {
    error.value = parseApiError(e)
  }
}

function onNotification(ev) {
  const payload = ev.detail

  if (!shouldReloadTeleconsultationsTable(payload)) {
    return
  }

  toast.value = notificationToastText(payload)
  void loadTeleconsultations({ silent: true }).then(() => loadPatients())
  setTimeout(() => {
    toast.value = ''
  }, 5000)
}

watch(search, () => {
  syncTableFromStore()
})

watch([statusFilter, dateFrom, dateTo], () => {
  void loadTeleconsultations()
})

watch(storeItems, () => {
  syncTableFromStore()
})

watch(listVersion, () => {
  mergePatientsFromTeleconsultations(storeItems.value)
  syncTableFromStore()
})

onMounted(async () => {
  await loadTeleconsultations()
  await loadPatients()
  window.addEventListener('v4h-notification', onNotification)
})

onUnmounted(() => {
  window.removeEventListener('v4h-notification', onNotification)
})

function patientLabel(teleItem) {
  const p = resolvePatient(teleItem)
  if (!p?.nome) return '—'
  return `${patientInitials(p.nome)} — ${p.nome}`
}
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Teleconsultorias</h1>
        <p class="muted">Gerencie solicitações e acompanhe o status</p>
      </div>
      <router-link
        v-if="auth.isAPS"
        to="/teleconsultations/new"
        class="btn btn-accent"
      >
        Nova Teleconsultoria
      </router-link>
    </div>

    <div v-if="toast" class="alert alert-info">{{ toast }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div class="card">
      <div class="filters">
        <input
          v-model="search"
          type="search"
          placeholder="Buscar por paciente ou especialidade…"
        />
        <select v-model="statusFilter">
          <option
            v-for="opt in STATUS_FILTER_OPTIONS"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>
        <input v-model="dateFrom" type="date" title="Data inicial" />
        <input v-model="dateTo" type="date" title="Data final" />
        <button type="button" class="btn btn-secondary" @click="loadTeleconsultations()">
          Atualizar
        </button>
      </div>

      <div v-if="storeRefreshing" class="refresh-hint">Atualizando lista…</div>

      <div v-if="storeLoading && !tableItems.length" class="empty-state">
        Carregando…
      </div>

      <div v-else-if="!filteredItems.length" class="empty-state">
        Nenhuma teleconsultoria encontrada.
      </div>

      <div v-else class="table-wrap" :key="`table-${listVersion}`">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Paciente</th>
              <th>Especialidade</th>
              <th>Data</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in filteredItems"
              :key="`${item.id}-${item.status}-${listVersion}`"
              :class="{
                'row-cancelada': item.status === TELECONSULTATION_STATUS.CANCELADA,
              }"
            >
              <td><code class="id-short">{{ item.id.slice(0, 8) }}…</code></td>
              <td>{{ patientLabel(item) }}</td>
              <td>{{ item.specialty }}</td>
              <td>{{ formatDate(item.scheduled_at || item.created_at) }}</td>
              <td class="status-cell">
                <span
                  v-if="item.status === TELECONSULTATION_STATUS.CANCELADA"
                  class="cancel-icon"
                  title="Teleconsultoria cancelada"
                  aria-hidden="true"
                >
                  ⊘
                </span>
                <StatusBadge
                  :key="`badge-${item.id}-${item.status}-${listVersion}`"
                  :status="item.status"
                />
              </td>
              <td>
                <button
                  type="button"
                  class="btn btn-ghost"
                  @click="router.push(`/teleconsultations/${item.id}`)"
                >
                  Ver detalhes
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.muted { color: var(--color-muted); font-size: 0.9rem; margin: 0; }
.id-short { font-size: 0.8rem; }
.refresh-hint {
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  color: var(--color-muted);
}

.row-cancelada {
  opacity: 0.72;
  background: rgba(248, 215, 218, 0.35);
}

.row-cancelada td {
  color: var(--color-muted);
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.cancel-icon {
  font-size: 1rem;
  color: var(--color-danger);
  line-height: 1;
}
</style>
