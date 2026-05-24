import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { USER_ROLES } from '@/constants'
import { getAccessToken } from '@/utils/authStorage'

const routes = [
  {
    path: '/',
    redirect: () => {
      return getAccessToken() ? '/dashboard' : '/login'
    },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/verify',
    name: 'verify',
    component: () => import('@/views/VerifyView.vue'),
    meta: { guest: true },
  },
  {
    path: '/forbidden',
    name: 'forbidden',
    component: () => import('@/views/ForbiddenView.vue'),
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/patients',
    name: 'patients',
    component: () => import('@/views/PatientsView.vue'),
    meta: {
      requiresAuth: true,
      roles: [USER_ROLES.DOCTOR_APS, USER_ROLES.DOCTOR_SPECIALIST],
    },
  },
  {
    path: '/teleconsultations/new',
    name: 'teleconsultation-new',
    component: () => import('@/views/TeleconsultationFormView.vue'),
    meta: { requiresAuth: true, roles: [USER_ROLES.DOCTOR_APS] },
  },
  {
    path: '/teleconsultations/:id',
    name: 'teleconsultation-detail',
    component: () => import('@/views/TeleconsultationDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/pareceres/new',
    name: 'parecer-new',
    component: () => import('@/views/ParecerFormView.vue'),
    meta: { requiresAuth: true, roles: [USER_ROLES.DOCTOR_SPECIALIST] },
  },
  {
    path: '/admin/institutions',
    name: 'admin-institutions',
    component: () => import('@/views/AdminInstitutionsView.vue'),
    meta: { requiresAuth: true, roles: [USER_ROLES.GLOBAL_ADMIN] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  const token = getAccessToken()

  if (to.meta.guest && token && auth.user) {
    return '/dashboard'
  }

  if (to.meta.requiresAuth) {
    if (!token) return '/login'
    if (!auth.user) {
      const me = await auth.fetchMe()
      if (!me) return '/login'
    }
    if (to.meta.roles && !auth.hasRole(to.meta.roles)) {
      return '/forbidden'
    }
  }

  return true
})

export default router
