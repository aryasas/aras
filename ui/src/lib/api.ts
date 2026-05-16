import axios from 'axios'

const DEV_MULTI_TENANT = import.meta.env.VITE_DEV_MULTI_TENANT === 'true'
const TENANT_STORAGE_KEY = 'aras_tenant_id'

interface ApiEnvelope<T = unknown> {
  success: boolean
  data: T
  message?: string | null
  error?: string | null
  detail?: string | null
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
        // Prefer `error` from envelope, then `message`, then fallback
        const errorMessage = response.data.error || response.data.detail || response.data.message || 'Request failed';

        // Ensure the error object passed to consumers has the right structure
        const errorData = {
          ...response.data, // Preserve original data
          message: errorMessage,
          detail: response.data.detail || errorMessage, // Ensure detail is also set for consistency
          error: response.data.error || errorMessage, // Ensure error is also set
        };

        const error = new Error(errorMessage) as Error & { response?: typeof response };
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
        errorMessage = d.error || d.detail || d.message || errorMessage;
      } else if (typeof d === 'object') {
        // For non-envelope responses (e.g., FastAPI validation errors)
        errorMessage = d.error || d.detail || d.message || errorMessage;
      } else if (typeof d === 'string') {
        errorMessage = d;
      }

      // Ensure error.message reflects the primary error message
      error.message = errorMessage;

      // Normalize error.response.data to contain 'error', 'detail', and 'message'
      // This makes it consistent for consumers
      error.response.data = {
        ...d, // Preserve original data
        error: d.error || errorMessage,
        detail: d.detail || errorMessage,
        message: d.message || errorMessage,
      };
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('aras_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api
