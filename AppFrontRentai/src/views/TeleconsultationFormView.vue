<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { patientsApi, usersApi, teleconsultationsApi } from '@/api'
import { SPECIALTIES } from '@/constants'
import { parseApiError, fieldErrorsFromApi } from '@/utils/errors'
import { parseAiRejectionFromError } from '@/utils/aiDocumentValidation'
import { filterActivePatients } from '@/utils/patientValidation'
import { fromDatetimeLocalValue } from '@/utils/format'
import {
  validateTeleconsultationCreateForm,
  buildTeleconsultationBody,
  datetimeLocalNow,
  datetimeLocalMaxAhead,
} from '@/utils/teleconsultationValidation'
import { validatePatientFiles, formatFileSize } from '@/utils/files'

const router = useRouter()

const step = ref('select-specialist')
const specialists = ref([])
const selectedSpecialist = ref(null)
const nameFilter = ref('')
const specialtyFilter = ref('')

const patients = ref([])
const patientNameFilter = ref('')
const error = ref('')
const loading = ref(false)
const loadingPatients = ref(false)
const formFiles = ref([])
const formFilesInput = ref(null)
const fieldErrors = ref({})

const scheduledAtMin = datetimeLocalNow()
const scheduledAtMax = datetimeLocalMaxAhead()

const specialtyLocked = computed(
  () =>
    !!selectedSpecialist.value?.specialty &&
    SPECIALTIES.includes(selectedSpecialist.value.specialty)
)

const form = ref({
  patient_id: '',
  specialist_doctor_id: '',
  specialty: SPECIALTIES[0],
  diagnostic_hypothesis: '',
  clinical_history: '',
  scheduled_at: '',
})

const filteredSpecialists = computed(() => {
  let list = specialists.value

  if (specialtyFilter.value) {
    list = list.filter(
      (s) =>
        (s.specialty || '').toLowerCase() ===
        specialtyFilter.value.toLowerCase()
    )
  }

  const q = nameFilter.value.trim().toLowerCase()
  if (q) {
    list = list.filter((s) => (s.nome || '').toLowerCase().includes(q))
  }

  return list
})

const hasActiveFilters = computed(
  () => !!specialtyFilter.value || !!nameFilter.value.trim()
)

const filteredPatients = computed(() => {
  const q = patientNameFilter.value.trim().toLowerCase()
  if (!q) return patients.value
  return patients.value.filter((p) =>
    (p.nome || '').toLowerCase().includes(q)
  )
})

function clearFilters() {
  specialtyFilter.value = ''
  nameFilter.value = ''
}

function syncPatientSelection() {
  if (!filteredPatients.value.length) {
    form.value.patient_id = ''
    return
  }
  const visible = filteredPatients.value.some(
    (p) => p.id === form.value.patient_id
  )
  if (!visible) {
    form.value.patient_id = filteredPatients.value[0].id
  }
}

watch(filteredPatients, syncPatientSelection)

onMounted(loadSpecialists)

async function loadSpecialists() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await usersApi.specialists()
    specialists.value = data
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loading.value = false
  }
}

async function loadPatients() {
  loadingPatients.value = true
  try {
    const { data } = await patientsApi.list()
    patients.value = filterActivePatients(data)
    if (patients.value.length) {
      form.value.patient_id = patients.value[0].id
    }
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loadingPatients.value = false
  }
}

function selectSpecialist(specialist) {
  selectedSpecialist.value = specialist
  form.value.specialist_doctor_id = specialist.id
  if (specialist.specialty && SPECIALTIES.includes(specialist.specialty)) {
    form.value.specialty = specialist.specialty
  } else if (specialist.specialty) {
    form.value.specialty = specialist.specialty
  }
  step.value = 'form'
  error.value = ''
  loadPatients()
}

function backToSpecialistSelection() {
  step.value = 'select-specialist'
  selectedSpecialist.value = null
  form.value.specialist_doctor_id = ''
  patientNameFilter.value = ''
  formFiles.value = []
  if (formFilesInput.value) formFilesInput.value.value = ''
}

function onFormFilesChange(ev) {
  formFiles.value = Array.from(ev.target.files || [])
  if (fieldErrors.value.files) delete fieldErrors.value.files
}

function removeFormFile(index) {
  formFiles.value = formFiles.value.filter((_, i) => i !== index)
  if (!formFiles.value.length && formFilesInput.value) {
    formFilesInput.value.value = ''
  }
}

