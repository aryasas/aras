import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import { Lock, User, AlertCircle } from 'lucide-react'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const setToken = useAuthStore((state) => state.setToken)
  const setUser = useAuthStore((state) => state.setUser)
  const setOrganizations = useAuthStore((state) => state.setOrganizations)
  const setActiveOrg = useAuthStore((state) => state.setActiveOrg)
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await api.post('/auth/token', formData)
      setToken(response.data.access_token)

      const me = await api.get('/auth/me')
      const organizations = me.data.organizations || []
      const defaultOrgId = me.data.default_org_id || (organizations.length > 0 ? organizations[0].id : null)
      setUser(me.data)
      setOrganizations(organizations)
      setActiveOrg(defaultOrgId)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-xl shadow-slate-200 border border-slate-100 overflow-hidden">
        <div className="p-8 pb-0 flex flex-col items-center">
          <div className="relative mb-6 flex h-16 w-16 items-center justify-center rounded-[var(--aras-radius)] border border-[color-mix(in_srgb,var(--aras-accent)_34%,transparent)] bg-[var(--aras-accent)] shadow-lg shadow-indigo-200">
            <span className="font-serif text-[46px] font-black leading-none text-white">A</span>
            <span className="absolute bottom-[18px] left-[23px] h-[4px] w-[20px] rounded-full bg-white/90" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Welcome Back</h1>
          <p className="text-slate-500 mt-2">Sign in to your Aras account</p>
        </div>

        <form onSubmit={handleLogin} className="p-8 space-y-6">
          {error && (
            <div className="bg-rose-50 border border-rose-100 text-rose-600 px-4 py-3 rounded-xl flex items-center gap-3 text-sm animate-shake">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 ml-1">Username</label>
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                placeholder="Enter your username"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center ml-1">
              <label className="text-sm font-semibold text-slate-700">Password</label>
              <Link to="/forgot-password" className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button 
            type="submit"
            disabled={loading}
            className={`w-full py-4 bg-indigo-600 text-white rounded-2xl font-bold text-lg shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all transform hover:-translate-y-1 active:translate-y-0
              ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div className="px-8 pb-8 text-center">
          <p className="text-slate-400 text-sm">
            Contact your administrator for credentials.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
