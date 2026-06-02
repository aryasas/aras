import { useEffect, useState } from 'react'
import { Activity, RefreshCw } from 'lucide-react'
import api from '../../lib/api'
import { devApi } from './devApi'

type RequestRow = { ts: number; method: string; path: string; status: number; ms: number }
type Metrics = { total_requests: number; total_errors: number; error_rate: number; rate_per_second: number; latency_p50: number; latency_p95: number; latency_p99: number; spark?: number[]; recent_requests?: RequestRow[]; by_status?: Record<string, number> }

const methodClass = (m: string) => m === 'GET' ? 'bg-blue-100 text-blue-700' : m === 'POST' ? 'bg-emerald-100 text-emerald-700' : m === 'DELETE' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
const statusClass = (s: number) => s >= 500 ? 'text-red-600' : s >= 400 ? 'text-amber-600' : 'text-emerald-600'

export default function RequestTimeline() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [filter, setFilter] = useState('')
  const [paused, setPaused] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const res = await api.get(devApi.metrics)
      setMetrics(res.data)
      setError('')
    } catch {
      setError('Metrics endpoint unavailable.')
    }
  }

  useEffect(() => { load().catch(() => {}) }, [])
  useEffect(() => {
    if (paused) return
    const id = window.setInterval(() => load().catch(() => {}), 2500)
    return () => window.clearInterval(id)
  }, [paused])

  const rows = (metrics?.recent_requests || []).filter(r => !filter.trim() || `${r.method} ${r.path} ${r.status}`.toLowerCase().includes(filter.toLowerCase())).slice().reverse()
  const maxSpark = Math.max(1, ...(metrics?.spark || [0]))

  return (
    <div className="space-y-5">
      {error && <div className="rounded-[var(--radius)] border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-bold text-amber-800">{error}</div>}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
        {[
          ['Requests', metrics?.total_requests ?? 0],
          ['Errors', metrics?.total_errors ?? 0],
          ['Error rate', `${metrics?.error_rate ?? 0}%`],
          ['Rate/s', metrics?.rate_per_second ?? 0],
          ['p95', `${metrics?.latency_p95 ?? 0} ms`],
          ['p99', `${metrics?.latency_p99 ?? 0} ms`],
        ].map(([label, value]) => (
          <div key={label} className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] p-3">
            <div className="text-[10px] uppercase font-black tracking-wider text-[var(--text-3)]">{label}</div>
            <div className="text-lg font-black text-[var(--text)] mt-1">{value}</div>
          </div>
        ))}
      </div>

      <section className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-hidden">
        <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-[var(--line)] bg-[var(--surface-2)]">
          <div className="flex items-center gap-2 font-black text-sm text-[var(--text)]"><Activity size={16} /> Live Request Timeline</div>
          <div className="flex items-center gap-2">
            <input className="arc-input h-8 text-xs w-64" placeholder="Filter path, method, status" value={filter} onChange={e => setFilter(e.target.value)} />
            <button className="arc-btn" onClick={() => setPaused(p => !p)}>{paused ? 'Resume' : 'Pause'}</button>
            <button className="arc-btn" onClick={load}><RefreshCw size={13} /></button>
          </div>
        </div>
        <div className="flex items-end gap-1 h-16 px-4 py-3 border-b border-[var(--line)]">
          {(metrics?.spark || []).map((v, i) => (
            <div key={i} className="flex-1 rounded-sm bg-[var(--accent)]/70" style={{ height: `${Math.max(4, (v / maxSpark) * 40)}px` }} title={`${v} requests`} />
          ))}
        </div>
        <div className="max-h-[480px] overflow-auto">
          {rows.length === 0 ? <div className="py-12 text-center text-sm text-[var(--text-3)]">No recent requests.</div> : rows.map((r, i) => (
            <div key={`${r.ts}-${i}`} className="grid grid-cols-[82px_72px_1fr_72px_120px] gap-3 items-center px-4 py-2.5 border-b border-[var(--line)] text-xs hover:bg-[var(--surface-2)]">
              <span className="font-mono text-[var(--text-3)]">{new Date(r.ts * 1000).toLocaleTimeString()}</span>
              <span className={`w-fit px-2 py-0.5 rounded font-black ${methodClass(r.method)}`}>{r.method}</span>
              <code className="truncate text-[var(--accent)]">{r.path}</code>
              <span className={`font-black ${statusClass(r.status)}`}>{r.status}</span>
              <div className="flex items-center gap-2">
                <div className="h-1.5 flex-1 bg-[var(--surface-2)] rounded overflow-hidden">
                  <div className="h-full bg-[var(--accent)]" style={{ width: `${Math.min(100, r.ms)}%` }} />
                </div>
                <span className="font-mono text-[var(--text-2)] w-12 text-right">{r.ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
