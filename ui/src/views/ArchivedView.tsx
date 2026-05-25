import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, RotateCcw, Archive } from 'lucide-react'
import api from '../lib/api'
import { cleanResourcePath } from '../lib/resourceUtils'
import { useAras } from '../aras-core/hooks/useAras'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'

interface Field {
  name: string
  label: string
  type: string
  hidden?: boolean
  list_hidden?: boolean
}

export default function ArchivedView() {
  const params = useParams()
  const navigate = useNavigate()
  const { notify } = useAras()
  const resource = useMemo(() => params['*'] || '', [params])
  const cleanResource = useMemo(() => cleanResourcePath(resource), [resource])

  const [rows, setRows] = useState<any[]>([])
  const [columns, setColumns] = useState<Field[]>([])
  const [resourceTitle, setResourceTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | number | null>(null)

  const loadMetadata = useCallback(async () => {
    if (!cleanResource) return
    try {
      const res = await api.get(`/${cleanResource}/metadata`)
      const meta = res.data?.data ?? res.data
      setResourceTitle(meta?.title ?? cleanResource)
      const cols: Field[] = (meta?.fields ?? []).filter(
        (f: Field) => !f.hidden && !f.list_hidden && f.type !== 'child_table'
      ).slice(0, 6)
      setColumns(cols)
    } catch {
      // fallback: show id + name columns
      setColumns([{ name: 'id', label: 'ID', type: 'integer' }, { name: 'number', label: 'Number', type: 'text' }])
    }
  }, [cleanResource])

  const loadRows = useCallback(async () => {
    if (!cleanResource) return
    try {
      setLoading(true)
      const res = await api.get(`/${cleanResource}/deleted`)
      setRows(res.data?.data?.items ?? res.data?.items ?? res.data ?? [])
    } catch (err: any) {
      notify(err.message || 'Failed to load archived records', 'error')
    } finally {
      setLoading(false)
    }
  }, [cleanResource, notify])

  useEffect(() => {
    loadMetadata()
    loadRows()
  }, [loadMetadata, loadRows])

  const restore = async () => {
    if (!selectedId) return
    try {
      await api.post(`/${cleanResource}/${selectedId}/restore`)
      notify('Record restored', 'success')
      setSelectedId(null)
      loadRows()
    } catch (err: any) {
      notify(err.message || 'Failed to restore record', 'error')
    }
  }

  const parentPath = useMemo(() => `/${cleanResource}`, [cleanResource])

  if (loading) return <LoadingState label="Loading archive..." />

  return (
    <div className="flex flex-col rounded-[var(--app-radius-lg)] border border-[var(--app-border)] bg-[var(--app-panel)] shadow-sm">
      <div className="flex items-center justify-between gap-4 border-b border-[var(--app-border)] p-4">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(parentPath)} className="rounded-[var(--app-radius)] p-2 text-[var(--app-muted)] hover:bg-[var(--app-panel-soft)]">
            <ArrowLeft size={18} />
          </button>
          <div className="flex items-center gap-2">
            <Archive size={18} className="text-[var(--app-muted)]" />
            <div>
              <h1 className="text-lg font-bold text-[var(--app-text)]">Archived — {resourceTitle}</h1>
              <p className="text-xs font-medium uppercase tracking-wider text-[var(--app-muted)]">{cleanResource}</p>
            </div>
          </div>
        </div>
        <button
          onClick={restore}
          disabled={!selectedId}
          className="flex items-center gap-2 rounded-[var(--app-radius)] bg-[var(--app-accent)] px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-40"
        >
          <RotateCcw size={16} />
          Restore
        </button>
      </div>

      {rows.length === 0 ? (
        <EmptyState title="No archived records" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-[var(--app-panel-soft)] text-xs font-bold uppercase tracking-wider text-[var(--app-muted)]">
              <tr>
                <th className="w-10 px-4 py-3" />
                {columns.map(col => (
                  <th key={col.name} className="px-4 py-3">{col.label}</th>
                ))}
                <th className="px-4 py-3">Deleted At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((row) => (
                <tr key={row.id} className={selectedId === row.id ? 'bg-[var(--app-accent-glow)]/50' : 'hover:bg-[var(--app-panel-soft)]'}>
                  <td className="px-4 py-3">
                    <input
                      type="radio"
                      checked={selectedId === row.id}
                      onChange={() => setSelectedId(row.id)}
                      className="accent-indigo-600"
                    />
                  </td>
                  {columns.map(col => (
                    <td key={col.name} className="px-4 py-3 text-[var(--app-text)]">
                      {row[col.name] == null ? '—' : String(row[col.name])}
                    </td>
                  ))}
                  <td className="px-4 py-3 text-[var(--app-muted)] text-xs">
                    {row.deleted_at ? new Date(row.deleted_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
