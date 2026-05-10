import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { api } from '../lib/api'
import ArasTableToolbar from './ArasTableToolbar'
import ArasTanStackGrid from './ArasTanStackGrid'

export default function ArasFullListView({ app, resource, columns = [], title }) {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const [perPage, setPerPage] = useState(100)

  // Fetch resource metadata if columns are not provided
...
        <div className="flex items-center justify-end">
          <button 
            className="text-[#c9a568] hover:text-[#6b2c2c] font-medium text-sm flex items-center gap-1 group"
            onClick={(e) => {
              e.stopPropagation()
              navigate(`/admin/${app}/${resource}/form/${row.original.id}`)
            }}
          >
            More
            <svg className="w-3 h-3 group-hover:translate-y-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
          </button>
...
      size: 100,
      enableSorting: false,
    })

    return defs
  }, [activeColumns, app, resource, navigate])

  const table = useReactTable({
    data: rows,
    columns: colDefs,
    getCoreRowModel: getCoreRowModel(),
...
      
      <ArasTableToolbar
        title={activeTitle}
        searchValue={q}
        onSearch={(val) => { setQ(val); setPage(1) }}
        onAdd={() => navigate(`/admin/${app}/${resource}/form/add`)}
        totalRecords={total}
        isLoading={isLoading}
      />

      {error && (
...
      )}

      <ArasTanStackGrid 
        table={table}
        isLoading={isLoading}
        onRowClick={(row) => navigate(`/admin/${app}/${resource}/form/${row.original.id}`)}
      />

      {/* FOOTER - Leucine Pagination Style */}
      <div className="mt-4 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-medium text-gray-500 bg-white p-4 rounded-none border border-gray-100 shadow-sm">
        
