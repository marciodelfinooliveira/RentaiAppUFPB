import axios from 'axios'
import { API_BASE_URL } from '@/env'
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from '@/utils/authStorage'

const baseURL = API_BASE_URL

export const api = axios.create({
  baseURL,
  headers: { Accept: 'application/json' },
})

let isRefreshing = false
let refreshQueue = []

function processQueue(err, token = null) {
  refreshQueue.forEach((p) => (err ? p.reject(err) : p.resolve(token)))
  refreshQueue = []
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    const refresh = getRefreshToken()
    if (!refresh) return Promise.reject(error)

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject })
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      })
    }

    original._retry = true
    isRefreshing = true

    try {
      const { data } = await axios.post(
        `${baseURL}/users/new-access`,
        { refresh_token: refresh },
        { headers: { Accept: 'application/json' } }
      )
      setTokens(data.access_token, data.refresh_token)
      processQueue(null, data.access_token)
      original.headers.Authorization = `Bearer ${data.access_token}`
      return api(original)
    } catch (refreshError) {
      processQueue(refreshError, null)
      clearTokens()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export function wsNotificationsUrl(userId) {
  const id = encodeURIComponent(String(userId))
  const base = API_BASE_URL.replace(/\/$/, '')

  if (/^https:\/\//i.test(base)) {
    return `${base.replace(/^https:\/\//i, 'wss://')}/notifications/ws/${id}`
  }

  if (/^http:\/\//i.test(base)) {
    return `${base.replace(/^http:\/\//i, 'ws://')}/notifications/ws/${id}`
  }

  if (typeof window !== 'undefined') {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const path = base.startsWith('/') ? base : `/${base}`
    return `${proto}//${window.location.host}${path}/notifications/ws/${id}`
  }

  return `${base}/notifications/ws/${id}`
}
