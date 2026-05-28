import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAras } from '../aras-core/hooks/useAras'
import { useAuthStore } from '../store/authStore'
import { Database, Plus, Trash2, DatabaseZap } from 'lucide-react'
import ArasTable from '../aras-core/components/ArasTable'

interface Tenant {
  tenant_id: string
  db_name: string
  created_at?: string
}

export default function TenantAdmin() {
  const { api, notify } = useAras()
  const user = useAuthStore((state: any) => state.user)
  
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  
  // Provision form state
  const [tenantId, setTenantId] = useState('')
  const [dbName, setDbName] = useState('')
  const [provisioning, setProvisioning] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const fetchTenants = async () => {
    try {
      setLoading(true)
      const res = await api.get('/tenants')
      setTenants(res.data.data || [])
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Failed to fetch tenants', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user?.is_admin) {
      fetchTenants()
    }
  }, [user])

  if (!user?.is_admin) {
    return <Navigate to="/" replace />
  }

  const handleProvision = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!tenantId) return
    
    setErrorMsg('')
    setProvisioning(true)
    try {
      await api.post('/tenants/provision', {
        tenant_id: tenantId,
        db_name: dbName || undefined
      })
      notify('Tenant provisioned successfully', 'success')
      setTenantId('')
      setDbName('')
      fetchTenants()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Provisioning failed')
    } finally {
      setProvisioning(false)
    }
  }

  const handleSeed = async (id: string) => {
    if (!window.confirm(`Are you sure you want to seed demo data for tenant '${id}'? This might take a moment.`)) return
    try {
      await api.post(`/tenants/${id}/seed`)
      notify(`Tenant ${id} seeded successfully`, 'success')
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Seeding failed', 'error')
    }
  }

  const handleRemove = async (id: string) => {
    if (!window.confirm(`CRITICAL WARNING: Are you sure you want to completely remove tenant '${id}'? This will drop the database if it is dedicated.`)) return
    try {
      await api.delete(`/tenants/${id}`)
      notify(`Tenant ${id} removed successfully`, 'success')
      fetchTenants()
    } catch (err: any) {
      notify(err.response?.data?.detail || 'Removal failed', 'error')
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[var(--app-text)]">Tenant Administration</h1>
        <p className="text-sm text-[var(--app-muted)] mt-1">Manage multi-tenant databases and provisioning</p>
      </div>

      <div className="bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm overflow-hidden">
        <div className="p-5 border-b border-[var(--app-border)] bg-[var(--app-panel-soft)]/50">
          <h2 className="text-sm font-bold text-[var(--app-text)] flex items-center gap-2">
            <Plus size={16} /> Provision New Tenant
          </h2>
        </div>
        <form onSubmit={handleProvision} className="p-5 space-y-4">
          {errorMsg && (
            <div className="p-3 text-sm text-red-700 bg-red-50 rounded-[var(--app-radius)] border border-red-200">
              {errorMsg}
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-[var(--app-muted)] uppercase tracking-wider mb-1.5">Tenant ID (Slug)</label>
              <input
                type="text"
                required
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                placeholder="e.g. acme-corp"
                className="w-full px-4 py-2.5 rounded-[var(--app-radius)] border border-[var(--app-border)] bg-[var(--app-panel)] text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[var(--app-muted)] uppercase tracking-wider mb-1.5">Database Name (Optional)</label>
              <input
                type="text"
                value={dbName}
                onChange={(e) => setDbName(e.target.value)}
                placeholder={`aras_tenant_${tenantId || '{tenant_id}'}`}
                className="w-full px-4 py-2.5 rounded-[var(--app-radius)] border border-[var(--app-border)] bg-[var(--app-panel)] text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
              />
            </div>
          </div>
          <div className="pt-2">
            <button
              type="submit"
              disabled={!tenantId || provisioning}
              className="px-4 py-2 bg-[var(--app-accent)] hover:bg-indigo-700 text-white text-sm font-semibold rounded-[var(--app-radius)] disabled:opacity-50 transition-colors"
            >
              {provisioning ? 'Provisioning...' : 'Provision Tenant'}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm overflow-hidden">
        <div className="p-5 border-b border-[var(--app-border)] bg-[var(--app-panel-soft)]/50 flex items-center justify-between">
          <h2 className="text-sm font-bold text-[var(--app-text)] flex items-center gap-2">
            <Database size={16} /> Active Tenants
          </h2>
          <button 
            type="button" 
            onClick={fetchTenants} 
            className="text-xs font-semibold text-[var(--app-accent)] hover:text-indigo-700"
          >
            Refresh List
          </button>
        </div>
        
        {(() => {
          // claude-sonnet-4-6
          const tenantColumns = [
            { key: 'tenant_id', label: 'Tenant ID', render: (v: string) => <span className="font-semibold text-[var(--app-text)]">{v}</span> },
            { key: 'db_name', label: 'DB Name', render: (v: string) => <span className="text-[var(--app-muted)] font-mono text-xs">{v}</span> },
            { key: 'created_at', label: 'Created', render: (v: string) => <span className="text-[var(--app-muted)]">{v ? new Date(v).toLocaleDateString() : 'N/A'}</span> },
            { key: 'actions', label: 'Actions', align: 'right' as const, render: (_: any, t: any) => (
              <div className="flex items-center justify-end gap-2">
                <button onClick={() => handleSeed(t.tenant_id)} className="p-1.5 text-[var(--app-muted)] hover:text-[var(--app-accent)] hover:bg-[var(--app-accent-glow)] rounded-[var(--app-radius)] transition-colors" title="Seed Demo Data"><DatabaseZap size={16} /></button>
                <button onClick={() => handleRemove(t.tenant_id)} className="p-1.5 text-[var(--app-muted)] hover:text-red-600 hover:bg-red-50 rounded-[var(--app-radius)] transition-colors" title="Remove Tenant"><Trash2 size={16} /></button>
              </div>
            )},
          ]
          return (
            <ArasTable
              columns={tenantColumns}
              rows={tenants}
              rowKey={(t) => t.tenant_id}
              loading={loading}
              emptyMessage="No tenants provisioned yet."
            />
          )
        })()}
      </div>
    </div>
  )
}