async function submit() {
  error.value = ''
  fieldErrors.value = {}

  fieldErrors.value = {
    ...validateTeleconsultationCreateForm(form.value),
    ...validatePatientFiles(formFiles.value, { required: false }),
  }
  if (Object.keys(fieldErrors.value).length) return

  loading.value = true
  try {
    const body = buildTeleconsultationBody(form.value, fromDatetimeLocalValue)
    const { data } = await teleconsultationsApi.create(body, formFiles.value)

    router.push(`/teleconsultations/${data.id}`)
  } catch (e) {
    const ai = parseAiRejectionFromError(e)
    if (ai) {
      error.value = ai.message
      fieldErrors.value = {}
    } else {
      const apiFields = fieldErrorsFromApi(e)
      if (Object.keys(apiFields).length) {
        Object.assign(fieldErrors.value, apiFields)
        error.value = ''
      } else {
        error.value = parseApiError(e)
      }
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Nova Teleconsultoria</h1>
      <router-link to="/dashboard" class="btn btn-secondary">Voltar</router-link>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- Etapa 1: escolher especialista -->
    <div v-if="step === 'select-specialist'" class="card">
      <h2>Escolher especialista</h2>
      <p class="subtitle">
        Selecione o médico especialista que receberá a solicitação.
      </p>

      <div class="list-filters">
        <div class="form-group filter-field">
          <label for="spec-specialty-filter">Especialidade</label>
          <select id="spec-specialty-filter" v-model="specialtyFilter">
            <option value="">Todas as especialidades</option>
            <option v-for="s in SPECIALTIES" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="form-group filter-field">
          <label for="spec-name-filter">Nome</label>
          <input
            id="spec-name-filter"
            v-model="nameFilter"
            type="search"
            placeholder="Filtrar por nome"
            autocomplete="off"
          />
        </div>
        <button
          v-if="hasActiveFilters"
          type="button"
          class="btn btn-secondary btn-sm"
          @click="clearFilters"
        >
          Limpar filtros
        </button>
      </div>

      <div v-if="loading" class="empty-state">Carregando especialistas…</div>
      <div v-else-if="!specialists.length" class="empty-state">
        Nenhum especialista disponível.
      </div>
      <div v-else-if="!filteredSpecialists.length" class="empty-state">
        Nenhum especialista encontrado com os filtros aplicados.
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Especialidade</th>
              <th>E-mail</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in filteredSpecialists" :key="s.id">
              <td>{{ s.nome }}</td>
              <td>{{ s.specialty || '—' }}</td>
              <td>{{ s.email }}</td>
              <td class="actions-cell">
                <button
                  type="button"
                  class="btn btn-primary btn-sm"
                  @click="selectSpecialist(s)"
                >
                  Selecionar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Etapa 2: formulário da teleconsultoria -->
    <form v-else class="card" @submit.prevent="submit">
      <div class="form-step-header">
        <h2>Dados da teleconsultoria</h2>
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          @click="backToSpecialistSelection"
        >
          Trocar especialista
        </button>
      </div>

      <div v-if="selectedSpecialist" class="selected-specialist card-inline">
        <strong>Especialista:</strong> {{ selectedSpecialist.nome }}
        <span v-if="selectedSpecialist.specialty" class="muted">
          — {{ selectedSpecialist.specialty }}
        </span>
      </div>

      <div class="form-group patient-select-block">
        <label for="tele-patient">Paciente</label>
        <div
          v-if="patients.length && !loadingPatients"
          class="list-filters patient-filters"
        >
          <div class="form-group filter-field">
            <label for="tele-patient-name-filter">Nome</label>
            <input
              id="tele-patient-name-filter"
              v-model="patientNameFilter"
              type="search"
              placeholder="Filtrar por nome"
              autocomplete="off"
            />
          </div>
          <button
            v-if="patientNameFilter.trim()"
            type="button"
            class="btn btn-secondary btn-sm"
            @click="patientNameFilter = ''"
          >
            Limpar filtro
          </button>
        </div>
        <p
          v-if="patients.length && !loadingPatients && !filteredPatients.length"
          class="empty-filter-hint"
        >
          Nenhum paciente encontrado com esse nome.
        </p>
        <select
          id="tele-patient"
          v-model="form.patient_id"
          required
          :disabled="
            loadingPatients || !patients.length || !filteredPatients.length
          "
        >
          <option v-for="p in filteredPatients" :key="p.id" :value="p.id">
            {{ p.nome }} — {{ p.cpf }}
          </option>
        </select>
        <span v-if="fieldErrors.patient_id" class="error">{{
          fieldErrors.patient_id
        }}</span>
        <small v-if="loadingPatients">Carregando pacientes…</small>
        <small v-else-if="!patients.length">
          <router-link to="/patients">Cadastre um paciente primeiro</router-link>
        </small>
      </div>

      <div class="form-group">
        <label>Especialidade solicitada</label>
        <p v-if="specialtyLocked" class="readonly-field">{{ form.specialty }}</p>
        <select v-else id="tele-specialty" v-model="form.specialty" required>
          <option v-for="s in SPECIALTIES" :key="s" :value="s">{{ s }}</option>
        </select>
        <span v-if="fieldErrors.specialty" class="error">{{
          fieldErrors.specialty
        }}</span>
        <small v-if="specialtyLocked" class="hint">
          Definida pelo especialista selecionado.
        </small>
      </div>

      <div class="form-group">
        <label for="tele-scheduled">Data/hora prevista</label>
        <input
          id="tele-scheduled"
          v-model="form.scheduled_at"
          type="datetime-local"
          required
          :min="scheduledAtMin"
          :max="scheduledAtMax"
        />
        <span v-if="fieldErrors.scheduled_at" class="error">{{
          fieldErrors.scheduled_at
        }}</span>
        <small class="hint">Não pode ser no passado nem além de 2 anos.</small>
      </div>

      <div class="form-group">
        <label for="tele-hypothesis">Hipótese diagnóstica</label>
        <textarea
          id="tele-hypothesis"
          v-model="form.diagnostic_hypothesis"
          required
          minlength="5"
          maxlength="500"
          rows="3"
        />
        <span v-if="fieldErrors.diagnostic_hypothesis" class="error">{{
          fieldErrors.diagnostic_hypothesis
        }}</span>
        <small class="hint">Entre 5 e 500 caracteres.</small>
      </div>

      <div class="form-group">
        <label for="tele-history">História clínica resumida</label>
        <textarea
          id="tele-history"
          v-model="form.clinical_history"
          required
          minlength="10"
          maxlength="2000"
          rows="5"
        />
        <span v-if="fieldErrors.clinical_history" class="error">{{
          fieldErrors.clinical_history
        }}</span>
        <small class="hint">Entre 10 e 2000 caracteres.</small>
      </div>

      <div class="form-group">
        <label for="tele-files">Documentos de apoio</label>
        <input
          id="tele-files"
          ref="formFilesInput"
          type="file"
          accept=".pdf,image/*"
          multiple
          @change="onFormFilesChange"
        />
        <span v-if="fieldErrors.files" class="error">{{ fieldErrors.files }}</span>
        <small class="hint">
          Opcional: um ou mais arquivos (PDF ou imagem, máx. 10 MB cada).
        </small>
        <ul v-if="formFiles.length" class="file-list">
          <li v-for="(file, idx) in formFiles" :key="`${file.name}-${idx}`">
            <span>{{ file.name }} ({{ formatFileSize(file.size) }})</span>
            <button type="button" class="btn-link" @click="removeFormFile(idx)">
              remover
            </button>
          </li>
        </ul>
      </div>

      <button
        type="submit"
        class="btn btn-primary"
        :disabled="
          loading ||
          loadingPatients ||
          !patients.length ||
          !filteredPatients.length
        "
      >
        {{ loading ? 'Enviando…' : 'Solicitar teleconsultoria' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin: 0 0 1rem;
}
.hint {
  color: var(--color-muted);
  font-size: 0.8rem;
}
.muted {
  color: var(--color-muted);
  font-weight: normal;
}
.list-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.filter-field {
  flex: 1;
  min-width: 180px;
  max-width: 280px;
  margin-bottom: 0;
}
.actions-cell {
  white-space: nowrap;
}
.btn-sm {
  padding: 0.35rem 0.65rem;
  font-size: 0.85rem;
}
.form-step-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.form-step-header h2 {
  margin: 0;
}
.selected-specialist {
  margin-bottom: 1.25rem;
}
.card-inline {
  background: var(--color-bg);
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  font-size: 0.95rem;
}
.readonly-field {
  margin: 0;
  padding: 0.6rem 0.75rem;
  background: var(--color-bg);
  border-radius: var(--radius);
  font-weight: 500;
}
.patient-select-block .patient-filters {
  margin-bottom: 0.75rem;
}
.empty-filter-hint {
  margin: 0 0 0.5rem;
  font-size: 0.9rem;
  color: var(--color-muted);
}
.file-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0;
}
.file-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.35rem 0;
  font-size: 0.9rem;
}
.btn-link {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
}
</style>
