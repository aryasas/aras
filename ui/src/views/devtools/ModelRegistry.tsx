import { useEffect, useMemo, useState } from 'react'
import { Boxes, Search } from 'lucide-react'
import api from '../../lib/api'
import { devApi } from './devApi'

type ModelInfo = { name: string; class_name: string; module: string; table?: string; route?: string; features?: unknown[]; scoped_by?: unknown[]; columns?: { name: string; type: string; nullable: boolean; primary_key: boolean; foreign_keys: string[]; indexed: boolean; unique: boolean }[]; relationships?: { key: string; target: string; direction: string }[] }

export default function ModelRegistry() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<ModelInfo | null>(null)

  useEffect(() => {
    api.get(devApi.inspectModels).then(res => {
      const data = res.data
      const normalized = Array.isArray(data)
        ? data
        : Object.entries(data || {}).map(([name, value]) => ({ name, class_name: String(value), module: '', columns: [], relationships: [] }))
      setModels(normalized)
      setSelected(normalized[0] || null)
    }).catch(() => {})
  }, [])

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    return models.filter(m => `${m.name} ${m.class_name} ${m.table} ${m.module}`.toLowerCase().includes(q))
  }, [models, query])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-5">
      <section className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-hidden">
        <div className="p-3 border-b border-[var(--line)] bg-[var(--surface-2)]">
          <div className="flex items-center gap-2 font-black text-sm text-[var(--text)] mb-2"><Boxes size={16} /> Model Registry</div>
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
            <input className="arc-input pl-8 h-8 text-xs" placeholder="Search models" value={query} onChange={e => setQuery(e.target.value)} />
          </div>
        </div>
        <div className="max-h-[620px] overflow-auto">
          {filtered.map(m => (
            <button key={m.name} onClick={() => setSelected(m)} className={`w-full text-left px-4 py-3 border-b border-[var(--line)] hover:bg-[var(--surface-2)] ${selected?.name === m.name ? 'bg-[var(--accent)]/10' : ''}`}>
              <div className="font-black text-sm text-[var(--text)]">{m.class_name || m.name}</div>
              <div className="font-mono text-[11px] text-[var(--text-3)] truncate">{m.name} · {m.table || 'no table'}</div>
            </button>
          ))}
        </div>
      </section>

      <section className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius-lg)] overflow-hidden">
        {!selected ? <div className="p-10 text-center text-sm text-[var(--text-3)]">No model selected.</div> : (
          <>
            <div className="p-5 border-b border-[var(--line)] bg-[var(--surface-2)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-black text-[var(--text)]">{selected.class_name}</h2>
                  <div className="font-mono text-xs text-[var(--text-3)] mt-1">{selected.module}</div>
                </div>
                {selected.route && <code className="px-2 py-1 rounded bg-[var(--surface)] border border-[var(--line)] text-xs text-[var(--accent)]">{selected.route}</code>}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                <Stat label="Resource" value={selected.name} />
                <Stat label="Table" value={selected.table || '-'} />
                <Stat label="Fields" value={String(selected.columns?.length || 0)} />
                <Stat label="Relations" value={String(selected.relationships?.length || 0)} />
              </div>
            </div>
            <div className="p-5 space-y-5">
              <div>
                <h3 className="text-xs font-black uppercase tracking-wider text-[var(--text-3)] mb-2">Columns</h3>
                <div className="overflow-auto border border-[var(--line)] rounded-[var(--radius)]">
                  <table className="w-full text-xs">
                    <thead className="bg-[var(--surface-2)]"><tr>{['name', 'type', 'flags', 'foreign keys'].map(h => <th key={h} className="text-left px-3 py-2 font-black text-[var(--text-2)]">{h}</th>)}</tr></thead>
                    <tbody>
                      {(selected.columns || []).map(c => (
                        <tr key={c.name} className="border-t border-[var(--line)]">
                          <td className="px-3 py-2 font-mono font-bold text-[var(--text)]">{c.name}</td>
                          <td className="px-3 py-2 font-mono text-[var(--text-2)]">{c.type}</td>
                          <td className="px-3 py-2 text-[var(--text-3)]">{[c.primary_key && 'pk', !c.nullable && 'required', c.indexed && 'index', c.unique && 'unique'].filter(Boolean).join(' · ') || '-'}</td>
                          <td className="px-3 py-2 font-mono text-[var(--text-3)]">{c.foreign_keys?.join(', ') || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <h3 className="text-xs font-black uppercase tracking-wider text-[var(--text-3)] mb-2">Relationships</h3>
                <div className="flex flex-wrap gap-2">
                  {(selected.relationships || []).length ? selected.relationships!.map(r => <span key={r.key} className="px-2.5 py-1 rounded border border-[var(--line)] bg-[var(--surface-2)] text-xs font-mono">{r.key} → {r.target}</span>) : <span className="text-sm text-[var(--text-3)]">None</span>}
                </div>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="bg-[var(--surface)] border border-[var(--line)] rounded-[var(--radius)] p-3 min-w-0"><div className="text-[10px] uppercase font-black text-[var(--text-3)]">{label}</div><div className="text-sm font-bold text-[var(--text)] truncate mt-1">{value}</div></div>
}
