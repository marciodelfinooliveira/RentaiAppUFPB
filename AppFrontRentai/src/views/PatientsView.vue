<script setup>
import { ref, computed, onMounted } from 'vue'
import { patientsApi, filesApi } from '@/api'
import { parseApiError, fieldErrorsFromApi } from '@/utils/errors'
import { parseAiRejectionFromError } from '@/utils/aiDocumentValidation'
import FileAiAuditTag from '@/components/FileAiAuditTag.vue'
import { formatDate, formatDateTime, toDateInputValue } from '@/utils/format'
import { formatCpfDisplay, cleanCpf } from '@/utils/cpf'
import {
  validatePatientCreateForm,
  validatePatientUpdateForm,
  buildPatientBody,
  buildPatientUpdatePayload,
  filterActivePatients,
} from '@/utils/patientValidation'
import {
  validatePatientFiles,
  formatFileSize,
  filterActiveFiles,
  downloadPatientFile,
} from '@/utils/files'

const patients = ref([])
const error = ref('')
const success = ref('')
const loading = ref(false)
const fieldErrors = ref({})

const editingId = ref(null)
const form = ref({
  nome: '',
  cpf: '',
  data_nascimento: '',
})

const formFiles = ref([])
const formFilesInput = ref(null)

const todayIso = new Date().toISOString().slice(0, 10)
const cpfFilter = ref('')

const isEditing = computed(() => !!editingId.value)
const formTitle = computed(() =>
  isEditing.value ? 'Editar paciente' : 'Novo paciente'
)
const editingPatient = computed(() =>
  patients.value.find((p) => p.id === editingId.value)
)

const patientDocuments = computed(() =>
  filterActiveFiles(editingPatient.value?.files)
)

const filteredPatients = computed(() => {
  const query = cleanCpf(cpfFilter.value)
  if (!query) return patients.value
  return patients.value.filter((p) => cleanCpf(p.cpf).includes(query))
})

const downloadingFileId = ref(null)
const deletingFileId = ref(null)

function resetForm() {
  editingId.value = null
  form.value = { nome: '', cpf: '', data_nascimento: '' }
  formFiles.value = []
  fieldErrors.value = {}
  if (formFilesInput.value) formFilesInput.value.value = ''
}

function startNewPatient() {
  resetForm()
  error.value = ''
  success.value = ''
}

function startEdit(patient) {
  editingId.value = patient.id
  form.value = {
    nome: patient.nome,
    cpf: patient.cpf,
    data_nascimento: toDateInputValue(patient.data_nascimento),
  }
  formFiles.value = []
  error.value = ''
  success.value = ''
  fieldErrors.value = {}
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

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await patientsApi.list()
    patients.value = filterActivePatients(data)
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loading.value = false
  }
}

async function uploadFilesForPatient(patientId, files) {
  for (const file of files) {
    try {
      await filesApi.upload(patientId, file)
    } catch (e) {
      const ai = parseAiRejectionFromError(e)
      if (ai) {
        throw new Error(
          `${file.name}: ${ai.message}`
        )
      }
      throw e
    }
  }
}

async function submitPatient() {
  error.value = ''
  success.value = ''
  fieldErrors.value = {}

  if (isEditing.value) {
    const original = editingPatient.value
    if (!original) return

    fieldErrors.value = {
      ...validatePatientUpdateForm(form.value),
      ...validatePatientFiles(formFiles.value, { required: false }),
    }
    if (Object.keys(fieldErrors.value).length) return

    const payload = buildPatientUpdatePayload(form.value, original)
    const hasDataChanges = Object.keys(payload).length > 0
    const hasNewFiles = formFiles.value.length > 0

    if (!hasDataChanges && !hasNewFiles) {
      success.value = 'Nenhuma alteração para salvar.'
      return
    }

    loading.value = true
    try {
      if (hasDataChanges) {
        await patientsApi.update(editingId.value, payload)
      }
      if (hasNewFiles) {
        await uploadFilesForPatient(editingId.value, formFiles.value)
      }
      const parts = []
      if (hasDataChanges) parts.push('dados atualizados')
      if (hasNewFiles) {
        parts.push(
          `${formFiles.value.length} documento(s) adicionado(s)`
        )
      }
      success.value = `Paciente: ${parts.join('; ')}.`
      formFiles.value = []
      if (formFilesInput.value) formFilesInput.value.value = ''
      await load()
    } catch (e) {
      if (e?.response) {
        applySubmitError(e)
      } else {
        error.value = e.message || 'Erro ao enviar documentos.'
      }
    } finally {
      loading.value = false
    }
    return
  }

  fieldErrors.value = {
    ...validatePatientCreateForm(form.value),
    ...validatePatientFiles(formFiles.value, { required: false }),
  }
  if (Object.keys(fieldErrors.value).length) return

  loading.value = true
  try {
    await patientsApi.create(buildPatientBody(form.value), formFiles.value)
    success.value = formFiles.value.length
      ? `Paciente cadastrado com ${formFiles.value.length} documento(s).`
      : 'Paciente cadastrado.'
    resetForm()
    await load()
  } catch (e) {
    if (e?.response) {
      applySubmitError(e)
    } else {
      error.value = e.message || 'Erro ao cadastrar paciente.'
    }
  } finally {
    loading.value = false
  }
}

