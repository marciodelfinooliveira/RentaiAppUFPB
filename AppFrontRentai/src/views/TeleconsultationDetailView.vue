<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useTeleconsultationsStore } from '@/stores/teleconsultations'
import { useRoute, useRouter } from 'vue-router'
import {
  teleconsultationsApi,
  pareceresApi,
  usersApi,
  filesApi,
} from '@/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'
import FileAiAuditTag from '@/components/FileAiAuditTag.vue'
import { parseApiError } from '@/utils/errors'
import { formatDateTime } from '@/utils/format'
import { exportTeleconsultationPdf } from '@/utils/exportPdf'
import { STATUS_LABELS, TELECONSULTATION_STATUS } from '@/constants'
import {
  filterActiveFiles,
  formatFileSize,
  downloadPatientFile,
} from '@/utils/files'
import {
  shouldReloadTeleconsultationDetail,
  notificationToastText,
} from '@/utils/notifications'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const teleStore = useTeleconsultationsStore()
const { lastFetch: storeLastFetch } = storeToRefs(teleStore)

const tele = ref(null)
const contentKey = ref(0)
const patient = ref(null)
const timeline = ref([])
const specialists = ref([])
const error = ref('')
const loading = ref(true)
const refreshing = ref(false)
const toast = ref('')
const downloadingFileId = ref(null)
const showCancelModal = ref(false)
const cancelJustification = ref('')
const cancelLoading = ref(false)

const teleId = computed(() => route.params.id)

const teleDocuments = computed(() => filterActiveFiles(tele.value?.files))

const isAssignedSpecialist = computed(
  () =>
    auth.isSpecialist &&
    tele.value &&
    auth.user?.id === tele.value.specialist_doctor_id
)

const canCancel = computed(
  () =>
    isAssignedSpecialist.value &&
    (tele.value.status === TELECONSULTATION_STATUS.PENDENTE ||
      tele.value.status === TELECONSULTATION_STATUS.EM_ANDAMENTO)
)

const canRegisterParecer = computed(
  () =>
    isAssignedSpecialist.value &&
    tele.value.status === TELECONSULTATION_STATUS.EM_ANDAMENTO
)

const isCanceled = computed(
  () => tele.value?.status === TELECONSULTATION_STATUS.CANCELADA
)

const showSpecialistViewedHint = computed(
  () =>
    auth.isAPS &&
    tele.value?.status === TELECONSULTATION_STATUS.EM_ANDAMENTO
)

const specialistName = computed(() => {
  const s = specialists.value.find((x) => x.id === tele.value?.specialist_doctor_id)
  return s?.nome || ''
})

function applyTeleData(data) {
  if (!data) return
  tele.value = { ...data }
  if (data.patient) {
    patient.value = { ...data.patient }
  }
  contentKey.value += 1
  teleStore.upsertItem(data)
}

function syncFromStore() {
  const fresh = teleStore.findById(teleId.value)
  if (fresh) applyTeleData(fresh)
  return fresh
}

async function refreshTimeline() {
  const id = teleId.value
  if (!id) return
  try {
    const { data } = await pareceresApi.timeline(id)
    timeline.value = Array.isArray(data) ? data.map((p) => ({ ...p })) : []
  } catch (e) {
    if (!tele.value) {
      error.value = parseApiError(e)
    }
  }
}

async function loadTeleconsultationCore() {
  const id = teleId.value
  if (!id) return null

  try {
    const { data } = await teleconsultationsApi.get(id)
    applyTeleData(data)
    return data
  } catch (e) {
    const fromStore = teleStore.findById(id)
    if (fromStore) {
      applyTeleData(fromStore)
      return fromStore
    }
    throw e
  }
}

async function loadSpecialistsOnce() {
  if (specialists.value.length) return
  try {
    const { data } = await usersApi.specialists()
    specialists.value = data
  } catch {}
}

async function refreshAfterNotification() {
  refreshing.value = true
  error.value = ''
  syncFromStore()
  try {
    await loadTeleconsultationCore()
    await refreshTimeline()
  } catch (e) {
    if (!tele.value) {
      error.value = parseApiError(e)
    }
  } finally {
    refreshing.value = false
  }
}

