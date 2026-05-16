import axios from 'axios'

const DEV_MULTI_TENANT = import.meta.env.VITE_DEV_MULTI_TENANT === 'true'
const TENANT_STORAGE_KEY = 'aras_tenant_id'

interface ApiEnvelope<T = unknown> {
  success: boolean
  data: T
  message?: string | null
  error?: string | null
}

function isApiEnvelope(value: unknown): value is ApiEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'success' in value &&
    typeof (value as { success?: unknown }).success === 'boolean'
  )
}

function responseMessage(data: { message?: unknown; error?: unknown; detail?: unknown }) {
  if (typeof data.message === 'string' && data.message) return data.message
  if (typeof data.error === 'string' && data.error) return data.error
  if (typeof data.detail === 'string' && data.detail) return data.detail
  return 'Request failed'
}

const api = axios.create({
  baseURL: '/api/v1',
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aras_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  const companyId = localStorage.getItem('aras_company_id')
  if (companyId) {
    config.headers['X-Company-ID'] = companyId
  }

  if (DEV_MULTI_TENANT) {
    const tenantId = localStorage.getItem(TENANT_STORAGE_KEY)
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId
    }
  }

  return config
})

// Normalize error responses and handle 401
api.interceptors.response.use(
  (response) => {
    if (isApiEnvelope(response.data)) {
      if (!response.data.success) {
        const message = responseMessage(response.data)
        response.data = {
          detail: message,
          error: response.data.error,
          message,
        }

        const error = new Error(message) as Error & { response?: typeof response }
        error.response = response
        return Promise.reject(error)
      }

      response.data = response.data.data
    }

    return response
  },
  (error) => {
    if (error.response?.data) {
      const d = error.response.data
      if (isApiEnvelope(d)) {
        const message = responseMessage(d)
        error.message = message
        error.response.data = {
          detail: message,
          error: d.error,
          message,
        }
      } else if (typeof d === 'object') {
        // Backend custom handler uses {message:...}; FastAPI 422 uses {detail:...}
        // Normalize so all frontend code can read .detail consistently
        if (d.message && !d.detail) d.detail = d.message
        if (d.detail && !d.message && typeof d.detail === 'string') d.message = d.detail
      }
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('aras_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
