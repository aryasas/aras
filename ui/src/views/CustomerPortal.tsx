// claude-sonnet-4-6
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Copy, CreditCard, Eye, EyeOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { MODULE_LABELS } from '../lib/planUtils'
import { formatCurrency } from '../lib/formatters'
import { useNotify } from '../aras-core/contexts/NotificationContext'

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
  id?: number
  tenant_id: string
  plan: Plan
  status: string
  started_at: string
  expires_at: string
  next_billing_at?: string | null
  trial_ends_at?: string | null
  billing_cycle?: string
  auto_renew: boolean
  latest_token: { token: string; expires_at: string; revoked: boolean } | null
}

interface PortalApp {
  name: string
  label: string
  icon: string
  path: string
}

interface ApiEnvelope<T> {
  success: boolean
  data?: T
  message?: string | null
  error?: string | { message?: string } | null
}

interface Invoice {
  id: number
  subscription_id?: number
  number?: string
  amount?: number
  currency?: string
  status?: string
  due_at?: string
  paid_at?: string | null
}

interface PaymentMethod {
  code: string
  label: string
  provider_code?: string
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

async function readApiPayload<T>(res: Response): Promise<T> {
  const json = await res.json()
  if (json && typeof json === 'object' && typeof (json as ApiEnvelope<T>).success === 'boolean') {
    const envelope = json as ApiEnvelope<T>
    if (!envelope.success) {
      const message = typeof envelope.error === 'string'
        ? envelope.error
        : envelope.error?.message || envelope.message || 'Request failed'
      throw new Error(message)
    }
    return envelope.data as T
  }
  return json as T
}

async function readSafeApiPayload<T>(
  res: Response,
  notify: (message: string, type?: 'success' | 'error' | 'info' | 'warning') => void,
  fallbackMessage: string,
): Promise<T | null> {
  const data = await res.json().catch(() => null)
  if (!data || typeof data !== 'object') {
    notify(fallbackMessage, 'error')
    return null
  }
  if (typeof (data as ApiEnvelope<T>).success !== 'boolean' || !(data as ApiEnvelope<T>).success) {
    const envelope = data as ApiEnvelope<T>
    const message = typeof envelope.error === 'string'
      ? envelope.error
      : envelope.error?.message || envelope.message || fallbackMessage
    notify(message, 'error')
    return null
  }
  return (data as ApiEnvelope<T>).data as T
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
  const showNotification = useNotify()
  const [token, setToken] = useState(() => localStorage.getItem(tokenKey) || '')
  const [login, setLogin] = useState({ email: '', password: '' })
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [apps, setApps] = useState<PortalApp[]>([])
  const [upgradePlans, setUpgradePlans] = useState<Plan[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])
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
        const sub = await readSafeApiPayload<Subscription>(res, showNotification, 'Portal data load failed')
        if (!sub) { setError('Tidak dapat memuat data langganan.'); return }
        setSubscription(sub)

        // apps and plans are independent — fetch in parallel
        const [appsRes, plansRes, invoicesRes, methodsRes] = await Promise.all([
          fetch('/api/v1/saas/portal/apps', { headers: { Authorization: `Bearer ${token}` } }),
          fetch('/api/v1/saas/plans/public'),
          fetch('/api/v1/saas/billing/invoices', { headers: { Authorization: `Bearer ${token}` } }),
          fetch('/api/v1/saas/payments/methods'),
        ])
        const p = await readSafeApiPayload<{ apps?: PortalApp[] } | PortalApp[]>(appsRes, showNotification, 'Portal data load failed')
        if (!p) return
        setApps(Array.isArray(p) ? p : Array.isArray(p.apps) ? p.apps : [])

        const allPayload = await readSafeApiPayload<Plan[]>(plansRes, showNotification, 'Portal data load failed')
        if (!allPayload) return
        const all = Array.isArray(allPayload) ? allPayload : []
        setUpgradePlans(all.filter((p) => p.plan_key !== 'enterprise' && p.sort_order > (sub.plan.sort_order ?? 0)))

        const invoicePayload = await readSafeApiPayload<Invoice[]>(invoicesRes, showNotification, 'Portal data load failed')
        if (!invoicePayload) return
        setInvoices(Array.isArray(invoicePayload) ? invoicePayload : [])

