import { useEffect, useState } from 'react'
import { CheckCircle2, KeyRound, Plus, RefreshCw, RotateCw, XCircle } from 'lucide-react'
import api from '../../lib/api'
import { useAras } from '../../aras-core/hooks/useAras'
import { useUIStore } from '../../store/uiStore'

interface LicenseRow {
  tenant_id?: string
  tenant?: string
  company_name?: string
  plan?: string
  plan_key?: string
  status?: string
  issued_at?: string | null
  issued?: string | null
  expires_at?: string | null
  expiry_date?: string | null
}

const labelDate = (value?: string | null) => {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('id-ID')
}

export default function LicensesPanel() {
  const { confirm } = useAras()
  const showPrompt = useUIStore((state) => state.showPrompt)
  const [licenses, setLicenses] = useState<LicenseRow[]>([])
  const [loading, setLoading] = useState(true)
  const [busyKey, setBusyKey] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/saas/control-panel/licenses')
      setLicenses(Array.isArray(response.data) ? response.data : [])
    } catch (err: any) {
      setError(err.message || 'Failed to load licenses.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const issue = async (tenantId: string) => {
    showPrompt(`Issue license for ${tenantId}`, 'Enter a plan key for this tenant.', async (plan) => {
      if (!plan.trim()) return
      setBusyKey(`issue:${tenantId}`)
      setError(null)
      try {
        await api.post('/saas/control-panel/licenses/issue', { tenant_id: tenantId, plan: plan.trim() })
        await load()
      } catch (err: any) {
        setError(err.message || 'Failed to issue license.')
      } finally {
        setBusyKey(null)
      }
    }, { defaultValue: 'basic', placeholder: 'basic', confirmLabel: 'Issue' })
  }

  const renew = async (tenantId: string) => {
    setBusyKey(`renew:${tenantId}`)
    setError(null)
    try {
      await api.post(`/saas/control-panel/licenses/${tenantId}/renew`)
      await load()
    } catch (err: any) {
      setError(err.message || 'Failed to renew license.')
    } finally {
      setBusyKey(null)
    }
  }

  const revoke = async (tenantId: string) => {
    const confirmed = await confirm({
      title: 'Revoke license?',
      message: `Revoke license for ${tenantId}?`,
      confirmText: 'Revoke',
      type: 'danger',
    })
    if (!confirmed) return
    setBusyKey(`revoke:${tenantId}`)
    setError(null)
    try {
      await api.post(`/saas/control-panel/licenses/${tenantId}/revoke`)
      await load()
    } catch (err: any) {
      setError(err.message || 'Failed to revoke license.')
    } finally {
      setBusyKey(null)
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="arc-id"><b>control-panel</b>/licenses</p>
          <h1 className="mt-2 text-2xl font-bold text-[var(--text)]">Licenses</h1>
        </div>
        <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-[var(--radius)] bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {error && <div className="mt-5 rounded-[var(--radius)] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</div>}

      <section className="arc-card mt-6 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--surface-2)] text-xs uppercase text-[var(--text-3)]">
              <tr>
                <th className="px-5 py-3">Tenant</th>
                <th className="px-5 py-3">Plan</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Issued</th>
                <th className="px-5 py-3">Expires</th>
                <th className="px-5 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--line)]">
              {loading ? (
                <tr><td colSpan={6} className="px-5 py-6 text-[var(--text-3)]">Loading licenses...</td></tr>
              ) : licenses.length === 0 ? (
                <tr><td colSpan={6} className="px-5 py-6 text-[var(--text-3)]">No licenses found.</td></tr>
              ) : licenses.map((license) => {
                const tenantId = license.tenant_id || license.tenant || ''
                const status = license.status || 'unknown'
                const valid = ['active', 'valid'].includes(status.toLowerCase())
                return (
                  <tr key={tenantId} className="hover:bg-[var(--surface-2)]">
                    <td className="px-5 py-3">
                      <p className="font-semibold text-[var(--text)]">{license.company_name || tenantId}</p>
                      <p className="text-xs text-[var(--text-3)]">{tenantId || '-'}</p>
                    </td>
                    <td className="px-5 py-3">{license.plan || license.plan_key || '-'}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${valid ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' : 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'}`}>
                        {valid ? <CheckCircle2 size={13} /> : <KeyRound size={13} />}
                        {status}
                      </span>
                    </td>
                    <td className="px-5 py-3">{labelDate(license.issued_at || license.issued)}</td>
                    <td className="px-5 py-3">{labelDate(license.expires_at || license.expiry_date)}</td>
                    <td className="px-5 py-3">
                      <div className="flex flex-wrap gap-2">
                        <button type="button" onClick={() => issue(tenantId)} disabled={!tenantId || busyKey === `issue:${tenantId}`} className="inline-flex items-center gap-1 rounded-[var(--radius)] border border-[var(--line)] px-2 py-1 text-xs font-semibold text-[var(--text-2)] hover:text-[var(--text)] disabled:opacity-50">
                          <Plus size={13} /> Issue
                        </button>
                        <button type="button" onClick={() => renew(tenantId)} disabled={!tenantId || busyKey === `renew:${tenantId}`} className="inline-flex items-center gap-1 rounded-[var(--radius)] border border-[var(--line)] px-2 py-1 text-xs font-semibold text-[var(--text-2)] hover:text-[var(--text)] disabled:opacity-50">
                          <RotateCw size={13} /> Renew
                        </button>
                        <button type="button" onClick={() => revoke(tenantId)} disabled={!tenantId || busyKey === `revoke:${tenantId}`} className="inline-flex items-center gap-1 rounded-[var(--radius)] border border-red-200 px-2 py-1 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">
                          <XCircle size={13} /> Revoke
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
