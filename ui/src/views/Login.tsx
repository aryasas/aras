// claude-opus-4-7
// ARC-styled login. Dot-grid backdrop, coral accent, mono ID badge, submit on the LEFT.
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
      setUser(me.data)
      setOrganizations(organizations)
      setActiveOrg(organizations.length === 1 ? organizations[0].id : null)
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
    <div className="arc arc-bg arc-dotgrid min-h-screen flex items-center justify-center p-4">
      <div data-testid="login-card" className="w-full max-w-md arc-card overflow-hidden" style={{ background: 'var(--surface)' }}>
        <div className="px-8 pt-8 pb-2 flex items-start gap-4">
          <ArasLogo size="lg" />
          <div className="flex-1 min-w-0">
            <div className="arc-id"><b>arc</b>/auth/<b>login</b></div>
            <h1 className="text-[22px] font-semibold text-[var(--text)] tracking-tight mt-1">Welcome back</h1>
            <p className="arc-dim text-[12.5px] mt-0.5">Sign in to your Aras workspace.</p>
          </div>
        </div>

        <form onSubmit={handleLogin} className="px-8 py-6 flex flex-col gap-5">
          {error && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-[var(--radius)] border text-[12.5px]"
                 style={{ background: 'color-mix(in oklch, var(--danger) 10%, var(--surface))', borderColor: 'color-mix(in oklch, var(--danger) 30%, var(--line))', color: 'var(--danger)' }}>
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          <label className="flex flex-col gap-1.5">
            <span className="arc-id">user</span>
            <span className="relative">
              <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="arc-input"
                style={{ paddingLeft: 32 }}
                placeholder="username or email"
                autoFocus
              />
            </span>
          </label>

          <label className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <span className="arc-id">pass</span>
              <Link to="/forgot-password" className="text-[11.5px] font-medium text-[var(--accent)] hover:underline">
                forgot?
              </Link>
            </div>
            <span className="relative">
              <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="arc-input"
                style={{ paddingLeft: 32 }}
                placeholder="••••••••"
              />
            </span>
          </label>

          {/* Action bar: primary on the LEFT */}
          <div className="flex items-center gap-2 pt-2">
            <button type="submit" disabled={loading} className="arc-btn primary" style={{ height: 38, paddingInline: 18 }}>
              <LogIn size={15} />
              <span>{loading ? 'Signing in…' : 'Sign in'}</span>
            </button>
            <span className="flex-1" />
            <span className="arc-kbd">↵</span>
          </div>
        </form>

        <div className="px-8 pb-8 pt-4 border-t border-[var(--line)] arc-dim2 text-[11.5px] flex flex-col gap-1.5">
          <span>Contact your administrator for access.</span>
          <Link to="/portal" className="text-[var(--text-3)] hover:text-[var(--accent)]">
            Customer? Sign in to your portal →
          </Link>
          <Link to="/welcome" className="text-[var(--text-3)] hover:text-[var(--accent)]">
            New here? Start your free trial →
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Login
