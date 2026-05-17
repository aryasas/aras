import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, RotateCcw } from 'lucide-react'
import api from '../lib/api'
import { useAras } from '../aras-core/hooks/useAras'
import { LoadingState } from '../components/LoadingState'
import { EmptyState } from '../components/EmptyState'

export default function ArchivedView() {
  const params = useParams()
  const navigate = useNavigate()
  const { notify } = useAras()
  const resource = useMemo(() => params['*'] || '', [params])
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | number | null>(null)

  const loadRows = useCallback(async () => {
    if (!resource) return
    try {
      setLoading(true)
      const res = await api.get(`/${resource}/deleted`)
      setRows(res.data?.items ?? res.data ?? [])
    } catch (err: any) {
      notify(err.message || 'Failed to load archived records', 'error')
    } finally {
      setLoading(false)
    }
  }, [resource, notify])

  useEffect(() => {
    loadRows()
  }, [loadRows])

  const restore = async () => {
    if (!selectedId) return
    try {
      await api.post(`/${resource}/${selectedId}/restore`)
      notify('Record restored', 'success')
      setSelectedId(null)
      loadRows()
    } catch (err: any) {
      notify(err.message || 'Failed to restore record', 'error')
    }
  }

  if (loading) return <LoadingState label="Loading archive..." />

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-4 border-b border-slate-100 p-4">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="rounded-xl p-2 text-slate-500 hover:bg-slate-50">
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-lg font-bold text-slate-900">Archived Records</h1>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{resource}</p>
          </div>
        </div>
        <button
          onClick={restore}
          disabled={!selectedId}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-40"
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
            <thead className="bg-slate-50 text-xs font-bold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="w-10 px-6 py-3" />
                <th className="px-6 py-3">Record</th>
                <th className="px-6 py-3">Deleted At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((row) => (
                <tr key={row.id} className={selectedId === row.id ? 'bg-indigo-50/50' : 'hover:bg-slate-50'}>
                  <td className="px-6 py-3">
                    <input type="radio" checked={selectedId === row.id} onChange={() => setSelectedId(row.id)} />
                  </td>
                  <td className="px-6 py-3 font-medium text-slate-700">{row.name || row.code || row.description || row.id}</td>
                  <td className="px-6 py-3 text-slate-500">{row.deleted_at ? new Date(row.deleted_at).toLocaleString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
