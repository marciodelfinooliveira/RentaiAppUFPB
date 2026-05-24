<script setup>
import { watch, onMounted, provide } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import { useRoute } from 'vue-router'
import { getRealtimeNotifications } from '@/composables/realtimeNotifications'
import { hasAccessToken } from '@/utils/authStorage'

const auth = useAuthStore()
const route = useRoute()
const notifications = getRealtimeNotifications()

provide('wsNotifications', notifications)

watch(
  () => auth.user?.id,
  (id, prevId) => {
    if (!id) {
      notifications.disconnect()
      return
    }

    notifications.setUserId(id)

    if (id === prevId && notifications.connected.value) {
      return
    }

    if (prevId && prevId !== id) {
      notifications.disconnect()
    }

    notifications.connect()
  },
  { immediate: true }
)

onMounted(() => {
  if (hasAccessToken()) {
    auth.fetchMe()
  }
})
</script>

<template>
  <AppLayout v-if="route.meta.requiresAuth && auth.user">
    <router-view />
  </AppLayout>
  <router-view v-else />
</template>
