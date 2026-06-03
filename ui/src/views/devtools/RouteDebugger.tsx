import { useEffect, useMemo, useState } from 'react'
import { Copy, ExternalLink, RefreshCw, Route, Search } from 'lucide-react'
import api from '../../lib/api'
import { getApiDocsUrl } from '../../lib/apiDocs'
import { devApi } from './devApi'

type RouteRow = {
  path: string
  name: string
  methods: string[]
  tags: string[]
  summary?: string
  endpoint?: string
  auth?: string
}

const methodClass = (method: string) => method === 'GET'
  ? 'bg-emerald-100 text-emerald-700'
  : method === 'POST'
    ? 'bg-blue-100 text-blue-700'
    : method === 'DELETE'
      ? 'bg-red-100 text-red-700'
      : 'bg-amber-100 text-amber-700'

export default function RouteDebugger() {
  const [routes, setRoutes] = useState<RouteRow[]>([])
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<RouteRow | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<RouteRow[]>(devApi.inspectRoutes)
      setRoutes(res.data)
      setSelected(res.data.find(row => row.path.startsWith('/api/v1/dev')) || res.data[0] || null)
    } catch (e: any) {
      setError(e?.message || 'Route inspector unavailable.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load().catch(() => {}) }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return routes.filter(route => !q || `${route.path} ${route.name} ${(route.tags || []).join(' ')} ${route.endpoint}`.toLowerCase().includes(q))
  }, [routes, query])

  const copy = async (value: string) => {
    await navigator.clipboard?.writeText(value)
  }

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(360px,520px)_1fr]">
      <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)]">
        <div className="border-b border-[var(--line)] bg-[var(--surface-2)] p-3">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm font-black text-[var(--text)]"><Route size={16} /> Route Debugger</div>
            <button onClick={load} className="arc-btn h-8 text-xs" disabled={loading}>
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
          <div className="relative">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search path, tag, endpoint" className="arc-input h-9 pl-9 text-xs" />
          </div>
        </div>
        {error && <div className="m-3 rounded-[var(--radius)] border border-red-200 bg-red-50 px-3 py-2 text-sm font-bold text-red-700">{error}</div>}
        <div className="max-h-[620px] overflow-auto">
          {filtered.map(route => (
            <button
              key={`${route.path}:${route.methods?.join(',')}`}
              onClick={() => setSelected(route)}
              className={`w-full border-b border-[var(--line)] px-4 py-3 text-left hover:bg-[var(--surface-2)] ${selected === route ? 'bg-[var(--accent)]/10' : ''}`}
            >
              <div className="flex min-w-0 items-center gap-2">
                <div className="flex shrink-0 gap-1">
                  {(route.methods || []).filter(method => method !== 'HEAD').map(method => (
                    <span key={method} className={`rounded px-1.5 py-0.5 text-[9px] font-black ${methodClass(method)}`}>{method}</span>
                  ))}
                </div>
                <code className="truncate text-xs font-bold text-[var(--accent)]">{route.path}</code>
              </div>
              <div className="mt-1 truncate text-[11px] font-semibold text-[var(--text-3)]">{route.endpoint || route.name}</div>
            </button>
          ))}
          {!filtered.length && <div className="py-12 text-center text-sm text-[var(--text-3)]">No matching routes.</div>}
        </div>
      </section>

      <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)]">
        {!selected ? (
          <div className="py-16 text-center text-sm text-[var(--text-3)]">Select a route.</div>
        ) : (
          <div className="space-y-5 p-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap gap-1">
                  {(selected.methods || []).filter(method => method !== 'HEAD').map(method => (
                    <span key={method} className={`rounded px-2 py-1 text-[10px] font-black ${methodClass(method)}`}>{method}</span>
                  ))}
                </div>
                <code className="mt-3 block break-all text-base font-black text-[var(--text)]">{selected.path}</code>
                {selected.summary && <p className="mt-2 text-sm text-[var(--text-3)]">{selected.summary}</p>}
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => copy(selected.path)} className="arc-btn h-9 text-xs"><Copy size={13} /> Copy path</button>
                <a href={getApiDocsUrl()} target="_blank" rel="noopener noreferrer" className="arc-btn h-9 text-xs"><ExternalLink size={13} /> Swagger</a>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Fact label="Name" value={selected.name || '-'} />
              <Fact label="Auth" value={selected.auth || '-'} />
              <Fact label="Tags" value={(selected.tags || []).join(', ') || '-'} />
              <Fact label="Endpoint" value={selected.endpoint || '-'} mono />
            </div>

            <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-4">
              <div className="text-[10px] font-black uppercase tracking-[0.16em] text-[var(--text-3)]">Debug Flow</div>
              <div className="mt-3 grid gap-2 text-sm text-[var(--text-2)]">
                <p>1. Copy the route path or open Swagger.</p>
                <p>2. Use the Test Lab tab to run the operation with the current login token.</p>
                <p>3. Watch Timeline and Logs while reproducing the request.</p>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

function Fact({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="min-w-0 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] p-3">
      <div className="text-[10px] font-black uppercase tracking-[0.14em] text-[var(--text-3)]">{label}</div>
      <div className={`mt-1 truncate text-sm font-bold text-[var(--text)] ${mono ? 'font-mono' : ''}`} title={value}>{value}</div>
    </div>
  )
}