function applySubmitError(e) {
  const ai = parseAiRejectionFromError(e)
  if (ai) {
    error.value = ai.message
    fieldErrors.value = {}
    return
  }

  const apiFields = fieldErrorsFromApi(e)
  if (Object.keys(apiFields).length) {
    Object.assign(fieldErrors.value, apiFields)
    error.value = ''
  } else {
    error.value = parseApiError(e)
  }
}

async function handleDownload(file) {
  error.value = ''
  downloadingFileId.value = file.id
  try {
    await downloadPatientFile(file, filesApi)
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    downloadingFileId.value = null
  }
}

async function handleDeleteFile(file) {
  const ok = window.confirm(
    `Excluir o arquivo "${file.nome_arquivo}"? Esta ação não pode ser desfeita.`
  )
  if (!ok) return

  error.value = ''
  success.value = ''
  deletingFileId.value = file.id
  try {
    await filesApi.remove(file.id)
    success.value = 'Documento excluído.'
    await load()
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    deletingFileId.value = null
  }
}

async function removePatient(patient) {
  const ok = window.confirm(
    `Excluir o paciente "${patient.nome}"? O registro será removido (soft delete).`
  )
  if (!ok) return

  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await patientsApi.remove(patient.id)
    success.value = 'Paciente excluído.'
    if (editingId.value === patient.id) resetForm()
    await load()
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Pacientes</h1>
      <button
        v-if="isEditing"
        type="button"
        class="btn btn-accent"
        :disabled="loading"
        @click="startNewPatient"
      >
        Cadastrar paciente
      </button>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div :class="['patient-layout', { 'patient-layout--edit': isEditing }]">
    <form class="card patient-form" @submit.prevent="submitPatient">
      <h2>{{ formTitle }}</h2>
      <div class="form-group">
        <label for="pat-nome">Nome completo</label>
        <input
          id="pat-nome"
          v-model="form.nome"
          required
          minlength="3"
          maxlength="200"
          autocomplete="name"
        />
        <span v-if="fieldErrors.nome" class="error">{{ fieldErrors.nome }}</span>
        <small class="hint">Apenas letras e espaços (3–200 caracteres).</small>
      </div>
      <div class="form-group">
        <label for="pat-cpf">CPF</label>
        <input
          id="pat-cpf"
          v-model="form.cpf"
          required
          maxlength="14"
          inputmode="numeric"
          placeholder="000.000.000-00"
          autocomplete="off"
        />
        <span v-if="fieldErrors.cpf" class="error">{{ fieldErrors.cpf }}</span>
        <small class="hint">11 dígitos, com validação de dígitos verificadores.</small>
      </div>
      <div class="form-group">
        <label for="pat-nasc">Data de nascimento</label>
        <input
          id="pat-nasc"
          v-model="form.data_nascimento"
          type="date"
          required
          :max="todayIso"
        />
        <span v-if="fieldErrors.data_nascimento" class="error">{{
          fieldErrors.data_nascimento
        }}</span>
        <small class="hint">Formato AAAA-MM-DD. Não pode ser futura nem idade &gt; 120 anos.</small>
      </div>

      <div class="form-group">
        <label for="pat-files">Documentos de apoio</label>
        <input
          id="pat-files"
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

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Salvando…' : isEditing ? 'Salvar alterações' : 'Cadastrar' }}
        </button>
        <button
          v-if="isEditing"
          type="button"
          class="btn btn-secondary"
          :disabled="loading"
          @click="resetForm"
        >
          Cancelar
        </button>
      </div>
    </form>

    <div v-if="isEditing" class="card patient-files-card">
      <h2>Documentos do paciente</h2>
      <p v-if="editingPatient" class="files-subtitle">{{ editingPatient.nome }}</p>

      <div v-if="!patientDocuments.length" class="empty-state">
        Este paciente ainda não possui documentos cadastrados.
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Arquivo</th>
              <th>Validação IA</th>
              <th>Tipo</th>
              <th>Tamanho</th>
              <th>Enviado em</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in patientDocuments" :key="doc.id">
              <td class="file-name">{{ doc.nome_arquivo }}</td>
              <td>
                <FileAiAuditTag :file="doc" />
                <span v-if="doc.ai_score == null" class="muted">—</span>
              </td>
              <td>{{ doc.content_type }}</td>
              <td>{{ formatFileSize(doc.size_bytes) }}</td>
              <td>{{ formatDateTime(doc.created_at) }}</td>
              <td class="actions-cell">
                <button
                  type="button"
                  class="btn btn-ghost btn-sm"
                  :disabled="downloadingFileId === doc.id || deletingFileId === doc.id"
                  @click="handleDownload(doc)"
                >
                  {{ downloadingFileId === doc.id ? 'Baixando…' : 'Baixar' }}
                </button>
                <button
                  type="button"
                  class="btn btn-danger btn-sm"
                  :disabled="deletingFileId === doc.id || downloadingFileId === doc.id"
                  @click="handleDeleteFile(doc)"
                >
                  {{ deletingFileId === doc.id ? 'Excluindo…' : 'Excluir' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>

    <div class="card" style="margin-top: 1.25rem">
      <h2>Meus pacientes</h2>
      <div v-if="loading && !patients.length" class="empty-state">Carregando…</div>
      <div v-else-if="!patients.length" class="empty-state">Nenhum paciente cadastrado.</div>
      <template v-else>
        <div class="list-filters">
          <div class="form-group filter-cpf">
            <label for="pat-cpf-filter">Filtrar por CPF</label>
            <input
              id="pat-cpf-filter"
              v-model="cpfFilter"
              type="search"
              inputmode="numeric"
              placeholder="Digite parte do CPF (somente números)"
              autocomplete="off"
            />
          </div>
          <button
            v-if="cpfFilter"
            type="button"
            class="btn btn-secondary btn-sm"
            @click="cpfFilter = ''"
          >
            Limpar filtro
          </button>
        </div>
        <div v-if="!filteredPatients.length" class="empty-state">
          Nenhum paciente encontrado para este CPF.
        </div>
        <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>CPF</th>
              <th>Nascimento</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="p in filteredPatients"
              :key="p.id"
              :class="{ 'row-editing': editingId === p.id }"
            >
              <td>{{ p.nome }}</td>
              <td><code>{{ formatCpfDisplay(p.cpf) }}</code></td>
              <td>{{ formatDate(p.data_nascimento) }}</td>
              <td class="actions-cell">
                <button
                  type="button"
                  class="btn btn-ghost btn-sm"
                  :disabled="loading"
                  @click="startEdit(p)"
                >
                  Editar
                </button>
                <button
                  type="button"
                  class="btn btn-danger btn-sm"
                  :disabled="loading"
                  @click="removePatient(p)"
                >
                  Excluir
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.patient-layout {
  display: block;
}
.patient-layout--edit {
  display: grid;
  gap: 1.25rem;
  align-items: start;
}
@media (min-width: 900px) {
  .patient-layout--edit {
    grid-template-columns: 1fr 1fr;
  }
}
.patient-form {
  max-width: 520px;
}
.patient-layout--edit .patient-form {
  max-width: none;
}
.patient-files-card {
  min-height: 200px;
}
.files-subtitle {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin: -0.25rem 0 1rem;
}
.file-name {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hint {
  color: var(--color-muted);
  font-size: 0.75rem;
}
.form-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.actions-cell {
  white-space: nowrap;
}
.btn-sm {
  padding: 0.35rem 0.65rem;
  font-size: 0.85rem;
}
.btn-danger {
  background: var(--color-danger);
  color: #fff;
  border: none;
}
.btn-danger:hover:not(:disabled) {
  opacity: 0.9;
}
.row-editing {
  background: #e8f4f8;
}
code {
  font-size: 0.85rem;
}
.file-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0;
  font-size: 0.85rem;
}
.file-list li {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--color-border);
}
.btn-link {
  background: none;
  border: none;
  color: var(--color-danger);
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0;
}
.list-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.filter-cpf {
  flex: 1;
  min-width: 200px;
  max-width: 320px;
  margin-bottom: 0;
}
</style>
