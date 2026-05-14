import { useState, useEffect, useCallback } from 'react'
import api from '../lib/api'
import { Search, Clock, User, ArrowRight, RefreshCw, Database, Plus, Edit2, Trash2 } from 'lucide-react'

interface LogEntry {
  id: number
  resource: string
  resource_id: number
  action: 'INSERT' | 'UPDATE' | 'DELETE'
  changes: Record<string, [any, any]> | null
  note: string | null
  user_id: number | null
  created_at: string
}

const ACTION_META = {
  INSERT: { label: 'Created', icon: Plus, color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  UPDATE: { label: 'Updated', icon: Edit2, color: 'bg-blue-100 text-blue-700 border-blue-200' },
  DELETE: { label: 'Deleted', icon: Trash2, color: 'bg-rose-100 text-rose-700 border-rose-200' },
}

function DiffCell({ from, to }: { from: any; to: any }) {
  const fmt = (v: any) => (v === null || v === undefined ? <span className="italic text-slate-400">null</span> : <span>{String(v)}</span>)
  return (
    <span className="flex items-center gap-1.5 text-xs">
      <span className="line-through text-slate-400">{fmt(from)}</span>
      <ArrowRight size={10} className="text-slate-400 shrink-0" />
      <span className="font-semibold text-slate-800">{fmt(to)}</span>
    </span>
  )
}

function LogCard({ entry }: { entry: LogEntry }) {
  const [open, setOpen] = useState(false)
  const meta = ACTION_META[entry.action] ?? ACTION_META.UPDATE
  const Icon = meta.icon
  const changes = entry.changes ?? {}
  const changedFields = Object.keys(changes)

  return (
    <div className="flex gap-4">
      {/* Timeline dot */}
      <div className="flex flex-col items-center">
        <div className={`w-9 h-9 rounded-xl border flex items-center justify-center shrink-0 ${meta.color}`}>
          <Icon size={16} />
        </div>
        <div className="w-px flex-1 bg-slate-200 mt-1" />
      </div>

      {/* Card */}
      <div className="mb-4 flex-1 min-w-0">
        <div
          className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden cursor-pointer hover:border-indigo-200 transition-all"
          onClick={() => changedFields.length > 0 && setOpen(o => !o)}
        >
          <div className="px-4 py-3 flex items-center gap-3 flex-wrap">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-lg border ${meta.color}`}>{meta.label}</span>
            <span className="font-semibold text-slate-700 text-sm">
              <span className="text-slate-400 font-normal">on </span>{entry.resource}
              <span className="text-slate-400 font-normal"> #{entry.resource_id}</span>
            </span>
            {entry.user_id && (
              <span className="flex items-center gap-1 text-xs text-slate-500">
                <User size={12} /> user #{entry.user_id}
              </span>
            )}
            <span className="ml-auto flex items-center gap-1 text-xs text-slate-400">
              <Clock size={11} />
              {new Date(entry.created_at).toLocaleString()}
            </span>
            {changedFields.length > 0 && (
              <span className="text-xs text-indigo-500 font-medium">{changedFields.length} field{changedFields.length !== 1 ? 's' : ''} changed</span>
            )}
          </div>

          {open && changedFields.length > 0 && (
            <div className="border-t border-slate-100 bg-slate-50 px-4 py-3">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-400 text-left">
                    <th className="pb-1.5 font-semibold w-1/4">Field</th>
                    <th className="pb-1.5 font-semibold">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {changedFields.map(field => (
                    <tr key={field} className="border-t border-slate-100">
                      <td className="py-1.5 pr-4 text-slate-500 font-mono">{field}</td>
                      <td className="py-1.5">
                        <DiffCell from={changes[field][0]} to={changes[field][1]} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const AuditLogs = () => {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [actionFilter, setActionFilter] = useState<string>('')

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const filters: any[] = []
      if (actionFilter) filters.push({ field: 'action', op: '=', value: actionFilter })
      const res = await api.get('/aras_activity_logs/', {
        params: {
          page,
          per_page: 30,
          search: search || undefined,
          filters: filters.length ? JSON.stringify(filters) : undefined,
          order_by: 'id',
          desc: true,
        }
      })
      setEntries(res.data.items ?? [])
      setTotalPages(res.data.pages ?? 1)
    } catch {
      setEntries([])
    } finally {
      setLoading(false)
    }
  }, [page, search, actionFilter])

  useEffect(() => { fetchLogs() }, [fetchLogs])
  useEffect(() => { setPage(1) }, [search, actionFilter])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">System Audit Trail</h1>
          <p className="text-slate-500 mt-1">Full change history — click any entry to expand the field diff.</p>
        </div>
        <button onClick={fetchLogs} className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-all">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex gap-3 flex-wrap items-center">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder="Search resource, user..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          {(['', 'INSERT', 'UPDATE', 'DELETE'] as const).map(a => (
            <button
              key={a}
              onClick={() => setActionFilter(a)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${actionFilter === a ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}
            >
              {a || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400 gap-3">
          <RefreshCw size={20} className="animate-spin" /> Loading audit trail...
        </div>
      ) : entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400">
          <Database size={40} strokeWidth={1} />
          <p>No audit records found.</p>
        </div>
      ) : (
        <div className="max-h-[calc(100vh-300px)] overflow-y-auto pr-1">
          {entries.map(e => <LogCard key={e.id} entry={e} />)}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2 pb-4">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                className="px-4 py-1.5 rounded-xl border border-slate-200 text-sm font-medium disabled:opacity-40 hover:bg-slate-50 transition-all">
                Prev
              </button>
              <span className="text-sm text-slate-500">Page {page} of {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                className="px-4 py-1.5 rounded-xl border border-slate-200 text-sm font-medium disabled:opacity-40 hover:bg-slate-50 transition-all">
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AuditLogs
