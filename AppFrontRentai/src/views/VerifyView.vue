<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usersApi } from '@/api'
import { parseApiError } from '@/utils/errors'
import { validateVerifyCode } from '@/utils/userValidation'

const route = useRoute()
const router = useRouter()

const email = ref('')
const code = ref('')
const error = ref('')
const fieldErrors = ref({})
const success = ref('')
const loading = ref(false)

onMounted(() => {
  if (route.query.email) email.value = String(route.query.email)
})

async function submit() {
  error.value = ''
  fieldErrors.value = {}
  success.value = ''

  const codeErr = validateVerifyCode(code.value)
  if (codeErr) {
    fieldErrors.value.code = codeErr
    return
  }

  loading.value = true
  try {
    const { data } = await usersApi.verify({
      email: email.value,
      code: code.value,
    })
    success.value = data.message || 'Conta ativada!'
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>Verificar e-mail</h1>
      <p class="subtitle">
        Em desenvolvimento, confira o código no
        <a href="http://localhost:8025" target="_blank" rel="noopener">MailHog</a>.
      </p>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <form @submit.prevent="submit">
        <div class="form-group">
          <label for="verify-email">E-mail</label>
          <input id="verify-email" v-model="email" type="email" required />
        </div>
        <div class="form-group">
          <label for="verify-code">Código (6 dígitos)</label>
          <input
            id="verify-code"
            v-model="code"
            maxlength="6"
            minlength="6"
            required
            inputmode="numeric"
            pattern="\d{6}"
            autocomplete="one-time-code"
          />
          <span v-if="fieldErrors.code" class="error">{{ fieldErrors.code }}</span>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%" :disabled="loading">
          {{ loading ? 'Verificando…' : 'Ativar conta' }}
        </button>
      </form>

      <p class="footer-links">
        <router-link to="/login">Ir para login</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.subtitle { color: var(--color-muted); margin-bottom: 1rem; font-size: 0.9rem; }
.footer-links { margin-top: 1rem; text-align: center; font-size: 0.875rem; }
</style>
