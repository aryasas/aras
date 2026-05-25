import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../lib/api'
import { Lock, Mail, AlertCircle, LogIn } from 'lucide-react'
import { ArasLogo } from '../components/ArasLogo'

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
    } catch (err: unknown) {
      const detail =
        typeof err === 'object' && err !== null && 'response' in err
          ? (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
          : undefined
      setError(typeof detail === 'string' ? detail : 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--app-bg-main)] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] shadow-[var(--shadow-premium)] border border-[var(--app-border)] overflow-hidden">
        <div className="p-8 pb-0 flex flex-col items-center">
          <div className="mb-6">
            <ArasLogo size="lg" />
          </div>
          <h1 className="text-[calc(24px*var(--app-font-scale))] font-extrabold text-[var(--app-text)] tracking-tight">Welcome Back</h1>
          <p className="text-[var(--app-muted)] mt-2 text-[calc(14px*var(--app-font-scale))]">Sign in to your Aras Dashboard</p>
        </div>

        <form onSubmit={handleLogin} className="p-8 space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-500 px-4 py-3 rounded-[var(--app-radius)] flex items-center gap-3 text-sm animate-shake">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-[calc(12px*var(--app-font-scale))] font-bold text-[var(--app-text)] uppercase tracking-wider ml-1">Email / Username</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" size={18} />
              <input 
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full h-[52px] pl-11 pr-4 bg-[var(--app-panel-soft)] border border-[var(--app-border)] rounded-[var(--app-radius)] text-[var(--app-text)] text-[calc(14px*var(--app-font-scale))] focus:bg-[var(--app-panel)] focus:border-[var(--app-accent-strong)] focus:ring-[4px] focus:ring-[var(--app-accent-glow)] transition-all outline-none"
                placeholder="Enter your email"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center ml-1">
              <label className="text-[calc(12px*var(--app-font-scale))] font-bold text-[var(--app-text)] uppercase tracking-wider">Password</label>
              <Link to="/forgot-password" className="text-xs text-[var(--app-primary-action)] hover:text-[var(--app-primary-action-strong)] font-bold">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" size={18} />
              <input 
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-[52px] pl-11 pr-4 bg-[var(--app-panel-soft)] border border-[var(--app-border)] rounded-[var(--app-radius)] text-[var(--app-text)] text-[calc(14px*var(--app-font-scale))] focus:bg-[var(--app-panel)] focus:border-[var(--app-accent-strong)] focus:ring-[4px] focus:ring-[var(--app-accent-glow)] transition-all outline-none"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button 
            type="submit"
            disabled={loading}
            className={`w-full h-[52px] flex items-center justify-center gap-2 bg-[var(--app-primary-action)] text-white rounded-[var(--app-radius)] font-bold text-[calc(16px*var(--app-font-scale))] hover:bg-[var(--app-primary-action-strong)] transition-all transform hover:-translate-y-0.5 active:translate-y-0 shadow-lg shadow-[var(--app-accent-glow)]
              ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {loading ? 'Authenticating...' : (
              <>
                <LogIn size={20} />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        <div className="px-8 pb-8 text-center border-t border-[var(--app-border)] pt-6 mx-8">
          <p className="text-[var(--app-muted)] text-[calc(12px*var(--app-font-scale))]">
            Contact your administrator for credentials.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