        const methodPayload = await readSafeApiPayload<PaymentMethod[]>(methodsRes, showNotification, 'Portal data load failed')
        if (!methodPayload) return
        setPaymentMethods(Array.isArray(methodPayload) ? methodPayload : [])
      } catch (err) {
        console.error(err)
        setError('Tidak dapat memuat data portal.')
        showNotification('Portal data load failed', 'error')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [showNotification, token])

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
      const data = await readApiPayload<{ token: string; tenant_id: string }>(res)
      localStorage.setItem(tokenKey, data.token)
      localStorage.setItem(tenantKey, data.tenant_id)
      setToken(data.token)
    } finally {
      setLoading(false)
    }
  }

  const handlePayInvoice = async (invoice: Invoice) => {
    setLoading(true)
    setError(null)
    try {
      const payRes = await fetch(`/api/v1/saas/billing/invoices/${invoice.id}/pay`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (payRes.ok) {
        const payload = await readApiPayload<{ checkout_url?: string }>(payRes)
        if (payload.checkout_url) {
          window.location.href = payload.checkout_url
          return
        }
      }

      const subscriptionId = invoice.subscription_id || subscription?.id
      if (!subscriptionId) {
        setError('Invoice belum memiliki referensi subscription untuk checkout.')
        return
      }
      const checkoutRes = await fetch('/api/v1/saas/payments/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subscription_id: subscriptionId,
          return_url: `${window.location.origin}/portal/setup?status=pending&invoice_id=${invoice.id}`,
        }),
      })
      if (!checkoutRes.ok) {
        setError('Tidak dapat memulai pembayaran invoice.')
        return
      }
      const checkoutPayload = await readApiPayload<{ checkout_url?: string }>(checkoutRes)
      if (checkoutPayload.checkout_url) window.location.href = checkoutPayload.checkout_url
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
                  {formatCurrency(subscription.plan.price, subscription.plan.currency)}
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
            <div className="mt-5 grid gap-3 border-t border-[var(--line)] pt-5 sm:grid-cols-3">
              <div>
                <p className="text-xs text-[var(--text-3)]">Next billing</p>
                <p className="mt-1 text-sm font-medium">{subscription.next_billing_at ? formatDate(subscription.next_billing_at) : '-'}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">Amount</p>
                <p className="mt-1 text-sm font-medium">{formatCurrency(subscription.plan.price, subscription.plan.currency)}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">Trial ends</p>
                <p className="mt-1 text-sm font-medium">{subscription.trial_ends_at ? formatDate(subscription.trial_ends_at) : '-'}</p>
              </div>
            </div>
          </section>

          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">Billing</h3>
              <button
                type="button"
                onClick={() => {
                  const openInvoice = invoices.find((invoice) => invoice.status !== 'paid' && invoice.status !== 'void')
                  if (openInvoice) handlePayInvoice(openInvoice)
                }}
                disabled={!invoices.some((invoice) => invoice.status !== 'paid' && invoice.status !== 'void') || loading}
                className="inline-flex items-center gap-2 rounded-[var(--radius)] border border-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--aras-accent-glow)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <CreditCard size={14} /> Add payment method
              </button>
            </div>
            {paymentMethods.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {paymentMethods.slice(0, 8).map((method) => (
                  <span key={`${method.provider_code || 'provider'}-${method.code}`} className="rounded-full border border-[var(--line)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--text-2)]">
                    {method.label || method.code}
                  </span>
                ))}
              </div>
            )}
            <div className="mt-4 divide-y divide-[var(--line)] rounded-[var(--radius)] border border-[var(--line)]">
              {invoices.length === 0 ? (
                <p className="px-4 py-3 text-sm text-[var(--text-3)]">Belum ada invoice.</p>
              ) : invoices.map((invoice) => (
                <div key={invoice.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--text)]">{invoice.number || `Invoice #${invoice.id}`}</p>
                    <p className="text-xs text-[var(--text-3)]">{invoice.due_at ? formatDate(invoice.due_at) : 'No due date'} · {invoice.status || 'unpaid'}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <p className="text-sm font-semibold">{invoice.currency || subscription.plan.currency} {Number(invoice.amount || 0).toLocaleString('id-ID')}</p>
                    {invoice.status !== 'paid' && invoice.status !== 'void' && (
                      <button
                        type="button"
                        onClick={() => handlePayInvoice(invoice)}
                        disabled={loading}
                        className="rounded-[var(--radius)] bg-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                      >
                        Pay now
                      </button>
                    )}
                  </div>
                </div>
              ))}
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
                    <p className="text-xs text-[var(--text-2)]">{formatCurrency(p.price, p.currency)} · {p.max_users === -1 ? 'Unlimited' : p.max_users} pengguna</p>
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
