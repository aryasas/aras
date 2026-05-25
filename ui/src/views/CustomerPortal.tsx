// claude-sonnet-4-6
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Copy, Eye, EyeOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { MODULE_LABELS, formatPrice } from '../lib/planUtils'

interface Plan {
  id: number
  plan_key: string
  name: string
  price: number
  currency: string
  max_users: number
  max_branches: number
  max_transactions: number
  max_products: number
  api_access: boolean
  active_modules: string[]
  sort_order: number
  features: Record<string, unknown>
}

interface Subscription {
  tenant_id: string
  plan: Plan
  status: string
  started_at: string
  expires_at: string
  auto_renew: boolean
  latest_token: { token: string; expires_at: string; revoked: boolean } | null
}

interface PortalApp {
  name: string
  label: string
  icon: string
  path: string
}

const STATUS_TONE: Record<string, string> = {
  active: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  trial: 'border-amber-200 bg-amber-50 text-amber-700',
  suspended: 'border-red-200 bg-red-50 text-red-700',
  cancelled: 'border-red-200 bg-red-50 text-red-700',
}

const STATUS_LABEL: Record<string, string> = {
  active: 'Aktif', trial: 'Trial', suspended: 'Suspended', cancelled: 'Dibatalkan',
}

const tokenKey = 'portal_token'
const tenantKey = 'portal_tenant'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium' }).format(new Date(value))
}

function daysRemaining(value: string) {
  return Math.max(0, Math.ceil((new Date(value).getTime() - Date.now()) / 86400000))
}

function maskToken(token: string) {
  if (token.length <= 20) return token
  return `${token.slice(0, 12)}…${token.slice(-6)}`
}


