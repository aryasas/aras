import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Copy, Eye, EyeOff } from 'lucide-react'

interface Subscription {
  tenant_id: string
  plan: {
    id: number
    name: string
    price: number
    currency: string
  }
  status: string
  started_at: string
  expires_at: string
  auto_renew: boolean
  latest_token: {
    token: string
    expires_at: string
    revoked: boolean
  } | null
}

const tokenKey = 'portal_token'
const tenantKey = 'portal_tenant'

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}

function daysRemaining(value: string) {
  return Math.max(0, Math.ceil((new Date(value).getTime() - Date.now()) / 86400000))
}

function maskToken(token: string) {
  if (token.length <= 20) return token
  return `${token.slice(0, 12)}…${token.slice(-6)}`
}

export default function CustomerPortal() {
  const [token, setToken] = useState(() => localStorage.getItem(tokenKey) || '')
  const [login, setLogin] = useState({ email: '', password: '' })
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [showToken, setShowToken] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const clearSession = () => {
    localStorage.removeItem(tokenKey)
    localStorage.removeItem(tenantKey)
    setToken('')
    setSubscription(null)
  }

  useEffect(() => {
    if (!token) return
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetch('/api/v1/saas/portal/subscription', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (response.status === 401) {
          clearSession()
          return
        }
        if (!response.ok) {
          setError('Could not load subscription.')
          return
        }
        setSubscription(await response.json())
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [token])

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/v1/saas/portal/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(login),
      })
      if (!response.ok) {
        setError('Invalid email or password.')
        return
      }
      const data = await response.json()
      localStorage.setItem(tokenKey, data.token)
      localStorage.setItem(tenantKey, data.tenant_id)
      setToken(data.token)
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <main className="mx-auto max-w-md px-6 py-12">
        <h1 className="text-3xl font-bold text-[var(--app-text)]">Customer portal</h1>
        <form onSubmit={handleLogin} className="mt-8 space-y-5">
          <div>
            <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={login.email}
              onChange={(event) => setLogin({ ...login, email: event.target.value })}
              required
              className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-[var(--app-text)]" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={login.password}
              onChange={(event) => setLogin({ ...login, password: event.target.value })}
              required
              className="mt-2 w-full rounded-[var(--app-radius)] border border-[var(--app-border)] px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
            <p className="mt-2 text-xs text-[var(--app-muted)]">First time here? Use the setup link sent by your account admin.</p>
          </div>
          {error && <div className="rounded-[var(--app-radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="rounded-[var(--app-radius)] bg-[var(--app-accent)] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </main>
    )
  }

  if (loading && !subscription) {
    return <main className="mx-auto max-w-3xl px-6 py-12 text-sm text-[var(--app-muted)]">Loading...</main>
  }

  const statusTone = subscription?.status === 'active'
    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : subscription?.status === 'trial'
      ? 'border-amber-200 bg-amber-50 text-amber-700'
      : 'border-red-200 bg-red-50 text-red-700'

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-[var(--app-text)]">Subscription</h1>
        <button onClick={clearSession} className="text-sm font-semibold text-[var(--app-muted)] hover:text-[var(--app-text)]">Logout</button>
      </div>

      {error && <div className="mt-6 rounded-[var(--app-radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}

      {subscription && (
        <section className="mt-8 rounded-[var(--app-radius)] border border-[var(--app-border)] bg-white p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm text-[var(--app-muted)]">{subscription.tenant_id}</p>
              <h2 className="mt-1 text-2xl font-bold text-[var(--app-text)]">{subscription.plan.name}</h2>
              <p className="mt-2 text-sm text-[var(--app-muted)]">{subscription.plan.price} {subscription.plan.currency}/mo</p>
            </div>
            <span className={`rounded-full border px-3 py-1 text-xs font-bold uppercase ${statusTone}`}>{subscription.status}</span>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs font-semibold uppercase text-[var(--app-muted)]">Started</p>
              <p className="mt-1 text-sm text-[var(--app-text)]">{formatDate(subscription.started_at)}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-[var(--app-muted)]">Expires</p>
              <p className="mt-1 text-sm text-[var(--app-text)]">{formatDate(subscription.expires_at)}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-[var(--app-muted)]">Remaining</p>
              <p className="mt-1 text-sm text-[var(--app-text)]">{daysRemaining(subscription.expires_at)} days</p>
            </div>
          </div>

          <div className="mt-6 border-t border-[var(--app-border)] pt-5">
            <p className="text-xs font-semibold uppercase text-[var(--app-muted)]">Latest license token</p>
            {subscription.latest_token ? (
              <div className="mt-2 flex flex-wrap items-center gap-2 rounded-[var(--app-radius)] border border-[var(--app-border)] px-3 py-2">
                <code className="flex-1 break-all text-xs text-[var(--app-text)]">
                  {showToken ? subscription.latest_token.token : maskToken(subscription.latest_token.token)}
                </code>
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="rounded-[var(--app-radius)] p-2 text-[var(--app-muted)] hover:bg-gray-100 hover:text-[var(--app-text)]"
                  aria-label={showToken ? 'Hide token' : 'Show token'}
                >
                  {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(subscription.latest_token?.token || '')}
                  className="rounded-[var(--app-radius)] p-2 text-[var(--app-muted)] hover:bg-gray-100 hover:text-[var(--app-text)]"
                  aria-label="Copy token"
                >
                  <Copy size={16} />
                </button>
              </div>
            ) : (
              <p className="mt-2 text-sm text-[var(--app-muted)]">No active token found.</p>
            )}
          </div>
        </section>
      )}
    </main>
  )
}
