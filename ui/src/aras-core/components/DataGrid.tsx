import React from 'react'

// claude-opus-4-8
// Generic column/row grid for raw dev responses (SQL results, relations, matrices).
// Distinct from ArasTable (metadata-driven) — this renders arbitrary {columns, rows}.
export default function DataGrid({ columns, rows, empty = 'No rows', maxHeight = 480 }: {
  columns: string[]
  rows: Record<string, unknown>[]
  empty?: string
  maxHeight?: number
}) {
  if (!rows.length) {
    return (
      <div className="text-[var(--text-3)] text-sm py-10 text-center border border-dashed border-[var(--line)] rounded-[var(--radius)]">
        {empty}
      </div>
    )
  }
  const cols = columns.length ? columns : Object.keys(rows[0])
  return (
    <div className="overflow-auto border border-[var(--line)] rounded-[var(--radius)]" style={{ maxHeight }}>
      <table className="w-full text-sm border-collapse">
        <thead className="sticky top-0 bg-[var(--surface-2)] z-10">
          <tr>
            {cols.map(c => (
              <th key={c} className="text-left font-bold text-[var(--text-2)] px-3 py-2 border-b border-[var(--line)] whitespace-nowrap">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-[var(--surface-2)] transition-colors">
              {cols.map(c => (
                <td key={c} className="px-3 py-1.5 border-b border-[var(--line)] font-mono text-xs text-[var(--text)] whitespace-nowrap max-w-md truncate">
                  {fmt(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// claude-opus-4-8
function fmt(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