async function loadDetail({ silent = false } = {}) {
  const id = teleId.value
  if (!id) return

  if (!silent) {
    loading.value = true
  } else {
    refreshing.value = true
  }
  error.value = ''

  try {
    await loadTeleconsultationCore()
    await refreshTimeline()

    if (!silent) {
      await loadSpecialistsOnce()
    }
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function openCancelModal() {
  cancelJustification.value = ''
  showCancelModal.value = true
}

function closeCancelModal() {
  showCancelModal.value = false
  cancelJustification.value = ''
}

async function submitCancel() {
  const justification = cancelJustification.value.trim()
  if (justification.length < 5) {
    error.value = 'A justificativa deve ter entre 5 e 500 caracteres.'
    return
  }

  cancelLoading.value = true
  error.value = ''
  try {
    const { data } = await teleconsultationsApi.cancel(teleId.value, {
      justification,
    })
    applyTeleData(data)
    closeCancelModal()
    toast.value = 'Teleconsultoria cancelada.'
    setTimeout(() => {
      toast.value = ''
    }, 5000)
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    cancelLoading.value = false
  }
}

function onNotification(ev) {
  const payload = ev.detail

  if (
    !shouldReloadTeleconsultationDetail(payload, teleId.value, {
      isAPS: auth.isAPS,
    })
  ) {
    return
  }

  toast.value = notificationToastText(payload)
  void refreshAfterNotification()
  setTimeout(() => {
    toast.value = ''
  }, 5000)
}

watch(storeLastFetch, () => {
  if (!teleId.value || !tele.value) return
  const fresh = teleStore.findById(teleId.value)
  if (!fresh || fresh.status === tele.value.status) return
  void refreshAfterNotification()
})

watch(teleId, (id, prev) => {
  if (id && id !== prev) {
    tele.value = null
    timeline.value = []
    void loadDetail()
  }
})

function onTeleconsultationUpdated(ev) {
  const targetId = ev.detail?.teleconsultation_id
  if (!targetId || String(targetId) !== String(teleId.value)) return
  toast.value = notificationToastText(ev.detail?.payload)
  void refreshAfterNotification()
  setTimeout(() => {
    toast.value = ''
  }, 5000)
}

onMounted(() => {
  void loadDetail()
  window.addEventListener('v4h-notification', onNotification)
  window.addEventListener('v4h-teleconsultation-updated', onTeleconsultationUpdated)
})

onUnmounted(() => {
  window.removeEventListener('v4h-notification', onNotification)
  window.removeEventListener(
    'v4h-teleconsultation-updated',
    onTeleconsultationUpdated
  )
})

async function downloadDoc(file) {
  downloadingFileId.value = file.id
  error.value = ''
  try {
    await downloadPatientFile(file, filesApi)
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    downloadingFileId.value = null
  }
}

function exportPdf() {
  exportTeleconsultationPdf({
    teleconsultation: tele.value,
    patient: patient.value,
    timeline: timeline.value,
    specialistName: specialistName.value,
  })
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Detalhes da teleconsultoria</h1>
      <div class="actions">
        <button type="button" class="btn btn-secondary" @click="router.push('/dashboard')">
          Voltar
        </button>
        <button
          v-if="tele"
          type="button"
          class="btn btn-ghost"
          @click="exportPdf"
        >
          Exportar PDF
        </button>
        <button
          v-if="canCancel"
          type="button"
          class="btn btn-danger"
          @click="openCancelModal"
        >
          Cancelar teleconsultoria
        </button>
        <router-link
          v-if="canRegisterParecer"
          :to="{ name: 'parecer-new', query: { teleconsultation_id: tele.id } }"
          class="btn btn-accent"
        >
          Registrar Parecer
        </router-link>
      </div>
    </div>

    <div v-if="toast" class="alert alert-info">{{ toast }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="loading" class="empty-state">Carregando…</div>

    <template v-else-if="tele" :key="contentKey">
      <div v-if="refreshing" class="alert alert-info subtle-refresh">
        Atualizando dados…
      </div>

      <div v-if="isCanceled && tele.rejection_justification" class="alert alert-error">
        <strong>Cancelada:</strong> {{ tele.rejection_justification }}
      </div>

      <div class="grid-2">
        <div class="card">
          <h2>Dados clínicos</h2>
          <dl class="detail-list">
            <dt>Especialidade</dt>
            <dd>{{ tele.specialty }}</dd>
            <dt>Status</dt>
            <dd>
              <StatusBadge
                :key="`status-${tele.status}-${contentKey}`"
                :status="tele.status"
                :show-in-progress-hint="showSpecialistViewedHint"
              />
            </dd>
            <dt>Paciente</dt>
            <dd>{{ patient?.nome || '—' }}</dd>
            <dt>Agendamento</dt>
            <dd>{{ formatDateTime(tele.scheduled_at) }}</dd>
            <dt>Hipótese diagnóstica</dt>
            <dd>{{ tele.diagnostic_hypothesis }}</dd>
            <dt>História clínica</dt>
            <dd>{{ tele.clinical_history }}</dd>
          </dl>
        </div>

        <div class="card">
          <h2>Linha do tempo</h2>
          <ul v-if="timeline.length" class="timeline">
            <li v-for="p in timeline" :key="p.id">
              <strong>{{ STATUS_LABELS[p.status_at_time] || p.status_at_time }}</strong>
              <br />
              <span class="muted">{{ formatDateTime(p.created_at) }}</span>
              <p>{{ p.comment }}</p>
            </li>
          </ul>
          <p v-else class="empty-state">Sem registros na timeline.</p>
        </div>
      </div>

      <div v-if="teleDocuments.length" class="card" style="margin-top: 1.25rem">
        <h2>Documentos anexados</h2>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Arquivo</th>
                <th>Validação IA</th>
                <th>Tamanho</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in teleDocuments" :key="doc.id">
                <td class="file-name">{{ doc.nome_arquivo }}</td>
                <td>
                  <FileAiAuditTag :file="doc" />
                  <span v-if="doc.ai_score == null" class="muted">—</span>
                </td>
                <td>{{ formatFileSize(doc.size_bytes) }}</td>
                <td class="actions-cell">
                  <button
                    type="button"
                    class="btn btn-ghost btn-sm"
                    :disabled="downloadingFileId === doc.id"
                    @click="downloadDoc(doc)"
                  >
                    {{ downloadingFileId === doc.id ? 'Baixando…' : 'Baixar' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card" style="margin-top: 1.25rem">
        <h2>Pareceres</h2>
        <ul v-if="timeline.length" class="parecer-list">
          <li v-for="p in timeline" :key="p.id">
            <p>{{ p.comment }}</p>
            <span class="muted">{{ formatDateTime(p.created_at) }}</span>
          </li>
        </ul>
        <p v-else class="empty-state">Nenhum parecer registrado.</p>
      </div>
    </template>

    <div v-if="showCancelModal" class="modal-backdrop" @click.self="closeCancelModal">
      <div class="modal card" role="dialog" aria-labelledby="cancel-title">
        <h2 id="cancel-title">Cancelar teleconsultoria</h2>
        <p class="muted">
          Informe a justificativa do cancelamento (mínimo 5 caracteres).
        </p>
        <div class="form-group">
          <label for="cancel-justification">Justificativa</label>
          <textarea
            id="cancel-justification"
            v-model="cancelJustification"
            rows="4"
            maxlength="500"
            placeholder="Descreva o motivo do cancelamento…"
          />
        </div>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-secondary"
            :disabled="cancelLoading"
            @click="closeCancelModal"
          >
            Voltar
          </button>
          <button
            type="button"
            class="btn btn-danger"
            :disabled="cancelLoading"
            @click="submitCancel"
          >
            {{ cancelLoading ? 'Cancelando…' : 'Confirmar cancelamento' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.detail-list { display: grid; grid-template-columns: 140px 1fr; gap: 0.5rem 1rem; margin: 0; }
.detail-list dt { font-weight: 600; color: var(--color-muted); font-size: 0.85rem; }
.detail-list dd { margin: 0; }
.muted { color: var(--color-muted); font-size: 0.85rem; }
.parecer-list { list-style: none; padding: 0; margin: 0; }
.parecer-list li { padding: 0.75rem 0; border-bottom: 1px solid var(--color-border); }
.actions-cell { white-space: nowrap; }
.subtle-refresh {
  margin-bottom: 1rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(26, 26, 46, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 100;
}
.modal {
  width: 100%;
  max-width: 480px;
}
.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
}
</style>
