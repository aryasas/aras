import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function ArasListView({ app, resource, columns = [], title }) {
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: [app, resource, page, q],
    queryFn: () => api.list(app, resource, { page, q: q || undefined }),
  })

  const rows = data?.items ?? data ?? []
  const total = data?.total ?? rows.length

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">{title ?? resource}</h2>
        <div className="flex gap-2">
          <input
            type="search"
            placeholder="Search..."
            value={q}
            onChange={e => { setQ(e.target.value); setPage(1) }}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <a
            href={`/admin/${app}/${resource}/add/`}
            className="bg-blue-600 text-white text-sm px-3 py-1.5 rounded hover:bg-blue-700"
          >
            + Add
          </a>
        </div>
      </div>

      {error && (
        <div className="text-red-600 text-sm mb-3">{error.message}</div>
      )}

      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              {columns.map(col => (
                <th key={col.key} className="px-4 py-3 text-left font-medium">
                  {col.label ?? col.key}
                </th>
              ))}
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length + 1} className="px-4 py-8 text-center text-gray-400">
                  Loading...
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="px-4 py-8 text-center text-gray-400">
                  No records found.
                </td>
              </tr>
            ) : rows.map(row => (
              <tr key={row.id} className="hover:bg-gray-50">
                {columns.map(col => (
                  <td key={col.key} className="px-4 py-3 text-gray-700">
                    {row[col.key] ?? '—'}
                  </td>
                ))}
                <td className="px-4 py-3 text-right">
                  <a
                    href={`/admin/${app}/${resource}/${row.id}/edit/`}
                    className="text-blue-600 hover:underline text-xs mr-3"
                  >
                    Edit
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {total > 20 && (
        <div className="flex justify-between items-center mt-3 text-sm text-gray-500">
          <span>{total} total</span>
          <div className="flex gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Prev
            </button>
            <button
              disabled={rows.length < 20}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
