import React, { useState } from 'react'
import { Play, Loader2 } from 'lucide-react'
import api from '../../lib/api'
import DataGrid from '../../aras-core/components/DataGrid'
import { devApi } from './devApi'

// claude-opus-4-8
// Read-only SQL console. Backend (POST /dev/dev/sql) rejects any mutation; this is the UI.
export default function SqlRunner() {
  const [sql, setSql] = useState('SELECT name FROM sqlite_master WHERE type = \'table\' LIMIT 50')
  const [limit, setLimit] = useState(100)
  const [result, setResult] = useState<{ columns: string[]; rows: Record<string, unknown>[]; row_count: number; elapsed_ms: number } | null>(null)
  const [error, setError] = useState('')
  const [running, setRunning] = useState(false)

  const run = async () => {
    setRunning(true)
    setError('')
    try {
      const res = await api.post(devApi.sql, { sql, limit })
      setResult(res.data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err.response?.data?.detail || 'query failed')
      setResult(null)
    } finally {
      setRunning(false)
    }
  }

  const onKey = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') run()
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-black text-[var(--text)]">SQL Runner</h2>
          <span className="text-xs text-[var(--text-3)]">Read-only · ⌘/Ctrl+Enter to run</span>
        </div>
        <textarea
          value={sql}
          onChange={e => setSql(e.target.value)}
          onKeyDown={onKey}
          spellCheck={false}
          rows={5}
          className="w-full font-mono text-sm p-3 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/40 resize-y"
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={run}
          disabled={running}
          className="flex items-center gap-2 px-5 py-2 bg-[var(--accent)] text-white rounded-[var(--radius)] font-bold text-sm hover:opacity-90 disabled:opacity-50 transition-all"
        >
          {running ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
          Run
        </button>
        <label className="flex items-center gap-2 text-sm text-[var(--text-3)]">
          Limit
          <input
            type="number"
            value={limit}
            onChange={e => setLimit(Number(e.target.value) || 100)}
            className="w-20 px-2 py-1 rounded border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm"
          />
        </label>
        {result && (
          <span className="text-xs text-[var(--text-3)] ml-auto font-mono">
            {result.row_count} rows · {result.elapsed_ms}ms
          </span>
        )}
      </div>
      {error && (
        <div className="px-3 py-2 rounded-[var(--radius)] bg-red-50 text-red-700 text-sm font-mono border border-red-200">{error}</div>
      )}
      {result && <DataGrid columns={result.columns} rows={result.rows} empty="Query returned no rows" />}
    </div>
  )
}
