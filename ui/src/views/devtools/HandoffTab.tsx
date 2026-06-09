import { useEffect, useState } from 'react'
import { GitBranch, RefreshCw, X } from 'lucide-react'
import api from '../../lib/api'
import ArasTable from '../../aras-core/components/ArasTable'
import { useAras } from '../../aras-core/hooks/useAras'
import { devApi } from './devApi'

interface HandoffRun {
  id: number
  agent: string
  task: string
  status: string
  started_at: string
  finished_at: string
  summary: string
  branch: string
}

export default function HandoffTab() {
  const [handoffRuns, setHandoffRuns] = useState<HandoffRun[]>([])
  const [selectedRun, setSelectedRun] = useState<HandoffRun | null>(null)
  const [loadingHandoff, setLoadingHandoff] = useState(false)
  const { notify } = useAras()

  const fetchHandoffRuns = async () => {
    setLoadingHandoff(true)
    try {
      const res = await api.get(devApi.handoffRuns, { params: { limit: 50, sort: 'id', order: 'desc' } })
      setHandoffRuns(res.data.items || res.data || [])
    } catch {
      notify('Failed to load handoff runs', 'error')
    } finally {
      setLoadingHandoff(false)
    }
  }

  useEffect(() => {
    fetchHandoffRuns()
  }, [])

  const handoffColumns = [
    { key: 'started_at', label: 'Started', render: (v: string) => <span className="whitespace-nowrap font-mono text-xs text-[var(--text-3)]">{String(v || '').slice(0, 16).replace('T', ' ')}</span> },
    { key: 'agent', label: 'Agent', render: (v: string) => <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700">{v || '—'}</span> },
    { key: 'task', label: 'Task', render: (v: string) => <span className="block max-w-xs truncate font-semibold text-[var(--text)]">{v}</span> },
    { key: 'branch', label: 'Branch', render: (v: string) => <code className="font-mono text-xs text-[var(--text-2)]">{v || '—'}</code> },
    { key: 'status', label: 'Status', render: (v: string) => <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${v === 'success' ? 'bg-emerald-100 text-emerald-700' : v === 'error' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{v}</span> },
    { key: 'finished_at', label: 'Finished', render: (v: string) => <span className="whitespace-nowrap font-mono text-xs text-[var(--text-3)]">{v ? String(v).slice(0, 16).replace('T', ' ') : '—'}</span> },
  ]

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-black text-[var(--text)]">Handoff Run History</h2>
          <p className="mt-1 text-sm text-[var(--text-3)]">All AI agent code generation runs.</p>
        </div>
        <button
          onClick={fetchHandoffRuns}
          className="flex items-center gap-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface-2)] px-4 py-2 text-sm font-semibold transition-all hover:bg-[var(--surface)]"
        >
          <RefreshCw size={13} className={loadingHandoff ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {loadingHandoff ? (
        <div className="py-16 text-center text-[var(--text-3)]">Loading...</div>
      ) : handoffRuns.length === 0 ? (
        <div className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-2)] py-16 text-center">
          <GitBranch size={36} className="mx-auto mb-4 text-[var(--muted)]" />
          <p className="font-semibold text-[var(--text-2)]">No handoff runs yet.</p>
          <p className="mt-1 text-sm text-[var(--text-3)]">Runs will appear here after <code className="font-mono">python tools/multi_agent.py</code> completes.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)]">
          <ArasTable columns={handoffColumns} rows={handoffRuns} rowKey={(run) => run.id} onRowClick={(run) => setSelectedRun(run)} />
        </div>
      )}

      {selectedRun && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/30" onClick={() => setSelectedRun(null)}>
          <div
            className="h-full w-full max-w-3xl overflow-y-auto border-l border-[var(--line)] bg-[var(--surface)] shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="sticky top-0 flex items-start justify-between gap-4 border-b border-[var(--line)] bg-[var(--surface)]/95 px-6 py-4 backdrop-blur">
              <div>
                <h3 className="text-lg font-black text-[var(--text)]">{selectedRun.task}</h3>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-[var(--text-3)]">
                  <span className="font-mono">{String(selectedRun.started_at || '').slice(0, 16).replace('T', ' ')}</span>
                  <span className="rounded-full bg-indigo-50 px-2 py-0.5 font-bold text-indigo-700">{selectedRun.agent}</span>
                  {selectedRun.branch && <code className="font-mono">{selectedRun.branch}</code>}
                  <span className={`rounded-full px-2 py-0.5 font-bold ${selectedRun.status === 'success' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{selectedRun.status}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedRun(null)}
                className="rounded-[var(--radius)] p-2 text-[var(--text-3)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
              >
                <X size={16} />
              </button>
            </div>
            <div className="p-6">
              <div className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--text-3)]">Summary</div>
              <pre className="max-h-[60rem] overflow-x-auto overflow-y-auto whitespace-pre-wrap rounded-[var(--radius)] bg-slate-950 p-4 text-xs text-slate-200">{selectedRun.summary || 'No summary captured.'}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
