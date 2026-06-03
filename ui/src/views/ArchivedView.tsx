import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, RotateCcw, Archive } from 'lucide-react'
import api from '../lib/api'
import { cleanResourcePath } from '../lib/resourceUtils'
import { useAras } from '../aras-core/hooks/useAras'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'
import ArasTable from '../aras-core/components/ArasTable'
import { useAsyncData } from '../hooks/useAsyncData'

interface Field {
  name: string
  label: string
  type: string
  hidden?: boolean
  list_hidden?: boolean
}

interface MetaResult { title: string; columns: Field[] }
interface RowsResult { rows: any[] }

export default function ArchivedView() {
  const params = useParams()
  const navigate = useNavigate()
  const { notify } = useAras()
  const resource = useMemo(() => params['*'] || '', [params])
  const cleanResource = useMemo(() => cleanResourcePath(resource), [resource])

  const [selectedId, setSelectedId] = useState<string | number | null>(null)

  const { data: meta } = useAsyncData<MetaResult>(async () => {
    try {
      const res = await api.get(`/${cleanResource}/metadata`)
      const m = res.data?.data ?? res.data
      const cols: Field[] = (m?.fields ?? [])
        .filter((f: Field) => !f.hidden && !f.list_hidden && f.type !== 'child_table')
        .slice(0, 6)
      return { title: m?.title ?? cleanResource, columns: cols }
    } catch {
      return { title: cleanResource, columns: [{ name: 'id', label: 'ID', type: 'integer' }, { name: 'number', label: 'Number', type: 'text' }] }
    }
  }, [cleanResource])

  const { data: rowsData, loading, reload: reloadRows } = useAsyncData<RowsResult>(async () => {
    const res = await api.get(`/${cleanResource}/deleted`)
    return { rows: res.data?.data?.items ?? res.data?.items ?? res.data ?? [] }
  }, [cleanResource])

  const rows = rowsData?.rows ?? []
  const columns = meta?.columns ?? []
  const resourceTitle = meta?.title ?? cleanResource

  const restore = async () => {
    if (!selectedId) return
    try {
      await api.post(`/${cleanResource}/${selectedId}/restore`)
      notify('Record restored', 'success')
      setSelectedId(null)
      reloadRows()
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
        // claude-sonnet-4-6
        (() => {
          const archivedColumns = [
            { key: '__radio', label: '', width: 40, sortable: false, render: (_: any, row: any) => (
              <input type="radio" checked={selectedId === row.id} onChange={() => setSelectedId(row.id)} className="accent-indigo-600" />
            )},
            ...columns.map(col => ({ key: col.name, label: col.label, field: col.name, render: (v: any) => v == null ? '—' : String(v) })),
            { key: 'deleted_at', label: 'Deleted At', render: (v: any) => <span className="text-[var(--app-muted)] text-xs">{v ? new Date(v).toLocaleString() : '—'}</span> },
          ]
          return (
            <ArasTable
              columns={archivedColumns}
              rows={rows}
              rowKey={(row) => row.id}
              rowClassName={(row) => selectedId === row.id ? 'bg-[var(--accent)]/8' : ''}
              minWidth={640}
            />
          )
        })()
      )}
    </div>
  )
}
