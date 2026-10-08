import axios from 'axios'
import { auth } from '../stores/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  if (auth.token && !config.skipAuth) {
    config.headers.Authorization = `Token ${auth.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.skipAuth && auth.isAuthenticated) {
      auth.clear()
      window.location.assign('/login')
    }
    return Promise.reject(error)
  }
)

const open = { skipAuth: true }

export const authApi = {
  login: (payload) => api.post('/api/login/', payload, open),
  register: (payload) => api.post('/api/register/', payload, open),
  resendVerification: (email) => api.post('/api/resend-verification/', { email }, open),
  verifyEmail: (uid, token) => api.post('/api/users/verify-email/', { uid, token }, open)
}

export const tasksApi = {
  list: (params) => api.get('/api/tasks/', { params }),
  create: (payload) => api.post('/api/tasks/', payload),
  update: (id, payload) => api.patch(`/api/tasks/${id}/`, payload),
  remove: (id) => api.delete(`/api/tasks/${id}/`)
}

export const usersApi = {
  me: () => api.get('/api/users/me/'),
  updateMe: (payload) => api.patch('/api/users/me/', payload),
  settings: () => api.get('/api/users/settings/'),
  updateSettings: (payload) => api.patch('/api/users/settings/', payload),
  changePassword: (payload) => api.post('/api/users/change-password/', payload)
}

export function extractError(error, fallback = 'Something went wrong. Please try again.') {
  if (!error?.response) return 'Cannot reach the server.'
  if (error.response.status === 429) return 'Too many requests. Please wait a minute and try again.'
  const data = error.response.data
  if (typeof data === 'string') return data.length < 300 && !data.includes('<') ? data : fallback
  if (Array.isArray(data)) return data.join(' ')
  if (data && typeof data === 'object') {
    const direct = data.Error || data.error || data.detail || data.message
    if (direct) return Array.isArray(direct) ? direct.join(' ') : String(direct)
    const parts = Object.entries(data).map(([key, value]) => {
      const text = Array.isArray(value) ? value.join(' ') : String(value)
      return key === 'non_field_errors' ? text : `${key}: ${text}`
    })
    if (parts.length) return parts.join('\n')
  }
  return fallback
}

export default api
