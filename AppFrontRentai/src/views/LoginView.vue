<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { parseApiError } from '@/utils/errors'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
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
      <h1>V4H — Entrar</h1>
      <p class="subtitle">Plataforma de teleconsultoria ReNTAI</p>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form @submit.prevent="submit">
        <div class="form-group">
          <label for="email">E-mail</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <label for="password">Senha</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
          />
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%" :disabled="loading">
          {{ loading ? 'Entrando…' : 'Entrar' }}
        </button>
      </form>

      <p class="footer-links">
        <router-link to="/register">Criar conta</router-link>
        ·
        <router-link to="/verify">Verificar e-mail</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-muted);
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}
.footer-links {
  margin-top: 1.25rem;
  text-align: center;
  font-size: 0.875rem;
}
</style>
