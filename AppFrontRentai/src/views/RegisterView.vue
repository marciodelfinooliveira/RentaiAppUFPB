<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usersApi, institutionsApi } from '@/api'
import { USER_ROLES, SPECIALTIES } from '@/constants'
import { parseApiError, fieldErrorsFromApi } from '@/utils/errors'
import { validateUserCreateForm } from '@/utils/userValidation'

const router = useRouter()

const form = ref({
  nome: '',
  email: '',
  password: '',
  role: USER_ROLES.DOCTOR_APS,
  specialty: '',
  institution_id: '',
})
const institutions = ref([])
const error = ref('')
const fieldErrors = ref({})
const success = ref('')
const loading = ref(false)

watch(
  () => form.value.role,
  (role) => {
    if (role === USER_ROLES.DOCTOR_SPECIALIST) {
      if (!SPECIALTIES.includes(form.value.specialty)) {
        form.value.specialty = SPECIALTIES[0]
      }
    } else {
      form.value.specialty = ''
    }
  }
)

onMounted(async () => {
  try {
    const { data } = await institutionsApi.list()
    institutions.value = data
    if (data.length) form.value.institution_id = data[0].id
  } catch (e) {
    error.value = parseApiError(e)
  }
})

function buildPayload() {
  const isSpecialist = form.value.role === USER_ROLES.DOCTOR_SPECIALIST
  return {
    nome: form.value.nome.trim(),
    email: form.value.email.trim(),
    password: form.value.password,
    role: form.value.role,
    institution_id: form.value.institution_id,
    specialty: isSpecialist ? form.value.specialty : null,
  }
}

async function submit() {
  error.value = ''
  fieldErrors.value = {}
  success.value = ''

  fieldErrors.value = validateUserCreateForm({
    nome: form.value.nome,
    password: form.value.password,
    role: form.value.role,
    specialty: form.value.specialty || null,
    institutionId: form.value.institution_id,
  })
  if (Object.keys(fieldErrors.value).length) return

  loading.value = true
  try {
    const { data } = await usersApi.register(buildPayload())
    success.value = data.message || 'Registro iniciado. Verifique seu e-mail.'
    setTimeout(
      () => router.push({ path: '/verify', query: { email: form.value.email } }),
      2000
    )
  } catch (e) {
    error.value = parseApiError(e)
    Object.assign(fieldErrors.value, fieldErrorsFromApi(e))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card" style="max-width: 480px">
      <h1>Cadastro de médico</h1>
      <p class="subtitle">Solicitante (APS) ou Especialista</p>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <form @submit.prevent="submit">
        <div class="form-group">
          <label for="reg-nome">Nome completo</label>
          <input
            id="reg-nome"
            v-model="form.nome"
            required
            minlength="5"
            maxlength="100"
            autocomplete="name"
          />
          <span v-if="fieldErrors.nome" class="error">{{ fieldErrors.nome }}</span>
          <small class="hint">Apenas letras e espaços (mín. 5 caracteres).</small>
        </div>

        <div class="form-group">
          <label for="reg-email">E-mail</label>
          <input
            id="reg-email"
            v-model="form.email"
            type="email"
            required
            autocomplete="email"
          />
          <span v-if="fieldErrors.email" class="error">{{ fieldErrors.email }}</span>
        </div>

        <div class="form-group">
          <label for="reg-role">Perfil</label>
          <select id="reg-role" v-model="form.role">
            <option :value="USER_ROLES.DOCTOR_APS">Solicitante (APS)</option>
            <option :value="USER_ROLES.DOCTOR_SPECIALIST">Especialista</option>
          </select>
        </div>

        <div
          v-if="form.role === USER_ROLES.DOCTOR_SPECIALIST"
          class="form-group"
        >
          <label for="reg-specialty">Especialidade</label>
          <select id="reg-specialty" v-model="form.specialty" required>
            <option v-for="s in SPECIALTIES" :key="s" :value="s">{{ s }}</option>
          </select>
          <span v-if="fieldErrors.specialty" class="error">{{
            fieldErrors.specialty
          }}</span>
        </div>

        <div class="form-group">
          <label for="reg-institution">Instituição</label>
          <select
            id="reg-institution"
            v-model="form.institution_id"
            required
            :disabled="!institutions.length"
          >
            <option v-for="inst in institutions" :key="inst.id" :value="inst.id">
              {{ inst.nome }}
            </option>
          </select>
          <span v-if="fieldErrors.institution_id" class="error">{{
            fieldErrors.institution_id
          }}</span>
          <small v-if="!institutions.length" class="hint">
            Nenhuma instituição disponível. Peça ao administrador o cadastro.
          </small>
        </div>

        <div class="form-group">
          <label for="reg-password">Senha</label>
          <input
            id="reg-password"
            v-model="form.password"
            type="password"
            required
            minlength="8"
            maxlength="128"
            autocomplete="new-password"
          />
          <span v-if="fieldErrors.password" class="error">{{
            fieldErrors.password
          }}</span>
          <small class="hint"
            >8–128 caracteres, com maiúscula, número e caractere especial
            (!@#$%^&*…).</small
          >
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          style="width: 100%"
          :disabled="loading || !institutions.length"
        >
          {{ loading ? 'Cadastrando…' : 'Cadastrar' }}
        </button>
      </form>

      <p class="footer-links">
        <router-link to="/login">Já tenho conta</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-muted);
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.hint {
  color: var(--color-muted);
  font-size: 0.75rem;
}
.footer-links {
  margin-top: 1rem;
  text-align: center;
  font-size: 0.875rem;
}
</style>
