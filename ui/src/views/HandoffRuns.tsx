// claude-opus-4-7
// ARC handoff runs viewer: lists agent handoff records from /dev/dev_handoff_runs.
import { useEffect } from 'react'
import { History, RefreshCw, GitBranch } from 'lucide-react'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'
import { useAsyncData } from '../hooks/useAsyncData'
import { StatusBadge } from '../components/StatusBadge'

interface HandoffRun {
  id: number
  agent?: string | null
  task?: string | null
  status?: string | null
  started_at?: string | null
  finished_at?: string | null
  summary?: string | null
  branch?: string | null
  [k: string]: unknown
}

const fmt = (v?: string | null) => (v ? new Date(v).toLocaleString() : '—')


export default function HandoffRuns() {
  const setPageTitle = useUIStore((s) => s.setPageTitle)

  const { data, loading, error, reload } = useAsyncData<{ items: HandoffRun[] }>(
    () => api.get('/dev/dev_handoff_runs', { params: { limit: 100, sort: 'id', order: 'desc' } }).then((r) => r.data),
  )
  const runs = data?.items ?? []

  useEffect(() => {
    setPageTitle('Agent Handoff Runs', 'History of multi-agent task executions.', 'DEV')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  return (
    <div className="arc flex flex-col gap-5">
      <div className="arc-card arc-dotgrid p-6 flex items-center gap-5" style={{ background: 'var(--bg-2)' }}>
        <div className="grid place-items-center w-14 h-14 rounded-[var(--radius-lg)]"
             style={{ background: 'color-mix(in oklch, var(--accent) 18%, var(--surface))', color: 'var(--accent)', border: '1px solid color-mix(in oklch, var(--accent) 35%, var(--line))' }}>
          <History size={26} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="arc-id"><b>dev</b>/handoff-runs</div>
          <h1 className="text-[20px] font-semibold text-[var(--text)] tracking-tight mt-0.5">Agent Handoff Runs</h1>
          <div className="arc-dim text-[12px] mt-0.5">{runs.length} records · latest first</div>
        </div>
        <button onClick={reload} className="arc-btn" disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {loading && <LoadingState label="Loading handoff runs..." className="arc-card border-dashed" />}
      {!loading && error && <EmptyState title="Failed to load" description={error} />}
      {!loading && !error && runs.length === 0 && <EmptyState title="No handoff runs yet" description="Runs created via the multi-agent CLI will appear here." />}

      {!loading && !error && runs.length > 0 && (
        <section className="arc-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
            <span className="arc-id"><b>runs</b></span>
            <span className="arc-id arc-dim2">{runs.length}</span>
          </div>
          {runs.map((r) => (
            <div key={r.id} className="flex items-start gap-3 px-4 py-2.5 border-t border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors">
              <GitBranch size={14} className="text-[var(--text-3)] shrink-0 mt-0.5" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="arc-id"><b>#{r.id}</b></span>
                  {r.agent && <span className="text-[13px] font-medium text-[var(--text)] truncate">{r.agent}</span>}
                  {r.branch && <span className="arc-id arc-dim2">{r.branch}</span>}
                </div>
                {r.task && <div className="text-[12.5px] text-[var(--text)] mt-0.5 truncate">{r.task}</div>}
                {r.summary && <div className="arc-dim text-[11.5px] mt-0.5 line-clamp-2">{r.summary}</div>}
                <div className="arc-dim text-[11px] mt-1">
                  started {fmt(r.started_at)} · finished {fmt(r.finished_at)}
                </div>
              </div>
              <StatusBadge status={r.status} />
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
