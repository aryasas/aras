// claude-sonnet-4-6
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Copy, CreditCard, Eye, EyeOff, Lock, Mail, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { MODULE_LABELS } from '../lib/planUtils'
import { formatCurrency } from '../lib/formatters'
import { useNotify } from '../aras-core/contexts/NotificationContext'
import { ArasLogo } from '../components/ArasLogo'
import { useLanguage } from '../context/LanguageContext'
import api, { type ApiRequestConfig } from '../lib/api'

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

function LimitBar({ label, value, max, unlimitedLabel }: { label: string; value?: number; max: number; unlimitedLabel: string }) {
  if (max === -1 || value === undefined) {
    return (
      <div className="rounded-[var(--radius)] border border-[var(--line)] px-3 py-2">
        <p className="text-xs text-[var(--text-3)]">{label}</p>
        <p className="text-sm font-semibold text-[var(--text)]">{unlimitedLabel}</p>
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
  const { t } = useLanguage()
  const showNotification = useNotify()
  const [token, setToken] = useState(() => sessionStorage.getItem(tokenKey) || '')
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
  const portalAuthConfig = { portalAuth: true } as ApiRequestConfig
  const statusLabels: Record<string, string> = {
    active: t('portal.status.active'),
    trial: t('portal.status.trial'),
    suspended: t('portal.status.suspended'),
    cancelled: t('portal.status.cancelled'),
  }

  useEffect(() => {
    if (!showUpgrade) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setShowUpgrade(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [showUpgrade])

  const clearSession = () => {
    sessionStorage.removeItem(tokenKey)
    sessionStorage.removeItem(tenantKey)
    setToken('')
    setSubscription(null)
  }

  useEffect(() => {
    if (!token) return
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const { data: sub } = await api.get<Subscription>('/saas/portal/subscription', portalAuthConfig)
        setSubscription(sub)

        // apps and plans are independent — fetch in parallel
        const [appsRes, plansRes, invoicesRes, methodsRes] = await Promise.all([
          api.get<{ apps?: PortalApp[] } | PortalApp[]>('/saas/portal/apps', portalAuthConfig),
          api.get<Plan[]>('/saas/plans/public'),
          api.get<Invoice[]>('/saas/billing/invoices', portalAuthConfig),
          api.get<PaymentMethod[]>('/saas/payments/methods'),
        ])
        const p = appsRes.data
        setApps(Array.isArray(p) ? p : Array.isArray(p.apps) ? p.apps : [])

        const allPayload = plansRes.data
        const all = Array.isArray(allPayload) ? allPayload : []
        setUpgradePlans(all.filter((p) => p.plan_key !== 'enterprise' && p.sort_order > (sub.plan.sort_order ?? 0)))

        const invoicePayload = invoicesRes.data
        setInvoices(Array.isArray(invoicePayload) ? invoicePayload : [])

        const methodPayload = methodsRes.data
        setPaymentMethods(Array.isArray(methodPayload) ? methodPayload : [])
      } catch (err: any) {
        if (err?.response?.status === 401) {
          clearSession()
          return
        }
        console.error(err)
        setError(t('portal.error.loadPortal'))
        showNotification(t('portal.error.loadPortal'), 'error')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [showNotification, t, token])

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post<{ token: string; tenant_id: string }>('/saas/portal/login', login)
      sessionStorage.setItem(tokenKey, data.token)
      sessionStorage.setItem(tenantKey, data.tenant_id)
      setToken(data.token)
    } catch (err: any) {
      setError(err?.response?.status === 401 ? t('portal.login.invalidCredentials') : t('portal.login.failed'))
    } finally {
      setLoading(false)
    }
  }

  const handlePayInvoice = async (invoice: Invoice) => {
    setLoading(true)
    setError(null)
    try {
      try {
        const { data: payload } = await api.post<{ checkout_url?: string }>(`/saas/billing/invoices/${invoice.id}/pay`, {}, portalAuthConfig)
        if (payload.checkout_url) {
          window.location.href = payload.checkout_url
          return
        }
      } catch (err: any) {
        if (err?.response?.status === 401) {
          clearSession()
          return
        }
      }

      const subscriptionId = invoice.subscription_id || subscription?.id
      if (!subscriptionId) {
        setError(t('portal.billing.missingSubscription'))
        return
      }
      const { data: checkoutPayload } = await api.post<{ checkout_url?: string }>('/saas/payments/checkout', {
          subscription_id: subscriptionId,
          return_url: `${window.location.origin}/portal/setup?status=pending&invoice_id=${invoice.id}`,
        })
      if (checkoutPayload.checkout_url) window.location.href = checkoutPayload.checkout_url
      else setError(t('portal.billing.checkoutFailed'))
    } catch (err: any) {
      if (err?.response?.status === 401) {
        clearSession()
        return
      }
      setError(t('portal.billing.checkoutFailed'))
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <main className="arc arc-bg arc-dotgrid min-h-screen px-4 py-10">
        <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-5xl items-center gap-10 lg:grid-cols-[minmax(0,1fr)_420px]">
          <section className="max-lg:text-center">
            <p className="arc-id"><b>arc</b>/portal/<b>customer</b></p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-[var(--text)] lg:text-5xl">{t('portal.hero.title')}</h1>
            <p className="mt-4 max-w-xl text-base leading-7 text-[var(--text-2)] max-lg:mx-auto">
              {t('portal.hero.subtitle')}
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              <div className="arc-card bg-[var(--surface)] p-4">
                <p className="text-sm font-semibold text-[var(--text)]">{t('portal.hero.cards.billing.title')}</p>
                <p className="mt-1 text-sm text-[var(--text-2)]">{t('portal.hero.cards.billing.body')}</p>
              </div>
              <div className="arc-card bg-[var(--surface)] p-4">
                <p className="text-sm font-semibold text-[var(--text)]">{t('portal.hero.cards.access.title')}</p>
                <p className="mt-1 text-sm text-[var(--text-2)]">{t('portal.hero.cards.access.body')}</p>
              </div>
              <div className="arc-card bg-[var(--surface)] p-4">
                <p className="text-sm font-semibold text-[var(--text)]">{t('portal.hero.cards.license.title')}</p>
                <p className="mt-1 text-sm text-[var(--text-2)]">{t('portal.hero.cards.license.body')}</p>
              </div>
            </div>
          </section>

          <section className="arc-card overflow-hidden bg-[var(--surface)] shadow-[var(--shadow-card-lift)]">
            <div className="px-8 pt-8 pb-2 flex items-start gap-4">
              <ArasLogo size="lg" />
              <div className="flex-1 min-w-0">
                <div className="arc-id"><b>arc</b>/portal/<b>login</b></div>
                <h2 className="mt-1 text-[26px] font-semibold tracking-tight text-[var(--text)]">{t('portal.login.title')}</h2>
                <p className="mt-1 text-sm leading-6 text-[var(--text-2)]">{t('portal.login.subtitle')}</p>
              </div>
            </div>

            <form onSubmit={handleLogin} className="px-8 py-6 flex flex-col gap-5">
              <label className="flex flex-col gap-1.5">
                <span className="arc-id">{t('portal.login.emailLabel')}</span>
                <span className="relative">
                  <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                  <input
                    id="email"
                    type="email"
                    value={login.email}
                    onChange={(e) => setLogin({ ...login, email: e.target.value })}
                    required
                    className="arc-input"
                    style={{ paddingLeft: 32 }}
                    placeholder={t('portal.login.emailPlaceholder')}
                  />
                </span>
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="arc-id">{t('portal.login.passwordLabel')}</span>
                <span className="relative">
                  <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                  <input
                    id="password"
                    type="password"
                    value={login.password}
                    onChange={(e) => setLogin({ ...login, password: e.target.value })}
                    required
                    className="arc-input"
                    style={{ paddingLeft: 32 }}
                    placeholder={t('portal.login.passwordPlaceholder')}
                  />
                </span>
                <p className="mt-1 text-xs text-[var(--text-3)]">{t('portal.login.setupHint')}</p>
              </label>
              {error && (
                <div
                  className="rounded-[var(--radius)] border px-4 py-3 text-sm font-medium"
                  style={{
                    background: 'color-mix(in oklch, var(--danger) 8%, var(--surface))',
                    borderColor: 'color-mix(in oklch, var(--danger) 25%, var(--line))',
                    color: 'var(--danger)',
                  }}
                >
                  {error}
                </div>
              )}
              <button type="submit" disabled={loading} className="arc-btn primary w-full justify-center" style={{ height: 44 }}>
                {loading ? t('portal.login.signingIn') : t('portal.login.submit')}
              </button>
            </form>
            <div className="border-t border-[var(--line)] px-8 pb-8 pt-4 text-[11.5px] flex flex-col gap-2 text-[var(--text-3)]">
              <div className="inline-flex items-center gap-2 text-[var(--text-3)]">
                <ShieldCheck size={14} />
                {t('portal.login.securityNote')}
              </div>
              <p>
                {t('portal.login.needAccount')}{' '}
                <Link to="/signup" className="text-[var(--accent)] hover:underline">{t('portal.login.startPlan')}</Link>
              </p>
            </div>
          </section>
        </div>
      </main>
    )
  }

  if (loading && !subscription) {
    return <main className="mx-auto max-w-3xl px-6 py-12 text-sm text-[var(--text-3)]">{t('portal.loading')}</main>
  }

  const statusTone = STATUS_TONE[subscription?.status ?? ''] ?? 'border-red-200 bg-red-50 text-red-700'

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">{t('portal.title')}</h1>
        <button onClick={clearSession} className="text-sm text-[var(--text-3)] hover:text-[var(--text)]">{t('portal.logout')}</button>
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
                      {t(`public.modules.${m}`, MODULE_LABELS[m] ?? m)}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span className={`rounded-full border px-3 py-1 text-xs font-bold uppercase ${statusTone}`}>
                  {statusLabels[subscription.status] ?? subscription.status}
                </span>
                {upgradePlans.length > 0 && (
                  <button
                    onClick={() => setShowUpgrade(true)}
                    className="rounded-[var(--radius)] border border-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--aras-accent-glow)]"
                  >
                    {t('portal.plan.upgrade')}
                  </button>
                )}
              </div>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-4 border-t border-[var(--line)] pt-5">
              <div>
                <p className="text-xs text-[var(--text-3)]">{t('portal.plan.started')}</p>
                <p className="mt-1 text-sm font-medium">{formatDate(subscription.started_at)}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">{t('portal.plan.expires')}</p>
                <p className="mt-1 text-sm font-medium">{formatDate(subscription.expires_at)}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">{t('portal.plan.remaining')}</p>
                <p className="mt-1 text-sm font-medium">{t('portal.plan.remainingDays').replace('{days}', String(daysRemaining(subscription.expires_at)))}</p>
              </div>
            </div>
            <div className="mt-5 grid gap-3 border-t border-[var(--line)] pt-5 sm:grid-cols-3">
              <div>
                <p className="text-xs text-[var(--text-3)]">{t('portal.plan.nextBilling')}</p>
                <p className="mt-1 text-sm font-medium">{subscription.next_billing_at ? formatDate(subscription.next_billing_at) : '-'}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">{t('portal.plan.amount')}</p>
                <p className="mt-1 text-sm font-medium">{formatCurrency(subscription.plan.price, subscription.plan.currency)}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-3)]">{t('portal.plan.trialEnds')}</p>
                <p className="mt-1 text-sm font-medium">{subscription.trial_ends_at ? formatDate(subscription.trial_ends_at) : '-'}</p>
              </div>
            </div>
          </section>

          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">{t('portal.billing.title')}</h3>
              <button
                type="button"
                onClick={() => {
                  const openInvoice = invoices.find((invoice) => invoice.status !== 'paid' && invoice.status !== 'void')
                  if (openInvoice) void handlePayInvoice(openInvoice)
                }}
                disabled={!invoices.some((invoice) => invoice.status !== 'paid' && invoice.status !== 'void') || loading}
                className="inline-flex items-center gap-2 rounded-[var(--radius)] border border-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--aras-accent-glow)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <CreditCard size={14} /> {t('portal.billing.addPaymentMethod')}
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
                <p className="px-4 py-3 text-sm text-[var(--text-3)]">{t('portal.billing.noInvoices')}</p>
              ) : invoices.map((invoice) => (
                <div key={invoice.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--text)]">{invoice.number || t('portal.billing.invoiceNumber').replace('{id}', String(invoice.id))}</p>
                    <p className="text-xs text-[var(--text-3)]">{invoice.due_at ? formatDate(invoice.due_at) : t('portal.billing.noDueDate')} · {invoice.status || t('portal.billing.unpaid')}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <p className="text-sm font-semibold">{invoice.currency || subscription.plan.currency} {Number(invoice.amount || 0).toLocaleString('id-ID')}</p>
                    {invoice.status !== 'paid' && invoice.status !== 'void' && (
                      <button
                        type="button"
                        onClick={() => void handlePayInvoice(invoice)}
                        disabled={loading}
                        className="rounded-[var(--radius)] bg-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                      >
                        {t('portal.billing.payNow')}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Usage limits */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
            <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">{t('portal.usage.title')}</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <LimitBar label={t('portal.usage.users')} max={subscription.plan.max_users} unlimitedLabel={t('portal.plan.unlimited')} />
              <LimitBar label={t('portal.usage.branches')} max={subscription.plan.max_branches} unlimitedLabel={t('portal.plan.unlimited')} />
              <LimitBar label={t('portal.usage.transactions')} max={subscription.plan.max_transactions} unlimitedLabel={t('portal.plan.unlimited')} />
              <LimitBar label={t('portal.usage.products')} max={subscription.plan.max_products} unlimitedLabel={t('portal.plan.unlimited')} />
            </div>
          </section>

          {/* Apps */}
          {apps.length > 0 && (
            <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6">
              <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">{t('portal.apps.title')}</h3>
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
            <h3 className="text-sm font-semibold uppercase text-[var(--text-3)]">{t('portal.license.title')}</h3>
            {subscription.latest_token ? (
              <div className="mt-3 flex items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--bg)] px-3 py-2">
                <code className="flex-1 break-all text-xs text-[var(--text)]">
                  {showToken ? subscription.latest_token.token : maskToken(subscription.latest_token.token)}
                </code>
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="rounded p-1.5 text-[var(--text-3)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                  aria-label={showToken ? t('portal.license.hide') : t('portal.license.show')}
                >
                  {showToken ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await navigator.clipboard.writeText(subscription.latest_token?.token || '')
                    showNotification(t('portal.license.copied'), 'success')
                  }}
                  className="rounded p-1.5 text-[var(--text-3)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                  aria-label={t('portal.license.copy')}
                >
                  <Copy size={15} />
                </button>
              </div>
            ) : (
              <p className="mt-2 text-sm text-[var(--text-3)]">{t('portal.license.empty')}</p>
            )}
          </section>
        </div>
      )}

      {/* Upgrade modal */}
      {showUpgrade && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" onClick={() => setShowUpgrade(false)}>
          <div className="w-full max-w-lg rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="font-bold">{t('portal.plan.upgrade')}</h2>
              <button onClick={() => setShowUpgrade(false)} className="text-sm text-[var(--text-3)] hover:text-[var(--text)]">✕</button>
            </div>
            <div className="mt-4 space-y-3">
              {upgradePlans.map((p) => (
                <div key={p.id} className="flex items-center justify-between rounded-[var(--radius)] border border-[var(--line)] px-4 py-3">
                  <div>
                    <p className="font-semibold">{p.name}</p>
                    <p className="text-xs text-[var(--text-2)]">{formatCurrency(p.price, p.currency)} · {p.max_users === -1 ? t('portal.plan.unlimited') : `${p.max_users} ${t('portal.usage.users').toLowerCase()}`}</p>
                  </div>
                  <Link
                    to={`/signup?plan=${p.plan_key}`}
                    className="rounded-[var(--radius)] bg-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--aras-accent-strong)]"
                    onClick={() => setShowUpgrade(false)}
                  >
                    {t('portal.plan.select')}
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
