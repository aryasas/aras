import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import ArasTableToolbar from './ArasTableToolbar'

export default function ArasListView({ app, resource, columns = [], title }) {
  useEffect(() => {
    console.log('[aras] ArasListView mounting:', { app, resource, title });
  }, [app, resource, title]);

  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: [app, resource, page, q],
    queryFn: () => api.list(app, resource, { page, q: q || undefined }),
  })

  const rows = data?.data ?? []
  const total = data?.meta?.total ?? rows.length

  return (
    <div className="flex flex-col bg-white border border-gray-200 rounded-none overflow-hidden shadow-sm h-full min-h-[400px]">
      <ArasTableToolbar
        title={title ?? resource}
        searchValue={q}
        onSearch={(val) => { setQ(val); setPage(1) }}
        onAdd={() => window.location.href = `/admin/${app}/${resource}/add/`}
        totalRecords={total}
        onRefresh={() => refetch()}
        isLoading={isLoading}
      />

      {error && (
        <div className="p-3 bg-red-50 text-red-700 text-[13px] border-b border-red-100">
          {error.message}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead className="bg-[#f8fafc] text-gray-500 uppercase text-[11px] font-bold tracking-wider border-b border-gray-200">
            <tr>
              {columns.map(col => (
                <th key={col.name} className="px-4 py-3 text-left">
                  {col.label ?? col.name}
                </th>
              ))}
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading && rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="px-4 py-12 text-center text-gray-400 italic">
                  Loading data...
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="px-4 py-12 text-center text-gray-400 italic">
                  No records found.
                </td>
              </tr>
            ) : rows.map((row, i) => (
              <tr key={row?.id ?? i} className="hover:bg-[#f1f5f9] transition-colors group">
                {columns.map(col => (
                  <td key={col.name} className="px-4 py-3 text-gray-700">
                    {row?.[col.name] ?? '—'}
                  </td>
                ))}
                <td className="px-4 py-3 text-right">
                  {row?.id && (
                    <a
                      href={`/admin/${app}/${resource}/${row.id}/edit/`}
                      className="text-[#2d4a6b] hover:text-[#0f1b2d] font-semibold text-xs"
                    >
                      Edit
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* FOOTER */}
      <div className="bg-[#faf8f3] px-4 py-2 border-t border-gray-200 flex justify-between items-center text-[12px] text-gray-500 mt-auto">
        <span>Showing {rows.length} of {total} total</span>
        <div className="flex gap-1">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="p-1 px-3 border border-gray-300 rounded-none bg-white hover:bg-gray-50 disabled:opacity-30 disabled:hover:bg-white shadow-sm transition-all"
          >
            Prev
          </button>
          <button
            disabled={rows.length < 20}
            onClick={() => setPage(p => p + 1)}
            className="p-1 px-3 border border-gray-300 rounded-none bg-white hover:bg-gray-50 disabled:opacity-30 disabled:hover:bg-white shadow-sm transition-all"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
