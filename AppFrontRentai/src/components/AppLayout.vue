<script setup>
import { computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ROLE_LABELS } from '@/constants'

const auth = useAuthStore()
const router = useRouter()

const notifications = inject('wsNotifications', null)

const roleLabel = computed(
  () => ROLE_LABELS[auth.user?.role] || auth.user?.role
)

const connected = computed(() => notifications?.connected?.value ?? false)
const reconnecting = computed(() => notifications?.reconnecting?.value ?? false)
const lastMessage = computed(() => notifications?.lastMessage?.value ?? '')

async function handleLogout() {
  notifications?.disconnect()
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <header class="layout-header">
      <div class="brand">
        <span class="brand-logo">V4H</span>
        <span class="brand-sub">Teleconsultoria ReNTAI</span>
      </div>
      <nav class="layout-nav">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link
          v-if="auth.isAPS || auth.isSpecialist"
          to="/patients"
        >
          Pacientes
        </router-link>
        <router-link v-if="auth.isAdmin" to="/admin/institutions">
          Instituições
        </router-link>
        <router-link to="/profile">Meu perfil</router-link>
      </nav>
      <div class="layout-user">
        <span
          v-if="lastMessage"
          class="notif-dot"
          :title="lastMessage"
        />
        <span
          class="ws-status"
          :class="{
            online: connected,
            reconnecting: reconnecting && !connected,
          }"
          :title="
            connected
              ? 'Notificações em tempo real (WebSocket)'
              : reconnecting
                ? 'Reconectando WebSocket…'
                : 'WebSocket desconectado — tentando reconectar'
          "
        />
        <span>{{ auth.user?.nome }}</span>
        <span class="role-tag">{{ roleLabel }}</span>
        <button type="button" class="btn btn-ghost" @click="handleLogout">
          Sair
        </button>
      </div>
    </header>
    <main class="layout-main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow);
}

.brand {
  display: flex;
  flex-direction: column;
  margin-right: auto;
}

.brand-logo {
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--color-primary);
}

.brand-sub {
  font-size: 0.7rem;
  color: var(--color-muted);
}

.layout-nav {
  display: flex;
  gap: 1rem;
}

.layout-nav a {
  text-decoration: none;
  color: var(--color-muted);
  font-weight: 500;
  font-size: 0.9rem;
}

.layout-nav a.router-link-active {
  color: var(--color-primary);
}

.layout-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.role-tag {
  background: var(--color-bg);
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  color: var(--color-muted);
}

.layout-main {
  flex: 1;
  padding: 1.5rem;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}

.ws-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
}

.ws-status.online {
  background: var(--color-success);
}

.ws-status.reconnecting {
  background: #e6a700;
  animation: pulse 1s ease infinite;
}

.notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-accent);
  animation: pulse 1s ease infinite;
}

@keyframes pulse {
  50% { opacity: 0.4; }
}
</style>
