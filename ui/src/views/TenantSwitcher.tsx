import { useEffect, useMemo, useState } from 'react'
import { Building2, RefreshCw } from 'lucide-react'
import api from '../lib/api'
import { useTenant } from '../context/TenantContext'

const DEV_MULTI_TENANT = import.meta.env.VITE_DEV_MULTI_TENANT === 'true'

interface TenantRecord {
  tenant_id?: string
  tenantId?: string
  id?: string
  name?: string
  meta?: {
    label?: string
    name?: string
  }
}

function tenantKey(tenant: TenantRecord) {
  return tenant.tenant_id || tenant.tenantId || tenant.id || ''
}

function tenantLabel(tenant: TenantRecord) {
  return tenant.meta?.label || tenant.meta?.name || tenant.name || tenantKey(tenant)
}

function normalizeTenants(payload: unknown): TenantRecord[] {
  if (Array.isArray(payload)) return payload
  if (typeof payload === 'object' && payload !== null && 'items' in payload) {
    const items = (payload as { items?: unknown }).items
    if (Array.isArray(items)) return items
  }
  return []
}

export default function TenantSwitcher() {
  const { tenantId, setTenantId } = useTenant()
  const [tenants, setTenants] = useState<TenantRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedTenant = useMemo(
    () => tenants.find((tenant) => tenantKey(tenant) === tenantId),
    [tenantId, tenants],
  )

  const fetchTenants = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/tenants', { baseURL: '/api' })
      setTenants(normalizeTenants(response.data))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tenants')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (DEV_MULTI_TENANT) fetchTenants()
  }, [])

  if (!DEV_MULTI_TENANT) return null

  return (
    <div className="lg:col-span-3 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
            <Building2 size={22} />
          </div>
          <div>
            <h2 className="text-lg font-black text-slate-900">Tenant Context</h2>
            <p className="text-sm text-slate-500 font-medium">
              Active tenant: {selectedTenant ? tenantLabel(selectedTenant) : tenantId || 'None selected'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={tenantId}
            onChange={(event) => setTenantId(event.target.value)}
            className="min-w-56 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
          >
            <option value="">Select tenant</option>
            {tenants.map((tenant) => {
              const key = tenantKey(tenant)
              if (!key) return null
              return (
                <option key={key} value={key}>
                  {tenantLabel(tenant)}
                </option>
              )
            })}
          </select>

          <button
            type="button"
            onClick={fetchTenants}
            disabled={loading}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-600 transition hover:bg-slate-100 disabled:opacity-50"
            title="Refresh tenants"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}
    </div>
  )
}
