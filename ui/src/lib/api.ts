import axios from 'axios'
import { cleanResourcePath } from './resourceUtils'

const DEV_MULTI_TENANT = import.meta.env.VITE_DEV_MULTI_TENANT === 'true'
const TENANT_STORAGE_KEY = 'aras_tenant_id'
const TOKEN_STORAGE_KEY = 'aras_token'

function getAuthToken() {
  const sessionToken = sessionStorage.getItem(TOKEN_STORAGE_KEY)
  if (sessionToken) return sessionToken

  const legacyToken = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (legacyToken) {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, legacyToken)
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  }
  return legacyToken
}

function clearAuthToken() {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

interface ApiEnvelope<T = unknown> {
  success: boolean
  data: T
  message?: string | null
  error?: string | { message?: string; detail?: unknown } | null
  detail?: string | null
}

function getEnvelopeErrorMessage(value: ApiEnvelope | Record<string, any>): string {
  const error = value.error
  if (typeof error === 'string') return error
  if (error && typeof error === 'object' && typeof error.message === 'string') return error.message
  if (typeof value.detail === 'string') return value.detail
  if (typeof value.message === 'string') return value.message
  return 'Request failed'
}

function getEnvelopeErrorCode(value: ApiEnvelope | Record<string, any>): string | undefined {
  const error = value.error
  if (error && typeof error === 'object' && typeof (error as any).code === 'string') return (error as any).code
  if (typeof (value as any).code === 'string') return (value as any).code
  return undefined
}

function isApiEnvelope(value: unknown): value is ApiEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'success' in value &&
    typeof (value as { success?: unknown }).success === 'boolean'
  )
}



const api = axios.create({
  baseURL: '/api/v1',
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  if (config.url && !/^https?:\/\//i.test(config.url)) {
    const [path, query] = config.url.split('?')
    const leadingSlash = path.startsWith('/') ? '/' : ''
    config.url = `${leadingSlash}${cleanResourcePath(path)}${query ? `?${query}` : ''}`
  }

  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  const orgId = localStorage.getItem('org_id')
  if (orgId && orgId !== '-1') {
    config.headers['X-Org-ID'] = orgId
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
        // Prefer `error` from envelope, then `message`, then fallback
        const errorMessage = getEnvelopeErrorMessage(response.data);

        // Ensure the error object passed to consumers has the right structure
        const errorData = {
          ...response.data, // Preserve original data
          message: errorMessage,
          detail: response.data.detail || errorMessage, // Ensure detail is also set for consistency
          error: response.data.error || errorMessage, // Ensure error is also set
        };

        const error = new Error(errorMessage) as Error & { response?: typeof response; code?: string };
        error.code = getEnvelopeErrorCode(response.data);
        error.response = { ...response, data: errorData }; // Attach enriched error data to response
        return Promise.reject(error);
      }
      response.data = response.data.data; // Extract actual data for successful responses
    }
    return response;
  },
  (error) => {
    if (error.response?.data) {
      const d = error.response.data;
      let errorMessage = 'Request failed';

      if (isApiEnvelope(d)) {
        errorMessage = getEnvelopeErrorMessage(d);
      } else if (typeof d === 'object') {
        // For non-envelope responses (e.g., FastAPI validation errors)
        errorMessage = getEnvelopeErrorMessage(d);
      } else if (typeof d === 'string') {
        errorMessage = d;
      }

      // Ensure error.message reflects the primary error message
      error.message = errorMessage;
      error.code = getEnvelopeErrorCode(d);

      // Normalize error.response.data to contain 'error', 'detail', and 'message'
      // This makes it consistent for consumers
      error.response.data = {
        ...d, // Preserve original data
        error: d.error || errorMessage,
        detail: d.detail || errorMessage,
        message: d.message || errorMessage,
        code: d.code || error.code,
      };
    }
    if (error.response?.status === 401) {
      clearAuthToken();
      const path = window.location.pathname;
      const publicPaths = ['/login', '/welcome', '/signup', '/portal', '/portal/setup', '/forgot-password', '/reset-password', '/contact'];
      const isPublic = publicPaths.some((p) => path === p || path.startsWith(p + '/')) || path.startsWith('/p/');
      if (!isPublic) {
        window.location.href = '/login';
      }
    } else if (error.response?.status === 402) {
      const path = window.location.pathname;
      if (!path.startsWith('/portal')) {
        window.location.href = '/portal?tab=billing';
      }
    }
    return Promise.reject(error);
  }
);

export default api
