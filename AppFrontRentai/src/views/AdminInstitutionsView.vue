<script setup>
import { ref, computed, onMounted } from 'vue'
import { institutionsApi } from '@/api'
import { parseApiError, fieldErrorsFrom422 } from '@/utils/errors'
import { formatDateTime } from '@/utils/format'
import {
  cleanCnpj,
  validateCnpj,
  validateInstitutionNome,
  formatCnpjDisplay,
} from '@/utils/cnpj'

const institutions = ref([])
const error = ref('')
const success = ref('')
const loading = ref(false)
const fieldErrors = ref({})

const editingId = ref(null)
const form = ref({ nome: '', cnpj: '' })

const isEditing = computed(() => !!editingId.value)
const formTitle = computed(() =>
  isEditing.value ? 'Editar instituição' : 'Nova instituição'
)

function resetForm() {
  editingId.value = null
  form.value = { nome: '', cnpj: '' }
  fieldErrors.value = {}
}

function startEdit(inst) {
  editingId.value = inst.id
  form.value = {
    nome: inst.nome,
    cnpj: inst.cnpj || '',
  }
  error.value = ''
  success.value = ''
  fieldErrors.value = {}
}

function validateForm() {
  fieldErrors.value = {}
  const nomeErr = validateInstitutionNome(form.value.nome)
  const cnpjErr = validateCnpj(form.value.cnpj)
  if (nomeErr) fieldErrors.value.nome = nomeErr
  if (cnpjErr) fieldErrors.value.cnpj = cnpjErr
  return Object.keys(fieldErrors.value).length === 0
}

function buildPayload() {
  return {
    nome: form.value.nome.trim(),
    cnpj: cleanCnpj(form.value.cnpj),
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await institutionsApi.list()
    institutions.value = data
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loading.value = false
  }
}

async function submit() {
  error.value = ''
  success.value = ''
  if (!validateForm()) return

  loading.value = true
  try {
    const payload = buildPayload()
    if (isEditing.value) {
      await institutionsApi.update(editingId.value, payload)
      success.value = 'Instituição atualizada.'
    } else {
      await institutionsApi.create(payload)
      success.value = 'Instituição criada.'
    }
    resetForm()
    await load()
  } catch (e) {
    error.value = parseApiError(e)
    Object.assign(fieldErrors.value, fieldErrorsFrom422(e))
  } finally {
    loading.value = false
  }
}

async function removeInstitution(inst) {
  const ok = window.confirm(
    `Excluir a instituição "${inst.nome}"? Esta ação não pode ser desfeita.`
  )
  if (!ok) return

  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await institutionsApi.remove(inst.id)
    success.value = 'Instituição excluída.'
    if (editingId.value === inst.id) resetForm()
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
      <h1>Instituições</h1>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="grid-2">
      <form class="card" @submit.prevent="submit">
        <h2>{{ formTitle }}</h2>
        <div class="form-group">
          <label for="inst-nome">Nome</label>
          <input
            id="inst-nome"
            v-model="form.nome"
            required
            minlength="3"
            maxlength="200"
            autocomplete="organization"
          />
          <span v-if="fieldErrors.nome" class="error">{{ fieldErrors.nome }}</span>
        </div>
        <div class="form-group">
          <label for="inst-cnpj">CNPJ</label>
          <input
            id="inst-cnpj"
            v-model="form.cnpj"
            required
            maxlength="18"
            placeholder="00.000.000/0000-00"
            autocomplete="off"
          />
          <span v-if="fieldErrors.cnpj" class="error">{{ fieldErrors.cnpj }}</span>
          <small class="hint">14 caracteres alfanuméricos (único no sistema).</small>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? 'Salvando…' : isEditing ? 'Salvar alterações' : 'Criar' }}
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

      <div class="card">
        <h2>Lista</h2>
        <div v-if="loading && !institutions.length" class="empty-state">
          Carregando…
        </div>
        <div v-else-if="!institutions.length" class="empty-state">
          Nenhuma instituição cadastrada.
        </div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>CNPJ</th>
                <th>Criada em</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="inst in institutions"
                :key="inst.id"
                :class="{ 'row-editing': editingId === inst.id }"
              >
                <td>{{ inst.nome }}</td>
                <td><code>{{ formatCnpjDisplay(inst.cnpj) }}</code></td>
                <td>{{ formatDateTime(inst.created_at) }}</td>
                <td class="actions-cell">
                  <button
                    type="button"
                    class="btn btn-ghost btn-sm"
                    :disabled="loading"
                    @click="startEdit(inst)"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    class="btn btn-danger btn-sm"
                    :disabled="loading"
                    @click="removeInstitution(inst)"
                  >
                    Excluir
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hint {
  color: var(--color-muted);
  font-size: 0.8rem;
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
</style>
