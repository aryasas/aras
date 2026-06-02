// claude-opus-4-7
// ARC background tasks: enqueue + poll status against /dev/tasks/*.
import { useEffect, useState } from 'react'
import { Activity, Play, RefreshCw, Search, Copy, Trash2 } from 'lucide-react'
import api from '../lib/api'
import { useUIStore } from '../store/uiStore'
import { EmptyState } from '../components/EmptyState'

interface TaskStatus {
  task_id: string
  status?: string
  result?: unknown
  error?: string | null
  ready?: boolean
  [k: string]: unknown
}

interface TrackedTask {
  id: string
  name: string
  enqueuedAt: number
  status?: TaskStatus
}

const STORE_KEY = 'aras.bgtasks.tracked'

function loadTracked(): TrackedTask[] {
  try { return JSON.parse(localStorage.getItem(STORE_KEY) || '[]') } catch { return [] }
}
function saveTracked(items: TrackedTask[]) {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(items.slice(0, 50))) } catch { /* ignore */ }
}

const statusTone = (s?: string): string => {
  const v = (s || '').toLowerCase()
  if (v === 'success' || v === 'finished' || v === 'done') return 'var(--success, #2e7d32)'
  if (v === 'failed' || v === 'error') return 'var(--danger, #c62828)'
  if (v === 'started' || v === 'running' || v === 'queued' || v === 'pending') return 'var(--accent)'
  return 'var(--text-3)'
}

