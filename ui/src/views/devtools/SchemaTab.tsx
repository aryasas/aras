import React, { useEffect, useState } from 'react'
import { GitCompare, History, Network, Search } from 'lucide-react'
import api from '../../lib/api'
import DataGrid from '../../aras-core/components/DataGrid'
import { devApi } from './devApi'

// claude-opus-4-8
type Diff = { table: string; status: string; details: string[] }
type Migrations = { available: boolean; reason?: string; head?: string; current?: string; up_to_date?: boolean; pending?: { revision: string; doc: string }[] }
type Relations = { name: string; table: string; columns: { name: string; type: string; nullable: boolean; primary_key: boolean }[]; foreign_keys: { column: string; references_table: string; references_column: string }[]; referenced_by: { from_table: string; from_column: string; to_column: string }[] }

const statusColor = (s: string) =>
  s === 'ok' ? 'bg-emerald-100 text-emerald-700'
    : s === 'table_missing' ? 'bg-red-100 text-red-700'
      : 'bg-amber-100 text-amber-700'

// claude-opus-4-8
export default function SchemaTab() {
  const [diff, setDiff] = useState<Diff[]>([])
  const [migrations, setMigrations] = useState<Migrations | null>(null)
  const [relName, setRelName] = useState('')
  const [relations, setRelations] = useState<Relations | null>(null)
  const [relError, setRelError] = useState('')
  const [diffLoaded, setDiffLoaded] = useState(false)
  const [migrationLoaded, setMigrationLoaded] = useState(false)

  useEffect(() => {
    api.get(devApi.schemaDiff).then(r => setDiff(r.data)).catch(() => {}).finally(() => setDiffLoaded(true))
    api.get(devApi.migrations).then(r => setMigrations(r.data)).catch(() => {}).finally(() => setMigrationLoaded(true))
  }, [])

  const loadRelations = async () => {
    if (!relName.trim()) return
    setRelError('')
    try {
      const r = await api.get(devApi.relations(relName.trim()))
      setRelations(r.data)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setRelError(err.response?.data?.detail || 'not found')
      setRelations(null)
    }
  }

  const drift = diff.filter(d => d.status !== 'ok')

  return (
    <div className="space-y-6">
      {drift.length > 0 && (
        <div className="px-4 py-3 rounded-[var(--radius)] bg-amber-50 border border-amber-200 text-amber-800 text-sm font-semibold">
          ⚠ {drift.length} table{drift.length > 1 ? 's' : ''} drifted from the models. Run a migration to sync.
        </div>
      )}

      <Section icon={<GitCompare size={18} />} title="Schema Diff (model vs DB)">
        <div className="space-y-1.5">
          {diff.map(d => (
            <div key={d.table} className="flex items-center gap-3 text-sm py-1 border-b border-[var(--line)] last:border-0">
              <code className="font-mono text-[var(--text)] font-bold min-w-[180px]">{d.table}</code>
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${statusColor(d.status)}`}>{d.status}</span>
              <span className="text-[var(--text-3)] text-xs">{d.details.join(' · ')}</span>
            </div>
          ))}
          {!diff.length && <div className="text-[var(--text-3)] text-sm py-2">{diffLoaded ? 'No schema diff rows returned.' : 'Loading…'}</div>}
        </div>
      </Section>

      <Section icon={<History size={18} />} title="Migrations">
        {!migrations ? <div className="text-[var(--text-3)] text-sm">{migrationLoaded ? 'Migration status unavailable.' : 'Loading…'}</div>
          : !migrations.available ? <div className="text-[var(--text-3)] text-sm">Unavailable: {migrations.reason}</div>
            : (
              <div className="text-sm space-y-1.5">
                <div className="flex gap-2 items-center">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${migrations.up_to_date ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                    {migrations.up_to_date ? 'Up to date' : `${migrations.pending?.length || 0} pending`}
                  </span>
                </div>
                <div className="font-mono text-xs text-[var(--text-3)]">head: {migrations.head || '—'} · current: {migrations.current || '—'}</div>
                {migrations.pending?.map(p => (
                  <div key={p.revision} className="font-mono text-xs text-amber-700">↑ {p.revision} — {p.doc}</div>
                ))}
              </div>
            )}
      </Section>

      <Section icon={<Network size={18} />} title="Relations Inspector">
        <div className="flex gap-2 mb-3">
          <input
            value={relName}
            onChange={e => setRelName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && loadRelations()}
            placeholder="resource or table name…"
            className="flex-1 px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] text-[var(--text)] text-sm font-mono"
          />
          <button onClick={loadRelations} className="flex items-center gap-1.5 px-4 py-2 bg-[var(--accent)] text-white rounded-[var(--radius)] font-bold text-sm hover:opacity-90">
            <Search size={14} /> Inspect
          </button>
        </div>
        {relError && <div className="text-red-600 text-sm font-mono mb-2">{relError}</div>}
        {relations && (
          <div className="space-y-4">
            <div>
              <h4 className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-2">Columns</h4>
              <DataGrid columns={['name', 'type', 'nullable', 'primary_key']} rows={relations.columns as unknown as Record<string, unknown>[]} maxHeight={240} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-2">Foreign keys → ({relations.foreign_keys.length})</h4>
                <DataGrid columns={['column', 'references_table', 'references_column']} rows={relations.foreign_keys as unknown as Record<string, unknown>[]} empty="None" maxHeight={200} />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[var(--text-3)] uppercase tracking-wider mb-2">Referenced by ← ({relations.referenced_by.length})</h4>
                <DataGrid columns={['from_table', 'from_column', 'to_column']} rows={relations.referenced_by as unknown as Record<string, unknown>[]} empty="None" maxHeight={200} />
              </div>
            </div>
          </div>
        )}
      </Section>
    </div>
  )
}

// claude-opus-4-8
function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[var(--surface)] p-5 rounded-[var(--radius-lg)] border border-[var(--line)] shadow-sm">
      <div className="flex items-center gap-2 text-[var(--text)] mb-3">{icon}<h3 className="font-black text-sm">{title}</h3></div>
      {children}
    </div>
  )
}
