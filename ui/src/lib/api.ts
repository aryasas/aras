import axios from 'axios'

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

  return config
})

// Normalize error responses and handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data) {
      const d = error.response.data
      // Backend custom handler uses {message:...}; FastAPI 422 uses {detail:...}
      // Normalize so all frontend code can read .detail consistently
      if (d.message && !d.detail) d.detail = d.message
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
