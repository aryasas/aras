import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
})

// Request interceptor untuk menyematkan JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aras_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor untuk handle error auth
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('aras_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
