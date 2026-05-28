import { useState, useEffect } from 'react'
import { Globe, Search, Shield, ChevronLeft } from 'lucide-react'
import api from '../lib/api'
import { useNavigate } from 'react-router-dom'
import ArasTable from '../aras-core/components/ArasTable'

interface RouteInfo {
  path: string
  name: string
  methods: string[]
}

export default function InspectRoutes() {
  const [routes, setRoutes] = useState<RouteInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/dev/inspect/routes')
      .then(res => setRoutes(res.data))
      .catch(err => console.error('Failed to fetch routes', err))
      .finally(() => setLoading(false))
  }, [])

  const filteredRoutes = routes.filter(r => 
    r.path.toLowerCase().includes(search.toLowerCase()) || 
    (r.name && r.name.toLowerCase().includes(search.toLowerCase()))
  ).sort((a, b) => a.path.localeCompare(b.path))

  return (
    <div className="p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/dev')}
            className="p-3 bg-[var(--app-panel)] border border-[var(--app-border)] rounded-[var(--app-radius-lg)] text-slate-600 hover:bg-[var(--app-panel-soft)] transition-all shadow-sm"
          >
            <ChevronLeft size={20} />
          </button>
          <div>
            <h1 className="text-3xl font-black text-[var(--app-text)] tracking-tight flex items-center gap-3">
              <Globe className="text-[var(--app-accent)]" />
              API Route Map
            </h1>
            <p className="text-[var(--app-muted)] mt-1 font-medium">Full manifest of registered endpoints in the framework.</p>
          </div>
        </div>
        
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" size={18} />
          <input 
            type="text"
            placeholder="Search routes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-12 pr-6 py-3 bg-[var(--app-panel)] border border-[var(--app-border)] rounded-[var(--app-radius-lg)] w-80 focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-bold text-[var(--app-text)] shadow-sm"
          />
        </div>
      </div>

      {/* claude-sonnet-4-6 */}
      {(() => {
        const routeColumns = [
          { key: 'methods', label: 'Methods', width: 128, render: (_: any, route: RouteInfo) => (
            <div className="flex flex-wrap gap-1">
              {route.methods.filter(m => m !== 'OPTIONS' && m !== 'HEAD').map(m => (
                <span key={m} className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase ${
                  m === 'GET' ? 'bg-blue-100 text-blue-700' :
                  m === 'POST' ? 'bg-emerald-100 text-emerald-700' :
                  m === 'PUT' ? 'bg-amber-100 text-amber-700' :
                  m === 'DELETE' ? 'bg-rose-100 text-rose-700' :
                  'bg-[var(--app-panel-soft)] text-[var(--app-text)]'
                }`}>{m}</span>
              ))}
            </div>
          )},
          { key: 'path', label: 'Endpoint Path', render: (_: any, route: RouteInfo) => (
            <code className="text-[var(--app-accent)] font-bold text-sm bg-[var(--app-accent-glow)]/50 px-2 py-1 rounded-[var(--app-radius)]">{route.path}</code>
          )},
          { key: 'name', label: 'Internal Name', render: (_: any, route: RouteInfo) => (
            <span className="text-sm font-bold text-[var(--app-muted)] italic">{route.name || '-'}</span>
          )},
          { key: 'scope', label: 'Security Scope', align: 'right' as const, render: (_: any, route: RouteInfo) => (
            route.path.includes('/dev/') ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-600 text-[10px] font-black uppercase rounded-full border border-amber-100"><Shield size={12} /> Maintenance</span>
            ) : route.path.includes('/auth/') ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-600 text-[10px] font-black uppercase rounded-full border border-blue-100">Identity</span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-[var(--app-panel-soft)] text-[var(--app-muted)] text-[10px] font-black uppercase rounded-full border border-[var(--app-border)]">Resource</span>
            )
          )},
        ]
        return (
          <div className="bg-[var(--app-panel)] rounded-[2.5rem] border border-[var(--app-border)] shadow-sm overflow-hidden">
            <ArasTable
              columns={routeColumns}
              rows={filteredRoutes}
              rowKey={(_, i) => i}
              loading={loading}
              loadingRows={8}
              emptyMessage="No routes found matching your search."
            />
          </div>
        )
      })()}
    </div>
  )
}
