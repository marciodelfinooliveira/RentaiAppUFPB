<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersApi, institutionsApi } from '@/api'
import { USER_ROLES, SPECIALTIES, ROLE_LABELS } from '@/constants'
import { parseApiError, fieldErrorsFromApi } from '@/utils/errors'
import { validateUserUpdateForm } from '@/utils/userValidation'

const auth = useAuthStore()

const institutions = ref([])
const error = ref('')
const success = ref('')
const fieldErrors = ref({})
const loading = ref(false)

const form = ref({
  nome: '',
  email: '',
  institution_id: '',
  specialty: '',
  password: '',
})

const role = computed(() => auth.user?.role)
const isDoctor = computed(
  () =>
    role.value === USER_ROLES.DOCTOR_APS ||
    role.value === USER_ROLES.DOCTOR_SPECIALIST
)
const isSpecialist = computed(
  () => role.value === USER_ROLES.DOCTOR_SPECIALIST
)
const roleLabel = computed(() => ROLE_LABELS[role.value] || role.value)

function loadFormFromUser() {
  const u = auth.user
  if (!u) return
  form.value = {
    nome: u.nome || '',
    email: u.email || '',
    institution_id: u.institution_id || '',
    specialty: u.specialty || (isSpecialist.value ? SPECIALTIES[0] : ''),
    password: '',
  }
}

onMounted(async () => {
  if (!auth.user) await auth.fetchMe()
  loadFormFromUser()

  if (isDoctor.value) {
    try {
      const { data } = await institutionsApi.list()
      institutions.value = data
    } catch (e) {
      error.value = parseApiError(e)
    }
  }
})

function buildPayload() {
  const u = auth.user
  if (!u) return {}

  const payload = {}
  const nome = form.value.nome.trim()
  const email = form.value.email.trim()

  if (nome !== u.nome) payload.nome = nome
  if (email !== u.email) payload.email = email
  if (form.value.password) payload.password = form.value.password

  if (isDoctor.value) {
    const instId = form.value.institution_id || null
    if (instId !== u.institution_id) payload.institution_id = instId
  }

  if (isSpecialist.value && form.value.specialty !== u.specialty) {
    payload.specialty = form.value.specialty
  }

  return payload
}

async function submit() {
  error.value = ''
  success.value = ''
  fieldErrors.value = validateUserUpdateForm(
    {
      nome: form.value.nome,
      password: form.value.password,
      specialty: isSpecialist.value ? form.value.specialty : null,
      institution_id: isDoctor.value ? form.value.institution_id : null,
    },
    role.value
  )
  if (Object.keys(fieldErrors.value).length) return

  const payload = buildPayload()
  if (!Object.keys(payload).length) {
    success.value = 'Nenhuma alteração para salvar.'
    return
  }

  loading.value = true
  try {
    const { data } = await usersApi.updateMe(payload)
    auth.setUser(data)
    loadFormFromUser()
    form.value.password = ''
    success.value = 'Dados atualizados com sucesso.'
  } catch (e) {
    const apiFields = fieldErrorsFromApi(e)
    if (Object.keys(apiFields).length) {
      Object.assign(fieldErrors.value, apiFields)
      error.value = ''
    } else {
      error.value = parseApiError(e)
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Meu perfil</h1>
        <p class="muted">Perfil: {{ roleLabel }}</p>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <form class="card profile-form" @submit.prevent="submit">
      <div class="form-group">
        <label for="prof-nome">Nome completo</label>
        <input
          id="prof-nome"
          v-model="form.nome"
          required
          minlength="5"
          maxlength="100"
          autocomplete="name"
        />
        <span v-if="fieldErrors.nome" class="error">{{ fieldErrors.nome }}</span>
      </div>

      <div class="form-group">
        <label for="prof-email">E-mail</label>
        <input
          id="prof-email"
          v-model="form.email"
          type="email"
          required
          autocomplete="email"
        />
        <span v-if="fieldErrors.email" class="error">{{ fieldErrors.email }}</span>
      </div>

      <template v-if="isDoctor">
        <div class="form-group">
          <label for="prof-institution">Instituição</label>
          <select id="prof-institution" v-model="form.institution_id" required>
            <option
              v-for="inst in institutions"
              :key="inst.id"
              :value="inst.id"
            >
              {{ inst.nome }}
            </option>
          </select>
          <span v-if="fieldErrors.institution_id" class="error">{{
            fieldErrors.institution_id
          }}</span>
        </div>

        <div v-if="isSpecialist" class="form-group">
          <label for="prof-specialty">Especialidade</label>
          <select id="prof-specialty" v-model="form.specialty" required>
            <option v-for="s in SPECIALTIES" :key="s" :value="s">{{ s }}</option>
          </select>
          <span v-if="fieldErrors.specialty" class="error">{{
            fieldErrors.specialty
          }}</span>
        </div>
      </template>

      <div class="form-group">
        <label for="prof-password">Nova senha (opcional)</label>
        <input
          id="prof-password"
          v-model="form.password"
          type="password"
          minlength="8"
          maxlength="128"
          autocomplete="new-password"
          placeholder="Deixe em branco para manter a atual"
        />
        <span v-if="fieldErrors.password" class="error">{{
          fieldErrors.password
        }}</span>
        <small class="hint">Maiúscula, número e caractere especial, se alterar.</small>
      </div>

      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Salvando…' : 'Salvar alterações' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.muted {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin: 0;
}
.profile-form {
  max-width: 480px;
}
.hint {
  color: var(--color-muted);
  font-size: 0.75rem;
}
</style>
