import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, CreditCard, Database, FileText, KeyRound, Users } from 'lucide-react'
import api from '../../lib/api'
import { formatCurrency } from '../../lib/formatters'

interface TenantMetrics {
  storage_bytes?: number
  request_count_30d?: number
  active_users_30d?: number
  last_login_at?: string | null
  db_size_bytes?: number
  requests_daily?: number[]
}

interface Invoice {
  id: number
  number?: string
  amount?: number
  currency?: string
  status?: string
  due_at?: string
}

function bytes(value?: number) {
  const amount = Number(value || 0)
  if (amount >= 1024 ** 3) return `${(amount / 1024 ** 3).toFixed(1)} GB`
  if (amount >= 1024 ** 2) return `${(amount / 1024 ** 2).toFixed(1)} MB`
  return `${Math.round(amount / 1024)} KB`
}

function money(value?: number, currency?: string) {
  return formatCurrency(Number(value || 0), currency)
}

function Sparkline({ values }: { values: number[] }) {
  const max = Math.max(...values, 1)
  const points = values.map((value, index) => `${(index / Math.max(values.length - 1, 1)) * 100},${36 - (value / max) * 28}`).join(' ')
  return <svg viewBox="0 0 100 40" className="h-16 w-full"><polyline points={points} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></svg>
}

export default function TenantDetail() {
  const { id = '' } = useParams()
  const [metrics, setMetrics] = useState<TenantMetrics | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [metricsRes, invoicesRes] = await Promise.allSettled([
          api.get(`/saas/control-panel/tenants/${id}/metrics`),
          api.get('/saas/billing/invoices', { params: { tenant_id: id } }),
        ])
        if (cancelled) return
        if (metricsRes.status === 'fulfilled') setMetrics(metricsRes.value.data)
        if (invoicesRes.status === 'fulfilled') setInvoices(Array.isArray(invoicesRes.value.data) ? invoicesRes.value.data : [])
      } catch (err: any) {
        if (!cancelled) setError(err.message || 'Failed to load tenant details.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [id])

  const requests = useMemo(() => {
    if (metrics?.requests_daily?.length) return metrics.requests_daily
    const total = Number(metrics?.request_count_30d || 0)
    return Array.from({ length: 12 }, (_, index) => Math.round((total / 12) * (0.55 + index / 18)))
  }, [metrics])

  const statCards = [
    { label: 'Storage', value: bytes(metrics?.storage_bytes), icon: Database },
    { label: 'DB Size', value: bytes(metrics?.db_size_bytes), icon: Database },
    { label: '30d Requests', value: Number(metrics?.request_count_30d || 0).toLocaleString('id-ID'), icon: FileText },
    { label: '30d Active Users', value: Number(metrics?.active_users_30d || 0).toLocaleString('id-ID'), icon: Users },
  ]

  return (
    <div className="p-6 lg:p-8">
      <Link to="/control-panel" className="inline-flex items-center gap-2 text-sm text-[var(--text-3)] hover:text-[var(--text)]">
        <ArrowLeft size={15} /> Control Panel
      </Link>
      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="arc-id"><b>tenant</b>/{id}</p>
          <h1 className="mt-2 text-2xl font-bold text-[var(--text)]">Tenant Detail</h1>
        </div>
        {metrics?.last_login_at && <p className="text-sm text-[var(--text-3)]">Last login {new Date(metrics.last_login_at).toLocaleString('id-ID')}</p>}
      </div>

      {error && <div className="mt-5 rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {statCards.map(({ label, value, icon: Icon }) => (
          <section key={label} className="arc-card p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-[var(--text-3)]">{label}</p>
              <Icon size={18} className="text-[var(--accent)]" />
            </div>
            <p className="mt-3 text-xl font-bold text-[var(--text)]">{loading ? '...' : value}</p>
          </section>
        ))}
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[1fr_0.85fr]">
        <section className="arc-card p-5">
          <h2 className="text-sm font-semibold uppercase text-[var(--text-3)]">30d Requests</h2>
          <div className="mt-4"><Sparkline values={requests} /></div>
        </section>

        <section className="arc-card p-5">
          <div className="flex items-center gap-2">
            <CreditCard size={17} className="text-[var(--accent)]" />
            <h2 className="text-sm font-semibold uppercase text-[var(--text-3)]">Payment Methods</h2>
          </div>
          <p className="mt-3 text-sm text-[var(--text-3)]">Provider-hosted payment methods are managed through checkout sessions.</p>
        </section>
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[1fr_0.85fr]">
        <section className="arc-card overflow-hidden">
          <div className="border-b border-[var(--line)] px-5 py-4">
            <h2 className="text-sm font-semibold uppercase text-[var(--text-3)]">Invoices</h2>
          </div>
          <div className="divide-y divide-[var(--line)]">
            {invoices.length === 0 ? (
              <p className="px-5 py-4 text-sm text-[var(--text-3)]">No invoices found.</p>
            ) : invoices.slice(0, 8).map((invoice) => (
              <div key={invoice.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                <div>
                  <p className="font-semibold text-[var(--text)]">{invoice.number || `Invoice #${invoice.id}`}</p>
                  <p className="text-xs text-[var(--text-3)]">{invoice.due_at ? new Date(invoice.due_at).toLocaleDateString('id-ID') : 'No due date'} · {invoice.status || 'unpaid'}</p>
                </div>
                <p className="font-semibold">{money(invoice.amount, invoice.currency)}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="arc-card p-5">
          <div className="flex items-center gap-2">
            <KeyRound size={17} className="text-[var(--accent)]" />
            <h2 className="text-sm font-semibold uppercase text-[var(--text-3)]">License</h2>
          </div>
          <p className="mt-3 text-sm text-[var(--text-3)]">License status is tied to the subscription and active invoice state.</p>
        </section>
      </div>
    </div>
  )
}
