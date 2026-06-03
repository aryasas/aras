import { useState } from 'react'
import api from '../lib/api'
import { Search, Clock, User, ArrowRight, RefreshCw, Database, Plus, Edit2, Trash2 } from 'lucide-react'
import Combobox from '../aras-core/components/Combobox'
import { useAsyncData } from '../hooks/useAsyncData'
import { fmtDateTime } from '../lib/formatters'

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
  const fmt = (v: any) => (v === null || v === undefined ? <span className="italic text-[var(--app-muted)]">null</span> : <span>{String(v)}</span>)
  return (
    <span className="flex items-center gap-1.5 text-xs">
      <span className="line-through text-[var(--app-muted)]">{fmt(from)}</span>
      <ArrowRight size={10} className="text-[var(--app-muted)] shrink-0" />
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
        <div className={`w-9 h-9 rounded-[var(--app-radius)] border flex items-center justify-center shrink-0 ${meta.color}`}>
          <Icon size={16} />
        </div>
        <div className="w-px flex-1 bg-slate-200 mt-1" />
      </div>

      {/* Card */}
      <div className="mb-4 flex-1 min-w-0">
        <div
          className="bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] border border-[var(--app-border)] shadow-sm overflow-hidden cursor-pointer hover:border-indigo-200 transition-all"
          onClick={() => changedFields.length > 0 && setOpen(o => !o)}
        >
          <div className="px-4 py-3 flex items-center gap-3 flex-wrap">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-[var(--app-radius)] border ${meta.color}`}>{meta.label}</span>
            <span className="font-semibold text-[var(--app-text)] text-sm">
              <span className="text-[var(--app-muted)] font-normal">on </span>{entry.resource}
              <span className="text-[var(--app-muted)] font-normal"> #{entry.resource_id}</span>
            </span>
            {entry.user_id && (
              <span className="flex items-center gap-1 text-xs text-[var(--app-muted)]">
                <User size={12} /> user #{entry.user_id}
              </span>
            )}
            <span className="ml-auto flex items-center gap-1 text-xs text-[var(--app-muted)]">
              <Clock size={11} />
              {fmtDateTime(entry.created_at)}
            </span>
            {changedFields.length > 0 && (
              <span className="text-xs text-indigo-500 font-medium">{changedFields.length} field{changedFields.length !== 1 ? 's' : ''} changed</span>
            )}
          </div>

          {open && changedFields.length > 0 && (
            <div className="border-t border-[var(--app-border)] bg-[var(--app-panel-soft)] px-4 py-3">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[var(--app-muted)] text-left">
                    <th className="pb-1.5 font-semibold w-1/4">Field</th>
                    <th className="pb-1.5 font-semibold">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {changedFields.map(field => (
                    <tr key={field} className="border-t border-[var(--app-border)]">
                      <td className="py-1.5 pr-4 text-[var(--app-muted)] font-mono">{field}</td>
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

// claude-sonnet-4-6
const AuditLogs = () => {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(30)
  const [actionFilter, setActionFilter] = useState<string>('')

  const { data, loading, reload } = useAsyncData<{ items: LogEntry[]; pages: number }>(async () => {
    const filters: any[] = []
    if (actionFilter) filters.push({ field: 'action', op: '=', value: actionFilter })
    const res = await api.get('/aras_activity_logs/', {
      params: {
        page,
        per_page: perPage,
        search: search || undefined,
        filters: filters.length ? JSON.stringify(filters) : undefined,
        order_by: 'id',
        desc: true,
      }
    })
    return res.data
  }, [page, perPage, search, actionFilter])

  const entries = data?.items ?? []
  const totalPages = data?.pages ?? 1

  const setSearchAndReset = (v: string) => { setSearch(v); setPage(1) }
  const setActionFilterAndReset = (v: string) => { setActionFilter(v); setPage(1) }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-extrabold text-[var(--app-text)] tracking-tight">System Audit Trail</h1>
          <p className="text-[var(--app-muted)] mt-1">Full change history — click any entry to expand the field diff.</p>
        </div>
        <button onClick={reload} className="flex items-center gap-2 px-4 py-2 bg-[var(--app-panel)] border border-[var(--app-border)] rounded-[var(--app-radius)] text-sm font-medium text-slate-600 hover:bg-[var(--app-panel-soft)] transition-all">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex gap-3 flex-wrap items-center">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--app-muted)]" />
          <input
            className="w-full pl-9 pr-4 py-2 bg-[var(--app-panel)] border border-[var(--app-border)] rounded-[var(--app-radius)] text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder="Search resource, user..."
            value={search}
            onChange={e => setSearchAndReset(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          {(['', 'INSERT', 'UPDATE', 'DELETE'] as const).map(a => (
            <button
              key={a}
              onClick={() => setActionFilterAndReset(a)}
              className={`px-3 py-1.5 rounded-[var(--app-radius)] text-xs font-bold border transition-all ${actionFilter === a ? 'bg-[var(--app-accent)] text-white border-indigo-600' : 'bg-[var(--app-panel)] border-[var(--app-border)] text-slate-600 hover:bg-[var(--app-panel-soft)]'}`}
            >
              {a || 'All'}
            </button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs font-medium text-[var(--app-muted)]">Page size:</span>
          <Combobox 
            options={[
              { label: '10', value: 10 },
              { label: '20', value: 20 },
              { label: '30', value: 30 },
              { label: '50', value: 50 },
              { label: '100', value: 100 },
              { label: 'All', value: 999999 }
            ]}
            value={perPage}
            onChange={(val) => { setPerPage(Number(val)); setPage(1); }}
          />
        </div>

      </div>

      {/* Timeline */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-[var(--app-muted)] gap-3">
          <RefreshCw size={20} className="animate-spin" /> Loading audit trail...
        </div>
      ) : entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-[var(--app-muted)]">
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
                className="px-4 py-1.5 rounded-[var(--app-radius)] border border-[var(--app-border)] text-sm font-medium disabled:opacity-40 hover:bg-[var(--app-panel-soft)] transition-all">
                Prev
              </button>
              <span className="text-sm text-[var(--app-muted)]">Page {page} of {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                className="px-4 py-1.5 rounded-[var(--app-radius)] border border-[var(--app-border)] text-sm font-medium disabled:opacity-40 hover:bg-[var(--app-panel-soft)] transition-all">
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