function LimitBar({ label, value, max }: { label: string; value?: number; max: number }) {
  if (max === -1 || value === undefined) {
    return (
      <div className="rounded-[var(--radius)] border border-[var(--line)] px-3 py-2">
        <p className="text-xs text-[var(--text-3)]">{label}</p>
        <p className="text-sm font-semibold text-[var(--text)]">Unlimited</p>
      </div>
    )
  }
  const pct = Math.min(100, Math.round((value / max) * 100))
  const color = pct >= 90 ? 'bg-red-400' : pct >= 70 ? 'bg-amber-400' : 'bg-emerald-400'
  return (
    <div className="rounded-[var(--radius)] border border-[var(--line)] px-3 py-2">
      <div className="flex items-center justify-between">
        <p className="text-xs text-[var(--text-3)]">{label}</p>
        <p className="text-xs font-semibold text-[var(--text)]">{value.toLocaleString('id-ID')} / {max.toLocaleString('id-ID')}</p>
      </div>
      <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--line)]">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function CustomerPortal() {
  const [token, setToken] = useState(() => localStorage.getItem(tokenKey) || '')
  const [login, setLogin] = useState({ email: '', password: '' })
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [apps, setApps] = useState<PortalApp[]>([])
  const [upgradePlans, setUpgradePlans] = useState<Plan[]>([])
  const [showUpgrade, setShowUpgrade] = useState(false)
  const [showToken, setShowToken] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!showUpgrade) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setShowUpgrade(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [showUpgrade])

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
        const res = await fetch('/api/v1/saas/portal/subscription', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.status === 401) { clearSession(); return }
        if (!res.ok) { setError('Tidak dapat memuat data langganan.'); return }
        const sub: Subscription = await res.json()
        setSubscription(sub)

        // apps and plans are independent — fetch in parallel
        const [appsRes, plansRes] = await Promise.all([
          fetch('/api/v1/saas/portal/apps', { headers: { Authorization: `Bearer ${token}` } }),
          fetch('/api/v1/saas/plans/public'),
        ])
        if (appsRes.ok) {
          const p = await appsRes.json()
          setApps(Array.isArray(p.apps) ? p.apps : [])
        }
        if (plansRes.ok) {
          const all: Plan[] = await plansRes.json()
          setUpgradePlans(all.filter((p) => p.plan_key !== 'enterprise' && p.sort_order > (sub.plan.sort_order ?? 0)))
        }
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
      const res = await fetch('/api/v1/saas/portal/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(login),
      })
      if (!res.ok) { setError('Email atau password salah.'); return }
      const data = await res.json()
      localStorage.setItem(tokenKey, data.token)
      localStorage.setItem(tenantKey, data.tenant_id)
      setToken(data.token)
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <main className="mx-auto max-w-md px-6 py-16">
        <h1 className="text-3xl font-bold">Portal Pelanggan</h1>
        <p className="mt-1 text-sm text-[var(--text-2)]">Masuk untuk mengelola langganan Anda.</p>
        <form onSubmit={handleLogin} className="mt-8 space-y-5">
          <div>
            <label className="block text-sm font-semibold" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={login.email}
              onChange={(e) => setLogin({ ...login, email: e.target.value })}
              required
              className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={login.password}
              onChange={(e) => setLogin({ ...login, password: e.target.value })}
              required
              className="mt-2 w-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--aras-accent-glow)]"
            />
            <p className="mt-2 text-xs text-[var(--text-3)]">Pertama kali? Gunakan link setup yang dikirim admin.</p>
          </div>
          {error && <div className="rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-[var(--radius)] bg-[var(--accent)] py-3 text-sm font-semibold text-white hover:bg-[var(--aras-accent-strong)] disabled:opacity-50"
          >
            {loading ? 'Masuk...' : 'Masuk'}
          </button>
          <p className="text-center text-xs text-[var(--text-3)]">
            Belum punya akun?{' '}
            <Link to="/signup" className="text-[var(--accent)] hover:underline">Daftar di sini</Link>
          </p>
        </form>
      </main>
    )
  }

  if (loading && !subscription) {
    return <main className="mx-auto max-w-3xl px-6 py-12 text-sm text-[var(--text-3)]">Memuat...</main>
  }

  const statusTone = STATUS_TONE[subscription?.status ?? ''] ?? 'border-red-200 bg-red-50 text-red-700'

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Portal Pelanggan</h1>
        <button onClick={clearSession} className="text-sm text-[var(--text-3)] hover:text-[var(--text)]">Keluar</button>
      </div>

      {error && <div className="mt-6 rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}

      {subscription && (
        <div className="mt-6 space-y-5">

          {/* Plan card */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs text-[var(--text-3)]">{subscription.tenant_id}</p>
                <h2 className="mt-1 text-2xl font-bold">{subscription.plan.name}</h2>
                <p className="mt-1 text-sm text-[var(--text-2)]">
                  {formatPrice(subscription.plan.price)}
                </p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {subscription.plan.active_modules.map((m) => (
                    <span key={m} className="rounded-full border border-[var(--line)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--text-2)]">
                      {MODULE_LABELS[m] ?? m}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span className={`rounded-full border px-3 py-1 text-xs font-bold uppercase ${statusTone}`}>
                  {STATUS_LABEL[subscription.status] ?? subscription.status}
                </span>
                {upgradePlans.length > 0 && (
                  <button
                    onClick={() => setShowUpgrade(true)}
                    className="rounded-[var(--radius)] border border-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--aras-accent-glow)]"
                  >
                    Upgrade Paket
                  </button>
                )}
              </div>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-4 border-t border-[var(--line)] pt-5">
              <div>
                <p className="text-xs text-[var(--text-3)]">Mulai</p>
                <p className="mt-1 text-sm font-medium">{formatDate(subscription.started_at)}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">Berakhir</p>
                <p className="mt-1 text-sm font-medium">{formatDate(subscription.expires_at)}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">Sisa</p>
                <p className="mt-1 text-sm font-medium">{daysRemaining(subscription.expires_at)} hari</p>
              </div>
            </div>
          </section>

          {/* Usage limits */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
            <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">Penggunaan</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <LimitBar label="Pengguna" max={subscription.plan.max_users} />
              <LimitBar label="Cabang" max={subscription.plan.max_branches} />
              <LimitBar label="Transaksi / bulan" max={subscription.plan.max_transactions} />
              <LimitBar label="Produk" max={subscription.plan.max_products} />
            </div>
          </section>

          {/* Apps */}
          {apps.length > 0 && (
            <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
              <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">Aplikasi Tersedia</h3>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {apps.map((app) => (
                  <div key={app.name} className="rounded-[var(--radius)] border border-[var(--line)] px-3 py-2">
                    <p className="text-sm font-semibold">{app.label}</p>
                    <p className="text-xs text-[var(--text-3)]">{app.path}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* License token */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
            <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">License Token</h3>
            {subscription.latest_token ? (
              <div className="mt-3 flex items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--bg)] px-3 py-2">
                <code className="flex-1 break-all text-xs text-[var(--text)]">
                  {showToken ? subscription.latest_token.token : maskToken(subscription.latest_token.token)}
                </code>
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="rounded p-1.5 text-[var(--text-3)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                  aria-label={showToken ? 'Sembunyikan token' : 'Tampilkan token'}
                >
                  {showToken ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(subscription.latest_token?.token || '')}
                  className="rounded p-1.5 text-[var(--text-3)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                  aria-label="Salin token"
                >
                  <Copy size={15} />
                </button>
              </div>
            ) : (
              <p className="mt-2 text-sm text-[var(--text-3)]">Tidak ada token aktif.</p>
            )}
          </section>
        </div>
      )}

      {/* Upgrade modal */}
      {showUpgrade && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" onClick={() => setShowUpgrade(false)}>
          <div className="w-full max-w-lg rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="font-bold">Upgrade Paket</h2>
              <button onClick={() => setShowUpgrade(false)} className="text-sm text-[var(--text-3)] hover:text-[var(--text)]">✕</button>
            </div>
            <div className="mt-4 space-y-3">
              {upgradePlans.map((p) => (
                <div key={p.id} className="flex items-center justify-between rounded-[var(--radius)] border border-[var(--line)] px-4 py-3">
                  <div>
                    <p className="font-semibold">{p.name}</p>
                    <p className="text-xs text-[var(--text-2)]">Rp {p.price.toLocaleString('id-ID')}/bulan · {p.max_users === -1 ? 'Unlimited' : p.max_users} pengguna</p>
                  </div>
                  <Link
                    to={`/signup?plan=${p.plan_key}`}
                    className="rounded-[var(--radius)] bg-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--aras-accent-strong)]"
                    onClick={() => setShowUpgrade(false)}
                  >
                    Pilih
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
