import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Trash2, Pause, Play, Copy, X } from 'lucide-react'
import api from '../../lib/api'
import { devApi } from './devApi'

interface ErrorEntry {
  ts?: number
  timestamp: string
  method: string
  path: string
  status: number
  message: string
}

// claude-sonnet-4-6
export default function LogStream() {
  const [entries, setEntries] = useState<ErrorEntry[]>([])
  const [paused, setPaused] = useState(false)
  const [filter, setFilter] = useState('')
  const [clearing, setClearing] = useState(false)
  const [selected, setSelected] = useState<ErrorEntry | null>(null)
  const lastTs = useRef<number>(0)
  const bottomRef = useRef<HTMLDivElement>(null)
  const pausedRef = useRef(paused)
  pausedRef.current = paused

  const fetchTail = useCallback(async () => {
    if (pausedRef.current) return
    try {
      const params = lastTs.current ? { after: lastTs.current } : {}
      const res = await api.get<ErrorEntry[]>(devApi.errorsTail, { params })
      const newEntries: ErrorEntry[] = res.data
      if (newEntries.length > 0) {
        setEntries(prev => [...prev, ...newEntries].slice(-500))
        const maxTs = Math.max(...newEntries.map(e => e.ts ?? 0))
        if (maxTs > 0) lastTs.current = maxTs
      }
    } catch {
      // silently ignore poll errors
    }
  }, [])

  // Initial load — get existing errors without timestamp filter
  useEffect(() => {
    api.get<ErrorEntry[]>(devApi.errors).then(res => {
      const data = res.data
      setEntries(data)
      const maxTs = Math.max(...data.map((e: ErrorEntry) => e.ts ?? 0))
      if (maxTs > 0) lastTs.current = maxTs
    }).catch(() => {})
  }, [])

  useEffect(() => {
    const id = setInterval(fetchTail, 3000)
    return () => clearInterval(id)
  }, [fetchTail])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries])

  const handleClear = async () => {
    setClearing(true)
    try {
      await api.delete(devApi.errors)
      setEntries([])
      lastTs.current = 0
    } finally {
      setClearing(false)
    }
  }

  const fmt = (entry: ErrorEntry) => {
    if (entry.timestamp) {
      try {
        return new Date(entry.timestamp).toLocaleTimeString('en-GB', { hour12: false })
      } catch { /* fall through */ }
    }
    if (entry.ts) return new Date(entry.ts * 1000).toLocaleTimeString('en-GB', { hour12: false })
    return '??:??:??'
  }

  const statusColor = (status: number) => {
    if (status >= 500) return 'text-red-500'
    if (status >= 400) return 'text-amber-500'
    return 'text-[var(--text-3)]'
  }

  const filtered = filter.trim()
    ? entries.filter(e =>
        e.path?.toLowerCase().includes(filter.toLowerCase()) ||
        e.message?.toLowerCase().includes(filter.toLowerCase()) ||
        String(e.status).includes(filter)
      )
    : entries

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black text-[var(--text)]">Log Stream</h2>
        <div className="flex items-center gap-2">
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Filter logs…"
            className="text-sm px-3 py-1.5 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40 w-48"
          />
          <button
            onClick={() => setPaused(p => !p)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors"
          >
            {paused ? <Play size={13} /> : <Pause size={13} />}
            {paused ? 'Resume' : 'Pause'}
          </button>
          <button
            onClick={handleClear}
            disabled={clearing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors disabled:opacity-50"
          >
            <Trash2 size={13} />
            Clear
          </button>
        </div>
      </div>

      {paused && (
        <div className="text-xs text-amber-500 font-semibold px-1">Polling paused</div>
      )}

      <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] overflow-hidden">
        <div className="overflow-y-auto max-h-[520px] font-mono text-xs">
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-[var(--text-3)]">
              {entries.length === 0
                ? 'No errors logged — the app is healthy.'
                : 'No entries match filter.'}
            </div>
          ) : (
            filtered.map((entry, i) => (
              <button
                key={`${entry.ts ?? ''}-${i}`}
                onClick={() => setSelected(entry)}
                className="w-full text-left flex items-start gap-3 px-4 py-2 border-b border-[var(--line)] last:border-0 hover:bg-[var(--surface-2)] transition-colors"
              >
                <span className="text-[var(--text-3)] shrink-0 w-20">{fmt(entry)}</span>
                <span className={`shrink-0 font-bold w-8 ${statusColor(entry.status)}`}>{entry.status}</span>
                <span className="shrink-0 text-[var(--text-2)] w-12 uppercase">{entry.method}</span>
                <span className="text-[var(--accent)] shrink-0 truncate max-w-[200px]">{entry.path}</span>
                <span className="text-[var(--text-2)] truncate flex-1">{entry.message}</span>
              </button>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>
      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/30" onClick={() => setSelected(null)}>
          <div className="h-full w-full max-w-2xl bg-[var(--surface)] shadow-2xl border-l border-[var(--line)] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="sticky top-0 bg-[var(--surface)]/95 backdrop-blur border-b border-[var(--line)] px-5 py-4 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-black text-[var(--text)]">Error Detail</h3>
                <div className="mt-1 font-mono text-xs text-[var(--text-3)]">{selected.method} {selected.path} · {selected.status}</div>
              </div>
              <div className="flex gap-2">
                <button className="arc-btn" onClick={() => navigator.clipboard.writeText(JSON.stringify(selected, null, 2))}><Copy size={13} /> Copy JSON</button>
                <button className="p-2 rounded-[var(--radius)] hover:bg-[var(--surface-2)]" onClick={() => setSelected(null)}><X size={16} /></button>
              </div>
            </div>
            <div className="p-5">
              <pre className="bg-slate-950 text-slate-200 rounded-[var(--radius)] p-4 text-xs overflow-auto whitespace-pre-wrap">{JSON.stringify(selected, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
