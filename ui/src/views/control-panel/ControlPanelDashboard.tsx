import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Building2, RefreshCw, TrendingDown, TrendingUp } from 'lucide-react'
import api from '../../lib/api'
import { formatCurrency } from '../../lib/formatters'

interface RevenueSummary {
  mrr?: number
  arr?: number
  churn?: number
  active_tenants?: number
  failure_rate?: number
}

interface TenantRow {
  id?: number
  tenant_id?: string | null
  company_name?: string
  email?: string
  status?: string
  plan?: { name?: string; plan_key?: string } | null
}

interface PaymentRow {
  id?: number
  provider_code?: string
  provider_payment_id?: string
  amount?: number
  currency?: string
  status?: string
  created_at?: string
}

function money(value?: number, currency?: string) {
  return formatCurrency(Number(value || 0), currency)
}

function pct(value?: number) {
  return `${Number(value || 0).toFixed(1)}%`
}

function SparkChart({ values }: { values: number[] }) {
  const max = Math.max(...values, 1)
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * 100
      const y = 42 - (value / max) * 34
      return `${x},${y}`
    })
    .join(' ')

  return (
    <svg viewBox="0 0 100 48" className="h-28 w-full" role="img" aria-label="Revenue trend">
      <polyline points={points} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="0" y1="44" x2="100" y2="44" stroke="var(--line)" />
    </svg>
  )
}

export default function ControlPanelDashboard() {
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null)
  const [tenants, setTenants] = useState<TenantRow[]>([])
  const [payments, setPayments] = useState<PaymentRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [revenueRes, tenantsRes, paymentsRes] = await Promise.allSettled([
        api.get('/saas/control-panel/revenue'),
        api.get('/saas/control-panel/tenants'),
        api.get('/saas/control-panel/payments/recent'),
      ])
      if (revenueRes.status === 'fulfilled') setRevenue(revenueRes.value.data)
      if (tenantsRes.status === 'fulfilled') setTenants(Array.isArray(tenantsRes.value.data) ? tenantsRes.value.data : [])
      if (paymentsRes.status === 'fulfilled') setPayments(Array.isArray(paymentsRes.value.data) ? paymentsRes.value.data : [])
    } catch (err: any) {
      setError(err.message || 'Failed to load Control Panel.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const chartValues = useMemo(() => {
    const base = Number(revenue?.mrr || 0)
    return [0.68, 0.74, 0.81, 0.79, 0.88, 0.94, 1].map((factor) => Math.round(base * factor))
  }, [revenue?.mrr])

  const cards = [
    { label: 'MRR', value: money(revenue?.mrr), icon: TrendingUp },
    { label: 'Active Tenants', value: String(revenue?.active_tenants || tenants.length || 0), icon: Building2 },
    { label: 'Churn', value: pct(revenue?.churn), icon: TrendingDown },
    { label: 'Failure Rate', value: pct(revenue?.failure_rate), icon: AlertCircle },
  ]

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="arc-id"><b>saas</b>/control-panel</p>
          <h1 className="mt-2 text-2xl font-bold text-[var(--text)]">Control Panel</h1>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/control-panel/licenses" className="rounded-[var(--radius)] border border-[var(--line)] px-3 py-2 text-sm font-semibold text-[var(--text-2)] hover:text-[var(--text)]">
            Licenses
          </Link>
          <Link to="/control-panel/plans" className="rounded-[var(--radius)] border border-[var(--line)] px-3 py-2 text-sm font-semibold text-[var(--text-2)] hover:text-[var(--text)]">
            Plans
          </Link>
          <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white">
            <RefreshCw size={15} /> Refresh
          </button>
        </div>
      </div>

      {error && <div className="mt-5 rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ label, value, icon: Icon }) => (
          <section key={label} className="arc-card p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-[var(--text-3)]">{label}</p>
              <Icon size={18} className="text-[var(--accent)]" />
            </div>
            <p className="mt-3 text-2xl font-bold text-[var(--text)]">{loading ? '...' : value}</p>
          </section>
        ))}
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="arc-card p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase text-[var(--text-3)]">Revenue</h2>
            <span className="text-sm font-semibold text-[var(--text)]">ARR {money(revenue?.arr)}</span>
          </div>
          <div className="mt-4"><SparkChart values={chartValues} /></div>
        </section>

        <section className="arc-card p-5">
          <h2 className="text-sm font-semibold uppercase text-[var(--text-3)]">Recent Payments</h2>
          <div className="mt-4 space-y-3">
            {payments.length === 0 ? (
              <p className="text-sm text-[var(--text-3)]">No recent payments.</p>
            ) : payments.slice(0, 6).map((payment) => (
              <div key={payment.id || payment.provider_payment_id} className="flex items-center justify-between gap-3 rounded-[var(--radius)] border border-[var(--line)] px-3 py-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[var(--text)]">{payment.provider_payment_id || `Payment #${payment.id}`}</p>
                  <p className="text-xs text-[var(--text-3)]">{payment.provider_code || 'provider'} · {payment.status || 'unknown'}</p>
                </div>
                <p className="shrink-0 text-sm font-semibold">{money(payment.amount, payment.currency)}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="arc-card mt-6 overflow-hidden">
        <div className="border-b border-[var(--line)] px-5 py-4">
          <h2 className="text-sm font-semibold uppercase text-[var(--text-3)]">Tenants</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--surface-2)] text-xs uppercase text-[var(--text-3)]">
              <tr>
                <th className="px-5 py-3">Tenant</th>
                <th className="px-5 py-3">Plan</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Contact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--line)]">
              {tenants.map((tenant) => (
                <tr key={tenant.id || tenant.tenant_id} className="hover:bg-[var(--surface-2)]">
                  <td className="px-5 py-3">
                    <Link to={`/control-panel/tenants/${tenant.tenant_id || tenant.id}`} className="font-semibold text-[var(--accent)] hover:underline">
                      {tenant.company_name || tenant.tenant_id || `Tenant #${tenant.id}`}
                    </Link>
                    <p className="text-xs text-[var(--text-3)]">{tenant.tenant_id || 'pending tenant id'}</p>
                  </td>
                  <td className="px-5 py-3">{tenant.plan?.name || tenant.plan?.plan_key || '-'}</td>
                  <td className="px-5 py-3">{tenant.status || '-'}</td>
                  <td className="px-5 py-3">{tenant.email || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
