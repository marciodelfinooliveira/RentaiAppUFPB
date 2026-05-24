import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { usersApi } from '@/api'
import { USER_ROLES } from '@/constants'
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  hasAccessToken,
} from '@/utils/authStorage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)

  const accessToken = computed(() => getAccessToken())
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAPS = computed(() => user.value?.role === USER_ROLES.DOCTOR_APS)
  const isSpecialist = computed(
    () => user.value?.role === USER_ROLES.DOCTOR_SPECIALIST
  )
  const isAdmin = computed(() => user.value?.role === USER_ROLES.GLOBAL_ADMIN)
  const isDoctor = computed(
    () =>
      user.value?.role === USER_ROLES.DOCTOR_APS ||
      user.value?.role === USER_ROLES.DOCTOR_SPECIALIST
  )

  function clearSession() {
    user.value = null
    clearTokens()
  }

  async function fetchMe() {
    const token = getAccessToken()
    if (!token) {
      user.value = null
      return null
    }
    loading.value = true
    try {
      const { data } = await usersApi.me()
      user.value = data
      return data
    } catch {
      clearSession()
      return null
    } finally {
      loading.value = false
    }
  }

  async function login(email, password) {
    const { data } = await usersApi.login(email, password)
    setTokens(data.access_token, data.refresh_token)
    return fetchMe()
  }

  async function logout() {
    const refresh = getRefreshToken()
    try {
      if (refresh) await usersApi.logout(refresh)
    } catch {}
    clearSession()
  }

  function hasRole(roles) {
    if (!roles?.length) return true
    return roles.includes(user.value?.role)
  }

  function setUser(data) {
    user.value = data
  }

  return {
    user,
    loading,
    accessToken,
    isAuthenticated,
    isAPS,
    isSpecialist,
    isAdmin,
    isDoctor,
    clearSession,
    fetchMe,
    login,
    logout,
    hasRole,
    setUser,
    hasAccessToken,
  }
})