export default function BackgroundTasks() {
  const setPageTitle = useUIStore((s) => s.setPageTitle)
  const [tracked, setTracked] = useState<TrackedTask[]>(() => loadTracked())
  const [taskName, setTaskName] = useState('')
  const [argsText, setArgsText] = useState('')
  const [kwargsText, setKwargsText] = useState('')
  const [lookup, setLookup] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  useEffect(() => {
    setPageTitle('Background Tasks', 'Enqueue and inspect async jobs.', 'DEV')
    return () => setPageTitle('', '', '')
  }, [setPageTitle])

  useEffect(() => { saveTracked(tracked) }, [tracked])

  const refreshOne = async (id: string) => {
    try {
      const res = await api.get(`/dev/tasks/${encodeURIComponent(id)}/status`)
      setTracked((prev) => prev.map((t) => t.id === id ? { ...t, status: { task_id: id, ...res.data } } : t))
    } catch (e: any) {
      setTracked((prev) => prev.map((t) => t.id === id ? { ...t, status: { task_id: id, status: 'error', error: e?.response?.data?.detail || e.message } } : t))
    }
  }

  const refreshAll = async () => { for (const t of tracked) await refreshOne(t.id) }

  const enqueue = async () => {
    if (!taskName.trim()) { setMessage({ kind: 'err', text: 'Task name required' }); return }
    let args: unknown[] = []
    let kwargs: Record<string, unknown> = {}
    try { if (argsText.trim()) args = JSON.parse(argsText) } catch { setMessage({ kind: 'err', text: 'Args must be JSON array' }); return }
    try { if (kwargsText.trim()) kwargs = JSON.parse(kwargsText) } catch { setMessage({ kind: 'err', text: 'Kwargs must be JSON object' }); return }
    if (!Array.isArray(args)) { setMessage({ kind: 'err', text: 'Args must be a JSON array' }); return }
    setBusy(true)
    try {
      const res = await api.post('/dev/tasks/enqueue', { task_name: taskName.trim(), args, kwargs })
      const id = String(res.data?.task_id || '')
      if (!id) throw new Error('No task_id returned')
      setTracked((prev) => [{ id, name: taskName.trim(), enqueuedAt: Date.now() }, ...prev.filter((t) => t.id !== id)])
      setMessage({ kind: 'ok', text: `Enqueued ${id}` })
      setTaskName(''); setArgsText(''); setKwargsText('')
    } catch (e: any) {
      setMessage({ kind: 'err', text: e?.response?.data?.detail || e.message || 'Enqueue failed' })
    } finally {
      setBusy(false)
    }
  }

  const lookupTask = async () => {
    const id = lookup.trim()
    if (!id) return
    setTracked((prev) => prev.some((t) => t.id === id) ? prev : [{ id, name: '(lookup)', enqueuedAt: Date.now() }, ...prev])
    setLookup('')
    await refreshOne(id)
  }

  const forgetTask = (id: string) => setTracked(prev => prev.filter(t => t.id !== id))

  return (
    <div className="arc flex flex-col gap-5">
      <div className="arc-card arc-dotgrid p-6 flex items-center gap-5" style={{ background: 'var(--bg-2)' }}>
        <div className="grid place-items-center w-14 h-14 rounded-[var(--radius-lg)]"
             style={{ background: 'color-mix(in oklch, var(--accent) 18%, var(--surface))', color: 'var(--accent)', border: '1px solid color-mix(in oklch, var(--accent) 35%, var(--line))' }}>
          <Activity size={26} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="arc-id"><b>dev</b>/background-tasks</div>
          <h1 className="text-[20px] font-semibold text-[var(--text)] tracking-tight mt-0.5">Background Tasks</h1>
          <div className="arc-dim text-[12px] mt-0.5">{tracked.length} tracked · status cached in browser</div>
        </div>
        <button onClick={refreshAll} className="arc-btn" disabled={!tracked.length}>
          <RefreshCw size={14} /> Refresh all
        </button>
      </div>

      <section className="arc-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
          <span className="arc-id"><b>enqueue</b></span>
        </div>
        <div className="p-4 flex flex-col gap-3">
          <input className="arc-input" placeholder="task_name (e.g. apps.report.recompute)"
                 value={taskName} onChange={(e) => setTaskName(e.target.value)} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <textarea className="arc-input font-mono text-[12px]" rows={3} placeholder='args (JSON array, e.g. [1, "x"])'
                      value={argsText} onChange={(e) => setArgsText(e.target.value)} />
            <textarea className="arc-input font-mono text-[12px]" rows={3} placeholder='kwargs (JSON object, e.g. {"force": true})'
                      value={kwargsText} onChange={(e) => setKwargsText(e.target.value)} />
          </div>
          <div className="flex items-center gap-3">
            <button className="arc-btn primary" onClick={enqueue} disabled={busy}>
              <Play size={14} /> Enqueue
            </button>
            {message && (
              <span className="text-[12px]" style={{ color: message.kind === 'ok' ? 'var(--success, #2e7d32)' : 'var(--danger, #c62828)' }}>
                {message.text}
              </span>
            )}
          </div>
        </div>
      </section>

      <section className="arc-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
          <span className="arc-id"><b>lookup</b></span>
        </div>
        <div className="p-4 flex items-center gap-2">
          <input className="arc-input flex-1" placeholder="task_id"
                 value={lookup} onChange={(e) => setLookup(e.target.value)}
                 onKeyDown={(e) => { if (e.key === 'Enter') lookupTask() }} />
          <button className="arc-btn" onClick={lookupTask}><Search size={14} /> Lookup</button>
        </div>
      </section>

      <section className="arc-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line)]" style={{ background: 'var(--surface-2)' }}>
          <span className="arc-id"><b>tracked</b></span>
          <span className="arc-id arc-dim2">{tracked.length}</span>
        </div>
        {tracked.length === 0 && <EmptyState title="No tracked tasks" description="Enqueue a task or look one up by ID." />}
        {tracked.map((t) => (
          <div key={t.id} className="flex items-center gap-3 px-4 py-2.5 border-t border-[var(--line)] hover:bg-[var(--surface-2)] transition-colors">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[13px] font-medium text-[var(--text)] truncate">{t.name}</span>
                <span className="arc-id arc-dim2 truncate">{t.id}</span>
              </div>
              <div className="arc-dim text-[11px] mt-0.5">
                enqueued {new Date(t.enqueuedAt).toLocaleString()}
                {t.status?.error && <> · <span style={{ color: 'var(--danger, #c62828)' }}>{t.status.error}</span></>}
              </div>
            </div>
            <span className="arc-id shrink-0" style={{ color: statusTone(t.status?.status) }}>
              {t.status?.status || 'unknown'}
            </span>
            <button className="arc-btn" title="Copy task JSON" onClick={() => navigator.clipboard.writeText(JSON.stringify(t, null, 2))}>
              <Copy size={13} />
            </button>
            <button className="arc-btn" onClick={() => refreshOne(t.id)}>
              <RefreshCw size={13} />
            </button>
            <button className="arc-btn" title="Forget tracked task" onClick={() => forgetTask(t.id)}>
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </section>
    </div>
  )
}
